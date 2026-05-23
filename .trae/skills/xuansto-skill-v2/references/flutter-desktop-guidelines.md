# Flutter Desktop Development Guidelines
> 版本: 1.9.1 | 更新日期: 2026-05-03 | 编码: UTF-8 | 行尾: LF

## 目录

- [Window Management](#window-management)
- [Platform Channels](#platform-channels)
- [Plugin Development for Desktop](#plugin-development-for-desktop)
- [Build Configuration](#build-configuration)
- [Desktop-Specific UI Patterns](#desktop-specific-ui-patterns)
- [Security Considerations](#security-considerations)

---

## Window Management

### 基础窗口配置

使用 `window_manager` 包管理桌面窗口：

```yaml
# pubspec.yaml
dependencies:
  window_manager: ^0.4.0
```

```dart
import 'package:window_manager/window_manager.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await windowManager.ensureInitialized();

  WindowOptions windowOptions = const WindowOptions(
    size: Size(1200, 800),
    minimumSize: Size(800, 600),
    center: true,
    backgroundColor: Colors.transparent,
    skipTaskbar: false,
    titleBarStyle: TitleBarStyle.normal,
    title: 'My Application',
  );

  windowManager.waitUntilReadyToShow(windowOptions, () async {
    await windowManager.show();
    await windowManager.focus();
  });

  runApp(const MyApp());
}
```

### 窗口大小与位置持久化

```dart
class WindowStateService {
  static const _prefsKey = 'window_state';
  static const _sizeKey = 'window_size';
  static const _positionKey = 'window_position';
  static const _maximizedKey = 'window_maximized';

  Future<void> saveWindowState() async {
    final prefs = await SharedPreferences.getInstance();
    final size = await windowManager.getSize();
    final position = await windowManager.getPosition();
    final isMaximized = await windowManager.isMaximized();

    await prefs.setDouble('${_sizeKey}_w', size.width);
    await prefs.setDouble('${_sizeKey}_h', size.height);
    await prefs.setDouble('${_positionKey}_x', position.dx);
    await prefs.setDouble('${_positionKey}_y', position.dy);
    await prefs.setBool(_maximizedKey, isMaximized);
  }

  Future<void> restoreWindowState() async {
    final prefs = await SharedPreferences.getInstance();
    final width = prefs.getDouble('${_sizeKey}_w') ?? 1200;
    final height = prefs.getDouble('${_sizeKey}_h') ?? 800;
    final x = prefs.getDouble('${_positionKey}_x');
    final y = prefs.getDouble('${_positionKey}_y');
    final isMaximized = prefs.getBool(_maximizedKey) ?? false;

    await windowManager.setSize(Size(width, height));
    if (x != null && y != null) {
      await windowManager.setPosition(Offset(x, y));
    }
    if (isMaximized) {
      await windowManager.maximize();
    }
  }
}
```

### 窗口关闭确认

```dart
class AppWindowListener with WindowListener {
  @override
  void onWindowClose() async {
    bool isPreventClose = await windowManager.isPreventClose();
    if (isPreventClose) {
      final shouldClose = await _showCloseConfirmDialog();
      if (shouldClose) {
        await windowManager.destroy();
      }
    }
  }

  Future<bool> _showCloseConfirmDialog() async {
    final result = await showDialog<bool>(
      context: navigatorKey.currentContext!,
      builder: (context) => AlertDialog(
        title: const Text('确认退出'),
        content: const Text('有未保存的工作，确定要退出吗？'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('退出'),
          ),
        ],
      ),
    );
    return result ?? false;
  }

  void init() {
    windowManager.addListener(this);
    windowManager.setPreventClose(true);
  }

  void dispose() {
    windowManager.removeListener(this);
  }
}
```

### 自定义标题栏

```dart
WindowOptions windowOptions = const WindowOptions(
  titleBarStyle: TitleBarStyle.hidden,
);

// 自定义标题栏组件
class CustomTitleBar extends StatelessWidget {
  final Widget child;

  const CustomTitleBar({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.translucent,
      onPanStart: (_) => windowManager.startDragging(),
      child: Column(
        children: [
          Container(
            height: 32,
            child: Row(
              children: [
                Expanded(child: DragToMoveArea(
                  child: Container(
                    padding: EdgeInsets.only(left: 16),
                    alignment: Alignment.centerLeft,
                    child: Text('My Application', style: TextStyle(fontSize: 13)),
                  ),
                )),
                WindowCaptionButton.minimize(onPressed: windowManager.minimize),
                WindowCaptionButton.maximize(onPressed: windowManager.maximize),
                WindowCaptionButton.close(onPressed: () async {
                  bool isPreventClose = await windowManager.isPreventClose();
                  if (!isPreventClose) {
                    windowManager.close();
                  }
                }),
              ],
            ),
          ),
          Expanded(child: child),
        ],
      ),
    );
  }
}
```

---

## Platform Channels

### MethodChannel

用于一次性调用，如获取系统信息、打开原生对话框：

```dart
class PlatformService {
  static const _channel = MethodChannel('com.example.app/platform');

  Future<String> getPlatformVersion() async {
    try {
      return await _channel.invokeMethod('getPlatformVersion');
    } on PlatformException catch (e) {
      throw PlatformException(
        code: e.code,
        message: e.message ?? 'Unknown error',
      );
    }
  }

  Future<String?> openFileDialog(FileDialogFilter filter) async {
    try {
      return await _channel.invokeMethod('openFileDialog', {
        'filter': filter.toJson(),
      });
    } on PlatformException catch (e) {
      if (e.code == 'CANCELLED') return null;
      rethrow;
    }
  }

  Future<bool> setAutoStart(bool enable) async {
    try {
      return await _channel.invokeMethod('setAutoStart', {'enable': enable});
    } on PlatformException catch (e) {
      throw PlatformException(code: e.code, message: e.message ?? '');
    }
  }
}
```

**Windows原生端 (C++)**:

```cpp
// windows/runner/platform_channel.cpp
#include <flutter/method_channel.h>
#include <flutter/standard_method_codec.h>

void RegisterPlatformChannel(flutter::FlutterEngine* engine) {
  const static char* channel_name = "com.example.app/platform";

  flutter::MethodChannel<> channel(
    engine->messenger(), channel_name,
    &flutter::StandardMethodCodec::GetInstance());

  channel.SetMethodCallHandler(
    [](const flutter::MethodCall<>& call,
       std::unique_ptr<flutter::MethodResult<>> result) {
      if (call.method_name() == "getPlatformVersion") {
        result->Success("Windows " + GetWindowsVersion());
      } else if (call.method_name() == "openFileDialog") {
        auto* arguments = std::get_if<flutter::EncodableMap>(call.arguments());
        auto file_path = OpenFileDialog(arguments);
        if (file_path.has_value()) {
          result->Success(file_path.value());
        } else {
          result->Success(nullptr);
        }
      } else if (call.method_name() == "setAutoStart") {
        auto* arguments = std::get_if<flutter::EncodableMap>(call.arguments());
        bool enable = std::get<bool>(arguments->at(flutter::EncodableValue("enable")));
        SetAutoStart(enable);
        result->Success(true);
      } else {
        result->NotImplemented();
      }
    });
}
```

**macOS原生端 (Swift)**:

```swift
// macos/Runner/PlatformChannelHandler.swift
import FlutterMacOS

class PlatformChannelHandler: NSObject, FlutterPlugin {
  static func register(with registrar: FlutterPluginRegistrar) {
    let channel = FlutterMethodChannel(
      name: "com.example.app/platform",
      binaryMessenger: registrar.messenger)
    let instance = PlatformChannelHandler()
    registrar.addMethodCallDelegate(instance, channel: channel)
  }

  func handle(_ call: FlutterMethodCall, result: @escaping FlutterResult) {
    switch call.method {
    case "getPlatformVersion":
      let version = ProcessInfo.processInfo.operatingSystemVersion
      result("macOS \(version.majorVersion).\(version.minorVersion).\(version.patchVersion)")
    case "openFileDialog":
      guard let args = call.arguments as? [String: Any] else {
        result(FlutterError(code: "INVALID_ARGS", message: "Invalid arguments", details: nil))
        return
      }
      let panel = NSOpenPanel()
      panel.canChooseFiles = true
      panel.canChooseDirectories = false
      panel.allowsMultipleSelection = false
      if panel.runModal() == .OK, let url = panel.url {
        result(url.path)
      } else {
        result(nil)
      }
    case "setAutoStart":
      guard let args = call.arguments as? [String: Any],
            let enable = args["enable"] as? Bool else {
        result(FlutterError(code: "INVALID_ARGS", message: "Invalid arguments", details: nil))
        return
      }
      setAutoStart(enable: enable)
      result(true)
    default:
      result(FlutterMethodNotImplemented)
    }
  }
}
```

**Linux原生端 (C)**:

```c
// linux/platform_channel.c
#include <flutter_linux/flutter_linux.h>

static void platform_channel_handler(FlMethodChannel* channel,
                                      FlMethodCall* method_call,
                                      gpointer user_data) {
  g_autoptr(FlMethodResponse) response = nullptr;

  if (strcmp(fl_method_call_get_name(method_call), "getPlatformVersion") == 0) {
    g_autofree gchar* version = get_linux_version();
    response = FL_METHOD_RESPONSE(fl_method_success_response_new(
        fl_value_new_string(version)));
  } else if (strcmp(fl_method_call_get_name(method_call), "openFileDialog") == 0) {
    gchar* file_path = show_open_file_dialog();
    if (file_path != nullptr) {
      response = FL_METHOD_RESPONSE(fl_method_success_response_new(
          fl_value_new_string(file_path)));
      g_free(file_path);
    } else {
      response = FL_METHOD_RESPONSE(fl_method_success_response_new(
          fl_value_new_null()));
    }
  } else {
    response = FL_METHOD_RESPONSE(fl_method_not_implemented_response_new());
  }

  fl_method_call_respond(method_call, response, nullptr);
}

void register_platform_channel(FlPluginRegistrar* registrar) {
  g_autoptr(FlStandardMethodCodec) codec = fl_standard_method_codec_new();
  g_autoptr(FlMethodChannel) channel = fl_method_channel_new(
      fl_plugin_registrar_get_messenger(registrar),
      "com.example.app/platform",
      FL_METHOD_CODEC(codec));
  fl_method_channel_set_method_call_handler(channel,
                                             platform_channel_handler,
                                             nullptr, nullptr);
}
```

### EventChannel

用于持续事件流，如文件系统监听、USB设备变化：

```dart
class DeviceEventService {
  static const _channel = EventChannel('com.example.app/device_events');

  Stream<DeviceEvent>? _eventStream;

  Stream<DeviceEvent> get onDeviceChanged {
    _eventStream ??= _channel.receiveBroadcastStream().map((event) {
      return DeviceEvent.fromJson(event as Map<String, dynamic>);
    });
    return _eventStream!;
  }
}
```

### BasicMessageChannel

用于双向消息传递：

```dart
class SyncChannel {
  static const _channel = BasicMessageChannel<String>(
    'com.example.app/sync',
    StringCodec(),
  );

  Future<String> sendMessage(String message) async {
    return await _channel.send(message) ?? '';
  }

  void listenMessages(ValueChanged<String> onMessage) {
    _channel.setMessageHandler((message) async {
      if (message != null) {
        onMessage(message);
      }
      return null;
    });
  }
}
```

### Platform Channel契约定义

```yaml
# platform-channel-contract.yaml
channel: com.example.app/platform
type: method
methods:
  getPlatformVersion:
    description: 获取操作系统版本
    input: {}
    output:
      type: String
      description: 操作系统版本字符串
    errors:
      - code: PLATFORM_ERROR
        message: 无法获取平台版本
  openFileDialog:
    description: 打开文件选择对话框
    input:
      filter:
        type: Map
        description: 文件过滤器
    output:
      type: String?
      description: 选择的文件路径，取消返回null
    errors:
      - code: CANCELLED
        message: 用户取消选择
      - code: INVALID_ARGS
        message: 参数无效
  setAutoStart:
    description: 设置开机自启动
    input:
      enable:
        type: bool
        description: 是否启用
    output:
      type: bool
      description: 是否设置成功
    errors:
      - code: PERMISSION_DENIED
        message: 权限不足
```

---

## Plugin Development for Desktop

### Federated Plugin架构

Flutter桌面插件推荐使用Federated Plugin模式：

```
my_plugin/
├── my_plugin/                    # 主包（Dart接口）
│   ├── lib/
│   │   ├── my_plugin.dart        # 公共API
│   │   ├── method_channel_my_plugin.dart  # MethodChannel实现
│   │   └── platform_interface/
│   │       └── my_plugin_platform.dart    # 平台接口
│   └── pubspec.yaml
├── my_plugin_windows/            # Windows平台实现
│   ├── lib/
│   │   └── my_plugin_windows.dart
│   ├── windows/
│   │   ├── include/
│   │   │   └── my_plugin_windows/
│   │   │       └── my_plugin_windows_plugin.h
│   │   └── my_plugin_windows_plugin.cpp
│   └── pubspec.yaml
├── my_plugin_macos/              # macOS平台实现
│   ├── lib/
│   │   └── my_plugin_macos.dart
│   ├── macos/
│   │   └── Classes/
│   │       └── MyPluginMacosPlugin.swift
│   └── pubspec.yaml
├── my_plugin_linux/              # Linux平台实现
│   ├── lib/
│   │   └── my_plugin_linux.dart
│   ├── linux/
│   │   └── my_plugin_linux_plugin.c
│   └── pubspec.yaml
└── my_plugin_platform_interface/ # 平台接口定义
    ├── lib/
    │   └── my_plugin_platform_interface.dart
    └── pubspec.yaml
```

### 平台接口定义

```dart
abstract class MyPluginPlatform extends PlatformInterface {
  MyPluginPlatform() : super(token: _token);

  static final Object _token = Object();
  static MyPluginPlatform _instance = MethodChannelMyPlugin();

  static MyPluginPlatform get instance => _instance;

  static set instance(MyPluginPlatform instance) {
    PlatformInterface.verify(instance, _token);
    _instance = instance;
  }

  Future<String?> getPlatformVersion() {
    throw UnimplementedError('getPlatformVersion() has not been implemented.');
  }
}
```

### FFI绑定（性能敏感场景）

```dart
import 'dart:ffi';
import 'package:ffi/ffi.dart';

typedef NativeCompute = Double Function(Double a, Double b);
typedef DartCompute = double Function(double a, double b);

class NativeComputeLib {
  late final DynamicLibrary _lib;
  late final DartCompute _compute;

  NativeComputeLib() {
    _lib = Platform.isWindows
        ? DynamicLibrary.open('native_compute.dll')
        : Platform.isMacOS
            ? DynamicLibrary.open('libnative_compute.dylib')
            : DynamicLibrary.open('libnative_compute.so');

    _compute = _lib
        .lookup<NativeFunction<NativeCompute>>('compute')
        .asFunction();
  }

  double compute(double a, double b) => _compute(a, b);
}
```

### 插件桌面平台桩（Stub）

对于不支持桌面的插件功能，需提供平台桩：

```dart
class MyPluginDesktopStub extends MyPluginPlatform {
  @override
  Future<String?> getPlatformVersion() async {
    throw UnsupportedError(
      'getPlatformVersion is not supported on this platform');
  }
}

void registerWith() {
  MyPluginPlatform.instance = MyPluginDesktopStub();
}
```

---

## Build Configuration

### flutter build命令

```bash
# Windows
flutter build windows --release
flutter build windows --profile
flutter build windows --debug

# macOS
flutter build macos --release
flutter build macos --profile
flutter build macos --debug

# Linux
flutter build linux --release
flutter build linux --profile
flutter build linux --debug
```

### 构建产物路径

| 平台 | Release产物路径 | 产物格式 |
|------|----------------|----------|
| Windows | `build/windows/x64/runner/Release/` | `.exe` |
| macOS | `build/macos/Build/Products/Release/` | `.app` |
| Linux | `build/linux/x64/release/bundle/` | 可执行文件 |

### Windows平台配置

#### MSIX打包

```yaml
# pubspec.yaml
msix_config:
  display_name: My Application
  publisher_display_name: Example Corp
  identity_name: com.example.myapp
  msix_version: 1.0.0.0
  logo_path: assets/logo.png
  capabilities: internetClient, documentsLibrary
  certificate_path: certs/myapp.pfx
  certificate_password: ${WINDOWS_CERT_PASSWORD}
  publisher: CN=Example Corp, O=Example Corp, L=City, S=State, C=US
  store: false
  install_mode: perUser
```

```bash
flutter pub run msix:create
flutter pub run msix:create --store
flutter pub run msix:sign
```

#### Inno Setup打包

```iss
; installer.iss
[Setup]
AppName=My Application
AppVersion=1.0.0
AppPublisher=Example Corp
DefaultDirName={autopf}\MyApp
DefaultGroupName=My Application
OutputBaseFilename=MyApp-Setup-1.0.0
Compression=lzma2
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Files]
Source: "build\windows\x64\runner\Release\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\My Application"; Filename: "{app}\my_app.exe"
Name: "{autodesktop}\My Application"; Filename: "{app}\my_app.exe"

[Run]
Filename: "{app}\my_app.exe"; Description: "Launch My Application"; Flags: nowait postinstall skipifsilent
```

### macOS平台配置

#### Info.plist关键配置

```xml
<!-- macos/Runner/Info.plist -->
<dict>
    <key>CFBundleName</key>
    <string>My Application</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.myapp</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-only</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
</dict>
```

#### DMG打包

```bash
# 使用create-dmg
create-dmg \
  --volname "My Application" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "My Application.app" 175 190 \
  --app-drop-link 425 190 \
  "MyApp-1.0.0.dmg" \
  "build/macos/Build/Products/Release/My Application.app"
```

#### App Store准备

```bash
# 签名
codesign --deep --force --verify --verbose \
  --sign "Developer ID Application: Example Corp (TEAMID)" \
  --options runtime \
  "My Application.app"

# 公证
xcrun notarytool submit "MyApp-1.0.0.dmg" \
  --apple-id "dev@example.com" \
  --password "@keychain:AC_PASSWORD" \
  --team-id "TEAMID" \
  --wait

# 装订
xcrun stapler staple "My Application.app"
```

### Linux平台配置

#### deb包

```bash
# 目录结构
myapp_1.0.0_amd64/
├── DEBIAN/
│   ├── control
│   └── postinst
├── usr/
│   ├── bin/
│   │   └── myapp
│   ├── lib/
│   │   └── myapp/
│   │       └── (flutter bundle files)
│   └── share/
│       ├── applications/
│       │   └── myapp.desktop
│       └── icons/
│           └── hicolor/
│               └── 256x256/
│                   └── apps/
│                       └── myapp.png

# DEBIAN/control
Package: myapp
Version: 1.0.0
Architecture: amd64
Maintainer: Example Corp <dev@example.com>
Description: My Application
 A cross-platform desktop application built with Flutter
Depends: libgtk-3-0, libblkid1, liblzma5
```

```bash
dpkg-deb --build myapp_1.0.0_amd64
```

#### rpm包

```spec
Name:           myapp
Version:        1.0.0
Release:        1%{?dist}
Summary:        My Application
License:        Proprietary
URL:            https://example.com

Requires:       gtk3, libblkid, xz-libs

%description
A cross-platform desktop application built with Flutter

%install
mkdir -p %{buildroot}/usr/lib/myapp
cp -r bundle/* %{buildroot}/usr/lib/myapp/
mkdir -p %{buildroot}/usr/bin
ln -s /usr/lib/myapp/myapp %{buildroot}/usr/bin/myapp

%files
/usr/bin/myapp
/usr/lib/myapp/*
```

#### AppImage

```bash
# 使用appimage-builder
appimage-builder --recipe AppImageBuilder.yml
```

```yaml
# AppImageBuilder.yml
version: 1
AppDir:
  path: ./AppDir
  app_info:
    id: com.example.myapp
    name: My Application
    icon: myapp
    version: 1.0.0
    exec: usr/lib/myapp/myapp
  files:
    include:
      - usr/lib/myapp/**
      - usr/bin/myapp
AppImage:
  arch: x86_64
  update-information: gh-releases-zsync|example|myapp|latest|MyApp-*x86_64.AppImage.zsync
```

---

## Desktop-Specific UI Patterns

### 响应式布局

```dart
class ResponsiveLayout extends StatelessWidget {
  final Widget mobile;
  final Widget tablet;
  final Widget desktop;

  const ResponsiveLayout({
    super.key,
    required this.mobile,
    required this.tablet,
    required this.desktop,
  });

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 1200) {
          return desktop;
        } else if (constraints.maxWidth >= 800) {
          return tablet;
        } else {
          return mobile;
        }
      },
    );
  }
}
```

### 键盘快捷键

```dart
class KeyboardShortcuts extends StatelessWidget {
  final Widget child;

  const KeyboardShortcuts({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return Shortcuts(
      shortcuts: <LogicalKeySet, Intent>{
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyS):
            const SaveIntent(),
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyN):
            const NewIntent(),
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyO):
            const OpenIntent(),
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyW):
            const CloseIntent(),
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyQ):
            const QuitIntent(),
      },
      child: Actions(
        actions: <Type, Action<Intent>>{
          SaveIntent: CallbackAction<SaveIntent>(
            onInvoke: (intent) => _handleSave(context),
          ),
          NewIntent: CallbackAction<NewIntent>(
            onInvoke: (intent) => _handleNew(context),
          ),
          OpenIntent: CallbackAction<OpenIntent>(
            onInvoke: (intent) => _handleOpen(context),
          ),
          CloseIntent: CallbackAction<CloseIntent>(
            onInvoke: (intent) => _handleClose(context),
          ),
          QuitIntent: CallbackAction<QuitIntent>(
            onInvoke: (intent) => _handleQuit(context),
          ),
        },
        child: child,
      ),
    );
  }
}
```

### 平台感知快捷键

```dart
class PlatformShortcuts {
  static bool get isApple => Platform.isMacOS;

  static String get modKey => isApple ? '⌘' : 'Ctrl';

  static LogicalKeyboardKey get mod =>
      isApple ? LogicalKeyboardKey.meta : LogicalKeyboardKey.control;

  static String formatShortcut(String action) {
    switch (action) {
      case 'save': return '$modKey+S';
      case 'open': return '$modKey+O';
      case 'new': return '$modKey+N';
      case 'undo': return '$modKey+Z';
      case 'redo': return isApple ? '$modKey+Shift+Z' : 'Ctrl+Y';
      default: return action;
    }
  }
}
```

### 右键上下文菜单

```dart
class ContextMenuRegion extends StatelessWidget {
  final Widget child;
  final List<PopupMenuEntry<String>> menuItems;
  final ValueChanged<String>? onSelected;

  const ContextMenuRegion({
    super.key,
    required this.child,
    required this.menuItems,
    this.onSelected,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onSecondaryTapDown: (details) {
        final overlay = Overlay.of(context).context.findRenderObject() as RenderBox;
        final position = RelativeRect.fromRects(
          Rect.fromPoints(
            details.globalPosition,
            details.globalPosition,
          ),
          Offset.zero & overlay.size,
        );
        showMenu<String>(
          context: context,
          position: position,
          items: menuItems,
        ).then((value) {
          if (value != null) {
            onSelected?.call(value);
          }
        });
      },
      child: child,
    );
  }
}
```

### 文件拖放

```dart
class DropTarget extends StatefulWidget {
  final Widget child;
  final ValueChanged<List<String>> onFilesDropped;

  const DropTarget({
    super.key,
    required this.child,
    required this.onFilesDropped,
  });

  @override
  State<DropTarget> createState() => _DropTargetState();
}

class _DropTargetState extends State<DropTarget> {
  bool _isDragging = false;

  @override
  Widget build(BuildContext context) {
    return DropTarget(
      onDragEntered: (details) {
        setState(() => _isDragging = true);
      },
      onDragExited: (details) {
        setState(() => _isDragging = false);
      },
      onDragDone: (details) {
        final files = details.files.map((f) => f.path).toList();
        widget.onFilesDropped(files);
        setState(() => _isDragging = false);
      },
      child: Container(
        decoration: _isDragging
            ? BoxDecoration(border: Border.all(color: Colors.blue, width: 2))
            : null,
        child: widget.child,
      ),
    );
  }
}
```

### 导航侧边栏模式

```dart
class DesktopScaffold extends StatelessWidget {
  final int selectedIndex;
  final ValueChanged<int> onDestinationSelected;
  final List<NavigationDestination> destinations;
  final Widget body;

  const DesktopScaffold({
    super.key,
    required this.selectedIndex,
    required this.onDestinationSelected,
    required this.destinations,
    required this.body,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        NavigationRail(
          selectedIndex: selectedIndex,
          onDestinationSelected: onDestinationSelected,
          labelType: NavigationRailLabelType.all,
          leading: Padding(
            padding: const EdgeInsets.symmetric(vertical: 16),
            child: Icon(Icons.apps, size: 32),
          ),
          destinations: destinations,
        ),
        const VerticalDivider(thickness: 1, width: 1),
        Expanded(child: body),
      ],
    );
  }
}
```

---

## Security Considerations

### Platform Channel安全

1. **输入验证**: 所有Platform Channel参数必须在Dart端和原生端双重验证
2. **敏感数据**: 禁止通过Platform Channel明文传输密码、密钥等敏感数据
3. **最小权限**: 只暴露必要的Platform Channel方法
4. **错误处理**: 不在错误消息中泄露系统信息

```dart
class SecurePlatformService {
  static const _channel = MethodChannel('com.example.app/secure');

  Future<void> saveCredential(String key, String value) async {
    if (key.isEmpty) throw ArgumentError('Key cannot be empty');
    if (value.isEmpty) throw ArgumentError('Value cannot be empty');

    final encrypted = await _encrypt(value);
    await _channel.invokeMethod('saveCredential', {
      'key': key,
      'value': encrypted,
    });
  }

  Future<String?> getCredential(String key) async {
    if (key.isEmpty) throw ArgumentError('Key cannot be empty');

    final encrypted = await _channel.invokeMethod<String>('getCredential', {
      'key': key,
    });
    if (encrypted == null) return null;
    return _decrypt(encrypted);
  }
}
```

### 安全存储

```dart
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorageService {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
  );

  static Future<void> write(String key, String value) async {
    await _storage.write(key: key, value: value);
  }

  static Future<String?> read(String key) async {
    return await _storage.read(key: key);
  }

  static Future<void> delete(String key) async {
    await _storage.delete(key: key);
  }
}
```

### 文件系统安全

```dart
class SecureFileService {
  static final _allowedDirs = <String>[
    // 仅允许访问应用数据目录和用户文档目录
  ];

  static Future<String> getSafePath(String inputPath) async {
    final resolved = File(inputPath).absolute.path;
    final isAllowed = _allowedDirs.any((dir) => resolved.startsWith(dir));
    if (!isAllowed) {
      throw SecurityException('Access denied: path outside allowed directories');
    }
    if (resolved.contains('..')) {
      throw SecurityException('Path traversal detected');
    }
    return resolved;
  }
}
```

### 网络安全

```dart
class SecureHttpClient {
  static http.Client create() {
    return http.Client();
  }

  static Future<bool> validateCertificate(String url) async {
    final uri = Uri.parse(url);
    if (uri.scheme != 'https') {
      throw SecurityException('Only HTTPS connections are allowed');
    }
    return true;
  }
}
```

### macOS沙盒权限

```xml
<!-- macos/Runner/DebugProfile.entitlements -->
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-only</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>

<!-- macos/Runner/Release.entitlements -->
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-only</key>
    <true/>
</dict>
```

### Flutter桌面安全检查清单

- [ ] Platform Channel所有方法参数双重验证（Dart端+原生端）
- [ ] 敏感数据不通过Platform Channel明文传输
- [ ] 使用flutter_secure_storage存储凭证
- [ ] 文件访问限定在允许的目录范围内
- [ ] 网络请求强制使用HTTPS
- [ ] macOS沙盒权限最小化配置
- [ ] Windows UAC清单配置正确
- [ ] 不在日志中输出敏感信息
- [ ] 构建产物剥离调试信息
- [ ] 代码混淆（--obfuscate --split-debug-info）
- [ ] 原生代码编译时启用安全编译选项（Stack Canary, ASLR, DEP）
- [ ] 第三方依赖安全审计

## 相关参考

- [Desktop Development Guidelines](desktop-dev-guidelines.md) — 通用桌面开发指南（Electron/Tauri/Flutter）
- [Flutter Standards](flutter-standards.md) — Flutter编码规范与最佳实践
- [IPC Contracts](ipc-contracts.md) — IPC/Platform Channel契约定义规范
- [Security Guidelines](security-guidelines.md) — 安全开发通用指南
