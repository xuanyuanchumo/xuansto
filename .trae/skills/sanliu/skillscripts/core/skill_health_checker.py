#!/usr/bin/env python3
"""
三省六部协同开发系统 - 技能健康检查器
检查技能系统的整体健康状态

功能：
- 检查技能核心组件的运行状态
- 检查数据库连接状态
- 检查后端服务状态
- 检查前端服务状态
- 检查脚本可用性
- 检查目录结构完整性
- 生成健康度报告
- 提供修复建议
"""
import argparse
import importlib.util
import json
import logging
import os
import socket
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from skillscripts.utils.path_config_manager import PathConfigManager

PROJECT_ROOT = get_path_config().SKILL_ROOT
SKILLSCRIPTS_DIR = Path(__file__).parent
CORE_DIR = get_path_config().SCRIPTS_DIR / "core"


class HealthStatus(Enum):
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"
    UNKNOWN = "unknown"


class CheckCategory(Enum):
    CORE_COMPONENT = "core_component"
    DATABASE = "database"
    BACKEND = "backend"
    FRONTEND = "frontend"
    SCRIPT = "script"
    DIRECTORY = "directory"


@dataclass
class CheckResult:
    name: str
    category: CheckCategory
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    response_time_ms: Optional[float] = None
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['category'] = self.category.value
        result['status'] = self.status.value
        return result


@dataclass
class HealthReport:
    timestamp: str
    overall_status: HealthStatus
    health_score: float
    results: List[CheckResult]
    summary: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    duration_ms: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "overall_status": self.overall_status.value,
            "health_score": self.health_score,
            "results": [r.to_dict() for r in self.results],
            "summary": self.summary,
            "suggestions": self.suggestions,
            "duration_ms": self.duration_ms
        }


