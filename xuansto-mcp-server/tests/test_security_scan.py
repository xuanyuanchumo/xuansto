import pytest
import json
from pathlib import Path
from unittest.mock import patch
from mcp.server.fastmcp import FastMCP

from xuansto_mcp.tools.security_scan import (
    _inline_agentic_scan,
    _inline_dependency_scan,
    register,
)


@pytest.fixture
def tmp_project(tmp_path):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    return tmp_path


def test_inline_agentic_scan_detects_hardcoded_password(tmp_project):
    src_file = tmp_project / "src" / "config.py"
    src_file.write_text('password = "supersecret123"\napi_key = "sk-abc123"\n', encoding="utf-8")

    result = _inline_agentic_scan(str(tmp_project), "critical")

    vulns = result["vulnerabilities"]
    types = [v["type"] for v in vulns]
    assert "hardcoded_secret" in types
    assert result["by_severity"]["critical"] >= 2
    assert result["total"] >= 2

    for v in vulns:
        if v["type"] == "hardcoded_secret":
            assert v["severity"] == "critical"
            assert v["file"]
            assert v["line"] > 0
            assert v["pattern"]
            assert v["description"]


def test_inline_agentic_scan_detects_eval_exec(tmp_project):
    src_file = tmp_project / "src" / "runner.py"
    src_file.write_text('eval("1+1")\nexec("print(42)")\n', encoding="utf-8")

    result = _inline_agentic_scan(str(tmp_project), "critical")

    vulns = result["vulnerabilities"]
    types = [v["type"] for v in vulns]
    assert "eval_exec" in types
    assert result["by_severity"]["critical"] >= 2


def test_inline_agentic_scan_detects_sql_injection(tmp_project):
    src_file = tmp_project / "src" / "db.py"
    src_file.write_text('query = f"SELECT * FROM users WHERE id = {user_id}"\n', encoding="utf-8")

    result = _inline_agentic_scan(str(tmp_project), "high")

    vulns = result["vulnerabilities"]
    types = [v["type"] for v in vulns]
    assert "sql_injection" in types


def test_inline_agentic_scan_detects_unsafe_deserialization(tmp_project):
    src_file = tmp_project / "src" / "loader.py"
    src_file.write_text('import pickle\ndata = pickle.load(f)\nimport yaml\nobj = yaml.load(s)\n', encoding="utf-8")

    result = _inline_agentic_scan(str(tmp_project), "high")

    vulns = result["vulnerabilities"]
    types = [v["type"] for v in vulns]
    assert "unsafe_deserialization" in types


def test_inline_agentic_scan_detects_xss(tmp_project):
    src_file = tmp_project / "src" / "app.js"
    src_file.write_text('element.innerHTML = userInput;\ndocument.write(data);\n', encoding="utf-8")

    result = _inline_agentic_scan(str(tmp_project), "medium")

    vulns = result["vulnerabilities"]
    types = [v["type"] for v in vulns]
    assert "xss" in types


def test_inline_agentic_scan_detects_unsafe_shell(tmp_project):
    src_file = tmp_project / "src" / "cmd.py"
    src_file.write_text('import os\nos.system("rm -rf /")\nimport subprocess\nsubprocess.call(cmd, shell=True)\n', encoding="utf-8")

    result = _inline_agentic_scan(str(tmp_project), "medium")

    vulns = result["vulnerabilities"]
    types = [v["type"] for v in vulns]
    assert "unsafe_shell" in types


def test_inline_agentic_scan_severity_filtering(tmp_project):
    src_file = tmp_project / "src" / "mixed.py"
    src_file.write_text(
        'password = "secret"\neval("1+1")\n'
        'query = f"SELECT * FROM t WHERE id = {x}"\n'
        'element.innerHTML = data\n',
        encoding="utf-8",
    )

    critical_only = _inline_agentic_scan(str(tmp_project), "critical")
    for v in critical_only["vulnerabilities"]:
        assert v["severity"] == "critical"
    assert critical_only["by_severity"]["high"] == 0
    assert critical_only["by_severity"]["medium"] == 0

    high_and_above = _inline_agentic_scan(str(tmp_project), "high")
    severities = {v["severity"] for v in high_and_above["vulnerabilities"]}
    assert "critical" in severities
    assert "high" in severities
    assert "medium" not in severities

    all_results = _inline_agentic_scan(str(tmp_project), "low")
    all_severities = {v["severity"] for v in all_results["vulnerabilities"]}
    assert "critical" in all_severities
    assert "high" in all_severities
    assert "medium" in all_severities


def test_inline_agentic_scan_nonexistent_path():
    result = _inline_agentic_scan("/nonexistent/path/xyz", "medium")
    assert result["total"] == 0
    assert result["vulnerabilities"] == []
    assert result["by_severity"] == {"critical": 0, "high": 0, "medium": 0, "low": 0}


