from __future__ import annotations

import re
from pathlib import Path

from xuansto_mcp import __version__
from xuansto_mcp.server import mcp


def test_version_is_340():
    assert __version__ == "8.0.0"


def test_server_instructions_version():
    assert "v8.0.0" in mcp.instructions


def test_pyproject_version():
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    content = pyproject_path.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None
    assert match.group(1) == "8.0.0"
