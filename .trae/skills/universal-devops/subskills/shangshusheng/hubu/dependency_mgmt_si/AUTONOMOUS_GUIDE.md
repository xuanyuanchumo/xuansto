# 依赖管理司 自主操作指南 (Autonomous Operation Guide)

## 概述

依赖管理司（Dependency Management Si）是尚书省·户部下属四司之一，负责**项目依赖的全生命周期自主管理**。本司核心使命：自动化处理多语言、多包管理器场景下的依赖升级决策，实现从漏洞扫描到安全修复的端到端自主闭环。

### 定位

- **上级机构**：尚书省 · 户部（Hubu）
- **同级司署**：环境配置司、资源优化司、基础设施司
- **核心能力域**：依赖解析、版本升级、漏洞治理、许可证合规、图谱分析
- **自主等级**：L3（条件自主）— 可在预设风险阈值内独立完成升级决策与执行

## 核心原则

1. **语义化版本优先（SemVer）**：严格遵循 MAJOR.MINOR.PATCH 规范，对 breaking change 保持最高警惕
2. **安全驱动升级**：CVE 漏洞修复优先级高于功能升级，Critical/High 级别漏洞触发自动升级流程
3. **渐进式变更**：避免批量大版本跳跃，采用分阶段、可回滚的升级策略
4. **可追溯性**：每次依赖变更必须关联 issue/PR，保留完整的变更理由和测试结果
5. **许可证合规**：引入新依赖前必须完成许可证兼容性检查，禁止违规许可证进入生产代码

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 多包管理器依赖扫描

本司支持 6 种主流包管理器的自主扫描与分析：

| 包管理器 | 锁文件 | 扫描命令 | 解析工具 |
|---------|--------|---------|---------|
| **pip** | requirements.txt / pip.lock | `pip list --outdated --format=json` | pip-audit, safety |
| **poetry** | pyproject.toml / poetry.lock | `poetry show --outdated --no-ansi` | poetry-plugin-export |
| **npm** | package.json / package-lock.json | `npm outdated --json` | npm audit, snyk |
| **yarn** | package.json / yarn.lock | `yarn outdated --json` | yarn audit, dependabot |
| **cargo** | Cargo.toml / Cargo.lock | `cargo outdated` | cargo audit, diesel |
| **go.mod** | go.mod / go.sum | `go list -m -u all` | govulncheck, nancy |

**统一扫描入口脚本**：

```bash
#!/bin/bash
# universal_dep_scan.sh — 多包管理器统一依赖扫描
set -euo pipefail
OUTPUT_DIR="/tmp/dep-scan-$(date +%Y%m%d_%H%M%S)"
mkdir -p "${OUTPUT_DIR}"

scan_pip() {
    if [[ -f requirements.txt ]]; then
        echo "[PIP] Scanning requirements.txt..."
        pip list --outdated --format=json 2>/dev/null > "${OUTPUT_DIR}/pip_outdated.json" || true
        pip-audit --format=json 2>/dev/null > "${OUTPUT_DIR}/pip_vuln.json" || true
    fi
}

scan_poetry() {
    if [[ -f pyproject.toml ]] && grep -q '\[tool.poetry\]' pyproject.toml; then
        echo "[POETRY] Scanning pyproject.toml..."
        poetry show --outdated --no-ansi 2>/dev/null > "${OUTPUT_DIR}/poetry_outdated.txt" || true
        poetry export --without-hashes -f requirements.txt 2>/dev/null > "${OUTPUT_DIR}/poetry_export.txt" || true
    fi
}

scan_npm() {
    if [[ -f package.json ]]; then
        echo "[NPM] Scanning package.json..."
        npm outdated --json 2>/dev/null > "${OUTPUT_DIR}/npm_outdated.json" || true
        npm audit --json 2>/dev/null > "${OUTPUT_DIR}/npm_audit.json" || true
    fi
}

scan_yarn() {
    if [[ -f yarn.lock ]]; then
        echo "[YARN] Scanning yarn.lock..."
        yarn outdated --json 2>/dev/null > "${OUTPUT_DIR}/yarn_outdated.json" || true
        yarn audit --json 2>/dev/null > "${OUTPUT_DIR}/yarn_audit.json" || true
    fi
}

scan_cargo() {
    if [[ -f Cargo.toml ]]; then
        echo "[CARGO] Scanning Cargo.toml..."
        cargo outdated 2>/dev/null > "${OUTPUT_DIR}/cargo_outdated.txt" || true
        cargo audit 2>/dev/null > "${OUTPUT_DIR}/cargo_audit.json" || true
    fi
}

scan_go() {
    if [[ -f go.mod ]]; then
        echo "[GO] Scanning go.mod..."
        go list -m -u all 2>/dev/null > "${OUTPUT_DIR}/go_outdated.txt" || true
        govulncheck ./... 2>/dev/null > "${OUTPUT_DIR}/govulncheck.txt" || true
    fi
}

# 执行所有扫描
for scanner in scan_pip scan_poetry scan_npm scan_yarn scan_cargo scan_go; do
    $scanner
done

echo ""
echo "========================================="
echo "扫描完成！结果目录: ${OUTPUT_DIR}"
echo "文件列表:"
ls -la "${OUTPUT_DIR}/"
```

#### 1.2 语义版本冲突自主解析

