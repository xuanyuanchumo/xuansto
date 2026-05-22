#!/usr/bin/env python3
"""测试文件分类管理器模块"""

import json
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "utils"))

from file_classification_manager import (
from skillscripts.core.path_config_center import get_path_config
    ClassificationRule,
    ClassificationResult,
    CleanupPolicy,
    DocCategory,
    DocumentClassifier,
    DocumentInfo,
    FileClassificationError,
    FileClassificationManager,
    PathMapping,
    PathMode,
    PathRelationshipManager,
    ReportCategory,
    ReportClassifier,
    ReportInfo,
)


class TestDocCategory:
    def test_category_values(self):
        assert DocCategory.SPECIFICATION.value == "specification"
        assert DocCategory.DESIGN.value == "design"
        assert DocCategory.API.value == "api"
        assert DocCategory.USER.value == "user"
        assert DocCategory.CHANGELOG.value == "changelog"
        assert DocCategory.ARCHITECTURE.value == "architecture"
        assert DocCategory.UNKNOWN.value == "unknown"


class TestReportCategory:
    def test_category_values(self):
        assert ReportCategory.TEST.value == "test"
        assert ReportCategory.ANALYSIS.value == "analysis"
        assert ReportCategory.REVIEW.value == "review"
        assert ReportCategory.COVERAGE.value == "coverage"
        assert ReportCategory.PERFORMANCE.value == "performance"
        assert ReportCategory.UNKNOWN.value == "unknown"


class TestPathMode:
    def test_mode_values(self):
        assert PathMode.SELF_ITERATION.value == "self_iteration"
        assert PathMode.GUIDE_PROJECT.value == "guide_project"


class TestClassificationRule:
    def test_rule_creation(self):
        rule = ClassificationRule(
            name="test_rule",
            pattern=r"test",
            category="test",
            priority=10,
            description="测试规则",
            target_subdir="test_dir"
        )
        assert rule.name == "test_rule"
        assert rule.pattern == r"test"
        assert rule.category == "test"
        assert rule.priority == 10


class TestDocumentInfo:
    def test_document_info_creation(self):
        doc_info = DocumentInfo(
            file_path=Path("/docs/test.md"),
            file_name="test.md",
            category=DocCategory.SPECIFICATION,
            version="v1.0.0",
            size_bytes=1024,
            created_at="2024-01-01T00:00:00",
            modified_at="2024-01-01T00:00:00",
            extension=".md"
        )
        assert doc_info.file_name == "test.md"
        assert doc_info.category == DocCategory.SPECIFICATION
        assert doc_info.version == "v1.0.0"

    def test_document_info_defaults(self):
        doc_info = DocumentInfo(
            file_path=Path("/docs/test.md"),
            file_name="test.md",
            category=DocCategory.UNKNOWN,
            version=None,
            size_bytes=0,
            created_at="",
            modified_at="",
            extension=".md"
        )
        assert doc_info.tags == []
        assert doc_info.metadata == {}
        assert doc_info.classification_confidence == 0.0


class TestReportInfo:
    def test_report_info_creation(self):
        report_info = ReportInfo(
            file_path=Path("/reports/test_report.json"),
            file_name="test_report.json",
            category=ReportCategory.TEST,
            version="v1.0.0",
            date="2024-01-01",
            size_bytes=2048,
            created_at="2024-01-01T00:00:00",
            modified_at="2024-01-01T00:00:00",
            extension=".json"
        )
        assert report_info.file_name == "test_report.json"
        assert report_info.category == ReportCategory.TEST
        assert report_info.date == "2024-01-01"


class TestPathMapping:
    def test_path_mapping_creation(self):
        mapping = PathMapping(
            source_path=Path("/source/file.md"),
            target_path=Path("/target/file.md"),
            mapping_type="document_classification",
            created_at="2024-01-01T00:00:00"
        )
        assert mapping.is_active is True
        assert mapping.metadata == {}


class TestClassificationResult:
    def test_result_creation(self):
        result = ClassificationResult(
            total_files=10,
            classified_files=8,
            skipped_files=1,
            error_files=1,
            categories={"specification": 5, "design": 3},
            details=[],
            execution_time=1.5,
            timestamp="2024-01-01T00:00:00"
        )
        assert result.total_files == 10
        assert result.classified_files == 8


class TestCleanupPolicy:
    def test_default_policy(self):
        policy = CleanupPolicy()
        assert policy.keep_versions == 5
        assert policy.keep_days == 30
        assert policy.keep_min_count == 3
        assert policy.dry_run is True

    def test_custom_policy(self):
        policy = CleanupPolicy(
            keep_versions=10,
            keep_days=60,
            keep_min_count=5,
            dry_run=False
        )
        assert policy.keep_versions == 10
        assert policy.dry_run is False


class TestFileClassificationError:
    def test_error_without_file(self):
        error = FileClassificationError("测试错误")
        assert str(error) == "测试错误"

    def test_error_with_file(self):
        error = FileClassificationError("测试错误", Path("/test/file.md"))
        assert "测试错误" in str(error)
        assert "file.md" in str(error)


