# Desktop Development Guidelines
> 版本: 1.9.0 | 更新日期: 2026-04-28 | 编码: UTF-8 | 行尾: LF

## 目录

- [Project Structure](#project-structure)
- [IPC Patterns](#ipc-patterns)
- [Window Management](#window-management)
- [System Tray](#system-tray)
- [Auto-start](#auto-start)
- [File System Access](#file-system-access)
- [Notifications](#notifications)
- [Security](#security)

---

## Project Structure

### Electron Project Structure

```
my-electron-app/
├── main/                    # Main process code
│   ├── index.js             # Entry point
│   ├── ipc/                 # IPC handlers
│   │   ├── index.js         # Handler registry
│   │   ├── file-ops.js      # File operation handlers
│   │   └── window-ops.js    # Window operation handlers
│   ├── services/            # Business logic services
│   │   ├── auto-update.js
│   │   └── tray.js
│   └── utils/               # Utility functions
│       ├── logger.js
│       └── validator.js
├── preload/                 # Preload scripts
│   ├── index.js             # Main preload
│   └── api.js               # Exposed API bridge
├── renderer/                # Frontend code
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   ├── hooks/
│   │   │   └── useIpc.ts    # IPC hook
│   │   └── lib/
│   │       └── ipc.ts       # Typed IPC client
│   └── package.json
├── resources/               # App resources
│   ├── icons/
│   └── tray/
├── electron-builder.yml     # Build configuration
└── package.json
```

### Tauri Project Structure

```
my-tauri-app/
├── src/                     # Frontend code
│   ├── App.tsx
│   ├── components/
│   ├── hooks/
│   │   └── useCommand.ts    # Tauri command hook
│   └── lib/
│       └── commands.ts      # Typed command client
├── src-tauri/               # Rust backend
│   ├── src/
│   │   ├── main.rs          # Entry point
│   │   ├── commands/        # Command handlers
│   │   │   ├── mod.rs
│   │   │   ├── file_ops.rs
│   │   │   └── window_ops.rs
│   │   ├── services/        # Business logic
│   │   │   ├── mod.rs
│   │   │   └── auto_update.rs
│   │   └── utils/
│   │       ├── mod.rs
│   │       └── logger.rs
│   ├── Cargo.toml
│   ├── tauri.conf.json      # Tauri configuration
│   └── capabilities/        # Permission capabilities
│       └── default.json
├── public/                  # Static assets
└── package.json
```

### Flutter Desktop Project Structure

```
my-flutter-app/
├── lib/
│   ├── main.dart
│   ├── models/
│   ├── services/
│   │   ├── platform_service.dart   # Platform channel service
│   │   └── window_service.dart
│   ├── widgets/
│   └── utils/
├── windows/                 # Windows native code
│   ├── runner/
│   └── flutter/
├── macos/                   # macOS native code
│   ├── Runner/
│   └── Flutter/
├── linux/                   # Linux native code
│   ├── flutter/
│   └── my_application.cc
├── pubspec.yaml
└── test/
```

---

## IPC Patterns

### Electron IPC

#### Invoke/Handle Pattern (Recommended)

```javascript
// Main process
const { ipcMain } = require('electron');

ipcMain.handle('fs:readFile', async (event, filePath) => {
  try {
    const content = await fs.promises.readFile(filePath, 'utf-8');
    return { success: true, data: content };
  } catch (err) {
    return { success: false, error: { code: 'ERR_READ_FAILED', message: err.message } };
  }
});

// Preload
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('api', {
  readFile: (path) => ipcRenderer.invoke('fs:readFile', path),
});

// Renderer
const result = await window.api.readFile('/path/to/file');
```

#### Send/On Pattern (for events)

```javascript
// Main → Renderer
mainWindow.webContents.send('update:available', { version: '1.2.0' });

// Renderer → Main
ipcRenderer.send('analytics:event', { name: 'button_click', data: {} });

// Preload bridge for events
contextBridge.exposeInMainWorld('events', {
  onUpdateAvailable: (callback) => {
    ipcRenderer.on('update:available', (_, data) => callback(data));
  },
  sendAnalytics: (data) => ipcRenderer.send('analytics:event', data),
});
```

### Tauri IPC

#### Command Pattern

```rust
#[derive(Debug, Deserialize)]
struct ReadFileRequest {
    path: String,
}

#[derive(Debug, Serialize)]
struct ReadFileResponse {
    success: bool,
    data: Option<String>,
    error: Option<CommandError>,
}

#[command]
async fn fs_read_file(request: ReadFileRequest) -> ReadFileResponse {
    match tokio::fs::read_to_string(&request.path).await {
        Ok(content) => ReadFileResponse {
            success: true,
            data: Some(content),
            error: None,
        },
        Err(err) => ReadFileResponse {
            success: false,
            data: None,
            error: Some(CommandError {
                code: "ERR_READ_FAILED".to_string(),
                message: err.to_string(),
            }),
        },
    }
}
```

```typescript
import { invoke } from '@tauri-apps/api/core';

const result = await invoke<ReadFileResponse>('fs_read_file', {
  request: { path: '/path/to/file' },
});
```

#### Event Pattern

```rust
use tauri::Manager;
app_handle.emit("update:available", UpdatePayload { version: "1.2.0" })?;
```

```typescript
import { listen } from '@tauri-apps/api/event';
const unlisten = await listen<UpdatePayload>('update:available', (event) => {
  console.log('Update available:', event.payload);
});
```

### Flutter Platform Channels

```dart
class PlatformService {
  static const _channel = MethodChannel('com.example.app/platform');

  Future<String> readFile(String path) async {
    try {
      return await _channel.invokeMethod('readFile', {'path': path});
    } on PlatformException catch (e) {
      throw ServiceException(code: e.code, message: e.message ?? '');
    }
  }

  Stream<UpdateInfo> get onUpdateAvailable {
    return EventChannel('com.example.app/updates')
        .receiveBroadcastStream()
        .map((data) => UpdateInfo.fromJson(data));
  }
}
```

---

## Window Management

### Electron Window Management

```javascript
const { BrowserWindow, screen } = require('electron');

function createMainWindow() {
  const primaryDisplay = screen.getPrimaryDisplay();
  const { width, height } = primaryDisplay.workAreaSize;

  const mainWindow = new BrowserWindow({
    width: Math.min(1200, width * 0.8),
    height: Math.min(800, height * 0.8),
    minWidth: 800,
    minHeight: 600,
    center: true,
    show: false,
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      preload: path.join(__dirname, 'preload.js'),
    },
  });

  mainWindow.once('ready-to-show', () => {
    mainWindow.show();
  });

  mainWindow.on('close', (e) => {
    if (appState.isBusy) {
      e.preventDefault();
      dialog.showMessageBox(mainWindow, {
        type: 'warning',
        title: 'Confirm Exit',
        message: 'Work in progress. Are you sure you want to exit?',
        buttons: ['Exit', 'Cancel'],
      }).then(({ response }) => {
        if (response === 0) mainWindow.destroy();
      });
    }
  });

  return mainWindow;
}
```

### Tauri Window Management

```rust
use tauri::{Manager, WindowBuilder, WindowUrl};

fn create_main_window(app: &tauri::App) -> tauri::Result<()> {
    WindowBuilder::new(app, "main", WindowUrl::App("index.html".into()))
        .title("My App")
        .inner_size(1200.0, 800.0)
        .min_inner_size(800.0, 600.0)
        .center()
        .visible(false)
        .build()?;

    if let Some(window) = app.get_window("main") {
        window.show()?;
    }
    Ok(())
}
```

### Multi-Window Coordination

```javascript
class WindowManager {
  constructor() {
    this.windows = new Map();
  }

  create(name, options) {
    if (this.windows.has(name)) {
      const win = this.windows.get(name);
      if (!win.isDestroyed()) {
        win.focus();
        return win;
      }
    }

    const win = new BrowserWindow(options);
    this.windows.set(name, win);
    win.on('closed', () => this.windows.delete(name));
    return win;
  }

  broadcast(channel, data) {
    for (const win of this.windows.values()) {
      if (!win.isDestroyed()) {
        win.webContents.send(channel, data);
      }
    }
  }

  closeAll() {
    for (const win of this.windows.values()) {
      if (!win.isDestroyed()) win.close();
    }
  }
}
```

---

## System Tray

### Electron System Tray

```javascript
const { Tray, Menu, nativeImage } = require('electron');

class AppTray {
  constructor(mainWindow) {
    const icon = nativeImage.createFromPath(path.join(__dirname, 'resources/tray/icon.png'));
    this.tray = new Tray(icon.resize({ width: 16, height: 16 }));
    this.mainWindow = mainWindow;

    this.tray.setToolTip('My Application');
    this.tray.on('click', () => this.toggleWindow());

    const contextMenu = Menu.buildFromTemplate([
      { label: 'Show Window', click: () => this.showWindow() },
      { type: 'separator' },
      { label: 'Check for Updates', click: () => this.checkUpdates() },
      { type: 'separator' },
      { label: 'Quit', click: () => app.quit() },
    ]);

    this.tray.setContextMenu(contextMenu);
  }

  toggleWindow() {
    if (this.mainWindow.isVisible()) {
      this.mainWindow.hide();
    } else {
      this.showWindow();
    }
  }

  showWindow() {
    this.mainWindow.show();
    this.mainWindow.focus();
  }

  destroy() {
    this.tray.destroy();
  }
}
```

### Tauri System Tray

```rust
use tauri::{
    menu::{MenuBuilder, MenuItemBuilder},
    tray::{TrayIconBuilder, MouseButton, MouseButtonState},
    Manager,
};

fn setup_tray(app: &tauri::App) -> tauri::Result<()> {
    let show = MenuItemBuilder::with_id("show", "Show Window").build(app)?;
    let quit = MenuItemBuilder::with_id("quit", "Quit").build(app)?;

    let menu = MenuBuilder::new(app)
        .item(&show)
        .separator()
        .item(&quit)
        .build()?;

    TrayIconBuilder::new()
        .icon(app.default_window_icon().unwrap().clone())
        .tooltip("My Application")
        .menu(&menu)
        .on_menu_event(|app, event| match event.id.as_ref() {
            "show" => {
                if let Some(window) = app.get_window("main") {
                    window.show().unwrap();
                    window.set_focus().unwrap();
                }
            }
            "quit" => {
                app.exit(0);
            }
            _ => {}
        })
        .on_tray_icon_event(|tray, event| {
            if let MouseButtonState::Up(MouseButton::Left) = event {
                let app = tray.app_handle();
                if let Some(window) = app.get_window("main") {
                    window.show().unwrap();
                    window.set_focus().unwrap();
                }
            }
        })
        .build(app)?;

    Ok(())
}
```

---

## Auto-start

### Electron Auto-start (Windows/macOS/Linux)

```javascript
const app = require('electron').app;
const path = require('path');

function setAutoStart(enable) {
  if (process.platform === 'win32') {
    const key = 'HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run';
    if (enable) {
      const exePath = app.getPath('exe');
      require('child_process').exec(
        `reg add "${key}" /v "MyApp" /t REG_SZ /d "${exePath}" /f`
      );
    } else {
      require('child_process').exec(
        `reg delete "${key}" /v "MyApp" /f`
      );
    }
  } else if (process.platform === 'darwin') {
    const plistPath = path.join(
      process.env.HOME,
      'Library/LaunchAgents/com.example.myapp.plist'
    );
    if (enable) {
      const plist = `<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.example.myapp</string>
  <key>ProgramArguments</key><array>
    <string>${app.getPath('exe')}</string>
  </array>
  <key>RunAtLoad</key><true/>
</dict>
</plist>`;
      require('fs').writeFileSync(plistPath, plist);
    } else {
      try { require('fs').unlinkSync(plistPath); } catch {}
    }
  } else if (process.platform === 'linux') {
    const autostartDir = path.join(process.env.HOME, '.config/autostart');
    const desktopPath = path.join(autostartDir, 'myapp.desktop');
    if (enable) {
      require('fs').mkdirSync(autostartDir, { recursive: true });
      const desktop = `[Desktop Entry]
Type=Application
Name=MyApp
Exec=${app.getPath('exe')}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true`;
      require('fs').writeFileSync(desktopPath, desktop);
    } else {
      try { require('fs').unlinkSync(desktopPath); } catch {}
    }
  }
}
```

### Tauri Auto-start

```rust
use tauri::Manager;

#[command]
fn set_auto_start(app: tauri::AppHandle, enable: bool) -> Result<(), String> {
    #[cfg(target_os = "linux")]
    {
        let autostart_dir = dirs::home_dir()
            .ok_or("Cannot find home directory")?
            .join(".config/autostart");
        std::fs::create_dir_all(&autostart_dir).map_err(|e| e.to_string())?;
        let desktop_path = autostart_dir.join("myapp.desktop");
        if enable {
            let exe = std::env::current_exe().map_err(|e| e.to_string())?;
            let content = format!(
                "[Desktop Entry]\nType=Application\nName=MyApp\nExec={}\nHidden=false\nX-GNOME-Autostart-enabled=true",
                exe.display()
            );
            std::fs::write(&desktop_path, content).map_err(|e| e.to_string())?;
        } else {
            let _ = std::fs::remove_file(&desktop_path);
        }
    }
    Ok(())
}
```

---

## File System Access

### Electron File System Access

```javascript
const { dialog, ipcMain } = require('electron');
const fs = require('fs/promises');
const path = require('path');

const ALLOWED_EXTENSIONS = ['.txt', '.json', '.md', '.csv'];

ipcMain.handle('fs:openFile', async () => {
  const result = await dialog.showOpenDialog({
    properties: ['openFile'],
    filters: [{ name: 'Documents', extensions: ALLOWED_EXTENSIONS.map(e => e.slice(1)) }],
  });

  if (result.canceled || result.filePaths.length === 0) {
    return { success: false, error: { code: 'ERR_CANCELLED', message: 'User cancelled' } };
  }

  const filePath = result.filePaths[0];
  const ext = path.extname(filePath).toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return { success: false, error: { code: 'ERR_INVALID_TYPE', message: 'File type not allowed' } };
  }

  const content = await fs.readFile(filePath, 'utf-8');
  return { success: true, data: { path: filePath, content } };
});

ipcMain.handle('fs:saveFile', async (event, { filePath, content }) => {
  const resolved = path.resolve(filePath);
  const appDataPath = app.getPath('userData');
  if (!resolved.startsWith(appDataPath)) {
    return { success: false, error: { code: 'ERR_PERMISSION', message: 'Access denied' } };
  }
  await fs.writeFile(resolved, content, 'utf-8');
  return { success: true };
});
```

### Tauri File System Access

```rust
use tauri::api::dialog::blocking::FileDialogBuilder;
use std::path::PathBuf;
use std::fs;

#[derive(Debug, Serialize)]
struct FileResult {
    success: bool,
    data: Option<FileData>,
    error: Option<String>,
}

#[derive(Debug, Serialize)]
struct FileData {
    path: String,
    content: String,
}

#[command]
fn fs_open_file() -> FileResult {
    let path = match FileDialogBuilder::new()
        .add_filter("Documents", &["txt", "json", "md", "csv"])
        .pick_file()
    {
        Some(p) => p,
        None => return FileResult { success: false, data: None, error: Some("Cancelled".into()) },
    };

    match fs::read_to_string(&path) {
        Ok(content) => FileResult {
            success: true,
            data: Some(FileData {
                path: path.to_string_lossy().into(),
                content,
            }),
            error: None,
        },
        Err(err) => FileResult {
            success: false,
            data: None,
            error: Some(err.to_string()),
        },
    }
}
```

---

## Notifications

### Electron Notifications

```javascript
const { Notification, isMac } = require('electron');

function showNotification({ title, body, icon, actions }) {
  if (!Notification.isSupported()) {
    return;
  }

  const notification = new Notification({
    title,
    body,
    icon: icon || undefined,
    silent: false,
  });

  notification.on('click', () => {
    if (mainWindow) {
      mainWindow.show();
      mainWindow.focus();
    }
  });

  notification.show();
}
```

### Tauri Notifications

```rust
use tauri::api::notification::Notification;

#[command]
fn show_notification(app: tauri::AppHandle, title: String, body: String) -> Result<(), String> {
    Notification::new(&app.config().tauri.bundle.identifier)
        .title(&title)
        .body(&body)
        .show()
        .map_err(|e| e.to_string())
}
```

```typescript
import { sendNotification, isPermissionGranted, requestPermission } from '@tauri-apps/plugin-notification';

async function notify(title: string, body: string) {
  let permitted = await isPermissionGranted();
  if (!permitted) {
    const permission = await requestPermission();
    permitted = permission === 'granted';
  }
  if (permitted) {
    sendNotification({ title, body });
  }
}
```

---

## Security

### General Security Principles

1. **Principle of Least Privilege**: Only request the minimum permissions needed
2. **Defense in Depth**: Layer multiple security controls
3. **Input Validation**: Validate all inputs at every boundary
4. **Secure Defaults**: Default configurations should be secure
5. **No Trust Boundaries**: Never trust data from the renderer process

### Electron Security Checklist

- [ ] `contextIsolation: true` (default since Electron 12)
- [ ] `nodeIntegration: false`
- [ ] `sandbox: true`
- [ ] No use of `remote` module
- [ ] `webSecurity: true`
- [ ] Content Security Policy configured
- [ ] Preload scripts only expose necessary APIs
- [ ] IPC channel names follow convention
- [ ] All IPC inputs validated
- [ ] No `allowRunningInsecureContent: true`
- [ ] No `enableRemoteModule: true`

### Tauri Security Checklist

- [ ] Commands have explicit permission scopes
- [ ] Capability files define minimum required permissions
- [ ] No `allow-all` permissions in production
- [ ] File system access scoped to specific directories
- [ ] HTTP requests restricted to allowed origins
- [ ] Shell command execution restricted
- [ ] Update signatures verified

### Flutter Desktop Security Checklist

- [ ] Platform channels validate all method call arguments
- [ ] Sensitive data not passed through platform channels in plaintext
- [ ] File access scoped to app directories
- [ ] Network requests use HTTPS
- [ ] Secure storage for credentials (flutter_secure_storage)

---

## 相关参考

- [Electron Security Best Practices](electron-security.md) — Electron安全配置详解：contextIsolation、sandbox、CSP、IPC验证等
- [Tauri Development Guidelines](tauri-dev-guidelines.md) — Tauri安全模型、权限系统、能力范围与自动更新