```python
"""
SemVer 冲突解析引擎 — 自动分析依赖版本约束的兼容性
"""

import re
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class VersionBumpType(Enum):
    MAJOR = "major"      # 不兼容的 API 变更
    MINOR = "minor"      # 向后兼容的功能新增
    PATCH = "patch"      # 向后兼容的问题修复

class ConflictSeverity(Enum):
    CRITICAL = 5   # 必须立即解决，阻塞构建
    HIGH = 4       # 高优先级，建议尽快解决
    MEDIUM = 3     # 中等优先级，计划内解决
    LOW = 2        # 低优先级，可延后
    INFO = 1       # 信息性提示，无需操作

@dataclass
class SemVer:
    major: int
    minor: int
    patch: int
    prerelease: str = ""
    build: str = ""

    @classmethod
    def parse(cls, version_str: str) -> 'SemVer':
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-(.+))?(?:\+(.+))?$', version_str.strip())
        if not match:
            raise ValueError(f"Invalid semver: {version_str}")
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4) or "",
            build=match.group(5) or ""
        )

    def bump_type_to(self, other: 'SemVer') -> VersionBumpType:
        if self.major != other.major:
            return VersionBumpType.MAJOR
        elif self.minor != other.minor:
            return VersionBumpType.MINOR
        else:
            return VersionBumpType.PATCH

    def __lt__(self, other): ...
    def __le__(self, other): ...
    # ... 完整比较运算符实现

@dataclass
class DependencyConflict:
    package: str
    current_version: SemVer
    target_version: SemVer
    bump_type: VersionBumpType
    constraints: list[str]          # 各处对该包的版本约束
    conflict_reason: str
    severity: ConflictSeverity
    suggested_resolution: str
    risk_score: float               # 0.0 - 10.0

def analyze_version_conflicts(lock_file_path: str) -> list[DependencyConflict]:
    """
    分析锁文件中的版本冲突：
    1. 解析所有直接依赖和传递依赖
    2. 检测版本约束矛盾（如 A 需要 flask>=2.0, B 需要 flask<2.0）
    3. 评估每个冲突的影响范围和风险等级
    4. 生成解决方案建议
    """
    conflicts = []
    # ... 解析逻辑
    return conflicts

# 风险评估矩阵
RISK_MATRIX = {
    (VersionBumpType.MAJOR, "direct_dependency"):     9.0,
    (VersionBumpType.MAJOR, "transitive_dependency"): 7.0,
    (VersionBumpType.MINOR, "direct_dependency"):     4.0,
    (VersionBumpType.MINOR, "transitive_dependency"): 3.0,
    (VersionBumpType.PATCH, "direct_dependency"):     1.0,
    (VersionBumpType.PATCH, "transitive_dependency"): 0.5,
}
```

#### 1.3 依赖图谱可视化与循环检测

```python
"""
依赖图谱分析引擎 — 循环依赖检测 + 传递依赖深度分析
"""

from collections import defaultdict, deque
import graphviz

class DependencyGraph:
    def __init__(self):
        self.adjacency = defaultdict(set)   # pkg -> set of dependencies
        self.reverse_adj = defaultdict(set) # pkg -> set of dependents
        self.metadata = {}                  # pkg -> {version, license, type}

    def add_edge(self, from_pkg: str, to_pkg: str, **meta):
        self.adjacency[from_pkg].add(to_pkg)
        self.reverse_adj[to_pkg].add(from_pkg)
        self.metadata[to_pkg] = meta

    def detect_cycles(self) -> list[list[str]]:
        """DFS 循环依赖检测，返回所有环路"""
        WHITE, GRAY, BLACK = 0, 1, 2
        color = defaultdict(int)
        parent = {}
        cycles = []

        def dfs(node, path):
            color[node] = GRAY
            for neighbor in self.adjacency[node]:
                if color[neighbor] == GRAY:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                elif color[neighbor] == WHITE:
                    parent[neighbor] = node
                    dfs(neighbor, path + [neighbor])
            color[node] = BLACK

        for node in list(self.adjacency.keys()):
            if color[node] == WHITE:
                dfs(node, [node])
        return cycles

    def get_transitive_deps(self, pkg: str, max_depth: int = 10) -> dict[str, int]:
        """BFS 获取传递依赖及其层级深度"""
        visited = {}
        queue = deque([(pkg, 0)])
        while queue:
            current, depth = queue.popleft()
            if depth > max_depth:
                continue
            for dep in self.adjacency[current]:
                if dep not in visited:
                    visited[dep] = depth + 1
                    queue.append((dep, depth + 1))
        return visited

    def find_bottleneck_packages(self) -> list[tuple[str, int]]:
        """找出被最多其他包依赖的'瓶颈包'（扇入度高）"""
        fan_in = [(pkg, len(deps)) for pkg, deps in self.reverse_adj.items()]
        return sorted(fan_in, key=lambda x: -x[1])

    def render_graph(self, output_path: str = "dep_graph"):
        """使用 Graphviz 渲染依赖关系图"""
        dot = graphviz.Digraph(comment='Dependency Graph', format='png')
        dot.attr(rankdir='TB', splines='ortho')
        for pkg in self.adjacency:
            dot.node(pkg, pkg)
            for dep in self.adjacency[pkg]:
                dot.edge(pkg, dep)
        dot.render(output_path, cleanup=True)

# 使用示例
graph = DependencyGraph()
graph.add_edge("myapp", "flask", version="2.3.0", license="BSD-3")
graph.add_edge("flask", "jinja2", version="3.1.0", license="BSD-3")
graph.add_edge("myapp", "sqlalchemy", version="2.0.0", license="MIT")
graph.add_edge("sqlalchemy", "greenlet", version="2.0.0", license="MIT")

cycles = graph.detect_cycles()
if cycles:
    print(f"⚠️ 发现 {len(cycles)} 个循环依赖:")
    for i, cycle in enumerate(cycles, 1):
        print(f"  环路{i}: {' → '.join(cycle)}")

bottlenecks = graph.find_bottleneck_packages()
print("\n📊 瓶颈包排名（被依赖数）:")
for pkg, count in bottlenecks[:10]:
    print(f"  {pkg}: {count} 个上游依赖")

graph.render_graph("/tmp/dependency_graph")
```

