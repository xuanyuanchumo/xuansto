#!/usr/bin/env python3
"""
四维度输出防线系统
协调四层防线调用，确保输出质量和安全性

功能：
- 第1层 PromptLayer（Prompt工程层）：意图识别、上下文注入、歧义消解、输入验证
- 第2层 CapabilityLayer（能力约束层）：技能匹配、知识库检查、工具验证、缺口识别
- 第3层 RuleValidationLayer（规则校验层）：编码规范、安全扫描、性能基准、合规审查
- 第4层 FallbackRecoveryLayer（兜底恢复层）：质量评分、自动回滚、降级策略、错误日志
"""

import re
import json
import logging
import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class IntentType(Enum):
    """意图类型枚举"""
    CODE_GENERATION = "code_generation"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    DEBUGGING = "debugging"
    UNKNOWN = "unknown"


class LayerStatus(Enum):
    """防线状态枚举"""
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    SKIPPED = "skipped"


class FallbackStrategy(Enum):
    """降级策略枚举"""
    SIMPLIFY_TASK = "simplify_task"
    REQUEST_HUMAN_HELP = "request_human_help"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    RETRY_WITH_CONTEXT = "retry_with_context"
    USE_CACHE_RESULT = "use_cache_result"


@dataclass
class LayerResult:
    """单层防线处理结果"""
    layer_name: str
    status: LayerStatus
    score: float
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass
class DefenseResult:
    """完整防线检查结果"""
    success: bool
    overall_score: float
    intent_type: IntentType
    layers: List[LayerResult] = field(default_factory=list)
    fallback_strategy: Optional[FallbackStrategy] = None
    final_output: Optional[Dict[str, Any]] = None
    error_log: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    total_duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['success'] = self.success
        result['intent_type'] = self.intent_type.value
        result['fallback_strategy'] = (
            self.fallback_strategy.value if self.fallback_strategy else None
        )
        result['layers'] = [layer.to_dict() for layer in self.layers]
        return result


