---
name: huanjing_jiance
description: 环境检测流程指导，包含服务检测、Docker管理、服务依赖检测等完整流程和最佳实践。
---
# 环境检测流程

## 概述

环境检测是确保系统各组件正常运行的关键步骤，包括数据库连接、缓存服务、API健康状态等检测。通过系统化的检测流程，可以快速定位问题并保证服务的稳定性。

## 服务检测流程

### 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     环境检测流程                              │
│                                                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐ │
│  │ 数据库   │   │  Redis   │   │ 后端API  │   │  前端    │ │
│  │ 检测     │ ─►│ 检测     │ ─►│ 检测     │ ─►│ 检测     │ │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘ │
│       │              │              │              │        │
│       ▼              ▼              ▼              ▼        │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                  检测结果汇总                        │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 数据库连接检测（PostgreSQL）

#### 检测步骤

1. 检查数据库服务是否运行
2. 验证连接配置（主机、端口、用户名、密码）
3. 执行简单查询验证连接有效性
4. 检查数据库版本兼容性

#### Python示例

```python
import psycopg2
from psycopg2 import OperationalError

def check_postgresql_connection(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str
) -> dict:
    """检测PostgreSQL数据库连接"""
    result = {
        "service": "PostgreSQL",
        "status": "unknown",
        "message": "",
        "details": {}
    }
    
    try:
        connection = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password,
            connect_timeout=5
        )
        
        cursor = connection.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        
        result["status"] = "healthy"
        result["message"] = "数据库连接成功"
        result["details"]["version"] = version
        
        cursor.close()
        connection.close()
        
    except OperationalError as e:
        result["status"] = "unhealthy"
        result["message"] = f"数据库连接失败: {str(e)}"
    
    return result
```

#### Shell脚本示例

```bash
#!/bin/bash

check_postgresql() {
    local host="${DB_HOST:-localhost}"
    local port="${DB_PORT:-5432}"
    local database="${DB_NAME:-app_db}"
    local user="${DB_USER:-postgres}"
    
    echo "检测PostgreSQL连接..."
    
    if pg_isready -h "$host" -p "$port" -U "$user" -d "$database"; then
        echo "✅ PostgreSQL连接正常"
        return 0
    else
        echo "❌ PostgreSQL连接失败"
        return 1
    fi
}
```

### Redis连接检测

#### 检测步骤

1. 检查Redis服务是否运行
2. 验证连接配置
3. 执行PING命令验证响应
4. 检查Redis内存使用情况

#### Python示例

```python
import redis
from redis.exceptions import RedisError

def check_redis_connection(
    host: str = "localhost",
    port: int = 6379,
    password: str = None,
    db: int = 0
) -> dict:
    """检测Redis连接"""
    result = {
        "service": "Redis",
        "status": "unknown",
        "message": "",
        "details": {}
    }
    
    try:
        client = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            socket_connect_timeout=5
        )
        
        response = client.ping()
        if response:
            info = client.info("memory")
            
            result["status"] = "healthy"
            result["message"] = "Redis连接成功"
            result["details"]["used_memory"] = info.get("used_memory_human", "unknown")
            result["details"]["connected_clients"] = client.info().get("connected_clients", 0)
        
        client.close()
        
    except RedisError as e:
        result["status"] = "unhealthy"
        result["message"] = f"Redis连接失败: {str(e)}"
    
    return result
```

#### Shell脚本示例

```bash
#!/bin/bash

check_redis() {
    local host="${REDIS_HOST:-localhost}"
    local port="${REDIS_PORT:-6379}"
    
    echo "检测Redis连接..."
    
    response=$(redis-cli -h "$host" -p "$port" ping 2>/dev/null)
    
    if [ "$response" = "PONG" ]; then
        echo "✅ Redis连接正常"
        redis-cli -h "$host" -p "$port" info memory | grep used_memory_human
        return 0
    else
        echo "❌ Redis连接失败"
        return 1
    fi
}
```

### 后端API健康检测

#### 检测步骤