#### 1.4 CVE 漏洞扫描结果解读

**漏洞严重程度分级标准**：

| CVSS 分数范围 | 严重级别 | 自主响应策略 | SLA 目标 |
|-------------|---------|------------|---------|
| 9.0 - 10.0 | **CRITICAL** | 立即阻断 + 强制升级 + 安全告警 | < 4h |
| 7.0 - 8.9 | **HIGH** | 优先升级 + 创建安全工单 | < 24h |
| 4.0 - 6.9 | **MEDIUM** | 计划升级 + 下次发版纳入 | < 7d |
| 0.1 - 3.9 | **LOW** | 记录跟踪 + 定期回顾 | < 30d |

**CVE 解读与修复优先级算法**：

```python
@dataclass
class CVEVulnerability:
    cve_id: str                   # CVE-2024-12345
    affected_package: str         # lodash
    installed_version: str        # 4.17.15
    fixed_version: str            # 4.17.21
    cvss_score: float             # 7.5
    vector_string: str            # CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H
    cwe_id: str                   # CWE-79
    description: str              # Prototype Pollution vulnerability
    published_date: str           # 2024-03-15
    exploit_available: bool       # True
    has_fix: bool                 # True

def calculate_remediation_priority(cve: CVEVulnerability) -> dict:
    """
    综合计算修复优先级分数 (0-100)
    因子：CVSS分 + 利用可行性 + 影响面 + 修复难度
    """
    score = 0

    # 因子1: CVSS 基础分 (权重40%)
    score += cve.cvss_score * 4.0

    # 因子2: 利用可行性 (权重20%)
    if cve.exploit_available:
        score += 20  # 已有公开利用代码
    elif "AV:N" in cve.vector_string and "PR:N" in cve.vector_string:
        score += 15  # 远程无权限即可利用
    else:
        score += 5

    # 因子3: 影响面评估 (权重20%)
    # 判断受影响包是否在关键路径上
    critical_paths = ["express", "flask", "django", "spring-core", "lodash"]
    if cve.affected_package.lower() in [p.lower() for p in critical_paths]:
        score += 20
    elif is_direct_dependency(cve.affected_package):
        score += 12
    else:
        score += 4

    # 因子4: 修复可用性 (权重20%)
    if cve.has_fix and cve.fixed_version:
        score -= 10  # 有现成修复方案，降低紧急度
    else:
        score += 20  # 无修复方案，需缓解措施

    priority = min(100, max(0, score))

    if priority >= 75:
        level = "P0 - 立即修复"
        action = "auto_upgrade_or_block"
    elif priority >= 50:
        level = "P1 - 本周修复"
        action = "create_security_ticket"
    elif priority >= 25:
        level = "P2 - 计划修复"
        action = "schedule_for_next_release"
    else:
        level = "P3 - 低优先级"
        action = "track_only"

    return {
        "cve_id": cve.cve_id,
        "priority_score": priority,
        "priority_level": level,
        "recommended_action": action,
        "suggested_version": cve.fixed_version if cve.has_fix else "N/A",
        "workaround": generate_workaround(cve) if not cve.has_fix else None
    }
```

#### 1.5 许可证兼容性检查

**8类常见许可证兼容矩阵**：

```
                    MIT  Apache-2.0  BSD-2  BSD-3  GPL-2.0  GPL-3.0  LGPL-2.1  AGPL-3.0
MIT                 ✅      ✅        ✅     ✅      ⚠️*     ⚠️*      ⚠️*      ❌
Apache-2.0          ✅      ✅        ✅     ✅      ⚠️*     ⚠️*      ⚠️*      ❌
BSD-2               ✅      ✅        ✅     ✅      ⚠️*     ⚠️*      ⚠️*      ❌
BSD-3               ✅      ✅        ✅     ✅      ⚠️*     ⚠️*      ⚠️*      ❌
GPL-2.0             ❌      ❌        ❌     ❌      ✅       ❌       ⚠️†      ❌
GPL-3.0             ❌      ❌        ❌     ❌      ❌       ✅       ⚠️†      ❌
LGPL-2.1            ⚠️‡    ⚠️‡       ⚠️‡    ⚠️‡     ⚠️†     ⚠️†      ✅       ❌
AGPL-3.0            ❌      ❌        ❌     ❌      ❌       ❌       ❌       ✅

图例：
✅ = 完全兼容，可自由组合
⚠️* = GPL Copyleft 对动态链接有传染性要求，静态链接时需开源整个项目
⚠️† = LGPL 允许动态链接闭源，但修改 LGPL 代码本身必须开源
⚠️‡ = 使用 LGPL 库时，项目整体无需开源，但对库的修改需回馈
❌ = 许可证不兼容，禁止组合使用
```

