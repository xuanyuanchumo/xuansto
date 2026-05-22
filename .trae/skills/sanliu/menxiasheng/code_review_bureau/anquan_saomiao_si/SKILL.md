---
name: anquan_saomiao_si
description: 安全扫描司，负责OWASP Top 10扫描、依赖漏洞检测、硬编码密钥检测。集成四维防线第3层RuleValidationLayer的安全扫描子模块，集成密钥管理系统HardcodedDetector。
---

# 安全扫描司技能指令

## 职责定义

安全扫描司作为代码审查局的安全保障核心，承担以下职责：

| 职责类别 | 具体职责 | 关键产出 |
|----------|----------|----------|
| **OWASP扫描** | Top 10安全漏洞检测 | OWASP扫描报告 |
| **依赖安全** | 第三方依赖漏洞检测 | 依赖安全报告 |
| **密钥检测** | 硬编码密钥/密码检测 | 密钥泄露报告 |
| **安全审计** | 安全最佳实践审计 | 安全审计报告 |

---

## 工具集成

### 核心安全工具链

| 工具 | 用途 | 特点 |
|------|------|------|
| **Bandit** | Python安全漏洞扫描 | 专注Python安全 |
| **Snyk** | 依赖漏洞检测 | 实时漏洞数据库 |
| **Trivy** | 容器镜像安全扫描 | 多格式支持 |
| **Semgrep** | 多语言模式匹配安全扫描 | 可定制规则 |
| **HardcodedDetector** | 密钥泄露检测 | 自研密钥管理组件 |

### 四维防线第3层集成

```yaml
four_dimensional_defense:
  layer: 3
  component: "RuleValidationLayer"
  submodule: "security_scan"

security_scan_rules:
  owasp_top_10:
    - id: "A01-2021"
      name: "Broken Access Control"
      severity: "critical"
      check_items:
        - "权限绕过检测"
        - "水平/垂直越权检测"
        
    - id: "A02-2021"
      name: "Cryptographic Failures"
      severity: "critical"
      check_items:
        - "弱加密算法检测"
        - "明文传输检测"
        
    - id: "A03-2021"
      name: "Injection"
      severity: "critical"
      check_items:
        - "SQL注入检测"
        - "NoSQL注入检测"
        - "命令注入检测"
        - "XSS检测"
        
    - id: "A04-2021"
      name: "Insecure Design"
      severity: "high"
      check_items:
        - "不安全的架构模式"
        
    - id: "A05-2021"
      name: "Security Misconfiguration"
      severity: "high"
      check_items:
        - "默认凭证检测"
        - "不必要的功能启用"
        
    - id: "A06-2021"
      name: "Vulnerable and Outdated Components"
      severity: "high"
      check_items:
        - "已知CVE漏洞检测"
        
    - id: "A07-2021"
      name: "Identification and Authentication Failures"
      severity: "critical"
      check_items:
        - "弱密码策略"
        - "会话管理缺陷"
        
    - id: "A08-2021"
      name: "Software and Data Integrity Failures"
      severity: "medium"
      check_items:
        - "未签名的更新包"
        
    - id: "A09-2021"
      name: "Security Logging and Monitoring Failures"
      severity: "medium"
      check_items:
        - "日志记录不足"
        
    - id: "A10-2021"
      name: "Server-Side Request Forgery (SSRF)"
      severity: "high"
      check_items:
        - "SSRF漏洞检测"
```

### 密钥管理系统集成

```yaml
key_management_integration:
  detector_script: "skillscripts/security/hardcoded_detector.py"
  
  detection_patterns:
    - pattern: "(password|passwd|pwd)\\s*=\\s*['\"][^'\"]+['\"]"
      type: "password"
      severity: "critical"
      
    - pattern: "(secret|api_key|apikey|token)\\s*=\\s*['\"][^'\"]+['\"]"
      type: "api_key"
      severity: "critical"
      
    - pattern: "(private_key|secret_key)\\s*=\\s*['\"][^'\"]+['\"]"
      type: "private_key"
      severity: "critical"
      
    - pattern: "(connection_string|conn_str|db_url)\\s*=\\s*['\"][^'\"]+['\"]"
      type: "connection_string"
      severity: "high"
      
    - pattern: "(aws_access_key|aws_secret)\\s*=\\s*['\"][^'\"]+['\"]"
      type: "cloud_credential"
      severity: "critical"
      
  exemptions:
    - path: "tests/**"
      reason: "测试环境允许硬编码"
    - path: "examples/**"
      reason: "示例代码"
    - path: ".env.example"
      reason: "环境变量模板"
      
  remediation_actions:
    - action: "move_to_environment_variables"
      description: "迁移至环境变量或密钥管理服务"
    - action: "use_secrets_manager"
      description: "使用AWS Secrets Manager / Azure Key Vault"
    - action: "rotate_credentials"
      description: "立即轮换已泄露的凭据"
```

