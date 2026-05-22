import pytest
from pathlib import Path

from xuansto_mcp.tools.quality_gate_check import (
    _check_gate_007,
    _check_comment_language,
    _check_file_encoding,
    _check_script_security,
    INLINE_CHECKS,
    register,
)

from mcp.server.fastmcp import FastMCP


class TestCheckGate007:
    def test_pass_when_no_encoding_issues(self, tmp_path):
        (tmp_path / "app.py").write_text("print('hello')", encoding="utf-8")
        (tmp_path / "main.js").write_text("console.log('hi');", encoding="utf-8")
        result = _check_gate_007(str(tmp_path))
        assert result["status"] == "PASS"

    def test_fail_on_bom(self, tmp_path):
        (tmp_path / "bom.py").write_bytes(b"\xef\xbb\xbfprint('hello')")
        result = _check_gate_007(str(tmp_path))
        assert result["status"] == "FAIL"
        assert any("BOM" in i["issue"] for i in result["details"]["issues"])

    def test_fail_on_replacement_char(self, tmp_path):
        bad_bytes = b"print('\xff\xff')"
        (tmp_path / "bad.py").write_bytes(bad_bytes)
        result = _check_gate_007(str(tmp_path))
        assert result["status"] == "FAIL"
        assert any("U+FFFD" in i["issue"] for i in result["details"]["issues"])

    def test_skip_excluded_dirs(self, tmp_path):
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "pkg.js").write_bytes(b"\xef\xbb\xbfconsole.log('bom');")
        (tmp_path / "good.py").write_text("x = 1", encoding="utf-8")
        result = _check_gate_007(str(tmp_path))
        assert result["status"] == "PASS"


class TestCheckCommentLanguage:
    def test_pass_pure_chinese_comments(self, tmp_path):
        (tmp_path / "main.py").write_text("# 这是一个中文注释\nx = 1\n# 另一个中文注释\n", encoding="utf-8")
        result = _check_comment_language(str(tmp_path))
        assert result["status"] == "PASS"

    def test_pass_pure_english_comments(self, tmp_path):
        (tmp_path / "main.py").write_text("# This is an English comment\nx = 1\n# Another English comment\n", encoding="utf-8")
        result = _check_comment_language(str(tmp_path))
        assert result["status"] == "PASS"

    def test_fail_mixed_language_comments(self, tmp_path):
        content = "# This is English\n# 这是中文\n# More English here\n# 更多中文注释\n# Another EN comment\n# 继续中文\n"
        (tmp_path / "mixed.py").write_text(content, encoding="utf-8")
        result = _check_comment_language(str(tmp_path))
        assert result["status"] == "FAIL"
        assert len(result["details"]["mixed_files"]) > 0

    def test_js_block_comments(self, tmp_path):
        content = "/* This is English block comment */\n/* 这是中文块注释 */\n"
        (tmp_path / "app.js").write_text(content, encoding="utf-8")
        result = _check_comment_language(str(tmp_path))
        assert result["status"] == "FAIL"


class TestCheckFileEncoding:
    def test_pass_all_utf8(self, tmp_path):
        (tmp_path / "app.py").write_text("print('hello')", encoding="utf-8")
        (tmp_path / "config.json").write_text('{"key": "value"}', encoding="utf-8")
        result = _check_file_encoding(str(tmp_path))
        assert result["status"] == "PASS"

    def test_fail_on_bom(self, tmp_path):
        (tmp_path / "bom.py").write_bytes(b"\xef\xbb\xbfprint('hello')")
        result = _check_file_encoding(str(tmp_path))
        assert result["status"] == "FAIL"
        assert len(result["details"]["bom_files"]) > 0

    def test_fail_on_non_utf8(self, tmp_path):
        (tmp_path / "bad.py").write_bytes("print('你好')".encode("gbk"))
        result = _check_file_encoding(str(tmp_path))
        assert result["status"] == "FAIL"
        assert len(result["details"]["non_utf8_files"]) > 0

    def test_skip_non_text_files(self, tmp_path):
        (tmp_path / "image.png").write_bytes(b"\x89PNG\r\n")
        (tmp_path / "app.py").write_text("x = 1", encoding="utf-8")
        result = _check_file_encoding(str(tmp_path))
        assert result["status"] == "PASS"


class TestCheckScriptSecurity:
    def test_pass_no_scripts_dir(self, tmp_path):
        result = _check_script_security(str(tmp_path))
        assert result["status"] == "PASS"

    def test_pass_clean_scripts(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "deploy.sh").write_text("#!/bin/bash\necho 'deploying'\n", encoding="utf-8")
        result = _check_script_security(str(tmp_path))
        assert result["status"] == "PASS"

    def test_fail_hardcoded_secret(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "setup.sh").write_text("api_key=sk-1234567890abcdef\n", encoding="utf-8")
        result = _check_script_security(str(tmp_path))
        assert result["status"] == "FAIL"
        assert any(v["type"] == "hardcoded_secret" for v in result["details"]["vulnerabilities"])

    def test_fail_dangerous_command(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "clean.sh").write_text("rm -rf /tmp/old\n", encoding="utf-8")
        result = _check_script_security(str(tmp_path))
        assert result["status"] == "FAIL"
        assert any(v["type"] == "dangerous_command" for v in result["details"]["vulnerabilities"])

    def test_ignore_example_secrets(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "example.sh").write_text("api_key=your_api_key_example_here\n", encoding="utf-8")
        result = _check_script_security(str(tmp_path))
        assert result["status"] == "PASS"


class TestInlineChecksRegistry:
    def test_gate_007_registered(self):
        assert "GATE-007" in INLINE_CHECKS

    def test_comment_language_registered(self):
        assert "COMMENT-LANGUAGE" in INLINE_CHECKS

    def test_file_encoding_registered(self):
        assert "FILE-ENCODING" in INLINE_CHECKS

    def test_script_security_registered(self):
        assert "SCRIPT-SECURITY" in INLINE_CHECKS


class TestFallbackLogic:
    @pytest.mark.asyncio
    async def test_fallback_to_inline_when_script_missing(self, tmp_path):
        (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
        mcp = FastMCP("test")
        register(mcp)
        quality_gate_check = None
        for name, tool_fn in mcp._tool_manager._tools.items():
            if name == "quality_gate_check":
                quality_gate_check = tool_fn.fn
                break
        assert quality_gate_check is not None
        result = await quality_gate_check(gate_ids=["GATE-007"], project_path=str(tmp_path))
        checks = result["data"]["checks"]
        assert len(checks) == 1
        assert checks[0]["gate_id"] == "GATE-007"
        assert checks[0]["status"] != "SKIP"

    @pytest.mark.asyncio
    async def test_skip_when_no_script_no_inline(self, tmp_path):
        mcp = FastMCP("test")
        register(mcp)
        quality_gate_check = None
        for name, tool_fn in mcp._tool_manager._tools.items():
            if name == "quality_gate_check":
                quality_gate_check = tool_fn.fn
                break
        assert quality_gate_check is not None
        result = await quality_gate_check(gate_ids=["NONEXISTENT-GATE"], project_path=str(tmp_path))
        checks = result["data"]["checks"]
        assert len(checks) == 1
        assert checks[0]["status"] == "SKIP"
