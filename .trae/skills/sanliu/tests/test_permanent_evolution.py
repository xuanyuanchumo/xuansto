#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三省六部技能永久自演化增强功能测试

测试模块:
1. 技能自身演化测试
2. 路径动态解析测试
3. 子技能与脚本协同测试
4. 可视化监控集成测试
"""

import json
import os
import sys
import tempfile
import time
import unittest
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent / "skillscripts" / "core"))
sys.path.insert(0, str(Path(__file__).parent.parent / "skillscripts" / "utils"))

test_results: List[Dict[str, Any]] = []
failed_tests: List[Dict[str, Any]] = []


def record_result(test_name: str, passed: bool, message: str = "", details: Dict = None):
    result = {
        "test_name": test_name,
        "passed": passed,
        "message": message,
        "details": details or {},
        "timestamp": datetime.now().isoformat()
    }
    test_results.append(result)
    if not passed:
        failed_tests.append(result)
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"  {status}: {test_name} - {message}")


class TestSkillEvolution(unittest.TestCase):
    """技能自身演化测试"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(tempfile.mkdtemp())
        cls.skill_dir = cls.test_dir / "test_skill"
        cls.skill_dir.mkdir(parents=True, exist_ok=True)
        
        (cls.skill_dir / "SKILL.md").write_text("# Test Skill\n\nTest skill for evolution testing.\n")
        
        subskills_dir = cls.skill_dir / "subskills"
        subskills_dir.mkdir(exist_ok=True)
        (subskills_dir / "test_subskill.md").write_text("# Test Subskill\n\nTest subskill content.\n")
        
        scripts_dir = cls.skill_dir / "skillscripts"
        scripts_dir.mkdir(exist_ok=True)
        (scripts_dir / "test_script.py").write_text('"""Test script"""\n\ndef main():\n    return "test"\n')

    def test_01_skill_evolution_manager_init(self):
        """测试 SkillEvolutionManager 初始化"""
        try:
            from skill_evolution_manager import SkillEvolutionManager, ManagerState
            
            manager = SkillEvolutionManager(str(self.skill_dir))
            
            self.assertEqual(manager.state, ManagerState.IDLE)
            self.assertIsNotNone(manager.change_detector)
            self.assertIsNotNone(manager.knowledge)
            self.assertIsNotNone(manager.snapshot_manager)
            self.assertIsNotNone(manager.trigger_manager)
            self.assertIsNotNone(manager.rollback_manager)
            
            record_result(
                "skill_evolution_manager_init",
                True,
                "SkillEvolutionManager 初始化成功"
            )
        except Exception as e:
            record_result(
                "skill_evolution_manager_init",
                False,
                f"初始化失败: {str(e)}"
            )
            raise

    def test_02_skill_content_change_detector(self):
        """测试 SkillContentChangeDetector 变化检测"""
        try:
            from skill_content_change_detector import (
                SkillContentChangeDetector,
                ChangeType,
                FileType
            )
            
            cache_dir = self.test_dir / "cache"
            detector = SkillContentChangeDetector(
                str(self.skill_dir),
                str(cache_dir)
            )
            
            result = detector.detect_changes(incremental=False)
            
            self.assertTrue(result.total_files_scanned > 0)
            
            skill_md = self.skill_dir / "SKILL.md"
            skill_md.write_text("# Test Skill\n\nModified content.\n")
            
            result2 = detector.detect_changes(incremental=True)
            self.assertTrue(result2.has_changes)
            
            modified_files = [f for f in result2.changed_files if f.change_type == ChangeType.MODIFIED]
            self.assertTrue(len(modified_files) > 0)
            
            record_result(
                "skill_content_change_detector",
                True,
                f"检测到 {len(result2.changed_files)} 个文件变化"
            )
        except Exception as e:
            record_result(
                "skill_content_change_detector",
                False,
                f"变化检测失败: {str(e)}"
            )
            raise

    def test_03_skill_evolution_knowledge(self):
        """测试 SkillEvolutionKnowledge 知识积累"""
        try:
            from skill_evolution_knowledge import (
                SkillEvolutionKnowledge,
                EvolutionEvent,
                EvolutionType,
                EvolutionStatus,
                KnowledgeCategory
            )
            
            knowledge_dir = self.test_dir / "knowledge"
            knowledge = SkillEvolutionKnowledge(
                str(self.skill_dir),
                str(knowledge_dir)
            )
            
            event = EvolutionEvent(
                event_id=f"EVT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                evolution_type=EvolutionType.CONTENT_UPDATE,
                status=EvolutionStatus.COMPLETED,
                triggered_at=datetime.now(),
                trigger_reason="测试触发",
                affected_files=[str(self.skill_dir / "SKILL.md")],
                changes_summary="测试变更"
            )
            
            event_id = knowledge.record_evolution(event)
            self.assertIsNotNone(event_id)
            
            stats = knowledge.get_statistics()
            self.assertTrue(stats["total_events"] > 0)
            
            search_result = knowledge.search_knowledge("测试")
            self.assertIsNotNone(search_result)
            
            record_result(
                "skill_evolution_knowledge",
                True,
                f"知识积累成功，总事件数: {stats['total_events']}"
            )
        except Exception as e:
            record_result(
                "skill_evolution_knowledge",
                False,
                f"知识积累测试失败: {str(e)}"
            )
            raise

    def test_04_evolution_trigger_mechanism(self):
        """测试演化触发机制"""
        try:
            from skill_evolution_manager import (
                SkillEvolutionManager,
                TriggerType,
                TriggerCondition,
                EvolutionPriority
            )
            
            manager = SkillEvolutionManager(str(self.skill_dir))
            
            conditions = manager.trigger_manager.get_all_conditions()
            self.assertTrue(len(conditions) > 0)
            
            custom_condition = TriggerCondition(
                condition_id="test_custom",
                name="测试触发条件",
                description="自定义测试触发条件",
                trigger_type=TriggerType.MANUAL,
                enabled=True,
                priority=EvolutionPriority.HIGH
            )
            manager.add_custom_trigger(custom_condition)
            
            condition = manager.trigger_manager.get_condition("test_custom")
            self.assertIsNotNone(condition)
            self.assertEqual(condition.name, "测试触发条件")
            
            record_result(
                "evolution_trigger_mechanism",
                True,
                f"触发条件数量: {len(manager.trigger_manager.get_all_conditions())}"
            )
        except Exception as e:
            record_result(
                "evolution_trigger_mechanism",
                False,
                f"触发机制测试失败: {str(e)}"
            )
            raise


