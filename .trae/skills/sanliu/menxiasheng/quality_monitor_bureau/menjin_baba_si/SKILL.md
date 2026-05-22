---
name: menjin_baba_si
description: 门禁把控司，负责质量门禁配置与执行、pre-commit/pre-push钩子。集成四维防线RuleValidationLayer的门禁执行点。配置文件：quality_gate_config.yaml。
---

# 门禁把控司技能指令

## 职责定义

门禁把控司作为质量监控局的执行控制核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **门禁配置** | 质量门禁规则定义与维护 | quality_gate_config.yaml |
| **门禁执行** | 各阶段质量检查执行 | 门禁执行报告 |
| **钩子管理** | Git hooks自动化集成 | hook脚本配置 |
| **准入控制** | 代码合入/发布的最终把关 | 准入/拒绝决策 |

---

## 四维防线集成

```yaml
four_dimensional_defense_integration:
  layer: 3
  component: "RuleValidationLayer"
  role: "Gate Execution Point"
  
  execution_model:
    description: "门禁把控司是RuleValidationLayer的门禁执行实体，将规范检查转化为具体的通过/拒绝决策"
    
    validation_flow:
      input: "Code submission (commit / PR / release candidate)"
      processing: >
        1. 触发各子司分析（静态分析司、安全扫描司等）
        2. 收集分析结果
        3. 应用门禁规则进行判定
        4. 生成门禁决策（PASS / CONDITIONAL_PASS / FAIL）
      output: "Gate decision with detailed report"
      
  gate_checkpoints:
    pre_commit:
      name: "提交前门禁"
      position: "开发者本地，git commit之前"
      checks:
        - "formatting_and_linting (快速检查)"
        - "basic_syntax_validation"
        - "no_trailing_whitespace"
        - "no_debug_statements"
      duration_target: "< 10 seconds"
      block_commit_on_fail: true
      
    pre_push:
      name: "推送前门禁"
      position: "git push之前（远程仓库）"
      checks:
        - "all_pre_commit_checks"
        - "unit_tests_pass"
        - "incremental_code_coverage >= threshold"
        - "no_new_security_issues (basic scan)"
      duration_target: "< 2 minutes"
      block_push_on_fail: true
      
    continuous_integration:
      name: "CI流水线门禁"
      position: "远程CI服务器，每次push/PR"
      checks:
        - "full_test_suite_pass"
        - "code_quality_metrics_met"
        - "security_scan_clean"
        - "performance_baseline_not_regressed"
        - "documentation_generated_for_changes"
      duration_target: "< 10 minutes"
      block_merge_on_fail: true
      
    pre_release:
      name: "发布前门禁"
      position: "打release tag之前"
      checks:
        - "all_ci_checks_passed"
        - "e2e_tests_passed (staging environment)"
        - "security_penetration_test_passed"
        - "load_test_within_sla"
        - "compliance_audit_passed"
        - "changelog_complete"
        - "rollback_plan_tested"
      duration_target: "< 60 minutes"
      block_release_on_fail: true
      
    production_deploy:
      name: "生产部署门禁"
      position: "实际部署到生产环境"
      checks:
        - "health_checks_pass"
        - "canary_deployment_successful"
        - "error_rate_below_threshold"
        - "monitoring_alerts_configured"
        - "rollback_capability_verified"
      duration_target: "< 15 minutes (canary period)"
      auto_rollback_on_fail: true
```

---

## 核心配置文件：quality_gate_config.yaml

