# Tauri Development Guidelines
> 版本: 1.9.0 | 更新日期: 2026-04-28 | 编码: UTF-8 | 行尾: LF

## 目录

- [Tauri Security Model](#tauri-security-model)
- [Command Permissions](#command-permissions)
- [Capability Scope](#capability-scope)
- [IPC Patterns](#ipc-patterns)
- [Plugin System](#plugin-system)
- [Auto-Updater](#auto-updater)
- [Sidecar](#sidecar)

---

## Tauri Security Model

Tauri's security model is built on three core principles:

1. **Principle of Least Privilege**: Apps only have access to the APIs they explicitly request
2. **Capability-Based Security**: Permissions are grouped into capabilities assigned to windows
3. **Sandboxed WebView**: The frontend runs in a system WebView with no direct system access

### Architecture Overview

```
┌─────────────────────────────────────────────┐
│               Frontend (WebView)             │
│  ┌─────────────────────────────────────────┐ │
│  │  JavaScript / TypeScript                │ │
│  │  - invoke() for commands                │ │
│  │  - listen() for events                  │ │
│  │  - No direct filesystem/network access  │ │
│  └─────────────────────────────────────────┘ │
│                      │ IPC Bridge             │
├──────────────────────┼───────────────────────┤
│                      ▼                        │
│  ┌─────────────────────────────────────────┐ │
│  │         Rust Backend (Core)             │ │
│  │  - Command handlers                     │ │
│  │  - Plugin system                        │ │
│  │  - System API access (scoped)           │ │
│  │  - Permission enforcement               │ │
│  └─────────────────────────────────────────┘ │
│                      │                        │
│  ┌─────────────────────────────────────────┐ │
│  │         OS-Level Sandbox                │ │
│  │  - WebView sandbox                      │ │
│  │  - Filesystem scope                     │ │
│  │  - Network scope                        │ │
│  └─────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

### Security Configuration Files

```
src-tauri/
├── capabilities/          # Window capability definitions
│   ├── default.json       # Default window capabilities
│   └── main-window.json   # Main window specific capabilities
├── permissions/           # Custom permission definitions
│   └── my-plugin.md       # Plugin permission docs
├── tauri.conf.json        # Main Tauri configuration
└── Cargo.toml             # Rust dependencies
```

---

## Command Permissions

### Defining Commands with Permissions

Every Tauri command should have explicit permission requirements. Commands without permissions are accessible to all windows by default.

```rust
use tauri::command;

#[command]
pub fn get_app_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}

#[command]
pub async fn read_user_file(path: String) -> Result<String, String> {
    let allowed_dir = dirs::home_dir()
        .ok_or("Cannot find home directory")?
        .join(".myapp/data");

    let resolved = std::path::Path::new(&path)
        .canonicalize()
        .map_err(|e| e.to_string())?;

    if !resolved.starts_with(&allowed_dir) {
        return Err("Access denied: path outside allowed directory".into());
    }

    tokio::fs::read_to_string(&resolved)
        .await
        .map_err(|e| e.to_string())
}

#[command]
pub async fn write_user_file(path: String, content: String) -> Result<(), String> {
    if content.len() > 10 * 1024 * 1024 {
        return Err("Content exceeds maximum size (10MB)".into());
    }

    let allowed_dir = dirs::home_dir()
        .ok_or("Cannot find home directory")?
        .join(".myapp/data");

    let resolved = std::path::Path::new(&path)
        .canonicalize()
        .map_err(|e| e.to_string())?;

    if !resolved.starts_with(&allowed_dir) {
        return Err("Access denied: path outside allowed directory".into());
    }

    tokio::fs::write(&resolved, content)
        .await
        .map_err(|e| e.to_string())
}
```

### Registering Commands

```rust
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            get_app_version,
            read_user_file,
            write_user_file,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Permission Validation in Commands

```rust
use tauri::{command, AppHandle, Runtime};

#[command]
pub async fn delete_file<R: Runtime>(
    app: AppHandle<R>,
    path: String,
) -> Result<(), String> {
    if !app.config().plugins.exists("fs") {
        return Err("File system plugin not available".into());
    }

    let allowed_dir = app.path_resolver()
        .app_data_dir()
        .ok_or("Cannot resolve app data directory")?;

    let resolved = std::path::Path::new(&path)
        .canonicalize()
        .map_err(|e| e.to_string())?;

    if !resolved.starts_with(&allowed_dir) {
        return Err("Access denied: path outside app data directory".into());
    }

    if !resolved.exists() {
        return Err("File not found".into());
    }

    tokio::fs::remove_file(&resolved)
        .await
        .map_err(|e| e.to_string())
}
```

---

## Capability Scope

Capabilities define what permissions are available to specific windows. This is Tauri's primary access control mechanism.

### Capability File Structure

```json
// src-tauri/capabilities/default.json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Default capabilities for the main window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "core:window:default",
    "core:window:allow-close",
    "core:window:allow-set-title",
    "core:window:allow-minimize",
    "core:window:allow-maximize",
    "core:window:allow-unmaximize",
    "shell:allow-open",
    "dialog:default",
    "dialog:allow-open",
    "dialog:allow-save",
    "fs:default",
    "fs:allow-read-text-file",
    "fs:allow-write-text-file",
    {
      "identifier": "fs:scope",
      "allow": [
        { "path": "$APPDATA/**" },
        { "path": "$HOME/.myapp/**" }
      ]
    },
    "notification:default",
    "notification:allow-notify",
    "updater:default"
  ]
}
```

### Multiple Capability Files

```json
// src-tauri/capabilities/main-window.json
{
  "identifier": "main-window",
  "description": "Capabilities for the main application window",
  "windows": ["main"],
  "permissions": [
    "core:default",
    "core:window:default",
    "fs:default",
    "dialog:default",
    "shell:allow-open"
  ]
}
```

```json
// src-tauri/capabilities/settings-window.json
{
  "identifier": "settings-window",
  "description": "Restricted capabilities for settings window",
  "windows": ["settings"],
  "permissions": [
    "core:default",
    "core:window:default",
    "core:window:allow-close",
    "fs:allow-read-text-file",
    "notification:allow-notify"
  ]
}
```

### Scoped File System Access

```json
{
  "identifier": "fs:scope",
  "allow": [
    { "path": "$APPDATA/config/**" },
    { "path": "$APPDATA/data/**" },
    { "path": "$DOWNLOAD/**" }
  ],
  "deny": [
    { "path": "$APPDATA/config/secrets.json" },
    { "path": "$APPDATA/**/*.key" }
  ]
}
```

### Scoped HTTP Access

```json
{
  "identifier": "http:scope",
  "allow": [
    { "url": "https://api.example.com/**" },
    { "url": "https://cdn.example.com/**" }
  ],
  "deny": [
    { "url": "https://api.example.com/admin/**" }
  ]
}
```

### Scoped Shell Access

```json
{
  "identifier": "shell:scope",
  "allow": [
    {
      "name": "open-logs",
      "cmd": "open",
      "args": ["$APPDATA/logs"]
    }
  ]
}
```

---

## IPC Patterns

### Command Pattern (Request-Response)

```rust
use serde::{Deserialize, Serialize};
use tauri::command;

#[derive(Debug, Deserialize)]
pub struct SearchRequest {
    pub query: String,
    pub limit: Option<usize>,
    pub offset: Option<usize>,
}

#[derive(Debug, Serialize)]
pub struct SearchResponse {
    pub success: bool,
    pub results: Vec<SearchResult>,
    pub total: usize,
    pub error: Option<String>,
}

#[derive(Debug, Serialize)]
pub struct SearchResult {
    pub id: String,
    pub title: String,
    pub snippet: String,
}

#[command]
pub async fn search_items(request: SearchRequest) -> SearchResponse {
    let limit = request.limit.unwrap_or(20).min(100);
    let offset = request.offset.unwrap_or(0);

    if request.query.is_empty() {
        return SearchResponse {
            success: false,
            results: vec![],
            total: 0,
            error: Some("Query cannot be empty".into()),
        };
    }

    match perform_search(&request.query, limit, offset).await {
        Ok((results, total)) => SearchResponse {
            success: true,
            results,
            total,
            error: None,
        },
        Err(err) => SearchResponse {
            success: false,
            results: vec![],
            total: 0,
            error: Some(err.to_string()),
        },
    }
}
```

```typescript
import { invoke } from '@tauri-apps/api/core';

interface SearchRequest {
  query: string;
  limit?: number;
  offset?: number;
}

interface SearchResponse {
  success: boolean;
  results: SearchResult[];
  total: number;
  error?: string;
}

async function search(request: SearchRequest): Promise<SearchResponse> {
  return invoke<SearchResponse>('search_items', { request });
}
```

### Event Pattern (Push)

```rust
use tauri::Manager;

#[derive(Clone, Serialize)]
struct ProgressPayload {
    percent: f64,
    message: String,
}

fn emit_progress(app: &tauri::AppHandle, percent: f64, message: &str) {
    let _ = app.emit("task:progress", ProgressPayload {
        percent,
        message: message.to_string(),
    });
}

#[command]
async fn start_task(app: tauri::AppHandle) -> Result<(), String> {
    for i in 0..=100 {
        tokio::time::sleep(std::time::Duration::from_millis(50)).await;
        emit_progress(&app, i as f64, &format!("Processing... {}%", i));
    }
    Ok(())
}
```

```typescript
import { listen } from '@tauri-apps/api/event';

interface ProgressPayload {
  percent: number;
  message: string;
}

const unlisten = await listen<ProgressPayload>('task:progress', (event) => {
  console.log(`${event.payload.message}: ${event.payload.percent}%`);
  updateProgressBar(event.payload.percent);
});

unlisten();
```

### State Management

```rust
use std::sync::Mutex;
use tauri::State;

pub struct AppState {
    pub config: Mutex<AppConfig>,
    pub cache: Mutex<lru::LruCache<String, String>>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct AppConfig {
    pub theme: String,
    pub language: String,
    pub auto_update: bool,
}

impl Default for AppConfig {
    fn default() -> Self {
        Self {
            theme: "system".into(),
            language: "en".into(),
            auto_update: true,
        }
    }
}

#[command]
pub fn get_config(state: State<'_, AppState>) -> Result<AppConfig, String> {
    state.config.lock().map_err(|e| e.to_string()).map(|c| c.clone())
}

#[command]
pub fn set_config(state: State<'_, AppState>, config: AppConfig) -> Result<(), String> {
    let mut current = state.config.lock().map_err(|e| e.to_string())?;
    *current = config;
    Ok(())
}

fn main() {
    tauri::Builder::default()
        .manage(AppState {
            config: Mutex::new(AppConfig::default()),
            cache: Mutex::new(lru::LruCache::new(256)),
        })
        .invoke_handler(tauri::generate_handler![get_config, set_config])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

---

## Plugin System

### Using Official Plugins

```toml
# Cargo.toml
[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-shell = "2"
tauri-plugin-dialog = "2"
tauri-plugin-fs = "2"
tauri-plugin-http = "2"
tauri-plugin-notification = "2"
tauri-plugin-updater = "2"
tauri-plugin-process = "2"
tauri-plugin-os = "2"
tauri-plugin-clipboard-manager = "2"
tauri-plugin-global-shortcut = "2"
tauri-plugin-autostart = "2"
tauri-plugin-log = "2"
tauri-plugin-store = "2"
```

```rust
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_notification::init())
        .plugin(tauri_plugin_updater::Builder::new().build())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_os::init())
        .plugin(tauri_plugin_clipboard_manager::init())
        .plugin(tauri_plugin_global_shortcut::Builder::new().build())
        .plugin(tauri_plugin_autostart::init(
            tauri_plugin_autostart::MacosLauncher::LaunchAgent,
            None,
        ))
        .plugin(tauri_plugin_log::Builder::new().build())
        .plugin(tauri_plugin_store::Builder::new().build())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Creating a Custom Plugin

```rust
// src-tauri/src/plugins/my_plugin.rs
use tauri::{
    plugin::{Builder, TauriPlugin},
    AppHandle, Runtime,
};

#[tauri::command]
async fn my_plugin_command(app: AppHandle<impl Runtime>, name: String) -> Result<String, String> {
    Ok(format!("Hello, {}!", name))
}

pub fn init<R: Runtime>() -> TauriPlugin<R> {
    Builder::new("my-plugin")
        .invoke_handler(tauri::generate_handler![my_plugin_command])
        .build()
}
```

```rust
// src-tauri/src/main.rs
mod plugins;

fn main() {
    tauri::Builder::default()
        .plugin(plugins::my_plugin::init())
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Plugin Permissions

```json
// src-tauri/permissions/my-plugin/default.json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "my-plugin:default",
  "description": "Default permissions for my-plugin",
  "windows": ["main"],
  "permissions": [
    "my-plugin:allow-my-plugin-command"
  ]
}
```

---

## Auto-Updater

### Configuration

```json
// src-tauri/tauri.conf.json
{
  "plugins": {
    "updater": {
      "endpoints": [
        "https://updates.example.com/{{target}}/{{arch}}/{{current_version}}"
      ],
      "pubkey": "PUBLIC_KEY_BASE64_HERE"
    }
  }
}
```

### Generating Update Keys

```bash
# Generate keypair
cargo tauri signer generate -w ~/.tauri/myapp.key

# This outputs:
# - Public key (add to tauri.conf.json)
# - Private key (set as TAURI_SIGNING_PRIVATE_KEY env var)
```

### Update Server Response Format

```json
{
  "version": "1.2.0",
  "date": "2024-01-15T10:00:00Z",
  "notes": "## What's New\n- Feature A\n- Feature B\n\n## Bug Fixes\n- Fix C",
  "platforms": {
    "windows-x86_64": {
      "url": "https://updates.example.com/windows/x86_64/MyApp-1.2.0.msi",
      "signature": "SIGNATURE_BASE64"
    },
    "darwin-x86_64": {
      "url": "https://updates.example.com/darwin/x86_64/MyApp-1.2.0.app.tar.gz",
      "signature": "SIGNATURE_BASE64"
    },
    "darwin-aarch64": {
      "url": "https://updates.example.com/darwin/aarch64/MyApp-1.2.0.app.tar.gz",
      "signature": "SIGNATURE_BASE64"
    },
    "linux-x86_64": {
      "url": "https://updates.example.com/linux/x86_64/MyApp-1.2.0.AppImage.tar.gz",
      "signature": "SIGNATURE_BASE64"
    }
  }
}
```

### Frontend Update Flow

```typescript
import { check } from '@tauri-apps/plugin-updater';
import { relaunch } from '@tauri-apps/plugin-process';

async function checkForUpdates() {
  const update = await check();

  if (!update) {
    console.log('App is up to date');
    return;
  }

  console.log(`Update available: ${update.version}`);
  console.log(`Current version: ${update.currentVersion}`);

  let downloaded = 0;
  let contentLength = 0;

  await update.downloadAndInstall((event) => {
    switch (event.event) {
      case 'Started':
        contentLength = event.data.contentLength || 0;
        console.log(`Download started: ${contentLength} bytes`);
        break;
      case 'Progress':
        downloaded += event.data.chunkLength;
        const percent = contentLength > 0 ? (downloaded / contentLength * 100).toFixed(1) : '?';
        console.log(`Downloaded: ${percent}%`);
        break;
      case 'Finished':
        console.log('Download finished');
        break;
    }
  });

  console.log('Update installed, restarting...');
  await relaunch();
}
```

### Rust-Side Update Check

```rust
use tauri_plugin_updater::UpdaterExt;

#[command]
async fn check_update(app: tauri::AppHandle) -> Result<Option<UpdateInfo>, String> {
    let updater = app.updater().map_err(|e| e.to_string())?;
    let update = updater.check().await.map_err(|e| e.to_string())?;

    match update {
        Some(update) => Ok(Some(UpdateInfo {
            version: update.version.clone(),
            current_version: update.current_version.clone(),
            date: update.date.map(|d| d.to_string()),
            body: update.body.clone(),
        })),
        None => Ok(None),
    }
}

#[derive(Serialize)]
struct UpdateInfo {
    version: String,
    current_version: String,
    date: Option<String>,
    body: Option<String>,
}
```

---

## Sidecar

Sidecar allows bundling and executing external binaries alongside your Tauri application.

### Configuration

```json
// src-tauri/tauri.conf.json
{
  "bundle": {
    "externalBin": [
      "binaries/my-tool"
    ]
  }
}
```

### Binary Naming Convention

Tauri requires platform-specific binary names:

```
src-tauri/binaries/
├── my-tool-x86_64-pc-windows-msvc.exe    # Windows x64
├── my-tool-x86_64-unknown-linux-gnu      # Linux x64
├── my-tool-aarch64-unknown-linux-gnu     # Linux ARM64
├── my-tool-x86_64-apple-darwin           # macOS x64
└── my-tool-aarch64-apple-darwin          # macOS ARM64
```

### Running Sidecar from Rust

```rust
use tauri::Manager;
use tauri_plugin_shell::ShellExt;

#[command]
async fn run_sidecar(app: tauri::AppHandle, args: Vec<String>) -> Result<(), String> {
    let sidecar_command = app
        .shell()
        .sidecar("my-tool")
        .map_err(|e| e.to_string())?
        .args(&args);

    let (mut rx, mut child) = sidecar_command.spawn()
        .map_err(|e| e.to_string())?;

    tauri::async_runtime::spawn(async move {
        while let Some(event) = rx.recv().await {
            match event {
                tauri_plugin_shell::process::CommandEvent::Stdout(line) => {
                    println!("Sidecar stdout: {}", String::from_utf8_lossy(&line));
                }
                tauri_plugin_shell::process::CommandEvent::Stderr(line) => {
                    eprintln!("Sidecar stderr: {}", String::from_utf8_lossy(&line));
                }
                tauri_plugin_shell::process::CommandEvent::Terminated(status) => {
                    println!("Sidecar exited: {:?}", status);
                }
                _ => {}
            }
        }
    });

    Ok(())
}
```

### Running Sidecar from Frontend

```typescript
import { Command } from '@tauri-apps/plugin-shell';

async function runSidecar(args: string[]) {
  const command = Command.sidecar('my-tool', args);
  const child = await command.spawn();

  command.stdout.on('data', (line) => {
    console.log('stdout:', line);
  });

  command.stderr.on('data', (line) => {
    console.error('stderr:', line);
  });

  const exitCode = await child.status;
  console.log('Exit code:', exitCode);
}
```

### Sidecar Security

```json
// src-tauri/capabilities/default.json
{
  "permissions": [
    {
      "identifier": "shell:allow-spawn",
      "allow": [
        {
          "name": "my-tool",
          "cmd": "my-tool",
          "args": true
        }
      ]
    },
    "shell:allow-stdin-write"
  ]
}
```

### Sidecar Build Script

```rust
// src-tauri/build.rs
fn main() {
    tauri_build::build();

    // Download or build sidecar binary
    #[cfg(target_os = "windows")]
    let target = "x86_64-pc-windows-msvc";
    #[cfg(target_os = "macos")]
    let target = if cfg!(target_arch = "aarch64") {
        "aarch64-apple-darwin"
    } else {
        "x86_64-apple-darwin"
    };
    #[cfg(target_os = "linux")]
    let target = "x86_64-unknown-linux-gnu";

    let bin_path = format!("binaries/my-tool-{}", target);
    if !std::path::Path::new(&bin_path).exists() {
        println!("cargo:warning=Sidecar binary not found: {}", bin_path);
    }
}
```

---

## 相关参考

- [Desktop Development Guidelines](desktop-dev-guidelines.md) — 桌面端开发通用指南：项目结构、IPC模式、窗口管理、系统托盘等
- [Electron Security Best Practices](electron-security.md) — Electron安全配置详解：contextIsolation、sandbox、CSP、IPC验证等
