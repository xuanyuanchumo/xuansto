"""
模板管理司 - 项目脚手架生成、代码骨架生成、配置文件模板、模板变量替换
"""
from __future__ import annotations

import re
import json
import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class TemplateManagementError(Exception):
    """模板管理相关异常"""
    pass


class ScaffoldError(TemplateManagementError):
    """脚手架错误"""


class TechStack(str, Enum):
    """技术栈枚举"""
    FASTAPI = "fastapi"
    FLASK = "flask"
    DJANGO = "django"
    NEXTJS = "nextjs"
    REACT_VITE = "react_vite"
    VUE3_NUXT = "vue3_nuxt"
    NESTJS = "nestjs"
    GIN = "gin"
    ECHO = "echo"
    FIBER = "fiber"
    ACTIX_WEB = "actix_web"
    AXUM = "axum"
    REACT_NATIVE = "react_native"
    FLUTTER = "flutter"
    SWIFTUI = "swiftui"


@dataclass
class ProjectScaffold:
    """项目脚手架"""
    name: str
    tech_stack: TechStack
    directory_structure: dict[str, Any] = field(default_factory=dict)
    files: dict[str, str] = field(default_factory=dict)
    dependencies: list[dict[str, str]] = field(default_factory=list)
    dev_dependencies: list[dict[str, str]] = field(default_factory=list)
    scripts: dict[str, str] = field(default_factory=dict)
    description: str = ""
    version: str = "1.0.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "tech_stack": self.tech_stack.value,
            "description": self.description,
            "version": self.version,
            "file_count": len(self.files),
            "dependency_count": len(self.dependencies),
            "script_count": len(self.scripts),
        }


@dataclass
class CodeSkeleton:
    """代码骨架"""
    name: str
    language: str
    architecture_pattern: str = ""
    files: list[tuple[str, str]] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    base_classes: list[str] = field(default_factory=list)
    interfaces: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "language": self.language,
            "architecture_pattern": self.architecture_pattern,
            "file_count": len(self.files),
            "interfaces": self.interfaces,
            "base_classes": self.base_classes,
        }


@dataclass
class ConfigTemplate:
    """通用配置文件模板"""
    filename: str
    content: str
    category: str = "general"
    language: str = "universal"
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "filename": self.filename,
            "category": self.category,
            "language": self.language,
            "description": self.description,
            "content_length": len(self.content),
        }


@dataclass
class TemplateVariable:
    """模板变量定义"""
    name: str
    default_value: str = ""
    description: str = ""
    variable_type: str = "string"
    required: bool = False
    pattern: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "default_value": self.default_value,
            "description": self.description,
            "variable_type": self.variable_type,
            "required": self.required,
        }


@dataclass
class ScaffoldResult:
    """脚手架生成结果"""
    project_name: str
    tech_stack: TechStack
    total_files: int = 0
    total_dirs: int = 0
    generated_files: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    generation_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_name": self.project_name,
            "tech_stack": self.tech_stack.value,
            "total_files": self.total_files,
            "total_dirs": self.total_dirs,
            "generated_files": self.generated_files[:20],
            "warnings": self.warnings,
            "generation_time_ms": round(self.generation_time_ms, 2),
        }


