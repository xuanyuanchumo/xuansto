#!/usr/bin/env python3
"""
三省六部协同开发系统 - 环境检测脚本
检测数据库、Redis、后端API、前端服务等环境状态

功能：
- Docker 环境检测
- PostgreSQL 连接检测（支持 psycopg2 和端口检测）
- Redis 连接检测（支持 redis-py 和端口检测）
- 后端 API 健康检测
- 前端服务状态检测
- 依赖版本验证
- 环境变量检查
- 等待服务就绪功能
"""
import argparse
import json
import logging
import os
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from skillscripts.core.path_config_center import get_path_config

# 项目路径配置
PROJECT_ROOT = get_path_config().SKILL_ROOT


class EnvStatus(Enum):
    """环境状态枚举"""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    WARNING = "warning"
    SKIPPED = "skipped"
    ERROR = "error"


class LogLevel(Enum):
    """日志级别枚举"""
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    DEBUG = "debug"


@dataclass
class EnvCheckResult:
    """环境检查结果数据类"""
    name: str
    status: EnvStatus
    message: str
    response_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass
class DependencyInfo:
    """依赖信息数据类"""
    name: str
    installed: bool
    version: Optional[str] = None
    required_version: Optional[str] = None
    path: Optional[str] = None
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class EnvironmentReport:
    """环境检测报告"""
    timestamp: str
    overall_status: EnvStatus
    services: List[EnvCheckResult]
    dependencies: List[DependencyInfo] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    summary: Dict[str, int] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "services": [s.to_dict() for s in self.services],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "environment_variables": self.environment_variables,
            "summary": self.summary,
            "duration_ms": self.duration_ms
        }


