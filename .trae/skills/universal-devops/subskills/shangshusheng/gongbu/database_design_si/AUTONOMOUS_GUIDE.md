# 数据库设计司 自主操作指南 (Autonomous Operation Guide)

> 尚书省 · 工部 · 水部司 · Universal DevOps v5.0
> 自主 Schema 演化引擎

## 概述

数据库设计司（水部司）负责**自主数据模型设计、Schema 演化管理、索引优化与迁移策略**。本司的核心能力是将业务领域模型转化为高效、规范、可演进的数据存储方案，并确保从设计到迁移的全流程安全可控。

### 定位

- **ER 建模引擎**：基于业务需求自动生成实体关系图（Mermaid erDiagram）
- **Schema 演化守护者**：管理数据库结构的版本化变更，确保零停机迁移
- **性能优化顾问**：自主分析查询模式，提供索引优化和分区策略建议
- **多栈适配器**：支持 5 种数据库 × 4 种 ORM 的跨平台方案输出

### 目标

1. 接收业务实体描述后，自动产出符合范式要求的完整数据模型
2. 所有 Schema 变更通过版本化迁移脚本执行，可回滚、可审计
3. 索引策略基于实际查询模式分析，而非盲目添加

## 核心原则

### 原则一：渐进式演化（Evolutionary Schema）
数据库结构不是一次性设计的产物，而是随业务需求持续演化的。每次变更是增量式的，保持向后兼容。

### 原则二：数据完整性优先（Integrity First）
约束（Constraint）是数据质量的最后一道防线。主键、外键、唯一约束、Check 约束必须在 DDL 层面定义。

### 原则三：查询驱动设计（Query-Driven Design）
先理解应用层的查询模式（哪些字段常被联合查询？哪些表常被 JOIN？），再决定索引和反规范化程度。

### 原则四：迁移即代码（Migrations as Code）
所有 Schema 变更以可执行的迁移脚本形式存在，纳入版本控制，经过 CI/CD 流水线。

### 原则五：回滚能力（Rollback Capability）
每个迁移必须配套对应的 down/revert 迁移，保证在任何步骤都可以安全回退。

## 自主操作流程

### 阶段一：感知（Perceive）

#### 1.1 需求采集与领域建模

```
输入: 业务实体描述 / ER需求 / 现有数据库扫描结果
输出: 领域模型 + 实体属性清单 + 关系矩阵
```

**操作步骤**：

1. **实体识别**
   - 从需求文档中提取名词 → 候选实体（Candidate Entity）
   - 排除非实体名词（属性值、纯描述性词汇）
   - 识别弱实体（依赖其他实体存在的，如订单明细）

2. **属性定义**
   - 为每个实体列出属性（Attribute）
   - 标注属性特征：
     - 类型（String/Integer/Decimal/Boolean/DateTime/JSON/UUID）
     - 可空性（Nullable / Not Null）
     - 默认值（Default Value）
     - 唯一性（Unique / Non-unique）
     - 约束（Check constraint / Regex / Range）

3. **关系识别**
   - 实体间的基数关系（1:1 / 1:N / M:N）
   - 关系的参与度（mandatory / optional）
   - 关系属性（关系本身携带的信息，如"学生选课"的"成绩"）

#### 1.2 现有数据库感知（如改造场景）

当任务涉及现有数据库时，执行以下诊断：

```sql
-- 自主诊断 SQL 模板集

-- 1. 表清单及行数统计
SELECT
    schemaname,
    tablename,
    n_live_tup AS row_count,
    pg_size_p(pg_total_relation_size(schemaname||'.'||tablename)) AS total_size
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC;

-- 2. 未使用的外键（孤立约束）
SELECT
    tc.table_name,
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';

-- 3. 缺少索引的外键列
SELECT
    tc.table_name,
    kcu.column_name,
    tc.constraint_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
AND NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE tablename = tc.table_name
    AND indexdef LIKE '%' || kcu.column_name || '%'
);

-- 4. 大表识别（可能需要分区）
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size,
    pg_size_pretty(pg_relation_size(relid)) AS data_size,
    pg_size_pretty(pg_indexes_size(relid)) AS index_size,
    n_live_tup AS rows
FROM pg_stat_user_tables
WHERE n_live_tup > 100000
ORDER BY pg_total_relation_size(relid) DESC;

-- 5. 序列使用情况
SELECT
    c.relname AS sequence_name,
    a.attname AS associated_column
FROM pg_class c
JOIN pg_depend d ON d.objid = c.oid
JOIN pg_class t ON d.refobjid = t.oid
JOIN pg_attribute a ON a.attrelid = t.oid AND d.refobjsubid = a.attnum
WHERE c.relkind = 'S';
```

**诊断报告模板**：

```yaml
database_diagnostic:
  database_type: "PostgreSQL 15.x"
  total_tables: 24
  total_indexes: 67
  total_foreign_keys: 31
  estimated_total_size: "2.3 GB"
  findings:
    - severity: "high"
      type: "missing_index"
      description: "orders.customer_id 外键列缺少索引"
      impact: "JOIN customers 表时全表扫描"
      recommendation: "CREATE INDEX idx_orders_customer_id ON orders(customer_id)"
    - severity: "medium"
      type: "large_table"
      description: "audit_logs 表超过 500万行"
      impact: "查询和备份速度下降"
      recommendation: "考虑按时间范围分区 (PARTITION BY RANGE)"
    - severity: "low"
      type: "orphaned_constraint"
      description: "2个外键引用已删除的表"
      impact: "无功能影响但影响DDL操作"
      recommendation: "清理无效外键约束"
```

### 阶段二：决策（Decide）

#### 2.1 ER 图自主生成（Mermaid erDiagram）

