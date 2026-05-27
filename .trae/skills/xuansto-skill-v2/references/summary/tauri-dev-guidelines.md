# Tauri Development Guidelines

## Core Points
- Tauri安全模型：权限系统(Capability Scope)、命令权限(Command Permissions)、最小权限原则
- IPC模式：Tauri Command(invoke)、事件系统(listen/emit)、状态管理
- 插件系统：官方插件(autoupdater/dialog/fs/http)、自定义插件开发
- Auto-Updater：签名验证、增量更新、多平台分发
- Sidecar：打包外部可执行文件、进程管理

## Applicable Scenarios
- Desktop Developer Agent开发Tauri桌面应用
- IPC Specialist Agent设计Tauri Command和事件系统
- Auto-Update Engineer Agent实现自动更新机制
