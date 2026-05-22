# 9阶段工作流详细参考

> 本文件由SKILL.md按需加载

## Phase 0: 初始化

**目标：** 项目结构检测与设计系统建立

**MCP工具：** `skill_analyze`, `workflow_dispatch`, `agent_status`, `resource_load_status`

**门禁：** DESIGN-SYSTEM-COMPLETE, ANTI-PATTERN-CHECK, DESIGN-REVIEW

**详细步骤：**
1. 调用 `skill_analyze(skill_path, depth="full", include_agents=True, include_scripts=True)` → 获取项目元数据、目录结构、Agent注册表、脚本依赖
2. 检测平台类型 — 分析 package.json / pubspec.yaml / Cargo.toml 判断 Web/Desktop/Flutter
3. 评估项目规模 — 统计文件数：>50=大(full), 20-50=中(medium), <20=小(fast)
4. 调用 `workflow_dispatch(action="start", workflow=选定工作流, project_path=项目路径)` → 启动工作流实例
5. 调用 `agent_status(action="by_phase", phase=0)` → 查询初始化阶段可用Agent
6. 调用 `resource_load_status(action="preload", phase=0)` → 预加载Phase 0资源
7. 建立设计系统基线 — 确定色彩/字体/间距/组件规范
8. 调用 `quality_gate_check(gate_ids=["DESIGN-SYSTEM-COMPLETE", "ANTI-PATTERN-CHECK"])` → 验证初始化门禁
9. 门禁通过后触发 PhaseEnter Hook → 进入Phase 1

**Agent分配：**
| Agent | 职责 |
|-------|------|
| Orchestrator | 总体编排，决定工作流级别 |
| System Architect | 平台检测，技术栈判断 |
| Design System Generator | 设计系统基线建立 |
| Knowledge Manager | 检索项目初始化经验 |

**输出物：**
- 项目分析报告（metadata + structure + dependencies）
- 设计系统基线文档
- 工作流实例ID（workflow_id）
- Agent分配方案

## Phase 1: 需求分析

**目标：** 需求澄清与Brainstorming

**MCP工具：** `knowledge_search`, `resource_load_status`

**门禁：** BRAINSTORM-COMPLETE, GATE-001, GATE-002

**详细步骤：**
1. 调用 `knowledge_search(query="需求分析模板", scope="general", search_type="hybrid", top_k=5)` → 检索需求分析经验
2. 调用 `resource_load_status(action="preload", phase=1)` → 预加载Phase 1资源
3. 执行Brainstorming会话 — Product Manager引导，Brainstorming Facilitator主持
4. 澄清需求细节 — 用户故事、验收标准、非功能需求
5. 识别约束条件 — 技术约束、业务约束、时间约束
6. 生成需求文档 — PRD/用户故事/验收标准
7. 调用 `quality_gate_check(gate_ids=["BRAINSTORM-COMPLETE", "GATE-001", "GATE-002"])` → 验证需求门禁
8. 门禁通过后触发 PhaseEnter Hook → 进入Phase 2

**Agent分配：**
| Agent | 职责 |
|-------|------|
| Product Manager | 需求收集与优先级排序 |
| Brainstorming Facilitator | 头脑风暴引导 |
| Technical Writer | 需求文档编写 |
| Knowledge Manager | 经验检索与注入 |

**输出物：**
- 需求文档（PRD）
- 用户故事列表
- 验收标准清单
- 约束条件记录

## Phase 2: 架构设计

**目标：** 技术方案设计与原子任务分解

**MCP工具：** `knowledge_search`, `resource_load_status`

**门禁：** PLAN-ATOMIC, GATE-003, GATE-004

**详细步骤：**
1. 调用 `knowledge_search(query="架构模式 " + 技术栈, scope="experience", search_type="hybrid", top_k=5)` → 检索架构模式参考
2. 调用 `resource_load_status(action="preload", phase=2)` → 预加载Phase 2资源
3. 设计技术架构 — 系统架构图、模块划分、数据流、API契约
4. 技术选型决策 — 框架/库/中间件选择，记录ADR(Architecture Decision Record)
5. 分解为原子任务 — 每个任务独立可测试，单一职责
6. 生成实施计划 — 任务依赖关系、执行顺序、预估工时
7. 调用 `quality_gate_check(gate_ids=["PLAN-ATOMIC", "GATE-003", "GATE-004"])` → 验证架构门禁
8. 门禁通过后触发 PhaseEnter Hook → 进入Phase 3

**Agent分配：**
| Agent | 职责 |
|-------|------|
| System Architect | 架构设计与技术选型 |
| Product Manager | 需求到架构的映射验证 |
| Data Modeler | 数据模型设计 |
| Technical Writer | 架构文档编写 |
| Knowledge Manager | 架构经验检索 |