class SkillHealthChecker:
    CORE_SCRIPTS = [
        "unified_script_entry.py",
        "start_services.py",
        "stop_services.py",
        "init_db.py",
        "query_status.py",
        "health_check.py",
        "check_environment.py",
        "docker_manager.py",
        "service_dependency_manager.py",
        "provincial_coordinator.py",
        "agent_selector.py",
        "assign_agent.py",
        "record_skill_call.py",
        "script_base.py",
        "script_interface_standard.py"
    ]
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: List[CheckResult] = []
        self.path_manager = PathConfigManager()
        self._setup_logging()
        self._init_required_directories()
    
    def _init_required_directories(self):
        self.required_directories = [
            self.path_manager.get_skillscripts_path() / "core",
            self.path_manager.get_docs_reports_path() / "department_checks",
            self.path_manager.get_docs_reports_path() / "provincial_checks",
            self.path_manager.get_docs_reports_path() / "skill_call_chain",
            self.path_manager.get_skillscripts_path() / "utils",
            self.path_manager.get_skillscripts_path() / "analysis",
            self.path_manager.get_skillscripts_path() / "pipeline",
            self.path_manager.get_skillscripts_path() / "test",
            self.path_manager.get_skillscripts_path() / "monitoring",
            self.path_manager.get_skillscripts_path() / "requirements",
            self.path_manager.get_skillscripts_path() / "optimization",
            self.path_manager.get_cache_path(),
            self.path_manager.get_temp_path(),
            self.path_manager.get_data_path(),
            self.path_manager.get_config_path()
        ]
    
    def _setup_logging(self):
        level = logging.DEBUG if self.verbose else logging.WARNING
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def _log(self, message: str, level: str = "info"):
        icons = {
            "info": "ℹ️",
            "success": "✅",
            "warning": "⚠️",
            "error": "❌",
            "debug": "🔍"
        }
        icon = icons.get(level, "")
        if self.verbose:
            print(f"{icon} {message}")
        
        log_method = getattr(self.logger, level, self.logger.info)
        log_method(message)
    
    def _check_port(self, host: str, port: int, timeout: int = 5) -> Tuple[bool, Optional[float]]:
        start_time = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            response_time = round((time.time() - start_time) * 1000, 2)
            return result == 0, response_time
        except Exception as e:
            self._log(f"端口检查异常 {host}:{port}: {e}", "debug")
            return False, None
    
    def _http_request(self, url: str, timeout: int = 5) -> Tuple[bool, Optional[int], Optional[float], Optional[str]]:
        from urllib.request import Request, urlopen
        from urllib.error import URLError, HTTPError
        
        start_time = time.time()
        try:
            req = Request(url, method='GET')
            req.add_header('User-Agent', 'SkillHealthChecker/1.0')
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
    
    def _add_result(self, result: CheckResult):
        self.results.append(result)
        status_icons = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.UNHEALTHY: "❌",
            HealthStatus.ERROR: "💥",
            HealthStatus.SKIPPED: "⏭️"
        }
        icon = status_icons.get(result.status, "❓")
        self._log(f"{result.name}: {result.message}", 
                  "success" if result.status == HealthStatus.HEALTHY else 
                  "warning" if result.status == HealthStatus.WARNING else "error")
    
    def check_core_components(self) -> CheckResult:
        self._log("检查技能核心组件...")
        
        core_dir = self.path_manager.get_skillscripts_path() / "core"
        missing_scripts = []
        available_scripts = []
        import_errors = []
        
        for script in self.CORE_SCRIPTS:
            script_path = core_dir / script
            if not script_path.exists():
                missing_scripts.append(script)
                continue
            
            available_scripts.append(script)
            
            module_name = script.replace('.py', '')
            try:
                spec = importlib.util.spec_from_file_location(module_name, script_path)
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
            except Exception as e:
                import_errors.append({"script": script, "error": str(e)})
        
        total = len(self.CORE_SCRIPTS)
        available = len(available_scripts)
        score = (available / total) * 100 if total > 0 else 0
        
        suggestions = []
        if missing_scripts:
            suggestions.append(f"缺失核心脚本: {', '.join(missing_scripts)}。请从版本控制恢复或重新创建。")
        if import_errors:
            for err in import_errors:
                suggestions.append(f"脚本 {err['script']} 导入失败: {err['error']}")
        
        if score == 100 and not import_errors:
            status = HealthStatus.HEALTHY
            message = f"所有核心组件可用 ({available}/{total})"
        elif score >= 80:
            status = HealthStatus.WARNING
            message = f"部分核心组件异常 ({available}/{total})"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"核心组件严重缺失 ({available}/{total})"
        
        result = CheckResult(
            name="核心组件检查",
            category=CheckCategory.CORE_COMPONENT,
            status=status,
            message=message,
            details={
                "total": total,
                "available": available,
                "missing": missing_scripts,
                "import_errors": import_errors,
                "score": score
            },
            suggestions=suggestions
        )
        self._add_result(result)
        return result
    
    def check_database(self, host: str = "localhost", port: int = 5432, 
                       database: str = "skiller") -> CheckResult:
        self._log("检查数据库连接...")
        
        success, response_time = self._check_port(host, port)
        
        suggestions = []
        details = {
            "host": host,
            "port": port,
            "database": database,
            "connection_test": "port_check"
        }
        
        if success:
            try:
                import psycopg2
                start_time = time.time()
                user = os.environ.get("POSTGRES_USER", "postgres")
                password = os.environ.get("POSTGRES_PASSWORD", "")
                conn = psycopg2.connect(
                    host=host, port=port, database=database,
                    user=user, password=password, connect_timeout=5
                )
                conn.close()
                response_time = round((time.time() - start_time) * 1000, 2)
                details["connection_test"] = "full_connection"
                
                result = CheckResult(
                    name="数据库连接检查",
                    category=CheckCategory.DATABASE,
                    status=HealthStatus.HEALTHY,
                    message=f"数据库连接正常 (数据库: {database})",
                    details=details,
                    response_time=response_time
                )
            except ImportError:
                result = CheckResult(
                    name="数据库连接检查",
                    category=CheckCategory.DATABASE,
                    status=HealthStatus.HEALTHY,
                    message=f"数据库端口可访问 (数据库: {database}, psycopg2 未安装)",
                    details=details,
                    response_time=response_time,
                    suggestions=["安装 psycopg2 以进行完整连接测试: pip install psycopg2-binary"]
                )
            except Exception as e:
                suggestions.append(f"检查数据库配置: {host}:{port}/{database}")
                suggestions.append("确认数据库服务已启动")
                suggestions.append("检查用户名密码是否正确")
                result = CheckResult(
                    name="数据库连接检查",
                    category=CheckCategory.DATABASE,
                    status=HealthStatus.UNHEALTHY,
                    message=f"数据库连接失败: {str(e)}",
                    details={**details, "error": str(e)},
                    suggestions=suggestions
                )
        else:
            suggestions.append(f"启动数据库服务或检查 {host}:{port} 是否可访问")
            suggestions.append("使用 Docker 启动: docker-compose up -d postgres")
            result = CheckResult(
                name="数据库连接检查",
                category=CheckCategory.DATABASE,
                status=HealthStatus.UNHEALTHY,
                message=f"数据库无法连接: {host}:{port}",
                details=details,
                suggestions=suggestions
            )
        
        self._add_result(result)
        return result
    
    def check_backend(self, base_url: str = "http://localhost:8000") -> CheckResult:
        self._log("检查后端服务...")
        
        health_url = f"{base_url.rstrip('/')}/health"
        success, status_code, response_time, error = self._http_request(health_url)
        
        suggestions = []
        details = {"url": health_url}
        
        if success and status_code == 200:
            result = CheckResult(
                name="后端服务检查",
                category=CheckCategory.BACKEND,
                status=HealthStatus.HEALTHY,
                message="后端服务正常运行",
                details={**details, "status_code": status_code},
                response_time=response_time
            )
        elif success:
            suggestions.append(f"检查后端健康检查端点返回状态码: {status_code}")
            result = CheckResult(
                name="后端服务检查",
                category=CheckCategory.BACKEND,
                status=HealthStatus.WARNING,
                message=f"后端服务返回非预期状态码: {status_code}",
                details={**details, "status_code": status_code},
                response_time=response_time,
                suggestions=suggestions
            )
        else:
            suggestions.append("启动后端服务: python -m uvicorn main:app --reload")
            suggestions.append("检查后端服务配置和日志")
            result = CheckResult(
                name="后端服务检查",
                category=CheckCategory.BACKEND,
                status=HealthStatus.UNHEALTHY,
                message=f"后端服务无法访问: {error}",
                details={**details, "error": error},
                suggestions=suggestions
            )
        
        self._add_result(result)
        return result
    
    def check_frontend(self, host: str = "localhost", port: int = 5173) -> CheckResult:
        self._log("检查前端服务...")
        
        success, response_time = self._check_port(host, port)
        
        suggestions = []
        details = {"host": host, "port": port, "url": f"http://{host}:{port}"}
        
        if success:
            result = CheckResult(
                name="前端服务检查",
                category=CheckCategory.FRONTEND,
                status=HealthStatus.HEALTHY,
                message=f"前端服务正常运行 (端口: {port})",
                details=details,
                response_time=response_time
            )
        else:
            suggestions.append("启动前端开发服务器: npm run dev")
            suggestions.append("检查前端项目配置")
            result = CheckResult(
                name="前端服务检查",
                category=CheckCategory.FRONTEND,
                status=HealthStatus.UNHEALTHY,
                message=f"前端服务无法访问: {host}:{port}",
                details=details,
                suggestions=suggestions
            )
        
        self._add_result(result)
        return result
    
    def check_scripts_availability(self) -> CheckResult:
        self._log("检查脚本可用性...")
        
        skillscripts_path = self.path_manager.get_skillscripts_path()
        all_scripts = list(skillscripts_path.rglob("*.py"))
        test_scripts = [s for s in all_scripts if "test" in str(s).lower() or s.name.startswith("test_")]
        main_scripts = [s for s in all_scripts if s not in test_scripts]
        
        syntax_errors = []
        import_issues = []
        
        for script in main_scripts[:50]:
            try:
                with open(script, 'r', encoding='utf-8') as f:
                    content = f.read()
                compile(content, str(script), 'exec')
            except SyntaxError as e:
                syntax_errors.append({"script": str(script.relative_to(skillscripts_path)), "error": str(e)})
        
        total_main = len(main_scripts)
        total_test = len(test_scripts)
        error_count = len(syntax_errors)
        
        suggestions = []
        if syntax_errors:
            for err in syntax_errors[:5]:
                suggestions.append(f"修复语法错误: {err['script']} - {err['error']}")
        
        score = ((total_main - error_count) / total_main * 100) if total_main > 0 else 100
        
        if score == 100:
            status = HealthStatus.HEALTHY
            message = f"所有脚本可用 (主脚本: {total_main}, 测试脚本: {total_test})"
        elif score >= 90:
            status = HealthStatus.WARNING
            message = f"部分脚本有语法错误 ({error_count}/{total_main})"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"大量脚本存在语法错误 ({error_count}/{total_main})"
        
        result = CheckResult(
            name="脚本可用性检查",
            category=CheckCategory.SCRIPT,
            status=status,
            message=message,
            details={
                "total_main_scripts": total_main,
                "total_test_scripts": total_test,
                "syntax_errors": syntax_errors,
                "error_count": error_count,
                "score": score
            },
            suggestions=suggestions
        )
        self._add_result(result)
        return result
    
    def check_directory_structure(self) -> CheckResult:
        self._log("检查目录结构完整性...")
        
        missing_dirs = []
        existing_dirs = []
        
        for dir_path in self.required_directories:
            if dir_path.exists() and dir_path.is_dir():
                existing_dirs.append(str(dir_path.relative_to(self.path_manager.get_base_path())))
            else:
                missing_dirs.append(str(dir_path.relative_to(self.path_manager.get_base_path())))
        
        total = len(self.required_directories)
        existing = len(existing_dirs)
        score = (existing / total) * 100 if total > 0 else 100
        
        suggestions = []
        if missing_dirs:
            for dir_name in missing_dirs:
                suggestions.append(f"创建缺失目录: {dir_name}")
        
        if score == 100:
            status = HealthStatus.HEALTHY
            message = f"目录结构完整 ({existing}/{total})"
        elif score >= 80:
            status = HealthStatus.WARNING
            message = f"部分目录缺失 ({existing}/{total})"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"目录结构严重缺失 ({existing}/{total})"
        
        result = CheckResult(
            name="目录结构检查",
            category=CheckCategory.DIRECTORY,
            status=status,
            message=message,
            details={
                "total": total,
                "existing": existing,
                "missing": missing_dirs,
                "score": score
            },
            suggestions=suggestions
        )
        self._add_result(result)
        return result
    
    def check_docker_status(self) -> CheckResult:
        self._log("检查 Docker 状态...")
        
        suggestions = []
        
        try:
            proc = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if proc.returncode == 0:
                result = CheckResult(
                    name="Docker 状态检查",
                    category=CheckCategory.CORE_COMPONENT,
                    status=HealthStatus.HEALTHY,
                    message="Docker 正在运行"
                )
            else:
                suggestions.append("启动 Docker Desktop 或 Docker 服务")
                result = CheckResult(
                    name="Docker 状态检查",
                    category=CheckCategory.CORE_COMPONENT,
                    status=HealthStatus.UNHEALTHY,
                    message="Docker 未运行",
                    suggestions=suggestions
                )
        except FileNotFoundError:
            suggestions.append("安装 Docker Desktop")
            result = CheckResult(
                name="Docker 状态检查",
                category=CheckCategory.CORE_COMPONENT,
                status=HealthStatus.UNHEALTHY,
                message="Docker 未安装",
                suggestions=suggestions
            )
        except subprocess.TimeoutExpired:
            suggestions.append("检查 Docker 服务状态")
            result = CheckResult(
                name="Docker 状态检查",
                category=CheckCategory.CORE_COMPONENT,
                status=HealthStatus.ERROR,
                message="Docker 检查超时",
                suggestions=suggestions
            )
        except Exception as e:
            suggestions.append(f"检查 Docker 配置: {str(e)}")
            result = CheckResult(
                name="Docker 状态检查",
                category=CheckCategory.CORE_COMPONENT,
                status=HealthStatus.ERROR,
                message=f"Docker 检查失败: {str(e)}",
                suggestions=suggestions
            )
        
        self._add_result(result)
        return result
    
    def check_redis(self, host: str = "localhost", port: int = 6379) -> CheckResult:
        self._log("检查 Redis 连接...")
        
        success, response_time = self._check_port(host, port)
        
        suggestions = []
        details = {"host": host, "port": port}
        
        if success:
            try:
                import redis
