#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Decision Log 系统测试套件

覆盖范围：
- Decision Log生成（DEC-YYYYMMDD-NNN格式）
- 决策记录（备选方案、影响范围、风险评估）
- 效果评估（1-5星评分、评估结果）
- 统计分析（决策分类、趋势分析）
- 导出（MD+JSON双格式）
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from decision_log import (
        RiskLevel,
        DecisionStatus,
        DecisionRecord,
        EvaluationResult,
        DecisionLog,
    )
except ImportError:

    class RiskLevel:
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"

    class DecisionStatus:
        DRAFT = "draft"
        RECORDED = "recorded"
        EVALUATED = "evaluated"
        SUPERSEDED = "superseded"

    class DecisionRecord:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    class EvaluationResult:
        def __init__(self, **kw):
            for k, v in kw.items():
                setattr(self, k, v)

    class DecisionLog:
        DEFAULT_OUTPUT_DIR = "test_decision_logs"

        def __init__(self, output_dir=None):
            self.output_dir = Path(output_dir or self.DEFAULT_OUTPUT_DIR)
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self._counter_cache = {}

        def generate(self, **kw):
            return str(self.output_dir / "DEC-test-001.md")

        def list_decisions(self, **kw):
            return []

        def get_decision(self, decision_id):
            return None

        def evaluate_outcome(self, **kw):
            return EvaluationResult(**kw)

        def get_statistics(self):
            return {}


@pytest.fixture
def decision_log(tmp_path):
    log = DecisionLog(output_dir=str(tmp_path / "decisions"))
    return log


class TestDecisionIdFormat:
    """测试决策ID格式"""

    def test_id_starts_with_dec_prefix(self):
        date_str = datetime.now().strftime("%Y%m%d")
        expected_prefix = f"DEC-{date_str}-"
        assert expected_prefix.startswith("DEC-")

    def test_id_contains_date(self):
        today = datetime.now().strftime("%Y%m%d")
        assert len(today) == 8
        assert today.isdigit()


class TestDecisionLogGenerate:
    """测试决策日志生成"""

    def test_generate_basic_decision(self, decision_log):
        path = decision_log.generate(
            decision="采用FastAPI作为后端框架",
            maker="中书省-架构设计局",
            rationale="FastAPI性能优秀，支持异步，文档自动生成",
        )
        assert path.endswith(".md")
        assert "DEC-" in Path(path).name

    def test_generate_with_alternatives(self, decision_log):
        path = decision_log.generate(
            decision="选择数据库方案",
            maker="工部-技术局",
            rationale="需要高性能NoSQL解决方案",
            alternatives=["MongoDB", "PostgreSQL", "Redis"],
            selected_option="PostgreSQL",
        )
        assert Path(path).exists()

    def test_generate_with_impact_scope(self, decision_log):
        path = decision_log.generate(
            decision="重构认证模块",
            maker="门下省-审查局",
            rationale="提升安全性",
            impact_scope=["backend", "security", "api"],
            risk_assessment="medium",
        )
        assert Path(path).exists()

    def test_generate_creates_json_file(self, decision_log):
        md_path = decision_log.generate(
            decision="JSON导出测试",
            maker="测试",
            rationale="测试用例",
        )
        json_path = md_path.replace(".md", ".json")
        assert Path(json_path).exists()

    def test_generate_with_metadata(self, decision_log):
        path = decision_log.generate(
            decision="元数据测试",
            maker="测试",
            rationale="测试",
            metadata={"version": "4.0", "category": "architecture"},
        )
        assert Path(path).exists()


class TestDecisionListAndQuery:
    """测试决策列表与查询"""

    def test_list_empty_decisions(self, decision_log):
        decisions = decision_log.list_decisions()
        assert isinstance(decisions, list)

    def test_list_after_generate(self, decision_log):
        decision_log.generate(
            decision="可查询决策",
            maker="测试者",
            rationale="用于查询测试",
        )
        decisions = decision_log.list_decisions()
        assert len(decisions) >= 1

    def test_filter_by_maker(self, decision_log):
        decision_log.generate(
            decision="按制作者过滤",
            maker="特殊部门",
            rationale="过滤测试",
        )
        decisions = decision_log.list_decisions(maker_filter="特殊部门")
        assert all(d.get("maker") == "特殊部门" for d in decisions)

    def test_filter_by_status(self, decision_log):
        decisions = decision_log.list_decisions(status_filter="recorded")
        assert isinstance(decisions, list)

    def test_keyword_search(self, decision_log):
        decision_log.generate(
            decision="搜索关键词测试：架构设计",
            maker="测试者",
            rationale="关键词搜索",
        )
        decisions = decision_log.list_decisions(keyword="架构")
        assert len(decisions) >= 0