---

## 工作流程

### 阶段一：安全扫描准备

```
代码提交/构建触发
    ↓
[1] 扫描范围确定
    ↓
[2] 配置文件加载
    ↓
[3] 白名单/豁免规则应用
    ↓
进入安全扫描阶段
```

#### 扫描范围配置

```yaml
scan_configuration:
  scope_types:
    - "incremental"  # 只扫描变更文件
    - "full"         # 全量扫描
    - "targeted"     # 指定目标扫描
    
  target_languages:
    - "python"
    - "javascript"
    - "typescript"
    - "java"
    - "go"
    
  exclude_patterns:
    - "node_modules/**"
    - "vendor/**"
    - "*.min.js"
    - "*.min.css"
    - "__pycache__/**"
    - ".git/**"
    - "migrations/**"
```

---

### 阶段二：OWASP Top 10扫描流程

```
扫描准备完成
    ↓
[1] A01: 访问控制缺陷扫描
    ↓
[2] A02: 加密失败扫描
    ↓
[3] A03: 注入攻击扫描
    ↓
[4] A04-A05: 设计与配置缺陷扫描
    ↓
[5] A06-A07: 组件与认证缺陷扫描
    ↓
[6] A08-A10: 其他安全缺陷扫描
    ↓
[7] 漏洞分级与排序
    ↓
输出OWASP扫描报告
```

#### SQL注入检测详细规则

```yaml
sql_injection_rules:
  detection_patterns:
    - pattern: "execute\\(.*f['\"]|execute\\(.*format\\("
      type: "f-string injection"
      severity: "critical"
      example: |
        # 危险：使用f-string拼接SQL
        query = f"SELECT * FROM users WHERE id = {user_id}"
        db.execute(query)
        
    - pattern: "execute\\(.*\\+.*\\)|execute\\(.*%.*\\)"
      type: "string concatenation"
      severity: "critical"
      
    - pattern: "raw_sql|raw_query"
      type: "raw query usage"
      severity: "high"
      
  safe_patterns:
    - "parameterized queries (?, %s, :param)"
    - "ORM methods (filter(), get())"
    - "prepared statements"
    
  remediation_example: |
    # 安全：使用参数化查询
    query = "SELECT * FROM users WHERE id = ?"
    db.execute(query, (user_id,))
```

#### XSS检测详细规则

```yaml
xss_detection_rules:
  vulnerable_patterns:
    - pattern: "innerHTML\\s*=|document\\.write\\(|\\.html\\("
      severity: "critical"
      type: "DOM-based XSS"
      
    - pattern: "\\$\\(.*\\)\\.html\\(|\\.append\\("
      severity: "high"
      type: "jQuery XSS"
      
    - pattern: "render_template_string\\(|safe\\s*\\|"
      severity: "high"
      type: "Server-side XSS"
      
  safe_alternatives:
    - "textContent instead of innerHTML"
    - "DOMPurify for sanitization"
    - "autoescaping in templates"
    - "CSP headers"
```

#### OWASP扫描报告格式

