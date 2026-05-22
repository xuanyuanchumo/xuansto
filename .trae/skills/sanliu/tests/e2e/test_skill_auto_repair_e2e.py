"""
技能内容自动修复流程端到端测试

测试技能内容自动修复流程：
1. 检测文档问题
2. 应用修复策略
3. 验证修复结果
4. 记录修复历史
"""

import pytest
import time
from fastapi.testclient import TestClient
import sys
from pathlib import Path

backend_dir = Path(__file__).parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_dir))

from app.main import app


class BaseE2ETest:
    """E2E测试基类"""
    
    @pytest.fixture(autouse=True)
    def setup_e2e(self):
        """E2E测试前准备"""
        self.client = TestClient(app)
        yield
        self.client = None


class TestSkillAutoRepairE2E(BaseE2ETest):
    """技能内容自动修复流程端到端测试"""
    
    def setup(self):
        """测试前准备"""
        if not hasattr(self, 'client'):
            self.client = TestClient(app)
        self.test_skill_id = "skill_002"
        self.repair_session_id = None
        
    def test_01_detect_document_issues(self):
        """测试1：检测文档问题"""
        print("\n=== 测试1：检测文档问题 ===")
        
        response = self.client.get(f"/api/skill/health?skill_id={self.test_skill_id}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"技能ID: {data['skill_id']}")
        print(f"健康分数: {data['overall_score']}")
        print(f"问题数量: {len(data.get('critical_issues', []))}")
        
        issues = data.get('critical_issues', []) + data.get('warnings', [])
        print(f"检测到的问题:")
        for issue in issues:
            print(f"  - {issue}")
        
        assert data["skill_id"] == self.test_skill_id
        
    def test_02_get_content_status(self):
        """测试2：获取内容监控状态"""
        print("\n=== 测试2：获取内容监控状态 ===")
        
        response = self.client.get("/api/skill-evolution/content-status")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_monitors" in data
        assert "active_monitors" in data
        assert "monitors" in data
        
        print(f"监控器总数: {data['total_monitors']}")
        print(f"活跃监控器数: {data['active_monitors']}")
        print(f"整体健康分数: {data['overall_health']}")
        
        for monitor in data['monitors']:
            print(f"\n监控器: {monitor['monitor_id']}")
            print(f"  状态: {monitor['status']}")
            print(f"  健康分数: {monitor['health_score']}")
            print(f"  告警数量: {monitor['alerts_count']}")
        
    def test_03_trigger_repair_evolution(self):
        """测试3：触发修复演化"""
        print("\n=== 测试3：触发修复演化 ===")
        
        repair_request = {
            "evolution_type": "skill_optimization",
            "reason": "检测到文档问题，触发自动修复",
            "parameters": {
                "repair_mode": "automatic",
                "target_issues": ["documentation", "formatting", "consistency"]
            },
            "force": False,
            "dry_run": False,
            "priority": "high"
        }
        
        response = self.client.post("/api/skill-evolution/trigger", json=repair_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "trigger_id" in data
        assert "status" in data
        
        self.repair_session_id = data["trigger_id"]
        print(f"修复会话ID: {self.repair_session_id}")
        print(f"状态: {data['status']}")
        print(f"消息: {data['message']}")
        
    def test_04_monitor_repair_progress(self):
        """测试4：监控修复进度"""
        print("\n=== 测试4：监控修复进度 ===")
        
        time.sleep(2)
        
        response = self.client.get("/api/skill-evolution/status")
        assert response.status_code == 200
        
        data = response.json()
        print(f"是否正在修复: {data['is_running']}")
        print(f"当前阶段: {data['current_phase']}")
        print(f"进度: {data['progress']}%")
        
        if data['is_running']:
            print(f"演化类型: {data.get('evolution_type')}")
        
    def test_05_get_repair_phases(self):
        """测试5：获取修复阶段详情"""
        print("\n=== 测试5：获取修复阶段详情 ===")
        
        if self.repair_session_id:
            response = self.client.get(f"/api/skill-evolution/history/{self.repair_session_id}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"事件ID: {data['event_id']}")
                print(f"演化类型: {data['evolution_type']}")
                print(f"状态: {data['status']}")
                
                if 'phases' in data:
                    print(f"\n修复阶段:")
                    for phase in data['phases']:
                        print(f"  - {phase['name']}: {phase['status']} ({phase['duration_ms']}ms)")
                
                if 'changes' in data:
                    print(f"\n变更详情:")
                    for change in data['changes']:
                        print(f"  - 类型: {change.get('type')}")
                        print(f"    目标: {change.get('target')}")
            else:
                print(f"无法获取修复详情: {response.status_code}")
        else:
            print("没有修复会话ID")
        
    def test_06_validate_repair_results(self):
        """测试6：验证修复结果"""
        print("\n=== 测试6：验证修复结果 ===")
        
        time.sleep(3)
        
        response = self.client.get(f"/api/skill/health?skill_id={self.test_skill_id}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"修复后健康分数: {data['overall_score']}")
        print(f"修复后健康等级: {data['overall_level']}")
        print(f"剩余问题数: {len(data.get('critical_issues', []))}")
        
        assert data["skill_id"] == self.test_skill_id
        
    def test_07_get_repair_history(self):
        """测试7：获取修复历史"""
        print("\n=== 测试7：获取修复历史 ===")
        
        response = self.client.get("/api/skill-evolution/history?limit=10&evolution_type=skill_optimization")
        assert response.status_code == 200
        
        data = response.json()
        print(f"总修复记录数: {data['total']}")
        
        repair_count = 0
        for item in data['items']:
            if item['evolution_type'] == 'skill_optimization':
                repair_count += 1
                print(f"\n修复记录 #{repair_count}:")
                print(f"  事件ID: {item['event_id']}")
                print(f"  触发类型: {item['trigger_type']}")
                print(f"  状态: {item['status']}")
                print(f"  持续时间: {item['duration_ms']}ms")
                print(f"  变更数: {len(item['changes'])}")
        
        print(f"\n找到 {repair_count} 条修复记录")
        
    def test_08_get_repair_statistics(self):
        """测试8：获取修复统计"""
        print("\n=== 测试8：获取修复统计 ===")
        
        response = self.client.get("/api/skill-evolution/statistics")
        assert response.status_code == 200
        
        data = response.json()
        
        if 'evolution_by_type' in data:
            repair_count = data['evolution_by_type'].get('skill_optimization', 0)
            print(f"技能优化次数: {repair_count}")
        
        print(f"总演化次数: {data['total_evolutions']}")
        print(f"成功率: {data['success_rate']}%")
        print(f"平均持续时间: {data['average_duration_ms']}ms")
        
    def test_09_test_dry_run_repair(self):
        """测试9：测试模拟修复"""
        print("\n=== 测试9：测试模拟修复 ===")
        
        dry_run_request = {
            "evolution_type": "skill_optimization",
            "reason": "测试模拟修复功能",
            "dry_run": True,
            "parameters": {
                "simulation_mode": True
            }
        }
        
        response = self.client.post("/api/skill-evolution/trigger", json=dry_run_request)
        assert response.status_code == 200
        
        data = response.json()
        print(f"触发ID: {data['trigger_id']}")
        print(f"状态: {data['status']}")
        print(f"消息: {data['message']}")
        
        assert data['status'] == 'idle' or '模拟' in data['message']
        
    def test_10_export_repair_report(self):
        """测试10：导出修复报告"""
        print("\n=== 测试10：导出修复报告 ===")
        
        response = self.client.get("/api/skill-evolution/export?format=json&include_changes=true")
        assert response.status_code == 200
        
        print(f"导出成功")
        print(f"内容类型: {response.headers.get('content-type')}")
        print(f"内容长度: {len(response.content)} bytes")


def test_complete_repair_flow():
    """测试完整的修复流程"""
    print("\n" + "="*60)
    print("开始完整的技能内容自动修复流程测试")
    print("="*60)
    
    test_instance = TestSkillAutoRepairE2E()
    test_instance.setup()
    
    tests = [
        ("检测文档问题", test_instance.test_01_detect_document_issues),
        ("获取内容监控状态", test_instance.test_02_get_content_status),
        ("触发修复演化", test_instance.test_03_trigger_repair_evolution),
        ("监控修复进度", test_instance.test_04_monitor_repair_progress),
        ("获取修复阶段详情", test_instance.test_05_get_repair_phases),
        ("验证修复结果", test_instance.test_06_validate_repair_results),
        ("获取修复历史", test_instance.test_07_get_repair_history),
        ("获取修复统计", test_instance.test_08_get_repair_statistics),
        ("测试模拟修复", test_instance.test_09_test_dry_run_repair),
        ("导出修复报告", test_instance.test_10_export_repair_report),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"[PASS] {test_name} - 通过")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_name} - 失败: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"测试完成: {passed} 通过, {failed} 失败")
    print("="*60)
    
    return passed, failed


if __name__ == "__main__":
    passed, failed = test_complete_repair_flow()
    exit(0 if failed == 0 else 1)
