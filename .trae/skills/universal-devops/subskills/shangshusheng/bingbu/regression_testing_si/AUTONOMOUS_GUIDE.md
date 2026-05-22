# 回归测试司 自主操作指南 (Autonomous Operation Guide)

## 概述

回归测试司（regression_testing_si）是尚书省兵部下属质量保障执行机构，负责回归测试范围的自主决策、冒烟测试套件维护、不稳定测试治理及回归策略优化。本司的核心使命是：**在有限的测试资源约束下，通过智能的变更影响分析和精准的回归范围选择，最大化缺陷捕获率，最小化回归测试成本，确保每次代码变更不引入已知功能的退化**。

本司不负责编写新的业务测试用例（归属TDD执行司），不负责测试框架基础设施维护（归属测试框架司），也不负责覆盖率目标设定（归属覆盖率分析司）。本司的职责边界清晰聚焦于**已有测试用例的选择性执行与质量治理**。

## 核心原则

1. **影响驱动原则**：回归范围必须基于变更的实际影响面来确定，而非机械地执行全量。
2. **风险平衡原则**：在漏测风险和测试成本之间寻找最优平衡点，避免两个极端。
3. **快速反馈原则**：回归测试应尽可能早地提供结果，缩短反馈周期。
4. **持续精炼原则**：回归测试套件是活的实体，需要持续维护、淘汰冗余、补充盲区。
5. **稳定性优先原则**：一个不可靠的回归套件比没有回归套件更危险。
6. **可追溯原则**：每个回归测试用例必须能追溯到其保护的业务场景或历史缺陷。

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 变更感知
- 监听版本控制系统（Git等）的提交事件和PR/MR活动
- 解析变更文件集合（新增/修改/删除文件列表）
- 识别变更类型：功能新增、Bug修复、重构、配置调整、依赖更新
- 提取变更的diff内容，分析语义层面的改动范围
- 识别变更涉及的模块边界和接口契约

#### 1.2 测试资产感知
- 扫描现有测试套件的完整清单和元数据
- 获取每个测试用例的以下属性：
  - 测试名称和所属文件
  - 覆盖的源码文件和函数映射关系（从覆盖率分析司获取）
  - 测试标记（@unit/@integration/@e2e/@slow/@security）
  - 历史执行记录（通过率、平均耗时、最近失败时间）
  - 关联的需求ID或缺陷ID
- 识别当前冒烟测试套件的组成和覆盖范围
- 检测近期出现的不稳定测试（Flaky Test）

#### 1.3 环境与资源感知
- 确认当前可用的测试执行环境（CI节点、测试数据库等）
- 评估可用执行时间窗口（如CI超时限制）
- 了解当前的构建队列状态和预估等待时间
- 识别是否存在并行执行能力及其上限

### 阶段二：决策（Decide）

#### 2.1 变更影响分析优先级排序

根据变更类型自动确定回归测试的范围和优先级：

##### 第一优先级：直接变更文件 → 全量相关测试
**触发条件**：变更涉及核心业务逻辑文件的实现代码
**回归策略**：
- 对变更文件对应的所有测试用例执行全量回归
- 包含单元测试和相关的集成测试
- 若变更涉及公共API，需包含所有调用方的验证测试

**影响半径计算**：
```
直接影响 = {变更文件自身} ∪ {变更文件中修改的函数/方法}
间接影响 = {直接导入变更模块的所有模块} ∪ {被变更函数调用的所有上游调用方}
总影响集 = 直接影响 ∪ 间接影响
```

##### 第二优先级：导入依赖变更 → 相关模块测试
**触发条件**：变更涉及接口定义、类型声明、共享模块、公共工具函数
**回归策略**：
- 对所有导入该模块的其他模块执行回归测试
- 重点验证接口兼容性和类型安全
- 关注隐含的行为变化（如默认参数变更、异常类型变更）

**依赖图遍历算法**：
```python
class DependencyImpactAnalyzer:
    def analyze_import_change(self, changed_module, dependency_graph, max_depth=3):
        """
        分析模块变更的影响传播路径
        """
        affected = set()
        queue = [(changed_module, 0)]
        
        while queue:
            module, depth = queue.pop(0)
            if depth > max_depth:
                continue
            
            # 找到所有直接依赖此模块的下游模块
            downstream = dependency_graph.get_dependents(module)
            
            for dep_module in downstream:
                if dep_module not in affected:
                    affected.add(dep_module)
                    queue.append((dep_module, depth + 1))
        
        return {
            "changed_module": changed_module,
            "directly_affected": dependency_graph.get_dependents(changed_module),
            "transitively_affected": affected,
            "total_impact_count": len(affected),
            "max_depth_reached": max_depth
        }
```