```json
{
  "scan_id": "OWASP-SCAN-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "scan_type": "full",
  "scan_scope": {
    "repository": "project-name",
    "branch": "main",
    "commit_hash": "abc123def456",
    "files_scanned": 200,
    "lines_of_code": 35000
  },
  "owasp_findings": [
    {
      "id": "VULN-001",
      "owasp_category": "A03-2021-Injection",
      "cwe_id": "CWE-89",
      "title": "SQL Injection Vulnerability",
      "severity": "critical",
      "confidence": "high",
      "location": {
        "file": "src/repository/user_repository.py",
        "line_start": 45,
        "line_end": 48,
        "function": "find_by_username"
      },
      "vulnerable_code_snippet": "query = f\"SELECT * FROM users WHERE username = '{username}'\"",
      "description": "使用f-string拼接SQL查询，存在SQL注入风险",
      "impact": "攻击者可执行任意SQL命令，获取、修改或删除数据库数据",
      "remediation": "使用参数化查询替代字符串拼接",
      "secure_code_example": "query = \"SELECT * FROM users WHERE username = ?\"; cursor.execute(query, (username,))",
      "references": [
        "https://owasp.org/www-community/attacks/SQL_Injection",
        "https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html"
      ],
      "cvss_score": 9.8,
      "status": "open"
    },
    {
      "id": "VULN-002",
      "owasp_category": "A02-2021-Cryptographic Failures",
      "cwe_id": "CWE-326",
      "title": "Weak Encryption Algorithm Usage",
      "severity": "high",
      "confidence": "medium",
      "location": {
        "file": "src/utils/crypto_utils.py",
        "line_start": 23,
        "line_end": 26,
        "function": "encrypt_password"
      },
      "vulnerable_code_snippet": "hashed = hashlib.md5(password.encode()).hexdigest()",
      "description": "使用MD5进行密码哈希，MD5已被证明存在碰撞风险且不适合密码存储",
      "impact": "攻击者可通过彩虹表快速破解密码哈希",
      "remediation": "使用bcrypt、scrypt或argon2等专门设计的密码哈希算法",
      "secure_code_example": "hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())",
      "cvss_score": 7.5,
      "status": "open"
    },
    {
      "id": "VULN-003",
      "owasp_category": "A07-2021-Authentication Failures",
      "cwe_id": "CWE-522",
      "title": "Insufficiently Protected Credentials",
      "severity": "critical",
      "confidence": "high",
      "location": {
        "file": "config/settings.py",
        "line_start": 15,
        "line_end": 15
      },
      "vulnerable_code_snippet": "DATABASE_PASSWORD = 'SuperSecret123!'",
      "description": "数据库密码硬编码在源代码中",
      "impact": "任何能访问代码仓库的人都能获取数据库密码",
      "remediation": "使用环境变量或密钥管理服务存储敏感信息",
      "cvss_score": 9.1,
      "status": "open"
    }
  ],
  "summary": {
    "total_vulnerabilities": 3,
    "by_severity": {
      "critical": 2,
      "high": 1,
      "medium": 0,
      "low": 0,
      "info": 0
    },
    "by_owasp_category": {
      "A01": 0,
      "A02": 1,
      "A03": 1,
      "A04": 0,
      "A05": 0,
      "A06": 0,
      "A07": 1,
      "A08": 0,
      "A09": 0,
      "A10": 0
    },
    "overall_risk_level": "critical",
    "scan_passed": false,
    "blocking_vulnerabilities": 2
  },
  "recommendations": [
    "立即修复所有Critical级别的漏洞",
    "实施安全编码培训计划",
    "建立安全代码审查流程"
  ],
  "compliance_status": {
    "pci_dss": "non_compliant",
    "gdpr": "at_risk",
    "iso27001": "non_compliant",
    "soc2": "at_risk"
  }
}
```

---

### 阶段三：依赖漏洞检测流程

```
OWASP扫描完成
    ↓
[1] 依赖文件解析 (package.json/requirements.txt/pom.xml)
    ↓
[2] 依赖版本采集
    ↓
[3] 漏洞数据库比对
    ↓
[4] 已知CVE匹配
    ↓
[5] 许可证合规检查
    ↓
[6] 修复建议生成
    ↓
输出依赖安全报告
```

#### 依赖检测配置

```yaml
dependency_scan_config:
  package_managers:
    python:
      files: ["requirements.txt", "setup.py", "pyproject.toml"]
      tool: "safety || pip-audit"
      
    javascript:
      files: ["package.json", "package-lock.json", "yarn.lock"]
      tool: "npm audit || yarn audit"
      
    java:
      files: ["pom.xml", "build.gradle"]
      tool: "dependency-check || Snyk"
      
  vulnerability_database:
    sources:
      - "NVD (National Vulnerability Database)"
      - "GitHub Advisory Database"
      - "Snyk Vulnerability Database"
    update_frequency: "daily"
    
  severity_thresholds:
    auto_fail:
      - "critical"
      - "high"
    warn_only:
      - "medium"
    ignore:
      - "low"
      - "info"
```

#### 依赖安全报告格式

