# Go 开发规范

> 版本: 1.0.0 | 更新日期: 2026-04-17 | 编码: UTF-8 | 行尾: LF

---

## 目录

1. [命名规范与代码风格](#1-命名规范与代码风格)
2. [项目布局规范](#2-项目布局规范)
3. [依赖管理规范](#3-依赖管理规范)
4. [测试规范](#4-测试规范)
5. [并发安全规范](#5-并发安全规范)
6. [错误处理规范](#6-错误处理规范)
7. [常见框架规范](#7-常见框架规范)
8. [检查清单](#8-检查清单)

---

## 1. 命名规范与代码风格

### 1.1 包命名

```go
// 推荐: 简短、小写、单个单词
package user
package httputil
package jsonparser

// 避免: 下划线、驼峰、复数
package user_service  // 错误
package userService   // 错误
package users         // 避免
```

### 1.2 变量命名

```go
// 驼峰命名法
var userName string
var maxRetryCount int

// 导出变量: 首字母大写
var MaxConnections = 100
var DefaultTimeout = 30 * time.Second

// 私有变量: 首字母小写
var internalCounter int
var cacheSize int

// 短变量声明
for i, v := range values {
    fmt.Printf("index: %d, value: %s\n", i, v)
}

// 布尔变量: 使用 is/has/can/should 前缀
var isValid bool
var hasPermission bool
var canDelete bool
```

### 1.3 函数命名

```go
// 导出函数: 首字母大写
func GetUserByID(id int64) (*User, error) {
    // ...
}

// 私有函数: 首字母小写
func validateEmail(email string) bool {
    // ...
}

// 构造函数: NewXxx 模式
func NewUser(name string) *User {
    return &User{Name: name}
}

func NewUserService(repo UserRepository) *UserService {
    return &UserService{repo: repo}
}

// 接口方法命名
type Reader interface {
    Read(p []byte) (n int, err error)
}

// 单一职责: 动词+名词
func CalculateTotal(items []Item) float64
func SendEmail(to string, body string) error
func ParseConfig(path string) (*Config, error)
```

### 1.4 接口命名

```go
// 单方法接口: 动词+er 后缀
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type Closer interface {
    Close() error
}

// 组合接口
type ReadWriter interface {
    Reader
    Writer
}

type ReadWriteCloser interface {
    Reader
    Writer
    Closer
}

// 业务接口: 描述行为
type UserRepository interface {
    GetByID(ctx context.Context, id int64) (*User, error)
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id int64) error
}
```

### 1.5 常量命名

```go
// 导出常量: 首字母大写
const (
    MaxRetryCount     = 3
    DefaultTimeout    = 30 * time.Second
    MaxBufferSize     = 1024 * 1024
)

// 私有常量: 首字母小写
const (
    defaultPort       = 8080
    maxConnectionPool = 100
)

// 枚举常量: iota
type Status int

const (
    StatusPending Status = iota
    StatusActive
    StatusInactive
    StatusDeleted
)

// 带类型的常量组
type UserRole string

const (
    RoleAdmin   UserRole = "admin"
    RoleUser    UserRole = "user"
    RoleGuest   UserRole = "guest"
)
```

### 1.6 结构体命名

```go
// 导出结构体: 首字母大写
type User struct {
    ID        int64     `json:"id"`
    Name      string    `json:"name"`
    Email     string    `json:"email"`
    CreatedAt time.Time `json:"created_at"`
    UpdatedAt time.Time `json:"updated_at"`
}

// 私有结构体: 首字母小写
type userCache struct {
    data map[int64]*User
    mu   sync.RWMutex
}

// 配置结构体: Config 后缀
type ServerConfig struct {
    Host         string        `yaml:"host"`
    Port         int           `yaml:"port"`
    ReadTimeout  time.Duration `yaml:"read_timeout"`
    WriteTimeout time.Duration `yaml:"write_timeout"`
}

// 请求/响应结构体
type CreateUserRequest struct {
    Name  string `json:"name" binding:"required"`
    Email string `json:"email" binding:"required,email"`
}

type UserResponse struct {
    ID    int64  `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}
```

### 1.7 代码格式化

```go
// 使用 gofmt 格式化
// gofmt -w .

// 使用 goimports 管理导入
// goimports -w .

// 导入分组
import (
    // 标准库
    "context"
    "fmt"
    "net/http"
    "time"

    // 第三方库
    "github.com/gin-gonic/gin"
    "github.com/jmoiron/sqlx"
    "go.uber.org/zap"

    // 本地包
    "myapp/internal/user"
    "myapp/pkg/config"
)
```

---

## 2. 项目布局规范

### 2.1 标准项目结构

```
myapp/
├── cmd/                          # 主程序入口
│   ├── api/
│   │   └── main.go              # API 服务入口
│   ├── worker/
│   │   └── main.go              # Worker 服务入口
│   └── cli/
│       └── main.go              # CLI 工具入口
│
├── internal/                     # 私有应用代码
│   ├── user/                    # 用户模块
│   │   ├── handler.go           # HTTP 处理器
│   │   ├── service.go           # 业务逻辑
│   │   ├── repository.go        # 数据访问
│   │   └── model.go             # 领域模型
│   ├── auth/                    # 认证模块
│   ├── order/                   # 订单模块
│   └── middleware/              # 中间件
│       ├── auth.go
│       ├── logging.go
│       └── recovery.go
│
├── pkg/                          # 可被外部引用的公共库
│   ├── config/
│   │   └── config.go
│   ├── logger/
│   │   └── logger.go
│   ├── validator/
│   │   └── validator.go
│   └── httputil/
│       └── response.go
│
├── api/                          # API 定义
│   ├── openapi/
│   │   └── openapi.yaml
│   └── proto/
│       └── user.proto
│
├── configs/                      # 配置文件
│   ├── config.yaml
│   ├── config.dev.yaml
│   └── config.prod.yaml
│
├── scripts/                      # 脚本文件
│   ├── build.sh
│   ├── migrate.sh
│   └── docker-entrypoint.sh
│
├── deployments/                  # 部署配置
│   ├── docker/
│   │   ├── Dockerfile
│   │   └── docker-compose.yaml
│   └── k8s/
│       ├── deployment.yaml
│       └── service.yaml
│
├── docs/                         # 文档
│   ├── api/
│   ├── design/
│   └── adr/
│
├── test/                         # 集成测试
│   ├── integration/
│   └── e2e/
│
├── go.mod
├── go.sum
├── Makefile
├── README.md
└── .gitignore
```

### 2.2 目录职责说明

| 目录 | 职责 | 可见性 |
|------|------|--------|
| `cmd/` | 应用程序入口点，每个子目录一个可执行程序 | 公开 |
| `internal/` | 私有应用代码，不可被外部导入 | 私有 |
| `pkg/` | 可被外部引用的公共库 | 公开 |
| `api/` | API 协议定义（OpenAPI、Proto） | 公开 |
| `configs/` | 配置文件模板 | 公开 |
| `scripts/` | 构建、安装、分析等脚本 | 公开 |
| `deployments/` | 部署配置（Docker、K8s） | 公开 |
| `docs/` | 设计文档、用户文档 | 公开 |
| `test/` | 额外的外部测试应用和测试数据 | 公开 |

### 2.3 模块内分层架构

```
internal/user/
├── model.go           # 领域模型/实体
├── dto.go             # 数据传输对象
├── repository.go      # 数据访问接口
├── service.go         # 业务逻辑
├── handler.go         # HTTP 处理器
└── user_test.go       # 单元测试
```

```go
// model.go - 领域模型
package user

type User struct {
    ID        int64
    Name      string
    Email     string
    CreatedAt time.Time
    UpdatedAt time.Time
}

// dto.go - 数据传输对象
type CreateUserRequest struct {
    Name  string `json:"name" validate:"required"`
    Email string `json:"email" validate:"required,email"`
}

type UserResponse struct {
    ID    int64  `json:"id"`
    Name  string `json:"name"`
    Email string `json:"email"`
}

// repository.go - 数据访问接口
type Repository interface {
    GetByID(ctx context.Context, id int64) (*User, error)
    Create(ctx context.Context, user *User) error
    Update(ctx context.Context, user *User) error
    Delete(ctx context.Context, id int64) error
}

// service.go - 业务逻辑
type Service struct {
    repo Repository
}

func NewService(repo Repository) *Service {
    return &Service{repo: repo}
}

func (s *Service) Create(ctx context.Context, req *CreateUserRequest) (*User, error) {
    user := &User{
        Name:  req.Name,
        Email: req.Email,
    }
    if err := s.repo.Create(ctx, user); err != nil {
        return nil, fmt.Errorf("create user: %w", err)
    }
    return user, nil
}

// handler.go - HTTP 处理器
type Handler struct {
    service *Service
}

func NewHandler(service *Service) *Handler {
    return &Handler{service: service}
}

func (h *Handler) Create(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    user, err := h.service.Create(c.Request.Context(), &req)
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusCreated, UserResponse{
        ID:    user.ID,
        Name:  user.Name,
        Email: user.Email,
    })
}
```

---

## 3. 依赖管理规范

### 3.1 go.mod 文件

```go
// go.mod 示例
module github.com/myorg/myapp

go 1.22

require (
    github.com/gin-gonic/gin v1.9.1
    github.com/jmoiron/sqlx v1.3.5
    github.com/redis/go-redis/v9 v9.3.0
    go.uber.org/zap v1.26.0
)

require (
    github.com/bytedance/sonic v1.10.2 // indirect
    github.com/gabriel-vasile/mimetype v1.4.3 // indirect
)
```

### 3.2 依赖管理命令

```bash
# 初始化模块
go mod init github.com/myorg/myapp

# 下载依赖
go mod download

# 整理依赖（添加缺失的、移除未使用的）
go mod tidy

# 验证依赖
go mod verify

# 查看依赖图
go mod graph

# 查看为什么需要某个依赖
go mod why github.com/gin-gonic/gin

# 添加特定版本依赖
go get github.com/gin-gonic/gin@v1.9.1

# 更新所有依赖
go get -u ./...

# 更新到最新补丁版本
go get -u=patch ./...

# 清理模块缓存
go clean -modcache
```

### 3.3 版本选择规则

```bash
# 语义化版本: vMAJOR.MINOR.PATCH
# MAJOR: 不兼容的 API 变更
# MINOR: 向后兼容的功能新增
# PATCH: 向后兼容的问题修复

# 选择特定版本
go get github.com/gin-gonic/gin@v1.9.1

# 选择版本范围
go get github.com/gin-gonic/gin@>=v1.9.0

# 选择最新版本
go get github.com/gin-gonic/gin@latest

# 选择特定 commit
go get github.com/gin-gonic/gin@abc123

# 使用 replace 指令（本地开发）
replace github.com/myorg/mylib => ../mylib

// go.mod
replace (
    github.com/myorg/mylib => ../mylib
    github.com/old/pkg => github.com/new/pkg v1.0.0
)

# 使用 exclude 排除有问题的版本
exclude github.com/bad/package v1.0.0
```

### 3.4 私有模块配置

```bash
# 设置私有模块（跳过校验和验证）
go env -w GOPRIVATE=github.com/myorg/*

# 设置代理
go env -w GOPROXY=https://proxy.golang.org,direct
go env -w GOPROXY=https://goproxy.cn,direct  # 中国区

# 设置校验和数据库
go env -w GOSUMDB=sum.golang.org
go env -w GOSUMDB=off  # 禁用（不推荐）

# 查看当前配置
go env
```

### 3.5 vendor 目录

```bash
# 创建 vendor 目录
go mod vendor

# 使用 vendor 目录构建
go build -mod=vendor

# 使用 vendor 目录运行测试
go test -mod=vendor ./...
```

---

## 4. 测试规范

### 4.1 测试文件组织

```
internal/user/
├── user.go
├── user_test.go          # 单元测试
├── user_bench_test.go    # 基准测试
├── user_example_test.go  # 示例测试
└── testdata/             # 测试数据
    ├── input.json
    └── golden.json
```

### 4.2 单元测试

```go
// user_test.go
package user

import (
    "context"
    "errors"
    "testing"

    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/mock"
    "github.com/stretchr/testify/require"
)

// 基本测试
func TestUser_Validate(t *testing.T) {
    tests := []struct {
        name    string
        user    *User
        wantErr bool
    }{
        {
            name: "valid user",
            user: &User{Name: "John", Email: "john@example.com"},
            wantErr: false,
        },
        {
            name: "empty name",
            user: &User{Name: "", Email: "john@example.com"},
            wantErr: true,
        },
        {
            name: "invalid email",
            user: &User{Name: "John", Email: "invalid-email"},
            wantErr: true,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := tt.user.Validate()
            if tt.wantErr {
                assert.Error(t, err)
            } else {
                assert.NoError(t, err)
            }
        })
    }
}

// 使用 testify/assert
func TestService_Create(t *testing.T) {
    // 准备
    mockRepo := NewMockRepository(t)
    service := NewService(mockRepo)

    ctx := context.Background()
    req := &CreateUserRequest{
        Name:  "John",
        Email: "john@example.com",
    }

    mockRepo.On("Create", ctx, mock.AnythingOfType("*user.User")).
        Return(nil).
        Run(func(args mock.Arguments) {
            user := args.Get(1).(*User)
            user.ID = 1
        })

    // 执行
    user, err := service.Create(ctx, req)

    // 断言
    require.NoError(t, err)
    assert.Equal(t, int64(1), user.ID)
    assert.Equal(t, "John", user.Name)
    mockRepo.AssertExpectations(t)
}

// 使用 testify/require（失败时立即停止）
func TestService_GetByID(t *testing.T) {
    mockRepo := NewMockRepository(t)
    service := NewService(mockRepo)

    ctx := context.Background()
    expectedUser := &User{ID: 1, Name: "John"}

    mockRepo.On("GetByID", ctx, int64(1)).Return(expectedUser, nil)

    user, err := service.GetByID(ctx, 1)
    require.NoError(t, err)
    require.NotNil(t, user)
    assert.Equal(t, expectedUser, user)
}

// 表驱动测试
func TestParseEmail(t *testing.T) {
    tests := []struct {
        name     string
        input    string
        wantUser string
        wantHost string
        wantErr  error
    }{
        {
            name:     "valid email",
            input:    "user@example.com",
            wantUser: "user",
            wantHost: "example.com",
            wantErr:  nil,
        },
        {
            name:    "missing @",
            input:   "userexample.com",
            wantErr: ErrInvalidEmail,
        },
        {
            name:    "empty string",
            input:   "",
            wantErr: ErrInvalidEmail,
        },
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            user, host, err := ParseEmail(tt.input)
            if tt.wantErr != nil {
                assert.ErrorIs(t, err, tt.wantErr)
                return
            }
            require.NoError(t, err)
            assert.Equal(t, tt.wantUser, user)
            assert.Equal(t, tt.wantHost, host)
        })
    }
}
```

### 4.3 Mock 测试

```go
// mock_repository.go
package user

import (
    "context"

    "github.com/stretchr/testify/mock"
)

type MockRepository struct {
    mock.Mock
}

func NewMockRepository(t *testing.T) *MockRepository {
    m := &MockRepository{}
    m.Test(t)
    return m
}

func (m *MockRepository) GetByID(ctx context.Context, id int64) (*User, error) {
    args := m.Called(ctx, id)
    if args.Get(0) == nil {
        return nil, args.Error(1)
    }
    return args.Get(0).(*User), args.Error(1)
}

func (m *MockRepository) Create(ctx context.Context, user *User) error {
    args := m.Called(ctx, user)
    return args.Error(0)
}

func (m *MockRepository) Update(ctx context.Context, user *User) error {
    args := m.Called(ctx, user)
    return args.Error(0)
}

func (m *MockRepository) Delete(ctx context.Context, id int64) error {
    args := m.Called(ctx, id)
    return args.Error(0)
}
```

### 4.4 基准测试

```go
// user_bench_test.go
package user

import "testing"

func BenchmarkValidate(b *testing.B) {
    user := &User{
        Name:  "John Doe",
        Email: "john@example.com",
    }

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _ = user.Validate()
    }
}

func BenchmarkService_Create(b *testing.B) {
    mockRepo := &MockRepository{}
    service := NewService(mockRepo)
    ctx := context.Background()
    req := &CreateUserRequest{
        Name:  "John",
        Email: "john@example.com",
    }

    mockRepo.On("Create", ctx, mock.Anything).Return(nil)

    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        _, _ = service.Create(ctx, req)
    }
}

// 并行基准测试
func BenchmarkService_CreateParallel(b *testing.B) {
    mockRepo := &MockRepository{}
    service := NewService(mockRepo)
    ctx := context.Background()

    mockRepo.On("Create", ctx, mock.Anything).Return(nil)

    b.RunParallel(func(pb *testing.PB) {
        req := &CreateUserRequest{
            Name:  "John",
            Email: "john@example.com",
        }
        for pb.Next() {
            _, _ = service.Create(ctx, req)
        }
    })
}
```

### 4.5 示例测试

```go
// user_example_test.go
package user_test

import (
    "fmt"

    "github.com/myorg/myapp/internal/user"
)

func ExampleUser_Validate() {
    u := &user.User{
        Name:  "John Doe",
        Email: "john@example.com",
    }

    err := u.Validate()
    if err != nil {
        fmt.Println("validation failed:", err)
    } else {
        fmt.Println("validation passed")
    }
    // Output: validation passed
}

func ExampleParseEmail() {
    user, host, err := user.ParseEmail("john@example.com")
    if err != nil {
        fmt.Println("error:", err)
        return
    }
    fmt.Printf("user: %s, host: %s\n", user, host)
    // Output: user: john, host: example.com
}
```

### 4.6 测试覆盖率

```bash
# 运行测试并生成覆盖率报告
go test -cover ./...

# 生成详细覆盖率报告
go test -coverprofile=coverage.out ./...

# 查看覆盖率详情
go tool cover -func=coverage.out

# 生成 HTML 覆盖率报告
go tool cover -html=coverage.out -o coverage.html

# 按包查看覆盖率
go test -coverpkg=./internal/... ./...

# 设置覆盖率目标（CI 中使用）
go test -cover -coverprofile=coverage.out ./...
go tool cover -func=coverage.out | grep total | awk '{print $3}' | \
    awk -F. '{if ($1 < 80) exit 1}'
```

### 4.7 测试运行命令

```bash
# 运行所有测试
go test ./...

# 运行特定包的测试
go test ./internal/user/...

# 运行特定测试
go test -run TestUser_Validate ./...

# 运行匹配模式的测试
go test -run "TestUser.*" ./...

# 运行基准测试
go test -bench=. ./...

# 运行特定基准测试
go test -bench=BenchmarkValidate ./...

# 显示详细输出
go test -v ./...

# 运行测试并检测竞态条件
go test -race ./...

# 短测试（跳过长时间运行的测试）
go test -short ./...

# 设置超时
go test -timeout 30s ./...

# 并行运行测试
go test -parallel 4 ./...

# 生成 CPU profile
go test -cpuprofile=cpu.prof ./...

# 生成内存 profile
go test -memprofile=mem.prof ./...

# 分析 profile
go tool pprof cpu.prof
```

---

## 5. 并发安全规范

### 5.1 互斥锁保护

```go
package cache

import "sync"

type SafeCache struct {
    mu   sync.RWMutex
    data map[string]interface{}
}

func NewSafeCache() *SafeCache {
    return &SafeCache{
        data: make(map[string]interface{}),
    }
}

// 写操作使用写锁
func (c *SafeCache) Set(key string, value interface{}) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.data[key] = value
}

// 读操作使用读锁
func (c *SafeCache) Get(key string) (interface{}, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    value, ok := c.data[key]
    return value, ok
}

// 删除操作使用写锁
func (c *SafeCache) Delete(key string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    delete(c.data, key)
}

// 复合操作需要全程持有写锁
func (c *SafeCache) GetOrSet(key string, fn func() (interface{}, error)) (interface{}, error) {
    c.mu.RLock()
    if value, ok := c.data[key]; ok {
        c.mu.RUnlock()
        return value, nil
    }
    c.mu.RUnlock()

    c.mu.Lock()
    defer c.mu.Unlock()

    if value, ok := c.data[key]; ok {
        return value, nil
    }

    value, err := fn()
    if err != nil {
        return nil, err
    }
    c.data[key] = value
    return value, nil
}
```

### 5.2 sync.Map 使用

```go
package cache

import "sync"

type SyncMapCache struct {
    data sync.Map
}

func NewSyncMapCache() *SyncMapCache {
    return &SyncMapCache{}
}

func (c *SyncMapCache) Set(key string, value interface{}) {
    c.data.Store(key, value)
}

func (c *SyncMapCache) Get(key string) (interface{}, bool) {
    return c.data.Load(key)
}

func (c *SyncMapCache) Delete(key string) {
    c.data.Delete(key)
}

func (c *SyncMapCache) Range(fn func(key, value interface{}) bool) {
    c.data.Range(fn)
}

// 原子加载或存储
func (c *SyncMapCache) GetOrSet(key string, value interface{}) (actual interface{}, loaded bool) {
    return c.data.LoadOrStore(key, value)
}
```

### 5.3 Channel 通信

```go
package worker

import (
    "context"
    "sync"
)

type Task struct {
    ID   int
    Data interface{}
}

type WorkerPool struct {
    tasks    chan Task
    results  chan error
    workers  int
    wg       sync.WaitGroup
}

func NewWorkerPool(workers int, bufferSize int) *WorkerPool {
    return &WorkerPool{
        tasks:   make(chan Task, bufferSize),
        results: make(chan error, bufferSize),
        workers: workers,
    }
}

func (p *WorkerPool) Start(ctx context.Context, handler func(Task) error) {
    for i := 0; i < p.workers; i++ {
        p.wg.Add(1)
        go func() {
            defer p.wg.Done()
            for {
                select {
                case <-ctx.Done():
                    return
                case task, ok := <-p.tasks:
                    if !ok {
                        return
                    }
                    err := handler(task)
                    select {
                    case p.results <- err:
                    case <-ctx.Done():
                        return
                    }
                }
            }
        }()
    }
}

func (p *WorkerPool) Submit(task Task) bool {
    select {
    case p.tasks <- task:
        return true
    default:
        return false
    }
}

func (p *WorkerPool) Stop() {
    close(p.tasks)
    p.wg.Wait()
    close(p.results)
}

func (p *WorkerPool) Results() <-chan error {
    return p.results
}
```

### 5.4 Context 超时控制

```go
package service

import (
    "context"
    "time"
)

func (s *Service) ProcessWithTimeout(ctx context.Context, id int64) error {
    ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
    defer cancel()

    result, err := s.repo.GetByID(ctx, id)
    if err != nil {
        return fmt.Errorf("get by id: %w", err)
    }

    select {
    case <-ctx.Done():
        return ctx.Err()
    default:
    }

    return s.process(ctx, result)
}

func (s *Service) ProcessWithDeadline(ctx context.Context, id int64, deadline time.Time) error {
    ctx, cancel := context.WithDeadline(ctx, deadline)
    defer cancel()

    return s.process(ctx, id)
}

func (s *Service) ProcessWithCancel(ctx context.Context, id int64) (context.CancelFunc, <-chan error) {
    ctx, cancel := context.WithCancel(ctx)
    errCh := make(chan error, 1)

    go func() {
        defer close(errCh)
        errCh <- s.process(ctx, id)
    }()

    return cancel, errCh
}
```

### 5.5 并发安全检查清单

```go
// 使用 -race 标志检测竞态条件
// go test -race ./...

// 避免: 全局变量共享状态
var counter int  // 危险: 并发不安全

// 正确: 使用锁保护
var (
    counterMu sync.Mutex
    counter   int
)

func incrementCounter() {
    counterMu.Lock()
    counter++
    counterMu.Unlock()
}

// 避免: 在 goroutine 中直接使用循环变量
for _, item := range items {
    go func() {
        process(item)  // 错误: item 可能被覆盖
    }()
}

// 正确: 传递参数
for _, item := range items {
    go func(i Item) {
        process(i)
    }(item)
}

// 避免: goroutine 泄漏
func leak() {
    ch := make(chan int)
    go func() {
        ch <- 1  // 如果没有接收者，goroutine 会一直阻塞
    }()
}

// 正确: 使用 select + context
func noLeak(ctx context.Context) error {
    ch := make(chan int, 1)
    go func() {
        ch <- compute()
    }()

    select {
    case <-ctx.Done():
        return ctx.Err()
    case result := <-ch:
        return processResult(result)
    }
}
```

---

## 6. 错误处理规范

### 6.1 错误创建

```go
package errors

import (
    "errors"
    "fmt"
)

// 简单错误
var (
    ErrNotFound      = errors.New("resource not found")
    ErrUnauthorized  = errors.New("unauthorized access")
    ErrInvalidInput  = errors.New("invalid input")
    ErrInternalError = errors.New("internal server error")
)

// 格式化错误
func NewValidationError(field string, value interface{}) error {
    return fmt.Errorf("validation failed for field %s: invalid value %v", field, value)
}

// 自定义错误类型
type BusinessError struct {
    Code    string
    Message string
    Cause   error
}

func (e *BusinessError) Error() string {
    if e.Cause != nil {
        return fmt.Sprintf("[%s] %s: %v", e.Code, e.Message, e.Cause)
    }
    return fmt.Sprintf("[%s] %s", e.Code, e.Message)
}

func (e *BusinessError) Unwrap() error {
    return e.Cause
}

func NewBusinessError(code, message string, cause error) *BusinessError {
    return &BusinessError{
        Code:    code,
        Message: message,
        Cause:   cause,
    }
}

// 预定义业务错误
var (
    ErrUserNotFound = &BusinessError{Code: "USER_001", Message: "user not found"}
    ErrUserExists   = &BusinessError{Code: "USER_002", Message: "user already exists"}
)
```

### 6.2 错误包装

```go
package service

import (
    "fmt"
)

func (s *Service) GetUser(ctx context.Context, id int64) (*User, error) {
    user, err := s.repo.GetByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("get user by id %d: %w", id, err)
    }
    return user, nil
}

func (s *Service) CreateUser(ctx context.Context, req *CreateUserRequest) (*User, error) {
    if err := req.Validate(); err != nil {
        return nil, fmt.Errorf("validate request: %w", err)
    }

    user := &User{
        Name:  req.Name,
        Email: req.Email,
    }

    if err := s.repo.Create(ctx, user); err != nil {
        return nil, fmt.Errorf("create user in repository: %w", err)
    }

    return user, nil
}
```

### 6.3 错误解包与判断

```go
package service

import (
    "errors"
    "fmt"

    "github.com/myorg/myapp/internal/errors"
)

func (s *Service) ProcessUser(ctx context.Context, id int64) error {
    user, err := s.GetUser(ctx, id)
    if err != nil {
        if errors.Is(err, ErrNotFound) {
            return fmt.Errorf("user %d does not exist: %w", id, err)
        }
        return fmt.Errorf("failed to get user: %w", err)
    }

    return nil
}

func (s *Service) HandleError(err error) {
    var businessErr *errors.BusinessError
    if errors.As(err, &businessErr) {
        fmt.Printf("Business error: code=%s, message=%s\n", businessErr.Code, businessErr.Message)
        return
    }

    if errors.Is(err, ErrNotFound) {
        fmt.Println("Resource not found")
        return
    }

    fmt.Printf("Unknown error: %v\n", err)
}
```

### 6.4 错误处理模式

```go
// 模式 1: 立即返回
func (s *Service) Method1(ctx context.Context, id int64) (*User, error) {
    user, err := s.repo.GetByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("get user: %w", err)
    }

    if err := s.validate(user); err != nil {
        return nil, fmt.Errorf("validate user: %w", err)
    }

    return user, nil
}

// 模式 2: 错误收集
func (s *Service) ValidateAll(user *User) error {
    var errs []error

    if user.Name == "" {
        errs = append(errs, errors.New("name is required"))
    }

    if user.Email == "" {
        errs = append(errs, errors.New("email is required"))
    }

    if !isValidEmail(user.Email) {
        errs = append(errs, errors.New("email is invalid"))
    }

    if len(errs) > 0 {
        return fmt.Errorf("validation errors: %v", errs)
    }

    return nil
}

// 模式 3: 错误恢复
func (s *Service) SafeExecute(fn func() error) (err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("panic recovered: %v", r)
        }
    }()
    return fn()
}

// 模式 4: 重试
func (s *Service) Retry(ctx context.Context, maxAttempts int, fn func() error) error {
    var lastErr error
    for i := 0; i < maxAttempts; i++ {
        err := fn()
        if err == nil {
            return nil
        }
        lastErr = err

        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(time.Second * time.Duration(i+1)):
        }
    }
    return fmt.Errorf("after %d attempts: %w", maxAttempts, lastErr)
}
```

### 6.5 HTTP 错误响应

```go
package httputil

import (
    "net/http"

    "github.com/gin-gonic/gin"
)

type ErrorResponse struct {
    Code    string `json:"code"`
    Message string `json:"message"`
    Details string `json:"details,omitempty"`
}

func SendError(c *gin.Context, status int, code, message string, err error) {
    resp := ErrorResponse{
        Code:    code,
        Message: message,
    }
    if err != nil {
        resp.Details = err.Error()
    }
    c.JSON(status, resp)
}

func BadRequest(c *gin.Context, message string, err error) {
    SendError(c, http.StatusBadRequest, "BAD_REQUEST", message, err)
}

func Unauthorized(c *gin.Context, message string) {
    SendError(c, http.StatusUnauthorized, "UNAUTHORIZED", message, nil)
}

func Forbidden(c *gin.Context, message string) {
    SendError(c, http.StatusForbidden, "FORBIDDEN", message, nil)
}

func NotFound(c *gin.Context, message string) {
    SendError(c, http.StatusNotFound, "NOT_FOUND", message, nil)
}

func InternalError(c *gin.Context, message string, err error) {
    SendError(c, http.StatusInternalServerError, "INTERNAL_ERROR", message, err)
}

// 使用示例
func (h *Handler) GetUser(c *gin.Context) {
    id, err := strconv.ParseInt(c.Param("id"), 10, 64)
    if err != nil {
        httputil.BadRequest(c, "invalid user id", err)
        return
    }

    user, err := h.service.GetByID(c.Request.Context(), id)
    if err != nil {
        if errors.Is(err, user.ErrNotFound) {
            httputil.NotFound(c, "user not found")
            return
        }
        httputil.InternalError(c, "failed to get user", err)
        return
    }

    c.JSON(http.StatusOK, user)
}
```

---

## 7. 常见框架规范

### 7.1 Gin 框架

#### 项目结构

```
cmd/api/
└── main.go

internal/
├── handler/
│   ├── user_handler.go
│   └── auth_handler.go
├── middleware/
│   ├── auth.go
│   ├── logging.go
│   └── recovery.go
├── service/
│   ├── user_service.go
│   └── auth_service.go
├── repository/
│   └── user_repository.go
└── model/
    └── user.go

pkg/
├── config/
├── logger/
└── response/
```

#### 主入口

```go
// cmd/api/main.go
package main

import (
    "context"
    "log"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "github.com/gin-gonic/gin"
    "github.com/myorg/myapp/internal/handler"
    "github.com/myorg/myapp/internal/middleware"
    "github.com/myorg/myapp/internal/repository"
    "github.com/myorg/myapp/internal/service"
    "github.com/myorg/myapp/pkg/config"
    "github.com/myorg/myapp/pkg/logger"
)

func main() {
    cfg := config.Load()
    log := logger.New(cfg.LogLevel)

    db, err := repository.NewDB(cfg.Database)
    if err != nil {
        log.Fatal("failed to connect database", "error", err)
    }

    userRepo := repository.NewUserRepository(db)
    userService := service.NewUserService(userRepo)
    userHandler := handler.NewUserHandler(userService)

    r := gin.New()
    r.Use(
        middleware.Recovery(log),
        middleware.Logging(log),
        middleware.CORS(),
    )

    v1 := r.Group("/api/v1")
    {
        users := v1.Group("/users")
        {
            users.GET("", userHandler.List)
            users.GET("/:id", userHandler.GetByID)
            users.POST("", userHandler.Create)
            users.PUT("/:id", userHandler.Update)
            users.DELETE("/:id", userHandler.Delete)
        }
    }

    srv := &http.Server{
        Addr:         ":" + cfg.Port,
        Handler:      r,
        ReadTimeout:  10 * time.Second,
        WriteTimeout: 10 * time.Second,
    }

    go func() {
        if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Fatal("server error", "error", err)
        }
    }()

    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    if err := srv.Shutdown(ctx); err != nil {
        log.Fatal("server shutdown error", "error", err)
    }
}
```

#### Handler 规范

```go
// internal/handler/user_handler.go
package handler

import (
    "net/http"
    "strconv"

    "github.com/gin-gonic/gin"

    "github.com/myorg/myapp/internal/service"
    "github.com/myorg/myapp/pkg/response"
)

type UserHandler struct {
    service *service.UserService
}

func NewUserHandler(service *service.UserService) *UserHandler {
    return &UserHandler{service: service}
}

func (h *UserHandler) RegisterRoutes(r *gin.RouterGroup) {
    users := r.Group("/users")
    {
        users.GET("", h.List)
        users.GET("/:id", h.GetByID)
        users.POST("", h.Create)
        users.PUT("/:id", h.Update)
        users.DELETE("/:id", h.Delete)
    }
}

type ListUsersRequest struct {
    Page     int    `form:"page" binding:"min=1"`
    PageSize int    `form:"page_size" binding:"min=1,max=100"`
    Name     string `form:"name"`
    Email    string `form:"email"`
}

type CreateUserRequest struct {
    Name  string `json:"name" binding:"required,min=2,max=100"`
    Email string `json:"email" binding:"required,email"`
}

type UpdateUserRequest struct {
    Name  string `json:"name" binding:"omitempty,min=2,max=100"`
    Email string `json:"email" binding:"omitempty,email"`
}

func (h *UserHandler) List(c *gin.Context) {
    var req ListUsersRequest
    if err := c.ShouldBindQuery(&req); err != nil {
        response.BadRequest(c, "invalid query parameters", err)
        return
    }

    if req.Page == 0 {
        req.Page = 1
    }
    if req.PageSize == 0 {
        req.PageSize = 10
    }

    users, total, err := h.service.List(c.Request.Context(), req.Page, req.PageSize, req.Name, req.Email)
    if err != nil {
        response.InternalError(c, "failed to list users", err)
        return
    }

    response.SuccessWithPage(c, users, total, req.Page, req.PageSize)
}

func (h *UserHandler) GetByID(c *gin.Context) {
    id, err := strconv.ParseInt(c.Param("id"), 10, 64)
    if err != nil {
        response.BadRequest(c, "invalid user id", err)
        return
    }

    user, err := h.service.GetByID(c.Request.Context(), id)
    if err != nil {
        response.NotFound(c, "user not found")
        return
    }

    response.Success(c, user)
}

func (h *UserHandler) Create(c *gin.Context) {
    var req CreateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.BadRequest(c, "invalid request body", err)
        return
    }

    user, err := h.service.Create(c.Request.Context(), &req)
    if err != nil {
        response.InternalError(c, "failed to create user", err)
        return
    }

    response.Created(c, user)
}

func (h *UserHandler) Update(c *gin.Context) {
    id, err := strconv.ParseInt(c.Param("id"), 10, 64)
    if err != nil {
        response.BadRequest(c, "invalid user id", err)
        return
    }

    var req UpdateUserRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        response.BadRequest(c, "invalid request body", err)
        return
    }

    user, err := h.service.Update(c.Request.Context(), id, &req)
    if err != nil {
        response.InternalError(c, "failed to update user", err)
        return
    }

    response.Success(c, user)
}

func (h *UserHandler) Delete(c *gin.Context) {
    id, err := strconv.ParseInt(c.Param("id"), 10, 64)
    if err != nil {
        response.BadRequest(c, "invalid user id", err)
        return
    }

    if err := h.service.Delete(c.Request.Context(), id); err != nil {
        response.InternalError(c, "failed to delete user", err)
        return
    }

    response.NoContent(c)
}
```

#### 中间件规范

```go
// internal/middleware/auth.go
package middleware

import (
    "net/http"
    "strings"

    "github.com/gin-gonic/gin"
    "github.com/golang-jwt/jwt/v5"
)

type Claims struct {
    UserID int64  `json:"user_id"`
    Role   string `json:"role"`
    jwt.RegisteredClaims
}

func Auth(jwtSecret string) gin.HandlerFunc {
    return func(c *gin.Context) {
        authHeader := c.GetHeader("Authorization")
        if authHeader == "" {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "error": "authorization header required",
            })
            return
        }

        parts := strings.SplitN(authHeader, " ", 2)
        if len(parts) != 2 || parts[0] != "Bearer" {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "error": "invalid authorization header format",
            })
            return
        }

        tokenString := parts[1]
        claims := &Claims{}

        token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
            return []byte(jwtSecret), nil
        })

        if err != nil || !token.Valid {
            c.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{
                "error": "invalid token",
            })
            return
        }

        c.Set("user_id", claims.UserID)
        c.Set("role", claims.Role)
        c.Next()
    }
}

func RequireRole(roles ...string) gin.HandlerFunc {
    return func(c *gin.Context) {
        role, exists := c.Get("role")
        if !exists {
            c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
                "error": "role not found",
            })
            return
        }

        userRole := role.(string)
        for _, r := range roles {
            if userRole == r {
                c.Next()
                return
            }
        }

        c.AbortWithStatusJSON(http.StatusForbidden, gin.H{
            "error": "insufficient permissions",
        })
    }
}
```

### 7.2 Echo 框架

```go
// cmd/api/main.go
package main

import (
    "github.com/labstack/echo/v4"
    "github.com/labstack/echo/v4/middleware"
)

func main() {
    e := echo.New()

    e.Use(middleware.Logger())
    e.Use(middleware.Recover())
    e.Use(middleware.CORS())

    e.Validator = NewCustomValidator()

    api := e.Group("/api/v1")
    {
        users := api.Group("/users")
        {
            users.GET("", listUsers)
            users.GET("/:id", getUser)
            users.POST("", createUser)
            users.PUT("/:id", updateUser)
            users.DELETE("/:id", deleteUser)
        }
    }

    e.Logger.Fatal(e.Start(":8080"))
}

// handler
func getUser(c echo.Context) error {
    id := c.Param("id")

    user, err := userService.GetByID(c.Request().Context(), id)
    if err != nil {
        return echo.NewHTTPError(http.StatusNotFound, "user not found")
    }

    return c.JSON(http.StatusOK, user)
}

func createUser(c echo.Context) error {
    var req CreateUserRequest
    if err := c.Bind(&req); err != nil {
        return echo.NewHTTPError(http.StatusBadRequest, "invalid request")
    }

    if err := c.Validate(&req); err != nil {
        return echo.NewHTTPError(http.StatusBadRequest, err.Error())
    }

    user, err := userService.Create(c.Request().Context(), &req)
    if err != nil {
        return echo.NewHTTPError(http.StatusInternalServerError, "failed to create user")
    }

    return c.JSON(http.StatusCreated, user)
}
```

### 7.3 Fiber 框架

```go
// cmd/api/main.go
package main

import (
    "github.com/gofiber/fiber/v2"
    "github.com/gofiber/fiber/v2/middleware/cors"
    "github.com/gofiber/fiber/v2/middleware/logger"
    "github.com/gofiber/fiber/v2/middleware/recover"
)

func main() {
    app := fiber.New(fiber.Config{
        ErrorHandler: customErrorHandler,
    })

    app.Use(logger.New())
    app.Use(recover.New())
    app.Use(cors.New())

    api := app.Group("/api/v1")
    {
        users := api.Group("/users")
        {
            users.Get("/", listUsers)
            users.Get("/:id", getUser)
            users.Post("/", createUser)
            users.Put("/:id", updateUser)
            users.Delete("/:id", deleteUser)
        }
    }

    app.Listen(":8080")
}

func customErrorHandler(c *fiber.Ctx, err error) error {
    code := fiber.StatusInternalServerError
    message := "Internal Server Error"

    if e, ok := err.(*fiber.Error); ok {
        code = e.Code
        message = e.Message
    }

    return c.Status(code).JSON(fiber.Map{
        "error": message,
    })
}

func getUser(c *fiber.Ctx) error {
    id := c.Params("id")

    user, err := userService.GetByID(c.Context(), id)
    if err != nil {
        return fiber.NewError(fiber.StatusNotFound, "user not found")
    }

    return c.JSON(user)
}

func createUser(c *fiber.Ctx) error {
    var req CreateUserRequest
    if err := c.BodyParser(&req); err != nil {
        return fiber.NewError(fiber.StatusBadRequest, "invalid request body")
    }

    user, err := userService.Create(c.Context(), &req)
    if err != nil {
        return fiber.NewError(fiber.StatusInternalServerError, "failed to create user")
    }

    return c.Status(fiber.StatusCreated).JSON(user)
}
```

---

## 8. 检查清单

### 8.1 代码风格检查清单

- [ ] 所有导出标识符都有文档注释
- [ ] 包名简短、小写、单个单词
- [ ] 变量名使用驼峰命名法
- [ ] 常量使用有意义的名称
- [ ] 接口使用 -er 后缀（单方法接口）
- [ ] 使用 gofmt 格式化代码
- [ ] 使用 goimports 管理导入
- [ ] 导入分组：标准库 → 第三方库 → 本地包
- [ ] 避免未使用的变量和导入

### 8.2 项目结构检查清单

- [ ] cmd/ 目录包含应用程序入口
- [ ] internal/ 目录包含私有代码
- [ ] pkg/ 目录包含可复用的公共库
- [ ] 配置文件放在 configs/ 目录
- [ ] API 定义放在 api/ 目录
- [ ] 部署配置放在 deployments/ 目录
- [ ] 每个模块有清晰的分层（handler/service/repository）
- [ ] 测试文件与源文件同目录

### 8.3 依赖管理检查清单

- [ ] go.mod 文件存在且格式正确
- [ ] 使用语义化版本
- [ ] 定期运行 go mod tidy
- [ ] 私有模块配置 GOPRIVATE
- [ ] 使用 go mod verify 验证依赖
- [ ] 定期更新依赖（安全更新）
- [ ] 记录依赖变更原因

### 8.4 测试检查清单

- [ ] 所有公开函数都有测试
- [ ] 使用表驱动测试
- [ ] 测试覆盖率 >= 80%
- [ ] 使用 testify 断言库
- [ ] Mock 外部依赖
- [ ] 测试边界条件
- [ ] 测试错误路径
- [ ] 使用 go test -race 检测竞态
- [ ] 有基准测试（关键路径）

### 8.5 并发安全检查清单

- [ ] 共享数据使用互斥锁保护
- [ ] 读多写少使用 RWMutex
- [ ] goroutine 有退出机制
- [ ] 使用 context 控制超时
- [ ] channel 有明确的关闭策略
- [ ] 避免 goroutine 泄漏
- [ ] 使用 -race 标志测试
- [ ] defer 调用 Unlock

### 8.6 错误处理检查清单

- [ ] 错误使用 %w 包装
- [ ] 错误信息包含上下文
- [ ] 使用 errors.Is 判断错误类型
- [ ] 使用 errors.As 提取错误详情
- [ ] 定义业务错误类型
- [ ] HTTP 返回适当的错误码
- [ ] 记录错误日志
- [ ] 避免忽略错误

### 8.7 框架使用检查清单

- [ ] 路由分组组织
- [ ] 中间件链式调用
- [ ] 请求参数验证
- [ ] 统一响应格式
- [ ] 统一错误处理
- [ ] 优雅关闭
- [ ] 健康检查端点
- [ ] 请求日志记录

### 8.8 安全检查清单

- [ ] 输入验证
- [ ] SQL 注入防护（使用参数化查询）
- [ ] XSS 防护
- [ ] CSRF 防护
- [ ] 敏感数据加密
- [ ] 密码哈希（bcrypt/argon2）
- [ ] JWT 安全配置
- [ ] 速率限制
- [ ] HTTPS 强制

### 8.9 性能检查清单

- [ ] 避免不必要的内存分配
- [ ] 使用 sync.Pool 复用对象
- [ ] 数据库连接池配置
- [ ] 缓存热点数据
- [ ] 批量操作替代循环操作
- [ ] 使用 pprof 分析性能
- [ ] 压力测试关键接口

### 8.10 文档检查清单

- [ ] README.md 包含项目说明
- [ ] API 文档（OpenAPI/Swagger）
- [ ] 架构设计文档
- [ ] 部署文档
- [ ] 变更日志（CHANGELOG.md）
- [ ] 贡献指南（CONTRIBUTING.md）
- [ ] 代码注释清晰

---

## 附录

### A. 常用命令速查

```bash
# 格式化
gofmt -w .
goimports -w .

# 静态检查
go vet ./...
staticcheck ./...

# 测试
go test ./...
go test -race ./...
go test -cover ./...

# 构建
go build ./...
go build -o bin/api ./cmd/api

# 依赖
go mod tidy
go mod download
go mod verify

# 文档
go doc fmt.Println
godoc -http=:6060
```

### B. 推荐工具

| 工具 | 用途 | 安装 |
|------|------|------|
| golangci-lint | 综合静态检查 | `go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest` |
| staticcheck | 静态分析 | `go install honnef.co/go/tools/cmd/staticcheck@latest` |
| goimports | 导入管理 | `go install golang.org/x/tools/cmd/goimports@latest` |
| gomodifytags | 结构体标签 | `go install github.com/fatih/gomodifytags@latest` |
| impl | 接口实现 | `go install github.com/josharian/impl@latest` |
| gocode | 代码补全 | `go install github.com/mdempsky/gocode@latest` |
| delve | 调试器 | `go install github.com/go-delve/delve/cmd/dlv@latest` |
| pprof | 性能分析 | 内置 `go tool pprof` |

### C. 参考资源

- [Effective Go](https://golang.org/doc/effective_go)
- [Go Code Review Comments](https://github.com/golang/go/wiki/CodeReviewComments)
- [Standard Go Project Layout](https://github.com/golang-standards/project-layout)
- [Go by Example](https://gobyexample.com/)
- [Go Blog](https://blog.golang.org/)
- [Go Proverbs](https://go-proverbs.github.io/)

---

> 本规范基于 Go 官方文档和社区最佳实践整理，适用于 Go 1.22+ 版本。