##### 第三优先级：接口签名变更 → 所有调用方测试
**触发条件**：变更涉及公开API的函数签名（参数增减、返回值类型变更、异常声明变更）
**回归策略**：
- 定位所有调用方代码位置（静态分析+动态追踪）
- 对每个调用方执行对应的适配性验证测试
- 特别关注运行时可能延迟暴露的问题（如序列化/反序列化兼容性）

**调用方定位策略**：
- 静态分析：AST/符号表级别的引用搜索
- 动态分析：基于运行时调用图的追踪
- 文本搜索：作为后备手段的正则匹配（注意误报）

##### 第四优先级：配置变更 → 环境验证测试
**触发条件**：变更涉及配置文件、环境变量、特性开关（Feature Flag）、常量定义
**回归策略**：
- 执行环境一致性验证测试套件
- 验证配置加载的正确性和完整性
- 测试特性开关各分支路径的功能行为
- 验证默认值回退逻辑

#### 2.2 回归范围决策矩阵

| 变更规模 | 变更风险 | 推荐回归策略 | 预计执行时间 | 典型场景 |
|---------|---------|------------|------------|---------|
| 小（<5文件） | 低 | 冒烟 + 影响域 | 5-15分钟 | typo修复、文档更新 |
| 小（<5文件） | 高 | 冒烟 + 影响域 + 关联集成 | 15-30分钟 | 安全补丁、关键Bug修复 |
| 中（5-20文件） | 中 | 影响域全量 + 冒烟 | 30-60分钟 | 功能迭代、一般重构 |
| 大（>20文件） | 高 | 全量回归（分阶段） | 60-180分钟 | 架构迁移、大规模重构 |
| 任意 | 发布前 | 冒烟 + 全量回归 | 按项目规模 | 版本发布 |

#### 2.3 全量回归 vs 增量回归的策略选择

**增量回归适用条件（满足全部才推荐增量）**：
- ✅ 变更影响范围清晰且可控
- ✅ 存在可靠的测试-代码映射关系
- ✅ 有完善的冒烟测试套件作为安全网
- ✅ 团队对增量策略有信心和经验
- ✅ 上次全量回归距今不超过7天

**强制全量回归触发条件（满足任一即必须全量）**：
- 🔴 距上次全量回归超过14天
- 🔴 涉及数据库Schema变更或数据迁移脚本
- 🔴 涉及认证/授权机制的变更
- 🔴 涉及支付/财务相关核心逻辑
- 🔴 上次增量回归后发现了漏测的回归缺陷
- 🔴 发布正式版本前的最终验证

**混合策略（推荐用于大型项目）**：
```
每次提交: 自动冒烟测试（≤10分钟）
每日构建: 增量回归（影响域+冒烟，≤60分钟）
每周构建: 模块级轮转全量（每周覆盖不同模块）
发布前:   完整全量回归 + 探索性测试补充
```

### 阶段三：Execute

#### 3.1 冒烟测试套件自主维护

**冒烟测试的定义与组成**：

冒烟测试（Smoke Test）是一组快速执行的、覆盖最核心业务路径的测试用例集合。其目的是以最小的代价验证系统基本可用性。

**标准冒烟测试套件应包含**：

| 核心路径类别 | 必须覆盖的场景 | 最少用例数建议 |
|-------------|--------------|---------------|
| 用户认证 | 登录成功/失败/Token过期/权限不足 | ≥4 |
| 数据写入 | 核心实体的CRUD操作 | ≥8（每实体×2） |
| 核心业务流 | 端到端的主业务流程（如下单→支付→发货） | ≥3 |
| 关键查询 | 列表检索/详情查看/搜索功能 | ≥4 |
| 外部集成 | 第三方服务调用的可达性和基本响应 | ≥3 |
| 数据一致性 | 关键操作的后续状态验证 | ≥3 |
| 基础设施 | 健康检查/配置加载/连接池 | ≥3 |

**冒烟测试套件质量标准**：
- 总执行时间 ≤ 10分钟（理想 ≤ 5分钟）
- 通过率必须为100%（任何冒烟测试失败都是阻塞级的）
- 用例数量控制在 25-50 个之间（过多则失去"冒烟"的意义）
- 每个用例必须有明确的失败含义说明
- 套件至少每月评审一次，移除过时用例，补充新核心路径

