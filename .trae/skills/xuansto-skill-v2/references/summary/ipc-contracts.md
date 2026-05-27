# IPC契约规范参考文档

## Core Points
- IPC契约是桌面应用(Electron/Tauri)主进程与渲染进程通信的正式规范
- 契约格式：通道名称、方向(invoke/send/on)、参数Schema、返回类型、错误处理
- 通道定义Schema：JSON Schema验证参数和返回值，确保类型安全
- 常见桌面IPC契约示例：文件操作、窗口控制、系统信息、数据存储
- 验证规则：通道名命名规范、参数必填校验、返回值类型匹配

## Applicable Scenarios
- IPC Specialist Agent设计IPC通信架构和契约
- Desktop Developer Agent实现IPC通道
- Code Reviewer Agent检查IPC契约合规性