class TestDocumentClassifier:
    def test_classify_api_document(self):
        classifier = DocumentClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = Path(tmpdir) / "api_document.md"
            doc_path.write_text("# API Documentation\n\nThis is an API doc.")
            
            category, confidence, subdir = classifier.classify(doc_path)
            
            assert category == DocCategory.API
            assert confidence >= 0.7

    def test_classify_design_document(self):
        classifier = DocumentClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = Path(tmpdir) / "architecture_design.md"
            doc_path.write_text("# Design Specification\n\nArchitecture design.")
            
            category, confidence, subdir = classifier.classify(doc_path)
            
            assert category in [DocCategory.DESIGN, DocCategory.ARCHITECTURE]

    def test_classify_test_document(self):
        classifier = DocumentClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = Path(tmpdir) / "test_guide.md"
            doc_path.write_text("# Test Guide\n\nUser testing guide.")
            
            category, confidence, subdir = classifier.classify(doc_path)
            
            assert category == DocCategory.USER

    def test_extract_version_from_filename(self):
        classifier = DocumentClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = Path(tmpdir) / "api_v1.2.3.md"
            doc_path.write_text("# API Doc")
            
            version = classifier.extract_version(doc_path)
            
            assert version == "v1.2.3"

    def test_extract_version_from_path(self):
        classifier = DocumentClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            version_dir = Path(tmpdir) / "v2.0.0"
            version_dir.mkdir()
            doc_path = version_dir / "document.md"
            doc_path.write_text("# Document")
            
            version = classifier.extract_version(doc_path)
            
            assert version == "v2.0.0"

    def test_get_document_info(self):
        classifier = DocumentClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            doc_path = Path(tmpdir) / "specification_v1.0.0.md"
            doc_path.write_text("# Specification\n\nVersion 1.0.0")
            
            info = classifier.get_document_info(doc_path)
            
            assert info.file_name == "specification_v1.0.0.md"
            assert info.category == DocCategory.SPECIFICATION
            assert info.version == "v1.0.0"
            assert info.extension == ".md"


class TestReportClassifier:
    def test_classify_test_report(self):
        classifier = ReportClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "test_report_2024-01-01.json"
            report_path.write_text('{"type": "test"}')
            
            category, confidence, subdir = classifier.classify(report_path)
            
            assert category == ReportCategory.TEST

    def test_classify_coverage_report(self):
        classifier = ReportClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "coverage_report.html"
            report_path.write_text("<html>Coverage Report</html>")
            
            category, confidence, subdir = classifier.classify(report_path)
            
            assert category == ReportCategory.COVERAGE

    def test_extract_date_from_filename(self):
        classifier = ReportClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "test_report_2024-03-15.json"
            report_path.write_text('{}')
            
            date = classifier.extract_date(report_path)
            
            assert date == "2024-03-15"

    def test_get_report_info(self):
        classifier = ReportClassifier()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "analysis_v1.0.0_2024-01-01.json"
            report_path.write_text('{"data": "test"}')
            
            info = classifier.get_report_info(report_path)
            
            assert info.category == ReportCategory.ANALYSIS
            assert info.version == "v1.0.0"
            assert info.date == "2024-01-01"


