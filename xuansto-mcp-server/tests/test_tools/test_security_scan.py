import pytest
from unittest.mock import patch, MagicMock
from mcp.server.fastmcp import FastMCP
from xuansto_mcp.tools.security_scan import (
    _inline_agentic_scan,
    _inline_dependency_scan,
    _calculate_security_score,
    _is_likely_false_positive,
    _parse_version,
    register,
)


@pytest.fixture
def mcp_server():
    return FastMCP("test-server")


def test_calculate_security_score_no_vulns():
    assert _calculate_security_score([]) == 100


def test_calculate_security_score_with_vulns():
    vulns = [{"severity": "critical"}, {"severity": "high"}]
    score = _calculate_security_score(vulns)
    assert score < 100
    assert score >= 0


def test_calculate_security_score_false_positive():
    vulns = [{"severity": "critical", "likely_false_positive": True}]
    assert _calculate_security_score(vulns) == 100


def test_is_likely_false_positive_env():
    assert _is_likely_false_positive("hardcoded_secret", "api_key = os.environ.get('KEY')", []) is True


def test_is_likely_false_positive_shell_false():
    assert _is_likely_false_positive("unsafe_shell", "subprocess.run(cmd, shell=False)", []) is True


def test_is_likely_false_positive_real():
    assert _is_likely_false_positive("hardcoded_secret", 'api_key = "sk-12345"', []) is False


def test_parse_version():
    assert _parse_version("2.5.1") == (2, 5, 1)
    assert _parse_version("v1.0") == (1, 0)
    assert _parse_version("3") == (3,)


def test_inline_agentic_scan_nonexistent():
    result = _inline_agentic_scan("/nonexistent/path", "medium")
    assert result["total"] == 0


def test_inline_agentic_scan_with_vuln(tmp_path):
    vuln_file = tmp_path / "vuln.py"
    vuln_file.write_text('api_key = "sk-hardcoded-key"\neval("1+1")\n', encoding="utf-8")
    result = _inline_agentic_scan(str(tmp_path), "critical")
    assert result["total"] > 0
    assert result["security_score"] < 100


def test_inline_agentic_scan_clean(tmp_path):
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("def hello():\n    return 'world'\n", encoding="utf-8")
    result = _inline_agentic_scan(str(tmp_path), "medium")
    assert result["security_score"] == 100


def test_inline_dependency_scan_no_deps(tmp_path):
    result = _inline_dependency_scan(str(tmp_path))
    assert result["total"] == 0


def test_inline_dependency_scan_with_requirements(tmp_path):
    req = tmp_path / "requirements.txt"
    req.write_text("Flask==1.0\nrequests>=2.30\n", encoding="utf-8")
    result = _inline_dependency_scan(str(tmp_path))
    assert result["total"] >= 2
    vuln = [d for d in result["dependencies"] if d["status"] == "potentially_vulnerable"]
    assert len(vuln) > 0


@pytest.mark.asyncio
async def test_security_scan_positive(mcp_server, tmp_path):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["security_scan"].fn
    with patch("xuansto_mcp.tools.security_scan.run_script") as mock_run:
        mock_run.return_value = {"error": True, "message": "script not found"}
        result = await tool_fn(target=str(tmp_path))
        assert result.get("error") is False


@pytest.mark.asyncio
async def test_security_scan_invalid_threshold(mcp_server):
    register(mcp_server)
    tool_fn = mcp_server._tool_manager._tools["security_scan"].fn
    with patch("xuansto_mcp.tools.security_scan.run_script") as mock_run:
        mock_run.return_value = {"error": True, "message": "script not found"}
        result = await tool_fn(target=".", severity_threshold="medium")