**冒烟测试套件自动演化机制**：
```python
class SmokeTestSuiteEvolver:
    def evaluate_and_evolve(self, current_suite, change_history, failure_history):
        """
        自主评估和演化冒烟测试套件
        """
        actions = []
        
        # 规则1: 新增核心路径检测
        new_core_paths = self._detect_new_critical_paths(change_history)
        for path in new_core_paths:
            if path not in current_suite:
                actions.append({
                    "action": "ADD",
                    "reason": f"检测到新的核心业务路径: {path}",
                    "priority": "HIGH"
                })
        
        # 规则2: 过时用例清理
        stale_tests = self._detect_stale_tests(current_suite, change_history)
        for test in stale_tests:
            actions.append({
                "action": "REMOVE",
                "reason": f"用例{test}对应的代码已超过90天未变更",
                "priority": "LOW"
            })
        
        # 规则3: 从历史缺陷反哺
        defect_derived = self._derive_from_defects(failure_history)
        for test_spec in defect_derived:
            if test_spec not in current_suite:
                actions.append({
                    "action": "ADD",
                    "reason": f"源于历史缺陷#{test_spec.defect_id}的防护",
                    "priority": "MEDIUM"
                })
        
        # 规则4: 执行时间控制
        estimated_time = self._estimate_execution_time(current_suite, actions)
        if estimated_time > 600:  # 超过10分钟
            # 标记最低优先级用例待移除
            candidates = self._find_removal_candidates(current_suite)
            for c in candidates[:len(actions)+1]:  # 多移除一些给余量
                actions.append({
                    "action": "REMOVE_CANDIDATE",
                    "test": c,
                    "reason": "套件执行时间超标，需精简"
                })
        
        return actions
```

#### 3.2 不稳定测试（Flaky Test）检测与治理

**Flaky Test 定义**：
在不改变代码和测试的前提下，同一测试用例在多次执行中产生不一致的结果（时而通过、时而失败）。

**检测方法**：

##### 方法一：统计性识别（推荐）
```python
class FlakyTestDetector:
    def __init__(self, failure_threshold=0.15, min_runs=10):
        """
        failure_threshold: 失败率超过此值视为可疑flaky
        min_runs: 至少执行多少次才开始判断
        """
        self.failure_threshold = failure_threshold
        self.min_runs = min_runs
    
    def analyze(self, test_execution_history):
        """
        分析测试执行历史，识别flaky测试
        """
        flaky_candidates = []
        
        for test_name, runs in test_execution_history.items():
            if len(runs) < self.min_runs:
                continue
            
            total = len(runs)
            failures = sum(1 for r in runs if not r.passed)
            failure_rate = failures / total
            
            # 计算失败的分布模式
            recent_failures = sum(1 for r in runs[-5:] if not r.passed)
            
            if failure_rate >= self.failure_threshold and 0 < failure_rate < 1.0:
                # 进一步分析失败模式
                pattern = self._classify_failure_pattern(runs)
                
                flaky_candidates.append({
                    "test_name": test_name,
                    "total_runs": total,
                    "failure_count": failures,
                    "failure_rate": round(failure_rate * 100, 1),
                    "pattern": pattern,
                    "severity": self._assess_severity(failure_rate, pattern),
                    "suggested_action": self._recommend_action(pattern),
                    "recent_failure_streak": recent_failures
                })
        
        # 按严重程度排序
        return sorted(flaky_candidates, key=lambda x: x['severity'], reverse=True)
    
    def _classify_failure_pattern(self, runs):
        """分类失败模式"""
        failures = [i for i, r in enumerate(runs) if not r.passed]
        if not failures:
            return "stable"
        
        intervals = [failures[i+1] - failures[i] for i in range(len(failures)-1)]
        avg_interval = sum(intervals) / len(intervals) if intervals else 0
        
        if avg_interval <= 2:
            return "clustered"  # 成簇失败 — 可能与环境状态相关
        elif len(set(r.error_message for r in runs if not r.passed)) == 1:
            return "consistent_error"  # 相同错误 — 可能是竞态条件
        else:
            return "random"  # 随机失败 — 最难诊断
    
    def _assess_severity(self, failure_rate, pattern):
        if failure_rate > 0.4 or pattern == "random":
            return "CRITICAL"
        elif failure_rate > 0.25 or pattern == "consistent_error":
            return "HIGH"
        else:
            return "MEDIUM"
    
    def _recommend_action(self, pattern):
        recommendations = {
            "clustered": "隔离执行、增加重试机制、检查共享状态",
            "consistent_error": "添加调试日志、分析竞态条件、加锁或串行化",
            "random": "全面审查测试设计、替换不确定断言、固定外部依赖",
            "stable": "无需操作"
        }
        return recommendations.get(pattern, "进一步调查")
```

##### 方法二：自动重试确认
在CI中对失败的测试自动重试N次（通常2-3次），如果重试后通过则标记为suspected-flaky。

**Flaky Test 分级处理策略**：

| 等级 | 失败率 | 处理方式 | 时限 |
|-----|-------|---------|------|
| 🟢 观察 | 5%-15% | 标记@flaky，从主套件隔离，持续监控 | 3个工作日内根因分析 |
| 🟠 警告 | 15%-30% | 从回归套件暂时移除，创建修复任务 | 本迭代内修复 |
| 🔴 阻塞 | >30% 或 在冒烟套件中 | 立即禁用并升级为最高优先级Bug | 24小时内修复或提供替代方案 |