1. 发送HTTP请求到健康检查端点
2. 验证响应状态码
3. 检查响应时间是否在可接受范围内
4. 验证响应内容格式

#### Python示例

```python
import requests
from typing import Optional

def check_api_health(
    base_url: str,
    health_endpoint: str = "/health",
    timeout: int = 10,
    expected_status: int = 200
) -> dict:
    """检测后端API健康状态"""
    result = {
        "service": "Backend API",
        "status": "unknown",
        "message": "",
        "details": {}
    }
    
    url = f"{base_url.rstrip('/')}{health_endpoint}"
    
    try:
        response = requests.get(url, timeout=timeout)
        response_time_ms = response.elapsed.total_seconds() * 1000
        
        result["details"]["url"] = url
        result["details"]["status_code"] = response.status_code
        result["details"]["response_time_ms"] = round(response_time_ms, 2)
        
        if response.status_code == expected_status:
            result["status"] = "healthy"
            result["message"] = "API健康检测通过"
            
            try:
                health_data = response.json()
                result["details"]["response"] = health_data
            except ValueError:
                result["details"]["response"] = response.text
        else:
            result["status"] = "unhealthy"
            result["message"] = f"API返回异常状态码: {response.status_code}"
            
    except requests.exceptions.Timeout:
        result["status"] = "unhealthy"
        result["message"] = f"API请求超时（>{timeout}秒）"
    except requests.exceptions.ConnectionError:
        result["status"] = "unhealthy"
        result["message"] = "API连接失败"
    except requests.exceptions.RequestException as e:
        result["status"] = "unhealthy"
        result["message"] = f"API请求异常: {str(e)}"
    
    return result
```

#### 健康检查端点实现示例

```python
from fastapi import FastAPI, Response
from datetime import datetime

app = FastAPI()

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "redis": "connected"
        }
    }

@app.get("/health/ready")
async def readiness_check():
    """就绪检查端点"""
    checks = {
        "database": check_postgresql_connection(...),
        "redis": check_redis_connection(...)
    }
    
    all_healthy = all(c["status"] == "healthy" for c in checks.values())
    
    if all_healthy:
        return {"status": "ready", "checks": checks}
    
    return Response(
        content={"status": "not_ready", "checks": checks},
        status_code=503
    )
```

### 前端服务检测

#### 检测步骤

1. 检查前端服务是否可访问
2. 验证静态资源加载
3. 检查前端应用版本信息
4. 验证关键页面可访问性

#### Python示例

```python
import requests
from bs4 import BeautifulSoup

def check_frontend_service(
    base_url: str,
    expected_title: str = None,
    timeout: int = 10
) -> dict:
    """检测前端服务"""
    result = {
        "service": "Frontend",
        "status": "unknown",
        "message": "",
        "details": {}
    }
    
    try:
        response = requests.get(base_url, timeout=timeout)
        response_time_ms = response.elapsed.total_seconds() * 1000
        
        result["details"]["url"] = base_url
        result["details"]["status_code"] = response.status_code
        result["details"]["response_time_ms"] = round(response_time_ms, 2)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else None
            
            result["details"]["title"] = title
            
            if expected_title and expected_title not in (title or ""):
                result["status"] = "degraded"
                result["message"] = f"前端标题不匹配，预期包含: {expected_title}"
            else:
                result["status"] = "healthy"
                result["message"] = "前端服务正常"
        else:
            result["status"] = "unhealthy"
            result["message"] = f"前端返回异常状态码: {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        result["status"] = "unhealthy"
        result["message"] = f"前端服务连接失败: {str(e)}"
    
    return result
```

## Docker服务管理

### Docker生命周期管理

