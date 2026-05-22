from __future__ import annotations

import json
import subprocess
import logging
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
            "error": True,
            "code": "SCRIPT_NOT_FOUND",
            "message": f"脚本不存在: {script_path.name}",
            "details": {"script": str(script_path)},
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
            return {"error": False, "data": json.loads(output)}
        except json.JSONDecodeError:
            return {
                "error": False,
                "data": {"raw_output": output[:2000]},
                "parse_warning": "Output was not valid JSON",
            }

    except subprocess.TimeoutExpired:
        return {
            "error": True,
            "code": "TIMEOUT",
            "message": f"脚本执行超时({timeout}s): {script_path.name}",
        }
    except FileNotFoundError:
        return {
            "error": True,
            "code": "PYTHON_NOT_FOUND",
            "message": "Python解释器未找到，请确保python在PATH中",
        }
    except Exception as e:
        return {
            "error": True,
            "code": "EXECUTION_ERROR",
            "message": str(e),
        }
