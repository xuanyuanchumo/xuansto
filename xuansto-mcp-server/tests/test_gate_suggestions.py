import pytest

from xuansto_mcp.tools.quality_gate_check import (
    _check_gate_007,
    _check_comment_language,
    _check_script_security,
    INLINE_CHECKS,
)


class TestGate007Suggestion:
    def test_fail_includes_suggestion(self, tmp_path):
        (tmp_path / "bom.py").write_bytes(b"\xef\xbb\xbfprint('hello')")
        result = _check_gate_007(str(tmp_path))
        assert result["status"] == "FAIL"
        assert "suggestion" in result
        assert "dos2unix" in result["suggestion"]
        assert "bom.py" in result["suggestion"]

    def test_fail_suggestion_contains_file_list(self, tmp_path):
        (tmp_path / "a.py").write_bytes(b"\xef\xbb\xbfx = 1")
        (tmp_path / "b.js").write_bytes(b"\xef\xbb\xbfy = 2")
        result = _check_gate_007(str(tmp_path))
        assert result["status"] == "FAIL"
        assert "a.py" in result["suggestion"]
        assert "b.js" in result["suggestion"]


class TestScriptSecuritySuggestion:
    def test_fail_includes_suggestion(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "setup.sh").write_text("api_key=sk-1234567890abcdef\n", encoding="utf-8")
        result = _check_script_security(str(tmp_path))
        assert result["status"] == "FAIL"
        assert "suggestion" in result
        assert "硬编码密钥" in result["suggestion"]
        assert "环境变量" in result["suggestion"]

    def test_fail_suggestion_contains_issue_detail(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "clean.sh").write_text("rm -rf /tmp/old\n", encoding="utf-8")
        result = _check_script_security(str(tmp_path))
        assert result["status"] == "FAIL"
        assert "suggestion" in result
        assert "危险命令" in result["suggestion"]

    def test_fail_suggestion_contains_file_reference(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "deploy.sh").write_text("password=mypassword123\n", encoding="utf-8")
        result = _check_script_security(str(tmp_path))
        assert result["status"] == "FAIL"
        assert "suggestion" in result
        assert "硬编码密钥" in result["suggestion"]


class TestCommentLanguageSuggestion:
    def test_fail_includes_suggestion(self, tmp_path):
        content = "# This is English\n# 这是中文\n# More English here\n# 更多中文注释\n# Another EN comment\n# 继续中文\n"
        (tmp_path / "mixed.py").write_text(content, encoding="utf-8")
        result = _check_comment_language(str(tmp_path))
        assert result["status"] == "FAIL"
        assert "suggestion" in result
        assert "统一注释语言" in result["suggestion"]
        assert "mixed.py" in result["suggestion"]

    def test_fail_suggestion_contains_file_list(self, tmp_path):
        py_content = "# English comment\n# 中文注释\n# More English\n# 更多中文\n# EN again\n# 中文继续\n"
        (tmp_path / "file1.py").write_text(py_content, encoding="utf-8")
        js_content = "// English comment\n// 中文注释\n// More English\n// 更多中文\n// EN again\n// 中文继续\n"
        (tmp_path / "file2.js").write_text(js_content, encoding="utf-8")
        result = _check_comment_language(str(tmp_path))
        assert result["status"] == "FAIL"
        assert "suggestion" in result
        assert "file1.py" in result["suggestion"]
        assert "file2.js" in result["suggestion"]


class TestAllInlineChecksSuggestion:
    @pytest.mark.parametrize("gate_id", [k for k, v in INLINE_CHECKS.items() if v is not None])
    def test_fail_response_has_suggestion(self, gate_id, tmp_path):
        check_fn = INLINE_CHECKS[gate_id]
        result = check_fn(str(tmp_path))
        if result["status"] == "FAIL":
            assert "suggestion" in result, f"Gate {gate_id} FAIL response missing 'suggestion' field"
            assert isinstance(result["suggestion"], str)
            assert len(result["suggestion"]) > 0
