"""
SDD规范解析器测试文件
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR))

from sdd_spec_parser import (
    GherkinParser,
    OpenAPIParser,
    SpecFormat,
    SDDSpecParserFactory,
)
from sdd_parser import SDDParser


def test_gherkin_parser():
    """测试Gherkin解析器"""
    print("\n=== 测试Gherkin解析器 ===")
    
    gherkin_content = """
@authentication @critical
Feature: 用户登录功能
    
    作为一个用户
    我想要登录系统
    以便访问我的账户
    
    Background:
        Given 系统已启动
        And 数据库已连接
    
    @smoke
    Scenario: 成功登录
        Given 用户在登录页面
        When 用户输入用户名 "testuser"
        And 用户输入密码 "password123"
        And 用户点击登录按钮
        Then 用户应该看到欢迎页面
        And 用户应该看到 "欢迎, testuser"
    
    @validation
    Scenario: 登录失败 - 错误密码
        Given 用户在登录页面
        When 用户输入用户名 "testuser"
        And 用户输入错误密码 "wrongpassword"
        And 用户点击登录按钮
        Then 用户应该看到错误消息 "用户名或密码错误"
    
    Scenario Outline: 多用户登录测试
        Given 用户在登录页面
        When 用户输入用户名 "<username>"
        And 用户输入密码 "<password>"
        And 用户点击登录按钮
        Then 用户应该看到 "<result>"
    
        Examples:
            | username | password     | result          |
            | user1    | pass1        | 欢迎, user1     |
            | user2    | pass2        | 欢迎, user2     |
            | admin    | admin123     | 欢迎, admin     |
"""
    
    parser = GherkinParser()
    feature = parser.parse(gherkin_content)
    
    print(f"Feature名称: {feature.name}")
    print(f"Feature描述: {feature.description.strip()}")
    print(f"Feature标签: {feature.tags}")
    print(f"场景数量: {len(feature.scenarios)}")
    
    for idx, scenario in enumerate(feature.scenarios, 1):
        print(f"\n场景 {idx}: {scenario.name}")
        print(f"  标签: {scenario.tags}")
        print(f"  步骤数: {len(scenario.steps)}")
        if scenario.examples:
            print(f"  示例数: {len(scenario.examples)}")
    
    validation_result = parser.validate(feature)
    print(f"\n验证结果:")
    print(f"  是否有效: {validation_result.is_valid}")
    print(f"  完整性分数: {validation_result.completeness_score:.1f}/100")
    print(f"  错误数: {len(validation_result.errors)}")
    print(f"  警告数: {len(validation_result.warnings)}")
    
    if validation_result.errors:
        print(f"  错误:")
        for error in validation_result.errors:
            print(f"    - {error}")
    
    if validation_result.warnings:
        print(f"  警告:")
        for warning in validation_result.warnings:
            print(f"    - {warning}")
    
    test_cases = parser.to_test_cases(feature)
    print(f"\n生成的测试用例数: {len(test_cases)}")
    for tc in test_cases[:2]:
        print(f"  - {tc.name}: {tc.description}")
    
    code_skeletons = parser.to_code_skeleton(feature, language="python")
    print(f"\n生成的代码骨架数: {len(code_skeletons)}")
    if code_skeletons:
        print(f"  文件名: {code_skeletons[0].file_name}")
        print(f"  语言: {code_skeletons[0].language}")


def test_openapi_parser():
    """测试OpenAPI解析器"""
    print("\n=== 测试OpenAPI解析器 ===")
    
    openapi_content = """
{
    "openapi": "3.0.0",
    "info": {
        "title": "用户管理API",
        "version": "1.0.0",
        "description": "用户管理系统的RESTful API"
    },
    "servers": [
        {
            "url": "https://api.example.com/v1"
        }
    ],
    "paths": {
        "/users": {
            "get": {
                "summary": "获取用户列表",
                "description": "获取所有用户的列表",
                "tags": ["users"],
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {
                            "type": "integer"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "成功返回用户列表"
                    },
                    "401": {
                        "description": "未授权"
                    }
                }
            },
            "post": {
                "summary": "创建新用户",
                "description": "创建一个新的用户账户",
                "tags": ["users"],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "username": {"type": "string"},
                                    "email": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "用户创建成功"
                    },
                    "400": {
                        "description": "请求参数错误"
                    }
                }
            }
        },
        "/users/{id}": {
            "get": {
                "summary": "获取用户详情",
                "tags": ["users"],
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "integer"
                        }
                    }
                ],
                "responses": {
                    "200": {
                        "description": "成功返回用户详情"
                    },
                    "404": {
                        "description": "用户不存在"
                    }
                }
            },
            "delete": {
                "summary": "删除用户",
                "tags": ["users"],
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": true,
                        "schema": {
                            "type": "integer"
                        }
                    }
                ],
                "responses": {
                    "204": {
                        "description": "用户删除成功"
                    },
                    "404": {
                        "description": "用户不存在"
                    }
                }
            }
        }
    }
}
"""
    
    parser = OpenAPIParser()
    api_spec = parser.parse(openapi_content)
    
    print(f"API标题: {api_spec.title}")
    print(f"API版本: {api_spec.version}")
    print(f"API描述: {api_spec.description}")
    print(f"基础URL: {api_spec.base_url}")
    print(f"端点数量: {len(api_spec.endpoints)}")
    
    for endpoint in api_spec.endpoints:
        print(f"\n端点: {endpoint.method} {endpoint.path}")
        print(f"  摘要: {endpoint.summary}")
        print(f"  标签: {endpoint.tags}")
        print(f"  参数数: {len(endpoint.parameters)}")
        print(f"  响应数: {len(endpoint.responses)}")
    
    validation_result = parser.validate(api_spec)
    print(f"\n验证结果:")
    print(f"  是否有效: {validation_result.is_valid}")
    print(f"  完整性分数: {validation_result.completeness_score:.1f}/100")
    print(f"  错误数: {len(validation_result.errors)}")
    print(f"  警告数: {len(validation_result.warnings)}")
    
    if validation_result.warnings:
        print(f"  警告:")
        for warning in validation_result.warnings:
            print(f"    - {warning}")
    
    test_cases = parser.to_test_cases(api_spec)
    print(f"\n生成的测试用例数: {len(test_cases)}")
    for tc in test_cases[:3]:
        print(f"  - {tc.name}: {tc.description}")
    
    code_skeletons = parser.to_code_skeleton(api_spec, language="python")
    print(f"\n生成的代码骨架数: {len(code_skeletons)}")
    if code_skeletons:
        print(f"  文件名: {code_skeletons[0].file_name}")
        print(f"  语言: {code_skeletons[0].language}")


def test_sdd_parser_integration():
    """测试SDD解析器集成功能"""
    print("\n=== 测试SDD解析器集成功能 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        feature_file = temp_path / "test.feature"
        feature_file.write_text("""
