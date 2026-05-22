# 外部技能注册模板

## 注册表格式

外部技能注册表采用 JSON 格式，用于标准化描述和注册外部技能。注册表文件应放置在 `.trae/skills/` 目录下，文件名建议使用 `skill_registry.json`。

```json
{
  "skills": [
    {
      "name": "技能名称",
      "path": "技能路径",
      "description": "功能描述",
      "scenarios": ["适用场景1", "适用场景2"],
      "departments": ["调用部门1", "调用部门2"]
    }
  ]
}
```

## 必填字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| name | string | 技能名称，用于唯一标识技能，建议使用英文小写和下划线命名方式，如 `code_review`、`api_design` |
| path | string | 技能路径，指向技能定义文件的相对路径，相对于 `.trae/skills/` 目录，如 `sanliu/code_review.md` |
| description | string | 功能描述，详细说明该技能的功能和用途，帮助使用者理解技能的能力范围 |
| scenarios | array | 适用场景列表，描述该技能适用的具体场景，如代码审查、API设计、数据库优化等 |
| departments | array | 调用部门列表，指定哪些部门或角色可以调用该技能，如开发部、测试部、运维部等 |

## 可选字段说明

| 字段名 | 类型 | 说明 |
|--------|------|------|
| version | string | 技能版本号，遵循语义化版本规范，如 `1.0.0` |
| author | string | 技能作者信息 |
| tags | array | 技能标签，用于分类和检索，如 `["code", "review", "quality"]` |
| dependencies | array | 依赖的其他技能列表 |
| config | object | 技能配置参数 |
| enabled | boolean | 是否启用该技能，默认为 `true` |

## 注册示例

### 示例一：代码审查技能

```json
{
  "skills": [
    {
      "name": "code_review",
      "path": "sanliu/code_review.md",
      "description": "提供代码审查能力，包括代码质量检查、安全漏洞扫描、性能优化建议等",
      "scenarios": [
        "代码提交前审查",
        "合并请求审查",
        "定期代码质量检查"
      ],
      "departments": ["开发部", "架构组"],
      "version": "1.0.0",
      "tags": ["code", "review", "quality"],
      "enabled": true
    }
  ]
}
```

### 示例二：API设计技能

```json
{
  "skills": [
    {
      "name": "api_design",
      "path": "sanliu/api_design.md",
      "description": "提供RESTful API设计能力，包括接口规范定义、请求响应格式设计、错误码设计等",
      "scenarios": [
        "新接口设计",
        "接口文档编写",
        "接口规范审查"
      ],
      "departments": ["开发部", "产品部"],
      "version": "1.2.0",
      "author": "架构组",
      "tags": ["api", "rest", "design"],
      "dependencies": ["code_review"],
      "enabled": true
    }
  ]
}
```

### 示例三：多技能注册

```json
{
  "skills": [
    {
      "name": "database_design",
      "path": "sanliu/database_design.md",
      "description": "提供数据库设计能力，包括表结构设计、索引优化、SQL语句优化等",
      "scenarios": [
        "新表设计",
        "数据库性能优化",
        "SQL审查"
      ],
      "departments": ["开发部", "DBA组"]
    },
    {
      "name": "test_generation",
      "path": "sanliu/test_generation.md",
      "description": "提供测试用例生成能力，包括单元测试、集成测试、端到端测试用例生成",
      "scenarios": [
        "单元测试编写",
        "测试覆盖率提升",
        "回归测试"
      ],
      "departments": ["开发部", "测试部"]
    },
    {
      "name": "security_audit",
      "path": "sanliu/security_audit.md",
      "description": "提供安全审计能力，包括代码安全检查、依赖漏洞扫描、安全规范检查",
      "scenarios": [
        "上线前安全检查",
        "定期安全审计",
        "漏洞修复验证"
      ],
      "departments": ["安全部", "开发部"],
      "config": {
        "scan_depth": "deep",
        "report_format": "json"
      }
    }
  ]
}
```
