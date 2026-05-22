#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
需求业务解析集成测试
验证所有脚本的功能完整性
"""

import os
import sys
import json
import tempfile
import shutil
from datetime import datetime

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from .requirement_parser import RequirementParser, RequirementType, RequirementFormat
from .business_rule_recognizer import BusinessRuleRecognizer, RecognitionMethod
from .business_rule_extractor import BusinessRuleExtractor
from .rule_library_manager import RuleLibraryManager, RuleQuery, RuleStatus
from .rule_validator import RuleValidator
from .requirement_trace_manager import RequirementTraceManager, TraceType
from .trace_matrix_visualizer import TraceMatrixVisualizer
from .trace_report_generator import TraceReportGenerator, ReportType
from .requirement_spec_generator import SpecificationGenerator, DocumentFormat
from skillscripts.core.path_config_center import get_path_config


def test_requirement_parser():
    print("\n" + "="*60)
    print("测试 1: 需求结构化解析器")
    print("="*60)
    
    parser = RequirementParser()
    
    test_cases = [
        {
            "name": "用户故事格式",
            "content": """
作为 注册用户，我希望 能够修改我的个人信息，以便 保持我的资料最新。

Scenario: 用户修改个人信息
    Given 用户已登录系统
    When 用户点击"修改个人信息"并更新信息
    Then 系统保存更新后的信息并显示成功提示
"""
        },
        {
            "name": "Markdown格式",
            "content": """
# 用户认证功能

## 登录功能
- 用户可以使用用户名和密码登录
- 系统应验证用户凭证
- 登录失败时显示错误提示

## 注册功能
- 新用户可以注册账户
- 必须提供有效的邮箱地址
"""
        },
        {
            "name": "自然语言格式",
            "content": """
