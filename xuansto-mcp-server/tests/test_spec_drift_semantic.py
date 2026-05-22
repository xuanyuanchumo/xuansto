import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.spec_drift_detect import _parse_python_ast, _match_spec_to_ast, _inline_spec_drift


def test_parse_python_ast_extracts_symbols(tmp_path: Path):
    (tmp_path / "app.py").write_text("class UserService:\n    def get_user(self): pass\n\ndef helper(): pass\n", encoding="utf-8")
    symbols = _parse_python_ast(str(tmp_path))
    names = [s["name"] for s in symbols]
    assert "userservice" in names
    assert "userservice.get_user" in names
    assert "helper" in names


def test_parse_python_ast_empty_dir(tmp_path: Path):
    symbols = _parse_python_ast(str(tmp_path))
    assert symbols == []


def test_match_spec_to_ast_finds_match():
    symbols = [
        {"name": "userservice", "type": "class", "file": "app.py", "line": 1},
        {"name": "userservice.get_user", "type": "method", "file": "app.py", "line": 2},
    ]
    matches = _match_spec_to_ast("Implement user service get_user", symbols)
    assert len(matches) > 0
    assert any("user" in m["name"] for m in matches)


def test_inline_spec_drift_ast_level(tmp_path: Path):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    (spec_dir / "tasks.md").write_text("- [ ] Task 1: Implement user service\n- [ ] Task 2: Build payment module\n", encoding="utf-8")
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "user_service.py").write_text("class UserService:\n    def get_user(self): pass\n", encoding="utf-8")
    result = _inline_spec_drift(str(spec_dir), str(src_dir))
    assert result["analysis_level"] == "ast"
    assert "interface_coverage" in result


def test_inline_spec_drift_keyword_fallback(tmp_path: Path):
    spec_dir = tmp_path / "specs"
    spec_dir.mkdir()
    (spec_dir / "tasks.md").write_text("- [ ] Task 1: Implement auth module\n", encoding="utf-8")
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "auth.js").write_text("function login() {}", encoding="utf-8")
    result = _inline_spec_drift(str(spec_dir), str(src_dir))
    assert result["analysis_level"] == "keyword_match"
