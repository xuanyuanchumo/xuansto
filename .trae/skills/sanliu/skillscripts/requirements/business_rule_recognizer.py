#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
业务规则识别器
支持关键词匹配、模式识别、语义分析
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Tuple, Set
from enum import Enum
from datetime import datetime
import hashlib


class RecognitionMethod(Enum):
    KEYWORD_MATCH = "keyword_match"
    PATTERN_RECOGNITION = "pattern_recognition"
    SEMANTIC_ANALYSIS = "semantic_analysis"
    HYBRID = "hybrid"


class RuleCategory(Enum):
    ACCESS_CONTROL = "access_control"
    DATA_VALIDATION = "data_validation"
    BUSINESS_LOGIC = "business_logic"
    CALCULATION = "calculation"
    WORKFLOW = "workflow"
    CONSTRAINT = "constraint"
    NOTIFICATION = "notification"
    SECURITY = "security"


@dataclass
class RulePattern:
    name: str
    pattern: re.Pattern
    category: RuleCategory
    description: str
    examples: List[str] = field(default_factory=list)
    
    def match(self, text: str) -> List[Tuple[str, Tuple[int, int]]]:
        matches = []
        for match in self.pattern.finditer(text):
            matches.append((match.group(), match.span()))
        return matches


@dataclass
class KeywordSet:
    category: RuleCategory
    keywords: List[str]
    weight: float = 1.0
    context_words: List[str] = field(default_factory=list)


@dataclass
class RecognizedRule:
    text: str
    start_pos: int
    end_pos: int
    category: RuleCategory
    confidence: float
    method: RecognitionMethod
    matched_keywords: List[str] = field(default_factory=list)
    matched_patterns: List[str] = field(default_factory=list)
    context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "category": self.category.value,
            "confidence": self.confidence,
            "method": self.method.value,
            "matched_keywords": self.matched_keywords,
            "matched_patterns": self.matched_patterns,
            "context": self.context
        }


@dataclass
class RecognitionResult:
    source_text: str
    recognized_rules: List[RecognizedRule]
    categories_found: Set[RuleCategory]
    total_confidence: float
    processing_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_text": self.source_text[:200] + "..." if len(self.source_text) > 200 else self.source_text,
            "recognized_rules": [r.to_dict() for r in self.recognized_rules],
            "categories_found": [c.value for c in self.categories_found],
            "total_confidence": self.total_confidence,
            "processing_time_ms": self.processing_time_ms
        }


