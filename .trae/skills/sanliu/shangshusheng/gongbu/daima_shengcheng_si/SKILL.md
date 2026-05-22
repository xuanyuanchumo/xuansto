---
name: daima_shengcheng_si
description: 代码生成司，负责基于规范的代码生成、脚手架搭建。操作优先级第一优先级，推荐使用MANUAL模式进行代码生成。
---
# 代码生成司技能指令

## 职责
- 基于SDD/TDD规范的结构化代码生成
- 项目脚手架快速搭建
- 模板驱动的代码片段生成
- OperationPriority集成：MANUAL模式优先
- 生成代码的质量验证

## OperationPriority集成

### 代码生成的操作优先级策略

```yaml
operation_priority_config:
  code_generation:
    primary_mode: "MANUAL"       # 第一优先级：手动精确操作
    reasoning: |
      代码生成需要精确控制：
      - 理解上下文后逐文件编辑
      - 确保与现有代码风格一致
      - 避免批量操作引入隐蔽错误
      - 支持增量式逐步构建

    fallback_mode: "SCRIPT"     # 第二选择：脚本辅助
    use_case: "重复性模板填充、批量重命名"

    avoid_mode: "COMMAND"       # 避免：终端命令
    reason: "sed/awk等命令易破坏文件编码和结构"
```

### MANUAL模式执行规范

```
MANUAL模式代码生成流程：
  1. 分析需求和现有代码上下文
  2. 规划需要创建/修改的文件清单
  3. 逐个文件使用Write/Edit工具精确操作
  4. 每个文件完成后立即验证语法正确性
  5. 确保导入关系正确
  6. 运行lint检查
  7. 记录生成决策到DecisionLog
```

## 代码生成能力矩阵

### 支持的生成场景

| 场景 | 输入 | 输出 | 复杂度 | 推荐模式 |
|------|------|------|--------|----------|
| 脚手架搭建 | 项目类型+技术栈 | 完整项目结构 | 中 | MANUAL+SCRIPT |
| API端点 | OpenAPI/SDD规范 | 路由+处理函数+测试 | 高 | MANUAL |
| 数据模型 | ER图/字段定义 | Model类+迁移脚本 | 中 | MANUAL |
| CRUD模块 | 实体定义 | Service+Repository+Controller | 高 | MANUAL |
| 测试用例 | SDD条款 | pytest测试骨架 | 中 | MANUAL |
| 配置文件 | 环境需求 | .env/docker-compose等 | 低 | SCRIPT |

## 脚手架模板体系

### 项目模板结构

```yaml
scaffold_templates:
  python_fastapi:
    structure:
      - "src/__init__.py"
      - "src/main.py"
      - "src/config.py"
      - "src/api/__init__.py"
      - "src/api/routes.py"
      - "src/models/__init__.py"
      - "src/models/base.py"
      - "src/services/__init__.py"
      - "tests/__init__.py"
      - "tests/conftest.py"
      - "requirements.txt"
      - "pytest.ini"
      - ".env.example"
      - "Dockerfile"
      - "docker-compose.yml"

  vue_frontend:
    structure:
      - "src/main.ts"
      - "src/App.vue"
      - "src/router/index.ts"
      - "src/stores/"
      - "src/views/"
      - "src/components/"
      - "src/api/index.ts"
      - "vite.config.ts"
      - "tsconfig.json"
      - "package.json"
```

## 工作流程

```
1. 接收代码生成请求（含规范/描述/参考）
2. 分析技术栈和项目约定
3. 确定OperationPriority为MANUAL
4. 规划文件清单和依赖关系
5. 按依赖顺序逐个文件生成
6. 每步进行语法和导入校验
7. 运行lint和type check
8. 执行初步测试验证
9. 将生成记录到DecisionLog
10. 输出生成报告
```

## 代码质量门禁

| 检查项 | 标准 | 失败处理 |
|--------|------|----------|
| 语法正确 | 无SyntaxError | 修复后重新生成 |
| 类型注解完整 | 公开API必须有类型 | 补充注解 |
| 导入有效 | 所有import可解析 | 修正路径或移除 |
| 命名符合规范 | 通过linter检查 | 重命名 |
| 无硬编码敏感值 | SecretsManager检查 | 移至环境变量 |

## 协同接口

| 接口 | 描述 | 调用方 |
|------|------|--------|
| `generate_code` | 代码生成 | 尚书省/吏部分配 |
| `create_scaffold` | 脚手架搭建 | 新项目启动 |
| `validate_output` | 输出验证 | 生成后自动 |
| `get_template` | 获取模板 | 内部调用 |
