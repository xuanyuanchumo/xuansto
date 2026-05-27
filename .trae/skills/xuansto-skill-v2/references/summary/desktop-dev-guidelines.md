# Desktop Development Guidelines

## Core Points
- 桌面开发核心主题：项目结构、IPC模式、窗口管理、系统托盘、自启动、文件系统访问、通知、安全
- IPC模式：主进程-渲染进程通信、contextBridge安全桥接、双向invoke/handle模式
- 窗口管理：多窗口生命周期、窗口间通信、无边框窗口自定义
- 安全：contextIsolation启用、nodeIntegration禁用、sandbox启用、CSP配置

## Applicable Scenarios
- Desktop Developer Agent开发Electron/Tauri桌面应用
- IPC Specialist Agent设计进程间通信架构
- 桌面应用安全配置和最佳实践
