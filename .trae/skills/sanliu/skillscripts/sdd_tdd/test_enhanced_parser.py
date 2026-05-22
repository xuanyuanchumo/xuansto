#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SDD规范解析器增强功能测试脚本
测试业务规则提取、完整性验证和覆盖率报告功能
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "sdd_tdd"))

from enhanced_spec_parser import (
    EnhancedSDDSpecParser,
    BusinessRuleExtractor,
    EnhancedCompletenessValidator,
    CoverageReportGenerator,
    SpecFormat,
    SpecType
)


def create_test_spec_yaml():
    return """
apiVersion: sdd/v1
kind: EntitySpec
metadata:
  id: SPC-TEST-001
  name: 用户管理规范
  version: v1.0.0
  author: 测试用户
  status: draft
  tags:
    - user
    - management
spec:
  description: |
    用户管理模块规范定义，包含用户实体的属性定义、业务规则和约束条件。
    用户可以进行注册、登录、修改信息等操作。
    
    如果用户状态为禁用，则不允许登录系统。
    当用户连续登录失败超过5次时，自动锁定账户。
  attributes:
    - name: userId
      type: string
      description: 用户唯一标识符
      required: true
      unique: true
      constraints:
        minLength: 8
        maxLength: 32
      example: "user_12345678"
    
    - name: username
      type: string
      description: 用户名
      required: true
      unique: true
      constraints:
        minLength: 3
        maxLength: 50
        pattern: "^[a-zA-Z0-9_]+$"
    
    - name: email
      type: string
      description: 用户邮箱地址
      required: true
      unique: true
      constraints:
        pattern: '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
    
    - name: status
      type: enum
      description: 用户状态
      required: true
      enumValues:
        - active
        - inactive
        - suspended
        - deleted
      default: active
    
    - name: loginAttempts
      type: integer
      description: 登录尝试次数
      required: false
      default: 0
      constraints:
        min: 0
        max: 10
  
  businessRules:
    - id: BR-001
      name: 用户状态验证
      description: 禁用用户不允许登录
      condition: 用户状态为inactive或suspended
      action: 拒绝登录请求
      priority: 1
      enabled: true
      tags:
        - security
        - authentication
    
    - id: BR-002
      name: 登录失败锁定
      description: 连续登录失败锁定账户
      condition: loginAttempts >= 5
      action: 锁定账户并发送通知
      priority: 1
      enabled: true
      tags:
        - security
  
  constraints:
    - name: 用户名唯一性
      type: business
      description: 用户名在系统中必须唯一
      rule: username必须全局唯一
      errorMessage: 用户名已存在
    
    - name: 邮箱格式验证
      type: validation
      description: 邮箱地址必须符合标准格式
      rule: email匹配邮箱正则表达式
      errorMessage: 邮箱格式不正确
  
  endpoints:
    - name: 用户注册
      method: POST
      path: /api/users
      description: 注册新用户
      authentication: false
      rateLimit: 10
      parameters:
        - name: username
          in: body
          required: true
          type: string
        - name: email
          in: body
          required: true
          type: string
        - name: password
          in: body
          required: true
          type: string
      response:
        status: 201
        body:
          userId: string
          username: string
      errors:
        - code: 400
          message: 参数验证失败
        - code: 409
          message: 用户名或邮箱已存在
    
    - name: 用户登录
      method: POST
      path: /api/users/login
      description: 用户登录
      authentication: false
      rateLimit: 5
      parameters:
        - name: username
          in: body
          required: true
          type: string
        - name: password
          in: body
          required: true
          type: string
      response:
        status: 200
        body:
          token: string
          expiresIn: integer
      errors:
        - code: 401
          message: 用户名或密码错误
        - code: 403
          message: 账户已被锁定
  
  scenarios:
    - name: 正常用户注册
      given: 系统正常运行
      when: 用户提交有效的注册信息
      then: 用户注册成功并返回用户ID
      testData:
        username: "testuser"
        email: "test@example.com"
        password: "Test@123456"
      priority: high
    
    - name: 重复用户名注册失败
      given: 系统中已存在用户名testuser
      when: 用户使用相同用户名注册
      then: 返回409错误，提示用户名已存在
      priority: high
    
    - name: 用户登录成功
      given: 用户已注册且状态为active
      when: 用户提交正确的登录凭证
      then: 返回登录token
      priority: critical
    
    - name: 禁用用户登录失败
      given: 用户状态为suspended
      when: 用户尝试登录
      then: 返回403错误，提示账户已被锁定
      priority: high
  
  securityConstraints:
    - name: 认证安全
      type: authentication
      description: 敏感操作需要认证
      authenticationRequired: true
      authorizationRoles:
        - user
        - admin
      auditLogging: true
    
    - name: 数据加密
      type: encryption
      description: 敏感数据需要加密存储
      encryptionRequired: true
      encryptionAlgorithm: AES-256
  
  performanceConstraints:
    - name: 响应时间要求
      metric: response_time
      threshold: 500
      unit: ms
      description: API响应时间不超过500ms
      percentiles:
        - 50
        - 95
        - 99
    
    - name: 吞吐量要求
      metric: throughput
      threshold: 1000
      unit: rps
      description: 系统支持每秒1000次请求
  
  exceptionHandlers:
    - exceptionType: DatabaseConnectionError
      description: 数据库连接异常
      errorCode: DB_001
      httpStatus: 503
      message: 服务暂时不可用
      recoveryAction: 重试连接
      retryPolicy:
        maxRetries: 3
        delay: 1000
      fallbackBehavior: 返回缓存数据
    
    - exceptionType: ValidationError
      description: 数据验证异常
      errorCode: VAL_001
      httpStatus: 400
      message: 数据验证失败
      recoveryAction: 返回详细错误信息
"""


