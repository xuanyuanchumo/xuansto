#!/usr/bin/env python3
"""
三省六部协同开发系统 - 服务启动脚本
启动所有必要的服务

功能：
- 启动 Docker 服务（PostgreSQL、Redis）
- 启动后端 API 服务
- 启动前端开发服务器
- 环境检测和依赖检查
- 服务状态诊断
"""
import subprocess
import sys
import os
import time
import socket
import argparse
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

from skillscripts.utils.script_utils import (
    ScriptBase, ScriptResult, ScriptLogger, ExitCode, create_result
)
from skillscripts.core.path_config_center import get_path_config

# 项目路径配置
PROJECT_ROOT = get_path_config().SKILL_ROOT
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
SCRIPTS_DIR = Path(__file__).parent
LOGS_DIR = PROJECT_ROOT / "logs"

# 服务端口配置
SERVICE_PORTS = {
    "postgresql": 5432,
    "redis": 6379,
    "backend": 8000,
    "frontend": 5173
}


class ServiceStatus(Enum):
    """服务状态枚举"""
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    WARNING = "warning"
    SKIPPED = "skipped"
    STARTING = "starting"
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
class ServiceResult:
    """服务操作结果数据类"""
    name: str
    status: ServiceStatus
    message: str
    success: bool = False
    error_details: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> Optional[float]:
        """获取操作持续时间"""
        if self.start_time and self.end_time:
            return round(self.end_time - self.start_time, 2)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = asdict(self)
        result['status'] = self.status.value
        result['duration'] = self.duration
        return result