```yaml
# quality_gate_config.yaml
# 门禁把控司主配置文件
# 位置: .trae/config/quality_gate_config.yaml

version: "1.0.0"
last_updated: "2024-01-01"
maintainer: "menjin_baba_si"

global_settings:
  strict_mode: false  # true=任何fail即阻塞, false=只阻塞marked_as_blocking的检查
  fail_fast: false     # true=第一个失败即停止, false=运行全部检查并汇总
  parallel_execution: true
  cache_results_minutes: 30  # 缓存相同代码的分析结果
  
gates:
  
  # ==================== Pre-Commit Gate ====================
  pre_commit:
    enabled: true
    blocking: true
    description: "本地提交前的快速检查"
    
    checks:
      formatting:
        name: "代码格式化检查"
        enabled: true
        blocking: true
        tools:
          python:
            command: "black --check --diff ."
            fix_command: "black ."
          javascript:
            command: "prettier --check '**/*.{js,ts,jsx,tsx}'"
            fix_command: "prettier --write '**/*.{js,ts,jsx,tsx}'"
        file_patterns: ["*.py", "*.js", "*.ts", "*.jsx", "*.tsx"]
        exclude_patterns: ["node_modules/**", "__pycache__/**", "*.min.js", "migrations/**"]
        
      linting:
        name: "静态Lint检查"
        enabled: true
        blocking: true
        tools:
          python:
            command: "flake8 --max-line-length=120 --statistics src/"
            config: ".flake8"
          javascript:
            command: "eslint src/ --ext .js,.ts,.jsx,.tsx"
            config: ".eslintrc.js"
            
      no_debug_code:
        name: "调试代码检测"
        enabled: true
        blocking: true
        patterns:
          - regex: "(console\\.log|debugger|pdb\\.set_trace|print\\(.*\\))"
            exclude_files: ["*.spec.ts", "*.test.py", "**/tests/**"]
        message: "发现调试代码，请移除后再提交"
        
      no_secret_exposure:
        name: "敏感信息检测"
        enabled: true
        blocking: true
        tool: "git-secrets --scan"
        patterns: ["password", "secret", "api_key", "token", "private_key"]
        
  # ==================== Pre-Push Gate ====================
  pre_push:
    enabled: true
    blocking: true
    description: "推送前的完整检查"
    includes_pre_commit_checks: true
    
    additional_checks:
      unit_tests:
        name: "单元测试"
        enabled: true
        blocking: true
        tools:
          python:
            command: "pytest tests/unit/ -v --tb=short --cov=src --cov-fail-under=75"
            coverage_threshold: 75
          javascript:
            command: "jest --coverage --coverageThreshold='{\"global\": {\"branches\": 70, \"functions\": 80, \"lines\": 80, \"statements\": 80}}'"
        timeout_seconds: 300
        
      incremental_coverage:
        name: "增量覆盖率检查"
        enabled: true
        blocking: false  # 仅警告不阻塞
        tool: "diff-cover"
        threshold:
          line_coverage_diff: -5  # 允许下降不超过5%
        message: "新代码覆盖率不足，建议补充测试"
        
      security_quick_scan:
        name: "快速安全扫描"
        enabled: true
        blocking: true
        tool: "bandit -r src/ -ll"  # 只报告low及以上
        allowed_severity: ["low"]  # medium和above会阻塞
        
  # ==================== CI Pipeline Gate ====================
  ci_pipeline:
    enabled: true
    blocking: true
    description: "CI流水线全量门禁"
    includes_all_previous: true
    
    full_test_suite:
      name: "完整测试套件"
      enabled: true
      blocking: true
      test_types:
        unit:
          command: "pytest tests/unit/ -v --junitxml=junit-unit.xml"
          required_pass_rate: 100
          
        integration:
          command: "pytest tests/integration/ -v --junitxml=junit-integration.xml"
          required_pass_rate: 100
          services_required: ["postgres", "redis"]
          
        e2e:
          command: "npx playwright test e2e/ --reporter=list"
          required_pass_rate: 100
          environment: "staging"
          
    code_quality_metrics:
      name: "代码质量指标"
      enabled: true
      blocking: true
      metrics:
        sonarqube_quality_gate:
          tool: "sonar-scanner"
          gate_status: "OK"
          project_key: "${SONAR_PROJECT_KEY}"
          
        complexity:
          max_cyclomatic_complexity: 15
          max_function_lines: 80
          max_file_lines: 500
          
        duplication:
          max_duplication_percent: 8
          
    security_scan:
      name: "全面安全扫描"
      enabled: true
      blocking: true
      scans:
        bandit_full:
          command: "bandit -r src/ -f json -o bandit-report.json"
          exit_code_handling: "parse JSON for severity counts"
          thresholds:
            critical: 0
            high: 0
            medium: 5
            
        dependency_vulnerabilities:
          tool: "snyk test --json"
          thresholds:
            critical: 0
            high: 2
            
        secrets_scan:
          tool: "python skillscripts/security/hardcoded_detector.py"
          findings_allowed: 0
          
    performance_baseline:
      name: "性能基线检查"
      enabled: true
      blocking: false  # 性能退化通常不阻塞但告警
      baselines:
        api_response_time_p95:
          current_vs_baseline_ratio_max: 1.2  # 允许最多慢20%
          
        test_execution_time:
          max_regression_percent: 15
          
        bundle_size:
          max_increase_kb: 200
          
    documentation:
      name: "文档完整性"
      enabled: true
      blocking: false
      checks:
        - "README updated if user-facing changes"
        - "CHANGELOG entry added"
        - "New APIs have OpenAPI spec updates"
        - "Complex functions have docstrings"
        
  # ==================== Pre-Release Gate ====================
  pre_release:
    enabled: true
    blocking: true
    description: "发布前最严格门禁"
    requires_manual_approval: true
    approvers: ["tech_lead", "qa_manager"]
    
    additional_checks:
      staging_e2e:
        name: "预发布环境E2E测试"
        enabled: true
        blocking: true
        environment: "staging-production-like"
        test_suites:
          - "smoke_tests"
          - "critical_user_journeys"
          - "regression_suite"
        pass_rate_required: 100
        
      security_penetration:
        name: "安全渗透测试"
        enabled: true
        blocking: true
        type: "automated_scanning + manual_review_summary"
        tools: ["OWASP ZAP automated scan"]
        requirements:
          - "No Critical or High vulnerabilities"
          - "Authentication bypass not possible"
          - "Data encryption verified"
          
      load_testing:
        name: "负载测试"
        enabled: true
        blocking: true
        tool: "k6 or Locust"
        scenarios:
          - name: "expected_load"
            vusers: 1000
            duration: "10m"
            pass_criteria:
              p99_response_time_ms: "< 1000"
              error_rate: "< 0.1%"
              
          - name: "peak_load"
            vusers: 3000
            duration: "5m"
            pass_criteria:
              p99_response_time_ms: "< 2000"
              error_rate: "< 1%"
              no_service_crashes: true
              
      compliance_audit:
        name: "合规审计检查"
        enabled: true
        blocking: true
        frameworks:
          gdpr:
            checks:
              - "Personal data encrypted at rest"
              - "Data retention policy implemented"
              - "Privacy policy up to date"
              
          soc2:
            checks:
              - "Access control logs maintained"
              - "Change management process followed"
              - "Incident response plan tested"
              
      release_readiness:
        name: "发布就绪检查"
        enabled: true
        blocking: true
        checklist:
          - "Version number incremented correctly"
          - "CHANGELOG complete with all changes"
          - "Migration scripts tested forward and backward"
          - "Rollback procedure documented and tested"
          - "Monitoring dashboards updated"
          - "On-call engineer notified"
          - "Customer communication drafted"

# ==================== Notification Configuration ====================
notification:
  on_pass:
    message: "✅ All quality gates passed"
    channels: ["ci_status_badge", "pr_comment_success"]
    
  on_fail:
    message: "❌ Quality gate(s) failed"
    channels: ["pr_comment_failure", "slack_alerts", "email_responsible"]
    include_details:
      - failed_check_names
      - actual_values
      - threshold_values
      - remediation_links
      
  on_conditional_pass:
    message: "⚠️ Passed with warnings"
    channels: ["pr_comment_warning"]
    list_non_blocking_failures: true

# ==================== Exemptions & Overrides ====================
exemptions:
  hotfix_branches:
    pattern: "^hotfix/.*$"
    relaxed_gates:
      - skip_e2e_tests: true
      - skip_performance_baseline: true
      - reduce_unit_coverage_threshold: 65
    require_reason: true
    max_duration_hours: 24
    auto_expire: true
    
  emergency_override:
    enabled: true
    authorized_roles: ["vp_engineering", "cto"]
    require_jira_ticket: true
    audit_log: true
    notification: "Notify all stakeholders when override used"
```