根据阶段一的领域建模结果，自动生成标准化的 Mermaid ER 图：

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    USER {
        UUID id PK
        varchar(50) email UK "唯一邮箱"
        varchar(100) nickname
        varchar(255) password_hash
        user_status_enum status "active/suspended/banned"
        timestamp created_at
        timestamp updated_at
    }

    ORDER ||--|{ ORDER_ITEM : contains
    ORDER }o--|| USER : "belongs_to"
    ORDER }o--o| ADDRESS : "ships_to"
    ORDER {
        UUID id PK
        UUID customer_id FK
        UUID shipping_address_id FK
        order_status_enum status
        decimal(10,2) subtotal
        decimal(10,2) tax
        decimal(10,2) total_amount
        decimal(10,2) discount
        timestamp created_at
        timestamp paid_at
        timestamp shipped_at
    }

    ORDER_ITEM {
        UUID id PK
        UUID order_id FK
        UUID product_id FK
        int quantity
        decimal(10,2) unit_price
        decimal(10,2) line_total
    }

    PRODUCT ||--o{ ORDER_ITEM : "ordered_in"
    PRODUCT {
        UUID id PK
        varchar(200) name
        text description
        decimal(10,2) price
        int stock_quantity
        product_category_enum category
        boolean is_active
        timestamp created_at
        timestamp updated_at
    }

    CATEGORY ||--o{ PRODUCT : "contains"
    CATEGORY {
        UUID id PK
        varchar(100) name
        UUID parent_id FK "自引用，支持层级分类"
        int sort_order
    }

    ADDRESS ||--o{ ORDER : "used_by"
    ADDRESS {
        UUID id PK
        UUID user_id FK
        varchar(200) recipient_name
        varchar(500) street_address
        varchar(100) city
        varchar(100) province
        varchar(20) postal_code
        varchar(50) phone
        address_type_enum type "shipping/billing/both"
        boolean is_default
    }
```

#### 2.2 数据库选型决策矩阵

| 维度 | PostgreSQL | MySQL | SQLite | MongoDB | Redis |
|------|-----------|-------|--------|---------|-------|
| 适用场景 | 复杂查询/事务/JSON | Web应用/读密集 | 嵌入式/本地/测试 | 文档型/快速迭代 | 缓存/会话/队列 |
| ACID事务 | ✅ 完整 | ✅ 完整 | ✅ 完整 | ⚠️ 单文档 | ❌ 不适用 |
| JSON支持 | ✅ JSONB（强） | ✅ JSON（中） | ✅ JSON | ✅ 原生文档 | ⚠️ Hash/String |
| 全文搜索 | ✅ 内置tsvector | ❌ 需插件 | ❌ 弱 | ✅ 文本索引 | ❌ 不适用 |
| 地理空间 | ✅ PostGIS | ⚠️ 基础 | ❌ | ✅ GeoJSON | ❌ |
| 并发模型 | MVCC | MVCC | 串行 | 文档锁 | 单线程 |
| 最佳数据量 | < 10TB | < 5TB | < 1TB | < 4TB | < 100GB(RAM) |
| 迁移工具首选 | Alembic | Flyway/Alembic | Alembic | 无（需自定义） | N/A |

**自主选型规则**：
- 需要 JOIN 和复杂事务 → PostgreSQL
- 简单 CRUD 为主、团队熟悉 → MySQL
- 本地开发/嵌入式/测试 → SQLite
- 数据结构频繁变化/原型阶段 → MongoDB
- 会话缓存/排行榜/实时计数 → Redis

#### 2.3 ORM 选型适配

##### SQLAlchemy（Python）

```python
# SQLAlchemy 2.0 风格 — 声明式映射
from sqlalchemy import String, Integer, Numeric, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import enum

class Base(DeclarativeBase):
    pass

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    BANNED = "banned"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    nickname: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[UserStatus] = mapped_column(
        SAEnum(UserStatus, name="user_status_enum"),
        default=UserStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    orders: Mapped[list["Order"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    addresses: Mapped[list["Address"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    customer_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    tax: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")
```

##### TypeORM（TypeScript/Node.js）

```typescript
// TypeORM Entity — 装饰器风格
import {
  Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, UpdateDateColumn,
  OneToMany, ManyToOne, JoinColumn, Index, Unique
} from 'typeorm';
import { IsEmail, Length, IsEnum, IsOptional } from 'class-validator';
import { Order } from './order.entity';
import { Address } from './address.entity';
import { OrderStatus } from '../enums/order-status.enum';

export enum UserStatus {
  ACTIVE = 'active',
  SUSPENDED = 'suspended',
  BANNED = 'banned',
}

@Entity('users')
@Unique(['email'])
@Index(['email']) // 显式索引声明
export class User {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ type: 'varchar', length: 50, unique: true })
  @IsEmail()
  email: string;

  @Column({ type: 'varchar', length: 100 })
  @Length(1, 100)
  nickname: string;

  @Column({ type: 'varchar', length: 255 })
  passwordHash: string;

  @Column({
    type: 'enum',
    enum: UserStatus,
    default: UserStatus.ACTIVE,
    name: 'status',
  })
  @IsEnum(UserStatus)
  status: UserStatus;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relations
  @OneToMany(() => Order, (order) => order.customer, { cascade: true })
  orders: Order[];

  @OneToMany(() => Address, (address) => address.user, { cascade: true })
  addresses: Address[];
}
```

##### Prisma（TypeScript/Node.js — 新一代 ORM）

```prisma
// schema.prisma — Prisma Schema Language
generator client {
  provider = "prisma-client-js"
}

datasource db {
  provider = "postgresql"
  url      = env("DATABASE_URL")
}

enum UserStatus {
  ACTIVE
  SUSPENDED
  BANNED
}

enum OrderStatus {
  PENDING
  PROCESSING
  SHIPPED
  DELIVERED
  CANCELLED
}

model User {
  id           String       @id @default(uuid())
  email        String       @unique @db.VarChar(50)
  nickname     String?      @db.VarChar(100)
  passwordHash String       @map("password_hash") @db.VarChar(255)
  status       UserStatus   @default(ACTIVE) @db.UserStatus
  createdAt    DateTime     @default(now()) @map("created_at")
  updatedAt    DateTime     @updatedAt @map("updated_at")

  orders       Order[]
  addresses    Address[]

  @@index([email])
  @@map("users")
}

model Order {
  id                String       @id @default(uuid())
  customerId        String       @map("customer_id") @db.Uuid
  status            OrderStatus  @default(PENDING) @db.OrderStatus
  subtotal          Decimal      @db.Decimal(10, 2) @default(0)
  tax               Decimal      @db.Decimal(10, 2) @default(0)
  totalAmount       Decimal      @map("total_amount") @db.Decimal(10, 2) @default(0)
  discount          Decimal      @db.Decimal(10, 2) @default(0)
  createdAt         DateTime     @default(now()) @map("created_at")
  paidAt            DateTime?    @map("paid_at")
  shippedAt         DateTime?    @map("shipped_at")

  customer          User         @relation(fields: [customerId], references: [id])
  items             OrderItem[]
  shippingAddress   Address?     @relation("OrderShipping")

  @@index([customerId])
  @@index([status, createdAt]) // 复合索引
  @@map("orders")
}

model OrderItem {
  id        String  @id @default(uuid())
  orderId  String  @map("order_id") @db.Uuid
  productId String  @map("product_id") @db.Uuid
  quantity Int
  unitPrice Decimal @map("unit_price") @db.Decimal(10, 2)
  lineTotal Decimal @map("line_total") @db.Decimal(10, 2)

  order     Order   @relation(fields: [orderId], references: [id], onDelete: Cascade)
  product   Product @relation(fields: [productId], references: [id])

  @@index([orderId])
  @@index([productId])
  @@map("order_items")
}
```

##### Mongoose（Node.js — MongoDB ODM）

```typescript
// Mongoose Schema — MongoDB 文档模型
import { Schema, model, Document, Types, Index } from 'mongoose';
import { IUser } from '../interfaces/user.interface';

const UserSchema = new Schema<IUser>(
  {
    email: {
      type: String,
      required: true,
      unique: true,
      lowercase: true,
      trim: true,
      match: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
    },
    nickname: {
      type: String,
      maxlength: 100,
      trim: true,
    },
    passwordHash: {
      type: String,
      required: true,
      select: false, // 查询时不默认返回密码哈希
    },
    status: {
      type: String,
      enum: ['active', 'suspended', 'banned'],
      default: 'active',
      index: true,
    },
    profile: {
      avatar: { type: String, default: null },
      bio: { type: String, maxlength: 500 },
      birthday: { type: Date },
      preferences: {
        theme: { type: String, enum: ['light', 'dark'], default: 'light' },
        language: { type: String, default: 'zh-CN' },
        notifications: { type: Boolean, default: true },
      },
    }, // 嵌套文档
    lastLoginAt: { type: Date, default: null },
    loginCount: { type: Number, default: 0 },
  },
  {
    timestamps: true, // 自动添加 createdAt, updatedAt
    versionKey: false, // 移除 __v 字段
    toJSON: {
      virtuals: true,
      transform: (_doc, ret) => {
        delete ret.passwordHash;
        delete ret._id;
        ret.id = doc._id.toString();
        return ret;
      },
    },
  }
);

// 复合索引
UserSchema.index({ status: 1, createdAt: -1 });
UserSchema.index({ 'profile.preferences.theme': 1 });

// 虚拟字段
UserSchema.virtual('fullName').get(function () {
  return this.profile?.nickname || this.email.split('@')[0];
});

// 实例方法
UserSchema.methods.comparePassword = async function (
  candidatePassword: string
): Promise<boolean> {
  return bcrypt.compare(candidatePassword, this.passwordHash);
};

// 静态方法
UserSchema.statics.findByEmail = function (email: string) {
  return this.findOne({ email: email.toLowerCase() });
};

export const User = model<IUser>('User', UserSchema);
```

#### 2.4 规范化检查：1NF → 2NF → 3NF → BCNF

```yaml
normalization_checklist:
  # 第一范式 (1NF)：原子值
  first_normal_form:
    rule: "每个单元格只包含一个原子值（不可再分）"
    check_items:
      - "无重复组/数组类型的列（除非使用原生JSON类型）"
      - "每行有唯一标识（主键）"
      - "每个列名在表中唯一"
    anti_patterns:
      - "用户表中的 phone_numbers 列存为逗号分隔字符串 → 应拆分为关联表"
      - "地址信息全部塞在一个 text 列 → 应拆分为独立字段或关联表"
    auto_fix: "检测到违反1NF的模式时，建议拆分为独立表"

  # 第二范式 (2NF)：消除部分依赖
  second_normal_form:
    rule: "非主属性完全依赖于整个主键（而非主键的一部分）"
    check_items:
      - "复合主键的所有非键属性都完全函数依赖于整个主键"
      - "单主键的表天然满足2NF"
    anti_patterns:
      - "订单明细表(order_id, product_id, product_name) 中 product_name 只依赖 product_id"
      - "课程选课表(student_id, course_id, student_name) 中 student_name 只依赖 student_id"
    auto_fix: "将部分依赖的属性移到对应的表中"

  # 第三范式 (3NF)：消除传递依赖
  third_normal_form:
    rule: "非主属性不传递依赖于主键（A→B→C，其中C通过B间接依赖A）"
    check_items:
      - "无非主属性依赖于其他非主属性"
    anti_patterns:
      - "员工表(emp_id, emp_name, dept_name, dept_location) 中 dept_location 通过 dept_name 传递依赖"
      - "产品表含 category_name 而 category 有独立属性时"
    auto_fix: "将传递依赖的属性提取为独立表，用外键关联"

  # BCNF（Boyce-Codd 范式）：更强的3NF
  bcnf:
    rule: "每个决定因素都是候选键"
    check_items:
      - "对于每个非平凡函数依赖 X→A，X 必须是超键"
    note: "BCNF 在大多数实践中与3NF 的差异很小，但能捕获一些边界情况"
    example_violation:
      table: "student_courses(student_id, course_id, instructor)"
      issue: "(student_id, course_id) → instructor 且 course_id → instructor"
      fix: "拆分为 student_courses(student_id, course_id) + course_instructor(course_id, instructor)"

  # 反规范化决策（何时故意违反范式）
  denormalization_decision_matrix:
    condition: "读远多于写（读写比 > 10:1）且 性能有明确瓶颈"
    trade_off: "牺牲写入性能和数据一致性换取读取速度"
    common_techniques:
      - name: "冗余存储常用字段"
        example: "订单表冗余 customer_email（避免JOIN查用户表）"
        risk: "需同步维护一致性"
      - name: "预计算聚合值"
        example: "用户表增加 order_count, total_spent 字段"
        risk: "每次下单需更新聚合值"
      - name: "嵌套文档（NoSQL）"
        example: "MongoDB中将订单项嵌入订单文档"
        risk: "文档大小膨胀"
```

### 阶段三：执行（Execute）

#### 3.1 迁移脚本生成

##### Alembic 迁移（Python/SQLAlchemy）

```python
"""${migration_description}

Revision ID: ${revision_id}
Revises: ${parent_revision}
Create Date: ${create_date}
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = '${revision_id}'
down_revision = '${parent_revision}'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # === 创建枚举类型 ===
    user_status_enum = sa.Enum(
        'active', 'suspended', 'banned',
        name='user_status_enum'
    )
    user_status_enum.create(op.get_bind(), checkfirst=True)

    order_status_enum = sa.Enum(
        'pending', 'processing', 'shipped', 'delivered', 'cancelled',
        name='order_status_enum'
    )
    order_status_enum.create(op.get_bind(), checkfirst=True)

    # === 创建 users 表 ===
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('email', sa.String(50), nullable=False, unique=True),
        sa.Column('nickname', sa.String(100), nullable=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('status', user_status_enum, nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('idx_users_email', 'users', ['email'], unique=True)

    # === 创建 categories 表 ===
    op.create_table(
        'categories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('sort_order', sa.Integer, nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['parent_id'], ['categories.id'], ondelete='SET NULL'),
    )

    # === 创建 products 表 ===
    op.create_table(
        'products',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('stock_quantity', sa.Integer, nullable=False, server_default='0'),
        sa.Column('category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, server_default=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
    )
    op.create_index('idx_products_category', 'products', ['category_id'])
    op.create_index('idx_products_active', 'products', ['is_active'])

    # === 创建 addresses 表 ===
    op.create_table(
        'addresses',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('recipient_name', sa.String(200), nullable=False),
        sa.Column('street_address', sa.String(500), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('province', sa.String(100), nullable=False),
        sa.Column('postal_code', sa.String(20), nullable=False),
        sa.Column('phone', sa.String(50), nullable=False),
        sa.Column('type', sa.String(20), nullable=False, server_default='shipping'),
        sa.Column('is_default', sa.Boolean, server_default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_addresses_user', 'addresses', ['user_id'])

    # === 创建 orders 表 ===
    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('shipping_address_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', order_status_enum, nullable=False, server_default='pending'),
        sa.Column('subtotal', sa.Numeric(10, 2), server_default='0'),
        sa.Column('tax', sa.Numeric(10, 2), server_default='0'),
        sa.Column('total_amount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('discount', sa.Numeric(10, 2), server_default='0'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('paid_at', sa.DateTime, nullable=True),
        sa.Column('shipped_at', sa.DateTime, nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id']),
        sa.ForeignKeyConstraint(['shipping_address_id'], ['addresses.id']),
    )
    op.create_index('idx_orders_customer', 'orders', ['customer_id'])
    op.create_index('idx_orders_status_created', 'orders', ['status', 'created_at'])

    # === 创建 order_items 表 ===
    op.create_table(
        'order_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('product_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('line_total', sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['product_id'], ['products.id']),
    )
    op.create_index('idx_order_items_order', 'order_items', ['order_id'])
    op.create_index('idx_order_items_product', 'order_items', ['product_id'])


def downgrade() -> None:
    # 按逆序删除（先删子表，再删父表）
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('addresses')
    op.drop_table('products')
    op.drop_table('categories')
    op.drop_table('users')

    # 删除枚举类型
    sa.Enum(name='order_status_enum').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='user_status_enum').drop(op.get_bind(), checkfirst=True)
```

##### Flyway 迁移（Java/通用 SQL）

```sql
-- V1__init_schema.sql
-- Flyway Versioned Migration

-- ============================================
-- 1. 枚举类型（PostgreSQL 特有）
-- ============================================
DO $$ BEGIN
    CREATE TYPE user_status_enum AS ENUM ('active', 'suspended', 'banned');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE order_status_enum AS ENUM ('pending', 'processing', 'shipped', 'delivered', 'cancelled');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================
-- 2. users 表
-- ============================================
CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(50) NOT NULL UNIQUE,
    nickname        VARCHAR(100),
    password_hash   VARCHAR(255) NOT NULL,
    status          user_status_enum NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================
-- 3. categories 表（自引用层级）
-- ============================================
CREATE TABLE IF NOT EXISTS categories (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        VARCHAR(100) NOT NULL,
    parent_id   UUID REFERENCES categories(id) ON DELETE SET NULL,
    sort_order  INTEGER NOT NULL DEFAULT 0
);

-- ============================================
-- 4. products 表
-- ============================================
CREATE TABLE IF NOT EXISTS products (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    price           DECIMAL(10,2) NOT NULL,
    stock_quantity  INTEGER NOT NULL DEFAULT 0,
    category_id     UUID REFERENCES categories(id),
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active);

-- ============================================
-- 5. addresses 表
-- ============================================
CREATE TABLE IF NOT EXISTS addresses (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    recipient_name  VARCHAR(200) NOT NULL,
    street_address  VARCHAR(500) NOT NULL,
    city            VARCHAR(100) NOT NULL,
    province        VARCHAR(100) NOT NULL,
    postal_code     VARCHAR(20) NOT NULL,
    phone           VARCHAR(50) NOT NULL,
    type            VARCHAR(20) NOT NULL DEFAULT 'shipping',
    is_default      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_addresses_user ON addresses(user_id);

-- ============================================
-- 6. orders 表
-- ============================================
CREATE TABLE IF NOT EXISTS orders (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id         UUID NOT NULL REFERENCES users(id),
    shipping_address_id UUID REFERENCES addresses(id),
    status              order_status_enum NOT NULL DEFAULT 'pending',
    subtotal            DECIMAL(10,2) NOT NULL DEFAULT 0,
    tax                 DECIMAL(10,2) NOT NULL DEFAULT 0,
    total_amount        DECIMAL(10,2) NOT NULL DEFAULT 0,
    discount            DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    paid_at             TIMESTAMPTZ,
    shipped_at          TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_status_created ON orders(status, created_at);

-- ============================================
-- 7. order_items 表
-- ============================================
CREATE TABLE IF NOT EXISTS order_items (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    order_id    UUID NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id  UUID NOT NULL REFERENCES products(id),
    quantity    INTEGER NOT NULL,
    unit_price  DECIMAL(10,2) NOT NULL,
    line_total  DECIMAL(10,2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product ON order_items(product_id);
```

##### Prisma Migrate

```bash
# Prisma 迁移命令序列
npx prisma migrate dev --name init_schema    # 开发环境：创建并应用
npx prisma migrate deploy                    # 生产环境：仅应用已有迁移
npx prisma migrate reset                     # 重置数据库
npx prisma migrate status                    # 查看迁移状态
npx prisma migrate resolve --applied xxx     # 手动标记已应用的迁移
```

#### 3.2 索引优化建议系统

##### 索引类型选择指南

```yaml
index_strategy_guide:

  b_tree:
    full_name: "B-Tree Index"
    best_for:
      - "等值查询 (=, IN)"
      - "范围查询 (>, <, BETWEEN)"
      - "排序 (ORDER BY)"
      - "前缀匹配 (LIKE 'prefix%')"
    not_recommended_for:
      - "正则表达式匹配"
      - "全文搜索"
      - "数组/JSON 内部查询（PostgreSQL 用 GIN 替代）"
    syntax_postgresql: "CREATE INDEX idx_name ON table(column);"
    syntax_mysql: "CREATE INDEX idx_name ON table(column);"

  hash:
    full_name: "Hash Index"
    best_for:
      - "仅等值查询（内存中的哈希查找）"
    limitations:
      - "PostgreSQL 中不支持 WAL 日志（不安全用于复制）"
      - "不支持范围查询和排序"
      - "MySQL InnoDB 不支持 Hash 索引"
    use_case: "内存表或不需要持久化的临时索引"

  gist:
    full_name: "Generalized Search Tree (GiST)"
    best_for:
      - "几何数据（PostGIS: point, polygon, geometry）"
      - "全文搜索（tsvector）"
      - "范围类型（int4range, tsrange）"
      - "排除约束（EXCLUDE）"
    syntax: "CREATE INDEX idx_geom ON locations USING GIST(geography);"

  gin:
    full_name: "Generalized Inverted Index (GIN)"
    best_for:
      - "JSONB 内部元素查询（@>, ?）"
      - "数组包含查询（&&, @>)"
      - "全文搜索（tsvector，比 GiST 更适合静态数据）"
      - "trigram 模糊匹配（pg_trgm 扩展）"
    syntax: "CREATE INDEX idx_metadata ON products USING GIN(metadata);"

  brin:
    full_name: "Block Range Index (BRIN)"
    best_for:
      - "物理有序的大表（按时间递增的日志表）"
      - "存储空间极小（比 B-Tree 小约 100x）"
    syntax: "CREATE INDEX idx_audit_ts ON audit_logs USING BRIN(created_at);"
    condition: "数据插入顺序与索引列的自然排序高度相关"
```

##### 索引推荐决策树

```
需要加速什么查询?
├── 精确匹配某列值?
│   ├── 单列等值? → B-Tree (最常见选择)
│   └── 多列联合等值? → Composite B-Tree (注意列顺序!)
│
├── 范围查询?
│   ├── 数值/日期范围? → B-Tree
│   └── 时间范围且表很大且有序? → BRIN (极省空间)
│
├── 排序 (ORDER BY)?
│   └── B-Tree (天然有序，避免 filesort)
│
├── 模糊搜索?
│   ├── 前缀匹配 LIKE 'abc%'? → B-Tree
│   ├── 后缀/中间匹配? → trigram GIN 索引 (pg_trgm)
│   └── 全文搜索? → GIN tsvector 或 GiST tsvector
│
├── JSON/JSONB 内部查询?
│   └── GIN (PostgreSQL jsonb_path_ops)
│
├── 地理位置?
│   └── GiST (PostGIS geometry)
│
├── 多列组合条件?
│   ├── 等值+范围? → 复合索引 (等值列在前)
│   └── 多个独立条件? → 多个单列索引 (考虑 Index Merge)
│
└── 低选择性列 (< 5%)?
    └── 不要建索引! 全表扫描更快
```

##### 复合索引列顺序规则

```
复合索引 (a, b, c) 的使用情况:
├── WHERE a = ? AND b = ? AND c = ?    → ✅ 完全命中 (Index Scan)
├── WHERE a = ? AND b = ?               → ✅ 命中前缀 (Index Scan)
├── WHERE a = ?                         → ✅ 命中前缀 (Index Scan)
├── WHERE b = ? AND c = ?               → ❌ 不能使用 (跳过了a)
├── WHERE a = ? AND c = ?               → ⚠️ 部分使用 (只用a, c被跳过)
├── ORDER BY a, b, c                   → ✅ 避免排序
├── ORDER BY a DESC, b ASC             → ⚠️ 混合方向可能无法利用
└── SELECT a, b FROM ...               → ✅ Index Only Scan (覆盖索引)

规则: 将等值过滤条件放在前面，范围条件和排序列放在后面
```

#### 3.3 分片策略

```yaml
sharding_strategies:

  horizontal_sharding:
    name: "水平分片（Sharding）"
    description: "按某个分片键将数据分布到多个物理节点"
    shard_keys:
      - user_id: "用户维度分片（最常见，用户数据聚集在同一节点）"
      - tenant_id: "多租户 SaaS 分片"
      - time_range: "时间范围分片（日志类数据）"
      - hash: "哈希分片（均匀分布）"
    pros: ["线性扩展", "单个查询只访问一个节点"]
    cons: ["跨分片 JOIN 困难", "分片键选择不可逆"]
    tools: ["Vitess", "Citus (PG)", "ShardingSphere", "MongoDB Sharding"]

  vertical_sharding:
    name: "垂直拆分"
    description: "按业务域将表分配到不同数据库"
    strategy:
      - "用户服务库: users, profiles, auth"
      - "订单服务库: orders, order_items, payments"
      - "商品服务库: products, categories, inventory"
    pros: ["业务隔离清晰", "各库可独立扩展"]
    cons: ["跨服务事务复杂", "需要分布式事务或最终一致"]

  read_write_splitting:
    name: "读写分离"
    description: "写操作走主库，读操作走从库副本"
    implementation:
      - "应用层路由: 代码中区分 read/write DataSource"
      - "中间件层: ProxySQL / MySQL Router / PgPool-II"
      - "云托管: RDS Aurora / Cloud SQL (内置读写分离)"
    considerations:
      - "复制延迟问题（写后立即读可能读到旧数据）"
      - "从库数量与读负载成正比"
      - "需要监控主从延迟"

  geographic_distribution:
    name: "地理分布"
    description: "数据就近存储，满足数据主权要求"
    pattern:
      - "亚太用户 → 亚太区域数据库"
      - "欧洲用户 → 欧洲区域数据库（GDPR 合规）"
      - "全球查询 → 聚合层 / CDN 边缘"
    challenges:
      - "跨区域延迟"
      - "数据同步冲突解决"
      - "合规性差异处理"
```

### 阶段四：验证（Verify）

#### 4.1 Schema 变更影响评估

每次 Schema 变更前，评估对应用层的影响：

```yaml
impact_assessment_template:
  change_type: "ADD_COLUMN / DROP_COLUMN / MODIFY_TYPE / ADD_INDEX / DROP_INDEX / RENAME"

  backward_compatibility_check:
    add_column_with_default:
      breaking: false
      notes: "新列有默认值，旧代码不受影响"
    add_column_not_null_without_default:
      breaking: true
      notes: "需要两步迁移：(1)加可空列+填默认值 (2)改NOT NULL"
    drop_column:
      breaking: true
      notes: "任何引用此列的代码都会失败"
      mitigation: "先标记废弃，保留至少一个版本周期"
    modify_type_narrowing:
      breaking: true  # 如 VARCHAR(100) → VARCHAR(50)
      notes: "可能截断现有数据"
    modify_type_widening:
      breaking: false  # 如 VARCHAR(50) → VARCHAR(100)
      notes: "PostgreSQL/MySQL 支持在线扩大列宽"
    rename_column/table:
      breaking: true
      notes: "所有 ORM 映射、SQL 查询都需要更新"
      mitigation: "创建视图别名过渡"

  application_layer_impact:
    orm_layer:
      - "Entity 类字段是否需要更新？"
      - "DTO/Schema 是否需要同步修改？"
      - "Repository 查询是否受影响？"
    api_layer:
      - "请求/响应 DTO 是否变化？"
      - "OpenAPI 文档是否需要更新？"
      - "前端是否需要配合修改？"
    test_layer:
      - "单元测试 fixture 是否需要更新？"
      - "集成测试断言是否需要调整？"
      - "Seed 数据脚本是否需要修改？"

  performance_impact:
    add_index:
      write_impact: "每次 INSERT/UPDATE/DELETE 需维护索引"
      storage_impact: "索引占用额外磁盘空间（通常为数据的 10-50%）"
      query_benefit: "目标查询从 SeqScan 变为 IndexScan"
    drop_index:
      query_regression: "依赖此索引的查询退化为全表扫描"
```

#### 4.2 迁移安全性检查

```bash
# 迁移前安全检查清单

# 1. 备份当前数据库
pg_dump -Fc -f backup_$(date +%Y%m%d_%H%M%S).dump db_name

# 2. 在 staging 环境预演迁移
# 3. 检查锁竞争风险（大表 DDL 可能导致长时间排他锁）
# 4. 对于生产环境大表变更，使用 pg_repack / gh-ost / pt-online-schema-change
# 5. 准备回滚脚本（downgrade/migration --down）

# 迁移后验证
# 6. 行数一致性检查
SELECT count(*) FROM new_table;  # vs expected
# 7. 应用层冒烟测试
# 8. 慢查询监控（新索引是否生效？是否有新的慢查询？）
```

### 阶段五：记录（Record）

#### 5.1 Schema 变更日志

```markdown
## Schema Change Log

| Date | Migration ID | Type | Description | Impact | Author | Status |
|------|-------------|------|-------------|--------|--------|--------|
| 2024-01-15 | 001_init | CREATE | 初始化7张核心表 | New feature | autonomous | ✅ Applied |
| 2024-01-18 | 002_add_user_avatar | ALTER | users表新增avatar_url字段 | Feature | autonomous | ✅ Applied |
| 2024-01-20 | 003_orders_idx | INDEX | 订单表新增状态+时间复合索引 | Performance | autonomous | ✅ Applied |
| 2024-01-25 | 004_audit_partition | PARTITION | audit_logs表按月分区 | Scale | autonomous | 🔄 Pending Review |
```

#### 5.2 ER 图版本管理

每次 Schema 变更后，自动更新 Mermaid ER 图并提交至 `docs/database/er-diagrams/` 目录。

## 典型自主场景

### 场景1：为新业务模块设计完整数据模型

**输入**: "设计一个库存管理系统的数据库"

**自主流程**:

1. **感知**：识别核心实体（Warehouse/Product/InventoryLog/Shelf/StockMovement）→ 定义属性和关系
2. **决策**：选用 PostgreSQL（事务强一致性需求）+ SQLAlchemy ORM（Python项目）→ 设计到3NF + 合理的反规范化
3. **执行**：生成 Mermaid ER 图 → 生成 Alembic 迁移脚本（含 up/down）→ 生成 SQLAlchemy Model
4. **验证**：规范化检查通过（1NF✓ 2NF✓ 3NF✓ BCNF✓）→ 外键完整性检查通过
5. **记录**：输出 Schema Change Log + ER 图文件

### 场景2：发现并修复缺失索引

**输入**: 定期巡检模式（分析慢查询日志）

**自主流程**:

1. **感知**：解析 slow_query_log → 发现 `SELECT * FROM orders WHERE customer_id = ? AND status = 'pending'` 耗时 > 2s
2. **决策**：该查询缺少 `(customer_id, status)` 复合索引 → 推荐创建 B-Tree 复合索引
3. **执行**：生成迁移脚本 `CREATE INDEX CONCURRENTLY idx_orders_cust_status ON orders(customer_id, status)`（CONCURRENTLY 避免锁表）
4. **验证**：重新执行慢查询 → 从 2.3s 降至 12ms
5. **记录**：记录索引变更及其性能提升数据

### 场景3：Schema 大表在线变更

**输入**: "给 users 表增加 phone_number 列（表有 500 万行）"

**自主流程**:

1. **感知**：评估表规模 → 直接 ALTER TABLE 可能锁表数十秒
2. **决策**：采用两步安全迁移策略
3. **执行**：
   - Step 1: `ALTER TABLE users ADD COLUMN phone_number VARCHAR(20);` （瞬时完成，允许NULL）
   - Step 2: `UPDATE users SET phone_number = '' WHERE phone_number IS NULL;` （分批更新）
   - Step 3: `ALTER TABLE users ALTER COLUMN phone_number SET NOT NULL;` （此时无NULL值）
4. **验证**：全量测试通过，无锁表事件
5. **记录**：记录大表安全变更过程作为后续参考

## 决策框架

### 数据类型选择决策树

```
要存储什么类型的数据?
├── 整数?
│   ├── 自增ID? → SERIAL/BIGSERIAL (PG) / AUTO_INCREMENT (MySQL)
│   ├── 范围 0-255? → SMALLINT / TINYINT
│   ├── 范围 ±21亿? → INT
│   └── 更大范围? → BIGINT
├── 小数/金额?
│   ├── 需要精确计算? → DECIMAL/NUMERIC (绝不使用 FLOAT 存钱!)
│   └── 近似科学计算? → FLOAT / DOUBLE PRECISION
├── 字符串?
│   ├── 定长短串（如国家代码）? → CHAR(2)
│   ├── 变长文本? → VARCHAR(n) / TEXT (PG 中无性能差异)
│   ├── 可能超长? → TEXT (PG) / LONGTEXT (MySQL)
│   └── 结构化键值对? → JSONB (PG) / JSON (其他)
├── 布尔? → BOOLEAN
├── 日期时间?
│   ├── 仅日期? → DATE
│   ├── 时间戳? → TIMESTAMP / TIMESTAMPTZ (推荐带时区)
│   ├── 时间间隔? → INTERVAL (PG) / 不直接支持 (MySQL)
│   └── 同时存日期和时间? → TIMESTAMPTZ
├── 二进制?
│   ├── 小文件? → BYTEA (PG) / BLOB (MySQL)
│   └── 大文件? → 存对象存储(S3/OSS)，DB只存URL
├── 枚举?
│   ├── 少量固定选项? → ENUM 类型
│   └── 可能扩展? → 查找表 (reference table) + 外键
└── UUID/GUID?
    └── UUID (PG原生) / CHAR(36) (兼容模式)
```

### 主键策略对比

| 策略 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| 自增整数 | 紧凑、自然有序 | 可预测、分布式困难 | 单机简单应用 |
| UUID v4 | 全球唯一、无需协调 | 无序（随机写入）、36字符 | 分布式系统 |
| ULID/UUID v7 | 有序+唯一 | 非标准、需库支持 | 新项目推荐 |
| Snowflake | 有序+分布式 | 依赖时钟同步 | 高并发分布式 |

## 安全与治理

### 数据安全红线

1. **绝不明文存储密码**：必须使用 bcrypt/scrypt/argon2 哈希
2. **绝不硬编码连接字符串**：数据库凭证走环境变量或密钥管理服务
3. **绝不 GRANT 过度权限**：应用账号仅需最小必要权限（SELECT/INSERT/UPDATE/DELETE，不用 DROP/ALTER/GRANT）
4. **绝不在查询中拼接用户输入**：参数化查询是底线（防 SQL 注入）
5. **敏感字段加密存储**：PII（身份证号、手机号、银行卡）考虑字段级加密
6. **审计日志不可关闭**：关键表的 DML 操作必须有审计追踪

### 权限分级

| 操作等级 | 需要审批 | 自主执行范围 |
|----------|---------|-------------|
| 只读分析 | 否 | EXPLAIN ANALYZE、查询计划分析、度量报告 |
| 新增表/索引 | 建议 | 新业务实体的表和索引创建 |
| 修改表结构 | 必须 | ALTER TABLE（特别是生产环境） |
| 删除表/数据 | 必须 | DROP TABLE / TRUNCATE / DELETE（无条件限制） |
| 权限变更 | 必须 | GRANT / REVOKE / ROLE 管理 |
| 迁移执行 | 必须 | 生产环境 migrate deploy（staging 可自主） |

### 数据备份策略

```yaml
backup_policy:
  full_backup:
    frequency: "每日凌晨 02:00"
    retention: "30 天"
    method: "pg_dump -Fc (PostgreSQL) / mysqldump (MySQL)"
  incremental_backup:
    frequency: "每小时"
    retention: "7 天"
    method: "WAL 归档 (PG) / binlog (MySQL)"
  point_in_time_recovery:
    enabled: true
    rpo_target: "< 1 小时"
  backup_encryption: "AES-256 at rest"
  offsite_replication: "跨可用区异步复制"
```

## 协作关系

### 上游依赖

| 上游司 | 协作内容 | 接口方式 |
|--------|---------|---------|
| **API设计司** (api_design_si) | API 响应结构驱动表字段设计 | 接收 OpenAPI Schema |
| **代码生成司** (code_generation_si) | 根据 Model 生成 Repository 层代码 | 接收 ER 图 / DDL |
| 产品规划司 | 业务实体和关系定义 | 接收 PRD 中的数据需求 |

### 下游输出

| 下游消费者 | 输出物 | 格式 |
|------------|--------|------|
| 后端开发 | ORM Model + 迁移脚本 | Python/TS/Prisma/SQL |
| DevOps司 | 数据库初始化脚本 + 备份配置 | SQL / YAML |
| 测试司 | Test Fixture / Seed Data | SQL / Factory |
| 运维司 | 监控指标 + 容量规划建议 | Markdown / Grafana Dashboard |

---

## 🤝 v5.1 增强：Agency Agent 协作指南

### 可调用的 Agency Agents

| Agent 名称 | 所属部门 | 协作模式 | 适用场景 |
|-----------|---------|---------|---------|
| Database Optimizer | Data Division | 诊断→优化 | 慢查询分析、索引策略、查询重写、分区方案 |
| Data Engineer | Data Division | 管线→基建 | ETL Pipeline 设计、数据仓库建模、数据质量监控 |

### Agent 协作工作流

1. **Schema 设计阶段**：本司完成 ER 建模和规范化检查后，Database Optimizer 审核索引策略和查询性能影响
2. **迁移脚本生成阶段**：Data Engineer 评估迁移对现有 ETL/Data Pipeline 的影响范围
3. **性能验证阶段**：Database Optimizer 对新增 Schema 执行 EXPLAIN 分析，确认查询计划最优
4. **运维交接阶段**：两个 Agent 共同输出数据库容量规划和监控面板配置

### 典型协作场景

- **场景一：高并发订单表设计** — 本司设计 Order 表Schema（含复合索引）→ Database Optimizer 分析高并发写入瓶颈推荐分区策略 → Data Engineer 评估对下游数仓ETL的影响 → 输出兼顾OLTP性能和数据管道兼容的最终方案
- **场景二：大表在线迁移** — 本司生成安全迁移脚本（两步ALTER TABLE）→ Database Optimizer 验证迁移期间锁竞争风险 → Data Engineer 同步调整依赖该表的 ETL 任务容错逻辑 → 输出零停机迁移方案

---

## 🏗️ v5.1 增强：Harness 工程实践

### 相关 Harness 模块

- **CD 流水线 — Database Migration Strategy**：将数据库迁移脚本纳入 CD 流水线的独立阶段，支持 `staging 预演 → 生产执行 → 回滚预案` 的标准化流程
- **Chaos Engineering — DB Fault Injection**：通过 Chaos 实验注入数据库故障（连接池耗尽、主从延迟、死锁），验证应用的数据库容错能力
- **Service Reliability (SRE)**：将数据库查询延迟(P95)、连接池使用率、慢查询数量纳入 SLO 监控

### 实践指南

1. **CD 驱动的数据库迁移标准化**：所有 Schema 变更迁移脚本（Alembic/Flyway/Prisma Migrate）通过 Harness CD 流水线的 `database-migration` stage 自动执行。流程为：(1) Staging 环境自动执行迁移 + 数据一致性校验 → (2) 生成 migration 报告（行数校验、外键完整性、性能基线对比）→ (3) 人工审批后生产环境执行 → (4) 自动保留回滚脚本。
2. **Chaos 实验中的 DB 故障注入**：每季度通过 Harness Chaos Engineering 执行一次数据库层面的故障演练——包括主从切换（模拟主库宕机）、连接池耗尽（模拟流量突增）、查询超时（模拟慢SQL）。验证本司设计的 Schema 在极端场景下是否能优雅降级而非级联崩溃。
3. **SLO 驱动的数据库健康度监控**：在 Harness SRE 中配置以下 SLO：P95 查询延迟 < 100ms、连接池利用率 < 80%、每小时慢查询(<1s) 数量 < 10。任一 SLO 违规时自动触发 Database Optimizer Agent 进行诊断并输出优化建议。

---

## 🆕 v6.0 增强能力集成

### MARC资源协调器集成指南

本司在多Agent并发场景下的资源协调要求：

#### 资源锁机制
- **文件写锁**：当本司需要修改数据库Schema、迁移脚本、ORM配置时，必须通过MARC申请互斥锁
  ```python
  # 示例：申请文件写锁
  from skillscripts.resource_coordinator import LockManager, LockType
  lock_mgr = LockManager()
  lock_id = lock_mgr.acquire_lock(
      resource_id="path/to/migrations/001_init.sql",
      agent_id="数据库开发司",
      lock_type=LockType.EXCLUSIVE,
      priority=9,
      timeout=180.0
  )
  ```
- **读锁**：读取Schema定义、ORM模型、数据字典时申请读锁（高频查询场景）
- **释放锁**：数据库设计和迁移操作完成后立即释放锁，避免阻塞其他司的数据访问

#### 终端会话池使用
- 从MARC终端会话_pool获取会话执行数据库迁移命令（alembic upgrade/flyway migrate等）
- 会话使用完毕后及时归还池中
- 单个命令超时设置为300秒（大型数据库迁移可能耗时较长）

#### 并发安全注意事项
- 数据库Schema是核心共享资产，写入时必须独占锁保护
- 迁移脚本执行需串行化，避免并发迁移导致Schema不一致
- 死锁预防：按固定顺序申请锁（先锁Schema定义→再锁迁移脚本→最后锁ORM配置）

### 四维度输出防线集成

| 防线层级 | 本司检查重点 | 自动化程度 |
|---------|-------------|----------|
| **提示词工程层** | Schema设计提示词、ER图生成提示词、索引优化提示词 | 半自动（AI辅助） |
| **能力约束层** | 仅允许数据库操作（Schema/迁移/优化），禁止修改应用业务逻辑 | 全自动 |
| **规则校验层** | 输出格式：SQL迁移脚本、Prisma/SQLAlchemy ORM模型、Markdown数据字典 | 全自动 |
| **兜底恢复层** | 迁移失败时自动执行回滚脚本并恢复至上一版本 | 半自动 |

### 操作优先级指引（v6.0核心）

本司推荐的操作方式：

1. 🥇 **Agent自主手动操作**（强烈推荐用于Schema设计、迁移脚本编写、索引优化）
   - 示例：直接编辑SQL迁移文件、手动编写ORM模型、逐步优化查询性能
   - 优势：精确控制数据库结构、可逐步验证正确性、可随时回滚迁移

2. 🥈 **规划脚本操作**（适用于数据库初始化、周期性性能分析）
   - 推荐脚本：
     - `skillscripts/resource_coordinator/quota_manager.py` — 检查数据库存储配额和连接数限制
     - `skillscripts/open_source_philosophy/clawcode_sdd_tdd_engine.py` — SDD/TDD驱动的数据库实践
     - `skillscripts/platform/powershell_adapter.py` — PS7环境适配

3. 🥉 **命令操作**（仅限数据库迁移执行、备份恢复等极少数场景）
   - ⚠️ 必须预演影响范围（数据库变更影响全局数据完整性）
   - ⚠️ 生产环境迁移需获得DBA审批并准备回滚预案
   - 推荐使用PS7适配器转换alembic/flyway/prisma migrate等迁移工具命令

### PowerShell 7 执行指南

本司相关操作的PS7适配要点：
- 迁移执行：alembic upgrade head / flyway migrate / prisma migrate deploy 等命令原生可用
- 数据库操作：psql / mysql / sqlite3 等CLI工具用于查询和诊断
- 性能分析：EXPLAIN ANALYZE / pg_stat_statements 等工具用于慢查询分析
- 编码：确保所有输出 UTF-8 无 BOM（迁移脚本和数据字典）

### 与其他司的协作接口

- 上游依赖：API设计司（接收数据模型需求以设计Schema）、代码生成司（获取ORM配置用于数据访问）
- 下游输出：依赖管理司（推送数据库驱动版本要求）、环境配置司（提供数据库连接配置）
- 数据交换格式：SQL / Prisma Schema / SQLAlchemy Model / Markdown（统一UTF-8无BOM）