```
┌───────────────────────────────────────────────────────────┐
│                  Docker服务生命周期                         │
│                                                           │
│    ┌─────────┐     ┌─────────┐     ┌─────────┐           │
│    │  创建   │ ──► │  运行   │ ──► │  暂停   │           │
│    └─────────┘     └─────────┘     └─────────┘           │
│         │               │               │                 │
│         │               ▼               │                 │
│         │         ┌─────────┐           │                 │
│         │         │  停止   │ ◄─────────┘                 │
│         │         └─────────┘                             │
│         │               │                                 │
│         ▼               ▼                                 │
│    ┌─────────┐     ┌─────────┐                           │
│    │  删除   │ ◄── │  重启   │                           │
│    └─────────┘     └─────────┘                           │
└───────────────────────────────────────────────────────────┘
```

### Docker服务启动/停止/重启

#### 启动服务

```bash
#!/bin/bash

docker_start_services() {
    echo "启动Docker服务..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d
        echo "✅ 服务启动完成"
    else
        echo "❌ 未找到docker-compose.yml文件"
        return 1
    fi
}

docker_start_single() {
    local container_name="$1"
    
    echo "启动容器: $container_name"
    docker start "$container_name"
    
    if [ $? -eq 0 ]; then
        echo "✅ 容器 $container_name 启动成功"
    else
        echo "❌ 容器 $container_name 启动失败"
    fi
}
```

#### 停止服务

```bash
#!/bin/bash

docker_stop_services() {
    echo "停止Docker服务..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose down
        echo "✅ 服务停止完成"
    else
        echo "❌ 未找到docker-compose.yml文件"
        return 1
    fi
}

docker_stop_single() {
    local container_name="$1"
    local timeout="${2:-10}"
    
    echo "停止容器: $container_name (超时: ${timeout}秒)"
    docker stop -t "$timeout" "$container_name"
    
    if [ $? -eq 0 ]; then
        echo "✅ 容器 $container_name 停止成功"
    else
        echo "❌ 容器 $container_name 停止失败"
    fi
}
```

#### 重启服务

```bash
#!/bin/bash

docker_restart_services() {
    echo "重启Docker服务..."
    
    if [ -f "docker-compose.yml" ]; then
        docker-compose restart
        echo "✅ 服务重启完成"
    else
        echo "❌ 未找到docker-compose.yml文件"
        return 1
    fi
}

docker_restart_single() {
    local container_name="$1"
    local timeout="${2:-10}"
    
    echo "重启容器: $container_name"
    docker restart -t "$timeout" "$container_name"
    
    if [ $? -eq 0 ]; then
        echo "✅ 容器 $container_name 重启成功"
    else
        echo "❌ 容器 $container_name 重启失败"
    fi
}
```

### Docker容器状态查询

#### Python示例

```python
import docker
from typing import List, Dict

def get_container_status(container_name: str = None) -> List[Dict]:
    """获取Docker容器状态"""
    client = docker.from_env()
    results = []
    
    if container_name:
        containers = [client.containers.get(container_name)]
    else:
        containers = client.containers.list(all=True)
    
    for container in containers:
        status = {
            "name": container.name,
            "id": container.short_id,
            "status": container.status,
            "image": container.image.tags[0] if container.image.tags else "none",
            "ports": container.ports,
            "created": container.attrs["Created"],
            "health": None
        }
        
        if "Health" in container.attrs["State"]:
            status["health"] = container.attrs["State"]["Health"]["Status"]
        
        results.append(status)
    
    return results

def print_container_status():
    """打印容器状态表格"""
    containers = get_container_status()
    
    print(f"{'容器名称':<30} {'状态':<15} {'健康状态':<10} {'镜像':<20}")
    print("-" * 75)
    
    for c in containers:
        health = c["health"] or "N/A"
        print(f"{c['name']:<30} {c['status']:<15} {health:<10} {c['image']:<20}")
```

#### Shell脚本示例

