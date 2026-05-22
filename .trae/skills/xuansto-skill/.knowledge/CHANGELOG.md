# Knowledge Base Changelog

## 版本策略说明

- **Skill 主版本**（SKILL.md 中的 version）：遵循语义化版本（SemVer），仅在功能架构发生重大变更时递增
- **知识库独立版本**（.knowledge/VERSION）：独立于 Skill 主版本迭代，反映知识内容的增量和更新
- 两者关系：知识库版本 >= Skill 主版本，知识库版本号的小版本递增表示知识内容的增量更新，不反映 Skill 架构变更

## [1.6.5] - 2026-04-29

### 新增
- 知识库目录：experience/integration/third-party-services/（第三方服务集成经验）
- 知识库目录：experience/refactoring/（重构经验记录）
- 知识库文件：index/vector_index.json（向量索引初始结构）
- 配置节：security、observability、cost_optimization、platform_detection、human_collaboration、karpathy_guidelines
- 门禁别名映射表（quality-gates.md）
- 独立 PERFORMANCE 质量门禁
- TypeScript 防护代码：ASI01、ASI05、ASI07（owasp-agentic-top10-2026.md）
- 质量门禁检查项映射：AGENTIC-SECURITY、AI-PENTEST
- 桌面应用 MCP 集成指南：Electron + Tauri
- MCP 与 A2A 协同使用场景
- Xuansto Skill Agent 到 A2A agentType 集成映射
- Agent 间核心依赖关系说明
- 并发写入冲突处理机制
- 灾难恢复策略
- 可维护性需求（8.1-8.4）
- 可移植性需求（9.1-9.4）
- 版本策略说明

### 修复
- configs/default.yaml max_concurrent_agents: 5 → 3
- karpathy-guidelines.md 准则三核心原则语义偏移修正
- a2a-protocol.md 7处 example.com 占位链接替换
- sdd-tdd-full.md Phase 4 活动编号重复修正
- sdd-tdd-full.md 补充 Phase 7 → Phase 2 架构层回退路径
- agent-registry.md 层级命名统一为"数据层（Database）"

## [1.6.4] - 2026-04-29

### Fixed
- SPEC-CONSISTENCY门禁阶段归属从Phase 1修正为Phase 5（逻辑修正：规格与实现一致性验证必须在实现后执行）
- 设计层3个Agent frontmatter统一为标准格式（agent_id/agent_name/status/created_at/outputs替换agent_type/role/provides）
- 构建脚本平台标识全部统一为macos（build-desktop.sh/build-desktop.ps1/sign-desktop.ps1）
- build-desktop.ps1 Sign-Build函数引用从sign-desktop.sh修正为sign-desktop.ps1，使用PowerShell调用

### Added
- Auto Mode协作模式补充至SKILL.md（与需求文档7.1节对齐）
- SKILL.md工作流文件索引（10个工作流文件及适用场景）
- SKILL.md参考资源添加IPC契约规范和memory目录说明
- Flutter Desktop框架构建支持（build-desktop.sh和build-desktop.ps1新增flutter构建分支）

## [1.6.3] - 2026-04-29

### Fixed
- Orchestrator AGENT.md调度决策矩阵旧式Agent名称修正为正式agent_id
- 脚本和命令文件中平台标识"mac"统一为"macos"（sign-desktop.sh/build-desktop.sh/release-desktop.md/build-desktop.md）
- implement.md和test.md Agent引用规范化为agent_id格式，补充桌面端和安全测试Agent
- review.md补充FILE-ENCODING和COMMENT-LANGUAGE门禁
- 所有参考文档版本号统一为1.6.0（20个1.0.0+3个2.0.0）

### Added
- sdd-tdd-fast.md快速工作流4个阶段添加正式门禁ID映射和强制门禁
- .knowledge/general/devops/ci-cd-pipelines.md - CI/CD流水线知识条目
- .knowledge/general/devops/containerization.md - 容器化知识条目

## [1.6.2] - 2026-04-29

### Fixed
- SKILL.md Phase表Agent名称修正为正式名称（Product Manager、System Architect、Test Architect等）
- SKILL.md协作模式从5种扩展至8种（+Review/Challenge/Consult/Hivecoding）
- sdd-tdd-full.md工作流Phase 0-3门禁补全、Phase 4 TDD循环扩展为4步（+VERIFY）
- a2a-protocol.md消息格式与需求7.3节对齐（type/broadcast/protocol/signature/platform字段）
- knowledge-base-architecture.md Agent知识检索优先级与需求8.6.1节对齐
- agent-registry.md层命名统一为"数据库层（Database）"
- quality-gates.md SPEC-CONSISTENCY门禁Phase归属修正（Phase 1→Phase 4/5）
- 9个脚本功能问题修复（coverage-check/api-contract-validator/check-encoding等）

### Added
- references/ipc-contracts.md - IPC契约规范参考文档
- .knowledge/general/devops/ - DevOps知识目录
- 所有41个Agent frontmatter新增color和services字段
- 安全参考文档交叉引用（security-guidelines/owasp/desktop-dev等6个文件）

### Changed
- design-tokens.json补充完整令牌类别示例定义
- ipc-contract-template.md格式与ipc-contract-validator.js对齐
- 5个Agent定义补充内容（跨平台职责、角色区别说明、Karpathy准则等）

## [1.6.1] - 2026-04-29

### Fixed
- 统一知识库文件命名与需求8.8节一致
  - `general/desktop/tauri-best-practices.md` → `tauri-guidelines.md`
  - `general/security/owasp-top10-overview.md` → `owasp-top10.md`
  - `general/security/secure-coding-basics.md` → `secure-coding.md`
  - `general/standards/coding-standards-overview.md` → `coding-standards.md`
  - `general/testing/test-pyramid-guide.md` → `test-pyramid.md`

### Added
- `workspace/api/openapi.yaml` - OpenAPI 3.0规范模板文件

## [1.6.0] - 2026-04-28

### Added
- 三层知识库目录结构（general / workspace / experience）
- 知识库配置文件 `config.yaml`，支持自动同步与索引
- Desktop 开发知识层（v1.6.0 新增）
  - `general/desktop/` - 桌面端通用知识
  - `workspace/desktop/` - 桌面端工作空间知识
  - `experience/desktop/` - 桌面端经验知识
    - `build-fixes/` - 构建问题修复经验
    - `signing-issues/` - 签名问题经验
    - `platform-compatibility/` - 平台兼容性经验
  - `experience/errors/desktop/` - 桌面端错误经验
- 知识索引目录 `index/`
- 向量索引支持（`indexing.vector_enabled`）
- Desktop 框架支持：Electron、Tauri、Flutter Desktop
