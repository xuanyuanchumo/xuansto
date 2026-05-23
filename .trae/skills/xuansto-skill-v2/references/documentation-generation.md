# 文档站点生成参考文档

> 版本: 3.2.0 | 更新日期: 2026-05-06 | 编码: UTF-8 without BOM | 行尾: LF

---

## 概述

文档站点生成是项目知识交付的关键环节。本文档涵盖Docusaurus和MkDocs两大文档框架、API文档自动生成、Changelog自动化以及与xuansto-skill的集成模式。

---

## Docusaurus

### 概述

Docusaurus是Meta开源的静态文档站点生成器，基于React，适合技术文档和开源项目文档。

### 项目配置

```yaml
docusaurus:
  version: "3.x"
  features:
    - MDX支持（Markdown + React组件）
    - 版本化文档
    - i18n国际化
    - 插件系统
    - 搜索集成（Algolia）
  config:
    title: "Project Docs"
    url: "https://docs.example.com"
    baseUrl: "/"
    presets:
      - name: "classic"
        options:
          docs:
            path: "docs"
            sidebarPath: "sidebars.js"
            editUrl: "https://github.com/org/repo/edit/main/"
          blog:
            path: "blog"
          theme:
            customCss: "src/css/custom.css"
```

### 版本化文档

```bash
# 创建新版本
npm run docusaurus docs:version 2.0

# 版本目录结构
docs/           → 当前版本（next）
versioned_docs/
  version-1.0/  → v1.0文档
  version-2.0/  → v2.0文档
versioned_sidebars/
  version-1.0-sidebars.json
  version-2.0-sidebars.json
```

### MDX增强

```mdx
# API Reference

import { APITable } from "@site/src/components/APITable"

<APITable
  endpoints={[
    { method: "GET", path: "/api/users", description: "获取用户列表" },
    { method: "POST", path: "/api/users", description: "创建用户" },
  ]}
/>
```

---

## MkDocs

### 概述

MkDocs是基于Python的静态文档站点生成器，配置简单，适合技术文档和内部文档。

### 项目配置

```yaml
# mkdocs.yml
mkdocs:
  version: "1.6+"
  features:
    - YAML配置驱动
    - Material主题
    - 插件生态
    - 实时预览
  config:
    site_name: "Project Docs"
    theme:
      name: "material"
      features:
        - navigation.tabs
        - navigation.sections
        - navigation.top
        - search.suggest
        - search.highlight
      palette:
        primary: "blue"
    plugins:
      - search
      - git-revision-date-localized
      - minify
    markdown_extensions:
      - admonition
      - codehilite
      - footnotes
      - toc:
          permalink: true
      - pymdownx.superfences
      - pymdownx.tabbed
```

### 多语言支持

```yaml
mkdocs_i18n:
  plugin: "mkdocs-static-i18n"
  languages:
    - locale: "zh"
      name: "中文"
      default: true
    - locale: "en"
      name: "English"
  nav_translations:
    en:
      Home: "Home"
      API: "API Reference"
    zh:
      Home: "首页"
      API: "API参考"
```

---

## API文档自动生成

### OpenAPI/Swagger

```yaml
api_doc_generation:
  openapi:
    version: "3.1.0"
    tools:
      - name: "swagger-ui"
        purpose: "交互式API文档"
      - name: "redoc"
        purpose: "精美API文档"
      - name: "scalar"
        purpose: "现代API文档"
    generation:
      typescript:
        tool: "tsoa"
        approach: "装饰器注解 → OpenAPI JSON"
      python:
        tool: "fastapi"
        approach: "类型注解 → OpenAPI JSON"
      go:
        tool: "swaggo/swag"
        approach: "注释注解 → OpenAPI JSON"
```

### TypeDoc（TypeScript项目）

```yaml
typedoc:
  version: "0.26+"
  config:
    entryPoints: ["src/index.ts"]
    out: "docs/api"
    plugin:
      - "typedoc-plugin-markdown"
      - "typedoc-plugin-missing-exports"
    readme: "none"
    excludePrivate: true
    excludeProtected: false
```

### Docusaurus API文档集成

```yaml
docusaurus_api:
  plugin: "docusaurus-plugin-typedoc"
  workflow:
    - TypeDoc从TypeScript源码提取API
    - 生成Markdown文档
    - 集成到Docusaurus docs目录
    - 自动更新sidebar
```

---

## Changelog自动化

### 工具链

| 工具 | 格式 | 集成 | 适用场景 |
|------|------|------|---------|
| conventional-changelog | Conventional Commits | npm/git | Node.js项目 |
| git-cliff | TOML配置 | Cargo/git | Rust/多语言项目 |
| standard-version | SemVer | npm/git | 自动版本+Changelog |
| release-please | Conventional Commits | GitHub | 自动PR发布 |

### Conventional Commits规范

```
feat: 新增用户认证功能
fix: 修复登录页面样式问题
docs: 更新API文档
style: 调整按钮间距
refactor: 重构数据获取逻辑
perf: 优化列表渲染性能
test: 添加用户模块单元测试
chore: 升级依赖版本
```

### 自动化流程

```yaml
changelog_automation:
  tool: "conventional-changelog"
  workflow:
    - 开发者使用Conventional Commits格式提交
    - CI自动验证提交消息格式
    - 发布时自动生成Changelog
    - Changelog集成到文档站点
  config:
    preset: "angular"
    releaseCount: 0
    types:
      - type: "feat"
        section: "Features"
      - type: "fix"
        section: "Bug Fixes"
      - type: "perf"
        section: "Performance"
```

---

## 与xuansto-skill的集成

| xuansto模块 | 文档工具 | 集成方式 |
|------------|---------|---------|
| Documentation Writer | Docusaurus/MkDocs | Agent输出文档到docs目录 |
| API Developer | TypeDoc/OpenAPI | API代码自动生成文档 |
| Release Manager | Changelog自动化 | 发布时自动生成变更日志 |
| Quality Gates | 文档完整性检查 | 门禁验证文档覆盖率 |

---

> 本文档由 Multi-Agent SDD/TDD Orchestrator 维护 | 最后更新: 2026-05-06
