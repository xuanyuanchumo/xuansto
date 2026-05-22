# 用户管理规范

规范ID: SPC-USER-001
版本: v1.0
作者: SDD-TDD系统

## 功能描述

用户管理模块提供用户的增删改查功能，包括用户注册、登录、信息更新和注销等核心功能。

## 属性定义

- username: 用户名，必填，唯一，类型: string，描述: 用户登录名，长度3-20字符
- email: 电子邮箱，必填，唯一，类型: string，描述: 用户邮箱地址
- password: 密码，必填，类型: string，描述: 用户密码，长度6-50字符
- age: 年龄，可选，类型: integer，描述: 用户年龄
- status: 状态，必填，类型: enum，枚举值: [active, inactive, banned]，默认值: active
- created_at: 创建时间，必填，类型: datetime，描述: 账户创建时间

## 接口定义

### 用户注册
- 方法: POST
- 路径: /api/v1/users/register
- 描述: 用户注册接口

### 用户登录
- 方法: POST
- 路径: /api/v1/users/login
- 描述: 用户登录接口

### 获取用户信息
- 方法: GET
- 路径: /api/v1/users/{user_id}
- 描述: 根据ID获取用户信息

### 更新用户信息
- 方法: PUT
- 路径: /api/v1/users/{user_id}
- 描述: 更新用户信息

### 删除用户
- 方法: DELETE
- 路径: /api/v1/users/{user_id}
- 描述: 删除用户账户

## 测试场景

### 场景1: 用户注册成功
- Given: 系统正常运行，用户未注册
- When: 提交有效的注册信息（用户名、邮箱、密码）
- Then: 用户注册成功，返回用户ID和成功消息

### 场景2: 用户注册失败-用户名重复
- Given: 系统正常运行，用户名已存在
- When: 提交已存在的用户名进行注册
- Then: 注册失败，返回用户名已存在错误

### 场景3: 用户登录成功
- Given: 用户已注册，状态为active
- When: 提交正确的用户名和密码
- Then: 登录成功，返回认证令牌

### 场景4: 用户登录失败-密码错误
- Given: 用户已注册
- When: 提交错误的密码
- Then: 登录失败，返回密码错误提示

## 约束条件

- 用户名长度必须在3-20字符之间
- 密码长度必须在6-50字符之间
- 邮箱格式必须符合标准格式
- 用户年龄必须在1-150之间

## 业务规则

- BR-001: 新注册用户默认状态为active
- BR-002: 被ban的用户无法登录
- BR-003: 密码必须加密存储

## 异常处理

- UserNotFoundException: 用户不存在
- DuplicateUsernameException: 用户名重复
- InvalidPasswordException: 密码格式错误
- AuthenticationFailedException: 认证失败
