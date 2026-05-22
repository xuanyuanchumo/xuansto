#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动学习主控制器 - Auto Learner

整合模式识别、最佳实践提取、知识库更新和知识应用的完整自动学习系统。

核心功能:
- 自动学习流程管理
- 多组件协调
- 学习任务调度
- 学习效果评估
- 学习报告生成
"""

import json
import logging
import threading
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .pattern_recognizer import (
    PatternRecognizer,
    PatternType,
    PatternConfidence,
    RecognizedPattern
)

from .best_practice_extractor import (
    BestPracticeExtractor,
    PracticeCategory,
    PracticeQuality,
    ExtractedPractice
)

from .knowledge_updater import (
    KnowledgeUpdater,
    KnowledgeCategory,
    KnowledgeQuality,
    KnowledgeEntry,
    UpdateStrategy
)

from .knowledge_application_engine import (
    KnowledgeApplicationEngine,
    ApplicationContext,
    ApplicationSuggestion,
    ApplicationResult,
    FeedbackType
)


class LearningMode(Enum):
    """学习模式枚举"""
    PASSIVE = "passive"
    ACTIVE = "active"
    AGGRESSIVE = "aggressive"
    CUSTOM = "custom"


class LearningStatus(Enum):
    """学习状态枚举"""
    IDLE = "idle"
    LEARNING = "learning"
    EXTRACTING = "extracting"
    UPDATING = "updating"
    APPLYING = "applying"


@dataclass
class LearningTask:
    """学习任务数据类"""
    task_id: str
    task_type: str
    priority: int
    data: Dict[str, Any]
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@dataclass
class LearningReport:
    """学习报告数据类"""
    report_id: str
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    patterns_recognized: int
    practices_extracted: int
    knowledge_updated: int
    applications_tracked: int
    feedbacks_collected: int
    effectiveness_score: float
    recommendations: List[str]
    statistics: Dict[str, Any]


class AutoLearner:
    """自动学习主控制器"""
    
    def __init__(
        self,
        storage_dir: Optional[str] = None,
        learning_mode: LearningMode = LearningMode.ACTIVE
    ):
        self._storage_dir = Path(storage_dir) if storage_dir else None
        self._learning_mode = learning_mode
        self._logger = logging.getLogger('AutoLearner')
        self._lock = threading.Lock()
        
        if self._storage_dir:
            self._storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._pattern_recognizer = PatternRecognizer(
            storage_path=str(self._storage_dir / "patterns.json") if self._storage_dir else None
        )
        
        self._practice_extractor = BestPracticeExtractor(
            pattern_recognizer=self._pattern_recognizer,
            storage_path=str(self._storage_dir / "practices.json") if self._storage_dir else None
        )
        
        self._knowledge_updater = KnowledgeUpdater(
            storage_path=str(self._storage_dir / "knowledge.json") if self._storage_dir else None
        )
        
        self._application_engine = KnowledgeApplicationEngine(
            knowledge_updater=self._knowledge_updater,
            storage_path=str(self._storage_dir / "applications.json") if self._storage_dir else None
        )
        
        self._status = LearningStatus.IDLE
        self._task_queue: List[LearningTask] = []
        self._learning_history: List[Dict[str, Any]] = []
        
        self._mode_configs = self._initialize_mode_configs()
    
    def _initialize_mode_configs(self) -> Dict[LearningMode, Dict[str, Any]]:
        """初始化模式配置"""
        return {
            LearningMode.PASSIVE: {
                "pattern_threshold": 0.9,
                "practice_threshold": 0.8,
                "auto_extract": False,
                "auto_apply": False,
                "min_occurrences": 10
            },
            LearningMode.ACTIVE: {
                "pattern_threshold": 0.8,
                "practice_threshold": 0.7,
                "auto_extract": True,
                "auto_apply": False,
                "min_occurrences": 5
            },
            LearningMode.AGGRESSIVE: {
                "pattern_threshold": 0.6,
                "practice_threshold": 0.6,
                "auto_extract": True,
                "auto_apply": True,
                "min_occurrences": 2
            },
            LearningMode.CUSTOM: {
                "pattern_threshold": 0.75,
                "practice_threshold": 0.7,
                "auto_extract": True,
                "auto_apply": False,
                "min_occurrences": 3
            }
        }
    
    def learn_from_execution(
        self,
        execution_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """从执行中学习
        
        Args:
            execution_data: 执行数据
            context: 上下文信息
        
        Returns:
            学习结果
        """
        self._status = LearningStatus.LEARNING
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "patterns": [],
            "practices": [],
            "knowledge": [],
            "status": "success"
        }
        
        try:
            status = execution_data.get('status', 'unknown')
            
            if status in ['success', 'completed', 'passed']:
                pattern = self._pattern_recognizer.recognize_success_pattern(
                    execution_data,
                    context
                )
                
                if pattern:
                    result["patterns"].append(pattern.to_dict())
                    
                    config = self._mode_configs[self._learning_mode]
                    
                    if config["auto_extract"] and pattern.occurrences >= config["min_occurrences"]:
                        practice = self._practice_extractor.extract_code_practice(
                            pattern,
                            execution_data.get('code_analysis')
                        )
                        
                        if practice:
                            result["practices"].append(practice.to_dict())
                            
                            knowledge = self._knowledge_updater.add_knowledge({
                                "title": practice.title,
                                "content": practice.to_dict(),
                                "category": "practice",
                                "quality_score": practice.quality_score,
                                "tags": practice.tags
                            })
                            
                            result["knowledge"].append(knowledge.to_dict())
            
            elif status in ['failed', 'error', 'timeout']:
                error_info = execution_data.get('error_info', {})
                
                pattern = self._pattern_recognizer.recognize_failure_pattern(
                    execution_data,
                    error_info,
                    context
                )
                
                if pattern:
                    result["patterns"].append(pattern.to_dict())
                    
                    knowledge = self._knowledge_updater.add_knowledge({
                        "title": f"失败教训: {pattern.name}",
                        "content": {
                            "pattern": pattern.to_dict(),
                            "lesson": pattern.description
                        },
                        "category": "lesson",
                        "quality_score": pattern.confidence_score,
                        "tags": pattern.tags + ["failure", "lesson"]
                    })
                    
                    result["knowledge"].append(knowledge.to_dict())
            
            self._learning_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "execution",
                "result": result
            })
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._logger.error(f"学习失败: {e}")
        
        finally:
            self._status = LearningStatus.IDLE
        
        return result
    
    def learn_from_optimization(
        self,
        before_data: Dict[str, Any],
        after_data: Dict[str, Any],
        optimization_type: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """从优化中学习
        
        Args:
            before_data: 优化前数据
            after_data: 优化后数据
            optimization_type: 优化类型
            context: 上下文信息
        
        Returns:
            学习结果
        """
        self._status = LearningStatus.LEARNING
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "patterns": [],
            "practices": [],
            "knowledge": [],
            "status": "success"
        }
        
        try:
            pattern = self._pattern_recognizer.recognize_optimization_pattern(
                before_data,
                after_data,
                optimization_type,
                context
            )
            
            if pattern:
                result["patterns"].append(pattern.to_dict())
                
                config = self._mode_configs[self._learning_mode]
                
                if config["auto_extract"]:
                    practice = self._practice_extractor.extract_architecture_practice(
                        pattern,
                        after_data.get('architecture_analysis')
                    )
                    
                    if practice:
                        result["practices"].append(practice.to_dict())
                        
                        knowledge = self._knowledge_updater.add_knowledge({
                            "title": practice.title,
                            "content": practice.to_dict(),
                            "category": "practice",
                            "quality_score": practice.quality_score,
                            "tags": practice.tags + [optimization_type]
                        })
                        
                        result["knowledge"].append(knowledge.to_dict())
            
            self._learning_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "optimization",
                "result": result
            })
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._logger.error(f"从优化学习失败: {e}")
        
        finally:
            self._status = LearningStatus.IDLE
        
        return result
    
    def apply_knowledge(
        self,
        context: ApplicationContext,
        auto_apply: bool = False
    ) -> Dict[str, Any]:
        """应用知识
        
        Args:
            context: 应用上下文
            auto_apply: 是否自动应用
        
        Returns:
            应用结果
        """
        self._status = LearningStatus.APPLYING
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "suggestions": [],
            "applied": [],
            "status": "success"
        }
        
        try:
            suggestions = self._application_engine.generate_suggestions(context)
            
            result["suggestions"] = [s.to_dict() for s in suggestions]
            
            config = self._mode_configs[self._learning_mode]
            
            if auto_apply or config["auto_apply"]:
                for suggestion in suggestions[:3]:
                    if suggestion.applicability_score > 0.7:
                        applied_result = self._application_engine.track_application_effect(
                            suggestion.suggestion_id,
                            context.current_state,
                            context.current_state
                        )
                        
                        result["applied"].append(applied_result.to_dict())
            
            self._learning_history.append({
                "timestamp": datetime.now().isoformat(),
                "type": "application",
                "result": result
            })
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            self._logger.error(f"应用知识失败: {e}")
        
        finally:
            self._status = LearningStatus.IDLE
        
        return result
    
    def collect_feedback(
        self,
        knowledge_id: str,
        result_id: Optional[str],
        rating: int,
        comment: str,
        feedback_type: str = "neutral"
    ) -> Dict[str, Any]:
        """收集反馈
        
        Args:
            knowledge_id: 知识ID
            result_id: 结果ID
            rating: 评分
            comment: 评论
            feedback_type: 反馈类型
        
        Returns:
            反馈结果
        """
        try:
            fb_type = FeedbackType(feedback_type)
        except ValueError:
            fb_type = FeedbackType.NEUTRAL
        
        feedback = self._application_engine.collect_feedback(
            knowledge_id=knowledge_id,
            result_id=result_id,
            feedback_type=fb_type,
            rating=rating,
            comment=comment
        )
        
        return {
            "status": "success",
            "feedback_id": feedback.feedback_id,
            "timestamp": feedback.created_at.isoformat()
        }
    
    def generate_learning_report(
        self,
        period_days: int = 7
    ) -> LearningReport:
        """生成学习报告
        
        Args:
            period_days: 报告周期（天）
        
        Returns:
            学习报告
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(days=period_days)
        
        period_history = [
            h for h in self._learning_history
            if datetime.fromisoformat(h["timestamp"]) >= start_time
        ]
        
        patterns_recognized = sum(
            len(h["result"].get("patterns", []))
            for h in period_history
        )
        
        practices_extracted = sum(
            len(h["result"].get("practices", []))
            for h in period_history
        )
        
        knowledge_updated = sum(
            len(h["result"].get("knowledge", []))
            for h in period_history
        )
        
        app_stats = self._application_engine.get_statistics()
        
        pattern_stats = self._pattern_recognizer.get_statistics()
        practice_stats = self._practice_extractor.get_statistics()
        knowledge_stats = self._knowledge_updater.get_statistics()
        
        effectiveness_score = (
            pattern_stats.get("avg_confidence_score", 0) * 0.3 +
            practice_stats.get("avg_quality_score", 0) * 0.3 +
            knowledge_stats.get("avg_quality_score", 0) * 0.2 +
            app_stats.get("avg_effectiveness", 0) * 0.2
        )
        
        recommendations = self._generate_recommendations(
            pattern_stats,
            practice_stats,
            knowledge_stats,
            app_stats
        )
        
        report = LearningReport(
            report_id=f"REPORT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            generated_at=datetime.now(),
            period_start=start_time,
            period_end=end_time,
            patterns_recognized=patterns_recognized,
            practices_extracted=practices_extracted,
            knowledge_updated=knowledge_updated,
            applications_tracked=app_stats["total_results"],
            feedbacks_collected=app_stats["total_feedbacks"],
            effectiveness_score=effectiveness_score,
            recommendations=recommendations,
            statistics={
                "patterns": pattern_stats,
                "practices": practice_stats,
                "knowledge": knowledge_stats,
                "applications": app_stats
            }
        )
        
        return report
    
    def _generate_recommendations(
        self,
        pattern_stats: Dict[str, Any],
        practice_stats: Dict[str, Any],
        knowledge_stats: Dict[str, Any],
        app_stats: Dict[str, Any]
    ) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if pattern_stats.get("avg_confidence_score", 0) < 0.7:
            recommendations.append("建议增加学习样本数量以提高模式识别准确性")
        
        if practice_stats.get("verified_count", 0) < practice_stats.get("total_practices", 0) * 0.3:
            recommendations.append("建议加强最佳实践的验证工作")
        
        if knowledge_stats.get("avg_success_rate", 0) < 0.6:
            recommendations.append("建议优化知识库质量，移除低效知识")
        
        if app_stats.get("avg_effectiveness", 0) < 0.5:
            recommendations.append("建议改进知识应用策略，提高应用效果")
        
        if app_stats.get("total_feedbacks", 0) < app_stats.get("total_results", 0) * 0.5:
            recommendations.append("建议增加反馈收集频率，以便持续改进")
        
        if not recommendations:
            recommendations.append("学习系统运行良好，继续保持当前学习模式")
        
        return recommendations
    
    def set_learning_mode(self, mode: LearningMode) -> None:
        """设置学习模式
        
        Args:
            mode: 学习模式
        """
        self._learning_mode = mode
        self._logger.info(f"学习模式已切换为: {mode.value}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态
        
        Returns:
            状态信息
        """
        return {
            "status": self._status.value,
            "learning_mode": self._learning_mode.value,
            "task_queue_size": len(self._task_queue),
            "learning_history_size": len(self._learning_history),
            "components": {
                "pattern_recognizer": self._pattern_recognizer.get_statistics(),
                "practice_extractor": self._practice_extractor.get_statistics(),
                "knowledge_updater": self._knowledge_updater.get_statistics(),
                "application_engine": self._application_engine.get_statistics()
            }
        }
    
    def export_learning_data(self, output_path: str) -> str:
        """导出学习数据
        
        Args:
            output_path: 输出路径
        
        Returns:
            导出文件路径
        """
        data = {
            "exported_at": datetime.now().isoformat(),
            "learning_mode": self._learning_mode.value,
            "patterns": [p.to_dict() for p in self._pattern_recognizer._patterns.values()],
            "practices": [p.to_dict() for p in self._practice_extractor._practices.values()],
            "knowledge": [e.to_dict() for e in self._knowledge_updater._entries.values()],
            "learning_history": self._learning_history[-100:]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self._logger.info(f"学习数据已导出到: {output_path}")
        return output_path
    
    def import_learning_data(
        self,
        input_path: str,
        merge: bool = True
    ) -> int:
        """导入学习数据
        
        Args:
            input_path: 输入路径
            merge: 是否合并
        
        Returns:
            导入的项目数量
        """
        with open(input_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        
        if not merge:
            self._pattern_recognizer._patterns.clear()
            self._practice_extractor._practices.clear()
            self._knowledge_updater._entries.clear()
        
        for pattern_data in data.get("patterns", []):
            pattern = RecognizedPattern.from_dict(pattern_data)
            self._pattern_recognizer._patterns[pattern.pattern_id] = pattern
            count += 1
        
        for practice_data in data.get("practices", []):
            practice = ExtractedPractice.from_dict(practice_data)
            self._practice_extractor._practices[practice.practice_id] = practice
            count += 1
        
        for knowledge_data in data.get("knowledge", []):
            knowledge = KnowledgeEntry.from_dict(knowledge_data)
            self._knowledge_updater._entries[knowledge.entry_id] = knowledge
            count += 1
        
        self._logger.info(f"从 {input_path} 导入了 {count} 个学习项目")
        return count
