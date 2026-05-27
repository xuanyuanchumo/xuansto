# Agent脚本文件修改规范

## Core Points
- 脚本语言选型矩阵：Python(通用修改/首选)、Node.js(Web前端操作)、PowerShell(系统级操作/桌面构建)
- 强制约束：Shell脚本(.sh)仅限CI/CD和容器内操作，所有脚本必须有错误处理和日志输出
- 脚本模板：标准头部(#!/usr/bin/env)、参数解析、错误处理、日志格式、退出码规范
- 安全约束：禁止硬编码密钥、路径必须验证、文件操作需备份、权限最小化

## Applicable Scenarios
- Agent执行文件修改操作时选择脚本语言
- 编写自动化脚本和工具
- Code Reviewer Agent检查脚本规范
