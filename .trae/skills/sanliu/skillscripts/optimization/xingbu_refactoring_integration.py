"""
刑部重构流程集成模块

将代码质量优化器集成到刑部（代码审查和重构）流程中
提供自动化的代码质量改进和重构建议执行
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .code_quality_optimizer_enhanced import (
    UnifiedCodeQualityOptimizer,
    RefactoringSuggestion,
    RefactoringContext,
    ComplexityLevel
)


class XingbuRefactoringPhase(Enum):
    """刑部重构阶段"""
    ANALYSIS = "analysis"
    SUGGESTION = "suggestion"
    EXECUTION = "execution"
    VALIDATION = "validation"
    REPORT = "report"


class XingbuRefactoringMode(Enum):
    """刑部重构模式"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


@dataclass
class XingbuRefactoringConfig:
    """刑部重构配置"""
    mode: XingbuRefactoringMode = XingbuRefactoringMode.BALANCED
    auto_apply: bool = False
    max_refactorings_per_cycle: int = 10
    require_tests: bool = True
    auto_rollback_on_failure: bool = True
    complexity_threshold: ComplexityLevel = ComplexityLevel.HIGH
    enable_snapshot: bool = True
    output_dir: Optional[Path] = None


@dataclass
class XingbuRefactoringResult:
    """刑部重构结果"""
    cycle_id: str
    timestamp: str
    phase: XingbuRefactoringPhase
    mode: XingbuRefactoringMode
    suggestions_generated: int
    refactorings_executed: int
    refactorings_successful: int
    refactorings_rolled_back: int
    quality_improvement: float
    complexity_reduction: float
    details: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class XingbuRefactoringIntegrator:
    """刑部重构流程集成器"""

    def __init__(self, project_path: Path, config: Optional[XingbuRefactoringConfig] = None):
        self.project_path = project_path
        self.config = config or XingbuRefactoringConfig()
        
        self.optimizer = UnifiedCodeQualityOptimizer(project_path)
        
        self._cycle_counter = 0
        self._results: List[XingbuRefactoringResult] = []
        self._current_phase = XingbuRefactoringPhase.ANALYSIS

    def run_xingbu_refactoring_cycle(
        self,
        target_files: Optional[List[str]] = None,
        custom_config: Optional[XingbuRefactoringConfig] = None
    ) -> XingbuRefactoringResult:
        """执行刑部重构周期"""
        config = custom_config or self.config
        self._cycle_counter += 1
        cycle_id = f"XINGBU-{datetime.now().strftime('%Y%m%d%H%M%S')}-{self._cycle_counter}"
        
        start_time = datetime.now()

        if config.enable_snapshot:
            snapshot_id = self.optimizer.safe_executor.create_snapshot(f"pre_refactor_{cycle_id}")
        
        self._current_phase = XingbuRefactoringPhase.ANALYSIS
        complexity_issues = self.optimizer.complexity_analyzer.analyze_complexity(self.project_path)
        duplication_issues = self.optimizer.duplication_detector.detect_duplications(self.project_path)
        
        if target_files:
            complexity_issues = [i for i in complexity_issues if i.file_path in target_files]
            duplication_issues = [i for i in duplication_issues if i.file_path in target_files]

        self._current_phase = XingbuRefactoringPhase.SUGGESTION
        suggestions = self.optimizer.refactoring_advisor.generate_refactoring_suggestions(
            complexity_issues, duplication_issues
        )
        
        suggestions = self._filter_suggestions_by_mode(suggestions, config)

        self._current_phase = XingbuRefactoringPhase.EXECUTION
        executed_contexts = []
        for suggestion in suggestions[:config.max_refactorings_per_cycle]:
            context = self.optimizer.safe_executor.execute_safe_refactoring(
                suggestion,
                run_tests=config.require_tests,
                auto_rollback=config.auto_rollback_on_failure
            )
            executed_contexts.append(context)
            
            self.optimizer.history_manager.record_optimization(
                context, suggestion.refactoring_type.value
            )

        self._current_phase = XingbuRefactoringPhase.VALIDATION
        successful_count = sum(1 for ctx in executed_contexts if ctx.validation_passed)
        rolled_back_count = sum(1 for ctx in executed_contexts if not ctx.validation_passed)
        
        quality_improvement = self._calculate_quality_improvement(executed_contexts)
        complexity_reduction = self._calculate_complexity_reduction(executed_contexts)

        self._current_phase = XingbuRefactoringPhase.REPORT
        recommendations = self._generate_recommendations(
            executed_contexts, quality_improvement, complexity_reduction
        )

        end_time = datetime.now()
        
        result = XingbuRefactoringResult(
            cycle_id=cycle_id,
            timestamp=start_time.isoformat(),
            phase=self._current_phase,
            mode=config.mode,
            suggestions_generated=len(suggestions),
            refactorings_executed=len(executed_contexts),
            refactorings_successful=successful_count,
            refactorings_rolled_back=rolled_back_count,
            quality_improvement=quality_improvement,
            complexity_reduction=complexity_reduction,
            details={
                'duration_seconds': (end_time - start_time).total_seconds(),
                'complexity_issues_found': len(complexity_issues),
                'duplication_issues_found': len(duplication_issues),
                'high_complexity_count': sum(
                    1 for i in complexity_issues 
                    if i.complexity_level in [ComplexityLevel.HIGH, ComplexityLevel.VERY_HIGH]
                ),
                'contexts': [
                    {
                        'refactoring_id': ctx.refactoring_id,
                        'file_path': ctx.file_path,
                        'validation_passed': ctx.validation_passed,
                        'improvements': ctx.improvements,
                        'risks': ctx.risks_identified
                    }
                    for ctx in executed_contexts
                ]
            },
            recommendations=recommendations
        )
        
        self._results.append(result)
        
        if config.output_dir:
            self._export_result(result, config.output_dir)
        
        return result

    def _filter_suggestions_by_mode(
        self, 
        suggestions: List[RefactoringSuggestion],
        config: XingbuRefactoringConfig
    ) -> List[RefactoringSuggestion]:
        """根据模式过滤建议"""
        if config.mode == XingbuRefactoringMode.CONSERVATIVE:
            return [s for s in suggestions if s.priority in ['critical', 'high'] and s.estimated_effort in ['low', 'medium']]
        elif config.mode == XingbuRefactoringMode.AGGRESSIVE:
            return suggestions
        else:  # BALANCED
            return [s for s in suggestions if s.priority in ['critical', 'high', 'medium']]

    def _calculate_quality_improvement(self, contexts: List[RefactoringContext]) -> float:
        """计算质量改进分数"""
        if not contexts:
            return 0.0
        
        improvement_scores = []
        for ctx in contexts:
            if ctx.validation_passed:
                before_complexity = ctx.complexity_before.get('max_complexity', 0)
                after_complexity = ctx.complexity_after.get('max_complexity', 0)
                
                if before_complexity > 0:
                    improvement = (before_complexity - after_complexity) / before_complexity * 100
                    improvement_scores.append(max(0, improvement))
                
                improvement_scores.append(len(ctx.improvements) * 5)
        
        return sum(improvement_scores) / len(contexts) if improvement_scores else 0.0

    def _calculate_complexity_reduction(self, contexts: List[RefactoringContext]) -> float:
        """计算复杂度降低百分比"""
        total_before = 0
        total_after = 0
        
        for ctx in contexts:
            total_before += ctx.complexity_before.get('max_complexity', 0)
            total_after += ctx.complexity_after.get('max_complexity', 0)
        
        if total_before == 0:
            return 0.0
        
        return (total_before - total_after) / total_before * 100

    def _generate_recommendations(
        self,
        contexts: List[RefactoringContext],
        quality_improvement: float,
        complexity_reduction: float
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        failed_count = sum(1 for ctx in contexts if not ctx.validation_passed)
        if failed_count > 0:
            recommendations.append(f"有 {failed_count} 个重构失败，建议检查并重试")
        
        if quality_improvement > 20:
            recommendations.append("质量改进显著，建议继续执行优化")
        elif quality_improvement > 10:
            recommendations.append("质量有所改进，建议持续优化")
        elif quality_improvement > 0:
            recommendations.append("质量略有改进，建议加大优化力度")
        else:
            recommendations.append("质量未改进，建议重新评估优化策略")
        
        if complexity_reduction > 30:
            recommendations.append("复杂度显著降低，代码可维护性提升")
        elif complexity_reduction > 15:
            recommendations.append("复杂度有所降低，继续优化可进一步提升")
        
        high_risk_contexts = [ctx for ctx in contexts if len(ctx.risks_identified) > 2]
        if high_risk_contexts:
            recommendations.append(f"发现 {len(high_risk_contexts)} 个高风险重构，建议仔细审查")
        
        if not recommendations:
            recommendations.append("优化效果良好，建议定期执行以保持代码质量")
        
        return recommendations[:5]

    def _export_result(self, result: XingbuRefactoringResult, output_dir: Path):
        """导出结果"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = output_dir / f"xingbu_refactoring_{result.cycle_id}.json"
        
        report_data = {
            'cycle_id': result.cycle_id,
            'timestamp': result.timestamp,
            'phase': result.phase.value,
            'mode': result.mode.value,
            'suggestions_generated': result.suggestions_generated,
            'refactorings_executed': result.refactorings_executed,
            'refactorings_successful': result.refactorings_successful,
            'refactorings_rolled_back': result.refactorings_rolled_back,
            'quality_improvement': result.quality_improvement,
            'complexity_reduction': result.complexity_reduction,
            'details': result.details,
            'recommendations': result.recommendations
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)

    def get_xingbu_refactoring_history(self) -> List[XingbuRefactoringResult]:
        """获取刑部重构历史"""
        return self._results.copy()

    def get_current_phase(self) -> XingbuRefactoringPhase:
        """获取当前阶段"""
        return self._current_phase

    def rollback_last_cycle(self, reason: str = "用户请求回滚") -> bool:
        """回滚最后一个周期"""
        if not self._results:
            return False
        
        last_result = self._results[-1]
        rolled_back = []
        
        for context_data in last_result.details.get('contexts', []):
            refactoring_id = context_data['refactoring_id']
            success = self.optimizer.safe_executor.rollback_refactoring(refactoring_id, reason)
            rolled_back.append(success)
        
        return all(rolled_back) if rolled_back else False

    def generate_xingbu_report(self) -> Dict[str, Any]:
        """生成刑部重构报告"""
        if not self._results:
            return {'error': '无重构历史记录'}
        
        total_cycles = len(self._results)
        total_refactorings = sum(r.refactorings_executed for r in self._results)
        total_successful = sum(r.refactorings_successful for r in self._results)
        total_rolled_back = sum(r.refactorings_rolled_back for r in self._results)
        
        avg_quality_improvement = sum(r.quality_improvement for r in self._results) / total_cycles
        avg_complexity_reduction = sum(r.complexity_reduction for r in self._results) / total_cycles
        
        success_rate = (total_successful / total_refactorings * 100) if total_refactorings > 0 else 0
        
        return {
            'report_id': f"XINGBU-REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'generated_at': datetime.now().isoformat(),
            'project_path': str(self.project_path),
            'summary': {
                'total_cycles': total_cycles,
                'total_refactorings': total_refactorings,
                'successful_refactorings': total_successful,
                'rolled_back_refactorings': total_rolled_back,
                'success_rate': success_rate,
                'average_quality_improvement': avg_quality_improvement,
                'average_complexity_reduction': avg_complexity_reduction
            },
            'recent_cycles': [
                {
                    'cycle_id': r.cycle_id,
                    'timestamp': r.timestamp,
                    'mode': r.mode.value,
                    'success_rate': (r.refactorings_successful / r.refactorings_executed * 100) 
                                   if r.refactorings_executed > 0 else 0,
                    'quality_improvement': r.quality_improvement
                }
                for r in self._results[-10:]
            ],
            'recommendations': self._generate_global_recommendations()
        }

    def _generate_global_recommendations(self) -> List[str]:
        """生成全局建议"""
        recommendations = []
        
        if self._results:
            latest = self._results[-1]
            
            if latest.refactorings_rolled_back > latest.refactorings_successful:
                recommendations.append("最近周期回滚率较高，建议检查重构策略")
            
            if latest.quality_improvement < 5:
                recommendations.append("质量改进不明显，建议调整优化策略")
            
            success_rate = (latest.refactorings_successful / latest.refactorings_executed * 100) \
                          if latest.refactorings_executed > 0 else 0
            if success_rate < 70:
                recommendations.append("成功率较低，建议使用保守模式")
        
        if not recommendations:
            recommendations.append("刑部重构流程运行良好，建议持续执行")
        
        return recommendations


def create_xingbu_integrator(
    project_path: Path,
    mode: str = "balanced",
    auto_apply: bool = False,
    max_refactorings: int = 10
) -> XingbuRefactoringIntegrator:
    """创建刑部重构集成器的便捷函数"""
    mode_mapping = {
        'conservative': XingbuRefactoringMode.CONSERVATIVE,
        'balanced': XingbuRefactoringMode.BALANCED,
        'aggressive': XingbuRefactoringMode.AGGRESSIVE
    }
    
    config = XingbuRefactoringConfig(
        mode=mode_mapping.get(mode, XingbuRefactoringMode.BALANCED),
        auto_apply=auto_apply,
        max_refactorings_per_cycle=max_refactorings
    )
    
    return XingbuRefactoringIntegrator(project_path, config)
