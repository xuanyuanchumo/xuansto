#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
操作优先级控制器核心模块

功能：
1. 定义三级操作优先级（MANUAL / SCRIPT / COMMAND）
2. 根据任务上下文智能选择最优操作模式
3. 提供命令预演机制与危险命令拦截
4. 支持任务特征自动提取与决策树推理

优先级说明：
- MANUAL (第一优先级): Agent 自主手动操作文件，适用于精确编辑、复杂重构
- SCRIPT (第二优先级): 规划脚本操作，适用于批量处理、可复用流程
- COMMAND (第三优先级): 终端命令操作，需预演检查，适用于环境配置、依赖安装
"""

import re
import json
import logging
import shlex
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger(__name__)


class OperationPriority(Enum):
    """操作优先级枚举 - 三级优先级体系"""

    MANUAL = "manual"
    SCRIPT = "script"
    COMMAND = "command"

    @property
    def level(self) -> int:
        """优先级数值，数值越小优先级越高"""
        _level_map = {
            OperationPriority.MANUAL: 1,
            OperationPriority.SCRIPT: 2,
            OperationPriority.COMMAND: 3,
        }
        return _level_map[self]

    @property
    def description(self) -> str:
        """优先级描述"""
        _desc_map = {
            OperationPriority.MANUAL: "Agent自主手动操作文件",
            OperationPriority.SCRIPT: "规划脚本操作",
            OperationPriority.COMMAND: "终端命令操作，需预演",
        }
        return _desc_map[self]


class RiskLevel(Enum):
    """风险等级枚举"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def emoji(self) -> str:
        _emoji_map = {
            RiskLevel.LOW: "\U0001f7e2",
            RiskLevel.MEDIUM: "\U0001f7e1",
            RiskLevel.HIGH: "\U0001f534",
        }
        return _emoji_map[self]

    @property
    def label(self) -> str:
        _label_map = {
            RiskLevel.LOW: "低风险",
            RiskLevel.MEDIUM: "中风险",
            RiskLevel.HIGH: "高风险",
        }
        return _label_map[self]

    def __str__(self) -> str:
        return f"{self.emoji} {self.label}"


@dataclass
class TaskFeatures:
    """提取的任务特征数据类"""

    involves_file_operations: bool = False
    estimated_file_count: int = 0
    is_batch_operation: bool = False
    has_existing_script: bool = False
    requires_domain_experts: bool = False
    task_description: str = ""
    target_files: List[str] = field(default_factory=list)
    operation_types: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PreflightResult:
    """命令预演结果数据类"""

    command: str
    is_safe: bool
    risk_level: RiskLevel
    risk_reasons: List[str] = field(default_factory=list)
    impact_analysis: Dict[str, Any] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    blocked: bool = False
    block_reason: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["risk_level"] = self.risk_level.value
        return result


@dataclass
class DecisionResult:
    """决策结果数据类"""

    priority: OperationPriority
    reason: str
    confidence: float
    features: TaskFeatures
    alternatives: List[OperationPriority] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["priority"] = self.priority.value
        result["alternatives"] = [p.value for p in self.alternatives]
        result["features"] = self.features.to_dict()
        return result


