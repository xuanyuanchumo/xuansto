#!/usr/bin/env python3
"""
三省六部协同开发系统 - 健康检查脚本
检查所有服务的运行状态

功能：
- Docker 状态检查
- PostgreSQL 连接检查
- Redis 连接检查
- 后端 API 健康检查
- 前端服务状态检查
- Docker 容器健康检查
- 详细的状态报告生成
"""
import subprocess
import sys
import json
import time
import socket
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from skillscripts.core.path_config_center import get_path_config

# 项目路径配置
PROJECT_ROOT = get_path_config().SKILL_ROOT
SCRIPTS_DIR = Path(__file__).parent


class HealthStatus(Enum):
    """健康状态枚举"""
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
class HealthCheckResult:
    """健康检查结果数据类"""
    name: str
    status: HealthStatus
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
class HealthReport:
    """健康检查报告"""
    timestamp: str
    overall_status: HealthStatus
    services: List[HealthCheckResult]
    summary: Dict[str, int] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "services": [s.to_dict() for s in self.services],
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


class HealthChecker:
    """健康检查器"""
    
    def __init__(self, verbose: bool = True):
        self.logger = Logger(verbose=verbose)
        self.results: List[HealthCheckResult] = []
    
    def _create_result(
        self,
        name: str,
        status: HealthStatus,
        message: str,
        response_time_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> HealthCheckResult:
        """创建检查结果"""
        result = HealthCheckResult(
            name=name,
            status=status,
            message=message,
            response_time_ms=response_time_ms,
            metadata=metadata or {}
        )
        self.results.append(result)
        return result
    
    def _check_port(self, host: str, port: int, timeout: int = 5) -> tuple[bool, Optional[float]]:
        """
        检查端口是否可连接
        
        Returns:
            (是否成功, 响应时间ms)
        """
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
    
    def _http_get(self, url: str, timeout: int = 5) -> tuple[bool, Optional[int], Optional[float], Optional[str]]:
        """
        发送 HTTP GET 请求
        
        Returns:
            (是否成功, 状态码, 响应时间ms, 错误信息)
        """
        start_time = time.time()
        try:
            req = Request(url, method='GET')
            req.add_header('User-Agent', 'HealthChecker/1.0')
            
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
    
    def check_docker(self) -> HealthCheckResult:
        """检查 Docker 状态"""
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
                    status=HealthStatus.HEALTHY,
                    message="Docker 正在运行",
                    response_time_ms=response_time
                )
            else:
                return self._create_result(
                    name="Docker",
                    status=HealthStatus.UNHEALTHY,
                    message="Docker 未运行",
                    response_time_ms=response_time,
                    metadata={"stderr": proc.stderr[:200]}
                )
        except subprocess.TimeoutExpired:
            return self._create_result(
                name="Docker",
                status=HealthStatus.UNHEALTHY,
                message="Docker 检查超时"
            )
        except FileNotFoundError:
            return self._create_result(
                name="Docker",
                status=HealthStatus.UNHEALTHY,
                message="Docker 未安装"
            )
        except Exception as e:
            return self._create_result(
                name="Docker",
                status=HealthStatus.ERROR,
                message=f"Docker 检查失败: {str(e)}"
            )
    
    def check_postgresql(self, host: str = "localhost", port: int = 5432) -> HealthCheckResult:
        """检查 PostgreSQL 状态"""
        self.logger.info("检查 PostgreSQL 状态...")
        
        success, response_time = self._check_port(host, port, timeout=5)
        
        if success:
            return self._create_result(
                name="PostgreSQL",
                status=HealthStatus.HEALTHY,
                message=f"PostgreSQL 连接正常",
                response_time_ms=response_time,
                metadata={"host": host, "port": port}
            )
        else:
            return self._create_result(
                name="PostgreSQL",
                status=HealthStatus.UNHEALTHY,
                message=f"PostgreSQL 无法连接: {host}:{port}",
                metadata={"host": host, "port": port}
            )
    
    def check_redis(self, host: str = "localhost", port: int = 6379) -> HealthCheckResult:
        """检查 Redis 状态"""
        self.logger.info("检查 Redis 状态...")
        
        success, response_time = self._check_port(host, port, timeout=5)
        
        if success:
            return self._create_result(
                name="Redis",
                status=HealthStatus.HEALTHY,
                message=f"Redis 连接正常",
                response_time_ms=response_time,
                metadata={"host": host, "port": port}
            )
        else:
            return self._create_result(
                name="Redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis 无法连接: {host}:{port}",
                metadata={"host": host, "port": port}
            )
    
    def check_backend(self, url: str = "http://localhost:8000", timeout: int = 5) -> HealthCheckResult:
        """检查后端 API 状态"""
        self.logger.info("检查后端 API 状态...")
        
        health_url = f"{url.rstrip('/')}/health"
        success, status_code, response_time, error = self._http_get(health_url, timeout)
        
        if success and status_code == 200:
            return self._create_result(
                name="Backend API",
                status=HealthStatus.HEALTHY,
                message=f"后端 API 正常运行",
                response_time_ms=response_time,
                metadata={"url": health_url, "status_code": status_code}
            )
        elif success:
            return self._create_result(
                name="Backend API",
                status=HealthStatus.WARNING,
                message=f"后端 API 返回非预期状态码: {status_code}",
                response_time_ms=response_time,
                metadata={"url": health_url, "status_code": status_code}
            )
        else:
            return self._create_result(
                name="Backend API",
                status=HealthStatus.UNHEALTHY,
                message=f"后端 API 无法访问: {error}",
                metadata={"url": health_url, "error": error}
            )
    
    def check_frontend(self, host: str = "localhost", port: int = 5173) -> HealthCheckResult:
        """检查前端服务状态"""
        self.logger.info("检查前端服务状态...")
        
        success, response_time = self._check_port(host, port, timeout=5)
        
        if success:
            return self._create_result(
                name="Frontend",
                status=HealthStatus.HEALTHY,
                message=f"前端服务正常运行",
                response_time_ms=response_time,
                metadata={"host": host, "port": port, "url": f"http://{host}:{port}"}
            )
        else:
            return self._create_result(
                name="Frontend",
                status=HealthStatus.UNHEALTHY,
                message=f"前端服务无法访问: {host}:{port}",
                metadata={"host": host, "port": port}
            )
    
    def check_disk_space(self, threshold_percent: float = 90.0) -> HealthCheckResult:
        """检查磁盘空间"""
        self.logger.info("检查磁盘空间...")
        
        try:
            import shutil
            stat = shutil.disk_usage(PROJECT_ROOT)
            
            total_gb = stat.total / (1024**3)
            used_gb = stat.used / (1024**3)
            free_gb = stat.free / (1024**3)
            used_percent = (stat.used / stat.total) * 100
            
            metadata = {
                "total_gb": round(total_gb, 2),
                "used_gb": round(used_gb, 2),
                "free_gb": round(free_gb, 2),
                "used_percent": round(used_percent, 2)
            }
            
            if used_percent >= threshold_percent:
                return self._create_result(
                    name="Disk Space",
                    status=HealthStatus.WARNING,
                    message=f"磁盘空间不足: {used_percent:.1f}% 已使用",
                    metadata=metadata
                )
            else:
                return self._create_result(
                    name="Disk Space",
                    status=HealthStatus.HEALTHY,
                    message=f"磁盘空间充足: {used_percent:.1f}% 已使用",
                    metadata=metadata
                )
        except Exception as e:
            return self._create_result(
                name="Disk Space",
                status=HealthStatus.ERROR,
                message=f"磁盘空间检查失败: {str(e)}"
            )
    
    def check_memory(self, threshold_percent: float = 90.0) -> HealthCheckResult:
        """检查内存使用情况"""
        self.logger.info("检查内存使用情况...")
        
        try:
            import psutil
            memory = psutil.virtual_memory()
            
            metadata = {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_percent": memory.percent
            }
            
            if memory.percent >= threshold_percent:
                return self._create_result(
                    name="Memory",
                    status=HealthStatus.WARNING,
                    message=f"内存使用率较高: {memory.percent:.1f}%",
                    metadata=metadata
                )
            else:
                return self._create_result(
                    name="Memory",
                    status=HealthStatus.HEALTHY,
                    message=f"内存使用正常: {memory.percent:.1f}%",
                    metadata=metadata
                )
        except ImportError:
            return self._create_result(
                name="Memory",
                status=HealthStatus.SKIPPED,
                message="psutil 未安装，跳过内存检查",
                metadata={"install_hint": "pip install psutil"}
            )
        except Exception as e:
            return self._create_result(
                name="Memory",
                status=HealthStatus.ERROR,
                message=f"内存检查失败: {str(e)}"
            )
    
    def get_docker_manager(self):
        """获取 DockerManager 实例"""
        docker_manager_script = SCRIPTS_DIR / "docker_manager.py"
        if not docker_manager_script.exists():
            return None
        
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("docker_manager", docker_manager_script)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                return module.DockerManager(project_dir=PROJECT_ROOT, verbose=False)
        except Exception as e:
            self.logger.debug(f"导入 DockerManager 失败: {e}")
        return None
    
    def check_docker_containers(self, container_name: Optional[str] = None) -> HealthCheckResult:
        """检查 Docker 容器健康状态"""
        self.logger.info("检查 Docker 容器状态...")
        
        try:
            docker_manager = self.get_docker_manager()
            if docker_manager is None:
                return self._create_result(
                    name="Docker Containers",
                    status=HealthStatus.SKIPPED,
                    message="docker_manager.py 模块不可用"
                )
            
            health_result = docker_manager.get_container_health(container_name=container_name)
            
            if not health_result.get("success", False):
                return self._create_result(
                    name="Docker Containers",
                    status=HealthStatus.ERROR,
                    message=health_result.get("message", "获取容器状态失败")
                )
            
            containers = health_result.get("containers", [])
            overall_status = health_result.get("overall_status", "unknown")
            
            if not containers:
                return self._create_result(
                    name="Docker Containers",
                    status=HealthStatus.WARNING,
                    message="没有运行中的 Docker 容器",
                    metadata={"containers": []}
                )
            
            healthy_count = sum(1 for c in containers if c.get("health") in ("healthy", "no-healthcheck"))
            total_count = len(containers)
            
            if overall_status == "healthy":
                status = HealthStatus.HEALTHY
                message = f"所有容器健康 ({healthy_count}/{total_count})"
            else:
                status = HealthStatus.UNHEALTHY
                unhealthy = [c["name"] for c in containers if c.get("health") == "unhealthy" or c.get("state") != "running"]
                message = f"部分容器异常: {', '.join(unhealthy)}"
            
            return self._create_result(
                name="Docker Containers",
                status=status,
                message=message,
                metadata={
                    "containers": containers,
                    "healthy_count": healthy_count,
                    "total_count": total_count
                }
            )
            
        except Exception as e:
            return self._create_result(
                name="Docker Containers",
                status=HealthStatus.ERROR,
                message=f"Docker 容器检查失败: {str(e)}"
            )
    
    def check_docker_services(self) -> HealthCheckResult:
        """检查 Docker Compose 服务状态"""
        self.logger.info("检查 Docker Compose 服务状态...")
        
        try:
            docker_manager = self.get_docker_manager()
            if docker_manager is None:
                return self._create_result(
                    name="Docker Services",
                    status=HealthStatus.SKIPPED,
                    message="docker_manager.py 模块不可用"
                )
            
            status_result = docker_manager.get_status()
            
            if not status_result.get("success", False):
                return self._create_result(
                    name="Docker Services",
                    status=HealthStatus.ERROR,
                    message=status_result.get("message", "获取服务状态失败")
                )
            
            containers = status_result.get("containers", [])
            
            if not containers:
                return self._create_result(
                    name="Docker Services",
                    status=HealthStatus.WARNING,
                    message="没有运行中的 Docker 服务",
                    metadata={"services": []}
                )
            
            running_count = sum(1 for c in containers if c.get("state") == "running")
            total_count = len(containers)
            
            if running_count == total_count:
                status = HealthStatus.HEALTHY
                message = f"所有服务运行中 ({running_count}/{total_count})"
            else:
                status = HealthStatus.UNHEALTHY
                stopped = [c["service"] for c in containers if c.get("state") != "running"]
                message = f"部分服务停止: {', '.join(stopped)}"
            
            return self._create_result(
                name="Docker Services",
                status=status,
                message=message,
                metadata={
                    "services": containers,
                    "running_count": running_count,
                    "total_count": total_count
                }
            )
            
        except Exception as e:
            return self._create_result(
                name="Docker Services",
                status=HealthStatus.ERROR,
                message=f"Docker 服务检查失败: {str(e)}"
            )
    
    def run_health_check(
        self,
        include_docker_containers: bool = False,
        include_system: bool = False,
        container_name: Optional[str] = None,
        backend_url: str = "http://localhost:8000",
        frontend_port: int = 5173
    ) -> HealthReport:
        """运行完整健康检查"""
        start_time = time.time()
        self.results = []
        
        checks: List[Callable[[], HealthCheckResult]] = [
            self.check_docker,
            lambda: self.check_postgresql("localhost", 5432),
            lambda: self.check_redis("localhost", 6379),
            lambda: self.check_backend(backend_url),
            lambda: self.check_frontend("localhost", frontend_port)
        ]
        
        if include_docker_containers:
            checks.append(lambda: self.check_docker_containers(container_name))
            checks.append(self.check_docker_services)
        
        if include_system:
            checks.append(self.check_disk_space)
            checks.append(self.check_memory)
        
        for check in checks:
            try:
                check()
            except Exception as e:
                self.logger.error(f"健康检查项执行失败: {e}")
        
        # 计算整体状态
        overall_status = HealthStatus.HEALTHY
        for result in self.results:
            if result.status == HealthStatus.ERROR:
                overall_status = HealthStatus.ERROR
                break
            elif result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result.status == HealthStatus.WARNING and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.WARNING
        
        # 生成摘要
        summary = {
            "total": len(self.results),
            "healthy": sum(1 for r in self.results if r.status == HealthStatus.HEALTHY),
            "unhealthy": sum(1 for r in self.results if r.status == HealthStatus.UNHEALTHY),
            "warning": sum(1 for r in self.results if r.status == HealthStatus.WARNING),
            "skipped": sum(1 for r in self.results if r.status == HealthStatus.SKIPPED),
            "error": sum(1 for r in self.results if r.status == HealthStatus.ERROR)
        }
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        return HealthReport(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            overall_status=overall_status,
            services=self.results,
            summary=summary,
            duration_ms=duration_ms
        )
    
    def run_docker_health_check(self, container_name: Optional[str] = None) -> HealthReport:
        """运行 Docker 容器健康检查"""
        start_time = time.time()
        self.results = []
        
        # 检查 Docker
        docker_result = self.check_docker()
        
        if docker_result.status != HealthStatus.HEALTHY:
            duration_ms = round((time.time() - start_time) * 1000, 2)
            return HealthReport(
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                overall_status=HealthStatus.UNHEALTHY,
                services=self.results,
                duration_ms=duration_ms
            )
        
        # 检查容器
        containers_result = self.check_docker_containers(container_name)
        
        # 确定整体状态
        if containers_result.status == HealthStatus.HEALTHY:
            overall_status = HealthStatus.HEALTHY
        elif containers_result.status == HealthStatus.WARNING:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.UNHEALTHY
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        summary = {
            "total": len(self.results),
            "healthy": sum(1 for r in self.results if r.status == HealthStatus.HEALTHY),
            "unhealthy": sum(1 for r in self.results if r.status == HealthStatus.UNHEALTHY),
            "warning": sum(1 for r in self.results if r.status == HealthStatus.WARNING)
        }
        
        return HealthReport(
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            overall_status=overall_status,
            services=self.results,
            summary=summary,
            duration_ms=duration_ms
        )


