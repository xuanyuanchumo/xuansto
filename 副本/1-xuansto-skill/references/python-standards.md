# Python 开发规范

> 版本: 1.0.0 | 更新日期: 2025-04-17 | 编码: UTF-8 without BOM | 行尾: LF

---

## 目录

1. [PEP 8 命名规范与代码风格](#1-pep-8-命名规范与代码风格)
2. [类型注解规范 (Type Hints)](#2-类型注解规范-type-hints)
3. [项目结构规范](#3-项目结构规范)
4. [测试规范](#4-测试规范)
5. [依赖管理规范](#5-依赖管理规范)
6. [安全规范](#6-安全规范)
7. [常见框架规范](#7-常见框架规范)
8. [检查清单](#8-检查清单)

---

## 1. PEP 8 命名规范与代码风格

### 1.1 命名规范

| 类型 | 命名风格 | 示例 |
|------|----------|------|
| 模块 | snake_case | `user_service.py` |
| 包 | snake_case | `my_package/` |
| 类 | PascalCase | `UserService` |
| 函数 | snake_case | `get_user_by_id()` |
| 方法 | snake_case | `calculate_total()` |
| 变量 | snake_case | `user_count` |
| 常量 | UPPER_SNAKE_CASE | `MAX_CONNECTIONS` |
| 私有属性 | _leading_underscore | `_internal_value` |
| 强私有属性 | __double_underscore | `__private_data` |
| 魔术方法 | __double_underscore__ | `__init__`, `__str__` |

### 1.2 代码风格示例

```python
"""
模块文档字符串示例。
描述模块的主要功能和用途。
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30.0


class UserService:
    """用户服务类，处理用户相关业务逻辑。

    Attributes:
        db_connection: 数据库连接实例。
        cache: 缓存实例。

    Example:
        >>> service = UserService(db)
        >>> user = service.get_user(user_id=1)
    """

    def __init__(
        self,
        db_connection: DatabaseConnection,
        cache: Optional[Cache] = None,
    ) -> None:
        self._db = db_connection
        self._cache = cache or MemoryCache()
        self._initialized = False

    def get_user(self, user_id: int) -> Optional[User]:
        """根据ID获取用户信息。

        Args:
            user_id: 用户唯一标识符。

        Returns:
            用户对象，如果不存在则返回None。

        Raises:
            DatabaseError: 数据库连接异常。
        """
        cache_key = f"user:{user_id}"

        if cached := self._cache.get(cache_key):
            return cached

        user = self._db.query(User).filter_by(id=user_id).first()

        if user:
            self._cache.set(cache_key, user, ttl=300)

        return user

    def _validate_user_data(self, data: Dict[str, Any]) -> bool:
        """验证用户数据（内部方法）。"""
        required_fields = {"name", "email", "age"}
        return required_fields.issubset(data.keys())


def calculate_total_price(
    items: List[Dict[str, float]],
    discount: float = 0.0,
) -> float:
    """计算订单总价。

    Args:
        items: 商品列表，每个商品包含price和quantity。
        discount: 折扣率，范围0.0-1.0。

    Returns:
        折扣后的总价。

    Example:
        >>> items = [{"price": 100.0, "quantity": 2}]
        >>> calculate_total_price(items, discount=0.1)
        180.0
    """
    subtotal = sum(
        item["price"] * item["quantity"]
        for item in items
    )
    return subtotal * (1 - discount)
```

### 1.3 行长度与缩进

```python
# 行长度限制：88字符（Black默认）或79字符（PEP 8）

# 正确：使用括号换行
result = some_function_with_long_name(
    first_argument,
    second_argument,
    third_argument,
)

# 正确：链式调用换行
users = (
    session.query(User)
    .filter(User.is_active == True)
    .order_by(User.created_at.desc())
    .limit(10)
    .all()
)

# 缩进：4个空格，禁止Tab
def long_function_name(
    var_one: int,
    var_two: int,
    var_three: int,
) -> int:
    return var_one + var_two + var_three
```

### 1.4 导入规范

```python
# 导入顺序（isort标准）：
# 1. 标准库
# 2. 第三方库
# 3. 本地应用/库

# 标准库
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict

# 第三方库
import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# 本地模块
from myapp.models import User, Order
from myapp.services import UserService
from myapp.utils.helpers import format_date

# 避免使用通配符导入
# 错误：from module import *
# 正确：from module import specific_function
```

---

## 2. 类型注解规范 (Type Hints)

### 2.1 基础类型注解

```python
from typing import (
    Optional,
    List,
    Dict,
    Set,
    Tuple,
    Union,
    Any,
    Callable,
    TypeVar,
    Generic,
    Protocol,
    runtime_checkable,
)
from collections.abc import Iterator, Iterable


# 基本类型
def greet(name: str) -> str:
    return f"Hello, {name}"


# Optional类型（可为None）
def find_user(user_id: int) -> Optional[User]:
    """返回User或None。"""
    pass


# 容器类型
def process_items(
    items: List[str],
    mapping: Dict[str, int],
    unique_ids: Set[int],
) -> Tuple[int, str]:
    """处理多个容器类型参数。"""
    pass


# Union类型
def parse_value(value: Union[str, int, float]) -> float:
    """接受多种类型参数。"""
    pass


# Python 3.10+ 简化语法
def parse_value_modern(value: str | int | float) -> float:
    pass
```

### 2.2 高级类型注解

```python
from typing import TypeAlias, TypedDict, Literal, Final, ClassVar

# 类型别名
UserId: TypeAlias = int
JsonDict: TypeAlias = Dict[str, Any]
Handler: TypeAlias = Callable[[str], None]


# TypedDict（结构化字典）
class UserDict(TypedDict):
    id: int
    name: str
    email: str
    is_active: NotRequired[bool]  # Python 3.11+


class UserDictTotal(TypedDict, total=True):
    """所有字段都是必需的。"""
    id: int
    name: str


class UserDictPartial(TypedDict, total=False):
    """所有字段都是可选的。"""
    id: int
    name: str


# Literal类型
Status = Literal["pending", "active", "inactive", "deleted"]
Direction = Literal["asc", "desc"]


def set_status(user_id: int, status: Status) -> None:
    pass


# Final常量
MAX_SIZE: Final[int] = 100
API_VERSION: Final[str] = "v1"


# ClassVar类变量
class Config:
    instance_count: ClassVar[int] = 0
    default_timeout: ClassVar[int] = 30

    def __init__(self) -> None:
        Config.instance_count += 1
```

### 2.3 泛型与Protocol

```python
from typing import TypeVar, Generic, Protocol, runtime_checkable

T = TypeVar("T")
K = TypeVar("K")
V = TypeVar("V")


# 泛型类
class Repository(Generic[T]):
    """通用仓库基类。"""

    def __init__(self, model_class: type[T]) -> None:
        self.model_class = model_class

    def get_by_id(self, id: int) -> Optional[T]:
        pass

    def save(self, entity: T) -> T:
        pass


# Protocol（结构化子类型）
@runtime_checkable
class Serializable(Protocol):
    """可序列化协议。"""

    def to_dict(self) -> Dict[str, Any]: ...
    def from_dict(self, data: Dict[str, Any]) -> "Serializable": ...


@runtime_checkable
class Comparable(Protocol):
    """可比较协议。"""

    def __lt__(self, other: Any) -> bool: ...
    def __eq__(self, other: Any) -> bool: ...


def sort_items(items: List[Comparable]) -> List[Comparable]:
    return sorted(items)
```

### 2.4 函数签名最佳实践

```python
from typing import ParamSpec, Concatenate, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


# ParamSpec用于装饰器
def retry(
    max_attempts: int = 3,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """重试装饰器。"""

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
            raise RuntimeError("Unreachable")

        return wrapper

    return decorator


# 重载（Overload）
from typing import overload


class DataProcessor:
    @overload
    def process(self, data: str) -> str: ...

    @overload
    def process(self, data: bytes) -> bytes: ...

    @overload
    def process(self, data: List[str]) -> List[str]: ...

    def process(
        self,
        data: str | bytes | List[str],
    ) -> str | bytes | List[str]:
        if isinstance(data, str):
            return data.upper()
        elif isinstance(data, bytes):
            return data.upper()
        else:
            return [item.upper() for item in data]
```

---

## 3. 项目结构规范

### 3.1 标准项目结构 (src layout)

```
project_name/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
│   │   └── release.yml
│   └── ISSUE_TEMPLATE/
├── .vscode/
│   ├── settings.json
│   └── extensions.json
├── docs/
│   ├── index.md
│   ├── api.md
│   └── changelog.md
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── __main__.py
│       ├── core/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── exceptions.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py
│       │   └── order.py
│       ├── services/
│       │   ├── __init__.py
│       │   ├── user_service.py
│       │   └── order_service.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── routes/
│       │   │   ├── __init__.py
│       │   │   ├── users.py
│       │   │   └── orders.py
│       │   └── dependencies.py
│       └── utils/
│           ├── __init__.py
│           ├── helpers.py
│           └── validators.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_user_service.py
│   │   └── test_order_service.py
│   ├── integration/
│   │   ├── __init__.py
│   │   └── test_api.py
│   └── e2e/
│       ├── __init__.py
│       └── test_user_flow.py
├── .gitignore
├── .pre-commit-config.yaml
├── .python-version
├── LICENSE
├── README.md
├── pyproject.toml
└── uv.lock
```

### 3.2 pyproject.toml 配置

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "project-name"
version = "0.1.0"
description = "A modern Python project"
readme = "README.md"
license = {text = "MIT"}
requires-python = ">=3.10"
authors = [
    {name = "Your Name", email = "your@email.com"},
]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
dependencies = [
    "fastapi>=0.109.0",
    "pydantic>=2.5.0",
    "sqlalchemy>=2.0.0",
    "uvicorn[standard]>=0.27.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
    "pre-commit>=3.6.0",
]
docs = [
    "mkdocs>=1.5.0",
    "mkdocs-material>=9.5.0",
]

[project.scripts]
project-cli = "project_name.__main__:main"

[project.urls]
Homepage = "https://github.com/user/project-name"
Documentation = "https://user.github.io/project-name"
Repository = "https://github.com/user/project-name.git"

[tool.hatch.build.targets.wheel]
packages = ["src/project_name"]

[tool.ruff]
target-version = "py310"
line-length = 88
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
    "ARG",    # flake8-unused-arguments
    "SIM",    # flake8-simplify
]
ignore = [
    "E501",   # line too long (handled by formatter)
    "B008",   # do not perform function calls in argument defaults
]

[tool.ruff.isort]
known-first-party = ["project_name"]

[tool.mypy]
python_version = "3.10"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
show_error_codes = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
pythonpath = ["src"]
addopts = [
    "-ra",
    "-q",
    "--strict-markers",
    "--strict-config",
]
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
    "e2e: marks end-to-end tests",
]
filterwarnings = [
    "ignore::DeprecationWarning",
]

[tool.coverage.run]
source = ["src/project_name"]
branch = true
parallel = true
omit = [
    "*/tests/*",
    "*/__main__.py",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
fail_under = 80
show_missing = true

[tool.bandit]
exclude_dirs = ["tests", "venv"]
skips = ["B101"]
```

### 3.3 模块初始化

```python
# src/project_name/__init__.py
"""
Project Name - A modern Python project.

This package provides...
"""

from importlib.metadata import version, PackageNotFoundError

__version__: str

try:
    __version__ = version("project-name")
except PackageNotFoundError:
    __version__ = "0.0.0.dev0"

from project_name.core.config import Config
from project_name.core.exceptions import ProjectError

__all__ = [
    "__version__",
    "Config",
    "ProjectError",
]
```

```python
# src/project_name/__main__.py
"""CLI入口点。"""

import sys


def main() -> int:
    """主函数入口。"""
    print("Hello from Project Name!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

---

## 4. 测试规范

### 4.1 pytest 基础

```python
# tests/conftest.py
"""Pytest配置和共享fixtures。"""

import pytest
from typing import Generator
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from project_name.core.config import Config
from project_name.models.base import Base
from project_name.main import app


@pytest.fixture(scope="session")
def config() -> Config:
    """测试配置。"""
    return Config(
        database_url="sqlite:///:memory:",
        testing=True,
    )


@pytest.fixture(scope="function")
def db_session(config: Config) -> Generator[Session, None, None]:
    """数据库会话fixture。"""
    engine = create_engine(config.database_url)
    Base.metadata.create_all(engine)

    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    yield session

    session.close()
    Base.metadata.drop_all(engine)


@pytest.fixture
def async_client() -> Generator[AsyncClient, None, None]:
    """异步HTTP客户端。"""
    from httpx import ASGITransport

    transport = ASGITransport(app=app)
    with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_user_data() -> dict:
    """示例用户数据。"""
    return {
        "name": "Test User",
        "email": "test@example.com",
        "age": 25,
    }
```

### 4.2 单元测试

```python
# tests/unit/test_user_service.py
"""用户服务单元测试。"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from project_name.services.user_service import UserService
from project_name.models.user import User
from project_name.core.exceptions import UserNotFoundError


class TestUserService:
    """UserService测试类。"""

    @pytest.fixture
    def user_service(self, db_session) -> UserService:
        """创建UserService实例。"""
        return UserService(db_session)

    def test_get_user_by_id_success(
        self,
        user_service: UserService,
        db_session,
    ) -> None:
        """测试成功获取用户。"""
        user = User(id=1, name="Test", email="test@example.com")
        db_session.add(user)
        db_session.commit()

        result = user_service.get_user_by_id(1)

        assert result is not None
        assert result.id == 1
        assert result.name == "Test"

    def test_get_user_by_id_not_found(
        self,
        user_service: UserService,
    ) -> None:
        """测试用户不存在。"""
        result = user_service.get_user_by_id(999)

        assert result is None

    def test_create_user_success(
        self,
        user_service: UserService,
        sample_user_data: dict,
    ) -> None:
        """测试创建用户。"""
        result = user_service.create_user(sample_user_data)

        assert result.id is not None
        assert result.name == sample_user_data["name"]
        assert result.email == sample_user_data["email"]

    @pytest.mark.parametrize("invalid_email", [
        "invalid",
        "@example.com",
        "test@",
        "test.example.com",
    ])
    def test_create_user_invalid_email(
        self,
        user_service: UserService,
        sample_user_data: dict,
        invalid_email: str,
    ) -> None:
        """测试无效邮箱。"""
        sample_user_data["email"] = invalid_email

        with pytest.raises(ValueError, match="Invalid email"):
            user_service.create_user(sample_user_data)


class TestUserServiceAsync:
    """异步测试示例。"""

    @pytest.mark.asyncio
    async def test_async_operation(self) -> None:
        """测试异步操作。"""
        result = await some_async_function()
        assert result is True
```

### 4.3 集成测试

```python
# tests/integration/test_api.py
"""API集成测试。"""

import pytest
from httpx import AsyncClient


class TestUserAPI:
    """用户API测试。"""

    @pytest.mark.asyncio
    async def test_create_user(
        self,
        async_client: AsyncClient,
        sample_user_data: dict,
    ) -> None:
        """测试创建用户API。"""
        response = await async_client.post(
            "/api/v1/users",
            json=sample_user_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == sample_user_data["name"]
        assert "id" in data

    @pytest.mark.asyncio
    async def test_get_user(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试获取用户API。"""
        response = await async_client.get("/api/v1/users/1")

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(
        self,
        async_client: AsyncClient,
    ) -> None:
        """测试获取不存在用户。"""
        response = await async_client.get("/api/v1/users/99999")

        assert response.status_code == 404
```

### 4.4 测试覆盖率

```bash
# 运行测试并生成覆盖率报告
pytest --cov=src/project_name --cov-report=term-missing --cov-report=html

# 只运行特定标记的测试
pytest -m "not slow"

# 运行并显示详细输出
pytest -v --tb=short

# 并行运行测试
pytest -n auto
```

---

## 5. 依赖管理规范

### 5.1 pip + venv

```bash
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt

# 生成依赖文件
pip freeze > requirements.txt
```

```
# requirements.txt
fastapi>=0.109.0,<1.0.0
pydantic>=2.5.0
sqlalchemy>=2.0.0
uvicorn[standard]>=0.27.0

# requirements-dev.txt
-r requirements.txt
pytest>=8.0.0
pytest-cov>=4.1.0
ruff>=0.2.0
mypy>=1.8.0
```

### 5.2 Poetry

```bash
# 初始化项目
poetry init

# 安装依赖
poetry add fastapi pydantic sqlalchemy

# 安装开发依赖
poetry add --group dev pytest pytest-cov ruff mypy

# 安装所有依赖
poetry install

# 更新依赖
poetry update

# 导出requirements.txt
poetry export -f requirements.txt --output requirements.txt

# 运行命令
poetry run pytest
```

```toml
# pyproject.toml (Poetry格式)
[tool.poetry]
name = "project-name"
version = "0.1.0"
description = "A modern Python project"
authors = ["Your Name <your@email.com>"]

[tool.poetry.dependencies]
python = "^3.10"
fastapi = "^0.109.0"
pydantic = "^2.5.0"
sqlalchemy = "^2.0.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
pytest-cov = "^4.1.0"
ruff = "^0.2.0"
mypy = "^1.8.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### 5.3 uv (推荐)

```bash
# 安装uv
pip install uv

# 创建虚拟环境
uv venv

# 激活虚拟环境
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# 安装依赖
uv pip install fastapi pydantic sqlalchemy

# 从pyproject.toml安装
uv pip install -e ".[dev]"

# 同步依赖（更快）
uv pip sync requirements.txt

# 编译依赖锁定
uv pip compile pyproject.toml -o requirements.txt
```

```bash
# 使用uv管理整个项目
uv init project-name
cd project-name

# 添加依赖
uv add fastapi pydantic

# 添加开发依赖
uv add --dev pytest pytest-cov

# 安装所有依赖
uv sync

# 运行脚本
uv run pytest
```

---

## 6. 安全规范

### 6.1 Bandit 安全检查

```bash
# 安装bandit
pip install bandit

# 运行安全检查
bandit -r src/

# 跳过特定检查
bandit -r src/ -s B101,B311

# 生成报告
bandit -r src/ -f json -o security-report.json
```

### 6.2 Safety 依赖安全检查

```bash
# 安装safety
pip install safety

# 检查依赖漏洞
safety check

# 使用requirements文件
safety check -r requirements.txt

# 使用pyproject.toml
safety check --full-report
```

### 6.3 安全编码实践

```python
# 错误：SQL注入风险
def get_user_unsafe(user_id: str) -> User:
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)


# 正确：参数化查询
from sqlalchemy import text


def get_user_safe(user_id: int, session: Session) -> Optional[User]:
    query = text("SELECT * FROM users WHERE id = :id")
    result = session.execute(query, {"id": user_id})
    return result.fetchone()


# 错误：命令注入风险
import os


def list_files_unsafe(filename: str) -> None:
    os.system(f"ls {filename}")


# 正确：使用subprocess
import subprocess


def list_files_safe(filename: str) -> str:
    result = subprocess.run(
        ["ls", filename],
        capture_output=True,
        text=True,
        shell=False,
    )
    return result.stdout


# 正确：密码处理
import secrets
import hashlib


def hash_password(password: str) -> str:
    """安全地哈希密码。"""
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000,
    )
    return f"{salt}:{hashed.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """验证密码。"""
    salt, hashed = stored.split(":")
    new_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000,
    )
    return secrets.compare_digest(new_hash.hex(), hashed)


# 正确：敏感信息处理
import os
from functools import lru_cache


@lru_cache()
def get_secret_key() -> str:
    """从环境变量获取密钥。"""
    key = os.environ.get("SECRET_KEY")
    if not key:
        raise ValueError("SECRET_KEY environment variable not set")
    return key


# 错误：日志中记录敏感信息
def log_user_login(email: str, password: str) -> None:
    logger.info(f"User login: {email}, password: {password}")


# 正确：脱敏处理
def log_user_login_safe(email: str) -> None:
    masked_email = email[:3] + "***" + email.split("@")[-1]
    logger.info(f"User login attempt: {masked_email}")
```

### 6.4 pre-commit 配置

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-json
      - id: check-added-large-files
        args: ['--maxkb=1000']
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.2.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic>=2.0
          - types-requests

  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.6
    hooks:
      - id: bandit
        args: ["-c", "pyproject.toml"]
        additional_dependencies: ["bandit[toml]"]
```

---

## 7. 常见框架规范

### 7.1 FastAPI

```python
# src/project_name/main.py
"""FastAPI应用入口。"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from project_name.core.config import Config
from project_name.core.exceptions import AppException
from project_name.api.routes import users, orders


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理。"""
    config = Config.from_env()
    await setup_database(config)
    yield
    await cleanup_database()


def create_app() -> FastAPI:
    """创建FastAPI应用实例。"""
    app = FastAPI(
        title="Project Name API",
        version="0.1.0",
        description="API documentation",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)

    app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
    app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])

    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    return app


async def app_exception_handler(
    request: Request,
    exc: AppException,
) -> JSONResponse:
    """应用异常处理。"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "detail": exc.detail,
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """验证异常处理。"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "detail": exc.errors(),
        },
    )


app = create_app()
```

```python
# src/project_name/api/routes/users.py
"""用户路由。"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr

from project_name.services.user_service import UserService
from project_name.api.dependencies import get_user_service


router = APIRouter()


class UserCreate(BaseModel):
    """创建用户请求。"""

    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=0, le=150)


class UserResponse(BaseModel):
    """用户响应。"""

    id: int
    name: str
    email: str
    age: int
    is_active: bool = True

    class Config:
        from_attributes = True


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    user_data: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """创建新用户。"""
    user = service.create_user(user_data.model_dump())
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """获取用户信息。"""
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found",
        )
    return UserResponse.model_validate(user)


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    service: UserService = Depends(get_user_service),
) -> List[UserResponse]:
    """获取用户列表。"""
    users = service.list_users(skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]
```

### 7.2 Django

```python
# project_name/settings/base.py
"""Django基础配置。"""

from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = "{{ secret_key }}"

INSTALLED_APPS: List[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "project_name.apps.users",
    "project_name.apps.orders",
]

MIDDLEWARE: List[str] = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "project_name.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "project_name.wsgi.application"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

```python
# project_name/apps/users/models.py
"""用户模型。"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """自定义用户模型。"""

    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "users"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.email
```

```python
# project_name/apps/users/serializers.py
"""用户序列化器。"""

from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer[User]):
    """用户序列化器。"""

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "phone",
            "avatar",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class UserCreateSerializer(serializers.ModelSerializer[User]):
    """创建用户序列化器。"""

    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "confirm_password",
            "phone",
        ]

    def validate(self, data: dict) -> dict:
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data: dict) -> User:
        validated_data.pop("confirm_password")
        password = validated_data.pop("password")
        user = User.objects.create_user(**validated_data, password=password)
        return user
```

```python
# project_name/apps/users/views.py
"""用户视图。"""

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from .models import User
from .serializers import UserSerializer, UserCreateSerializer


class UserViewSet(viewsets.ModelViewSet[User]):
    """用户视图集。"""

    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self) -> type[serializers.Serializer]:
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def create(self, request: Request) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def activate(self, request: Request, pk: int | None = None) -> Response:
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({"status": "activated"})
```

### 7.3 Flask

```python
# src/project_name/app.py
"""Flask应用工厂。"""

from typing import Optional

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from marshmallow import Schema, fields, validate, ValidationError

db = SQLAlchemy()
ma = Marshmallow()


def create_app(config_name: Optional[str] = None) -> Flask:
    """创建Flask应用实例。"""
    app = Flask(__name__)

    config_name = config_name or "development"
    app.config.from_object(f"project_name.config.{config_name.capitalize()}Config")

    db.init_app(app)
    ma.init_app(app)

    register_routes(app)
    register_error_handlers(app)

    return app


def register_routes(app: Flask) -> None:
    """注册路由。"""

    @app.route("/api/v1/users", methods=["GET"])
    def list_users():
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        pagination = User.query.paginate(page=page, per_page=per_page)
        return jsonify(
            {
                "users": UserSchema().dump(pagination.items, many=True),
                "total": pagination.total,
                "pages": pagination.pages,
            }
        )

    @app.route("/api/v1/users/<int:user_id>", methods=["GET"])
    def get_user(user_id: int):
        user = User.query.get_or_404(user_id)
        return jsonify(UserSchema().dump(user))

    @app.route("/api/v1/users", methods=["POST"])
    def create_user():
        try:
            data = UserCreateSchema().load(request.json)
        except ValidationError as e:
            return jsonify({"errors": e.messages}), 400

        user = User(**data)
        db.session.add(user)
        db.session.commit()

        return jsonify(UserSchema().dump(user)), 201


def register_error_handlers(app: Flask) -> None:
    """注册错误处理器。"""

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({"error": "Internal server error"}), 500


class User(db.Model):
    """用户模型。"""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self) -> str:
        return f"<User {self.email}>"


class UserSchema(ma.SQLAlchemyAutoSchema):
    """用户序列化Schema。"""

    class Meta:
        model = User
        load_instance = True


class UserCreateSchema(Schema):
    """创建用户Schema。"""

    name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = fields.Email(required=True)
```

---

## 8. 检查清单

### 8.1 代码风格检查清单

- [ ] 所有命名遵循PEP 8规范
- [ ] 行长度不超过88字符（Black默认）
- [ ] 使用4个空格缩进，无Tab
- [ ] 导入语句按标准库/第三方/本地模块排序
- [ ] 每个模块、类、函数都有文档字符串
- [ ] 使用f-string进行字符串格式化
- [ ] 避免使用通配符导入

### 8.2 类型注解检查清单

- [ ] 所有公共函数都有类型注解
- [ ] 使用Optional表示可能为None的返回值
- [ ] 使用Union或|表示多种类型
- [ ] 使用TypedDict定义结构化字典
- [ ] 使用Protocol定义接口协议
- [ ] mypy检查通过，无错误

### 8.3 项目结构检查清单

- [ ] 使用src layout结构
- [ ] pyproject.toml配置完整
- [ ] __init__.py正确导出公共API
- [ ] 测试目录结构清晰（unit/integration/e2e）
- [ ] 配置文件分离（开发/测试/生产）

### 8.4 测试检查清单

- [ ] 测试覆盖率>=80%
- [ ] 单元测试覆盖核心逻辑
- [ ] 集成测试覆盖API端点
- [ ] 使用pytest fixtures管理测试数据
- [ ] 参数化测试覆盖边界情况
- [ ] 异步测试正确标记@pytest.mark.asyncio

### 8.5 安全检查清单

- [ ] 无SQL注入风险（使用参数化查询）
- [ ] 无命令注入风险（不使用shell=True）
- [ ] 密码使用安全哈希存储
- [ ] 敏感信息不记录在日志中
- [ ] 环境变量管理密钥，无硬编码
- [ ] bandit检查通过
- [ ] safety检查无已知漏洞

### 8.6 依赖管理检查清单

- [ ] 使用虚拟环境隔离依赖
- [ ] requirements文件或pyproject.toml完整
- [ ] 依赖版本有明确约束
- [ ] 开发依赖与生产依赖分离
- [ ] 依赖锁定文件存在（poetry.lock/uv.lock）

### 8.7 框架特定检查清单

**FastAPI:**
- [ ] 使用Pydantic模型验证请求/响应
- [ ] 使用依赖注入管理服务
- [ ] 异常处理统一
- [ ] CORS配置正确

**Django:**
- [ ] 使用自定义User模型
- [ ] settings按环境分离
- [ ] 使用select_related/prefetch_related优化查询
- [ ] migrations正确管理

**Flask:**
- [ ] 使用应用工厂模式
- [ ] 蓝图组织路由
- [ ] 配置类分离
- [ ] 错误处理统一

---

## 参考资料

- [PEP 8 -- Style Guide for Python Code](https://peps.python.org/pep-0008/)
- [PEP 484 -- Type Hints](https://peps.python.org/pep-0484/)
- [Python Packaging User Guide](https://packaging.python.org/en/latest/)
- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Django Documentation](https://docs.djangoproject.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Bandit Documentation](https://bandit.readthedocs.io/)
- [Safety Documentation](https://pyup.io/safety/)
