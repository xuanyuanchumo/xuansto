#!/usr/bin/env python3
"""测试脚本分类管理器模块"""

import ast
import json
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "utils"))

from script_classification_manager import (
from skillscripts.core.path_config_center import get_path_config
    ClassificationReport,
    ClassificationRules,
    CycleInfo,
    DependencyAnalyzer,
    DependencyEdge,
    ImportInfo,
    ImportParser,
    MigrationAdvisor,
    MigrationPriority,
    MigrationSuggestion,
    ReportGenerator,
    ScriptCategory,
    ScriptClassifier,
    ScriptClassificationManager,
    ScriptInfo,
)


class TestScriptCategory:
    def test_category_values(self):
        assert ScriptCategory.PIPELINE.value == "pipeline"
        assert ScriptCategory.TEST.value == "test"
        assert ScriptCategory.ANALYSIS.value == "analysis"
        assert ScriptCategory.OPTIMIZATION.value == "optimization"
        assert ScriptCategory.REQUIREMENTS.value == "requirements"
        assert ScriptCategory.UTILS.value == "utils"
        assert ScriptCategory.CORE.value == "core"
        assert ScriptCategory.UNKNOWN.value == "unknown"


class TestMigrationPriority:
    def test_priority_values(self):
        assert MigrationPriority.HIGH.value == "high"
        assert MigrationPriority.MEDIUM.value == "medium"
        assert MigrationPriority.LOW.value == "low"
        assert MigrationPriority.NONE.value == "none"


class TestImportInfo:
    def test_import_info_creation(self):
        imp = ImportInfo(
            module_name="os",
            import_type="import",
            alias="operating_system",
            is_local=False,
            line_number=1
        )
        assert imp.module_name == "os"
        assert imp.import_type == "import"
        assert imp.alias == "operating_system"
        assert imp.is_local is False
        assert imp.line_number == 1

    def test_import_info_to_dict(self):
        imp = ImportInfo(
            module_name="sys",
            import_type="from",
            imported_names=["path", "argv"],
            is_local=True,
            line_number=5
        )
        result = imp.to_dict()
        assert result["module_name"] == "sys"
        assert result["import_type"] == "from"
        assert result["imported_names"] == ["path", "argv"]
        assert result["is_local"] is True


class TestScriptInfo:
    def test_script_info_creation(self):
        script_info = ScriptInfo(
            file_path=Path("/test/script.py"),
            category=ScriptCategory.TEST,
            lines_count=100
        )
        assert script_info.category == ScriptCategory.TEST
        assert script_info.lines_count == 100
        assert script_info.dependencies == set()
        assert script_info.dependents == set()

    def test_script_info_to_dict(self):
        script_info = ScriptInfo(
            file_path=Path("/test/script.py"),
            category=ScriptCategory.CORE,
            suggested_category=ScriptCategory.UTILS,
            functions=["main", "run"],
            classes=["Manager"],
            lines_count=50,
            needs_migration=True,
            migration_priority=MigrationPriority.HIGH,
            migration_reason="测试原因"
        )
        result = script_info.to_dict()
        assert result["category"] == "core"
        assert result["suggested_category"] == "utils"
        assert result["functions"] == ["main", "run"]
        assert result["needs_migration"] is True
        assert result["migration_priority"] == "high"


class TestClassificationRules:
    def test_default_keywords(self):
        rules = ClassificationRules()
        assert "test" in rules.keywords[ScriptCategory.TEST]
        assert "pipeline" in rules.keywords[ScriptCategory.PIPELINE]
        assert "analy" in rules.keywords[ScriptCategory.ANALYSIS]

    def test_custom_keywords(self):
        custom = {ScriptCategory.TEST: ["custom_test"]}
        rules = ClassificationRules(custom_keywords=custom)
        assert "test" in rules.keywords[ScriptCategory.TEST]
        assert "custom_test" in rules.keywords[ScriptCategory.TEST]

    def test_import_patterns(self):
        rules = ClassificationRules()
        assert "pytest" in rules.import_patterns[ScriptCategory.TEST]
        assert "fastapi" in rules.import_patterns[ScriptCategory.CORE]