class TaskFeatureExtractor:
    """任务特征提取器 - 从任务上下文中提取关键特征用于决策"""

    FILE_OPERATION_PATTERNS = {
        "read": [
            r"读\s*取?",
            r"读取",
            r"查看",
            r"浏览",
            r"\bread\b",
            r"open.*file",
            r"get.*content",
            r"查看.*内容",
            r"分析.*代码",
            r"检查.*文件",
        ],
        "write": [
            r"写\s*入?",
            r"写入",
            r"创建.*文件",
            r"生成.*文件",
            r"\bwrite\b",
            r"create.*file",
            r"生成.*代码",
            r"新建",
        ],
        "edit": [
            r"编\s*辑?",
            r"编辑",
            r"修改",
            r"改\s*动?",
            r"更新",
            r"\bedit\b",
            r"modify",
            r"update",
            r"调整",
            r"优化.*代码",
            r"修复.*bug",
            r"修正",
            r"替换",
        ],
        "delete": [
            r"删\s*除?",
            r"删除",
            r"移除",
            r"\bdelete\b",
            r"\bremove\b",
            r"清理",
        ],
        "rename": [
            r"重命名",
            r"改名",
            r"\brename\b",
            r"移动.*文件",
        ],
        "copy": [
            r"复制",
            r"拷贝",
            r"\bcopy\b",
            r"\bcp\b",
        ],
    }

    BATCH_OPERATION_KEYWORDS = [
        "批量", "所有", "全部", "多个", "一系列", "遍历", "循环",
        "batch", "all files", "multiple", "bulk", "each file",
        "glob", "wildcard", "*.py", "*.js",
    ]

    SCRIPT_INDICATORS = [
        "脚本", "自动化", "pipeline", "workflow", "ci/cd",
        "构建", "部署", "测试套件", "lint", "format",
        "script", "automation", "makefile", "task runner",
    ]

    DOMAIN_EXPERT_KEYWORDS = [
        "架构", "安全", "性能优化", "数据库设计", "分布式",
        "微服务", "领域模型", "DDD", "设计模式",
        "architecture", "security", "performance", "database design",
        "distributed", "microservice", "domain model",
    ]

    @classmethod
    def extract(cls, task_context: Dict[str, Any]) -> TaskFeatures:
        """
        从任务上下文中提取任务特征

        Args:
            task_context: 任务上下文字典，包含任务描述、目标文件等信息

        Returns:
            TaskFeatures: 提取的特征对象
        """
        features = TaskFeatures()
        desc = task_context.get("description", "") or task_context.get("task", "") or ""
        features.task_description = desc

        if not desc and isinstance(task_context.get("prompt"), str):
            desc = task_context["prompt"]
            features.task_description = desc

        features.involves_file_operations = cls._detect_file_operations(desc)
        features.operation_types = cls._detect_operation_types(desc)
        features.estimated_file_count = cls._estimate_file_count(task_context, desc)
        features.is_batch_operation = cls._detect_batch_operation(
            desc, features.estimated_file_count
        )
        features.has_existing_script = cls._check_script_availability(task_context)
        features.requires_domain_experts = cls._detect_domain_expert_need(desc)
        features.target_files = cls._extract_target_files(task_context)

        logger.debug("Task features extracted: %s", features.to_dict())
        return features

    @classmethod
    def _detect_file_operations(cls, text: str) -> bool:
        """检测是否涉及文件操作"""
        if not text:
            return False
        text_lower = text.lower()
        for patterns in cls.FILE_OPERATION_PATTERNS.values():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    return True
        file_indicators = [".py", ".js", ".ts", ".json", ".md", ".yaml", ".yml", ".html", ".css"]
        return any(ext in text_lower for ext in file_indicators)

    @classmethod
    def _detect_operation_types(cls, text: str) -> List[str]:
        """检测具体的操作类型列表"""
        if not text:
            return []
        detected = []
        text_lower = text.lower()
        for op_type, patterns in cls.FILE_OPERATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    if op_type not in detected:
                        detected.append(op_type)
                    break
        return detected

    @classmethod
    def _estimate_file_count(cls, context: Dict, desc: str) -> int:
        """估算涉及的文件数量"""
        target_files = context.get("target_files") or context.get("files") or []
        if isinstance(target_files, list) and len(target_files) > 0:
            return len(target_files)

        count_patterns = [
            (r"(\d+)\s*个?\s*文件", 1),
            (r"(\d+)\s*个?\s*[Ff]ile[s]?", 1),
            (r"[`\"']([^'\"]+)[`\"']\s*(?:和|以及|[,，]\s*)[`\"']([^'\"]+)[`\"']", 2),
        ]
        for pattern, group in count_patterns:
            match = re.search(pattern, desc)
            if match:
                try:
                    if group == 1:
                        return int(match.group(1))
                    else:
                        return 2
                except (ValueError, IndexError):
                    pass

        if any(kw in desc.lower() for kw in ["批量", "batch", "所有文件", "all files"]):
            return 5
        return 1

    @classmethod
    def _detect_batch_operation(cls, text: str, estimated_count: int) -> bool:
        """检测是否为批量操作"""
        if estimated_count >= 3:
            return True
        if not text:
            return False
        text_lower = text.lower()
        return any(kw in text_lower for kw in cls.BATCH_OPERATION_KEYWORDS)

    @classmethod
    def _check_script_availability(cls, context: Dict) -> bool:
        """检查是否有可用脚本"""
        script_hints = [
            context.get("has_existing_script"),
            context.get("script_available"),
            context.get("use_script"),
        ]
        if any(script_hints):
            return True
        desc = (context.get("description", "") or context.get("task", "") or "").lower()
        return any(indicator in desc for indicator in cls.SCRIPT_INDICATORS)

    @classmethod
    def _detect_domain_expert_need(cls, text: str) -> bool:
        """检测是否需要领域专家知识"""
        if not text:
            return False
        text_lower = text.lower()
        return any(kw in text_lower for kw in cls.DOMAIN_EXPERT_KEYWORDS)

    @classmethod
    def _extract_target_files(cls, context: Dict) -> List[str]:
        """提取目标文件列表"""
        files = context.get("target_files") or context.get("files") or []
        if isinstance(files, list):
            return [str(f) for f in files if f]
        if isinstance(files, str):
            return [files]
        return []


