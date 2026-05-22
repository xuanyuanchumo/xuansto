#!/usr/bin/env python3
"""
上下文压缩脚本
功能：压缩长对话，保留关键信息
"""

import argparse
import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional
from collections import Counter
from dataclasses import dataclass, field


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='上下文压缩脚本 - 压缩长对话，保留关键信息'
    )
    parser.add_argument(
        '--input',
        type=str,
        default=None,
        help='输入对话文件路径（JSON格式）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='compressed-context.json',
        help='输出文件路径（默认：compressed-context.json）'
    )
    parser.add_argument(
        '--max-tokens',
        type=int,
        default=4000,
        help='最大token数（默认：4000）'
    )
    parser.add_argument(
        '--strategy',
        type=str,
        choices=['summary', 'key-points', 'sliding-window', 'hierarchical', 'lossless', 'semantic', 'selective'],
        default='key-points',
        help='压缩策略（默认：key-points）'
    )
    parser.add_argument(
        '--preserve-code',
        action='store_true',
        help='保留代码块'
    )
    parser.add_argument(
        '--preserve-decisions',
        action='store_true',
        help='保留决策点'
    )
    parser.add_argument(
        '--auto',
        action='store_true',
        help='自动根据Token使用率选择压缩级别'
    )
    return parser.parse_args()


@dataclass
class Message:
    """消息数据类"""
    role: str
    content: str
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    importance: float = 0.0


@dataclass
class CompressedContext:
    """压缩后的上下文"""
    summary: str
    key_points: List[str]
    decisions: List[str]
    code_snippets: List[str]
    entities: Dict[str, List[str]]
    original_length: int
    compressed_length: int
    compression_ratio: float


def extract_key_facts(text: str) -> list[str]:
    facts = []

    named_entities = re.findall(r'\b[A-Z][a-zA-Z0-9]*(?:\s+[A-Z][a-zA-Z0-9]*)*\b', text)
    facts.extend(named_entities)

    quoted_terms = re.findall(r'["\u201c\u300c]([^"\u201d\u300d]+)["\u201d\u300d]', text)
    facts.extend(quoted_terms)

    numerical = re.findall(r'\b\d+(?:\.\d+)?\s*(?:%|percent|阈值|上限|下限|threshold|limit|max|min)\b', text, re.IGNORECASE)
    facts.extend(numerical)

    numerical_plain = re.findall(r'\b\d+(?:\.\d+)?\b', text)
    facts.extend(numerical_plain)

    conditionals = re.findall(r'(?:if|when|unless|如果|当|除非|若)\s+[^。！？.!?]{3,80}', text, re.IGNORECASE)
    facts.extend(conditionals)

    mandatory = re.findall(r'(?:MUST|SHALL|REQUIRED|强制|必须|应当|不得|禁止)[^。！？.!?]{0,80}', text, re.IGNORECASE)
    facts.extend(mandatory)

    return facts


def verify_key_facts(original: str, compressed: str, threshold: float = 0.95) -> tuple[bool, float]:
    original_facts = extract_key_facts(original)
    compressed_facts = extract_key_facts(compressed)

    if not original_facts:
        return True, 1.0

    compressed_lower = compressed.lower()
    preserved = 0
    for fact in original_facts:
        if fact.lower() in compressed_lower:
            preserved += 1

    retention_rate = preserved / len(original_facts)
    return (retention_rate >= threshold, retention_rate)


class LosslessCompressor:
    """Level 1: 无损压缩 - 移除空白、合并引用、压缩JSON/YAML"""

    def compress(self, content: str) -> Tuple[str, float]:
        result = content
        result = re.sub(r'\n{3,}', '\n\n', result)
        result = re.sub(r'[\t ]+$', '', result, flags=re.MULTILINE)
        result = re.sub(r'<!--[\s\S]*?-->', '', result)
        result = re.sub(r'(\[.*?\])\[\]\(\)', r'\1', result)
        json_blocks = re.findall(r'```json\n([\s\S]*?)```', result)
        for block in json_blocks:
            try:
                parsed = json.loads(block)
                compressed = json.dumps(parsed, ensure_ascii=False, separators=(',', ':'))
                result = result.replace(f'```json\n{block}```', f'```json\n{compressed}```')
            except json.JSONDecodeError:
                pass
        yaml_blocks = re.findall(r'```yaml\n([\s\S]*?)```', result)
        for block in yaml_blocks:
            lines = [line.rstrip() for line in block.split('\n') if line.strip()]
            compressed = '\n'.join(lines)
            result = result.replace(f'```yaml\n{block}```', f'```yaml\n{compressed}```')
        ratio = 1 - (len(result) / max(len(content), 1))
        return result, ratio


