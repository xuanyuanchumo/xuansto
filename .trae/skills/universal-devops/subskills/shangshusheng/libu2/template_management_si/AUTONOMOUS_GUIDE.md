# 模板管理司 自主操作指南 (Autonomous Operation Guide)

## 概述

模板管理司（template_management_si）是尚书省礼部负责项目脚手架模板全生命周期管理的核心单元。本司维护覆盖15种主流技术栈的脚手架模板库，提供基于Jinja2语法的 `{{variable}}` 模板引擎能力，支持根据项目特性自动选择和定制模板，并建立完整的模板版本管理与反馈驱动改进机制。

**核心目标：**
- 维护15种技术栈的高质量、可即刻使用的脚手架模板
- 实现项目特性驱动的智能模板选择与参数化定制
- 提供强大的变量模板引擎，支持条件渲染、循环渲染和嵌套继承
- 建立模板版本管理体系，支持迭代追踪与安全回滚
- 构建反馈闭环，将使用中发现的问题自动转化为模板改进

## 核心原则

1. **约定优于配置（Convention over Configuration）**：每个模板自带合理默认值，开箱即用；仅在必要时暴露可配置项
2. **渐进式披露（Progressive Disclosure）**：基础模板保持简洁，高级特性通过可选模块按需引入
3. **模板即代码（Template as Code）**：模板本身受版本控制、可审查、可测试、遵循DRY原则
4. **向后兼容（Backward Compatibility）**：模板升级不破坏已有项目的使用方式，通过版本号语义管理兼容性
5. **实测优先（Tested First）**：每个模板必须能成功生成可运行的"Hello World"项目并通过冒烟测试
6. **社区感知（Community Aware）**：跟踪各技术栈生态的最新最佳实践，定期同步到模板中

## 自主操作流程

### 阶段一：感知（Perceive）

**1.1 技术栈检测**

当接收到项目初始化或模板应用请求时，自动执行技术栈识别：

```
检测信号源（按优先级排序）：
├── 显式声明：用户在请求中指定 tech_stack 参数
├── 配置文件推断：
│   ├── package.json → Node.js生态（React/Vue/Angular/Express等）
│   ├── pyproject.toml / setup.py / requirements.txt → Python生态
│   ├── go.mod / main.go → Go语言
│   ├── Cargo.toml → Rust语言
│   ├── pom.xml / build.gradle → Java/Spring生态
│   └── *.csproj → .NET/C#生态
├── 目录结构推断：
│   ├── src/ + public/ → 前端项目可能性高
│   ├── app/ + migrations/ → Django/Flask等Web框架
│   ├── cmd/ + internal/ → Go标准项目布局
│   └── lib/ + spec/ → Ruby/Rails可能性
└── 文件内容采样：
    ├── import/require 语句分析
    ├── 装饰器/注解模式识别
    └── 框架特征字符串匹配（如 @SpringBootApplication, React.createElement）
```

**1.2 15种技术栈模板清单**

| 编号 | 技术栈 | 模板标识符 | 核心文件数 | 默认特性 |
|------|--------|------------|------------|----------|
| T01 | Python (Pure) | `python-base` | ~12 | venv, pytest, ruff, pyproject.toml |
| T02 | Python FastAPI | `python-fastapi` | ~18 | FastAPI, SQLAlchemy, Alembic, Pydantic v2 |
| T03 | Python Django | `python-django` | ~25 | Django 5.x, DRF, django-environ, whitenoise |
| T04 | Node.js (Express) | `node-express` | ~15 | Express 4.x, TypeScript, eslint, jest |
| T05 | React (Vite) | `react-vite` | ~20 | React 18+, Vite 5, TypeScript, TailwindCSS, Vitest |
| T06 | Vue (Vite) | `vue-vite` | ~18 | Vue 3.4+, Vite 5, Pinia, Vue Router, TypeScript |
| T07 | Next.js | `nextjs-app` | ~22 | Next.js 14 App Router, TypeScript, Prisma |
| T08 | Go (Standard) | `go-standard` | ~14 | Go 1.22+, standard layout, gin/echo可选 |
| T09 | Go (Gin Web) | `go-gin-web` | ~18 | Gin framework, GORM, Zap logger, Swagger |
| T10 | Rust (CLI) | `rust-cli` | ~12 | Rust 2021 edition, clap, anyhow, tokio |
| T11 | Rust (Axum Web) | `rust-axum-web` | ~16 | Axum, SQLx, Tower middleware, tracing |
| T12 | Java (Spring Boot) | `java-springboot` | ~24 | Spring Boot 3.x, Maven, Lombok, MapStruct |
| T13 | Java (Spring Boot + JPA) | `java-springboot-jpa` | ~28 | Spring Data JPA, Flyway, PostgreSQL |
| T14 | TypeScript (Library) | `ts-library` | ~16 | tsup, vitest, tsconfig strict, API Extractor |
| T15 | Monorepo (pnpm) | `monorepo-pnpm` | ~30+ | pnpm workspaces, turborepo, changesets |

