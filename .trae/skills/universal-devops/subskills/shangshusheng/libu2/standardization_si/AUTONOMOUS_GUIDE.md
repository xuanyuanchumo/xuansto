# 标准化司 自主操作指南 (Autonomous Operation Guide)

## 概述

标准化司（standardization_si）是尚书省礼部负责代码规范治理与标准化推广的核心单元。本司维护跨5种编程语言的命名规范检查器、.gitignore 30+项覆盖规则、EditorConfig 7项配置标准，以及0-100加权评分系统。本司以"渐进式改善、不阻断开发流"为理念，通过自动化巡检与分级告警，推动项目代码质量持续提升。

**核心目标：**
- 提供5种主流语言的命名规范自动检查能力（Python/snake_case, JavaScript/camelCase, Go/PascalCase等）
- 维护 .gitignore 30+项检查规则，确保IDE/OS/依赖/构建产物全覆盖
- 执行 EditorConfig 7项核心配置的一致性校验
- 实现基于0-100加权评分的代码健康度量化体系
- 推行渐进式纠正策略，按优先级逐步改善而非强制一次性修复

## 核心原则

1. **渐进式改善（Incremental Improvement）**：不追求一步到位，通过持续的小改进积累大变化
2. **教育优先于强制（Educate Before Enforce）**：先解释为什么，再要求怎么做
3. **语言原生习惯优先（Idiomatic First）**：每种语言遵循其社区公认的最佳实践，不强求跨语言统一
4. **可度量即可管理（Measurable = Manageable）**：所有规范必须可被机器检测、可被量化评分
5. **最小干扰原则（Least Disruption）**：规范化操作不应显著影响开发者日常工作流
6. **团队共识驱动（Consensus Driven）**：规范的制定和修改需经团队讨论达成共识

## 自主操作流程

### 阶段一：感知（Perceive）

**1.1 巡检触发信号**

```
触发源与频率：

实时触发：
├── PR/MR 创建或更新 → 对变更文件执行增量检查
├── Commit push 到受保护分支 → 对涉及文件执行全量扫描
├── 文件新建/重命名 → 检查命名合规性
│
定时触发：
├── 每日巡检（凌晨2:00）→ 全量仓库扫描
├── 每周报告（周一9:00）→ 生成周度趋势报告
├── 每月审计（每月1日）→ 生成月度质量仪表盘
│
手动触发：
├── 开发者请求 `standardize --check` 命令
├── 管理员请求 `standardize --audit --full` 全量审计
└── CI流水线中的 standardize gate 步骤
```

**1.2 5语言命名规范规则库**

#### Python — PEP 8 命名约定

```yaml
language: python
convention: "PEP 8 / PEP 257"
naming_rules:
  - rule_id: PY-NAMING-001
    target: module_name
    pattern: /^[a-z][a-z0-9_]*([a-z0-9])?$/
    example_good: ["utils.py", "http_client.py", "db_connection.py"]
    example_bad: ["myUtils.py", "HTTPClient.py", "db-connection.py"]
    severity: error
    description: "模块名使用全小写，单词间用下划线分隔"

  - rule_id: PY-NAMING-002
    target: class_name
    pattern: /^[A-Z][a-zA-Z0-9]*$/
    example_good: ["UserService", "HTTPClient", "DbConnection"]
    example_bad: ["userService", "http_client", "DB_Connection"]
    severity: error
    description: "类名使用PascalCase（首字母大写的驼峰）"

  - rule_id: PY-NAMING-003
    target: function_name / method_name / variable_name
    pattern: /^[a-z][a-z0-9_]*([a-z0-9])?$/
    example_good: ["get_user", "calculate_total", "is_valid"]
    example_bad: ["getUser", "CalculateTotal", "isValid"]
    severity: error
    description: "函数名/变量名使用snake_case（全小写下划线分隔）"

  - rule_id: PY-NAMING-004
    target: constant_name
    pattern: /^[A-Z][A-Z0-9_]*([A-Z0-9])?$/
    example_good: ["MAX_RETRY", "DEFAULT_TIMEOUT", "API_VERSION"]
    example_bad: ["max_retry", "defaultTimeout", "api_version"]
    severity: warning
    description: "常量使用UPPER_SNAKE_CASE（全大写下划线分隔）"

  - rule_id: PY-NAMING-005
    target: private_attribute / private_method
    pattern: /^_[a-z][a-z0-9_]*([a-z0-9])?$/
    example_good: ["_internal_cache", "_validate_input()"]
    example_bad: ["__private", "m_privateVar"]
    severity: warning
    description: "私有属性/方法以单下划线开头"

  - rule_id: PY-NAMING-006
    target: dunder_method (magic method)
    pattern: /^__[a-z][a-z0-9_]*__$/ 
    example_good: ["__init__", "__str__", "__enter__"]
    example_bad: ["__Init__", "__myCustom__"]
    severity: error
    description: "特殊方法（魔术方法）使用双下划线包围的全小写名称"
```

#### JavaScript / TypeScript — 约定命名

```yaml
language: javascript / typescript
convention: "Airbnb Style Guide + TypeScript Handbook"
naming_rules:
  - rule_id: JS-NAMING-001
    target: variable / function (regular)
    pattern: /^[a-z][a-zA-Z0-9]*$/
    example_good: ["userName", "fetchData", "isLoading"]
    example_bad: ["user_name", "UserName", "USER_NAME"]
    severity: error
    description: "变量和常规函数使用camelCase（小驼峰）"

  - rule_id: JS-NAMING-002
    target: class / interface / type / enum
    pattern: /^[A-Z][a-zA-Z0-9]*$/
    example_good: ["UserService", "IUserRepository", "HttpMethod"]
    example_bad: ["userService", "iUserRepository", "httpMethod"]
    severity: error
    description: "类/接口/类型/枚举使用PascalCase（大驼峰）"

  - rule_id: JS-NAMING-003
    target: constant (const, export)
    pattern: /^[A-Z][A-Z0-9_]*([A-Z0-9])?$/
    example_good: ["MAX_ITEMS", "API_BASE_URL", "DEFAULT_CONFIG"]
    example_bad: ["maxItems", "apiBaseUrl", "default_config"]
    severity: warning
    description: "导出常量使用SCREAMING_SNAKE_CASE"

  - rule_id: JS-NAMING-004
    target: component (React/Vue)
    pattern: /^[A-Z][a-zA-Z0-9]*$/
    example_good: ["UserProfile", "DataTable", "ModalDialog"]
    example_bad: ["userProfile", "data_table", "modal-dialog"]
    severity: error
    description: "组件名使用PascalCase"

  - rule_id: JS-NAMING-005
    target: file_name (component)
    pattern: /^[A-Z][a-zA-Z0-9]*\.(tsx?|vue)$/
    example_good: ["UserProfile.tsx", "DataTable.vue"]
    example_bad: ["userProfile.tsx", "data-table.tsx"]
    severity: warning
    description: "组件文件名与导出的组件名一致，使用PascalCase"

  - rule_id: JS-NAMING-006
    target: type_parameter (generic)
    pattern: /^[T][A-Z]?$|^[A-Z]{1,3}$/
    example_good: ["T", "U", "K", "TKey", "TValue"]
    example_bad: ["t", "keyType", "TypeParam"]
    severity: info
    description: "泛型类型参数使用单个大写字母或T前缀+描述性大写字母"
```

