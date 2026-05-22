# 文档模板

## API文档模板

```markdown
# API名称

## 概述
简要描述API的功能和用途。

## 基本信息
- **接口地址**: `/api/v1/resource`
- **请求方法**: `POST` / `GET` / `PUT` / `DELETE`
- **认证方式**: Bearer Token / API Key / OAuth2

## 请求参数

### Headers
| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | 认证令牌 |
| Content-Type | string | 是 | application/json |

### Query Parameters
| 参数名 | 类型 | 必填 | 说明 | 默认值 |
|--------|------|------|------|--------|
| page | int | 否 | 页码 | 1 |
| size | int | 否 | 每页数量 | 20 |

### Request Body
```json
{
  "field1": "value1",
  "field2": 123
}
```

## 响应结果

### 成功响应
**状态码**: 200 OK
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "xxx",
    "name": "xxx"
  }
}
```

### 错误响应
**状态码**: 400/401/403/404/500
```json
{
  "code": 1001,
  "message": "错误描述",
  "errors": [
    {
      "field": "field1",
      "message": "字段错误详情"
    }
  ]
}
```

## 示例

### 请求示例
```bash
curl -X POST "https://api.example.com/api/v1/resource" \
  -H "Authorization: Bearer token" \
  -H "Content-Type: application/json" \
  -d '{"field1": "value1", "field2": 123}'
```

### 响应示例
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": "abc123",
    "name": "示例数据"
  }
}
```

## 注意事项
- 特殊说明1
- 特殊说明2

## 变更历史
| 版本 | 日期 | 变更内容 | 作者 |
|------|------|----------|------|
| 1.0.0 | 2024-01-01 | 初始版本 | xxx |
```

## 设计文档模板

```markdown
# 功能名称 设计文档

## 1. 概述
### 1.1 背景
描述功能需求的背景和来源。

### 1.2 目标
明确设计要达成的目标。

### 1.3 范围
定义功能的边界，包括做什么和不做什么。

## 2. 系统设计
### 2.1 架构设计
描述整体架构方案，可包含架构图。

### 2.2 模块划分
列出主要模块及其职责。

### 2.3 数据流
描述数据在系统中的流转过程。

## 3. 详细设计
### 3.1 接口设计
定义模块间的接口契约。

### 3.2 数据模型
定义数据结构和存储方案。

### 3.3 算法设计
描述核心算法的实现方案。

## 4. 非功能性设计
### 4.1 性能设计
性能目标和优化策略。

### 4.2 安全设计
安全措施和权限控制。

### 4.3 可扩展性设计
未来扩展的考虑。

## 5. 实施计划
### 5.1 开发计划
分阶段开发计划。

### 5.2 测试计划
测试策略和计划。

### 5.3 上线计划
上线步骤和回滚方案。

## 6. 风险评估
识别潜在风险和应对措施。

## 7. 附录
参考资料、术语表等。
```

## README文档模板

```markdown
# 项目名称

简短的项目描述。

## 功能特性

- 特性1
- 特性2
- 特性3

## 快速开始

### 环境要求

- Node.js >= 18.0
- Python >= 3.10

### 安装

```bash
npm install project-name
```

### 基本使用

```javascript
const project = require('project-name');
project.doSomething();
```

## 开发

### 本地开发

```bash
# 克隆项目
git clone <repository-url>
cd project
npm install
npm run dev
```

### 运行测试

```bash
npm test
```
```