def test_inline_agentic_scan_empty_directory(tmp_path):
    result = _inline_agentic_scan(str(tmp_path), "medium")
    assert result["total"] == 0
    assert result["vulnerabilities"] == []


def test_inline_dependency_scan_checks_requirements_txt(tmp_project):
    req_file = tmp_project / "requirements.txt"
    req_file.write_text(
        "Flask==1.1.0\nDjango==3.1.0\nrequests==2.26.0\nPyYAML==5.3\nnumpy==1.21.0\n",
        encoding="utf-8",
    )

    result = _inline_dependency_scan(str(tmp_project))

    assert result["total"] == 5
    assert result["vulnerable_count"] == 3

    deps_by_name = {d["name"]: d for d in result["dependencies"]}
    assert deps_by_name["Flask"]["status"] == "potentially_vulnerable"
    assert deps_by_name["Django"]["status"] == "potentially_vulnerable"
    assert deps_by_name["PyYAML"]["status"] == "potentially_vulnerable"
    assert deps_by_name["requests"]["status"] == "ok"
    assert deps_by_name["numpy"]["status"] == "ok"


def test_inline_dependency_scan_checks_package_json(tmp_project):
    pkg_file = tmp_project / "package.json"
    pkg_file.write_text(
        json.dumps({
            "dependencies": {"express": "^4.18.0", "lodash": "~4.17.21"},
            "devDependencies": {"jest": "^29.0.0"},
        }),
        encoding="utf-8",
    )

    result = _inline_dependency_scan(str(tmp_project))

    assert result["total"] == 3
    names = [d["name"] for d in result["dependencies"]]
    assert "express" in names
    assert "lodash" in names
    assert "jest" in names


def test_inline_dependency_scan_no_files(tmp_project):
    result = _inline_dependency_scan(str(tmp_project))
    assert result["total"] == 0
    assert result["vulnerable_count"] == 0
    assert result["dependencies"] == []


def test_inline_dependency_scan_comments_and_empty_lines(tmp_project):
    req_file = tmp_project / "requirements.txt"
    req_file.write_text(
        "# This is a comment\n\nFlask==1.0.0\n# Another comment\nrequests==2.26.0\n",
        encoding="utf-8",
    )

    result = _inline_dependency_scan(str(tmp_project))

    assert result["total"] == 2
    names = [d["name"] for d in result["dependencies"]]
    assert "Flask" in names
    assert "requests" in names


def test_inline_dependency_scan_bare_dependency(tmp_project):
    req_file = tmp_project / "requirements.txt"
    req_file.write_text("some-package\n", encoding="utf-8")

    result = _inline_dependency_scan(str(tmp_project))

    assert result["total"] == 1
    assert result["dependencies"][0]["name"] == "some-package"
    assert result["dependencies"][0]["version"] == "unknown"
    assert result["dependencies"][0]["status"] == "ok"


@pytest.mark.asyncio
async def test_security_scan_registered():
    mcp = FastMCP("test")
    register(mcp)
    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]
    assert "security_scan" in tool_names


@pytest.mark.asyncio
async def test_security_scan_uses_inline_when_no_scripts(tmp_project):
    mcp = FastMCP("test")
    register(mcp)

    src_file = tmp_project / "src" / "vuln.py"
    src_file.write_text('password = "secret123"\n', encoding="utf-8")

    tool_fn = None
    for name, fn in mcp._tool_manager._tools.items():
        if name == "security_scan":
            tool_fn = fn
            break

    assert tool_fn is not None

    fake_scripts_dir = tmp_project / "nonexistent_scripts"
    fake_scripts_dir.mkdir()
    with patch("xuansto_mcp.tools.security_scan.SCRIPTS_DIR", fake_scripts_dir):
        result = await tool_fn.fn(target=str(tmp_project), severity_threshold="critical")

    assert result.get("error") is False
    data = result.get("data", {})
    assert "agentic_scan" in data
    assert data["agentic_scan"].get("degradation_level") == "inline"
    assert data["agentic_scan"]["total"] >= 1


@pytest.mark.asyncio
async def test_security_scan_degradation_level_in_response(tmp_project):
    mcp = FastMCP("test")
    register(mcp)

    tool_fn = None
    for name, fn in mcp._tool_manager._tools.items():
        if name == "security_scan":
            tool_fn = fn
            break

    fake_scripts_dir = tmp_project / "nonexistent_scripts"
    fake_scripts_dir.mkdir()
    with patch("xuansto_mcp.tools.security_scan.SCRIPTS_DIR", fake_scripts_dir):
        result = await tool_fn.fn(target=str(tmp_project))

    assert result.get("error") is False
    assert result.get("degradation_level") == "inline"