class TestEnhancedPathConfig(unittest.TestCase):
    """路径动态解析测试"""

    @classmethod
    def setUpClass(cls):
        cls.test_skill_dir = Path(tempfile.mkdtemp()) / "test_skill_path"
        cls.test_skill_dir.mkdir(parents=True, exist_ok=True)
        
        (cls.test_skill_dir / "SKILL.md").write_text("# Test Skill\n")
        
        subskills_dir = cls.test_skill_dir / "subskills"
        subskills_dir.mkdir(exist_ok=True)
        
        scripts_dir = cls.test_skill_dir / "skillscripts"
        scripts_dir.mkdir(exist_ok=True)
        for subdir in ["core", "utils", "test", "analysis"]:
            (scripts_dir / subdir).mkdir(exist_ok=True)

    def test_01_path_config_manager_init(self):
        """测试 EnhancedSkillPathManager 初始化"""
        try:
            from enhanced_path_config_manager import (
                EnhancedSkillPathManager,
                PathKey,
                reset_instance
            )
            
            reset_instance()
            
            manager = EnhancedSkillPathManager(
                skill_root=self.test_skill_dir,
                auto_detect=False,
                lazy_init=True
            )
            
            self.assertEqual(manager.skill_root, self.test_skill_dir)
            self.assertIsNotNone(manager.path_config)
            
            record_result(
                "enhanced_path_config_manager_init",
                True,
                f"路径管理器初始化成功: {manager.skill_root}"
            )
        except Exception as e:
            record_result(
                "enhanced_path_config_manager_init",
                False,
                f"初始化失败: {str(e)}"
            )
            raise

    def test_02_path_resolution(self):
        """测试路径解析功能"""
        try:
            from enhanced_path_config_manager import (
                EnhancedSkillPathManager,
                PathKey,
                reset_instance
            )
            
            reset_instance()
            manager = EnhancedSkillPathManager(
                skill_root=self.test_skill_dir,
                auto_detect=False,
                lazy_init=True
            )
            
            skill_md_path = manager.resolve_path(PathKey.SKILL_MD)
            self.assertEqual(skill_md_path, self.test_skill_dir / "SKILL.md")
            
            subskills_path = manager.resolve_path(PathKey.SUBSKILLS_DIR)
            self.assertEqual(subskills_path, self.test_skill_dir / "subskills")
            
            scripts_path = manager.resolve_path(PathKey.SCRIPTS_DIR)
            self.assertEqual(scripts_path, self.test_skill_dir / "skillscripts")
            
            record_result(
                "path_resolution",
                True,
                "路径解析功能正常"
            )
        except Exception as e:
            record_result(
                "path_resolution",
                False,
                f"路径解析失败: {str(e)}"
            )
            raise

    def test_03_env_override(self):
        """测试环境变量覆盖功能"""
        try:
            from enhanced_path_config_manager import (
                EnhancedSkillPathManager,
                PathKey,
                EnvironmentVariableManager,
                reset_instance
            )
            
            reset_instance()
            
            override_path = str(self.test_skill_dir / "custom_subskills")
            os.environ["SANLIU_SUBSKILLS_DIR"] = override_path
            
            manager = EnhancedSkillPathManager(
                skill_root=self.test_skill_dir,
                auto_detect=False,
                lazy_init=True
            )
            
            resolved_path = manager.resolve_path(PathKey.SUBSKILLS_DIR)
            
            del os.environ["SANLIU_SUBSKILLS_DIR"]
            
            self.assertEqual(str(resolved_path), override_path)
            
            record_result(
                "env_override",
                True,
                f"环境变量覆盖成功: {override_path}"
            )
        except Exception as e:
            record_result(
                "env_override",
                False,
                f"环境变量覆盖失败: {str(e)}"
            )
            raise

    def test_04_path_validation(self):
        """测试路径验证功能"""
        try:
            from enhanced_path_config_manager import (
                EnhancedSkillPathManager,
                PathKey,
                reset_instance
            )
            
            reset_instance()
            manager = EnhancedSkillPathManager(
                skill_root=self.test_skill_dir,
                auto_detect=False,
                lazy_init=True
            )
            
            valid, error = manager.validate_path(PathKey.SKILL_MD)
            self.assertTrue(valid)
            self.assertIsNone(error)
            
            valid, error = manager.validate_path("nonexistent_path")
            self.assertFalse(valid)
            self.assertIsNotNone(error)
            
            record_result(
                "path_validation",
                True,
                "路径验证功能正常"
            )
        except Exception as e:
            record_result(
                "path_validation",
                False,
                f"路径验证失败: {str(e)}"
            )
            raise