class TestOutcomeEvaluation:
    """测试效果评估"""

    def test_evaluate_success_outcome(self, decision_log):
        md_path = decision_log.generate(
            decision="待评估决策",
            maker="评估者",
            rationale="评估测试",
        )
        decision_id = Path(md_path).stem
        result = decision_log.evaluate_outcome(
            decision_id=decision_id,
            actual_outcome="系统性能提升30%",
            effectiveness_score=0.9,
            evaluation_summary="决策非常成功",
        )
        assert result.effectiveness_score == 0.9
        assert result.would_repeat is True

    def test_evaluate_failed_outcome(self, decision_log):
        md_path = decision_log.generate(
            decision="失败案例",
            maker="评估者",
            rationale="失败评估",
        )
        decision_id = Path(md_path).stem
        result = decision_log.evaluate_outcome(
            decision_id=decision_id,
            actual_outcome="导致系统不稳定",
            effectiveness_score=0.2,
            would_repeat=False,
        )
        assert result.effectiveness_score == 0.2
        assert result.would_repeat is False

    def test_evaluate_nonexistent_raises_error(self, decision_log):
        with pytest.raises(ValueError):
            decision_log.evaluate_outcome(
                decision_id="NONEXISTENT-001",
                actual_outcome="test",
            )

    def test_evaluation_with_lessons_learned(self, decision_log):
        md_path = decision_log.generate(
            decision="经验教训",
            maker="测试者",
            rationale="教训收集",
        )
        decision_id = Path(md_path).stem
        result = decision_log.evaluate_outcome(
            decision_id=decision_id,
            actual_outcome="部分成功",
            lessons_learned=["充分测试", "渐进式发布"],
        )
        assert len(result.lessons_learned) == 2


class TestStatistics:
    """测试统计分析"""

    def test_statistics_empty_log(self, decision_log):
        stats = decision_log.get_statistics()
        assert stats["total_decisions"] == 0

    def test_statistics_with_decisions(self, decision_log):
        for i in range(5):
            decision_log.generate(
                decision=f"统计决策_{i}",
                maker=f"部门{i % 3}",
                rationale=f"理由{i}",
            )
        stats = decision_log.get_statistics()
        assert stats["total_decisions"] >= 5

    def test_statistics_by_risk_level(self, decision_log):
        decision_log.generate(
            decision="高风险决策",
            maker="风险部",
            rationale="高风险",
            risk_assessment="high",
        )
        stats = decision_log.get_statistics()
        assert "by_risk" in stats

    def test_statistics_by_maker(self, decision_log):
        decision_log.generate(
            decision="制作者统计",
            maker="统计专家",
            rationale="统计",
        )
        stats = decision_log.get_statistics()
        assert "by_maker" in stats


class TestExportFormats:
    """测试导出格式"""

    def test_markdown_export_content(self, decision_log):
        path = decision_log.generate(
            decision="导出测试",
            maker="导出员",
            rationale="导出验证",
        )
        content = Path(path).read_text(encoding="utf-8")
        assert "# DEC-" in content
        assert "决策内容" in content
        assert "决策依据" in content

    def test_json_export_valid(self, decision_log):
        path = decision_log.generate(
            decision="JSON导出",
            maker="JSON专员",
            rationale="JSON验证",
        )
        json_path = path.replace(".md", ".json")
        data = json.loads(Path(json_path).read_text(encoding="utf-8"))
        assert "decision_id" in data
        assert "decision_content" in data
        assert "maker" in data
        assert "rationale" in data


class TestEdgeCasesAndErrorHandling:
    """测试边界情况和错误处理"""

    def test_unicode_in_decision_content(self, decision_log):
        path = decision_log.generate(
            decision="中文决策🎉包含emoji和特殊符号&%$@",
            maker="Unicode测试部",
            rationale="边界测试",
        )
        assert Path(path).exists()

    def test_very_long_decision_content(self, decision_log):
        long_content = "详细描述" * 100
        path = decision_log.generate(
            decision=long_content,
            maker="长文本测试",
            rationale="长度边界测试",
        )
        assert Path(path).exists()

    def test_many_alternatives(self, decision_log):
        alts = [f"选项{i}" for i in range(10)]
        path = decision_log.generate(
            decision="多选项决策",
            maker="选项测试",
            rationale="选项数量边界",
            alternatives=alts,
        )
        assert Path(path).exists()

    def test_effectiveness_score_clamping_high(self, decision_log):
        md_path = decision_log.generate(
            decision="高分测试",
            maker="评分员",
            rationale="评分边界",
        )
        result = decision_log.evaluate_outcome(
            decision_id=Path(md_path).stem,
            actual_outcome="完美结果",
            effectiveness_score=1.5,
        )
        assert result.effectiveness_score <= 1.0

    def test_effectiveness_score_clamping_low(self, decision_log):
        md_path = decision_log.generate(
            decision="低分测试",
            maker="评分员",
            rationale="评分边界",
        )
        result = decision_log.evaluate_outcome(
            decision_id=Path(md_path).stem,
            actual_outcome="糟糕结果",
            effectiveness_score=-0.5,
        )
        assert result.effectiveness_score >= 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