```bash
#!/bin/bash

docker_status_all() {
    echo "查询所有容器状态..."
    echo ""
    
    docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}\t{{.Image}}"
}

docker_status_single() {
    local container_name="$1"
    
    echo "查询容器状态: $container_name"
    echo ""
    
    docker inspect "$container_name" --format '
容器名称: {{.Name}}
状态: {{.State.Status}}
健康状态: {{if .State.Health}}{{.State.Health.Status}}{{else}}N/A{{end}}
启动时间: {{.State.StartedAt}}
镜像: {{.Config.Image}}
IP地址: {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}
'
}

docker_status_health() {
    local container_name="$1"
    
    echo "查询容器健康状态: $container_name"
    
    docker inspect "$container_name" --format '
健康状态: {{if .State.Health}}{{.State.Health.Status}}{{else}}未配置健康检查{{end}}
{{if .State.Health}}
最近检查:
{{range .State.Health.Log}}
  - 时间: {{.End}}
    退出码: {{.ExitCode}}
    输出: {{.Output}}
{{end}}
{{end}}
'
}
```

### Docker容器健康检查

#### docker-compose.yml健康检查配置

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: app_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres -d app_db"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build: ./backend
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  frontend:
    build: ./frontend
    depends_on:
      backend:
        condition: service_healthy
    ports:
      - "80:80"
```

#### Python健康检查脚本

```python
import docker
import time
from typing import Dict, List

def wait_for_healthy_containers(
    container_names: List[str],
    timeout: int = 300,
    interval: int = 5
) -> Dict[str, bool]:
    """等待容器变为健康状态"""
    client = docker.from_env()
    results = {name: False for name in container_names}
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        all_healthy = True
        
        for name in container_names:
            if results[name]:
                continue
                
            try:
                container = client.containers.get(name)
                state = container.attrs["State"]
                
                if state["Status"] != "running":
                    print(f"⏳ {name}: 容器未运行")
                    all_healthy = False
                    continue
                
                if "Health" in state:
                    health_status = state["Health"]["Status"]
                    if health_status == "healthy":
                        print(f"✅ {name}: 健康检查通过")
                        results[name] = True
                    else:
                        print(f"⏳ {name}: 健康状态 - {health_status}")
                        all_healthy = False
                else:
                    print(f"⚠️ {name}: 未配置健康检查，假设健康")
                    results[name] = True
                    
            except docker.errors.NotFound:
                print(f"❌ {name}: 容器不存在")
                all_healthy = False
        
        if all_healthy:
            break
            
        time.sleep(interval)
    
    return results
```

### docker-compose.yml配置识别

#### Python解析示例

```python
import yaml
from typing import Dict, List, Any