_SCAFFOLD_TEMPLATES: dict[TechStack, dict[str, Any]] = {
    TechStack.FASTAPI: {
        "description": "FastAPI异步Web框架，支持Pydantic验证和依赖注入",
        "structure": {
            "app/": {"__init__.py": "", "main.py": "", "config.py": "",
                     "api/": {"__init__.py": "", "v1/": {"__init__.py": "", "router.py": ""}},
                     "models/": {"__init__.py": "", "user.py": ""},
                     "schemas/": {"__init__.py": "", "user.py": ""},
                     "services/": {"__init__.py": "", "user_service.py": ""},
                     "core/": {"__init__.py": "", "security.py": "", "database.py": ""},
                     "utils/": {"__init__.py": "", "logger.py": ""}},
            "tests/": {"__init__.py": "", "conftest.py": "", "test_api/": {"__init__.py": "", "test_users.py": ""}},
            "alembic/": {"env.py": "", "versions/": None},
            "scripts/": {},
        },
        "key_files": {
            "app/main.py": '''"""FastAPI应用入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.config import settings

app = FastAPI(
    title="{{project_name}}",
    description="{{project_description}}",
    version="{{version}}",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "{{project_name}}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
            "app/config.py": '''"""应用配置管理"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "{{project_name}}"
    debug: bool = True
    database_url: str = "postgresql://localhost:5432/{{project_name}}"
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str = "change-me-in-production"
    cors_origins: list[str] = ["http://localhost:3000"]
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    class Config:
        env_file = ".env"

settings = Settings()
''',
            "requirements.txt": """fastapi>=0.109.0,<0.110.0
uvicorn[standard]>=0.27.0
pydantic>=2.6.0
pydantic-settings>=2.1.0
sqlalchemy>=2.0.0
asyncpg>=0.29.0
redis[hiredis]>=4.6.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
alembic>=1.13.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
httpx>=0.27.0
""",
            ".gitignore": """__pycache__/
*.py[cod]
*.egg-info/
dist/
build/
.eggs/
.env
.venv/
venv/
*.db
.coverage
htmlcov/
.pytest_cache/
.ruff_cache/
""",
        },
        "dependencies": [
            {"name": "fastapi", "version": "^0.109.0"},
            {"name": "uvicorn", "version": "^0.27.0"},
            {"name": "pydantic", "version": "^2.6.0"},
            {"name": "sqlalchemy", "version": "^2.0.0"},
            {"name": "python-jose", "version": "^3.3.0"},
        ],
        "dev_dependencies": [
            {"name": "pytest", "version": "^8.0.0"},
            {"name": "pytest-asyncio", "version": "^0.23.0"},
            {"name": "httpx", "version": "^0.27.0"},
            {"name": "ruff", "version": "^0.3.0"},
        ],
        "scripts": {
            "dev": "uvicorn app.main:app --reload --port 8000",
            "test": "pytest -v",
            "lint": "ruff check . && ruff format --check .",
            "format": "ruff format .",
            "migrate": "alembic upgrade head",
        },
    },
    TechStack.FLASK: {
        "description": "Flask轻量级Web框架，支持Blueprint和Jinja2模板",
        "structure": {
            "app/": {"__init__.py": "", "factory.py": "",
                    "routes/": {"__init__.py": "", "home.py": "", "api.py": ""},
                    "models/": {"__init__.py": "", "user.py": ""},
                    "templates/": {"base.html": "", "index.html": ""},
                    "static/": {"css/": {}, "js/": {}}},
            "tests/": {"__init__.py": "", "conftest.py": "", "test_routes.py": ""},
            "migrations/": {},
        },
        "key_files": {
            "app/__init__.py": '''"""Flask Application Factory"""
from flask import Flask
from app.routes.home import home_bp
from app.routes.api import api_bp

def create_app(config_name="development"):
    app = Flask("{{project_name}}")
    app.config.from_object(f"app.config.{config_name}Config")

    app.register_blueprint(home_bp)
    app.register_blueprint(api_bp, url_prefix="/api/v1")

    return app
''',
            "app/factory.py": '''"""应用工厂模式实现"""
def create_app():
    from app.__init__ import create_app as _create
    return _create()
''',
            "requirements.txt": """Flask>=3.0.0
SQLAlchemy>=3.0.0
Flask-SQLAlchemy>=3.1.0
Flask-Migrate>=4.0.0
Flask-JWT-Extended>=4.6.0
gunicorn>=21.2.0
pytest>=8.0.0
""",
            ".gitignore": "__pycache__/\n*.pyc\ninstance/\n.env\n.venv/\n",
        },
        "dependencies": [{"name": "Flask", "version": "^3.0.0"}],
        "dev_dependencies": [{"name": "pytest", "version": "^8.0.0"}],
        "scripts": {"run": "flask run --debug", "test": "pytest"},
    },
    TechStack.DJANGO: {
        "description": "Django全栈框架，MTV架构，含apps/settings/urls",
        "structure": {
            "{{project_name}}/": {
                "__init__.py": "", "asgi.py": "", "wsgi.py": "", "settings.py": "", "urls.py": "",
                "apps/": {
                    "users/": {"models.py": "", "views.py": "", "urls.py": "", "admin.py": "",
                              "tests.py": "", "apps.py": "", "migrations/": {}},
                    "core/": {"models.py": "", "views.py": "", "urls.py": "", "apps.py": "", "migrations/": {}}},
                "templates/": {"base.html": ""},
                "static/": {"css/": {}, "js/": {}}},
            "manage.py": "",
            "requirements.txt": "",
        },
        "key_files": {
            "manage.py": '''#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{{project_name}}.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(...) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
''',
            "{{project_name}}/settings.py": '''"""Django settings for {{project_name}}"""
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-change-me'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    '{{project_name}}.apps.users',
    '{{project_name}}.apps.core',
]

MIDDLEWARE = [...]

DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql', ...}}

ROOT_URLCONF = '{{project_name}}.urls'

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
''',
            "requirements.txt": """Django>=5.0.0
djangorestframework>=3.14.0
psycopg2-binary>=2.9.9
celery>=5.3.0
redis>=5.0.0
gunicorn>=21.2.0
pytest-django>=4.7.0
""",
            ".gitignore": "*.pyc\n__pycache__/\nlocal_settings.py\ndb.sqlite3\nmedia/\n.static_storage/\n",
        },
        "dependencies": [{"name": "Django", "version": "^5.0.0"}, {"name": "djangorestframework", "version": "^3.14.0"}],
        "dev_dependencies": [{"name": "pytest-django", "version": "^4.7.0"}],
        "scripts": {"run": "python manage.py runserver", "migrate": "python manage.py migrate", "test": "pytest"},
    },
    TechStack.REACT_VITE: {
        "description": "React + Vite + TypeScript 现代前端工程",
        "structure": {
            "src/": {
                "App.tsx": "", "main.tsx": "",
                "components/": {"Button.tsx": "", "Header.tsx": ""},
                "pages/": {"Home.tsx": "", "About.tsx": ""},
                "hooks/": {"useAuth.ts": "", "useApi.ts": ""},
                "services/": {"api.ts": ""},
                "store/": {"index.ts": ""},
                "types/": {"index.ts": ""},
                "styles/": {"globals.css": ""},
                "assets/": {},
            },
            "public/": {},
            "tests/": {},
        },
        "key_files": {
            "package.json": '{"name":"{{project_name}}","private":true,"version":"{{version}}","type":"module",'
                            '"scripts":{"dev":"vite","build":"tsc -b && vite build","preview":"vite preview","test":"vitest"},'
                            '"dependencies":{"react":"^18.2.0","react-dom":"^18.2.0"},"devDependencies":{"@types/react":"^18.2.0",'
                            '@vitejs/plugin-react":"^4.2.0","typescript":"^5.3.0","vite":"^5.1.0","vitest":"^1.2.0"}}',
            "tsconfig.json": '{"compilerOptions":{"target":"ES2020","useDefineForClassFields":true,"lib":["ES2020","DOM","DOM.Iterable"],'
                             '"module":"ESNext","skipLibCheck":true,"moduleResolution":"bundler","allowImportingTsExtensions":true,'
                             '"resolveJsonModule":true,"isolatedModules":true,"noEmit":true,"jsx":"react-jsx","strict":true,'
                             '"noUnusedLocals":true,"noUnusedParameters":true,"noFallthroughCasesInSwitch":true},'
                             '"include":["src"],"references":[{"path":"./tsconfig.node.json"}]}',
            "vite.config.ts": '''import { defineConfig } from "vite"
import react from "@vitejs/plugin-react"

export default defineConfig({
  plugins: [react()],
  server: { port: 3000, open: true },
  build: { outDir: "dist", sourcemap: true },
})
''',
            ".gitignore": "node_modules/\ndist/\n.env\n.DS_Store\n*.log\n",
        },
        "dependencies": [{"name": "react", "version": "^18.2.0"}, {"name": "react-dom", "version": "^18.2.0"}],
        "dev_dependencies": [{"name": "typescript", "version": "^5.3.0"}, {"name": "vite", "version": "^5.1.0"}],
        "scripts": {"dev": "vite", "build": "tsc -b && vite build", "preview": "vite preview", "test": "vitest"},
    },
    TechStack.VUE3_NUXT: {
        "description": "Vue3 Composition API + Nuxt3 全栈框架",
        "structure": {
            "app/": {"app.vue": "", "error.vue": "", "page.vue": ""},
            "pages/": {"index.vue": "", "about.vue": ""},
            "components/": {"Header.vue": "", "Footer.vue": ""},
            "composables/": {"useAuth.ts": ""},
            "server/api/": {"hello.ts": ""},
            "layouts/": {"default.vue": ""},
            "assets/": {"css/": {}},
            "public/": {},
        },
        "key_files": {
            "nuxt.config.ts": '''export default defineNuxtConfig({
  devtools: { enabled: true },
  modules: ['@nuxt/ui'],
  runtimeConfig: { public: { apiBase: '/api' } },
})
''',
            "package.json": '{"name":"{{project_name}}","private":true,"scripts":{"dev":"nuxt dev","build":"nuxt build",'
                            '"generate":"nuxt generate","preview":"nuxt preview"},"dependencies":{"nuxt":"^3.10.0"}}',
            ".gitignore": "node_modules/\n.nuxt/\n.output/\n.env\n",
        },
        "dependencies": [{"name": "nuxt", "version": "^3.10.0"}],
        "dev_dependencies": [],
        "scripts": {"dev": "nuxt dev", "build": "nuxt build", "generate": "nuxt generate"},
    },
    TechStack.NEXTJS: {
        "description": "Next.js App Router + React Server Components",
        "structure": {
            "src/app/": {
                "layout.tsx": "", "page.tsx": "", "globals.css": "",
                "(auth)/": {"layout.tsx": "", "login/page.tsx": "", "register/page.tsx": ""},
                "api/": {"users/route.ts": "", "health/route.ts": ""},
                "about/page.tsx": "",
            },
            "src/components/": {"Navbar.tsx": "", "Footer.tsx": ""},
            "src/lib/": {"utils.ts": "", "api.ts": ""},
            "src/types/": {"index.ts": ""},
            "public/": {},
        },
        "key_files": {
            "next.config.ts": '''import type { NextConfig } from "next"

const nextConfig: NextConfig = {
  reactStrictMode: true,
  experimental: { serverActions: true },
}

export default nextConfig
''',
            "tsconfig.json": '{"compilerOptions":{"target":"es5","lib":["dom","dom.iterable","esnext"],'
                             '"allowJs":true,"skipLibCheck":true,"strict":true,"noEmit":true,"esModuleInterop":true,'
                             '"module":"esnext","moduleResolution":"bundler","resolveJsonModule":true,"isolatedModules":true,'
                             '"jsx":"preserve","incremental":true,"plugins":[{"name":"next"}],"paths":{"@/*":["./src/*"]}},'
                             '"include":["next-env.d.ts","**/*.ts","**/*.tsx"],"exclude":["node_modules"]}',
            "package.json": '{"name":"{{project_name}}","version":"{{version}}","private":true,"scripts":{'
                            '"dev":"next dev","build":"next build","start":"next start","lint":"next lint"},'
                            '"dependencies":{"next":"14.1.0","react":"^18.2.0","react-dom":"^18.2.0"}}',
            ".gitignore": "node_modules/\n.next/\nout/\n.env*\n",
        },
        "dependencies": [{"name": "next", "version": "14.1.0"}, {"name": "react", "version": "^18.2.0"}],
        "dev_dependencies": [],
        "scripts": {"dev": "next dev", "build": "next build", "start": "next start", "lint": "next lint"},
    },
    TechStack.NESTJS: {
        "description": "NestJS企业级Node.js框架，Modules/Guards/Interceptors",
        "structure": {
            "src/": {
                "main.ts": "", "app.module.ts": "",
                "common/": {"decorators/": "", "filters/": "", "interceptors/": ""},
                "users/": {"users.module.ts": "", "users.controller.ts": "", "users.service.ts": "",
                           "dto/": {"create-user.dto.ts": "", "update-user.dto.ts": ""},
                           "entities/": {"user.entity.ts": ""},
                           "users.controller.spec.ts": "", "users.service.spec.ts": ""},
                "auth/": {"auth.module.ts": "", "auth.controller.ts": "", "auth.service.ts":"",
                          "guards/jwt-auth.guard.ts": "", "strategies/jwt.strategy.ts": ""},
                "config/": {"configuration.ts": ""},
            },
            "test/": {"app.e2e-spec.ts": ""},
        },
        "key_files": {
            "nest-cli.json": '{"$schema":"@nestjs/schematics","collection":"@nestjs/schematics","sourceRoot":"src",'
                               '"compilerOptions":{"deleteOutDir":true}}',
            "package.json": '{"name":"{{project_name}}","version":"{{version}}","description":"","scripts":{'
                            '"build":"nest build","start":"nest start","start:dev":"nest start --watch","start:debug":"nest start --debug --watch",'
                            '"start:prod":"node dist/main","lint":"eslint \\"{src,apps,libs,test}/**/*.ts\\" --fix",'
                            '"test":"jest","test:watch":"jest --watch","test:cov":"jest --coverage","test:e2e":"jest --config ./test/jest-e2e.json"},'
                            '"dependencies":{"@nestjs/common":"^10.3.0","@nestjs/core":"^10.3.0","@nestjs/platform-express":"^10.3.0",'
                            '"@nestjs/typeorm":"^10.0.0","reflect-metadata":"^0.2.1","rxjs":"^7.8.0"},'
                            '"devDependencies":{"@nestjs/cli":"^10.3.0","@nestjs/schematics":"^10.0.0","@nestjs/testing":"^10.3.0",'
                            '"@types/express":"^4.17.17","@types/jest":"^29.5.12","@types/node":"^20.11.0","typescript":"^5.3.0",'
                            '"jest":"^29.7.0","ts-jest":"^29.1.0","eslint":"^8.56.0"}}',
            "tsconfig.json": '{"compilerOptions":{"module":"commonjs","declaration":true,"removeComments":true,'
                             '"emitDecoratorMetadata":true,"experimentalDecorators":true,"allowSyntheticDefaultImports":true,'
                             '"target":"ES2021","sourceMap":true,"outDir":"./dist","baseUrl":"./","incremental":true,"skipLibCheck":true,'
                             '"strictNullChecks":false,"noImplicitAny":false,"strictBindCallApply":false,'
                             '"forceConsistentCasingInFileNames":false,"noFallthroughCasesInSwitch":false}}',
            ".gitignore": "node_modules/\ndist/\ncoverage/\n.env\n",
        },
        "dependencies": [{"name": "@nestjs/common", "version": "^10.3.0"}, {"name": "@nestjs/core", "version": "^10.3.0"}],
        "dev_dependencies": [{"name": "typescript", "version": "^5.3.0"}, {"name": "jest", "version": "^29.7.0"}],
        "scripts": {"build": "nest build", "start:dev": "nest start --watch", "test": "jest"},
    },
    TechStack.GIN: {
        "description": "Gin高性能Go Web框架，middleware模式",
        "structure": {
            "cmd/server/main.go": "",
            "internal/handler/": {"user.go": "", "health.go": ""},
            "internal/middleware/": {"auth.go": "", "logger.go": "", "cors.go": ""},
            "internal/model/": {"user.go": ""},
            "internal/service/": {"user_service.go": ""},
            "internal/repository/": {"user_repo.go": ""},
            "pkg/response/": {"response.go": ""},
            "configs/": {"config.yaml": ""},
            "docs/": {},
            "tests/": {"handler/user_test.go": ""},
        },
        "key_files": {
            "go.mod": """module {{project_name}}

go 1.21

require (
	github.com/gin-gonic/gin v1.9.1
	github.com/spf13/viper v1.18.2
	go.uber.org/zap v1.26.0
	golang.org/x/crypto v0.16.0
)
""",
            "cmd/server/main.go": """package main

import (
	"{{project_name}}/internal/handler"
	"{{project_name}}/internal/middleware"
	"log"
	"net/http"

	"github.com/gin-gonic/gin"
)

func main() {
	r := gin.New()
	r.Use(gin.Logger(), gin.Recovery())
	r.Use(middleware.CORS())

	api := r.Group("/api/v1")
	{
		api.GET("/health", handler.HealthCheck)
		users := api.Group("/users")
		{
			users.GET("", handler.ListUsers)
			users.POST("", handler.CreateUser)
			users.GET("/:id", handler.GetUser)
		}
	}

	log.Println("Server starting on :8080")
	r.Run(":8080")
}
""",
            ".gitignore": "*.exe\n*.exe~\n*.dll\n*.so\n*.dylib\n*.test\n*.out\nvendor/\n\n# IDE\n.idea/\n.vscode/\n",
        },
        "dependencies": [{"name": "github.com/gin-gonic/gin", "version": "v1.9.1"}],
        "dev_dependencies": [],
        "scripts": {"build": "go build -o bin/server ./cmd/server", "run": "go run cmd/server/main.go", "test": "go test ./..."},
    },
    TechStack.ECHO: {
        "description": "Echo轻量级Go Web框架，handler groups",
        "structure": {
            "cmd/server/main.go": "",
            "handler/": {"user.go": "", "health.go": ""},
            "middleware/": {"auth.go": ""},
            "model/": {"user.go": ""},
            "config/": {"config.go": ""},
        },
        "key_files": {
            "cmd/server/main.go": """package main

import (
	"{{project_name}}/handler"
	"{{project_name}}/middleware"

	"github.com/labstack/echo/v4"
	"github.com/labstack/echo/v4/middleware"
)

func main() {
	e := echo.New()
	e.Use(middleware.Logger())
	e.Use(middleware.Recover())
	e.Use(middleware.CORS())

	api := e.Group("/api/v1")
	{
		api.GET("/health", handler.HealthCheck)
		users := api.Group("/users", middleware.JWTAuth())
		{
			users.GET("", handler.ListUsers)
			users.POST("", handler.CreateUser)
		}
	}

	e.Logger.Fatal(e.Start(":8080"))
}
""",
            "go.mod": f"""module {{project_name}}

go 1.21

require github.com/labstack/echo/v4 v4.11.4
""",
            ".gitignore": "*.exe\n*.test\nvendor/\n",
        },
        "dependencies": [{"name": "github.com/labstack/echo/v4", "version": "v4.11.4"}],
        "dev_dependencies": [],
        "scripts": {"run": "go run cmd/server/main.go", "test": "go test ./..."},
    },
    TechStack.FIBER: {
        "description": "Fiber超高速Go Web框架（基于fasthttp）",
        "structure": {
            "cmd/main.go": "",
            "handler/": {"user.go": "", "health.go": ""},
            "model/": {"user.go": ""},
        },
        "key_files": {
            "cmd/main.go": """package main

import (
	"{{project_name}}/handler"
	"log"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/logger"
)

func main() {
	app := fiber.New(fiber.Config{})
	app.Use(logger.New())
	app.Use(cors.New())

	api := app.Group("/api/v1")
	api.Get("/health", handler.HealthCheck)
	users := api.Group("/users")
	users.Get("", handler.ListUsers)
	users.Post("", handler.CreateUser)

	log.Println("Server on :3000")
	app.Listen(":3000")
}
""",
            "go.mod": f"""module {{project_name}}

go 1.21

require github.com/gofiber/fiber/v2 v2.52.0
""",
            ".gitignore": "*.exe\n*.test\n",
        },
        "dependencies": [{"name": "github.com/gofiber/fiber/v2", "version": "v2.52.0"}],
        "dev_dependencies": [],
        "scripts": {"run": "go run cmd/main.go", "test": "go test ./..."},
    },
    TechStack.ACTIX_WEB: {
        "description": "Actix-web Rust Web框架，extractors/responders",
        "structure": {
            "src/main.rs": "",
            "src/handlers/mod.rs": "", "src/handlers/user.rs": "", "src/handlers/health.rs": "",
            "src/models/mod.rs": "", "src/models/user.rs": "",
            "src/config/mod.rs": "",
            "src/errors/mod.rs": "",
            "tests/integration_tests.rs": "",
        },
        "key_files": {
            "Cargo.toml": """[package]
name = "{{project_name}}"
version = "{{version}}"
edition = "2021"

[dependencies]
actix-web = "4"
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tokio = { version = "1", features = ["full"] }
tracing = "0.1"
tracing-subscriber = "0.3"
uuid = { version = "1", features = ["v4"] }
""",

            "src/main.rs": """mod handlers;
mod models;
mod config;
mod errors;

use actix_web::{web::Data, App, HttpServer};
use handlers::health;
use handlers::user;

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    tracing_subscriber::fmt::init();

    println!("🚀 {{project_name}} server starting on :8080");

    HttpServer::new(|| {
        App::new()
            .route("/health", web::get().to(health::check))
            .service(
                web::scope("/api/v1")
                    .service(user::list_users)
                    .service(user::create_user)
                    .service(user::get_user)
            )
    })
    .bind(("127.0.0.1", 8080))?
    .run()
    .await
}
""",
            ".gitignore": "/target\n**/*.rs.bk\n",
        },
        "dependencies": [{"name": "actix-web", "version": "4"}],
        "dev_dependencies": [],
        "scripts": {"run": "cargo run", "build": "cargo build --release", "test": "cargo test"},
    },
    TechStack.AXUM: {
        "description": "Axum现代Rust Web框架，routing+extract",
        "structure": {
            "src/main.rs": "",
            "src/routes/mod.rs": "", "src/routes/user.rs": "",
            "src/handlers/mod.rs": "", "src/handlers/user.rs": "",
            "src/state/mod.rs": "",
            "src/error.rs": "",
        },
        "key_files": {
            "Cargo.toml": """[package]
name = "{{project_name}}"
version = "{{version}}"
edition = "2021"

[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tower-http = { version = "0.5", features = ["cors", "trace"] }
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
""",

            "src/main.rs": """mod routes;
mod handlers;
mod state;
mod error;

use axum::{
    routing::get,
    Router,
};

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let app = Router::new()
        .route("/health", get(handlers::health))
        .nest("/api/v1", routes::user_routes());

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await.unwrap();
    println!("🚀 {{project_name}} running on http://localhost:3000");
    axum::serve(listener, app).await.unwrap();
}
""",
            ".gitignore": "/target\n**/*.rs.bk\n",
        },
        "dependencies": [{"name": "axum", "version": "0.7"}],
        "dev_dependencies": [],
        "scripts": {"run": "cargo run", "test": "cargo test"},
    },
    TechStack.REACT_NATIVE: {
        "description": "React Native跨平台移动端开发",
        "structure": {
            "src/": {
                "App.tsx": "",
                "navigation/": {"AppNavigator.tsx": "", "AuthNavigator.tsx": ""},
                "screens/": {"HomeScreen.tsx": "", "LoginScreen.tsx": "", "ProfileScreen.tsx": ""},
                "components/": {"Button.tsx": "", "Input.tsx": ""},
                "services/": {"api.ts": "", "auth.ts": ""},
                "store/": {"index.ts": ""},
                "hooks/": {"useAuth.ts": ""},
                "types/": {"index.ts": ""},
                "assets/": {},
                "theme/": {"colors.ts": "", "spacing.ts": ""},
            },
            "__tests__/": {},
            "android/": {},
            "ios/": {},
        },
        "key_files": {
            "package.json": '{"name":"{{project_name}}","version":"{{version}}","private":true,"scripts":{'
                            '"android":"react-native run-android","ios":"react-native run-ios","start":"react-native start",'
                            '"test":"jest","lint":"eslint ."},"dependencies":{"react":"18.2.0","react-native":"0.73.0",'
                            '"@react-navigation/native":"^6.9.0","@react-navigation/native-stack":"^9.9.0",'
                            '"@reduxjs/toolkit":"^2.0.0","react-redux":"^9.0.0"},'
                            '"devDependencies":{"@testing-library/react-native":"^12.4.0","typescript":"^5.3.0"}}',
            "tsconfig.json": '{"compilerOptions":{"target":"esnext","module":"commonjs","lib":["es2021"],"jsx":"react-native",'
                             '"strict":true,"resolveJsonModule":true,"esModuleInterop":true},"include":["src"]}',
            ".gitignore": "node_modules/\n.android/\n.ios/\nlib/\n*.jks\n*.p8\n",
        },
        "dependencies": [{"name": "react-native", "version": "0.73.0"}],
        "dev_dependencies": [{"name": "typescript", "version": "^5.3.0"}],
        "scripts": {"start": "react-native start", "android": "react-native run-android", "ios": "react-native run-ios"},
    },
    TechStack.FLUTTER: {
        "description": "Flutter跨平台UI框架，BLoC状态管理模式",
        "structure": {
            "lib/": {
                "main.dart": "",
                "app.dart": "",
                "core/theme/": {"app_theme.dart": "", "colors.dart": ""},
                "features/auth/": {"data/": {"repositories/": "", "datasources/": ""},
                                   "domain/entities/": {"user.dart": ""},
                                   "presentation/bloc/": {"auth_bloc.dart": "", "auth_event.dart": "", "auth_state.dart": ""},
                                   "presentation/pages/": {"login_page.dart": "", "register_page.dart": ""}},
                "features/home/": {"presentation/pages/": {"home_page.dart": ""}},
                "shared/widgets/": {"custom_button.dart": "", "loading_indicator.dart": ""},
            },
            "test/": {},
        },
        "key_files": {
            "pubspec.yaml": """name: {{project_name}}
description: {{project_description}}
version: {{version}}

environment:
  sdk: '>=3.2.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  flutter_bloc: ^8.1.3
  equatable: ^2.0.5
  go_router: ^13.0.0
  dio: ^5.4.0
  shared_preferences: ^2.2.2
  intl: ^0.19.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
  mocktail: ^1.0.1
  build_runner: ^2.4.7

flutter:
  uses-material-design: true
""",
            "lib/main.dart": """import 'package:flutter/material.dart';
import 'app.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const MyApp());
}
""",
            ".gitignore": "\n# Misc\n.DS_Store\n.env\n# Flutter\nflutter_build/\n.packages\n.pub-cache/\n.pub/",
        },
        "dependencies": [{"name": "flutter", "version": "sdk"}, {"name": "flutter_bloc", "version": "^8.1.3"}],
        "dev_dependencies": [{"name": "flutter_lints", "version": "^3.0.0"}],
        "scripts": {"run": "flutter run", "build": "flutter build apk", "test": "flutter test"},
    },
    TechStack.SWIFTUI: {
        "description": "SwiftUI原生iOS/macOS开发，MVVM架构",
        "structure": {
            "{{project_name}}/": {
                "App.swift": "",
                "Views/": {"ContentView.swift": "", "LoginView.swift": "", "ProfileView.swift": ""},
                "ViewModels/": {"AuthViewModel.swift": "", "ProfileViewModel.swift": ""},
                "Models/": {"User.swift": "", "ApiResponse.swift": ""},
                "Services/": {"APIService.swift": "", "AuthService.swift": ""},
                "Utils/": {"Constants.swift": "", "Extensions.swift": ""},
                "Resources/": {"Assets.xcassets/": {}},
            },
            "{{project_name}}Tests/": {},
        },
        "key_files": {
            "Package.swift": "// swift-tools-version: 5.9\n"
                         "import PackageDescription\n\nlet package = Package(\n"
                         '    name: "{{project_name}}",\n'
                         "    platforms: [.iOS(.v15), .macOS(.v12)],\n"
                         "    products: [\n"
                         '        .executable(name: "{{project_name}}", targets: ["{{project_name}}"]),\n'
                         "    ],\n"
                         "    dependencies: [\n"
                         '        .package(url: "https://github.com/Alamofire/Alamofire.git", from: "5.8.0"),\n'
                         '        .package(url: "https://github.com/pointfreeco/swift-composable-architecture.git", from: "1.10.0"),\n'
                         "    ],\n"
                         '    targets: [\n        .executableTarget(name: "{{project_name}}")]\n)\n',
            "{{project_name}}/App.swift": """import SwiftUI

@main
struct {{project_class_name}}App: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
""",
            ".gitignore": ".build/\n.swiftpm/\nxcodeuserdata/\nDerivedData/\n",
        },
        "dependencies": [{"name": "Alamofire", "version": "5.8.0"}],
        "dev_dependencies": [],
        "scripts": {"build": "swift build", "run": "swift run", "test": "swift test"},
    },
}


_CONFIG_TEMPLATES: list[ConfigTemplate] = [
    ConfigTemplate(filename="Dockerfile", category="containerization", language="universal",
                   content="""FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runner
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --from=builder /app ./ 
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""),
    ConfigTemplate(filename=".dockerignore", category="containerization", language="universal",
                   content="""__pycache__
*.pyc
*.pyo
.env
.venv
venv
.git
.gitignore
*.md
!.env.example
tests
coverage
htmlcov
.pytest_cache
.ruff_cache
.mypy_cache
"""),
    ConfigTemplate(filename=".gitignore", category="version-control", language="universal",
                   content="""__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST
.env
.venv
venv/
ENV/
env.bak/
venv.bak
.spellchecker
node_modules/
*.db
*.sqlite3
.DS_Store
Thumbs.db
*.log
coverage/
htmlcov/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.idea/
.vscode/
*.swp
*.swo
*~
"""),
    ConfigTemplate(filename=".editorconfig", category="editor", language="universal",
                   content="""root = true

[*]
charset = utf-8
end_of_line = lf
indent_style = space
indent_size = 4
insert_final_newline = true
trim_trailing_whitespace = true

[*.{yml,yaml}]
indent_size = 2

[*.{json,cjs,mjs}]
indent_size = 2

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab
"""),
    ConfigTemplate(filename=".prettierrc", category="formatter", language="javascript",
                   content='{"semi": true, "singleQuote": true, "tabWidth": 2, "trailingComma": "all", '
                   '"printWidth": 100, "bracketSpacing": true, "arrowParens": "always"}'),
    ConfigTemplate(filename=".eslintrc.cjs", category="linter", language="javascript",
                   content="""module.exports = {
  env: { browser: true, es2021: true, node: true },
  extends: ["eslint:recommended", "plugin:@typescript-eslint/recommended"],
  parser: "@typescript-eslint/parser",
  parserOptions: { ecmaVersion: "latest", sourceType: "module" },
  rules: { "no-unused-vars": "warn", "no-console": "off", "@typescript-eslint/no-explicit-any": "warn" },
}
"""),
    ConfigTemplate(filename="pyproject.toml", category="python", language="python",
                   content="""[project]
name = "{{project_name}}"
version = "{{version}}"
description = "{{project_description}}"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8.0", "ruff>=0.3.0", "mypy>=1.8"]

[tool.ruff]
line-length = 120
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]
ignore = ["E501"]

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
"""),
]