from skillscripts.core.path_config_center import get_path_config
                client = redis.Redis(host=host, port=port, socket_timeout=5)
                client.ping()
                client.close()
                
                result = CheckResult(
                    name="Redis 连接检查",
                    category=CheckCategory.DATABASE,
                    status=HealthStatus.HEALTHY,
                    message="Redis 连接正常",
                    details=details,
                    response_time=response_time
                )
            except ImportError:
                result = CheckResult(
                    name="Redis 连接检查",
                    category=CheckCategory.DATABASE,
                    status=HealthStatus.HEALTHY,
                    message="Redis 端口可访问 (redis-py 未安装)",
                    details=details,
                    response_time=response_time,
                    suggestions=["安装 redis-py: pip install redis"]
                )
            except Exception as e:
                suggestions.append("检查 Redis 配置")
                result = CheckResult(
                    name="Redis 连接检查",
                    category=CheckCategory.DATABASE,
                    status=HealthStatus.WARNING,
                    message=f"Redis 连接异常: {str(e)}",
                    details={**details, "error": str(e)},
                    suggestions=suggestions
                )
        else:
            suggestions.append(f"启动 Redis 服务或检查 {host}:{port}")
            suggestions.append("使用 Docker 启动: docker-compose up -d redis")
            result = CheckResult(
                name="Redis 连接检查",
                category=CheckCategory.DATABASE,
                status=HealthStatus.UNHEALTHY,
                message=f"Redis 无法连接: {host}:{port}",
                details=details,
                suggestions=suggestions
            )
        
        self._add_result(result)
        return result
    
    def run_full_check(
        self,
        db_host: str = "localhost",
        db_port: int = 5432,
        db_name: str = "skiller",
        backend_url: str = "http://localhost:8000",
        frontend_host: str = "localhost",
        frontend_port: int = 5173,
        redis_host: str = "localhost",
        redis_port: int = 6379,
        skip_docker: bool = False,
        checks: Optional[List[str]] = None
    ) -> HealthReport:
        start_time = time.time()
        self.results = []
        
        all_checks = {
            "core": lambda: self.check_core_components(),
            "database": lambda: self.check_database(db_host, db_port, db_name),
            "backend": lambda: self.check_backend(backend_url),
            "frontend": lambda: self.check_frontend(frontend_host, frontend_port),
            "scripts": lambda: self.check_scripts_availability(),
            "directories": lambda: self.check_directory_structure(),
            "docker": lambda: self.check_docker_status() if not skip_docker else None,
            "redis": lambda: self.check_redis(redis_host, redis_port)
        }
        
        checks_to_run = checks if checks else list(all_checks.keys())
        
        for check_name in checks_to_run:
            if check_name in all_checks:
                try:
                    check_func = all_checks[check_name]
                    if check_func:
                        check_func()
                except Exception as e:
                    self._log(f"检查项 {check_name} 执行失败: {e}", "error")
        
        overall_status = HealthStatus.HEALTHY
        for result in self.results:
            if result.status == HealthStatus.ERROR:
                overall_status = HealthStatus.ERROR
                break
            elif result.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif result.status == HealthStatus.WARNING and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.WARNING
        
        health_score = self._calculate_health_score()
        
        summary = {
            "total_checks": len(self.results),
            "healthy": sum(1 for r in self.results if r.status == HealthStatus.HEALTHY),
            "warning": sum(1 for r in self.results if r.status == HealthStatus.WARNING),
            "unhealthy": sum(1 for r in self.results if r.status == HealthStatus.UNHEALTHY),
            "error": sum(1 for r in self.results if r.status == HealthStatus.ERROR),
            "skipped": sum(1 for r in self.results if r.status == HealthStatus.SKIPPED)
        }
        
        all_suggestions = []
        for result in self.results:
            all_suggestions.extend(result.suggestions)
        
        duration_ms = round((time.time() - start_time) * 1000, 2)
        
        return HealthReport(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            overall_status=overall_status,
            health_score=health_score,
            results=self.results,
            summary=summary,
            suggestions=list(set(all_suggestions)),
            duration_ms=duration_ms
        )
    
    def _calculate_health_score(self) -> float:
        if not self.results:
            return 0.0
        
        weights = {
            HealthStatus.HEALTHY: 100,
            HealthStatus.WARNING: 70,
            HealthStatus.SKIPPED: 50,
            HealthStatus.UNHEALTHY: 20,
            HealthStatus.ERROR: 0,
            HealthStatus.UNKNOWN: 50
        }
        
        category_weights = {
            CheckCategory.CORE_COMPONENT: 2.0,
            CheckCategory.DATABASE: 1.5,
            CheckCategory.BACKEND: 1.5,
            CheckCategory.FRONTEND: 1.0,
            CheckCategory.SCRIPT: 1.2,
            CheckCategory.DIRECTORY: 0.8
        }
        
        total_weight = 0
        weighted_score = 0
        
        for result in self.results:
            cat_weight = category_weights.get(result.category, 1.0)
            status_score = weights.get(result.status, 50)
            
            total_weight += cat_weight
            weighted_score += status_score * cat_weight
        
        return round(weighted_score / total_weight, 2) if total_weight > 0 else 0.0