---

## 工作流程

### 阶段一：门禁规则加载与初始化

```
触发门禁检查（各种入口）
    ↓
[1] 加载 quality_gate_config.yaml
    ↓
[2] 解析当前上下文（哪个gate？什么触发源？）
    ↓
[3] 确定适用的检查项集合
    ↓
[4] 初始化检查环境
    ↓
[5] 开始并行执行检查
```

### 阶段二：门禁检查执行

```
开始执行
    ↓
[1] 并行启动所有适用检查
    ↓
[2] 收集各检查结果
    ↓
[3] 结果标准化
    ↓
[4] 应用阻塞/非阻塞逻辑
    ↓
[5] 汇总生成门禁报告
    ↓
输出门禁决策
```

#### 门禁执行报告格式

```json
{
  "gate_execution_report": {
    "execution_id": "GATE-EXEC-20240108-143000",
    "timestamp": "2024-01-08T14:30:00Z",
    "gate_type": "ci_pipeline",
    "trigger_source": "github_actions",
    "trigger_ref": "refs/pull/145/head",
    "duration_seconds": 487,
    
    "decision": "FAIL",
    "decision_reason": "2个阻塞性检查未通过",
    "can_merge": false,
    
    "check_results": {
      "summary": {
        "total_checks": 18,
        "passed": 14,
        "failed": 3,
        "warning": 1,
        "skipped": 0,
        "blocked_by": 2
      },
      
      "details": [
        {
          "check_id": "unit_tests",
          "name": "单元测试",
          "status": "passed",
          "blocking": true,
          "duration_seconds": 125,
          "details": {
            "total_tests": 245,
            "passed": 245,
            "failed": 0,
            "skipped": 3,
            "coverage": {"line": 86.2, "branch": 79.5}
          }
        },
        {
          "check_id": "integration_tests",
          "name: "集成测试",
          "status": "passed",
          "blocking": true,
          "duration_seconds": 198,
          "details": {...}
        },
        {
          "check_id": "security_scan_bandit",
          "name: "Bandit安全扫描",
          "status": "FAILED",
          "blocking": true,
          "failure_type": "threshold_exceeded",
          "duration_seconds": 45,
          "details": {
            "tool": "bandit 1.7.4",
            "issues_found": {
              "critical": 0,
              "high": 2,
              "medium": 5,
              "low": 12
            },
            "threshold": {"high": 0},
            "exceeded_by": 2,
            "top_issues": [
              {
                "id": "B101",
                "severity": "high",
                "file": "src/auth/token_manager.py",
                "line": 89,
                "issue": "assert_used - Use of assert detected"
              },
              {
                "id": "B310",
                "severity": "high",
                "file": "src/utils/xml_parser.py",
                "line": 34,
                "issue: "xml_etree_element_tree - Possible XML vulnerability"
              }
            ]
          },
          "remediation": "修复High级别安全问题后重新提交"
        },
        {
          "check_id": "dependency_vulnerabilities",
          "name: "依赖漏洞检查",
          "status": "FAILED",
          "blocking": true,
          "failure_type": "threshold_exceeded",
          "duration_seconds": 67,
          "details": {
            "tool": "Snyk",
            "vulnerabilities": [
              {
                "package": "lodash",
                "installed_version": "4.17.21",
                "vulnerability_id": "CVE-2021-23337",
                "severity": "high",
                "description": "Command Injection in lodash utilities"
              }
            ],
            "threshold": {"high": 0},
            "exceeded_by": 1
          },
          "remediation": "升级lodash至>=4.17.21-patch或移除有漏洞的功能"
        },
        {
          "check_id": "code_quality_sonar",
          "name: "SonarQube质量门",
          "status": "WARNING",
          "blocking": false,
          "failure_type": "below_target",
          "details": {
            "quality_gate_status": "OK",
            "rating": "B",
            "new_technical_debt": "2h",
            "notes": "Quality gate passed but debt increased"
          }
        }
      ]
    },
    
    "metrics_snapshot": {
      "code_coverage": {"line": 86.2, "branch": 79.5, "function": 91.0},
      "security_score": 72,
      "quality_rating": "B",
      "duplication": 3.2,
      "complexity_avg": 8.3
    },
    
    "recommendations": [
      {
        "priority": "P0-Critical",
        "item": "修复2个Bandit High安全问题",
        "effort": "~1 hour",
        "blocks_merge": true
      },
      {
        "priority": "P0-Critical",
        "item": "升级lodash依赖或移除有漏洞功能",
        "effort": "~30 minutes",
        "blocks_merge": true
      },
      {
        "priority": "P1-High",
        "item": "关注SonarQube新增2h技术债务",
        "effort": "Track in backlog",
        "blocks_merge": false
      }
    ],
    
    "attachments": [
      {"type": "bandit_report", "url": ".../bandit-report.json"},
      {"type": "snyk_report", "url": ".../snyk-results.json"},
      {"type": "sonarqube_dashboard", "url": "https://sonar.example.com/dashboard?id=project"}
    ]
  }
}
```

