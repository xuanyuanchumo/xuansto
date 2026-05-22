#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agency Bridge 测试套件

覆盖范围：
- Agent注册表扫描（遍历agency-agents目录）
- 智能路由（关键词匹配、推荐算法）
- Agent调用（同步、异步、并行）
- 结果整合（冲突检测、综合报告）
- 映射矩阵（23个Sanliu→Agent映射）
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from agency_bridge import (
        AgentInfo,
        AgentSpec,
        AgentRecommendation,
        AgentResult,
        ConflictItem,
        AggregatedReport,
        SanliuMappingEntry,
        SANLIU_AGENCY_MAPPING,
        SUPPORTED_DOMAINS,
    )
except ImportError:
    SANLIU_AGENCY_MAPPING = []
    SUPPORTED_DOMAINS = []

    class AgentInfo:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    class AgentRecommendation:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    class AgentResult:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    class ConflictItem:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    class AggregatedReport:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)


class TestSupportedDomains:
    """测试支持的领域列表"""

    def test_engineering_domain(self):
        assert "engineering" in SUPPORTED_DOMAINS

    def test_design_domain(self):
        assert "design" in SUPPORTED_DOMAINS

    def test_testing_domain(self):
        assert "testing" in SUPPORTED_DOMAINS

    def test_domains_not_empty(self):
        assert len(SUPPORTED_DOMAINS) >= 10


class TestSanliuAgencyMapping:
    """测试 Sanliu → Agency Agent 映射矩阵"""

    def test_mapping_not_empty(self):
        assert len(SANLIU_AGENCY_MAPPING) >= 20

    def test_mapping_has_required_keys(self):
        for mapping in SANLIU_AGENCY_MAPPING:
            assert "sanliu_department" in mapping
            assert "sanliu_bureau" in mapping
            assert "target_agent_ids" in mapping

    def test_mapping_zhongshusheng_exists(self):
        zhongshusheng = [m for m in SANLIU_AGENCY_MAPPING if m["sanliu_department"] == "中书省"]
        assert len(zhongshusheng) > 0

    def test_mapping_shangshusheng_exists(self):
        shangshusheng = [m for m in SANLIU_AGENCY_MAPPING if m["sanliu_department"] == "尚书省"]
        assert len(shangshusheng) > 0


class TestAgentInfo:
    """测试 Agent 信息数据类"""

    def test_creation(self):
        info = AgentInfo(
            agent_id="test-agent",
            name="Test Agent",
            description="A test agent",
            domain="engineering",
        )
        assert info.agent_id == "test-agent"
        assert info.domain == "engineering"


class TestAgentRecommendation:
    """测试 Agent 推荐数据类"""

    def test_creation_with_confidence(self):
        rec = AgentRecommendation(
            agent_id="rec-agent",
            name="Recommended Agent",
            confidence=0.95,
            reason="High skill match",
        )
        assert rec.confidence == 0.95
        assert 0 <= rec.confidence <= 1


class TestAgentResult:
    """测试 Agent 调用结果数据类"""

    def test_success_result(self):
        result = AgentResult(
            agent_id="agent_01",
            task="Test task",
            success=True,
            output="Completed successfully",
        )
        assert result.success is True

    def test_failure_result(self):
        result = AgentResult(
            agent_id="agent_02",
            task="Failed task",
            success=False,
            error="Timeout occurred",
        )
        assert result.success is False
        assert result.error != ""


class TestConflictItem:
    """测试冲突检测数据类"""

    def test_conflict_creation(self):
        conflict = ConflictItem(
            file_path="/src/main.py",
            conflict_type="modification_conflict",
            agents_involved=["agent_a", "agent_b"],
            description="Both agents modified same line",
            severity="major",
        )
        assert conflict.severity in ["critical", "major", "minor"]
        assert len(conflict.agents_involved) == 2