**许可证检查规则引擎**：

```python
@dataclass
class LicenseCheckResult:
    package: str
    license_id: str
    compatible: bool
    risk_level: str              # SAFE / WARNING / BLOCKED
    issues: list[str]
    recommendation: str

INCOMPATIBLE_PAIRS = [
    ("AGPL-3.0", "proprietary"),  # AGPL 要求网络交互也需开源
    ("GPL-3.0", "proprietary"),   # GPL-3.0 与专有软件不兼容
    ("GPL-2.0", "Apache-2.0"),    # GPL-2.0 的专利终止条款与 Apache-2.0 冲突
]

DANGEROUS_LICENSES = [
    "AGPL-3.0", "AGPL-1.0",       # 强传染性
    "GPL-3.0-only", "GPL-3.0-or-later",
    "SSPL-1.0",                    # Server Side Public License（非OSI认证）
    "Elastic-2.0",                 # Elastic License（限制性）
    "JSON-LICENSE",                # JSON.org 许可证（有争议）
]

def check_license_compatibility(
    project_license: str,
    dep_license: str,
    link_type: str = "dynamic"
) -> LicenseCheckResult:
    """
    检查依赖许可证与项目许可证的兼容性
    link_type: dynamic(动态链接) / static(静态链接) / source(源码包含)
    """
    issues = []

    # 规则1: 检查黑名单许可证
    if dep_license.upper() in [l.upper() for l in DANGEROUS_LICENSES]:
        issues.append(f"危险许可证 '{dep_license}' 可能带来法律风险")

    # 规则2: 检查不兼容配对
    for blocked_a, blocked_b in INCOMPATIBLE_PAIRS:
        if (dep_license.upper() == blocked_a.upper() and
            project_license.upper() == blocked_b.upper()):
            issues.append(f"许可证冲突: {dep_license} 与 {project_license} 不兼容")

    # 规则3: GPL 传染性检查
    if dep_license.upper().startswith("GPL") and link_type == "static":
        issues.append("GPL 许可证在静态链接下具有传染性，可能要求项目开源")

    # 规则4: AGPL 网络使用条款
    if "AGPL" in dep_license.upper():
        issues.append("AGPL 要求通过网络提供服务时也需开源完整源码")

    if len(issues) == 0:
        return LicenseCheckResult(
            package="", license_id=dep_license,
            compatible=True, risk_level="SAFE",
            issues=[], recommendation=f"{dep_license} 与 {project_license} 兼容"
        )
    elif any("不兼容" in i for i in issues):
        return LicenseCheckResult(
            package="", license_id=dep_license,
            compatible=False, risk_level="BLOCKED",
            issues=issues, recommendation="替换为兼容许可证的替代包或移除此依赖"
        )
    else:
        return LicenseCheckResult(
            package="", license_id=dep_license,
            compatible=True, risk_level="WARNING",
            issues=issues, recommendation="可使用但需法务审核确认"
        )
```

### 阶段二：决策（Decide）

#### 2.1 升级决策树

```
START: 检测到可升级依赖
  │
  ├─ 是否存在 CVE 漏洞？
  │   ├─ YES → CVSS ≥ 7.0 (HIGH/CRITICAL)？
  │   │   ├─ YES → 【P0】强制升级，自动创建 PR，通知安全团队
  │   │   └─ NO  → 【P1-P2】纳入下一发版计划
  │   │
  │   └─ NO  → 版本跳跃类型？
  │       ├─ PATCH 升级 → 【自动批准】低风险，可直接执行
  │       ├─ MINOR 升级 → 【有条件批准】需要通过单元测试 + 集成测试
  │       └─ MAJOR 升级 → 【人工审批】需 Breaking Change 分析报告
  │
  └─ END
```

#### 2.2 升级风险评估模型

