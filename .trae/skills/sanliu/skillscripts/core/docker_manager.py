#!/usr/bin/env python3
"""
三省六部协同开发系统 - Docker 管理脚本
管理 Docker Compose 服务的启动、停止、状态查询和健康检查

功能：
- 启动 Docker 服务
- 停止 Docker 服务
- 查看服务状态
- 容器健康检查
- 日志查看
- 容器重启
"""
import subprocess
import sys
import os
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

DEFAULT_PROJECT_DIR = Path(__file__).parent.parent


class DockerStatus(Enum):
    """Docker 状态枚举"""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    WARNING = "warning"
    ERROR = "error"
    RUNNING = "running"
    STOPPED = "stopped"


class LogLevel(Enum):
    """日志级别枚举"""
    INFO = "info"
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    PROGRESS = "progress"
    DEBUG = "debug"


@dataclass
class DockerOperationResult:
    """Docker 操作结果数据类"""
    success: bool
    message: str
    operation: str
    output: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class ContainerInfo:
    """容器信息数据类"""
    id: str
    name: str
    image: str
    state: str
    status: str
    health: str
    service: str = ""
    ports: str = ""
    created: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class DockerHealthReport:
    """Docker 健康报告"""
    timestamp: str
    overall_status: DockerStatus
    containers: List[ContainerInfo]
    summary: Dict[str, int] = field(default_factory=dict)
    message: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "containers": [c.to_dict() for c in self.containers],
            "summary": self.summary,
            "message": self.message
        }


