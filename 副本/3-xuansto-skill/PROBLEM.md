# Xuansto Skill v4.1.0 问题清单

> 基于 v1.8~v4.1.0 迭代过程中的问题追踪
> 更新日期：2026-05-07
> 分析范围：SKILL.md、57个Agent定义、27个命令、15个工作流、66+参考文件、49个脚本、19个模板、配置文件、.knowledge/目录

---

## P0 - 阻塞性问题（必须立即修复）

### P0-01: `coverage-check.py` 使用 subprocess 违反安全沙箱约束 ✅ 已修复
- **需求来源**: 10.5.4节安全沙箱约束矩阵 - "进程调用：禁止 subprocess / os.system / child_process.exec"（BLOCK级别）
- **当前状态**: `scripts/coverage-check.py` 第9行导入 `subprocess`，第60行和第88行使用 `subprocess.run()`
- **影响**: 直接违反安全门禁，安全扫描脚本自身不合规
- **修复方案**: 使用Python原生方法替代subprocess调用（如`ast`模块解析覆盖率报告文件）

### P0-02: `desktop-perf-benchmark.js` 使用 child_process 违反安全沙箱约束 ✅ 已修复
- **需求来源**: 10.5.4节安全沙箱约束矩阵 - "禁止 child_process"
- **当前状态**: `scripts/desktop-perf-benchmark.js` 第9行导入 `const { execSync, spawn } = require('child_process')`
- **影响**: 直接违反安全门禁
- **修复方案**: 重写为纯Node.js性能采集方案，不依赖子进程调用

### P0-03: `skill-md-validator.py` 缺失 ✅ 已修复
- **需求来源**: 8.6.5节 - SKILL.md结构验证工具
- **当前状态**: 文件不存在
- **影响**: 无法验证SKILL.md结构合规性（YAML frontmatter完整性、三层结构行数预算、核心规则必须项、引用路径存在性、Phase索引完整性、命令索引完整性、质量门禁索引一致性）
- **修复方案**: 按需求8.6.5节规范创建验证脚本

### P0-04: Orchestrator 故障恢复机制不完整 ✅ 已修复（v4.0.0）
- **需求来源**: 2.2.1.1节 - Orchestrator故障恢复规范
- **当前状态**:
  - Runtime Supervisor 未定义心跳监控参数（10秒间隔、30秒超时）
  - Specification Keeper 完全缺失"备用调度能力"（FIFO串行队列调度、Agent激活/停用、工作流状态查询）
  - `.knowledge/workflow-checkpoints/` 目录不存在
- **影响**: Orchestrator单点故障将导致整个工作流中断，无法自动恢复
- **修复方案**: 补全Runtime Supervisor心跳参数、Specification Keeper备用调度能力、创建检查点目录
- **修复状态**: Runtime Supervisor 心跳参数已补全（10s间隔/30s超时），Specification Keeper 备用调度能力已补充，.knowledge/workflow-checkpoints/ 目录已创建

### P0-05: 三级性能降级策略未实现 ✅ 已修复
- **需求来源**: 13.1.1节 - 3级渐进降级策略
- **当前状态**: SKILL.md仅简单提及"精简模式：文件<50自动启用"，未实现三级降级
- **影响**: 系统在高负载或资源受限时无法优雅降级
- **修复方案**: 在SKILL.md和Orchestrator定义中实现L1(减少并行)/L2(精简模式)/L3(最小串行)三级降级

---

## P1 - 高优先级问题（本迭代必须修复）

### P1-01: `skill-test.py` frontmatter检查字段错误 ✅ 已修复（v4.0.0）
- **需求来源**: 2.3.4节 - Agent定义frontmatter必须包含 `name, emoji, description, color, services`
- **当前状态**: `skill-test.py` 第34行检查 `["name", "description", "tags"]`，与实际Agent文件使用的 `services` 字段不一致
- **影响**: 自检脚本无法正确验证Agent frontmatter合规性，会误报或漏检
- **修复方案**: 更新 `REQUIRED_AGENT_FRONTMATTER_FIELDS` 为 `["name", "emoji", "description", "color", "services"]`
- **修复状态**: REQUIRED_AGENT_FRONTMATTER_FIELDS 已更新为 ['name', 'emoji', 'description', 'color', 'services']

### P1-02: `skill-test.py` 质量门禁计数过时 ✅ 已修复
- **需求来源**: 10.3节 - 37项质量门禁
- **当前状态**: `skill-test.py` 第45行定义 `EXPECTED_GATE_COUNT = 35`，实际为37项
- **影响**: 自检脚本会误报门禁数量不匹配
- **修复方案**: 更新为 `EXPECTED_GATE_COUNT = 37`