class TestPathRelationshipManager:
    def test_init(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PathRelationshipManager(Path(tmpdir))
            assert manager.base_path == Path(tmpdir)
            assert manager.mode == PathMode.SELF_ITERATION

    def test_get_all_paths(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PathRelationshipManager(Path(tmpdir))
            paths = manager.get_all_paths()
            
            assert "base" in paths
            assert "docs" in paths
            assert "docs_libs" in paths
            assert "docs_reports" in paths

    def test_validate_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PathRelationshipManager(Path(tmpdir))
            
            valid, error = manager.validate_path(Path(tmpdir), must_exist=True)
            assert valid is True
            
            valid, error = manager.validate_path(Path(tmpdir), must_exist=False)
            assert valid is True
            
            nonexistent = Path(tmpdir) / "nonexistent_file_12345.txt"
            valid, error = manager.validate_path(nonexistent, must_exist=True)
            assert valid is False

    def test_fix_relative_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PathRelationshipManager(Path(tmpdir))
            
            fixed = manager.fix_path(Path("relative/path"))
            assert fixed.is_absolute()

    def test_add_mapping(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PathRelationshipManager(Path(tmpdir))
            
            manager.add_mapping(
                Path("/source/file.md"),
                Path("/target/file.md"),
                "test_mapping"
            )
            
            assert len(manager.mappings) == 1
            assert manager.mappings[0].mapping_type == "test_mapping"

    def test_get_mapping(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PathRelationshipManager(Path(tmpdir))
            
            source = Path("/source/file.md")
            target = Path("/target/file.md")
            manager.add_mapping(source, target, "test")
            
            mapping = manager.get_mapping(source)
            assert mapping is not None
            assert mapping.target_path == target

    def test_generate_path_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = PathRelationshipManager(Path(tmpdir))
            report = manager.generate_path_report()
            
            assert "base_path" in report
            assert "mode" in report
            assert "paths" in report


class TestFileClassificationManager:
    def test_init(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            assert manager.base_path == Path(tmpdir)

    def test_ensure_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            assert manager.docs_dir.exists()
            assert manager.libs_dir.exists()
            assert manager.reports_dir.exists()

    def test_scan_documents(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            doc_path = manager.docs_dir / "test_api.md"
            doc_path.write_text("# API Documentation")
            
            documents = manager.scan_documents()
            
            assert len(documents) >= 1
            assert any(d.file_name == "test_api.md" for d in documents)

    def test_scan_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            report_path = manager.reports_dir / "test_report.json"
            report_path.write_text('{"type": "test"}')
            
            reports = manager.scan_reports()
            
            assert len(reports) >= 1

    def test_classify_documents_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            doc_path = manager.docs_dir / "api_spec.md"
            doc_path.write_text("# API Specification")
            
            result = manager.classify_documents(dry_run=True)
            
            assert result.total_files >= 1
            assert result.classified_files >= 1

    def test_classify_reports_dry_run(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            report_path = manager.reports_dir / "coverage_report.json"
            report_path.write_text('{"coverage": 80}')
            
            result = manager.classify_reports(dry_run=True)
            
            assert result.total_files >= 1

    def test_generate_json_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            doc_path = manager.docs_dir / "api_doc.md"
            doc_path.write_text("# API Documentation")
            
            report = manager.generate_classification_report(output_format="json")
            
            data = json.loads(report)
            assert "summary" in data
            assert "documents" in data

    def test_generate_markdown_report(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            doc_path = manager.docs_dir / "design_doc.md"
            doc_path.write_text("# Design Document")
            
            report = manager.generate_classification_report(output_format="markdown")
            
            assert "# 文件归类报告" in report

    def test_generate_file_manifest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            doc_path = manager.docs_dir / "test_doc.md"
            doc_path.write_text("# Test Document")
            
            manifest = manager.generate_file_manifest()
            
            assert "generated_at" in manifest
            assert "documents" in manifest
            assert "statistics" in manifest

    def test_generate_path_diagram(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            diagram = manager.generate_path_diagram()
            
            assert "```mermaid" in diagram
            assert "graph TD" in diagram

    def test_add_custom_doc_rule(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            manager.add_custom_doc_rule(
                name="custom_rule",
                pattern=r"custom",
                category=DocCategory.USER,
                priority=15,
                target_subdir="custom"
            )
            
            doc_path = manager.docs_dir / "custom_document.md"
            doc_path.write_text("# Custom Document")
            
            category, _, _ = manager.doc_classifier.classify(doc_path)
            assert category == DocCategory.USER

    def test_add_custom_report_rule(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            manager.add_custom_report_rule(
                name="custom_report_rule",
                pattern=r"custom_report",
                category=ReportCategory.ANALYSIS,
                priority=15,
                target_subdir="custom"
            )
            
            report_path = manager.reports_dir / "custom_report_data.json"
            report_path.write_text('{}')
            
            category, _, _ = manager.report_classifier.classify(report_path)
            assert category == ReportCategory.ANALYSIS

    def test_cleanup_old_reports(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            v1_dir = manager.reports_dir / "v1.0.0"
            v2_dir = manager.reports_dir / "v2.0.0"
            v1_dir.mkdir()
            v2_dir.mkdir()
            
            old_report = v1_dir / "old_report.json"
            old_report.write_text('{}')
            new_report = v2_dir / "new_report.json"
            new_report.write_text('{}')
            
            policy = CleanupPolicy(keep_versions=1, keep_days=0, dry_run=True)
            result = manager.cleanup_old_reports(policy=policy, dry_run=True)
            
            assert "deleted_files" in result
            assert "kept_files" in result


class TestIntegration:
    def test_full_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = FileClassificationManager(base_path=tmpdir)
            
            doc_path = manager.docs_dir / "api_specification_v1.0.0.md"
            doc_path.write_text("# API Specification\n\nThis is the API documentation.")
            
            report_path = manager.reports_dir / "test_report_2024-03-15.json"
            report_path.write_text('{"tests": 10, "passed": 9}')
            
            documents = manager.scan_documents()
            assert len(documents) >= 1
            
            reports = manager.scan_reports()
            assert len(reports) >= 1
            
            doc_result = manager.classify_documents(dry_run=True)
            assert doc_result.classified_files >= 1
            
            report_result = manager.classify_reports(dry_run=True)
            assert report_result.classified_files >= 1
            
            manifest = manager.generate_file_manifest()
            assert manifest["statistics"]["total_documents"] >= 1
            
            path_report = manager.path_manager.generate_path_report()
            assert path_report["mode"] == "self_iteration"


def run_all_tests():
    """运行所有测试"""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()
