import os
import sys
import tempfile
from pathlib import Path

SKILL_PATH = Path(__file__).resolve().parent.parent.parent / ".trae" / "skills" / "xuansto-skill"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools import hook_manage
from mcp.server.fastmcp import FastMCP


def test_register():
    mcp = FastMCP("test")
    hook_manage.register(mcp)
    assert True


def test_hook_profiles():
    assert "minimal" in hook_manage.HOOK_PROFILES
    assert "standard" in hook_manage.HOOK_PROFILES
    assert "strict" in hook_manage.HOOK_PROFILES
    assert len(hook_manage.HOOK_PROFILES["minimal"]) < len(hook_manage.HOOK_PROFILES["standard"])
    assert len(hook_manage.HOOK_PROFILES["standard"]) < len(hook_manage.HOOK_PROFILES["strict"])


def test_hook_scripts_map():
    assert "encoding-check" in hook_manage.HOOK_SCRIPTS_MAP
    assert hook_manage.HOOK_SCRIPTS_MAP["encoding-check"] == "check-encoding.py"


def test_inline_hook_logic_exists():
    assert "security-block" in hook_manage.INLINE_HOOK_LOGIC
    assert "dangerous-cmd-confirm" in hook_manage.INLINE_HOOK_LOGIC
    assert "auto-format" in hook_manage.INLINE_HOOK_LOGIC
    assert "console-log-detect" in hook_manage.INLINE_HOOK_LOGIC
    assert "type-check" in hook_manage.INLINE_HOOK_LOGIC
    assert "git-status-check" in hook_manage.INLINE_HOOK_LOGIC
    assert "decision-log-persist" in hook_manage.INLINE_HOOK_LOGIC


def test_security_block_pass():
    result = hook_manage._security_block_logic(".", {"command": "ls -la"})
    assert result["status"] == "pass"


def test_security_block_dangerous():
    result = hook_manage._security_block_logic(".", {"command": "rm -rf /"})
    assert result["status"] == "block"
    assert len(result["details"]["matched_patterns"]) > 0


def test_security_block_sudo():
    result = hook_manage._security_block_logic(".", {"command": "sudo apt install foo"})
    assert result["status"] == "block"


def test_security_block_drop_table():
    result = hook_manage._security_block_logic(".", {"command": "DROP TABLE users;"})
    assert result["status"] == "block"


def test_security_block_no_context():
    result = hook_manage._security_block_logic(".", None)
    assert result["status"] == "pass"


def test_dangerous_cmd_confirm_warn():
    result = hook_manage._dangerous_cmd_confirm_logic(".", {"command": "git push --force origin main"})
    assert result["status"] == "warn"
    assert len(result["details"]["matched_patterns"]) > 0


def test_dangerous_cmd_confirm_npm_publish():
    result = hook_manage._dangerous_cmd_confirm_logic(".", {"command": "npm publish"})
    assert result["status"] == "warn"


def test_dangerous_cmd_confirm_safe():
    result = hook_manage._dangerous_cmd_confirm_logic(".", {"command": "git commit -m 'fix'"})
    assert result["status"] == "pass"


def test_dangerous_cmd_confirm_no_context():
    result = hook_manage._dangerous_cmd_confirm_logic(".", None)
    assert result["status"] == "pass"


def test_auto_format_clean():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "src"
        src.mkdir()
        (src / "clean.py").write_text("x = 1\ny = 2\n")
        result = hook_manage._auto_format_logic(tmpdir)
        assert result["status"] == "pass"


def test_auto_format_trailing_whitespace():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "src"
        src.mkdir()
        (src / "messy.py").write_text("x = 1   \ny = 2\n")
        result = hook_manage._auto_format_logic(tmpdir)
        assert result["status"] == "warn"
        assert result["details"]["files_with_issues"] >= 1


def test_auto_format_missing_newline():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "src"
        src.mkdir()
        (src / "noeol.py").write_text("x = 1")
        result = hook_manage._auto_format_logic(tmpdir)
        assert result["status"] == "warn"


def test_auto_format_nonexistent_path():
    result = hook_manage._auto_format_logic("/nonexistent/path/xyz")
    assert result["status"] == "pass"


def test_console_log_detect_with_logs():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "src"
        src.mkdir()
        (src / "app.js").write_text("console.log('hello');\n")
        result = hook_manage._console_log_detect_logic(tmpdir)
        assert result["status"] == "warn"
        assert result["details"]["total_hits"] >= 1


def test_console_log_detect_clean():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "src"
        src.mkdir()
        (src / "app.js").write_text("function add(a, b) { return a + b; }\n")
        result = hook_manage._console_log_detect_logic(tmpdir)
        assert result["status"] == "pass"


def test_console_log_detect_ignores_test_files():
    with tempfile.TemporaryDirectory() as tmpdir:
        src = Path(tmpdir) / "src"
        src.mkdir()
        (src / "app.test.js").write_text("console.log('test');\n")
        result = hook_manage._console_log_detect_logic(tmpdir)
        assert result["status"] == "pass"


def test_type_check_no_ts():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = hook_manage._type_check_logic(tmpdir)
        assert result["status"] == "pass"


def test_type_check_ts_without_tsconfig():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.ts").write_text("const x: number = 1;\n")
        result = hook_manage._type_check_logic(tmpdir)
        assert result["status"] == "warn"
        assert result["details"]["has_tsconfig"] is False


def test_type_check_ts_with_tsconfig():
    with tempfile.TemporaryDirectory() as tmpdir:
        (Path(tmpdir) / "app.ts").write_text("const x: number = 1;\n")
        (Path(tmpdir) / "tsconfig.json").write_text("{}\n")
        result = hook_manage._type_check_logic(tmpdir)
        assert result["status"] == "pass"
        assert result["details"]["has_tsconfig"] is True


def test_decision_log_persist_creates_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        result = hook_manage._decision_log_persist_logic(tmpdir)
        assert result["status"] == "pass"
        assert (Path(tmpdir) / ".xuansto" / "decisions").exists()


def test_decision_log_persist_existing_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        decisions = Path(tmpdir) / ".xuansto" / "decisions"
        decisions.mkdir(parents=True)
        result = hook_manage._decision_log_persist_logic(tmpdir)
        assert result["status"] == "pass"
        assert result["details"]["created"] is False


def test_is_test_file():
    assert hook_manage._is_test_file(Path("src/app.test.ts")) is True
    assert hook_manage._is_test_file(Path("src/app_spec.js")) is False
    assert hook_manage._is_test_file(Path("tests/test_app.py")) is True
    assert hook_manage._is_test_file(Path("src/utils.ts")) is False
