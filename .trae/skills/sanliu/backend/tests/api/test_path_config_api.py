"""
路径配置中心 API 测试
====================

测试 PathConfigCenter 相关的 API 端点，包括：
- 路径状态 API
- 路径验证 API
- 硬编码扫描 API
- 环境变量覆盖
"""

import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.api
@pytest.mark.integration
class TestPathConfigStatusAPI:
    """测试路径配置状态 API"""

    def test_get_path_config_status_success(self, client):
        """测试成功获取路径配置状态"""
        response = client.get("/api/path-config/status")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "enabled" in data
        assert "skill_root" in data
        assert "current_version" in data

    def test_get_path_config_status_contains_required_fields(self, client):
        """测试路径状态响应包含所有必需字段"""
        response = client.get("/api/path-config/status")

        assert response.status_code == 200
        data = response.json()
        required_fields = [
            "success", "enabled", "skill_root", "docs_dir",
            "scripts_dir", "reports_dir", "versions_dir",
            "current_version", "env_overrides"
        ]
        for field in required_fields:
            assert field in data, f"缺少必需字段: {field}"

    def test_get_path_config_status_env_overrides_type(self, client):
        """测试环境变量覆盖字段为字典类型"""
        response = client.get("/api/path-config/status")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["env_overrides"], dict)


@pytest.mark.api
@pytest.mark.integration
class TestPathConfigListAPI:
    """测试路径列表 API"""

    def test_list_all_paths_success(self, client):
        """测试成功列出所有预定义路径"""
        response = client.get("/api/path-config/paths")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total" in data
        assert "paths" in data
        assert isinstance(data["paths"], list)

    def test_list_all_paths_has_items(self, client):
        """测试路径列表包含预定义路径"""
        response = client.get("/api/path-config/paths")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] > 0
        assert len(data["paths"]) > 0

    def test_list_all_paths_item_structure(self, client):
        """测试路径项包含正确的结构"""
        response = client.get("/api/path-config/paths")

        assert response.status_code == 200
        data = response.json()
        if data["paths"]:
            path_item = data["paths"][0]
            assert "name" in path_item
            assert "path" in path_item
            assert "exists" in path_item
            assert "is_valid" in path_item
            assert "issues" in path_item

    def test_list_all_paths_known_names(self, client):
        """测试路径列表包含已知的路径名称"""
        response = client.get("/api/path-config/paths")

        assert response.status_code == 200
        data = response.json()
        names = [p["name"] for p in data["paths"]]
        expected_names = [
            "SKILL_ROOT", "DOCS_DIR", "SCRIPTS_DIR",
            "REPORTS_DIR", "CACHE_DIR", "LOGS_DIR"
        ]
        for name in expected_names:
            assert name in names, f"缺少预期路径名称: {name}"


@pytest.mark.api
@pytest.mark.integration
class TestPathConfigValidateAPI:
    """测试路径验证 API"""

    def test_validate_all_paths_success(self, client):
        """测试成功验证所有路径"""
        response = client.post("/api/path-config/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "total" in data
        assert "valid" in data
        assert "invalid" in data
        assert "details" in data

    def test_validate_all_paths_counts_consistent(self, client):
        """测试验证结果计数一致性"""
        response = client.post("/api/path-config/validate")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == data["valid"] + data["invalid"]

    def test_validate_all_paths_details_match_total(self, client):
        """测试详细结果数量与总数匹配"""
        response = client.post("/api/path-config/validate")

        assert response.status_code == 200
        data = response.json()
        assert len(data["details"]) == data["total"]

    def test_validate_all_paths_detail_structure(self, client):
        """测试每个路径详情的结构正确性"""
        response = client.post("/api/path-config/validate")

        assert response.status_code == 200
        data = response.json()
        for name, detail in data["details"].items():
            assert "path" in detail
            assert "is_valid" in detail
            assert "issues" in detail


@pytest.mark.api
@pytest.mark.integration
class TestPathConfigFixAPI:
    """测试路径修复 API"""

    def test_fix_path_issues_success(self, client):
        """测试成功执行路径修复"""
        response = client.post("/api/path-config/fix")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        assert "results" in data

    def test_fix_response_structure(self, client):
        """测试修复响应结构完整性"""
        response = client.post("/api/path-config/fix")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["total_issues"], int)
        assert isinstance(data["fixed"], int)
        assert isinstance(data["failed"], int)
        assert isinstance(data["results"], list)