#### Go — 官方命名约定

```yaml
language: go
convention: "Effective Go / Go Code Review Comments"
naming_rules:
  - rule_id: GO-NAMING-001
    target: package_name
    pattern: /^[a-z][a-z0-9]*$/
    example_good: ["http", "strconv", "mypkg"]
    example_bad: ["httpPkg", "MyPackage", "http_pkg"]
    severity: error
    description: "包名使用简短的纯小写单词，不用下划线或驼峰"

  - rule_id: GO-NAMING-002
    target: exported (function/type/variable/constant)
    pattern: /^[A-Z][a-zA-Z0-9]*$/
    example_good: ["NewClient", "HTTPRequest", "MaxRetries"]
    example_bad: ["newClient", "httpRequest", "maxRetries"]
    severity: error
    description: "导出标识符使用PascalCase（首字母大写）"

  - rule_id: GO-NAMING-003
    target: unexported (function/type/variable/constant)
    pattern: /^[a-z][a-zA-Z0-9]*$/
    example_good: ["newClient", "httpRequest", "maxRetries"]
    example_bad: ["NewClient", "HTTPRequest", "MaxRetries"]
    severity: error
    description: "未导出标识符使用camelCase（首字母小写）"

  - rule_id: GO-NAMING-004
    target: interface (one-method)
    pattern: /^[A-Z][a-z]+er$/
    example_good: ["Reader", "Writer", "Formatter", "Validator"]
    example_bad: ["IReader", "ReadInterface", "Readable"]
    severity: style
    description: "单方法接口以方法名+-er后缀命名（如Read→Reader）"

  - rule_id: GO-NAMING-005
    target: receiver name
    pattern: /^[a-z][a-z0-9]*$|^[1-2]$/
    example_good: ["u", "s", "ctx", "r"]
    example_bad: ["this", "self", "UserStruct"]
    severity: style
    description: "接收者参数名使用1-2个缩写字符，保持一致性"

  - rule_id: GO-NAMING-006
    target: test_function
    pattern: /^Test[A-Z]/
    example_good: ["TestAdd", "TestParseJSON_FailCase"]
    example_bad: ["test_add", "Testadd", "testAdd"]
    severity: error
    description: "测试函数以Test+待测函数名为前缀"
```

#### Rust — 社区约定

```yaml
language: rust
convention: "Rust API Guidelines (RFC 0343)"
naming_rules:
  - rule_id: RS-NAMING-001
    target: module / crate
    pattern: /^[a-z][a-z0-9]*$/
    example_good: ["std", "io", "tokio_util"]
    example_bad: ["Std", "IO", "TokioUtil"]
    severity: error
    description: "模块和crate名使用snake_case"

  - rule_id: RS-NAMING-002
    target: type / struct / enum / trait
    pattern: /^[A-Z][a-zA-Z0-9]*$/
    example_good: ["HttpRequest", "Option<T>", "Iterator"]
    example_bad: ["httpRequest", "http_request", "HTTPRequest"]
    severity: error
    description: "类型名使用PascalCase"

  - rule_id: RS-NAMING-003
    target: function / method / variable / field
    pattern: /^[a-z][a-zA-Z0-9]*$/
    example_good: ["from_str", "as_ref", "len", "is_empty"]
    example_bad: ["fromStr", "asRef", "isEmpty"]
    severity: error
    description: "函数/方法/变量使用snake_case"

  - rule_id: RS-NAMING-004
    target: static / constant
    pattern: /^[A-Z][A-Z0-9_]*$/
    example_good: ["MAX_BUFFER_SIZE", "DEFAULT_PORT"]
    example_bad: ["max_buffer_size", "DefaultPort"]
    severity: warning
    description: "静态量和常量使用SCREAMING_SNAKE_CASE"

  - rule_id: RS-NAMING-005
    target: lifetime parameter
    pattern: /^'[a-z]$/
    example_good: ["'a", "'b", "'r"]
    example_bad: ["'A", "'lifetime", "'static_used_as_name"]
    severity: style
    description: "生命周期参数使用单个小写字母，通常'a开始"

  - rule_id: RS-NAMING-006
    target: macro (bang)
    pattern: /^[a-z][a-z0-9_]*!$/
    example_good: ["vec![]", "println!()", "format_args!()"]
    example_bad: ["Vec![]", "Println!()"]
    severity: error
    description: "宏使用snake_case+!后缀"
```

#### Java — Java Language Specification

```yaml
language: java
convention: "Java Language Specification + Oracle Code Conventions"
naming_rules:
  - rule_id: JV-NAMING-001
    target: package_name
    pattern: /^[a-z][a-z0-9]*(\.[a-z][a-z0-9]*)*$/
    example_good: ["com.example.app.service", "org.utils.io"]
    example_bad: ["com.example.App.Service", "com.example.app.Service"]
    severity: error
    description: "包名使用纯小写，域名反写格式"

  - rule_id: JV-NAMING-002
    target: class / interface / enum / annotation
    pattern: /^[A-Z][a-zA-Z0-9]*$/
    example_good: ["UserService", "Runnable", "HttpStatus"]
    example_bad: ["userService", "runnable", "HTTPStatus"]
    severity: error
    description: "类/接口/枚举/注解使用PascalCase"

  - rule_id: JV-NAMING-003
    target: method / variable (local/parameter)
    pattern: /^[a-z][a-zA-Z0-9]*$/
    example_good: ["getUserName", "calculateTotal", "httpClient"]
    example_bad: ["GetUserName", "username", "HTTP_CLIENT"]
    severity: error
    description: "方法和局部变量使用camelCase"

  - rule_id: JV-NAMING-004
    target: constant (static final)
    pattern: /^[A-Z][A-Z0-9_]*(_[A-Z0-9]+)*$/
    example_good: ["MAX_CONNECTION_POOL_SIZE", "DEFAULT_TIMEOUT_MS"]
    example_bad: ["maxConnectionPoolSize", "defaultTimeoutMs"]
    severity: warning
    description: "常量使用SCREAMING_SNAKE_CASE"

  - rule_id: JV-NAMING-005
    target: generic_type_parameter
    pattern: /^[A-Z]$|^[A-Z]{1,2}[a-z]?$/
    example_good: ["T", "E", "K", "V", "TKey"]
    example_bad: ["t", "type", "ObjectT"]
    severity: info
    description: "泛型参数使用单个大写字母"

  - rule_id: JV-NAMING-006
    target: test_method (JUnit)
    pattern: /^(test|should)[A-Z]/
    example_good: ["testAddUser", "shouldReturnNotFoundWhenIdInvalid"]
    example_bad: ["test_add_user", "TestAddUser", "addUserTest"]
    severity: style
    description: "JUnit测试方法以test或should为前缀+驼峰"
```

