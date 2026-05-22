---
name: bushu
description: 进行软件部署上线，包括环境配置、部署执行、监控配置，支持Docker容器化和CI/CD自动化流程。
---
# 部署流程

## 概述
软件部署是将开发完成的应用程序发布到生产环境的过程。良好的部署流程应确保部署的可靠性、可重复性和可回滚性。

## 部署步骤

### 1. 环境准备
配置服务器、数据库、缓存等基础设施。

**环境检查清单：**
- [ ] 服务器资源（CPU、内存、磁盘）满足需求
- [ ] 网络配置正确（端口、防火墙、域名）
- [ ] 数据库已创建并配置访问权限
- [ ] 缓存服务（Redis/Memcached）已启动
- [ ] 消息队列服务已配置
- [ ] SSL证书已安装
- [ ] 环境变量已配置

### 2. 构建应用
编译、打包应用程序。

**构建步骤：**
1. 安装依赖包
2. 执行代码编译
3. 运行单元测试
4. 打包构建产物
5. 生成版本标签

### 3. 部署执行
将应用部署到目标环境。

### 4. 配置管理
配置环境变量、参数。

### 5. 健康检查
验证部署成功。

### 6. 监控配置
配置日志、监控告警。

## Docker 配置示例

### Dockerfile 示例

```dockerfile
# Node.js 应用
FROM node:18-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

# 生产镜像
FROM node:18-alpine

WORKDIR /app

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules

EXPOSE 3000

USER node

CMD ["node", "dist/main.js"]
```

```dockerfile
# Python 应用
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

## docker-compose.yml 示例

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/myapp
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=myapp
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    restart: always

volumes:
  postgres_data:
  redis_data:
```

### Docker 部署命令

```bash
# 构建镜像
docker build -t myapp:v1.0.0 .

# 推送到镜像仓库
docker tag myapp:v1.0.0 registry.example.com/myapp:v1.0.0
docker push registry.example.com/myapp:v1.0.0

# 部署服务
docker-compose up -d

# 查看日志
docker-compose logs -f web

# 滚动更新
docker-compose pull web
docker-compose up -d --no-deps --build web
```

## CI/CD 流程说明

### CI/CD 流程图

```
代码提交 → 代码检查 → 单元测试 → 构建 → 集成测试 → 部署预发 → 部署生产
    │          │          │        │         │           │           │
    ▼          ▼          ▼        ▼         ▼           ▼           ▼
  Git       ESLint    Jest/JUnit  Docker   E2E Test    Staging     Production
  Push      Pylint    Pytest      Build    Selenium    Deploy      Deploy
```

### GitHub Actions 配置示例

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: registry.example.com
  IMAGE_NAME: myapp

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run linter
        run: npm run lint

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run unit tests
        run: npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build:
    runs-on: ubuntu-latest
    needs: test
    outputs:
      image_tag: ${{ steps.meta.outputs.tags }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Login to Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ secrets.REGISTRY_USER }}
          password: ${{ secrets.REGISTRY_PASSWORD }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=sha,prefix=
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - name: Deploy to staging
        run: |
          echo "Deploying to staging environment..."
          # 部署脚本

  deploy-production:
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - name: Deploy to production
        run: |
          echo "Deploying to production environment..."
          # 部署脚本
```

## GitLab CI 配置示例

```yaml
stages:
  - lint
  - test
  - build
  - deploy

variables:
  REGISTRY: registry.example.com
  IMAGE_NAME: myapp

lint:
  stage: lint
  image: node:18-alpine
  script:
    - npm ci
    - npm run lint

test:
  stage: test
  image: node:18-alpine
  script:
    - npm ci
    - npm run test:coverage
  coverage: '/Lines\s*:\s*(\d+\.?\d*)%/'

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $REGISTRY_USER -p $REGISTRY_PASSWORD $REGISTRY
    - docker build -t $REGISTRY/$IMAGE_NAME:$CI_COMMIT_SHA .
    - docker push $REGISTRY/$IMAGE_NAME:$CI_COMMIT_SHA

deploy_staging:
  stage: deploy
  image: alpine:latest
  environment: staging
  script:
    - echo "Deploying to staging..."
  only:
    - develop

deploy_production:
  stage: deploy
  image: alpine:latest
  environment: production
  script:
    - echo "Deploying to production..."
  only:
    - main
  when: manual
```

## 部署策略

### 蓝绿部署

```
         ┌─────────────┐
         │   负载均衡   │
         └──────┬──────┘
                │
        ┌───────┴───────┐
        │               │
   ┌────▼────┐    ┌────▼────┐
   │  Blue   │    │  Green  │
   │ (v1.0)  │    │ (v1.1)  │
   │ Active  │    │ Standby │
   └─────────┘    └─────────┘
```

**特点：**
- 两套完全相同的生产环境
- 零停机时间
- 快速回滚
- 资源占用高

### 金丝雀发布

```
         ┌─────────────┐
         │   负载均衡   │
         └──────┬──────┘
                │
        ┌───────┴───────┐
        │               │
   ┌────▼────┐    ┌────▼────┐
   │  旧版本  │    │  新版本  │
   │  (95%)  │    │  (5%)   │
   └─────────┘    └─────────┘
```

**特点：**
- 逐步增加新版本流量
- 降低风险
- 实时监控反馈
- 适合大规模系统

### 滚动更新

```
时间线：
T1: [v1][v1][v1][v1] → [v2][v1][v1][v1]
T2: [v2][v1][v1][v1] → [v2][v2][v1][v1]
T3: [v2][v2][v1][v1] → [v2][v2][v2][v1]
T4: [v2][v2][v2][v1] → [v2][v2][v2][v2]
```

**特点：**
- 逐个更新实例
- 资源利用率高
- 简单易实现
- 更新过程较长

## 部署检查清单

### 部署前
- [ ] 代码已合并到目标分支
- [ ] 所有测试通过
- [ ] 版本号已更新
- [ ] 变更日志已更新
- [ ] 数据库迁移脚本已准备
- [ ] 回滚方案已准备

### 部署中
- [ ] 备份当前版本
- [ ] 执行数据库迁移
- [ ] 部署新版本
- [ ] 运行健康检查
- [ ] 验证核心功能

### 部署后
- [ ] 监控指标正常
- [ ] 错误日志无异常
- [ ] 性能指标符合预期
- [ ] 用户反馈正常
- [ ] 文档已更新

## 常见问题处理

| 问题 | 解决方案 |
|------|----------|
| 部署失败 | 检查日志，回滚到上一版本 |
| 数据库迁移失败 | 手动修复数据，重新执行迁移 |
| 服务启动失败 | 检查配置和依赖，查看启动日志 |
| 性能下降 | 检查资源使用，优化配置 |
| 内存泄漏 | 分析堆栈，重启服务并排查 |

## 输出物
- 部署脚本
- 部署文档
- 运维手册
- 回滚方案
- 监控配置