**1.3 模板健康度巡检**

每日定时执行模板健康度扫描：

```yaml
巡检维度:
  - name: 冒烟测试通过率
    method: 对每个模板执行 generate → install → build → test 全流程
    threshold: 100%（任一失败立即告警）

  - name: 依赖版本时效性
    method: 检查模板锁文件中的依赖版本 vs 最新稳定版
    action: 落后 >2个minor版本时标记为需更新

  - name: 模板结构完整性
    method: 验证必需文件存在、目录结构符合规范
    threshold: 必需文件缺失 = 严重告警

  - name: 变量定义完整性
    method: 扫描模板中所有 {{variable}} 引用，确认均有默认值或必填声明
    threshold: 未定义变量 = 阻断性错误

  - name: 安全基线合规性
    method: 检查模板是否包含安全配置（CSP头、依赖审计、secret扫描）
    threshold: 缺失安全配置 = 警告级别
```

### 阶段二：决策（Decide）

**2.1 模板选择决策树**

```
输入：项目初始化请求 + （可选）tech_stack hint
│
├── 用户显式指定了 tech_stack？
│   ├── 是 → 直接选用对应模板，进入【定制阶段】
│   └── 否 → 进入【自动检测流程】
│       │
│       ├── 检测到单一明确技术栈？
│       │   ├── 是 → 匹配度 ≥ 0.8？→ 选用该模板
│       │   └── 否 → 返回候选列表供用户确认
│       │
│       ├── 检测到多技术栈混合？
│       │   ├── 前后端分离模式？→ 推荐组合模板（如 react-vite + python-fastapi）
│       │   └── monorepo模式？→ 推荐 monorepo-pnpm 并配置子workspace
│       │
│           └── 无法确定？→ 展示交互式选择面板（按使用频率排序）
```

**2.2 模板定制策略矩阵**

| 定制维度 | 触发条件 | 自动动作 | 需人工确认 |
|----------|----------|----------|------------|
| 包管理器选择 | 检测到系统已安装的工具链 | 优先使用已安装的 | 多工具可用时询问 |
| 测试框架选择 | 项目规模 < 小型 | 使用模板默认框架 | 中大型项目建议讨论 |
| Lint/Format工具 | 检测到已有全局配置 | 复用现有偏好 | — |
| CI/CD平台 | 检测到 .github/ 或 .gitlab-ci.yml | 匹配已有平台 | 无线索时推荐GitHub Actions |
| 数据库选型 | 项目类型暗示 | Web项目默认PostgreSQL | 有明确需求时切换 |
| 容器化支持 | 检测到Dockerfile/docker-compose | 保持一致 | 未检测到时询问 |
| i18n需求 | 检测到 locale 文件夹或i18n配置 | 启用i18n模块 | 默认关闭 |

**2.3 模板更新决策规则**

```
触发条件满足以下任一即可启动模板评估：

RULE-DEPENDENCY-OUTDATED:
  IF 模板核心依赖落后 >= 2个minor版本
  OR 存在已知CVE的安全漏洞
  THEN 标记为"待更新"，优先级=HIGH

RULE-ECOSYSTEM-SHIFT:
  IF 技术栈发布新的major版本且社区采用率 > 30%
  THEN 创建新版本模板分支，保留旧版作为 legacy

RULE-PATTERN-IMPROVEMENT:
  IF 社区公认的最佳实践发生重大变化
  （如 React 从 Class Components → Hooks 已成为绝对主流）
  THEN 将新实践纳入默认模板，旧做法移至 optional/

RULE-FEEDBACK-ACCUMULATED:
  IF 同一问题被反馈 >= 3次
  OR 同一改进建议被提出 >= 2次
  THEN 纳入下一轮模板迭代计划
```

### 阶段三：执行（Execute）

**3.1 Jinja2模板引擎核心语法规范**

