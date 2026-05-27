---
id: containerization
type: knowledge
category: devops
tags: [Docker, 容器化, 多阶段构建, 容器安全, 桌面应用容器化, Kubernetes]
version: 1.6.0
created: 2026-04-29
updated: 2026-04-29
confidence: high
---

# 容器化知识

## Docker 开发最佳实践

### 镜像构建原则

- **单一职责**：每个容器只运行一个进程
- **无状态设计**：应用状态外置到数据库/缓存/卷
- **最小化镜像**：使用 `alpine` 或 `distroless` 基础镜像
- **层缓存优化**：将变更频率低的指令放在前面（如依赖安装），变更频率高的放在后面（如源码复制）
- **.dockerignore**：排除 `node_modules`、`.git`、测试文件等无关内容

### 开发环境容器化

- 使用 `docker-compose` 编排多服务开发环境
- 开发镜像挂载源码目录实现热重载
- 环境变量通过 `.env` 文件或 `docker-compose.yml` 注入
- 数据持久化使用命名卷（Named Volumes）

### 常用开发模式

```yaml
development:
  build:
    context: .
    target: development
  volumes:
    - ./src:/app/src
  environment:
    - NODE_ENV=development
  ports:
    - "3000:3000"
```

## 多阶段构建

多阶段构建用于分离构建环境和运行环境，显著减小最终镜像体积：

### 典型模式

```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/package*.json ./
RUN npm ci --production
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

### 阶段划分建议

| 阶段 | 用途 | 包含内容 |
|------|------|----------|
| `deps` | 依赖安装 | 完整 node_modules |
| `builder` | 编译构建 | 源码 + 构建工具 + 产物 |
| `test` | 测试执行 | 构建产物 + 测试依赖 |
| `production` | 生产运行 | 仅运行时依赖 + 构建产物 |

### 优化技巧

- 依赖安装阶段单独抽离，利用 Docker 层缓存
- 使用 `npm ci` 替代 `npm install` 确保可复现构建
- 生产阶段仅复制必要文件，排除开发依赖和源码
- 使用 `--mount=type=cache` 缓存包管理器下载目录

## 桌面应用容器化考虑

桌面应用的容器化场景与 Web 应用有本质区别，主要用于构建环境而非运行环境：

### 构建环境容器化

- 使用容器提供一致的跨平台构建环境
- Electron 应用可在 Linux 容器中构建 Windows/macOS 安装包（需 Wine 和交叉编译工具链）
- Tauri/Rust 应用需要对应平台的原生依赖

### 桌面构建容器模式

```yaml
desktop-build:
  image: electron-builder:latest
  volumes:
    - ./src:/project/src
    - ./dist:/project/dist
  environment:
    - GH_TOKEN=${GH_TOKEN}
  command: npm run build:all
```

### 注意事项

- macOS 构建通常需要 macOS 主机（Apple 许可证限制）
- 代码签名证书需通过安全卷或密钥管理服务注入
- 原生模块（native modules）需要在目标平台上编译
- GPU 加速相关功能在容器中可能不可用，需特殊配置

### 桌面测试容器化

- 无头模式（Headless）运行 UI 测试：`electron --no-sandbox --disable-gpu`
- 使用 Xvfb 提供虚拟显示环境
- 集成测试可在容器中运行 IPC 通信验证

## 容器安全基础

### 镜像安全

- **基础镜像选择**：优先使用官方镜像和精简版本（alpine/distroless）
- **镜像扫描**：使用 Trivy/Snyk/Clair 扫描已知漏洞
- **固定版本标签**：使用具体版本号（`node:20.11.0-alpine`）而非浮动标签（`node:latest`）
- **最小权限原则**：容器内使用非 root 用户运行

### 运行时安全

```dockerfile
RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
```

- **只读文件系统**：`docker run --read-only` 配合 tmpfs 挂载
- **资源限制**：设置 CPU/内存限制防止资源耗尽
- **网络隔离**：使用自定义网络，限制容器间通信
- **密钥管理**：不将密钥写入镜像，通过环境变量或密钥管理服务注入

### 安全检查清单

- [ ] 基础镜像无高危漏洞
- [ ] 容器以非 root 用户运行
- [ ] 无硬编码密钥或凭证
- [ ] 镜像使用固定版本标签
- [ ] 仅暴露必要端口
- [ ] 设置资源限制
- [ ] 日志不包含敏感信息