def print_report(report: HealthReport, verbose: bool = False):
    print("\n" + "=" * 70)
    print("🏥 三省六部协同开发系统 - 技能健康检查报告")
    print("=" * 70)
    print(f"⏰ 检查时间: {report.timestamp}")
    print(f"⏱️ 检查耗时: {report.duration_ms}ms")
    print(f"📊 整体状态: {report.overall_status.value}")
    print(f"💯 健康评分: {report.health_score}/100")
    
    print("-" * 70)
    print("📈 检查统计:")
    summary = report.summary
    print(f"   总计: {summary.get('total_checks', 0)}")
    print(f"   ✅ 健康: {summary.get('healthy', 0)}")
    print(f"   ⚠️ 警告: {summary.get('warning', 0)}")
    print(f"   ❌ 异常: {summary.get('unhealthy', 0)}")
    print(f"   💥 错误: {summary.get('error', 0)}")
    print(f"   ⏭️ 跳过: {summary.get('skipped', 0)}")
    
    print("-" * 70)
    print("📋 检查详情:")
    
    status_icons = {
        HealthStatus.HEALTHY: "✅",
        HealthStatus.WARNING: "⚠️",
        HealthStatus.UNHEALTHY: "❌",
        HealthStatus.ERROR: "💥",
        HealthStatus.SKIPPED: "⏭️",
        HealthStatus.UNKNOWN: "❓"
    }
    
    for result in report.results:
        icon = status_icons.get(result.status, "❓")
        print(f"\n{icon} [{result.category.value}] {result.name}")
        print(f"   状态: {result.message}")
        
        if result.response_time_ms:
            print(f"   响应时间: {result.response_time_ms}ms")
        
        if verbose and result.details:
            for key, value in result.details.items():
                if key not in ["error", "stderr"]:
                    print(f"   {key}: {value}")
        
        if result.suggestions:
            print(f"   💡 建议:")
            for suggestion in result.suggestions[:3]:
                print(f"      - {suggestion}")
    
    if report.suggestions:
        print("-" * 70)
        print("🔧 修复建议汇总:")
        for i, suggestion in enumerate(report.suggestions[:10], 1):
            print(f"   {i}. {suggestion}")
    
    print("=" * 70)
    
    if report.overall_status == HealthStatus.HEALTHY:
        print("🎉 所有检查项通过！技能系统运行正常。")
    elif report.overall_status == HealthStatus.WARNING:
        print("⚠️ 部分检查项有警告，建议检查并优化。")
    else:
        print("❌ 发现异常项，请根据建议进行修复。")
    
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="三省六部协同开发系统 - 技能健康检查器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python skill_health_checker.py                    # 运行完整检查
  python skill_health_checker.py --json             # JSON 格式输出
  python skill_health_checker.py --check core database  # 仅检查指定项
  python skill_health_checker.py --skip-docker      # 跳过 Docker 检查
  python skill_health_checker.py -v                 # 详细输出
  python skill_health_checker.py --db-host 192.168.1.100  # 指定数据库地址

