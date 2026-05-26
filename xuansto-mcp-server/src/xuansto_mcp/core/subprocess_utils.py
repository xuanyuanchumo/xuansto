from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any

logger = logging.getLogger("xuansto-mcp")


def run_script(
    script_path: Path,
    args: list[str] | None = None,
    cwd: str = ".",
    timeout: int = 60,
) -> dict[str, Any]:
    if not script_path.exists():
        return {
            "status": "error",
            "data": None,
            "error": {"code": "SCRIPT_NOT_FOUND", "message": f"脚本不存在: {script_path.name}", "details": {"script": str(script_path)}},
            "metadata": {},
        }

    cmd = ["python", str(script_path)]
    if args:
        cmd.extend(args)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        if result.returncode != 0 and result.stderr:
            logger.warning("Script %s stderr: %s", script_path.name, result.stderr[:500])

        output = result.stdout.strip() if result.stdout else ""
        try:
            return {"status": "success", "data": json.loads(output), "error": None, "metadata": {}}
        except json.JSONDecodeError:
            return {
                "status": "success",
                "data": {"raw_output": output[:2000]},
                "error": None,
                "metadata": {"parse_warning": "Output was not valid JSON"},
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "data": None,
            "error": {"code": "TIMEOUT", "message": f"脚本执行超时({timeout}s): {script_path.name}"},
            "metadata": {},
        }
    except FileNotFoundError:
        return {
            "status": "error",
            "data": None,
            "error": {"code": "PYTHON_NOT_FOUND", "message": "Python解释器未找到，请确保python在PATH中"},
            "metadata": {},
        }
    except Exception as e:
        return {
            "status": "error",
            "data": None,
            "error": {"code": "EXECUTION_ERROR", "message": str(e)},
            "metadata": {},
        }
