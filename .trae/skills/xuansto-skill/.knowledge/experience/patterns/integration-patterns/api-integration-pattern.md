---
id: "KP-EXP-PAT-API-001"
type: "pattern"
category: "integration"
tags: ["API集成", "适配器模式", "重试", "熔断", "超时"]
version: "1.0.0"
confidence: 0.88
---

## API 集成模式 (置信度: 0.88 | 技术栈: HTTP/REST)

### 现象
第三方 API 调用不稳定：超时、限流 429、服务不可用 503，导致级联故障。

### 根因
缺少重试/熔断/超时机制，同步阻塞调用，错误未隔离。

### 解决方案

```typescript
class ResilientApiClient {
  async request(url: string, options?: RequestInit): Promise<Response> {
    return retry(() => fetch(url, { ...options, signal: AbortSignal.timeout(5000) }), {
      attempts: 3, backoff: "exponential", delay: 1000,
    });
  }
}
```

```typescript
class CircuitBreaker {
  private failures = 0;
  private state: "closed" | "open" | "half-open" = "closed";
  async execute(fn: () => Promise<unknown>) {
    if (this.state === "open") throw new Error("Circuit open");
    try { const result = await fn(); this.onSuccess(); return result; }
    catch (e) { this.onFailure(); throw e; }
  }
}
```

### 验证
模拟第三方 API 故障，验证重试和熔断行为符合预期。