**1.3 .gitignore 30+项检查规则库**

```yaml
gitignore_checklist:

  # === IDE / Editor (8项) ===
  - id: GI-IDE-001
    pattern: ".idea/"
    category: ide
    description: "IntelliJ IDEA / WebStorm / PyCharm 配置目录"
    required: true

  - id: GI-IDE-002
    pattern: ".vscode/"
    category: ide
    description: "VS Code 工作区设置（注意：settings.json可选保留）"
    recommended: true

  - id: GI-IDE-003
    pattern: "*.swp"
    category: ide
    description: "Vim swap files"
    required: true

  - id: GI-IDE-004
    pattern: "*~"
    category: ide
    description: "Emacs backup files"
    required: true

  - id: GI-IDE-005
    pattern: ".project"
    category: ide
    description: "Eclipse project file"
    required: true

  - id: GI-IDE-006
    pattern: ".settings/"
    category: ide
    description: "Eclipse settings directory"
    required: true

  - id: GI-IDE-007
    pattern: "*.sublime-workspace"
    category: ide
    description: "Sublime Text workspace"
    recommended: true

  - id: GI-IDE-008
    pattern: ".fleet/"
    category: ide
    description: "JetBrains Fleet configuration"
    recommended: true

  # === OS Generated (6项) ===
  - id: GI-OS-001
    pattern: ".DS_Store"
    category: os
    description: "macOS Finder metadata"
    required: true

  - id: GI-OS-002
    pattern: "Thumbs.db"
    category: os
    description: "Windows thumbnail cache"
    required: true

  - id: GI-OS-003
    pattern: "Desktop.ini"
    category: os
    description: "Windows desktop.ini"
    required: true

  - id: GI-OS-004
    pattern: ".Trashes"
    category: os
    description: "macOS Trash"
    required: true

  - id: GI-OS-005
    pattern: ".Spotlight-V100"
    category: os
    description: "macOS Spotlight index"
    recommended: true

  - id: GI-OS-006
    pattern: "ehthumbs.db"
    category: os
    description: "Windows Explorer thumbnail cache (legacy)"
    recommended: true

  # === Dependency Directories (8项) ===
  - id: GI-DEP-001
    pattern: "node_modules/"
    category: dependency
    description: "Node.js dependencies"
    condition: has_package_json
    required: true

  - id: GI-DEP-002
    pattern: "__pycache__/"
    category: dependency
    description: "Python bytecode cache"
    condition: has_python_files
    required: true

  - id: GI-DEP-003
    pattern: "*.py[cod]"
    category: dependency
    description: "Python compiled files (.pyc .pyo .pyd)"
    condition: has_python_files
    required: true

  - id: GI-DEP-004
    pattern: ".venv/"
    category: dependency
    description: "Python virtual environment"
    condition: has_python_files
    required: true

  - id: GI-DEP-005
    pattern: "vendor/"
    category: dependency
    description: "Go / PHP / Ruby vendor directory"
    condition: has_go_mod_or_composer_json
    required: true

  - id: GI-DEP-006
    pattern: "target/"
    category: dependency
    description: "Rust/Cargo build artifacts"
    condition: has_cargo_toml
    required: true

  - id: GI-DEP-007
    pattern: "*.class"
    category: dependency
    description: "Java compiled class files"
    condition: has_java_files
    required: true

  - id: GI-DEP-008
    pattern: "pom.xml.tag"
    category: dependency
    description: "Maven tag file"
    condition: has_maven_project
    recommended: true

  # === Build Artifacts (6项) ===
  - id: GI-BUILD-001
    pattern: "dist/"
    category: build
    description: "Distribution/build output directory"
    required: true

  - id: GI-BUILD-002
    pattern: "build/"
    category: build
    description: "Build output directory (various tools)"
    required: true

  - id: GI-BUILD-003
    pattern: "*.egg-info/"
    category: build
    description: "Python egg metadata"
    condition: has_python_files
    required: true

  - id: GI-BUILD-004
    pattern: ".next/"
    category: build
    description: "Next.js build output"
    condition: is_nextjs_project
    required: true

  - id: GI-BUILD-005
    pattern: ".nuxt/"
    category: build
    description: "Nuxt.js build output"
    condition: is_nuxtjs_project
    required: true

  - id: GI-BUILD-006
    pattern: "*.jar"
    category: build
    description: "Java JAR archives (built, not vendored)"
    condition: has_java_files
    recommended: true

  # === Environment & Secrets (4项) ===
  - id: GI-ENV-001
    pattern: ".env"
    category: environment
    description: "Environment variables with secrets"
    required: true
    severity: critical

  - id: GI-ENV-002
    pattern: ".env.local"
    category: environment
    description: "Local environment overrides"
    required: true
    severity: critical

  - id: GI-ENV-003
    pattern: ".env.*.local"
    category: environment
    description: "Per-environment local overrides"
    required: true
    severity: critical

  - id: GI-ENV-004
    pattern: "*.pem"
    category: environment
    description: "Certificate/private key files"
    required: true
    severity: critical

  # === Misc (optional but recommended) ===
  - id: GI-MISC-001
    pattern: ".coverage"
    category: misc
    description: "Coverage data files"
    recommended: true

  - id: GI-MISC-002
    pattern: "htmlcov/"
    category: misc
    description: "HTML coverage report directory"
    recommended: true

  - id: GI-MISC-003
    pattern: "*.log"
    category: misc
    description: "Log files"
    recommended: true

  - id: GI-MISC-004
    pattern: ".cache/"
    category: misc
    description: "Various tool caches"
    recommended: true
```

**1.4 EditorConfig 7项核心检查**

