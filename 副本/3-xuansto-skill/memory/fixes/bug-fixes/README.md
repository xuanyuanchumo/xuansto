# 缺陷修复记录

本目录用于存储已确认缺陷的修复记录，包括缺陷根因分析、修复方案、影响范围及验证结果。

## 记录格式

```json
{
  "id": "FIX-BG-YYYYMMDD-NNN",
  "timestamp": "ISO8601时间戳",
  "bugId": "关联缺陷编号",
  "severity": "critical|high|medium|low",
  "summary": "修复摘要",
  "rootCause": "根因分析",
  "affectedModules": ["受影响模块"],
  "fixDescription": "修复方案描述",
  "changedFiles": ["变更文件列表"],
  "testCoverage": "新增或修改的测试",
  "regressionRisk": "回归风险等级",
  "verifiedBy": "验证人",
  "resolution": "解决状态",
  "status": "open|in-review|merged|verified"
}
```

## 示例记录

```json
{
  "id": "FIX-BG-20260428-001",
  "timestamp": "2026-04-28T13:20:00.000Z",
  "bugId": "BUG-20260428-012",
  "severity": "high",
  "summary": "用户登录后Token未正确刷新导致会话过期",
  "rootCause": "Token刷新逻辑在并发请求时存在竞态条件，旧Token覆盖了新Token",
  "affectedModules": ["auth-service", "session-manager"],
  "fixDescription": "引入原子性Token刷新机制，使用乐观锁确保并发安全",
  "changedFiles": ["src/auth/TokenRefresher.ts", "src/session/SessionManager.ts"],
  "testCoverage": "新增并发Token刷新测试用例3个",
  "regressionRisk": "low",
  "verifiedBy": "QA团队",
  "resolution": "已合并至main分支",
  "status": "verified"
}
```
