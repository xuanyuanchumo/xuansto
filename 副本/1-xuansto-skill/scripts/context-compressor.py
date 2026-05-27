#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
        required=True,
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
        choices=['summary', 'key-points', 'sliding-window', 'hierarchical'],
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


class ContextCompressor:
    """上下文压缩器"""
    
    def __init__(self, max_tokens: int, preserve_code: bool, preserve_decisions: bool):
        """
        初始化压缩器
        
        参数:
            max_tokens: 最大token数
            preserve_code: 是否保留代码
            preserve_decisions: 是否保留决策
        """
        self.max_tokens = max_tokens
        self.preserve_code = preserve_code
        self.preserve_decisions = preserve_decisions
        self.messages: List[Message] = []
    
    def load_conversation(self, input_path: str) -> bool:
        """
        加载对话
        
        参数:
            input_path: 输入文件路径
        
        返回:
            是否成功加载
        """
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
        """
        执行压缩
        
        参数:
            strategy: 压缩策略
        
        返回:
            压缩后的上下文
        """
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
            return self._compress_by_summary()
        elif strategy == 'key-points':
            return self._compress_by_key_points()
        elif strategy == 'sliding-window':
            return self._compress_by_sliding_window()
        else:
            return self._compress_hierarchical()
    
    def _calculate_importance(self):
        """计算每条消息的重要性分数"""
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
        """检查是否包含决策"""
        decision_patterns = [
            r'决定|决策|选择|采用|确定',
            r'decide|decision|choose|select|determine',
            r'我们(将|会|决定)',
            r'let\'s|we will|we decided'
        ]
        return any(re.search(p, content, re.IGNORECASE) for p in decision_patterns)
    
    def _contains_code(self, content: str) -> bool:
        """检查是否包含代码"""
        return bool(re.search(r'```[\s\S]*?```|`[^`]+`', content))
    
    def _contains_question(self, content: str) -> bool:
        """检查是否包含问题"""
        return '?' in content or '？' in content
    
    def _compress_by_summary(self) -> CompressedContext:
        """通过摘要方式压缩"""
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
        """通过关键点方式压缩"""
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
        """通过滑动窗口方式压缩"""
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
        """通过层次化方式压缩"""
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
        """生成摘要"""
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
        """从关键点生成摘要"""
        if not key_points:
            return "无关键信息"
        
        return f"对话包含 {len(key_points)} 个关键点，涉及 {len(self._extract_entities())} 个实体。"
    
    def _summarize_chunk(self, messages: List[Message]) -> str:
        """摘要消息块"""
        if not messages:
            return ""
        
        content = ' '.join([m.content for m in messages])
        sentences = re.split(r'[。！？.!?]', content)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            return sentences[0][:150]
        return content[:150]
    
    def _extract_key_points(self) -> List[str]:
        """提取关键点"""
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
        """提取决策"""
        decisions = []
        
        for msg in self.messages:
            if self._contains_decision(msg.content):
                sentences = re.split(r'[。！？.!?]', msg.content)
                for sentence in sentences:
                    if self._contains_decision(sentence):
                        decisions.append(sentence.strip())
        
        return decisions[:10]
    
    def _extract_code_snippets(self) -> List[str]:
        """提取代码片段"""
        code_snippets = []
        
        for msg in self.messages:
            matches = re.findall(r'```[\s\S]*?```', msg.content)
            code_snippets.extend(matches)
        
        return code_snippets[:5]
    
    def _extract_entities(self) -> Dict[str, List[str]]:
        """提取实体"""
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


def save_compressed_context(output_path: str, context: CompressedContext):
    """
    保存压缩后的上下文
    
    参数:
        output_path: 输出路径
        context: 压缩后的上下文
    """
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
    """打印压缩摘要"""
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
    """主函数"""
    args = parse_args()
    
    compressor = ContextCompressor(
        args.max_tokens,
        args.preserve_code,
        args.preserve_decisions
    )
    
    if not compressor.load_conversation(args.input):
        sys.exit(1)
    
    context = compressor.compress(args.strategy)
    
    save_compressed_context(args.output, context)
    print_summary(context)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