```python
@dataclass
class UpgradeRiskAssessment:
    package: str
    from_version: str
    to_version: str
    bump_type: VersionBumpType
    risk_score: float              # 0-10
    test_coverage: float           # 该包相关测试覆盖率
    api_surface_change: str        # none / low / medium / high
    community_adoption: float      # 新版本的周下载量占比
    breakage_reports: int          # GitHub Issues 中关于此升级的报错数
    recommendation: str
    rollback_plan_available: bool

def assess_upgrade_risk(package: str, from_ver: str, to_ver: str) -> UpgradeRiskAssessment:
    """
    综合评估单次升级的风险
    """
    from_semver = SemVer.parse(from_ver)
    to_semver = SemVer.parse(to_ver)
    bump = from_semver.bump_type_to(to_semver)

    risk = 0.0

    # 基础风险：版本跳跃类型
    base_risk = {VersionBumpType.MAJOR: 8.0, VersionBumpType.MINOR: 3.0, VersionBumpType.PATCH: 0.5}
    risk += base_risk[bump]

    # API 变更影响（从 CHANGELOG 分析）
    changelog_impact = analyze_changelog_impact(package, from_ver, to_ver)
    risk += changelog_impact * 1.5

    # 测试覆盖率加权
    coverage = get_test_coverage_for_package(package)
    risk *= (1.0 - coverage * 0.5)  # 覆盖率高则降低风险感知

    # 社区反馈因子
    breakage_count = count_breakage_reports(package, to_ver)
    risk += min(breakage_count * 0.5, 3.0)

    risk = min(10.0, max(0.0, risk))

    if risk <= 2.0:
        rec = "AUTO_APPROVE - 低风险，可自主执行"
    elif risk <= 5.0:
        rec = "CONDITIONAL - 通过全量测试套件后执行"
    elif risk <= 7.5:
        rec = "REVIEW_REQUIRED - 需代码审查 + 人工审批"
    else:
        rec = "BLOCKED - 高风险，需详细影响分析 + 灰度验证"

    return UpgradeRiskAssessment(
        package=package, from_version=from_ver, to_version=to_ver,
        bump_type=bump, risk_score=risk,
        test_coverage=coverage, api_surface_change=changelog_impact_label(changelog_impact),
        community_adoption=get_community_adoption(package, to_ver),
        breakage_reports=breakage_count,
        recommendation=rec,
        rollback_plan_available=bump != VersionBumpType.MAJOR or has_rollback_strategy(package)
    )
```

### 阶段三：执行（Execute）

#### 3.1 渐进式升级执行计划

```yaml
# upgrade_plan.yaml — 渐进升级计划模板
metadata:
  plan_id: "UP-20260406-001"
  created_by: "dependency_mgmt_si (autonomous)"
  status: "planning"

phases:
  - phase_id: 1
    name: "信息收集"
    duration: "30min"
    tasks:
      - task: "获取当前依赖快照"
        command: "capture_dependency_snapshot()"
      - task: "分析 CHANGELOG"
        command: "fetch_and_parse_changelog()"
      - task: "识别 Breaking Changes"
        command: "extract_breaking_changes()"
    gate: "info_collection_complete"

  - phase_id: 2
    name: "影响分析"
    duration: "1h"
    tasks:
      - task: "搜索代码中使用该 API 的位置"
        command: "grep_codebase_usage()"
      - task: "评估测试覆盖充分性"
        command: "assess_test_coverage()"
      - task: "生成兼容性适配代码（如需）"
        command: "generate_compat_shim()"
    gate: "impact_analysis_approved"

  - phase_id: 3
    name: "测试验证"
    duration: "2h"
    tasks:
      - task: "运行单元测试"
        command: "run_unit_tests()"
        expected_result: "100% pass"
      - task: "运行集成测试"
        command: "run_integration_tests()"
        expected_result: "100% pass"
      - task: "运行 E2E 测试"
        command: "run_e2e_tests()"
        expected_result: "100% pass"
      - task: "性能基准对比"
        command: "run_performance_baseline()"
        expected_result: "退化 < 5%"
    gate: "all_tests_passed"

  - phase_id: 4
    name: "灰度发布"
    duration: "24-72h"
    tasks:
      - task: "合并到 develop 分支"
        command: "merge_to_develop()"
      - task: "部署到 staging 环境"
        command: "deploy_to_staging()"
      - task: "监控关键指标"
        command: "monitor_metrics(['error_rate', 'latency_p99', 'throughput'])"
      - task: "收集用户反馈"
        command: "aggregate_feedback()"
    gate: "staging_validation_passed"

  - phase_id: 5
    name: "全量发布"
    duration: "1h"
    tasks:
      - task: "合并到 main 分支"
        command: "merge_to_main()"
      - task: "部署到生产环境"
        command: "deploy_to_production()"
      - task: "发布后健康检查"
        command: "post_deploy_health_check()"
    gate: "production_stable"

rollback_plan:
  trigger_conditions:
    - "error_rate_increase > 200%"
    - "latency_p99_increase > 500ms"
    - "any_test_failure_in_gate"
  steps:
    - "revert_merge_commit()"
    - "redeploy_previous_version()"
    - "verify_service_recovery()"
    - "notify_incident_team()"
  max_rollback_time: "10min"
```

#### 3.2 各包管理器升级命令速查

```bash
# === PIP ===
pip install --upgrade package_name==1.2.3
pip compile requirements.in --upgrade-package=package_name  # 使用 pip-tools

# === POETRY ===
poetry add package_name@^1.2.3
poetry update package_name

# === NPM ===
npm install package_name@1.2.3
npm update package_name

# === YARN ===
yarn add package_name@1.2.3
yarn up package_name

# === CARGO ===
cargo update -p package_name --precise 1.2.3

# === GO ===
go get package_name@v1.2.3
go mod tidy
```

### 阶段四：验证（Verify）

#### 4.1 升级后验证矩阵

| 验证维度 | 验证方法 | 通过标准 | 失败动作 |
|---------|---------|---------|---------|
| 编译构建 | `build` 命令 | 零错误零警告 | 回滚 PR |
| 单元测试 | `test:unit` | 100% 通过率 | 定位失败用例 |
| 集成测试 | `test:integration` | 100% 通过率 | 检查 mock/stub |
| E2E 测试 | `test:e2e` | 关键路径全绿 | 回归分析 |
| 类型检查 | `tsc --noEmit` / mypy | 零类型错误 | 补充类型定义 |
| Lint | eslint / flake8 / clippy | 零 error | 自动修复或手动修正 |
| 性能基准 | k6 / wrk / benchmark | 退化 < 5% | 性能调优 |
| 安全扫描 | npm audit / pip-audit | 无 HIGH/CRITICAL | 寻找替代方案 |
| 许可证检查 | license-checker / licensee | 无 BLOCKED | 替换依赖 |
| 依赖完整性 | lock file 一致性 | lock 文件已更新 | 重新锁定 |