def test_business_rule_extraction():
    print("\n" + "=" * 60)
    print("测试1: 业务规则自动提取功能")
    print("=" * 60)
    
    parser = EnhancedSDDSpecParser()
    extractor = BusinessRuleExtractor()
    
    yaml_content = create_test_spec_yaml()
    
    try:
        spec, validation_result = parser.parse_content(yaml_content, SpecFormat.YAML)
        
        rules = extractor.extract_business_rules(spec)
        
        print(f"\n✅ 成功提取 {len(rules)} 条业务规则")
        
        categories = extractor.categorize_rules(rules)
        print("\n规则分类统计:")
        for category, cat_rules in categories.items():
            if cat_rules:
                print(f"  - {category}: {len(cat_rules)}条")
        
        print("\n规则详情示例:")
        for rule in rules[:5]:
            print(f"\n  [{rule.id}] {rule.name}")
            print(f"    条件: {rule.condition[:60]}..." if len(rule.condition) > 60 else f"    条件: {rule.condition}")
            print(f"    动作: {rule.action[:60]}..." if len(rule.action) > 60 else f"    动作: {rule.action}")
            print(f"    标签: {', '.join(rule.tags)}")
        
        dependencies = extractor.extract_rule_dependencies(rules)
        if dependencies:
            print(f"\n发现 {len(dependencies)} 条规则存在依赖关系")
        
        return True, rules
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, []