---

### 阶段三：Git Hooks集成

```
门禁规则配置完成
    ↓
[1] 生成pre-commit hook脚本
    ↓
[2] 生成pre-push hook脚本
    ↓
[3] 生成commit-msg hook（可选）
    ↓
[4] 配置hook安装机制
    ↓
[5] 提供开发者本地安装指南
    ↓
输出hooks配置包
```

#### Pre-commit Hook实现示例

```bash
#!/bin/bash
# .git/hooks/pre-commit
# 由门禁把控司自动生成和管理

set -euo pipefail

echo "🚪 门下省·门禁把控司 - Pre-Commit Quality Gate"
echo "============================================="

# ===== 配置 =====
GATE_CONFIG=".trae/config/quality_gate_config.yaml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE=".gate_logs/pre_commit_${TIMESTAMP}.log"
PASS=true

# ===== 工具函数 =====
log() { echo "[$(date '+%H:%M:%S')] $@" | tee -a "$LOG_FILE"; }
pass() { log "✅ $1"; }
fail() { log "❌ $1"; PASS=false; }
warn() { log "⚠️  $1"; }

# ===== 1. 格式化检查 =====
log "[1/4] 检查代码格式..."

# Python Black check
if command -v black &> /dev/null; then
    BLACK_OUTPUT=$(black --check --diff --color . 2>&1 || true)
    if [ -z "$BLACK_OUTPUT" ]; then
        pass "Python格式: 符合Black规范"
    else
        fail "Python格式: 不符合Black规范"
        echo "$BLACK_OUTPUT" | head -20
        echo "提示: 运行 'black .' 自动修复格式"
    fi
fi

# JavaScript Prettier check
if command -v prettier &> /dev/null; then
    PRETTIER_OUTPUT=$(prettier --check '**/*.{js,ts,jsx,tsx}' 2>&1 || true)
    if [ -z "$(echo $PRETTIER_OUTPUT | grep -v 'Checking...')"; then
        pass "JavaScript格式: 符合Prettier规范"
    else
        fail "JavaScript格式: 不符合Prettier规范"
        echo "提示: 运行 'prettier --write .' 自动修复格式"
    fi
fi

# ===== 2. Lint检查 =====
log "[2/4] 运行静态Lint检查..."

# Python Flake8
if command -v flake8 &> /dev/null; then
    FLAKE8_OUTPUT=$(flake8 src/ --max-line-length=120 --statistics 2>&1 || true)
    if [ -z "$FLAKE8_OUTPUT" ]; then
        pass "Flake8: 无Lint错误"
    else
        FLAKE8_ERRORS=$(echo "$FLAKE8_OUTPUT" | wc -l)
        fail "Flake8: 发现 ${FLAKE8_ERRORS} 个Lint问题"
        echo "$FLAKE8_OUTPUT" | head -10
    fi
fi

# ===== 3. 调试代码检测 =====
log "[3/4] 扫描调试代码..."

DEBUG_PATTERNS="console\.log|debugger|pdb\.set_trace|print\(.*\)"
if grep -rInE --include="*.py" --exclude-dir=tests --exclude-dir=__pycache__ "$DEBUG_PATTERNS" src/ 2>/dev/null; then
    fail "发现调试代码! 请移除console.log/debugger/print语句后再提交"
else
    pass "未发现调试代码"
fi

# ===== 4. 敏感信息检测 =====
log "[4/4] 扫描敏感信息..."

if command -v git-secrets &> /dev/null; then
    if git-secrets --scan 2>/dev/null; then
        pass "未发现硬编码密钥"
    else
        fail "发现可能的硬编码密钥或敏感信息!"
    fi
else
    warn "git-secrets未安装，跳过密钥扫描 (建议安装: brew install git-secrets)"
fi

# ===== 结果汇总 =====
echo ""
echo "============================================="
if [ "$PASS" = true ]; then
    echo "✅ Pre-Commit 门禁: 通过 🎉"
    echo "============================================="
    exit 0
else
    echo "❌ Pre-Commit 门禁: 未通过"
    echo "============================================="
    echo ""
    echo "请修复上述问题后重新提交。"
    echo "详细日志: ${LOG_FILE}"
    exit 1
fi
```

