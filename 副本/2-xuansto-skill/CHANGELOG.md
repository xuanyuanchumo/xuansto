# Changelog

本项目的所有重要变更都将记录在此文件中。

本文件格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [2.0.0] - 2026-05-04

### Added
- backup_history table for backup audit trail
- Incremental sync module (sync.py) for file change detection and delta synchronization
- Bidirectional sync module (exporter.py) for DB→Markdown writeback
- Lifecycle management module (lifecycle.py) for auto-archival of stale knowledge entries
- visual-regression.js gate script for visual regression testing
- accessibility-test.js gate script for WCAG 2.1 AA compliance testing
- .editorconfig for unified coding style

### Fixed
- backup_history table missing from schema (runtime error)
- MCP knowledge_add title field using id instead of title
- Optimistic lock forced update after retry failure (now returns 409 Conflict)
- RRF k value hardcoded instead of reading from config
- Semantic search scope filtering N+1 query performance issue
- SQLite thread safety for concurrent write operations
- Chroma persist() compatibility with newer versions
- Dedup threshold inconsistency between config and code (unified to 0.92)
- Design document port mismatch (8900→8765)

### Changed
- Unified all version identifiers to 2.0.0
- Archived entries excluded from search results (three-layer filtering)

## [1.10.0] - 2026-05-04

### Changed
- 重构knowledge-server.py为模块化包结构(knowledge_server/)，修复并发安全和CORS配置
- 修复token-budget-guard.py数据持久化(JSONL)、yaml fallback、阈值缓冲区间
- 修复context-compressor.py验证阈值(0.98→0.95)、ratio语义统一、架构简化
- 修复pattern-learner.py跨文件统计、AST类方法统计、正则性能、参数过滤
- 修复knowledge-index-builder.py yaml.safe_load、增量索引、相对路径
- 修复kb-migrate.py事务管理、历史保留、列重命名兼容性
- 修复script-security-scanner.py urllib精确匹配、白名单检查
- 修复script-cleanup-checker.py递归扫描子目录
- 修复skill-test.py None检查、动态Agent计数
- 修复dependency-scan.py npm v7+兼容、移除自动安装、项目路径参数
- 修复agentic-security-scanner.py Python兼容性
- 修复ai-pentest-runner.py路径拼接
- 修复infra-health-check.py路径统一、WARN判断
- 修复token-dashboard.py TES常量、退出码
- 修复agent-frontmatter-validator.py yaml容错、文本输出
- 修复knowledge-server-tests.py断言、yaml容错
- 修复coverage-check.py test-dir参数、subprocess运行
- 修复check-comment-lang.py glob模式
- 修复spec-drift-detector.py条件优先级、孤立代码检测
- 更新SKILL.md参考索引补充4个遗漏文件

### Removed
- scripts/accessibility-test.js（v1.9.3标记Deprecated，假实现）
- scripts/visual-regression.js（v1.9.3标记Deprecated，假实现）
- scripts/performance-benchmark.js（v1.9.3标记Deprecated，与desktop-perf-benchmark.js重叠）

## [1.9.3] - 2026-05-03

### Fixed
- **BUG-01**: `agent-frontmatter-validator.py` --json参数default=True导致JSON输出始终开启，改为default=False
- **BUG-02**: `api-contract-validator.py` validate_response_schema调用传入args.spec（文件路径）而非解析后参数，修复为遍历已解析端点
- **BUG-03**: `check-encoding.py` Windows平台ANSI颜色码显示异常，添加平台检测条件判断

### Added
- `workflows/flutter-desktop-workflow.md` + `_yaml/flutter-desktop-workflow.yaml`：Flutter桌面专项工作流（5阶段+5质量门禁）
- `references/flutter-desktop-guidelines.md`：Flutter桌面开发指南（窗口管理/Platform Channel/插件开发/构建配置/安全）
- `templates/flutter-build-config-template.yaml`：Flutter桌面构建配置模板（Windows/macOS/Linux三平台）
- SKILL.md description触发优化：新增中文触发词（全流程开发/规格驱动/多agent协作/桌面打包/渗透测试）和推式触发语言

