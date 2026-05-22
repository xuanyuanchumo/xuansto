from __future__ import annotations

import ast
import inspect
import threading

from xuansto_mcp import __version__
from xuansto_mcp.core.config import _config_lock, reload_config


def test_cli_uses_registered_tool_names():
    import xuansto_mcp.cli as cli_mod

    source = inspect.getsource(cli_mod)
    tree = ast.parse(source)

    private_access_count = 0
    registered_import_count = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if (
                isinstance(node.value, ast.Attribute)
                and isinstance(node.value.value, ast.Name)
                and node.value.attr == "_tool_manager"
                and node.attr == "_tools"
            ):
                private_access_count += 1
        if isinstance(node, ast.ImportFrom):
            if node.level >= 1 and node.module and node.module.endswith("server"):
                for alias in node.names:
                    if alias.name == "_REGISTERED_TOOL_NAMES":
                        registered_import_count += 1

    assert registered_import_count >= 1, "cli.py should import _REGISTERED_TOOL_NAMES from server"
    assert private_access_count == 0, (
        f"cli.py should not access mcp._tool_manager._tools directly, found {private_access_count} access(es)"
    )


def test_config_lock_exists():
    assert isinstance(_config_lock, type(threading.Lock())), (
        f"_config_lock should be a threading.Lock, got {type(_config_lock)}"
    )


def test_config_reload_thread_safe():
    source = inspect.getsource(reload_config)
    assert "_config_lock" in source, "reload_config should reference _config_lock"
    assert "with _config_lock" in source, "reload_config should use 'with _config_lock' to protect global assignments"


def test_version_is_341():
    assert __version__ == "3.5.0"
