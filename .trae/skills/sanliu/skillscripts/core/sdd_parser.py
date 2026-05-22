"""
SDD解析器主模块 - 提供高级规范解析、测试生成和代码生成功能
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .sdd_spec_parser import (
        APISpec,
        CodeSkeleton,
        Feature,
        SpecFormat,
        TestCase,
        ValidationResult,
        generate_code_skeleton,
        generate_test_cases,
        parse_spec_file,
        validate_spec,
        SDDSpecParserFactory,
    )
except ImportError:
    from sdd_spec_parser import (
        APISpec,
        CodeSkeleton,
        Feature,
        SpecFormat,
        TestCase,
        ValidationResult,
        generate_code_skeleton,
        generate_test_cases,
        parse_spec_file,
        validate_spec,
        SDDSpecParserFactory,
    )


@dataclass
class SDDParseResult:
    """SDD解析结果"""
    spec: Any
    format_type: SpecFormat
    validation_result: ValidationResult
    test_cases: List[TestCase] = field(default_factory=list)
    code_skeletons: List[CodeSkeleton] = field(default_factory=list)


@dataclass
class SDDReport:
    """SDD分析报告"""
    spec_name: str
    format_type: str
    is_valid: bool
    completeness_score: float
    test_case_count: int
    code_skeleton_count: int
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    summary: str = ""


class SDDParser:
    """SDD解析器主类"""
    
    def __init__(self, language: str = "python"):
        self.language = language
        self.results: List[SDDParseResult] = []
    
    def parse_and_analyze(self, file_path: str, generate_tests: bool = True, generate_code: bool = True) -> SDDParseResult:
        """解析并分析规范文件"""
        spec, format_type = parse_spec_file(file_path)
        
        validation_result = validate_spec(spec, format_type)
        
        test_cases = []
        if generate_tests:
            test_cases = generate_test_cases(spec, format_type)
        
        code_skeletons = []
        if generate_code:
            code_skeletons = generate_code_skeleton(spec, format_type, self.language)
        
        result = SDDParseResult(
            spec=spec,
            format_type=format_type,
            validation_result=validation_result,
            test_cases=test_cases,
            code_skeletons=code_skeletons
        )
        
        self.results.append(result)
        
        return result
    
    def parse_directory(self, directory: str, pattern: str = "**/*", generate_tests: bool = True, generate_code: bool = True) -> List[SDDParseResult]:
        """解析目录中的所有规范文件"""
        results = []
        dir_path = Path(directory)
        
        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                try:
                    format_type = SDDSpecParserFactory.detect_format(str(file_path))
                    if format_type != SpecFormat.UNKNOWN:
                        result = self.parse_and_analyze(
                            str(file_path),
                            generate_tests=generate_tests,
                            generate_code=generate_code
                        )
                        results.append(result)
                except Exception as e:
                    print(f"解析文件 {file_path} 时出错: {e}")
        
        return results
    
    def generate_report(self, result: Optional[SDDParseResult] = None) -> SDDReport:
        """生成分析报告"""
        if result is None and self.results:
            result = self.results[-1]
        
        if not result:
            raise ValueError("没有可用的解析结果")
        
        spec_name = self._get_spec_name(result.spec)
        
        summary = self._generate_summary(result)
        
        return SDDReport(
            spec_name=spec_name,
            format_type=result.format_type.value,
            is_valid=result.validation_result.is_valid,
            completeness_score=result.validation_result.completeness_score,
            test_case_count=len(result.test_cases),
            code_skeleton_count=len(result.code_skeletons),
            errors=result.validation_result.errors,
            warnings=result.validation_result.warnings,
            summary=summary
        )
    
    def _get_spec_name(self, spec: Any) -> str:
        """获取规范名称"""
        if isinstance(spec, Feature):
            return spec.name
        elif isinstance(spec, APISpec):
            return spec.title
        return "Unknown"
    
    def _generate_summary(self, result: SDDParseResult) -> str:
        """生成摘要"""
        spec_name = self._get_spec_name(result.spec)
        
        summary = f"规范 '{spec_name}' 分析结果:\n"
        summary += f"- 格式: {result.format_type.value}\n"
        summary += f"- 完整性分数: {result.validation_result.completeness_score:.1f}/100\n"
        summary += f"- 验证状态: {'通过' if result.validation_result.is_valid else '失败'}\n"
        summary += f"- 错误数: {len(result.validation_result.errors)}\n"
        summary += f"- 警告数: {len(result.validation_result.warnings)}\n"
        summary += f"- 生成测试用例: {len(result.test_cases)}个\n"
        summary += f"- 生成代码骨架: {len(result.code_skeletons)}个\n"
        
        return summary
    
    def export_test_cases(self, output_dir: str, result: Optional[SDDParseResult] = None) -> List[str]:
        """导出测试用例到文件"""
        if result is None and self.results:
            result = self.results[-1]
        
        if not result or not result.test_cases:
            return []
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        
        if self.language == "python":
            exported_files = self._export_python_tests(output_path, result.test_cases)
        elif self.language == "javascript":
            exported_files = self._export_javascript_tests(output_path, result.test_cases)
        
        return exported_files
    
    def _export_python_tests(self, output_path: Path, test_cases: List[TestCase]) -> List[str]:
        """导出Python测试文件"""
        exported_files = []
        
        for test_case in test_cases:
            file_name = f"{test_case.name}.py"
            file_path = output_path / file_name
            
            code = self._generate_python_test_code(test_case)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            exported_files.append(str(file_path))
        
        return exported_files
    
    def _generate_python_test_code(self, test_case: TestCase) -> str:
        """生成Python测试代码"""
        code = f'''"""
{test_case.description}
"""

import pytest


class Test{self._to_class_name(test_case.name)}:
    """测试类: {test_case.name}"""
    
'''
        
        code += f'''    def {test_case.name}(self):
        """
        {test_case.description}
        预期结果: {test_case.expected_result}
        """
'''
        
        for idx, step in enumerate(test_case.steps, 1):
            if isinstance(step, dict):
                action = step.get('action', 'step')
                description = step.get('description', '')
                code += f'''        # 步骤{idx}: {action} - {description}
        # TODO: 实现步骤逻辑
        pass

'''
        
        return code
    
    def _export_javascript_tests(self, output_path: Path, test_cases: List[TestCase]) -> List[str]:
        """导出JavaScript测试文件"""
        exported_files = []
        
        for test_case in test_cases:
            file_name = f"{test_case.name}.test.js"
            file_path = output_path / file_name
            
            code = self._generate_javascript_test_code(test_case)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            exported_files.append(str(file_path))
        
        return exported_files
    
    def _generate_javascript_test_code(self, test_case: TestCase) -> str:
        """生成JavaScript测试代码"""
        code = f'''/**
 * {test_case.description}
 */

describe('{test_case.name}', () => {{
    test('{test_case.description}', () => {{
'''
        
        for idx, step in enumerate(test_case.steps, 1):
            if isinstance(step, dict):
                action = step.get('action', 'step')
                description = step.get('description', '')
                code += f'''        // 步骤{idx}: {action} - {description}
        // TODO: 实现步骤逻辑

'''
        
        code += f'''        // 预期结果: {test_case.expected_result}
    }});
}});
'''
        
        return code
    
    def export_code_skeletons(self, output_dir: str, result: Optional[SDDParseResult] = None) -> List[str]:
        """导出代码骨架到文件"""
        if result is None and self.results:
            result = self.results[-1]
        
        if not result or not result.code_skeletons:
            return []
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = []
        
        for skeleton in result.code_skeletons:
            file_path = output_path / skeleton.file_name
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(skeleton.code)
            
            exported_files.append(str(file_path))
        
        return exported_files
    
    def export_report(self, output_file: str, result: Optional[SDDParseResult] = None) -> str:
        """导出分析报告"""
        report = self.generate_report(result)
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_file.endswith('.json'):
            report_dict = {
                'spec_name': report.spec_name,
                'format_type': report.format_type,
                'is_valid': report.is_valid,
                'completeness_score': report.completeness_score,
                'test_case_count': report.test_case_count,
                'code_skeleton_count': report.code_skeleton_count,
                'errors': report.errors,
                'warnings': report.warnings,
                'summary': report.summary
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, ensure_ascii=False, indent=2)
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report.summary)
                f.write("\n\n详细信息:\n")
                f.write(f"错误:\n")
                for error in report.errors:
                    f.write(f"  - {error}\n")
                f.write(f"\n警告:\n")
                for warning in report.warnings:
                    f.write(f"  - {warning}\n")
        
        return str(output_path)
    
    def _to_class_name(self, name: str) -> str:
        """转换为类名"""
        return ''.join(word.capitalize() for word in name.split('_'))


def parse_sdd_spec(file_path: str, language: str = "python") -> SDDParseResult:
    """解析SDD规范的便捷函数"""
    parser = SDDParser(language=language)
    return parser.parse_and_analyze(file_path)


def analyze_sdd_specs(directory: str, pattern: str = "**/*", language: str = "python") -> List[SDDParseResult]:
    """分析目录中所有SDD规范的便捷函数"""
    parser = SDDParser(language=language)
    return parser.parse_directory(directory, pattern=pattern)


def generate_tests_from_spec(file_path: str, output_dir: str, language: str = "python") -> List[str]:
    """从规范生成测试用例的便捷函数"""
    parser = SDDParser(language=language)
    result = parser.parse_and_analyze(file_path, generate_tests=True, generate_code=False)
    return parser.export_test_cases(output_dir, result)


def generate_code_from_spec(file_path: str, output_dir: str, language: str = "python") -> List[str]:
    """从规范生成代码骨架的便捷函数"""
    parser = SDDParser(language=language)
    result = parser.parse_and_analyze(file_path, generate_tests=False, generate_code=True)
    return parser.export_code_skeletons(output_dir, result)


def validate_sdd_spec(file_path: str) -> ValidationResult:
    """验证SDD规范的便捷函数"""
    spec, format_type = parse_spec_file(file_path)
    return validate_spec(spec, format_type)
