---
name: daima_shengcheng
description: 代码生成子技能，根据结构化规范自动生成实现代码。
---

# 代码生成子技能

## 概述

代码生成子技能负责将结构化规范转换为可执行的实现代码。通过预定义的映射规则和模板，确保生成的代码符合最佳实践和项目规范。

## 代码生成流程

```
┌─────────────────┐
│   结构化规范     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   规范解析器     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   映射规则引擎   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   模板渲染器     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   代码输出       │
└─────────────────┘
```

## 规范到代码映射规则

### 实体 → 模型映射

| 规范元素 | Python | TypeScript | Go |
|---------|--------|------------|-----|
| 实体 | dataclass / Pydantic Model | interface / class | struct |
| 属性 | 字段 + 类型注解 | 属性 + 类型定义 | 字段 + 类型 + 标签 |
| 主键 | id: int | id: number | ID int64 `json:"id"` |
| 必填 | 必填字段 | 必填属性 | 必填字段 |
| 可选 | Optional[T] | T \| null | *T |
| 默认值 | field(default=...) | = value | - |
| 枚举 | Enum | enum | const / iota |

### 接口 → API 映射

| 规范元素 | Python (FastAPI) | TypeScript (Express) | Go (Gin) |
|---------|------------------|---------------------|----------|
| GET 列表 | @router.get("/") | router.get("/", ...) | r.GET("/", ...) |
| GET 详情 | @router.get("/{id}") | router.get("/:id", ...) | r.GET("/:id", ...) |
| POST 创建 | @router.post("/") | router.post("/", ...) | r.POST("/", ...) |
| PUT 更新 | @router.put("/{id}") | router.put("/:id", ...) | r.PUT("/:id", ...) |
| DELETE 删除 | @router.delete("/{id}") | router.delete("/:id", ...) | r.DELETE("/:id", ...) |
| 路径参数 | Path参数 | req.params | c.Param() |
| 查询参数 | Query参数 | req.query | c.Query() |
| 请求体 | Body参数 | req.body | c.BindJSON() |
| 响应 | return dict | res.json() | c.JSON() |

### 规则 → 逻辑映射

| 规范规则 | Python | TypeScript | Go |
|---------|--------|------------|-----|
| 验证规则 | Pydantic validator | class-validator | validator package |
| 业务规则 | Service 方法 | Service 方法 | Service 方法 |
| 计算规则 | @property | getter | 方法 |
| 状态转换 | 状态机 / 条件判断 | 状态机 / 条件判断 | 状态机 / 条件判断 |
| 事件触发 | 事件发射器 | EventEmitter | channel / callback |

### 约束 → 验证映射

| 约束类型 | Python | TypeScript | Go |
|---------|--------|------------|-----|
| 非空 | Optional + 检查 | !null | != nil |
| 长度限制 | len() + validator | length decorator | len() |
| 范围限制 | 比较运算符 | range decorator | 比较运算符 |
| 格式验证 | regex / validator | pattern decorator | regexp |
| 唯一性 | 数据库约束 | 数据库约束 | 数据库约束 |
| 引用完整性 | 外键约束 | 外键约束 | 外键约束 |

## Python 代码生成模板

### 模型模板

```python
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum

{{#each enums}}
class {{name}}(str, Enum):
    {{#each values}}
    {{key}} = "{{value}}"
    {{/each}}

{{/each}}

{{#each entities}}
class {{name}}(BaseModel):
    {{#each attributes}}
    {{field_name}}: {{python_type}}{{#if optional}} | None{{/if}} = {{#if optional}}None{{else}}...{{/if}}
    {{/each}}

    {{#each validators}}
    @validator('{{field}}')
    def validate_{{name}}(cls, v):
        {{logic}}
        return v
    {{/each}}

    class Config:
        from_attributes = True

{{/each}}
```

### API 模板

```python
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/{{resource_name}}", tags=["{{resource_name}}"])

{{#each endpoints}}
@router.{{method}}("{{path}}")
async def {{operation_id}}(
    {{#each parameters}}
    {{name}}: {{python_type}}{{#if required}}{{else}} = {{default_value}}{{/if}},
    {{/each}}
) -> {{return_type}}:
    """
    {{description}}
    """
    {{#each logic}}
    {{code}}
    {{/each}}
{{/each}}
```

### Service 模板