**常见Flaky根因及解决方案**：

| 根因类别 | 典型表现 | 解决方案 |
|---------|---------|---------|
| 竞态条件 | 并发测试间互相干扰 | 串行化执行、独立测试数据库、锁机制 |
| 时间依赖 | 断言涉及时钟/超时 | 使用可控时钟（FakeTimer）、放宽时间窗口 |
| 顺序依赖 | 测试B依赖测试A的状态 | 强化Setup/Teardown、消除共享状态 |
| 外部依赖不稳定 | API Mock偶尔失败 | 使用更稳定的Stub、增加容错重试 |
| 资源泄漏 | 文件句柄/数据库连接未释放 | 强制Teardown清理、使用上下文管理器 |
| 非确定性数据 | 随机数/UUID/HASH相关断言 | 固定种子、使用确定性替身 |
| 并行执行冲突 | 并行Worker间的资源竞争 | 降低并行度、资源隔离分配 |

#### 3.3 测试去重

**去重目标**：消除冗余测试用例，减少维护成本和执行时间，同时保持等效的缺陷捕获能力。

**去重检测维度**：

| 维度 | 检测方法 | 合并阈值 |
|-----|---------|---------|
| 代码相似度 | AST结构比对或文本编辑距离 | 相似度>80% |
| 覆盖重叠度 | 覆盖的代码行/分支交集比例 | 重叠度>90% |
| 断言等价性 | 断言逻辑的语义分析 | 完全等价 |
| 数据差异度 | 仅测试数据不同的参数化测试 | 属正常情况，不需合并 |

**去重执行流程**：
```python
class TestDeduplicator:
    def find_duplicates(self, test_suite):
        """
        发现可合并的重复/近似重复测试
        """
        duplicates = []
        tests = list(test_suite.tests)
        
        for i in range(len(tests)):
            for j in range(i+1, len(tests)):
                t1, t2 = tests[i], tests[j]
                
                code_sim = self._code_similarity(t1, t2)
                coverage_overlap = self._coverage_overlap(t1, t2)
                
                if code_sim > 0.8 and coverage_overlap > 0.9:
                    duplicates.append({
                        "test_a": t1.name,
                        "test_b": t2.name,
                        "similarity": round(code_sim * 100, 1),
                        "coverage_overlap": round(coverage_overlap * 100, 1),
                        "recommendation": self._merge_recommendation(t1, t2),
                        "risk_assessment": self._assess_merge_risk(t1, t2)
                    })
        
        return duplicates
    
    def _merge_recommendation(self, t1, t2):
        """生成合并建议"""
        # 选择保留哪个测试的规则
        if t1.assertion_count > t2.assertion_count:
            keep, remove = t1, t2
        elif t2.assertion_count > t1.assertion_count:
            keep, remove = t2, t1
        else:
            # 断言数相同，保留命名更好的
            keep = t1 if len(t1.name) >= len(t2.name) else t2
            remove = t2 if keep == t1 else t1
        
        diff_assertions = self._find_unique_assertions(remove, keep)
        
        return {
            "keep": keep.name,
            "remove": remove.name,
            "action": f"将{remove.name}中的独有断言合并到{keep.name}",
            "unique_assertions_in_removed": diff_assertions
        }
    
    def _assess_merge_risk(self, t1, t2):
        """评估合并风险"""
        risk_factors = []
        
        # 如果两个测试有不同的标记，合并需谨慎
        if set(t1.tags) != set(t2.tags):
            risk_factors.append("标记不同，合并后需确认标记语义")
        
        # 如果属于不同测试类/文件
        if t1.file_path != t2.file_path:
            risk_factors.append("跨文件测试，合并可能影响组织结构")
        
        # 如果有不同关联的缺陷ID
        if t1.linked_defects != t2.linked_defects:
            risk_factors.append("关联不同缺陷，需保留追溯关系")
        
        return {
            "risk_level": "HIGH" if len(risk_factors) > 1 else ("MEDIUM" if risk_factors else "LOW"),
            "factors": risk_factors
        }
```

#### 3.4 回归测试执行编排

