---
name: environment-config-si
parent: universal-devops
department: hubu
province: shangshusheng
description: |
  环境配置司 - 户部·度支司

  【职责】开发/测试/生产环境配置、环境一致性保障、配置管理

  【触发条件】
  - 多环境配置管理
  - 环境一致性问题和排查
  - 配置版本控制和回滚

  【能力】
  - 多环境配置模板
  - 配置差异检测
  - 环境变量管理
  - 配置热更新
---

# 环境配置司 (Environment Config Si)

> 尚书省 · 户部 · Universal DevOps v4.0

**状态**: 占位符 - 具体内容由后续任务填充

## 🤖 自主化操作指南 (v7.0)

### 推荐操作模式
| 操作场景 | 推荐模式 | 置信度 | 说明 |
|---------|---------|--------|------|
| 配置文件编写 | SCRIPTED_BATCH | 92% | 高度模板化，遵循12-Factor App原则 |
| 环境差异检测 | SCRIPTED_BATCH | 96% | 自动对比dev/staging/prod配置 |
| 配置热更新 | HYBRID_ASSISTED | 85% | 工具执行 + 人工确认影响范围 |
| 配置迁移与重构 | AUTONOMOUS_MANUAL | 74% | 涉及多系统协调和数据迁移 |

### 常用工具组合
- **读操作**: Read, SearchCodebase, Grep（读取.env.*、config/*.yaml、docker-compose.yml）
- **写操作**: Write, SearchReplace（创建配置模板、更新环境变量）
- **批量操作**: 配置校验脚本(如env-ci)、配置加密工具(sops/vault)、配置同步工具
- **验证操作**: 配置diff检查器、环境一致性验证工具

### 注意事项
- ⚠️ 绝对禁止将敏感凭证（密码、API Key）硬编码到代码或提交到代码仓库
- ⚠️ 生产环境配置变更必须有完整的审批流程和回滚方案
- ✅ 采用"配置即代码"(Configuration as Code)理念：所有配置版本化管理并可审计
- ✅ 遵循12-Factor App原则：严格分离config和code，通过环境变量注入配置

## 🔗 资源协调要点 (v7.0)

### 常访问资源
| 资源类型 | 典型路径 | 锁策略建议 |
|---------|---------|-----------|
| FILE | .env.example / config/*.yaml | SHARED (读) / EXCLUSIVE (修改) |
| SECRET | HashiCorp Vault / AWS Secrets Manager | HIGHLY_RESTRICTED + AUDITED |
| SERVICE | 配置中心(Apollo/Nacos/Consul) | REAL_TIME + AUTHENTICATED |
| CI/CD | Pipeline环境变量配置 | PROTECTED (需审批) |
| LOG | 配置变更审计日志 | APPEND_ONLY |

### 竞争规避策略
1. **配置所有权明确**: 每个配置项有明确的owner，避免多人同时修改导致冲突
2. **变更窗口限制**: 敏感配置变更限定在低流量时段（如凌晨），减少影响面
3. **灰度发布机制**: 配置变更支持按百分比灰度（如先10%用户生效），快速回滚能力

## 💡 开源哲学应用 (v7.0)

### OpenCode 透明化
- 配置文档完整公开：每个环境变量的用途、默认值、可选值都有清晰注释
- 变更历史可追溯：谁在什么时间改了什么配置、原因是什么，完整记录
- 配置漂移检测报告：定期对比各环境配置差异，标识非预期的偏差

### OpenClaude 编排
- 智能配置推荐：根据应用特征推荐最佳实践配置（如连接池大小、超时时间）
- 异常配置检测：自动识别异常值配置（如生产环境debug=true）并告警
- 配置依赖分析：自动绘制配置项之间的依赖关系图，辅助理解影响范围

### Claw-Code 契约驱动
- 配置schema验证：使用JSON Schema/YAML Schema定义配置结构，CI阶段强制校验
- 敏感信息零容忍契约：代码中检测到硬编码密钥时自动阻止合入
- 配置一致性保障：通过基础设施测试(Infrastructure Testing)确保跨环境配置符合预期