class SemanticCompressor:
    """Level 2: 语义压缩 - 摘要化、知识条目精简、消息压缩"""

    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def compress(self, messages: List[Message]) -> Tuple[List[Message], float]:
        if not messages:
            return messages, 0.0
        compressed = []
        for msg in messages:
            if len(msg.content) > 500:
                sentences = re.split(r'[。！？.!?]', msg.content)
                sentences = [s.strip() for s in sentences if s.strip()]
                if len(sentences) > 3:
                    summary = '。'.join(sentences[:3]) + '。'
                    new_msg = Message(
                        role=msg.role,
                        content=summary,
                        timestamp=msg.timestamp,
                        metadata={**msg.metadata, 'compressed': True, 'original_length': len(msg.content)},
                        importance=msg.importance
                    )
                    compressed.append(new_msg)
                else:
                    compressed.append(msg)
            else:
                compressed.append(msg)
        merged = self._merge_consecutive_short(compressed)
        original_len = sum(len(m.content) for m in messages)
        compressed_len = sum(len(m.content) for m in merged)
        ratio = 1 - (compressed_len / max(original_len, 1))
        return merged, ratio

    def _merge_consecutive_short(self, messages: List[Message], threshold: int = 100) -> List[Message]:
        if not messages:
            return messages
        result = [messages[0]]
        for msg in messages[1:]:
            last = result[-1]
            if (last.role == msg.role and len(last.content) < threshold and len(msg.content) < threshold):
                merged_content = last.content + ' ' + msg.content
                result[-1] = Message(
                    role=last.role,
                    content=merged_content,
                    timestamp=last.timestamp,
                    metadata={**last.metadata, 'merged': True},
                    importance=max(last.importance, msg.importance)
                )
            else:
                result.append(msg)
        return result


class SelectiveCompressor:
    """Level 3: 选择性压缩 - 丢弃低相关性历史、仅保留核心上下文"""

    def __init__(self, max_tokens: int = 4000, top_k: int = 3):
        self.max_tokens = max_tokens
        self.top_k = top_k

    def compress(self, messages: List[Message], core_decisions: List[str] = None) -> Tuple[List[Message], float]:
        if not messages:
            return messages, 0.0
        core_decisions = core_decisions or []
        recent = messages[-3:] if len(messages) > 3 else messages[:]
        important = sorted(
            [m for m in messages[:-3] if m.importance >= 0.7],
            key=lambda m: m.importance,
            reverse=True
        )[:self.top_k]
        decision_msgs = []
        for msg in messages:
            for decision in core_decisions:
                if decision in msg.content:
                    decision_msgs.append(msg)
                    break
        seen_ids = set()
        result = []
        for msg in important + decision_msgs + recent:
            msg_id = id(msg)
            if msg_id not in seen_ids:
                seen_ids.add(msg_id)
                result.append(msg)
        msg_index = {id(m): i for i, m in enumerate(messages)}
        result.sort(key=lambda m: msg_index.get(id(m), 0))
        original_len = sum(len(m.content) for m in messages)
        compressed_len = sum(len(m.content) for m in result)
        ratio = 1 - (compressed_len / max(original_len, 1))
        return result, ratio