本司所有模板统一采用Jinja2语法体系，以下是完整的能力边界说明：

**变量插值（Variable Interpolation）：**

```jinja2
{# 基础变量 #}
project_name = "{{ project_name }}"
version = "{{ version | default('0.1.0') }}"

{# 带过滤器的变量 #}
class_name = "{{ project_name | capitalize }}Service"
kebab_name = "{{ project_name | replace('_', '-') | lower }}"
```

**条件渲染（Conditional Rendering）：**

```jinja2
{% if use_typescript %}
<script lang="ts">
  const app: {{ project_name | capitalize }}App = createApp();
</script>
{% else %}
<script>
  const app = createApp();
</script>
{% endif %}

{% if database == 'postgresql' %}
  DATABASE_URL="postgresql://{{ db_user }}:{{ db_pass }}@localhost:5432/{{ db_name }}"
{% elif database == 'mysql' %}
  DATABASE_URL="mysql://{{ db_user }}:{{ db_pass }}@localhost:3306/{{ db_name }}"
{% else %}
  DATABASE_URL="sqlite:///./{{ db_name | default('app') }}.db"
{% endif %}
```

**循环渲染（Loop Rendering）：**

```jinja2
{# 生成多个环境配置文件 #}
{% for env in environments %}
# {{ env.name | upper }} Environment Configuration
{{ env.name | upper }}_HOST={{ env.host }}
{{ env.name | upper }}_PORT={{ env.port }}
{{ env.name | upper }}_DEBUG={{ 'true' if env.debug else 'false' }}

{% endfor %}

{# 生成API路由注册表 #}
{% for route in api_routes %}
app.{{ route.method | lower }}("{{ route.path }}", {{ route.handler }})
{%- endfor %}
```

**模板继承（Template Inheritance）：**

```jinja2
{# base.html.j2 — 基础模板 #}
<!DOCTYPE html>
<html lang="{{ locale | default('zh-CN') }}">
<head>
    <meta charset="UTF-8">
    <title>{% block title %}{{ project_name }}{% endblock %}</title>
    {% block head_extra %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
    {% block scripts %}{% endblock %}
</body>
</html>

{# index.html.j2 — 继承并扩展 #}
{% extends "base.html.j2" %}

{% block title %}{{ project_name }} - Home{% endblock %}

{% block content %}
<div id="app"></div>
{% endblock %}

{% block scripts %}
<script src="/static/bundle.js"></script>
{% endblock %}
```

**宏定义与复用（Macros）：**

```jinja2
{# macros/utils.j2 #}
{% macro render_field(name, type, required=false, default='') %}
  {% if type == 'str' %}
    {{ name }}: str{{ " = '" ~ default ~ "'" if default else "" }}
  {% elif type == 'int' %}
    {{ name }}: int{{ " = " ~ default if default else "" }}
  {% elif type == 'bool' %}
    {{ name }}: bool{{ " = " ~ default | lower if default else "" }}
  {% elif type == 'list' %}
    {{ name }}: list{{ " = " ~ default if default else " = []" }}
  {% endif %}
  {%- if required %}  # required{%- endif %}
{% endmacro %}

{# 使用宏生成数据模型字段 #}
class {{ model_name }}(Base):
    __tablename__ = "{{ model_name | lower }}s"
    
    {% for field in fields %}
    {{ render_field(field.name, field.type, field.required, field.default) }}
    {% endfor %}
```

**内置过滤器全集：**

| 过滤器 | 功能 | 示例 |
|--------|------|------|
| `default(val)` | 设置默认值 | `{{ port \| default(3000) }}` |
| `capitalize` | 首字母大写 | `{{ name \| capitalize }}` |
| `lower / upper` | 大小写转换 | `{{ env \| upper }}` |
| `replace(old, new)` | 字符串替换 | `{{ name \| replace(' ', '_') }}` |
| `trim` | 去首尾空白 | `{{ desc \| trim }}` |
| `wordwrap(width)` | 按宽度换行 | `{{ long_text \| wordwrap(80) }}` |
| `tojson` | 序列化为JSON | `{{ config \| tojson }}` |
| `length / count` | 获取长度 | `{{ items \| length }}` |
| `join(sep)` | 列表拼接为字符串 | `{{ tags \| join(', ') }}` |
| `selectattr / rejectattr` | 按属性过滤 | `{{ items \| selectattr('enabled') \| list }}` |
| `sort` | 排序 | `{{ deps \| sort(attribute='name') }}` |
| `unique` | 去重 | `{{ imports \| unique \| list }}` |
| `batch(n)` | 分批 | `{{ items \| batch(3) \| list }}` |

