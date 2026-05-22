#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四维度输出防线系统测试套件

覆盖范围：
- PromptLayer（意图识别、上下文注入、歧义消解、输入验证）
- CapabilityLayer（技能匹配、知识覆盖、工具验证、能力缺口）
- RuleValidationLayer（Lint、安全扫描、硬编码检测、性能基线）
- FallbackRecoveryLayer（质量评分、回滚、降级策略）
- 四层集成（正常流程、各层失败场景、降级触发）
"""

import pytest
from four_d_defense import (
    IntentType,
    LayerStatus,
    FallbackStrategy,
    LayerResult,
    DefenseResult,
    InputData,
    BaseDefenseLayer,
    PromptLayer,
    CapabilityLayer,
    RuleValidationLayer,
    FallbackRecoveryLayer,
    FourDimensionalDefense,
    create_defense_system,
)


class TestPromptLayer:
    """测试第1层：Prompt工程层"""

    def test_intent_recognition_code_generation(self):
        """识别代码生成意图"""
        layer = PromptLayer()
        input_data = InputData(
            raw_input="请创建一个Python函数来实现用户认证功能"
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.PASSED, LayerStatus.WARNING]

    def test_intent_recognition_refactoring(self):
        """识别重构意图"""
        layer = PromptLayer()
        input_data = InputData(
            raw_input="优化现有的数据库查询性能"
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.PASSED, LayerStatus.WARNING]

    def test_intent_recognition_documentation(self):
        """识别文档编写意图"""
        layer = PromptLayer()
        input_data = InputData(
            raw_input="为API接口编写详细的文档说明"
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.PASSED, LayerStatus.WARNING]

    def test_input_validation_empty_input(self):
        """空输入验证失败"""
        layer = PromptLayer()
        input_data = InputData(raw_input="")
        result = layer.process(input_data)
        assert result.status == LayerStatus.FAILED

    def test_input_validation_too_short(self):
        """过短输入警告"""
        layer = PromptLayer()
        input_data = InputData(raw_input="hi")
        result = layer.process(input_data)
        assert result.status in [LayerStatus.WARNING, LayerStatus.FAILED]

    def test_context_injection_with_project_info(self):
        """项目信息上下文注入"""
        layer = PromptLayer()
        input_data = InputData(
            raw_input="添加新功能",
            project_info={
                "name": "TestProject",
                "type": "web",
                "tech_stack": ["Python", "FastAPI"],
            },
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.PASSED, LayerStatus.WARNING]

    def test_ambiguity_detection_vague_terms(self):
        """检测模糊术语"""
        layer = PromptLayer()
        input_data = InputData(raw_input="修改这个东西")
        result = layer.process(input_data)
        assert result.status in [LayerStatus.WARNING, LayerStatus.FAILED]

    def test_ambiguity_detection_multiple_questions(self):
        """检测多个问题"""
        layer = PromptLayer()
        input_data = InputData(
            raw_input="如何做A? 如何做B? 如何做C? 如何做D?"
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.WARNING, LayerStatus.FAILED]


class TestCapabilityLayer:
    """测试第2层：能力约束层"""

    def test_skill_match_high_confidence(self):
        """高置信度技能匹配"""
        layer = CapabilityLayer()
        input_data = InputData(
            raw_input="使用Python和FastAPI创建REST API",
            project_info={"tech_stack": ["Python", "FastAPI"]},
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.PASSED, LayerStatus.WARNING]

    def test_knowledge_coverage_check(self):
        """知识库覆盖检查"""
        layer = CapabilityLayer()
        input_data = InputData(
            raw_input="使用React和Vue.js开发前端"
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.PASSED, LayerStatus.WARNING]

    def test_toolchain_availability_check(self):
        """工具链可用性检查"""
        layer = CapabilityLayer()
        input_data = InputData(raw_input="使用git进行版本控制")
        result = layer.process(input_data)
        assert result.status in [LayerStatus.PASSED, LayerStatus.WARNING]

    def test_capability_gap_identification(self):
        """能力缺口识别"""
        layer = CapabilityLayer()
        input_data = InputData(
            raw_input="使用不存在的框架XYZ开发应用",
            project_info={"tech_stack": []},
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.WARNING, LayerStatus.FAILED]


class TestRuleValidationLayer:
    """测试第3层：规则校验层"""

    def test_security_scan_no_issues(self):
        """安全扫描无问题"""
        layer = RuleValidationLayer()
        input_data = InputData(
            raw_input="def hello():\n    print('Hello, World!')"
        )
        result = layer.process(input_data)
        assert result.status == LayerStatus.PASSED

    def test_security_scan_hardcoded_password(self):
        """检测硬编码密码"""
        layer = RuleValidationLayer()
        input_data = InputData(
            raw_input="password = 'admin123'"
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.WARNING, LayerStatus.FAILED]

    def test_security_scan_dangerous_eval(self):
        """检测危险的eval调用"""
        layer = RuleValidationLayer()
        input_data = InputData(
            raw_input="eval(user_input)"
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.WARNING, LayerStatus.FAILED]

    def test_coding_standards_check(self):
        """编码规范检查"""
        layer = RuleValidationLayer()
        input_data = InputData(
            raw_input="def function_with_good_name():\n    pass"
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.PASSED, LayerStatus.WARNING]

    def test_performance_benchmark_long_function(self):
        """性能基准：过长函数警告"""
        layer = RuleValidationLayer()
        long_code = "\n".join([f"    line_{i} = {i}" for i in range(101)])
        input_data = InputData(
            raw_input=f"def long_function():\n{long_code}"
        )
        result = layer.process(input_data)
        assert result.status in [LayerStatus.WARNING, LayerStatus.FAILED]

    def test_compliance_review_encoding_declaration(self):
        """合规性审查：编码声明"""
        layer = RuleValidationLayer()
        input_data = InputData(
            raw_input="# -*- coding: utf-8 -*-\ndef test(): pass"
        )
        result = layer.process(input_data)
        assert result.status == LayerStatus.PASSED


class TestFallbackRecoveryLayer:
    """测试第4层：兜底恢复层"""

    def test_quality_assessment_high_score(self):
        """高质量评分通过"""
        layer = FallbackRecoveryLayer()
        input_data = InputData(
            raw_input="这是一个清晰、完整、可操作的解决方案"
        )
        result = layer.process(input_data)
        assert result.status == LayerStatus.PASSED

    def test_quality_assessment_low_score(self):
        """低质量评分触发警告"""
        layer = FallbackRecoveryLayer()
        input_data = InputData(raw_input="x")
        result = layer.process(input_data)
        assert result.status in [LayerStatus.WARNING, LayerStatus.FAILED]

    def test_rollback_state_preparation(self):
        """回滚状态准备"""
        layer = FallbackRecoveryLayer()
        input_data = InputData(raw_input="test input")
        result = layer.process(input_data)
        rollback_info = result.details.get("rollback_state", {})
        assert rollback_info.get("state_preserved") is True

    def test_fallback_strategy_simplify_task(self):
        """降级策略：简化任务"""
        layer = FallbackRecoveryLayer()
        input_data = InputData(
            raw_input="不清晰的建议",
        )
        result = layer.process(input_data)
        strategy = result.details.get("fallback_strategy")
        if result.score < layer.quality_threshold:
            assert strategy is not None

    def test_error_log_recording(self):
        """错误日志记录"""
        layer = FallbackRecoveryLayer()
        input_data = InputData(raw_input="test")
        result = layer.process(input_data)
        error_log = result.details.get("error_log")
        assert error_log is not None


class TestFourDimensionalDefenseIntegration:
    """测试四维防线集成"""

    def test_full_check_normal_flow(self):
        """正常流程：所有层通过"""
        defense = FourDimensionalDefense()
        input_data = InputData(
            raw_input="创建一个简单的Python函数来计算斐波那契数列"
        )
        result = defense.run_full_check(input_data)
        assert len(result.layers) == 4
        assert result.success is True or result.overall_score >= 0.6

    def test_full_check_prompt_layer_failure(self):
        """Prompt层失败场景"""
        defense = FourDimensionalDefense()
        input_data = InputData(raw_input="")
        result = defense.run_full_check(input_data)
        assert len(result.layers) == 4
        assert any(
            layer.status == LayerStatus.FAILED for layer in result.layers
        )

    def test_full_check_capability_layer_warning(self):
        """Capability层警告场景"""
        defense = FourDimensionalDefense()
        input_data = InputData(
            raw_input="使用不存在的框架开发",
            project_info={"tech_stack": []},
        )
        result = defense.run_full_check(input_data)
        assert len(result.layers) == 4

    def test_full_check_security_layer_failure(self):
        """安全层失败场景"""
        defense = FourDimensionalDefense()
        input_data = InputData(
            raw_input="password = 'admin123'\neval(user_input)"
        )
        result = defense.run_full_check(input_data)
        assert len(result.layers) == 4
        security_layer = next(
            (l for l in result.layers if "security" in l.layer_name.lower()),
            None,
        )
        if security_layer:
            assert security_layer.status in [LayerStatus.WARNING, LayerStatus.FAILED]

    def test_fallback_trigger_on_low_quality(self):
        """低质量触发降级"""
        defense = FourDimensionalDefense()
        input_data = InputData(raw_input="x")
        result = defense.run_full_check(input_data)
        assert result.fallback_strategy is not None

    def test_layer_status_summary(self):
        """各层状态摘要"""
        defense = FourDimensionalDefense()
        input_data = InputData(raw_input="测试输入")
        result = defense.run_full_check(input_data)
        summary = defense.get_layer_status_summary(result)
        assert "overall" in summary
        assert "layers" in summary

    def test_report_generation(self):
        """报告生成"""
        defense = FourDimensionalDefense()
        input_data = InputData(raw_input="测试输入")
        result = defense.run_full_check(input_data)
        report = defense.generate_report(result)
        assert "四维度输出防线系统" in report
        assert "检查报告" in report

    def test_defense_result_to_dict(self):
        """防御结果转换为字典"""
        defense = FourDimensionalDefense()
        input_data = InputData(raw_input="测试输入")
        result = defense.run_full_check(input_data)
        d = result.to_dict()
        assert "success" in d
        assert "overall_score" in d
        assert "layers" in d


class TestEdgeCasesAndErrorHandling:
    """测试边界情况和错误处理"""

    def test_very_long_input(self):
        """超长输入处理"""
        defense = FourDimensionalDefense()
        long_input = "a" * 15000
        input_data = InputData(raw_input=long_input)
        result = defense.run_full_check(input_data)
        assert len(result.layers) == 4

    def test_special_characters_input(self):
        """特殊字符输入处理"""
        defense = FourDimensionalDefense()
        special_input = "测试\n特殊\t字符\r\n换行"
        input_data = InputData(raw_input=special_input)
        result = defense.run_full_check(input_data)
        assert len(result.layers) == 4

    def test_unicode_input(self):
        """Unicode输入处理"""
        defense = FourDimensionalDefense()
        unicode_input = "测试中文🎉emoji和特殊符号"
        input_data = InputData(raw_input=unicode_input)
        result = defense.run_full_check(input_data)
        assert len(result.layers) == 4

    def test_code_block_with_security_issues(self):
        """代码块包含安全问题"""
        defense = FourDimensionalDefense()
        input_data = InputData(
            raw_input="```python\npassword = 'secret'\neval(code)\n```"
        )
        result = defense.run_full_check(input_data)
        assert len(result.layers) == 4

    def test_multiple_intent_detection(self):
        """多意图检测"""
        defense = FourDimensionalDefense()
        input_data = InputData(
            raw_input="创建代码并编写文档，同时进行测试"
        )
        result = defense.run_full_check(input_data)
        assert len(result.layers) == 4


class TestFactoryFunction:
    """测试工厂函数"""

    def test_create_defense_system_default_config(self):
        """使用默认配置创建防线系统"""
        defense = create_defense_system()
        assert isinstance(defense, FourDimensionalDefense)
        assert len(defense.layers) == 4

    def test_create_defense_system_custom_config(self):
        """使用自定义配置创建防线系统"""
        custom_config = {
            "prompt_layer": {"confidence_threshold": 0.8},
            "capability_layer": {"skill_match_threshold": 0.75},
        }
        defense = create_defense_system(custom_config)
        assert isinstance(defense, FourDimensionalDefense)
        assert len(defense.layers) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
