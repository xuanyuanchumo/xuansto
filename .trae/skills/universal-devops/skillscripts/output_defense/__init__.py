"""
Universal DevOps v6.0 - 四维度输出防线（4D Output Defense）模块

本模块实现完整的输出质量保障体系，包含四层纵深防御：
  Layer 1: PromptEngineeringLayer  - 提示词工程层（结构化模板、Few-shot、上下文裁剪、角色一致性）
  Layer 2: CapabilityGuard        - 原生能力约束层（权限白名单、频率限制、沙箱、命令过滤）
  Layer 3: RuleValidationEngine   - 底层规则校验层（格式验证、编码规范、安全策略、文档完整性）
  Layer 4: FallbackRecovery       - 兜底恢复机制（降级策略、自动重试、状态回滚、人工介入）
"""

from .prompt_engineering_layer import (
    ChainOfThoughtTemplate,
    ReActTemplate,
    TreeOfThoughtsTemplate,
    PromptTemplate,
    FewShotExample,
    ContextWindow,
    RoleProfile,
    PromptEngineeringLayer,
)

from .capability_guard import (
    PermissionPolicy,
    RateLimitConfig,
    SandboxConfig,
    TokenBucket,
    ToolPermissionManager,
    RateLimiter,
    FileSandbox,
    CommandSecurityFilter,
    CapabilityGuard,
)

from .rule_validation_engine import (
    ValidationResult,
    BaseValidator,
    SchemaValidator,
    CodeStyleValidator,
    SecurityPolicyValidator,
    DocumentIntegrityValidator,
    RuleValidationEngine,
)

from .fallback_recovery import (
    FallbackLevel,
    FallbackStrategy,
    FallbackContext,
    FallbackRecovery,
)

__all__ = [
    "PromptEngineeringLayer",
    "CapabilityGuard",
    "RuleValidationEngine",
    "FallbackRecovery",
    "ChainOfThoughtTemplate",
    "ReActTemplate",
    "TreeOfThoughtsTemplate",
    "PromptTemplate",
    "FewShotExample",
    "ContextWindow",
    "RoleProfile",
    "PermissionPolicy",
    "RateLimitConfig",
    "SandboxConfig",
    "TokenBucket",
    "ToolPermissionManager",
    "RateLimiter",
    "FileSandbox",
    "CommandSecurityFilter",
    "ValidationResult",
    "BaseValidator",
    "SchemaValidator",
    "CodeStyleValidator",
    "SecurityPolicyValidator",
    "DocumentIntegrityValidator",
    "FallbackLevel",
    "FallbackStrategy",
    "FallbackContext",
]