def parse_compose_file(file_path: str = "docker-compose.yml") -> Dict[str, Any]:
    """解析docker-compose.yml文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    result = {
        "version": config.get("version", "unknown"),
        "services": [],
        "networks": list(config.get("networks", {}).keys()),
        "volumes": list(config.get("volumes", {}).keys())
    }
    
    for service_name, service_config in config.get("services", {}).items():
        service_info = {
            "name": service_name,
            "image": service_config.get("image", "build"),
            "ports": service_config.get("ports", []),
            "environment": list(service_config.get("environment", {}).keys()) if isinstance(service_config.get("environment"), dict) else [],
            "depends_on": service_config.get("depends_on", []),
            "healthcheck": "healthcheck" in service_config,
            "volumes": service_config.get("volumes", [])
        }
        result["services"].append(service_info)
    
    return result

def print_compose_info(file_path: str = "docker-compose.yml"):
    """打印docker-compose配置信息"""
    config = parse_compose_file(file_path)
    
    print(f"Docker Compose 版本: {config['version']}")
    print(f"\n服务列表:")
    print("-" * 80)
    
    for service in config["services"]:
        print(f"\n📦 {service['name']}")
        print(f"   镜像: {service['image']}")
        print(f"   端口: {', '.join(service['ports']) or '无'}")
        print(f"   健康检查: {'已配置' if service['healthcheck'] else '未配置'}")
        print(f"   依赖: {', '.join(service['depends_on']) or '无'}")
```

## 服务依赖检测

### 测试前环境检测流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    测试前环境检测流程                              │
│                                                                 │
│  ┌─────────────┐                                               │
│  │  开始测试    │                                               │
│  └──────┬──────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐     ┌─────────────┐                           │
│  │ 检测CI环境  │──是──►│ 跳过部分检测 │                           │
│  └──────┬──────┘     └─────────────┘                           │
│         │否                                                     │
│         ▼                                                       │
│  ┌─────────────┐                                               │
│  │ 检测Docker  │                                               │
│  │ 服务状态    │                                               │
│  └──────┬──────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐     ┌─────────────┐                           │
│  │ 服务是否    │──否──►│ 启动服务    │                           │
│  │ 运行中？    │      └──────┬──────┘                           │
│  └──────┬──────┘             │                                   │
│         │是                  │                                   │
│         ▼                    │                                   │
│  ┌─────────────┐◄────────────┘                                   │
│  │ 等待服务    │                                               │
│  │ 就绪        │                                               │
│  └──────┬──────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐                                               │
│  │ 执行健康    │                                               │
│  │ 检查        │                                               │
│  └──────┬──────┘                                               │
│         │                                                       │
│         ▼                                                       │
│  ┌─────────────┐     ┌─────────────┐                           │
│  │ 健康检查    │──否──►│ 报告错误    │                           │
│  │ 通过？      │      │ 并退出      │                           │
│  └──────┬──────┘     └─────────────┘                           │
│         │是                                                     │
│         ▼                                                       │
│  ┌─────────────┐                                               │
│  │ 开始测试    │                                               │
│  └─────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘
```

### Python环境检测实现

```python
import os
import time
import subprocess
from typing import Dict, List, Callable, Optional

class EnvironmentChecker:
    """环境检测器"""
    
    def __init__(self, skip_in_ci: bool = True):
        self.skip_in_ci = skip_in_ci
        self.ci_env_vars = ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "JENKINS_URL"]
        self.checks: List[Dict] = []
    
    def is_ci_environment(self) -> bool:
        """检测是否在CI环境中"""
        return any(os.getenv(var) for var in self.ci_env_vars)
    
    def add_check(
        self,
        name: str,
        check_func: Callable[[], bool],
        required: bool = True,
        skip_in_ci: bool = False
    ):
        """添加检测项"""
        self.checks.append({
            "name": name,
            "func": check_func,
            "required": required,
            "skip_in_ci": skip_in_ci
        })
    
    def run_checks(self) -> Dict:
        """运行所有检测"""
        results = {
            "passed": [],
            "failed": [],
            "skipped": [],
            "is_ci": self.is_ci_environment()
        }
        
        for check in self.checks:
            if results["is_ci"] and check["skip_in_ci"]:
                print(f"⏭️ 跳过检测（CI环境）: {check['name']}")
                results["skipped"].append(check["name"])
                continue
            
            print(f"🔍 执行检测: {check['name']}")
            
            try:
                if check["func"]():
                    print(f"✅ 检测通过: {check['name']}")
                    results["passed"].append(check["name"])
                else:
                    print(f"❌ 检测失败: {check['name']}")
                    results["failed"].append(check["name"])
                    
                    if check["required"]:
                        print(f"⚠️ 必要检测失败，停止后续检测")
                        break
                        
            except Exception as e:
                print(f"❌ 检测异常: {check['name']} - {str(e)}")
                results["failed"].append(check["name"])
                
                if check["required"]:
                    break
        
        return results


def check_docker_running() -> bool:
    """检测Docker是否运行"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def check_compose_file() -> bool:
    """检测docker-compose.yml是否存在"""
    return os.path.exists("docker-compose.yml")