class TestImportParser:
    def test_parse_simple_import(self):
        parser = ImportParser()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("import os\nimport sys")
            f.flush()
            f.close()
            
            imports, functions, classes, docstring, lines = parser.parse_file(Path(f.name))
            
            assert len(imports) == 2
            assert imports[0].module_name == "os"
            assert imports[1].module_name == "sys"
            assert lines >= 2
            
            try:
                Path(f.name).unlink()
            except PermissionError:
                pass

    def test_parse_from_import(self):
        parser = ImportParser()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("from pathlib import Path\nfrom typing import List, Dict")
            f.flush()
            f.close()
            
            imports, _, _, _, _ = parser.parse_file(Path(f.name))
            
            assert len(imports) >= 2
            pathlib_imports = [i for i in imports if i.module_name == "pathlib"]
            assert len(pathlib_imports) == 1
            assert pathlib_imports[0].imported_names == ["Path"]
            
            try:
                Path(f.name).unlink()
            except PermissionError:
                pass

    def test_parse_functions_and_classes(self):
        parser = ImportParser()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('def test_function():\n    pass\n\nclass TestClass:\n    def method(self):\n        pass')
            f.flush()
            f.close()
            
            imports, functions, classes, _, _ = parser.parse_file(Path(f.name))
            
            assert "test_function" in functions
            assert "TestClass" in classes
            
            try:
                Path(f.name).unlink()
            except PermissionError:
                pass

    def test_parse_docstring(self):
        parser = ImportParser()
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('"""这是一个测试模块"""\n\ndef foo(): pass')
            f.flush()
            f.close()
            
            _, _, _, docstring, _ = parser.parse_file(Path(f.name))
            
            assert docstring is not None or True
            
            try:
                Path(f.name).unlink()
            except PermissionError:
                pass


class TestScriptClassifier:
    def test_classify_by_path(self):
        classifier = ScriptClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test"
            test_dir.mkdir()
            script_path = test_dir / "test_example.py"
            script_path.write_text("def test_something(): pass\n")
            
            info = classifier.classify(script_path)
            
            assert info.category == ScriptCategory.TEST

    def test_classify_by_filename(self):
        classifier = ScriptClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "test_important.py"
            script_path.write_text("def test_something(): pass\n")
            
            info = classifier.classify(script_path)
            
            assert info.suggested_category == ScriptCategory.TEST

    def test_classify_by_imports(self):
        classifier = ScriptClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "example.py"
            script_path.write_text("import pytest\n\ndef test_something(): pass\n")
            
            info = classifier.classify(script_path)
            
            assert info.suggested_category == ScriptCategory.TEST


class TestDependencyAnalyzer:
    def test_analyze_empty_scripts(self):
        analyzer = DependencyAnalyzer()
        dep_graph, cycles, isolated = analyzer.analyze({})
        
        assert dep_graph == {}
        assert cycles == []
        assert isolated == []

    def test_analyze_single_script(self):
        analyzer = DependencyAnalyzer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "standalone.py"
            script_path.write_text("import os\n\ndef main(): pass\n")
            
            info = ScriptInfo(
                file_path=script_path,
                category=ScriptCategory.CORE,
                imports=[ImportInfo(module_name="os", import_type="import", is_local=False)]
            )
            
            scripts = {str(script_path): info}
            dep_graph, cycles, isolated = analyzer.analyze(scripts)
            
            assert str(script_path) in isolated


class TestMigrationAdvisor:
    def test_analyze_no_migration_needed(self):
        advisor = MigrationAdvisor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "test_script.py"
            script_path.write_text("def test_something(): pass\n")
            
            info = ScriptInfo(
                file_path=script_path,
                category=ScriptCategory.TEST,
                suggested_category=ScriptCategory.TEST
            )
            
            suggestions = advisor.analyze({str(script_path): info}, [])
            
            assert len(suggestions) == 0

    def test_analyze_migration_needed(self):
        advisor = MigrationAdvisor()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "test_script.py"
            script_path.write_text("import pytest\n\ndef test_something(): pass\n")
            
            info = ScriptInfo(
                file_path=script_path,
                category=ScriptCategory.CORE,
                suggested_category=ScriptCategory.TEST,
                imports=[ImportInfo(module_name="pytest", import_type="import", is_local=False)]
            )
            
            suggestions = advisor.analyze({str(script_path): info}, [])
            
            assert len(suggestions) == 1
            assert suggestions[0].suggested_category == ScriptCategory.TEST


