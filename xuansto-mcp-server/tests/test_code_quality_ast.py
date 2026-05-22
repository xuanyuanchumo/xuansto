import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from xuansto_mcp.tools.code_simplify import (
    _calculate_cyclomatic_complexity,
    _calculate_quality_score,
    _analyze_python_ast,
    _inline_simplify,
)
import ast


def test_cyclomatic_complexity_simple():
    source = "def simple():\n    return 1\n"
    tree = ast.parse(source)
    func = tree.body[0]
    assert _calculate_cyclomatic_complexity(func) == 1


def test_cyclomatic_complexity_with_branches():
    source = "def branched(x):\n    if x > 0:\n        return 1\n    elif x < 0:\n        return -1\n    else:\n        return 0\n"
    tree = ast.parse(source)
    func = tree.body[0]
    complexity = _calculate_cyclomatic_complexity(func)
    assert complexity >= 3


def test_quality_score_no_issues():
    score = _calculate_quality_score([], 100)
    assert score == 100


def test_quality_score_with_issues():
    suggestions = [{"severity": "high"}, {"severity": "medium"}]
    score = _calculate_quality_score(suggestions, 100)
    assert score < 100
    assert score >= 0


def test_analyze_python_ast_detects_complex(tmp_path: Path):
    complex_code = "def complex_func(x, y, z):\n"
    for i in range(12):
        complex_code += f"    if x > {i}: pass\n"
    (tmp_path / "complex.py").write_text(complex_code, encoding="utf-8")
    suggestions: list[dict] = []
    by_type: dict = {}
    _analyze_python_ast(tmp_path / "complex.py", "complex.py", suggestions, by_type)
    assert any(s["type"] == "high_complexity" for s in suggestions)


def test_inline_simplify_returns_quality_score(tmp_path: Path):
    (tmp_path / "simple.py").write_text("def hello():\n    print('hello')\n", encoding="utf-8")
    result = _inline_simplify(str(tmp_path), "dir")
    assert "quality_score" in result
    assert "analysis_level" in result
    assert result["analysis_level"] == "ast"


def test_inline_simplify_text_level_for_js(tmp_path: Path):
    (tmp_path / "app.js").write_text("function hello() { console.log('hello'); }\n", encoding="utf-8")
    result = _inline_simplify(str(tmp_path), "dir")
    assert result["analysis_level"] == "text_level"
