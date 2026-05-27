<!-- version: 1.9.0 | 编码: UTF-8 -->
# Agent脚本文件修改规范

## 1. 脚本语言选型矩阵

| 使用场景 | 首选语言 | 文件扩展名 | 运行时要求 | 说明 |
|----------|----------|------------|------------|------|
| 通用文件修改（批量替换、格式转换、代码生成） | Python 3.10+ | .py | python / python3 | 优先选择，跨平台 |
| Web项目前端操作（DOM处理、样式计算、设计令牌同步） | Node.js / JavaScript | .js | node | Web场景专用 |
| 系统级操作（文件权限、进程管理、注册表） | PowerShell 7+ | .ps1 | pwsh | 减少使用 |
| 构建打包（桌面应用构建、签名） | PowerShell 7+ | .ps1 | pwsh | 桌面构建专用 |

### 强制约束

- Shell脚本(.sh)仅限CI/CD流水线和容器内操作
- PowerShell脚本(.ps1)应尽量减少使用
- 任何可跨平台操作优先使用Python

### 决策树

```
需要修改文件？
├── 是否为Web前端操作（DOM、样式、设计令牌）？
│   └── 是 → 使用 JavaScript (.js)
├── 是否需要系统级操作（权限、注册表、进程管理）？
│   └── 是 → 使用 PowerShell (.ps1)
├── 是否为桌面构建打包？
│   └── 是 → 使用 PowerShell (.ps1)
└── 其他所有场景 → 使用 Python (.py) [首选]
```

---

## 2. 编码规范

| 脚本语言 | 第一行内容 | 编码声明要求 | 编码格式 | 行尾 |
|----------|------------|-------------|----------|------|
| Python (.py) | `#!/usr/bin/env python3` | 禁止 `# -*- coding: utf-8 -*-` | UTF-8 without BOM | LF |
| JavaScript (.js) | `#!/usr/bin/env node` | 禁止任何编码声明 | UTF-8 without BOM | LF |
| PowerShell (.ps1) | `#Requires -Version 7.0` | 禁止任何编码声明 | UTF-8 without BOM | LF |

### Python编码声明禁止理由

Python 3.x默认使用UTF-8编码，PEP 263声明已冗余。此外，`# -*- coding: utf-8 -*-` 声明与PyInstaller等工具链存在兼容性冲突，会导致打包失败或运行时异常。

---

## 3. 五步闭环流程

### 步骤1：创建脚本（CREATE）

- 写入 `.knowledge/temp-scripts/` 目录
- 命名格式：`{agent-name}-{task-hash}-{timestamp}.{ext}`
- 必须包含docstring或注释说明脚本目的
- 禁止硬编码密码、Token、密钥等敏感信息

### 步骤2：审查脚本（REVIEW）

- Agent必须进行自我审查，确认以下内容：
  - 修改目标是否正确
  - 逻辑是否正确
  - 无越权操作
  - 无危险操作
- 涉及安全敏感路径或批量删除操作时，必须提交Code Reviewer进行人工审查
- 检查安全沙箱违规项，确保不触发任何BLOCK级别约束

### 步骤3：执行脚本（EXECUTE）

- 使用对应运行时执行脚本
- 超时限制：
  - Python / JavaScript：120秒
  - PowerShell：300秒
- 执行失败时立即停止，不再继续后续步骤
- 失败时保存错误日志到 `.knowledge/script-errors/` 目录

### 步骤4：验证修改结果（VERIFY）

- 文件存在性验证：确认目标文件已正确生成或修改
- UTF-8 without BOM编码验证：确保文件编码符合规范
- 内容完整性对比：对比修改前后的内容差异
- 语法检查：
  - Python：`python -m py_compile`
  - JavaScript：`node --check`
- 受影响的单元测试必须通过
- 验证失败则通过 `git restore` 回滚所有变更

### 步骤5：清理脚本文件（CLEANUP）

质量门禁：SCRIPT-CLEANUP

- 删除临时脚本文件
- 有价值的脚本经Orchestrator审批后可保留至 `scripts/` 目录
- 确认 `.knowledge/temp-scripts/` 目录清洁
- 清理失败时记录警告日志

### 闭环流程图

```
创建脚本 → 审查脚本 → 执行脚本 → 验证结果 → 清理脚本
   ↓失败      ↓失败      ↓失败      ↓失败
  中止       中止       中止+回滚   中止+回滚
```

---

## 4. 安全沙箱约束

### 安全约束矩阵

| 约束项 | 规则 | 检测方式 | 级别 |
|--------|------|----------|------|
| 文件系统写入白名单 | 仅允许写入任务指定的目标文件，禁止写入系统目录 | 路径前缀检查 | BLOCK |
| 文件系统读取范围 | 仅允许读取项目目录和标准库路径 | 路径前缀检查 | BLOCK |
| 进程调用 | 禁止 subprocess / os.system / child_process.exec | 代码模式匹配 | BLOCK |
| 网络访问 | 禁止 requests / fetch / urllib / Invoke-WebRequest | 代码模式匹配 | BLOCK |
| 动态代码执行 | 禁止 eval / exec / Function() | 代码模式匹配 | BLOCK |
| 文件删除范围 | 禁止 shutil.rmtree / os.unlink 删除非临时文件 | 代码模式匹配 | BLOCK |

### 违规检测正则示例

**Python：**
```
subprocess\.run|os\.system|requests\.get|eval\(|exec\(
```

**JavaScript：**
```
child_process\.exec|fetch\(|eval\(|new Function\(
```

**PowerShell：**
```
Invoke-WebRequest|Invoke-Expression|Start-Process
```

---

## 5. 文件修改能力边界

### 白名单（允许修改）

- 项目源代码文件（`src/`、`app/` 等）
- 配置文件（`.env.example`、`tsconfig.json` 等）
- 前端资源文件（CSS、图片、字体等）
- 测试文件（`tests/`、`__tests__/`）
- 文档文件（`docs/`、`README.md`）
- Skill自身脚本（`scripts/`，需经Orchestrator审批）

### 黑名单（禁止修改）

- 系统配置文件（`/etc/`、`C:\Windows\System32\`）
- 版本控制元数据（`.git/`）
- 第三方依赖目录（`node_modules/`、`.venv/`）
- 包管理器锁定文件（`package-lock.json` 除外）
- 其他Agent正在修改的文件
- 环境变量文件（`.env`、`.env.local`）
- 已编译的二进制文件（`.exe`、`.dll`、`.so`）

---

## 6. 错误处理与回滚流程

```
脚本执行失败 →
  1. 停止执行，不继续后续步骤
  2. 保存错误日志到 .knowledge/script-errors/{script-name}-error.log
  3. 通过 git restore {file} 回滚所有已修改文件
  4. 重新分析修改方案
  5. 若连续3次失败，触发死循环检测，从头重新开始
```

---

## 7. Agent自查清单

提交脚本前Agent必须逐项确认：

- [ ] 脚本语言符合选型矩阵（Python优先）
- [ ] 文件编码为UTF-8 without BOM
- [ ] 无 `# -*- coding: utf-8 -*-` 声明（Python）
- [ ] 第一行为正确shebang或版本声明
- [ ] 包含完整的docstring或注释
- [ ] 脚本存入 `.knowledge/temp-scripts/` 目录
- [ ] 文件名格式正确（`{agent-name}-{task-hash}-{timestamp}.{ext}`）
- [ ] 已自我审查：无越权操作、无危险操作
- [ ] 已确认修改范围与任务需求一致
- [ ] 已确认执行后会自动清理脚本