def print_report(report: HealthReport, show_containers: bool = False, verbose: bool = False):
    """打印健康检查报告"""
    print("\n" + "=" * 60)
    print("🏥 三省六部协同开发系统 - 健康检查报告")
    print("=" * 60)
    print(f"⏰ 检查时间: {report.timestamp}")
    print(f"⏱️ 检查耗时: {report.duration_ms}ms")
    
    # 整体状态
    status_icons = {
        HealthStatus.HEALTHY: "✅",
        HealthStatus.WARNING: "⚠️",
        HealthStatus.UNHEALTHY: "❌",
        HealthStatus.ERROR: "💥",
        HealthStatus.UNKNOWN: "❓"
    }
    icon = status_icons.get(report.overall_status, "❓")
    print(f"📊 整体状态: {icon} {report.overall_status.value}")
    
    # 摘要
    summary = report.summary
    print(f"📈 检查项统计: 总计 {summary.get('total', 0)}")
    print(f"   ✅ 健康: {summary.get('healthy', 0)}")
    print(f"   ⚠️ 警告: {summary.get('warning', 0)}")
    print(f"   ❌ 异常: {summary.get('unhealthy', 0)}")
    print(f"   ⏭️ 跳过: {summary.get('skipped', 0)}")
    print(f"   💥 错误: {summary.get('error', 0)}")
    
    print("-" * 60)
    
    # 详细结果
    for service in report.services:
        status_icon = status_icons.get(service.status, "❓")
        print(f"{status_icon} {service.name}")
        print(f"   消息: {service.message}")
        
        if service.response_time_ms:
            print(f"   响应时间: {service.response_time_ms}ms")
        
        if verbose and service.metadata:
            for key, value in service.metadata.items():
                if key == "containers" and show_containers:
                    print(f"   🐳 容器 ({len(value)} 个):")
                    for container in value[:10]:  # 最多显示10个
                        c_status = container.get("state", "unknown")
                        c_health = container.get("health", "unknown")
                        c_icon = "💚" if c_health == "healthy" else ("💔" if c_health == "unhealthy" else "⚪")
                        print(f"      - {container.get('name', 'unknown')}: {c_status} {c_icon}")
                elif key != "containers":
                    print(f"   {key}: {value}")
        
        print()
    
    print("=" * 60)
    
    # 建议
    if report.overall_status == HealthStatus.HEALTHY:
        print("🎉 所有服务运行正常！")
    elif report.overall_status == HealthStatus.WARNING:
        print("⚠️ 部分服务有警告，请检查")
    elif report.overall_status == HealthStatus.ERROR:
        print("💥 检查过程中发生错误，请检查配置")
    else:
        print("❌ 部分服务异常，请检查日志或重启服务")
    
    print("=" * 60)
    
    return report.overall_status in (HealthStatus.HEALTHY, HealthStatus.WARNING)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="三省六部协同开发系统健康检查",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python health_check.py                    # 运行完整健康检查
  python health_check.py --json             # JSON 格式输出
  python health_check.py --docker           # 包含 Docker 容器检查
  python health_check.py --docker-only      # 仅检查 Docker 服务
  python health_check.py --docker -c postgres  # 检查指定容器
  python health_check.py --system           # 包含系统资源检查
  python health_check.py -v                 # 详细输出
        """
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--docker", action="store_true", help="包含 Docker 容器健康检查")
    parser.add_argument("--docker-only", action="store_true", help="仅检查 Docker 服务状态")
    parser.add_argument("--system", action="store_true", help="包含系统资源检查（磁盘、内存）")
    parser.add_argument("-c", "--container", type=str, help="指定检查的容器名称")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--backend-url", type=str, default="http://localhost:8000", help="后端 API URL")
    parser.add_argument("--frontend-port", type=int, default=5173, help="前端服务端口")
    
    args = parser.parse_args()
    
    checker = HealthChecker(verbose=not args.json)
    
    if args.docker_only:
        report = checker.run_docker_health_check(container_name=args.container)
    else:
        report = checker.run_health_check(
            include_docker_containers=args.docker,
            include_system=args.system,
            container_name=args.container,
            backend_url=args.backend_url,
            frontend_port=args.frontend_port
        )
    
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    else:
        print_report(report, show_containers=args.docker or args.docker_only, verbose=args.verbose)
    
    return 0 if report.overall_status in (HealthStatus.HEALTHY, HealthStatus.WARNING) else 1


if __name__ == "__main__":
    sys.exit(main())