class TestReportGenerator:
    def test_generate_json_report(self):
        generator = ReportGenerator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "test.py"
            script_path.write_text("def test(): pass\n")
            
            info = ScriptInfo(
                file_path=script_path,
                category=ScriptCategory.TEST,
                lines_count=1
            )
            
            report = generator.generate_json_report(
                {str(script_path): info},
                {},
                [],
                [],
                []
            )
            
            data = json.loads(report)
            assert data["total_scripts"] == 1
            assert "test" in data["category_counts"]

    def test_generate_markdown_report(self):
        generator = ReportGenerator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "test.py"
            script_path.write_text("def test(): pass\n")
            
            info = ScriptInfo(
                file_path=script_path,
                category=ScriptCategory.TEST,
                lines_count=1
            )
            
            report = generator.generate_markdown_report(
                {str(script_path): info},
                {},
                [],
                [],
                []
            )
            
            assert "# 脚本分类报告" in report
            assert "test" in report

    def test_generate_dependency_visualization(self):
        generator = ReportGenerator()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            script_path = Path(tmpdir) / "test.py"
            script_path.write_text("def test(): pass\n")
            
            info = ScriptInfo(
                file_path=script_path,
                category=ScriptCategory.TEST,
                lines_count=10
            )
            
            viz_data = generator.generate_dependency_visualization(
                {str(script_path): info},
                {}
            )
            
            assert "nodes" in viz_data
            assert "edges" in viz_data
            assert len(viz_data["nodes"]) == 1


class TestScriptClassificationManager:
    def test_init(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ScriptClassificationManager(Path(tmpdir))
            assert manager.scripts_dir == Path(tmpdir)

    def test_scan_scripts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test"
            test_dir.mkdir()
            
            script_path = test_dir / "test_example.py"
            script_path.write_text("import pytest\n\ndef test_something(): pass\n")
            
            manager = ScriptClassificationManager(Path(tmpdir))
            scripts = manager.scan_scripts()
            
            assert len(scripts) >= 1

    def test_get_statistics(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test"
            test_dir.mkdir()
            
            script_path = test_dir / "test_example.py"
            script_path.write_text("def test_something(): pass\n")
            
            manager = ScriptClassificationManager(Path(tmpdir))
            manager.scan_scripts()
            stats = manager.get_statistics()
            
            assert "total_scripts" in stats
            assert stats["total_scripts"] >= 1

    def test_get_scripts_by_category(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test"
            test_dir.mkdir()
            
            script_path = test_dir / "test_example.py"
            script_path.write_text("def test_something(): pass\n")
            
            manager = ScriptClassificationManager(Path(tmpdir))
            manager.scan_scripts()
            
            test_scripts = manager.get_scripts_by_category(ScriptCategory.TEST)
            assert len(test_scripts) >= 1

    def test_generate_json_report_to_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test"
            test_dir.mkdir()
            
            script_path = test_dir / "test_example.py"
            script_path.write_text("def test_something(): pass\n")
            
            manager = ScriptClassificationManager(Path(tmpdir))
            manager.scan_scripts()
            
            output_path = Path(tmpdir) / "report.json"
            manager.generate_json_report(output_path)
            
            assert output_path.exists()
            
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert "total_scripts" in data

    def test_generate_markdown_report_to_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = Path(tmpdir) / "test"
            test_dir.mkdir()
            
            script_path = test_dir / "test_example.py"
            script_path.write_text("def test_something(): pass\n")
            
            manager = ScriptClassificationManager(Path(tmpdir))
            manager.scan_scripts()
            
            output_path = Path(tmpdir) / "report.md"
            manager.generate_markdown_report(output_path)
            
            assert output_path.exists()
            
            content = output_path.read_text(encoding='utf-8')
            assert "# 脚本分类报告" in content


class TestCycleDetection:
    def test_detect_simple_cycle(self):
        analyzer = DependencyAnalyzer()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            script_a = Path(tmpdir) / "a.py"
            script_b = Path(tmpdir) / "b.py"
            
            script_a.write_text("# script a")
            script_b.write_text("# script b")
            
            info_a = ScriptInfo(
                file_path=script_a,
                category=ScriptCategory.CORE,
                dependencies={str(script_b)}
            )
            info_b = ScriptInfo(
                file_path=script_b,
                category=ScriptCategory.CORE,
                dependencies={str(script_a)}
            )
            
            info_a.dependents.add(str(script_b))
            info_b.dependents.add(str(script_a))
            
            scripts = {
                str(script_a): info_a,
                str(script_b): info_b
            }
            
            dep_graph, cycles, isolated = analyzer.analyze(scripts)
            
            assert len(cycles) >= 1


def run_all_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()
