---
id: "KP-EXP-PAT-ERR-001"
type: "error-solution"
severity: "medium"
category: "pattern"
tags: ["错误处理", "中间件", "Express", "FastAPI", "全局异常", "错误码"]
version: "1.0.0"
confidence: 0.90
occurrences: 3
---

## 错误处理中间件 (置信度: 0.90 | 技术栈: Express/FastAPI)

### 现象
API 返回 500 状态码但无结构化错误信息、异常堆栈泄露到客户端、不同端点错误格式不一致。

### 根因
缺少全局错误处理中间件、业务异常与系统异常未区分、错误响应格式未标准化。

### 解决方案

```typescript
app.use((err: Error, req: Request, res: Response, next: NextFunction) => {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({ error: { code: err.code, message: err.message } });
  }
  logger.error("Unhandled error", err);
  res.status(500).json({ error: { code: "INTERNAL_ERROR", message: "服务器内部错误" } });
});
```

```python
@app.exception_handler(AppError)
async def handle_app_error(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"error": {"code": exc.code, "message": exc.message}})
```

### 验证
集成测试覆盖所有错误类型，确认响应格式一致且不泄露堆栈。
