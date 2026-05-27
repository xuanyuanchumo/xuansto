---
name: /build
aliases:
  - b
category: system
phase: "8"
description: Web应用构建与打包
trigger: 需要构建或打包Web应用时
workflow: desktop-build-workflow
---

# /build 命令

## 命令描述

`/build` 命令用于Web应用的构建与打包，是交付流程中的核心构建命令。该命令管理从依赖安装到产物输出的完整构建流程，支持多平台框架（React、Vue、Angular、Next.js、Nuxt、Svelte），自动检测项目类型并执行最优构建策略，确保构建产物的高质量与可部署性。

---

## 触发条件

| 触发方式 | 说明 |
|----------|------|
| 命令输入 | 用户输入 `/build` |
| 关键词触发 | 用户提及"构建"、"打包"、"compile"、"bundle"、"webpack"、"vite" |
| 自动触发 | `/deploy` 部署前自动触发构建 |
| 流程触发 | CI/CD流水线构建阶段自动触发 |

---

## 命令名称与语法

```
/build [options]
```

---

## 参数定义

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| --platform | string | 否 | auto-detect | 目标平台：react、vue、angular、next、nuxt、svelte |
| --mode | string | 否 | production | 构建模式：development、production |
| --output | string | 否 | dist/ | 输出目录 |
| --skip-lint | boolean | 否 | false | 跳过代码检查 |
| --skip-tests | boolean | 否 | false | 跳过构建前测试 |
| --analyze | boolean | 否 | false | 分析构建产物体积 |
| --minify | boolean | 否 | true | 压缩代码 |
| --source-map | boolean | 否 | false | 生成Source Map |
| --env-file | string | 否 | .env.production | 环境变量文件 |

---

## 执行流程

> 标准四步框架：1. 输入验证 → 2. Agent调度 → 3. 任务执行 → 4. 结果验证

```
┌─────────────────────────────────────────────────────────────┐
│                    /build 执行流程                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 输入验证                                                 │
│     ├── 检测项目类型（从package.json读取）                    │
│     ├── 验证构建配置文件完整性                                │
│     ├── 检查依赖是否已安装                                    │
│     └── 验证环境变量配置                                      │
│                                                             │
│  2. Agent调度                                                │
│     ├── DevOps Engineer 接收构建任务                         │
│     ├── CI/CD Specialist 准备构建环境                        │
│     └── Frontend Developer 审查构建配置                      │
│                                                             │
│  3. 构建执行                                                 │
│     ├── 安装依赖（npm/ci install）                           │
│     ├── 执行代码检查（如未跳过）                              │
│     ├── 运行构建前测试（如未跳过）                            │
│     ├── 执行构建命令                                         │
│     │   ├── React: npm run build (CRA/webpack/vite)         │
│     │   ├── Vue: npm run build (vite/webpack)               │
│     │   ├── Angular: ng build --configuration=production    │
│     │   ├── Next.js: next build                            │
│     │   ├── Nuxt: nuxt build                               │
│     │   └── Svelte: vite build / svelte-kit build          │
│     ├── 优化静态资源                                         │
│     │   ├── 图片压缩与格式转换                               │
│     │   ├── CSS压缩与去重                                    │
│     │   ├── JS Tree-shaking与代码分割                       │
│     │   └── 字体子集化                                       │
│     └── 生成构建产物                                         │
│                                                             │
│  4. 结果验证                                                 │
│     ├── 检查构建退出码                                       │
│     ├── 验证输出目录非空                                     │
│     ├── 检查产物完整性                                       │
│     ├── 运行构建后测试                                       │
│     └── 生成构建报告                                         │
│                                                             │
│  5. 产物交付                                                 │
│     ├── 输出构建产物清单                                     │
│     ├── 生成构建报告                                         │
│     ├── 记录构建元数据                                       │
│     └── 归档构建产物                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 涉及Agent

| Agent | 角色 | 职责 |
|-------|------|------|
| build-release-engineer | 主导 | 构建流程协调、构建环境管理 |
| cicd-specialist | 辅助 | CI/CD流水线执行、构建缓存管理 |
| frontend-developer | 辅助 | 构建配置审查、框架特定优化 |

---

## 输出格式

### 1. 构建报告 (build-report.md)

```markdown
# 构建报告

