import sys
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("测试知识共享API端点...")
print("=" * 60)

response = client.get("/api/evolution-knowledge/sharing")
print(f"状态码: {response.status_code}")
print(f"响应内容: {response.json()}")

if response.status_code == 200:
    print("\n✅ 测试成功！知识共享API端点正常工作")
    data = response.json()
    print(f"总共享数: {data.get('total', 0)}")
    print(f"返回项目数: {len(data.get('items', []))}")
else:
    print(f"\n❌ 测试失败！状态码: {response.status_code}")
    print(f"错误信息: {response.text}")