```json
{
  "report_id": "DEP-SEC-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "project_info": {
    "name": "project-name",
    "package_manager": "pip",
    "manifest_file": "requirements.txt",
    "total_dependencies": 45,
    "direct_dependencies": 18,
    "transitive_dependencies": 27
  },
  "vulnerabilities": [
    {
      "id": "CVE-2024-1234",
      "package_name": "requests",
      "installed_version": "2.28.0",
      "fixed_version": "2.31.0",
      "severity": "high",
      "cvss_score": 7.5,
      "cwe_ids": ["CWE-502"],
      "title": "Deserialization vulnerability in requests library",
      "description": "The requests library is vulnerable to unsafe deserialization when handling malicious responses",
      "affected_paths": [
        "requirements.txt -> requests@2.28.0"
      ],
      "recommendation": "Upgrade to version 2.31.0 or later",
      "patch_available": true,
      "exploitability": "easy",
      "impact": "Remote Code Execution"
    },
    {
      "id": "CVE-2024-5678",
      "package_name": "flask",
      "installed_version": "2.2.0",
      "fixed_version": "2.3.2",
      "severity": "medium",
      "cvss_score": 5.5,
      "cwe_ids": ["CWE-79"],
      "title": "Cross-site Scripting in Flask debug mode",
      "description": "Flask's debugger can be exploited to execute arbitrary code when debug mode is enabled",
      "recommendation": "Disable debug mode in production or upgrade to 2.3.2+",
      "patch_available": true
    }
  ],
  "license_compliance": {
    "violations": [],
    "licenses_found": {
      "MIT": 30,
      "Apache-2.0": 10,
      "BSD-3-Clause": 5
  },
    "compliant": true
  },
  "summary": {
    "total_vulnerabilities": 2,
    "by_severity": {
      "critical": 0,
      "high": 1,
      "medium": 1,
      "low": 0
    },
    "fixable_with_upgrade": 2,
    "requires_security_advisory": 0,
    "scan_passed": false,
    "blocking_issues": 1
  },
  "remediation_plan": [
    {
      "priority": "high",
      "action": "upgrade",
      "package": "requests",
      "from_version": "2.28.0",
      "to_version": "2.31.0",
      "command": "pip install --upgrade requests==2.31.0"
    },
    {
      "priority": "medium",
      "action": "upgrade",
      "package": "flask",
      "from_version": "2.2.0",
      "to_version": "2.3.2",
      "command": "pip install --upgrade flask==2.3.2"
    }
  ],
  "dependency_health_score": 72
}
```

---

### 阶段四：硬编码密钥检测流程

```
依赖检测完成
    ↓
[1] 调用 HardcodedDetector 脚本
    ↓
[2] 正则表达式模式匹配
    ↓
[3] 误报过滤（白名单）
    ↓
[4] 密钥类型分类
    ↓
[5] 泄露风险评估
    ↓
[6] 整改建议生成
    ↓
输出密钥泄露报告
```

#### HardcodedDetector调用方式

```bash
# 调用密钥检测脚本
python skillscripts/security/hardcoded_detector.py \
  --source-path ./src \
  --output reports/security/hardcoded_keys_$(date +%Y%m%d).json \
  --severity-threshold medium \
  --exclude-patterns "tests/**,*.example,*_test.py" \
  --enable-git-history-scan
```

#### 密钥泄露检测报告格式