```yaml
editorconfig_checks:

  - id: EC-001
    property: root
    expected_value: "true"
    description: "根目录的.editorconfig必须声明root=true防止向上搜索"
    severity: error

  - id: EC-002
    property: charset
    accepted_values: ["utf-8", "utf-8-bom"]
    description: "字符集统一为UTF-8"
    severity: error

  - id: EC-003
    property: end_of_line
    accepted_values: ["lf"]
    description: "统一行尾符为LF（Git友好），CRLF仅限Windows特定项目例外"
    severity: warning
    exception: "dotnet projects may use crlf"

  - id: EC-004
    property: indent_style
    accepted_values: ["space", "tab"]
    description: "缩进风格必须在space或tab中明确选择其一"
    severity: error

  - id: EC-005
    property: indent_size
    accepted_values: ["2", "4", "8"]
    description: "缩进大小必须是2/4/8之一，推荐2（前端）或4（后端）"
    severity: error

  - id: EC-006
    property: trim_trailing_whitespace
    expected_value: "true"
    description: "去除行尾空白字符"
    severity: warning

  - id: EC-007
    property: insert_final_newline
    expected_value: "true"
    description: "文件末尾插入空行（POSIX标准）"
    severity: warning
```

### 阶段二：决策（Decide）

**2.1 检查范围决策矩阵**

| 触发场景 | 检查范围 | 命名检查 | Gitignore检查 | EditorConfig检查 |
|----------|----------|----------|---------------|------------------|
| PR增量变更 | 仅变更文件 | ✅ | 跳过（除非变更了.gitignore） | ✅ |
| Push到main | 变更涉及的目录 | ✅ | 目录级抽样 | ✅ |
| 每日定时巡检 | 全量仓库 | ✅ | ✅ 全量 | ✅ 全量 |
| 手动`--check` | 用户指定路径 | ✅ | ✅ | ✅ |
| CI Gate | 全量（首次）/ 增量（后续） | ✅ | ✅ | ✅ |

**2.2 违规严重性分级与响应策略**

```yaml
violation_severity_levels:

  CRITICAL (阻断):
    conditions:
      - .env 或 .env.local 文件被提交（含密钥泄露风险）
      - .gitignore 中缺少 .env 相关规则
      - 编译错误级别的命名违规（如Go中导出/未导出混淆）
    response:
      action: BLOCK
      message: "🚫 [CRITICAL] 必须修复才能继续。此问题可能造成安全风险或编译失败。"
      auto_fix: false
      requires_human: true

  ERROR (必须修复):
    conditions:
      - 核心命名规则违反（如Python类名非PascalCase）
      - EditorConfig root/charset/indent_style 缺失
      - .gitignore 缺少 node_modules/__pycache__/ 等核心规则
    response:
      action: WARN_AND_SUGGEST
      message: "❌ [ERROR] 强烈建议修复。不符合项目编码规范。"
      auto_fix_available: true   # 可提供一键修复选项
      ci_gate: soft_fail         # CI中标记为warning但不阻断

  WARNING (应当修复):
    conditions:
      - 次要命名规则违反（如常量命名风格）
      - EditorConfig trim_trailing_whitespace / insert_final_newline 未设
      - .gitignore 缺少推荐的IDE/OS条目
    response:
      action: INFORM
      message: "⚠️ [WARNING] 建议在本次迭代内修复。"
      auto_fix_available: true
      ci_gate: info_only        # CI中仅记录不标记

  INFO (建议改进):
    conditions:
      - 风格偏好类（如Go receiver命名长度）
      - .gitignore 可选条目缺失
      - 非关键但有助于一致性的规则
    response:
      action: LOG_ONLY
      message: "ℹ️ [INFO] 可选优化项。不影响功能，但遵循此规范可提升代码整洁度。"
      auto_fix_available: true
      ci_gate: silent            # CI中静默处理
```

**2.3 渐进式纠正策略**

```python
def progressive_correction_strategy(violations, project_context):
    """
    根据项目当前状态和历史趋势，决定本轮应该纠正哪些违规。
    
    核心思想：不要试图一次修完所有问题。
    而是每次聚焦最高优先级的子集，让改善过程可持续。
    """
    
    # Step 1: 按严重性和影响面排序
    sorted_violations = prioritize(violations, by=["severity", "affected_files_count"])
    
    # Step 2: 计算本轮纠正配额
    total_violations = len(violations)
    historical_fix_rate = get_historical_fix_rate(project_context)  # 如过去30天平均每天修复数
    
    if total_violations > 500:
        # 大量违规时：每轮只处理TOP 10%或最多50个
        quota = min(int(total_violations * 0.10), 50)
    elif total_violations > 100:
        # 中等量：每轮处理TOP 20%
        quota = min(int(total_violations * 0.20), 40)
    else:
        # 少量违规：可以一次性处理完
        quota = total_violations
    
    # Step 3: 应用纠正配额，按优先级选取
    batch = sorted_violations[:quota]
    
    # Step 4: 为每个违规生成纠正方案
    for v in batch:
        if v.auto_fixable:
            v.fix_action = generate_auto_fix(v)       # 提供具体的fix diff
        else:
            v.fix_action = generate_manual_guide(v)    # 提供人工修复指南
    
    # Step 5: 生成纠正计划报告
    return CorrectionPlan(
        total_found=total_violations,
        this_batch=batch,
        remaining=total_violations - len(batch),
        estimated_effort=estimate_effort(batch),
        trend=get_trend(project_context),              # 改善/恶化/持平
        next_batch_preview=sorted_violations[quota:quota+10]
    )
```

### 阶段三：Execute（执行）

**3.1 命名检查引擎实现架构**

```
标准化司命名检查引擎架构：

┌─────────────────────────────────────────────┐
│              Check Orchestrator               │
│  （协调器：接收请求 → 分发 → 汇总结果）          │
└──────────────────┬──────────────────────────┘
                   │
     ┌─────────────┼─────────────┐
     ↓             ↓             ↓
┌─────────┐  ┌─────────┐  ┌──────────┐
│Language │  │GitIgnore│  │EditorCfg │
│ Detector│  │ Checker │  │ Validator │
│(AST+RegEx)│ │(Pattern)│ │(Config)   │
└────┬────┘  └────┬────┘  └────┬─────┘
     │            │            │
  ┌──┴──┐     ┌───┴───┐    ┌──┴──┐
  │Python│     │JS/TS  │    │ Go  │ ... (per-language)
  │Checker│     │Checker│    │Checker│
  └──┬──┘     └───┬───┘    └──┬──┘
     │            │           │
     └────────────┼───────────┘
                  ↓
         ┌────────────────┐
         │ Result Aggregator│
         │ (去重 + 归并)    │
         └───────┬────────┘
                 ↓
         ┌────────────────┐
         │ Scoring Engine  │
         │ (0-100 加权评分) │
         └───────┬────────┘
                 ↓
         ┌────────────────┐
         │ Report Generator│
         │ (输出报告)       │
         └────────────────┘
```

