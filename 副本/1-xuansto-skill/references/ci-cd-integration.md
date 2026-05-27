# CI/CD集成参考文档

## 流水线配置

### 流水线架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        CI/CD 流水线架构                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │  代码   │───>│  构建   │───>│  测试   │───>│  部署   │     │
│  │  提交   │    │  阶段   │    │  阶段   │    │  阶段   │     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │
│       │              │              │              │            │
│       ▼              ▼              ▼              ▼            │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐     │
│  │ 触发器  │    │ 编译    │    │ 单元测试│    │ 开发环境│     │
│  │ Webhook │    │ 打包    │    │ 集成测试│    │ 测试环境│     │
│  │ 定时    │    │ 镜像构建│    │ E2E测试 │    │ 生产环境│     │
│  └─────────┘    └─────────┘    └─────────┘    └─────────┘     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### GitHub Actions配置

#### 基础工作流

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        description: '部署环境'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

env:
  NODE_VERSION: '20'
  PYTHON_VERSION: '3.11'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: 检出代码
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: 设置Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: 安装依赖
        run: npm ci

      - name: 构建
        run: npm run build

      - name: 上传构建产物
        uses: actions/upload-artifact@v4
        with:
          name: build-output
          path: dist/
          retention-days: 7

  test:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: 安装依赖
        run: npm ci

      - name: 运行单元测试
        run: npm run test:unit -- --coverage

      - name: 运行集成测试
        run: npm run test:integration

      - name: 上传测试覆盖率
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/lcov.info
          fail_ci_if_error: true

  lint:
    runs-on: ubuntu-latest
    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'

      - name: 安装依赖
        run: npm ci

      - name: ESLint检查
        run: npm run lint

      - name: TypeScript类型检查
        run: npm run typecheck

      - name: 格式检查
        run: npm run format:check

  security:
    runs-on: ubuntu-latest
    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 运行安全审计
        run: npm audit --audit-level=high

      - name: Snyk安全扫描
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

      - name: 依赖检查
        uses: dependency-check/Dependency-Check_Action@main
        with:
          project: 'my-project'
          path: '.'
          format: 'HTML'
          out: 'reports'

  deploy-staging:
    needs: [test, lint, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 下载构建产物
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/

      - name: 配置AWS凭证
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-northeast-1

      - name: 部署到S3
        run: |
          aws s3 sync dist/ s3://staging-bucket/ --delete

      - name: 清除CDN缓存
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} \
            --paths "/*"

  deploy-production:
    needs: [test, lint, security]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://example.com
    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 下载构建产物
        uses: actions/download-artifact@v4
        with:
          name: build-output
          path: dist/

      - name: 部署到生产环境
        run: |
          echo "部署到生产环境"
```

#### 矩阵构建

```yaml
jobs:
  test-matrix:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node: [18, 20, 22]
        exclude:
          - os: macos-latest
            node: 18
        include:
          - os: ubuntu-latest
            node: 20
            experimental: true
    steps:
      - name: 检出代码
        uses: actions/checkout@v4

      - name: 设置Node.js ${{ matrix.node }}
        uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node }}

      - name: 安装依赖
        run: npm ci

      - name: 运行测试
        run: npm test
```

### GitLab CI配置

```yaml
stages:
  - build
  - test
  - security
  - deploy

variables:
  NODE_VERSION: "20"
  DOCKER_REGISTRY: registry.example.com

.default_rules:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

build:
  stage: build
  extends: .default_rules
  image: node:${NODE_VERSION}
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
    expire_in: 1 week

test:unit:
  stage: test
  extends: .default_rules
  image: node:${NODE_VERSION}
  script:
    - npm ci
    - npm run test:unit -- --coverage
  coverage: '/Lines\s*:\s*(\d+.\d+)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

test:integration:
  stage: test
  extends: .default_rules
  image: node:${NODE_VERSION}
  services:
    - postgres:15
    - redis:7
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: test
    POSTGRES_PASSWORD: test
  script:
    - npm ci
    - npm run test:integration

security:scan:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy fs --exit-code 1 --severity HIGH,CRITICAL .

deploy:staging:
  stage: deploy
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"
  environment:
    name: staging
    url: https://staging.example.com
  script:
    - echo "部署到staging环境"
  when: manual

deploy:production:
  stage: deploy
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  environment:
    name: production
    url: https://example.com
  script:
    - echo "部署到生产环境"
  when: manual