def test_completeness_validation():
    print("\n" + "=" * 60)
    print("测试2: 规范完整性验证功能")
    print("=" * 60)
    
    parser = EnhancedSDDSpecParser()
    validator = EnhancedCompletenessValidator()
    
    yaml_content = create_test_spec_yaml()
    
    try:
        spec, validation_result = parser.parse_content(yaml_content, SpecFormat.YAML)
        
        report = validator.validate_completeness(spec)
        
        print(f"\n✅ 完整性检查完成")
        print(f"\n完整性得分: {report.completeness_score}%")
        print(f"完整性级别: {report.level.value}")
        print(f"通过检查: {len(report.passed_checks)}")
        print(f"未通过检查: {len(report.failed_checks)}")
        print(f"质量问题: {len(report.quality_issues)}")
        
        if report.passed_checks:
            print("\n通过的检查 (前10项):")
            for check in report.passed_checks[:10]:
                print(f"  ✅ {check}")
        
        if report.failed_checks:
            print("\n未通过的检查:")
            for check in report.failed_checks[:10]:
                print(f"  ❌ {check}")
        
        if report.suggestions:
            print("\n改进建议:")
            for suggestion in report.suggestions[:5]:
                print(f"  💡 {suggestion}")
        
        print("\n详细指标:")
        metrics = report.detailed_metrics
        print(f"  属性: {metrics['attributes']['total']}个, 有描述: {metrics['attributes']['with_description']}")
        print(f"  端点: {metrics['endpoints']['total']}个, 有认证: {metrics['endpoints']['with_auth']}")
        print(f"  场景: {metrics['scenarios']['total']}个, 完整GWT: {metrics['scenarios']['complete_gwt']}")
        print(f"  业务规则: {metrics['business_rules']['total']}个")
        print(f"  安全约束: {metrics['security']['total']}个")
        print(f"  性能约束: {metrics['performance']['total']}个")
        
        return True, report
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_coverage_report():
    print("\n" + "=" * 60)
    print("测试3: 覆盖率报告生成功能")
    print("=" * 60)
    
    parser = EnhancedSDDSpecParser()
    generator = CoverageReportGenerator()
    
    yaml_content = create_test_spec_yaml()
    
    try:
        spec, validation_result = parser.parse_content(yaml_content, SpecFormat.YAML)
        
        report = generator.generate_coverage_report(spec)
        
        print(f"\n✅ 覆盖率报告生成完成")
        print(f"\n报告ID: {report.report_id}")
        print(f"总体覆盖率: {report.overall_coverage}%")
        print(f"风险等级: {report.risk_assessment.get('overall_risk_level', 'unknown')}")
        
        print("\n各类型覆盖率:")
        for type_name, mapping in report.coverage_by_type.items():
            if mapping.total_requirements > 0:
                status = "🟢" if mapping.coverage_percentage >= 80 else "🟡" if mapping.coverage_percentage >= 50 else "🔴"
                print(f"  {status} {mapping.spec_name}: {mapping.coverage_percentage}% ({mapping.covered_requirements}/{mapping.total_requirements})")
        
        if report.missing_coverage:
            print(f"\n缺失覆盖 ({len(report.missing_coverage)}项):")
            for item in report.missing_coverage[:5]:
                print(f"  - [{item['priority']}] {item['type']}: {item['item']}")
        
        if report.recommendations:
            print("\n建议:")
            for rec in report.recommendations[:5]:
                print(f"  {rec}")
        
        risk = report.risk_assessment
        print(f"\n风险评估:")
        print(f"  高风险项: {len(risk.get('high_risk', []))}")
        print(f"  中风险项: {len(risk.get('medium_risk', []))}")
        print(f"  整体风险等级: {risk.get('overall_risk_level', 'unknown')}")
        
        return True, report
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_integration():
    print("\n" + "=" * 60)
    print("测试4: 集成测试 - 完整流程")
    print("=" * 60)
    
    parser = EnhancedSDDSpecParser()
    extractor = BusinessRuleExtractor()
    validator = EnhancedCompletenessValidator()
    generator = CoverageReportGenerator()
    
    yaml_content = create_test_spec_yaml()
    
    try:
        spec, validation_result = parser.parse_content(yaml_content, SpecFormat.YAML)
        
        print(f"\n✅ 规范解析成功")
        print(f"  ID: {spec.metadata.id}")
        print(f"  名称: {spec.metadata.name}")
        print(f"  类型: {spec.kind.value}")
        
        rules = extractor.extract_business_rules(spec)
        print(f"\n✅ 业务规则提取: {len(rules)}条")
        
        completeness = validator.validate_completeness(spec)
        print(f"\n✅ 完整性验证: {completeness.completeness_score}%")
        
        coverage = generator.generate_coverage_report(spec)
        print(f"\n✅ 覆盖率报告: {coverage.overall_coverage}%")
        
        output = {
            "test_time": datetime.now().isoformat(),
            "spec": {
                "id": spec.metadata.id,
                "name": spec.metadata.name,
                "type": spec.kind.value
            },
            "business_rules": {
                "total": len(rules),
                "categories": {}
            },
            "completeness": {
                "score": completeness.completeness_score,
                "level": completeness.level.value,
                "passed": len(completeness.passed_checks),
                "failed": len(completeness.failed_checks)
            },
            "coverage": {
                "overall": coverage.overall_coverage,
                "risk_level": coverage.risk_assessment.get("overall_risk_level")
            }
        }
        
        categories = extractor.categorize_rules(rules)
        output["business_rules"]["categories"] = {k: len(v) for k, v in categories.items()}
        
        output_path = Path(__file__).parent / "test_output.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 测试结果已保存到: {output_path}")
        
        return True, output
    
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
from skillscripts.core.path_config_center import get_path_config
        traceback.print_exc()
        return False, None


def main():
    print("=" * 60)
    print("SDD规范解析器增强功能测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    success, _ = test_business_rule_extraction()
    results.append(("业务规则提取", success))
    
    success, _ = test_completeness_validation()
    results.append(("完整性验证", success))
    
    success, _ = test_coverage_report()
    results.append(("覆盖率报告", success))
    
    success, _ = test_integration()
    results.append(("集成测试", success))
    
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"  {name}: {status}")
        if not success:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败，请检查错误信息")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