class BusinessRuleRecognizer:
    KEYWORD_SETS: Dict[RuleCategory, KeywordSet] = {
        RuleCategory.ACCESS_CONTROL: KeywordSet(
            category=RuleCategory.ACCESS_CONTROL,
            keywords=["权限", "访问", "授权", "登录", "认证", "角色", "permission", "access", "auth", "login", "role"],
            weight=1.2,
            context_words=["用户", "系统", "管理员", "user", "admin"]
        ),
        RuleCategory.DATA_VALIDATION: KeywordSet(
            category=RuleCategory.DATA_VALIDATION,
            keywords=["验证", "校验", "检查", "必须", "不能为空", "格式", "validate", "check", "verify", "required", "format"],
            weight=1.0,
            context_words=["输入", "数据", "字段", "input", "data", "field"]
        ),
        RuleCategory.BUSINESS_LOGIC: KeywordSet(
            category=RuleCategory.BUSINESS_LOGIC,
            keywords=["如果", "当", "则", "否则", "条件", "if", "then", "else", "when", "condition"],
            weight=1.1,
            context_words=["执行", "处理", "触发", "execute", "process", "trigger"]
        ),
        RuleCategory.CALCULATION: KeywordSet(
            category=RuleCategory.CALCULATION,
            keywords=["计算", "公式", "等于", "总和", "平均值", "calculate", "formula", "sum", "average", "total"],
            weight=1.0,
            context_words=["金额", "数量", "价格", "amount", "quantity", "price"]
        ),
        RuleCategory.WORKFLOW: KeywordSet(
            category=RuleCategory.WORKFLOW,
            keywords=["流程", "步骤", "审批", "状态", "流转", "workflow", "step", "approval", "status", "transition"],
            weight=1.0,
            context_words=["开始", "结束", "下一步", "start", "end", "next"]
        ),
        RuleCategory.CONSTRAINT: KeywordSet(
            category=RuleCategory.CONSTRAINT,
            keywords=["限制", "约束", "最大", "最小", "范围", "limit", "constraint", "max", "min", "range"],
            weight=0.9,
            context_words=["数量", "时间", "长度", "count", "time", "length"]
        ),
        RuleCategory.NOTIFICATION: KeywordSet(
            category=RuleCategory.NOTIFICATION,
            keywords=["通知", "提醒", "消息", "邮件", "短信", "notify", "alert", "message", "email", "sms"],
            weight=0.8,
            context_words=["发送", "接收", "推送", "send", "receive", "push"]
        ),
        RuleCategory.SECURITY: KeywordSet(
            category=RuleCategory.SECURITY,
            keywords=["安全", "加密", "密码", "敏感", "防护", "security", "encrypt", "password", "sensitive", "protection"],
            weight=1.3,
            context_words=["数据", "信息", "传输", "data", "info", "transfer"]
        ),
    }
    
    RULE_PATTERNS: List[RulePattern] = [
        RulePattern(
            name="conditional_rule",
            pattern=re.compile(r'(?:如果|当|若)\s*.+?\s*(?:则|那么|就)\s*.+?(?:。|；|$)', re.DOTALL),
            category=RuleCategory.BUSINESS_LOGIC,
            description="条件规则模式：如果...则...",
            examples=["如果用户未登录，则跳转到登录页面。"]
        ),
        RulePattern(
            name="validation_rule",
            pattern=re.compile(r'.+?\s*(?:必须|需要|应该)\s*(?:是|为|包含|符合).+?(?:，|。|$)', re.DOTALL),
            category=RuleCategory.DATA_VALIDATION,
            description="验证规则模式：...必须...",
            examples=["用户名必须为字母数字组合。"]
        ),
        RulePattern(
            name="calculation_rule",
            pattern=re.compile(r'.+?\s*(?:等于|为|=)\s*.+?(?:之和|积|的结果)?(?:。|；|$)', re.DOTALL),
            category=RuleCategory.CALCULATION,
            description="计算规则模式：...等于...",
            examples=["总价等于单价乘以数量。"]
        ),
        RulePattern(
            name="constraint_rule",
            pattern=re.compile(r'.+?\s*(?:不能超过|不超过|最大|最小|范围).+?(?:，|。|$)', re.DOTALL),
            category=RuleCategory.CONSTRAINT,
            description="约束规则模式：...不能超过...",
            examples=["订单数量不能超过库存。"]
        ),
        RulePattern(
            name="access_control_rule",
            pattern=re.compile(r'(?:只有|仅)?\s*.+?\s*(?:可以|能够|有权|允许)\s*.+?(?:，|。|$)', re.DOTALL),
            category=RuleCategory.ACCESS_CONTROL,
            description="访问控制规则模式：...可以...",
            examples=["只有管理员可以删除用户。"]
        ),
        RulePattern(
            name="notification_rule",
            pattern=re.compile(r'(?:当|如果)\s*.+?\s*(?:时|情况下)\s*(?:发送|通知|提醒)\s*.+?(?:，|。|$)', re.DOTALL),
            category=RuleCategory.NOTIFICATION,
            description="通知规则模式：当...时发送...",
            examples=["当订单状态变更时，发送通知给用户。"]
        ),
        RulePattern(
            name="workflow_rule",
            pattern=re.compile(r'.+?\s*(?:完成后|通过后|审批后)\s*.+?(?:，|。|$)', re.DOTALL),
            category=RuleCategory.WORKFLOW,
            description="工作流规则模式：...完成后...",
            examples=["审批完成后，自动进入下一环节。"]
        ),
        RulePattern(
            name="security_rule",
            pattern=re.compile(r'.+?\s*(?:加密|脱敏|隐藏|保护)\s*.+?(?:，|。|$)', re.DOTALL),
            category=RuleCategory.SECURITY,
            description="安全规则模式：...加密...",
            examples=["密码必须加密存储。"]
        ),
    ]
    
    SENTENCE_DELIMITERS = re.compile(r'[。！？；\n]')
    
    def __init__(self, min_confidence: float = 0.5):
        self.min_confidence = min_confidence
        self._build_keyword_index()
    
    def _build_keyword_index(self):
        self._keyword_to_category: Dict[str, Tuple[RuleCategory, float]] = {}
        for category, keyword_set in self.KEYWORD_SETS.items():
            for keyword in keyword_set.keywords:
                self._keyword_to_category[keyword.lower()] = (category, keyword_set.weight)
    
    def _split_into_sentences(self, text: str) -> List[Tuple[str, int, int]]:
        sentences = []
        start = 0
        
        for match in self.SENTENCE_DELIMITERS.finditer(text):
            end = match.end()
            sentence = text[start:end].strip()
            if sentence:
                sentences.append((sentence, start, end))
            start = end
        
        if start < len(text):
            sentence = text[start:].strip()
            if sentence:
                sentences.append((sentence, start, len(text)))
        
        return sentences
    
    def _match_keywords(self, text: str) -> Tuple[RuleCategory, float, List[str]]:
        text_lower = text.lower()
        category_scores: Dict[RuleCategory, List[Tuple[float, str]]] = {}
        
        for keyword, (category, weight) in self._keyword_to_category.items():
            if keyword in text_lower:
                if category not in category_scores:
                    category_scores[category] = []
                
                keyword_set = self.KEYWORD_SETS[category]
                context_bonus = 0.0
                
                for context_word in keyword_set.context_words:
                    if context_word.lower() in text_lower:
                        context_bonus += 0.1
                
                score = weight + context_bonus
                category_scores[category].append((score, keyword))
        
        if not category_scores:
            return (RuleCategory.BUSINESS_LOGIC, 0.0, [])
        
        best_category = max(category_scores.keys(), 
                          key=lambda c: sum(s[0] for s in category_scores[c]))
        scores_and_keywords = category_scores[best_category]
        total_score = sum(s[0] for s in scores_and_keywords) / len(scores_and_keywords)
        matched_keywords = [s[1] for s in scores_and_keywords]
        
        confidence = min(total_score / 2.0, 1.0)
        
        return (best_category, confidence, matched_keywords)
    
    def _match_patterns(self, text: str) -> List[Tuple[RulePattern, str, Tuple[int, int]]]:
        matches = []
        
        for pattern in self.RULE_PATTERNS:
            pattern_matches = pattern.match(text)
            for match_text, span in pattern_matches:
                matches.append((pattern, match_text, span))
        
        return matches
    
    def _calculate_confidence(self, 
                             keyword_confidence: float, 
                             pattern_matched: bool,
                             sentence_length: int) -> float:
        base_confidence = keyword_confidence
        
        if pattern_matched:
            base_confidence = min(base_confidence + 0.3, 1.0)
        
        length_factor = min(sentence_length / 50.0, 1.0)
        
        return base_confidence * (0.7 + 0.3 * length_factor)
    
    def recognize_by_keywords(self, text: str) -> List[RecognizedRule]:
        sentences = self._split_into_sentences(text)
        recognized = []
        
        for sentence, start, end in sentences:
            category, confidence, matched_keywords = self._match_keywords(sentence)
            
            if confidence >= self.min_confidence:
                rule = RecognizedRule(
                    text=sentence,
                    start_pos=start,
                    end_pos=end,
                    category=category,
                    confidence=confidence,
                    method=RecognitionMethod.KEYWORD_MATCH,
                    matched_keywords=matched_keywords
                )
                recognized.append(rule)
        
        return recognized
    
    def recognize_by_patterns(self, text: str) -> List[RecognizedRule]:
        recognized = []
        
        pattern_matches = self._match_patterns(text)
        
        for pattern, match_text, (start, end) in pattern_matches:
            rule = RecognizedRule(
                text=match_text,
                start_pos=start,
                end_pos=end,
                category=pattern.category,
                confidence=0.85,
                method=RecognitionMethod.PATTERN_RECOGNITION,
                matched_patterns=[pattern.name]
            )
            recognized.append(rule)
        
        return recognized
    
    def recognize_hybrid(self, text: str) -> List[RecognizedRule]:
        keyword_results = self.recognize_by_keywords(text)
        pattern_results = self.recognize_by_patterns(text)
        
        all_rules = []
        used_positions = set()
        
        for rule in pattern_results:
            pos_key = (rule.start_pos, rule.end_pos)
            if pos_key not in used_positions:
                all_rules.append(rule)
                used_positions.add(pos_key)
        
        for rule in keyword_results:
            overlaps = False
            for start, end in used_positions:
                if not (rule.end_pos <= start or rule.start_pos >= end):
                    overlaps = True
                    break
            
            if not overlaps:
                all_rules.append(rule)
                used_positions.add((rule.start_pos, rule.end_pos))
        
        all_rules.sort(key=lambda r: r.start_pos)
        
        return all_rules
    
    def recognize(self, 
                  text: str, 
                  method: RecognitionMethod = RecognitionMethod.HYBRID) -> RecognitionResult:
        import time
        start_time = time.time()
        
        if method == RecognitionMethod.KEYWORD_MATCH:
            rules = self.recognize_by_keywords(text)
        elif method == RecognitionMethod.PATTERN_RECOGNITION:
            rules = self.recognize_by_patterns(text)
        else:
            rules = self.recognize_hybrid(text)
        
        categories_found = {rule.category for rule in rules}
        
        total_confidence = sum(r.confidence for r in rules) / len(rules) if rules else 0.0
        
        processing_time = (time.time() - start_time) * 1000
        
        return RecognitionResult(
            source_text=text,
            recognized_rules=rules,
            categories_found=categories_found,
            total_confidence=total_confidence,
            processing_time_ms=processing_time
        )
    
    def get_rule_statistics(self, result: RecognitionResult) -> Dict[str, Any]:
        category_counts: Dict[RuleCategory, int] = {}
        for rule in result.recognized_rules:
            category_counts[rule.category] = category_counts.get(rule.category, 0) + 1
        
        return {
            "total_rules": len(result.recognized_rules),
            "categories": {c.value: count for c, count in category_counts.items()},
            "average_confidence": result.total_confidence,
            "processing_time_ms": result.processing_time_ms
        }