```python
from typing import List, Optional
from sqlalchemy.orm import Session
from models.{{module_name}} import {{entity_name}}
from schemas.{{module_name}} import {{entity_name}}Create, {{entity_name}}Update

class {{entity_name}}Service:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100) -> List[{{entity_name}}]:
        return self.db.query({{entity_name}}).offset(skip).limit(limit).all()

    def get_by_id(self, id: int) -> Optional[{{entity_name}}]:
        return self.db.query({{entity_name}}).filter({{entity_name}}.id == id).first()

    def create(self, data: {{entity_name}}Create) -> {{entity_name}}:
        db_obj = {{entity_name}}(**data.model_dump())
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, id: int, data: {{entity_name}}Update) -> Optional[{{entity_name}}]:
        db_obj = self.get_by_id(id)
        if not db_obj:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(db_obj, key, value)
        self.db.commit()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, id: int) -> bool:
        db_obj = self.get_by_id(id)
        if not db_obj:
            return False
        self.db.delete(db_obj)
        self.db.commit()
        return True
```

## TypeScript 代码生成模板

### 模型模板

```typescript
{{#each enums}}
export enum {{name}} {
  {{#each values}}
  {{key}} = '{{value}}',
  {{/each}}
}

{{/each}}

{{#each entities}}
export interface {{name}} {
  {{#each attributes}}
  {{field_name}}{{#if optional}}?{{/if}}: {{typescript_type}};
  {{/each}}
}

export class {{name}}Model {
  {{#each attributes}}
  private _{{field_name}}: {{typescript_type}}{{#if optional}} | undefined{{/if}};
  {{/each}}

  {{#each attributes}}
  get {{field_name}}(): {{typescript_type}}{{#if optional}} | undefined{{/if}} {
    return this._{{field_name}};
  }

  set {{field_name}}(value: {{typescript_type}}{{#if optional}} | undefined{{/if}}) {
    {{#if has_validation}}
    this.validate{{field_name_pascal}}(value);
    {{/if}}
    this._{{field_name}} = value;
  }
  {{/each}}

  {{#each validators}}
  private validate{{name}}(value: any): void {
    {{logic}}
  }
  {{/each}}

  toJSON(): {{name}} {
    return {
      {{#each attributes}}
      {{field_name}}: this._{{field_name}},
      {{/each}}
    };
  }
}

{{/each}}
```

### API 模板

```typescript
import { Router, Request, Response, NextFunction } from 'express';
import { {{service_name}} } from '../services/{{module_name}}.service';

const router = Router();
const service = new {{service_name}}();

{{#each endpoints}}
router.{{method}}('{{path}}', async (req: Request, res: Response, next: NextFunction) => {
  try {
    {{#each parameters}}
    const {{name}} = {{#if is_path}}req.params.{{name}}{{else if is_query}}req.query.{{name}}{{else}}req.body.{{name}}{{/if}};
    {{/each}}

    const result = await service.{{operation_id}}({{parameter_list}});
    res.json(result);
  } catch (error) {
    next(error);
  }
});

{{/each}}

export default router;
```

### Service 模板

```typescript
import { {{entity_name}} } from '../models/{{module_name}}';
import { Repository } from '../repositories/base.repository';

export class {{entity_name}}Service {
  private repository: Repository<{{entity_name}}>;

  constructor() {
    this.repository = new Repository<{{entity_name}}>('{{table_name}}');
  }

  async getAll(skip: number = 0, limit: number = 100): Promise<{{entity_name}}[]> {
    return this.repository.findAll({ skip, limit });
  }

  async getById(id: number): Promise<{{entity_name}} | null> {
    return this.repository.findById(id);
  }

  async create(data: Omit<{{entity_name}}, 'id'>): Promise<{{entity_name}}> {
    return this.repository.create(data);
  }

  async update(id: number, data: Partial<{{entity_name}}>): Promise<{{entity_name}} | null> {
    return this.repository.update(id, data);
  }

  async delete(id: number): Promise<boolean> {
    return this.repository.delete(id);
  }
}
```

## Go 代码生成模板

### 模型模板