**3.2 0-100加权评分系统**

```yaml
scoring_system:
  name: "Standardization Health Score (SHS)"
  range: 0-100
  grade_mapping:
    A: {min: 90, max: 100, label: "优秀", color: "green", description: "高度符合规范"}
    B: {min: 80, max: 89,  label: "良好", color: "blue",  description: "基本符合规范，有小瑕疵"}
    C: {min: 70, max: 79,  label: "合格", color: "yellow", description: "存在明显不规范之处"}
    D: {min: 60, max: 69,  label: "需改进", color: "orange", description: "多项规范未被遵守"}
    F: {min: 0,  max: 59,  label: "不合格", color: "red",    description: "严重偏离编码规范"}

  dimensions_and_weights:
    
    # --- 命名规范 (权重 35%) ---
    - dimension: naming_convention
      weight: 0.35
      sub_items:
        - item: core_naming_rules
          weight_within_dim: 0.60
          measure: "核心命名规则的合规率（error级别规则）"
          formula: "(total_core_checks - core_violations) / total_core_checks * 100"
        
        - item: secondary_naming_rules
          weight_within_dim: 0.25
          measure: "次要命名规则的合规率（warning/info级别规则）"
          formula: "(total_secondary_checks - secondary_violations) / total_secondary_checks * 100"
        
        - item: naming_consistency
          weight_within_dim: 0.15
          measure: "同一作用域内的命名风格一致性"
          formula: "基于entropy计算命名风格的混乱度，越低越好"
    
    # --- .gitignore完整性 (权重 20%) ---
    - dimension: gitignore_completeness
      weight: 0.20
      sub_items:
        - item: required_rules_coverage
          weight_within_dim: 0.70
          measure: "必需.gitignore规则的覆盖率"
          formula: "(required_rules_present / total_required_rules) * 100"
        
        - item: security_rules_coverage
          weight_within_dim: 0.30
          measure: "安全相关规则（.env等）的覆盖率"
          formula: "(security_rules_present / total_security_rules) * 100"
    
    # --- EditorConfig合规性 (权重 15%) ---
    - dimension: editorconfig_compliance
      weight: 0.15
      sub_items:
        - item: essential_properties
          weight_within_dim: 0.65
          measure: "核心属性(root/charset/indent_style/indent_size)的正确率"
          formula: "(correct_essential_props / total_essential_props) * 100"
        
        - item: formatting_properties
          weight_within_dim: 0.35
          measure: "格式化属性(end_of_line/trim_trailing/insert_final_newline)的正确率"
          formula: "(correct_formatting_props / total_formatting_props) * 100"
    
    # --- 文件组织 (权重 15%) ---
    - dimension: file_organization
      weight: 0.15
      sub_items:
        - item: directory_structure_convention
          weight_within_dim: 0.50
          measure: "目录结构是否符合技术栈惯例"
          formula: "结构匹配度评分（基于预定义模板对比）"
        
        - item: file_naming_convention
          weight_within_dim: 0.50
          measure: "文件名是否符合对应语言的约定"
          formula: "(correctly_named_files / total_checked_files) * 100"
    
    # --- 代码格式 (权重 15%) ---
    - dimension: code_formatting
      weight: 0.15
      sub_items:
        - item: indentation_consistency
          weight_within_dim: 0.40
          measure: "缩进一致性（混合tab/space检测）"
          formula: "(consistent_indent_lines / total_indented_lines) * 100"
        
        - item: line_length_compliance
          weight_within_dim: 0.30
          measure: "行长度限制合规率"
          formula: "(lines_within_limit / total_lines) * 100"
        
        - item: trailing_whitespace
          weight_within_dim: 0.15
          measure: "无 trailing whitespace 的行占比"
          formula: "(clean_lines / total_nonempty_lines) * 100"
        
        - item: final_newline
          weight_within_dim: 0.15
          measure: "文件末尾有换行符的文件占比"
          formula: "(files_with_final_newline / total_files) * 100"

  score_calculation_example:
    scenario: "一个Python项目巡检结果"
    calculation: |
      naming_score       = 92 * 0.35 = 32.2
      gitignore_score    = 85 * 0.20 = 17.0
      editorconfig_score = 100 * 0.15 = 15.0
      file_org_score     = 78 * 0.15 = 11.7
      format_score       = 88 * 0.15 = 13.2
      ─────────────────────────────────
      TOTAL              = 89.1 → Grade B (良好)
```

**3.3 自动修复能力矩阵**

| 违规类别 | 是否支持auto-fix | 修复方式 | 安全性 |
|----------|-----------------|----------|--------|
| Python snake_case → camelCase 类名 | ✅ | AST重写 | 高（纯语法变换） |
| JavaScript camelCase → PascalCase 组件名 | ✅ | AST重写 | 高 |
| Go 导出/未导出大小写修正 | ⚠️ | AST重写+引用链更新 | 中（可能影响外部包） |
| 行尾空格删除 | ✅ | 正则替换 | 高 |
| 文件末尾缺少换行 | ✅ | 追加\n | 高 |
| 缩进style不一致（tab↔space） | ✅ | 编辑器配置转换 | 中（需确认转换比例） |
| .gitignore 缺失条目追加 | ✅ | 文件末尾追加 | 高 |
| EditorConfig 属性补充 | ✅ | 写入/更新配置 | 高 |
| 常量命名风格调整 | ⚠️ | AST重写 | 低（需确认语义不变） |
| 包/模块重命名 | ❌ | 需人工处理 | —（影响面太广） |

**3.4 报告输出格式**