def main():
    recognizer = BusinessRuleRecognizer(min_confidence=0.4)
    
    test_texts = [
        """
        用户登录系统时，必须输入正确的用户名和密码。如果连续登录失败超过3次，则锁定账户24小时。
        只有管理员可以删除用户账户。密码必须加密存储，不能明文保存。
        订单总金额等于商品单价乘以数量。当订单状态变更为"已发货"时，发送通知邮件给用户。
        """,
        """
        数据验证规则：用户名长度必须在6-20个字符之间，只能包含字母和数字。
        邮箱地址必须符合标准格式。手机号码必须是11位数字。
        """,
        """
        业务流程：用户提交订单后，系统自动检查库存。如果库存充足，则创建订单并扣减库存；
        如果库存不足，则提示用户并取消订单。订单完成后，发送确认短信给用户。
        """
    ]
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n{'='*60}")
        print(f"测试用例 {i}")
        print('='*60)
        print(f"原文: {text.strip()[:100]}...")
        
        result = recognizer.recognize(text)
        
        print(f"\n识别结果:")
        print(f"  总规则数: {len(result.recognized_rules)}")
        print(f"  平均置信度: {result.total_confidence:.2f}")
        print(f"  处理时间: {result.processing_time_ms:.2f}ms")
        print(f"  发现类别: {[c.value for c in result.categories_found]}")
        
        print(f"\n详细规则:")
        for rule in result.recognized_rules:
            print(f"  [{rule.category.value}] ({rule.confidence:.2f}) {rule.text[:50]}...")
        
        stats = recognizer.get_rule_statistics(result)
        print(f"\n统计信息:")
        print(f"  {json.dumps(stats, ensure_ascii=False, indent=4)}")


if __name__ == "__main__":
    main()