```json
{
  "detection_id": "KEY-LEAK-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "detector_version": "1.0.0",
  "scan_configuration": {
    "source_path": "./src",
    "files_scanned": 150,
    "patterns_checked": 12,
    "git_history_scanned": true,
    "commits_analyzed": 500
  },
  "findings": [
    {
      "id": "FINDING-001",
      "type": "database_password",
      "severity": "critical",
      "confidence": "very_high",
      "location": {
        "file": "config/database.py",
        "line": 23,
        "column": 20,
        "snippet": "DB_PASSWORD = 'P@ssw0rd123!'"
      },
      "detected_pattern": "(password|passwd)\\s*=\\s*['\"][^'\"]{8,}['\"]",
      "key_value_preview": "P@ssw***",
      "risk_assessment": {
        "exposure_risk": "critical",
        "git_history_exposed": true,
        "first_commit_date": "2023-06-15",
        "commits_containing_secret": 12,
        "potential_impact": "Database fully compromised if credentials leaked"
      },
      "remediation": {
        "immediate_action": "ROTATE CREDENTIALS IMMEDIATELY",
        "recommended_solution": "Use environment variables or AWS Secrets Manager",
        "code_fix": |
          import os
          DB_PASSWORD = os.environ.get('DB_PASSWORD')
          if not DB_PASSWORD:
              raise ValueError("DB_PASSWORD environment variable not set")
        ,
        "tools": ["AWS Secrets Manager", "Azure Key Vault", "HashiCorp Vault"]
      },
      "status": "open",
      "assigned_to": "Security Team"
    },
    {
      "id": "FINDING-002",
      "type": "api_key",
      "severity": "critical",
      "confidence": "high",
      "location": {
        "file": "services/payment_service.py",
        "line": 56,
        "snippet": "STRIPE_API_KEY = 'sk_live_abc123def456'"
      },
      "risk_assessment": {
        "exposure_risk": "critical",
        "git_history_exposed": true,
        "potential_impact": "Financial loss, unauthorized transactions"
      },
      "remediation": {
        "immediate_action": "REVOKE AND ROTATE API KEY",
        "recommended_solution": "Use Stripe managed environment variables"
      }
    },
    {
      "id": "FINDING-003",
      "type": "jwt_secret",
      "severity": "high",
      "confidence": "medium",
      "location": {
        "file": "auth/token_manager.py",
        "line": 12,
        "snippet": "JWT_SECRET = 'my-super-secret-jwt-key'"
      },
      "risk_assessment": {
        "exposure_risk": "high",
        "git_history_exposed": true,
        "potential_impact": "Token forgery, authentication bypass"
      },
      "remediation": {
        "immediate_action": "Generate new strong secret using crypto.random",
        "code_fix": |
          import secrets
          JWT_SECRET = secrets.token_hex(32)
        }
      }
    }
  ],
  "summary": {
    "total_findings": 3,
    "by_severity": {
      "critical": 2,
      "high": 1,
      "medium": 0,
      "low": 0
    },
    "by_type": {
      "database_password": 1,
      "api_key": 1,
      "jwt_secret": 1
    },
    "in_git_history": 3,
    "require_immediate_rotation": 2,
    "scan_passed": false
  },
  "immediate_actions_required": [
    "🔴 CRITICAL: Rotate database password immediately",
    "🔴 CRITICAL: Revoke Stripe API key and issue new one",
    "🟠 HIGH: Regenerate JWT secret with cryptographically secure method",
    "📋 Clean git history to remove exposed secrets (git filter-repo or BFG Repo Cleaner)",
    "📋 Implement pre-commit hook to prevent future hardcoded secrets"
  ],
  "prevention_recommendations": [
    "Implement git-secrets or detect-secrets as pre-commit hooks",
    "Use .env files with .gitignore protection",
    "Integrate with cloud provider secret management services",
    "Enable branch protection rules blocking commits with secrets",
    "Conduct regular secret scanning on all branches"
  ]
}
```

---

### 阶段五：综合安全报告生成

```
所有安全扫描完成
    ↓
[1] 数据汇总整合
    ↓
[2] 风险等级评定
    ↓
[3] 合规状态评估
    ↓
[4] 修复优先级排序
    ↓
[5] 报告生成与告警
    ↓
输出综合安全扫描报告
```

#### 综合安全报告格式