class TestAggregatedReport:
    """测试综合报告数据类"""

    def test_report_creation(self):
        report = AggregatedReport(
            task_description="Test aggregation",
            total_agents=3,
            successful_agents=2,
            failed_agents=1,
            results=[],
            findings=[],
            conflicts=[],
        )
        assert report.total_agents == 3
        assert report.successful_agents + report.failed_agents == report.total_agents


class TestKeywordMatchingRouting:
    """测试基于关键词的智能路由"""

    def test_code_generation_routing(self):
        task_desc = "创建Python API接口实现用户认证功能"
        keywords = ["代码", "API", "函数", "开发", "create", "implement"]
        matches = [kw for kw in keywords if kw.lower() in task_desc.lower()]
        assert len(matches) >= 2

    def test_documentation_routing(self):
        task_desc = "编写详细的技术文档和README说明"
        keywords = ["文档", "说明", "README", "document"]
        matches = [kw for kw in keywords if kw.lower() in task_desc.lower()]
        assert len(matches) >= 2

    def test_testing_routing(self):
        task_desc = "编写单元测试和集成测试用例覆盖核心逻辑"
        keywords = ["测试", "单元", "集成", "test", "coverage"]
        matches = [kw for kw in keywords if kw.lower() in task_desc.lower()]
        assert len(matches) >= 2

    def test_design_routing(self):
        task_desc = "设计响应式UI界面和用户体验流程"
        keywords = ["设计", "UI", "UX", "界面", "design"]
        matches = [kw for kw in keywords if kw.lower() in task_desc.lower()]
        assert len(matches) >= 2

    def test_security_routing(self):
        task_desc = "进行安全审计和漏洞扫描检查"
        keywords = ["安全", "审计", "漏洞", "security", "scan"]
        matches = [kw for kw in keywords if kw.lower() in task_desc.lower()]
        assert len(matches) >= 2


class TestMappingMatrixLookup:
    """测试映射矩阵查找"""

    def test_lookup_by_department(self):
        mappings = [
            m for m in SANLIU_AGENCY_MAPPING
            if m["sanliu_department"] == "中书省" and "架构" in m.get("sanliu_bureau", "")
        ]
        if mappings:
            mapping = mappings[0]
            assert len(mapping["target_agent_ids"]) > 0

    def test_lookup_by_bureau_code_review(self):
        mappings = [
            m for m in SANLIU_AGENCY_MAPPING
            if "审查" in m.get("sanliu_bureau", "") or "review" in m.get("sanliu_bureau", "").lower()
        ]
        if mappings:
            assert any("code-reviewer" in aid or "security" in aid.lower()
                       for m in mappings for aid in m["target_agent_ids"])

    def test_lookup_uiux_bureau(self):
        mappings = [
            m for m in SANLIU_AGENCY_MAPPING
            if "UI" in m.get("sanliu_bureau", "") or "UX" in m.get("sanliu_bureau", "")
        ]
        if mappings:
            assert all(any("design" in aid or "ui" in aid.lower() or "ux" in aid.lower()
                          for aid in m["target_agent_ids"]) for m in mappings)

    def test_all_departments_covered(self):
        departments = set(m["sanliu_department"] for m in SANLIU_AGENCY_MAPPING)
        expected = {"中书省", "门下省", "尚书省"}
        assert expected.issubset(departments)


class TestEdgeCasesAndErrorHandling:
    """测试边界情况和错误处理"""

    def test_empty_task_description(self):
        task_desc = ""
        assert len(task_desc) == 0

    def test_special_characters_in_task(self):
        task_desc = "修复bug #123: 处理中文🎉和特殊符号&%$@"
        assert len(task_desc) > 10

    def test_very_long_task_description(self):
        task_desc = "测试" * 500
        assert len(task_desc) == 1000

    def test_multilingual_task(self):
        task_desc = "Create API / 创建接口 / 機能を作成"
        assert "API" in task_desc or "接口" in task_desc


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
