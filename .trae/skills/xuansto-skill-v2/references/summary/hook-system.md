# Hook生命周期系统

## Core Points
- 五类生命周期Hook：PreToolUse(工具调用前拦截)、PostToolUse(工具调用后处理)、SessionStart(会话启动初始化)、Stop(会话停止收尾)、PreCompact(上下文压缩前保存)
- 配置文件：hooks/hooks.json，支持条件匹配和正则过滤
- PreToolUse可拦截和修改工具调用参数，PostToolUse可处理和转换工具返回结果
- SessionStart/Stop实现会话状态保存和恢复，PreCompact确保压缩前持久化关键数据

## Applicable Scenarios
- 实现Agent执行流程的自动化拦截和处理
- 配置会话持久化和上下文压缩策略
- 设计工具调用的安全审计和参数校验
