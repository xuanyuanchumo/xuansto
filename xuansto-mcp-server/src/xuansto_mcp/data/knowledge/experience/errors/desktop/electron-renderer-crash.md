---
id: "KP-EXP-ERR-DESK-001"
type: "error-solution"
severity: "high"
category: "desktop"
tags: ["Electron", "渲染进程", "崩溃", "GPU", "内存泄漏", "V8", "原生模块"]
version: "1.0.0"
confidence: 0.90
occurrences: 4
---

## Electron 渲染进程崩溃 (置信度: 0.90 | 技术栈: Electron)

### 现象
窗口白屏、GPU 进程崩溃（exit_code=133）、JS heap out of memory、Maximum call stack size exceeded。

### 根因
GPU 加速与显卡驱动不兼容（虚拟机/远程桌面常见）、内存泄漏（未清理事件监听器/闭包）、V8 堆栈溢出（无限递归）、原生模块 ABI 版本不匹配。

### 解决方案

```typescript
app.disableHardwareAcceleration();
app.commandLine.appendSwitch('js-flags', '--max-old-space-size=4096');
```

```typescript
class ResourceManager {
  private intervals: NodeJS.Timeout[] = [];
  startInterval(fn: () => void, ms: number) { this.intervals.push(setInterval(fn, ms)); }
  destroy() { this.intervals.forEach(clearInterval); this.intervals = []; }
}
```

```bash
npx electron-rebuild
```

### 验证
集成 Sentry 崩溃监控，定期采样 process.memoryUsage() 检测内存增长。
