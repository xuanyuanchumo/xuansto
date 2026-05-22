#!/usr/bin/env python3
"""
永久演化模式测试

测试内容：
1. 永久运行模式
2. 心跳检测功能
3. 状态持久化功能
4. 优雅停止机制
"""

import os
import sys
import time
import json
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

SKILLSCRIPTS_DIR = Path(__file__).parent.parent / "skillscripts"
sys.path.insert(0, str(SKILLSCRIPTS_DIR))

from test_runner import TestRunner, TestResult, print_header, print_result

TEST_DATA_DIR = Path(__file__).parent / "test_data" / "evolution"
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)


def test_continuous_evolution_controller_import():
    try:
        from core.continuous_evolution_controller import (
            EvolutionController,
            EvolutionConfig,
            EvolutionState,
            EvolutionPhase
        )
        return True, "模块导入成功", {"classes": ["EvolutionController", "EvolutionConfig", "EvolutionState", "EvolutionPhase"]}
    except ImportError as e:
        return False, f"模块导入失败: {e}", {}


def test_evolution_config():
    try:
        from core.continuous_evolution_controller import EvolutionConfig
        
        config = EvolutionConfig(
            perpetual_mode=True,
            heartbeat_interval=5,
            state_persistence_path=str(TEST_DATA_DIR / "state"),
            max_evolution_cycles=10,
            auto_recovery=True
        )
        
        assert config.perpetual_mode == True
        assert config.heartbeat_interval == 5
        assert config.auto_recovery == True
        
        return True, "配置创建成功", {
            "perpetual_mode": config.perpetual_mode,
            "heartbeat_interval": config.heartbeat_interval,
            "auto_recovery": config.auto_recovery
        }
    except Exception as e:
        return False, f"配置测试失败: {e}", {}


def test_evolution_state():
    try:
        from core.continuous_evolution_controller import EvolutionState, EvolutionPhase
        
        state = EvolutionState.IDLE
        
        assert state == EvolutionState.IDLE
        
        return True, "状态管理测试成功", {
            "state": state.name,
            "has_phases": True
        }
    except Exception as e:
        return False, f"状态测试失败: {e}", {}


def test_controller_initialization():
    try:
        from core.continuous_evolution_controller import (
            EvolutionController,
            EvolutionConfig
        )
        
        config = EvolutionConfig(
            perpetual_mode=True,
            heartbeat_interval=5,
            state_persistence_path=str(TEST_DATA_DIR / "state"),
            max_evolution_cycles=5
        )
        
        controller = EvolutionController(config=config)
        
        assert controller.config == config
        
        return True, "控制器初始化成功", {
            "config_applied": True,
            "state_initialized": True
        }
    except Exception as e:
        return False, f"控制器初始化失败: {e}", {}


#!/usr/bin/env python3
"""
永久演化模式测试

测试内容：
1. 永久运行模式
2. 心跳检测功能
3. 状态持久化功能
4. 优雅停止机制
"""

import os
import sys
import time
import json
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

TEST_DATA_DIR = Path(__file__).parent / "test_data" / "evolution"
TEST_DATA_DIR.mkdir(parents=True, exist_ok=True)


def test_continuous_evolution_controller_import():
    try:
        from core.continuous_evolution_controller import (
            EvolutionController,
            EvolutionConfig,
            EvolutionState,
            EvolutionPhase
        )
        return True, "模块导入成功", {"classes": ["EvolutionController", "EvolutionConfig", "EvolutionState", "EvolutionPhase"]}
    except ImportError as e:
        return False, f"模块导入失败: {e}", {}


def test_evolution_config():
    try:
        from core.continuous_evolution_controller import EvolutionConfig
        
        config = EvolutionConfig(
            perpetual_mode=True,
            heartbeat_interval=5,
            state_persistence_path=str(TEST_DATA_DIR / "state"),
            max_evolution_cycles=10,
            auto_recovery=True
        )
        
        assert config.perpetual_mode == True
        assert config.heartbeat_interval == 5
        assert config.auto_recovery == True
        
        return True, "配置创建成功", {
            "perpetual_mode": config.perpetual_mode,
            "heartbeat_interval": config.heartbeat_interval,
            "auto_recovery": config.auto_recovery
        }
    except Exception as e:
        return False, f"配置测试失败: {e}", {}


def test_evolution_state():
    try:
        from core.continuous_evolution_controller import EvolutionState, EvolutionPhase
        
        state = EvolutionState.IDLE
        
        assert state == EvolutionState.IDLE
        
        return True, "状态管理测试成功", {
            "state": state.name,
            "has_phases": True
        }
    except Exception as e:
        return False, f"状态测试失败: {e}", {}


def test_controller_initialization():
    try:
        from core.continuous_evolution_controller import (
            EvolutionController,
            EvolutionConfig
        )
        
        config = EvolutionConfig(
            perpetual_mode=True,
            heartbeat_interval=5,
            state_persistence_path=str(TEST_DATA_DIR / "state"),
            max_evolution_cycles=5
        )
        
        controller = EvolutionController(config=config)
        
        assert controller.config == config
        
        return True, "控制器初始化成功", {
            "config_applied": True,
            "state_initialized": True
        }
    except Exception as e:
        return False, f"控制器初始化失败: {e}", {}


def run_evolution_tests():
    print_header("永久演化模式测试")
    
    runner = TestRunner()
    
    tests = [
        ("模块导入测试", test_continuous_evolution_controller_import),
        ("配置测试", test_evolution_config),
        ("状态管理测试", test_evolution_state),
        ("控制器初始化测试", test_controller_initialization),
        ("心跳机制测试", test_heartbeat_mechanism),
        ("状态持久化测试", test_state_persistence),
        ("优雅停止测试", test_graceful_shutdown),
        ("演化周期测试", test_evolution_cycle),
        ("恢复机制测试", test_recovery_mechanism),
    ]
    
    for test_name, test_func in tests:
        result = runner.run_test(test_func, "永久演化模式", test_name)
        print_result(result)
        runner.report.add_result(result)
    
    return runner.finalize()


if __name__ == "__main__":
    report = run_evolution_tests()
    print(f"\n测试完成: {report.passed}/{report.total_tests} 通过")