### Changed
- 全项目版本号统一至1.9.1：knowledge-server.py(KB_VERSION)、.knowledge/config.yaml、10个workflow yaml文件
- `script-cleanup-checker.py` 增强（92行→227行）：多目录扫描、文件名格式合规检查、过期文件检测、--auto-clean、--format json|text
- `infra-health-check.py` 增强（127行→338行）：知识库服务健康检查、数据库完整性检查、目录结构检查、配置文件检查、工具链可用性检查、--format json|text
- SKILL.md参考资源索引新增Flutter桌面指南条目
- SKILL.md专项工作流索引新增Flutter桌面条目

### Deprecated
- `scripts/accessibility-test.js`：使用Math.random模拟测试结果（假实现），建议使用真实axe-core集成替代
- `scripts/visual-regression.js`：使用Math.random模拟像素对比（假实现），建议使用Playwright截图对比替代
- `scripts/performance-benchmark.js`：与desktop-perf-benchmark.js功能重叠

### Agent修复
- PenetrationTester emoji 🎯→🔓（与Orchestrator去重）
- DBA emoji 🛡️→🗄️（与SecurityAuditor去重）
- DesktopTester emoji 🖥️→🧪（与DesktopDeveloper去重）

## [1.9.2] - 2026-05-03

### Fixed
- **P0-01**: `coverage-check.py` 重写为使用 coverage Python API，移除 subprocess 调用（安全沙箱合规）
- **P0-02**: `desktop-perf-benchmark.js` 重写为纯Node.js静态分析，移除 child_process 调用（安全沙箱合规）
- **P0-03**: 新建 `skill-md-validator.py` SKILL.md结构验证工具
- **P0-04**: 补全Orchestrator故障恢复机制（Runtime Supervisor心跳监控、Specification Keeper备用调度）
- **P0-05**: 实现三级性能降级策略（L1/L2/L3）

### Added
- `.knowledge/workflow-checkpoints/` 目录结构（Phase 0-8）
- `.skill-logs/` 日志目录
- `migrations/` 数据库迁移目录
- `.knowledge/experience/decisions/sync-log.md` 跨分支同步日志
- `docs/knowledge-service-design.md` 知识库服务层技术设计文档
- `references/flutter-standards.md` Flutter/Dart语言规范
- `references/runtime-supervisor-details.md` Runtime Supervisor详细参考
- `references/specification-keeper-details.md` Specification Keeper详细参考
- `references/frontend-developer-details.md` Frontend Developer详细参考
- `references/ai-penetration-tester-details.md` AI Penetration Tester详细参考
- `.skill-config.yaml` 降级配置（L1/L2/L3阈值）
- SKILL.md 三级降级策略声明
- SKILL.md 参考资源索引补全

### Changed
- `skill-test.py` frontmatter检查字段更新为 name/emoji/description/color/services
- `skill-test.py` 质量门禁计数更新为 37
- `check-comment-lang.py` 重写为注释语言合规性检查（支持zh-business策略）
- `context-compressor.py` 新增 `--auto` 自动触发模式
- Orchestrator文件重命名：AGENT.md → orchestrator.md
- 精简4个Agent定义文件（runtime-supervisor/specification-keeper/frontend-developer/ai-penetration-tester）
- Agent定义新增：RCA强制要求、安全修复闭环、跨分支知识同步

## [1.9.1] - 2026-05-03

### Fixed

- knowledge-server.py: `import yaml` 缺少try/except包裹，PyYAML未安装时直接崩溃（严重）
- token-dashboard.py: `render_text`函数依赖全局变量`args`，重构为参数传递
- api-contract-validator.py: 移除未使用的`subprocess`和`urllib.parse`导入
- db-migration-validator.py: 移除未使用的`subprocess`导入
- agent-frontmatter-validator.py: 变量命名`Kebab_case_RE`修正为`KEBAB_CASE_RE`
- `.skill-config.yaml` Token预算阈值修正：compression_threshold从1.2修正为0.8，block_threshold从1.5修正为1.0（与需求8.3.1节对齐）
- `token-budget-guard.py` Token预算阈值修正：默认配置和check_status()逻辑对齐需求8.3.1节（80%触发WARN、100%触发BLOCK）

