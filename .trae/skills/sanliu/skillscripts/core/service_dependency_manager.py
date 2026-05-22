#!/usr/bin/env python3
"""
服务依赖管理器 - 管理服务启动顺序、依赖关系和健康检查

功能：
1. 服务依赖关系管理
2. 自动重试机制
3. 健康检查验证
4. 服务启动顺序控制
"""

import time
import logging
import subprocess
import requests
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服务状态枚举"""
    UNKNOWN = "unknown"
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


@dataclass
class ServiceInfo:
    """服务信息"""
    name: str
    host: str
    port: int
    health_endpoint: Optional[str] = None
    dependencies: List[str] = None
    startup_timeout: int = 60
    retry_count: int = 3
    retry_delay: int = 5
    health_check_timeout: int = 5
    socket_timeout: int = 3
    status: ServiceStatus = ServiceStatus.UNKNOWN
    last_check: Optional[datetime] = None
    error_message: Optional[str] = None


class ServiceDependencyManager:
    """服务依赖管理器"""
    
    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self._setup_default_services()
    
    def _setup_default_services(self):
        """设置默认服务配置"""
        self.register_service(ServiceInfo(
            name="postgres",
            host="localhost",
            port=5432,
            health_endpoint=None,
            dependencies=[],
            startup_timeout=60,
            retry_count=5,
            retry_delay=3
        ))
        
        self.register_service(ServiceInfo(
            name="redis",
            host="localhost",
            port=6379,
            health_endpoint=None,
            dependencies=[],
            startup_timeout=30,
            retry_count=3,
            retry_delay=2
        ))
        
        self.register_service(ServiceInfo(
            name="backend",
            host="localhost",
            port=8000,
            health_endpoint="http://localhost:8000/health",
            dependencies=["postgres", "redis"],
            startup_timeout=60,
            retry_count=3,
            retry_delay=5
        ))
        
        self.register_service(ServiceInfo(
            name="frontend",
            host="localhost",
            port=5173,
            health_endpoint="http://localhost:5173",
            dependencies=["backend"],
            startup_timeout=30,
            retry_count=3,
            retry_delay=3
        ))
    
    def register_service(self, service: ServiceInfo):
        """注册服务"""
        self.services[service.name] = service
        logger.info(f"Registered service: {service.name} at {service.host}:{service.port}")
    
    def check_service_health(self, service_name: str) -> bool:
        """检查服务健康状态"""
        service = self.services.get(service_name)
        if not service:
            logger.error(f"Service not found: {service_name}")
            return False
        
        try:
            if service.health_endpoint:
                response = requests.get(
                    service.health_endpoint,
                    timeout=service.health_check_timeout
                )
                is_healthy = response.status_code == 200
            else:
                import socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(service.socket_timeout)
                result = sock.connect_ex((service.host, service.port))
                sock.close()
                is_healthy = result == 0
            
            service.status = ServiceStatus.RUNNING if is_healthy else ServiceStatus.STOPPED
            service.last_check = datetime.now()
            service.error_message = None
            
            return is_healthy
            
        except Exception as e:
            service.status = ServiceStatus.ERROR
            service.last_check = datetime.now()
            service.error_message = str(e)
            logger.error(f"Health check failed for {service_name}: {e}")
            return False
    
    def wait_for_service(self, service_name: str, timeout: int = None) -> bool:
        """等待服务就绪"""
        service = self.services.get(service_name)
        if not service:
            return False
        
        timeout = timeout or service.startup_timeout
        retry_count = service.retry_count
        retry_delay = service.retry_delay
        
        logger.info(f"Waiting for service {service_name} (timeout: {timeout}s, retries: {retry_count})")
        
        start_time = time.time()
        attempts = 0
        
        while time.time() - start_time < timeout:
            if self.check_service_health(service_name):
                logger.info(f"Service {service_name} is ready")
                return True
            
            attempts += 1
            if attempts >= retry_count:
                logger.error(f"Service {service_name} failed after {retry_count} attempts")
                return False
            
            logger.debug(f"Service {service_name} not ready, retrying in {retry_delay}s...")
            time.sleep(retry_delay)
        
        logger.error(f"Timeout waiting for service {service_name}")
        return False
    
    def check_dependencies(self, service_name: str, parallel: bool = True) -> Dict[str, bool]:
        """检查服务依赖"""
        service = self.services.get(service_name)
        if not service:
            return {}
        
        dependencies = service.dependencies or []
        if not dependencies:
            return {}
        
        dependencies_status = {}
        
        if parallel and len(dependencies) > 1:
            with ThreadPoolExecutor(max_workers=len(dependencies)) as executor:
                futures = {
                    executor.submit(self.check_service_health, dep_name): dep_name
                    for dep_name in dependencies
                }
                for future in as_completed(futures):
                    dep_name = futures[future]
                    is_healthy = future.result()
                    dependencies_status[dep_name] = is_healthy
                    
                    if not is_healthy:
                        logger.warning(f"Dependency {dep_name} for {service_name} is not healthy")
        else:
            for dep_name in dependencies:
                is_healthy = self.check_service_health(dep_name)
                dependencies_status[dep_name] = is_healthy
                
                if not is_healthy:
                    logger.warning(f"Dependency {dep_name} for {service_name} is not healthy")
        
        return dependencies_status
    
    def start_service_with_dependencies(self, service_name: str, start_command: str = None) -> bool:
        """按依赖顺序启动服务"""
        service = self.services.get(service_name)
        if not service:
            logger.error(f"Service not found: {service_name}")
            return False
        
        logger.info(f"Starting service {service_name}...")
        
        dependencies_ok = True
        for dep_name in (service.dependencies or []):
            if not self.check_service_health(dep_name):
                logger.info(f"Dependency {dep_name} not ready, waiting...")
                if not self.wait_for_service(dep_name):
                    logger.error(f"Dependency {dep_name} failed to start")
                    dependencies_ok = False
                    break
        
        if not dependencies_ok:
            logger.error(f"Cannot start {service_name}: dependencies not met")
            return False
        
        if self.check_service_health(service_name):
            logger.info(f"Service {service_name} is already running")
            return True
        
        if start_command:
            try:
                logger.info(f"Executing start command: {start_command}")
                subprocess.Popen(
                    start_command,
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except Exception as e:
                logger.error(f"Failed to start service {service_name}: {e}")
                return False
        
        return self.wait_for_service(service_name)
    
    def get_service_status_report(self, parallel: bool = True) -> Dict:
        """获取服务状态报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "services": {},
            "overall_status": "healthy"
        }
        
        if parallel and len(self.services) > 1:
            with ThreadPoolExecutor(max_workers=len(self.services)) as executor:
                futures = {
                    executor.submit(self.check_service_health, name): name 
                    for name in self.services
                }
                for future in as_completed(futures):
                    name = futures[future]
                    service = self.services[name]
                    is_healthy = future.result()
                    
                    report["services"][name] = {
                        "status": service.status.value,
                        "host": service.host,
                        "port": service.port,
                        "healthy": is_healthy,
                        "last_check": service.last_check.isoformat() if service.last_check else None,
                        "error_message": service.error_message,
                        "dependencies": service.dependencies or []
                    }
                    
                    if not is_healthy:
                        report["overall_status"] = "unhealthy"
        else:
            for name, service in self.services.items():
                is_healthy = self.check_service_health(name)
                
                report["services"][name] = {
                    "status": service.status.value,
                    "host": service.host,
                    "port": service.port,
                    "healthy": is_healthy,
                    "last_check": service.last_check.isoformat() if service.last_check else None,
                    "error_message": service.error_message,
                    "dependencies": service.dependencies or []
                }
                
                if not is_healthy:
                    report["overall_status"] = "unhealthy"
        
        return report
    
    def validate_startup_order(self) -> List[str]:
        """验证启动顺序"""
        visited = set()
        order = []
        
        def visit(name: str, path: List[str]):
            if name in path:
                raise ValueError(f"Circular dependency detected: {' -> '.join(path + [name])}")
            
            if name in visited:
                return
            
            service = self.services.get(name)
            if not service:
                return
            
            for dep in (service.dependencies or []):
                visit(dep, path + [name])
            
            visited.add(name)
            order.append(name)
        
        for name in self.services:
            visit(name, [])
        
        return order


