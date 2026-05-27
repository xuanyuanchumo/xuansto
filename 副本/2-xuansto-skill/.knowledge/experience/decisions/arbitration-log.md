---
id: "KP-EXP-DEC-001"
type: "decision"
severity: "medium"
category: "architecture"
tags: ["arbitration", "architecture", "缓存策略", "决策记录", "ADR", "多Agent冲突"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "auto_precipitation"
confidence: 0.85
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
occurrences: 1
trigger: "arbitration_completed"
references:
  - id: "KP-GEN-030"
    relation: "complies"
---

# 缓存策略架构决策仲裁记录

## 冲突描述

在电商平台重构项目中，两个 Agent 对缓存策略的选择产生严重分歧：

- **Agent-Backend**（后端架构师角色）主张使用服务端缓存（Redis）
- **Agent-Frontend**（前端架构师角色）主张使用客户端缓存（SWR/本地存储）

冲突发生在订单列表查询接口的缓存设计环节，双方各执一词，无法达成共识，触发三级仲裁机制。

---

## Agent-Backend 论点：服务端缓存（Redis）

### 核心主张

1. **数据一致性保障**：Redis 作为单一缓存源，失效策略统一可控
2. **多端一致性**：Web、App、小程序共享同一缓存层，数据视图一致
3. **缓存穿透防护**：Redis 支持布隆过滤器，有效防止缓存穿透
4. **集群共享**：多实例部署时缓存天然共享，无需额外同步
5. **运维可控**：缓存命中率、内存使用等指标集中监控

### 代码示例

```python
from redis import asyncio as aioredis

class OrderCacheService:
    def __init__(self, redis: aioredis.Redis, ttl: int = 300):
        self._redis = redis
        self._ttl = ttl

    async def get_orders(self, user_id: str) -> list[dict] | None:
        key = f"orders:user:{user_id}"
        cached = await self._redis.get(key)
        if cached:
            return json.loads(cached)
        return None

    async def set_orders(self, user_id: str, orders: list[dict]) -> None:
        key = f"orders:user:{user_id}"
        await self._redis.setex(key, self._ttl, json.dumps(orders))

    async def invalidate(self, user_id: str) -> None:
        key = f"orders:user:{user_id}"
        await self._redis.delete(key)
```

### 风险承认

- 增加 Redis 运维成本
- 网络往返延迟（约 1-3ms）
- 缓存雪崩风险需额外防护

---

## Agent-Frontend 论点：客户端缓存（SWR）

### 核心主张

1. **零网络延迟**：本地缓存命中时无网络请求，体验极致流畅
2. **离线可用**：断网场景下仍可展示缓存数据
3. **降低服务端压力**：减少重复请求，节省带宽和计算资源
4. **开发效率**：SWR/React-Query 开箱即用，代码量少
5. **用户感知优化**：stale-while-revalidate 策略，先展示旧数据再更新

### 代码示例

```typescript
import useSWR from "swr";

function useUserOrders(userId: string) {
    const { data, error, isLoading, mutate } = useSWR(
        `/api/orders?userId=${userId}`,
        fetcher,
        {
            revalidateOnFocus: true,
            revalidateOnReconnect: true,
            dedupingInterval: 5000,
            staleTime: 60_000,
        }
    );

    return {
        orders: data?.items ?? [],
        total: data?.total ?? 0,
        isLoading,
        isError: !!error,
        refresh: mutate,
    };
}
```

### 风险承认

- 多端数据可能不一致
- 本地存储容量有限
- 缓存失效依赖客户端策略，不可靠

---

## 编排者仲裁推理过程

### 第一步：需求分析

| 维度 | 需求 | 权重 |
|------|------|------|
| 数据一致性 | 订单状态变更须实时反映 | 高 |
| 响应速度 | 列表加载 < 200ms | 高 |
| 多端支持 | Web + App + 小程序 | 中 |
| 离线能力 | 弱网/断网可用 | 低 |
| 运维成本 | 团队规模有限 | 中 |

### 第二步：方案评估

| 评估维度 | 纯 Redis | 纯 SWR | 混合方案 |
|---------|----------|--------|---------|
| 数据一致性 | ★★★★★ | ★★☆☆☆ | ★★★★☆ |
| 响应速度 | ★★★☆☆ | ★★★★★ | ★★★★☆ |
| 多端一致 | ★★★★★ | ★★☆☆☆ | ★★★★☆ |
| 离线能力 | ★☆☆☆☆ | ★★★★★ | ★★★☆☆ |
| 运维成本 | ★★☆☆☆ | ★★★★★ | ★★★☆☆ |

### 第三步：决策推理

订单数据属于**一致性敏感**场景——用户支付后必须立即看到状态变更，纯客户端缓存的 stale 数据可能导致用户重复操作。但纯服务端缓存忽略了客户端的体验优化潜力。

**结论：采用混合缓存架构**，服务端缓存保障一致性，客户端缓存优化体验。

---

## 最终决策

### 混合缓存架构

```
客户端 (SWR) → API 网关 → 服务端 (Redis) → 数据库
     ↑ stale-while-revalidate    ↑ 短 TTL + 主动失效
```

### 具体规则

1. **服务端 Redis**：TTL 60s，订单状态变更时主动失效
2. **客户端 SWR**：`staleTime: 30s`，`dedupingInterval: 5s`
3. **状态变更推送**：通过 WebSocket 通知客户端 `mutate`，确保即时更新
4. **降级策略**：Redis 不可用时回退到数据库直查，客户端仍用 SWR 兜底

### ADR 参考

- **ADR-2026-004**：订单查询混合缓存架构决策
- 状态：已采纳
- 决策者：Orchestrator（仲裁模式）
- 日期：2026-04-28

---

## 决策复盘要点

| 检查项 | 频率 | 说明 |
|--------|------|------|
| Redis 命中率 | 每日 | 目标 > 85% |
| 客户端缓存命中率 | 每周 | 通过埋点统计 |
| 数据不一致事件 | 实时 | 监控 stale 数据导致的客诉 |
| WebSocket 推送延迟 | 每日 | 目标 < 500ms |
| 3 个月后全面复盘 | 一次 | 评估是否需要调整策略 |

## 相关知识

- [KP-GEN-030] 软件设计最佳实践 — 缓存策略选型
