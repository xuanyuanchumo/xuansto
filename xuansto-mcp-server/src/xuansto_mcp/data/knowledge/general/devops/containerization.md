---
id: containerization
type: knowledge
category: devops
tags: [Docker, 容器化, 多阶段构建, 容器安全, 桌面应用容器化, Kubernetes]
version: 1.6.0
confidence: high
---

## 容器化知识 (版本: 1.6 | 适用: Docker/通用)

### 核心规则
- 单一职责：每个容器只运行一个进程，无状态设计
- 最小化镜像：使用 alpine/distroless 基础镜像，配置 .dockerignore
- 层缓存优化：变更频率低的指令在前（依赖安装），高的在后（源码复制）
- 多阶段构建：分离构建环境和运行环境，生产阶段仅含运行时依赖
- 容器安全：非 root 用户运行，固定版本标签，镜像漏洞扫描
- 密钥不写入镜像，通过环境变量或密钥管理服务注入

### 代码示例

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS production
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
RUN npm ci --production
CMD ["node", "dist/main.js"]
```

### 反模式
- ❌ 使用 `node:latest` 浮动标签 — 构建不可复现
- ❌ 容器以 root 用户运行 — 安全风险
- ❌ 将密钥硬编码到 Dockerfile — 泄露风险