@dataclass
class StartServicesResult:
    """启动服务整体结果"""
    timestamp: str
    overall_status: ServiceStatus
    services: List[ServiceResult]
    started_services: List[str] = field(default_factory=list)
    failed_services: List[str] = field(default_factory=list)
    skipped_services: List[str] = field(default_factory=list)
    total_duration: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "services": [s.to_dict() for s in self.services],
            "started_services": self.started_services,
            "failed_services": self.failed_services,
            "skipped_services": self.skipped_services,
            "total_duration": self.total_duration
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
    
    def __init__(self, verbose: bool = True, log_file: Optional[Path] = None):
        self.verbose = verbose
        self.log_file = log_file
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志配置"""
        if self.log_file:
            LOGS_DIR.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(
                level=logging.DEBUG,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.log_file, encoding='utf-8'),
                    logging.StreamHandler(sys.stdout) if self.verbose else logging.NullHandler()
                ]
            )
        else:
            logging.basicConfig(
                level=logging.DEBUG if self.verbose else logging.WARNING,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[logging.StreamHandler(sys.stdout)]
            )
        self.logger = logging.getLogger(__name__)
    
    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        """记录日志"""
        icon = self.ICONS.get(level, "")
        formatted_message = f"{icon} {message}"
        
        if self.verbose:
            print(formatted_message)
        
        # 同时记录到 Python logging
        log_method = getattr(self.logger, level.value if level.value != "progress" else "info", self.logger.info)
        log_method(message)
    
    def debug(self, message: str):
        """调试日志"""
        self.log(message, LogLevel.DEBUG)
    
    def info(self, message: str):
        """信息日志"""
        self.log(message, LogLevel.INFO)
    
    def success(self, message: str):
        """成功日志"""
        self.log(message, LogLevel.SUCCESS)
    
    def error(self, message: str):
        """错误日志"""
        self.log(message, LogLevel.ERROR)
    
    def warning(self, message: str):
        """警告日志"""
        self.log(message, LogLevel.WARNING)
    
    def progress(self, message: str):
        """进度日志"""
        self.log(message, LogLevel.PROGRESS)


class ServiceManager:
    """服务管理器"""
    
    def __init__(self, verbose: bool = True, log_file: Optional[Path] = None):
        self.logger = Logger(verbose=verbose, log_file=log_file)
        self.started_services: List[str] = []
        self.failed_services: List[str] = []
        self.skipped_services: List[str] = []
        self.service_results: List[ServiceResult] = []
    
    def _create_result(
        self,
        name: str,
        status: ServiceStatus,
        message: str,
        success: bool = False,
        error_details: Optional[str] = None,
        start_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ServiceResult:
        """创建服务结果对象"""
        result = ServiceResult(
            name=name,
            status=status,
            message=message,
            success=success,
            error_details=error_details,
            start_time=start_time,
            end_time=time.time(),
            metadata=metadata or {}
        )
        self.service_results.append(result)
        return result
    
    def check_command_exists(self, command: str) -> bool:
        """检查命令是否存在"""
        try:
            if os.name == 'nt':
                result = subprocess.run(
                    ["where", command],
                    capture_output=True,
                    timeout=10
                )
            else:
                result = subprocess.run(
                    ["which", command],
                    capture_output=True,
                    timeout=10
                )
            return result.returncode == 0
        except Exception as e:
            self.logger.debug(f"检查命令 {command} 存在性失败: {e}")
            return False
    
    def check_port_available(self, port: int) -> bool:
        """检查端口是否可用"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            return result != 0
        except Exception as e:
            self.logger.debug(f"检查端口 {port} 可用性失败: {e}")
            return True
    
    def wait_for_port(
        self,
        port: int,
        timeout: int = 30,
        service_name: str = "",
        expected_state: str = "open"
    ) -> bool:
        """
        等待端口达到预期状态
        
        Args:
            port: 端口号
            timeout: 超时时间（秒）
            service_name: 服务名称（用于日志）
            expected_state: 预期状态 ('open' 或 'closed')
        
        Returns:
            是否达到预期状态
        """
        start_time = time.time()
        check_count = 0
        
        while time.time() - start_time < timeout:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                
                is_open = result == 0
                
                if expected_state == "open" and is_open:
                    return True
                elif expected_state == "closed" and not is_open:
                    return True
                
            except Exception as e:
                self.logger.debug(f"等待端口 {port} 时发生异常: {e}")
            
            check_count += 1
            time.sleep(1)
            
            if self.logger.verbose and service_name and check_count % 5 == 0:
                elapsed = int(time.time() - start_time)
                self.logger.progress(f"等待 {service_name} 启动... ({elapsed}s/{timeout}s)")
        
        return False
    
    def check_dependencies(self) -> Dict[str, bool]:
        """检查依赖项"""
        self.logger.info("检查依赖项...")
        
        dependencies = {
            "docker": self.check_command_exists("docker"),
            "python": self.check_command_exists("python"),
            "node": self.check_command_exists("node"),
            "npm": self.check_command_exists("npm")
        }
        
        for name, exists in dependencies.items():
            if exists:
                self.logger.success(f"{name} 已安装")
            else:
                self.logger.error(f"{name} 未安装")
        
        return dependencies
    
    def run_environment_check(
        self,
        skip_docker: bool = False,
        json_output: bool = False
    ) -> Dict[str, Any]:
        """运行环境检测"""
        self.logger.progress("运行环境检测...")
        
        check_env_script = SCRIPTS_DIR / "check_environment.py"
        if not check_env_script.exists():
            self.logger.warning("check_environment.py 脚本不存在，跳过环境检测")
            return {"overall_status": "skipped", "services": []}
        
        start_time = time.time()
        
        try:
            cmd = [sys.executable, str(check_env_script), "--json"]
            if skip_docker:
                cmd.append("--skip-docker")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0 and result.stdout:
                try:
                    env_result = json.loads(result.stdout)
                    
                    if not json_output:
                        for service in env_result.get("services", []):
                            status = service.get("status", "unknown")
                            if status == "healthy":
                                self.logger.success(f"{service['name']}: {service['message']}")
                            elif status == "skipped":
                                self.logger.warning(f"{service['name']}: {service['message']}")
                            else:
                                self.logger.error(f"{service['name']}: {service['message']}")
                    
                    env_result["duration"] = round(time.time() - start_time, 2)
                    return env_result
                    
                except json.JSONDecodeError as e:
                    error_msg = f"环境检测结果解析失败: {str(e)}"
                    self.logger.error(error_msg)
                    return {
                        "overall_status": "error",
                        "services": [],
                        "error": error_msg,
                        "raw_output": result.stdout[:500]
                    }
            else:
                error_msg = f"环境检测执行失败: {result.stderr}"
                self.logger.error(error_msg)
                return {"overall_status": "error", "services": [], "error": error_msg}
                
        except subprocess.TimeoutExpired:
            error_msg = "环境检测超时"
            self.logger.error(error_msg)
            return {"overall_status": "error", "services": [], "error": error_msg}
        except Exception as e:
            error_msg = f"环境检测异常: {str(e)}"
            self.logger.error(error_msg)
            return {"overall_status": "error", "services": [], "error": error_msg}
    
    def wait_for_environment(
        self,
        timeout: int = 60,
        skip_docker: bool = False
    ) -> bool:
        """等待环境就绪"""
        self.logger.progress(f"等待环境就绪 (最长等待: {timeout}s)...")
        
        check_env_script = SCRIPTS_DIR / "check_environment.py"
        if not check_env_script.exists():
            self.logger.warning("check_environment.py 脚本不存在，跳过等待")
            return True
        
        try:
            cmd = [
                sys.executable, str(check_env_script),
                "--wait", "--wait-timeout", str(timeout), "--json"
            ]
            if skip_docker:
                cmd.append("--skip-docker")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout + 10
            )
            
            if result.returncode == 0 and result.stdout:
                try:
                    env_result = json.loads(result.stdout)
                    if env_result.get("overall_status") == "healthy":
                        self.logger.success("环境已就绪")
                        return True
                    else:
                        unhealthy = [
                            s["name"] for s in env_result.get("services", [])
                            if s["status"] not in ("healthy", "skipped")
                        ]
                        self.logger.error(f"部分服务未就绪: {', '.join(unhealthy)}")
                        return False
                except json.JSONDecodeError:
                    self.logger.error("环境检测结果解析失败")
                    return False
            else:
                self.logger.error("等待环境超时或失败")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("等待环境超时")
            return False
        except Exception as e:
            self.logger.error(f"等待环境异常: {str(e)}")
            return False
    
    def diagnose_failure(self, service_name: str, error_details: str = "") -> str:
        """诊断服务启动失败原因"""
        diagnosis = []
        diagnosis.append(f"\n{'='*60}")
        diagnosis.append(f"🔍 服务 '{service_name}' 启动失败诊断")
        diagnosis.append("=" * 60)
        
        if service_name == "Docker Services":
            diagnosis.extend([
                "可能的原因:",
                "  1. Docker 未安装或未启动",
                "  2. docker-compose.yml 配置错误",
                "  3. 端口 5432 (PostgreSQL) 或 6379 (Redis) 被占用",
                "\n建议操作:",
                "  - 检查 Docker Desktop 是否运行: docker info",
                "  - 检查端口占用: netstat -ano | findstr '5432 6379'",
                "  - 查看 Docker 日志: docker-compose logs"
            ])
            
        elif service_name == "Backend API":
            diagnosis.extend([
                "可能的原因:",
                "  1. Python 依赖未安装",
                "  2. 数据库连接失败",
                "  3. 端口 8000 被占用",
                "  4. 配置文件错误",
                "\n建议操作:",
                "  - 检查依赖: pip install -r requirements.txt",
                "  - 检查端口: netstat -ano | findstr '8000'",
                "  - 手动启动测试: cd backend && python run.py"
            ])
            
        elif service_name == "Frontend":
            diagnosis.extend([
                "可能的原因:",
                "  1. Node.js 依赖未安装",
                "  2. 端口 5173 被占用",
                "  3. package.json 配置错误",
                "\n建议操作:",
                "  - 安装依赖: cd frontend && npm install",
                "  - 检查端口: netstat -ano | findstr '5173'",
                "  - 手动启动测试: cd frontend && npm run dev"
            ])
        
        if error_details:
            diagnosis.append(f"\n错误详情: {error_details}")
        
        diagnosis.append("=" * 60)
        return "\n".join(diagnosis)
    
    def start_docker_services(self) -> ServiceResult:
        """启动 Docker 服务"""
        start_time = time.time()
        self.logger.info("启动 Docker 服务 (PostgreSQL, Redis)...")
        
        docker_compose_file = PROJECT_ROOT / "docker-compose.yml"
        if not docker_compose_file.exists():
            error_msg = "docker-compose.yml 文件不存在"
            self.logger.error(error_msg)
            return self._create_result(
                name="Docker Services",
                status=ServiceStatus.UNHEALTHY,
                message=error_msg,
                error_details=error_msg,
                start_time=start_time
            )
        
        try:
            result = subprocess.run(
                ["docker-compose", "up", "-d"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                error_msg = f"Docker 服务启动失败: {result.stderr}"
                self.logger.error(error_msg)
                return self._create_result(
                    name="Docker Services",
                    status=ServiceStatus.UNHEALTHY,
                    message="Docker 服务启动失败",
                    error_details=result.stderr,
                    start_time=start_time
                )
            
            # 等待 PostgreSQL
            self.logger.progress("等待 PostgreSQL 启动...")
            pg_ready = self.wait_for_port(
                SERVICE_PORTS["postgresql"],
                timeout=30,
                service_name="PostgreSQL"
            )
            
            # 等待 Redis
            self.logger.progress("等待 Redis 启动...")
            redis_ready = self.wait_for_port(
                SERVICE_PORTS["redis"],
                timeout=30,
                service_name="Redis"
            )
            
            if pg_ready and redis_ready:
                self.logger.success("Docker 服务启动成功")
                return self._create_result(
                    name="Docker Services",
                    status=ServiceStatus.HEALTHY,
                    message="Docker 服务启动成功",
                    success=True,
                    start_time=start_time,
                    metadata={"postgresql_ready": pg_ready, "redis_ready": redis_ready}
                )
            else:
                errors = []
                if not pg_ready:
                    errors.append("PostgreSQL 启动超时")
                    self.logger.error("PostgreSQL 启动超时")
                if not redis_ready:
                    errors.append("Redis 启动超时")
                    self.logger.error("Redis 启动超时")
                
                return self._create_result(
                    name="Docker Services",
                    status=ServiceStatus.UNHEALTHY,
                    message="; ".join(errors),
                    error_details="; ".join(errors),
                    start_time=start_time
                )
                
        except subprocess.TimeoutExpired:
            error_msg = "Docker 服务启动超时"
            self.logger.error(error_msg)
            return self._create_result(
                name="Docker Services",
                status=ServiceStatus.UNHEALTHY,
                message=error_msg,
                error_details=error_msg,
                start_time=start_time
            )
        except Exception as e:
            error_msg = f"Docker 服务启动异常: {str(e)}"
            self.logger.error(error_msg)
            return self._create_result(
                name="Docker Services",
                status=ServiceStatus.UNHEALTHY,
                message=error_msg,
                error_details=str(e),
                start_time=start_time
            )
    
    def start_backend(self) -> ServiceResult:
        """启动后端 API 服务"""
        start_time = time.time()
        self.logger.info("启动后端 API 服务...")
        
        # 检查端口是否已被占用
        if not self.check_port_available(SERVICE_PORTS["backend"]):
            warning_msg = f"端口 {SERVICE_PORTS['backend']} 已被占用，后端服务可能已在运行"
            self.logger.warning(warning_msg)
            return self._create_result(
                name="Backend API",
                status=ServiceStatus.WARNING,
                message=warning_msg,
                success=True,
                start_time=start_time,
                metadata={"port_already_in_use": True}
            )
        
        run_py = BACKEND_DIR / "run.py"
        if not run_py.exists():
            error_msg = "run.py 文件不存在"
            self.logger.error(error_msg)
            return self._create_result(
                name="Backend API",
                status=ServiceStatus.UNHEALTHY,
                message=error_msg,
                error_details=error_msg,
                start_time=start_time
            )
        
        try:
            # 启动后端进程
            if os.name == 'nt':
                subprocess.Popen(
                    ["python", "run.py"],
                    cwd=str(BACKEND_DIR),
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    ["python", "run.py"],
                    cwd=str(BACKEND_DIR),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # 等待服务启动
            self.logger.progress("等待后端 API 启动...")
            if self.wait_for_port(SERVICE_PORTS["backend"], timeout=30, service_name="Backend API"):
                time.sleep(2)  # 额外等待确保服务完全启动
                self.logger.success("后端 API 启动成功")
                return self._create_result(
                    name="Backend API",
                    status=ServiceStatus.HEALTHY,
                    message="后端 API 启动成功",
                    success=True,
                    start_time=start_time
                )
            else:
                error_msg = "后端 API 启动超时"
                self.logger.error(error_msg)
                return self._create_result(
                    name="Backend API",
                    status=ServiceStatus.UNHEALTHY,
                    message=error_msg,
                    error_details=error_msg,
                    start_time=start_time
                )
                
        except Exception as e:
            error_msg = f"后端服务启动异常: {str(e)}"
            self.logger.error(error_msg)
            return self._create_result(
                name="Backend API",
                status=ServiceStatus.UNHEALTHY,
                message=error_msg,
                error_details=str(e),
                start_time=start_time
            )
    
    def start_frontend(self) -> ServiceResult:
        """启动前端开发服务器"""
        start_time = time.time()
        self.logger.info("启动前端开发服务器...")
        
        # 检查端口是否已被占用
        if not self.check_port_available(SERVICE_PORTS["frontend"]):
            warning_msg = f"端口 {SERVICE_PORTS['frontend']} 已被占用，前端服务可能已在运行"
            self.logger.warning(warning_msg)
            return self._create_result(
                name="Frontend",
                status=ServiceStatus.WARNING,
                message=warning_msg,
                success=True,
                start_time=start_time,
                metadata={"port_already_in_use": True}
            )
        
        package_json = FRONTEND_DIR / "package.json"
        if not package_json.exists():
            error_msg = "package.json 文件不存在"
            self.logger.error(error_msg)
            return self._create_result(
                name="Frontend",
                status=ServiceStatus.UNHEALTHY,
                message=error_msg,
                error_details=error_msg,
                start_time=start_time
            )
        
        # 检查并安装依赖
        node_modules = FRONTEND_DIR / "node_modules"
        if not node_modules.exists():
            self.logger.progress("正在安装前端依赖...")
            try:
                result = subprocess.run(
                    ["npm", "install"],
                    cwd=str(FRONTEND_DIR),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                if result.returncode != 0:
                    error_msg = f"前端依赖安装失败: {result.stderr}"
                    self.logger.error(error_msg)
                    return self._create_result(
                        name="Frontend",
                        status=ServiceStatus.UNHEALTHY,
                        message=error_msg,
                        error_details=result.stderr,
                        start_time=start_time
                    )
                self.logger.success("前端依赖安装完成")
            except Exception as e:
                error_msg = f"前端依赖安装异常: {str(e)}"
                self.logger.error(error_msg)
                return self._create_result(
                    name="Frontend",
                    status=ServiceStatus.UNHEALTHY,
                    message=error_msg,
                    error_details=str(e),
                    start_time=start_time
                )
        
        try:
            # 启动前端进程
            if os.name == 'nt':
                subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=str(FRONTEND_DIR),
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=str(FRONTEND_DIR),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # 等待服务启动
            self.logger.progress("等待前端服务启动...")
            if self.wait_for_port(SERVICE_PORTS["frontend"], timeout=30, service_name="Frontend"):
                time.sleep(2)  # 额外等待确保服务完全启动
                self.logger.success("前端服务启动成功")
                return self._create_result(
                    name="Frontend",
                    status=ServiceStatus.HEALTHY,
                    message="前端服务启动成功",
                    success=True,
                    start_time=start_time
                )
            else:
                error_msg = "前端服务启动超时"
                self.logger.error(error_msg)
                return self._create_result(
                    name="Frontend",
                    status=ServiceStatus.UNHEALTHY,
                    message=error_msg,
                    error_details=error_msg,
                    start_time=start_time
                )
                
        except Exception as e:
            error_msg = f"前端服务启动异常: {str(e)}"
            self.logger.error(error_msg)
            return self._create_result(
                name="Frontend",
                status=ServiceStatus.UNHEALTHY,
                message=error_msg,
                error_details=str(e),
                start_time=start_time
            )
    
    def print_status_report(self):
        """打印服务状态报告"""
        print("\n" + "=" * 60)
        print("🚀 三省六部协同开发系统 - 服务状态")
        print("=" * 60)
        
        services_info = [
            ("PostgreSQL", SERVICE_PORTS["postgresql"], "数据库"),
            ("Redis", SERVICE_PORTS["redis"], "缓存"),
            ("Backend API", SERVICE_PORTS["backend"], "后端 API"),
            ("Frontend", SERVICE_PORTS["frontend"], "前端界面")
        ]
        
        for name, port, desc in services_info:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex(('localhost', port))
                sock.close()
                status = "✅ 运行中" if result == 0 else "❌ 未运行"
            except Exception:
                status = "❌ 未运行"
            
            url = ""
            if name == "Backend API":
                url = f"http://localhost:{port}"
            elif name == "Frontend":
                url = f"http://localhost:{port}"
            elif name == "PostgreSQL":
                url = f"localhost:{port}"
            elif name == "Redis":
                url = f"localhost:{port}"
            
            print(f"  {name} ({desc})")
            print(f"    状态: {status}")
            print(f"    地址: {url}")
            print()
        
        print("=" * 60)
        print("📝 访问地址:")
        print(f"   前端界面: http://localhost:{SERVICE_PORTS['frontend']}")
        print(f"   后端 API: http://localhost:{SERVICE_PORTS['backend']}")
        print(f"   API 文档: http://localhost:{SERVICE_PORTS['backend']}/docs")
        print("=" * 60)
    
    def print_detailed_report(self, result: StartServicesResult):
        """打印详细启动报告"""
        print("\n" + "=" * 60)
        print("📊 服务启动详细报告")
        print("=" * 60)
        print(f"⏰ 启动时间: {result.timestamp}")
        print(f"⏱️ 总耗时: {result.total_duration}s")
        
        status_icon = "✅" if result.overall_status == ServiceStatus.HEALTHY else "❌"
        print(f"📈 整体状态: {status_icon} {result.overall_status.value}")
        print("-" * 60)
        
        for service in result.services:
            if service.status == ServiceStatus.HEALTHY:
                icon = "✅"
            elif service.status == ServiceStatus.WARNING:
                icon = "⚠️"
            else:
                icon = "❌"
            
            print(f"{icon} {service.name}")
            print(f"   状态: {service.status.value}")
            print(f"   消息: {service.message}")
            if service.duration:
                print(f"   耗时: {service.duration}s")
            if service.error_details:
                print(f"   错误: {service.error_details}")
            print()
        
        if result.started_services:
            print(f"✅ 成功启动: {', '.join(result.started_services)}")
        if result.failed_services:
            print(f"❌ 启动失败: {', '.join(result.failed_services)}")
        if result.skipped_services:
            print(f"⏭️ 跳过启动: {', '.join(result.skipped_services)}")
        
        print("=" * 60)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="三省六部协同开发系统 - 服务启动脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python start_services.py              # 启动所有服务
  python start_services.py --no-docker  # 不启动 Docker 服务（使用本地服务）
  python start_services.py --backend    # 仅启动后端服务
  python start_services.py --frontend   # 仅启动前端服务
  python start_services.py -q           # 静默模式
  python start_services.py --check-env  # 启动前进行环境检测
  python start_services.py --wait-env   # 等待环境就绪后再启动
  python start_services.py --json       # JSON 格式输出
  python start_services.py --log-file   # 记录日志到文件
        """
    )
    parser.add_argument("--no-docker", action="store_true", help="不启动 Docker 服务")
    parser.add_argument("--no-backend", action="store_true", help="不启动后端服务")
    parser.add_argument("--no-frontend", action="store_true", help="不启动前端服务")
    parser.add_argument("--backend", action="store_true", help="仅启动后端服务")
    parser.add_argument("--frontend", action="store_true", help="仅启动前端服务")
    parser.add_argument("-q", "--quiet", action="store_true", help="静默模式")
    parser.add_argument("--skip-deps-check", action="store_true", help="跳过依赖检查")
    parser.add_argument("--check-env", action="store_true", help="启动前进行环境检测")
    parser.add_argument("--wait-env", action="store_true", help="等待环境就绪后再启动")
    parser.add_argument("--wait-env-timeout", type=int, default=60, help="等待环境就绪超时时间（秒），默认 60")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--log-file", action="store_true", help="记录日志到文件")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 三省六部协同开发系统 - 服务启动")
    print("=" * 60)
    
    # 设置日志文件
    log_file_path = LOGS_DIR / f"start_services_{time.strftime('%Y%m%d_%H%M%S')}.log" if args.log_file else None
    
    manager = ServiceManager(verbose=not args.quiet, log_file=log_file_path)
    overall_start_time = time.time()
    
    # 依赖检查
    if not args.skip_deps_check:
        deps = manager.check_dependencies()
        if not deps["python"]:
            print("❌ Python 未安装，请先安装 Python")
            return 1
        if not args.no_docker and not deps["docker"]:
            print("❌ Docker 未安装，请先安装 Docker 或使用 --no-docker 参数")
            return 1
    
    # 环境检查或等待
    if args.wait_env:
        if not manager.wait_for_environment(timeout=args.wait_env_timeout, skip_docker=args.no_docker):
            print("\n❌ 环境未就绪，无法启动服务")
            env_result = manager.run_environment_check(skip_docker=args.no_docker, json_output=True)
            print(manager.diagnose_failure("Environment", json.dumps(env_result, indent=2, ensure_ascii=False)))
            return 1
    elif args.check_env:
        env_result = manager.run_environment_check(skip_docker=args.no_docker)
        if env_result.get("overall_status") not in ("healthy", "skipped"):
            print("\n❌ 环境检测未通过，请先解决以下问题:")
            for service in env_result.get("services", []):
                if service["status"] not in ("healthy", "skipped"):
                    print(f"   - {service['name']}: {service['message']}")
            return 1
    
    # 确定要启动的服务
    start_docker = not args.no_docker and not args.backend and not args.frontend
    start_backend = not args.no_backend or args.backend
    start_frontend = not args.no_frontend or args.frontend
    
    if args.backend:
        start_docker = False
        start_frontend = False
    if args.frontend:
        start_docker = False
        start_backend = False
    
    # 启动服务
    services_to_start = []
    if start_docker:
        services_to_start.append(("Docker Services", manager.start_docker_services))
    if start_backend:
        services_to_start.append(("Backend API", manager.start_backend))
    if start_frontend:
        services_to_start.append(("Frontend", manager.start_frontend))
    
    for service_name, start_func in services_to_start:
        result = start_func()
        
        if result.success:
            if result.status == ServiceStatus.WARNING:
                manager.skipped_services.append(service_name)
            else:
                manager.started_services.append(service_name)
        else:
            manager.failed_services.append(service_name)
    
    # 打印状态报告
    manager.print_status_report()
    
    # 构建结果
    overall_status = ServiceStatus.HEALTHY if not manager.failed_services else ServiceStatus.UNHEALTHY
    total_duration = round(time.time() - overall_start_time, 2)
    
    result = StartServicesResult(
        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
        overall_status=overall_status,
        services=manager.service_results,
        started_services=manager.started_services,
        failed_services=manager.failed_services,
        skipped_services=manager.skipped_services,
        total_duration=total_duration
    )
    
    # 输出失败诊断
    if manager.failed_services:
        print("\n⚠️ 以下服务启动失败:")
        for service_name in manager.failed_services:
            print(f"   - {service_name}")
            # 找到对应的结果获取错误详情
            for sr in manager.service_results:
                if sr.name == service_name:
                    print(manager.diagnose_failure(service_name, sr.error_details or ""))
                    break
        print("\n请检查日志并重试")
        
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        
        return 1
    
    print("\n🎉 所有服务启动完成！")
    
    if args.json:
        print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