#### Hook安装指南

```markdown
# 门禁Git Hooks安装指南

## 自动安装（推荐）

### 使用 pre-commit 框架

```bash
# 1. 安装 pre-commit
pip install pre-commit

# 2. 在项目根目录创建 .pre-commit-config.yaml
# （此文件由门禁把控司维护）

# 3. 安装hooks
pre-commit install
pre-commit install --hook-type pre-push

# 4. hooks将在对应的git操作时自动运行
```

### .pre-commit-config.yaml 示例

```yaml
repos:
  - repo: local
    hooks:
      - id: menxiasheng-pre-commit-gate
        name: "🚪 门下省Pre-Commit门禁"
        entry: .git/hooks/pre-commit
        language: script
        pass_filenames: false
        always_run: true
        stages: [commit]
        
  - repo: local
    hooks:
      - id: menxiasheng-pre-push-gate
        name: "🚪 门下省Pre-Push门禁"
        entry: .git/hooks/pre-push
        language: script
        pass_filenames: false
        always_run: true
        stages: [push]
        
  # 第三方hooks（可选择性启用）
  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.56.0
    hooks:
      - id: eslint
        files: \.(js|ts)$
        
  - repo: https://github.com/pre-commit/mirrors-black
    rev: 23.12.0
    hooks:
      - id: black
        files: \.py$
        
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
        args: ['--baseline', '.secrets.baseline']