class TestSubskillAndScript(unittest.TestCase):
    """子技能与脚本协同测试"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(tempfile.mkdtemp())
        cls.skill_dir = cls.test_dir / "test_skill"
        cls.skill_dir.mkdir(parents=True, exist_ok=True)
        
        subskills_dir = cls.skill_dir / "subskills"
        subskills_dir.mkdir(exist_ok=True)
        
        test_subskill_content = """---
name: test_subskill
version: 1.0.0
description: Test subskill for testing
category: testing
tags: [test, demo]
---

# Test Subskill

This is a test subskill.

## Commands

```bash
echo "Hello from test subskill"
```

## Templates

Reference: template.md
"""
        (subskills_dir / "test_subskill.md").write_text(test_subskill_content)
        
        scripts_dir = cls.skill_dir / "skillscripts"
        scripts_dir.mkdir(exist_ok=True)
        
        core_dir = scripts_dir / "core"
        core_dir.mkdir(exist_ok=True)

    def test_01_subskill_manager_discovery(self):
        """测试 SubskillManager 发现子技能"""
        try:
            from subskill_manager import SubskillManager, SubskillState, reset_instance
            
            reset_instance()
            manager = SubskillManager(base_path=self.skill_dir)
            
            discovered = manager.discover_subskills(incremental=False)
            
            self.assertTrue(len(discovered) >= 0)
            
            record_result(
                "subskill_manager_discovery",
                True,
                f"发现 {len(discovered)} 个子技能"
            )
        except Exception as e:
            record_result(
                "subskill_manager_discovery",
                False,
                f"子技能发现失败: {str(e)}"
            )
            raise

    def test_02_subskill_parser(self):
        """测试子技能解析"""
        try:
            from subskill_manager import SubskillParser
            
            parser = SubskillParser()
            
            test_content = """---