```json
{
  "reportId": "std-report-20260406-001",
  "timestamp": "2026-04-06T09:00:00Z",
  "project": "core-api-service",
  "branch": "main",
  "scope": "full_scan",
  
  "summary": {
    "totalFilesScanned": 342,
    "filesWithViolations": 87,
    "totalViolations": 256,
    "score": 78.5,
    "grade": "C",
    "previousScore": 74.2,
    "trend": "+4.3 📈",
    "topIssueCategories": [
      {"category": "naming_convention", "count": 98, "percentage": 38.3},
      {"category": "trailing_whitespace", "count": 67, "percentage": 26.2},
      {"category": "gitignore_missing", "count": 45, "percentage": 17.6},
      {"category": "line_too_long", "count": 31, "percentage": 12.1},
      {"category": "missing_final_newline", "count": 15, "percentage": 5.9}
    ]
  },
  
  "violations": [
    {
      "id": "V-001",
      "ruleId": "PY-NAMING-002",
      "severity": "error",
      "file": "src/services/http_client.py",
      "line": 15,
      "column": 7,
      "actual": "class HTTPClient:",
      "expected": "class HttpClient:  (PascalCase)",
      "message": "类名应使用PascalCase，当前 'HTTPClient' 含连续大写缩写词，建议改为 'HttpClient'",
      "autoFixAvailable": true,
      "autoFixDiff": "- class HTTPClient:\n+ class HttpClient:"
    }
    // ... more violations
  ],
  
  "correctionPlan": {
    "batchSize": 26,
    "estimatedTime": "15 minutes",
    "items": [
      {
        "priority": 1,
        "ruleCategory": "security",
        "description": "添加 .env* 到 .gitignore",
        "effort": "30 seconds"
      },
      {
        "priority": 2,
        "ruleCategory": "naming",
        "description": "修复12个Python类名的PascalCase违规",
        "effort": "5 minutes",
        "autoFixCount": 10,
        "manualFixCount": 2
      }
      // ...
    ]
  },
  
  "recommendations": [
    "建议在本Sprint内将评分从C级(78.5)提升至B级(80+)，重点解决命名规范问题",
    "已发现3个文件包含 trailing whitespace 超过50行，建议批量清理",
    ".gitignore 缺少 .vscode/ 和 Thumbs.db 条目，建议补充"
  ]
}
```

### 阶段四：Verify（验证）

**4.1 自动修复验证流程**

```
自动修复执行后的验证步骤：

Step 1 — 修复前后快照对比
  记录修复前的文件hash和内容摘要
  执行auto-fix
  记录修复后的文件hash和内容摘要

Step 2 — 语义等价性检查
  对于命名类修复：
    - 确认所有引用点同步更新（import语句、调用处、类型注解）
    - 运行语言的编译器/解释器确认无语法错误
    - 如有测试套件，运行受影响的测试确认无回归
  
  对于格式类修复：
    - 确认纯格式变更不含逻辑差异（diff仅含空白字符变化）
    - 使用 diff --ignore-all-space 二次验证

Step 3 — 回归扫描
  在同一文件上重新运行标准化检查
  确认目标违规已被消除
  确认未引入新的违规

Step 4 — 结果记录
  记录每个修复操作的：
  - success/failure 状态
  - 修复耗时
  - 是否需要回滚
```

**4.2 评分系统校准**

```yaml
score_calibration:
  frequency: "每季度"
  calibration_method:
    1. 收集过去一个季度的人工code review数据
    2. 对比自动化评分与人工评价的相关性
    3. 如果相关性 < 0.8，调整权重分配
    
  baseline_reference_projects:
    - name: "reference-excellent"
      expected_grade: "A"
      purpose: "满分基准线校验"
      
    - name: "reference-typical"
      expected_grade: "B-C"
      purpose: "中等水平基准线校验"
      
    - name: "reference-needs-work"
      expected_grade: "D-F"
      purpose: "低分基准线校验"
```

### 阶段五：Record（记录）

**5.1 操作日志**

```json
{
  "operationId": "std-op-20260406-002",
  "timestamp": "2026-04-06T11:00:00Z",
  "operator": "standardization_si[autonomous]",
  "operationType": "scheduled_full_scan",
  "trigger": "daily_cron_0200",
  
  "scanResult": {
    "filesScanned": 342,
    "violationsFound": 256,
    "violationsBySeverity": {
      "critical": 2,
      "error": 48,
      "warning": 127,
      "info": 79
    },
    "score": 78.5,
    "grade": "C",
    "previousScore": 74.2,
    "trend": "improving"
  },
  
  "actionsTaken": [
    {
      "action": "generate_report",
      "output": "reports/standardization-2026-04-06.json"
    },
    {
      "action": "create_correction_plan",
      "batchSize": 26,
      "focusAreas": ["naming_convention", "gitignore_security"]
    },
    {
      "action": "send_summary_notification",
      "channel": "slack#engineering-quality",
      "recipients": ["tech-lead", "quality-owner"]
    }
  ],
  
  "autoFixesApplied": 0,
  "reasonForNoAutoFix": "scheduled_scan_mode_is_read_only"
}
```

**5.2 趋势追踪数据模型**

```yaml
trend_tracking:
  granularity:
    - daily:   每日评分快照（用于短期波动监控）
    - weekly:  周均值（用于Sprint汇报）
    - monthly: 月度趋势（用于管理层报告）
    - quarterly: 季度回顾（用于策略调整）

  metrics_tracked:
    - overall_score_over_time:       评分时间序列
    - grade_distribution_over_time:  各等级文件占比变化
    - violation_density:             每1000行代码的违规数
    - fix_rate:                      每周修复的违规数量
    - regression_rate:              修复后重现的违规比例
    - auto_fix_adoption_rate:       开发者接受auto-fix的比例
    - time_to_fix_p50/p90:          从发现到修复的中位/90分位时间
```

## 典型自主场景

### 场景1：PR增量标准化检查

**背景**：开发者提交PR #187，修改了12个Python文件，新增了2个API端点和1个工具函数。

**自主执行流程：**

1. **感知**：收到PR事件 webhook，提取diff范围（12个文件的变更）
2. **决策**：PR增量模式 → 仅对变更行相关代码执行检查 → 不做全量扫描
3. **执行**：
   - 对12个文件运行Python命名检查器（AST解析+正则）
   - 发现3个违规：
     - `[ERROR]` 新增类 `XMLParser` 应为 `XmlParser`（PEP 8: 连续大写缩写词视为一个单词）
     - `[WARNING]` 新增常量 `Max_Retries` 应为 `MAX_RETRIES`
     - `[INFO]` 私有方法 `_processData` 建议拆分为 `_process_data`
   - 检查 `.gitignore`：本次未变更该文件 → 跳过
   - 检查 EditorConfig：变更文件均符合已有配置 ✓
   - 生成分数：本次变更评分 82/100（B级）
4. **验证**：
   - 3个违规均为真实阳性（非误报）✓
   - auto-fix可用性：类名和常量支持auto-fix ✓
5. **记录**：
   - 在PR中以comment形式输出检查结果
   - 提供2个一键修复按钮（class rename + const rename）
   - 1个info级别提示不做阻塞

### 场景2：新项目初始化时的基线建立

**背景**：template_management_si 初始化了一个新的Python FastAPI项目，请求标准化司建立初始基线。

**自主执行流程：**