系统必须提供用户认证功能。用户可以通过用户名和密码登录系统。
如果用户输入错误的密码超过3次，系统应该锁定账户。
"""
        }
    ]
    
    results = []
    for test_case in test_cases:
        result = parser.parse(test_case['content'])
        results.append({
            "name": test_case['name'],
            "format": result.source_format.value,
            "type": result.requirement_type.value,
            "id": result.id,
            "title": result.title,
            "user_stories_count": len(result.user_stories),
            "functional_points_count": len(result.functional_points),
            "acceptance_criteria_count": len(result.acceptance_criteria)
        })
        print(f"\n  [{test_case['name']}]")
        print(f"    格式: {result.source_format.value}")
        print(f"    类型: {result.requirement_type.value}")
        print(f"    ID: {result.id}")
        print(f"    用户故事: {len(result.user_stories)}")
        print(f"    功能点: {len(result.functional_points)}")
        print(f"    验收标准: {len(result.acceptance_criteria)}")
    
    print("\n  ✓ 需求解析器测试通过")
    return results


def test_business_rule_recognizer():
    print("\n" + "="*60)
    print("测试 2: 业务规则识别器")
    print("="*60)
    
    recognizer = BusinessRuleRecognizer(min_confidence=0.4)
    
    test_text = """
    用户登录系统时，必须输入正确的用户名和密码。如果连续登录失败超过3次，则锁定账户24小时。
    只有管理员可以删除用户账户。密码必须加密存储，不能明文保存。
    订单总金额等于商品单价乘以数量。当订单状态变更为"已发货"时，发送通知邮件给用户。
    """
    
    result = recognizer.recognize(test_text)
    
    print(f"\n  识别结果:")
    print(f"    总规则数: {len(result.recognized_rules)}")
    print(f"    平均置信度: {result.total_confidence:.2f}")
    print(f"    处理时间: {result.processing_time_ms:.2f}ms")
    print(f"    发现类别: {[c.value for c in result.categories_found]}")
    
    stats = recognizer.get_rule_statistics(result)
    print(f"\n  统计信息:")
    print(f"    {json.dumps(stats, ensure_ascii=False, indent=4)}")
    
    print("\n  ✓ 业务规则识别器测试通过")
    return result


def test_business_rule_extractor():
    print("\n" + "="*60)
    print("测试 3: 业务规则提取器")
    print("="*60)
    
    extractor = BusinessRuleExtractor()
    
    test_text = """
    如果用户登录失败超过3次，则锁定账户24小时。
    用户密码长度必须大于8位。
    订单总金额等于商品单价乘以数量。
    """
    
    rules = extractor.extract_all_rules(test_text)
    
    print(f"\n  提取到 {len(rules)} 条规则:")
    for rule in rules:
        print(f"\n  [{rule.id}] {rule.name}")
        print(f"    类型: {rule.rule_type.value}")
        print(f"    描述: {rule.description}")
        
        if rule.conditions:
            print(f"    条件: {[c.to_expression() for c in rule.conditions]}")
        if rule.actions:
            print(f"    动作: {[(a.action_type, a.target) for a in rule.actions]}")
        if rule.validation_rules:
            print(f"    验证: {[(v.field, v.validation_type) for v in rule.validation_rules]}")
        if rule.calculation_rules:
            print(f"    计算: {[(c.result_field, c.formula) for c in rule.calculation_rules]}")
    
    print("\n  ✓ 业务规则提取器测试通过")
    return rules


def test_rule_library_manager():
    print("\n" + "="*60)
    print("测试 4: 规则库管理器")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "test_rule_library.db")
    
    try:
        manager = RuleLibraryManager(temp_db)
        
        rule1 = manager.store_rule(
            name="用户登录验证规则",
            category="security",
            rule_type="validation",
            description="用户登录时的密码验证规则",
            content={
                "min_length": 8,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_number": True
            },
            tags=["登录", "密码", "安全"],
            created_by="test_user"
        )
        print(f"\n  创建规则: {rule1.id}")
        
        rule2 = manager.store_rule(
            name="订单金额计算规则",
            category="calculation",
            rule_type="formula",
            description="订单总金额的计算公式",
            content={
                "formula": "total = price * quantity - discount",
                "dependencies": ["price", "quantity", "discount"]
            },
            tags=["订单", "计算", "金额"],
            created_by="test_user"
        )
        print(f"  创建规则: {rule2.id}")
        
        updated_rule = manager.update_rule(
            rule1.id,
            content={
                "min_length": 10,
                "require_uppercase": True,
                "require_lowercase": True,
                "require_number": True,
                "require_special": True
            },
            changed_by="test_user",
            change_description="增加密码复杂度要求"
        )
        print(f"  更新规则: {updated_rule.id}, 新版本: {updated_rule.current_version}")
        
        print("\n  查询安全类规则:")
        security_rules = manager.query_rules(RuleQuery(category="security"))
        for r in security_rules:
            print(f"    - {r.id}: {r.name}")
        
        print("\n  规则版本历史:")
        versions = manager.get_rule_versions(rule1.id)
        for v in versions:
            print(f"    - 版本 {v.version}: {v.change_type.value} - {v.change_description}")
        
        stats = manager.get_statistics()
        print(f"\n  统计信息:")
        print(f"    {json.dumps(stats, ensure_ascii=False, indent=4)}")
        
        print("\n  ✓ 规则库管理器测试通过")
        return True
    finally:
        if os.path.exists(temp_db):
            try:
                os.remove(temp_db)
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass


def test_rule_validator():
    print("\n" + "="*60)
    print("测试 5: 规则验证器")
    print("="*60)
    
    validator = RuleValidator()
    
    test_rules = [
        {
            "id": "RULE-001",
            "name": "密码长度验证",
            "description": "用户密码长度必须在8-20位之间",
            "source_text": "用户密码长度必须在8-20位之间",
            "content": {
                "validation_rules": [
                    {"field": "password", "validation_type": "min_length", "parameters": {"min_length": 8}},
                    {"field": "password", "validation_type": "max_length", "parameters": {"max_length": 20}}
                ]
            }
        },
        {
            "id": "RULE-002",
            "name": "密码长度验证（冲突）",
            "description": "用户密码长度必须大于10位",
            "source_text": "用户密码长度必须大于10位",
            "content": {
                "validation_rules": [
                    {"field": "password", "validation_type": "min_length", "parameters": {"min_length": 10}}
                ]
            }
        },
        {
            "id": "RULE-003",
            "name": "订单金额计算",
            "description": "订单总金额等于单价乘以数量",
            "source_text": "订单总金额等于单价乘以数量",
            "content": {
                "calculation_rules": [
                    {"result_field": "total_amount", "formula": "price * quantity", "dependencies": ["price", "quantity"]}
                ]
            }
        }
    ]
    
    result = validator.validate_rules(test_rules)
    
    print(f"\n  验证结果: {'通过' if result.is_valid else '存在问题'}")
    print(f"  检查规则数: {result.checked_rules_count}")
    print(f"  发现问题: {len(result.issues)}")
    print(f"  检测冲突: {len(result.conflicts)}")
    
    if result.issues:
        print("\n  问题详情:")
        for issue in result.issues[:5]:
            print(f"    [{issue.severity.value}] {issue.issue_type}: {issue.description}")
    
    if result.conflicts:
        print("\n  冲突详情:")
        for conflict in result.conflicts[:5]:
            print(f"    [{conflict.conflict_type.value}] {conflict.description}")
    
    print("\n  ✓ 规则验证器测试通过")
    return result


def test_requirement_trace_manager():
    print("\n" + "="*60)
    print("测试 6: 需求追溯管理器")
    print("="*60)
    
    temp_dir = tempfile.mkdtemp()
    temp_db = os.path.join(temp_dir, "test_requirement_trace.db")
    
    try:
        manager = RequirementTraceManager(temp_db)
        
        req1 = manager.add_requirement(
            name="用户登录功能",
            requirement_type="functional",
            description="用户可以通过用户名和密码登录系统"
        )
        print(f"\n  创建需求: {req1.id} - {req1.name}")
        
        req2 = manager.add_requirement(
            name="密码重置功能",
            requirement_type="functional",
            description="用户可以重置忘记的密码"
        )
        print(f"  创建需求: {req2.id} - {req2.name}")
        
        test1 = manager.add_test_case(
            name="用户登录测试",
            test_type="acceptance",
            scenario="成功登录",
            given="用户已注册且账户正常",
            when="输入正确的用户名和密码",
            then="成功登录并跳转到首页"
        )
        print(f"\n  创建测试用例: {test1.id} - {test1.name}")
        
        link1 = manager.create_trace_link(
            source_type="requirement",
            source_id=req1.id,
            source_name=req1.name,
            target_type="test_case",
            target_id=test1.id,
            target_name=test1.name,
            trace_type=TraceType.REQUIREMENT_TO_TEST
        )
        print(f"\n  创建追溯链接: {link1.id}")
        
        coverage = manager.calculate_coverage()
        print(f"\n  覆盖率统计:")
        print(f"    {json.dumps(coverage, ensure_ascii=False, indent=4)}")
        
        matrix = manager.get_trace_matrix()
        print(f"\n  追溯矩阵:")
        print(f"    需求数: {len(matrix.requirements)}")
        print(f"    测试用例数: {len(matrix.test_cases)}")
        print(f"    追溯链接数: {len(matrix.trace_links)}")
        
        print("\n  ✓ 需求追溯管理器测试通过")
        return True
    finally:
        if os.path.exists(temp_db):
            try:
                os.remove(temp_db)
            except:
                pass
        try:
            os.rmdir(temp_dir)
        except:
            pass


def test_trace_matrix_visualizer():
    print("\n" + "="*60)
    print("测试 7: 追溯矩阵可视化器")
    print("="*60)
    
    visualizer = TraceMatrixVisualizer()
    
    test_matrix_data = {
        "requirements": [
            {"id": "REQ-001", "name": "用户登录功能", "status": "active", "requirement_type": "functional"},
            {"id": "REQ-002", "name": "密码重置功能", "status": "active", "requirement_type": "functional"},
            {"id": "REQ-003", "name": "用户注册功能", "status": "active", "requirement_type": "functional"}
        ],
        "test_cases": [
            {"id": "TC-001", "name": "登录成功测试", "status": "passed", "execution_result": "passed"},
            {"id": "TC-002", "name": "登录失败测试", "status": "passed", "execution_result": "passed"},
            {"id": "TC-003", "name": "密码重置测试", "status": "pending", "execution_result": None}
        ],
        "trace_links": [
            {"source_id": "REQ-001", "target_id": "TC-001", "trace_type": "requirement_to_test", "status": "covered"},
            {"source_id": "REQ-001", "target_id": "TC-002", "trace_type": "requirement_to_test", "status": "covered"},
            {"source_id": "REQ-002", "target_id": "TC-003", "trace_type": "requirement_to_test", "status": "pending"}
        ],
        "coverage_stats": {
            "total_requirements": 3,
            "covered_requirements": 2,
            "verified_requirements": 1,
            "coverage_rate": 66.67
        }
    }
    
    visualization = visualizer.generate_visualization(test_matrix_data)
    
    print(f"\n  生成可视化数据:")
    print(f"    节点数: {visualization.statistics['total_nodes']}")
    print(f"    边数: {visualization.statistics['total_edges']}")
    print(f"    节点类型: {visualization.statistics['node_types']}")
    
    html_output = visualizer.to_html(visualization)
    print(f"\n  生成HTML文档长度: {len(html_output)} 字符")
    
    print("\n  ✓ 追溯矩阵可视化器测试通过")
    return visualization


def test_trace_report_generator():
    print("\n" + "="*60)
    print("测试 8: 追溯报告生成器")
    print("="*60)
    
    generator = TraceReportGenerator()
    
    test_matrix_data = {
        "requirements": [
            {"id": "REQ-001", "name": "用户登录功能", "requirement_type": "functional", "priority": "high", "status": "active"},
            {"id": "REQ-002", "name": "密码重置功能", "requirement_type": "functional", "priority": "high", "status": "active"},
            {"id": "REQ-003", "name": "用户注册功能", "requirement_type": "functional", "priority": "medium", "status": "active"},
            {"id": "REQ-004", "name": "性能要求", "requirement_type": "non_functional", "priority": "medium", "status": "active"},
            {"id": "REQ-005", "name": "安全要求", "requirement_type": "non_functional", "priority": "high", "status": "active"}
        ],
        "test_cases": [
            {"id": "TC-001", "name": "登录成功测试", "test_type": "acceptance", "status": "passed", "execution_result": "passed"},
            {"id": "TC-002", "name": "登录失败测试", "test_type": "acceptance", "status": "passed", "execution_result": "passed"},
            {"id": "TC-003", "name": "密码重置测试", "test_type": "acceptance", "status": "pending", "execution_result": None},
            {"id": "TC-004", "name": "性能测试", "test_type": "performance", "status": "passed", "execution_result": "passed"}
        ],
        "trace_links": [
            {"source_id": "REQ-001", "target_id": "TC-001", "trace_type": "requirement_to_test", "status": "verified", "source_name": "用户登录功能", "target_name": "登录成功测试"},
            {"source_id": "REQ-001", "target_id": "TC-002", "trace_type": "requirement_to_test", "status": "verified", "source_name": "用户登录功能", "target_name": "登录失败测试"},
            {"source_id": "REQ-002", "target_id": "TC-003", "trace_type": "requirement_to_test", "status": "pending", "source_name": "密码重置功能", "target_name": "密码重置测试"},
            {"source_id": "REQ-004", "target_id": "TC-004", "trace_type": "requirement_to_test", "status": "verified", "source_name": "性能要求", "target_name": "性能测试"}
        ]
    }
    
    summary_report = generator.generate_summary_report(test_matrix_data, "用户管理系统")
    
    print(f"\n  摘要报告:")
    print(f"    报告ID: {summary_report.report_id}")
    print(f"    项目: {summary_report.project_name}")
    print(f"    覆盖率: {summary_report.statistics.coverage_rate}%")
    print(f"    验证率: {summary_report.statistics.verification_rate}%")
    print(f"    缺口数: {len(summary_report.gaps)}")
    print(f"    建议数: {len(summary_report.recommendations)}")
    
    gap_report = generator.generate_gap_analysis_report(test_matrix_data, "用户管理系统")
    print(f"\n  缺口分析报告:")
    print(f"    发现缺口: {len(gap_report.gaps)}")
    for gap in gap_report.gaps[:3]:
        print(f"      - {gap.requirement_name}: {gap.description}")
    
    print("\n  ✓ 追溯报告生成器测试通过")
    return summary_report


def test_specification_generator():
    print("\n" + "="*60)
    print("测试 9: 需求规格文档生成器")
    print("="*60)
    
    parser = RequirementParser()
    extractor = BusinessRuleExtractor()
    generator = SpecificationGenerator(
        project_name="用户管理系统",
        author="需求分析团队"
    )
    
    test_requirement = """