#### 4.2 自动化验证流水线

```yaml
# .github/workflows/dependency-upgrade-verify.yml
name: Dependency Upgrade Verification
on:
  pull_request:
    types: [opened, synchronize]
    paths:
      - 'requirements.txt'
      - 'package.json'
      - 'Cargo.toml'
      - 'go.mod'
      - 'pyproject.toml'

jobs:
  verify-upgrade:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup environment
        run: |
          # 根据 lock 文件类型安装对应工具链
          if [ -f package.json ]; then
            corepack enable && corepack prepare yarn@stable --activate
            npm ci
          fi
          if [ -f requirements.txt ]; then
            pip install -r requirements.txt
          fi
          if [ -f Cargo.toml ]; then
            cargo fetch
          fi
          if [ -f go.mod ]; then
            go mod download
          fi

      - name: Build check
        run: make build

      - name: Unit tests
        run: make test-unit

      - name: Integration tests
        run: make test-integration

      - name: Security audit
        run: |
          if [ -f package.json ]; then npm audit --audit-level=high; fi
          if [ -f requirements.txt ]; then pip-audit; fi
          if [ -f Cargo.toml ]; then cargo audit; fi

      - name: License compliance
        run: make license-check

      - name: Performance baseline
        run: make benchmark

      - name: Diff report
        run: |
          echo "## 📦 依赖变更摘要" >> $GITHUB_STEP_SUMMARY
          git diff --stat HEAD~1 >> $GITHUB_STEP_SUMMARY
```

### 阶段五：记录（Record）

#### 5.1 升级事件记录格式

```json
{
  "event_id": "DEPU-20260406-001",
  "timestamp": "2026-04-06T14:00:00Z",
  "si_department": "dependency_mgmt_si",
  "operation_type": "dependency_upgrade",
  "trigger_mode": "cve_driven_autonomous",
  "packages_upgraded": [
    {
      "package": "lodash",
      "from_version": "4.17.15",
      "to_version": "4.17.21",
      "bump_type": "patch",
      "reason": "CVE-2024-12345 (CVSS 7.5) Prototype Pollution fix",
      "risk_assessment": {"score": 1.5, "level": "AUTO_APPROVE"},
      "license_check": {"compatible": true, "license": "MIT"}
    }
  ],
  "test_results": {
    "unit": {"total": 342, "passed": 342, "failed": 0},
    "integration": {"total": 56, "passed": 56, "failed": 0},
    "e2e": {"total": 12, "passed": 12, "failed": 0},
    "security_audit": {"critical": 0, "high": 0, "medium": 1, "low": 3}
  },
  "verification_status": "ALL_PASS",
  "rollback_executed": false,
  "post_upgrade_metrics": {
    "error_rate_delta": "-0.02%",
    "latency_p99_delta": "+3ms",
    "bundle_size_delta": "+0.5KB"
  }
}
```

## 典型自主场景

### 场景1：CVE 驱动的紧急安全升级

**背景**：`lodash` 4.17.15 存在原型链污染漏洞（CVE-2024-12345，CVSS 7.5），已发现公开 PoC 利用代码。

**自主处理流程**：

1. **感知**：每日定时 `cargo audit` / `npm audit` 扫描发现新 CVE
2. **决策**：CVSS 7.5 ≥ HIGH 阈值 + 有 PoC → **P0 强制升级**
3. **执行**：
   - 自动创建分支 `fix/cve-2024-12345-lodash`
   - 执行 `npm install lodash@4.17.21`
   - 运行全量测试套件
   - 提交 PR 并自动标注 `[security] [auto]` 标签
4. **验证**：所有测试通过，安全扫描显示漏洞已修复
5. **记录**：写入升级事件日志，通知安全团队

### 场景2：Major 版本升级的全流程管理

**背景**：团队决定将 Express.js 从 v4 升级到 v5（Major 跳跃），涉及大量 Breaking Change。

**自主处理流程**：

1. **信息收集**：拉取 Express 5 CHANGELOG，提取 23 条 Breaking Change
2. **影响分析**：搜索代码库中使用了废弃 API 的 47 个位置
3. **生成迁移代码**：为每个 BC 生成兼容 shim 或重写建议
4. **分阶段升级**：
   - Phase 1：先升级到 v4.19.x（最后一个 v4 版本），确保最新 patch
   - Phase 2：创建 feature/v5-migration 分支，应用所有迁移改动
   - Phase 3：在 staging 环境运行 72 小时灰度验证
   - Phase 4：全量发布到 production
5. **回滚预案**：保留 v4 完整 Docker 镜像，可在 5 分钟内回滚

### 场景3：循环依赖检测与解除

**背景**：Python 项目中 `models.py` ↔ `utils.py` 形成循环导入，导致模块加载偶发失败。

**自主处理流程**：

