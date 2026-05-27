# Electron Security Best Practices

## Core Points
- 核心安全配置：contextIsolation=true、nodeIntegration=false、sandbox=true
- Preload脚本安全：仅暴露必要API、不暴露Node.js模块、使用contextBridge
- IPC验证：通道名白名单、参数Schema校验、返回值过滤
- CSP配置：限制script-src/style-src、禁用unsafe-inline/unsafe-eval
- Remote模块禁用、webSecurity启用、额外安全措施(导航限制、新窗口控制)

## Applicable Scenarios
- Desktop Developer Agent开发安全Electron应用
- Security Auditor Agent审查桌面应用安全配置
- IPC Specialist Agent设计安全的IPC通信
