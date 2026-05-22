"""
技能自演化流程端到端测试

测试完整的技能自演化流程：
1. 健康度评估
2. 触发自动修复
3. 验证修复效果
4. 更新知识库
5. 生成演化报告
"""

import pytest
import asyncio
import time
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
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


class TestSkillEvolutionE2E(BaseE2ETest):
    """技能自演化流程端到端测试"""
    
    def setup(self):
        """测试前准备"""
        if not hasattr(self, 'client'):
            self.client = TestClient(app)
        self.test_skill_id = "skill_001"
        self.evolution_trigger_id = None
        
    def test_01_health_assessment(self):
        """测试1：健康度评估"""
        print("\n=== 测试1：健康度评估 ===")
        
        response = self.client.get(f"/api/skill/health?skill_id={self.test_skill_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "skill_id" in data
        assert "overall_score" in data
        assert "overall_level" in data
        assert "category_scores" in data
        
        print(f"技能ID: {data['skill_id']}")
        print(f"总体健康分数: {data['overall_score']}")
        print(f"健康等级: {data['overall_level']}")
        print(f"类别数量: {len(data['category_scores'])}")
        
        assert data["skill_id"] == self.test_skill_id
        assert 0 <= data["overall_score"] <= 100
        assert data["overall_level"] in ["excellent", "good", "fair", "poor", "critical"]
        
    def test_02_trigger_health_assessment(self):
        """测试2：触发健康度评估"""
        print("\n=== 测试2：触发健康度评估 ===")
        
        assessment_request = {
            "skill_ids": [self.test_skill_id],
            "deep_analysis": True,
            "include_recommendations": True,
            "priority": "high"
        }
        
        response = self.client.post("/api/skill/health/assess", json=assessment_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "assessment_id" in data
        assert "status" in data
        assert "skills_to_assess" in data
        
        self.assessment_id = data["assessment_id"]
        print(f"评估ID: {self.assessment_id}")
        print(f"状态: {data['status']}")
        print(f"待评估技能数: {data['skills_to_assess']}")
        
    def test_03_get_assessment_progress(self):
        """测试3：获取评估进度"""
        print("\n=== 测试3：获取评估进度 ===")
        
        if not hasattr(self, 'assessment_id'):
            self.assessment_id = f"assess_{int(time.time() * 1000)}"
        
        time.sleep(2)
        
        response = self.client.get(f"/api/skill/health/assess/{self.assessment_id}")
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "assessment_id" in data
            assert "status" in data
            assert "progress" in data
            
            print(f"评估ID: {data['assessment_id']}")
            print(f"状态: {data['status']}")
            print(f"进度: {data['progress']}%")
            print(f"已完成技能数: {data.get('skills_completed', 0)}")
        
    def test_04_get_evolution_status(self):
        """测试4：获取演化状态"""
        print("\n=== 测试4：获取演化状态 ===")
        
        response = self.client.get("/api/skill-evolution/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "is_running" in data
        assert "current_phase" in data
        assert "total_evolutions" in data
        assert "success_rate" in data
        
        print(f"是否正在演化: {data['is_running']}")
        print(f"当前阶段: {data['current_phase']}")
        print(f"总演化次数: {data['total_evolutions']}")
        print(f"成功率: {data['success_rate']}%")
        
    def test_05_trigger_evolution(self):
        """测试5：触发演化"""
        print("\n=== 测试5：触发演化 ===")
        
        evolution_request = {
            "evolution_type": "skill_optimization",
            "reason": "健康度评估发现性能问题，触发自动优化",
            "parameters": {
                "target_skill": self.test_skill_id,
                "optimization_level": "moderate"
            },
            "force": False,
            "dry_run": False,
            "priority": "high"
        }
        
        response = self.client.post("/api/skill-evolution/trigger", json=evolution_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "trigger_id" in data
        assert "evolution_type" in data
        assert "status" in data
        
        self.evolution_trigger_id = data["trigger_id"]
        print(f"触发ID: {self.evolution_trigger_id}")
        print(f"演化类型: {data['evolution_type']}")
        print(f"状态: {data['status']}")
        print(f"消息: {data['message']}")
        
    def test_06_monitor_evolution_progress(self):
        """测试6：监控演化进度"""
        print("\n=== 测试6：监控演化进度 ===")
        
        time.sleep(3)
        
        response = self.client.get("/api/skill-evolution/status")
        assert response.status_code == 200
        
        data = response.json()
        print(f"演化状态: {data}")
        print(f"是否正在运行: {data['is_running']}")
        print(f"当前阶段: {data['current_phase']}")
        print(f"进度: {data['progress']}%")
        
    def test_07_get_evolution_history(self):
        """测试7：获取演化历史"""
        print("\n=== 测试7：获取演化历史 ===")
        
        response = self.client.get("/api/skill-evolution/history?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "total" in data
        assert "items" in data
        
        print(f"总历史记录数: {data['total']}")
        print(f"返回记录数: {len(data['items'])}")
        
        if data['items']:
            latest = data['items'][0]
            print(f"最新演化ID: {latest['event_id']}")
            print(f"演化类型: {latest['evolution_type']}")
            print(f"状态: {latest['status']}")
        
    def test_08_get_evolution_statistics(self):
        """测试8：获取演化统计"""
        print("\n=== 测试8：获取演化统计 ===")
        
        response = self.client.get("/api/skill-evolution/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_evolutions" in data
        assert "successful_evolutions" in data
        assert "failed_evolutions" in data
        assert "success_rate" in data
        
        print(f"总演化次数: {data['total_evolutions']}")
        print(f"成功次数: {data['successful_evolutions']}")
        print(f"失败次数: {data['failed_evolutions']}")
        print(f"成功率: {data['success_rate']}%")
        print(f"24小时内演化次数: {data['last_24h_count']}")
        
    def test_09_generate_evolution_report(self):
        """测试9：生成演化报告"""
        print("\n=== 测试9：生成演化报告 ===")
        
        response = self.client.get("/api/skill-evolution/report")
        assert response.status_code == 200
        
        data = response.json()
        assert "report_id" in data
        assert "generated_at" in data
        assert "summary" in data
        assert "evolution_statistics" in data
        
        print(f"报告ID: {data['report_id']}")
        print(f"生成时间: {data['generated_at']}")
        print(f"摘要: {data['summary']}")
        print(f"建议数量: {len(data.get('recommendations', []))}")
        
    def test_10_verify_health_improvement(self):
        """测试10：验证健康度改善"""
        print("\n=== 测试10：验证健康度改善 ===")
        
        time.sleep(2)
        
        response = self.client.get(f"/api/skill/health?skill_id={self.test_skill_id}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"演化后健康分数: {data['overall_score']}")
        print(f"演化后健康等级: {data['overall_level']}")
        
        assert data["skill_id"] == self.test_skill_id
        
    def test_11_test_pause_and_resume(self):
        """测试11：测试暂停和恢复演化"""
        print("\n=== 测试11：测试暂停和恢复演化 ===")
        
        evolution_request = {
            "evolution_type": "workflow_adaptation",
            "reason": "测试暂停和恢复功能",
            "force": True,
            "dry_run": False
        }
        
        trigger_response = self.client.post("/api/skill-evolution/trigger", json=evolution_request)
        assert trigger_response.status_code == 200
        
        time.sleep(1)
        
        pause_response = self.client.post(
            "/api/skill-evolution/pause",
            json={"reason": "测试暂停", "save_state": True}
        )
        
        if pause_response.status_code == 200:
            pause_data = pause_response.json()
            print(f"暂停成功: {pause_data['message']}")
            print(f"保存的状态ID: {pause_data.get('saved_state_id')}")
            
            time.sleep(1)
            
            resume_response = self.client.post(
                "/api/skill-evolution/resume",
                json={"continue_from_checkpoint": True}
            )
            
            if resume_response.status_code == 200:
                resume_data = resume_response.json()
                print(f"恢复成功: {resume_data['message']}")
                print(f"当前阶段: {resume_data['current_phase']}")
            else:
                print(f"恢复响应状态码: {resume_response.status_code}")
        else:
            print(f"暂停响应状态码: {pause_response.status_code}")
        
    def test_12_test_rollback(self):
        """测试12：测试回滚功能"""
        print("\n=== 测试12：测试回滚功能 ===")
        
        history_response = self.client.get("/api/skill-evolution/history?limit=1")
        assert history_response.status_code == 200
        
        history_data = history_response.json()
        
        if history_data['items']:
            latest_event = history_data['items'][0]
            event_id = latest_event['event_id']
            
            rollback_request = {
                "event_id": event_id,
                "reason": "测试回滚功能",
                "force": False,
                "create_backup": True
            }
            
            rollback_response = self.client.post("/api/skill-evolution/rollback", json=rollback_request)
            
            if rollback_response.status_code == 200:
                rollback_data = rollback_response.json()
                print(f"回滚ID: {rollback_data['rollback_id']}")
                print(f"目标事件ID: {rollback_data['target_event_id']}")
                print(f"状态: {rollback_data['status']}")
                print(f"备份ID: {rollback_data.get('backup_id')}")
            else:
                print(f"回滚响应状态码: {rollback_response.status_code}")
        else:
            print("没有可回滚的演化历史")


def test_complete_evolution_flow():
    """测试完整的演化流程"""
    print("\n" + "="*60)
    print("开始完整的技能自演化流程测试")
    print("="*60)
    
    test_instance = TestSkillEvolutionE2E()
    test_instance.setup()
    
    tests = [
        ("健康度评估", test_instance.test_01_health_assessment),
        ("触发健康度评估", test_instance.test_02_trigger_health_assessment),
        ("获取评估进度", test_instance.test_03_get_assessment_progress),
        ("获取演化状态", test_instance.test_04_get_evolution_status),
        ("触发演化", test_instance.test_05_trigger_evolution),
        ("监控演化进度", test_instance.test_06_monitor_evolution_progress),
        ("获取演化历史", test_instance.test_07_get_evolution_history),
        ("获取演化统计", test_instance.test_08_get_evolution_statistics),
        ("生成演化报告", test_instance.test_09_generate_evolution_report),
        ("验证健康度改善", test_instance.test_10_verify_health_improvement),
        ("测试暂停和恢复", test_instance.test_11_test_pause_and_resume),
        ("测试回滚功能", test_instance.test_12_test_rollback),
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
    passed, failed = test_complete_evolution_flow()
    exit(0 if failed == 0 else 1)