class Logger:
    """日志记录器"""
    
    ICONS = {
        LogLevel.INFO: "ℹ️",
        LogLevel.SUCCESS: "✅",
        LogLevel.ERROR: "❌",
        LogLevel.WARNING: "⚠️",
        LogLevel.DEBUG: "🔍"
    }
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        logging.basicConfig(
            level=logging.DEBUG if verbose else logging.WARNING,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        """记录日志"""
        icon = self.ICONS.get(level, "")
        formatted_message = f"{icon} {message}"
        
        if self.verbose:
            print(formatted_message)
        
        log_method = getattr(self.logger, level.value, self.logger.info)
        log_method(message)
    
    def debug(self, message: str):
        self.log(message, LogLevel.DEBUG)
    
    def info(self, message: str):
        self.log(message, LogLevel.INFO)
    
    def success(self, message: str):
        self.log(message, LogLevel.SUCCESS)
    
    def error(self, message: str):
        self.log(message, LogLevel.ERROR)
    
    def warning(self, message: str):
        self.log(message, LogLevel.WARNING)


class EnvironmentChecker:
    """环境检测器"""
    
    def __init__(self, verbose: bool = True):
        self.logger = Logger(verbose=verbose)
        self.results: List[EnvCheckResult] = []
        self.dependencies: List[DependencyInfo] = []
    
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取环境变量"""
        return os.environ.get(key, default)
    
    def _create_result(
        self,
        name: str,
        status: EnvStatus,
        message: str,
        response_time_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> EnvCheckResult:
        """创建检查结果"""
        result = EnvCheckResult(
            name=name,
            status=status,
            message=message,
            response_time_ms=response_time_ms,
            metadata=metadata or {}
        )
        self.results.append(result)
        return result
    
    def _check_port(self, host: str, port: int, timeout: int = 5) -> tuple[bool, Optional[float]]:
        """检查端口是否可连接"""
        start_time = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if result == 0:
                return True, response_time
            return False, None
        except Exception as e:
            self.logger.debug(f"端口检查异常 {host}:{port}: {e}")
            return False, None
    
    def _http_get(self, url: str, timeout: int = 10) -> tuple[bool, Optional[int], Optional[float], Optional[str]]:
        """发送 HTTP GET 请求"""
        start_time = time.time()
        try:
            req = Request(url, method='GET')
            req.add_header('User-Agent', 'EnvironmentChecker/1.0')
            
            with urlopen(req, timeout=timeout) as response:
                response_time = round((time.time() - start_time) * 1000, 2)
                return True, response.status, response_time, None
                
        except HTTPError as e:
            response_time = round((time.time() - start_time) * 1000, 2)
            return False, e.code, response_time, str(e.reason)
        except URLError as e:
            return False, None, None, str(e.reason)
        except socket.timeout:
            return False, None, None, "Connection timeout"
        except Exception as e:
            return False, None, None, str(e)
    
    def check_docker(self, skip: bool = False) -> EnvCheckResult:
        """检查 Docker 状态"""
        if skip:
            return self._create_result(
                name="Docker",
                status=EnvStatus.SKIPPED,
                message="已跳过 Docker 检测"
            )
        
        self.logger.info("检查 Docker 状态...")
        start_time = time.time()
        
        try:
            proc = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            response_time = round((time.time() - start_time) * 1000, 2)
            
            if proc.returncode == 0:
                return self._create_result(
                    name="Docker",
                    status=EnvStatus.HEALTHY,
                    message="Docker 正在运行",
                    response_time_ms=response_time
                )
            else:
                return self._create_result(
                    name="Docker",
                    status=EnvStatus.UNHEALTHY,
                    message="Docker 未运行",
                    response_time_ms=response_time,
                    metadata={"stderr": proc.stderr[:200]}
                )
        except FileNotFoundError:
            return self._create_result(
                name="Docker",
                status=EnvStatus.UNHEALTHY,
                message="Docker 未安装"
            )
        except subprocess.TimeoutExpired:
            return self._create_result(
                name="Docker",
                status=EnvStatus.UNHEALTHY,
                message="Docker 检查超时"
            )
        except Exception as e:
            return self._create_result(
                name="Docker",
                status=EnvStatus.ERROR,
                message=f"Docker 检查失败: {str(e)}"
            )
    
    def check_postgresql(self) -> EnvCheckResult:
        """检查 PostgreSQL 连接状态"""
        self.logger.info("检查 PostgreSQL 连接...")
        
        host = self.get_env("POSTGRES_HOST", "localhost")
        port = int(self.get_env("POSTGRES_PORT", "5432"))
        database = self.get_env("POSTGRES_DB", "skiller")
        user = self.get_env("POSTGRES_USER", "postgres")
        password = self.get_env("POSTGRES_PASSWORD", "")
        
        metadata = {
            "host": host,
            "port": port,
            "database": database,
            "user": user
        }
        
        # 尝试使用 psycopg2 连接
        try:
            import psycopg2
            start_time = time.time()
            conn = psycopg2.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                connect_timeout=5
            )
            conn.close()
            response_time = round((time.time() - start_time) * 1000, 2)
            
            return self._create_result(
                name="PostgreSQL",
                status=EnvStatus.HEALTHY,
                message=f"PostgreSQL 连接正常 (数据库: {database})",
                response_time_ms=response_time,
                metadata=metadata
            )
        except ImportError:
            self.logger.debug("psycopg2 未安装，使用端口检测")
        except Exception as e:
            return self._create_result(
                name="PostgreSQL",
                status=EnvStatus.UNHEALTHY,
                message=f"PostgreSQL 连接失败: {str(e)}",
                metadata={**metadata, "error": str(e)}
            )
        
        # 回退到端口检测
        success, response_time = self._check_port(host, port, timeout=5)
        
        if success:
            return self._create_result(
                name="PostgreSQL",
                status=EnvStatus.HEALTHY,
                message=f"PostgreSQL 端口可访问 (数据库: {database})",
                response_time_ms=response_time,
                metadata=metadata
            )
        else:
            return self._create_result(
                name="PostgreSQL",
                status=EnvStatus.UNHEALTHY,
                message=f"PostgreSQL 无法连接: {host}:{port}",
                metadata=metadata
            )
    
    def check_redis(self) -> EnvCheckResult:
        """检查 Redis 连接状态"""
        self.logger.info("检查 Redis 连接...")
        
        host = self.get_env("REDIS_HOST", "localhost")
        port = int(self.get_env("REDIS_PORT", "6379"))
        db = int(self.get_env("REDIS_DB", "0"))
        password = self.get_env("REDIS_PASSWORD", None)
        
        metadata = {
            "host": host,
            "port": port,
            "db": db
        }
        
        # 尝试使用 redis-py 连接
        try:
            import redis
            start_time = time.time()
            client = redis.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            client.ping()
            response_time = round((time.time() - start_time) * 1000, 2)
            client.close()
            
            return self._create_result(
                name="Redis",
                status=EnvStatus.HEALTHY,
                message=f"Redis 连接正常 (DB: {db})",
                response_time_ms=response_time,
                metadata=metadata
            )
        except ImportError:
            self.logger.debug("redis-py 未安装，使用端口检测")
        except Exception as e:
            return self._create_result(
                name="Redis",
                status=EnvStatus.UNHEALTHY,
                message=f"Redis 连接失败: {str(e)}",
                metadata={**metadata, "error": str(e)}
            )
        
        # 回退到端口检测
        success, response_time = self._check_port(host, port, timeout=5)
        
        if success:
            return self._create_result(
                name="Redis",
                status=EnvStatus.HEALTHY,
                message=f"Redis 端口可访问 (DB: {db})",
                response_time_ms=response_time,
                metadata=metadata
            )
        else:
            return self._create_result(
                name="Redis",
                status=EnvStatus.UNHEALTHY,
                message=f"Redis 无法连接: {host}:{port}",
                metadata=metadata
            )
    
    def check_backend_api(self, timeout: int = 10) -> EnvCheckResult:
        """检查后端 API 健康状态"""
        self.logger.info("检查后端 API 状态...")
        
        base_url = self.get_env("BACKEND_URL", "http://localhost:8000")
        health_endpoint = self.get_env("HEALTH_ENDPOINT", "/health")
        health_url = f"{base_url.rstrip('/')}{health_endpoint}"
        
        success, status_code, response_time, error = self._http_get(health_url, timeout)
        
        metadata = {"url": health_url}
        
        if success and status_code == 200:
            return self._create_result(
                name="Backend API",
                status=EnvStatus.HEALTHY,
                message=f"后端 API 正常 (响应时间: {response_time}ms)",
                response_time_ms=response_time,
                metadata=metadata
            )
        elif success:
            return self._create_result(
                name="Backend API",
                status=EnvStatus.WARNING,
                message=f"后端 API 返回异常状态码: {status_code}",
                response_time_ms=response_time,
                metadata={**metadata, "status_code": status_code}
            )
        else:
            return self._create_result(
                name="Backend API",
                status=EnvStatus.UNHEALTHY,
                message=f"后端 API 无法访问: {error}",
                metadata={**metadata, "error": error}
            )
    
    def check_frontend(self, port: int = 5173) -> EnvCheckResult:
        """检查前端服务状态"""
        self.logger.info("检查前端服务状态...")
        
        host = self.get_env("FRONTEND_HOST", "localhost")
        frontend_port = int(self.get_env("FRONTEND_PORT", str(port)))
        
        success, response_time = self._check_port(host, frontend_port, timeout=5)
        
        metadata = {
            "host": host,
            "port": frontend_port,
            "url": f"http://{host}:{frontend_port}"
        }
        
        if success:
            return self._create_result(
                name="Frontend",
                status=EnvStatus.HEALTHY,
                message=f"前端服务正常运行 (端口: {frontend_port})",
                response_time_ms=response_time,
                metadata=metadata
            )
        else:
            return self._create_result(
                name="Frontend",
                status=EnvStatus.UNHEALTHY,
                message=f"前端服务无法访问 (端口: {frontend_port})",
                metadata=metadata
            )
    
    def check_python_dependency(self, package_name: str, import_name: Optional[str] = None) -> DependencyInfo:
        """检查 Python 依赖"""
        import_name = import_name or package_name
        
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', None)
            if not version:
                version = getattr(module, 'VERSION', None)
            
            return DependencyInfo(
                name=package_name,
                installed=True,
                version=version,
                message=f"已安装 (版本: {version})" if version else "已安装"
            )
        except ImportError:
            return DependencyInfo(
                name=package_name,
                installed=False,
                message="未安装"
            )
    
    def check_command_dependency(self, command: str, version_flag: str = "--version") -> DependencyInfo:
        """检查命令行依赖"""
        try:
            result = subprocess.run(
                [command, version_flag],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version_output = (result.stdout or result.stderr).strip().split('\n')[0][:100]
                return DependencyInfo(
                    name=command,
                    installed=True,
                    version=version_output,
                    message=f"已安装: {version_output}"
                )
            else:
                return DependencyInfo(
                    name=command,
                    installed=False,
                    message=f"命令返回错误: {result.stderr[:100]}"
                )
        except FileNotFoundError:
            return DependencyInfo(
                name=command,
                installed=False,
                message="未找到命令"
            )
        except Exception as e:
            return DependencyInfo(
                name=command,
                installed=False,
                message=f"检查失败: {str(e)}"
            )
    
    def check_dependencies(self) -> List[DependencyInfo]:
        """检查所有依赖"""
        self.logger.info("检查依赖...")
        
        self.dependencies = []
        
        # 系统命令依赖
        commands = [
            ("docker", "--version"),
            ("docker-compose", "--version"),
            ("python", "--version"),
            ("node", "--version"),
            ("npm", "--version"),
            ("git", "--version")
        ]
        
        for cmd, flag in commands:
            dep = self.check_command_dependency(cmd, flag)
            self.dependencies.append(dep)
            if dep.installed:
                self.logger.success(f"{cmd}: {dep.message}")
            else:
                self.logger.warning(f"{cmd}: {dep.message}")
        
        # Python 依赖
        python_packages = [
            ("psycopg2", "psycopg2"),
            ("redis", "redis"),
            ("fastapi", "fastapi"),
            ("uvicorn", "uvicorn"),
            ("sqlalchemy", "sqlalchemy"),
            ("pydantic", "pydantic")
        ]
        
        for pkg, import_name in python_packages:
            dep = self.check_python_dependency(pkg, import_name)
            self.dependencies.append(dep)
            if dep.installed:
                self.logger.success(f"{pkg}: {dep.message}")
            else:
                self.logger.debug(f"{pkg}: {dep.message}")
        
        return self.dependencies
    
    def get_environment_variables(self) -> Dict[str, str]:
        """获取相关环境变量"""
        env_vars = {}
        
        keys = [
            "POSTGRES_HOST", "POSTGRES_PORT", "POSTGRES_DB",
            "POSTGRES_USER", "POSTGRES_PASSWORD",
            "REDIS_HOST", "REDIS_PORT", "REDIS_DB", "REDIS_PASSWORD",
            "BACKEND_URL", "HEALTH_ENDPOINT",
            "FRONTEND_HOST", "FRONTEND_PORT",
            "ENV", "DEBUG", "LOG_LEVEL"
        ]
        
        for key in keys:
            value = self.get_env(key)
            if value is not None:
                # 隐藏密码
                if "PASSWORD" in key or "SECRET" in key:
                    env_vars[key] = "***"
                else:
                    env_vars[key] = value
        
        return env_vars
    
    def run_environment_check(
        self,
        skip_docker: bool = False,
        backend_timeout: int = 10,
        frontend_port: int = 5173,
        check_deps: bool = False
    ) -> EnvironmentReport:
        """运行完整环境检测"""
        start_time = time.time()
        self.results = []
        
        # 服务检查
        checks: List[Callable[[], EnvCheckResult]] = [
            lambda: self.check_docker(skip_docker),
            self.check_postgresql,
            self.check_redis,
            lambda: self.check_backend_api(backend_timeout),
            lambda: self.check_frontend(frontend_port)
        ]
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.logger.error(f"环境检查项执行失败: {e}")
        
        # 依赖检查
        if check_deps:
            self.check_dependencies()
        
        # 计算整体状态
        overall_status = EnvStatus.HEALTHY
        for result in self.results:
            if result.status == EnvStatus.ERROR:
                overall_status = EnvStatus.ERROR
                break
            elif result.status == EnvStatus.UNHEALTHY:
                overall_status = EnvStatus.UNHEALTHY
            elif result.status == EnvStatus.WARNING and overall_status == EnvStatus.HEALTHY:
                overall_status = EnvStatus.WARNING
        
        # 生成摘要
        summary = {
            "total": len(self.results),
            "healthy": sum(1 for r in self.results if r.status == EnvStatus.HEALTHY),
            "unhealthy": sum(1 for r in self.results if r.status == EnvStatus.UNHEALTHY),
            "warning": sum(1 for r in self.results if r.status == EnvStatus.WARNING),
            "skipped": sum(1 for r in self.results if r.status == EnvStatus.SKIPPED),
            "error": sum(1 for r in self.results if r.status == EnvStatus.ERROR)
        }
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        return EnvironmentReport(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            overall_status=overall_status,
            services=self.results,
            dependencies=self.dependencies,
            environment_variables=self.get_environment_variables(),
            summary=summary,
            duration_ms=duration_ms
        )
    
    def wait_for_services(
        self,
        max_wait: int = 60,
        interval: int = 5,
        skip_docker: bool = False,
        backend_timeout: int = 10,
        frontend_port: int = 5173
    ) -> EnvironmentReport:
        """等待服务就绪"""
        self.logger.info(f"等待服务就绪 (最长等待: {max_wait}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            report = self.run_environment_check(
                skip_docker=skip_docker,
                backend_timeout=backend_timeout,
                frontend_port=frontend_port
            )
            
            unhealthy_services = [
                s for s in report.services
                if s.status not in (EnvStatus.HEALTHY, EnvStatus.SKIPPED)
            ]
            
            if not unhealthy_services:
                self.logger.success("所有服务已就绪")
                return report
            
            pending = [s.name for s in unhealthy_services]
            elapsed = int(time.time() - start_time)
            remaining = max_wait - elapsed
            self.logger.info(f"等待服务: {', '.join(pending)}... (已等待 {elapsed}s, 剩余 {remaining}s)")
            time.sleep(interval)
        
        self.logger.warning("等待超时，部分服务未就绪")
        return self.run_environment_check(
            skip_docker=skip_docker,
            backend_timeout=backend_timeout,
            frontend_port=frontend_port
        )


def print_report(report: EnvironmentReport, verbose: bool = False) -> bool:
    """打印环境检测报告"""
    print("\n" + "=" * 60)
    print("🔍 三省六部协同开发系统 - 环境检测报告")
    print("=" * 60)
    print(f"⏰ 检查时间: {report.timestamp}")
    print(f"⏱️ 检查耗时: {report.duration_ms}ms")
    
    # 整体状态
    status_icons = {
        EnvStatus.HEALTHY: "✅",
        EnvStatus.WARNING: "⚠️",
        EnvStatus.UNHEALTHY: "❌",
        EnvStatus.ERROR: "💥",
        EnvStatus.UNKNOWN: "❓",
        EnvStatus.SKIPPED: "⏭️"
    }
    icon = status_icons.get(report.overall_status, "❓")
    print(f"📊 整体状态: {icon} {report.overall_status.value}")
    
    # 摘要
    summary = report.summary
    print(f"📈 服务统计: 总计 {summary.get('total', 0)}")
    print(f"   ✅ 健康: {summary.get('healthy', 0)}")
    print(f"   ⚠️ 警告: {summary.get('warning', 0)}")
    print(f"   ❌ 异常: {summary.get('unhealthy', 0)}")
    print(f"   ⏭️ 跳过: {summary.get('skipped', 0)}")
    print(f"   💥 错误: {summary.get('error', 0)}")
    
    print("-" * 60)
    
    # 服务详情
    print("🖥️ 服务状态:")
    for service in report.services:
        status_icon = status_icons.get(service.status, "❓")
        print(f"{status_icon} {service.name}: {service.message}")
        
        if service.response_time_ms:
            print(f"   响应时间: {service.response_time_ms}ms")
        
        if verbose and service.metadata:
            for key, value in service.metadata.items():
                if key not in ["password", "PASSWORD"]:
                    print(f"   {key}: {value}")
    
    # 依赖详情
    if report.dependencies:
        print("-" * 60)
        print("📦 依赖状态:")
        for dep in report.dependencies:
            icon = "✅" if dep.installed else "❌"
            print(f"{icon} {dep.name}: {dep.message}")
    
    # 环境变量
    if report.environment_variables and verbose:
        print("-" * 60)
        print("🔧 环境变量:")
        for key, value in report.environment_variables.items():
            print(f"   {key}: {value}")
    
    print("=" * 60)
    
    if report.overall_status == EnvStatus.HEALTHY:
        print("🎉 所有环境检测通过！")
    else:
        print("⚠️ 部分环境检测失败，请检查配置或启动相关服务")
    
    return report.overall_status == EnvStatus.HEALTHY


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="三省六部协同开发系统环境检测",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
环境变量配置:
  POSTGRES_HOST      PostgreSQL 主机地址 (默认: localhost)
  POSTGRES_PORT      PostgreSQL 端口 (默认: 5432)
  POSTGRES_DB        PostgreSQL 数据库名 (默认: skiller)
  POSTGRES_USER      PostgreSQL 用户名 (默认: postgres)
  POSTGRES_PASSWORD  PostgreSQL 密码
  
  REDIS_HOST         Redis 主机地址 (默认: localhost)
  REDIS_PORT         Redis 端口 (默认: 6379)
  REDIS_DB           Redis 数据库编号 (默认: 0)
  REDIS_PASSWORD     Redis 密码
  
  BACKEND_URL        后端 API 基础 URL (默认: http://localhost:8000)
  HEALTH_ENDPOINT    健康检查端点 (默认: /health)
  
  FRONTEND_HOST      前端服务主机 (默认: localhost)
  FRONTEND_PORT      前端服务端口 (默认: 5173)

示例:
  python check_environment.py                    # 运行检测
  python check_environment.py --json             # JSON 格式输出
  python check_environment.py --wait             # 等待服务就绪
  python check_environment.py --skip-docker      # 跳过 Docker 检测
  python check_environment.py --wait --wait-timeout 120  # 等待最长 120 秒
  python check_environment.py --deps             # 包含依赖检查
  python check_environment.py -v                 # 详细输出
        """
    )
    
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--wait", action="store_true", help="等待服务就绪")
    parser.add_argument("--wait-timeout", type=int, default=60, help="等待超时时间（秒），默认 60")
    parser.add_argument("--wait-interval", type=int, default=5, help="等待检查间隔（秒），默认 5")
    parser.add_argument("--skip-docker", action="store_true", help="跳过 Docker 检测")
    parser.add_argument("--backend-timeout", type=int, default=10, help="后端 API 检测超时时间（秒），默认 10")
    parser.add_argument("--frontend-port", type=int, default=5173, help="前端服务端口，默认 5173")
    parser.add_argument("--deps", action="store_true", help="检查依赖")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    checker = EnvironmentChecker(verbose=not args.json)
    
    if args.wait:
        report = checker.wait_for_services(
            max_wait=args.wait_timeout,
            interval=args.wait_interval,
            skip_docker=args.skip_docker,
            backend_timeout=args.backend_timeout,
            frontend_port=args.frontend_port
        )
    else:
        report = checker.run_environment_check(
            skip_docker=args.skip_docker,
            backend_timeout=args.backend_timeout,
            frontend_port=args.frontend_port,
            check_deps=args.deps
        )
    
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print_report(report, verbose=args.verbose)
    
    return 0 if report.overall_status == EnvStatus.HEALTHY else 1


if __name__ == "__main__":
    sys.exit(main())