class OperationPriorityController:
    """
    操作优先级控制器

    职责：
    1. 接收任务上下文，通过特征提取器获取任务特征
    2. 运行决策树推理引擎，输出最优操作优先级
    3. 为 COMMAND 模式提供预演检查能力
    """

    DANGEROUS_COMMAND_PATTERNS = [
        (re.compile(r"rm\s+-rf\s+/$", re.IGNORECASE), "尝试删除根目录"),
        (re.compile(r"rm\s+-rf\s+/[^\s]*", re.IGNORECASE), "强制递归删除系统目录"),
        (re.compile(r"rm\s+-rf\s+\*\s*$", re.IGNORECASE), "强制递归删除当前目录所有内容"),
        (re.compile(r"DROP\s+TABLE", re.IGNORECASE), "删除数据库表操作"),
        (re.compile(r"DROP\s+DATABASE", re.IGNORECASE), "删除数据库操作"),
        (re.compile(r"TRUNCATE", re.IGNORECASE), "清空数据库表"),
        (re.compile(r"FORMAT\s+[A-Z]:", re.IGNORECASE), "格式化磁盘驱动器"),
        (re.compile(r"mkfs\.", re.IGNORECASE), "创建文件系统（格式化）"),
        (re.compile(r"dd\s+if=.*of=/dev/", re.IGNORECASE), "直接磁盘写入操作"),
        (re.compile(r">\s*/dev/sd[a-z]", re.IGNORECASE), "覆盖磁盘分区"),
        (re.compile(r"chmod\s+-R\s+777", re.IGNORECASE), "设置全局可写权限"),
        (re.compile(r"chown\s+-R", re.IGNORECASE), "递归更改文件所有权"),
        (re.compile(r":(){.*|};:", re.IGNORECASE), "Fork炸弹攻击模式"),
        (re.compile(r"curl.*\|\s*bash", re.IGNORECASE), "远程代码执行（管道到bash）"),
        (re.compile(r"wget.*\|\s*sh", re.IGNORECASE), "远程代码执行（管道到sh）"),
        (re.compile(r"shutdown\s+(?:-h|-P)\s+now", re.IGNORECASE), "立即关机"),
        (re.compile(r"reboot\s+(-f|--force)?$", re.IGNORECASE), "强制重启系统"),
        (re.compile(r"mv\s+/\s*/dev/null", re.IGNORECASE), "将根目录移至空设备"),
        (re.compile(r"git\s+push\s+--force\s+.*origin\s+master(?:$|\s)", re.IGNORECASE), "强制推送主分支"),
        (re.compile(r"git\s+reset\s+--hard\s+HEAD~\d+", re.IGNORECASE), "硬重置丢失提交"),
        (re.compile(r"DELETE\s+FROM\s+\w+\s+WHERE\s+1=1", re.IGNORECASE), "无条件删除记录"),
    ]

    DESTRUCTIVE_COMMAND_KEYWORDS = [
        ("rm", "删除文件/目录"),
        ("del", "删除文件(Windows)"),
        ("drop", "数据库删除"),
        ("truncate", "清空表"),
        ("format", "格式化"),
        ("mkfs", "创建文件系统"),
        ("shutdown", "关机"),
        ("reboot", "重启"),
    ]

    @staticmethod
    def decide(task_context: Dict[str, Any]) -> Tuple[str, str]:
        """
        根据任务上下文决定最优操作优先级（简化接口）

        Args:
            task_context: 任务上下文字典，包含任务描述和相关特征信息

        Returns:
            tuple[str, str]: (优先级值, 决策原因)
        """
        result = OperationPriorityController.decide_full(task_context)
        return result.priority.value, result.reason

    @staticmethod
    def decide_full(task_context: Dict[str, Any]) -> DecisionResult:
        """
        完整的决策方法，返回包含详细信息的 DecisionResult

        Args:
            task_context: 任务上下文字典

        Returns:
            DecisionResult: 包含优先级、原因、置信度等完整决策结果
        """
        features = TaskFeatureExtractor.extract(task_context)
        priority, reason, confidence, alternatives = (
            OperationPriorityController._run_decision_tree(features, task_context)
        )
        return DecisionResult(
            priority=priority,
            reason=reason,
            confidence=confidence,
            features=features,
            alternatives=alternatives,
        )

    @staticmethod
    def _run_decision_tree(
        features: TaskFeatures, context: Dict[str, Any]
    ) -> Tuple[OperationPriority, str, float, List[OperationPriority]]:
        """
        智能模式选择决策树

        决策规则（按优先级排序）：

        规则1: 需要领域专家 + 精确文件编辑 → MANUAL
        规则2: 单一文件精确编辑操作 → MANUAL
        规则3: 批量文件操作 + 有现成脚本 → SCRIPT
        规则4: 批量文件操作 + 无脚本但可编写 → SCRIPT
        规则5: 环境/依赖/构建相关操作 → COMMAND
        规则6: 默认 → MANUAL
        """
        ctx_desc = (context.get("description", "") or context.get("task", "") or "").lower()

        rule1 = OperationPriorityController._rule_expert_precise_edit(features, ctx_desc)
        if rule1:
            return rule1

        rule2 = OperationPriorityController._rule_single_file_edit(features)
        if rule2:
            return rule2

        rule3 = OperationPriorityController._rule_batch_with_script(features)
        if rule3:
            return rule3

        rule4 = OperationPriorityController._rule_batch_creatable_script(features, ctx_desc)
        if rule4:
            return rule4

        rule5 = OperationPriorityController._rule_environment_command(ctx_desc, context)
        if rule5:
            return rule5

        return (
            OperationPriority.MANUAL,
            "默认策略：使用手动操作模式确保精确控制",
            0.6,
            [OperationPriority.SCRIPT],
        )

    @staticmethod
    def _rule_expert_precise_edit(
        features: TaskFeatures, desc: str
    ) -> Optional[Tuple[OperationPriority, str, float, List[OperationPriority]]]:
        """规则1: 需要领域专家知识的精确编辑 → MANUAL"""
        if features.requires_domain_experts and features.involves_file_operations:
            if features.estimated_file_count <= 3:
                return (
                    OperationPriority.MANUAL,
                    "需要领域专家精确控制：任务涉及专业知识且文件数量少，"
                    "手动操作可保证代码质量和架构正确性",
                    0.95,
                    [OperationPriority.SCRIPT],
                )
        return None

    @staticmethod
    def _rule_single_file_edit(
        features: TaskFeatures,
    ) -> Optional[Tuple[OperationPriority, str, float, List[OperationPriority]]]:
        """规则2: 单一或少量文件的精确编辑 → MANUAL"""
        if features.involves_file_operations and features.estimated_file_count <= 2:
            edit_ops = {"edit", "write", "delete"}
            if set(features.operation_types) & edit_ops:
                return (
                    OperationPriority.MANUAL,
                    f"少量文件精确操作：涉及 {features.estimated_file_count} 个文件"
                    f"的 {', '.join(features.operation_types) or '通用'} 操作，"
                    "手动模式提供最佳粒度控制",
                    0.90,
                    [OperationPriority.SCRIPT],
                )
        return None

    @staticmethod
    def _rule_batch_with_script(
        features: TaskFeatures,
    ) -> Optional[Tuple[OperationPriority, str, float, List[OperationPriority]]]:
        """规则3: 批量操作且有现成脚本 → SCRIPT"""
        if features.is_batch_operation and features.has_existing_script:
            return (
                OperationPriority.SCRIPT,
                f"批量脚本执行：检测到 {features.estimated_file_count}+ 文件的批量操作需求，"
                "且存在可用脚本，脚本模式效率最高且可复用",
                0.92,
                [OperationPriority.MANUAL, OperationPriority.COMMAND],
            )
        return None

    @staticmethod
    def _rule_batch_creatable_script(
        features: TaskFeatures, desc: str,
    ) -> Optional[Tuple[OperationPriority, str, float, List[OperationPriority]]]:
        """规则4: 批量操作无脚本但可编写 → SCRIPT"""
        if features.is_batch_operation and not features.has_existing_script:
            if features.estimated_file_count >= 3:
                creatable_indicators = [
                    "统一", "规范", "格式化", "重构", "迁移", "转换",
                    "uniform", "standardize", "refactor", "migrate",
                ]
                is_creatable = any(ind in desc for ind in creatable_indicators)
                if is_creatable or features.estimated_file_count >= 5:
                    return (
                        OperationPriority.SCRIPT,
                        f"建议编写脚本：{features.estimated_file_count} 个文件的批量操作，"
                        "编写脚本可实现自动化并保证一致性",
                        0.82,
                        [OperationPriority.MANUAL, OperationPriority.COMMAND],
                    )
        return None

    @staticmethod
    def _rule_environment_command(
        desc: str, context: Dict[str, Any],
    ) -> Optional[Tuple[OperationPriority, str, float, List[OperationPriority]]]:
        """规则5: 环境/依赖/构建操作 → COMMAND"""
        command_indicators = [
            "安装", "install", "依赖", "dependency", "npm install", "pip install",
            "构建", "build", "编译", "compile", "运行", "run", "execute",
            "启动", "start", "停止", "stop", "服务", "server", "容器", "container",
            "docker", "环境变量", "env", "配置", "config", "打包", "package",
            "发布", "deploy", "测试运行", "test run", "lint", "类型检查",
        ]
        if any(ind in desc for ind in command_indicators):
            explicit_command = context.get("command") or context.get("shell_command")
            if explicit_command:
                return (
                    OperationPriority.COMMAND,
                    "明确的终端命令任务：用户指定了具体命令，使用命令模式执行",
                    0.95,
                    [OperationPriority.MANUAL],
                )
            return (
                OperationPriority.COMMAND,
                "基础设施操作：任务涉及环境配置、依赖管理或构建流程，"
                "适合通过终端命令完成",
                0.80,
                [OperationPriority.MANUAL, OperationPriority.SCRIPT],
            )
        return None

    @staticmethod
    def preflight_check(command: str) -> PreflightResult:
        """
        命令预演机制

        对即将执行的命令进行影响分析和风险评估，
        拦截已知的危险命令模式。

        Args:
            command: 待执行的命令字符串

        Returns:
            PreflightResult: 预演结果，包含安全性判断、风险等级和建议
        """
        command_stripped = command.strip()
        if not command_stripped:
            return PreflightResult(
                command=command,
                is_safe=False,
                risk_level=RiskLevel.HIGH,
                risk_reasons=["空命令"],
                blocked=True,
                block_reason="命令不能为空",
            )

        blocked_result = OperationPriorityController._check_dangerous_patterns(
            command_stripped
        )
        if blocked_result:
            return blocked_result

        risk_level, reasons = OperationPriorityController._assess_risk(command_stripped)
        impact = OperationPriorityController._analyze_impact(command_stripped)
        suggestions = OperationPriorityController._generate_suggestions(
            command_stripped, risk_level
        )

        is_safe = risk_level != RiskLevel.HIGH
        return PreflightResult(
            command=command,
            is_safe=is_safe,
            risk_level=risk_level,
            risk_reasons=reasons,
            impact_analysis=impact,
            suggestions=suggestions,
            blocked=risk_level == RiskLevel.HIGH,
            block_reason=reasons[0] if reasons and risk_level == RiskLevel.HIGH else "",
        )

    @staticmethod
    def _check_dangerous_patterns(command: str) -> Optional[PreflightResult]:
        """检查是否匹配已知危险命令模式"""
        cmd_normalized = " ".join(command.lower().split())
        for pattern, description in OperationPriorityController.DANGEROUS_COMMAND_PATTERNS:
            if pattern.search(cmd_normalized):
                logger.warning("Dangerous command blocked: %s - %s", command, description)
                return PreflightResult(
                    command=command,
                    is_safe=False,
                    risk_level=RiskLevel.HIGH,
                    risk_reasons=[f"匹配危险命令模式: {description}"],
                    blocked=True,
                    block_reason=f"命令已被安全策略拦截: {description}",
                    suggestions=[
                        "请确认此操作的必要性",
                        "考虑使用更安全的替代方案",
                        "如确需执行，请联系管理员进行审批",
                    ],
                )
        return None

    @staticmethod
    def _assess_risk(command: str) -> Tuple[RiskLevel, List[str]]:
        """评估命令的风险等级"""
        reasons = []
        risk_score = 0

        cmd_lower = command.lower()

        for keyword, desc in OperationPriorityController.DESTRUCTIVE_COMMAND_KEYWORDS:
            keyword_pattern = rf"\b{keyword}\b"
            if re.search(keyword_pattern, cmd_lower):
                risk_score += 3
                reasons.append(f"包含破坏性关键字 '{keyword}': {desc}")

        if re.search(r"-f\b|--force", cmd_lower):
            risk_score += 2
            reasons.append("使用了 --force/-f 强制标志")

        if re.search(r"-R\b|-r\b|--recursive", cmd_lower):
            risk_score += 1
            reasons.append("使用了递归操作标志")

        sudo_match = re.search(r"\bsudo\b", cmd_lower)
        if sudo_match:
            risk_score += 2
            reasons.append("需要提权(sudo)执行")

        pipe_match = re.search(r"\|", command)
        if pipe_match:
            risk_score += 1
            reasons.append("包含管道操作，可能产生组合效应")

        redirect_match = re.search(r">>|>", command)
        if redirect_match:
            risk_score += 1
            reasons.append("包含输出重定向，可能覆盖文件")

        glob_pattern = re.search(r"[\*?\[]", command)
        if glob_pattern:
            risk_score += 1
            reasons.append("包含通配符，影响范围可能超出预期")

        if not reasons:
            reasons.append("未检测到明显风险因素")
            return RiskLevel.LOW, reasons

        if risk_score >= 5:
            return RiskLevel.HIGH, reasons
        elif risk_score >= 3:
            return RiskLevel.MEDIUM, reasons
        return RiskLevel.LOW, reasons

    @staticmethod
    def _analyze_impact(command: str) -> Dict[str, Any]:
        """分析命令的影响范围"""
        impact = {
            "affected_scope": "unknown",
            "filesystem_operations": [],
            "network_operations": [],
            "process_operations": [],
            "estimated_reversibility": "unknown",
        }

        cmd_lower = command.lower()

        fs_ops = []
        if re.search(r"\b(mv|cp|rm|mkdir|touch|chmod|chown|ln)\b", cmd_lower):
            match = re.search(r"\b(mv|cp|rm|mkdir|touch|chmod|chown|ln)\b", cmd_lower)
            fs_ops.append(match.group(1))
        impact["filesystem_operations"] = fs_ops

        network_ops = []
        for net_cmd in ["curl", "wget", "ssh", "scp", "rsync", "ping", "telnet"]:
            if net_cmd in cmd_lower.split():
                network_ops.append(net_cmd)
        impact["network_operations"] = network_ops

        process_ops = []
        for proc_cmd in ["kill", "pkill", "systemctl", "service", "nohup", "screen", "tmux"]:
            if proc_cmd in cmd_lower.split():
                process_ops.append(proc_cmd)
        impact["process_operations"] = process_ops

        if fs_ops:
            destructive_fs = {"rm", "mv"}
            if set(fs_ops) & destructive_fs:
                impact["estimated_reversibility"] = "difficult"
            else:
                impact["estimated_reversibility"] = "easy"
        elif network_ops:
            impact["estimated_reversibility"] = "depends"
        elif process_ops:
            impact["estimated_reversibility"] = "depends"
        else:
            impact["estimated_reversibility"] = "safe"

        scope_parts = []
        if fs_ops:
            scope_parts.append("文件系统")
        if network_ops:
            scope_parts.append("网络")
        if process_ops:
            scope_parts.append("进程")
        impact["affected_scope"] = ", ".join(scope_parts) if scope_parts else "仅当前进程"

        return impact

    @staticmethod
    def _generate_suggestions(command: str, risk_level: RiskLevel) -> List[str]:
        """根据风险等级生成安全建议"""
        suggestions = []

        if risk_level == RiskLevel.LOW:
            suggestions.append("命令看起来是安全的，可以正常执行")
            suggestions.append("建议先在非关键环境中验证结果")
        elif risk_level == RiskLevel.MEDIUM:
            suggestions.append("命令存在中等风险，建议先进行干运行(dry-run)")
            suggestions.append("确认命令参数和目标路径的正确性")
            suggestions.append("考虑备份受影响的文件或数据")
            cmd_lower = command.lower()
            if "rm" in cmd_lower:
                suggestions.append("建议先用 ls 确认要删除的文件列表")
            if "--force" in cmd_lower or "-f " in command:
                suggestions.append("移除 --force/-f 参数以启用安全确认")
        else:
            suggestions.append("高风险命令！强烈建议不要直接执行")
            suggestions.append("寻找更安全的替代方案")
            suggestions.append("如果必须执行，请先进行完整备份")
            suggestions.append("建议在隔离环境中先行测试")

        cmd_lower = command.lower()
        if "sudo" in cmd_lower:
            suggestions.append("评估是否真的需要管理员权限")
        if "|" in command:
            suggestions.append("分步执行管道中的每个命令以便调试")

        return suggestions


__all__ = [
    "OperationPriority",
    "RiskLevel",
    "TaskFeatures",
    "PreflightResult",
    "DecisionResult",
    "TaskFeatureExtractor",
    "OperationPriorityController",
]
