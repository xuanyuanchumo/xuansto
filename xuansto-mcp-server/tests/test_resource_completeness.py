from __future__ import annotations

import inspect
from typing import Any

import pytest

from xuansto_mcp.resources import skill_resources


EXPECTED_RESOURCE_URIS = [
    "xuansto://config/skill",
    "xuansto://templates/{name}",
    "xuansto://sessions/latest",
    "xuansto://sessions/{session_id}",
    "xuansto://agents/{name}",
    "xuansto://agents/{layer}/{name}",
    "xuansto://loading/status",
    "xuansto://loading/requirements",
    "xuansto://metrics/summary",
    "xuansto://degradation/status",
    "xuansto://skill/constraints",
    "xuansto://agents/registry",
    "xuansto://gates/definitions",
    "xuansto://workflows/definitions",
    "xuansto://hooks/definitions",
    "xuansto://knowledge/stats",
    "xuansto://templates/index",
    "xuansto://commands/routes",
    "xuansto://session/state",
    "xuansto://health/status",
    "xuansto://audit/log",
    "xuansto://decisions/latest",
    "xuansto://workflows/active",
    "xuansto://agents/list",
    "xuansto://sessions/list",
    "xuansto://gates/list",
    "xuansto://workflows/list",
    "xuansto://audit/recent",
    "xuansto://decisions/recent",
    "xuansto://references/summary/{name}",
]

PARAMETERIZED_URIS = [
    "xuansto://templates/{name}",
    "xuansto://sessions/{session_id}",
    "xuansto://agents/{name}",
    "xuansto://agents/{layer}/{name}",
    "xuansto://references/summary/{name}",
]


class TestResourceModuleStructure:
    def test_skill_resources_module_importable(self):
        assert skill_resources is not None

    def test_skill_resources_has_register_function(self):
        assert hasattr(skill_resources, "register")
        assert callable(skill_resources.register)

    def test_register_function_signature(self):
        sig = inspect.signature(skill_resources.register)
        params = list(sig.parameters.keys())
        assert "mcp" in params


class TestResourceURICoverage:
    def test_resource_uri_count(self):
        source = inspect.getsource(skill_resources)
        resource_count = source.count("@mcp.resource(")
        assert resource_count >= 29, f"Expected at least 29 resource decorators, found {resource_count}"

    @pytest.mark.parametrize("uri", EXPECTED_RESOURCE_URIS)
    def test_resource_uri_defined_in_source(self, uri: str):
        source = inspect.getsource(skill_resources)
        assert uri in source, f"Resource URI '{uri}' should be defined in skill_resources.py"

    def test_all_expected_resource_uris_present(self):
        source = inspect.getsource(skill_resources)
        missing = [uri for uri in EXPECTED_RESOURCE_URIS if uri not in source]
        assert not missing, f"Missing resource URIs: {missing}"


class TestResourceHandlers:
    def test_each_resource_decorator_has_handler(self):
        source = inspect.getsource(skill_resources)
        resource_count = source.count("@mcp.resource(")
        def_count = source.count("def ") - 1
        assert def_count >= resource_count, (
            f"Each @mcp.resource decorator should have a handler function "
            f"(resources={resource_count}, defs={def_count})"
        )

    def test_resource_handlers_return_string(self):
        source = inspect.getsource(skill_resources)
        handler_functions = []
        lines = source.split("\n")
        in_resource = False
        for line in lines:
            if "@mcp.resource(" in line:
                in_resource = True
                continue
            if in_resource and "def " in line:
                func_name = line.strip().split("def ")[1].split("(")[0]
                handler_functions.append(func_name)
                in_resource = False

        for func_name in handler_functions:
            assert func_name in source, f"Resource handler '{func_name}' should exist in source"

    def test_degraded_resource_function_exists(self):
        assert hasattr(skill_resources, "_degraded_resource")
        assert callable(skill_resources._degraded_resource)


class TestParameterizedResources:
    @pytest.mark.parametrize("uri", PARAMETERIZED_URIS)
    def test_parameterized_uri_has_path_parameter(self, uri: str):
        assert "{" in uri and "}" in uri, f"Parameterized URI '{uri}' should contain {{param}}"

    def test_template_resource_has_name_parameter(self):
        source = inspect.getsource(skill_resources)
        assert 'xuansto://templates/{name}' in source
        assert "def template(name: str)" in source

    def test_reference_summary_has_name_parameter(self):
        source = inspect.getsource(skill_resources)
        assert 'xuansto://references/summary/{name}' in source
        assert "def reference_summary(name: str)" in source

    def test_session_by_id_has_session_id_parameter(self):
        source = inspect.getsource(skill_resources)
        assert 'xuansto://sessions/{session_id}' in source
        assert "def session_by_id(session_id: str)" in source

    def test_agent_by_name_has_name_parameter(self):
        source = inspect.getsource(skill_resources)
        assert 'xuansto://agents/{name}' in source
        assert "def agent_by_name(name: str)" in source

    def test_agent_by_layer_name_has_two_parameters(self):
        source = inspect.getsource(skill_resources)
        assert 'xuansto://agents/{layer}/{name}' in source
        assert "def agent_by_layer_name(layer: str, name: str)" in source


class TestResourceSubscription:
    def test_subscribe_resource_function_exists(self):
        assert hasattr(skill_resources, "subscribe_resource")
        assert callable(skill_resources.subscribe_resource)

    def test_unsubscribe_resource_function_exists(self):
        assert hasattr(skill_resources, "unsubscribe_resource")
        assert callable(skill_resources.unsubscribe_resource)

    def test_get_subscriptions_function_exists(self):
        assert hasattr(skill_resources, "get_subscriptions")
        assert callable(skill_resources.get_subscriptions)

    def test_subscribe_returns_dict(self):
        result = skill_resources.subscribe_resource("xuansto://test", "client1")
        assert isinstance(result, dict)
        assert result.get("subscribed") is True

    def test_unsubscribe_returns_dict(self):
        skill_resources.subscribe_resource("xuansto://test2", "client1")
        result = skill_resources.unsubscribe_resource("xuansto://test2", "client1")
        assert isinstance(result, dict)
        assert result.get("unsubscribed") is True


class TestResourceSafety:
    def test_is_safe_path_function_exists(self):
        assert hasattr(skill_resources, "_is_safe_path")
        assert callable(skill_resources._is_safe_path)
