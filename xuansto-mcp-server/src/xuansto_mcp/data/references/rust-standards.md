# Rust 开发规范

> 版本: 1.9.0 | 更新日期: 2026-04-17 | 编码: UTF-8 without BOM | 行尾: LF

---

## 目录

1. [API 指南命名规范](#1-api-指南命名规范)
2. [代码风格规范](#2-代码风格规范)
3. [项目结构规范](#3-项目结构规范)
4. [依赖管理规范](#4-依赖管理规范)
5. [测试规范](#5-测试规范)
6. [安全编码规范](#6-安全编码规范)
7. [错误处理规范](#7-错误处理规范)
8. [检查清单](#8-检查清单)

---

## 1. API 指南命名规范

### 1.1 命名约定总览

| 条目 | 约定 | 示例 |
|------|------|------|
| Crate | `snake_case` | `serde_json`, `tokio_core` |
| Module | `snake_case` | `mod user_service;` |
| Type | `PascalCase` | `struct UserService`, `enum HttpStatus` |
| Trait | `PascalCase` | `trait FromStr`, `trait Iterator` |
| Enum 变体 | `PascalCase` | `Option::Some`, `Result::Ok` |
| Function | `snake_case` | `fn calculate_total()`, `fn get_user_by_id()` |
| Method | `snake_case` | `self.get_name()`, `user.set_email()` |
| Local 变量 | `snake_case` | `let user_count = 0;` |
| Static/Const | `SCREAMING_SNAKE_CASE` | `const MAX_CONNECTIONS: usize = 100;` |
| Type Parameter | 简短 `PascalCase` | `<T>`, `<U>`, `<E>`, `'a`, `'b` |
| Lifetime | 简短小写 | `'a`, `'b`, `'static` |

### 1.2 类型命名规范

```rust
pub struct UserAccount {
    pub id: Uuid,
    pub user_name: String,
    pub email_address: String,
    pub created_at: DateTime<Utc>,
    pub is_active: bool,
}

pub enum HttpResult {
    Success(Response),
    ClientError(ErrorInfo),
    ServerError(ErrorInfo),
}

pub trait Repository<T> {
    fn find_by_id(&self, id: Uuid) -> Option<T>;
    fn save(&mut self, entity: T) -> Result<(), RepositoryError>;
    fn delete(&mut self, id: Uuid) -> Result<(), RepositoryError>;
}
```

### 1.3 函数/方法命名规范

```rust
impl UserService {
    pub fn new(config: ServiceConfig) -> Self { }
    
    pub fn get_user_by_id(&self, id: Uuid) -> Result<User, ServiceError> { }
    
    pub fn create_user(&mut self, request: CreateUserRequest) -> Result<User, ServiceError> { }
    
    pub fn update_user_email(&mut self, id: Uuid, email: String) -> Result<(), ServiceError> { }
    
    pub fn delete_user(&mut self, id: Uuid) -> Result<(), ServiceError> { }
    
    pub fn list_users(&self, filter: UserFilter) -> Result<Vec<User>, ServiceError> { }
    
    pub fn user_exists(&self, id: Uuid) -> bool { }
    
    pub async fn fetch_user_async(&self, id: Uuid) -> Result<User, ServiceError> { }
}

impl User {
    pub fn is_admin(&self) -> bool { }
    
    pub fn has_permission(&self, permission: &str) -> bool { }
    
    pub fn to_dto(&self) -> UserDto { }
    
    pub fn from_dto(dto: UserDto) -> Self { }
}
```

### 1.4 Getter/Setter 规范

```rust
pub struct Configuration {
    max_connections: usize,
    timeout_seconds: u64,
    api_endpoint: String,
}

impl Configuration {
    pub fn max_connections(&self) -> usize {
        self.max_connections
    }
    
    pub fn set_max_connections(&mut self, value: usize) {
        self.max_connections = value;
    }
    
    pub fn api_endpoint(&self) -> &str {
        &self.api_endpoint
    }
}
```

### 1.5 布尔类型命名规范

```rust
pub struct User {
    pub is_active: bool,
    pub is_verified: bool,
    pub has_completed_onboarding: bool,
    pub can_access_admin_panel: bool,
    pub should_receive_notifications: bool,
}

pub fn is_valid_email(email: &str) -> bool { }
pub fn has_required_permissions(user: &User) -> bool { }
pub fn can_perform_action(user: &User, action: Action) -> bool { }
```

---

## 2. 代码风格规范

### 2.1 格式化工具配置

```toml
[toolchain]
channel = "stable"

[profile.dev]
opt-level = 0
debug = true

[profile.release]
opt-level = 3
lto = true
codegen-units = 1
strip = true
```

```toml
[lints.rust]
unsafe_code = "warn"
missing_docs = "warn"

[lints.clippy]
all = "warn"
pedantic = "warn"
nursery = "warn"
cargo = "warn"
```

### 2.2 rustfmt.toml 配置

```toml
max_width = 100
hard_tabs = false
tab_spaces = 4
newline_style = "Unix"
use_small_heuristics = "Default"
indent_style = "Block"
wrap_comments = true
comment_width = 80
normalize_comments = true
format_strings = true
format_macro_matchers = true
format_macro_bodies = true
empty_item_single_line = true
struct_lit_single_line = true
fn_single_line = false
where_single_line = false
imports_indent = "Block"
imports_layout = "Mixed"
imports_granularity = "Crate"
group_imports = "StdExternalCrate"
reorder_imports = true
reorder_modules = true
reorder_impl_items = true
type_punctuation_density = "Wide"
space_before_colon = false
space_after_colon = true
spaces_around_ranges = false
binop_separator = "Front"
remove_nested_parens = true
combine_control_expr = true
overflow_delimited_expr = true
struct_field_align_threshold = 0
enum_discrim_align_threshold = 0
match_arm_blocks = true
force_multiline_blocks = false
fn_args_layout = "Tall"
brace_style = "SameLineWhere"
control_brace_style = "AlwaysSameLine"
trailing_semicolon = true
trailing_comma = "Vertical"
match_block_trailing_comma = false
blank_lines_upper_bound = 1
blank_lines_lower_bound = 0
edition = "2021"
version = "Two"
inline_attribute_width = 0
emit_mode = "Files"
```

### 2.3 代码组织规范

```rust
use std::collections::HashMap;
use std::sync::Arc;

use anyhow::Result;
use serde::{Deserialize, Serialize};
use tokio::sync::RwLock;
use tracing::{debug, error, info, instrument};
use uuid::Uuid;

use crate::domain::entities::User;
use crate::domain::errors::DomainError;
use crate::infrastructure::persistence::Repository;

const MAX_RETRY_ATTEMPTS: u32 = 3;
const DEFAULT_TIMEOUT_MS: u64 = 5000;

pub struct UserService {
    repository: Arc<dyn Repository<User>>,
    cache: RwLock<HashMap<Uuid, User>>,
}

impl UserService {
    pub fn new(repository: Arc<dyn Repository<User>>) -> Self {
        Self {
            repository,
            cache: RwLock::new(HashMap::new()),
        }
    }
    
    #[instrument(skip(self))]
    pub async fn get_user(&self, id: Uuid) -> Result<User, DomainError> {
        if let Some(user) = self.cache.read().await.get(&id) {
            debug!("Cache hit for user: {}", id);
            return Ok(user.clone());
        }
        
        let user = self.repository
            .find_by_id(id)
            .await
            .map_err(|e| DomainError::NotFound(format!("User {}: {}", id, e)))?;
        
        self.cache.write().await.insert(id, user.clone());
        Ok(user)
    }
}
```

### 2.4 文档注释规范

```rust
/// Represents a user account in the system.
///
/// # Examples
///
/// ```
/// use myapp::domain::User;
/// use uuid::Uuid;
///
/// let user = User::new(
///     Uuid::new_v4(),
///     "john.doe".to_string(),
///     "john@example.com".to_string(),
/// );
///
/// assert!(user.is_active());
/// ```
///
/// # Safety
///
/// This type does not contain any unsafe code.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct User {
    pub id: Uuid,
    pub username: String,
    pub email: String,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub status: UserStatus,
}

impl User {
    /// Creates a new user with the given parameters.
    ///
    /// # Arguments
    ///
    /// * `id` - The unique identifier for the user.
    /// * `username` - The username for the user (must be unique).
    /// * `email` - The email address for the user (must be valid).
    ///
    /// # Returns
    ///
    /// A new `User` instance with default status and timestamps.
    ///
    /// # Errors
    ///
    /// This function does not return errors.
    ///
    /// # Panics
    ///
    /// This function does not panic.
    pub fn new(id: Uuid, username: String, email: String) -> Self {
        let now = Utc::now();
        Self {
            id,
            username,
            email,
            created_at: now,
            updated_at: now,
            status: UserStatus::Active,
        }
    }
}
```

---

## 3. 项目结构规范

### 3.1 Cargo Workspace 结构

```
my-project/
├── Cargo.toml
├── Cargo.lock
├── .cargo/
│   └── config.toml
├── crates/
│   ├── api/
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── handlers.rs
│   │       ├── handlers/
│   │       │   ├── user.rs
│   │       │   └── health.rs
│   │       ├── middleware.rs
│   │       ├── middleware/
│   │       │   └── auth.rs
│   │       ├── routes.rs
│   │       └── routes/
│   │           └── v1.rs
│   ├── domain/
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── entities.rs
│   │       ├── entities/
│   │       │   ├── user.rs
│   │       │   └── session.rs
│   │       ├── value_objects.rs
│   │       ├── value_objects/
│   │       │   ├── email.rs
│   │       │   └── password.rs
│   │       ├── services.rs
│   │       ├── services/
│   │       │   └── user_service.rs
│   │       └── errors.rs
│   ├── infrastructure/
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── persistence.rs
│   │       ├── persistence/
│   │       │   ├── postgres.rs
│   │       │   ├── postgres/
│   │       │   │   └── user_repository.rs
│   │       │   ├── redis.rs
│   │       │   └── redis/
│   │       │       └── cache.rs
│   │       ├── external.rs
│   │       ├── external/
│   │       │   └── email_client.rs
│   │       └── config.rs
│   ├── application/
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── use_cases.rs
│   │       ├── use_cases/
│   │       │   ├── create_user.rs
│   │       │   └── authenticate.rs
│   │       ├── dto.rs
│   │       └── dto/
│   │           ├── requests.rs
│   │           └── responses.rs
│   └── shared/
│       ├── Cargo.toml
│       └── src/
│           ├── lib.rs
│           ├── types.rs
│           ├── constants.rs
│           └── utils.rs
├── tests/
│   ├── integration/
│   │   ├── api_tests.rs
│   │   └── fixtures/
│   └── e2e/
│       └── user_flow.rs
├── benches/
│   └── performance.rs
├── examples/
│   └── basic_usage.rs
├── docs/
│   ├── architecture.md
│   └── api.md
├── .clippy.toml
├── .rustfmt.toml
├── rust-toolchain.toml
└── README.md
```

> **Rust 2018+ edition 推荐使用 `module_name.rs` 替代 `module_name/mod.rs` 声明子模块。** 旧版 `mod.rs` 模式仍可编译，但新项目应采用新约定。上述结构中所有模块均采用 `module_name.rs` + `module_name/` 目录的新式组织方式。

### 3.2 Workspace Cargo.toml

```toml
[workspace]
resolver = "2"
members = [
    "crates/api",
    "crates/domain",
    "crates/infrastructure",
    "crates/application",
    "crates/shared",
]

[workspace.package]
version = "0.1.0"
edition = "2021"
rust-version = "1.75"
authors = ["Team <team@example.com>"]
license = "MIT OR Apache-2.0"
repository = "https://github.com/org/my-project"
homepage = "https://my-project.io"
documentation = "https://docs.my-project.io"
readme = "README.md"
keywords = ["api", "async", "web"]
categories = ["web-programming", "asynchronous"]

[workspace.dependencies]
tokio = { version = "1.35", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
thiserror = "1.0"
anyhow = "1.0"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
uuid = { version = "1.6", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
sqlx = { version = "0.7", features = ["runtime-tokio", "postgres", "uuid", "chrono"] }
redis = { version = "0.24", features = ["tokio-comp"] }
reqwest = { version = "0.11", features = ["json"] }
async-trait = "0.1"
futures = "0.3"

[workspace.lints.rust]
unsafe_code = "warn"
missing_docs = "warn"
rust_2018_idioms = "warn"

[workspace.lints.clippy]
all = "warn"
pedantic = "warn"
nursery = "warn"
cargo = "warn"
```

### 3.3 Crate Cargo.toml 模板

```toml
[package]
name = "myapp-domain"
version.workspace = true
edition.workspace = true
rust-version.workspace = true
authors.workspace = true
license.workspace = true
repository.workspace = true

[dependencies]
serde = { workspace = true }
thiserror = { workspace = true }
uuid = { workspace = true }
chrono = { workspace = true }

[dev-dependencies]
tokio = { workspace = true }
proptest = "1.4"

[lints]
workspace = true
```

---

## 4. 依赖管理规范

### 4.1 依赖选择原则

```toml
[dependencies]
tokio = { version = "1.35", features = ["full"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
thiserror = "1.0"
anyhow = "1.0"
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
uuid = { version = "1.6", features = ["v4", "serde"] }
chrono = { version = "0.4", features = ["serde"] }
sqlx = { version = "0.7", features = ["runtime-tokio", "postgres", "uuid", "chrono"] }
redis = { version = "0.24", features = ["tokio-comp"] }
reqwest = { version = "0.11", features = ["json"] }
async-trait = "0.1"
futures = "0.3"

[dev-dependencies]
tokio-test = "0.4"
mockall = "0.12"
proptest = "1.4"
criterion = { version = "0.5", features = ["html_reports"] }
tempfile = "3.9"

[build-dependencies]
```

### 4.2 版本约束规范

```toml
[dependencies]
tokio = "1.35"
serde = "1.0"
uuid = "1.6"

anyhow = "1"
thiserror = "1"

regex = "1.10.2"

ring = "=0.17.7"

base64 = ">=0.21, <0.22"

sha2 = "^0.10"
```

### 4.3 Feature 管理规范

```toml
[features]
default = ["std", "async"]

std = []
async = ["tokio", "futures"]
tls = ["rustls", "webpki-roots"]
json = ["serde", "serde_json"]
full = ["std", "async", "tls", "json"]

[dependencies]
tokio = { version = "1.35", optional = true }
futures = { version = "0.3", optional = true }
serde = { version = "1.0", optional = true }
serde_json = { version = "1.0", optional = true }
rustls = { version = "0.22", optional = true }
webpki-roots = { version = "0.26", optional = true }
```

### 4.4 依赖审计配置

```toml
[advisories]
db-path = "~/.cargo/advisory-db"
db-urls = ["https://github.com/rustsec/advisory-db"]
vulnerability = "deny"
unmaintained = "warn"
yanked = "warn"
notice = "warn"
ignore = []

[licenses]
unlicensed = "deny"
allow = ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC"]
deny = ["GPL-3.0", "AGPL-3.0"]
copyleft = "warn"
allow-osi-fsf-free = "both"
default = "deny"
confidence-threshold = 0.8

[bans]
multiple-versions = "warn"
wildcards = "deny"
highlight = "all"
allow = []
deny = []
skip = []
skip-tree = []

[sources]
unknown-registry = "deny"
unknown-git = "deny"
allow-registry = ["https://github.com/rust-lang/crates.io-index"]
allow-git = []
```

---

## 5. 测试规范

### 5.1 单元测试规范

```rust
#[cfg(test)]
mod tests {
    use super::*;
    use proptest::prelude::*;
    
    #[test]
    fn test_user_creation() {
        let id = Uuid::new_v4();
        let user = User::new(
            id,
            "testuser".to_string(),
            "test@example.com".to_string(),
        );
        
        assert_eq!(user.id, id);
        assert_eq!(user.username, "testuser");
        assert_eq!(user.email, "test@example.com");
        assert!(user.is_active());
    }
    
    #[test]
    fn test_user_email_validation() {
        let result = Email::try_from("invalid-email");
        assert!(result.is_err());
        
        let result = Email::try_from("valid@example.com");
        assert!(result.is_ok());
    }
    
    #[test]
    #[should_panic(expected = "empty username")]
    fn test_empty_username_panics() {
        User::new(Uuid::new_v4(), "".to_string(), "test@example.com".to_string());
    }
    
    #[test]
    fn test_user_status_transitions() {
        let mut user = User::new(
            Uuid::new_v4(),
            "testuser".to_string(),
            "test@example.com".to_string(),
        );
        
        assert!(user.is_active());
        
        user.deactivate();
        assert!(!user.is_active());
        
        user.activate();
        assert!(user.is_active());
    }
    
    #[tokio::test]
    async fn test_async_user_fetch() {
        let service = UserService::new(Arc::new(MockRepository::new()));
        let id = Uuid::new_v4();
        
        let result = service.get_user(id).await;
        assert!(result.is_ok());
    }
    
    #[tokio::test]
    async fn test_concurrent_access() {
        let service = Arc::new(UserService::new(Arc::new(MockRepository::new())));
        let mut handles = vec![];
        
        for i in 0..10 {
            let svc = Arc::clone(&service);
            handles.push(tokio::spawn(async move {
                svc.get_user(Uuid::new_v4()).await
            }));
        }
        
        let results = futures::future::join_all(handles).await;
        assert!(results.iter().all(|r| r.is_ok()));
    }
}
```

### 5.2 属性测试 (proptest)

```rust
#[cfg(test)]
mod proptests {
    use super::*;
    use proptest::prelude::*;
    
    proptest! {
        #[test]
        fn test_email_parsing_valid(email in "[a-zA-Z0-9]+@[a-zA-Z0-9]+\\.[a-z]{2,}") {
            let result = Email::try_from(&email as &str);
            prop_assert!(result.is_ok());
        }
        
        #[test]
        fn test_username_length(username in ".{1,100}") {
            let result = User::new(
                Uuid::new_v4(),
                username.clone(),
                "test@example.com".to_string(),
            );
            prop_assert_eq!(result.username.len(), username.len());
        }
        
        #[test]
        fn test_string_roundtrip(s in ".*") {
            let encoded = encode_string(&s);
            let decoded = decode_string(&encoded)?;
            prop_assert_eq!(s, decoded);
        }
        
        #[test]
        fn test_addition_commutative(a: i32, b: i32) {
            prop_assert_eq!(a + b, b + a);
        }
        
        #[test]
        fn test_vec_push_pop(mut v: Vec<i32>, elem: i32) {
            let len = v.len();
            v.push(elem);
            prop_assert_eq!(v.len(), len + 1);
            prop_assert_eq!(v.pop(), Some(elem));
            prop_assert_eq!(v.len(), len);
        }
    }
}
```

### 5.3 集成测试规范

```rust
use myapp::api::create_app;
use axum::{
    body::Body,
    http::{Request, StatusCode},
};
use tower::ServiceExt;

#[tokio::test]
async fn test_health_endpoint() {
    let app = create_app().await;
    
    let response = app
        .oneshot(Request::builder().uri("/health").body(Body::empty()).unwrap())
        .await
        .unwrap();
    
    assert_eq!(response.status(), StatusCode::OK);
}

#[tokio::test]
async fn test_create_user_endpoint() {
    let app = create_app().await;
    
    let body = serde_json::json!({
        "username": "testuser",
        "email": "test@example.com"
    });
    
    let response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/v1/users")
                .header("Content-Type", "application/json")
                .body(Body::from(serde_json::to_string(&body).unwrap()))
                .unwrap(),
        )
        .await
        .unwrap();
    
    assert_eq!(response.status(), StatusCode::CREATED);
}

#[tokio::test]
async fn test_authentication_flow() {
    let app = create_app().await;
    
    let register_body = serde_json::json!({
        "username": "authuser",
        "email": "auth@example.com",
        "password": "SecurePass123!"
    });
    
    let register_response = app
        .clone()
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/v1/auth/register")
                .header("Content-Type", "application/json")
                .body(Body::from(serde_json::to_string(&register_body).unwrap()))
                .unwrap(),
        )
        .await
        .unwrap();
    
    assert_eq!(register_response.status(), StatusCode::CREATED);
    
    let login_body = serde_json::json!({
        "email": "auth@example.com",
        "password": "SecurePass123!"
    });
    
    let login_response = app
        .oneshot(
            Request::builder()
                .method("POST")
                .uri("/api/v1/auth/login")
                .header("Content-Type", "application/json")
                .body(Body::from(serde_json::to_string(&login_body).unwrap()))
                .unwrap(),
        )
        .await
        .unwrap();
    
    assert_eq!(login_response.status(), StatusCode::OK);
}
```

### 5.4 Mock 测试规范

```rust
use mockall::automock;

#[automock]
#[async_trait]
pub trait UserRepository: Send + Sync {
    async fn find_by_id(&self, id: Uuid) -> Result<Option<User>, RepositoryError>;
    async fn save(&self, user: &User) -> Result<(), RepositoryError>;
    async fn delete(&self, id: Uuid) -> Result<(), RepositoryError>;
}

#[cfg(test)]
mod tests {
    use super::*;
    use mockall::predicate::*;
    
    #[tokio::test]
    async fn test_service_with_mock() {
        let mut mock_repo = MockUserRepository::new();
        let user = User::new(
            Uuid::new_v4(),
            "testuser".to_string(),
            "test@example.com".to_string(),
        );
        let user_clone = user.clone();
        
        mock_repo
            .expect_find_by_id()
            .with(eq(user.id))
            .times(1)
            .returning(move |_| Ok(Some(user_clone.clone())));
        
        let service = UserService::new(Arc::new(mock_repo));
        let result = service.get_user(user.id).await;
        
        assert!(result.is_ok());
        assert_eq!(result.unwrap().username, "testuser");
    }
}
```

### 5.5 测试组织结构

```
tests/
├── integration.rs
├── integration/
│   ├── api.rs
│   ├── api/
│   │   ├── users.rs
│   │   └── auth.rs
│   ├── database.rs
│   ├── database/
│   │   └── migrations.rs
│   ├── fixtures.rs
│   └── fixtures/
│       ├── users.json
│       └── database.rs
├── common.rs
├── common/
│   ├── fixtures.rs
│   └── test_utils.rs
├── e2e.rs
└── e2e/
    └── user_flows.rs
```

---

## 6. 安全编码规范

### 6.1 unsafe 代码使用准则

```rust
pub mod safe_wrappers {
    use std::ptr;
    
    pub struct SafeBuffer {
        ptr: *mut u8,
        len: usize,
        capacity: usize,
    }
    
    impl SafeBuffer {
        pub fn new(capacity: usize) -> Self {
            let layout = std::alloc::Layout::array::<u8>(capacity).unwrap();
            
            let ptr = unsafe { std::alloc::alloc(layout) };
            
            if ptr.is_null() {
                std::alloc::handle_alloc_error(layout);
            }
            
            Self {
                ptr,
                len: 0,
                capacity,
            }
        }
        
        pub fn push(&mut self, byte: u8) -> Result<(), BufferError> {
            if self.len >= self.capacity {
                return Err(BufferError::CapacityExceeded);
            }
            
            unsafe {
                ptr::write(self.ptr.add(self.len), byte);
            }
            self.len += 1;
            
            Ok(())
        }
        
        pub fn get(&self, index: usize) -> Option<u8> {
            if index >= self.len {
                return None;
            }
            
            unsafe { Some(ptr::read(self.ptr.add(index))) }
        }
    }
    
    impl Drop for SafeBuffer {
        fn drop(&mut self) {
            if !self.ptr.is_null() {
                let layout = std::alloc::Layout::array::<u8>(self.capacity).unwrap();
                unsafe {
                    std::alloc::dealloc(self.ptr, layout);
                }
            }
        }
    }
    
    #[derive(Debug, thiserror::Error)]
    pub enum BufferError {
        #[error("Capacity exceeded")]
        CapacityExceeded,
    }
}
```

### 6.2 unsafe 代码审查清单

```rust
#[deny(unsafe_code)]
#[allow(unsafe_code)]
mod unsafe_block {
    use std::ptr::NonNull;
    
    pub struct SafeWrapper<T> {
        ptr: NonNull<T>,
    }
    
    impl<T> SafeWrapper<T> {
        /// Creates a new SafeWrapper.
        ///
        /// # Safety
        ///
        /// The caller must ensure that:
        /// - `ptr` is a valid, non-null pointer to a `T`
        /// - The memory pointed to by `ptr` remains valid for the lifetime of this wrapper
        /// - No other mutable references to the same memory exist
        ///
        /// # Invariants
        ///
        /// - `ptr` always points to valid, properly aligned memory
        /// - The pointed-to data is never mutated through this wrapper
        pub unsafe fn new(ptr: *mut T) -> Self {
            Self {
                ptr: NonNull::new_unchecked(ptr),
            }
        }
        
        pub fn get(&self) -> &T {
            unsafe { self.ptr.as_ref() }
        }
    }
    
    unsafe impl<T: Send> Send for SafeWrapper<T> {}
    unsafe impl<T: Sync> Sync for SafeWrapper<T> {}
}
```

### 6.3 安全数据处理

```rust
use secrecy::{ExposeSecret, Secret};

pub struct UserCredentials {
    pub username: String,
    password: Secret<String>,
}

impl UserCredentials {
    pub fn new(username: String, password: String) -> Self {
        Self {
            username,
            password: Secret::new(password),
        }
    }
    
    pub fn verify_password(&self, hash: &str) -> bool {
        let password = self.password.expose_secret();
        argon2::verify_encoded(hash, password.as_bytes()).unwrap_or(false)
    }
}

impl std::fmt::Debug for UserCredentials {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.debug_struct("UserCredentials")
            .field("username", &self.username)
            .field("password", &"[REDACTED]")
            .finish()
    }
}

pub fn hash_password(password: &Secret<String>) -> Result<String, PasswordError> {
    let password = password.expose_secret();
    let salt = password_hash::SaltString::generate(&mut rand::thread_rng());
    let argon2 = argon2::Argon2::default();
    
    let hash = argon2
        .hash_password(password.as_bytes(), &salt)
        .map_err(|_| PasswordError::HashingFailed)?
        .to_string();
    
    Ok(hash)
}
```

### 6.4 输入验证规范

```rust
use validator::{Validate, ValidationError};

#[derive(Debug, Deserialize, Validate)]
pub struct CreateUserRequest {
    #[validate(length(min = 3, max = 50, message = "Username must be 3-50 characters"))]
    #[validate(regex(path = "USERNAME_REGEX", message = "Username can only contain alphanumeric characters and underscores"))]
    pub username: String,
    
    #[validate(email(message = "Invalid email format"))]
    pub email: String,
    
    #[validate(length(min = 12, max = 128, message = "Password must be 12-128 characters"))]
    #[validate(custom(function = "validate_password_strength"))]
    pub password: String,
}

lazy_static::lazy_static! {
    static ref USERNAME_REGEX: regex::Regex = regex::Regex::new(r"^[a-zA-Z0-9_]+$").unwrap();
}

fn validate_password_strength(password: &str) -> Result<(), ValidationError> {
    let has_uppercase = password.chars().any(|c| c.is_uppercase());
    let has_lowercase = password.chars().any(|c| c.is_lowercase());
    let has_digit = password.chars().any(|c| c.is_ascii_digit());
    let has_special = password.chars().any(|c| "!@#$%^&*()_+-=[]{}|;:,.<>?".contains(c));
    
    let strength_count = [has_uppercase, has_lowercase, has_digit, has_special]
        .iter()
        .filter(|&&x| x)
        .count();
    
    if strength_count < 3 {
        return Err(ValidationError::new("weak_password")
            .with_message("Password must contain at least 3 of: uppercase, lowercase, digit, special character".into()));
    }
    
    Ok(())
}

pub async fn create_user(
    State(service): State<Arc<UserService>>,
    Json(request): Json<CreateUserRequest>,
) -> Result<Json<UserResponse>, ApiError> {
    request.validate()?;
    
    let user = service.create_user(request).await?;
    Ok(Json(UserResponse::from(user)))
}
```

---

## 7. 错误处理规范

### 7.1 thiserror 错误定义

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum DomainError {
    #[error("User not found: {0}")]
    UserNotFound(Uuid),
    
    #[error("User already exists: {0}")]
    UserAlreadyExists(String),
    
    #[error("Invalid email format: {0}")]
    InvalidEmail(String),
    
    #[error("Authentication failed: {0}")]
    AuthenticationFailed(String),
    
    #[error("Authorization denied: {0}")]
    AuthorizationDenied(String),
    
    #[error("Validation error: {0}")]
    Validation(String),
    
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
    
    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("Internal error: {0}")]
    Internal(String),
}

impl DomainError {
    pub fn is_retryable(&self) -> bool {
        matches!(
            self,
            DomainError::Database(sqlx::Error::PoolTimedOut)
                | DomainError::Database(sqlx::Error::PoolClosed)
        )
    }
    
    pub fn error_code(&self) -> &'static str {
        match self {
            DomainError::UserNotFound(_) => "USER_NOT_FOUND",
            DomainError::UserAlreadyExists(_) => "USER_ALREADY_EXISTS",
            DomainError::InvalidEmail(_) => "INVALID_EMAIL",
            DomainError::AuthenticationFailed(_) => "AUTH_FAILED",
            DomainError::AuthorizationDenied(_) => "AUTH_DENIED",
            DomainError::Validation(_) => "VALIDATION_ERROR",
            DomainError::Database(_) => "DATABASE_ERROR",
            DomainError::Io(_) => "IO_ERROR",
            DomainError::Internal(_) => "INTERNAL_ERROR",
        }
    }
}
```

### 7.2 Result 类型别名

```rust
pub type AppResult<T> = Result<T, DomainError>;

pub type RepositoryResult<T> = Result<T, RepositoryError>;

pub type ServiceResult<T> = Result<T, ServiceError>;
```

### 7.3 错误转换与传播

```rust
impl UserService {
    pub async fn get_user(&self, id: Uuid) -> AppResult<User> {
        let user = self.repository
            .find_by_id(id)
            .await
            .map_err(|e| match e {
                RepositoryError::NotFound => DomainError::UserNotFound(id),
                RepositoryError::ConnectionFailed(msg) => DomainError::Database(
                    sqlx::Error::PoolTimedOut
                ),
                other => DomainError::Internal(other.to_string()),
            })?;
        
        Ok(user)
    }
    
    pub async fn create_user(&self, request: CreateUserRequest) -> AppResult<User> {
        self.validate_request(&request)?;
        
        if self.repository.exists_by_email(&request.email).await? {
            return Err(DomainError::UserAlreadyExists(request.email));
        }
        
        let user = User::from_request(request);
        self.repository.save(&user).await?;
        
        Ok(user)
    }
    
    fn validate_request(&self, request: &CreateUserRequest) -> AppResult<()> {
        if request.username.is_empty() {
            return Err(DomainError::Validation("Username cannot be empty".into()));
        }
        
        if !request.email.contains('@') {
            return Err(DomainError::InvalidEmail(request.email.clone()));
        }
        
        Ok(())
    }
}
```

### 7.4 API 错误响应

```rust
use axum::{
    http::StatusCode,
    response::{IntoResponse, Response},
    Json,
};
use serde_json::json;

#[derive(Debug)]
pub struct ApiError {
    pub status: StatusCode,
    pub code: String,
    pub message: String,
    pub details: Option<serde_json::Value>,
}

impl IntoResponse for ApiError {
    fn into_response(self) -> Response {
        let body = json!({
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        });
        
        (self.status, Json(body)).into_response()
    }
}

impl From<DomainError> for ApiError {
    fn from(err: DomainError) -> Self {
        match err {
            DomainError::UserNotFound(id) => ApiError {
                status: StatusCode::NOT_FOUND,
                code: "USER_NOT_FOUND".into(),
                message: format!("User with ID {} not found", id),
                details: Some(json!({ "user_id": id })),
            },
            DomainError::UserAlreadyExists(email) => ApiError {
                status: StatusCode::CONFLICT,
                code: "USER_ALREADY_EXISTS".into(),
                message: format!("User with email {} already exists", email),
                details: Some(json!({ "email": email })),
            },
            DomainError::Validation(msg) => ApiError {
                status: StatusCode::BAD_REQUEST,
                code: "VALIDATION_ERROR".into(),
                message: msg,
                details: None,
            },
            DomainError::AuthenticationFailed(msg) => ApiError {
                status: StatusCode::UNAUTHORIZED,
                code: "AUTHENTICATION_FAILED".into(),
                message: msg,
                details: None,
            },
            DomainError::AuthorizationDenied(msg) => ApiError {
                status: StatusCode::FORBIDDEN,
                code: "AUTHORIZATION_DENIED".into(),
                message: msg,
                details: None,
            },
            _ => ApiError {
                status: StatusCode::INTERNAL_SERVER_ERROR,
                code: "INTERNAL_ERROR".into(),
                message: "An internal error occurred".into(),
                details: None,
            },
        }
    }
}
```

### 7.5 错误日志记录

```rust
use tracing::{error, warn, instrument};

impl UserService {
    #[instrument(skip(self), fields(user_id = %id))]
    pub async fn get_user(&self, id: Uuid) -> AppResult<User> {
        match self.repository.find_by_id(id).await {
            Ok(Some(user)) => {
                tracing::Span::current().record("username", &user.username);
                Ok(user)
            }
            Ok(None) => {
                warn!("User not found: {}", id);
                Err(DomainError::UserNotFound(id))
            }
            Err(e) => {
                error!("Database error while fetching user {}: {}", id, e);
                Err(DomainError::Internal(e.to_string()))
            }
        }
    }
}
```

---

## 8. 检查清单

### 8.1 代码提交前检查清单

- [ ] **格式化检查**
  - [ ] 运行 `cargo fmt -- --check` 确保代码格式正确
  - [ ] 所有文件使用 LF 行尾
  - [ ] 文件编码为 UTF-8 without BOM

- [ ] **静态分析检查**
  - [ ] 运行 `cargo clippy -- -D warnings` 无警告
  - [ ] 运行 `cargo clippy --all-targets --all-features -- -D warnings`
  - [ ] 修复所有 pedantic 和 nursery 级别警告

- [ ] **文档检查**
  - [ ] 所有公开 API 都有文档注释
  - [ ] 运行 `cargo doc --no-deps` 无警告
  - [ ] 示例代码可编译运行

- [ ] **测试检查**
  - [ ] 运行 `cargo test --all` 全部通过
  - [ ] 运行 `cargo test --all-features` 全部通过
  - [ ] 新增代码有对应测试覆盖
  - [ ] 边界条件已测试

- [ ] **安全检查**
  - [ ] 运行 `cargo audit` 无已知漏洞
  - [ ] unsafe 代码有安全注释
  - [ ] 敏感数据使用 `Secret<T>` 包装
  - [ ] 输入验证完整

### 8.2 代码审查检查清单

- [ ] **命名规范**
  - [ ] 类型使用 `PascalCase`
  - [ ] 函数/变量使用 `snake_case`
  - [ ] 常量使用 `SCREAMING_SNAKE_CASE`
  - [ ] 布尔类型以 `is_`, `has_`, `can_`, `should_` 开头

- [ ] **错误处理**
  - [ ] 使用 `Result<T, E>` 而非 `Option<T>` 表示可能失败的操作
  - [ ] 错误类型实现 `std::error::Error`
  - [ ] 错误消息清晰、可操作
  - [ ] 错误正确传播或处理

- [ ] **并发安全**
  - [ ] 共享状态使用 `Arc<Mutex<T>>` 或 `Arc<RwLock<T>>`
  - [ ] 避免死锁（锁顺序一致）
  - [ ] 异步代码正确使用 `.await`

- [ ] **性能考虑**
  - [ ] 避免不必要的克隆
  - [ ] 使用引用而非所有权转移（适当场景）
  - [ ] 大数据结构考虑使用 `Box`, `Rc`, `Arc`

### 8.3 发布前检查清单

- [ ] **版本检查**
  - [ ] `Cargo.toml` 版本号已更新
  - [ ] `CHANGELOG.md` 已更新
  - [ ] 依赖版本已锁定

- [ ] **构建检查**
  - [ ] `cargo build --release` 成功
  - [ ] `cargo build --all-features --release` 成功
  - [ ] 目标平台交叉编译成功

- [ ] **文档检查**
  - [ ] README.md 已更新
  - [ ] API 文档已生成
  - [ ] 迁移指南已编写（如有破坏性变更）

- [ ] **安全审计**
  - [ ] `cargo audit` 通过
  - [ ] 依赖许可证合规
  - [ ] 敏感信息未硬编码

### 8.4 依赖更新检查清单

- [ ] **更新前检查**
  - [ ] 检查 CHANGELOG 了解破坏性变更
  - [ ] 检查最低 Rust 版本要求
  - [ ] 备份 `Cargo.lock`

- [ ] **更新后检查**
  - [ ] `cargo build` 成功
  - [ ] `cargo test` 全部通过
  - [ ] `cargo clippy` 无新警告
  - [ ] 性能基准测试无退化

---

## 附录

### A. 常用命令速查

```bash
cargo fmt
cargo fmt -- --check
cargo clippy
cargo clippy -- -D warnings
cargo clippy --all-targets --all-features -- -D warnings
cargo test
cargo test --all
cargo test --all-features
cargo test -- --nocapture
cargo test <test_name>
cargo test --test <integration_test>
cargo bench
cargo doc --open
cargo doc --no-deps
cargo audit
cargo tree
cargo tree --duplicates
cargo outdated
cargo build --release
cargo publish --dry-run
```

### B. 推荐工具

| 工具 | 用途 | 安装命令 |
|------|------|----------|
| `rustfmt` | 代码格式化 | `rustup component add rustfmt` |
| `clippy` | 静态分析 | `rustup component add clippy` |
| `cargo-audit` | 安全审计 | `cargo install cargo-audit` |
| `cargo-tree` | 依赖树 | `cargo install cargo-tree` |
| `cargo-outdated` | 依赖更新检查 | `cargo install cargo-outdated` |
| `cargo-nextest` | 增强测试运行器 | `cargo install cargo-nextest` |
| `cargo-watch` | 文件监视 | `cargo install cargo-watch` |
| `cargo-flamegraph` | 性能分析 | `cargo install flamegraph` |

### C. 参考资源

- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)
- [The Rust Programming Language Book](https://doc.rust-lang.org/book/)
- [Rust by Example](https://doc.rust-lang.org/rust-by-example/)
- [Rust Design Patterns](https://rust-unofficial.github.io/patterns/)
- [Effective Rust](https://www.lurklurk.org/effective-rust/)
- [Rust Security Guidelines](https://anssi-fr.github.io/rust-guide/)

---

> 文档版本: 1.9.0 | 最后更新: 2026-04-28