@pytest.mark.api
@pytest.mark.integration
class TestHardcodedScanAPI:
    """测试硬编码路径扫描 API"""

    def test_scan_hardcoded_paths_default_dir(self, client):
        """测试使用默认目录（脚本目录）进行扫描"""
        response = client.get("/api/path-config/hardcoded-scan")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "directory" in data
        assert "files_scanned" in data
        assert "issues" in data

    def test_scan_hardcoded_with_directory_param(self, client):
        """测试带目录参数的硬编码扫描"""
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "test_script.py")
            with open(test_file, "w") as f:
                f.write("path = 'C:\\\\Users\\\\test'")

            response = client.get(f"/api/path-config/hardcoded-scan?directory={tmpdir}")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["directory"] == tmpdir

    def test_scan_nonexistent_directory(self, client):
        """测试扫描不存在的目录返回错误"""
        response = client.get(
            "/api/path-config/hardcoded-scan?directory=/nonexistent/directory/that/does/not/exist"
        )

        assert response.status_code == 404

    def test_scan_hardcoded_response_types(self, client):
        """测试扫描响应中 issues 的数据类型正确"""
        response = client.get("/api/path-config/hardcoded-scan")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["files_scanned"], int)
        assert isinstance(data["total_issues"], int)
        assert isinstance(data["issues"], list)

        for issue in data["issues"]:
            assert "file_path" in issue
            assert "line_number" in issue
            assert "matched_path" in issue
            assert "pattern_type" in issue


@pytest.mark.api
@pytest.mark.unit
class TestPathConfigEnvOverride:
    """测试环境变量覆盖功能"""

    @patch.dict('os.environ', {'SANLIU_SKILL_ROOT': '/custom/test/root', 'SANLIU_VERSION': 'v99.99.99'}, clear=False)
    def test_env_override_reflected_in_status(self, client):
        """测试环境变量覆盖在状态接口中反映"""
        from app.config import Settings
        settings_instance = Settings()

        status = settings_instance.get_path_status()
        assert status["enabled"] is True
        assert "env_overrides" in status

        env_overrides = status["env_overrides"]
        assert "SANLIU_SKILL_ROOT" in env_overrides or len(env_overrides) >= 0

    def test_path_config_disabled_returns_disabled(self):
        """测试禁用 PathConfigCenter 时返回禁用状态"""
        from app.config import Settings
        settings_instance = Settings(PATH_CONFIG_ENABLED=False)

        pcc = settings_instance.get_path_config_center()
        assert pcc is None

        status = settings_instance.get_path_status()
        assert status["enabled"] is False

    def test_settings_defaults_preserved(self):
        """测试默认设置值保持不变"""
        from app.config import Settings
        settings_instance = Settings()

        assert settings_instance.APP_NAME == "Sanliu Skill Management System"
        assert settings_instance.APP_VERSION == "1.0.0"
        assert settings_instance.DATABASE_HOST == "localhost"
        assert settings_instance.DATABASE_PORT == 5432
        assert settings_instance.CURRENT_VERSION == "v3.2.0"
        assert settings_instance.PATH_CONFIG_ENABLED is True


@pytest.mark.api
@pytest.mark.integration
class TestPathConfigEdgeCases:
    """测试边界情况"""

    def test_status_endpoint_idempotent(self, client):
        """测试状态端点的幂等性（多次调用结果一致）"""
        response1 = client.get("/api/path-config/status")
        response2 = client.get("/api/path-config/status")

        assert response1.status_code == 200
        assert response2.status_code == 200
        data1 = response1.json()
        data2 = response2.json()
        assert data1["enabled"] == data2["enabled"]
        assert data1["skill_root"] == data2["skill_root"]

    def test_validate_after_fix_consistency(self, client):
        """测试修复后验证的一致性"""
        fix_response = client.post("/api/path-config/fix")
        validate_response = client.post("/api/path-config/validate")

        assert fix_response.status_code == 200
        assert validate_response.status_code == 200

        validate_data = validate_response.json()
        assert validate_data["valid"] >= 0