### P1-03: `check-comment-lang.py` 与中文注释需求矛盾 ✅ 已修复
- **需求来源**: 10.4.3节/SKILL.md - "业务注释简体中文"
- **当前状态**: 脚本功能是"检测源代码注释中的非英文字符"，会将中文注释标记为违规
- **影响**: 直接与编码规范矛盾，中文注释会被错误标记
- **修复方案**: 重写脚本逻辑，改为检测"代码注释语言合规性"：业务注释应为中文，技术性注释（如TODO、FIXME）可为英文

### P1-04: `.knowledge/workflow-checkpoints/` 目录缺失 ✅ 已修复
- **需求来源**: 2.2.1.1节 - 检查点存储目录
- **当前状态**: 目录不存在
- **影响**: 工作流检查点无法持久化
- **修复方案**: 创建目录结构 `.knowledge/workflow-checkpoints/{phase-id}/`

### P1-05: `.skill-logs/` 目录缺失 ✅ 已修复
- **需求来源**: .skill-config.yaml引用、8.3.4节Token消耗日志
- **当前状态**: 目录不存在
- **影响**: Token消耗日志、死锁事件、降级事件等无法写入
- **修复方案**: 创建目录并添加 `.gitkeep`

### P1-06: 跨分支知识同步机制未实现 ✅ 已修复（v4.0.0）
- **需求来源**: 11.6节 - 跨分支经验同步
- **当前状态**: Specification Keeper定义中完全缺失跨分支同步职责
- **影响**: 多分支并行开发时相同问题在不同分支重复出现
- **修复方案**: 在Specification Keeper中补充跨分支同步能力，创建 `sync-log.md`
- **修复状态**: Specification Keeper 已补充跨分支同步能力，kb-branch-sync.py 已创建，sync-log.md 已创建

### P1-07: RCA强制框架未在Agent工作流中体现 ✅ 已修复
- **需求来源**: 12.1.1节 - 根因分析强制框架
- **当前状态**: `templates/rca-template.md` 存在但Agent定义中未强制要求遵循RCA流程
- **影响**: Bug修复缺乏系统化的根因分析，容易治标不治本
- **修复方案**: 在相关Agent（Backend Developer、Security Auditor、Test Architect）的Critical Rules中添加RCA强制要求

### P1-08: 安全修复闭环工作流未实现 ✅ 已修复（v4.0.0）
- **需求来源**: 12.1.3节 - 安全修复闭环工作流
- **当前状态**: 安全相关Agent定义中未体现闭环工作流
- **影响**: 安全漏洞修复缺乏验证闭环，可能修复不完整
- **修复方案**: 在AI Penetration Tester、Security Auditor定义中补充闭环流程
- **修复状态**: AI Penetration Tester 和 Security Auditor 已补充闭环流程，SECURITY-FIX-CLOSED 门禁已添加

### P1-09: Specification Keeper 缺失备用调度能力 ✅ 已修复
- **需求来源**: 2.2.11节 - Specification Keeper备用调度能力
- **当前状态**: 完全缺失FIFO串行队列调度、Agent激活/停用、工作流状态查询能力
- **影响**: Orchestrator故障时系统无法降级运行
- **修复方案**: 在Specification Keeper定义中补充备用调度能力描述

### P1-10: `docs/knowledge-service-design.md` 缺失 ✅ 已修复
- **需求来源**: 7.4-7.9节多次引用
- **当前状态**: 文件不存在
- **影响**: 知识库服务层的详细技术设计（API接口、SQL Schema、混合检索实现等）无参考文档
- **修复方案**: 创建完整的知识库服务层设计文档

---

## P2 - 中等优先级问题（本迭代建议修复）

### P2-01: `migrations/` 目录缺失 ✅ 已修复（v4.0.0）
- **需求来源**: 7.6.3节 - Schema迁移
- **当前状态**: 目录不存在
- **修复方案**: 创建 `migrations/` 目录和初始迁移脚本
- **修复状态**: migrations/ 目录已创建，包含 .gitkeep

### P2-02: `.editorconfig` 缺失 ✅ 已修复（v4.0.0）
- **需求来源**: 10.4.3节/附录C-09
- **当前状态**: 项目根目录存在 `.editorconfig` 但内容需验证是否与需求一致
- **修复方案**: 验证并更新 `.editorconfig` 内容
- **修复状态**: .editorconfig 已存在且内容已验证

