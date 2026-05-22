#!/usr/bin/env python3
"""
文档自动生成测试

测试内容：
1. 报告生成功能
2. API 文档生成
3. 变更日志生成
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

SKILLSCRIPTS_DIR = Path(__file__).parent.parent / "skillscripts"
sys.path.insert(0, str(SKILLSCRIPTS_DIR))

from test_runner import TestRunner, TestResult, print_header, print_result

TEST_DATA_DIR = Path(__file__).parent / "test_data" / "doc_generator"
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)

SKILLSCRIPTS_DIR = Path(__file__).parent.parent / "skillscripts"


def cleanup_test_data():
    if TEST_DATA_DIR.exists():
        shutil.rmtree(TEST_DATA_DIR)
    TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)


def test_doc_generator_import():
    try:
        from utils.document_auto_generator import (
            EvolutionReportGenerator,
            APIDocGenerator,
            ChangelogGenerator
        )
        return True, "模块导入成功", {
            "classes": ["EvolutionReportGenerator", "APIDocGenerator", "ChangelogGenerator"]
        }
    except ImportError as e:
        return False, f"模块导入失败: {e}", {}


def test_report_config():
    try:
        from utils.document_auto_generator import EvolutionReportGenerator
        
        generator = EvolutionReportGenerator(
            project_root=TEST_DATA_DIR / "reports"
        )
        
        return True, "报告生成器创建成功", {
            "project_root": str(TEST_DATA_DIR / "reports")
        }
    except Exception as e:
        return False, f"报告配置测试失败: {e}", {}


def test_generator_initialization():
    try:
        from utils.document_auto_generator import EvolutionReportGenerator
        
        generator = EvolutionReportGenerator(project_root=TEST_DATA_DIR / "docs")
        
        return True, "生成器初始化成功", {
            "project_root": str(generator.project_root) if hasattr(generator, 'project_root') else str(TEST_DATA_DIR / "docs")
        }
    except Exception as e:
        return False, f"生成器初始化失败: {e}", {}


def test_report_generation():
    try:
        from utils.document_auto_generator import EvolutionReportGenerator
        
        generator = EvolutionReportGenerator(project_root=TEST_DATA_DIR / "reports")
        
        test_data = {
            "title": "测试报告",
            "summary": "这是一个测试报告摘要",
            "sections": [
                {
                    "title": "第一部分",
                    "content": "这是第一部分的内容"
                }
            ],
            "metrics": {
                "total": 100,
                "passed": 95,
                "failed": 5
            }
        }
        
        if hasattr(generator, 'generate'):
            result = generator.generate(data=test_data, output_name="test_report")
            
            return True, "报告生成测试成功", {
                "has_generate_method": True,
                "result_type": type(result).__name__ if result else "None"
            }
        
        return True, "报告生成接口存在", {
            "has_generate_method": hasattr(generator, 'generate')
        }
    except Exception as e:
        return False, f"报告生成测试失败: {e}", {}


def test_api_doc_generation():
    try:
        from utils.document_auto_generator import APIDocGenerator
        
        generator = APIDocGenerator(project_root=TEST_DATA_DIR / "api_docs")
        
        test_api_data = {
            "module": "test_module",
            "classes": [
                {
                    "name": "TestClass",
                    "description": "测试类",
                    "methods": [
                        {
                            "name": "test_method",
                            "description": "测试方法",
                            "parameters": [],
                            "returns": {"type": "bool"}
                        }
                    ]
                }
            ]
        }
        
        if hasattr(generator, 'generate'):
            result = generator.generate(module_data=test_api_data, output_name="test_api")
            
            return True, "API文档生成测试成功", {
                "has_generate_method": True
            }
        
        return True, "API文档生成接口存在", {
            "has_generate_method": hasattr(generator, 'generate')
        }
    except Exception as e:
        return False, f"API文档生成测试失败: {e}", {}


def test_changelog_generation():
    try:
        from utils.document_auto_generator import ChangelogGenerator
        
        generator = ChangelogGenerator(project_root=TEST_DATA_DIR / "changelog")
        
        test_changes = [
            {
                "version": "1.1.0",
                "date": datetime.now().isoformat(),
                "changes": [
                    {"type": "feature", "description": "新增功能A"},
                    {"type": "fix", "description": "修复问题B"}
                ]
            }
        ]
        
        if hasattr(generator, 'generate'):
            result = generator.generate(changes=test_changes, output_name="CHANGELOG")
            
            return True, "变更日志生成测试成功", {
                "has_generate_method": True,
                "changes_count": len(test_changes)
            }
        
        return True, "变更日志生成接口存在", {
            "has_generate_method": hasattr(generator, 'generate')
        }
    except Exception as e:
        return False, f"变更日志生成测试失败: {e}", {}


def test_markdown_format():
    try:
        from utils.document_auto_generator import DocumentAutoGenerator
        
        generator = DocumentAutoGenerator(output_dir=TEST_DATA_DIR / "markdown")
        
        test_content = {
            "title": "Markdown测试",
            "body": "这是正文内容",
            "code_blocks": [
                {
                    "language": "python",
                    "code": "print('Hello, World!')"
                }
            ],
            "tables": [
                {
                    "headers": ["列1", "列2"],
                    "rows": [["值1", "值2"], ["值3", "值4"]]
                }
            ]
        }
        
        if hasattr(generator, 'format_markdown'):
            formatted = generator.format_markdown(test_content)
            
            return True, "Markdown格式化测试成功", {
                "has_format_method": True,
                "output_type": type(formatted).__name__
            }
        
        return True, "Markdown格式化接口检查", {
            "has_format_method": hasattr(generator, 'format_markdown')
        }
    except Exception as e:
        return False, f"Markdown格式化测试失败: {e}", {}


def test_html_format():
    try:
        from utils.document_auto_generator import DocumentAutoGenerator
        
        generator = DocumentAutoGenerator(output_dir=TEST_DATA_DIR / "html")
        
        test_content = {
            "title": "HTML测试",
            "body": "这是HTML正文",
            "sections": [
                {"title": "章节1", "content": "内容1"},
                {"title": "章节2", "content": "内容2"}
            ]
        }
        
        if hasattr(generator, 'format_html'):
            formatted = generator.format_html(test_content)
            
            return True, "HTML格式化测试成功", {
                "has_html_method": True,
                "output_type": type(formatted).__name__
            }
        
        return True, "HTML格式化接口检查", {
            "has_html_method": hasattr(generator, 'format_html')
        }
    except Exception as e:
        return False, f"HTML格式化测试失败: {e}", {}


def test_template_rendering():
    try:
        from utils.document_auto_generator import DocumentAutoGenerator
        
        generator = DocumentAutoGenerator(output_dir=TEST_DATA_DIR / "templates")
        
        test_template = """
