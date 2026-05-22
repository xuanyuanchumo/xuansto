import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.security_scan import (
    _is_likely_false_positive,
    _calculate_security_score,
    _inline_agentic_scan,
    _VULNERABILITY_PATTERNS,
)


def test_vulnerability_patterns_have_cwe():
    for vuln in _VULNERABILITY_PATTERNS:
        assert "cwe_id" in vuln, f"{vuln['type']} missing cwe_id"
        assert "cwe_url" in vuln, f"{vuln['type']} missing cwe_url"
        assert "remediation" in vuln, f"{vuln['type']} missing remediation"
        assert vuln["cwe_id"].startswith("CWE-"), f"{vuln['type']} invalid cwe_id format"


def test_false_positive_env_variable():
    assert _is_likely_false_positive("hardcoded_secret", 'api_key = os.environ["API_KEY"]', []) is True


def test_false_positive_real_secret():
    assert _is_likely_false_positive("hardcoded_secret", 'api_key = "sk-1234567890"', []) is False


def test_false_positive_safe_subprocess():
    assert _is_likely_false_positive("unsafe_shell", "subprocess.run(['ls'], shell=False)", []) is True


def test_security_score_no_vulns():
    assert _calculate_security_score([]) == 100


def test_security_score_with_vulns():
    vulns = [
        {"severity": "critical", "likely_false_positive": False},
        {"severity": "high", "likely_false_positive": False},
    ]
    score = _calculate_security_score(vulns)
    assert score == 100 - 25 - 15


def test_security_score_fp_not_counted():
    vulns = [
        {"severity": "critical", "likely_false_positive": True},
        {"severity": "high", "likely_false_positive": False},
    ]
    score = _calculate_security_score(vulns)
    assert score == 100 - 15


def test_inline_scan_returns_cwe_fields(tmp_path: Path):
    (tmp_path / "app.py").write_text('api_key = "hardcoded-secret-value"\n', encoding="utf-8")
    result = _inline_agentic_scan(str(tmp_path), "low")
    assert result["security_score"] < 100
    if result["vulnerabilities"]:
        vuln = result["vulnerabilities"][0]
        assert "cwe_id" in vuln
        assert "remediation" in vuln
        assert "likely_false_positive" in vuln