**输出物：**
- 架构设计文档
- ADR记录
- 原子任务列表（含依赖关系）
- 实施计划
- API契约定义

## Phase 3: 测试先行

**目标：** 编写测试用例

**门禁：** TEST-FIRST

**详细步骤：**
1. 根据原子任务列表，为每个任务确定测试策略（单元/集成/E2E）
2. 编写单元测试 — 覆盖核心逻辑，目标覆盖率≥80%
3. 编写集成测试 — 覆盖模块间交互
4. 编写E2E测试骨架 — 覆盖关键用户流程
5. 验证测试可运行 — 执行测试确认全部FAIL（RED状态）
6. 确认覆盖率目标 — 测试覆盖所有需求点
7. 调用 `quality_gate_check(gate_ids=["TEST-FIRST"])` → 验证测试先行门禁
8. 门禁通过后触发 PhaseEnter Hook → 进入Phase 4

**Agent分配：**
| Agent | 职责 |
|-------|------|
| Test Architect | 测试策略设计 |
| Unit Tester | 单元测试编写 |
| Integration Tester | 集成测试编写 |
| E2E Tester | E2E测试骨架 |
| Specification Keeper | 规格与测试映射 |

**输出物：**
- 单元测试文件
- 集成测试文件
- E2E测试骨架
- 测试覆盖率报告（RED状态）
- 测试-需求映射矩阵

## Phase 4: 代码实现

**目标：** 按测试驱动实现代码

**MCP工具：** `quality_gate_check`, `agent_status`

**门禁：** GATE-007, TEST-PASS, FILE-ENCODING, GATE-009

**详细步骤：**
1. 调用 `agent_status(action="by_phase", phase=4)` → 查询实现阶段Agent
2. 逐个原子任务实现代码 — 严格按测试驱动：RED→GREEN→REFACTOR
3. 每完成一个原子任务：
   - 运行相关测试确认GREEN
   - 调用 `quality_gate_check(gate_ids=["TEST-PASS"])` → 验证测试通过
   - 调用 `quality_gate_check(gate_ids=["FILE-ENCODING"])` → 验证UTF-8无BOM
4. 实现完成后全量测试 — 确认所有测试GREEN
5. 调用 `quality_gate_check(gate_ids=["GATE-007", "GATE-009"])` → 验证实现门禁
6. 门禁通过后触发 PhaseEnter Hook → 进入Phase 5

**Agent分配：**
| Agent | 职责 |
|-------|------|
| Backend Developer | 后端逻辑实现 |
| Frontend Developer | 前端界面实现 |
| Fullstack Developer | 全栈功能实现 |
| Database Developer | 数据库操作实现 |
| Mobile Developer | 移动端实现（如需） |
| Subagent Dispatcher | 子任务分发与并行编排 |
| Task Coordinator | 任务协调与依赖管理 |

**输出物：**
- 源代码文件
- 测试覆盖率报告（GREEN状态）
- 实现日志
- 门禁检查报告

## Phase 5: 测试验证

**目标：** 全面测试与安全扫描

**MCP工具：** `security_scan`, `spec_drift_detect`, `agent_status`

**门禁：** AI-PENTEST, SPEC-CONSISTENCY, GATE-011, GATE-012

**详细步骤：**
1. 调用 `security_scan(target=".", severity_threshold="medium", include_agentic=True, include_dependency=True)` → 安全扫描
2. 调用 `spec_drift_detect(spec_dir=".trae/specs", src_dir=".")` → 规格漂移检测
3. 调用 `agent_status(action="by_phase", phase=5)` → 查询验证阶段Agent
4. 执行E2E测试 — 覆盖关键用户流程
5. 执行性能测试 — 响应时间/吞吐量/资源占用
6. 执行AI渗透测试 — 模拟攻击向量
7. 修复发现的问题 — 安全漏洞/规格偏差/测试失败
8. 调用 `quality_gate_check(gate_ids=["AI-PENTEST", "SPEC-CONSISTENCY", "GATE-011", "GATE-012"])` → 验证测试门禁
9. 门禁通过后触发 PhaseEnter Hook → 进入Phase 6

**Agent分配：**
| Agent | 职责 |
|-------|------|
| Security Auditor | 安全扫描结果分析 |
| Penetration Tester | AI渗透测试执行 |
| E2E Tester | E2E测试执行 |
| Performance Tester | 性能测试执行 |
| QA Tester | 回归测试验证 |
| Specification Keeper | 规格一致性验证 |

**输出物：**
- 安全扫描报告
- 规格漂移检测报告
- E2E测试结果
- 性能测试报告
- 渗透测试报告
- 问题修复记录