def check_services_running() -> bool:
    """检测服务是否运行"""
    try:
        result = subprocess.run(
            ["docker-compose", "ps", "-q"],
            capture_output=True,
            timeout=10
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def setup_test_environment():
    """设置测试环境"""
    checker = EnvironmentChecker(skip_in_ci=True)
    
    checker.add_check(
        "Docker服务",
        check_docker_running,
        required=True,
        skip_in_ci=True
    )
    
    checker.add_check(
        "docker-compose.yml",
        check_compose_file,
        required=True,
        skip_in_ci=False
    )
    
    checker.add_check(
        "服务运行状态",
        check_services_running,
        required=False,
        skip_in_ci=True
    )
    
    return checker.run_checks()
```

### 服务就绪等待机制

```python
import time
import socket
import requests
from typing import Optional, Callable

def wait_for_port(
    host: str,
    port: int,
    timeout: int = 60,
    interval: float = 1.0
) -> bool:
    """等待端口可用"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                print(f"✅ 端口 {host}:{port} 已就绪")
                return True
                
        except socket.error:
            pass
        
        time.sleep(interval)
    
    print(f"❌ 等待端口 {host}:{port} 超时")
    return False


def wait_for_url(
    url: str,
    expected_status: int = 200,
    timeout: int = 60,
    interval: float = 1.0
) -> bool:
    """等待URL可访问"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            
            if response.status_code == expected_status:
                print(f"✅ URL {url} 已就绪")
                return True
                
        except requests.exceptions.RequestException:
            pass
        
        time.sleep(interval)
    
    print(f"❌ 等待URL {url} 超时")
    return False


def wait_for_condition(
    condition: Callable[[], bool],
    description: str = "条件",
    timeout: int = 60,
    interval: float = 1.0
) -> bool:
    """等待条件满足"""
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            if condition():
                print(f"✅ {description} 已满足")
                return True
        except Exception:
            pass
        
        time.sleep(interval)
    
    print(f"❌ 等待 {description} 超时")
    return False


class ServiceWaiter:
    """服务等待器"""
    
    def __init__(self, timeout: int = 120):
        self.timeout = timeout
        self.services = []
    
    def add_port_check(self, name: str, host: str, port: int):
        """添加端口检测"""
        self.services.append({
            "type": "port",
            "name": name,
            "host": host,
            "port": port
        })
    
    def add_url_check(self, name: str, url: str, expected_status: int = 200):
        """添加URL检测"""
        self.services.append({
            "type": "url",
            "name": name,
            "url": url,
            "expected_status": expected_status
        })
    
    def wait_all(self) -> Dict[str, bool]:
        """等待所有服务就绪"""
        results = {}
        
        for service in self.services:
            print(f"⏳ 等待服务就绪: {service['name']}")
            
            if service["type"] == "port":
                success = wait_for_port(
                    service["host"],
                    service["port"],
                    timeout=self.timeout
                )
            elif service["type"] == "url":
                success = wait_for_url(
                    service["url"],
                    service["expected_status"],
                    timeout=self.timeout
                )
            else:
                success = False
            
            results[service["name"]] = success
            
            if not success:
                print(f"⚠️ 服务 {service['name']} 未就绪，继续检测其他服务...")
        
        return results
```

### CI环境跳过检测选项

```python
import os
import functools
from typing import Optional, Callable, Any

def skip_in_ci(reason: str = "CI环境"):
    """装饰器：在CI环境中跳过检测"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Optional[Any]:
            if is_ci_environment():
                print(f"⏭️ 跳过 {func.__name__}（{reason}）")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def is_ci_environment() -> bool:
    """检测CI环境"""
    ci_indicators = [
        "CI",
        "CONTINUOUS_INTEGRATION",
        "GITHUB_ACTIONS",
        "GITLAB_CI",
        "CIRCLECI",
        "TRAVIS",
        "JENKINS_URL",
        "BUILDKITE",
        "DRONE"
    ]
    return any(os.getenv(var) for var in ci_indicators)


def should_skip_check(check_name: str, config: dict = None) -> bool:
    """判断是否应该跳过检测"""
    if is_ci_environment():
        if config and config.get("skip_in_ci"):
            print(f"⏭️ CI环境跳过检测: {check_name}")
            return True
    
    if os.getenv("SKIP_ENV_CHECK") == "true":
        print(f"⏭️ 配置跳过检测: {check_name}")
        return True
    
    return False


class CIEnvironmentConfig:
    """CI环境配置"""
    
    def __init__(self):
        self.is_ci = is_ci_environment()
        self.skip_docker_checks = self._get_bool_env("SKIP_DOCKER_CHECKS", self.is_ci)
        self.skip_service_startup = self._get_bool_env("SKIP_SERVICE_STARTUP", self.is_ci)
        self.use_mock_services = self._get_bool_env("USE_MOCK_SERVICES", False)
        self.health_check_timeout = int(os.getenv("HEALTH_CHECK_TIMEOUT", "30"))
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        value = os.getenv(key, "").lower()
        if value in ("true", "1", "yes"):
            return True
        if value in ("false", "0", "no"):
            return False
        return default
    
    def get_config(self) -> dict:
        return {
            "is_ci": self.is_ci,
            "skip_docker_checks": self.skip_docker_checks,
            "skip_service_startup": self.skip_service_startup,
            "use_mock_services": self.use_mock_services,
            "health_check_timeout": self.health_check_timeout
        }


def configure_for_ci():
    """配置CI环境"""
    config = CIEnvironmentConfig()
    
    if config.is_ci:
        print("🔧 检测到CI环境，应用CI配置...")
        print(f"   - 跳过Docker检测: {config.skip_docker_checks}")
        print(f"   - 跳过服务启动: {config.skip_service_startup}")
        print(f"   - 使用Mock服务: {config.use_mock_services}")
        print(f"   - 健康检查超时: {config.health_check_timeout}秒")
    
    return config
```

## 检测结果报告

### 报告生成

```python
from datetime import datetime
from typing import List, Dict

def generate_health_report(results: List[Dict]) -> str:
    """生成健康检测报告"""
    report_lines = [
        "=" * 60,
        "环境健康检测报告",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 60,
        ""
    ]
    
    healthy_count = sum(1 for r in results if r["status"] == "healthy")
    unhealthy_count = sum(1 for r in results if r["status"] == "unhealthy")
    degraded_count = sum(1 for r in results if r["status"] == "degraded")
    
    report_lines.append("📊 检测摘要:")
    report_lines.append(f"   ✅ 健康: {healthy_count}")
    report_lines.append(f"   ⚠️ 降级: {degraded_count}")
    report_lines.append(f"   ❌ 不健康: {unhealthy_count}")
    report_lines.append("")
    report_lines.append("-" * 60)
    report_lines.append("📋 详细结果:")
    report_lines.append("")
    
    for result in results:
        status_icon = {
            "healthy": "✅",
            "unhealthy": "❌",
            "degraded": "⚠️",
            "unknown": "❓"
        }.get(result["status"], "❓")
        
        report_lines.append(f"{status_icon} {result['service']}")
        report_lines.append(f"   状态: {result['status']}")
        report_lines.append(f"   消息: {result['message']}")
        
        if result.get("details"):
            for key, value in result["details"].items():
                report_lines.append(f"   {key}: {value}")
        
        report_lines.append("")
    
    report_lines.append("=" * 60)
    
    return "\n".join(report_lines)
```

## 检查清单

### 服务检测检查清单

- [ ] PostgreSQL数据库连接检测完成
- [ ] Redis缓存服务连接检测完成
- [ ] 后端API健康端点可访问
- [ ] 前端服务可访问
- [ ] 所有服务响应时间在可接受范围内
- [ ] 服务版本信息正确

### Docker管理检查清单

- [ ] Docker服务正常运行
- [ ] docker-compose.yml配置正确
- [ ] 所有容器处于运行状态
- [ ] 容器健康检查配置完成
- [ ] 服务依赖关系正确配置
- [ ] 端口映射配置正确

### 环境检测检查清单

- [ ] CI环境识别正确
- [ ] 必要服务启动检测完成
- [ ] 服务就绪等待机制正常
- [ ] 健康检查超时配置合理
- [ ] 错误报告机制完善
- [ ] 日志记录完整

### 测试前检查清单

- [ ] 环境检测脚本已执行
- [ ] 所有依赖服务已启动
- [ ] 数据库连接池配置正确
- [ ] 测试数据准备完成
- [ ] Mock服务配置正确（如需要）
- [ ] 清理脚本准备就绪