class TemplateManagementSi:
    """
    模板管理司 - 礼部·主客司

    提供全面的项目脚手架和模板管理能力：
    - 项目脚手架生成器（Python/JS/TS/Go/Rust/Mobile多技术栈）
    - 代码骨架生成（根据架构设计生成目录结构和占位文件）
    - 通用配置文件模板（Dockerfile/.dockerignore/.gitignore/.editorconfig等）
    - 模板变量替换系统（{{project_name}}/{{author}}/{{year}}等变量自动填充）
    """

    _INSTANCE: TemplateManagementSi | None = None

    def __init__(self) -> None:
        self._scaffolds: dict[str, ProjectScaffold] = {}
        self._skeletons: dict[str, CodeSkeleton] = {}
        self._config_templates: dict[str, ConfigTemplate] = {}
        self._template_variables: dict[str, TemplateVariable] = {}
        self._results: list[ScaffoldResult] = []
        for ct in _CONFIG_TEMPLATES:
            self._config_templates[ct.filename] = ct

    @classmethod
    def get_instance(cls) -> TemplateManagementSi:
        """获取单例实例"""
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    # ==================== 项目脚手架 ====================

    def generate_scaffold(
        self,
        tech_stack: TechStack,
        project_name: str = "my-project",
        **variables: Any,
    ) -> ScaffoldResult:
        """
        生成项目脚手架

        Args:
            tech_stack: 目标技术栈
            project_name: 项目名称
            **variables: 模板变量（author, year, description等）

        Returns:
            ScaffoldResult对象
        """
        import time
        start_time = time.perf_counter()

        template_data = _SCAFFOLD_TEMPLATES.get(tech_stack)
        if template_data is None:
            raise ScaffoldError(f"不支持的技术栈: {tech_stack.value}")

        defaults: dict[str, str] = {
            "project_name": project_name,
            "project_description": variables.get("description", f"A {tech_stack.value} application"),
            "version": variables.get("version", "0.1.0"),
            "author": variables.get("author", "Developer"),
            "year": variables.get("year", __import__("datetime").date.today().strftime("%Y")),
            "email": variables.get("email", "dev@example.com"),
            "license": variables.get("license", "MIT"),
            "project_class_name": "".join(word.capitalize() for word in project_name.replace("-", "_").replace(".", "_").split("_")),
        }

        all_vars = {**defaults, **{k: str(v) for k, v in variables.items()}}

        structure = template_data["structure"]
        key_files = template_data.get("key_files", {})
        generated_files: list[str] = []
        total_files = 0
        total_dirs = 0

        flat_structure: list[tuple[str, str | None]] = []
        self._flatten_structure(structure, all_vars, "", flat_structure)

        for rel_path, content in flat_structure:
            if content is not None:
                rendered_content = self._replace_variables(content, all_vars)
                generated_files.append(rel_path)
                total_files += 1
            else:
                total_dirs += 1

        for filepath, raw_content in key_files.items():
            resolved_path = filepath.replace("{{project_name}}", project_name)
            rendered = self._replace_variables(raw_content, all_vars)
            generated_files.append(resolved_path)
            total_files += 1

        elapsed = (time.perf_counter() - start_time) * 1000

        scaffold = ProjectScaffold(
            name=project_name,
            tech_stack=tech_stack,
            directory_structure=structure,
            files={f: self._replace_variables(c, all_vars) for f, c in key_files.items()},
            dependencies=template_data.get("dependencies", []),
            dev_dependencies=template_data.get("dev_dependencies", []),
            scripts=template_data.get("scripts", {}),
            description=template_data.get("description", ""),
        )

        result = ScaffoldResult(
            project_name=project_name,
            tech_stack=tech_stack,
            total_files=total_files,
            total_dirs=total_dirs,
            generated_files=generated_files,
            generation_time_ms=elapsed,
        )

        key = f"{tech_stack.value}_{project_name}"
        self._scaffolds[key] = scaffold
        self._results.append(result)
        return result

    def _flatten_structure(
        self,
        structure: dict[str, Any],
        variables: dict[str, str],
        prefix: str,
        output: list[tuple[str, str | None]],
    ) -> None:
        """递归展平目录结构"""
        for name, value in sorted(structure.items()):
            resolved_name = self._replace_variables(name, variables)
            full_path = f"{prefix}/{resolved_name}" if prefix else resolved_name

            if isinstance(value, dict):
                output.append((full_path, None))
                self._flatten_structure(value, variables, full_path, output)
            elif isinstance(value, str):
                output.append((full_path, value))
            elif value is None:
                output.append((full_path, None))

    # ==================== 代码骨架 ====================

    def generate_code_skeleton(
        self,
        name: str,
        language: str,
        architecture: str = "layered",
        modules: list[str] | None = None,
    ) -> CodeSkeleton:
        """
        生成代码骨架

        Args:
            name: 项目/模块名称
            language: 编程语言
            architecture: 架构模式 (layered/clean/hexagonal/event-driven)
            modules: 子模块列表

        Returns:
            CodeSkeleton对象
        """
        mods = modules or ["core", "user", "order", "notification"]
        files: list[tuple[str, str]] = []
        imports: list[str] = []
        base_classes: list[str] = []
        interfaces: list[str] = []

        match architecture:
            case "layered":
                for mod in mods:
                    mod_lower = mod.lower().replace(" ", "_")
                    files.extend([
                        (f"{mod_lower}/entities/{mod}.py",
                         f'"""{mod} entity model"""\nclass {mod}:\n    id: int\n'),
                        (f"{mod_lower}/repositories/{mod}_repository.py",
                         f'"""{mod} data repository"""\nclass {mod}Repository:\n    async def find_by_id(self, id: int): ...\n'),
                        (f"{mod_lower}/services/{mod}_service.py",
                         f'"""{mod} business service"""\nclass {mod}Service:\n    def __init__(self, repo: "{mod}Repository"): ...\n'),
                        (f"{mod_lower}/controllers/{mod}_controller.py",
                         f'"""{mod} REST controller""}\nclass {mod}Controller:\n    def __init__(self, service: "{mod}Service"): ...\n'),
                    ])
                    interfaces.append(f"I{mod}Repository")
                    base_classes.append(f"Base{mod}")
            case "clean":
                files.extend([
                    ("domain/entities/base_entity.py", "# Base entity with ID and timestamps"),
                    ("domain/repositories/i_repository.py", "# Generic repository interface"),
                    ("application/use_cases/create_{name}.py", f"# Create{name.title()} use case"),
                    ("application/dto/{name}_dto.py", f"# {name.title()} DTO definitions"),
                    ("infrastructure/persistence/sqlalchemy_repo.py", "# SQLAlchemy repository implementation"),
                    ("infrastructure/external_api/client.py", "# External API client adapter"),
                    ("interfaces/rest/{name}_controller.py", f"# REST controller for {name}"),
                ])
                interfaces = ["IRepository", "IUseCase"]
                base_classes = ["BaseEntity"]
            case "hexagonal":
                files.extend([
                    ("domain/model.py", f"# {name.title()} domain model"),
                    ("domain/port/input_port.py", "# Input port interface"),
                    ("domain/port/output_port.py", "# Output port interface"),
                    ("application/service.py", f"# {name.title()} application service"),
                    ("adapter/in/rest_controller.py", "# REST input adapter"),
                    ("adapter/out/persistence.py", "# Persistence output adapter"),
                    ("adapter/out/messaging.py", "# Messaging output adapter"),
                ])
                interfaces = ["InputPort", "OutputPort"]
                base_classes = [f"{name.title()}Model"]
            case "event-driven":
                for mod in mods:
                    mod_lower = mod.lower()
                    files.extend([
                        (f"{mod_lower}/events/{mod}_created.py", f"# {mod}Created event definition"),
                        (f"{mod_lower}/handlers/{mod}_handler.py", f"# Event handler for {mod} events"),
                        (f"{mod_lower}/producers/{mod}_producer.py", f"# Event producer for {mod}"),
                        (f"{mod_lower}/consumers/{mod}_consumer.py", f"# Event consumer for {mod}"),
                    ])
                interfaces = ["EventHandler", "EventProducer"]
                base_classes = ["BaseEvent"]

        skeleton = CodeSkeleton(
            name=name,
            language=language,
            architecture_pattern=architecture,
            files=files,
            imports=imports,
            base_classes=base_classes,
            interfaces=interfaces,
        )
        self._skeletons[f"{language}_{architecture}_{name}"] = skeleton
        return skeleton

    # ==================== 配置文件模板 ====================

    def get_config_template(self, filename: str) -> ConfigTemplate | None:
        """
        获取配置文件模板

        Args:
            filename: 配置文件名

        Returns:
            ConfigTemplate对象或None
        """
        return self._config_templates.get(filename)

    def list_config_templates(self, category: str | None = None) -> list[ConfigTemplate]:
        """
        列出配置文件模板

        Args:
            category: 可选的分类过滤

        Returns:
            匹配的模板列表
        """
        templates = list(self._config_templates.values())
        if category:
            templates = [t for t in templates if t.category == category]
        return sorted(templates, key=lambda t: t.filename)

    def render_config_template(
        self,
        filename: str,
        variables: dict[str, str] | None = None,
    ) -> str:
        """
        渲染配置文件模板并替换变量

        Args:
            filename: 配置文件名
            variables: 变量字典

        Returns:
            渲染后的内容

        Raises:
            TemplateError: 当模板不存在时
        """
        template = self._config_templates.get(filename)
        if template is None:
            raise TemplateError(f"配置模板不存在: {filename}")

        vars_to_use = variables or {}
        return self._replace_variables(template.content, vars_to_use)

    # ==================== 变量替换系统 ====================

    def register_variable(
        self,
        name: str,
        default_value: str = "",
        description: str = "",
        variable_type: str = "string",
        required: bool = False,
    ) -> TemplateVariable:
        """
        注册模板变量

        Args:
            name: 变量名
            default_value: 默认值
            description: 描述
            variable_type: 类型
            required: 是否必填

        Returns:
            TemplateVariable对象
        """
        var = TemplateVariable(
            name=name,
            default_value=default_value,
            description=description,
            variable_type=variable_type,
            required=required,
        )
        self._template_variables[name] = var
        return var

    def replace_in_text(
        self,
        text: str,
        variables: dict[str, str],
    ) -> str:
        """
        在文本中执行变量替换

        Args:
            text: 原始文本
            variables: 变量字典

        Returns:
            替换后的文本
        """
        merged = {**{v.name: v.default_value for v in self._template_variables.values()}, **variables}
        return self._replace_variables(text, merged)

    @staticmethod
    def _replace_variables(text: str, variables: dict[str, str]) -> str:
        """执行{{variable}}格式的变量替换"""
        result = text
        for var_name, var_value in variables.items():
            placeholder = "{{" + var_name + "}}"
            result = result.replace(placeholder, var_value)
        return result

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成完整的模板管理报告(Markdown)"""
        lines: list[str] = []
        lines.append("# 🏗️ 模板管理司 · 综合报告\n")

        lines.append("## 📦 项目脚手架\n")
        lines.append(f"| 项目 | 技术栈 | 文件数 | 目录数 | 耗时(ms) |")
        lines.append(f"| --- | --- | --- | --- | --- |")
        for result in self._results:
            lines.append(
                f"`{result.project_name}` | `{result.tech_stack.value}` "
                f"| {result.total_files} | {result.total_dirs} | {result.generation_time_ms:.1f} |"
            )

        lines.append(f"\n## 📋 代码骨架\n")
        lines.append(f"- 总骨架数: {len(self._skeletons)}")
        for skey, skeleton in self._skeletons.items():
            lines.append(f"  - **{skey}**: {skeleton.architecture_pattern}, "
                          f"{len(skeleton.files)}个文件, 接口: {skeleton.interfaces}")

        lines.append(f"\n## ⚙️ 配置文件模板\n")
        lines.append(f"- 总模板数: {len(self._config_templates)}")
        categories: dict[str, int] = {}
        for t in self._config_templates.values():
            categories[t.category] = categories.get(t.category, 0) + 1
        for cat, count in sorted(categories.items()):
            lines.append(f"  - **{cat}**: {count} 个模板")

        lines.append(f"\n## 🔧 模板变量\n")
        lines.append(f"- 注册变量数: {len(self._template_variables)}")
        for var in self._template_variables.values():
            req = "✅ 必填" if var.required else "⚪ 可选"
            lines.append(f"  - `{{{var.name}}}` ({var.variable_type}): {var.description} [{req}]")

        supported_stacks = [ts.value for ts in TechStack]
        lines.append(f"\n## 🛠️ 支持的技术栈 ({len(TechStack)})\n")
        for i in range(0, len(supported_stacks), 4):
            chunk = supported_stacks[i:i + 4]
            lines.append(" | ".join(f"`{s}`" for s in chunk))

        lines.append("\n---\n")
        lines.append("*此报告由尚书省·礼部·模板管理司自动生成*\n")
        return "\n".join(lines)

    @property
    def scaffold_count(self) -> int:
        return len(self._scaffolds)

    @property
    def skeleton_count(self) -> int:
        return len(self._skeletons)

    @property
    def config_template_count(self) -> int:
        return len(self._config_templates)

    @property
    def supported_stacks(self) -> list[str]:
        return [ts.value for ts in TechStack]

    def __repr__(self) -> str:
        return (
            f"TemplateManagementSi(scaffolds={self.scaffold_count}, "
            f"skeletons={self.skeleton_count}, "
            f"configs={self.config_template_count})"
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 模板管理司测试")
    print("=" * 60)

    si = TemplateManagementSi()

    print("\n--- 项目脚手架生成 ---")
    stacks_to_test = [
        (TechStack.FASTAPI, "fastapi-demo"),
        (TechStack.REACT_VITE, "react-vite-app"),
        (TechStack.GIN, "gin-api-server"),
        (TechStack.FLUTTER, "flutter-mobile"),
        (TechStack.NESTJS, "nestjs-backend"),
        (TechStack.AXUM, "axum-rust-api"),
    ]

    for stack, pname in stacks_to_test:
        try:
            result = si.generate_scaffold(stack, project_name=pname, author="DevTeam", version="1.0.0")
            print(f"   ✅ {stack.value:15s} → '{pname}': "
                  f"{result.total_files} 文件, {result.total_dirs} 目录, "
                  f"{result.generation_time_ms:.1f}ms")
        except Exception as e:
            print(f"   ❌ {stack.value}: {e}")

    print(f"\n   总共生成 {len(si._results)} 个脚手架")

    print("\n--- 代码骨架生成 ---")
    for arch in ["layered", "clean", "hexagonal", "event-driven"]:
        skeleton = si.generate_code_skeleton(name="ECommerce", language="python", architecture=arch)
        print(f"   ✅ [{arch:12s}] {skeleton.file_count} 个文件, "
              f"接口: {skeleton.interfaces}, 基类: {skeleton.base_classes}")

    print("\n--- 配置文件模板 ---")
    config_templates = si.list_config_templates()
    print(f"   共 {len(config_templates)} 个配置模板:")
    for ct in config_templates:
        print(f"      • {ct.filename} ({ct.category}/{ct.language}): {ct.description[:40]}")

    print("\n--- 渲染配置模板 ---")
    pyproject_rendered = si.render_config_template("pyproject.toml", variables={
        "project_name": "my-awesome-app",
        "version": "2.0.0",
        "project_description": "An awesome Python application",
    })
    print(f"   pyproject.toml 渲染结果 (前400字符):")
    for line in pyproject_rendered.split("\n")[:15]:
        print(f"      {line}")

    gitignore_rendered = si.render_config_template(".gitignore")
    print(f"\n   .gitignore 行数: {len(gitignore_rendered.splitlines())}")

    print("\n--- 变量替换系统 ---")
    si.register_variable("company", default_value="Acme Inc.", description="公司名称", required=True)
    si.register_variable("copyright_year", default_value="2024", description="版权年份")
    sample_text = """
# {{project_name}}
Copyright (c) {{copyright_year}} {{company}}. All rights reserved.
Author: {{author}}
License: {{license}}
"""
    replaced = si.replace_in_text(sample_text, {
        "project_name": "SuperProject",
        "author": "Alice Chen",
        "license": "MIT",
    })
    print("   替换前:")
    for line in sample_text.strip().split("\n"):
        print(f"      {line}")
    print("   替换后:")
    for line in replaced.strip().split("\n"):
        print(f"      {line}")

    print("\n--- 支持的技术栈 ---")
    for ts in TechStack:
        tmpl = _SCAFFOLD_TEMPLATES.get(ts)
        desc = tmpl["description"][:50] if tmpl else "无模板"
        deps_count = len(tmpl.get("dependencies", [])) if tmpl else 0
        print(f"   • {ts.value:18s}: {desc}... ({deps_count} 核心依赖)")

    print("\n--- 综合报告预览 (前1500字符) ---")
    report = si.generate_report()
    print(report[:1500])

    print("\n✅ 所有测试通过!")
