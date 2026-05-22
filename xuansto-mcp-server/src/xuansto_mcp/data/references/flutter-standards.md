# Flutter/Dart 开发规范

> 版本: 1.0.0 | 更新日期: 2026-05-03 | 编码: UTF-8 without BOM | 行尾: LF

---

## 目录

1. [命名规范](#1-命名规范)
2. [项目结构](#2-项目结构)
3. [代码规范](#3-代码规范)
4. [测试规范](#4-测试规范)
5. [安全规范](#5-安全规范)
6. [性能规范](#6-性能规范)
7. [桌面端特定规范](#7-桌面端特定规范)
8. [检查清单](#8-检查清单)

---

## 1. 命名规范

### 1.1 命名规则总览

| 类型 | 命名风格 | 示例 |
|------|----------|------|
| 文件名 | snake_case | `user_service.dart` |
| 类名 | PascalCase | `UserService` |
| 扩展类文件名 | PascalCase | `user_service_extension.dart` |
| 函数/方法 | camelCase | `getUserById()` |
| 变量 | camelCase | `userCount` |
| 常量 | camelCase / SCREAMING_SNAKE_CASE | `defaultTimeout` / `MAX_RETRY_COUNT` |
| 私有成员 | _前缀 | `_internalValue` |
| 包/导入 | snake_case | `import 'user_service.dart'` |
| 枚举值 | camelCase | `ColorScheme.light` |
| 命名参数 | camelCase | `{required String userName}` |
| 位置参数 | camelCase | `(String userName, int age)` |
| 类型参数 | PascalCase | `T`, `E`, `Repository<T>` |
| 注解 | PascalCase | `@JsonSerializable()` |
| 库名 | snake_case | `library user_service;` |

### 1.2 文件命名规范

```dart
// 正确：文件名使用 snake_case
user_service.dart
order_repository.dart
api_client.dart
home_screen.dart
user_profile_widget.dart

// 错误：不符合 Dart 惯例
userService.dart
OrderRepository.dart
api-client.dart
```

### 1.3 类与成员命名

```dart
class UserService {
  static const maxRetryCount = 3;
  static const DEFAULT_TIMEOUT = 30;

  final String _apiBaseUrl;
  final HttpClient _httpClient;
  int _requestCount = 0;

  UserService({
    required String apiBaseUrl,
    required HttpClient httpClient,
  })  : _apiBaseUrl = apiBaseUrl,
        _httpClient = httpClient;

  Future<User> getUserById(int userId) async {
    _requestCount++;
    final response = await _httpClient.get('$_apiBaseUrl/users/$userId');
    return User.fromJson(response.data);
  }

  bool _validateUserData(Map<String, dynamic> data) {
    return data.containsKey('name') && data.containsKey('email');
  }
}

enum AuthStatus {
  authenticated,
  unauthenticated,
  loading,
}

extension StringExtension on String {
  String get capitalized {
    if (isEmpty) return this;
    return '${this[0].toUpperCase()}${substring(1)}';
  }
}
```

---

## 2. 项目结构

### 2.1 标准项目结构

```
project_name/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── release.yml
├── android/
├── ios/
├── linux/
├── macos/
├── windows/
├── web/
├── lib/
│   ├── main.dart
│   ├── app.dart
│   ├── core/
│   │   ├── constants/
│   │   │   └── app_constants.dart
│   │   ├── theme/
│   │   │   ├── app_theme.dart
│   │   │   └── color_palette.dart
│   │   ├── utils/
│   │   │   ├── date_formatter.dart
│   │   │   └── validators.dart
│   │   ├── network/
│   │   │   ├── api_client.dart
│   │   │   ├── api_interceptor.dart
│   │   │   └── api_exception.dart
│   │   └── router/
│   │       └── app_router.dart
│   ├── models/
│   │   ├── user.dart
│   │   └── order.dart
│   ├── services/
│   │   ├── auth_service.dart
│   │   ├── user_service.dart
│   │   └── storage_service.dart
│   ├── viewmodels/
│   │   ├── auth_viewmodel.dart
│   │   ├── user_viewmodel.dart
│   │   └── home_viewmodel.dart
│   ├── views/
│   │   ├── home/
│   │   │   ├── home_screen.dart
│   │   │   └── home_binding.dart
│   │   ├── auth/
│   │   │   ├── login_screen.dart
│   │   │   └── register_screen.dart
│   │   └── profile/
│   │       ├── profile_screen.dart
│   │       └── edit_profile_screen.dart
│   └── widgets/
│       ├── common/
│       │   ├── loading_indicator.dart
│       │   ├── error_view.dart
│       │   └── custom_button.dart
│       └── shared/
│           ├── user_avatar.dart
│           └── rating_stars.dart
├── test/
│   ├── unit/
│   │   ├── services/
│   │   │   └── user_service_test.dart
│   │   └── viewmodels/
│   │       └── auth_viewmodel_test.dart
│   ├── widget/
│   │   └── widgets/
│   │       └── custom_button_test.dart
│   └── helpers/
│       └── test_helpers.dart
├── integration_test/
│   └── app_test.dart
├── assets/
│   ├── images/
│   ├── fonts/
│   └── l10n/
├── analysis_options.yaml
├── pubspec.yaml
├── pubspec.lock
└── README.md
```

### 2.2 特征优先组织方式

```
lib/
├── features/
│   ├── auth/
│   │   ├── models/
│   │   │   └── user.dart
│   │   ├── services/
│   │   │   └── auth_service.dart
│   │   ├── viewmodels/
│   │   │   └── auth_viewmodel.dart
│   │   ├── views/
│   │   │   ├── login_screen.dart
│   │   │   └── register_screen.dart
│   │   └── widgets/
│   │       └── auth_form.dart
│   ├── profile/
│   │   ├── models/
│   │   ├── services/
│   │   ├── viewmodels/
│   │   ├── views/
│   │   └── widgets/
│   └── settings/
│       ├── models/
│       ├── services/
│       ├── viewmodels/
│       ├── views/
│       └── widgets/
└── core/
    ├── constants/
    ├── theme/
    ├── utils/
    ├── network/
    └── widgets/
```

### 2.3 MVVM 架构模式

```dart
// Model - 数据模型
class User {
  final int id;
  final String name;
  final String email;

  const User({
    required this.id,
    required this.name,
    required this.email,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int,
      name: json['name'] as String,
      email: json['email'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {'id': id, 'name': name, 'email': email};
  }
}

// ViewModel - 业务逻辑与状态管理
class UserViewModel extends ChangeNotifier {
  final UserService _userService;

  User? _user;
  User? get user => _user;

  bool _isLoading = false;
  bool get isLoading => _isLoading;

  String? _errorMessage;
  String? get errorMessage => _errorMessage;

  UserViewModel({required UserService userService})
      : _userService = userService;

  Future<void> loadUser(int userId) async {
    _isLoading = true;
    _errorMessage = null;
    notifyListeners();

    try {
      _user = await _userService.getUserById(userId);
      _isLoading = false;
      notifyListeners();
    } catch (e) {
      _isLoading = false;
      _errorMessage = e.toString();
      notifyListeners();
    }
  }
}

// View - UI 层
class UserProfileScreen extends StatelessWidget {
  const UserProfileScreen({super.key, required this.userId});

  final int userId;

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (context) => UserViewModel(
        userService: context.read<UserService>(),
      )..loadUser(userId),
      child: const _UserProfileContent(),
    );
  }
}
```

---

## 3. 代码规范

### 3.1 类型声明

```dart
// 正确：显式类型声明
String userName = 'Alice';
int itemCount = 42;
List<User> users = [];
Map<String, dynamic> config = {};
final double taxRate = 0.08;

// 错误：避免使用 var 和 dynamic
var userName = 'Alice';       // 不推荐
dynamic config = {};           // 禁止使用
final users = <User>[];       // 可接受，类型通过泛型推断

// 正确：final 和 const 优先
const Duration animationDuration = Duration(milliseconds: 300);
final String sessionId = generateSessionId();

// 正确：函数返回类型必须显式声明
Future<List<User>> fetchUsers() async {
  final response = await _httpClient.get('/users');
  return (response.data as List).map((e) => User.fromJson(e)).toList();
}

// 错误：省略返回类型
fetchUsers() async { ... }
```

### 3.2 空安全规范

```dart
// 非空类型 - 默认
String name = 'Alice';
int count = 0;

// 可空类型 - 显式标记
String? nickname;
int? age;

// 空值检查
void greet(String? name) {
  // 方式1：if 检查
  if (name != null) {
    print('Hello, $name');
  }

  // 方式2：空值合并
  final displayName = name ?? 'Guest';

  // 方式3：条件成员访问
  final length = name?.length ?? 0;
}

// late 关键字 - 延迟初始化
class UserController {
  late final User _currentUser;

  void initialize(User user) {
    _currentUser = user;
  }
}

// 正确：使用 ! 断言仅在确定非空时
void process(String? value) {
  if (value != null) {
    print(value.length);
  }
}

// 错误：滥用 ! 断言
void processUnsafe(String? value) {
  print(value!.length); // 可能抛出异常
}
```

### 3.3 构造函数规范

```dart
class User {
  final int id;
  final String name;
  final String email;
  final String? avatarUrl;

  // 主构造函数 - 使用初始化列表
  const User({
    required this.id,
    required this.name,
    required this.email,
    this.avatarUrl,
  });

  // 命名构造函数 - fromJson
  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: json['id'] as int,
      name: json['name'] as String,
      email: json['email'] as String,
      avatarUrl: json['avatar_url'] as String?,
    );
  }

  // 命名构造函数 - empty
  const User.empty()
      : id = 0,
        name = '',
        email = '',
        avatarUrl = null;

  // 命名构造函数 - fromRow (数据库行)
  factory User.fromRow(List<dynamic> row) {
    return User(
      id: row[0] as int,
      name: row[1] as String,
      email: row[2] as String,
    );
  }

  // copyWith 方法
  User copyWith({
    int? id,
    String? name,
    String? email,
    String? avatarUrl,
  }) {
    return User(
      id: id ?? this.id,
      name: name ?? this.name,
      email: email ?? this.email,
      avatarUrl: avatarUrl ?? this.avatarUrl,
    );
  }
}

// factory 构造函数 - 缓存实例
class Logger {
  static final Map<String, Logger> _cache = {};

  final String name;

  factory Logger(String name) {
    return _cache.putIfAbsent(name, () => Logger._internal(name));
  }

  const Logger._internal(this.name);
}
```

### 3.4 异步编程规范

```dart
// 正确：使用 async/await
Future<User> fetchUser(int id) async {
  try {
    final response = await _httpClient.get('/users/$id');
    return User.fromJson(response.data);
  } on SocketException {
    throw NetworkException('网络连接失败');
  } on FormatException {
    throw DataParseException('数据解析失败');
  }
}

// 正确：并行执行多个异步操作
Future<void> loadDashboard() async {
  final results = await Future.wait([
    fetchUserProfile(),
    fetchNotifications(),
    fetchSettings(),
  ]);
}

// 正确：Stream 使用
Stream<List<Order>> watchOrders() async* {
  await for (final event in _eventSource) {
    if (event.type == 'order_updated') {
      yield await _orderRepository.getOrders();
    }
  }
}

// 正确：StreamController 使用
class OrderBloc {
  final _ordersController = StreamController<List<Order>>.broadcast();

  Stream<List<Order>> get orders => _ordersController.stream;

  Future<void> loadOrders() async {
    try {
      final orders = await _orderService.getOrders();
      _ordersController.add(orders);
    } catch (e) {
      _ordersController.addError(e);
    }
  }

  void dispose() {
    _ordersController.close();
  }
}

// 正确：超时处理
Future<Response> fetchWithTimeout(Uri url) async {
  return await _httpClient
      .get(url)
      .timeout(const Duration(seconds: 10));
}

// 正确：取消操作
Future<void> performTask(CancellationToken token) async {
  for (int i = 0; i < 100; i++) {
    token.throwIfCancelled();
    await _processItem(i);
  }
}
```

### 3.5 Widget 规范

```dart
// 正确：优先使用 StatelessWidget
class UserCard extends StatelessWidget {
  const UserCard({
    super.key,
    required this.user,
    this.onTap,
  });

  final User user;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(
          backgroundImage: user.avatarUrl != null
              ? NetworkImage(user.avatarUrl!)
              : null,
          child: user.avatarUrl == null
              ? Text(user.name[0])
              : null,
        ),
        title: Text(user.name),
        subtitle: Text(user.email),
        onTap: onTap,
      ),
    );
  }
}

// 正确：const 构造函数
class AppColors {
  const AppColors._();

  static const primaryColor = Color(0xFF2196F3);
  static const backgroundColor = Color(0xFFF5F5F5);
}

// 正确：使用 const Widget 减少重建
Widget build(BuildContext context) {
  return const Column(
    children: [
      SizedBox(height: 16),
      Divider(),
      SizedBox(height: 8),
    ],
  );
}

// 正确：StatefulWidget 使用
class CounterWidget extends StatefulWidget {
  const CounterWidget({super.key, this.initialValue = 0});

  final int initialValue;

  @override
  State<CounterWidget> createState() => _CounterWidgetState();
}

class _CounterWidgetState extends State<CounterWidget> {
  late int _count;

  @override
  void initState() {
    super.initState();
    _count = widget.initialValue;
  }

  @override
  void didUpdateWidget(CounterWidget oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.initialValue != widget.initialValue) {
      _count = widget.initialValue;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Text('Count: $_count');
  }
}
```

---

## 4. 测试规范

### 4.1 单元测试

```dart
// test/unit/services/user_service_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

import 'package:project_name/services/user_service.dart';
import 'package:project_name/models/user.dart';
import 'package:project_name/core/network/api_client.dart';

class MockApiClient extends Mock implements ApiClient {}

void main() {
  group('UserService', () {
    late UserService userService;
    late MockApiClient mockApiClient;

    setUp(() {
      mockApiClient = MockApiClient();
      userService = UserService(apiClient: mockApiClient);
    });

    test('should_returnUser_when_validIdProvided', () async {
      final expectedUser = User(
        id: 1,
        name: 'Alice',
        email: 'alice@example.com',
      );

      when(() => mockApiClient.get('/users/1')).thenAnswer(
        (_) async => ApiResponse(data: expectedUser.toJson()),
      );

      final result = await userService.getUserById(1);

      expect(result, equals(expectedUser));
      verify(() => mockApiClient.get('/users/1')).called(1);
    });

    test('should_throwNetworkException_when_networkFails', () async {
      when(() => mockApiClient.get('/users/1')).thenThrow(
        SocketException('网络连接失败'),
      );

      expect(
        () => userService.getUserById(1),
        throwsA(isA<NetworkException>()),
      );
    });

    test('should_returnNull_when_userNotFound', () async {
      when(() => mockApiClient.get('/users/999')).thenAnswer(
        (_) async => ApiResponse(data: null),
      );

      final result = await userService.getUserById(999);

      expect(result, isNull);
    });
  });
}
```

### 4.2 Widget 测试

```dart
// test/widget/widgets/custom_button_test.dart
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:project_name/widgets/common/custom_button.dart';

void main() {
  group('CustomButton', () {
    testWidgets('should_displayLabel_when_rendered', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CustomButton(label: '提交'),
          ),
        ),
      );

      expect(find.text('提交'), findsOneWidget);
      expect(find.byType(ElevatedButton), findsOneWidget);
    });

    testWidgets('should_callOnPressed_when_tapped', (tester) async {
      var pressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: CustomButton(
              label: '提交',
              onPressed: () => pressed = true,
            ),
          ),
        ),
      );

      await tester.tap(find.byType(ElevatedButton));
      expect(pressed, isTrue);
    });

    testWidgets('should_showLoadingIndicator_when_isLoading', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: CustomButton(label: '提交', isLoading: true),
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
      expect(find.text('提交'), findsNothing);
    });
  });
}
```

### 4.3 集成测试

```dart
// integration_test/app_test.dart
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';

import 'package:project_name/main.dart' as app;

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('端到端测试', () {
    testWidgets('should_completeLoginFlow', (tester) async {
      app.main();
      await tester.pumpAndSettle();

      await tester.enterText(
        find.byKey(const Key('email_field')),
        'test@example.com',
      );
      await tester.enterText(
        find.byKey(const Key('password_field')),
        'password123',
      );
      await tester.tap(find.byKey(const Key('login_button')));
      await tester.pumpAndSettle();

      expect(find.text('欢迎回来'), findsOneWidget);
    });
  });
}
```

### 4.4 测试命名与组织

```dart
// 测试命名规范：should_[预期行为]_when_[条件]
test('should_returnEmptyList_when_noUsersExist', () async { ... });
test('should_throwValidationException_when_emailIsInvalid', () { ... });
test('should_cacheResult_when_sameRequestMadeTwice', () async { ... });

// 测试组织：使用 group 分组
group('UserService', () {
  group('getUserById', () {
    test('should_returnUser_when_validId', () { ... });
    test('should_returnNull_when_userNotFound', () { ... });
    test('should_throwException_when_networkFails', () { ... });
  });

  group('createUser', () {
    test('should_createUser_when_validData', () { ... });
    test('should_throwException_when_duplicateEmail', () { ... });
  });
});
```

### 4.5 Mock 使用规范

```dart
// 使用 mocktail 创建 Mock
class MockUserRepository extends Mock implements UserRepository {}
class MockAuthService extends Mock implements AuthService {}

// 注册 fallback 值（用于任意参数匹配）
setUpAll(() {
  registerFallbackValue(User.empty());
});

// 验证调用
verify(() => repository.save(any(that: isA<User>()))).called(1);
verifyNever(() => repository.delete(any()));

// 设置连续返回值
when(() => api.get(any())).thenAnswer((_) async => response1);
when(() => api.get(any())).thenAnswer((_) async => response2);
```

---

## 5. 安全规范

### 5.1 敏感数据存储

```dart
// 正确：使用 flutter_secure_storage 存储敏感数据
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class SecureStorageService {
  static const _storage = FlutterSecureStorage(
    aOptions: AndroidOptions(encryptedSharedPreferences: true),
    iOptions: IOSOptions(accessibility: KeychainAccessibility.first_unlock),
  );

  Future<void> saveToken(String token) async {
    await _storage.write(key: 'auth_token', value: token);
  }

  Future<String?> getToken() async {
    return await _storage.read(key: 'auth_token');
  }

  Future<void> deleteToken() async {
    await _storage.delete(key: 'auth_token');
  }

  Future<void> clearAll() async {
    await _storage.deleteAll();
  }
}

// 错误：使用 SharedPreferences 存储敏感数据
class InsecureStorage {
  Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    prefs.setString('auth_token', token); // 不安全！
  }
}
```

### 5.2 网络安全

```dart
// 正确：HTTPS + 证书校验
class SecureApiClient {
  late final Dio _dio;

  SecureApiClient() {
    _dio = Dio(BaseOptions(
      baseUrl: 'https://api.example.com',
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 15),
    ));

    _dio.interceptors.add(LogInterceptor(
      requestBody: false,
      responseBody: false,
    ));
  }

  // 正确：证书固定
  void enableCertificatePinning() {
    _dio.httpClientAdapter = IOHttpClientAdapter(
      createHttpClient: () {
        final client = HttpClient();
        client.badCertificateCallback = (cert, host, port) => false;
        return client;
      },
    );
  }
}

// 正确：请求头安全
Options _secureOptions() {
  return Options(
    headers: {
      'Authorization': 'Bearer ${_tokenService.currentToken}',
      'X-Request-ID': _generateRequestId(),
      'Content-Type': 'application/json',
    },
  );
}
```

### 5.3 代码混淆

```bash
# 发布构建时启用混淆
flutter build apk --obfuscate --split-debug-info=/<project-name>/debug-info
flutter build ios --obfuscate --split-debug-info=/<project-name>/debug-info
flutter build windows --obfuscate --split-debug-info=/<project-name>/debug-info

# 保留符号表用于崩溃分析
flutter symbolize --input=/<project-name>/debug-info/app.android-arm64.symbols
```

### 5.4 权限最小化

```yaml
# android/app/src/main/AndroidManifest.xml
<manifest>
    <!-- 仅声明必要权限 -->
    <uses-permission android:name="android.permission.INTERNET" />
    <!-- 避免过度权限 -->
    <!-- <uses-permission android:name="android.permission.READ_CONTACTS" /> -->
</manifest>
```

```dart
// 正确：运行时权限请求
import 'package:permission_handler/permission_handler.dart';

Future<bool> requestCameraPermission() async {
  final status = await Permission.camera.request();
  if (status.isGranted) {
    return true;
  }
  if (status.isPermanentlyDenied) {
    await openAppSettings();
    return false;
  }
  return false;
}
```

---

## 6. 性能规范

### 6.1 Widget 重建优化

```dart
// 正确：使用 const 构造函数
class UserListTile extends StatelessWidget {
  const UserListTile({
    super.key,
    required this.name,
    required this.email,
  });

  final String name;
  final String email;

  @override
  Widget build(BuildContext context) {
    return ListTile(
      title: Text(name),
      subtitle: Text(email),
    );
  }
}

// 正确：使用 Key 优化列表更新
ListView.builder(
  itemCount: users.length,
  itemBuilder: (context, index) {
    return UserListTile(
      key: ValueKey(users[index].id),
      name: users[index].name,
      email: users[index].email,
    );
  },
)

// 正确：拆分 Widget 减少重建范围
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Column(
      children: [
        _HeaderSection(),
        _StatsSection(),
        _RecentActivitySection(),
      ],
    );
  }
}

// 正确：使用 Selector 精确监听状态变化
class UserNameDisplay extends StatelessWidget {
  const UserNameDisplay({super.key});

  @override
  Widget build(BuildContext context) {
    final name = context.select<UserViewModel, String>((vm) => vm.user?.name ?? '');
    return Text(name);
  }
}
```

### 6.2 列表优化

```dart
// 错误：使用 Column 渲染长列表
Column(
  children: items.map((item) => ItemWidget(item: item)).toList(),
)

// 正确：使用 ListView.builder 懒加载
ListView.builder(
  itemCount: items.length,
  itemBuilder: (context, index) {
    return ItemWidget(item: items[index]);
  },
)

// 正确：使用 Sliver 优化复杂滚动视图
CustomScrollView(
  slivers: [
    const SliverToBoxAdapter(child: HeaderWidget()),
    SliverList.builder(
      itemCount: items.length,
      itemBuilder: (context, index) => ItemWidget(item: items[index]),
    ),
    const SliverToBoxAdapter(child: FooterWidget()),
  ],
)

// 正确：分页加载
class PaginatedListView extends StatefulWidget {
  const PaginatedListView({super.key});

  @override
  State<PaginatedListView> createState() => _PaginatedListViewState();
}

class _PaginatedListViewState extends State<PaginatedListView> {
  final _scrollController = ScrollController();
  static const _pageSize = 20;

  @override
  void initState() {
    super.initState();
    _scrollController.addListener(_onScroll);
  }

  void _onScroll() {
    if (_scrollController.position.pixels >=
        _scrollController.position.maxScrollExtent * 0.8) {
      context.read<ItemViewModel>().loadMore();
    }
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }
}
```

### 6.3 图片优化

```dart
// 正确：使用 cached_network_image 缓存网络图片
CachedNetworkImage(
  imageUrl: user.avatarUrl,
  placeholder: (context, url) => const CircularProgressIndicator(),
  errorWidget: (context, url, error) => const Icon(Icons.person),
  memCacheWidth: 200,
  memCacheHeight: 200,
)

// 正确：指定图片缓存尺寸
Image.asset(
  'assets/images/logo.png',
  cacheWidth: 100,
  cacheHeight: 100,
  fit: BoxFit.cover,
)

// 正确：预缓存关键图片
precacheImage(NetworkImage(url), context);
```

### 6.4 状态管理选择

| 场景 | 推荐方案 | 说明 |
|------|----------|------|
| 简单局部状态 | setState | 少量UI状态 |
| 跨Widget共享 | Provider | 轻量级依赖注入 |
| 响应式状态 | Riverpod | 编译时安全，灵活 |
| 复杂事件流 | Bloc/Cubit | 事件驱动，可测试 |
| 表单/动画 | StatefulWidget | 局部临时状态 |

```dart
// Provider 示例
void main() {
  runApp(
    MultiProvider(
      providers: [
        ChangeNotifierProvider(create: (_) => AuthViewModel(authService: AuthService())),
        ChangeNotifierProvider(create: (_) => ThemeViewModel()),
        Provider(create: (_) => ApiClient()),
      ],
      child: const MyApp(),
    ),
  );
}

// Riverpod 示例
final userProvider = FutureProvider.family<User, int>((ref, userId) async {
  final service = ref.watch(userServiceProvider);
  return service.getUserById(userId);
});

// Bloc 示例
class AuthBloc extends Bloc<AuthEvent, AuthState> {
  final AuthService _authService;

  AuthBloc({required AuthService authService})
      : _authService = authService,
        super(const AuthInitial()) {
    on<LoginRequested>(_onLoginRequested);
    on<LogoutRequested>(_onLogoutRequested);
  }

  Future<void> _onLoginRequested(
    LoginRequested event,
    Emitter<AuthState> emit,
  ) async {
    emit(const AuthLoading());
    try {
      final user = await _authService.login(event.email, event.password);
      emit(AuthAuthenticated(user: user));
    } catch (e) {
      emit(AuthError(message: e.toString()));
    }
  }
}
```

---

## 7. 桌面端特定规范

### 7.1 窗口管理

```dart
import 'package:window_manager/window_manager.dart';

Future<void> setupWindow() async {
  await windowManager.ensureInitialized();

  const windowOptions = WindowOptions(
    size: Size(1280, 800),
    minimumSize: Size(800, 600),
    center: true,
    backgroundColor: Colors.transparent,
    skipTaskbar: false,
    titleBarStyle: TitleBarStyle.hidden,
    title: 'App Name',
  );

  windowManager.waitUntilReadyToShow(windowOptions, () async {
    await windowManager.show();
    await windowManager.focus();
  });
}

// 窗口事件监听
class MainWindowListener with WindowListener {
  @override
  void onWindowClose() async {
    final isPreventClose = await windowManager.isPreventClose();
    if (isPreventClose) {
      final shouldClose = await _showCloseDialog();
      if (shouldClose) {
        await windowManager.destroy();
      }
    }
  }

  @override
  void onWindowResize() {}

  @override
  void onWindowMaximize() {}

  @override
  void onWindowUnmaximize() {}

  @override
  void onWindowMinimize() {}

  @override
  void onWindowRestore() {}
}
```

### 7.2 键盘快捷键

```dart
import 'package:flutter/services.dart';

class KeyboardShortcuts extends StatelessWidget {
  const KeyboardShortcuts({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Shortcuts(
      shortcuts: <LogicalKeySet, Intent>{
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyS):
            const SaveIntent(),
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyN):
            const NewFileIntent(),
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.keyW):
            const CloseTabIntent(),
        LogicalKeySet(LogicalKeyboardKey.control, LogicalKeyboardKey.shift, LogicalKeyboardKey.keyZ):
            const RedoIntent(),
      },
      child: Actions(
        actions: <Type, Action<Intent>>{
          SaveIntent: CallbackAction<SaveIntent>(
            onInvoke: (intent) => _handleSave(context),
          ),
          NewFileIntent: CallbackAction<NewFileIntent>(
            onInvoke: (intent) => _handleNewFile(context),
          ),
        },
        child: child,
      ),
    );
  }
}

// 平台感知快捷键
bool get isMacOS => Platform.isMacOS;
bool get useMetaKey => isMacOS;

SingleActivator saveShortcut() {
  return SingleActivator(
    useMetaKey ? LogicalKeyboardKey.meta : LogicalKeyboardKey.control,
    LogicalKeyboardKey.keyS,
  );
}
```

### 7.3 响应式布局

```dart
class ResponsiveLayout extends StatelessWidget {
  const ResponsiveLayout({
    super.key,
    required this.mobile,
    required this.tablet,
    this.desktop,
  });

  final Widget mobile;
  final Widget tablet;
  final Widget? desktop;

  static bool isMobile(BuildContext context) =>
      MediaQuery.sizeOf(context).width < 650;

  static bool isTablet(BuildContext context) =>
      MediaQuery.sizeOf(context).width >= 650 &&
      MediaQuery.sizeOf(context).width < 1100;

  static bool isDesktop(BuildContext context) =>
      MediaQuery.sizeOf(context).width >= 1100;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 1100) {
          return desktop ?? tablet;
        } else if (constraints.maxWidth >= 650) {
          return tablet;
        } else {
          return mobile;
        }
      },
    );
  }
}

// 使用示例
ResponsiveLayout(
  mobile: const MobileNavigation(),
  tablet: const TabletNavigation(),
  desktop: const DesktopNavigation(),
)
```

### 7.4 平台通道使用

```dart
// MethodChannel - 调用原生方法
class NativeService {
  static const _channel = MethodChannel('com.example.app/native');

  Future<String> getPlatformVersion() async {
    final version = await _channel.invokeMethod<String>('getPlatformVersion');
    return version!;
  }

  Future<void> setWindowTitle(String title) async {
    await _channel.invokeMethod<void>('setWindowTitle', {'title': title});
  }
}

// EventChannel - 监听原生事件
class BatteryService {
  static const _eventChannel = EventChannel('com.example.app/battery');

  Stream<int> get onBatteryChanged {
    return _eventChannel.receiveBroadcastStream().map((event) => event as int);
  }
}

// 平台判断
import 'dart:io' show Platform;

TargetPlatform get currentPlatform {
  if (Platform.isAndroid) return TargetPlatform.android;
  if (Platform.isIOS) return TargetPlatform.iOS;
  if (Platform.isMacOS) return TargetPlatform.macOS;
  if (Platform.isWindows) return TargetPlatform.windows;
  if (Platform.isLinux) return TargetPlatform.linux;
  return TargetPlatform.fuchsia;
}
```

---

## 8. 检查清单

### 8.1 命名规范检查清单

- [ ] 文件名使用 snake_case
- [ ] 类名使用 PascalCase
- [ ] 函数/变量使用 camelCase
- [ ] 私有成员使用 _ 前缀
- [ ] 常量使用 camelCase 或 SCREAMING_SNAKE_CASE
- [ ] 枚举值使用 camelCase
- [ ] 导入路径使用 snake_case

### 8.2 代码规范检查清单

- [ ] 所有公共函数/方法有显式返回类型
- [ ] 避免使用 var 和 dynamic
- [ ] 正确使用空安全（?、!、late）
- [ ] 优先使用 const 构造函数
- [ ] 优先使用 StatelessWidget
- [ ] 使用命名构造函数提高可读性
- [ ] 实现 copyWith 方法用于不可变对象
- [ ] 异步操作正确处理异常
- [ ] StreamController 在 dispose 时关闭

### 8.3 项目结构检查清单

- [ ] lib/ 目录结构清晰
- [ ] 遵循 MVVM 或选定架构模式
- [ ] Model/View/ViewModel/Service 分层
- [ ] 公共 Widget 抽取到 widgets/ 目录
- [ ] analysis_options.yaml 配置完整
- [ ] pubspec.yaml 依赖版本有约束

### 8.4 测试检查清单

- [ ] 单元测试覆盖核心业务逻辑
- [ ] Widget 测试覆盖关键交互
- [ ] 集成测试覆盖核心用户流程
- [ ] 测试命名遵循 should_[行为]_when_[条件]
- [ ] 使用 Mock 隔离外部依赖
- [ ] 测试覆盖正常与异常路径

### 8.5 安全检查清单

- [ ] 敏感数据使用 flutter_secure_storage
- [ ] 网络请求使用 HTTPS
- [ ] 实现证书固定（生产环境）
- [ ] 发布构建启用代码混淆
- [ ] 权限声明最小化
- [ ] 运行时权限正确请求与处理
- [ ] 无硬编码密钥或凭据

### 8.6 性能检查清单

- [ ] Widget 使用 const 构造函数
- [ ] 列表使用 ListView.builder
- [ ] 网络图片使用缓存（cached_network_image）
- [ ] 状态管理方案选择合理
- [ ] 避免不必要的 Widget 重建
- [ ] 图片指定缓存尺寸
- [ ] 分页加载大数据集

### 8.7 桌面端检查清单

- [ ] 窗口尺寸与最小尺寸设置合理
- [ ] 实现键盘快捷键
- [ ] 响应式布局适配不同窗口大小
- [ ] 平台通道正确处理跨平台差异
- [ ] 窗口关闭事件正确处理
- [ ] 自定义标题栏时实现拖拽与双击最大化

---

## 参考资料

- [Effective Dart](https://dart.dev/guides/language/effective-dart)
- [Flutter Documentation](https://docs.flutter.dev/)
- [Dart Language Tour](https://dart.dev/language)
- [Flutter Secure Storage](https://pub.dev/packages/flutter_secure_storage)
- [Riverpod Documentation](https://riverpod.dev/)
- [Bloc Library](https://bloclibrary.dev/)
- [Flutter Testing](https://docs.flutter.dev/testing)
- [window_manager](https://pub.dev/packages/window_manager)
