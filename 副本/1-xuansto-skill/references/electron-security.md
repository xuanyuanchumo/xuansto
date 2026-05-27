# Electron Security Best Practices
> 版本: 1.9.0 | 更新日期: 2026-04-28 | 编码: UTF-8 | 行尾: LF

## 目录

- [contextIsolation](#contextisolation)
- [nodeIntegration](#nodeintegration)
- [sandbox](#sandbox)
- [Preload Script Security](#preload-script-security)
- [IPC Validation](#ipc-validation)
- [Content Security Policy](#content-security-policy)
- [Remote Module](#remote-module)
- [webSecurity](#websecurity)
- [Additional Security Measures](#additional-security-measures)

---

## contextIsolation

`contextIsolation` separates the preload script's JavaScript context from the renderer's JavaScript context. When enabled, the renderer cannot access Electron internals or Node.js APIs through the prototype chain.

### Why It Matters

Without context isolation, a malicious script loaded in the renderer (even from a CDN or XSS) can access Electron internals via prototype pollution:

```javascript
// Without contextIsolation, renderer can access preload's globals
Array.prototype.push.call(preloadGlobals, maliciousCode);
```

### Correct Configuration

```javascript
const mainWindow = new BrowserWindow({
  webPreferences: {
    contextIsolation: true,  // ALWAYS true (default since Electron 12)
    nodeIntegration: false,
    sandbox: true,
    preload: path.join(__dirname, 'preload.js'),
  },
});
```

### Safe Preload Pattern

```javascript
// preload.js - CORRECT
const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('api', {
  readFile: (filePath) => ipcRenderer.invoke('fs:readFile', filePath),
  onSave: (callback) => ipcRenderer.on('file:saved', (_, data) => callback(data)),
});
```

### Unsafe Preload Pattern (NEVER DO THIS)

```javascript
// preload.js - DANGEROUS
const { ipcRenderer } = require('electron');

window.readFile = (filePath) => ipcRenderer.invoke('fs:readFile', filePath);

// Even worse:
window.ipcRenderer = ipcRenderer;
window.require = require;
```

---

## nodeIntegration

`nodeIntegration` controls whether Node.js APIs are available in the renderer process. It must always be `false` in production.

### Why It Matters

With `nodeIntegration: true`, renderer JavaScript has full access to Node.js:

```javascript
// With nodeIntegration: true, renderer can do:
const { exec } = require('child_process');
exec('rm -rf /');  // Catastrophic

const fs = require('fs');
fs.readFileSync('/etc/shadow');  // Read sensitive files

const net = require('net');
// Open reverse shells, exfiltrate data
```

### Correct Configuration

```javascript
const mainWindow = new BrowserWindow({
  webPreferences: {
    contextIsolation: true,
    nodeIntegration: false,  // ALWAYS false
    sandbox: true,
    preload: path.join(__dirname, 'preload.js'),
  },
});
```

### If Node.js APIs Are Needed in Renderer

Use IPC to delegate Node.js operations to the main process:

```javascript
// Instead of using Node.js in renderer:
// const fs = require('fs');  // NEVER

// Use IPC:
// Renderer
const content = await window.api.readFile('/path/to/file');

// Main
ipcMain.handle('fs:readFile', async (event, filePath) => {
  const validated = validatePath(filePath);
  if (!validated) throw new Error('Invalid path');
  return fs.promises.readFile(filePath, 'utf-8');
});
```

---

## sandbox

When `sandbox: true`, the renderer process runs in an OS-level sandbox with restricted capabilities. The preload script also loses access to most Node.js APIs.

### Why It Matters

The OS sandbox provides an additional layer of defense:

- No direct file system access from renderer
- No direct network access from renderer
- No ability to spawn child processes
- Limited system call surface

### Correct Configuration

```javascript
const mainWindow = new BrowserWindow({
  webPreferences: {
    contextIsolation: true,
    nodeIntegration: false,
    sandbox: true,  // ALWAYS true in production
    preload: path.join(__dirname, 'preload.js'),
  },
});
```

### Sandbox-Compatible Preload

In sandboxed mode, preload scripts can only use a subset of Electron APIs:

```javascript
// preload.js - Sandbox compatible
const { contextBridge, ipcRenderer } = require('electron');

// These are available in sandboxed preload:
// - contextBridge
// - ipcRenderer (invoke, send, on, once, removeListener)
// - webFrame

// These are NOT available in sandboxed preload:
// - require() (except for 'electron')
// - process
// - Buffer
// - __dirname, __filename
// - Node.js core modules

contextBridge.exposeInMainWorld('api', {
  // Use ipcRenderer for all operations
  readFile: (path) => ipcRenderer.invoke('fs:readFile', path),
  writeFile: (path, content) => ipcRenderer.invoke('fs:writeFile', path, content),
  onNotification: (callback) => {
    ipcRenderer.on('notification', (_, data) => callback(data));
  },
});
```

---

## Preload Script Security

### Rules for Secure Preload Scripts

1. **Only expose through `contextBridge`**: Never assign directly to `window`
2. **Never expose raw IPC methods**: Wrap with validation
3. **Never expose `ipcRenderer` directly**: Create specific methods
4. **Validate parameters before sending**: Don't trust renderer input
5. **Sanitize return values**: Don't leak internal data structures

### Secure Preload Template

```javascript
const { contextBridge, ipcRenderer } = require('electron');

const ALLOWED_READ_EXTENSIONS = ['.txt', '.json', '.md', '.csv'];
const ALLOWED_WRITE_EXTENSIONS = ['.txt', '.json', '.md', '.csv'];

function validateFilePath(filePath) {
  if (typeof filePath !== 'string') return false;
  if (filePath.length === 0 || filePath.length > 4096) return false;
  if (filePath.includes('..')) return false;
  return true;
}

function validateExtension(filePath, allowed) {
  const ext = filePath.slice(filePath.lastIndexOf('.')).toLowerCase();
  return allowed.includes(ext);
}

contextBridge.exposeInMainWorld('api', {
  readFile: (filePath) => {
    if (!validateFilePath(filePath)) {
      return Promise.reject(new Error('Invalid file path'));
    }
    if (!validateExtension(filePath, ALLOWED_READ_EXTENSIONS)) {
      return Promise.reject(new Error('File extension not allowed'));
    }
    return ipcRenderer.invoke('fs:readFile', filePath);
  },

  writeFile: (filePath, content) => {
    if (!validateFilePath(filePath)) {
      return Promise.reject(new Error('Invalid file path'));
    }
    if (!validateExtension(filePath, ALLOWED_WRITE_EXTENSIONS)) {
      return Promise.reject(new Error('File extension not allowed'));
    }
    if (typeof content !== 'string' || content.length > 10 * 1024 * 1024) {
      return Promise.reject(new Error('Invalid content'));
    }
    return ipcRenderer.invoke('fs:writeFile', filePath, content);
  },

  onEvent: (eventName, callback) => {
    const allowedEvents = ['update:available', 'file:saved', 'notification'];
    if (!allowedEvents.includes(eventName)) {
      console.error(`Event not allowed: ${eventName}`);
      return () => {};
    }
    const handler = (_, data) => callback(data);
    ipcRenderer.on(eventName, handler);
    return () => ipcRenderer.removeListener(eventName, handler);
  },
});
```

---

## IPC Validation

### Validate All Inputs in Main Process

Never trust data from the renderer process. Validate every IPC message.

```javascript
const { ipcMain } = require('electron');
const Joi = require('joi');

const readFileSchema = Joi.object({
  filePath: Joi.string().max(4096).required(),
  encoding: Joi.string().valid('utf-8', 'ascii', 'base64').default('utf-8'),
});

ipcMain.handle('fs:readFile', async (event, params) => {
  const { error, value } = readFileSchema.validate(params);
  if (error) {
    return {
      success: false,
      error: { code: 'ERR_VALIDATION', message: error.message },
    };
  }

  const { filePath, encoding } = value;

  if (filePath.includes('..')) {
    return {
      success: false,
      error: { code: 'ERR_PATH_TRAVERSAL', message: 'Path traversal detected' },
    };
  }

  const allowedDir = app.getPath('userData');
  const resolved = path.resolve(filePath);
  if (!resolved.startsWith(allowedDir)) {
    return {
      success: false,
      error: { code: 'ERR_PERMISSION', message: 'Access denied' },
    };
  }

  try {
    const content = await fs.promises.readFile(resolved, encoding);
    return { success: true, data: content };
  } catch (err) {
    return {
      success: false,
      error: { code: 'ERR_READ_FAILED', message: err.message },
    };
  }
});
```

### Rate Limiting for IPC

```javascript
class IpcRateLimiter {
  constructor(maxRequests = 100, windowMs = 1000) {
    this.limits = new Map();
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }

  check(senderId, channel) {
    const key = `${senderId}:${channel}`;
    const now = Date.now();

    if (!this.limits.has(key)) {
      this.limits.set(key, { count: 1, start: now });
      return true;
    }

    const entry = this.limits.get(key);
    if (now - entry.start > this.windowMs) {
      entry.count = 1;
      entry.start = now;
      return true;
    }

    entry.count++;
    return entry.count <= this.maxRequests;
  }
}

const rateLimiter = new IpcRateLimiter(50, 1000);

ipcMain.handle('fs:readFile', async (event, params) => {
  const senderId = event.sender.id;
  if (!rateLimiter.check(senderId, 'fs:readFile')) {
    return {
      success: false,
      error: { code: 'ERR_RATE_LIMIT', message: 'Too many requests' },
    };
  }

  // ... handle request
});
```

### Channel Whitelisting

```javascript
const ALLOWED_CHANNELS = new Set([
  'fs:readFile',
  'fs:writeFile',
  'app:getVersion',
  'window:minimize',
  'window:maximize',
  'update:check',
]);

ipcMain.handle('*', async (event, channel, ...args) => {
  if (!ALLOWED_CHANNELS.has(channel)) {
    console.error(`Blocked IPC call to unknown channel: ${channel}`);
    return {
      success: false,
      error: { code: 'ERR_FORBIDDEN', message: 'Channel not allowed' },
    };
  }
});
```

---

## Content Security Policy

### Setting CSP in Main Process

```javascript
const { session } = require('electron');

session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
  callback({
    responseHeaders: {
      ...details.responseHeaders,
      'Content-Security-Policy': [
        "default-src 'self'; " +
        "script-src 'self'; " +
        "style-src 'self' 'unsafe-inline'; " +
        "img-src 'self' data: https:; " +
        "font-src 'self'; " +
        "connect-src 'self' https://api.example.com; " +
        "media-src 'self'; " +
        "object-src 'none'; " +
        "frame-src 'none'; " +
        "base-uri 'self'; " +
        "form-action 'self';"
      ],
    },
  });
});
```

### CSP in HTML Meta Tag

```html
<!DOCTYPE html>
<html>
<head>
  <meta http-equiv="Content-Security-Policy"
    content="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api.example.com; object-src 'none';">
</head>
<body>
  <div id="root"></div>
</body>
</html>
```

### CSP Directives Explained

| Directive | Purpose | Recommended Value |
|-----------|---------|-------------------|
| `default-src` | Fallback for all resource types | `'self'` |
| `script-src` | JavaScript sources | `'self'` (never `'unsafe-inline'` or `'unsafe-eval'`) |
| `style-src` | CSS sources | `'self' 'unsafe-inline'` (often needed for frameworks) |
| `img-src` | Image sources | `'self' data: https:` |
| `connect-src` | AJAX/WebSocket sources | `'self' https://api.example.com` |
| `font-src` | Font sources | `'self'` |
| `object-src` | Plugin sources | `'none'` |
| `frame-src` | iframe sources | `'none'` |
| `base-uri` | `<base>` element | `'self'` |
| `form-action` | Form submissions | `'self'` |

---

## Remote Module

### Never Use the Remote Module

The `remote` module exposes main process objects to the renderer, creating massive security holes.

```javascript
// NEVER DO THIS
const { remote } = require('@electron/remote');
const { dialog } = remote;
dialog.showOpenDialog();  // Renderer can access main process APIs

// NEVER DO THIS
const { BrowserWindow } = remote;
new BrowserWindow({});  // Renderer can create windows

// NEVER DO THIS
remote.require('child_process').exec('malicious-command');
```

### Alternatives to Remote Module

| Remote Usage | Secure Alternative |
|---|---|
| `remote.dialog` | IPC → main process dialog |
| `remote.BrowserWindow` | IPC → main process window management |
| `remote.app` | IPC → main process app info |
| `remote.getCurrentWindow()` | IPC → main process window state |
| `remote.Menu` | IPC → main process menu construction |

```javascript
// Instead of remote.dialog:
// Renderer
const result = await window.api.showOpenDialog(options);

// Preload
contextBridge.exposeInMainWorld('api', {
  showOpenDialog: (options) => ipcRenderer.invoke('dialog:open', options),
});

// Main
ipcMain.handle('dialog:open', async (event, options) => {
  const validatedOptions = validateDialogOptions(options);
  return dialog.showOpenDialog(mainWindow, validatedOptions);
});
```

---

## webSecurity

### Never Disable webSecurity

`webSecurity` enforces the same-origin policy. Disabling it allows cross-origin requests without CORS.

```javascript
// NEVER DO THIS
const mainWindow = new BrowserWindow({
  webPreferences: {
    webSecurity: false,  // DANGEROUS - disables same-origin policy
  },
});
```

### If Cross-Origin Requests Are Needed

Use proper CORS configuration on the server, or proxy through the main process:

```javascript
// Main process proxy
const { net } = require('electron');

ipcMain.handle('http:fetch', async (event, { url, options }) => {
  const allowedOrigins = ['https://api.example.com', 'https://cdn.example.com'];
  const parsedUrl = new URL(url);
  if (!allowedOrigins.some(origin => url.startsWith(origin))) {
    return { success: false, error: { code: 'ERR_ORIGIN', message: 'Origin not allowed' } };
  }

  const response = await net.fetch(url, {
    method: options?.method || 'GET',
    headers: options?.headers,
    body: options?.body,
  });

  const data = await response.text();
  return { success: true, data, status: response.status };
});
```

---

## Additional Security Measures

### Disable DevTools in Production

```javascript
if (app.isPackaged) {
  mainWindow.webContents.on('devtools-opened', () => {
    mainWindow.webContents.closeDevTools();
  });
}
```

### Validate Navigation

```javascript
mainWindow.webContents.on('will-navigate', (event, url) => {
  const allowedOrigins = ['file://', 'app://'];
  if (!allowedOrigins.some(origin => url.startsWith(origin))) {
    event.preventDefault();
  }
});

mainWindow.webContents.setWindowOpenHandler(({ url }) => {
  const allowedUrls = ['https://example.com'];
  if (allowedUrls.some(allowed => url.startsWith(allowed))) {
    return { action: 'allow' };
  }
  return { action: 'deny' };
});
```

### Secure Protocol Registration

```javascript
const { protocol } = require('electron');

protocol.registerSchemesAsPrivileged([
  {
    scheme: 'app',
    privileges: {
      secure: true,
      standard: true,
      supportFetchAPI: true,
      corsEnabled: false,
    },
  },
]);
```

### Prevent Clickjacking

```javascript
mainWindow.webContents.on('new-window', (event) => {
  event.preventDefault();
});
```

### Secure Storage

```javascript
const { safeStorage } = require('electron');

function encryptString(text) {
  if (safeStorage.isEncryptionAvailable()) {
    return safeStorage.encryptString(text).toString('base64');
  }
  throw new Error('Encryption not available');
}

function decryptString(encrypted) {
  if (safeStorage.isEncryptionAvailable()) {
    const buffer = Buffer.from(encrypted, 'base64');
    return safeStorage.decryptString(buffer);
  }
  throw new Error('Encryption not available');
}
```

### Security Audit Checklist

| Check | Status |
|-------|--------|
| `contextIsolation: true` | ☐ |
| `nodeIntegration: false` | ☐ |
| `sandbox: true` | ☐ |
| `webSecurity: true` | ☐ |
| No `remote` module | ☐ |
| CSP configured | ☐ |
| Preload uses `contextBridge` only | ☐ |
| IPC inputs validated | ☐ |
| Path traversal protection | ☐ |
| Rate limiting on IPC | ☐ |
| Navigation validation | ☐ |
| DevTools disabled in production | ☐ |
| No `allowRunningInsecureContent` | ☐ |
| Secure storage for secrets | ☐ |
| Dependencies audited (`npm audit`) | ☐ |

---

## 相关参考

- [Desktop Development Guidelines](desktop-dev-guidelines.md) — 桌面端开发通用指南：项目结构、IPC模式、窗口管理、系统托盘等
- [安全指南参考文档](security-guidelines.md) — 安全编码实践、常见漏洞防护、桌面端安全规范完整指南