**执行计划生成**：
```python
class RegressionExecutionPlanner:
    def create_plan(self, scope_analysis, resource_constraints):
        """
        基于影响分析和资源约束生成最优执行计划
        """
        plan = {
            "phases": [],
            "estimated_total_time": 0,
            "parallel_groups": []
        }
        
        # Phase 1: 冒烟测试（始终首先执行）
        plan["phases"].append({
            "name": "smoke",
            "tests": scope_analysis.smoke_suite,
            "mode": "sequential",
            "blocking": True,  # 冒烟失败则终止后续阶段
            "timeout": 600     # 10分钟硬超时
        })
        
        # Phase 2: 直接影响域测试
        direct_tests = scope_analysis.directly_affected_tests
        if direct_tests:
            plan["phases"].append({
                "name": "direct_impact",
                "tests": direct_tests,
                "mode": "parallel",
                "workers": min(resource_constraints.max_workers, 4),
                "blocking": False
            })
        
        # Phase 3: 间接影响域测试
        indirect_tests = scope_analysis.indirectly_affected_tests
        if indirect_tests:
            plan["phases"].append({
                "name": "indirect_impact",
                "tests": indirect_tests,
                "mode": "parallel",
                "workers": min(resource_constraints.max_workers, 4),
                "blocking": False
            })
        
        # Phase 4: 全量回归（仅在需要时）
        if scope_analysis.requires_full_regression:
            plan["phases"].append({
                "name": "full_regression",
                "tests": scope_analysis.full_test_suite,
                "mode": "parallel",
                "workers": resource_constraints.max_workers,
                "blocking": False
            })
        
        # 计算总时间估算
        plan["estimated_total_time"] = sum(
            self._estimate_phase_time(phase) for phase in plan["phases"]
        )
        
        return plan
    
    def optimize_for_time_budget(self, plan, time_budget_seconds):
        """
        在时间预算约束下优化执行计划
        """
        current_estimate = plan["estimated_total_time"]
        
        if current_estimate <= time_budget_seconds:
            return plan  # 无需优化
        
        # 按优先级裁剪非冒烟阶段的测试
        remaining_budget = time_budget_seconds - self._estimate_phase_time(plan["phases"][0])
        
        for phase in plan["phases"][1:]:
            phase_time = self._estimate_phase_time(phase)
            if remaining_budget <= 0:
                phase["tests"] = []  # 清空此阶段
                continue
            
            if phase_time > remaining_budget:
                # 按风险评分裁剪测试
                sorted_tests = sorted(
                    phase["tests"],
                    key=lambda t: t.risk_score,
                    reverse=True
                )
                # 保留能在预算内完成的最高风险测试
                fitted_tests = []
                accumulated_time = 0
                for test in sorted_tests:
                    if accumulated_time + test.avg_duration <= remaining_budget:
                        fitted_tests.append(test)
                        accumulated_time += test.avg_duration
                    else:
                        break
                phase["tests"] = fitted_tests
                remaining_budget -= accumulated_time
            else:
                remaining_budget -= phase_time
        
        plan["estimated_total_time"] = time_budget_seconds - max(0, remaining_budget)
        plan["optimization_applied"] = True
        plan["truncated_phases"] = [
            p["name"] for p in plan["phases"] 
            if len(p["tests"]) < getattr(p.get('original_test_count', 0), 'int', lambda: len(p["tests"]))()
        ]
        
        return plan
```

### 阶段四：Verify

#### 4.1 回归执行结果验证
- 确认所有计划的测试均已执行（无遗漏）
- 验证失败测试的分类正确性（真正的回归缺陷 vs Flaky vs 环境问题）
- 确认执行日志完整且可追溯
- 验证执行时间在预算范围内

#### 4.2 缺陷分类与归因
- 将失败测试归入以下类别：
  - **真正的回归缺陷**：由本次变更引入的缺陷 → 升级给开发团队
  - **预已存在的缺陷**：之前就存在但未被发现的缺陷 → 创建技术债务记录
  - **测试本身缺陷**：测试代码有问题 → 转交给TDD执行司修复
  - **环境/基础设施问题**：测试环境异常 → 转交给测试框架司排查
  - **Flaky Test**：不稳定测试 → 进入Flaky治理流程

#### 4.3 回归效果度量
- 计算本轮回归的缺陷发现率
- 统计回归测试的有效性（发现的真缺陷数 / 总失败数）
- 追踪从回归发现缺陷到修复的平均时长
- 度量回归测试的投资回报率（ROI）

### 阶段五：Record

#### 5.1 回归执行档案
- 每次回归的完整执行报告（计划 vs 实际）
- 变更集合与回归范围的映射记录
- 失败测试的详细信息和截图/日志附件
- 缺陷归因结论和后续跟踪信息

#### 5.2 冒烟套件变更日志
- 新增/移除的冒烟测试用例及理由
- 套件执行时间的趋势变化
- 套件有效性的定期评审结论

#### 5.3 Flaky Test治理台账
- 所有被识别的不稳定测试及其处理状态
- 每个Flaky Test的根因分析记录和修复方案
- Flaky率的趋势监控数据

#### 5.4 协作记录
- 向TDD执行司发送的测试缺陷转交请求
- 向测试框架司发送的环境问题排查请求
- 向覆盖率分析司提供的回归执行覆盖率数据

## 典型自主场景