可用检查项:
  core        - 核心组件检查
  database    - 数据库连接检查
  backend     - 后端服务检查
  frontend    - 前端服务检查
  scripts     - 脚本可用性检查
  directories - 目录结构检查
  docker      - Docker 状态检查
  redis       - Redis 连接检查
        """
    )
    
    parser.add_argument("--json", action="store_true", help="输出 JSON 格式")
    parser.add_argument("--check", nargs="+", choices=[
        "core", "database", "backend", "frontend", "scripts", "directories", "docker", "redis"
    ], help="指定检查项")
    parser.add_argument("--skip-docker", action="store_true", help="跳过 Docker 检查")
    parser.add_argument("--db-host", type=str, default="localhost", help="数据库主机")
    parser.add_argument("--db-port", type=int, default=5432, help="数据库端口")
    parser.add_argument("--db-name", type=str, default="skiller", help="数据库名称")
    parser.add_argument("--backend-url", type=str, default="http://localhost:8000", help="后端服务 URL")
    parser.add_argument("--frontend-host", type=str, default="localhost", help="前端服务主机")
    parser.add_argument("--frontend-port", type=int, default=5173, help="前端服务端口")
    parser.add_argument("--redis-host", type=str, default="localhost", help="Redis 主机")
    parser.add_argument("--redis-port", type=int, default=6379, help="Redis 端口")
    parser.add_argument("-v", "--verbose", action="store_true", help="详细输出")
    parser.add_argument("--output", "-o", type=str, help="输出报告文件路径")
    
    args = parser.parse_args()
    
    checker = SkillHealthChecker(verbose=not args.json)
    
    report = checker.run_full_check(
        db_host=args.db_host,
        db_port=args.db_port,
        db_name=args.db_name,
        backend_url=args.backend_url,
        frontend_host=args.frontend_host,
        frontend_port=args.frontend_port,
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        skip_docker=args.skip_docker,
        checks=args.check
    )
    
    if args.json:
        output = json.dumps(report.to_dict(), indent=2, ensure_ascii=False)
        print(output)
    else:
        print_report(report, verbose=args.verbose)
    
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        if not args.json:
            print(f"\n📄 报告已保存至: {args.output}")
    
    return 0 if report.overall_status in (HealthStatus.HEALTHY, HealthStatus.WARNING) else 1


if __name__ == "__main__":
    sys.exit(main())