**3.2 项目脚手架生成流水线**

```
Step 1: 模板加载与解析
  ├─ 读取选定模板的全部文件（含嵌套子模板）
  ├─ 解析 variables.json（变量定义与默认值）
  └─ 构建模板依赖图（处理 extends/include 关系）

Step 2: 变量收集与校验
  ├─ 收集用户提供的变量值（交互式 / 配置文件 / CLI参数）
  ├─ 应用默认值填充未提供变量
  ├─ 执行自定义验证器（如：project_name 符合命名规范）
  └─ 输出最终变量上下文（context dict）

Step 3: 渲染执行
  ├─ 按依赖拓扑序逐文件渲染
  ├─ 处理条件分支（根据变量值决定包含/排除哪些文件）
  ├─ 处理循环展开（动态生成重复结构）
  └─ 生成目标文件树

Step 4: 后处理
  ├─ 格式化生成的代码（prettier/black/gofmt/rustfmt）
  ├─ 修正行尾符号（LF vs CRLF，根据目标平台）
  ├─ 赋予执行权限（shell脚本、entrypoint）
  └─ 生成 .gitignore 和初始 commit（可选）

Step 5: 冒烟测试
  ├─ 在临时目录中执行 generated_project 的构建命令
  ├─ 运行测试套件（如有）
  └─ 验证项目能正常启动（端口探测或进程检查）
```

**3.3 模板版本管理**

每个模板维护独立的版本线，遵循语义化版本规范：

```
版本号格式：{模板ID}@{major}.{minor}.{patch}

示例：
  python-fastapi@3.2.1
  react-vite@2.0.0
  go-gin-web@1.5.3

版本递增规则：
  MAJOR（主版本）：
    - 模板整体架构重构（如从JavaScript迁移到TypeScript-only）
    - 不再支持的破坏性变更（如删除某个optional模块的默认包含）
    - 依赖的核心框架major版本升级
  
  MINOR（次版本）：
    - 新增 optional 模块或功能开关
    - 新增支持的选项（如新增数据库选型）
    - 依赖的次要版本升级（带来新特性但不破坏现有用法）
  
  PATCH（修订版）：
    - 修复模板中的bug（错误的默认值、缺失的文件等）
    - 依赖的安全补丁版本升级
    - 文档/注释的改进
```

**回滚机制：**

```yaml
回滚操作规程:
  前置条件:
    - 目标版本必须在版本历史记录中存在
    - 回滚操作需要记录理由（用于后续分析）

  执行步骤:
    1. 将当前模板状态快照归档到 archived/ 目录
    2. 从版本历史中检出目标版本的完整文件集
    3. 更新 VERSION 文件中的版本号
    4. 执行冒烟测试确保回滚后模板可用
    5. 写入回滚操作日志

  限制:
    - 不允许跨 major 版本回滚（防止结构性不兼容）
    - 连续回滚不超过2次（强制人工介入评估根本原因）
    - 回滚后的模板标记为"frozen"状态，直到人工解除
```

**3.4 反馈驱动的模板改进**

```python
# 反馈收集与处理管道伪代码
def process_feedback(feedback_item):
    """
    feedback_item 结构:
    {
        "source": "user_report" | "smoke_test_failure" | "dependency_audit",
        "template_id": "react-vite",
        "severity": "critical" | "major" | "minor" | "suggestion",
        "category": "bug" | "improvement" | "feature_request" | "security",
        "description": "...",
        "reproduction_steps": [...],  // 可选
        "timestamp": "ISO-8601",
        "reporter": "user_id or system"
    }
    """

    # Step 1: 去重与聚合
    similar = find_similar_feedback(feedback_item)
    feedback_item.cluster_id = similar[0].cluster_id if similar else new_cluster()

    # Step 2: 严重性评估
    if feedback_item.severity == "critical":
        priority = "P0-IMMEDIATE"      # 立即修复，可能阻断模板使用
        auto_action = "pause_template"  # 暂停受影响模板的对外服务
    elif feedback_item.severity == "major":
        priority = "P1-HIGH"            # 本轮迭代必须修复
        auto_action = "schedule_fix"
    elif feedback_item.severity == "minor":
        priority = "P2-MEDIUM"          # 纳入下个patch版本
        auto_action = "queue_for_review"
    else:  # suggestion
        priority = "P3-LOW"             # 记录并等待更多同类反馈
        auto_action = "log_only"

    # Step 3: 同类反馈累积阈值判定
    cluster_count = count_cluster_members(feedback_item.cluster_id)
    if cluster_count >= 3 and priority in ("P2-MEDIUM", "P3-LOW"):
        priority = upgrade_priority(priority)  # 升级优先级

    # Step 4: 执行对应动作
    execute_auto_action(auto_action, feedback_item)

    # Step 5: 通知相关方
    if priority in ("P0-IMMEDIATE", "P1-HIGH"):
        send_alert_to_template_owner(feedback_item)
```

