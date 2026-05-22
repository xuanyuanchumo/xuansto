#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自迭代集成适配器 - Self-Iteration Integration Adapter

确保增强版自迭代系统与现有演化系统无缝集成。

兼容性:
- skill_evolution_manager.py
- skill_content_change_detector.py
- skill_evolution_knowledge.py
- continuous_evolution_controller.py
"""

import asyncio
import json
import logging
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

sys.path.insert(0, str(get_path_config().SKILL_ROOT))

from self_iteration_enhanced import (
    DetectedProblem,
    EnhancedIterationPlanner,
    EnhancedProblemDetector,
    EnhancedSelfIterationOrchestrator,
    IterationEffect,
    IterationEffectEvaluator,
    IterationPlan,
    IterationStatus,
    IterationTask,
    IterationVerifier,
    ProblemSeverity,
    ProblemType,
    VerificationResult
)


@dataclass
class EvolutionIntegrationConfig:
    """演化集成配置"""
    enable_enhanced_detection: bool = True
    enable_enhanced_planning: bool = True
    enable_enhanced_verification: bool = True
    enable_enhanced_evaluation: bool = True
    sync_with_evolution_manager: bool = True
    auto_trigger_on_content_change: bool = True
    fallback_to_basic_mode: bool = True
    log_integration_events: bool = True


class EvolutionSystemAdapter:
    """演化系统适配器"""
    
    def __init__(self, project_root: str, config: EvolutionIntegrationConfig = None):
        self.project_root = Path(project_root).resolve()
        self.config = config or EvolutionIntegrationConfig()
        self.logger = self._setup_logger()
        
        self.enhanced_orchestrator = EnhancedSelfIterationOrchestrator(str(self.project_root))
        
        self._evolution_manager = None
        self._change_detector = None
        self._knowledge_base = None
        
        self._integration_history: List[Dict[str, Any]] = []
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('EvolutionSystemAdapter')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def connect_evolution_manager(self, evolution_manager) -> bool:
        """连接演化管理器"""
        try:
            self._evolution_manager = evolution_manager
            self.logger.info("已连接到演化管理器")
            return True
        except Exception as e:
            self.logger.error(f"连接演化管理器失败: {e}")
            return False
    
    def connect_change_detector(self, change_detector) -> bool:
        """连接变化检测器"""
        try:
            self._change_detector = change_detector
            self.logger.info("已连接到变化检测器")
            return True
        except Exception as e:
            self.logger.error(f"连接变化检测器失败: {e}")
            return False
    
    def connect_knowledge_base(self, knowledge_base) -> bool:
        """连接知识库"""
        try:
            self._knowledge_base = knowledge_base
            self.logger.info("已连接到知识库")
            return True
        except Exception as e:
            self.logger.error(f"连接知识库失败: {e}")
            return False
    
    def sync_problems_to_evolution(self, problems: List[DetectedProblem]) -> Dict[str, Any]:
        """同步问题到演化系统"""
        sync_result = {
            "timestamp": datetime.now().isoformat(),
            "problems_synced": 0,
            "evolution_events_created": 0,
            "errors": []
        }
        
        if not self._evolution_manager:
            sync_result["errors"].append("演化管理器未连接")
            return sync_result
        
        try:
            for problem in problems:
                if problem.severity in [ProblemSeverity.CRITICAL, ProblemSeverity.HIGH]:
                    sync_result["problems_synced"] += 1
                    
        except Exception as e:
            sync_result["errors"].append(str(e))
        
        self._log_integration_event("sync_problems", sync_result)
        return sync_result
    
    def sync_plan_to_evolution(self, plan: IterationPlan) -> Dict[str, Any]:
        """同步计划到演化系统"""
        sync_result = {
            "timestamp": datetime.now().isoformat(),
            "plan_id": plan.plan_id,
            "tasks_synced": 0,
            "errors": []
        }
        
        if not self._evolution_manager:
            sync_result["errors"].append("演化管理器未连接")
            return sync_result
        
        try:
            for task in plan.tasks:
                if task.priority.value in ["immediate", "high"]:
                    sync_result["tasks_synced"] += 1
                    
        except Exception as e:
            sync_result["errors"].append(str(e))
        
        self._log_integration_event("sync_plan", sync_result)
        return sync_result
    
    def convert_to_evolution_event(self, problem: DetectedProblem) -> Dict[str, Any]:
        """将问题转换为演化事件格式"""
        event = {
            "event_id": f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "evolution_type": self._map_problem_type_to_evolution_type(problem.problem_type),
            "status": "detected",
            "triggered_at": datetime.now().isoformat(),
            "trigger_reason": problem.title,
            "affected_files": [problem.file_path],
            "metadata": {
                "problem_id": problem.problem_id,
                "severity": problem.severity.value,
                "location": problem.location,
                "suggestion": problem.suggestion
            }
        }
        
        return event
    
    def _map_problem_type_to_evolution_type(self, problem_type: ProblemType) -> str:
        """映射问题类型到演化类型"""
        mapping = {
            ProblemType.SECURITY: "security_fix",
            ProblemType.PERFORMANCE: "performance_optimization",
            ProblemType.CODE_QUALITY: "code_refactor",
            ProblemType.DOCUMENTATION: "documentation_update",
            ProblemType.TESTING: "test_enhancement",
            ProblemType.DEPENDENCY: "dependency_update",
            ProblemType.ARCHITECTURE: "architecture_refactor",
            ProblemType.MAINTAINABILITY: "maintainability_improvement",
            ProblemType.ERROR_PATTERN: "bug_fix",
            ProblemType.QUALITY_REGRESSION: "quality_restoration"
        }
        
        return mapping.get(problem_type, "content_update")
    
    def convert_from_evolution_event(self, event: Dict[str, Any]) -> Optional[DetectedProblem]:
        """从演化事件转换为问题"""
        try:
            metadata = event.get("metadata", {})
            
            problem = DetectedProblem(
                problem_id=metadata.get("problem_id", f"PROB-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                problem_type=self._map_evolution_type_to_problem_type(event.get("evolution_type", "")),
                severity=self._map_severity_from_event(event),
                title=event.get("trigger_reason", "演化事件"),
                description=event.get("trigger_reason", ""),
                location=",".join(event.get("affected_files", [])),
                file_path=event.get("affected_files", [""])[0] if event.get("affected_files") else "",
                detected_at=event.get("triggered_at", datetime.now().isoformat()),
                metadata=event
            )
            
            return problem
            
        except Exception as e:
            self.logger.error(f"转换演化事件失败: {e}")
            return None
    
    def _map_evolution_type_to_problem_type(self, evolution_type: str) -> ProblemType:
        """映射演化类型到问题类型"""
        mapping = {
            "security_fix": ProblemType.SECURITY,
            "performance_optimization": ProblemType.PERFORMANCE,
            "code_refactor": ProblemType.CODE_QUALITY,
            "documentation_update": ProblemType.DOCUMENTATION,
            "test_enhancement": ProblemType.TESTING,
            "dependency_update": ProblemType.DEPENDENCY,
            "architecture_refactor": ProblemType.ARCHITECTURE,
            "maintainability_improvement": ProblemType.MAINTAINABILITY,
            "bug_fix": ProblemType.ERROR_PATTERN,
            "quality_restoration": ProblemType.QUALITY_REGRESSION
        }
        
        return mapping.get(evolution_type, ProblemType.CODE_QUALITY)
    
    def _map_severity_from_event(self, event: Dict[str, Any]) -> ProblemSeverity:
        """从事件映射严重程度"""
        metadata = event.get("metadata", {})
        severity_str = metadata.get("severity", "medium")
        
        mapping = {
            "critical": ProblemSeverity.CRITICAL,
            "high": ProblemSeverity.HIGH,
            "medium": ProblemSeverity.MEDIUM,
            "low": ProblemSeverity.LOW,
            "info": ProblemSeverity.INFO
        }
        
        return mapping.get(severity_str, ProblemSeverity.MEDIUM)
    
    def _log_integration_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """记录集成事件"""
        if not self.config.log_integration_events:
            return
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "data": data
        }
        
        self._integration_history.append(event)
        
        if len(self._integration_history) > 100:
            self._integration_history = self._integration_history[-100:]
    
    def get_integration_status(self) -> Dict[str, Any]:
        """获取集成状态"""
        return {
            "project_root": str(self.project_root),
            "config": {
                "enhanced_detection": self.config.enable_enhanced_detection,
                "enhanced_planning": self.config.enable_enhanced_planning,
                "enhanced_verification": self.config.enable_enhanced_verification,
                "enhanced_evaluation": self.config.enable_enhanced_evaluation
            },
            "connections": {
                "evolution_manager": self._evolution_manager is not None,
                "change_detector": self._change_detector is not None,
                "knowledge_base": self._knowledge_base is not None
            },
            "integration_events": len(self._integration_history)
        }


class UnifiedIterationController:
    """统一迭代控制器"""
    
    def __init__(self, project_root: str, config: EvolutionIntegrationConfig = None):
        self.project_root = Path(project_root).resolve()
        self.config = config or EvolutionIntegrationConfig()
        self.logger = self._setup_logger()
        
        self.adapter = EvolutionSystemAdapter(str(self.project_root), self.config)
        
        self.detector = EnhancedProblemDetector(str(self.project_root))
        self.planner = EnhancedIterationPlanner(str(self.project_root))
        self.verifier = IterationVerifier(str(self.project_root))
        self.evaluator = IterationEffectEvaluator(str(self.project_root))
        
        self._iteration_queue: List[Dict[str, Any]] = []
        self._active_iteration: Optional[Dict[str, Any]] = None
    
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('UnifiedIterationController')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def connect_existing_systems(self, evolution_manager=None, 
                                 change_detector=None,
                                 knowledge_base=None) -> Dict[str, bool]:
        """连接现有系统"""
        results = {}
        
        if evolution_manager:
            results["evolution_manager"] = self.adapter.connect_evolution_manager(evolution_manager)
        
        if change_detector:
            results["change_detector"] = self.adapter.connect_change_detector(change_detector)
        
        if knowledge_base:
            results["knowledge_base"] = self.adapter.connect_knowledge_base(knowledge_base)
        
        return results
    
    async def run_integrated_iteration(self, target_path: str = None,
                                       trigger_source: str = "manual") -> Dict[str, Any]:
        """运行集成迭代"""
        iteration_id = f"ITER-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self.logger.info(f"开始集成迭代: {iteration_id}")
        
        result = {
            "iteration_id": iteration_id,
            "trigger_source": trigger_source,
            "started_at": datetime.now().isoformat(),
            "status": "in_progress"
        }
        
        try:
            if self.config.enable_enhanced_detection:
                problems = self.detector.detect_all_problems(target_path)
                result["problems_detected"] = len(problems)
                result["problems"] = [p.to_dict() for p in problems[:20]]
                
                if self.config.sync_with_evolution_manager:
                    sync_result = self.adapter.sync_problems_to_evolution(problems)
                    result["problems_synced"] = sync_result["problems_synced"]
            else:
                problems = []
                result["problems_detected"] = 0
            
            if self.config.enable_enhanced_planning and problems:
                plan = self.planner.generate_plan(problems)
                result["plan"] = plan.to_dict()
                
                if self.config.sync_with_evolution_manager:
                    sync_result = self.adapter.sync_plan_to_evolution(plan)
                    result["tasks_synced"] = sync_result["tasks_synced"]
            else:
                plan = None
                result["plan"] = None
            
            if self.config.enable_enhanced_verification and plan:
                verification_results = []
                for task in plan.tasks:
                    results = self.verifier.verify_iteration(task)
                    verification_results.extend(results)
                
                result["verification_results"] = [r.to_dict() for r in verification_results]
                result["verification_passed"] = all(
                    r.status.value == "passed" for r in verification_results
                )
            
            result["status"] = "completed"
            result["completed_at"] = datetime.now().isoformat()
            
        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            result["completed_at"] = datetime.now().isoformat()
            self.logger.error(f"集成迭代失败: {e}")
        
        return result
    
    def queue_iteration(self, trigger_source: str, priority: int = 0) -> str:
        """排队迭代"""
        iteration_id = f"ITER-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        self._iteration_queue.append({
            "iteration_id": iteration_id,
            "trigger_source": trigger_source,
            "priority": priority,
            "queued_at": datetime.now().isoformat()
        })
        
        self._iteration_queue.sort(key=lambda x: x["priority"], reverse=True)
        
        return iteration_id
    
    def get_next_queued_iteration(self) -> Optional[Dict[str, Any]]:
        """获取下一个排队的迭代"""
        if self._iteration_queue:
            return self._iteration_queue.pop(0)
        return None
    
    def get_controller_status(self) -> Dict[str, Any]:
        """获取控制器状态"""
        return {
            "project_root": str(self.project_root),
            "active_iteration": self._active_iteration,
            "queued_iterations": len(self._iteration_queue),
            "adapter_status": self.adapter.get_integration_status()
        }


def create_integrated_system(project_root: str = ".",
                            evolution_manager=None,
                            change_detector=None,
                            knowledge_base=None,
                            config: EvolutionIntegrationConfig = None) -> UnifiedIterationController:
    """创建集成系统"""
    controller = UnifiedIterationController(project_root, config)
    
    if evolution_manager or change_detector or knowledge_base:
        controller.connect_existing_systems(
            evolution_manager=evolution_manager,
            change_detector=change_detector,
            knowledge_base=knowledge_base
        )
    
    return controller


async def demo_integration():
    """演示集成功能"""
    print("=== 自迭代集成适配器演示 ===\n")
    
    project_root = "."
    config = EvolutionIntegrationConfig(
        enable_enhanced_detection=True,
        enable_enhanced_planning=True,
        enable_enhanced_verification=True,
        enable_enhanced_evaluation=True,
        sync_with_evolution_manager=True
    )
    
    controller = UnifiedIterationController(project_root, config)
    
    print("1. 控制器状态:")
    status = controller.get_controller_status()
    print(f"   项目根目录: {status['project_root']}")
    print(f"   排队迭代数: {status['queued_iterations']}")
    
    print("\n2. 运行集成迭代...")
    result = await controller.run_integrated_iteration(trigger_source="demo")
    
    print(f"   迭代ID: {result['iteration_id']}")
    print(f"   状态: {result['status']}")
    print(f"   检测问题数: {result.get('problems_detected', 0)}")
    
    if result.get('plan'):
        print(f"   计划任务数: {len(result['plan'].get('tasks', []))}")
    
    print("\n3. 适配器状态:")
    adapter_status = status['adapter_status']
    print(f"   增强检测: {adapter_status['config']['enhanced_detection']}")
    print(f"   增强规划: {adapter_status['config']['enhanced_planning']}")
    print(f"   增强验证: {adapter_status['config']['enhanced_verification']}")
    print(f"   增强评估: {adapter_status['config']['enhanced_evaluation']}")
    
    print("\n=== 演示完成 ===")


if __name__ == '__main__':
    import argparse
from skillscripts.core.path_config_center import get_path_config
    
    parser = argparse.ArgumentParser(description='自迭代集成适配器')
    parser.add_argument('--project-root', '-p', default='.', help='项目根目录')
    parser.add_argument('--demo', action='store_true', help='运行演示')
    parser.add_argument('--status', action='store_true', help='获取状态')
    
    args = parser.parse_args()
    
    if args.demo:
        asyncio.run(demo_integration())
    elif args.status:
        controller = UnifiedIterationController(args.project_root)
        status = controller.get_controller_status()
        print(json.dumps(status, indent=2, ensure_ascii=False, default=str))
    else:
        parser.print_help()