name: parser_test
version: 2.0.0
description: Parser test
---

# Parser Test

## Section 1
Content for section 1.

## Commands
```bash
test command
```
"""
            
            info = parser.parse_subskill_content(
                test_content,
                self.skill_dir / "test.md"
            )
            
            self.assertEqual(info.name, "parser_test")
            self.assertEqual(info.version, "2.0.0")
            self.assertTrue(len(info.sections) > 0)
            self.assertTrue(len(info.commands) > 0)
            
            record_result(
                "subskill_parser",
                True,
                f"解析成功: {info.name}, 版本: {info.version}"
            )
        except Exception as e:
            record_result(
                "subskill_parser",
                False,
                f"子技能解析失败: {str(e)}"
            )
            raise

    def test_03_script_registry(self):
        """测试 ScriptRegistry 注册功能"""
        try:
            from script_registry import (
                ScriptRegistry,
                ScriptCategory,
                ScriptState,
                get_registry
            )
            
            registry = ScriptRegistry(base_path=self.skill_dir / "skillscripts")
            
            result = registry.register(
                name="test_script",
                version="1.0.0",
                description="Test script",
                category=ScriptCategory.UTILITY,
                dependencies=[]
            )
            
            self.assertTrue(result)
            
            script_info = registry.get_script("test_script")
            self.assertIsNotNone(script_info)
            self.assertEqual(script_info.metadata.name, "test_script")
            
            record_result(
                "script_registry",
                True,
                f"脚本注册成功: test_script"
            )
        except Exception as e:
            record_result(
                "script_registry",
                False,
                f"脚本注册失败: {str(e)}"
            )
            raise

    def test_04_cross_type_call(self):
        """测试跨类型调用功能"""
        try:
            from script_registry import (
                ScriptRegistry,
                ScriptCategory,
                CallChainTracker,
                CallStatus
            )
            
            tracker = CallChainTracker()
            
            call_id = tracker.start_call(
                caller_type="script",
                caller_name="test_caller",
                callee_type="subskill",
                callee_name="test_callee"
            )
            
            self.assertIsNotNone(call_id)
            
            node = tracker.end_call(call_id, CallStatus.SUCCESS)
            self.assertIsNotNone(node)
            self.assertEqual(node.status, CallStatus.SUCCESS)
            
            stats = tracker.get_statistics()
            self.assertEqual(stats["total_calls"], 1)
            
            record_result(
                "cross_type_call",
                True,
                f"跨类型调用成功: {call_id}"
            )
        except Exception as e:
            record_result(
                "cross_type_call",
                False,
                f"跨类型调用失败: {str(e)}"
            )
            raise

    def test_05_call_chain_trace(self):
        """测试调用链追踪功能"""
        try:
            from script_registry import (
                CallChainTracker,
                CallStatus
            )
            
            tracker = CallChainTracker()
            
            call_ids = []
            for i in range(3):
                call_id = tracker.start_call(
                    caller_type="script",
                    caller_name=f"caller_{i}",
                    callee_type="subskill",
                    callee_name=f"callee_{i}"
                )
                call_ids.append(call_id)
                tracker.end_call(call_id, CallStatus.SUCCESS)
            
            chain = tracker.get_call_chain()
            self.assertEqual(len(chain), 3)
            
            graph = tracker.generate_call_chain_graph()
            self.assertEqual(graph["total_calls"], 3)
            
            record_result(
                "call_chain_trace",
                True,
                f"调用链追踪成功，共 {len(chain)} 个调用"
            )
        except Exception as e:
            record_result(
                "call_chain_trace",
                False,
                f"调用链追踪失败: {str(e)}"
            )
            raise


class TestHeartbeatMechanism(unittest.TestCase):
    """心跳机制测试"""

    @classmethod
    def setUpClass(cls):
        cls.test_dir = Path(tempfile.mkdtemp())
        cls.skill_dir = cls.test_dir / "test_skill"
        cls.skill_dir.mkdir(parents=True, exist_ok=True)
        
        (cls.skill_dir / "SKILL.md").write_text("# Test Skill\n\nTest skill for heartbeat testing.\n")

    def test_01_heartbeat_info_creation(self):
        """测试 HeartbeatInfo 数据结构创建"""
        try:
            from continuous_evolution_controller import HeartbeatInfo, EvolutionState
            
            heartbeat = HeartbeatInfo(
                heartbeat_id="HB-20260401120000",
                timestamp=datetime.now(),
                state=EvolutionState.IDLE,
                active_tasks=0,
                queue_size=0,
                memory_usage_mb=50.5,
                cpu_usage_percent=25.3,
                uptime_seconds=3600.0
            )
            
            self.assertEqual(heartbeat.heartbeat_id, "HB-20260401120000")
            self.assertEqual(heartbeat.state, EvolutionState.IDLE)
            self.assertEqual(heartbeat.active_tasks, 0)
            self.assertEqual(heartbeat.queue_size, 0)
            self.assertTrue(heartbeat.memory_usage_mb > 0)
            self.assertTrue(heartbeat.cpu_usage_percent >= 0)
            self.assertTrue(heartbeat.uptime_seconds >= 0)
            
            heartbeat_dict = heartbeat.to_dict()
            self.assertIn("heartbeat_id", heartbeat_dict)
            self.assertIn("timestamp", heartbeat_dict)
            self.assertIn("state", heartbeat_dict)
            
            record_result(
                "heartbeat_info_creation",
                True,
                f"HeartbeatInfo 创建成功: {heartbeat.heartbeat_id}"
            )
        except Exception as e:
            record_result(
                "heartbeat_info_creation",
                False,
                f"HeartbeatInfo 创建失败: {str(e)}"
            )
            raise

    def test_02_evolution_controller_heartbeat(self):
        """测试 EvolutionController 心跳功能"""
        try:
            from continuous_evolution_controller import EvolutionController, EvolutionConfig
            
            config = EvolutionConfig(
                perpetual_mode=False,
                heartbeat_interval_seconds=5,
                state_persistence_enabled=False
            )
            
            controller = EvolutionController(config=config, project_dir=str(self.skill_dir))
            
            status = controller.get_status()
            self.assertIsNotNone(status)
            self.assertIn("running", status)
            self.assertIn("current_state", status)
            
            record_result(
                "evolution_controller_heartbeat",
                True,
                f"控制器状态获取成功: {status['current_state']}"
            )
        except Exception as e:
            record_result(
                "evolution_controller_heartbeat",
                False,
                f"控制器心跳测试失败: {str(e)}"
            )
            raise

    def test_03_heartbeat_send(self):
        """测试心跳发送功能"""
        try:
            from continuous_evolution_controller import EvolutionController, EvolutionConfig, HeartbeatInfo
            
            config = EvolutionConfig(
                perpetual_mode=False,
                heartbeat_interval_seconds=5,
                state_persistence_enabled=False
            )
            
            controller = EvolutionController(config=config, project_dir=str(self.skill_dir))
            
            heartbeat = controller._send_heartbeat()
            
            self.assertIsNotNone(heartbeat)
            self.assertIsInstance(heartbeat, HeartbeatInfo)
            self.assertIsNotNone(heartbeat.heartbeat_id)
            self.assertIsNotNone(heartbeat.timestamp)
            self.assertIsNotNone(heartbeat.state)
            
            record_result(
                "heartbeat_send",
                True,
                f"心跳发送成功: {heartbeat.heartbeat_id}"
            )
        except Exception as e:
            record_result(
                "heartbeat_send",
                False,
                f"心跳发送失败: {str(e)}"
            )
            raise

    def test_04_heartbeat_info_retrieval(self):
        """测试心跳信息获取"""
        try:
            from continuous_evolution_controller import EvolutionController, EvolutionConfig
            
            config = EvolutionConfig(
                perpetual_mode=False,
                heartbeat_interval_seconds=5,
                state_persistence_enabled=False
            )
            
            controller = EvolutionController(config=config, project_dir=str(self.skill_dir))
            
            heartbeat_info = controller.get_heartbeat_info()
            
            self.assertIsNone(heartbeat_info)
            
            record_result(
                "heartbeat_info_retrieval",
                True,
                "心跳信息获取功能正常（控制器未运行时返回 None）"
            )
        except Exception as e:
            record_result(
                "heartbeat_info_retrieval",
                False,
                f"心跳信息获取失败: {str(e)}"
            )
            raise

    def test_05_heartbeat_persistence(self):
        """测试心跳持久化"""
        try:
            from continuous_evolution_controller import (
                EvolutionController,
                EvolutionConfig,
                EvolutionStatePersistence,
                PersistentState,
                HealthStatus
            )
            
            state_file = self.test_dir / "heartbeat_state.json"
            persistence = EvolutionStatePersistence(str(state_file))
            
            initial_state = persistence.create_initial_state()
            initial_state.last_heartbeat = datetime.now()
            initial_state.health_status = HealthStatus.HEALTHY
            
            save_result = persistence.save_state(initial_state)
            self.assertTrue(save_result)
            
            loaded_state = persistence.load_state()
            self.assertIsNotNone(loaded_state)
            self.assertEqual(loaded_state.state_id, initial_state.state_id)
            self.assertEqual(loaded_state.health_status, HealthStatus.HEALTHY)
            
            record_result(
                "heartbeat_persistence",
                True,
                f"心跳持久化成功: {loaded_state.state_id}"
            )
        except Exception as e:
            record_result(
                "heartbeat_persistence",
                False,
                f"心跳持久化失败: {str(e)}"
            )
            raise


class TestVisualizationMonitoring(unittest.TestCase):
    """可视化监控集成测试"""

    def test_01_backend_api_response(self):
        """测试后端 API 响应"""
        try:
            from skill_evolution_api import (
                SkillEvolutionStatus,
                EvolutionStatus,
                EvolutionPhase,
                _generate_mock_status,
                _generate_mock_statistics,
                _generate_mock_history
            )
            
            status = _generate_mock_status()
            self.assertIsInstance(status, SkillEvolutionStatus)
            self.assertIsNotNone(status.current_phase)
            
            stats = _generate_mock_statistics()
            self.assertTrue(stats.total_evolutions > 0)
            
            history = _generate_mock_history(0, 10)
            self.assertTrue(history.total > 0)
            
            record_result(
                "backend_api_response",
                True,
                f"API 响应正常，总演化次数: {stats.total_evolutions}"
            )
        except Exception as e:
            record_result(
                "backend_api_response",
                False,
                f"API 响应测试失败: {str(e)}"
            )
            raise

    def test_02_websocket_manager(self):
        """测试 WebSocket 管理器"""
        try:
            from skill_evolution_api import SkillEvolutionManager
            
            manager = SkillEvolutionManager()
            
            state = manager.get_state()
            self.assertIsNotNone(state)
            self.assertIn("is_running", state)
            
            manager.update_state(is_running=True, current_phase="analysis")
            updated_state = manager.get_state()
            self.assertTrue(updated_state["is_running"])
            
            record_result(
                "websocket_manager",
                True,
                "WebSocket 管理器状态管理正常"
            )
        except Exception as e:
            record_result(
                "websocket_manager",
                False,
                f"WebSocket 管理器测试失败: {str(e)}"
            )
            raise

    def test_03_evolution_history(self):
        """测试演化历史记录"""
        try:
            from skill_evolution_api import (
                SkillEvolutionManager,
                _generate_mock_history
            )
            
            manager = SkillEvolutionManager()
            
            history_item = {
                "event_id": f"evt_{int(time.time())}",
                "timestamp": datetime.now().isoformat(),
                "evolution_type": "skill_optimization",
                "trigger_type": "manual",
                "status": "completed",
                "duration_ms": 5000,
                "changes": ["测试变更"]
            }
            manager.add_history_item(history_item)
            
            history = manager.get_history(0, 10)
            self.assertTrue(len(history) > 0)
            
            record_result(
                "evolution_history",
                True,
                f"演化历史记录正常，共 {len(history)} 条记录"
            )
        except Exception as e:
            record_result(
                "evolution_history",
                False,
                f"演化历史测试失败: {str(e)}"
            )
            raise

    def test_04_frontend_component_structure(self):
        """测试前端组件结构"""
        try:
            frontend_path = Path(__file__).parent.parent / "frontend" / "src" / "components" / "evolution"
            
            self.assertTrue(frontend_path.exists(), "前端组件目录不存在")
            
            expected_files = [
                "SkillEvolutionStatus.vue",
                "index.ts"
            ]
            
            found_files = []
            for f in expected_files:
                if (frontend_path / f).exists():
                    found_files.append(f)
            
            self.assertTrue(len(found_files) > 0, "未找到前端组件文件")
            
            record_result(
                "frontend_component_structure",
                True,
                f"前端组件结构正常，找到 {len(found_files)} 个组件"
            )
        except Exception as e:
            record_result(
                "frontend_component_structure",
                False,
                f"前端组件测试失败: {str(e)}"
            )
            raise


def generate_report():
    """生成测试报告"""
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r["passed"])
    failed_count = len(failed_tests)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    report = {
        "report_title": "三省六部技能永久自演化增强功能测试报告",
        "generated_at": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_count,
            "success_rate": round(success_rate, 2)
        },
        "test_results": test_results,
        "failed_tests": failed_tests,
        "recommendations": []
    }
    
    if failed_count > 0:
        for failed in failed_tests:
            report["recommendations"].append({
                "test_name": failed["test_name"],
                "issue": failed["message"],
                "suggestion": f"检查 {failed['test_name']} 相关模块的实现和依赖关系"
            })
    
    report_path = Path(__file__).parent / "reports" / f"evolution_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    md_report_path = report_path.with_suffix('.md')
    md_content = f"""# {report['report_title']}

