---
id: "KP-EXP-PAT-002"
type: "success-pattern"
category: "middleware"
tags: ["错误处理", "中间件", "Express", "FastAPI", "统一响应", "异常捕获", "日志"]
version: "1.0.0"
created: "2026-04-28T10:00:00Z"
updated: "2026-04-28T10:00:00Z"
source: "auto_precipitation"
confidence: 0.88
last_validated: "2026-04-28T10:00:00Z"
success_count: 0
failure_count: 0
trigger: "pattern_validated"
references:
  - id: "KP-GEN-002"
    relation: "implements"
  - id: "KP-EXP-ERR-001"
    relation: "extends"
  - id: "KP-EXP-ERR-002"
    relation: "extends"
---

# 错误处理中间件模式

## 模式描述

错误处理中间件模式将应用中的异常捕获、错误分类、日志记录和统一响应格式化集中到中间件层处理。业务代码只需抛出特定异常，中间件自动完成错误转换和响应生成。这是函数组合思想在中间件架构中的体现。

### 核心价值

| 价值 | 说明 |
|------|------|
| **关注点分离** | 业务逻辑不关心错误响应格式 |
| **一致性** | 所有 API 错误响应遵循统一格式 |
| **可观测性** | 错误自动记录日志，便于监控和排查 |
| **安全性** | 避免内部错误信息泄露给客户端 |

### 处理流程

```
请求 → 业务逻辑 → 抛出异常
                         │
                         ▼
              ┌─────────────────────┐
              │  错误处理中间件       │
              │  1. 捕获异常         │
              │  2. 分类错误         │
              │  3. 记录日志         │
              │  4. 生成统一响应      │
              └─────────────────────┘
                         │
                         ▼
              统一格式错误响应 → 客户端
```

---

## Python 实现 (FastAPI)

### 自定义异常

```python
from enum import Enum

class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    CONFLICT = "CONFLICT"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"

class AppException(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        status_code: int = 500,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)

class NotFoundException(AppException):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=f"{resource}不存在",
            status_code=404,
            details={"resource": resource, "id": resource_id},
        )

class ValidationException(AppException):
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            status_code=422,
            details=details or {},
        )

class DatabaseException(AppException):
    def __init__(self, message: str, original_error: Exception | None = None):
        super().__init__(
            code=ErrorCode.DATABASE_ERROR,
            message=message,
            status_code=503,
            details={"original_type": type(original_error).__name__} if original_error else {},
        )
```

### 错误处理中间件

```python
import logging
import traceback
from datetime import datetime, timezone
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except AppException as exc:
            logger.warning(
                "业务异常",
                extra={
                    "code": exc.code.value,
                    "message": exc.message,
                    "path": request.url.path,
                    "details": exc.details,
                },
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "success": False,
                    "error": {
                        "code": exc.code.value,
                        "message": exc.message,
                        "details": exc.details,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "path": str(request.url.path),
                },
            )
        except Exception as exc:
            logger.error(
                "未处理异常",
                extra={
                    "type": type(exc).__name__,
                    "message": str(exc),
                    "path": request.url.path,
                    "traceback": traceback.format_exc(),
                },
            )
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": ErrorCode.INTERNAL_ERROR.value,
                        "message": "服务器内部错误",
                        "details": {},
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "path": str(request.url.path),
                },
            )
```

### 使用示例

```python
from fastapi import FastAPI

app = FastAPI()
app.add_middleware(ErrorHandlerMiddleware)

@app.get("/api/users/{user_id}")
async def get_user(user_id: str):
    user = await user_repo.find_by_id(user_id)
    if user is None:
        raise NotFoundException("用户", user_id)
    return {"success": True, "data": user}
```

---

## TypeScript 实现 (Express)

### 自定义错误类

