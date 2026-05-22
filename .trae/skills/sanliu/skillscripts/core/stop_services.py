#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三省六部协同开发系统 - 服务停止脚本

停止所有运行中的服务，包括：
- 后端 API 服务
- 前端开发服务器
- Docker 容器（可选）

使用示例:
    python stop_services.py                    # 停止后端和前端服务
    python stop_services.py --stop-docker      # 同时停止 Docker 容器
    python stop_services.py --all              # 停止所有服务
    python stop_services.py --json             # JSON 格式输出
    python stop_services.py --markdown         # Markdown 格式输出

退出码:
    0 - 成功
    1 - 错误
    2 - 警告（部分服务停止失败）
"""

import subprocess
import sys
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any

from skillscripts.core.path_config_center import get_path_config

PROJECT_ROOT = get_path_config().SKILL_ROOT
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"

from skillscripts.utils.script_utils import (
    ScriptBase, ScriptResult, ScriptLogger, ExitCode, create_result
)


@dataclass
class ServiceStopResult:
    name: str
    success: bool
    message: str
    error: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "success": self.success,
            "message": self.message,
            "error": self.error
        }


class StopServicesScript(ScriptBase):
    DEFAULT_DESCRIPTION = "三省六部协同开发系统 - 服务停止脚本"
    DEFAULT_EPILOG = """
示例:
  python stop_services.py                    # 停止后端和前端服务
  python stop_services.py --stop-docker      # 同时停止 Docker 容器
  python stop_services.py --all              # 停止所有服务
  python stop_services.py --json             # JSON 格式输出
  python stop_services.py --markdown         # Markdown 格式输出

退出码:
  0 - 成功
  1 - 错误
  2 - 警告（部分服务停止失败）
"""
    
    def _add_arguments(self):
        self.parser.add_argument(
            "--stop-docker",
            action="store_true",
            help="同时停止 Docker 容器"
        )
        self.parser.add_argument(
            "--all",
            action="store_true",
            help="停止所有服务包括 Docker"
        )
        self.parser.add_argument(
            "--backend-only",
            action="store_true",
            help="仅停止后端服务"
        )
        self.parser.add_argument(
            "--frontend-only",
            action="store_true",
            help="仅停止前端服务"
        )
    
    def stop_backend(self) -> ServiceStopResult:
        self.logger.info("停止后端服务...")
        try:
            if os.name == 'nt':
                subprocess.run(
                    ["taskkill", "/F", "/IM", "python.exe", "/FI", "WINDOWTITLE eq *run.py*"],
                    capture_output=True
                )
                subprocess.run(
                    ["taskkill", "/F", "/IM", "uvicorn.exe"],
                    capture_output=True
                )
            else:
                subprocess.run(["pkill", "-f", "run.py"], capture_output=True)
                subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
            self.logger.success("后端服务已停止")
            return ServiceStopResult("Backend", True, "后端服务已停止")
        except Exception as e:
            self.logger.error(f"停止后端服务时出错: {e}")
            return ServiceStopResult("Backend", False, "停止失败", str(e))
    
    def stop_frontend(self) -> ServiceStopResult:
        self.logger.info("停止前端服务...")
        try:
            if os.name == 'nt':
                subprocess.run(
                    ["taskkill", "/F", "/IM", "node.exe", "/FI", "WINDOWTITLE eq *vite*"],
                    capture_output=True
                )
            else:
                subprocess.run(["pkill", "-f", "vite"], capture_output=True)
            self.logger.success("前端服务已停止")
            return ServiceStopResult("Frontend", True, "前端服务已停止")
        except Exception as e:
            self.logger.error(f"停止前端服务时出错: {e}")
            return ServiceStopResult("Frontend", False, "停止失败", str(e))
    
    def stop_docker(self) -> ServiceStopResult:
        self.logger.info("停止 Docker 容器...")
        try:
            result = subprocess.run(
                ["docker-compose", "down"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                self.logger.success("Docker 容器已停止")
                return ServiceStopResult("Docker", True, "Docker 容器已停止")
            else:
                self.logger.error(f"Docker 容器停止失败: {result.stderr}")
                return ServiceStopResult("Docker", False, "停止失败", result.stderr)
        except Exception as e:
            self.logger.error(f"停止 Docker 容器时出错: {e}")
            return ServiceStopResult("Docker", False, "停止失败", str(e))
    
    def run(self) -> int:
        results: List[ServiceStopResult] = []
        errors: List[str] = []
        warnings: List[str] = []
        
        stop_docker = self.args.stop_docker or self.args.all
        
        if self.args.backend_only:
            results.append(self.stop_backend())
        elif self.args.frontend_only:
            results.append(self.stop_frontend())
        else:
            results.append(self.stop_frontend())
            results.append(self.stop_backend())
            
            if stop_docker:
                results.append(self.stop_docker())
            else:
                self.logger.info("保留 Docker 容器运行（使用 --stop-docker 参数停止容器）")
        
        for r in results:
            if not r.success:
                errors.append(f"{r.name}: {r.error}")
        
        success = all(r.success for r in results)
        stopped_services = [r.name for r in results if r.success]
        failed_services = [r.name for r in results if not r.success]
        
        message_parts = []
        if stopped_services:
            message_parts.append(f"成功停止: {', '.join(stopped_services)}")
        if failed_services:
            message_parts.append(f"停止失败: {', '.join(failed_services)}")
        
        result = create_result(
            success=success,
            message=" | ".join(message_parts) if message_parts else "无服务需要停止",
            data={"services": [r.to_dict() for r in results]},
            errors=errors,
            warnings=warnings,
            duration_ms=self.get_duration_ms()
        )
        
        if self.args.json:
            self.output_json(result)
        elif self.args.markdown:
            self.output_markdown(result)
        else:
            self.output_console(result)
        
        if success:
            return ExitCode.EXIT_CODE_SUCCESS.value
        elif failed_services:
            return ExitCode.EXIT_CODE_WARNING.value
        return ExitCode.EXIT_CODE_ERROR.value


def main():
    script = StopServicesScript()
    return script.execute()


if __name__ == "__main__":
    sys.exit(main())