**生成时间**: {report['generated_at']}

## 测试摘要

| 指标 | 值 |
|------|-----|
| 总测试数 | {total_tests} |
| 通过数 | {passed_tests} |
| 失败数 | {failed_count} |
| 成功率 | {success_rate:.2f}% |

## 测试结果详情

| 测试名称 | 状态 | 消息 |
|----------|------|------|
"""
    
    for result in test_results:
        status = "✓ 通过" if result["passed"] else "✗ 失败"
        md_content += f"| {result['test_name']} | {status} | {result['message']} |\n"
    
    if failed_tests:
        md_content += "\n## 失败测试详情\n\n"
        for failed in failed_tests:
            md_content += f"### {failed['test_name']}\n\n"
            md_content += f"- **错误信息**: {failed['message']}\n"
            md_content += f"- **时间**: {failed['timestamp']}\n\n"
    
    if report["recommendations"]:
        md_content += "\n## 修复建议\n\n"
        for rec in report["recommendations"]:
            md_content += f"### {rec['test_name']}\n\n"
            md_content += f"- **问题**: {rec['issue']}\n"
            md_content += f"- **建议**: {rec['suggestion']}\n\n"
    
    with open(md_report_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return report_path, md_report_path


def run_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("三省六部技能永久自演化增强功能测试")
    print("=" * 60 + "\n")
    
    print("\n[1/5] 技能自身演化测试")
    print("-" * 40)
    suite1 = unittest.TestLoader().loadTestsFromTestCase(TestSkillEvolution)
    unittest.TextTestRunner(verbosity=0).run(suite1)
    
    print("\n[2/5] 路径动态解析测试")
    print("-" * 40)
    suite2 = unittest.TestLoader().loadTestsFromTestCase(TestEnhancedPathConfig)
    unittest.TextTestRunner(verbosity=0).run(suite2)
    
    print("\n[3/5] 子技能与脚本协同测试")
    print("-" * 40)
    suite3 = unittest.TestLoader().loadTestsFromTestCase(TestSubskillAndScript)
    unittest.TextTestRunner(verbosity=0).run(suite3)
    
    print("\n[4/5] 心跳机制测试")
    print("-" * 40)
    suite4 = unittest.TestLoader().loadTestsFromTestCase(TestHeartbeatMechanism)
    unittest.TextTestRunner(verbosity=0).run(suite4)
    
    print("\n[5/5] 可视化监控集成测试")
    print("-" * 40)
    suite5 = unittest.TestLoader().loadTestsFromTestCase(TestVisualizationMonitoring)
    unittest.TextTestRunner(verbosity=0).run(suite5)
    
    print("\n" + "=" * 60)
    print("生成测试报告...")
    print("=" * 60 + "\n")
    
    json_path, md_path = generate_report()
    
    total = len(test_results)
    passed = sum(1 for r in test_results if r["passed"])
    failed = len(failed_tests)
    
    print(f"\n测试完成!")
    print(f"  总测试数: {total}")
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")
    print(f"  成功率: {(passed/total*100):.2f}%" if total > 0 else "  成功率: 0%")
    print(f"\n报告已生成:")
    print(f"  JSON: {json_path}")
    print(f"  Markdown: {md_path}")
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