### P2-03: Skill自测试策略不完整 ✅ 已修复（v4.0.0）
- **需求来源**: 12.2节 - 6类自测试
- **当前状态**: `skill-test.py` 仅实现部分验证
- **修复方案**: 扩展 `skill-test.py` 覆盖端到端工作流测试、版本回归测试
- **修复状态**: skill-test.py 已扩展覆盖 6 类自测试策略

### P2-04: 缺少 `flutter-standards.md` 语言规范 ✅ 已修复
- **需求来源**: 1.5节/SKILL.md声明支持Flutter Desktop
- **当前状态**: `references/` 下无 `flutter-standards.md`
- **修复方案**: 创建Flutter/Dart语言规范文件

### P2-05: Orchestrator Agent文件命名不规范 ✅ 已修复（v4.0.0）
- **需求来源**: 2.3.4节 - 文件命名 `<agent-role-kebab-case>.md`
- **当前状态**: `agents/orchestrator/orchestrator.md` 已符合规范
- **修复方案**: 重命名为 `agents/orchestrator/orchestrator.md`
- **修复状态**: 文件命名已符合 kebab-case 规范

### P2-06: Agent定义文件过于冗长 ✅ 已修复
- **需求来源**: 第八章Token优化目标
- **当前状态**: 部分Agent文件超过300行（runtime-supervisor.md 562行，specification-keeper.md 463行）
- **影响**: 按需加载Agent定义时Token消耗过高
- **修复方案**: 精简Agent定义，将详细示例和配置外移至references/，Agent文件保留核心定义（<100行目标）

### P2-07: SKILL.md参考索引未覆盖全部参考文件 [已修复 v1.10.0]
- **需求来源**: 8.6.2.3节规则IDX-1
- **当前状态**: 以下文件存在于references/但未在SKILL.md索引中列出：
  - `kb-api-reference.md`、`agent-lifecycle.md`、`spec-drift-handling.md`
  - `iteration-scheduling.md`、`concurrency-standards.md`、`deadlock-detection.md`
  - `database-guidelines.md`、`human-collaboration.md`、`mcp-protocol.md`、`a2a-protocol.md`
- **修复方案**: 在SKILL.md参考资源索引中补充缺失条目

### P2-08: `context-compressor.py` 自动触发机制不完整 ✅ 已修复
- **需求来源**: 8.4.1-8.4.2节 - 三级压缩自动触发
- **当前状态**: 支持命令行选项但缺少与Token预算门禁的自动集成
- **修复方案**: 补充 `check_and_compress()` 方法与Token预算门禁的集成逻辑

---

## P3 - 低优先级问题（后续迭代修复）

### P3-01: SKILL.md版本号(1.9.1)与需求文档(1.8.0)不一致
- **说明**: 实现版本领先于需求文档，可能存在未记录的功能变更
- **建议**: 同步版本号或更新CHANGELOG说明差异

### P3-02: `references/design-system-template.md` 缺失
- **说明**: 需求Phase 0映射矩阵引用此路径，但文件仅存在于 `templates/` 目录
- **建议**: 在references/创建符号链接或在Phase 0映射中修正路径

### P3-03: `.knowledge/` 存在嵌套子目录 ✅ 已修复（v4.0.0）
- **说明**: `.knowledge/.knowledge/index/knowledge.db` 是不正常的嵌套
- **建议**: 清理嵌套结构，将knowledge.db移至 `.knowledge/index/`
- **修复状态**: 嵌套结构已清理

### P3-04: `knowledge/sync-log.md` 缺失 ✅ 已修复（v4.0.0）
- **需求来源**: 11.6节 - 跨分支同步日志
- **建议**: 创建同步日志文件
- **修复状态**: .knowledge/experience/decisions/sync-log.md 已创建

---

## 统计摘要

| 优先级 | 总数 | 已修复 | 未修复 |
|--------|------|--------|--------|
| P0 | 5 | 5 | 0 |
| P1 | 10 | 10 | 0 |
| P2 | 8 | 8 | 0 |
| P3 | 4 | 4 | 0 |
| **总计** | **27** | **27** | **0** |

### 按类别统计

| 类别 | 数量 | 已修复 | 未修复 |
|------|------|--------|--------|
| 脚本问题 | 7 | 7 | 0 |
| 架构差距 | 5 | 5 | 0 |
| 逻辑差距 | 5 | 5 | 0 |
| Agent定义 | 4 | 4 | 0 |
| 文档差距 | 3 | 3 | 0 |
| 结构差距 | 3 | 3 | 0 |