作为 注册用户，我希望 能够修改我的个人信息，以便 保持我的资料最新。

Scenario: 用户修改个人信息
    Given 用户已登录系统
    When 用户点击"修改个人信息"并更新信息
    Then 系统保存更新后的信息并显示成功提示

## 密码管理功能
- 用户可以修改密码
- 密码长度必须大于8位
- 新密码不能与最近5次使用的密码相同

如果用户连续登录失败超过3次，则锁定账户24小时。
"""
    
    parsed_req = parser.parse(test_requirement)
    generator.add_requirement(parsed_req)
    
    rules = extractor.extract_all_rules(test_requirement)
    for rule in rules:
        generator.add_business_rule(rule)
    
    generator.add_glossary_term("用户", "使用系统的注册人员")
    generator.add_glossary_term("认证", "验证用户身份的过程")
    
    generator.add_assumption("用户具备基本的计算机操作能力")
    generator.add_assumption("网络环境稳定可靠")
    
    generator.add_constraint("系统需在3秒内响应用户请求")
    generator.add_constraint("支持至少1000并发用户")
    
    md_content = generator.generate_markdown()
    print(f"\n  生成Markdown文档长度: {len(md_content)} 字符")
    
    json_content = generator.generate_json()
    print(f"  生成JSON文档长度: {len(json_content)} 字符")
    
    print(f"\n  需求数: {len(generator.requirements)}")
    print(f"  业务规则数: {len(generator.business_rules)}")
    print(f"  术语数: {len(generator.glossary)}")
    print(f"  假设数: {len(generator.assumptions)}")
    print(f"  约束数: {len(generator.constraints)}")
    
    print("\n  ✓ 需求规格文档生成器测试通过")
    return True


def run_all_tests():
    print("\n" + "="*60)
    print("需求业务解析集成测试")
    print(f"测试时间: {datetime.now().isoformat()}")
    print("="*60)
    
    results = {}
    
    try:
        results['requirement_parser'] = test_requirement_parser()
    except Exception as e:
        print(f"\n  ✗ 需求解析器测试失败: {e}")
        results['requirement_parser'] = None
    
    try:
        results['business_rule_recognizer'] = test_business_rule_recognizer()
    except Exception as e:
        print(f"\n  ✗ 业务规则识别器测试失败: {e}")
        results['business_rule_recognizer'] = None
    
    try:
        results['business_rule_extractor'] = test_business_rule_extractor()
    except Exception as e:
        print(f"\n  ✗ 业务规则提取器测试失败: {e}")
        results['business_rule_extractor'] = None
    
    try:
        results['rule_library_manager'] = test_rule_library_manager()
    except Exception as e:
        print(f"\n  ✗ 规则库管理器测试失败: {e}")
        results['rule_library_manager'] = None
    
    try:
        results['rule_validator'] = test_rule_validator()
    except Exception as e:
        print(f"\n  ✗ 规则验证器测试失败: {e}")
        results['rule_validator'] = None
    
    try:
        results['requirement_trace_manager'] = test_requirement_trace_manager()
    except Exception as e:
        print(f"\n  ✗ 需求追溯管理器测试失败: {e}")
        results['requirement_trace_manager'] = None
    
    try:
        results['trace_matrix_visualizer'] = test_trace_matrix_visualizer()
    except Exception as e:
        print(f"\n  ✗ 追溯矩阵可视化器测试失败: {e}")
        results['trace_matrix_visualizer'] = None
    
    try:
        results['trace_report_generator'] = test_trace_report_generator()
    except Exception as e:
        print(f"\n  ✗ 追溯报告生成器测试失败: {e}")
        results['trace_report_generator'] = None
    
    try:
        results['specification_generator'] = test_specification_generator()
    except Exception as e:
        print(f"\n  ✗ 需求规格文档生成器测试失败: {e}")
        results['specification_generator'] = None
    
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is not None)
    total = len(results)
    
    print(f"\n  通过: {passed}/{total}")
    print(f"  失败: {total - passed}/{total}")
    
    for name, result in results.items():
        status = "✓ 通过" if result is not None else "✗ 失败"
        print(f"    - {name}: {status}")
    
    print("\n" + "="*60)
    print("所有测试完成")
    print("="*60)
    
    return results


if __name__ == "__main__":
    run_all_tests()