```typescript
enum ErrorCode {
  VALIDATION_ERROR = "VALIDATION_ERROR",
  NOT_FOUND = "NOT_FOUND",
  UNAUTHORIZED = "UNAUTHORIZED",
  FORBIDDEN = "FORBIDDEN",
  CONFLICT = "CONFLICT",
  INTERNAL_ERROR = "INTERNAL_ERROR",
  DATABASE_ERROR = "DATABASE_ERROR",
}

class AppError extends Error {
  constructor(
    public readonly code: ErrorCode,
    message: string,
    public readonly statusCode: number = 500,
    public readonly details: Record<string, unknown> = {},
  ) {
    super(message);
    this.name = "AppError";
    Object.setPrototypeOf(this, AppError.prototype);
  }
}

class NotFoundError extends AppError {
  constructor(resource: string, resourceId: string) {
    super(
      ErrorCode.NOT_FOUND,
      `${resource}不存在`,
      404,
      { resource, id: resourceId },
    );
  }
}

class ValidationError extends AppError {
  constructor(message: string, details?: Record<string, unknown>) {
    super(ErrorCode.VALIDATION_ERROR, message, 422, details ?? {});
  }
}

class DatabaseError extends AppError {
  constructor(message: string, originalError?: Error) {
    super(ErrorCode.DATABASE_ERROR, message, 503, {
      originalType: originalError?.constructor.name,
    });
  }
}
```

### 错误处理中间件

```typescript
import { Request, Response, NextFunction } from "express";
import { logger } from "./logger";

interface ErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
  timestamp: string;
  path: string;
}

function errorHandler(
  err: Error,
  req: Request,
  res: Response,
  _next: NextFunction,
): void {
  if (err instanceof AppError) {
    logger.warn({
      code: err.code,
      message: err.message,
      path: req.path,
      details: err.details,
    });

    const response: ErrorResponse = {
      success: false,
      error: {
        code: err.code,
        message: err.message,
        details: err.details,
      },
      timestamp: new Date().toISOString(),
      path: req.path,
    };

    res.status(err.statusCode).json(response);
    return;
  }

  logger.error({
    type: err.constructor.name,
    message: err.message,
    path: req.path,
    stack: err.stack,
  });

  const response: ErrorResponse = {
    success: false,
    error: {
      code: ErrorCode.INTERNAL_ERROR,
      message: "服务器内部错误",
      details: {},
    },
    timestamp: new Date().toISOString(),
    path: req.path,
  };

  res.status(500).json(response);
}

export { errorHandler, AppError, NotFoundError, ValidationError, DatabaseError, ErrorCode };
```

### 使用示例

```typescript
import express from "express";

const app = express();

app.get("/api/users/:userId", async (req, res, next) => {
  try {
    const user = await userRepo.findById(req.params.userId);
    if (!user) {
      throw new NotFoundError("用户", req.params.userId);
    }
    res.json({ success: true, data: user });
  } catch (err) {
    next(err);
  }
});

app.use(errorHandler);
```

---

## 统一响应格式

### 成功响应

```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-04-28T10:00:00.000Z"
}
```

### 错误响应

```json
{
  "success": false,
  "error": {
    "code": "NOT_FOUND",
    "message": "用户不存在",
    "details": {
      "resource": "用户",
      "id": "usr_001"
    }
  },
  "timestamp": "2026-04-28T10:00:00.000Z",
  "path": "/api/users/usr_001"
}
```

---

## 适用场景

| 场景 | 说明 |
|------|------|
| REST API 服务 | 统一所有端点的错误响应格式 |
| 微服务架构 | 各服务遵循一致的错误规范 |
| 前后端分离 | 前端可统一处理错误逻辑 |
| API 网关 | 网关层聚合下游服务的错误响应 |

## 注意事项

- 生产环境不应向客户端暴露堆栈跟踪或内部实现细节
- 错误日志应包含请求上下文（请求 ID、用户 ID、路径等）
- 数据库异常应转换为通用错误，不泄露 SQL 语句
- 考虑为不同错误类型设置不同的日志级别（warn vs error）
- 异步中间件中的未捕获 Promise 拒绝需要额外处理

## 相关知识

- [KP-GEN-002] 函数式编程原则 — 中间件链即函数组合
- [KP-EXP-ERR-001] 数据库连接超时 — 数据库异常的中间件处理
- [KP-EXP-ERR-002] 空指针异常 — 业务异常的统一捕获