class Logger:
    """日志记录器"""
    
    ICONS = {
        LogLevel.INFO: "ℹ️",
        LogLevel.SUCCESS: "✅",
        LogLevel.ERROR: "❌",
        LogLevel.WARNING: "⚠️",
        LogLevel.PROGRESS: "🔄",
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
        
        log_method = getattr(self.logger, level.value if level.value != "progress" else "info", self.logger.info)
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
    
    def progress(self, message: str):
        self.log(message, LogLevel.PROGRESS)


class DockerManager:
    """Docker 管理器"""
    
    def __init__(self, project_dir: Optional[Path] = None, verbose: bool = True):
        self.project_dir = project_dir or DEFAULT_PROJECT_DIR
        self.logger = Logger(verbose=verbose)
        self._compose_command: Optional[List[str]] = None
    
    def _run_command(
        self,
        command: List[str],
        cwd: Optional[Path] = None,
        timeout: int = 60,
        capture_output: bool = True
    ) -> tuple[bool, str, str, Optional[float]]:
        """
        运行命令
        
        Returns:
            (是否成功, stdout, stderr, 耗时ms)
        """
        start_time = time.time()
        work_dir = cwd or self.project_dir
        
        try:
            result = subprocess.run(
                command,
                cwd=str(work_dir),
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            
            duration = round((time.time() - start_time) * 1000, 2)
            
            return result.returncode == 0, result.stdout, result.stderr, duration
        except subprocess.TimeoutExpired:
            duration = round((time.time() - start_time) * 1000, 2)
            return False, "", "Command timeout", duration
        except Exception as e:
            duration = round((time.time() - start_time) * 1000, 2)
            return False, "", str(e), duration
    
    def _create_result(
        self,
        success: bool,
        operation: str,
        message: str,
        output: str = "",
        error: Optional[str] = None,
        duration_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> DockerOperationResult:
        """创建操作结果"""
        return DockerOperationResult(
            success=success,
            operation=operation,
            message=message,
            output=output,
            error=error,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
    
    def check_docker_available(self) -> bool:
        """检查 Docker 是否可用"""
        try:
            success, _, _, _ = self._run_command(["docker", "--version"], timeout=10)
            return success
        except Exception:
            return False
    
    def check_docker_compose_available(self) -> bool:
        """检查 Docker Compose 是否可用"""
        try:
            # 尝试 docker-compose
            success, _, _, _ = self._run_command(["docker-compose", "--version"], timeout=10)
            if success:
                return True
        except Exception:
            pass
        
        # 尝试 docker compose
        try:
            success, _, _, _ = self._run_command(["docker", "compose", "version"], timeout=10)
            return success
        except Exception:
            return False
    
    def get_compose_command(self) -> List[str]:
        """获取 Docker Compose 命令"""
        if self._compose_command is not None:
            return self._compose_command
        
        # 尝试 docker-compose
        try:
            success, _, _, _ = self._run_command(["docker-compose", "--version"], timeout=10)
            if success:
                self._compose_command = ["docker-compose"]
                return self._compose_command
        except Exception:
            pass
        
        # 尝试 docker compose
        self._compose_command = ["docker", "compose"]
        return self._compose_command
    
    def start_services(
        self,
        service_names: Optional[List[str]] = None,
        detached: bool = True,
        build: bool = False,
        no_deps: bool = False
    ) -> DockerOperationResult:
        """启动 Docker 服务"""
        operation = "start_services"
        self.logger.progress(f"启动 Docker 服务: {', '.join(service_names or ['all'])}")
        
        # 前置检查
        if not self.check_docker_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker 未安装或未运行"
            )
        
        if not self.check_docker_compose_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker Compose 未安装"
            )
        
        compose_file = self.project_dir / "docker-compose.yml"
        if not compose_file.exists():
            return self._create_result(
                success=False,
                operation=operation,
                message=f"docker-compose.yml 文件不存在: {compose_file}"
            )
        
        # 构建命令
        cmd = self.get_compose_command()
        cmd.extend(["up"])
        
        if detached:
            cmd.append("-d")
        
        if build:
            cmd.append("--build")
        
        if no_deps:
            cmd.append("--no-deps")
        
        if service_names:
            cmd.extend(service_names)
        
        # 执行命令
        success, stdout, stderr, duration = self._run_command(cmd, timeout=120)
        
        if success:
            return self._create_result(
                success=True,
                operation=operation,
                message="Docker 服务启动成功",
                output=stdout,
                duration_ms=duration,
                metadata={"services": service_names or ["all"]}
            )
        else:
            return self._create_result(
                success=False,
                operation=operation,
                message=f"Docker 服务启动失败: {stderr[:200]}",
                output=stdout,
                error=stderr,
                duration_ms=duration
            )
    
    def stop_services(
        self,
        service_names: Optional[List[str]] = None,
        remove_volumes: bool = False,
        remove_images: bool = False,
        timeout: int = 10
    ) -> DockerOperationResult:
        """停止 Docker 服务"""
        operation = "stop_services"
        self.logger.progress(f"停止 Docker 服务: {', '.join(service_names or ['all'])}")
        
        # 前置检查
        if not self.check_docker_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker 未安装或未运行"
            )
        
        if not self.check_docker_compose_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker Compose 未安装"
            )
        
        # 构建命令
        cmd = self.get_compose_command()
        cmd.extend(["down"])
        
        if remove_volumes:
            cmd.append("-v")
            self.logger.warning("将清理卷数据")
        
        if remove_images:
            cmd.extend(["--rmi", "all"])
        
        if timeout != 10:
            cmd.extend(["-t", str(timeout)])
        
        # 执行命令
        success, stdout, stderr, duration = self._run_command(cmd, timeout=60)
        
        if success:
            return self._create_result(
                success=True,
                operation=operation,
                message="Docker 服务停止成功",
                output=stdout,
                duration_ms=duration,
                metadata={"services": service_names or ["all"]}
            )
        else:
            return self._create_result(
                success=False,
                operation=operation,
                message=f"Docker 服务停止失败: {stderr[:200]}",
                output=stdout,
                error=stderr,
                duration_ms=duration
            )
    
    def restart_services(
        self,
        service_names: Optional[List[str]] = None,
        timeout: int = 10
    ) -> DockerOperationResult:
        """重启 Docker 服务"""
        operation = "restart_services"
        self.logger.progress(f"重启 Docker 服务: {', '.join(service_names or ['all'])}")
        
        # 前置检查
        if not self.check_docker_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker 未安装或未运行"
            )
        
        if not self.check_docker_compose_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker Compose 未安装"
            )
        
        # 构建命令
        cmd = self.get_compose_command()
        cmd.extend(["restart"])
        
        if timeout != 10:
            cmd.extend(["-t", str(timeout)])
        
        if service_names:
            cmd.extend(service_names)
        
        # 执行命令
        success, stdout, stderr, duration = self._run_command(cmd, timeout=60)
        
        if success:
            return self._create_result(
                success=True,
                operation=operation,
                message="Docker 服务重启成功",
                output=stdout,
                duration_ms=duration,
                metadata={"services": service_names or ["all"]}
            )
        else:
            return self._create_result(
                success=False,
                operation=operation,
                message=f"Docker 服务重启失败: {stderr[:200]}",
                output=stdout,
                error=stderr,
                duration_ms=duration
            )
    
    def get_logs(
        self,
        service_names: Optional[List[str]] = None,
        tail: Optional[int] = None,
        follow: bool = False,
        since: Optional[str] = None
    ) -> DockerOperationResult:
        """获取服务日志"""
        operation = "get_logs"
        
        # 前置检查
        if not self.check_docker_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker 未安装或未运行"
            )
        
        if not self.check_docker_compose_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker Compose 未安装"
            )
        
        # 构建命令
        cmd = self.get_compose_command()
        cmd.extend(["logs"])
        
        if tail:
            cmd.extend(["--tail", str(tail)])
        
        if follow:
            cmd.append("-f")
        
        if since:
            cmd.extend(["--since", since])
        
        if service_names:
            cmd.extend(service_names)
        
        # 执行命令
        if follow:
            # 对于跟随模式，直接运行不捕获输出
            try:
                subprocess.run(cmd, cwd=str(self.project_dir))
                return self._create_result(
                    success=True,
                    operation=operation,
                    message="日志查看结束"
                )
            except Exception as e:
                return self._create_result(
                    success=False,
                    operation=operation,
                    message=f"查看日志失败: {str(e)}"
                )
        else:
            success, stdout, stderr, duration = self._run_command(cmd, timeout=30)
            
            if success:
                return self._create_result(
                    success=True,
                    operation=operation,
                    message="获取日志成功",
                    output=stdout,
                    duration_ms=duration
                )
            else:
                return self._create_result(
                    success=False,
                    operation=operation,
                    message=f"获取日志失败: {stderr[:200]}",
                    error=stderr,
                    duration_ms=duration
                )
    
    def get_status(self) -> DockerOperationResult:
        """获取服务状态"""
        operation = "get_status"
        
        # 前置检查
        if not self.check_docker_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker 未安装或未运行"
            )
        
        if not self.check_docker_compose_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker Compose 未安装"
            )
        
        cmd = self.get_compose_command()
        cmd.extend(["ps", "--format", "json"])
        
        success, stdout, stderr, duration = self._run_command(cmd, timeout=30)
        
        if not success:
            return self._create_result(
                success=False,
                operation=operation,
                message=f"获取容器状态失败: {stderr}",
                error=stderr,
                duration_ms=duration
            )
        
        containers = []
        output = stdout.strip()
        
        if output:
            try:
                if output.startswith("["):
                    containers_raw = json.loads(output)
                else:
                    containers_raw = [json.loads(line) for line in output.split("\n") if line.strip()]
                
                for container in containers_raw:
                    container_info = ContainerInfo(
                        id=container.get("ID", container.get("Id", ""))[:12],
                        name=container.get("Name", container.get("name", "")),
                        service=container.get("Service", container.get("service", "")),
                        image=container.get("Image", container.get("image", "")),
                        state=container.get("State", container.get("state", "")),
                        status=container.get("Status", container.get("status", "")),
                        health=container.get("Health", container.get("health", "unknown")),
                        ports=str(container.get("Publishers", container.get("ports", "")))
                    )
                    containers.append(container_info)
            except json.JSONDecodeError as e:
                return self._create_result(
                    success=False,
                    operation=operation,
                    message=f"解析容器信息失败: {str(e)}",
                    error=str(e),
                    duration_ms=duration
                )
        
        return self._create_result(
            success=True,
            operation=operation,
            message=f"获取到 {len(containers)} 个容器状态",
            output=stdout,
            duration_ms=duration,
            metadata={"containers": [c.to_dict() for c in containers]}
        )
    
    def get_container_health(self, container_name: Optional[str] = None) -> DockerOperationResult:
        """获取容器健康状态"""
        operation = "get_container_health"
        
        # 前置检查
        if not self.check_docker_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker 未安装或未运行"
            )
        
        cmd = ["docker", "ps", "--format", "json"]
        if container_name:
            cmd.extend(["--filter", f"name={container_name}"])
        
        success, stdout, stderr, duration = self._run_command(cmd, timeout=30)
        
        if not success:
            return self._create_result(
                success=False,
                operation=operation,
                message=f"获取容器列表失败: {stderr}",
                error=stderr,
                duration_ms=duration
            )
        
        output = stdout.strip()
        
        if not output:
            return self._create_result(
                success=True,
                operation=operation,
                message="没有运行中的容器",
                duration_ms=duration,
                metadata={"containers": [], "overall_status": "unhealthy"}
            )
        
        containers_raw = []
        try:
            if output.startswith("["):
                containers_raw = json.loads(output)
            else:
                containers_raw = [json.loads(line) for line in output.split("\n") if line.strip()]
        except json.JSONDecodeError as e:
            return self._create_result(
                success=False,
                operation=operation,
                message=f"解析容器信息失败: {str(e)}",
                error=str(e),
                duration_ms=duration
            )
        
        containers = []
        all_healthy = True
        
        for container in containers_raw:
            container_id = container.get("ID", container.get("Id", ""))
            container_info = ContainerInfo(
                id=container_id[:12] if container_id else "",
                name=container.get("Names", container.get("names", "")),
                image=container.get("Image", container.get("image", "")),
                state=container.get("State", container.get("state", "")),
                status=container.get("Status", container.get("status", "")),
                health="unknown"
            )
            
            # 获取健康检查状态
            inspect_cmd = ["docker", "inspect", "--format", "{{.State.Health.Status}}", container_id]
            inspect_success, inspect_stdout, _, _ = self._run_command(inspect_cmd, timeout=10)
            
            if inspect_success:
                health_status = inspect_stdout.strip()
                if health_status:
                    container_info.health = health_status
                else:
                    container_info.health = "no-healthcheck"
            
            if container_info.state != "running":
                all_healthy = False
            
            if container_info.health == "unhealthy":
                all_healthy = False
            
            containers.append(container_info)
        
        overall_status = "healthy" if all_healthy else "unhealthy"
        
        return self._create_result(
            success=True,
            operation=operation,
            message=f"检查了 {len(containers)} 个容器",
            duration_ms=duration,
            metadata={
                "containers": [c.to_dict() for c in containers],
                "overall_status": overall_status
            }
        )
    
    def build_services(
        self,
        service_names: Optional[List[str]] = None,
        no_cache: bool = False,
        pull: bool = False
    ) -> DockerOperationResult:
        """构建服务镜像"""
        operation = "build_services"
        self.logger.progress(f"构建 Docker 镜像: {', '.join(service_names or ['all'])}")
        
        # 前置检查
        if not self.check_docker_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker 未安装或未运行"
            )
        
        if not self.check_docker_compose_available():
            return self._create_result(
                success=False,
                operation=operation,
                message="Docker Compose 未安装"
            )
        
        cmd = self.get_compose_command()
        cmd.extend(["build"])
        
        if no_cache:
            cmd.append("--no-cache")
        
        if pull:
            cmd.append("--pull")
        
        if service_names:
            cmd.extend(service_names)
        
        success, stdout, stderr, duration = self._run_command(cmd, timeout=300)
        
        if success:
            return self._create_result(
                success=True,
                operation=operation,
                message="镜像构建成功",
                output=stdout,
                duration_ms=duration
            )
        else:
            return self._create_result(
                success=False,
                operation=operation,
                message=f"镜像构建失败: {stderr[:200]}",
                output=stdout,
                error=stderr,
                duration_ms=duration
            )
    
    def print_status_report(self, result: DockerOperationResult):
        """打印状态报告"""
        print("\n" + "=" * 60)
        print("🐳 Docker 服务状态")
        print("=" * 60)
        print(f"⏰ 检查时间: {result.timestamp}")
        
        if not result.success:
            print(f"❌ {result.message}")
            return
        
        metadata = result.metadata or {}
        containers = metadata.get("containers", [])
        
        if not containers:
            print("ℹ️ 没有运行中的容器")
            return
        
        print("-" * 60)
        
        for container in containers:
            state_icon = "✅" if container.get("state") == "running" else "❌"
            health = container.get("health", "unknown")
            
            if health == "healthy":
                health_icon = "💚"
            elif health == "unhealthy":
                health_icon = "💔"
            elif health == "no-healthcheck":
                health_icon = "⚪"
            else:
                health_icon = "❓"
            
            print(f"{state_icon} {container.get('name', 'unknown')}")
            print(f"   服务: {container.get('service', 'N/A')}")
            print(f"   镜像: {container.get('image', 'N/A')}")
            print(f"   状态: {container.get('state', 'unknown')} {health_icon} {health}")
            print(f"   详情: {container.get('status', 'unknown')}")
            print()
        
        print("=" * 60)
    
    def print_health_report(self, result: DockerOperationResult):
        """打印健康报告"""
        print("\n" + "=" * 60)
        print("🏥 Docker 容器健康检查报告")
        print("=" * 60)
        print(f"⏰ 检查时间: {result.timestamp}")
        
        metadata = result.metadata or {}
        overall_status = metadata.get("overall_status", "unknown")
        
        status_icon = "✅" if overall_status == "healthy" else "❌"
        print(f"📊 整体状态: {status_icon} {overall_status}")
        
        if not result.success:
            print(f"❌ {result.message}")
            return
        
        containers = metadata.get("containers", [])
        
        if not containers:
            print("ℹ️ 没有运行中的容器")
            return
        
        print("-" * 60)
        
        for container in containers:
            state_icon = "✅" if container.get("state") == "running" else "❌"
            health = container.get("health", "unknown")
            
            if health == "healthy":
                health_icon = "💚"
            elif health == "unhealthy":
                health_icon = "💔"
            elif health == "no-healthcheck":
                health_icon = "⚪"
            else:
                health_icon = "❓"
            
            print(f"{state_icon} {container.get('name', 'unknown')}")
            print(f"   镜像: {container.get('image', 'N/A')}")
            print(f"   状态: {container.get('state', 'unknown')} {health_icon} {health}")
            print(f"   详情: {container.get('status', 'unknown')}")
            print()
        
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Docker 服务管理脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python docker_manager.py start                    # 启动所有服务（后台运行）
  python docker_manager.py start -s postgres redis  # 启动指定服务
  python docker_manager.py start --build            # 启动并重新构建
  python docker_manager.py stop                     # 停止所有服务
  python docker_manager.py stop -v                  # 停止并清理卷数据
  python docker_manager.py restart                  # 重启所有服务
  python docker_manager.py status                   # 查看服务状态
  python docker_manager.py status --json            # JSON 格式输出状态
  python docker_manager.py health                   # 健康检查
  python docker_manager.py health -c postgres       # 检查指定容器
  python docker_manager.py logs                     # 查看日志
  python docker_manager.py logs -f                  # 实时查看日志
  python docker_manager.py build                    # 构建镜像
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="可用命令")
    
    # start 命令
    start_parser = subparsers.add_parser("start", help="启动 Docker 服务")
    start_parser.add_argument("-s", "--services", nargs="+", help="指定服务名称")
    start_parser.add_argument("-d", "--detached", action="store_true", default=True, help="后台运行模式（默认）")
    start_parser.add_argument("--foreground", action="store_true", help="前台运行模式")
    start_parser.add_argument("--build", action="store_true", help="启动前重新构建镜像")
    start_parser.add_argument("--no-deps", action="store_true", help="不启动依赖服务")
    
    # stop 命令
    stop_parser = subparsers.add_parser("stop", help="停止 Docker 服务")
    stop_parser.add_argument("-s", "--services", nargs="+", help="指定服务名称")
    stop_parser.add_argument("-v", "--volumes", action="store_true", help="清理卷数据")
    stop_parser.add_argument("--rmi", action="store_true", help="删除镜像")
    stop_parser.add_argument("-t", "--timeout", type=int, default=10, help="停止超时时间")
    
    # restart 命令
    restart_parser = subparsers.add_parser("restart", help="重启 Docker 服务")
    restart_parser.add_argument("-s", "--services", nargs="+", help="指定服务名称")
    restart_parser.add_argument("-t", "--timeout", type=int, default=10, help="重启超时时间")
    
    # status 命令
    status_parser = subparsers.add_parser("status", help="查询服务状态")
    status_parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    
    # health 命令
    health_parser = subparsers.add_parser("health", help="容器健康检查")
    health_parser.add_argument("-c", "--container", help="指定容器名称")
    health_parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    
    # logs 命令
    logs_parser = subparsers.add_parser("logs", help="查看服务日志")
    logs_parser.add_argument("-s", "--services", nargs="+", help="指定服务名称")
    logs_parser.add_argument("-f", "--follow", action="store_true", help="实时跟踪日志")
    logs_parser.add_argument("-n", "--tail", type=int, help="显示最后 N 行")
    logs_parser.add_argument("--since", help="显示自某个时间以来的日志")
    
    # build 命令
    build_parser = subparsers.add_parser("build", help="构建服务镜像")
    build_parser.add_argument("-s", "--services", nargs="+", help="指定服务名称")
    build_parser.add_argument("--no-cache", action="store_true", help="不使用缓存")
    build_parser.add_argument("--pull", action="store_true", help="总是拉取最新基础镜像")
    
    # 全局参数
    parser.add_argument("--project-dir", type=str, help="指定项目目录")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    project_dir = Path(args.project_dir) if args.project_dir else DEFAULT_PROJECT_DIR
    manager = DockerManager(project_dir=project_dir, verbose=not args.quiet)
    
    result: Optional[DockerOperationResult] = None
    
    if args.command == "start":
        detached = not args.foreground
        result = manager.start_services(
            service_names=args.services,
            detached=detached,
            build=args.build,
            no_deps=args.no_deps
        )
        
        if not args.quiet and not args.json:
            if result.success:
                manager.logger.success(result.message)
            else:
                manager.logger.error(result.message)
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        
        return 0 if result.success else 1
    
    elif args.command == "stop":
        result = manager.stop_services(
            service_names=args.services,
            remove_volumes=args.volumes,
            remove_images=args.rmi,
            timeout=args.timeout
        )
        
        if not args.quiet and not args.json:
            if result.success:
                manager.logger.success(result.message)
            else:
                manager.logger.error(result.message)
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        
        return 0 if result.success else 1
    
    elif args.command == "restart":
        result = manager.restart_services(
            service_names=args.services,
            timeout=args.timeout
        )
        
        if not args.quiet and not args.json:
            if result.success:
                manager.logger.success(result.message)
            else:
                manager.logger.error(result.message)
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        
        return 0 if result.success else 1
    
    elif args.command == "status":
        result = manager.get_status()
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            manager.print_status_report(result)
        
        return 0 if result.success else 1
    
    elif args.command == "health":
        result = manager.get_container_health(container_name=args.container)
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            manager.print_health_report(result)
        
        metadata = result.metadata or {}
        overall_status = metadata.get("overall_status", "unhealthy")
        return 0 if overall_status == "healthy" else 1
    
    elif args.command == "logs":
        result = manager.get_logs(
            service_names=args.services,
            tail=args.tail,
            follow=args.follow,
            since=args.since
        )
        
        if not args.follow:
            if args.json:
                print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
            elif not args.quiet:
                if result.output:
                    print(result.output)
        
        return 0 if result.success else 1
    
    elif args.command == "build":
        result = manager.build_services(
            service_names=args.services,
            no_cache=args.no_cache,
            pull=args.pull
        )
        
        if not args.quiet and not args.json:
            if result.success:
                manager.logger.success(result.message)
            else:
                manager.logger.error(result.message)
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        
        return 0 if result.success else 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