### Changed

- 统一6个Agent文件的Critical Rules格式：design/(ui-designer, ux-designer, frontend-stylist)从"硬性约束/设计边界"改为"🚫绝对禁止/⚠️必须遵守"标准格式；product/(product-manager, system-architect, technical-writer)从YAML must/must_not改为标准格式
- 统一3个design/Agent文件的Identity子章节命名：从"身份定义"改为"核心身份"
- 修复Orchestrator orchestrator.md标题层级：从h1(#)改为h2(##)，与其他40个Agent保持一致
- 修复8个工作流文件YAML frontmatter与Markdown正文阶段数不匹配问题（acceptance/ai-pentest/bug-fix/cross-platform/desktop-build/performance-test/security-audit/ui-ux-workflow）
- 修复ui-ux-workflow.md重复"阶段5"编号问题
- SKILL.md精简优化：从129行精简至113行，移除版本历史和通信配置冗余章节，合并多语言规范到参考资源索引
- SKILL.md description触发优化：新增14个触发短语、10个触发关键词、5类排除模式
- SKILL.md质量门禁索引更新：Phase 0门禁数从2项更新为4项，总门禁数从35项更新为37项

### Added

- 补充10个Agent缺失的10.5节脚本文件修改规范引用（orchestrator, doc-reviewer, compliance-officer, penetration-tester, security-auditor, qa-engineer, ui-designer, ux-designer, product-manager, system-architect）
- templates/deployment-plan-template.md（部署计划模板）
- templates/ci-cd-pipeline-template.yaml（CI/CD流水线配置模板）
- quality-gates.md新增DESIGN-VISUAL-REGRESSION门禁（视觉回归测试，差异像素<0.1%或人工确认，WARN/BLOCK）
- quality-gates.md新增DESIGN-ACCESSIBILITY门禁（可访问性检查，无A级违规且AA级违规数≤0，BLOCK）

### Removed

- commands/_fix2.ps1（一次性迁移脚本，已执行完毕）
- commands/_fix3.ps1（一次性迁移脚本，编码损坏）
- commands/_fix_all.py（一次性迁移脚本，与_fix2.ps1重复）
- commands/_fix_phase1.ps1（一次性迁移脚本，与_fix2.ps1重复）
- commands/_fix_phase1_pwsh.ps1（一次性迁移脚本，与_fix_phase1.ps1重复）
- commands/_fix_phase2_pwsh.ps1（一次性迁移脚本，与_fix_all.py重复）
- workflows/_restructure.py（硬编码frontmatter维护脚本，约2000行冗余代码）
- scripts/build-desktop.sh（违反"禁止Agent本地创建Shell脚本"规则，已有同名.ps1替代）
- scripts/sign-desktop.sh（同上）
- scripts/verify-auto-update.sh（同上）
- workflows/_merge.ps1（一次性手动工具，无任何文件引用）
- .knowledge/index/keyword_index.db（v1.6遗留，v1.8计划移除）
- .knowledge/index/vector_index.json（同上）
- .knowledge/index/metadata_index.json（同上）
- .knowledge/index/cross_reference.json（同上）

## [1.9.0] - 2026-05-02

### Added

- knowledge-server.py核心服务增强：WebSocket实时通知推送（知识条目变更事件、服务降级事件）
- knowledge-server.py版本回滚功能（条目级版本回滚、版本历史查询）
- knowledge-server.py三级降级策略（Normal→Local Semantic→BM25-only，自动恢复探测）
- knowledge-server.py安全过滤：SensitiveContentFilter（10种敏感内容模式检测）、InputValidator（SQL注入/路径穿越/XSS防御）
- knowledge-server.py API Key认证与权限分级（read-only/read-write/admin三级权限）
- knowledge-server.py滑动窗口限流（RateLimiter）
- knowledge-server.py备份与恢复（BackupManager，tar.gz备份，一致性校验）
- knowledge-server.py首次运行自动导入（FirstRunImporter，三层知识库目录扫描）
- knowledge-server.py去重与智能合并（DedupEngine，精确去重+语义去重双重检测）
- ContextCompressor主控类（上下文压缩，Token优化）
- Token Dashboard（Token使用仪表盘）
- 知识库目录补全与主动学习机制
- 21个Agent定义文件补充10.5节脚本文件修改规范引用
- references/kb-api-reference.md（知识库API参考文档，v1.9.0）
- references/knowledge-base-architecture.md扩充（三层架构+双引擎+API契约，2524行）
- SKILL.md description触发优化

### Changed

- SKILL.md版本号从1.8.1升至1.9.0
- .knowledge/VERSION从1.8.1升至1.9.0
- knowledge-server.py KB_VERSION设为1.9.0
- 所有references/*.md文件版本号统一为1.9.0

## [1.8.1] - 2026-05-02

### Added

- 5个参考文档：agent-lifecycle.md、workflow-checkpoints.md、human-collaboration.md、spec-drift-handling.md、iteration-scheduling.md
- references/spec-drift-handling.md扩充（三级漂移处理流程、SPEC-CONSISTENCY门禁复核、Spec-Drift标记规范）
- references/iteration-scheduling.md扩充（修复优先级矩阵、修复价值评分公式、增量验证策略、跨分支经验同步）
- references/script-standards.md版本元数据头补充

### Changed

- 所有41个Agent定义文件版本号从v1.6.0升至v1.8.1
- .knowledge/VERSION从1.8.0升至1.8.1
- SKILL.md版本号从1.8.0升至1.8.1

## [1.8.0] - 2026-05-01

### Added

- 10.5节Agent脚本文件修改规范（语言选型矩阵、编码规范、五步闭环生命周期、安全沙箱约束）
- SCRIPT-SECURITY和SCRIPT-CLEANUP质量门禁
- SKILL.md超精简重构（<150行核心内容）
- Token预算门禁（TOKEN-BUDGET跨阶段门禁）
- 按需加载策略（references/按需读取，不预加载全部内容）

### Changed

- Phase 4和Phase 7 Agent职责描述更新（脚本规范约束）
- 文件编码规范扩展（Python编码声明禁止）

## [1.7.0] - 2026-04-29

### Added

- SQLite+Chroma双引擎知识库服务层（knowledge-server.py）
- 知识去重与智能更新（DedupEngine）
- Token消耗优化体系（SKILL.md超精简重构、按需加载、Token预算门禁）
- 混合检索引擎（RRF融合算法，BM25+Cosine双引擎）
- 知识库REST API（FastAPI，7个核心端点）
- 知识库MCP Tool接口（5个工具）

### Changed

- SKILL.md从386行精简至<150行核心内容
- 知识库从"文件存储+脚本索引"进化为"数据库服务+智能检索"

## [1.6.0] - 2026-04-28

### Added

- 跨平台桌面开发支持（Electron/Tauri/Flutter Desktop）
- 6个桌面专用Agent（Desktop Developer, Desktop UI Adapter, Native Module Developer, Desktop Tester, Build & Release Engineer, Runtime Supervisor）
- 5个桌面质量门禁（DESKTOP-BUILD, DESKTOP-SIGN, DESKTOP-UPDATE, DESKTOP-CROSS, IPC-CONTRACT）
- 九阶段工作流（新增Phase 0: UX/UI Design, Phase 8: Build & Release）
- 桌面应用构建脚本（build-desktop.sh/ps1, sign-desktop.sh/ps1）
- IPC契约规范（references/ipc-contracts.md）
- 跨平台工作流适配（workflows/cross-platform-workflow.md, desktop-build-workflow.md）

## [1.0.0] - 2026-04-17

### Added

- 初始版本，完整SDD+TDD工作流
- 41个Agent角色定义（11层架构）
- 9阶段工作流（Phase 0-8）
- 35项质量门禁
- Karpathy行为准则集成
- 多语言开发规范支持（Python/Go/Java/Rust/TypeScript）
- A2A/v1.1协议和MCP协议支持
- 三层知识库架构（通用/工作/经验）
- 8种协作模式（Auto/串行/并行/Review/Challenge/迭代/层级/Consult/Hivecoding）
- 17个命令（/sprint /clarify /plan /spec /design /implement /test /review /fix /accept /deploy /build-desktop /release-desktop /refactor /audit /agent-status /learn）
