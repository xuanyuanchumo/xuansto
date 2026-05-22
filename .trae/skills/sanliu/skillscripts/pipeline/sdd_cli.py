#!/usr/bin/env python3
"""
SDD规范智能解析工具 - 统一CLI入口

整合所有SDD规范解析和生成功能：
1. 规范解析与验证
2. 测试用例生成
3. 代码骨架生成
4. API文档生成

使用示例：
    python sdd_cli.py parse specs/user_auth.md --validate
    python sdd_cli.py test specs/user_auth.md --framework pytest
    python sdd_cli.py code specs/user_auth.md --language python
    python sdd_cli.py doc specs/user_auth.md --format openapi
    python sdd_cli.py all specs/user_auth.md
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from skillscripts.core.path_config_center import get_path_config

sys.path.insert(0, str(get_path_config().SKILL_ROOT))
sys.path.insert(0, str(get_path_config().SKILL_ROOT / "skillscripts"))

from skillscripts.pipeline.sdd_spec_parser import (
    SDDSpecParserEnhanced,
    SpecFormat,
    SDDSpecification,
)
from skillscripts.test.sdd_test_generator_enhanced import (
    MultiFrameworkTestGenerator,
    TestFramework,
)
from skillscripts.pipeline.sdd_code_generator import (
    MultiLanguageCodeGenerator,
    ProgrammingLanguage,
)
from skillscripts.pipeline.sdd_api_doc_generator import (
    APIDocGenerator,
    DocFormat,
)


class SDDCLI:
    """SDD规范智能解析工具CLI"""
    
    def __init__(self):
        self.spec_parser = SDDSpecParserEnhanced()
        self.test_generator = MultiFrameworkTestGenerator()
        self.code_generator = MultiLanguageCodeGenerator()
        self.doc_generator = APIDocGenerator()
    
    def parse(
        self,
        spec_path: str,
        validate: bool = True,
        convert: Optional[str] = None,
        output: Optional[str] = None,
    ):
        """解析规范文件"""
        print(f"\n{'='*60}")
        print(f"解析规范文件: {spec_path}")
        print(f"{'='*60}\n")
        
        try:
            spec, validation_result = self.spec_parser.parse_file(spec_path)
            
            self._print_spec_info(spec)
            
            if validate or validation_result.errors or validation_result.warnings:
                self._print_validation_result(validation_result)
            
            if convert:
                format_map = {
                    "yaml": SpecFormat.YAML,
                    "json": SpecFormat.JSON,
                    "markdown": SpecFormat.MARKDOWN,
                }
                target_format = format_map.get(convert.lower())
                if target_format:
                    converted = self.spec_parser.convert_format(spec, target_format)
                    
                    if output:
                        Path(output).write_text(converted, encoding="utf-8")
                        print(f"\n已转换并保存到: {output}")
                    else:
                        print(f"\n转换结果 ({convert}):")
                        print("-" * 40)
                        print(converted)
            
            return spec, validation_result
        
        except FileNotFoundError as e:
            print(f"错误: {e}")
            return None, None
        except Exception as e:
            print(f"解析错误: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def test(
        self,
        spec_path: str,
        framework: str = "pytest",
        output: str = "tests/generated",
    ):
        """生成测试用例"""
        print(f"\n{'='*60}")
        print(f"生成测试用例: {spec_path}")
        print(f"{'='*60}\n")
        
        frameworks = self._parse_frameworks(framework)
        
        try:
            results = self.test_generator.generate_from_spec_file(
                spec_path, frameworks, output
            )
            
            print(f"\n生成完成:")
            for result in results:
                print(f"  - {result.filename}: {result.test_count} 个测试用例 ({result.framework.value})")
            
            return results
        
        except Exception as e:
            print(f"生成错误: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def code(
        self,
        spec_path: str,
        language: str = "python",
        output: str = "generated",
    ):
        """生成代码骨架"""
        print(f"\n{'='*60}")
        print(f"生成代码骨架: {spec_path}")
        print(f"{'='*60}\n")
        
        languages = self._parse_languages(language)
        
        try:
            project = self.code_generator.generate_from_spec_file(
                spec_path, languages, output
            )
            
            print(f"\n生成完成:")
            print(f"  语言: {project.language.value}")
            print(f"  文件数: {len(project.files)}")
            for file in project.files:
                print(f"    - {file.filename} ({file.artifact_type.value})")
            
            return project
        
        except Exception as e:
            print(f"生成错误: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def doc(
        self,
        spec_path: str,
        format: str = "all",
        output: str = "docs/api",
    ):
        """生成API文档"""
        print(f"\n{'='*60}")
        print(f"生成API文档: {spec_path}")
        print(f"{'='*60}\n")
        
        formats = self._parse_doc_formats(format)
        
        try:
            results = self.doc_generator.generate_from_spec_file(
                spec_path, formats, output
            )
            
            print(f"\n生成完成:")
            for result in results:
                print(f"  - {result.filename} ({result.format.value})")
            
            return results
        
        except Exception as e:
            print(f"生成错误: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def all(
        self,
        spec_path: str,
        output_dir: str = "generated",
    ):
        """执行全部生成任务"""
        print(f"\n{'='*60}")
        print(f"执行全部生成任务: {spec_path}")
        print(f"{'='*60}\n")
        
        spec, validation_result = self.parse(spec_path, validate=True)
        if not spec:
            return
        
        base_output = Path(output_dir)
        
        print("\n[1/3] 生成测试用例...")
        self.test(spec_path, "pytest", str(base_output / "tests"))
        
        print("\n[2/3] 生成代码骨架...")
        self.code(spec_path, "python", str(base_output / "code"))
        
        print("\n[3/3] 生成API文档...")
        self.doc(spec_path, "all", str(base_output / "docs"))
        
        print(f"\n{'='*60}")
        print("全部生成任务完成!")
        print(f"{'='*60}")
    
    def _print_spec_info(self, spec: SDDSpecification):
        print("规范信息:")
        print(f"  ID: {spec.metadata.id}")
        print(f"  名称: {spec.metadata.name}")
        print(f"  版本: {spec.metadata.version}")
        print(f"  类型: {spec.kind.value}")
        print(f"  状态: {spec.metadata.status}")
        print(f"  作者: {spec.metadata.author or '未指定'}")
        print(f"  命名空间: {spec.metadata.namespace}")
        print(f"  标签: {', '.join(spec.metadata.tags) if spec.metadata.tags else '无'}")
        print()
        print("规范内容:")
        print(f"  属性数量: {len(spec.attributes)}")
        print(f"  端点数量: {len(spec.endpoints)}")
        print(f"  场景数量: {len(spec.scenarios)}")
        print(f"  约束数量: {len(spec.constraints)}")
        print(f"  关系数量: {len(spec.relationships)}")
    
    def _print_validation_result(self, result):
        print(f"\n验证结果:")
        print(f"  有效: {'✓ 是' if result.is_valid else '✗ 否'}")
        
        if result.errors:
            print(f"\n  错误 ({len(result.errors)}):")
            for err in result.errors:
                print(f"    ✗ [{err.path}] {err.message}")
                if err.suggestion:
                    print(f"      建议: {err.suggestion}")
        
        if result.warnings:
            print(f"\n  警告 ({len(result.warnings)}):")
            for warn in result.warnings:
                print(f"    ⚠ [{warn.path}] {warn.message}")
                if warn.suggestion:
                    print(f"      建议: {warn.suggestion}")
    
    def _parse_frameworks(self, framework: str) -> List[TestFramework]:
        if framework == "all":
            return [TestFramework.PYTEST, TestFramework.JEST, TestFramework.PLAYWRIGHT]
        
        framework_map = {
            "pytest": TestFramework.PYTEST,
            "jest": TestFramework.JEST,
            "playwright": TestFramework.PLAYWRIGHT,
        }
        return [framework_map.get(framework, TestFramework.PYTEST)]
    
    def _parse_languages(self, language: str) -> List[ProgrammingLanguage]:
        if language == "all":
            return [ProgrammingLanguage.PYTHON, ProgrammingLanguage.TYPESCRIPT]
        
        language_map = {
            "python": ProgrammingLanguage.PYTHON,
            "typescript": ProgrammingLanguage.TYPESCRIPT,
        }
        return [language_map.get(language, ProgrammingLanguage.PYTHON)]
    
    def _parse_doc_formats(self, format: str) -> List[DocFormat]:
        if format == "all":
            return [DocFormat.OPENAPI, DocFormat.POSTMAN, DocFormat.MARKDOWN]
        
        format_map = {
            "openapi": DocFormat.OPENAPI,
            "postman": DocFormat.POSTMAN,
            "markdown": DocFormat.MARKDOWN,
        }
        return [format_map.get(format, DocFormat.OPENAPI)]


def main():
    parser = argparse.ArgumentParser(
        description="SDD规范智能解析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 解析规范文件
  python sdd_cli.py parse specs/user_auth.md --validate
  
  # 转换规范格式
  python sdd_cli.py parse specs/user_auth.md --convert yaml --output spec.yaml
  
  # 生成pytest测试用例
  python sdd_cli.py test specs/user_auth.md --framework pytest
  
  # 生成所有框架的测试用例
  python sdd_cli.py test specs/user_auth.md --framework all
  
  # 生成Python代码骨架
  python sdd_cli.py code specs/user_auth.md --language python
  
  # 生成OpenAPI文档
  python sdd_cli.py doc specs/user_auth.md --format openapi
  
  # 执行全部生成任务
  python sdd_cli.py all specs/user_auth.md
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    parse_parser = subparsers.add_parser("parse", help="解析规范文件")
    parse_parser.add_argument("spec_file", help="规范文件路径")
    parse_parser.add_argument("--validate", action="store_true", default=True, help="验证规范")
    parse_parser.add_argument("--convert", choices=["yaml", "json", "markdown"], help="转换格式")
    parse_parser.add_argument("--output", "-o", help="输出文件路径")
    
    test_parser = subparsers.add_parser("test", help="生成测试用例")
    test_parser.add_argument("spec_file", help="规范文件路径")
    test_parser.add_argument("--framework", "-f", choices=["pytest", "jest", "playwright", "all"], default="pytest", help="测试框架")
    test_parser.add_argument("--output", "-o", default="tests/generated", help="输出目录")
    
    code_parser = subparsers.add_parser("code", help="生成代码骨架")
    code_parser.add_argument("spec_file", help="规范文件路径")
    code_parser.add_argument("--language", "-l", choices=["python", "typescript", "all"], default="python", help="编程语言")
    code_parser.add_argument("--output", "-o", default="generated", help="输出目录")
    
    doc_parser = subparsers.add_parser("doc", help="生成API文档")
    doc_parser.add_argument("spec_file", help="规范文件路径")
    doc_parser.add_argument("--format", "-f", choices=["openapi", "postman", "markdown", "all"], default="all", help="文档格式")
    doc_parser.add_argument("--output", "-o", default="docs/api", help="输出目录")
    
    all_parser = subparsers.add_parser("all", help="执行全部生成任务")
    all_parser.add_argument("spec_file", help="规范文件路径")
    all_parser.add_argument("--output", "-o", default="generated", help="输出目录")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = SDDCLI()
    
    if args.command == "parse":
        cli.parse(args.spec_file, args.validate, args.convert, args.output)
    elif args.command == "test":
        cli.test(args.spec_file, args.framework, args.output)
    elif args.command == "code":
        cli.code(args.spec_file, args.language, args.output)
    elif args.command == "doc":
        cli.doc(args.spec_file, args.format, args.output)
    elif args.command == "all":
        cli.all(args.spec_file, args.output)


if __name__ == "__main__":
    main()