### 场景1：PR触发的自动化增量回归

**场景描述**：开发者提交了一个修改了用户认证模块的PR，需要自动决定回归范围

**自主执行过程**：
1. **感知**：接收PR事件，解析出变更涉及 `auth/token_manager.py` 和 `auth/middleware.py` 两个文件
2. **决策**：
   - 变更类型判定：认证核心逻辑变更 → 高风险
   - 影响分析：token_manager被15个模块导入，middleware拦截所有API请求
   - 策略选择：冒烟 + 直接影响域 + 导入依赖方测试（第二优先级全覆盖）
3. **执行**：
   - Phase 1: 冒烟测试（28个用例，预计4分钟）→ 全部通过 ✅
   - Phase 2: auth模块全部测试（45个用例，预计8分钟）→ 2个失败 ❌
   - Phase 3: 15个导入依赖模块的相关测试（120个用例，预计25分钟）→ 1个失败 ❌
4. **验证**：3个失败均为真正的回归缺陷（Token过期时间计算错误导致）
5. **输出**：生成PR评论格式的回归报告，标注3个回归缺陷及具体位置
6. **记录**：存档回归报告，通知开发者修复

### 场景2：Flaky Test爆发时的紧急治理

**场景描述**：某日CI中发现测试通过率突然从98%下降至82%，大量测试间歇性失败

**自主执行过程**：
1. **感知**：监控系统告警，检测到18个测试出现非确定性失败
2. **决策**：启动Flaky Test紧急响应流程
3. **执行**：
   - 对18个可疑测试各执行10次重试，确认其中14个为真正Flaky（失败率15%-45%）
   - 分类Flaky模式：6个竞态条件、4个时间依赖、3个顺序依赖、1个随机
   - 即时措施：
     - 将14个Flaky测试从主套件移至隔离套件（@flaky标记）
     - 其中2个位于冒烟套件中的Flaky → 立即禁用并创建P0 Bug
     - 启动根因分析任务
4. **验证**：主套件通过率恢复至99.2%
5. **输出**：发布Flaky紧急治理报告，分配修复任务
6. **记录**：更新Flaky台账，设置7天后的治理效果复查

### 场景3：发布前全量回归编排

**场景描述**：v2.4.0版本即将发布，需要在有限的时间窗口内完成全面回归验证

**自主执行过程**：
1. **感知**：收到发布计划，回归时间预算为3小时，涉及上次全量回归以来累计200+个提交
2. **决策**：采用分阶段全量回归策略
3. **执行**：
   - Phase 1: 冒烟测试（35用例，5分钟）→ 通过 ✅
   - Phase 2: 核心模块全量测试（payment/order/user/auth，300用例，40分钟，8 Worker并行）→ 通过 ✅
   - Phase 3: 通用模块全量测试（utils/helpers/common，250用例，30分钟，8 Worker并行）→ 3个Flaky（已隔离）
   - Phase 4: 集成/E2E测试（80用例，60分钟，串行）→ 1个失败（环境问题，重试后通过）
   - Phase 5: 安全专项测试（25用例，15分钟）→ 通过 ✅
   - 总耗时：约150分钟（在3小时预算内）
4. **验证**：确认所有非Flaky测试均通过，环境问题已记录
5. **输出**：签署回归通过决议，附详细执行报告
6. **记录**：归档发布回归报告，更新下次发布的基线数据

## 决策框架

### 回归范围选择决策树

```
收到回归触发信号
  │
  ├─ 触发类型？
  │    ├─ PR提交 → 增量回归
  │    │    ├─ 变更文件 ≤5 且低风险？
  │    │    │    └─ 是 → 冒烟 + 直接影响域
  │    │    └─ 否 → 冒烟 + 影响域 + 依赖方
  │    │
  │    ├─ 定时任务(每日) → 增量回归(当日变更)
  │    │
  │    ├─ 定时任务(每周) → 模块轮转全量
  │    │
  │    └─ 发布前 → 分阶段全量回归
  │         ├─ 冒烟失败？ → 🔴 阻塞发布
  │         ├─ 核心模块失败？ → 🔴 阻塞发布
  │         ├─ 一般模块失败？ → 🟡 评估风险后决定
  │         └─ 全部通过 → 🟢 签署放行
  │
  └─ 特殊触发？
       ├─ 生产事故后 → 全量回归 + 相关专项加深
       ├─ 安全漏洞修复后 → 安全测试全量 + 影响域
       └─ 大规模重构后 → 全量回归（可能分多轮）
```

### 测试失效处理决策矩阵