```

### Jenkins Pipeline配置

```groovy
pipeline {
    agent any
    
    environment {
        NODE_VERSION = '20'
        DOCKER_REGISTRY = 'registry.example.com'
    }
    
    options {
        timeout(time: 30, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '10'))
        disableConcurrentBuilds()
    }
    
    triggers {
        githubPush()
        cron('H 2 * * *')
    }
    
    stages {
        stage('检出代码') {
            steps {
                checkout scm
                sh 'git rev-parse HEAD > commit-hash.txt'
                stash name: 'source', includes: '**/*'
            }
        }
        
        stage('构建') {
            agent {
                docker {
                    image "node:${NODE_VERSION}"
                    args '-v ${HOME}/.npm:/root/.npm'
                }
            }
            steps {
                unstash 'source'
                sh 'npm ci'
                sh 'npm run build'
                stash name: 'build', includes: 'dist/**/*'
            }
        }
        
        stage('测试') {
            parallel {
                stage('单元测试') {
                    agent {
                        docker { image "node:${NODE_VERSION}" }
                    }
                    steps {
                        unstash 'source'
                        sh 'npm ci'
                        sh 'npm run test:unit -- --coverage'
                        publishHTML([
                            allowMissing: false,
                            alwaysLinkToLastBuild: true,
                            keepAll: true,
                            reportDir: 'coverage',
                            reportFiles: 'index.html',
                            reportName: 'Coverage Report'
                        ])
                    }
                }
                
                stage('集成测试') {
                    agent {
                        docker { image "node:${NODE_VERSION}" }
                    }
                    steps {
                        unstash 'source'
                        sh 'npm ci'
                        sh 'npm run test:integration'
                    }
                }
                
                stage('E2E测试') {
                    agent {
                        docker { image "cypress/included:latest" }
                    }
                    steps {
                        unstash 'source'
                        sh 'npm ci'
                        sh 'npm run test:e2e'
                    }
                }
            }
        }
        
        stage('安全扫描') {
            steps {
                sh 'npm audit --audit-level=high'
                sh 'docker run --rm -v $(pwd):/app aquasec/trivy:latest fs /app'
            }
        }
        
        stage('部署') {
            when {
                anyOf {
                    branch 'main'
                    branch 'develop'
                }
            }
            steps {
                unstash 'build'
                script {
                    if (env.BRANCH_NAME == 'main') {
                        input message: '确认部署到生产环境?', ok: '确认部署'
                        sh 'echo "部署到生产环境"'
                    } else {
                        sh 'echo "部署到staging环境"'
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            slackSend(
                color: 'good',
                message: "构建成功: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            )
        }
        failure {
            slackSend(
                color: 'danger',
                message: "构建失败: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
            )
        }
    }
}
```

## 质量门禁

### 质量门禁配置

#### SonarQube集成

```yaml
sonarqube:
  stage: quality
  image: sonarsource/sonar-scanner-cli
  script:
    - sonar-scanner
      -Dsonar.projectKey=my-project
      -Dsonar.sources=src
      -Dsonar.tests=tests
      -Dsonar.test.inclusions=**/*.test.ts
      -Dsonar.javascript.lcov.reportPaths=coverage/lcov.info
      -Dsonar.qualitygate.wait=true
      -Dsonar.qualitygate.timeout=300
```

#### 质量门禁规则

| 指标 | 阈值 | 说明 |
|------|------|------|
| 代码覆盖率 | ≥ 80% | 新代码覆盖率 |
| 重复代码 | ≤ 3% | 重复代码比例 |
| 代码异味 | 0 | 新代码不允许异味 |
| 安全漏洞 | 0 | 新代码不允许漏洞 |
| 安全热点 | 0 | 新代码不允许热点 |
| 技术债务 | ≤ 5% | 技术债务比例 |

### 代码质量检查

```yaml
quality-check:
  stage: quality
  script:
    - npm run lint
    - npm run typecheck
    - npm run complexity-report
  artifacts:
    reports:
      codequality: gl-code-quality-report.json
```

### 测试覆盖率要求

```yaml
coverage-check:
  stage: test
  script:
    - npm run test:coverage
    - |
      coverage=$(cat coverage/coverage-summary.json | jq '.total.lines.pct')
      if (( $(echo "$coverage < 80" | bc -l) )); then
        echo "测试覆盖率 $coverage% 低于阈值 80%"
        exit 1
      fi
```

## 部署策略

### 蓝绿部署

```
┌─────────────────────────────────────────────────────────────┐
│                      蓝绿部署架构                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                    ┌─────────────┐                         │
│                    │   负载均衡   │                         │
│                    └──────┬──────┘                         │
│                           │                                 │
│              ┌────────────┴────────────┐                   │
│              │                         │                    │
│              ▼                         ▼                    │
│     ┌────────────────┐       ┌────────────────┐            │
│     │   蓝环境       │       │   绿环境       │            │
│     │   (当前版本)   │       │   (新版本)     │            │
│     │   v1.0.0      │       │   v1.1.0       │            │
│     └────────────────┘       └────────────────┘            │
│              │                         │                    │
│              ▼                         ▼                    │
│     ┌────────────────┐       ┌────────────────┐            │
│     │   数据库       │◄─────►│   数据库       │            │
│     └────────────────┘       └────────────────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 实现脚本

```yaml
deploy-blue-green:
  stage: deploy
  script:
    - |
      if kubectl get service my-app -o jsonpath='{.spec.selector.version}' | grep -q "blue"; then
        ACTIVE="blue"
        INACTIVE="green"
      else
        ACTIVE="green"
        INACTIVE="blue"
      fi
    
    - echo "当前活跃环境: ${ACTIVE}, 部署到: ${INACTIVE}"
    
    - kubectl apply -f k8s/deployment-${INACTIVE}.yaml
    
    - kubectl rollout status deployment/my-app-${INACTIVE} --timeout=300s
    
    - kubectl patch service my-app -p '{"spec":{"selector":{"version":"'${INACTIVE}'"}}}'
    
    - kubectl scale deployment my-app-${ACTIVE} --replicas=0
```

### 金丝雀发布

```
┌─────────────────────────────────────────────────────────────┐
│                      金丝雀发布流程                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    流量分配                          │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐             │   │
│  │  │  90%    │  │  9%     │  │  1%     │             │   │
│  │  │  稳定版  │  │ 金丝雀  │  │ 金丝雀  │             │   │
│  │  │  v1.0   │  │ v1.1    │  │ v1.1    │             │   │
│  │  └─────────┘  └─────────┘  └─────────┘             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  阶段1: 1%流量 → 阶段2: 10%流量 → 阶段3: 50%流量 → 完成    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Istio配置

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-app
spec:
  hosts:
    - my-app
  http:
    - route:
        - destination:
            host: my-app
            subset: stable
          weight: 90
        - destination:
            host: my-app
            subset: canary
          weight: 10
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: my-app
spec:
  host: my-app
  subsets:
    - name: stable
      labels:
        version: v1.0.0
    - name: canary
      labels:
        version: v1.1.0
```

### 滚动更新

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  replicas: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  template:
    spec:
      containers:
        - name: app
          image: my-app:latest
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 10
```

### A/B测试

```yaml
ab-testing:
  stage: deploy
  script:
    - kubectl apply -f k8s/ab-test.yaml
  artifacts:
    reports:
      a_b_testing: ab-results.json
```

## 监控集成

### Prometheus集成

```yaml
monitoring:
  stage: post-deploy
  script:
    - |
      curl -X POST http://prometheus.example.com/api/v1/alerts \
        -H "Content-Type: application/json" \
        -d '{
          "alerts": [{
            "labels": {
              "alertname": "DeploymentComplete",
              "service": "my-app",
              "environment": "production"
            },
            "annotations": {
              "summary": "部署完成",
              "description": "my-app v1.0.0 已部署到生产环境"
            }
          }]
        }'
```

### Grafana Dashboard

```json
{
  "dashboard": {
    "title": "CI/CD Pipeline Dashboard",
    "panels": [
      {
        "title": "构建成功率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ci_build_success_total[1h]) / rate(ci_build_total[1h]) * 100"
          }
        ]
      },
      {
        "title": "部署频率",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(deployment_total[1d])"
          }
        ]
      },
      {
        "title": "平均构建时间",
        "type": "graph",
        "targets": [
          {
            "expr": "avg(ci_build_duration_seconds)"
          }
        ]
      }
    ]
  }
}
```

### 告警配置

```yaml
groups:
  - name: cicd-alerts
    rules:
      - alert: BuildFailureRate
        expr: rate(ci_build_failure_total[1h]) / rate(ci_build_total[1h]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "构建失败率过高"
          description: "最近1小时构建失败率超过10%"
      
      - alert: DeploymentStuck
        expr: deployment_in_progress > 0 and deployment_duration_seconds > 1800
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "部署卡住"
          description: "部署已超过30分钟未完成"
```

### 通知集成

#### Slack通知

```yaml
notify-slack:
  stage: .post
  script:
    - |
      curl -X POST $SLACK_WEBHOOK \
        -H "Content-Type: application/json" \
        -d '{
          "blocks": [
            {
              "type": "header",
              "text": {
                "type": "plain_text",
                "text": "🚀 部署完成"
              }
            },
            {
              "type": "section",
              "fields": [
                {"type": "mrkdwn", "text": "*项目:*\n${CI_PROJECT_NAME}"},
                {"type": "mrkdwn", "text": "*环境:*\n${DEPLOY_ENV}"},
                {"type": "mrkdwn", "text": "*版本:*\n${CI_COMMIT_SHORT_SHA}"},
                {"type": "mrkdwn", "text": "*分支:*\n${CI_COMMIT_REF_NAME}"}
              ]
            }
          ]
        }'
```

## 最佳实践

### 流水线优化

1. **并行执行**：独立任务并行运行
2. **缓存利用**：缓存依赖和构建产物
3. **增量构建**：只构建变更部分
4. **资源优化**：合理配置Runner资源

### 安全最佳实践

1. **密钥管理**：使用密钥管理系统
2. **最小权限**：遵循最小权限原则
3. **审计日志**：记录所有操作
4. **镜像安全**：扫描镜像漏洞

### 成本优化

1. **资源调度**：使用Spot实例
2. **缓存策略**：减少重复构建
3. **自动扩缩**：按需配置资源
4. **清理策略**：定期清理旧资源

## 参考资源

- GitHub Actions文档: https://docs.github.com/actions
- GitLab CI文档: https://docs.gitlab.com/ee/ci
- Jenkins文档: https://www.jenkins.io/doc
- Prometheus文档: https://prometheus.io/docs