1. **感知**：依赖图谱 DFS 检测到环 `models → utils → models`
2. **分析**：`utils.py` 导入了 `models.Base` 用于类型注解，`models.py` 导入了 `utils.format_date`
3. **决策**：属于代码结构问题 → **生成重构建议**
4. **执行**：
   - 方案A（推荐）：将 `utils.py` 中的 `from models import Base` 改为 `TYPE_CHECKING` 块内导入
   - 方案B：抽取共享类型到单独的 `types.py` 模块
5. **验证**：`python -c "import models; import utils"` 成功，循环消除

### 场景4：许可证违规拦截

**背景**：开发者尝试添加 `serverless-http`（AGPL-3.0 许可证）到专有项目中。

**自主处理流程**：

1. **感知**：PR 中检测到新依赖 `serverless-http@3.1.0`
2. **许可证检查**：AGPL-3.0 与项目 MIT 许可证 → **BLOCKED**
3. **决策**：AGPL 具有强网络传染性，专有项目不可使用
4. **执行**：
   - 自动评论 PR，说明许可证冲突原因
   - 推荐替代方案：`werkzeug`（BSD-3）或 `starlette`（BSD-3）
   - 阻止 PR 合并，等待开发者更换依赖
5. **记录**：记录许可证拦截事件，供月度合规审计

## 决策框架

### 升级审批权限矩阵

| 升级类型 | 自主执行 | 需 Tech Lead 审批 | 需架构师审批 |
|---------|---------|-------------------|------------|
| Patch 升级（无 CVE） | ✅ | - | - |
| Patch 升级（含 CVE Low/Medium） | ✅ | - | - |
| Patch 升级（含 CVE High/Critical） | ✅（自动PR） | 抄送 | - |
| Minor 升级（低风险包） | ✅（测试通过后） | - | - |
| Minor 升级（高风险包） | - | ✅ | - |
| Major 升级（任何包） | - | ✅ | ✅ |
| 移除依赖 | - | ✅ | - |
| 更换许可证类型的依赖 | - | ✅ | ✅ |

### 回滚触发条件

满足以下任一条件即触发自动回滚：
- 任何门禁阶段测试失败
- 生产环境错误率上升超过基线 100%
- P99 延迟增加超过 300ms
- 新增的安全漏洞（降级导致）
- 服务可用性下降至低于 99.9%

## 安全与治理

### 供应链安全措施

| 措施 | 实施方式 | 频率 |
|------|---------|------|
| 依赖源镜像 | 使用私有 registry / 镜像 npm registry | 持续 |
| 校验和验证 | 锁文件 integrity 字段校验 | 每次 install |
| 签名验证 | sigstore / cosign 包签名验证 | 每次 CI 构建 |
| SBOM 生成 | CycloneDX / SPDX 格式的物料清单 | 每次发版 |
| 供应者信任评分 | OSSF Scorecard / deps.dev 评级 | 每周审查 |

### 数据保留策略

- 依赖扫描原始数据：保留 90 天
- 升级事件日志：保留 1 年
- CVE 处置记录：永久保留（合规要求）
- 许可证审查记录：保留 2 年

## 协作关系

### 向上汇报（户部）

| 报送内容 | 频率 | 格式 |
|---------|------|------|
| 依赖健康日报 | 每日 | 过期依赖数量 + CVE 数量 |
| 安全漏洞周报 | 每周 | 新增/修复 CVE 清单 |
| 升级趋势月报 | 每月 | 升级次数/成功率/MTTR 图表 |
| 许可证合规季报 | 每季度 | 合规率 + 风险项清单 |

### 平级协作

| 协作对象 | 协作内容 | 接口协议 |
|---------|---------|---------|
| **环境配置司** | 依赖版本号与环境变量的一致性 | 共享 config schema |
| **资源优化司** | 依赖升级后的资源消耗变化 | 提供 before/after metrics |
| **基础设施司** | CI 流水线中的依赖安装与缓存策略 | 缓存 key + 安装步骤 |

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| **Data Engineer** | Agency Data | 数据管线构建 | 为金部司提供依赖图谱数据的深度分析能力，构建依赖关系的 ETL 管线和可视化看板 |
| **Email Intelligence Engineer** | Agency Communication | 通知与告警智能化 | 将金部司的 CVE 漏洞报告、升级通知等输出转化为智能化的分级通知邮件/消息，确保关键信息不被淹没 |

### Agent 协作工作流

1. **依赖数据采集**: 金部司执行多包管理器扫描 → 原始扫描结果推送至 Data Engineer → 构建统一的依赖图谱数据仓库（支持 6 种包管理器的归一化模型）
2. **图谱深度分析**: Data Engineer 对依赖图谱运行高级分析——循环依赖检测、瓶颈包识别、传递依赖深度分析、许可证传染性评估 → 结果回流金部司用于升级决策
3. **CVE 智能通报**: 金部司发现新的 CVE 漏洞 → Email Intelligence Engineer 根据严重程度和影响面生成差异化通知：
   - CRITICAL: 即时短信+邮件+Slack @here + 创建紧急工单
   - HIGH: 邮件+Slack频道通知 + 下次站会议题
   - MEDIUM: 周报摘要 + 下次发版计划纳入
   - LOW: 月度汇总报告