## 构建概要
- 构建时间: 2026-05-06 10:00:00
- 构建平台: next
- 构建模式: production
- 输出目录: dist/
- 构建状态: ✅ 成功

## 构建产物
| 文件 | 大小 | Gzip | 类型 |
|------|------|------|------|
| main.js | 245KB | 78KB | JS |
| vendor.js | 512KB | 156KB | JS |
| main.css | 89KB | 22KB | CSS |
| assets/ | 1.2MB | - | 静态资源 |

## 构建时间线
- 10:00:00 - 开始输入验证
- 10:00:30 - 检测项目类型: Next.js
- 10:01:00 - 安装依赖
- 10:03:00 - 依赖安装完成
- 10:03:10 - 执行构建命令
- 10:08:30 - 构建完成
- 10:08:40 - 资源优化完成
- 10:08:50 - 结果验证通过

## 优化结果
- Tree-shaking: 移除 23 个未使用模块
- 代码分割: 生成 5 个chunk
- 图片优化: 压缩 12 张图片，节省 340KB
- CSS去重: 合并 8 个重复规则

## 验证结果
- 构建退出码: 0 ✅
- 输出目录: 非空 ✅
- 产物完整性: 通过 ✅
- 构建测试: 通过 ✅
```

### 2. 构建清单 (build-manifest.json)

```json
{
  "build_id": "BUILD-20260506-001",
  "platform": "next",
  "mode": "production",
  "output_dir": "dist/",
  "status": "success",
  "duration_seconds": 530,
  "artifacts": [
    {
      "name": "main.js",
      "size": 250880,
      "gzip_size": 79872,
      "type": "js"
    },
    {
      "name": "vendor.js",
      "size": 524288,
      "gzip_size": 159744,
      "type": "js"
    },
    {
      "name": "main.css",
      "size": 91136,
      "gzip_size": 22528,
      "type": "css"
    }
  ],
  "optimizations": {
    "tree_shaking_modules_removed": 23,
    "code_splitting_chunks": 5,
    "images_optimized": 12,
    "css_rules_deduplicated": 8
  }
}
```

---

## 示例用法

### 示例1: 标准构建

```bash
/build
```

自动检测项目类型并执行生产环境构建。

### 示例2: 指定平台构建

```bash
/build --platform next --mode production
```

指定Next.js平台执行生产环境构建。

### 示例3: 开发模式构建

```bash
/build --mode development --source-map
```

开发模式构建并生成Source Map。

### 示例4: 构建分析

```bash
/build --analyze
```

执行构建并分析产物体积分布。

### 示例5: 自定义输出目录

```bash
/build --output ./build --platform vue
```

指定Vue平台构建，输出到./build目录。

---

## 质量门禁

| 门禁标识 | 阻塞级别(BLOCK/WARN) | 通过标准 |
|----------|----------------------|----------|
| BUILD-SUCCESS | BLOCK | 构建退出码=0且输出目录非空 |

---

## 注意事项

1. **依赖检查**: 构建前确保所有依赖已正确安装
2. **环境变量**: 确认环境变量文件存在且配置正确
3. **构建缓存**: 合理利用构建缓存加速重复构建
4. **资源优化**: 生产构建务必开启压缩与优化
5. **产物验证**: 构建完成后务必验证产物完整性

---

## 相关脚本

- `scripts/build-optimizer.py` - 构建产物优化器，执行资源压缩、Tree-shaking验证与产物分析

---

## 相关工作流

- `workflows/sdd-tdd-full.md` (Phase 7) - SDD+TDD全生命周期工作流的构建阶段

---

## 相关命令

- `/deploy` - 构建完成后执行部署
- `/test` - 构建前执行测试
- `/review` - 构建前执行代码审查