```
回归测试发现失败
  │
  ├─ 首次失败？
  │    └─ 是 → 自动重试1次
  │         ├─ 重试通过 → 标记@suspected_flaky，继续监控
  │         └─ 重试仍失败 → 进入分类流程
  │
  ├─ 失败分类
  │    ├─ 真正回归缺陷 → 🐛 创建Bug，指派开发者，阻塞合并/发布
  │    ├─ 预已存在缺陷 → 📝 记录技术债务，不阻塞但需关注
  │    ├─ 测试代码缺陷 → 🔧 转TDD执行司修复，暂跳过该测试
  │    ├─ 环境问题 → 🛠️ 转测试框架司排查，重试或切换节点
  │    └─ Flaky Test → ⚠️ 进入Flaky治理流程
  │
  └─ 影响评估
       ├── 在冒烟套件中？ → 🔴 最高优先级处理
       ├── 在核心模块中？ → 🟠 高优先级处理
       └── 在边缘模块中？ → 🟡 正常优先级处理
```

## 安全与治理

### 回归测试纪律红线
1. **严禁跳过冒烟测试**：任何情况下不得在没有通过冒烟测试的情况下继续后续回归阶段。
2. **严禁忽略Flaky Test**：不得将Flaky Test静默地视为"偶发问题"而不处理。
3. **严禁无依据地缩减回归范围**：范围缩减必须基于影响分析，不能因为"赶时间"而随意裁剪。
4. **严禁篡改回归结果**：不得为了"让数字好看"而人为修改测试结果或排除失败测试。

### 自主权限边界
- 本司有权自主决定每次回归的具体范围和执行策略
- 本司有权自主维护和演化冒烟测试套件
- 本司有权自主实施Flaky Test的隔离和处理措施
- 本司有权自主进行测试去重和套件精简
- 本司无权自行修改业务测试用例的内容（仅可调整执行策略）
- 本司无权自行设定覆盖率目标（需遵从覆盖率分析司的标准）

### 变更管控要求
- 冒烟套件的重大变更（增删>5个用例）需通知TDD执行司
- Flaky Test的永久禁用需经过根因分析和审批
- 回归策略的重大调整需提前告知所有相关方

## 协作关系

### 上游协作者
- **工部（技术架构）**：遵循其设定的模块边界和依赖关系来进行影响分析
- **户部（项目管理）**：接收其发布的发布计划和里程碑，协调回归测试的资源安排
- **刑部（质量管理）**：接收其发布的质量标准和验收准则，作为回归通过的基准

### 平级协作者
- **TDD执行司（tdd_execution_si）**：
  - 向其转交确认为测试代码缺陷的失败用例修复任务
  - 接收其新增的测试用例，将其纳入回归候选池
  - 共享回归发现的业务缺陷信息，帮助其理解易出错区域

- **测试框架司（test_framework_si）**：
  - 向其转交确认为环境/基础设施问题的排查请求
  - 请求其支持Flaky Test诊断所需的工具增强（如执行隔离、调试模式）
  - 协作设计测试执行环境的稳定性和可靠性改进方案

- **覆盖率分析司（coverage_analysis_si）**：
  - 向其提供回归执行的覆盖率数据，辅助其完善覆盖率基线
  - 接收其提供的模块覆盖率热力图，辅助回归范围决策
  - 协作设计覆盖率门禁规则（如回归必须满足的最低覆盖率）

### 下游消费者
- **发布管理团队**：消费回归通过/阻塞决议，作为发布决策的关键输入
- **开发团队**：接收回归发现的缺陷报告，进行修复
- **运维团队**：接收回归通过的环境验证结果，作为部署的前提条件
- **管理层**：接收回归质量趋势报告，了解整体质量态势

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Performance Benchmarker | 性能基准部 | 基准测试 | 性能回归检测与基线对比 |
| API Tester | 接口测试部 | 合约验证 | API回归验证与契约一致性检查 |

### Agent 协作工作流

1. **变更感知**：regression_testing_si 监听代码变更事件，执行影响分析和范围决策
2. **基础回归编排**：本司按既定策略编排冒烟→直接影响域→间接影响域→全量（可选）的回归执行计划
3. **Agent 委派**：
   - 变更涉及性能敏感路径（算法优化、缓存策略、数据库查询变更等） → 调用 **Performance Benchmarker** 在回归流程中插入性能基准测试环节，对比变更前后的关键性能指标（响应时间、吞吐量、资源消耗），识别性能退化
   - 变更涉及API接口（签名变更、新增端点、协议升级等） → 调用 **API Tester** 执行API级别的契约回归验证，确保所有调用方的兼容性不受破坏
4. **结果整合**：将Agent返回的性能基线数据和API契约验证结果融入回归执行报告
5. **综合裁决**：结合功能回归、性能回归和API契约三方面结果，给出最终的通过/阻塞/有条件通过判定
6. **持续监控**：将性能基线和API契纳入回归基线管理，后续每次回归自动对比

### 典型协作场景

