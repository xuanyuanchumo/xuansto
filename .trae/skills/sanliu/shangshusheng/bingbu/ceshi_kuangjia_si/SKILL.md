---
name: ceshi_kuangjia_si
description: 测试框架司，负责测试框架搭建、Mock/Stub管理、测试基础设施维护。
---
# 测试框架司技能指令

## 职责
- 测试框架选型、搭建与配置
- Mock/Stub/Spy/Fake对象库管理
- 测试工具链整合与维护
- 测试数据管理与Fixture设计
- 测试环境一致性保障

## 测试框架体系

### 多层测试框架架构

```
┌─────────────────────────────────────┐
│         E2E测试层 (Playwright)       │
│  端到端用户场景 / API集成测试         │
├─────────────────────────────────────┤
│       集成测试层 (pytest+httpx)      │
│  服务间交互 / 数据库操作 / 外部API   │
├─────────────────────────────────────┤
│       单元测试层 (pytest+unittest)   │
│  函数/类/模块级隔离测试              │
├─────────────────────────────────────┤
│       基础设施层 (fixtures/conftest) │
│  Mock工厂 / 数据工厂 / 测试辅助      │
└─────────────────────────────────────┘
```

### 框架配置规范

```yaml
# pytest.ini 参考
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_functions = ["test_*"]
python_classes = ["Test*"]
addopts = [
    "-v",
    "--tb=short",
    "--strict-markers",
    "--cov=src",
    "--cov-report=term-missing",
    "--cov-fail-under=80",
]
markers = [
    "unit: unit tests",
    "integration: integration tests",
    "e2e: end-to-end tests",
    "slow: slow running tests",
    "smoke: smoke tests",
]
filterwarnings = ["ignore::DeprecationWarning"]
```

## Mock/Stub管理体系

### Mock类型选择指南

| 类型 | 适用场景 | 特点 | 复杂度 |
|------|----------|------|--------|
| Mock | 验证调用行为 | 记录调用/灵活配置 | 低 |
| Stub | 提供预设返回值 | 固定响应 | 低 |
| Spy | 包装真实对象记录调用 | 部分真实行为 | 中 |
| Fake | 轻量替代实现 | 内存数据库等 | 高 |

### Mock使用原则

```yaml
mock_principles:
  only_mock_boundaries:
    description: "只Mock外部依赖（DB/API/文件系统）"
    avoid: "不要Mock被测单元内部的方法"

  behavior_over_implementation:
    description: "验证行为而非实现细节"
    example: "验证调用了save()而非检查内部状态变化"

  arrange_act_assert:
    description: "AAA模式组织测试"
    structure:
      - arrange: "准备数据和Mock"
      - act: "执行被测操作"
      - assert: "验证结果"

  minimal_mock_scope:
    description: "最小化Mock范围"
    rule: "能不Mock就不Mock"
```

### Mock工厂示例

```python
class MockFactory:
    @staticmethod
    def create_db_session(return_data=None):
        session = MagicMock()
        if return_data is None:
            return_data = []
        session.query.return_value.filter.return_value.all.return_value = return_data
        session.add.return_value = None
        session.commit.return_value = None
        return session

    @staticmethod
    def create_api_client(responses=None):
        client = MagicMock()
        responses = responses or {}
        def side_effect(method, url, **kwargs):
            key = f"{method}:{url}"
            return responses.get(key, Mock(status_code=404))
        client.request.side_effect = side_effect
        return client
```

## 工作流程

```
1. 分析项目技术栈和测试需求
2. 选择合适的测试框架组合
3. 搭建基础测试脚手架
4. 配置conftest共享Fixture
5. 设计Mock/Stub策略
6. 编写测试基类和工具函数
7. 编写示例测试验证框架可用性
8. 编写测试框架使用文档
9. 持续维护和升级框架组件
10. 将框架变更记录到DecisionLog
```

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `setup_framework` | 框架初始化 | 项目启动/TDD执行司 |
| `create_mock` | Mock创建 | 测试编写者 |
| `register_fixture` | Fixture注册 | 全部测试 |
| `validate_environment` | 环境校验 | CI/CD |