@dataclass
class InputData:
    """输入数据结构"""
    raw_input: str
    context: Dict[str, Any] = field(default_factory=dict)
    project_info: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseDefenseLayer(ABC):
    """防线基类"""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self._start_time: Optional[float] = None

    def _start_timer(self) -> None:
        self._start_time = time.time()

    def _stop_timer(self) -> float:
        if self._start_time is None:
            return 0.0
        return (time.time() - self._start_time) * 1000

    @abstractmethod
    def process(self, input_data: InputData) -> LayerResult:
        pass

    def _create_result(
        self,
        status: LayerStatus,
        score: float,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> LayerResult:
        return LayerResult(
            layer_name=self.name,
            status=status,
            score=score,
            message=message,
            details=details or {},
            duration_ms=self._stop_timer()
        )


class PromptLayer(BaseDefenseLayer):
    """
    第1层：Prompt工程层
    负责意图识别与分类、上下文自动注入、歧义消解与确认、输入验证与标准化
    """

    INTENT_PATTERNS: Dict[IntentType, List[str]] = {
        IntentType.CODE_GENERATION: [
            r'创建|生成|新建|实现|开发|编写.*代码|函数|类|模块|接口|API',
            r'write|create|generate|implement|develop.*code|function|class|module'
        ],
        IntentType.REFACTORING: [
            r'重构|优化|改进|整理|简化.*代码|结构|逻辑',
            r'refactor|optimize|improve|simplify.*code|structure|logic'
        ],
        IntentType.DOCUMENTATION: [
            r'文档|注释|说明|README|API文档|使用说明',
            r'document|comment|docstring|README|documentation'
        ],
        IntentType.TESTING: [
            r'测试|单元测试|集成测试|测试用例|覆盖|pytest|unittest',
            r'test|testing|unit test|integration test|test case|coverage'
        ],
        IntentType.DEPLOYMENT: [
            r'部署|发布|上线|CI/CD|Docker|容器|发布流程',
            r'deploy|release|publish|CI/CD|Docker|container'
        ],
        IntentType.DEBUGGING: [
            r'调试|排查|修复|bug|错误|异常|问题定位',
            r'debug|troubleshoot|fix|bug|error|exception|issue'
        ]
    }

    AMBIGUITY_INDICATORS = [
        '可能', '也许', '大概', '或者', '还是', '是否',
        'maybe', 'perhaps', 'possibly', 'or', 'whether'
    ]

    REQUIRED_FIELDS = ['raw_input']

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("PromptLayer", config)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)

    def process(self, input_data: InputData) -> LayerResult:
        self._start_timer()
        try:
            validation_result = self._validate_input(input_data)
            if validation_result.status == LayerStatus.FAILED:
                return validation_result

            intent_result = self._identify_intent(input_data)
            context_result = self._inject_context(input_data, intent_result.details.get('intent'))
            ambiguity_result = self._resolve_ambiguity(input_data)

            combined_score = (
                validation_result.score * 0.25 +
                intent_result.score * 0.35 +
                context_result.score * 0.25 +
                ambiguity_result.score * 0.15
            )

            all_details = {
                **validation_result.details,
                **intent_result.details,
                **context_result.details,
                **ambiguity_result.details
            }

            overall_status = LayerStatus.PASSED if combined_score >= 0.7 else LayerStatus.WARNING

            return self._create_result(
                status=overall_status,
                score=combined_score,
                message=f"Prompt层处理完成，识别意图: {intent_result.details.get('intent', 'unknown')}",
                details=all_details
            )
        except Exception as e:
            logger.error(f"PromptLayer处理异常: {e}")
            return self._create_result(
                status=LayerStatus.FAILED,
                score=0.0,
                message=f"Prompt层处理失败: {str(e)}",
                details={'error': str(e)}
            )

    def _validate_input(self, input_data: InputData) -> LayerResult:
        """输入验证与标准化"""
        issues = []
        normalized_input = input_data.raw_input.strip()

        if not normalized_input:
            issues.append("输入内容为空")

        if len(normalized_input) < 3:
            issues.append(f"输入过短({len(normalized_input)}字符)，可能缺少必要信息")

        if len(normalized_input) > 10000:
            issues.append(f"输入过长({len(normalized_input)}字符)，建议分段处理")

        dangerous_patterns = [
            (r'rm\s+-rf', "检测到危险命令: rm -rf"),
            (r'DROP\s+TABLE', "检测到危险SQL操作: DROP TABLE"),
            (r'eval\(', "检测到潜在危险的eval调用"),
            (r'__import__', "检测到动态导入操作")
        ]

        for pattern, warning in dangerous_patterns:
            if re.search(pattern, normalized_input, re.IGNORECASE):
                issues.append(warning)

        score = max(0.0, 1.0 - len(issues) * 0.15)
        status = LayerStatus.FAILED if score < 0.4 else (LayerStatus.WARNING if score < 0.7 else LayerStatus.PASSED)

        return LayerResult(
            layer_name=f"{self.name}_validation",
            status=status,
            score=score,
            message="输入验证完成",
            details={
                'input_length': len(normalized_input),
                'issues': issues,
                'normalized_input': normalized_input[:500]
            }
        )

    def _identify_intent(self, input_data: InputData) -> LayerResult:
        """意图识别与分类"""
        text = input_data.raw_input.lower()
        intent_scores: Dict[IntentType, float] = {}

        for intent_type, patterns in self.INTENT_PATTERNS.items():
            max_score = 0.0
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score = min(1.0, matches * 0.3)
                max_score = max(max_score, score)
            intent_scores[intent_type] = max_score

        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        confidence = best_intent[1]

        if confidence < self.confidence_threshold:
            detected_intent = IntentType.UNKNOWN
            confidence = 0.3
        else:
            detected_intent = best_intent[0]

        all_intents = sorted(
            [(k.value, v) for k, v in intent_scores.items()],
            key=lambda x: x[1],
            reverse=True
        )

        return LayerResult(
            layer_name=f"{self.name}_intent",
            status=LayerStatus.PASSED if confidence >= self.confidence_threshold else LayerStatus.WARNING,
            score=confidence,
            message=f"识别意图: {detected_intent.value}, 置信度: {confidence:.2f}",
            details={
                'intent': detected_intent.value,
                'confidence': confidence,
                'all_intents': all_intents[:3]
            }
        )

    def _inject_context(self, input_data: InputData, intent: Optional[str]) -> LayerResult:
        """上下文自动注入"""
        context = {}

        if input_data.project_info:
            context['project'] = {
                'name': input_data.project_info.get('name', 'unknown'),
                'type': input_data.project_info.get('type', 'general'),
                'tech_stack': input_data.project_info.get('tech_stack', []),
                'coding_standards': input_data.project_info.get('coding_standards', {})
            }

        context['session'] = {
            'user_id': input_data.user_id,
            'session_id': input_data.session_id,
            'timestamp': datetime.now().isoformat()
        }

        context['intent_context'] = self._get_intent_specific_context(intent)

        existing_context = input_data.context or {}
        merged_context = {**existing_context, **context}

        completeness = self._calculate_context_completeness(merged_context)

        return LayerResult(
            layer_name=f"{self.name}_context",
            status=LayerStatus.PASSED if completeness >= 0.6 else LayerStatus.WARNING,
            score=completeness,
            message=f"上下文注入完成，完整度: {completeness:.2f}",
            details={
                'injected_context': context,
                'merged_context_keys': list(merged_context.keys()),
                'completeness': completeness
            }
        )

    def _get_intent_specific_context(self, intent: Optional[str]) -> Dict[str, Any]:
        """获取特定意图的上下文模板"""
        templates = {
            'code_generation': {
                'requirements': 'focus_on_correctness_and_readability',
                'output_format': 'structured_code_with_explanation'
            },
            'refactoring': {
                'requirements': 'maintain_behavior_improve_structure',
                'output_format': 'diff_or_full_file_with_changes'
            },
            'documentation': {
                'requirements': 'clear_comprehensive_accurate',
                'output_format': 'markdown_documentation'
            },
            'testing': {
                'requirements': 'coverage_edge_cases_error_handling',
                'output_format': 'test_suite_with_assertions'
            },
            'deployment': {
                'requirements': 'safe_rollback_automation',
                'output_format': 'deployment_manifest_instructions'
            },
            'debugging': {
                'requirements': 'root_cause_reproduction_steps',
                'output_format': 'diagnosis_fix_verification'
            }
        }
        return templates.get(intent or '', {})

    def _calculate_context_completeness(self, context: Dict[str, Any]) -> float:
        required_keys = ['session']
        optional_keys = ['project', 'intent_context', 'history', 'preferences']

        present_required = sum(1 for k in required_keys if k in context)
        present_optional = sum(1 for k in optional_keys if k in context)

        required_score = present_required / len(required_keys) if required_keys else 1.0
        optional_score = present_optional / len(optional_keys) if optional_keys else 0.0

        return required_score * 0.7 + optional_score * 0.3

    def _resolve_ambiguity(self, input_data: InputData) -> LayerResult:
        """歧义消解与确认"""
        text = input_data.raw_input.lower()
        ambiguities = []
        clarifications_needed = []

        for indicator in self.AMBIGUITY_INDICATORS:
            if indicator in text:
                ambiguities.append(indicator)

        vague_terms = {
            '这个东西': '请明确具体的对象或组件名称',
            '那个功能': '请指定具体的功能名称和位置',
            '一些问题': '请列出具体的问题描述',
            '改一下': '请说明需要修改的具体内容和期望结果',
            '优化它': '请明确优化的目标（性能/可读性/可维护性）'
        }

        for term, suggestion in vague_terms.items():
            if term in text:
                ambiguities.append(term)
                clarifications_needed.append({'term': term, 'suggestion': suggestion})

        questions_count = text.count('?') + text.count('？')
        if questions_count > 3:
            ambiguities.append('multiple_questions')
            clarifications_needed.append({
                'term': 'multiple_questions',
                'suggestion': '检测到多个问题，建议分批提问以获得更精确的回答'
            })

        ambiguity_score = max(0.0, 1.0 - len(ambiguities) * 0.15)
        status = LayerStatus.PASSED if ambiguity_score >= 0.7 else LayerStatus.WARNING

        return LayerResult(
            layer_name=f"{self.name}_ambiguity",
            status=status,
            score=ambiguity_score,
            message=f"歧义检测完成，发现{len(ambiguities)}个潜在歧义点",
            details={
                'ambiguity_count': len(ambiguities),
                'ambiguities': ambiguities,
                'clarifications_needed': clarifications_needed,
                'requires_confirmation': len(clarifications_needed) > 0
            }
        )