```json
{
  "report_id": "SECURITY-COMPLETE-001",
  "timestamp": "2024-01-01T00:00:00Z",
  "scan_trigger": "pull_request",
  "pr_info": {
    "number": 123,
    "author": "developer",
    "branch": "feature/payment-integration"
  },
  "executive_summary": {
    "overall_security_status": "FAILED",
    "security_score": 35,
    "risk_level": "CRITICAL",
    "blocking_issues": 2,
    "key_findings": [
      "发现2个Critical级别安全漏洞",
      "检测到3个硬编码密钥泄露",
      "1个高危依赖漏洞需立即修复"
    ],
    "recommendation": "阻止合并，必须先修复所有Critical和High级别问题"
  },
  "scan_results": {
    "owasp_scan": {
      "status": "failed",
      "vulnerabilities_found": 3,
      "critical": 2,
      "high": 1,
      "scan_duration_seconds": 125
    },
    "dependency_scan": {
      "status": "failed",
      "vulnerabilities_found": 2,
      "fixable_with_upgrade": 2,
      "scan_duration_seconds": 45
    },
    "hardcoded_key_scan": {
      "status": "failed",
      "secrets_found": 3,
      "require_rotation": 2,
      "scan_duration_seconds": 30
    }
  },
  "risk_matrix": {
    "likelihood_vs_impact": [
      {"likelihood": "high", "impact": "high", "count": 2, "action": "immediate"},
      {"likelihood": "medium", "impact": "high", "count": 1, "action": "urgent"},
      {"likelihood": "high", "impact": "medium", "count": 2, "action": "plan"}
    ]
  },
  "compliance_impact": {
    "gdpr": "Non-compliant - Article 32 (Security of Processing)",
    "pci_dss": "Non-compliant - Requirement 6 (Secure Software Development)",
    "soc2": "At Risk - CC6.1-CC6.8 Security principles",
    "iso27001": "Non-compliant - A.14.1 System security"
  },
  "action_plan": {
    "immediate_actions": [
      {
        "priority": "P0",
        "deadline": "24 hours",
        "action": "Rotate all exposed credentials",
        "assignee": "DevOps Team"
      },
      {
        "priority": "P0",
        "deadline": "48 hours",
        "action": "Fix SQL injection vulnerabilities",
        "assignee": "Development Team"
      },
      {
        "priority": "P1",
        "deadline": "1 week",
        "action": "Upgrade vulnerable dependencies",
        "assignee": "Development Team"
      }
    ],
    "preventive_measures": [
      "Implement mandatory security code review",
      "Add security scanning to CI/CD pipeline",
      "Deploy secret scanning pre-commit hooks",
      "Schedule monthly dependency updates"
    ]
  },
  "rule_validation_layer_integration": {
    "layer": 3,
    "submodule": "security_scan",
    "security_gates_passed": false,
    "gates_failed": [
      "no_critical_vulnerabilities",
      "no_hardcoded_secrets",
      "dependencies_patched"
    ]
  }
}
```

---

## 与MARC资源协调器的资源需求

```yaml
marc_resource_requirements:
  compute_resources:
    cpu_cores: 4
    memory_gb: 8
    disk_space_gb: 20
    
  execution_time:
    owasp_scan: "< 3 minutes"
    dependency_scan: "< 2 minutes"
    key_detection: "< 1 minute"
    full_security_scan: "< 5 minutes"
    
  external_services:
    - "Snyk API (for vulnerability database)"
    - "NVD API (for CVE data)"
    - "Git history access"
    
  tool_dependencies:
    - "bandit>=1.7.0"
    - "safety>=2.0.0"
    - "semgrep>=1.0.0"
    - "trivy>=0.40.0"
    
  output_storage:
    location: "docs/reviews/code_reviews/security/"
    format: ["json", "sarif"]
    retention_days: 365
    
  alerting:
    channels: ["email", "slack", "pagerduty"]
    escalation_policy: "Critical findings within 15 minutes"
```

---

## 协同调用接口

### 接口定义

| 接口名称 | 接口描述 | 调用方 |
|----------|----------|--------|
| `run_owasp_scan` | OWASP Top 10扫描接口 | 审查报告司、门禁把控司 |
| `scan_dependencies` | 依赖漏洞检测接口 | 审查报告司、许可证审计司 |
| `detect_hardcoded_keys` | 硬编码密钥检测接口 | 审查报告司、安全合规司 |
| `run_full_security_scan` | 完整安全扫描接口 | 门下省主流程、门禁把控司 |

### 调用示例

```bash
# 执行完整安全扫描
python skillscripts/security/security_scanner.py \
  --scan-type full \
  --source ./src \
  --include-owasp \
  --include-dependencies \
  --include-key-detection \
  --output docs/reports/security/full_scan_$(date +%Y%m%d_%H%M%S).json
```

---

## 安全响应流程

### Critical漏洞响应流程

```
发现Critical漏洞
    ↓
[1] 自动阻断合并/部署
    ↓
[2] 立即通知安全团队和负责人
    ↓
[3] 创建高优先级Issue
    ↓
[4] 分配修复责任人
    ↓
[5] 设置SLA: 24小时内修复
    ↓
[6] 修复后重新扫描验证
    ↓
[7] 关闭漏洞并归档
```

---

## 版本历史

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| 1.0.0 | 2026-04-06 | 初始版本，包含OWASP扫描、依赖检测、密钥检测完整能力 |