def main():
    """主函数"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="服务依赖管理器")
    parser.add_argument("--check", "-c", help="检查指定服务状态")
    parser.add_argument("--wait", "-w", help="等待服务就绪")
    parser.add_argument("--report", "-r", action="store_true", help="生成状态报告")
    parser.add_argument("--order", "-o", action="store_true", help="显示启动顺序")
    parser.add_argument("--timeout", "-t", type=int, default=60, help="超时时间（秒）")
    parser.add_argument("--json", "-j", action="store_true", help="JSON格式输出")
    
    args = parser.parse_args()
    
    manager = ServiceDependencyManager()
    
    if args.check:
        is_healthy = manager.check_service_health(args.check)
        result = {
            "service": args.check,
            "healthy": is_healthy,
            "status": manager.services[args.check].status.value
        }
        print(json.dumps(result, indent=2) if args.json else f"Service {args.check}: {'healthy' if is_healthy else 'unhealthy'}")
    
    elif args.wait:
        is_ready = manager.wait_for_service(args.wait, args.timeout)
        result = {
            "service": args.wait,
            "ready": is_ready,
            "timeout": args.timeout
        }
        print(json.dumps(result, indent=2) if args.json else f"Service {args.wait}: {'ready' if is_ready else 'timeout'}")
    
    elif args.report:
        report = manager.get_service_status_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))
    
    elif args.order:
        try:
            order = manager.validate_startup_order()
            result = {"startup_order": order}
            print(json.dumps(result, indent=2) if args.json else " -> ".join(order))
        except ValueError as e:
            print(f"Error: {e}")
    
    else:
        report = manager.get_service_status_report()
        print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