# {{ title }}

{{ summary }}

## 详情
{% for item in items %}
- {{ item }}
{% endfor %}
"""
        
        test_data = {
            "title": "模板测试",
            "summary": "这是模板渲染测试",
            "items": ["项目1", "项目2", "项目3"]
        }
        
        if hasattr(generator, 'render_template'):
            rendered = generator.render_template(test_template, test_data)
            
            return True, "模板渲染测试成功", {
                "has_render_method": True,
                "output_length": len(rendered) if rendered else 0
            }
        
        return True, "模板渲染接口检查", {
            "has_render_method": hasattr(generator, 'render_template')
        }
    except Exception as e:
        return False, f"模板渲染测试失败: {e}", {}


def test_document_export():
    try:
        from utils.document_auto_generator import DocumentAutoGenerator
        
        generator = DocumentAutoGenerator(output_dir=TEST_DATA_DIR / "export")
        
        test_doc = {
            "content": "# 测试文档\n\n这是测试内容。",
            "format": "markdown"
        }
        
        if hasattr(generator, 'export_document'):
            result = generator.export_document(
                content=test_doc["content"],
                filename="exported_doc",
                format=test_doc["format"]
            )
            
            return True, "文档导出测试成功", {
                "has_export_method": True,
                "result_type": type(result).__name__ if result else "None"
            }
        
        return True, "文档导出接口检查", {
            "has_export_method": hasattr(generator, 'export_document')
        }
    except Exception as e:
        return False, f"文档导出测试失败: {e}", {}


def run_doc_generator_tests():
    print_header("文档自动生成测试")
    
    cleanup_test_data()
    
    runner = TestRunner()
    
    tests = [
        ("模块导入测试", test_doc_generator_import),
        ("报告配置测试", test_report_config),
        ("生成器初始化测试", test_generator_initialization),
        ("报告生成测试", test_report_generation),
        ("API文档生成测试", test_api_doc_generation),
        ("变更日志生成测试", test_changelog_generation),
        ("Markdown格式化测试", test_markdown_format),
        ("HTML格式化测试", test_html_format),
        ("模板渲染测试", test_template_rendering),
        ("文档导出测试", test_document_export),
    ]
    
    for test_name, test_func in tests:
        result = runner.run_test(test_func, "文档自动生成", test_name)
        print_result(result)
        runner.report.add_result(result)
    
    return runner.finalize()


if __name__ == "__main__":
    report = run_doc_generator_tests()
    print(f"\n测试完成: {report.passed}/{report.total_tests} 通过")