4. **升级影响预测**: 金部司规划 Major 版本升级 → Data Engineer 运行代码库全量搜索（API 使用位置、Breaking Change 影响范围）→ 生成精确的影响面报告
5. **供应链安全监控**: Data Engineer 构建 SBOM (Software Bill of Materials) 时间线 → 金部司持续监控新增依赖的安全态势 → Email Intel Engineer 定期发送供应链安全简报
6. **许可证合规审计**: 金部司执行许可证兼容性检查 → Data Engineer 生成依赖树的可视化许可证图谱（标注传染路径）→ Email Intel Engineer 向法务团队发送合规审查请求

### 典型协作场景

- **场景一 - 全栈依赖全景看板**: 金部司每日扫描 6 种包管理器的依赖 → Data Engineer 将结果聚合到统一的 Grafana 看板（依赖数量趋势、过期包占比、漏洞分布热力图、许可证风险矩阵）→ 团队每日晨会参考该看板决定当日技术债务处理优先级
- **场景二 - Log4j 级别安全事件响应**: 金部司扫描发现 log4j 存在 RCE 漏洞（CVSS 10.0）→ 立即触发 P0 流程 → Email Intel Engineer 在 30 秒内发出全组织告警（含受影响服务清单和临时缓解方案）→ Data Engineer 快速定位所有直接/间接依赖 log4j 的服务（共 23 个）→ 金部司协调逐个修复
- **场景三 - Major 升级影响面精准分析**: 计划将 React 18 升级到 19 → Data Engineer 搜索全部代码库找到 347 个使用废弃 API 的位置 → 按 Module 分组生成影响面热力图 → 金部司据此制定分阶段迁移计划（核心模块优先，工具页面延后）→ Email Intel Engineer 向各模块负责人发送个性化迁移任务清单

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **Harness SSC (Security Step Connector)**: 将金部司的 CVE 扫描和安全审计流程集成到 Harness Pipeline 的 Security Stage 中，实现依赖安全左移
- **Harness STO (Security Testing Orchestration)**: 利用 Harness STO 的动态应用安全测试能力，补充金部司静态依赖扫描之外的运行时 vulnerability 检测维度

### 实践指南

1. **依赖安全门禁集成**: 将金部司的 `pip-audit` / `npm audit` / `cargo audit` 等扫描命令封装为 Harness SSC 的自定义 Security Step，配置为 Pipeline 的必过门禁——任何 HIGH/CRITICAL 级别的依赖漏洞都会阻断部署
2. **SBOM 自动生成与追踪**: 在每次 CI 构建成功后，Harness STO 自动生成 CycloneDX 格式的 SBOM → 金部司的依赖图谱数据仓库持续接收 SBOM 快照 → 实现"构建产物↔依赖清单"的全链路可追溯

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改依赖声明文件（requirements.txt/package.json等）、lock文件、许可证配置时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/requirements.txt",
      agent_id="依赖管理司",
      lock_type=LockType.EXCLUSIVE,
      priority=6,
      timeout=120.0
  )
  ```
- **读锁**：读取依赖列表、lock文件、漏洞扫描报告时申请读锁
- **释放锁**：依赖升级和修复操作完成后立即释放锁，避免阻塞其他司的依赖查询

#### 终端会话池使用
- 从MARC终端会话_pool获取会话执行包管理器命令（pip/npm/cargo/go等）
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（依赖安装和测试可能耗时较长）

#### 并发安全注意事项
- 依赖声明文件和lock文件必须同时锁定，保证一致性
- 多包管理器并行升级时需分别锁定各自的lock文件
- 死锁预防：按固定顺序申请锁（先锁依赖声明→再lock文件→最后lock缓存目录）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | CVE解读提示词、升级决策提示词、许可证兼容性检查提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许依赖管理操作（版本升级/漏洞修复/许可证检查），禁止修改业务代码 | 全自动 |
| **规则校验层** | 输出格式：JSON依赖图谱、Markdown升级报告、YAML许可证矩阵 | 全自动 |
| **兜底恢复层** | 升级失败时自动回滚lock文件至上一版本并重新安装依赖 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于依赖升级决策、CVE修复、许可证审查）
   - 示例：直接编辑requirements.txt/package.json、手动执行升级命令、编写兼容性适配代码
   - 优势：精确控制依赖版本、可逐步验证升级影响、可随时回滚依赖变更

2. 🥈 **规划脚本操作**（适用于批量依赖扫描、周期性漏洞检测）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查依赖安装配额和存储空间
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的依赖安全实践
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限紧急CVE修复、lock文件重建等极少数场景）
   - ⚠️ 必须预演影响范围（依赖升级可能破坏API兼容性）
   - ⚠️ Major版本升级需逐条确认并通过全量测试
   - 推荐使用PS7适配器转换pip/npm/cargo等包管理器命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- 包管理操作：pip/poetry/npm/yarn/cargo/go等命令在PS7中原生可用
- 文件操作：使用原生PowerShell Cmdlet处理lock文件和配置JSON
- Git操作：git命令用于依赖变更版本管理
- 编码：确保所有输出 UTF-8 无 BOM（依赖报告和审计记录）

### 与其他司的协作接口

- 上游依赖：环境配置司（获取环境特定的依赖版本）、基础设施司（接收CI/CD依赖安装步骤）
- 下游输出：资源优化司（推送依赖升级后的资源消耗变化）、工部代码司（通知API变更）
- 数据交换格式：JSON / YAML / Markdown（统一UTF-8无BOM）
