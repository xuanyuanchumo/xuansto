from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


def test_main_default_stdio_transport():
    with patch.dict(os.environ, {}, clear=False):
        if "XUANSTO_TRANSPORT" in os.environ:
            del os.environ["XUANSTO_TRANSPORT"]

        with patch("xuansto_mcp.server.mcp") as mock_mcp, \
             patch("xuansto_mcp.server.setup_logging"), \
             patch("xuansto_mcp.core.config.start_config_watcher"), \
             patch("xuansto_mcp.core.database.init_db"), \
             patch("xuansto_mcp.tools.session_manage.restore_on_startup"), \
             patch("xuansto_mcp.tools.workflow_dispatch.load_on_startup"), \
             patch("xuansto_mcp.tools.agent_manage.load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.degradation_load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.metrics_load_on_startup"), \
             patch("xuansto_mcp.core.degradation.start_fallback_watcher"):
            from xuansto_mcp.server import main
            main()
            mock_mcp.run.assert_called_once_with(transport="stdio")


def test_main_streamable_http_transport():
    with patch.dict(os.environ, {
        "XUANSTO_TRANSPORT": "streamable-http",
        "XUANSTO_HOST": "0.0.0.0",
        "XUANSTO_PORT": "9000",
    }):
        with patch("xuansto_mcp.server.mcp") as mock_mcp, \
             patch("xuansto_mcp.server.setup_logging"), \
             patch("xuansto_mcp.core.config.start_config_watcher"), \
             patch("xuansto_mcp.core.database.init_db"), \
             patch("xuansto_mcp.tools.session_manage.restore_on_startup"), \
             patch("xuansto_mcp.tools.workflow_dispatch.load_on_startup"), \
             patch("xuansto_mcp.tools.agent_manage.load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.degradation_load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.metrics_load_on_startup"), \
             patch("xuansto_mcp.core.degradation.start_fallback_watcher"):
            from xuansto_mcp.server import main
            main()
            mock_mcp.run.assert_called_once_with(
                transport="streamable-http",
                host="0.0.0.0",
                port=9000,
            )


def test_main_streamable_http_default_host_port():
    with patch.dict(os.environ, {
        "XUANSTO_TRANSPORT": "streamable-http",
    }):
        with patch("xuansto_mcp.server.mcp") as mock_mcp, \
             patch("xuansto_mcp.server.setup_logging"), \
             patch("xuansto_mcp.core.config.start_config_watcher"), \
             patch("xuansto_mcp.core.database.init_db"), \
             patch("xuansto_mcp.tools.session_manage.restore_on_startup"), \
             patch("xuansto_mcp.tools.workflow_dispatch.load_on_startup"), \
             patch("xuansto_mcp.tools.agent_manage.load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.degradation_load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.metrics_load_on_startup"), \
             patch("xuansto_mcp.core.degradation.start_fallback_watcher"):
            from xuansto_mcp.server import main
            main()
            mock_mcp.run.assert_called_once_with(
                transport="streamable-http",
                host="127.0.0.1",
                port=8000,
            )


def test_main_explicit_stdio_transport():
    with patch.dict(os.environ, {"XUANSTO_TRANSPORT": "stdio"}):
        with patch("xuansto_mcp.server.mcp") as mock_mcp, \
             patch("xuansto_mcp.server.setup_logging"), \
             patch("xuansto_mcp.core.config.start_config_watcher"), \
             patch("xuansto_mcp.core.database.init_db"), \
             patch("xuansto_mcp.tools.session_manage.restore_on_startup"), \
             patch("xuansto_mcp.tools.workflow_dispatch.load_on_startup"), \
             patch("xuansto_mcp.tools.agent_manage.load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.degradation_load_on_startup"), \
             patch("xuansto_mcp.tools.server_health.metrics_load_on_startup"), \
             patch("xuansto_mcp.core.degradation.start_fallback_watcher"):
            from xuansto_mcp.server import main
            main()
            mock_mcp.run.assert_called_once_with(transport="stdio")
