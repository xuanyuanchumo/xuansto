"""
Philosophy Integration - 理念融合协调器
作为四大开源理念的统一入口和协调中心

核心理念来源：
- OpenCode: 透明化开发、开发者体验优先
- OpenClaude: Agent编排即代码、上下文感知
- Claw-Code: SDD契约驱动、TDD闭环反馈
- Harness: 持续交付、基础设施即代码

核心功能：
1. 统一调用入口 - 单一入口点调用任何开源理念
2. 理念冲突解决机制 - 不同理念矛盾建议的仲裁逻辑
3. 最佳实践推荐引擎 - 基于项目特征推荐最佳实践组合
4. 理念效能评估 - 统计各理念使用频次和效果
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any


class PhilosophyType(Enum):
    """理念类型枚举"""
    OPENCODE = "OpenCode Transparency"
    OPENCLAUDE = "OpenClaude Orchestrator"
    CLAWCODE = "Claw-Code SDD/TDD"
    HARNESS = "Harness CI/CD"


class ConflictPriority(Enum):
    """冲突解决优先级（数值越高越优先）"""
    SAFETY = 100
    QUALITY = 80
    DX = 60
    PERFORMANCE = 40
    SPEED = 20


class TaskCategory(Enum):
    """任务类别枚举"""
    ARCHITECTURE_DECISION = auto()
    CODE_GENERATION = auto()
    TESTING = auto()
    WORKFLOW_ORCHESTRATION = auto()
    DOCUMENTATION = auto()
    REFACTORING = auto()
    DEBUGGING = auto()
    DEPLOYMENT = auto()


@dataclass
class PhilosophyRecommendation:
    """理念推荐结果"""
    primary_philosophy: PhilosophyType
    secondary_philosophies: list[PhilosophyType]
    confidence: float
    reasoning: list[str]
    suggested_actions: list[str]


@dataclass
class ConflictRecord:
    """理念冲突记录"""
    conflict_id: str
    timestamp: datetime
    philosophies_involved: list[PhilosophyType]
    conflict_description: str
    resolution: str
    winning_philosophy: PhilosophyType
    priority_applied: ConflictPriority
    task_context: str


@dataclass
class PhilosophyUsageRecord:
    """理念使用记录"""
    philosophy: PhilosophyType
    task_type: TaskCategory
    timestamp: datetime
    success: bool
    duration_ms: int
    notes: str = ""


@dataclass
class PhilosophyEffectivenessReport:
    """理念效能报告"""
    report_id: str
    generated_at: datetime
    total_usages: int
    by_philosophy: dict[PhilosophyType, dict[str, Any]]
    success_rates: dict[PhilosophyType, float]
    average_durations: dict[PhilosophyType, int]
    recommendations: list[str]


class PhilosophyConflictResolver:
    """
    理念冲突解决器
    
    当不同开源理念给出矛盾建议时，根据预定义的优先级规则进行仲裁
    """

    PRIORITY_RULES = {
        ConflictPriority.SAFETY: {
            "description": "安全性和合规性最高优先",
            "examples": ["安全漏洞修复", "数据保护", "访问控制", "加密实现"],
        },
        ConflictPriority.QUALITY: {
            "description": "代码质量和正确性次高优先",
            "examples": ["核心业务逻辑", "数据处理", "事务一致性", "关键算法"],
        },
        ConflictPriority.DX: {
            "description": "开发者体验优先",
            "examples": ["API设计", "错误处理", "日志格式", "文档生成"],
        },
        ConflictPriority.PERFORMANCE: {
            "description": "性能优化",
            "examples": ["查询优化", "缓存策略", "异步处理", "资源管理"],
        },
        ConflictPriority.SPEED: {
            "description": "开发速度优先（最低优先级）",
            "examples": ["原型开发", "快速迭代", "实验性功能", "演示代码"],
        },
    }

    PHILOSOPHY_CONFLICT_MATRIX = {
        (PhilosophyType.OPENCODE, PhilosophyType.OPENCLAUDE): {
            "common_conflicts": [
                "透明度 vs 自动化效率",
                "详细文档 vs 快速执行",
            ],
            "resolution_rule": "根据任务复杂度选择：简单任务优先自动化，复杂任务优先透明度",
        },
        (PhilosophyType.CLAWCODE, PhilosophyType.OPENCODE): {
            "common_conflicts": [
                "测试覆盖率要求 vs 开发速度",
                "契约严格性 vs 灵活性",
            ],
            "resolution_rule": "关键路径使用TDD，非关键路径可适当放宽",
        },
    }

    def __init__(self):
        self._conflict_history: list[ConflictRecord] = []

    def resolve_conflict(
        self,
        philosophy_a: PhilosophyType,
        philosophy_b: PhilosophyType,
        conflict_description: str,
        task_context: str = "",
    ) -> ConflictRecord:
        """
        解决两个理念之间的冲突
        
        Args:
            philosophy_a: 第一个理念
            philosophy_b: 第二个理念
            conflict_description: 冲突描述
            task_context: 任务上下文
            
        Returns:
            冲突解决记录
        """
        priority_a = self._determine_priority(philosophy_a, task_context)
        priority_b = self._determine_priority(philosophy_b, task_context)
        
        if priority_a.value >= priority_b.value:
            winner = philosophy_a
            applied_priority = priority_a
        else:
            winner = philosophy_b
            applied_priority = priority_b
        
        resolution = self._generate_resolution(winner, philosophy_a, philosophy_b, task_context)
        
        record = ConflictRecord(
            conflict_id=f"CF-{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.now(timezone.utc),
            philosophies_involved=[philosophy_a, philosophy_b],
            conflict_description=conflict_description,
            resolution=resolution,
            winning_philosophy=winner,
            priority_applied=applied_priority,
            task_context=task_context,
        )
        
        self._conflict_history.append(record)
        return record

    def _determine_priority(self, philosophy: PhilosophyType, context: str) -> ConflictPriority:
        """根据理念和上下文确定优先级"""
        context_lower = context.lower()
        
        safety_keywords = ["安全", "security", "漏洞", "vuln", "敏感", "sensitive", "加密", "encrypt"]
        quality_keywords = ["质量", "quality", "正确", "correct", "准确", "accurate", "核心", "critical"]
        dx_keywords = ["体验", "experience", "可用", "usable", "友好", "friendly", "文档", "document"]
        performance_keywords = ["性能", "performance", "速度", "speed", "延迟", "latency", "优化", "optimize"]
        
        if any(kw in context_lower for kw in safety_keywords):
            return ConflictPriority.SAFETY
        elif any(kw in context_lower for kw in quality_keywords):
            return ConflictPriority.QUALITY
        elif any(kw in context_lower for kw in dx_keywords):
            return ConflictPriority.DX
        elif any(kw in context_lower for kw in performance_keywords):
            return ConflictPriority.PERFORMANCE
        else:
            return ConflictPriority.SPEED

    def _generate_resolution(
        self,
        winner: PhilosophyType,
        loser_a: PhilosophyType,
        loser_b: PhilosophyType,
        context: str,
    ) -> str:
        """生成冲突解决方案说明"""
        loser = loser_a if loser_a != winner else loser_b
        
        resolutions = {
            PhilosophyType.OPENCODE: f"采用{PhilosophyType.OPENCODE.value}的透明化方案，保留完整决策记录，同时吸收{loser.value}中适用的部分建议。",
            PhilosophyType.OPENCLAUDE: f"采用{PhilosophyType.OPENCLAUDE.value}的自动化工作流，在关键决策点添加人工审核环节以兼顾{loser.value}的要求。",
            PhilosophyType.CLAWCODE: f"采用{PhilosophyType.CLAWCODE.value}的TDD方法，确保测试覆盖率和代码质量符合{loser.value}的基本要求。",
            PhilosophyType.HARNESS: f"采用{PhilosophyType.HARNESS.value}的CI/CD流水线，在部署前集成{loser.value}的质量门禁检查。",
        }
        
        return resolutions.get(winner, f"基于优先级规则选择 {winner.value}")

    def get_conflict_summary(self) -> dict[str, Any]:
        """获取冲突解决摘要"""
        if not self._conflict_history:
            return {"total_conflicts": 0, "message": "No conflicts recorded"}
        
        winner_counts = {}
        for record in self._conflict_history:
            key = record.winning_philosophy.name
            winner_counts[key] = winner_counts.get(key, 0) + 1
        
        return {
            "total_conflicts": len(self._conflict_history),
            "winners_distribution": winner_counts,
            "recent_conflicts": [
                {
                    "id": c.conflict_id,
                    "philosophies": [p.name for p in c.philosophies_involved],
                    "winner": c.winning_philosophy.name,
                    "priority": c.priority_applied.name,
                }
                for c in self._conflict_history[-5:]
            ],
        }


class BestPracticeRecommender:
    """
    最佳实践推荐引擎
    
    基于项目特征和历史数据推荐最佳实践组合
    """

    TASK_PHILOSOPHY_MAPPING = {
        TaskCategory.ARCHITECTURE_DECISION: {
            PhilosophyType.OPENCODE: {"weight": 0.9, "reason": "架构决策需要高度透明化"},
            PhilosophyType.CLAWCODE: {"weight": 0.7, "reason": "需要契约驱动的接口定义"},
            PhilosophyType.OPENCLAUDE: {"weight": 0.5, "reason": "多角色协作评审"},
        },
        TaskCategory.CODE_GENERATION: {
            PhilosophyType.OPENCODE: {"weight": 0.6, "reason": "代码决策需记录"},
            PhilosophyType.CLAWCODE: {"weight": 0.95, "reason": "TDD驱动开发"},
            PhilosophyType.OPENCLAUDE: {"weight": 0.7, "reason": "多Agent协作编码"},
        },
        TaskCategory.TESTING: {
            PhilosophyType.CLAWCODE: {"weight": 1.0, "reason": "SDD/TDD核心理念"},
            PhilosophyType.HARNESS: {"weight": 0.7, "reason": "CI/CD集成测试"},
            PhilosophyType.OPENCODE: {"weight": 0.5, "reason": "测试决策记录"},
        },
        TaskCategory.WORKFLOW_ORCHESTRATION: {
            PhilosophyType.OPENCLAUDE: {"weight": 1.0, "reason": "Agent编排核心能力"},
            PhilosophyType.HARNESS: {"weight": 0.8, "reason": "流水线编排"},
            PhilosophyType.OPENCODE: {"weight": 0.4, "reason": "流程透明化"},
        },
        TaskCategory.DOCUMENTATION: {
            PhilosophyType.OPENCODE: {"weight": 1.0, "reason": "透明化和文档是核心"},
            PhilosophyType.CLAWCODE: {"weight": 0.6, "reason": "规格文档维护"},
        },
        TaskCategory.REFACTORING: {
            PhilosophyType.CLAWCODE: {"weight": 0.85, "reason": "回归测试保障"},
            PhilosophyType.OPENCODE: {"weight": 0.75, "reason": "重构决策记录"},
            PhilosophyType.OPENCLAUDE: {"weight": 0.5, "reason": "自动化重构流程"},
        },
        TaskCategory.DEBUGGING: {
            PhilosophyType.OPENCODE: {"weight": 0.7, "reason": "调试过程记录"},
            PhilosophyType.CLAWCODE: {"weight": 0.65, "reason": "失败用例分析"},
        },
        TaskCategory.DEPLOYMENT: {
            PhilosophyType.HARNESS: {"weight": 1.0, "reason": "CI/CD核心理念"},
            PhilosophyType.OPENCODE: {"weight": 0.6, "reason": "部署决策审计"},
            PhilosophyType.OPENCLAUDE: {"weight": 0.5, "reason": "多环境协调"},
        },
    }

    PROJECT_TYPE_RECOMMENDATIONS = {
        "web_application": {
            "primary": PhilosophyType.OPENCLAUDE,
            "secondary": [PhilosophyType.CLAWCODE, PhilosophyType.HARNESS],
            "confidence": 0.85,
        },
        "api_service": {
            "primary": PhilosophyType.CLAWCODE,
            "secondary": [PhilosophyType.OPENCODE, PhilosophyType.HARNESS],
            "confidence": 0.88,
        },
        "library_sdk": {
            "primary": PhilosophyType.CLAWCODE,
            "secondary": [PhilosophyType.OPENCODE],
            "confidence": 0.90,
        },
        "data_pipeline": {
            "primary": PhilosophyType.HARNESS,
            "secondary": [PhilosophyType.OPENCODE, PhilosophyType.OPENCLAUDE],
            "confidence": 0.78,
        },
        "ml_model": {
            "primary": PhilosophyType.OPENCODE,
            "secondary": [PhilosophyType.CLAWCODE],
            "confidence": 0.75,
        },
    }

    def recommend(self, task_category: TaskCategory, project_type: str = "general") -> PhilosophyRecommendation:
        """
        根据任务类别和项目类型推荐理念组合
        
        Args:
            task_category: 任务类别
            project_type: 项目类型
            
        Returns:
            推荐结果对象
        """
        task_mapping = self.TASK_PHILOSOPHY_MAPPING.get(task_category, {})
        project_rec = self.PROJECT_TYPE_RECOMMENDATIONS.get(project_type, {})
        
        scores: dict[PhilosophyType, float] = {}
        reasoning: list[str] = []
        
        for philosophy, info in task_mapping.items():
            base_score = info["weight"] * 0.6
            scores[philosophy] = scores.get(philosophy, 0) + base_score
            reasoning.append(f"{philosophy.value}: {info['reason']}")
        
        if project_rec:
            primary = project_rec["primary"]
            scores[primary] = scores.get(primary, 0) + 0.3
            for secondary in project_rec.get("secondary", []):
                scores[secondary] = scores.get(secondary, 0) + 0.15
        
        sorted_philosophies = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary_philosophy = sorted_philosophies[0][0] if sorted_philosophies else PhilosophyType.OPENCODE
        secondary_philosophies = [p for p, _ in sorted_philosophies[1:4]]
        
        confidence = min(sorted_philosophies[0][1] if sorted_philosophies else 0.5, 0.99)
        
        actions = self._generate_suggested_actions(primary_philosophy, task_category)
        
        return PhilosophyRecommendation(
            primary_philosophy=primary_philosophy,
            secondary_philosophies=secondary_philosophies,
            confidence=round(confidence, 2),
            reasoning=reasoning,
            suggested_actions=actions,
        )

    def _generate_suggested_actions(self, philosophy: PhilosophyType, category: TaskCategory) -> list[str]:
        """生成建议操作列表"""
        action_templates = {
            PhilosophyType.OPENCODE: [
                "启用Decision Log自动记录",
                "执行DX评分评估",
                "生成任务分解步骤",
                "记录关键决策依据",
            ],
            PhilosophyType.OPENCLAUDE: [
                "加载对应的工作流模板",
                "初始化Agent协作链路",
                "注入项目技术栈上下文",
                "配置变量传递规则",
            ],
            PhilosophyType.CLAWCODE: [
                "解析SDD文档提取可执行条款",
                "生成验收测试用例",
                "计算当前覆盖率",
                "更新追踪矩阵",
            ],
            PhilosophyType.HARNESS: [
                "配置CI/CD流水线",
                "设置质量门禁",
                "配置自动部署策略",
                "启用监控告警",
            ],
        }
        
        base_actions = action_templates.get(philosophy, ["应用通用最佳实践"])
        category_specific = {
            TaskCategory.ARCHITECTURE_DECISION: ["创建架构决策记录(ADR)", "组织多方评审"],
            TaskCategory.CODE_GENERATION: ["遵循TDD红绿蓝循环", "保持小步提交"],
            TaskCategory.TESTING: ["确保边界条件覆盖", "运行完整测试套件"],
        }
        
        return base_actions + category_specific.get(category, [])


class PhilosophyEffectivenessEvaluator:
    """
    理念效能评估器
    
    统计各理念的使用频次和效果，生成效能报告
    """

    def __init__(self):
        self._usage_records: list[PhilosophyUsageRecord] = []

    def record_usage(
        self,
        philosophy: PhilosophyType,
        task_type: TaskCategory,
        success: bool,
        duration_ms: int,
        notes: str = "",
    ) -> None:
        """
        记录一次理念使用
        
        Args:
            philosophy: 使用的理念类型
            task_type: 任务类型
            success: 是否成功
            duration_ms: 执行耗时（毫秒）
            notes: 备注
        """
        record = PhilosophyUsageRecord(
            philosophy=philosophy,
            task_type=task_type,
            timestamp=datetime.now(timezone.utc),
            success=success,
            duration_ms=duration_ms,
            notes=notes,
        )
        self._usage_records.append(record)

    def generate_report(self) -> PhilosophyEffectivenessReport:
        """
        生成理念效能报告
        
        Returns:
            完整的效能报告对象
        """
        total = len(self._usage_records)
        
        by_philosophy: dict[PhilosophyType, dict[str, Any]] = {}
        success_rates: dict[PhilosophyType, float] = {}
        avg_durations: dict[PhilosophyType, int] = {}
        
        for philosophy in PhilosophyType:
            records = [r for r in self._usage_records if r.philosophy == philosophy]
            
            if records:
                success_count = sum(1 for r in records if r.success)
                avg_duration = sum(r.duration_ms for r in records) // len(records)
                
                by_philosophy[philosophy] = {
                    "total_uses": len(records),
                    "successes": success_count,
                    "failures": len(records) - success_count,
                    "avg_duration_ms": avg_duration,
                    "by_task_type": {
                        tt.name: sum(1 for r in records if r.task_type == tt)
                        for tt in TaskCategory
                    },
                }
                
                success_rates[philosophy] = round(success_count / len(records), 2)
                avg_durations[philosophy] = avg_duration
            else:
                by_philosophy[philosophy] = {
                    "total_uses": 0,
                    "successes": 0,
                    "failures": 0,
                    "avg_duration_ms": 0,
                    "by_task_type": {},
                }
                success_rates[philosophy] = 0.0
                avg_durations[philosophy] = 0
        
        recommendations = self._generate_recommendations(by_philosophy, success_rates)
        
        return PhilosophyEffectivenessReport(
            report_id=f"RPT-{uuid.uuid4().hex[:10].upper()}",
            generated_at=datetime.now(timezone.utc),
            total_usages=total,
            by_philosophy=by_philosophy,
            success_rates=success_rates,
            average_durations=avg_durations,
            recommendations=recommendations,
        )

    def _generate_recommendations(
        self,
        by_philosophy: dict[PhilosophyType, dict[str, Any]],
        success_rates: dict[PhilosophyType, float],
    ) -> list[str]:
        """基于统计数据生成改进建议"""
        recommendations = []
        
        best_success = max(success_rates.items(), key=lambda x: x[1])
        worst_success = min(success_rates.items(), key=lambda x: x[1])
        
        if best_success[1] > 0.85:
            recommendations.append(f"✅ {best_success[0].value} 表现优异（成功率 {best_success[1]*100:.0f}%），建议在更多场景中使用")
        
        if worst_success[1] < 0.6 and worst_success[1] > 0:
            recommendations.append(f"⚠️ {worst_success[0].value} 成功率较低（{worst_success[1]*100:.0f}%），建议审查使用场景或增加培训")
        
        underused = [
            p for p, stats in by_philosophy.items() 
            if stats["total_uses"] < max(s["total_uses"] for s in by_philosophy.values()) * 0.3 
            and stats["total_uses"] > 0
        ]
        if underused:
            names = ", ".join(p.value for p in underused[:2])
            recommendations.append(f"💡 {names} 使用频率较低，考虑扩展其适用场景")
        
        slowest = max(avg_durations.items(), key=lambda x: x[1]) if any(avg_durations.values()) else None
        fastest = min((p, d for p, d in avg_durations.items() if d > 0), key=lambda x: x[1], default=(None, 0))
        
        if slowest and slowest[1] > 0 and fastest[1] > 0 and slowest[1] > fastest[1] * 2:
            recommendations.append(f"⏱️ {slowest[0].value} 平均耗时较长（{slowest[1]}ms），考虑优化流程")
        
        if not recommendations:
            recommendations.append("📊 数据量不足，继续收集使用数据后再次评估")
        
        return recommendations

    def get_usage_statistics(self) -> dict[str, Any]:
        """获取使用统计摘要"""
        if not self._usage_records:
            return {"total_records": 0, "message": "No usage data collected yet"}
        
        return {
            "total_records": len(self._usage_records),
            "date_range": {
                "earliest": min(r.timestamp for r in self._usage_records).isoformat(),
                "latest": max(r.timestamp for r in self._usage_records).isoformat(),
            },
            "overall_success_rate": round(
                sum(1 for r in self._usage_records if r.success) / len(self._usage_records), 2
            ),
            "average_duration_ms": (
                sum(r.duration_ms for r in self._usage_records) // len(self._usage_records)
            ),
        }


class PhilosophyIntegration:
    """
    理念融合协调器主类
    
    作为四大开源理念的统一入口和协调中心，提供：
    - 统一调用入口
    - 理念冲突解决
    - 最佳实践推荐
    - 效能评估与报告
    """

    def __init__(self, project_root: Path | str | None = None):
        """
        初始化理念融合协调器
        
        Args:
            project_root: 项目根目录路径
        """
        if isinstance(project_root, str):
            project_root = Path(project_root)
        self.project_root = project_root or Path.cwd()
        
        self.conflict_resolver = PhilosophyConflictResolver()
        self.recommender = BestPracticeRecommender()
        self.evaluator = PhilosophyEffectivenessEvaluator()
        
        self._initialized = False
        self._components: dict[str, Any] = {}

    def initialize(self) -> dict[str, Any]:
        """
        初始化所有子组件
        
        Returns:
            初始化状态信息
        """
        try:
            from .opencode_transparency import OpenCodeTransparency
            from .openclaude_orchestrator import OpenClaudeOrchestrator
            from .clawcode_sdd_tdd_engine import ClawCodeSDDTDDEngine
            
            self._components["opencode"] = OpenCodeTransparency(self.project_root)
            self._components["openclaude"] = OpenClaudeOrchestrator(self.project_root)
            self._components["clawcode"] = ClawCodeSDDTDDEngine(self.project_root)
            
            self._initialized = True
            
            return {
                "status": "initialized",
                "components_loaded": list(self._components.keys()),
                "project_root": str(self.project_root),
            }
            
        except Exception as e:
            return {
                "status": "partial_init",
                "error": str(e),
                "components_loaded": list(self._components.keys()),
            }

    def execute_with_philosophy(
        self,
        philosophy: PhilosophyType,
        action: str,
        params: dict[str, Any] | None = None,
        task_category: TaskCategory = TaskCategory.CODE_GENERATION,
    ) -> dict[str, Any]:
        """
        通过指定理念执行动作
        
        Args:
            philosophy: 要使用的理念类型
            action: 动作名称
            params: 动作参数
            task_category: 任务类别（用于记录）
            
        Returns:
            执行结果字典
        """
        import time
        
        params = params or {}
        start_time = time.time()
        success = False
        result = {}
        
        try:
            if not self._initialized:
                init_result = self.initialize()
                if init_result["status"] != "initialized":
                    return {"error": "Failed to initialize components", "details": init_result}
            
            component_map = {
                PhilosophyType.OPENCODE: "opencode",
                PhilosophyType.OPENCLAUDE: "openclaude",
                PhilosophyType.CLAWCODE: "clawcode",
                PhilosophyType.HARNESS: "harness",
            }
            
            component_key = component_map.get(philosophy)
            if component_key and component_key in self._components:
                component = self._components[component_key]
                handler = getattr(component, action, None)
                
                if callable(handler):
                    result = handler(**params) if params else handler()
                    success = True
                else:
                    result = {"error": f"Action '{action}' not found on {philosophy.value}"}
            else:
                result = {"error": f"Philosophy {philosophy.value} not available or not implemented yet"}
                
        except Exception as e:
            result = {"error": str(e), "exception_type": type(e).__name__}
        
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            self.evaluator.record_usage(
                philosophy=philosophy,
                task_type=task_category,
                success=success,
                duration_ms=duration_ms,
                notes=f"Action: {action}",
            )
        
        result["_meta"] = {
            "philosophy_used": philosophy.value,
            "action": action,
            "success": success,
            "duration_ms": duration_ms,
        }
        
        return result

    def auto_execute(
        self,
        task_description: str,
        task_category: TaskCategory,
        params: dict[str, Any] | None = None,
        project_type: str = "general",
    ) -> dict[str, Any]:
        """
        自动选择最佳理念并执行任务
        
        Args:
            task_description: 任务描述
            task_category: 任务类别
            params: 任务参数
            project_type: 项目类型
            
        Returns:
            执行结果和建议信息
        """
        recommendation = self.recommender.recommend(task_category, project_type)
        
        action_map = {
            TaskCategory.ARCHITECTURE_DECISION: "record_decision",
            TaskCategory.CODE_GENERATION: "decompose_task",
            TaskCategory.TESTING: "batch_generate_tests",
            TaskCategory.WORKFLOW_ORCHESTRATION: "execute_workflow",
            TaskCategory.DOCUMENTATION: "generate_report",
            TaskCategory.REFACTORING: "parse_sdd_document",
            TaskCategory.DEBUGGING: "trace_decision_chain",
            TaskCategory.DEPLOYMENT: "get_execution_status",
        }
        
        action = action_map.get(task_category, "generate_report")
        
        primary_result = self.execute_with_philosophy(
            philosophy=recommendation.primary_philosophy,
            action=action,
            params=params,
            task_category=task_category,
        )
        
        return {
            "result": primary_result,
            "recommendation": {
                "primary": recommendation.primary_philosophy.value,
                "secondary": [p.value for p in recommendation.secondary_philosophies],
                "confidence": recommendation.confidence,
                "reasoning": recommendation.reasoning,
            },
            "suggested_actions": recommendation.suggested_actions,
        }

    def resolve_and_execute(
        self,
        conflicting_suggestions: list[tuple[PhilosophyType, str]],
        task_context: str,
        execution_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        解决理念冲突并执行获胜方建议
        
        Args:
            conflicting_suggestions: 冲突的建议列表 [(理念, 建议内容), ...]
            task_context: 任务上下文
            execution_params: 执行参数
            
        Returns:
            包含冲突解决信息和执行结果的字典
        """
        if len(conflicting_suggestions) < 2:
            philosophy, suggestion = conflicting_suggestions[0]
            return self.execute_with_philosophy(
                philosophy=philosophy,
                action="execute_workflow" if "workflow" in suggestion.lower() else "record_decision",
                params=execution_params,
            )
        
        phil_a, sug_a = conflicting_suggestions[0]
        phil_b, sug_b = conflicting_suggestions[1]
        
        conflict_record = self.conflict_resolver.resolve_conflict(
            philosophy_a=phil_a,
            philosophy_b=phil_b,
            conflict_description=f"Suggestion A ({phil_a.value}): {sug_a[:50]}... vs Suggestion B ({phil_b.value}): {sug_b[:50]}...",
            task_context=task_context,
        )
        
        winner_action = sug_a if conflict_record.winning_philosophy == phil_a else sug_b
        
        execution_result = self.execute_with_philosophy(
            philosophy=conflict_record.winning_philosophy,
            action=self._infer_action_from_suggestion(winner_action),
            params=execution_params,
        )
        
        return {
            "execution_result": execution_result,
            "conflict_resolution": {
                "conflict_id": conflict_record.conflict_id,
                "winner": conflict_record.winning_philosophy.value,
                "priority_applied": conflict_record.priority_applied.name,
                "resolution": conflict_record.resolution,
            },
        }

    @staticmethod
    def _infer_action_from_suggestion(suggestion: str) -> str:
        """从建议文本推断要执行的动作"""
        suggestion_lower = suggestion.lower()
        
        if any(kw in suggestion_lower for kw in ["workflow", "pipeline", "orchestrat"]):
            return "execute_workflow"
        elif any(kw in suggestion_lower for kw in ["decision", "choose", "select"]):
            return "record_decision"
        elif any(kw in suggestion_lower for kw in ["test", "coverage", "tdd"]):
            return "batch_generate_tests"
        elif any(kw in suggestion_lower for kw in ["context", "inject", "detect"]):
            return "get_enhanced_prompt"
        else:
            return "generate_report"

    def get_comprehensive_report(self) -> dict[str, Any]:
        """
        生成综合报告（包含所有子系统的状态和统计）
        
        Returns:
            综合报告字典
        """
        effectiveness_report = self.evaluator.generate_report()
        conflict_summary = self.conflict_resolver.get_conflict_summary()
        usage_stats = self.evaluator.get_usage_statistics()
        
        report = {
            "report_title": "Philosophy Integration Comprehensive Report",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "integration_status": "active" if self._initialized else "not_initialized",
            "components_status": {
                name: "loaded" for name in self._components.keys()
            },
            "effectiveness_report": {
                "report_id": effectiveness_report.report_id,
                "total_usages": effectiveness_report.total_usages,
                "success_rates": {p.name: rate for p, rate in effectiveness_report.success_rates.items()},
                "recommendations": effectiveness_report.recommendations,
            },
            "conflict_resolution_summary": conflict_summary,
            "usage_statistics": usage_stats,
        }
        
        if self._initialized:
            try:
                opencode = self._components.get("opencode")
                if opencode:
                    report["opencode_transparency"] = {
                        "decisions_recorded": len(opencode._decisions),
                        "dx_evaluations": len(opencode._dx_scores),
                        "atomic_steps": len(opencode._atomic_steps),
                    }
                
                clawcode = self._components.get("clawcode")
                if clawcode:
                    sdd_summary = clawcode.get_summary()
                    report["clawcode_sdd_tdd"] = sdd_summary
                
                openclaude = self._components.get("openclaude")
                if openclaude:
                    report["openclaude_orchestrator"] = {
                        "workflows_loaded": len(openclaude._loaded_workflows),
                        "project_context": {
                            "language": openclaude.context_injector.get_context().language,
                            "framework": openclaude.context_injector.get_context().framework,
                        } if openclaude.context_injector._context else {},
                    }
                    
            except Exception as e:
                report["component_details_error"] = str(e)
        
        return report

    def export_state(self, output_path: Path | str | None = None) -> Path:
        """
        导出当前状态到JSON文件
        
        Args:
            output_path: 输出文件路径
            
        Returns:
            实际写入的文件路径
        """
        if isinstance(output_path, str):
            output_path = Path(output_path)
        
        if output_path is None:
            output_path = self.project_root / "reports" / "philosophy_integration_state.json"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        state = self.get_comprehensive_report()
        
        state["export_metadata"] = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "version": "6.0.0",
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2, default=str)
        
        return output_path