class ConversationCompressor:

    def __init__(self, max_tokens: int, preserve_code: bool, preserve_decisions: bool, knowledge_dir: str = '.knowledge'):
        self.max_tokens = max_tokens
        self.preserve_code = preserve_code
        self.preserve_decisions = preserve_decisions
        self.messages: List[Message] = []
        self.knowledge_dir = knowledge_dir
        self.compression_log_path = os.path.join(knowledge_dir, 'compression-log.json')
        self._ensure_log_file()

    def load_conversation(self, input_path: str) -> bool:
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if isinstance(data, list):
                for msg in data:
                    self.messages.append(Message(
                        role=msg.get('role', 'unknown'),
                        content=msg.get('content', ''),
                        timestamp=msg.get('timestamp'),
                        metadata=msg.get('metadata', {}),
                        importance=0.0
                    ))
            elif isinstance(data, dict):
                if 'messages' in data:
                    for msg in data['messages']:
                        self.messages.append(Message(
                            role=msg.get('role', 'unknown'),
                            content=msg.get('content', ''),
                            timestamp=msg.get('timestamp'),
                            metadata=msg.get('metadata', {}),
                            importance=0.0
                        ))

            return True

        except Exception as e:
            print(f"加载对话失败: {e}")
            return False

    def compress(self, strategy: str) -> CompressedContext:
        if not self.messages:
            return CompressedContext(
                summary="无对话内容",
                key_points=[],
                decisions=[],
                code_snippets=[],
                entities={},
                original_length=0,
                compressed_length=0,
                compression_ratio=0.0
            )

        self._calculate_importance()

        if strategy == 'summary':
            result = self._compress_by_summary()
        elif strategy == 'key-points':
            result = self._compress_by_key_points()
        elif strategy == 'sliding-window':
            result = self._compress_by_sliding_window()
        else:
            result = self._compress_hierarchical()

        max_chars = self.max_tokens * 4
        total_chars = len(result.summary)
        total_chars += sum(len(kp) for kp in result.key_points)
        total_chars += sum(len(d) for d in result.decisions)
        total_chars += sum(len(cs) for cs in result.code_snippets)
        for entity_list in result.entities.values():
            total_chars += sum(len(e) for e in entity_list)

        if total_chars > max_chars:
            result.summary = result.summary[:max_chars]
            result.compressed_length = len(result.summary)
            result.compression_ratio = 1 - (result.compressed_length / max(result.original_length, 1))

        return result

    def _calculate_importance(self):
        for i, msg in enumerate(self.messages):
            score = 0.0

            if msg.role == 'user':
                score += 0.3

            if self._contains_decision(msg.content):
                score += 0.5

            if self._contains_code(msg.content):
                score += 0.3

            if self._contains_question(msg.content):
                score += 0.2

            keywords = ['重要', '关键', '决定', '必须', '注意', '错误', '问题', 'important', 'key', 'decision', 'error', 'bug']
            for kw in keywords:
                if kw.lower() in msg.content.lower():
                    score += 0.1

            if i < 3:
                score += 0.2
            elif i >= len(self.messages) - 3:
                score += 0.3

            msg.importance = min(score, 1.0)

    def _contains_decision(self, content: str) -> bool:
        decision_patterns = [
            r'决定|决策|选择|采用|确定',
            r'decide|decision|choose|select|determine',
            r'我们(将|会|决定)',
            r'let\'s|we will|we decided'
        ]
        return any(re.search(p, content, re.IGNORECASE) for p in decision_patterns)

    def _contains_code(self, content: str) -> bool:
        return bool(re.search(r'```[\s\S]*?```|`[^`]+`', content))

    def _contains_question(self, content: str) -> bool:
        return '?' in content or '？' in content

    def _compress_by_summary(self) -> CompressedContext:
        all_content = '\n'.join([f"{m.role}: {m.content}" for m in self.messages])

        summary = self._generate_summary(all_content)
        key_points = self._extract_key_points()
        decisions = self._extract_decisions()
        code_snippets = self._extract_code_snippets()
        entities = self._extract_entities()

        original_length = len(all_content)
        compressed_length = len(summary) + sum(len(kp) for kp in key_points)

        return CompressedContext(
            summary=summary,
            key_points=key_points,
            decisions=decisions,
            code_snippets=code_snippets,
            entities=entities,
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=1 - (compressed_length / max(original_length, 1))
        )

    def _compress_by_key_points(self) -> CompressedContext:
        key_points = self._extract_key_points()
        decisions = self._extract_decisions() if self.preserve_decisions else []
        code_snippets = self._extract_code_snippets() if self.preserve_code else []
        entities = self._extract_entities()

        summary = self._generate_summary_from_points(key_points)

        original_length = sum(len(m.content) for m in self.messages)
        compressed_length = len(summary) + sum(len(kp) for kp in key_points)

        return CompressedContext(
            summary=summary,
            key_points=key_points,
            decisions=decisions,
            code_snippets=code_snippets,
            entities=entities,
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=1 - (compressed_length / max(original_length, 1))
        )

    def _compress_by_sliding_window(self) -> CompressedContext:
        window_size = max(5, len(self.messages) // 4)

        important_messages = sorted(
            self.messages,
            key=lambda m: m.importance,
            reverse=True
        )[:window_size]

        key_points = [m.content[:200] for m in important_messages]
        decisions = self._extract_decisions()
        code_snippets = self._extract_code_snippets()
        entities = self._extract_entities()

        summary = self._generate_summary_from_points(key_points)

        original_length = sum(len(m.content) for m in self.messages)
        compressed_length = sum(len(kp) for kp in key_points)

        return CompressedContext(
            summary=summary,
            key_points=key_points,
            decisions=decisions,
            code_snippets=code_snippets,
            entities=entities,
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=1 - (compressed_length / max(original_length, 1))
        )

    def _compress_hierarchical(self) -> CompressedContext:
        chunks = []
        chunk_size = max(3, len(self.messages) // 6)

        for i in range(0, len(self.messages), chunk_size):
            chunk = self.messages[i:i+chunk_size]
            chunk_summary = self._summarize_chunk(chunk)
            chunks.append(chunk_summary)

        key_points = chunks
        decisions = self._extract_decisions()
        code_snippets = self._extract_code_snippets()
        entities = self._extract_entities()

        summary = '\n'.join([f"• {c}" for c in chunks[:5]])

        original_length = sum(len(m.content) for m in self.messages)
        compressed_length = len(summary)

        return CompressedContext(
            summary=summary,
            key_points=key_points,
            decisions=decisions,
            code_snippets=code_snippets,
            entities=entities,
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=1 - (compressed_length / max(original_length, 1))
        )

    def _generate_summary(self, content: str) -> str:
        sentences = re.split(r'[。！？.!?]', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if len(sentences) <= 5:
            return ' '.join(sentences)

        word_freq = Counter()
        for sentence in sentences:
            words = re.findall(r'\w+', sentence.lower())
            word_freq.update(words)

        sentence_scores = []
        for sentence in sentences:
            words = re.findall(r'\w+', sentence.lower())
            score = sum(word_freq.get(w, 0) for w in words)
            sentence_scores.append((sentence, score))

        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        top_sentences = [s[0] for s in sentence_scores[:5]]

        return ' '.join(top_sentences)

    def _generate_summary_from_points(self, key_points: List[str]) -> str:
        if not key_points:
            return "无关键信息"

        return f"对话包含 {len(key_points)} 个关键点，涉及 {len(self._extract_entities())} 个实体。"

    def _summarize_chunk(self, messages: List[Message]) -> str:
        if not messages:
            return ""

        content = ' '.join([m.content for m in messages])
        sentences = re.split(r'[。！？.!?]', content)
        sentences = [s.strip() for s in sentences if s.strip()]

        if sentences:
            return sentences[0][:150]
        return content[:150]

    def _extract_key_points(self) -> List[str]:
        key_points = []

        for msg in self.messages:
            if msg.importance >= 0.5:
                content = msg.content
                sentences = re.split(r'[。！？.!?]', content)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if len(sentence) > 20 and len(sentence) < 300:
                        key_points.append(sentence)

        return key_points[:20]

    def _extract_decisions(self) -> List[str]:
        decisions = []

        for msg in self.messages:
            if self._contains_decision(msg.content):
                sentences = re.split(r'[。！？.!?]', msg.content)
                for sentence in sentences:
                    if self._contains_decision(sentence):
                        decisions.append(sentence.strip())

        return decisions[:10]

    def _extract_code_snippets(self) -> List[str]:
        code_snippets = []

        for msg in self.messages:
            matches = re.findall(r'```[\s\S]*?```', msg.content)
            code_snippets.extend(matches)

        return code_snippets[:5]

    def _extract_entities(self) -> Dict[str, List[str]]:
        entities = {
            'files': [],
            'functions': [],
            'classes': [],
            'urls': []
        }

        all_content = ' '.join([m.content for m in self.messages])

        files = re.findall(r'[\w/]+\.(py|js|ts|java|go|rs|rb|php)', all_content)
        entities['files'] = list(set(files))[:10]

        functions = re.findall(r'\b([a-z_][a-z0-9_]*)\s*\(', all_content)
        entities['functions'] = list(set(functions))[:10]

        classes = re.findall(r'\b([A-Z][a-zA-Z0-9]*)\b', all_content)
        entities['classes'] = list(set(classes))[:10]

        urls = re.findall(r'https?://[^\s]+', all_content)
        entities['urls'] = list(set(urls))[:5]

        return entities

    def compress_three_level(self, level: str = 'semantic') -> Tuple[CompressedContext, str]:
        all_content = '\n'.join([f"{m.role}: {m.content}" for m in self.messages])

        if level == 'lossless':
            compressor = LosslessCompressor()
            compressed_content, ratio = compressor.compress(all_content)
            summary = compressed_content[:500]
            key_points = self._extract_key_points()
            decisions = self._extract_decisions()
            code_snippets = self._extract_code_snippets()
            entities = self._extract_entities()
        elif level == 'semantic':
            compressor = SemanticCompressor(self.max_tokens)
            compressed_msgs, ratio = compressor.compress(self.messages)
            summary = ' '.join([m.content[:200] for m in compressed_msgs[:3]])
            key_points = self._extract_key_points()
            decisions = self._extract_decisions()
            code_snippets = self._extract_code_snippets()
            entities = self._extract_entities()
        else:
            compressor = SelectiveCompressor(self.max_tokens)
            decisions = self._extract_decisions()
            compressed_msgs, ratio = compressor.compress(self.messages, decisions)
            summary = ' '.join([m.content[:200] for m in compressed_msgs[:3]])
            key_points = self._extract_key_points()
            code_snippets = self._extract_code_snippets()
            entities = self._extract_entities()

        original_length = len(all_content)
        compressed_length = len(summary) + sum(len(kp) for kp in key_points)
        unified_ratio = (original_length - compressed_length) / max(original_length, 1)

        context = CompressedContext(
            summary=summary,
            key_points=key_points,
            decisions=decisions,
            code_snippets=code_snippets,
            entities=entities,
            original_length=original_length,
            compressed_length=compressed_length,
            compression_ratio=unified_ratio
        )

        return context, level

    def verify_facts(self, original_decisions: List[str], compressed_context: CompressedContext) -> Tuple[bool, float]:
        if not original_decisions:
            return True, 0.0

        compressed_content = compressed_context.summary
        compressed_content += ' '.join(compressed_context.key_points)
        compressed_content += ' '.join(compressed_context.decisions)

        preserved = 0
        for decision in original_decisions:
            key_terms = re.findall(r'\w+', decision.lower())
            key_terms = [t for t in key_terms if len(t) > 3]
            if any(term in compressed_content.lower() for term in key_terms):
                preserved += 1

        loss_rate = 1 - (preserved / len(original_decisions))

        if loss_rate > 0.02:
            return False, loss_rate

        return True, loss_rate

    def estimate_tokens(self, text):
        try:
            import tiktoken
            enc = tiktoken.get_encoding('cl100k_base')
            return len(enc.encode(text))
        except ImportError:
            return len(text) // 4

    def check_and_compress(self, context_text, token_budget, current_usage):
        usage_rate = current_usage / token_budget if token_budget > 0 else 0
        original_tokens = self.estimate_tokens(context_text)

        if usage_rate < 0.6:
            result = context_text
            level = 'none'
        elif usage_rate < 0.8:
            compressor = LosslessCompressor()
            result, _ = compressor.compress(context_text)
            level = 'lossless'
        elif usage_rate < 0.95:
            messages = [Message(role='system', content=context_text)]
            semantic = SemanticCompressor(self.max_tokens)
            compressed_msgs, _ = semantic.compress(messages)
            result = '\n'.join(m.content for m in compressed_msgs)
            level = 'semantic'
            passed, retention_rate = verify_key_facts(context_text, result)
            self._log_key_fact_verification(level, passed, retention_rate)
            if not passed:
                compressor = LosslessCompressor()
                result, _ = compressor.compress(context_text)
                level = 'lossless'
        else:
            messages = [Message(role='system', content=context_text)]
            selective = SelectiveCompressor(self.max_tokens)
            compressed_msgs, _ = selective.compress(messages)
            result = '\n'.join(m.content for m in compressed_msgs)
            level = 'selective'

        compressed_tokens = self.estimate_tokens(result)
        tokens_saved = original_tokens - compressed_tokens

        self._log_compression(level, original_tokens, compressed_tokens, tokens_saved, usage_rate)
        return result, level, tokens_saved

    def _ensure_log_file(self):
        os.makedirs(self.knowledge_dir, exist_ok=True)
        if not os.path.exists(self.compression_log_path):
            with open(self.compression_log_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _log_compression(self, level, original_tokens, compressed_tokens, tokens_saved, usage_rate):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'original_tokens': original_tokens,
            'compressed_tokens': compressed_tokens,
            'tokens_saved': tokens_saved,
            'usage_rate': usage_rate
        }
        try:
            with open(self.compression_log_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        logs.append(entry)
        with open(self.compression_log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)

    def _log_key_fact_verification(self, level, passed, retention_rate):
        entry = {
            'timestamp': datetime.now().isoformat(),
            'type': 'key_fact_verification',
            'compression_level': level,
            'passed': passed,
            'retention_rate': round(retention_rate, 4),
            'fallback_triggered': not passed
        }
        try:
            with open(self.compression_log_path, 'r', encoding='utf-8') as f:
                logs = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            logs = []
        logs.append(entry)
        with open(self.compression_log_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)


def _read_last_token_usage(log_path):
    if not os.path.exists(log_path):
        return None
    try:
        with open(log_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        if not lines:
            return None
        last_line = lines[-1].strip()
        if not last_line:
            return None
        return json.loads(last_line)
    except (json.JSONDecodeError, OSError):
        return None


def _read_token_budget(config_path):
    budget = 100000
    if not os.path.exists(config_path):
        return budget
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            in_token_budget = False
            for line in f:
                stripped = line.rstrip()
                if stripped.startswith('token_budget:'):
                    in_token_budget = True
                    continue
                if in_token_budget:
                    if stripped.startswith('  default:'):
                        value = stripped.split(':', 1)[1].strip()
                        budget = int(value)
                        break
                    if stripped and not stripped.startswith(' ') and not stripped.startswith('\t') and not stripped.startswith('#'):
                        in_token_budget = False
    except (OSError, ValueError):
        pass
    return budget


def check_and_compress(input_path: str, output_path: str = None, skill_root: str = None) -> dict:
    result = {
        'triggered': False,
        'level': 'none',
        'before_tokens': 0,
        'after_tokens': 0,
        'savings_percent': 0.0
    }

    if skill_root is None:
        skill_root = str(Path(__file__).parent.parent)

    skill_root_path = Path(skill_root)
    log_path = skill_root_path / '.skill-logs' / 'token-usage.jsonl'
    config_path = skill_root_path / '.skill-config.yaml'

    usage_data = _read_last_token_usage(str(log_path))
    if usage_data is None:
        return result

    token_budget = _read_token_budget(str(config_path))

    current_usage = usage_data.get('total_tokens', usage_data.get('tokens_used', 0))
    usage_ratio = current_usage / token_budget if token_budget > 0 else 0

    if usage_ratio <= 0.6:
        return result

    result['triggered'] = True

    if usage_ratio > 0.95:
        level = 'selective'
    elif usage_ratio > 0.8:
        level = 'semantic'
    else:
        level = 'lossless'

    result['level'] = level

    compressor = ConversationCompressor(
        max_tokens=token_budget,
        preserve_code=True,
        preserve_decisions=True
    )

    if not compressor.load_conversation(input_path):
        result['triggered'] = False
        return result

    all_content = '\n'.join([f"{m.role}: {m.content}" for m in compressor.messages])
    before_tokens = len(all_content) // 4
    result['before_tokens'] = before_tokens

    context, used_level = compressor.compress_three_level(level)

    compressed_content = context.summary
    compressed_content += ' '.join(context.key_points)
    compressed_content += ' '.join(context.decisions)
    after_tokens = len(compressed_content) // 4
    result['after_tokens'] = after_tokens

    if before_tokens > 0:
        result['savings_percent'] = round((1 - after_tokens / before_tokens) * 100, 2)

    log_dir = skill_root_path / '.skill-logs'
    os.makedirs(str(log_dir), exist_ok=True)
    compression_log_path = log_dir / 'auto-compression-log.jsonl'
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'trigger': 'auto',
        'level': level,
        'usage_ratio': round(usage_ratio, 4),
        'before_tokens': before_tokens,
        'after_tokens': after_tokens,
        'savings_percent': result['savings_percent']
    }
    try:
        with open(str(compression_log_path), 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    except OSError:
        pass

    if output_path:
        save_compressed_context(output_path, context)

    return result


def save_compressed_context(output_path: str, context: CompressedContext):
    data = {
        'timestamp': datetime.now().isoformat(),
        'summary': context.summary,
        'key_points': context.key_points,
        'decisions': context.decisions,
        'code_snippets': context.code_snippets,
        'entities': context.entities,
        'statistics': {
            'original_length': context.original_length,
            'compressed_length': context.compressed_length,
            'compression_ratio': f"{context.compression_ratio:.2%}"
        }
    }

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n压缩结果已保存: {output_path}")


def print_summary(context: CompressedContext):
    print(f"\n{'='*60}")
    print("上下文压缩结果")
    print(f"{'='*60}")
    print(f"原始长度: {context.original_length} 字符")
    print(f"压缩后长度: {context.compressed_length} 字符")
    print(f"压缩率: {context.compression_ratio:.2%}")

    print(f"\n摘要:")
    print(f"  {context.summary[:200]}...")

    if context.key_points:
        print(f"\n关键点 ({len(context.key_points)} 个):")
        for i, kp in enumerate(context.key_points[:5], 1):
            print(f"  {i}. {kp[:100]}...")

    if context.decisions:
        print(f"\n决策 ({len(context.decisions)} 个):")
        for d in context.decisions[:3]:
            print(f"  • {d[:100]}...")

    print(f"{'='*60}")


def main():
    args = parse_args()

    if args.auto:
        if not args.input:
            print("错误: --auto 模式需要 --input 参数")
            sys.exit(1)
        result = check_and_compress(args.input, args.output)
        if result['triggered']:
            print(f"\n自动压缩已触发")
            print(f"  压缩级别: {result['level']}")
            print(f"  压缩前Token数: {result['before_tokens']}")
            print(f"  压缩后Token数: {result['after_tokens']}")
            print(f"  节省比例: {result['savings_percent']:.2f}%")
        else:
            print("\nToken使用率未达到压缩阈值，无需压缩")
        sys.exit(0)

    if not args.input:
        print("错误: 需要 --input 参数")
        sys.exit(1)

    compressor = ConversationCompressor(
        args.max_tokens,
        args.preserve_code,
        args.preserve_decisions
    )

    if not compressor.load_conversation(args.input):
        sys.exit(1)

    context = compressor.compress(args.strategy)

    if args.strategy in ('lossless', 'semantic', 'selective'):
        context, used_level = compressor.compress_three_level(args.strategy)
        original_decisions = compressor._extract_decisions()
        passed, loss_rate = compressor.verify_facts(original_decisions, context)
        if not passed:
            fallback_map = {'selective': 'semantic', 'semantic': 'lossless', 'lossless': 'lossless'}
            fallback = fallback_map.get(used_level, 'lossless')
            if fallback != used_level:
                context, used_level = compressor.compress_three_level(fallback)

    save_compressed_context(args.output, context)
    print_summary(context)

    sys.exit(0)


if __name__ == '__main__':
    main()