### 阶段四：Verify（验证）

**4.1 模板冒烟测试套件**

每个模板必须通过的冒烟测试清单：

```yaml
通用测试（所有模板均需通过）:
  - id: file_structure_complete
    description: 所有声明的必需文件均已生成
    check: ls expected_files | diff --expected

  - id: variable_substitution_correct
    description: 所有 {{variable}} 均被正确替换，无残留模板语法
    check: grep -r '{{' output/ && grep -r '{%' output/ → must be empty

  - id: no_hardcoded_secrets
    description: 生成的项目中不含硬编码密钥或token
    check: secret_scanner scan output/

  - id: git_initialization
    description: .gitignore存在且有效，git init可正常执行
    check: cd output/ && git status → clean working tree

  - id: dependency_install
    description: 依赖安装命令可成功完成
    check: npm install / pip install / go mod download / cargo fetch

  - id: build_succeeds
    description: 项目构建命令可成功完成
    check: npm run build / python -m build / go build ./... / cargo build

  - id: test_passes
    description: 内置测试套件全部通过
    check: npm test / pytest / go test ./... / cargo test

语言特定测试:
  Python:
    - ruff lint 通过
    - mypy type check 通过（如启用type hints）
    - pytest 覆盖率 > 0%

  JavaScript/TypeScript:
    - eslint 通过
    - tsc --noEmit 通过（TypeScript模板）
    - vitest/jest 通过

  Go:
    - go vet 通过
    - gofmt -d 无差异输出
    - go test ./... 通过

  Rust:
    - cargo clippy warnings = 0
    - cargo fmt --check 通过
    - cargo test 通过

  Java:
    - mvn compile 成功
    - mvn test 通过
    - SpotBugs/Checkstyle 无新增违规
```

**4.2 模板质量评分卡**

| 维度 | 权重 | 评估方法 | 满分标准 |
|------|------|----------|----------|
| 功能完整性 | 25% | 冒烟测试通过率 | 100%通过 |
| 代码质量 | 20% | Lint/Format/TypeCheck | 0 warning, 0 error |
| 安全基线 | 15% | Secret扫描 + 依赖审计 | 0 secrets, 0 known CVEs |
| 文档完备性 | 15% | README完整性 + 内联注释 | 含快速开始+配置说明+FAQ |
| 最佳实践对齐 | 15% | 与官方推荐的对齐度 | ≥90%对齐 |
| 可维护性 | 10% | 模板代码清晰度 + 变量设计合理性 | 易读易扩展 |

**评级标准：**
- A级（90-100）：生产就绪，推荐广泛使用
- B级（80-89）：可用，有小改进空间
- C级（70-79）：基本可用，建议审阅后使用
- D级（60-69）：有已知问题，谨慎使用
- F级（<60）：不可用，暂停服务直至修复

### 阶段五：Record（记录）

**5.1 模板操作日志**

```json
{
  "operationId": "tmpl-op-20260406-003",
  "timestamp": "2026-04-06T14:20:00Z",
  "operator": "template_management_si[autonomous]",
  "operationType": "generate_project",
  "templateId": "python-fastapi",
  "templateVersion": "3.2.1",
  "variables": {
    "project_name": "my_api",
    "use_docker": true,
    "database": "postgresql",
    "test_framework": "pytest"
  },
  "outputStats": {
    "filesGenerated": 24,
    "totalLines": 1850,
    "renderTimeMs": 320,
    "smokeTestResult": "PASS"
  },
  "feedbackInvited": true
}
```

**5.2 版本变更日志**

每次模板版本升级时自动生成：

