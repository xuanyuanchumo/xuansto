---
id: "KP-EXP-PAT-SVC-001"
type: "pattern"
category: "refactoring"
tags: ["服务提取", "重构", "God Class", "单一职责", "依赖注入"]
version: "1.0.0"
confidence: 0.88
---

## 服务提取重构 (置信度: 0.88 | 技术栈: 通用)

### 现象
单个类/模块超过 500 行，承担多种职责（如 UserService 同时处理认证、通知、数据持久化），修改一处影响多处。

### 根因
初期快速开发未做职责划分，功能逐步堆叠形成 God Class，缺乏服务边界意识。

### 解决方案

```typescript
class UserService {
  constructor(
    private auth: AuthService,
    private notification: NotificationService,
    private repo: UserRepository,
  ) {}
  async register(email: string, password: string) {
    const user = await this.repo.save(new User(email));
    await this.auth.createCredentials(user.id, password);
    await this.notification.sendWelcome(user.email);
    return user;
  }
}
```

### 验证
提取后每个服务类 < 200 行，单一职责，可独立测试。