- **场景1 - 部署后性能回归验证**：一次包含数据库查询优化的PR合并 → regression_testing_si 执行功能回归的同时委派 Performance Benchmarker 对相关API端点进行性能基线对比 → 发现P95延迟从120ms恶化至350ms（超过阈值） → 标记为"功能通过但性能阻塞"，附带详细的火焰图和慢查询分析
- **场景2 - API版本升级后契约回归**：REST API从v1升级至v2，部分字段类型变更 → regression_testing_si 确定全量回归范围 → API Tester 并行执行所有已注册客户端的契约验证（消费者驱动契约测试） → 发现3个内部服务因未适配新字段格式而失败 → 输出精确到字段级的兼容性修复清单
- **场景3 - Chaos实验后回归确认**：Harness Chaos Engineering 完成故障注入实验后 → regression_testing_si 触发Chaos后专项回归 → Performance Benchmarker 验证系统在恢复后的性能是否回到基线水平 → API Tester 验证故障期间受影响的API是否完全恢复功能正确性 → 三方联合签署"系统恢复完整性确认"

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块
- Harness CD 部署验证（Deployment Verification）
- Harness Chaos Engineering 混沌实验后验证（Post-Chaos Validation）
- Harness Service Reliability Index (SRI) 服务可靠性指标集成

### 实践指南
- **CD部署验证集成**：将regression_testing_smoke的冒烟测试套件配置为Harness CD的Deployment Verification步骤，在每次部署到Staging/Production环境后自动触发快速冒烟回归（≤10分钟），验证部署成功性
- **Chaos实验后回归联动**：在Harness Chaos Engineering工作流中配置Post-Chaos Hook，混沌实验结束后自动触发regression_testing_si的恢复完整性回归验证（含功能+性能+API三重验证），确保系统从混沌状态完全恢复正常
- **SRI指标贡献**：将regression_testing_si的回归通过率、Flaky率、平均发现缺陷数等指标接入Harness SRI计算模型，作为服务可靠性评分的重要输入维度，实现质量数据与可靠性数据的统一视图

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改回归套件配置、冒烟测试用例、测试计划文档时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/regression/smoke_test_suite.yaml",
      agent_id="回归测试司",
      lock_type=LockType.EXCLUSIVE,
      priority=9,
      timeout=180.0
  )
  ```
- **读锁**：读取回归套件、历史测试报告、缺陷关联数据时申请读锁（高频查询场景）
- **释放锁**：套件更新和维护操作完成后立即释放锁，避免阻塞其他司的回归查询

#### 终端会话池使用
- 从MARC终端会话池获取会话运行回归测试套件、冒烟测试、Chaos后验证命令
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（完整回归可能耗时较长，特别是E2E场景）

#### 并发安全注意事项
- 回归套件是核心共享资产，写入时必须独占锁保护
- 多环境并行回归时需锁定各自环境的套件配置
- 死锁预防：按固定顺序申请锁（先锁回归套件→再锁冒烟配置→最后锁测试计划）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | 冒烟测试设计提示词、回归策略提示词、缺陷关联分析提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许回归测试操作（套件管理/执行/分析），禁止修改生产代码 | 全自动 |
| **规则校验层** | 输出格式：YAML回归套件、JSON测试报告、Markdown缺陷关联矩阵 | 全自动 |
| **兜底恢复层** | 回归失败时自动触发告警并提供快速回滚建议或热修复方案 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于冒烟测试设计、回归套件维护、缺陷关联分析）
   - 示例：直接编辑YAML回归套件、手动调整测试优先级、编写缺陷关联分析报告
   - 优势：精确控制回归范围、可逐步验证完整性、可随时回滚套件变更

2. 🥈 **规划脚本操作**（适用于自动化回归执行、周期性套件健康检查）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查回归测试时间配额和环境配额
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的回归策略
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限紧急生产回归验证、Chaos后快速恢复验证等极少数场景）
   - ⚠️ 必须预演影响范围（回归结果直接影响发布决策）
   - ⚠️ 生产环境回归需获得关键方Ack并留痕
   - 推荐使用PS7适配器转换pytest/playwright/cypress等测试工具命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- E2E测试：playwright test / cypress run / selenium等命令在PS7中原生可用
- API测试：newman / rest-assured / httpie等工具直接执行
- 冒烟测试：运行精简版测试套件的快速验证命令
- 编码：确保所有输出 UTF-8 无 BOM（回归报告和审计记录）

### 与其他司的协作接口

- 上游依赖：TDD执行司（接收稳定测试用例纳入回归套件）、覆盖率分析司（获取覆盖盲区补充回归）
- 下游输出：基础设施司（推送部署前回归验证结果）、协同调度司（报告回归状态和发布就绪度）
- 数据交换格式：YAML / JSON / Markdown（统一UTF-8无BOM）