class CapabilityLayer(BaseDefenseLayer):
    """
    第2层：能力约束层
    负责技能匹配度评估、知识库覆盖检查、工具链可用性验证、能力缺口识别
    """

    SKILL_MATCH_THRESHOLD = 0.7

    KNOWLEDGE_BASE: Dict[str, List[str]] = {
        'languages': [
            'python', 'javascript', 'typescript', 'java', 'go', 'rust',
            'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin'
        ],
        'frameworks': [
            'react', 'vue', 'angular', 'django', 'flask', 'fastapi',
            'spring', 'express', 'next.js', 'nuxt', 'rails'
        ],
        'tools': [
            'git', 'docker', 'kubernetes', 'redis', 'postgresql', 'mongodb',
            'webpack', 'vite', 'pytest', 'jest', 'ci/cd', 'terraform'
        ],
        'concepts': [
            'oop', 'functional_programming', 'design_patterns', 'microservices',
            'rest_api', 'graphql', 'async_programming', 'testing', 'devops'
        ]
    }

    TOOL_AVAILABILITY: Dict[str, bool] = {}

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("CapabilityLayer", config)
        self.skill_match_threshold = self.config.get(
            'skill_match_threshold', self.SKILL_MATCH_THRESHOLD
        )
        self._initialize_tool_status()

    def _initialize_tool_status(self) -> None:
        import shutil
        tools_to_check = ['git', 'docker', 'python', 'node', 'npm', 'pip']
        for tool in tools_to_check:
            self.TOOL_AVAILABILITY[tool] = shutil.which(tool) is not None

    def process(self, input_data: InputData) -> LayerResult:
        self._start_timer()
        try:
            skill_match_result = self._evaluate_skill_match(input_data)
            knowledge_result = self._check_knowledge_coverage(input_data)
            tool_result = self._verify_toolchain(input_data)
            gap_result = self._identify_capability_gaps(
                skill_match_result.details,
                knowledge_result.details,
                tool_result.details
            )

            combined_score = (
                skill_match_result.score * 0.35 +
                knowledge_result.score * 0.30 +
                tool_result.score * 0.20 +
                gap_result.score * 0.15
            )

            all_details = {
                'skill_match': skill_match_result.details,
                'knowledge_coverage': knowledge_result.details,
                'toolchain_status': tool_result.details,
                'capability_gaps': gap_result.details
            }

            overall_status = LayerStatus.PASSED if combined_score >= self.skill_match_threshold else LayerStatus.WARNING

            if gap_result.details.get('critical_gaps', 0) > 0:
                overall_status = LayerStatus.FAILED

            return self._create_result(
                status=overall_status,
                score=combined_score,
                message=f"能力约束检查完成，匹配度: {combined_score:.2f}",
                details=all_details
            )
        except Exception as e:
            logger.error(f"CapabilityLayer处理异常: {e}")
            return self._create_result(
                status=LayerStatus.FAILED,
                score=0.0,
                message=f"能力约束层处理失败: {str(e)}",
                details={'error': str(e)}
            )

    def _evaluate_skill_match(self, input_data: InputData) -> LayerResult:
        """技能匹配度评估（语义相似度）"""
        text = input_data.raw_input.lower()

        tech_keywords = set()
        for category, items in self.KNOWLEDGE_BASE.items():
            for item in items:
                if item.lower() in text:
                    tech_keywords.add(item.lower())

        context_tech = set()
        if input_data.project_info and input_data.project_info.get('tech_stack'):
            for tech in input_data.project_info['tech_stack']:
                context_tech.add(tech.lower())

        matched_skills = tech_keywords & context_tech
        total_relevant = tech_keywords | context_tech

        if total_relevant:
            similarity = len(matched_skills) / len(total_relevant)
        elif tech_keywords:
            similarity = 0.5
        else:
            similarity = 0.8

        semantic_features = self._extract_semantic_features(text)
        feature_score = self._calculate_semantic_similarity(semantic_features)

        final_score = (similarity * 0.6 + feature_score * 0.4)

        status = (
            LayerStatus.PASSED if final_score >= self.skill_match_threshold
            else LayerStatus.WARNING
        )

        return LayerResult(
            layer_name=f"{self.name}_skill_match",
            status=status,
            score=final_score,
            message=f"技能匹配度: {final_score:.2f} (阈值: {self.skill_match_threshold})",
            details={
                'similarity_score': similarity,
                'semantic_score': feature_score,
                'matched_skills': list(matched_skills),
                'detected_keywords': list(tech_keywords),
                'context_technologies': list(context_tech),
                'above_threshold': final_score >= self.skill_match_threshold
            }
        )

    def _extract_semantic_features(self, text: str) -> Dict[str, Any]:
        """提取语义特征"""
        features = {
            'code_indicators': len(re.findall(r'\b(def|class|function|import|const|let|var)\b', text)),
            'technical_terms': len(re.findall(
                r'\b(api|database|server|client|frontend|backend|algorithm|structure)\b',
                text
            )),
            'action_verbs': len(re.findall(
                r'\b(create|update|delete|get|set|build|deploy|test|debug|refactor)\b',
                text
            )),
            'has_code_block': bool(re.search(r'```[\s\S]*?```', text)),
            'has_file_path': bool(re.search(r'\.[a-z]{2,4}\b', text)),
            'complexity_markers': len(re.findall(r'\b(and|or|if|then|else|while|for)\b', text))
        }
        return features

    def _calculate_semantic_similarity(self, features: Dict[str, Any]) -> float:
        """计算语义相似度得分"""
        weights = {
            'code_indicators': 0.2,
            'technical_terms': 0.25,
            'action_verbs': 0.25,
            'has_code_block': 0.15,
            'has_file_path': 0.1,
            'complexity_markers': 0.05
        }

        normalized = {}
        for key, value in features.items():
            if isinstance(value, bool):
                normalized[key] = 1.0 if value else 0.0
            elif isinstance(value, int):
                normalized[key] = min(1.0, value / 5.0)
            else:
                normalized[key] = 0.0

        score = sum(normalized.get(k, 0) * w for k, w in weights.items())
        return min(1.0, score)

    def _check_knowledge_coverage(self, input_data: InputData) -> LayerResult:
        """知识库覆盖检查"""
        text = input_data.raw_input.lower()
        coverage_results = {}

        for category, items in self.KNOWLEDGE_BASE.items():
            found = [item for item in items if item.lower() in text]
            coverage_results[category] = {
                'total': len(items),
                'found': found,
                'coverage_ratio': len(found) / len(items) if items else 0.0
            }

        total_items = sum(len(items) for items in self.KNOWLEDGE_BASE.values())
        total_found = sum(len(r['found']) for r in coverage_results.values())
        overall_coverage = total_found / total_items if total_items > 0 else 1.0

        uncovered_categories = [
            cat for cat, result in coverage_results.items()
            if result['coverage_ratio'] == 0 and cat != 'concepts'
        ]

        status = (
            LayerStatus.PASSED if overall_coverage >= 0.3
            else (LayerStatus.WARNING if overall_coverage >= 0.1 else LayerStatus.FAILED)
        )

        return LayerResult(
            layer_name=f"{self.name}_knowledge",
            status=status,
            score=overall_coverage,
            message=f"知识库覆盖度: {overall_coverage:.2%}",
            details={
                'coverage_by_category': coverage_results,
                'overall_coverage': overall_coverage,
                'uncovered_categories': uncovered_categories,
                'total_technologies_mentioned': total_found
            }
        )

    def _verify_toolchain(self, input_data: InputData) -> LayerResult:
        """工具链可用性验证"""
        text = input_data.raw_input.lower()

        required_tools = []
        tool_mapping = {
            'git': ['git', 'commit', 'push', 'pull', 'branch', 'merge'],
            'docker': ['docker', 'container', 'image', 'compose'],
            'python': ['python', '.py', 'pip', 'pytest'],
            'node': ['node', 'npm', 'javascript', 'package.json'],
            'database': ['sql', 'database', 'mysql', 'postgresql', 'mongodb']
        }

        for tool, indicators in tool_mapping.items():
            if any(indicator in text for indicator in indicators):
                required_tools.append(tool)

        tool_status = {}
        available_count = 0
        for tool in required_tools:
            is_available = self.TOOL_AVAILABILITY.get(tool, True)
            tool_status[tool] = is_available
            if is_available:
                available_count += 1

        availability_rate = available_count / len(required_tools) if required_tools else 1.0
        missing_tools = [t for t, available in tool_status.items() if not available]

        status = (
            LayerStatus.PASSED if availability_rate >= 0.9
            else (LayerStatus.WARNING if availability_rate >= 0.7 else LayerStatus.FAILED)
        )

        return LayerResult(
            layer_name=f"{self.name}_tools",
            status=status,
            score=availability_rate,
            message=f"工具链可用性: {availability_rate:.0%} ({available_count}/{len(required_tools)})",
            details={
                'required_tools': required_tools,
                'tool_status': tool_status,
                'availability_rate': availability_rate,
                'missing_tools': missing_tools,
                'all_tools_available': len(missing_tools) == 0
            }
        )

    def _identify_capability_gaps(
        self,
        skill_details: Dict[str, Any],
        knowledge_details: Dict[str, Any],
        tool_details: Dict[str, Any]
    ) -> LayerResult:
        """能力缺口识别与补全建议"""
        gaps = []
        suggestions = []
        critical_gaps = 0

        if not skill_details.get('above_threshold', True):
            gaps.append({
                'type': 'skill_mismatch',
                'severity': 'high',
                'description': '技能匹配度低于阈值',
                'suggestion': '建议细化任务描述或分解为更小的子任务'
            })
            critical_gaps += 1
            suggestions.append('将复杂任务拆分为多个简单步骤')

        uncovered = knowledge_details.get('uncovered_categories', [])
        if uncovered:
            gaps.append({
                'type': 'knowledge_gap',
                'severity': 'medium',
                'description': f'知识库未覆盖类别: {uncovered}',
                'suggestion': '可能需要额外提供相关技术文档或示例代码'
            })
            suggestions.append(f'补充{"、".join(uncovered)}相关的上下文信息')

        missing_tools = tool_details.get('missing_tools', [])
        if missing_tools:
            gaps.append({
                'type': 'tool_unavailable',
                'severity': 'high' if 'git' in missing_tools else 'medium',
                'description': f'必需工具不可用: {missing_tools}',
                'suggestion': f'请安装缺失的工具: {" ".join(missing_tools)}'
            })
            if 'git' in missing_tools:
                critical_gaps += 1
            suggestions.append(f'安装并配置工具: {", ".join(missing_tools)}')

        gap_score = max(0.0, 1.0 - len(gaps) * 0.2 - critical_gaps * 0.3)
        status = (
            LayerStatus.PASSED if critical_gaps == 0 and len(gaps) <= 1
            else (LayerStatus.WARNING if critical_gaps == 0 else LayerStatus.FAILED)
        )

        return LayerResult(
            layer_name=f"{self.name}_gaps",
            status=status,
            score=gap_score,
            message=f"发现{len(gaps)}个能力缺口（{critical_gaps}个严重）",
            details={
                'gaps': gaps,
                'suggestions': suggestions,
                'gap_count': len(gaps),
                'critical_gaps': critical_gaps,
                'needs_completion_suggestions': len(suggestions) > 0
            }
        )