## Phase 6: 验收确认

**目标：** 用户验收与合规检查

**MCP工具：** `quality_gate_check`

**门禁：** GATE-013, GATE-014, UX-ACCEPTANCE, INFRA-HEALTH

**详细步骤：**
1. 调用 `quality_gate_check(phase="6")` → 验证阶段6全部门禁
2. UX验收测试 — 用户交互体验评估
3. 基础设施健康检查 — 部署环境就绪性验证
4. 合规性检查 — 代码规范/安全合规/文档完整性
5. 用户确认验收 — 展示功能演示，获取用户确认
6. 生成验收报告 — 汇总所有测试和检查结果
7. 调用 `quality_gate_check(gate_ids=["GATE-013", "GATE-014", "UX-ACCEPTANCE", "INFRA-HEALTH"])` → 最终验收门禁
8. 门禁通过后触发 PhaseEnter Hook → 进入Phase 7

**Agent分配：**
| Agent | 职责 |
|-------|------|
| Product Manager | 验收标准确认 |
| UX Designer | UX验收评估 |
| Compliance Officer | 合规性检查 |
| Quality Monitor | 质量汇总 |
| Documentation Engineer | 验收文档编写 |

**输出物：**
- 验收报告
- UX评估报告
- 合规检查报告
- 基础设施就绪报告
- 用户确认记录

## Phase 7: 持续重构

**目标：** 代码简化与Chesterton's Fence检查

**MCP工具：** `code_simplify`, `context_compress`

**门禁：** SIMPLIFICATION-BEHAVIOR, CHESTERTON-FENCE, GATE-015

**详细步骤：**
1. 调用 `code_simplify(target=".", scope="recent", include_dedup=True)` → 分析简化机会
2. 评估简化建议 — 区分安全简化与需谨慎的变更
3. 执行安全简化 — 删除死代码、合并重复、简化命名
4. Chesterton's Fence检查 — 对每个简化确认"存在的理由"，防止破坏隐含依赖
5. 运行全量测试 — 确认行为不变
6. 调用 `context_compress(content=重构摘要, strategy="semantic", target_tokens=2000)` → 压缩重构上下文
7. 调用 `quality_gate_check(gate_ids=["SIMPLIFICATION-BEHAVIOR", "CHESTERTON-FENCE", "GATE-015"])` → 验证重构门禁
8. 门禁通过后触发 PhaseEnter Hook → 进入Phase 8

**Agent分配：**
| Agent | 职责 |
|-------|------|
| Refactoring Specialist | 重构执行 |
| Code Reviewer | 重构审查 |
| Bug Scanner | 重构后回归检测 |
| History Analyzer | 代码历史分析（Chesterton's Fence） |
| Token Optimizer | 上下文压缩 |

**输出物：**
- 代码简化报告
- 重构变更记录
- Chesterton's Fence检查记录
- 行为不变性验证报告
- 压缩后的上下文摘要

## Phase 8: 部署交付

**目标：** 构建、签名与发布

**门禁：** DESKTOP-BUILD, DESKTOP-SIGN, DESKTOP-UPDATE, DESKTOP-CROSS, IPC-CONTRACT

**详细步骤：**
1. 构建产物 — 执行构建命令，生成部署包
2. 代码签名 — 桌面应用需代码签名（Windows: Authenticode, macOS: Developer ID）
3. 自动更新配置 — 配置更新服务器和更新清单
4. 跨平台验证 — 在目标平台验证构建产物
5. IPC契约验证 — 桌面应用需验证主进程与渲染进程IPC安全性
6. 调用 `quality_gate_check(gate_ids=["DESKTOP-BUILD", "DESKTOP-SIGN", "DESKTOP-UPDATE", "DESKTOP-CROSS", "IPC-CONTRACT"])` → 验证部署门禁
7. 部署到目标环境
8. 触发 PhaseExit Hook → 工作流完成
9. 调用 `session_manage(action="save", completed_tasks=[...], experience=[...])` → 保存会话与经验

**Agent分配：**
| Agent | 职责 |
|-------|------|
| Build-Release Engineer | 构建与发布 |
| CI/CD Specialist | 部署流水线 |
| Desktop Developer | 桌面构建与签名 |
| IPC Specialist | IPC安全验证 |
| Auto-Update Engineer | 自动更新配置 |
| Runtime Supervisor | 运行时监控 |
| Monitor Specialist | 部署后监控 |

**输出物：**
- 构建产物（部署包）
- 代码签名证书记录
- 自动更新配置
- 跨平台验证报告
- IPC安全审计报告
- 部署记录
- 会话总结与经验沉淀