Feature: 购物车功能
    
    Scenario: 添加商品到购物车
        Given 用户已登录
        When 用户选择商品 "iPhone 15"
        And 用户点击添加到购物车
        Then 购物车中应该有1件商品
""", encoding='utf-8')
        
        openapi_file = temp_path / "api.json"
        openapi_file.write_text(json.dumps({
            "openapi": "3.0.0",
            "info": {
                "title": "产品API",
                "version": "1.0.0"
            },
            "paths": {
                "/products": {
                    "get": {
                        "summary": "获取产品列表",
                        "responses": {
                            "200": {"description": "成功"}
                        }
                    }
                }
            }
        }), encoding='utf-8')
        
        parser = SDDParser(language="python")
        
        print("\n解析Feature文件:")
        result1 = parser.parse_and_analyze(str(feature_file))
        print(f"  规范名称: {result1.spec.name}")
        print(f"  格式: {result1.format_type.value}")
        print(f"  验证通过: {result1.validation_result.is_valid}")
        print(f"  测试用例数: {len(result1.test_cases)}")
        
        print("\n解析OpenAPI文件:")
        result2 = parser.parse_and_analyze(str(openapi_file))
        print(f"  规范名称: {result2.spec.title}")
        print(f"  格式: {result2.format_type.value}")
        print(f"  验证通过: {result2.validation_result.is_valid}")
        print(f"  测试用例数: {len(result2.test_cases)}")
        
        print("\n生成报告:")
        report = parser.generate_report(result1)
        print(f"  规范名称: {report.spec_name}")
        print(f"  完整性分数: {report.completeness_score:.1f}/100")
        print(f"  摘要:\n{report.summary}")
        
        output_dir = temp_path / "output"
        output_dir.mkdir()
        
        print("\n导出测试用例:")
        exported_tests = parser.export_test_cases(str(output_dir), result1)
        print(f"  导出文件数: {len(exported_tests)}")
        if exported_tests:
            print(f"  示例文件: {Path(exported_tests[0]).name}")
        
        print("\n导出代码骨架:")
        exported_code = parser.export_code_skeletons(str(output_dir), result1)
        print(f"  导出文件数: {len(exported_code)}")
        if exported_code:
            print(f"  示例文件: {Path(exported_code[0]).name}")


def test_format_detection():
    """测试格式检测"""
    print("\n=== 测试格式检测 ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        feature_file = temp_path / "example.feature"
        feature_file.write_text("Feature: Test", encoding='utf-8')
        
        yaml_file = temp_path / "api.yaml"
        yaml_file.write_text("openapi: 3.0.0", encoding='utf-8')
        
        json_file = temp_path / "api.json"
        json_file.write_text('{"openapi": "3.0.0"}', encoding='utf-8')
        
        txt_file = temp_path / "readme.txt"
        txt_file.write_text("This is a readme", encoding='utf-8')
        
        print(f"Feature文件格式: {SDDSpecParserFactory.detect_format(str(feature_file)).value}")
        print(f"YAML文件格式: {SDDSpecParserFactory.detect_format(str(yaml_file)).value}")
        print(f"JSON文件格式: {SDDSpecParserFactory.detect_format(str(json_file)).value}")
        print(f"TXT文件格式: {SDDSpecParserFactory.detect_format(str(txt_file)).value}")


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("开始运行SDD规范解析器测试")
    print("=" * 60)
    
    try:
        test_gherkin_parser()
        print("\n" + "=" * 60)
        
        test_openapi_parser()
        print("\n" + "=" * 60)
        
        test_sdd_parser_integration()
        print("\n" + "=" * 60)
        
        test_format_detection()
        print("\n" + "=" * 60)
        
        print("\n✅ 所有测试通过!")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
from skillscripts.core.path_config_center import get_path_config
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