class RuleValidationLayer(BaseDefenseLayer):
    """
    第3层：规则校验层
    负责编码规范检查、安全扫描、性能基准对比、合规性审查
    """

    SECURITY_PATTERNS: List[Tuple[str, str, str]] = [
        (r'password\s*=\s*["\'][^"\']+["\']', 'hardcoded_password', 'HIGH'),
        (r'api_key\s*=\s*["\'][^"\']+["\']', 'hardcoded_api_key', 'HIGH'),
        (r'secret\s*=\s*["\'][^"\']+["\']', 'hardcoded_secret', 'HIGH'),
        (r'token\s*=\s*["\'][^"\']+["\']', 'hardcoded_token', 'MEDIUM'),
        (r'eval\(\s*[^)]+\)', 'dangerous_eval', 'HIGH'),
        (r'exec\(\s*[^)]+\)', 'dangerous_exec', 'HIGH'),
        (r'subprocess\.call\(.*shell\s*=\s*True', 'shell_injection', 'HIGH'),
        (r'os\.system\(', 'os_system_call', 'MEDIUM'),
        (r'pickle\.loads?\(', 'unsafe_deserialization', 'HIGH'),
        (r'yaml\.load\((?!.*Loader)', 'yaml_unsafe_load', 'MEDIUM')
    ]

    CODE_STYLE_RULES: Dict[str, Dict[str, Any]] = {
        'line_length': {'max': 120, 'weight': 0.15},
        'naming_convention': {'patterns': [r'^[a-z_][a-z0-9_]*$'], 'weight': 0.20},
        'indentation': {'consistent': True, 'weight': 0.15},
        'docstring_coverage': {'min_ratio': 0.5, 'weight': 0.25},
        'complexity': {'max_cyclomatic': 10, 'weight': 0.25}
    }

    PERFORMANCE_THRESHOLDS: Dict[str, Any] = {
        'max_function_length': 100,
        'max_nesting_depth': 5,
        'max_parameters': 7,
        'warn_loop_iterations': 1000,
        'critical_loop_iterations': 10000
    }

    COMPLIANCE_RULES: List[Dict[str, Any]] = [
        {'name': 'no_hardcoded_urls', 'pattern': r'https?://[^\s"\'`]+', 'severity': 'medium'},
        {'name': 'no_debug_statements', 'pattern': r'\bprint\(|console\.log\(', 'severity': 'low'},
        {'name': 'encoding_declaration', 'pattern': r'#\s*-\*-\s*coding\s*:', 'severity': 'info'}
    ]

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("RuleValidationLayer", config)
        self.security_enabled = self.config.get('security_enabled', True)
        self.style_check_enabled = self.config.get('style_check_enabled', True)
        self.performance_check_enabled = self.config.get('performance_check_enabled', True)
        self.compliance_check_enabled = self.config.get('compliance_check_enabled', True)

    def process(self, input_data: InputData) -> LayerResult:
        self._start_timer()
        try:
            results = {}

            if self.security_enabled:
                results['security'] = self._security_scan(input_data).details
            if self.style_check_enabled:
                results['style'] = self._check_coding_standards(input_data).details
            if self.performance_check_enabled:
                results['performance'] = self._performance_benchmark(input_data).details
            if self.compliance_check_enabled:
                results['compliance'] = self._compliance_review(input_data).details

            security_score = results.get('security', {}).get('score', 1.0)
            style_score = results.get('style', {}).get('score', 1.0)
            performance_score = results.get('performance', {}).get('score', 1.0)
            compliance_score = results.get('compliance', {}).get('score', 1.0)

            combined_score = (
                security_score * 0.35 +
                style_score * 0.25 +
                performance_score * 0.20 +
                compliance_score * 0.20
            )

            critical_issues = (
                results.get('security', {}).get('critical_count', 0) +
                results.get('performance', {}).get('critical_count', 0)
            )

            overall_status = (
                LayerStatus.FAILED if critical_issues > 0
                else (LayerStatus.WARNING if combined_score < 0.7 else LayerStatus.PASSED)
            )

            return self._create_result(
                status=overall_status,
                score=combined_score,
                message=f"规则校验完成，综合评分: {combined_score:.2f}，严重问题: {critical_issues}",
                details=results
            )
        except Exception as e:
            logger.error(f"RuleValidationLayer处理异常: {e}")
            return self._create_result(
                status=LayerStatus.FAILED,
                score=0.0,
                message=f"规则校验层处理失败: {str(e)}",
                details={'error': str(e)}
            )

    def _security_scan(self, input_data: InputData) -> LayerResult:
        """安全扫描接口（集成硬编码检测）"""
        findings = []
        critical_count = 0
        high_count = 0
        medium_count = 0
        low_count = 0

        text = input_data.raw_input

        for pattern, issue_type, severity in self.SECURITY_PATTERNS:
            matches = re.finditer(pattern, text)
            for match in matches:
                line_num = text[:match.start()].count('\n') + 1
                finding = {
                    'type': issue_type,
                    'severity': severity,
                    'line': line_num,
                    'content': match.group()[:100],
                    'recommendation': self._get_security_recommendation(issue_type)
                }
                findings.append(finding)

                if severity == 'HIGH':
                    critical_count += 1
                elif severity == 'MEDIUM':
                    medium_count += 1
                else:
                    low_count += 1

        high_count = critical_count

        total_findings = len(findings)
        if total_findings > 0:
            score = max(0.0, 1.0 - (critical_count * 0.3 + high_count * 0.2 + medium_count * 0.1 + low_count * 0.05))
        else:
            score = 1.0

        status = (
            LayerStatus.FAILED if critical_count > 0
            else (LayerStatus.WARNING if total_findings > 3 else LayerStatus.PASSED)
        )

        return LayerResult(
            layer_name=f"{self.name}_security",
            status=status,
            score=score,
            message=f"安全扫描发现{total_findings}个问题（{critical_count}严重）",
            details={
                'findings': findings,
                'critical_count': critical_count,
                'high_count': high_count,
                'medium_count': medium_count,
                'low_count': low_count,
                'total_findings': total_findings,
                'score': score
            }
        )

    def _get_security_recommendation(self, issue_type: str) -> str:
        recommendations = {
            'hardcoded_password': '使用环境变量或密钥管理服务存储敏感信息',
            'hardcoded_api_key': '使用环境变量或密钥管理服务存储API密钥',
            'hardcoded_secret': '使用安全的秘密管理方案',
            'hardcoded_token': '使用OAuth或JWT等标准认证机制',
            'dangerous_eval': '避免使用eval()，考虑使用ast.literal_eval()或更安全的替代方案',
            'dangerous_exec': '避免使用exec()，重构代码以避免动态执行',
            'shell_injection': '避免shell=True，使用列表形式传递参数',
            'os_system_call': '使用subprocess模块替代os.system()',
            'unsafe_deserialization': '使用安全的数据格式如JSON替代pickle',
            'yaml_unsafe_load': '指定安全的Loader，如yaml.safe_load()'
        }
        return recommendations.get(issue_type, '请审查此安全问题并采取适当的缓解措施')

    def _check_coding_standards(self, input_data: InputData) -> LayerResult:
        """编码规范自动检查接口"""
        text = input_data.raw_input
        violations = []

        lines = text.split('\n')
        rule_results = {}

        for idx, line in enumerate(lines, 1):
            stripped = line.rstrip()

            if self.CODE_STYLE_RULES.get('line_length'):
                max_len = self.CODE_STYLE_RULES['line_length']['max']
                if len(stripped) > max_len:
                    violations.append({
                        'rule': 'line_length',
                        'line': idx,
                        'message': f'行长度超限 ({len(stripped)}/{max_len})'
                    })

        code_blocks = re.findall(r'```[\w]*\n([\s\S]*?)```', text)
        if code_blocks:
            functions_found = 0
            documented_functions = 0
            for block in code_blocks:
                func_matches = re.findall(r'(?:def|function)\s+(\w+)', block)
                functions_found += len(func_matches)
                doc_matches = re.findall(r'""".*?"""', block, re.DOTALL)
                doc_matches += re.findall(r"'''.*?'''", block, re.DOTALL)
                documented_functions += len(doc_matches)

            if functions_found > 0:
                doc_ratio = documented_functions / functions_found
                rule_results['docstring_coverage'] = {
                    'ratio': doc_ratio,
                    'meets_standard': doc_ratio >= self.CODE_STYLE_RULES['docstring_coverage']['min_ratio']
                }
            else:
                rule_results['docstring_coverage'] = {'ratio': 1.0, 'meets_standard': True}

        violation_scores = []
        for rule_name, rule_config in self.CODE_STYLE_RULES.items():
            if rule_name in rule_results:
                result = rule_results[rule_name]
                if isinstance(result, dict) and 'meets_standard' in result:
                    score = 1.0 if result['meets_standard'] else 0.5
                else:
                    score = 1.0
            else:
                score = 1.0
            weight = rule_config.get('weight', 0.2)
            violation_scores.append(score * weight)

        if violation_scores:
            style_score = sum(violation_scores)
        else:
            style_score = 1.0

        status = (
            LayerStatus.WARNING if style_score < 0.8 else LayerStatus.PASSED
        )

        return LayerResult(
            layer_name=f"{self.name}_style",
            status=status,
            score=style_score,
            message=f"编码规范检查完成，发现{len(violations)}个违规项",
            details={
                'violations': violations[:20],
                'violation_count': len(violations),
                'rule_results': rule_results,
                'score': style_score
            }
        )

    def _performance_benchmark(self, input_data: InputData) -> LayerResult:
        """性能基准对比"""
        text = input_data.raw_input
        issues = []
        critical_count = 0

        code_blocks = re.findall(r'```[\w]*\n([\s\S]*?)```', text)

        for block in code_blocks:
            lines = block.split('\n')
            for line_idx, line in enumerate(lines, 1):
                stripped = line.strip()
                indent = len(line) - len(line.lstrip())

                if indent > self.PERFORMANCE_THRESHOLDS['max_nesting_depth'] * 4:
                    issues.append({
                        'type': 'deep_nesting',
                        'line': line_idx,
                        'message': f'嵌套深度过大 ({indent // 4}级)',
                        'severity': 'warning'
                    })

                func_match = re.match(r'(?:def|function)\s+\w+\(([^)]*)\)', stripped)
                if func_match:
                    params = func_match.group(1)
                    param_count = len([p for p in params.split(',') if p.strip()])
                    if param_count > self.PERFORMANCE_THRESHOLDS['max_parameters']:
                        issues.append({
                            'type': 'too_many_parameters',
                            'line': line_idx,
                            'message': f'参数过多 ({param_count}/{self.PERFORMANCE_THRESHOLDS["max_parameters"]})',
                            'severity': 'warning'
                        })

            if len(lines) > self.PERFORMANCE_THRESHOLDS['max_function_length']:
                issues.append({
                    'type': 'long_function',
                    'message': f'函数过长 ({len(lines)}行)',
                    'severity': 'warning'
                })

        loop_pattern = r'(?:for|while)\s*\([^)]*\)\s*\{?'
        loops = re.findall(loop_pattern, text)
        if len(loops) > 10:
            issues.append({
                'type': 'many_loops',
                'message': f'循环数量过多 ({len(loops)}个)',
                'severity': 'info'
            })

        critical_count = sum(1 for i in issues if i.get('severity') == 'critical')
        performance_score = max(0.0, 1.0 - len(issues) * 0.05 - critical_count * 0.2)

        status = (
            LayerStatus.FAILED if critical_count > 0
            else (LayerStatus.WARNING if len(issues) > 5 else LayerStatus.PASSED)
        )

        return LayerResult(
            layer_name=f"{self.name}_performance",
            status=status,
            score=performance_score,
            message=f"性能检查完成，发现{len(issues)}个问题（{critical_count}严重）",
            details={
                'issues': issues,
                'issue_count': len(issues),
                'critical_count': critical_count,
                'loop_count': len(loops),
                'score': performance_score
            }
        )

    def _compliance_review(self, input_data: InputData) -> LayerResult:
        """合规性审查"""
        text = input_data.raw_input
        violations = []

        for rule in self.COMPLIANCE_RULES:
            matches = re.finditer(rule['pattern'], text)
            for match in matches:
                line_num = text[:match.start()].count('\n') + 1
                violations.append({
                    'rule': rule['name'],
                    'severity': rule['severity'],
                    'line': line_num,
                    'content': match.group()[:80]
                })

        has_encoding = bool(re.search(r'#\s*-\*-\s*coding\s*:', text))
        compliance_score = max(0.0, 1.0 - len(violations) * 0.1)

        if not has_encoding and len(text) > 50:
            compliance_score *= 0.95

        status = (
            LayerStatus.WARNING if compliance_score < 0.9 else LayerStatus.PASSED
        )

        return LayerResult(
            layer_name=f"{self.name}_compliance",
            status=status,
            score=compliance_score,
            message=f"合规性审查完成，发现{len(violations)}个违规项",
            details={
                'violations': violations,
                'violation_count': len(violations),
                'has_encoding_declaration': has_encoding,
                'score': compliance_score
            }
        )