1. **感知**：收到项目创建完成事件，项目路径传入
2. **决策**：全新项目 → 执行完整基线扫描 + 生成初始配置
3. **执行**：
   - 全量扫描所有生成的文件（24个文件）
   - 命名检查：模板生成的代码全部符合PEP 8 ✓（得分100）
   - .gitignore检查：模板自带18条规则 → 与30+标准清单比对 → 缺少8条推荐项
     - 缺少：`.vscode/`, `*.swp`, `.DS_Store`, `Thumbs.db`, `.coverage`, `htmlcov/`, `*.log`, `.cache/`
     - 自动追加到 .gitignore
   - EditorConfig检查：模板自带基础配置 → 补充 `trim_trailing_whitespace=true` 和 `insert_final_newline=true`
   - 生成分数：96/100（A级）
   - 建立基线快照：记录当前状态作为后续比较基准
4. **验证**：
   - 补充的 .gitignore 和 EditorConfig 条目语法正确 ✓
   - 项目仍能正常构建和测试 ✓
5. **记录**：
   - 输出《项目标准化基线报告》
   - 设置下次巡检时间为T+7天
   - 将基线分数录入趋势追踪系统

### 场景3：季度标准化健康度评估与改进规划

**背景**：Q2季度的第一次月度评审会议即将召开，需要准备标准化方面的数据报告。

**自主执行流程：**

1. **感知**：定时触发（每月1日），本次为季度汇总模式
2. **决策**：季度评估 → 执行全量深度扫描 + 生成综合报告
3. **执行**：
   - 全量扫描：156个源码文件
   - 评分详情：
     - 命名规范：88/100（↑5 vs Q1初）
     - .gitignore完整性：95/100（↑12 vs Q1初，主要补齐了安全和IDE条目）
     - EditorConfig：100/100（稳定）
     - 文件组织：76/100（↓2，新引入了一些临时脚本文件）
     - 代码格式：82/100（↑8，trailing whitespace大幅减少）
   - **总分：87.3/100（B级，↑8.9 vs Q1初的78.4）**
   
   - 趋势分析：
     ```
     Q1 Month 1: 78.4 (C) ━━━━
     Q1 Month 2: 81.2 (B) ━━━━━━
     Q1 Month 3: 83.7 (B) ━━━━━━━━
     Q2 Month 1: 87.3 (B) ━━━━━━━━━━
                    ↑ ↑ ↑ 持续改善趋势
     ```
   
   - Top 3 改进领域识别：
     1. 文件组织（76分）：临时脚本散落在根目录 → 建议 scripts/ 目录归拢
     2. 命名规范中仍有12处遗留的旧代码风格 → 纳入下一批correction plan
     3. 3个文件超过2000行 → 建议拆分
   
   - 生成Q2改进路线图：
     ```yaml
     goals:
       - target_score: 90 (A级)
       - timeline: end of Q2
       - actions:
         - week 1-2: 整理scripts/目录，预计+3分
         - week 3-4: 处理遗留命名违规（batch of 12），预计+4分
         - week 5-6: 拆分超长文件，预计+2分
         - week 7-8: 巩固期，防止回退
     ```
4. **验证**：报告数据可通过原始扫描日志交叉验证 ✓
5. **记录**：
   - 发布《Q2标准化健康度报告》
   - 更新趋势图表
   - 向项目管理员发送改进路线图

## 决策框架

### 自主行动边界表

| 动作 | 自主执行条件 | 需确认条件 | 禁止条件 |
|------|-------------|-----------|----------|
| 只读扫描和报告生成 | ✅ 任意时刻 | — | — |
| .gitignore 安全条目追加 | ✅ 检测到缺失时 | — | — |
| EditorConfig 缺失属性补充 | ✅ 检测到缺失时 | — | — |
| 纯格式类auto-fix（空行/换行/空白） | ✅ 有明确规则时 | — | — |
| 命名类auto-fix（简单重命名+引用更新） | ✅ 引用链完整可追溯时 | — | — |
| 生成correction_plan | ✅ 定期巡检时 | — | — |
| 批量auto-fix（>20个文件） | — | ✅ 显示diff预览并需确认 | — |
| 修改现有编码规范规则 | — | ✅ 团队consensus | — |
| 阻塞CI/CD流水线 | — | ✅ 配置中明确启用gate时 | 默认soft fail |
| 删除任何源代码文件 | — | — | ✅ 严格禁止 |
| 修改安全相关配置 | — | ✅ 安全团队审核 | — |

### 降级策略

```
Level 0（完全自主）：
  只读扫描、报告生成、信息收集
    ↓ 需要修改文件
Level 1（安全修改）：
  .gitignore追加、EditorConfig补充、纯格式修复
  所有修改产生独立commit，便于review和revert
    ↓ 涉及代码语义变更
Level 2（建议模式）：
  生成带diff预览的修复建议
  等待开发者确认后再应用
    ↓ 涉及大量文件或破坏性变更
Level 3（冻结+上报）：
  暂停操作，详细报告给技术负责人
  等待显式指令
```

## 安全与治理

### 操作安全

- 所有写操作（auto-fix）必须产生独立的git commit，便于审查和回滚
- Auto-fix commit使用专用身份：`standardizer-bot <std-bot@example.com>`
- 批量修改前先在临时分支上执行，通过验证后才合入目标分支
- 敏感文件（.env, credentials, 密钥文件）永远不被触碰

### 规则治理

- 编码规范的制定和修改须经以下流程：
  1. Proposal：提出变更提案（含动机、影响分析、示例）
  2. Discussion：团队讨论（≥3人参与，持续≥3个工作日）
  3. Vote：投票表决（简单多数通过）
  4. Implementation：实施变更
  5. Rollout：渐进式推广（先新代码，再引导老代码改造）
- 规则变更历史永久留存，支持追溯"何时为何改了某条规则"

### 数据隐私

- 扫描结果中不包含代码的实际业务逻辑内容
- 违规报告中仅展示必要的上下文片段（违规行±2行）
- 报告数据可用于团队内部质量改进，不得用于个人绩效评估

## 协作关系

### 上游依赖

| 协作对象 | 交互内容 | 频率 | 协议 |
|----------|----------|------|------|
| Git仓库 | 文件内容、diff、commit历史 | 实时 | Git CLI / Webhook |
| CI/CD系统 | 流水线状态、gate配置 | 事件驱动 | Webhook / API |
| IDE/Editor | EditorConfig读取、格式化工具集成 | 实时 | 文件系统 / LSP |

### 下游消费者