```

## 手动安装

如果不想使用pre-commit框架：

```bash
# 1. 从门禁把控司获取最新hooks
cp .trae/hooks/pre-commit .git/hooks/pre-commit
cp .trae/hooks/pre-push .git/hooks/pre-push

# 2. 设置可执行权限
chmod +x .git/hooks/pre-commit
chmod +x .git/hooks/pre-push

# 3. 验证安装
.git/hooks/pre-commit --version
```

## 常见问题

### Q: 我想临时跳过门禁怎么办？
A: 
```bash
# 不推荐！仅在紧急情况下使用
git commit --no-verify -m "hotfix: ..."
git push --no-verify
```
注意：这会绕过所有质量检查，需要在PR说明中解释原因。

### Q: 门禁太慢了怎么优化？
A:
1. 使用 `--cache` 选项缓存分析结果
2. 只对变更文件进行检查（增量模式）
3. 将耗时检查移至pre-push而非pre-commit
4. 在 `.gate_ignore` 中排除不需要检查的目录

### Q: 如何添加自定义检查？
A: 编辑 `quality_gate_config.yaml` 的 `gates.pre_commit.checks` 部分，
或在 `.pre-commit-config.yaml` 中添加新的hook条目。
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 4  # 用于并行执行多个检查
    memory_gb: 8
    
  execution_time:
    pre_commit_gate: "< 15 seconds"
    pre_push_gate: "< 3 minutes"
    ci_pipeline_gate: "< 10 minutes"
    pre_release_gate: "< 60 minutes"
    
  integrations:
    version_control:
      - "Git hooks (pre-commit, pre-push, commit-msg)"
      - "GitHub/GitLab PR status API"
      
    ci_cd_platforms:
      - "GitHub Actions"
      - "GitLab CI"
      - "Jenkins"
      - "Azure DevOps"
      
    notification:
      - "PR comments (pass/fail/warning)"
      - "Status badges generation"
      - "Slack notifications"
      
  configuration_management:
    main_config: "quality_gate_config.yaml"
    config_location: ".trae/config/"
    version_controlled: true
    change_requires_review: true  # 配置变更也需要review
```

---

## 协同调用接口

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `execute_gate` | 执行指定门禁检查 | CI/CD流水线、Git hooks |
| `validate_config` | 验证门禁配置有效性 | 系统管理员 |
| `generate_hooks` | 生成Git hooks脚本 | 开发者onboarding |
| `get_gate_status` | 查询门禁历史状态 | 仪表板、报告系统 |

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含完整的五级门禁体系、配置管理、Hook集成能力 |