```markdown
## [python-fastapi@3.2.1] - 2026-04-05

### Fixed
- 修复 Dockerfile 中 PYTHONPATH 环境变量设置错误 (#89)
- 修复 alembic.ini 中 sqlalchemy.url 默认值与 .env 不一致 (#91)

### Changed
- 升级 FastAPI 从 0.109.0 到 0.110.0 (#88)
- 升级 Pydantic 从 2.6.0 到 2.7.0 (#88)

### Security
- 更新 uvicorn 至 0.27.1，修复 CVE-2024-XXXXX (#90)
```

## 典型自主场景

### 场景1：智能项目初始化 — 混合技术栈Monorepo

**背景**：团队要创建一个前后端分离的全栈项目，前端使用React+TypeScript，后端使用Python FastAPI，希望以monorepo方式管理。

**自主执行流程：**

1. **感知**：接收项目初始化请求，未指定具体技术栈。执行目录扫描发现无任何配置文件。
2. **决策**：
   - 无法从环境推断出单一技术栈
   - 分析团队历史项目偏好（如有的话）
   - 向用户展示引导式问答："请选择项目类型" → 用户选择 "Full-stack Monorepo"
   - 选择 `monorepo-pnpm` 作为根模板，`react-vite` 作为前端子模板，`python-fastapi` 作为后端子模板
3. **执行**：
   - 渲染根 workspace 配置（pnpm-workspace.yaml, turbo.json）
   - 渲染前端 apps/web/ 目录（react-vite模板，启用TypeScript+TailwindCSS+Vitest）
   - 渲染后端 apps/api/ 目录（python-fastapi模板，启用Docker+PostgreSQL+Alembic）
   - 渲染共享 packages/shared/ 目录（TS类型定义 + Python data models）
   - 生成根目录 package.json（scripts含 dev/build/test/lint）
   - 生成 .github/workflows/CI配置（同时覆盖前端和后端的build+test）
4. **验证**：
   - pnpm install 成功 ✓
   - 前端 npm run build 成功 ✓
   - 后端 pip install + pytest 成功 ✓
   - 整体 turbo run build 成功 ✓
   - 质量评分：93分（A级）
5. **记录**：记录本次生成操作，邀请用户填写体验反馈

### 场景2：依赖安全漏洞应急响应

**背景**：安全审计工具报告 `react-vite` 模板中依赖的 `lodash@4.17.21` 存在原型污染漏洞（CVE-2021-23337），且模板实际并未直接使用lodash（是某transitive dependency引入）。

**自主执行流程：**

1. **感知**：收到安全告警，定位影响范围：react-vite模板及其衍生项目
2. **决策**：
   - CVE严重性 = high → P0-IMMEDIATE
   - lodash非直接依赖 → 可以安全移除transitive引入路径
   - 立即启动紧急修补流程
3. **执行**：
   - 分析依赖链：some-dev-tool → lodash
   - 移除不必要的devDependency（如果确认不需要）
   - 或使用 `overrides` 字段锁定lodash到安全版本
   - 创建 patch 版本 `react-vite@2.0.1-patch.1`
   - 对所有使用该模板的历史项目发送安全通告建议
4. **验证**：
   - `npm audit` 零漏洞 ✓
   - 冒烟测试全通过 ✓
   - 无功能回归 ✓
5. **记录**：写入安全事件日志，更新模板CHANGELOG的Security章节

### 场景3：基于用户反馈的模板持续进化

**背景**：连续收到3份独立反馈，指出 `go-gin-web` 模板中Swagger文档集成过于复杂，新手用户经常在配置上遇到困难。

**自主执行流程：**

1. **感知**：反馈聚类系统检测到同一cluster_id下累计3条同类反馈
2. **决策**：
   - 触发 RULE-FEEDBACK-ACCUMULATED（≥3条同类反馈）
   - 优先级从 P3-LOW 自动升级为 P1-HIGH
   - 制定改进方案：简化Swagger配置为opt-in模式，默认关闭
3. **执行**：
   - 将Swagger相关配置从主模板移至 `optional/swagger/` 子目录
   - 主模板中仅保留一行注释提示如何启用
   - 创建新的 optional 模块启用脚本
   - 更新README中的Swagger章节
   - 版本号递增 patch：`go-gin-web@1.5.3` → `go-gin-web@1.5.4`
4. **验证**：
   - 默认配置下不再有Swagger依赖（减少复杂度）✓
   - 启用Swagger后功能完整可用 ✓
   - 冒烟测试全通过 ✓
5. **记录**：向3位反馈者发送"你的建议已被采纳"通知，记录改进详情

## 决策框架