class FallbackRecoveryLayer(BaseDefenseLayer):
    """
    第4层：兜底恢复层
    负责输出质量评分、自动回滚、降级策略、错误日志记录与根因分析
    """

    QUALITY_THRESHOLD = 3.5
    MAX_SCORE = 5.0

    ROLLBACK_STATES: List[Dict[str, Any]] = []

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("FallbackRecoveryLayer", config)
        self.quality_threshold = self.config.get('quality_threshold', self.QUALITY_THRESHOLD)
        self.max_score = self.config.get('max_score', self.MAX_SCORE)
        self._stable_state: Optional[Dict[str, Any]] = None

    def process(self, input_data: InputData) -> LayerResult:
        self._start_timer()
        try:
            quality_result = self._assess_output_quality(input_data)
            rollback_info = self._prepare_rollback_state(input_data)
            strategy = self._determine_fallback_strategy(quality_result)
            log_entry = self._record_error_log(input_data, quality_result, strategy)

            final_score = quality_result.score
            final_status = quality_result.status

            if final_score < self.quality_threshold and strategy:
                final_status = LayerStatus.WARNING

            return self._create_result(
                status=final_status,
                score=final_score,
                message=f"兜底恢复层处理完成，质量评分: {final_score:.1f}/{self.max_score}",
                details={
                    'quality_assessment': quality_result.details,
                    'rollback_state': rollback_info,
                    'fallback_strategy': strategy.value if strategy else None,
                    'error_log': log_entry,
                    'meets_threshold': final_score >= self.quality_threshold
                }
            )
        except Exception as e:
            logger.error(f"FallbackRecoveryLayer处理异常: {e}")
            return self._create_result(
                status=LayerStatus.FAILED,
                score=0.0,
                message=f"兜底恢复层处理失败: {str(e)}",
                details={'error': str(e)}
            )

    def _assess_output_quality(self, input_data: InputData) -> LayerResult:
        """输出质量评分（5分制）"""
        text = input_data.raw_input
        scores = {}

        scores['completeness'] = self._score_completeness(text)
        scores['accuracy'] = self._score_accuracy(text, input_data.context)
        scores['clarity'] = self._score_clarity(text)
        scores['actionability'] = self._score_actionability(text)
        scores['safety'] = self._score_safety(text)

        weights = {
            'completeness': 0.25,
            'accuracy': 0.25,
            'clarity': 0.20,
            'actionability': 0.15,
            'safety': 0.15
        }

        weighted_score = sum(scores[k] * weights.get(k, 0.2) for k in scores)
        final_score = min(self.max_score, weighted_score)

        status = (
            LayerStatus.PASSED if final_score >= self.quality_threshold
            else (LayerStatus.WARNING if final_score >= 2.5 else LayerStatus.FAILED)
        )

        return LayerResult(
            layer_name=f"{self.name}_quality",
            status=status,
            score=final_score,
            message=f"质量评分: {final_score:.1f}/{self.max_score} (阈值: {self.quality_threshold})",
            details={
                'dimension_scores': scores,
                'weighted_score': weighted_score,
                'final_score': final_score,
                'threshold': self.quality_threshold,
                'passes': final_score >= self.quality_threshold
            }
        )

    def _score_completeness(self, text: str) -> float:
        """完整性评分"""
        score = self.max_score

        if len(text) < 20:
            score -= 2.0
        elif len(text) < 50:
            score -= 1.0

        has_code_example = bool(re.search(r'```[\s\S]*?```', text))
        has_explanation = len(re.findall(r'[。！？.]', text)) >= 3
        has_structure = bool(re.search(r'(?:^|\n)\s*(?:#{1,3}|\d+[.)])', text))

        if not has_code_example and not has_explanation:
            score -= 1.5
        if not has_structure and len(text) > 200:
            score -= 0.5

        return max(0.0, min(self.max_score, score))

    def _score_accuracy(self, text: str, context: Optional[Dict[str, Any]]) -> float:
        """准确性评分"""
        score = self.max_score

        contradictory_patterns = [
            (r'但是.*但是', 'repeated_contrast'),
            (r'虽然.*虽然', 'repeated_concession')
        ]

        for pattern, issue_type in contradictory_patterns:
            if re.search(pattern, text):
                score -= 0.5

        uncertain_phrases = len(re.findall(
            r'(?:可能|也许|大概|应该|或许|probably|maybe|perhaps)',
            text
        ))
        if uncertain_phrases > 3:
            score -= min(1.0, uncertain_phrases * 0.2)

        technical_consistency = self._check_technical_consistency(text)
        score *= technical_consistency

        return max(0.0, min(self.max_score, score))

    def _check_technical_consistency(self, text: str) -> float:
        """检查技术术语一致性"""
        terms_found = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
        unique_terms = set(terms_found)

        if len(terms_found) > 0:
            consistency_ratio = len(unique_terms) / len(terms_found)
            return max(0.5, consistency_ratio)
        return 1.0

    def _score_clarity(self, text: str) -> float:
        """清晰度评分"""
        score = self.max_score

        avg_sentence_length = self._calculate_avg_sentence_length(text)
        if avg_sentence_length > 100:
            score -= 1.0
        elif avg_sentence_length > 50:
            score -= 0.5

        complex_words = len(re.findall(r'\b\w{15,}\b', text))
        if complex_words > 5:
            score -= min(0.5, complex_words * 0.05)

        has_formatting = bool(re.search(r'[`*_#]', text))
        if not has_formatting and len(text) > 100:
            score -= 0.5

        return max(0.0, min(self.max_score, score))

    def _calculate_avg_sentence_length(self, text: str) -> float:
        sentences = re.split(r'[。！？.!?\n]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences:
            return sum(len(s) for s in sentences) / len(sentences)
        return 0.0

    def _score_actionability(self, text: str) -> float:
        """可操作性评分"""
        score = self.max_score

        action_verbs = len(re.findall(
            r'\b(?:执行|运行|安装|配置|创建|修改|删除|添加|运行|执行|run|execute|install|config|create|modify|delete|add)\b',
            text
        ))
        if action_verbs >= 3:
            score = min(self.max_score, score)
        elif action_verbs >= 1:
            score -= 0.5
        else:
            score -= 1.5

        has_steps = bool(re.search(r'(?:步骤|Step\s*\d|^\d+[.)])', text, re.MULTILINE))
        if has_steps:
            score = min(self.max_score, score + 0.3)

        has_examples = bool(re.search(r'```\s*\w*', text))
        if has_examples:
            score = min(self.max_score, score + 0.2)

        return max(0.0, score)

    def _score_safety(self, text: str) -> float:
        """安全性评分"""
        score = self.max_score

        dangerous_commands = [
            r'rm\s+-rf\s+/',
            r'DROP\s+DATABASE',
            r'>\s*/etc/',
            r'chmod\s+777',
            r'curl.*\|\s*(sh|bash)'
        ]

        for pattern in dangerous_commands:
            if re.search(pattern, text, re.IGNORECASE):
                score -= 2.0

        destructive_actions = len(re.findall(
            r'\b(?:delete|drop|truncate|remove|destroy|格式化|删除)\b',
            text
        ))
        if destructive_actions > 0:
            has_warning = bool(re.search(
                r'(?:警告|注意|小心|warning|caution|backup)',
                text,
                re.IGNORECASE
            ))
            if not has_warning:
                score -= min(1.0, destructive_actions * 0.5)

        return max(0.0, min(self.max_score, score))

    def _prepare_rollback_state(self, input_data: InputData) -> Dict[str, Any]:
        """准备回滚状态"""
        state = {
            'timestamp': datetime.now().isoformat(),
            'input_hash': hashlib.md5(
                input_data.raw_input.encode('utf-8')
            ).hexdigest(),
            'previous_stable': self._stable_state is not None,
            'state_preserved': True
        }

        if self._stable_state is None:
            self._stable_state = {
                'original_input': input_data.raw_input[:1000],
                'context_snapshot': dict(input_data.context) if input_data.context else {},
                'timestamp': state['timestamp']
            }

        self.ROLLBACK_STATES.append(state)
        if len(self.ROLLBACK_STATES) > 10:
            self.ROLLBACK_STATES.pop(0)

        return state

    def _determine_fallback_strategy(
        self,
        quality_result: LayerResult
    ) -> Optional[FallbackStrategy]:
        """确定降级策略"""
        score = quality_result.score
        details = quality_result.details.get('dimension_scores', {})

        if score >= self.quality_threshold:
            return None

        safety_score = details.get('safety', self.max_score)
        clarity_score = details.get('clarity', self.max_score)

        if safety_score < 2.0:
            return FallbackStrategy.ESCALATE_TO_HUMAN

        if score < 2.5:
            return FallbackStrategy.REQUEST_HUMAN_HELP

        if clarity_score < 2.5:
            return FallbackStrategy.SIMPLIFY_TASK

        actionability_score = details.get('actionability', self.max_score)
        if actionability_score < 2.0:
            return FallbackStrategy.RETRY_WITH_CONTEXT

        return FallbackStrategy.SIMPLIFY_TASK

    def _record_error_log(
        self,
        input_data: InputData,
        quality_result: LayerResult,
        strategy: Optional[FallbackStrategy]
    ) -> Dict[str, Any]:
        """错误日志记录与根因分析"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'input_summary': input_data.raw_input[:200],
            'quality_score': quality_result.score,
            'dimension_scores': quality_result.details.get('dimension_scores', {}),
            'fallback_strategy': strategy.value if strategy else None,
            'root_cause_analysis': self._analyze_root_cause(quality_result),
            'session_info': {
                'user_id': input_data.user_id,
                'session_id': input_data.session_id
            }
        }

        logger.warning(
            f"[FallbackRecovery] 质量评分: {quality_result.score:.1f}, "
            f"策略: {strategy.value if strategy else 'none'}"
        )

        return log_entry

    def _analyze_root_cause(self, quality_result: LayerResult) -> Dict[str, Any]:
        """根因分析"""
        dimensions = quality_result.details.get('dimension_scores', {})
        weak_dimensions = sorted(
            [(k, v) for k, v in dimensions.items() if v < self.quality_threshold],
            key=lambda x: x[1]
        )

        causes = []
        for dim, score in weak_dimensions[:3]:
            cause_map = {
                'completeness': '输出内容不完整，可能缺少关键信息或示例',
                'accuracy': '存在矛盾或不准确的信息，需要事实核查',
                'clarity': '表达不够清晰，可能过于冗长或缺乏结构',
                'actionability': '缺乏可执行的步骤或指导',
                'safety': '包含潜在的安全风险或破坏性操作'
            }
            causes.append({
                'dimension': dim,
                'score': score,
                'likely_cause': cause_map.get(dim, '未知原因')
            })

        return {
            'weak_dimensions': weak_dimensions[:3],
            'primary_causes': causes,
            'recommendations': self._generate_recommendations(weak_dimensions)
        }

    def _generate_recommendations(
        self,
        weak_dimensions: List[Tuple[str, float]]
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        dimension_names = [d[0] for d in weak_dimensions]

        if 'completeness' in dimension_names:
            recommendations.append('增加详细的解释和代码示例')
        if 'accuracy' in dimension_names:
            recommendations.append('核实技术细节的准确性')
        if 'clarity' in dimension_names:
            recommendations.append('改善文本结构和格式化')
        if 'actionability' in dimension_names:
            recommendations.append('提供清晰的步骤说明')
        if 'safety' in dimension_names:
            recommendations.append('添加安全警告和预防措施')

        return recommendations


class FourDimensionalDefense:
    """
    四维度输出防线系统主类
    协调四层防线的调用，提供完整的输出质量控制
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.prompt_layer = PromptLayer(
            self.config.get('prompt_layer', {})
        )
        self.capability_layer = CapabilityLayer(
            self.config.get('capability_layer', {})
        )
        self.rule_validation_layer = RuleValidationLayer(
            self.config.get('rule_validation_layer', {})
        )
        self.fallback_layer = FallbackRecoveryLayer(
            self.config.get('fallback_layer', {})
        )

        self.layers = [
            self.prompt_layer,
            self.capability_layer,
            self.rule_validation_layer,
            self.fallback_layer
        ]

    def run_full_check(self, input_data: InputData) -> DefenseResult:
        """
        执行完整的四维度防线检查

        Args:
            input_data: 输入数据对象

        Returns:
            DefenseResult: 完整的防线检查结果
        """
        start_time = time.time()
        layers_result = []
        all_errors = []
        intent_type = IntentType.UNKNOWN

        for layer in self.layers:
            try:
                logger.info(f"执行防线层: {layer.name}")
                result = layer.process(input_data)
                layers_result.append(result)

                if layer.name == "PromptLayer":
                    intent_value = result.details.get('intent', 'unknown')
                    try:
                        intent_type = IntentType(intent_value)
                    except ValueError:
                        intent_type = IntentType.UNKNOWN

                if result.status == LayerStatus.FAILED:
                    logger.warning(f"防线层 {layer.name} 检查未通过: {result.message}")
                    all_errors.append({
                        'layer': layer.name,
                        'status': result.status.value,
                        'message': result.message,
                        'details': result.details
                    })
            except Exception as e:
                logger.error(f"防线层 {layer.name} 执行异常: {e}")
                error_result = LayerResult(
                    layer_name=layer.name,
                    status=LayerStatus.FAILED,
                    score=0.0,
                    message=f"执行异常: {str(e)}",
                    details={'error': str(e)}
                )
                layers_result.append(error_result)
                all_errors.append({
                    'layer': layer.name,
                    'status': LayerStatus.FAILED.value,
                    'message': str(e),
                    'details': {'exception': str(e)}
                })

        total_duration = (time.time() - start_time) * 1000

        if layers_result:
            overall_score = sum(layer.score for layer in layers_result) / len(layers_result)
        else:
            overall_score = 0.0

        failed_layers = sum(
            1 for l in layers_result if l.status == LayerStatus.FAILED
        )
        warning_layers = sum(
            1 for l in layers_result if l.status == LayerStatus.WARNING
        )

        success = (
            failed_layers == 0 and
            overall_score >= 0.6 and
            layers_result[-1].score >= 3.5 if layers_result else False
        )

        fallback_strategy = None
        if not success and layers_result:
            fallback_details = layers_result[-1].details
            strategy_str = fallback_details.get('fallback_strategy')
            if strategy_str:
                try:
                    fallback_strategy = FallbackStrategy(strategy_str)
                except ValueError:
                    pass

        defense_result = DefenseResult(
            success=success,
            overall_score=overall_score,
            intent_type=intent_type,
            layers=layers_result,
            fallback_strategy=fallback_strategy,
            error_log=all_errors,
            metadata={
                'total_layers': len(layers_result),
                'passed_layers': sum(
                    1 for l in layers_result if l.status == LayerStatus.PASSED
                ),
                'failed_layers': failed_layers,
                'warning_layers': warning_layers,
                'config_used': self.config
            },
            total_duration_ms=total_duration
        )

        logger.info(
            f"四维防线检查完成 - 成功: {success}, "
            f"总分: {overall_score:.2f}, 耗时: {total_duration:.0f}ms"
        )

        return defense_result

    def get_layer_status_summary(self, result: DefenseResult) -> Dict[str, Any]:
        """获取各层状态摘要"""
        summary = {
            'overall': {
                'success': result.success,
                'score': result.overall_score,
                'intent': result.intent_type.value
            },
            'layers': {}
        }

        for layer in result.layers:
            summary['layers'][layer.layer_name] = {
                'status': layer.status.value,
                'score': layer.score,
                'message': layer.message,
                'duration_ms': layer.duration_ms
            }

        return summary

    def generate_report(self, result: DefenseResult) -> str:
        """生成人类可读的报告"""
        lines = [
            "=" * 60,
            "四维度输出防线系统 - 检查报告",
            "=" * 60,
            "",
            f"检查时间: {result.timestamp}",
            f"总体状态: {'✅ 通过' if result.success else '❌ 未通过'}",
            f"综合评分: {result.overall_score:.2f}/5.00",
            f"识别意图: {result.intent_type.value}",
            f"总耗时: {result.total_duration_ms:.0f}ms",
            "",
            "-" * 40,
            "各层详情:",
            "-" * 40,
        ]

        for i, layer in enumerate(result.layers, 1):
            status_icon = {
                LayerStatus.PASSED: '✅',
                LayerStatus.WARNING: '⚠️',
                LayerStatus.FAILED: '❌',
                LayerStatus.SKIPPED: '⏭️'
            }.get(layer.status, '❓')

            lines.extend([
                "",
                f"第{i}层 [{layer.layer_name}] {status_icon}",
                f"  状态: {layer.status.value}",
                f"  评分: {layer.score:.2f}",
                f"  消息: {layer.message}",
                f"  耗时: {layer.duration_ms:.1f}ms"
            ])

        if result.fallback_strategy:
            lines.extend([
                "",
                "-" * 40,
                "降级策略:",
                "-" * 40,
                f"策略类型: {result.fallback_strategy.value}"
            ])

        if result.error_log:
            lines.extend([
                "",
                "-" * 40,
                "错误日志:",
                "-" * 40,
            ])
            for error in result.error_log[:5]:
                lines.append(f"  - [{error.get('layer', 'unknown')}] {error.get('message', '')}")

        lines.extend(["", "=" * 60])

        return "\n".join(lines)


def create_defense_system(config: Optional[Dict[str, Any]] = None) -> FourDimensionalDefense:
    """工厂函数：创建四维度防线系统实例"""
    return FourDimensionalDefense(config)


def main():
    """命令行入口"""
    import argparse

    parser = argparse.ArgumentParser(description='四维度输出防线系统')
    parser.add_argument('--input', '-i', type=str, help='输入文本')
    parser.add_argument('--file', '-f', type=str, help='输入文件路径')
    parser.add_argument('--json', '-j', action='store_true', help='JSON格式输出')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            input_text = f.read()
    elif args.input:
        input_text = args.input
    else:
        input_text = "请帮我创建一个Python函数来实现用户认证功能"

    input_data = InputData(raw_input=input_text)
    defense = create_defense_system()
    result = defense.run_full_check(input_data)

    if args.json:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(defense.generate_report(result))


if __name__ == '__main__':
    main()
