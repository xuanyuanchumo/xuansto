---
id: documentation-standards
type: knowledge
category: standards
tags: [文档规范, README, CHANGELOG, API文档, 代码注释]
version: 1.0.0
confidence: high
---

## 文档编写规范 (版本: 1.0 | 适用: 通用)

### 核心规则
- README 必含：简介 → 快速开始 → 使用示例 → 配置说明 → 开发指南 → 许可证
- CHANGELOG 遵循 Keep a Changelog：Added/Changed/Deprecated/Removed/Fixed/Security
- 版本号遵循 SemVer：MAJOR.MINOR.PATCH
- API 文档必含：描述、参数（名称/类型/必填/默认值）、返回值、异常、示例
- 代码注释说明意图（Why），代码表达行为（What）
- 过时注释比无注释更危险，修改代码时同步更新

### 代码示例

```python
def generate_token(user_id: str, expires_in: int = 900) -> str:
    """生成 JWT 访问令牌。

    Args:
        user_id: 用户唯一标识符
        expires_in: 令牌有效期（秒），默认15分钟

    Returns:
        签名后的 JWT 字符串
    """
```

### 反模式
- ❌ README 缺少快速开始 — 新人无法上手
- ❌ 注释描述代码行为而非意图 — 代码本身已表达行为
- ❌ 过时注释与代码不一致 — 比无注释更危险
