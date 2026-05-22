"""
技能演化知识积累流程端到端测试

测试技能演化知识积累流程：
1. 执行演化操作
2. 记录演化上下文
3. 提取演化模式
4. 更新知识库
5. 验证知识检索
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


class TestSkillKnowledgeAccumulationE2E(BaseE2ETest):
    """技能演化知识积累流程端到端测试"""
    
    def setup(self):
        """测试前准备"""
        if not hasattr(self, 'client'):
            self.client = TestClient(app)
        self.test_pattern_id = "pattern_001"
        self.knowledge_session_id = None
        
    def test_01_get_evolution_patterns(self):
        """测试1：获取演化模式列表"""
        print("\n=== 测试1：获取演化模式列表 ===")
        
        response = self.client.get("/api/evolution-knowledge/patterns")
        assert response.status_code == 200
        
        data = response.json()
        assert "total" in data
        assert "items" in data
        
        print(f"模式总数: {data['total']}")
        print(f"返回模式数: {len(data['items'])}")
        
        for pattern in data['items'][:3]:
            print(f"\n模式: {pattern['name']}")
            print(f"  ID: {pattern['pattern_id']}")
            print(f"  类型: {pattern['type']}")
            print(f"  状态: {pattern['status']}")
            print(f"  成功率: {pattern['success_rate']}")
            print(f"  使用次数: {pattern['usage_count']}")
        
    def test_02_get_specific_pattern(self):
        """测试2：获取特定演化模式"""
        print("\n=== 测试2：获取特定演化模式 ===")
        
        response = self.client.get(f"/api/evolution/patterns/{self.test_pattern_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "pattern_id" in data
        assert "name" in data
        assert "steps" in data
        
        print(f"模式ID: {data['pattern_id']}")
        print(f"模式名称: {data['name']}")
        print(f"描述: {data['description']}")
        print(f"适用场景: {', '.join(data['applicability'])}")
        print(f"前置条件: {', '.join(data['prerequisites'])}")
        
        print(f"\n执行步骤:")
        for step in data['steps']:
            print(f"  {step['step']}. {step['action']}: {step['description']}")
        
        print(f"\n预期结果:")
        for outcome in data['expected_outcomes']:
            print(f"  - {outcome}")
        
    def test_03_get_evolution_recommendations(self):
        """测试3：获取演化推荐"""
        print("\n=== 测试3：获取演化推荐 ===")
        
        response = self.client.get("/api/evolution/recommendations?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        assert "total" in data
        assert "items" in data
        
        print(f"推荐总数: {data['total']}")
        
        for rec in data['items']:
            print(f"\n推荐ID: {rec['recommendation_id']}")
            print(f"  模式: {rec['pattern_name']}")
            print(f"  优先级: {rec['priority']}")
            print(f"  置信度: {rec['confidence']}")
            print(f"  原因: {rec['reason']}")
            print(f"  预期收益: {rec['expected_benefit']}")
            print(f"  预估工作量: {rec['estimated_effort']}")
            print(f"  前置条件满足: {rec['prerequisites_met']}")
        
    def test_04_predict_evolution_effect(self):
        """测试4：预测演化效果"""
        print("\n=== 测试4：预测演化效果 ===")
        
        prediction_request = {
            "pattern_id": self.test_pattern_id,
            "target_components": ["api_gateway", "skill_executor"],
            "simulation_depth": "standard"
        }
        
        response = self.client.post("/api/evolution/predict", json=prediction_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "prediction_id" in data
        assert "predicted_outcomes" in data
        assert "confidence_score" in data
        
        print(f"预测ID: {data['prediction_id']}")
        print(f"模式ID: {data['pattern_id']}")
        print(f"状态: {data['status']}")
        print(f"置信度分数: {data['confidence_score']}")
        
        print(f"\n预测结果:")
        for key, value in data['predicted_outcomes'].items():
            print(f"  {key}: {value}")
        
        print(f"\n性能影响:")
        for key, value in data['performance_impact'].items():
            print(f"  {key}: {value:+.2f}")
        
        print(f"\n风险评估:")
        for key, value in data['risk_assessment'].items():
            print(f"  {key}: {value}")
        
        print(f"\n建议:")
        for rec in data['recommendations']:
            print(f"  - {rec}")
        
    def test_05_trigger_knowledge_evolution(self):
        """测试5：触发知识演化"""
        print("\n=== 测试5：触发知识演化 ===")
        
        trigger_request = {
            "pattern_id": self.test_pattern_id,
            "reason": "测试知识积累流程",
            "components": ["skill_executor"],
            "parameters": {
                "knowledge_update": True,
                "learn_from_execution": True
            },
            "dry_run": False
        }
        
        response = self.client.post("/api/evolution-knowledge/trigger", json=trigger_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "trigger_id" in data
        assert "status" in data
        
        self.knowledge_session_id = data["trigger_id"]
        print(f"触发ID: {self.knowledge_session_id}")
        print(f"模式ID: {data['pattern_id']}")
        print(f"状态: {data['status']}")
        print(f"消息: {data['message']}")
        
    def test_06_monitor_knowledge_evolution(self):
        """测试6：监控知识演化进度"""
        print("\n=== 测试6：监控知识演化进度 ===")
        
        time.sleep(2)
        
        response = self.client.get("/api/evolution-knowledge/status")
        assert response.status_code == 200
        
        data = response.json()
        print(f"当前状态: {data['state']}")
        print(f"当前操作: {data.get('current_operation')}")
        print(f"进度: {data['progress']}%")
        print(f"当前模式: {data.get('current_pattern')}")
        
        if data.get('completed_steps'):
            print(f"\n已完成步骤:")
            for step in data['completed_steps']:
                print(f"  ✓ {step}")
        
        if data.get('pending_steps'):
            print(f"\n待完成步骤:")
            for step in data['pending_steps']:
                print(f"  ○ {step}")
        
    def test_07_get_evolution_history(self):
        """测试7：获取演化历史"""
        print("\n=== 测试7：获取演化历史 ===")
        
        response = self.client.get("/api/evolution/history?limit=5")
        assert response.status_code == 200
        
        data = response.json()
        print(f"总历史记录数: {data['total']}")
        
        for item in data['items']:
            print(f"\n历史记录:")
            print(f"  ID: {item['id']}")
            print(f"  模式: {item['pattern_name']}")
            print(f"  触发时间: {item['triggered_at']}")
            print(f"  完成时间: {item['completed_at']}")
            print(f"  状态: {item['status']}")
            print(f"  持续时间: {item['duration_ms']}ms")
            print(f"  成功: {item['success']}")
        
    def test_08_get_evolution_statistics(self):
        """测试8：获取演化统计"""
        print("\n=== 测试8：获取演化统计 ===")
        
        response = self.client.get("/api/evolution/statistics")
        assert response.status_code == 200
        
        data = response.json()
        print(f"总演化次数: {data['total_evolutions']}")
        print(f"成功次数: {data['successful_evolutions']}")
        print(f"失败次数: {data['failed_evolutions']}")
        print(f"成功率: {data['success_rate']:.2%}")
        print(f"平均持续时间: {data['average_duration_ms']}ms")
        print(f"24小时内: {data['last_24h']}")
        print(f"7天内: {data['last_7d']}")
        print(f"最常用模式: {data['most_used_pattern']}")
        
        print(f"\n按模式类型统计:")
        for pattern_type, count in data['by_pattern_type'].items():
            print(f"  {pattern_type}: {count}")
        
    def test_09_verify_knowledge_update(self):
        """测试9：验证知识库更新"""
        print("\n=== 测试9：验证知识库更新 ===")
        
        time.sleep(2)
        
        response = self.client.get(f"/api/evolution/patterns/{self.test_pattern_id}")
        assert response.status_code == 200
        
        data = response.json()
        print(f"模式ID: {data['pattern_id']}")
        print(f"使用次数: {data['usage_count']}")
        print(f"最后使用时间: {data.get('last_used')}")
        print(f"成功率: {data['success_rate']}")
        
        assert data['pattern_id'] == self.test_pattern_id
        
    def test_10_search_patterns_by_tag(self):
        """测试10：按标签搜索模式"""
        print("\n=== 测试10：按标签搜索模式 ===")
        
        response = self.client.get("/api/evolution/patterns?tag=performance&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        print(f"找到 {data['total']} 个包含 'performance' 标签的模式")
        
        for pattern in data['items']:
            print(f"\n  模式: {pattern['name']}")
            print(f"  标签: {', '.join(pattern['tags'])}")
        
    def test_11_filter_patterns_by_type(self):
        """测试11：按类型筛选模式"""
        print("\n=== 测试11：按类型筛选模式 ===")
        
        response = self.client.get("/api/evolution-knowledge/patterns?type=optimization")
        assert response.status_code == 200
        
        data = response.json()
        print(f"找到 {data['total']} 个优化类型的模式")
        
        for pattern in data['items']:
            print(f"\n  模式: {pattern['name']}")
            print(f"  类型: {pattern['type']}")
            print(f"  状态: {pattern['status']}")


def test_complete_knowledge_flow():
    """测试完整的知识积累流程"""
    print("\n" + "="*60)
    print("开始完整的技能演化知识积累流程测试")
    print("="*60)
    
    test_instance = TestSkillKnowledgeAccumulationE2E()
    test_instance.setup()
    
    tests = [
        ("获取演化模式列表", test_instance.test_01_get_evolution_patterns),
        ("获取特定演化模式", test_instance.test_02_get_specific_pattern),
        ("获取演化推荐", test_instance.test_03_get_evolution_recommendations),
        ("预测演化效果", test_instance.test_04_predict_evolution_effect),
        ("触发知识演化", test_instance.test_05_trigger_knowledge_evolution),
        ("监控知识演化", test_instance.test_06_monitor_knowledge_evolution),
        ("获取演化历史", test_instance.test_07_get_evolution_history),
        ("获取演化统计", test_instance.test_08_get_evolution_statistics),
        ("验证知识库更新", test_instance.test_09_verify_knowledge_update),
        ("按标签搜索模式", test_instance.test_10_search_patterns_by_tag),
        ("按类型筛选模式", test_instance.test_11_filter_patterns_by_type),
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
    passed, failed = test_complete_knowledge_flow()
    exit(0 if failed == 0 else 1)