```go
package models

import (
    "time"
    "gorm.io/gorm"
)

{{#each enums}}
type {{name}} int

const (
    {{#each values}}
    {{name}}{{key}} {{name}} = iota{{#if value}} = {{value}}{{/if}}
    {{/each}}
)

func (e {{name}}) String() string {
    switch e {
    {{#each values}}
    case {{name}}{{key}}:
        return "{{value}}"
    {{/each}}
    default:
        return "unknown"
    }
}
{{/each}}

{{#each entities}}
type {{name}} struct {
    {{#each attributes}}
    {{field_name_pascal}} {{go_type}} `json:"{{field_name}}"{{#if gorm_tags}} gorm:"{{gorm_tags}}"{{/if}}`
    {{/each}}
    CreatedAt time.Time `json:"created_at"`
    UpdatedAt time.Time `json:"updated_at"`
}

func ({{entity_name}}) TableName() string {
    return "{{table_name}}"
}
{{/each}}
```

### API 模板

```go
package handlers

import (
    "net/http"
    "strconv"
    "github.com/gin-gonic/gin"
    "{{module_path}}/models"
    "{{module_path}}/services"
)

type {{entity_name}}Handler struct {
    service *services.{{entity_name}}Service
}

func New{{entity_name}}Handler(s *services.{{entity_name}}Service) *{{entity_name}}Handler {
    return &{{entity_name}}Handler{service: s}
}

func (h *{{entity_name}}Handler) RegisterRoutes(r *gin.RouterGroup) {
    {{resource_name}} := r.Group("/{{resource_name}}")
    {
        {{resource_name}}.GET("", h.getAll)
        {{resource_name}}.GET("/:id", h.getByID)
        {{resource_name}}.POST("", h.create)
        {{resource_name}}.PUT("/:id", h.update)
        {{resource_name}}.DELETE("/:id", h.delete)
    }
}

{{#each endpoints}}
func (h *{{entity_name}}Handler) {{operation_id_pascal}}(c *gin.Context) {
    {{#each parameters}}
    {{#if is_path}}
    {{name}}, err := strconv.{{convert_func}}(c.Param("{{name}}"))
    if err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": "invalid {{name}}"})
        return
    }
    {{else if is_query}}
    {{name}} := c.Query("{{name}}")
    {{else}}
    var {{name}} {{go_type}}
    if err := c.ShouldBindJSON(&{{name}}); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    {{/if}}
    {{/each}}

    result, err := h.service.{{operation_id_pascal}}({{parameter_list}})
    if err != nil {
        c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
        return
    }

    c.JSON(http.StatusOK, result)
}
{{/each}}
```

### Service 模板

```go
package services

import (
    "errors"
    "gorm.io/gorm"
    "{{module_path}}/models"
)

type {{entity_name}}Service struct {
    db *gorm.DB
}

func New{{entity_name}}Service(db *gorm.DB) *{{entity_name}}Service {
    return &{{entity_name}}Service{db: db}
}

func (s *{{entity_name}}Service) GetAll(skip, limit int) ([]models.{{entity_name}}, error) {
    var items []models.{{entity_name}}
    if err := s.db.Offset(skip).Limit(limit).Find(&items).Error; err != nil {
        return nil, err
    }
    return items, nil
}

func (s *{{entity_name}}Service) GetByID(id int64) (*models.{{entity_name}}, error) {
    var item models.{{entity_name}}
    if err := s.db.First(&item, id).Error; err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            return nil, nil
        }
        return nil, err
    }
    return &item, nil
}

func (s *{{entity_name}}Service) Create(data *models.{{entity_name}}) error {
    return s.db.Create(data).Error
}

func (s *{{entity_name}}Service) Update(id int64, data map[string]interface{}) error {
    return s.db.Model(&models.{{entity_name}}{}).Where("id = ?", id).Updates(data).Error
}

func (s *{{entity_name}}Service) Delete(id int64) error {
    return s.db.Delete(&models.{{entity_name}}{}, id).Error
}
```

## 代码生成配置

### 配置结构

```yaml
generation:
  language: python | typescript | go
  
  output:
    base_path: ./src
    models_path: models
    handlers_path: handlers
    services_path: services
    
  naming:
    style: snake_case | camelCase | PascalCase
    prefix: ""
    suffix: ""
    
  features:
    validation: true
    pagination: true
    filtering: true
    sorting: true
    caching: false
    
  database:
    orm: sqlalchemy | prisma | gorm
    migrations: true
    
  api:
    framework: fastapi | express | gin
    versioning: true
    documentation: openapi
    
  testing:
    unit_tests: true
    integration_tests: true
    coverage_threshold: 80
```

### 类型映射配置

```yaml
type_mappings:
  python:
    string: str
    integer: int
    float: float
    boolean: bool
    date: datetime.date
    datetime: datetime.datetime
    array: List
    object: dict
    
  typescript:
    string: string
    integer: number
    float: number
    boolean: boolean
    date: Date
    datetime: Date
    array: T[]
    object: Record<string, T>
    
  go:
    string: string
    integer: int64
    float: float64
    boolean: bool
    date: time.Time
    datetime: time.Time
    array: []T
    object: map[string]interface{}
```

## 生成示例

### 输入规范

```yaml
entity:
  name: User
  attributes:
    - name: id
      type: integer
      primary: true
    - name: username
      type: string
      required: true
      unique: true
      min_length: 3
      max_length: 50
    - name: email
      type: string
      required: true
      unique: true
      format: email
    - name: age
      type: integer
      optional: true
      min: 0
      max: 150
    - name: status
      type: enum
      values: [active, inactive, suspended]
      default: active

interfaces:
  - name: CreateUser
    method: POST
    path: /users
    parameters:
      - name: body
        type: UserCreate
        in: body
    returns: User
    
  - name: GetUser
    method: GET
    path: /users/{id}
    parameters:
      - name: id
        type: integer
        in: path
    returns: User
```

### Python 生成结果

```python
from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional
from enum import Enum
from datetime import datetime

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class User(BaseModel):
    id: int
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=150)
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    age: Optional[int] = Field(None, ge=0, le=150)
    status: UserStatus = UserStatus.ACTIVE

class UserService:
    def __init__(self, db):
        self.db = db

    async def create(self, data: UserCreate) -> User:
        user = User(**data.model_dump())
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, id: int) -> Optional[User]:
        return await self.db.query(User).filter(User.id == id).first()
```

### TypeScript 生成结果

```typescript
export enum UserStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
}

export interface User {
  id: number;
  username: string;
  email: string;
  age?: number;
  status: UserStatus;
  createdAt: Date;
  updatedAt: Date;
}

export interface UserCreate {
  username: string;
  email: string;
  age?: number;
  status?: UserStatus;
}

export class UserService {
  private repository: Repository<User>;

  constructor() {
    this.repository = new Repository<User>('users');
  }

  async create(data: UserCreate): Promise<User> {
    return this.repository.create({
      ...data,
      status: data.status ?? UserStatus.ACTIVE,
    });
  }

  async getById(id: number): Promise<User | null> {
    return this.repository.findById(id);
  }
}
```

### Go 生成结果

```go
package models

import (
    "time"
    "gorm.io/gorm"
)

type UserStatus int

const (
    UserStatusActive UserStatus = iota
    UserStatusInactive
    UserStatusSuspended
)

func (s UserStatus) String() string {
    switch s {
    case UserStatusActive:
        return "active"
    case UserStatusInactive:
        return "inactive"
    case UserStatusSuspended:
        return "suspended"
    default:
        return "unknown"
    }
}

type User struct {
    ID        uint64      `json:"id" gorm:"primaryKey"`
    Username  string      `json:"username" gorm:"uniqueIndex;size:50;not null"`
    Email     string      `json:"email" gorm:"uniqueIndex;not null"`
    Age       *int        `json:"age,omitempty" gorm:"check:age >= 0 AND age <= 150"`
    Status    UserStatus  `json:"status" gorm:"default:0"`
    CreatedAt time.Time   `json:"created_at"`
    UpdatedAt time.Time   `json:"updated_at"`
}

func (User) TableName() string {
    return "users"
}

type UserService struct {
    db *gorm.DB
}

func NewUserService(db *gorm.DB) *UserService {
    return &UserService{db: db}
}

func (s *UserService) Create(data *User) error {
    return s.db.Create(data).Error
}

func (s *UserService) GetByID(id uint64) (*User, error) {
    var user User
    if err := s.db.First(&user, id).Error; err != nil {
        if errors.Is(err, gorm.ErrRecordNotFound) {
            return nil, nil
        }
        return nil, err
    }
    return &user, nil
}
```

## 最佳实践

### 代码质量

- 生成的代码应遵循目标语言的代码规范
- 添加适当的错误处理和日志记录
- 实现必要的输入验证
- 遵循 SOLID 原则

### 安全性

- 验证所有用户输入
- 使用参数化查询防止 SQL 注入
- 实现适当的认证和授权
- 敏感数据加密存储

### 性能

- 实现数据库查询优化
- 添加适当的索引
- 实现缓存策略
- 支持分页和批量操作

### 可维护性

- 生成清晰的代码结构
- 添加必要的注释
- 遵循一致的命名约定
- 保持代码简洁易读