### 自主行动边界

| 动作类型 | 自主执行条件 | 需确认条件 | 禁止条件 |
|----------|-------------|-----------|----------|
| 模板渲染/项目生成 | ✅ 常规操作 | — | — |
| 依赖版本补丁升级（patch） | ✅ 安全修复或bug fix | — | — |
| 模板bug修复 | ✅ 影响范围明确且小 | 涉及架构调整 | — |
| 新增optional模块 | ✅ 非破坏性添加 | 替换现有默认行为 | — |
| 模板major版本升级 | — | ✅ 必须经过充分测试和评审 | — |
| 删除模板或模板功能 | — | ✅ 必须确认 | — |
| 修改模板安全策略 | — | ✅ 安全团队审核 | — |
| 修改模板许可协议 | — | — | ✅ 严格禁止 |

### 降级策略

```
Level 0（完全自主）：常规渲染、patch升级、格式修复
    ↓ 遇到不确定
Level 1（保守方案）：生成带标注的输出 <!-- TEMPLATE-AUTO-GENERATED -->
    ↓ 涉及破坏性变更
Level 2（并行方案）：同时生成新旧两个版本供对比选择
    ↓ 影响面广或涉及安全
Level 3（冻结+上报）：暂停操作，详细报告给模板负责人
```

## 安全与治理

### 生成产物安全

- 生成的项目中不得包含硬编码密钥、密码、token
- 模板中敏感占位符使用明显标记（如 `YOUR_SECRET_HERE`），并在生成后扫描确认已替换
- Docker镜像基础镜像使用固定digest而非浮动tag（防止供应链攻击）
- 依赖来源限制在官方registry或已批准的私有registry

### 模板供应链安全

- 所有模板的依赖声明文件（package.json/go.mod/Cargo.toml等）纳入lockfile管理
- 定期执行依赖审计（npm audit / pip-audit / cargo audit / go vuln）
- 发现CVE时根据CVSS评分决定响应速度：
  - CVSS ≥ 9.0：24小时内修复
  - CVSS ≥ 7.0：72小时内修复
  - CVSS ≥ 4.0：下个版本周期内修复
- 模板变更需经code review，禁止自行merge到main分支

### 访问控制

- 模板的写操作（创建/修改/删除）需要授权身份
- 模板的读操作（渲染/预览）按角色分级
- 操作日志完整留存，支持审计追溯

## 协作关系

### 上游依赖

| 协作对象 | 交互内容 | 交互频率 | 接口协议 |
|----------|----------|----------|----------|
| 包注册表（npm/PyPI/crates.io等） | 依赖版本信息、安全公告 | 定时轮询 + webhook | Registry API / OSV API |
| 安全审计工具 | CVE报告、依赖漏洞扫描结果 | 事件驱动 | JSON / SARIF |
| 用户反馈渠道 | 问题报告、改进建议 | 实时 | Issue / 表单 / 内嵌反馈组件 |

### 下游消费者

| 协作对象 | 提供内容 | 交付物 | 更新策略 |
|----------|----------|--------|----------|
| 开发者/团队 | 脚手架项目 | 完整项目目录树 | 按请求实时生成 |
| documentation_si | 模板使用文档 | 结构化文档片段 | 模板变更时同步 |
| knowledge_base_si | 模板设计模式知识 | 模式提炼卡片 | 定期沉淀 |
| standardization_si | 模板代码风格规范 | Lint规则集 | 模板更新时推送 |

### 同级协作

| 协作对象 | 协作场景 | 协议 |
|----------|----------|------|
| documentation_si | 模板生成项目的文档自动补充 | 事件驱动 |
| knowledge_base_si | 模板最佳实践的交叉验证 | 定期同步 |
| standardization_si | 模板产物的标准化检查 | 流水线集成 |

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Document Generator | 文档工程部 | 流水线集成 | 自动化文档模板生成与多格式输出 |

### Agent 协作工作流

1. **模板需求解析**：template_management_si 接收项目初始化请求，识别技术栈和文档输出需求
2. **模板渲染执行**：本司基于Jinja2引擎完成代码脚手架的渲染生成
3. **Agent 委派**：
   - 代码模板生成完成后 → 调用 **Document Generator** 基于项目特征自动生成配套文档模板（README、API文档骨架、CHANGELOG模板、贡献指南等）
   - Document Generator 根据技术栈选择对应的文档模板风格（如Python项目采用Sphinx结构、JS项目采用JSDoc规范）
