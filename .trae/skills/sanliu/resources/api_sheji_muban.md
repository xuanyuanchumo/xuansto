---
name: api_sheji_muban
description: API 设计模板，包含 RESTful API 设计规范和模板。
---
# API 设计模板

## RESTful API 设计原则

### URL 设计
- 使用名词复数：/users, /products
- 层级关系：/users/{id}/orders
- 过滤参数：/users?status=active

### HTTP 方法
- GET：获取资源
- POST：创建资源
- PUT：更新资源（完整）
- PATCH：更新资源（部分）
- DELETE：删除资源

### 状态码
- 200：成功
- 201：创建成功
- 400：请求错误
- 401：未授权
- 403：禁止访问
- 404：资源不存在
- 500：服务器错误

## API 文档模板

### 接口名称
- **路径**：/api/resource
- **方法**：GET/POST/PUT/DELETE
- **描述**：接口功能描述

### 请求参数
| 参数名 | 类型 | 必填 | 描述 |
|--------|------|------|------|
| id | int | 是 | 资源ID |

### 响应格式
```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 错误响应
```json
{
  "code": 400,
  "message": "错误描述",
  "errors": []
}
```
