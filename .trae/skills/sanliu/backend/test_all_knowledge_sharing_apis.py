import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("测试知识共享API端点...")
print("=" * 60)

tests = [
    ("GET /api/evolution-knowledge/sharing", "GET", "/api/evolution-knowledge/sharing"),
    ("GET /api/evolution-knowledge/sharing/sharing_001", "GET", "/api/evolution-knowledge/sharing/sharing_001"),
    ("GET /api/evolution-knowledge/sharing/status/summary", "GET", "/api/evolution-knowledge/sharing/status/summary"),
    ("POST /api/evolution-knowledge/sharing", "POST", "/api/evolution-knowledge/sharing", {
        "knowledge_id": "knowledge_004",
        "source_project_id": "project_001",
        "target_project_ids": ["project_002"],
        "permission": "read",
        "shared_by": "测试用户"
    })
]

passed = 0
failed = 0

for test in tests:
    test_name = test[0]
    method = test[1]
    url = test[2]
    
    print(f"\n测试: {test_name}")
    print("-" * 60)
    
    if method == "GET":
        response = client.get(url)
    elif method == "POST":
        data = test[3] if len(test) > 3 else {}
        response = client.post(url, json=data)
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        print(f"✅ 测试通过")
        data = response.json()
        print(f"响应数据: {data}")
        passed += 1
    else:
        print(f"❌ 测试失败")
        print(f"错误信息: {response.text}")
        failed += 1

print("\n" + "=" * 60)
print(f"测试完成: {passed} 通过, {failed} 失败")
print("=" * 60)