4. **产物整合**：将Agent生成的文档模板与代码脚手架合并为完整的项目初始包
5. **一致性校验**：验证生成的文档模板与代码脚手架在命名、结构和风格上的一致性
6. **交付与反馈**：向用户交付完整项目包，收集文档模板的使用反馈以驱动持续优化

### 典型协作场景

- **场景1 - 全栈项目初始化套件**：template_management_si 生成前后端代码脚手架 → Document Generator 同步生成前端README（含DevServer指令）、后端API文档骨架（含OpenAPI模板）、 monorepo根目录的CONTRIBUTING.md和项目总览文档
- **场景2 - 企业合规项目模板**：template_management_si 渲染含安全基线的代码模板 → Document Generator 附加生成合规检查清单文档（DOCX格式）、安全策略说明文档、审计日志模板
- **场景3 - SDK项目发布模板**：template_management_si 生成库代码及构建配置 → Document Generator 生成完整的SDK使用文档模板、版本迁移指南模板、示例代码仓库README模板

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块
- Harness CI 模板冒烟测试流水线（Template Smoke Test Pipeline）
- Harness CD 模板注册表分发（Template Registry Distribution）
- Harness Platform 模板版本管理（Template Version Control）

### 实践指南
- **CI模板验证门禁**：在Harness CI中为每个模板建立专属的冒烟测试Pipeline，模板变更时自动触发 generate→install→build→test 全流程验证，结果反馈至template_management_si的健康度巡检系统
- **CD模板分发策略**：利用Harness CD的多环境部署能力，将稳定版模板推送至全局模板注册表，实验性模板仅限于沙箱环境使用
- **模板供应链安全**：结合Harness SSEC（Software Security Engineering Compliance）模块，对模板依赖执行自动化安全扫描，发现CVE时自动触发模板回滚或修补流程

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改模板文件、注册表配置、版本元数据时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/templates/project-template.md",
      agent_id="模板管理司",
      lock_type=LockType.EXCLUSIVE,
      priority=7,
      timeout=120.0
  )
  ```
- **读锁**：读取模板库、注册表目录、版本历史时申请读锁（高频查询场景）
- **释放锁**：模板变更和注册操作完成后立即释放锁，避免阻塞其他司的模板使用

#### 终端会话池使用
- 从MARC终端会话池获取会话执行模板验证脚本、注册命令、版本管理操作
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（模板冒烟测试可能涉及多步骤验证）

#### 并发安全注意事项
- 模板注册表是核心共享资产，写入时必须独占锁保护
- 模板版本升级需原子性操作，避免出现"半升级"状态导致不一致
- 死锁预防：按固定顺序申请锁（先锁模板文件→再锁注册表→最后锁版本元数据）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | 模板生成提示词、参数化设计提示词、最佳实践提取提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许模板管理操作（创建/注册/分发），禁止修改业务代码 | 全自动 |
| **规则校验层** | 输出格式：标准Markdown模板、YAML参数定义、JSON注册表条目 | 全自动 |
| **兜底恢复层** | 模板验证失败时自动回滚至上一稳定版本并通知使用者 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于模板设计、参数优化、质量审核）
   - 示例：直接编辑Markdown模板、手动调整变量占位符、编写模板使用说明
   - 优势：精确控制模板细节、可逐步验证可用性、可随时回滚模板变更

2. 🥈 **规划脚本操作**（适用于批量模板初始化、周期性健康巡检）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查模板存储配额和使用统计
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的模板演化
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限模板注册表重建、批量版本清理等极少数场景）
   - ⚠️ 必须预演影响范围（模板变更影响所有后续项目初始化）
   - ⚠️ 批量模板操作需逐条确认并留痕
   - 推荐使用PS7适配器转换模板管理工具命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- 文件操作：使用原生PowerShell Cmdlet处理Markdown/YAML/JSON模板文件
- 版本管理：git命令用于模板版本控制和变更追踪
- 注册操作：运行自定义脚本或CLI工具进行模板注册和分发
- 编码：确保所有输出 UTF-8 无 BOM（模板文件和注册记录）

### 与其他司的协作接口

- 上游依赖：文档规范化司（获取文档模板需求）、标准化司（接收编码规范用于模板内嵌）
- 下游输出：基础设施司（推送项目脚手架模板）、环境配置司（提供环境配置模板）
- 数据交换格式：Markdown / YAML / JSON（统一UTF-8无BOM）
