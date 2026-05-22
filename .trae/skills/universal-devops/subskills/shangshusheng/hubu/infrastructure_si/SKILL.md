---
name: infrastructure-si
parent: universal-devops
department: hubu
province: shangshusheng
description: |
  基础设施司 - 户部·户部司

  【职责】CI/CD流水线、容器化部署、云资源管理、基础设施即代码

  【触发条件】
  - CI/CD流水线搭建和优化
  - 容器化和Kubernetes部署
  - 基础设施自动化管理

  【能力】
  - 流水线编排
  - Docker/K8s配置
  - Terraform/IaC管理
  - 监控告警集成
---

# 基础设施司 (Infrastructure Si)

> 尚书省 · 户部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| IaC代码编写(Terraform/K8s) | SCRIPTED_BATCH | 90% | 声明式配置，高度标准化 |
| 流水线配置(Jenkins/GitLab CI) | SCRIPTED_BATCH | 93% | YAML配置为主，模板复用率高 |
| 容器镜像构建 | SCRIPTED_BATCH | 95% | Dockerfile标准化，CI自动触发 |
| 架构优化重构 | AUTONOMOUS_MANUAL | 72% | 影响范围大，需要全面评估 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取Terraform/Helm/Dockerfile配置）
- **写操作**: Write, SearchReplace（编写IaC代码、更新pipeline配置）
- **批量操作**: Terraform plan/apply自动化、Docker镜像构建流水线、K8s部署脚本
- **验证操作**: Terraform validate/fmt、容器安全扫描(Trivy)、IaC安全检查(Checkov/tfsec)

### 注意事项
- ⚠️ IaC变更必须经过plan-review-apply流程，禁止直接apply到生产环境
- ⚠️ 容器镜像必须使用具体版本tag而非latest，确保可重现性
- ✅ 采用"不可变基础设施"(Immutable Infrastructure)理念：替换而非修改
- ✅ 建立IaC模块化复用：公共组件封装为共享module，减少重复和 drift

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| FILE | /terraform/ /k8s/ /docker/ | VERSION_CONTROLLED (Git管理) |
| STATE | Terraform state文件 | LOCKED (并发保护) |
| CLUSTER | Kubernetes集群 | RBAC (基于角色的访问控制) |
| REGISTRY | Docker镜像仓库(ACR/ECR/Harbor) | ACCESS_CONTROLLED |
| API | 云服务商API(AWS/Azure/Aliyun) | IAM_AUTHENTICATED |

### 竞争规避策略
1. **State Lock机制**: Terraform使用远程state backend(DynamoDB/Azurite)加锁防止并发冲突
2. **命名空间隔离**: K8s资源按团队/项目划分namespace，避免资源名称冲突
3. **蓝绿部署/金丝雀发布**: 通过部署策略减少基础设施变更的服务中断时间

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- 基础设施代码完全开源：Terraform/Helm/Dockerfile对所有DevOps工程师可见和可贡献
- 变更计划公开评审：每次terraform plan的结果作为PR展示，供团队review
- 成本分配透明化：云资源成本按项目/团队分摊，每个人能看到自己的资源开销

### OpenClaude 编排
- 智能Drift检测：自动对比实际基础设施与IaC代码的差异，标识未授权变更
- 成本优化建议引擎：基于使用模式自动推荐降配/预留实例/Spot实例等优化方案
- 多云编排抽象：统一屏蔽底层云厂商差异，简化跨云资源管理复杂度

### Claw-Code 契约驱动
- IaC合规扫描契约：Checkov/tfsec在PR阶段强制执行安全最佳实践检查
- 基础设施测试契约：使用Terratest/Puppeteer编写IaC的单元/集成测试
- 部署门禁自动化：pipeline包含自动化的健康检查、性能基线验证、回滚准备就绪检查
