from __future__ import annotations

import re
from pathlib import Path

from xuansto_mcp import __version__

EXPECTED = "5.0.0"
ROOT = Path(__file__).resolve().parent.parent


def test_init_version():
    assert __version__ == EXPECTED


def test_server_instructions_version():
    server_py = ROOT / "src" / "xuansto_mcp" / "server.py"
    content = server_py.read_text(encoding="utf-8")
    assert f"v{EXPECTED}" in content


def test_pyproject_version():
    pyproject = ROOT / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    assert match is not None
    assert match.group(1) == EXPECTED


def test_all_versions_equal():
    server_py = ROOT / "src" / "xuansto_mcp" / "server.py"
    pyproject = ROOT / "pyproject.toml"

    init_ver = __version__

    server_content = server_py.read_text(encoding="utf-8")
    server_match = re.search(rf"v(\d+\.\d+\.\d+)", server_content)
    server_ver = server_match.group(1) if server_match else None

    pyproject_content = pyproject.read_text(encoding="utf-8")
    pyproject_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_content, re.MULTILINE)
    pyproject_ver = pyproject_match.group(1) if pyproject_match else None

    assert init_ver == server_ver == pyproject_ver == EXPECTED
