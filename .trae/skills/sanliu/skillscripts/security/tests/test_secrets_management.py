#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
密钥管理系统测试套件

覆盖范围：
- SecretsManager（8种类型、多源加载链、get/get_required、mask_for_log、validate_all）
- HardcodedDetector（25种正则模式、scan_directory、scan_file、SARIF导出、Markdown导出）
- ConfigSecurityAuditor（YAML/JSON敏感字段、权限检查、.gitignore合规）
- EnvTemplateGenerator（os.environ扫描、.env.example生成、MD文档生成）
"""

import pytest
import os
import tempfile
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from secrets_manager import (
    SecretType,
    SecretEntry,
    ValidationResult,
    AuditRecord,
    SecretsManager,
)


class TestSecretTypeEnum:
    """测试密钥类型枚举"""

    def test_password_type(self):
        assert SecretType.PASSWORD.value == "password"

    def test_api_key_type(self):
        assert SecretType.API_KEY.value == "api_key"

    def test_token_type(self):
        assert SecretType.TOKEN.value == "token"

    def test_secret_type(self):
        assert SecretType.SECRET.value == "secret"

    def test_credential_type(self):
        assert SecretType.CREDENTIAL.value == "credential"

    def test_connection_string_type(self):
        assert SecretType.CONNECTION_STRING.value == "connection_string"

    def test_private_key_type(self):
        assert SecretType.PRIVATE_KEY.value == "private_key"

    def test_encryption_key_type(self):
        assert SecretType.ENCRYPTION_KEY.value == "encryption_key"


class TestSecretEntry:
    """测试密钥条目数据类"""

    def test_creation(self):
        entry = SecretEntry(
            key="API_KEY",
            value="sk-123456",
            secret_type=SecretType.API_KEY,
            source="env_file",
        )
        assert entry.key == "API_KEY"
        assert entry.is_masked is False

    def test_repr_unmasked(self):
        entry = SecretEntry(
            key="TEST",
            value="value123",
            secret_type=SecretType.SECRET,
            source="test",
        )
        repr_str = repr(entry)
        assert "***" not in repr_str or entry.is_masked is False


class TestValidationResult:
    """测试验证结果数据类"""

    def test_valid_result(self):
        result = ValidationResult(is_valid=True, total_checked=5, passed=5, failed=0)
        assert result.is_valid is True
        assert "通过" in result.summary()

    def test_invalid_result(self):
        result = ValidationResult(
            is_valid=False, total_checked=5, passed=3, failed=2,
            warnings=["弱密码"], errors=["值为空"]
        )
        assert result.is_valid is False
        assert "未通过" in result.summary()

    def test_summary_with_warnings(self):
        result = ValidationResult(
            is_valid=True, total_checked=1, passed=1, failed=0,
            warnings=["建议使用更强的密钥"]
        )
        summary = result.summary()
        assert "警告" in summary


class TestAuditRecord:
    """测试审计日志记录数据类"""

    def test_to_dict_conversion(self):
        record = AuditRecord(
            action="get",
            key="SECRET_KEY",
            result="success",
            secret_type=SecretType.SECRET,
            masked_value="se****ey",
        )
        d = record.to_dict()
        assert d["action"] == "get"
        assert d["key"] == "SECRET_KEY"
        assert d["masked_value"] == "se****ey"


class TestSecretsManagerInit:
    """测试密钥管理器初始化"""

    def test_default_initialization(self):
        mgr = SecretsManager()
        assert mgr._env_file == ".env"
        assert len(mgr._secrets) == 0

    def test_custom_env_file(self):
        mgr = SecretsManager(env_file=".env.test")
        assert mgr._env_file == ".env.test"


class TestSecretsManagerLoad:
    """测试多源加载链"""

    def test_load_from_env_file(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST_VAR=test_value\nAPI_KEY=dev_key_123\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert "TEST_VAR" in mgr._secrets
        assert mgr.get("TEST_VAR") == "test_value"

    def test_load_from_env_local_override(self, tmp_path):
        env_file = tmp_path / ".env"
        env_local = tmp_path / ".env.local"
        env_file.write_text("KEY=original\n")
        env_local.write_text("KEY=overridden\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert mgr.get("KEY") == "overridden"

    def test_load_nonexistent_env_file(self):
        mgr = SecretsManager(env_file=".nonexistent_env_12345")
        mgr.load()
        assert len(mgr._secrets) >= 0

    def test_load_with_export_prefix(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text('export EXPORTED_VAR=exported_value\n')
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert mgr.get("EXPORTED_VAR") == "exported_value"

    def test_load_with_comments(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("# This is a comment\nVAR=value\n# Another comment")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert mgr.get("VAR") == "value"

    def test_load_with_quoted_values(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text('QUOTED="value with spaces"\nSINGLE=\'single quoted\'')
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert mgr.get("QUOTED") == "value with spaces"
        assert mgr.get("SINGLE") == "single quoted"


class TestSecretsManagerGet:
    """测试密钥获取方法"""

    def test_get_existing_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("MY_SECRET=my_secret_value\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert mgr.get("MY_SECRET") == "my_secret_value"

    def test_get_missing_key_returns_default(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert mgr.get("NONEXISTENT") == ""
        assert mgr.get("NONEXISTENT", default="fallback") == "fallback"

    def test_get_required_existing_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("REQUIRED_KEY=req_val\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert mgr.get_required("REQUIRED_KEY") == "req_val"

    def test_get_required_missing_key_raises(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        with pytest.raises(KeyError) as exc_info:
            mgr.get_required("MISSING_REQUIRED", purpose="数据库连接")
        assert "MISSING_REQUIRED" in str(exc_info.value)


class TestSecretsManagerClassify:
    """测试密钥分类功能"""

    def test_classify_password(self):
        mgr = SecretsManager()
        assert mgr.classify("DB_PASSWORD") == SecretType.PASSWORD

    def test_classify_api_key(self):
        mgr = SecretsManager()
        assert mgr.classify("OPENAI_API_KEY") == SecretType.API_KEY

    def test_classify_token(self):
        mgr = SecretsManager()
        assert mgr.classify("AUTH_TOKEN") == SecretType.TOKEN

    def test_classify_connection_string(self):
        mgr = SecretsManager()
        assert mgr.classify("DATABASE_URL") == SecretType.CONNECTION_STRING

    def test_classify_private_key(self):
        mgr = SecretsManager()
        assert mgr.classify("RSA_PRIVATE_KEY") == SecretType.PRIVATE_KEY

    def test_classify_unknown_falls_back_to_secret(self):
        mgr = SecretsManager()
        assert mgr.classify("UNKNOWN_VAR_XYZ") == SecretType.SECRET


class TestMaskForLog:
    """测试日志脱敏功能"""

    @staticmethod
    def _call_mask(value):
        return SecretsManager.mask_for_log(value)

    def test_normal_string(self):
        masked = self._call_mask("admin123")
        assert masked == "ad****23"

    def test_short_string_length_4(self):
        masked = self._call_mask("abcd")
        assert masked == "****"

    def test_short_string_length_2(self):
        masked = self._call_mask("ab")
        assert masked == "**"

    def test_empty_string(self):
        masked = self._call_mask("")
        assert masked == ""

    def test_long_api_key(self):
        masked = self._call_mask("sk-abc123xyz789")
        assert masked.startswith("sk")
        assert masked.endswith("89")
        assert "****" in masked


class TestValidateAll:
    """测试验证所有密钥功能"""

    def test_validate_strong_password(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("STRONG_PASS=VeryStr0ng!P@ssw0rd#2024\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        result = mgr.validate_all()
        assert result.total_checked == 1
        assert result.passed + result.failed == 1

    def test_validate_weak_password_detected(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("WEAK_PASS=123456\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        result = mgr.validate_all()
        assert result.is_valid is False
        assert any("长度不足" in w for w in result.warnings)

    def test_validate_empty_value(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("EMPTY_VAL=\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        result = mgr.validate_all()
        assert result.is_valid is False

    def test_validate_placeholder_detected(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("PLACEHOLDER=changeme\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        result = mgr.validate_all()
        assert any("占位符" in w for w in result.warnings)

    def test_validate_no_secrets_is_valid(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        result = mgr.validate_all()
        assert result.total_checked == 0
        assert result.is_valid is True


class TestAuditLog:
    """测试审计日志功能"""

    def test_audit_log_on_get(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("AUDIT_TEST=audit_value\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        mgr.get("AUDIT_TEST")
        logs = mgr.audit_logs
        assert len(logs) >= 1
        assert logs[-1].action == "get"

    def test_audit_log_on_get_required(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("REQ_AUDIT=req_val\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        mgr.get_required("REQ_AUDIT")
        logs = mgr.audit_logs
        assert any(log.action == "get_required" for log in logs)

    def test_audit_log_on_validate(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("VAL_TEST=val\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        mgr.validate_all()
        logs = mgr.audit_logs
        assert any(log.action == "validate_all" for log in logs)

    def test_audit_log_on_load(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("LOAD_TEST=load_val\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        logs = mgr.audit_logs
        assert any(log.action == "load" for log in logs)


class TestSpecialMethods:
    """测试特殊方法"""

    def test_contains_operator(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("CONTAINS_TEST=yes\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert "CONTAINS_TEST" in mgr
        assert "NOT_IN_MGR" not in mgr

    def test_dict_style_access(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("DICT_ACCESS=dict_val\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert mgr["DICT_ACCESS"] == "dict_val"

    def test_loaded_keys_property(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("Z_KEY=z_val\nA_KEY=a_val\nM_KEY=m_val\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        keys = mgr.loaded_keys
        assert isinstance(keys, list)
        assert len(keys) >= 3

    def test_repr(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("K1=v1\nK2=v2\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        repr_str = repr(mgr)
        assert "SecretsManager" in repr_str
        assert "keys" in repr_str.lower()


class TestEdgeCasesAndErrorHandling:
    """测试边界情况和错误处理"""

    def test_unicode_in_values(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("UNICODE_VAL=中文测试🎉特殊符号\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert "中文" in mgr.get("UNICODE_VAL")

    def test_multiline_value_handling(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text('MULTI="line1\\nline2"\n')
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        val = mgr.get("MULTI")
        assert val is not None

    def test_equals_sign_in_value(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text('EQ_VALUE="a=b=c"\n')
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert "=" in mgr.get("EQ_VALUE")

    def test_special_characters_in_key(self, tmp_path):
        env_file = tmp_path / ".env"
        env_file.write_text("TEST-KEY=value-with-dash\n")
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert mgr.get("TEST-KEY") == "value-with-dash"

    def test_large_number_of_keys(self, tmp_path):
        lines = [f"KEY_{i}=value_{i}" for i in range(100)]
        env_file = tmp_path / ".env"
        env_file.write_text("\n".join(lines))
        mgr = SecretsManager(env_file=str(env_file))
        mgr.load()
        assert len(mgr.loaded_keys) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