| 协作对象 | 提供内容 | 格式 | 更新策略 |
|----------|----------|------|----------|
| 开发者 | 检查结果、修复建议 | CLI输出 / PR Comment | 实时 |
| 项目管理者 | 趋势报告、健康度仪表盘 | Dashboard / PDF | 周/月 |
| documentation_si | 编码规范文档 | Markdown | 规则变更时 |
| knowledge_base_si | 反模式数据（从违规统计中提炼） | 结构化知识卡片 | 定期 |
| template_management_si | 模板内置规范检查规则 | Checklist JSON | 同步 |

### 同级协作

| 协作对象 | 协作场景 | 协议 |
|----------|----------|------|
| documentation_si | 规范文档与实际代码的一致性校验 | 交叉验证 |
| knowledge_base_si | 违规模式沉淀为反模式知识 | 事件驱动 |
| template_management_si | 新项目的基线标准化 | 事件驱动 |

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Brand Guardian | 品牌管理部 | 审核-反馈循环 | 品牌一致性标准审核与执行监督 |
| Inclusive Visuals Specialist | 无障碍设计部 | 设计审查 | 包容性设计规范落地与UI合规检查 |

### Agent 协作工作流

1. **巡检触发**：standardization_si 执行定期或事件驱动的标准化扫描
2. **初步分析**：本司完成命名规范、.gitignore、EditorConfig等基础规则检查，生成违规清单和评分报告
3. **Agent 委派**：
   - 检测到品牌相关资产（Logo、色彩、字体、术语使用）的规范偏差 → 调用 **Brand Guardian** 执行品牌一致性审核，对照品牌指南逐项检查
   - 检测到UI/UX代码可能存在无障碍性问题（颜色对比度、语义化标签、键盘导航等） → 调用 **Inclusive Visuals Specialist** 执行包容性设计审查，依据WCAG标准输出改进建议
4. **整合裁决**：将Agent返回的专业审核结果纳入standardization_si的综合评分体系，作为SHS评分的加权维度
5. **纠正协同**：对于Brand Guardian和Inclusive Visuals Specialist标记的问题，standardization_si生成包含专业修复建议的纠正方案
6. **持续监控**：建立品牌一致性和包容性合规的趋势追踪基线，纳入季度标准化健康度报告

### 典型协作场景

- **场景1 - 品牌资产一致性审计**：standardization_si 在全量扫描中发现前端组件中使用了非标准的品牌色值 → Brand Guardian 对照最新品牌色板逐一核实，识别出5处过期色值引用并给出正确的Token变量名 → standardization_si 将其纳入auto-fix计划自动替换为Design Token引用
- **场景2 - 无障碍合规预检**：standardization_si 在PR增量检查中发现新增的仪表盘组件使用了低对比度配色方案 → Inclusive Visuals Specialist 依据WCAG 2.1 AA标准执行完整审查，发现3个对比度不达标区域和2个缺少ARIA标签的交互元素 → 输出含具体修复代码片段的审查报告
- **场景3 - 多产品线品牌统一**：standardization_si 跨多个代码仓库执行统一命名规范检查时发现产品间品牌术语不一致 → Brand Guardian 提供统一的品牌术语表（Glossary）作为标准化的新增规则源 → standardization_si 将术语表转化为可自动检测的正则规则集

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块
- Harness CI 标准化质量门禁（Standardization Quality Gate）
- Harness CD 策略即代码（Policy as Code）集成
- Harness SSEC 合规策略引擎（Compliance Policy Engine）

### 实践指南
- **CI标准化Gate**：在Harness CI Pipeline中将SHS（Standardization Health Score）作为质量门禁条件，A级/B级允许通过，C级触发警告并附加修复建议，D级及以下阻断Pipeline并提供auto-fix选项
- **策略即代码联动**：将standardization_si的命名规范规则和.gitignore检查规则导出为OPA（Open Policy Agent）Rego策略，接入Harness的策略即代码框架，在CD部署前自动执行合规性校验
- **合规审计追踪**：利用Harness SSEC的合规模块记录每次标准化检查的结果和纠正操作，满足审计需求；将Brand Guardian的品牌审核结果和Inclusive Visuals Specialist的无障碍审查结果一并归入合规证据链

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改规范文件、lint配置、.gitignore、编码标准时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/.eslintrc.json",
      agent_id="标准化司",
      lock_type=LockType.EXCLUSIVE,
      priority=8,
      timeout=120.0
  )
  ```
- **读锁**：读取规范文件、编码标准、合规策略时申请读锁（高频查询场景）
- **释放锁**：规范更新和配置变更完成后立即释放锁，避免阻塞其他司的标准查询

#### 终端会话池使用
- 从MARC终端会话池获取会话执行lint命令、格式化工具、合规检查脚本
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（全量代码扫描可能耗时较长）

#### 并发安全注意事项
- 规范配置文件是多司共享的核心资产，写入时必须独占锁保护
- lint规则变更需原子性操作，避免出现"半配置"状态导致检查结果不一致
- 死锁预防：按固定顺序申请锁（先锁规范文件→再锁lint配置→最后锁.gitignore）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | 规范解读提示词、违规修复建议提示词、命名推荐提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许标准化操作（规范制定/lint/格式化），禁止修改业务逻辑代码 | 全自动 |
| **规则校验层** | 输出格式：JSON lint报告、Markdown SHS评分报告、YAML规范定义 | 全自动 |
| **兜底恢复层** | 规范变更导致大量失败时自动回滚配置并通知团队 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于规范制定、lint配置、代码审查）
   - 示例：直接编辑.eslintrc.json/.prettierrc、手动调整命名规范、逐项审核代码合规性
   - 优势：精确控制规范粒度、可逐步验证效果、可随时回滚配置变更

2. 🥈 **规划脚本操作**（适用于批量代码格式化、周期性合规扫描）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查规范执行配额和扫描时间窗口
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的规范实践
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限紧急规范修复、批量auto-fix等极少数场景）
   - ⚠️ 必须预演影响范围（规范变更影响全局代码库）
   - ⚠️ 批量auto-fix需抽样检查修复正确性
   - 推荐使用PS7适配器转换eslint/prettier/black等lint工具命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- Lint操作：eslint/prettier/black/ruff等命令在PS7中原生可用
- 格式化工具：prettier --write / black . / ruff format 等命令直接执行
- Git钩子：pre-commit/pre-push钩子通过git命令管理
- 编码：确保所有输出 UTF-8 无 BOM（lint报告和审计记录）

### 与其他司的协作接口

- 上游依赖：文档规范化司（获取文档规范要求）、模板管理司（接收编码规范嵌入模板）
- 下游输出：刑部重构司（提供规范基线用于重构验收）、兵部测试司（推送编码规范用于测试用例编写）
- 数据交换格式：JSON / YAML / Markdown（统一UTF-8无BOM）
