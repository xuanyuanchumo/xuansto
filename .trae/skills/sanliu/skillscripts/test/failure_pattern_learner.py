#!/usr/bin/env python3
"""
Failure Pattern Learner - 失败模式学习器

从历史失败数据中学习模式，建立知识库，并将知识应用到新诊断中。

功能：
1. 历史数据收集
2. 失败模式知识库
3. 知识应用到新诊断
4. 模式演化追踪

使用示例：
    python failure_pattern_learner.py --collect --pytest-output test_output.txt
    python failure_pattern_learner.py --learn --knowledge-dir ./knowledge
    python failure_pattern_learner.py --apply --diagnosis diagnosis.json
"""

import argparse
import hashlib
import json
import logging
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from path_config_manager import PathConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PatternCategory(Enum):
    SYNTACTIC = "syntactic"
    SEMANTIC = "semantic"
    ENVIRONMENTAL = "environmental"
    BEHAVIORAL = "behavioral"
    PERFORMANCE = "performance"
    INTEGRATION = "integration"
    DATA = "data"
    CONFIGURATION = "configuration"


class LearningStatus(Enum):
    NEW = "new"
    LEARNING = "learning"
    LEARNED = "learned"
    DEPRECATED = "deprecated"


@dataclass
class FailureSignature:
    signature_id: str
    error_pattern: str
    exception_type: str
    stack_pattern: str
    file_pattern: str
    function_pattern: str
    created_at: str
    occurrence_count: int = 1


@dataclass
class PatternKnowledge:
    pattern_id: str
    category: PatternCategory
    name: str
    description: str
    signatures: List[FailureSignature] = field(default_factory=list)
    root_cause_template: str = ""
    fix_templates: List[Dict[str, str]] = field(default_factory=list)
    confidence_score: float = 0.0
    occurrence_count: int = 0
    success_rate: float = 0.0
    last_updated: str = ""
    status: LearningStatus = LearningStatus.NEW
    tags: List[str] = field(default_factory=list)
    related_patterns: List[str] = field(default_factory=list)


@dataclass
class LearningRecord:
    record_id: str
    timestamp: str
    source: str
    failure_info: Dict[str, Any]
    matched_patterns: List[str]
    applied_knowledge: Dict[str, Any]
    outcome: Optional[str] = None
    feedback: Optional[str] = None


@dataclass
class KnowledgeApplicationResult:
    application_id: str
    pattern_id: str
    confidence: float
    suggested_root_cause: str
    suggested_fixes: List[Dict[str, str]]
    evidence: List[str]
    warnings: List[str] = field(default_factory=list)


class HistoricalDataCollector:
    """历史数据收集器
    
    负责从多种数据源收集失败数据，支持数据去重、清洗和验证。
    
    功能特性：
    - 多数据源支持：pytest输出、JUnit XML、JSON格式、自定义格式
    - 数据去重：基于签名去重，避免重复记录
    - 数据清洗：标准化错误消息、过滤无效数据
    - 数据验证：验证数据完整性和有效性
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path("./failure_history")
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self._history_file = self.storage_dir / "failure_history.json"
        self._dedup_index_file = self.storage_dir / "dedup_index.json"
        self._history: List[Dict[str, Any]] = self._load_history()
        self._dedup_index: Dict[str, str] = self._load_dedup_index()
        self._collection_stats: Dict[str, Any] = {
            "total_collected": 0,
            "duplicates_skipped": 0,
            "invalid_skipped": 0,
            "sources": defaultdict(int)
        }
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载历史数据文件"""
        if self._history_file.exists():
            try:
                with open(self._history_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载历史数据失败: {e}")
        return []
    
    def _load_dedup_index(self) -> Dict[str, str]:
        """加载去重索引
        
        去重索引用于快速判断记录是否已存在，避免重复收集。
        索引格式：{签名哈希: 记录ID}
        """
        if self._dedup_index_file.exists():
            try:
                with open(self._dedup_index_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载去重索引失败: {e}")
        return {}
    
    def _save_history(self) -> None:
        """保存历史数据到文件"""
        try:
            with open(self._history_file, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存历史数据失败: {e}")
    
    def _save_dedup_index(self) -> None:
        """保存去重索引到文件"""
        try:
            with open(self._dedup_index_file, "w", encoding="utf-8") as f:
                json.dump(self._dedup_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存去重索引失败: {e}")
    
    def _create_signature(self, test_name: str, error_message: str, 
                          exception_type: Optional[str] = None) -> str:
        """创建记录签名用于去重
        
        基于测试名称、错误消息和异常类型生成唯一签名。
        对错误消息进行标准化处理，去除动态部分（如时间戳、随机值）。
        
        Args:
            test_name: 测试名称
            error_message: 错误消息
            exception_type: 异常类型
            
        Returns:
            签名字符串
        """
        normalized_error = self._normalize_error_message(error_message)
        content = f"{test_name}:{exception_type or 'unknown'}:{normalized_error}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _normalize_error_message(self, error_message: str) -> str:
        """标准化错误消息
        
        去除动态部分，保留核心错误信息，便于模式匹配和去重。
        
        Args:
            error_message: 原始错误消息
            
        Returns:
            标准化后的错误消息
        """
        normalized = error_message
        
        normalized = re.sub(r'0x[0-9a-fA-F]+', '0xADDR', normalized)
        normalized = re.sub(r'\b\d{10,}\b', 'TIMESTAMP', normalized)
        normalized = re.sub(r'\b\d+\.\d+\.\d+\.\d+\b', 'IP_ADDR', normalized)
        normalized = re.sub(r'/tmp/[\w/]+', '/tmp/PATH', normalized)
        normalized = re.sub(r'line \d+', 'line NUM', normalized)
        normalized = re.sub(r':\d+:', ':NUM:', normalized)
        
        return normalized.strip()
    
    def _validate_record(self, record: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """验证记录的完整性和有效性
        
        检查记录是否包含必要字段，数据格式是否正确。
        
        Args:
            record: 待验证的记录
            
        Returns:
            (是否有效, 错误信息)
        """
        required_fields = ["test_name", "failure_type", "error_message"]
        
        for field in required_fields:
            if field not in record or not record[field]:
                return False, f"缺少必要字段: {field}"
        
        if record["failure_type"] not in ["error", "failure", "unknown"]:
            return False, f"无效的失败类型: {record['failure_type']}"
        
        if len(record["error_message"]) > 10000:
            return False, "错误消息过长"
        
        return True, None
    
    def _clean_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """清洗记录数据
        
        标准化字段格式，去除无效数据，补充缺失信息。
        
        Args:
            record: 原始记录
            
        Returns:
            清洗后的记录
        """
        cleaned = record.copy()
        
        if "error_message" in cleaned:
            cleaned["error_message"] = cleaned["error_message"].strip()
            cleaned["error_message_normalized"] = self._normalize_error_message(
                cleaned["error_message"]
            )
        
        if "stack_trace" in cleaned and isinstance(cleaned["stack_trace"], list):
            cleaned["stack_trace"] = [
                frame for frame in cleaned["stack_trace"]
                if isinstance(frame, dict) and "file_path" in frame
            ]
        
        if "affected_files" in cleaned and isinstance(cleaned["affected_files"], list):
            cleaned["affected_files"] = list(set(
                f for f in cleaned["affected_files"] 
                if isinstance(f, str) and f.strip()
            ))
        
        if "metadata" not in cleaned:
            cleaned["metadata"] = {}
        
        cleaned["cleaned_at"] = datetime.now().isoformat()
        
        return cleaned
    
    def collect(
        self,
        test_name: str,
        failure_type: str,
        error_message: str,
        exception_type: Optional[str] = None,
        stack_trace: Optional[List[Dict[str, Any]]] = None,
        affected_files: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: str = "unknown",
        skip_duplicate: bool = True
    ) -> Optional[str]:
        """收集单条失败记录
        
        收集失败数据并进行去重、验证和清洗处理。
        
        Args:
            test_name: 测试名称
            failure_type: 失败类型 (error/failure/unknown)
            error_message: 错误消息
            exception_type: 异常类型
            stack_trace: 堆栈跟踪
            affected_files: 受影响的文件列表
            metadata: 元数据
            source: 数据来源标识
            skip_duplicate: 是否跳过重复记录
            
        Returns:
            记录ID，如果跳过重复则返回None
        """
        signature = self._create_signature(test_name, error_message, exception_type)
        
        if skip_duplicate and signature in self._dedup_index:
            self._collection_stats["duplicates_skipped"] += 1
            logger.debug(f"跳过重复记录: {signature[:8]}...")
            return None
        
        record = {
            "record_id": self._generate_record_id(test_name, error_message),
            "timestamp": datetime.now().isoformat(),
            "test_name": test_name,
            "failure_type": failure_type,
            "error_message": error_message,
            "exception_type": exception_type,
            "stack_trace": stack_trace or [],
            "affected_files": affected_files or [],
            "metadata": metadata or {},
            "source": source,
            "signature": signature
        }
        
        is_valid, error_msg = self._validate_record(record)
        if not is_valid:
            self._collection_stats["invalid_skipped"] += 1
            logger.warning(f"跳过无效记录: {error_msg}")
            return None
        
        record = self._clean_record(record)
        
        self._history.append(record)
        self._dedup_index[signature] = record["record_id"]
        self._collection_stats["total_collected"] += 1
        self._collection_stats["sources"][source] += 1
        
        self._save_history()
        self._save_dedup_index()
        
        logger.info(f"收集失败记录: {record['record_id']} (来源: {source})")
        return record["record_id"]
    
    def collect_from_pytest_output(self, pytest_output: str, source: str = "pytest") -> List[str]:
        """从pytest输出中收集失败数据
        
        解析pytest的输出文本，提取失败信息并收集。
        
        Args:
            pytest_output: pytest的输出文本
            source: 数据来源标识
            
        Returns:
            收集的记录ID列表
        """
        record_ids = []
        
        pattern = r"(FAILED|ERROR)\s+([^\s]+)"
        for match in re.finditer(pattern, pytest_output):
            test_name = match.group(2)
            
            block_start = match.start()
            next_match = re.search(pattern, pytest_output[block_start + 1:])
            if next_match:
                block_end = block_start + 1 + next_match.start()
            else:
                block_end = len(pytest_output)
            
            block = pytest_output[block_start:block_end]
            
            error_message = self._extract_error_message(block)
            exception_type = self._extract_exception_type(block)
            stack_trace = self._extract_stack_trace(block)
            affected_files = self._extract_affected_files(stack_trace)
            
            record_id = self.collect(
                test_name=test_name,
                failure_type="error" if "ERROR" in block[:20] else "failure",
                error_message=error_message,
                exception_type=exception_type,
                stack_trace=stack_trace,
                affected_files=affected_files,
                source=source
            )
            if record_id:
                record_ids.append(record_id)
        
        return record_ids
    
    def collect_from_file(self, file_path: str, source: Optional[str] = None) -> List[str]:
        """从文件中收集失败数据
        
        支持多种文件格式：
        - JSON格式：包含失败记录的JSON数组或对象
        - pytest输出：pytest的标准输出文本
        - JUnit XML：JUnit格式的测试报告（待实现）
        
        Args:
            file_path: 文件路径
            source: 数据来源标识，默认使用文件名
            
        Returns:
            收集的记录ID列表
        """
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        source_name = source or Path(file_path).stem
        
        if file_path.endswith(".json"):
            return self._collect_from_json(content, source_name)
        elif file_path.endswith(".xml"):
            return self._collect_from_junit_xml(content, source_name)
        else:
            return self.collect_from_pytest_output(content, source_name)
    
    def _collect_from_json(self, content: str, source: str) -> List[str]:
        """从JSON格式收集失败数据
        
        Args:
            content: JSON内容
            source: 数据来源标识
            
        Returns:
            收集的记录ID列表
        """
        record_ids = []
        
        try:
            data = json.loads(content)
            
            if isinstance(data, list):
                items = data
            elif isinstance(data, dict):
                if "failures" in data:
                    items = data["failures"]
                elif "records" in data:
                    items = data["records"]
                else:
                    items = [data]
            else:
                logger.warning(f"无法识别的JSON格式: {type(data)}")
                return record_ids
            
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                record_id = self.collect(
                    test_name=item.get("test_name", "unknown"),
                    failure_type=item.get("failure_type", "unknown"),
                    error_message=item.get("error_message", ""),
                    exception_type=item.get("exception_type"),
                    stack_trace=item.get("stack_trace"),
                    affected_files=item.get("affected_files"),
                    metadata=item.get("metadata"),
                    source=source
                )
                if record_id:
                    record_ids.append(record_id)
                    
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
        
        return record_ids
    
    def _collect_from_junit_xml(self, content: str, source: str) -> List[str]:
        """从JUnit XML格式收集失败数据
        
        解析JUnit XML格式的测试报告，提取失败信息。
        
        Args:
            content: XML内容
            source: 数据来源标识
            
        Returns:
            收集的记录ID列表
        """
        record_ids = []
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            
            for testcase in root.iter('testcase'):
                failure = testcase.find('failure')
                error = testcase.find('error')
                
                if failure is not None or error is not None:
                    elem = failure if failure is not None else error
                    test_name = testcase.get('name', 'unknown')
                    classname = testcase.get('classname', '')
                    if classname:
                        test_name = f"{classname}::{test_name}"
                    
                    error_message = elem.get('message', elem.text or 'Unknown error')
                    exception_type = elem.get('type', '')
                    
                    record_id = self.collect(
                        test_name=test_name,
                        failure_type="error" if error is not None else "failure",
                        error_message=error_message,
                        exception_type=exception_type,
                        source=source
                    )
                    if record_id:
                        record_ids.append(record_id)
                        
        except ET.ParseError as e:
            logger.error(f"XML解析失败: {e}")
        except ImportError:
            logger.warning("无法导入xml模块，跳过XML解析")
        
        return record_ids
    
    def collect_from_directory(self, dir_path: str, pattern: str = "*.json") -> List[str]:
        """从目录中批量收集失败数据
        
        扫描目录下匹配指定模式的文件，批量收集失败数据。
        
        Args:
            dir_path: 目录路径
            pattern: 文件匹配模式，默认为*.json
            
        Returns:
            收集的记录ID列表
        """
        record_ids = []
        dir_path = Path(dir_path)
        
        if not dir_path.exists() or not dir_path.is_dir():
            logger.warning(f"目录不存在或不是目录: {dir_path}")
            return record_ids
        
        for file_path in dir_path.glob(pattern):
            logger.info(f"处理文件: {file_path}")
            ids = self.collect_from_file(str(file_path))
            record_ids.extend(ids)
        
        logger.info(f"从目录 {dir_path} 收集了 {len(record_ids)} 条记录")
        return record_ids
    
    def _generate_record_id(self, test_name: str, error_message: str) -> str:
        content = f"{test_name}:{error_message}:{datetime.now().isoformat()}"
        return f"REC-{hashlib.md5(content.encode()).hexdigest()[:12]}"
    
    def _extract_error_message(self, block: str) -> str:
        lines = block.strip().split("\n")
        for line in reversed(lines):
            line = line.strip()
            if line and not line.startswith((" ", "\t", "File", "During", "Traceback")):
                if re.search(r"(Error|Exception|assert)", line):
                    return line
        return "Unknown error"
    
    def _extract_exception_type(self, block: str) -> Optional[str]:
        match = re.search(r"(\w+(?:Error|Exception)):", block)
        return match.group(1) if match else None
    
    def _extract_stack_trace(self, block: str) -> List[Dict[str, Any]]:
        frames = []
        pattern = r'File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+(\w+)'
        for match in re.finditer(pattern, block):
            frames.append({
                "file_path": match.group(1),
                "line_number": int(match.group(2)),
                "function_name": match.group(3)
            })
        return frames
    
    def _extract_affected_files(self, stack_trace: List[Dict[str, Any]]) -> List[str]:
        return list(set(
            frame["file_path"] for frame in stack_trace
            if "site-packages" not in frame["file_path"]
        ))
    
    def get_history(
        self,
        limit: int = 100,
        filter_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        history = self._history
        
        if filter_type:
            history = [h for h in history if h.get("failure_type") == filter_type]
        
        return history[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取收集统计信息
        
        返回历史数据的详细统计信息，包括：
        - 总记录数和唯一测试数
        - 失败类型和异常类型分布
        - 时间范围
        - 收集过程统计（去重、无效数据等）
        - 数据来源分布
        
        Returns:
            统计信息字典
        """
        if not self._history:
            return {
                "total_records": 0,
                "unique_tests": 0,
                "failure_types": {},
                "exception_types": {},
                "time_range": None,
                "collection_stats": self._collection_stats,
                "source_distribution": {}
            }
        
        failure_types: Dict[str, int] = defaultdict(int)
        exception_types: Dict[str, int] = defaultdict(int)
        unique_tests: Set[str] = set()
        timestamps = []
        source_distribution: Dict[str, int] = defaultdict(int)
        affected_files_stats: Dict[str, int] = defaultdict(int)
        
        for record in self._history:
            failure_types[record.get("failure_type", "unknown")] += 1
            if record.get("exception_type"):
                exception_types[record["exception_type"]] += 1
            unique_tests.add(record.get("test_name", ""))
            timestamps.append(record.get("timestamp", ""))
            
            source = record.get("source", "unknown")
            source_distribution[source] += 1
            
            for file_path in record.get("affected_files", []):
                file_name = Path(file_path).name
                affected_files_stats[file_name] += 1
        
        time_range = None
        if timestamps:
            timestamps.sort()
            time_range = {
                "start": timestamps[0],
                "end": timestamps[-1]
            }
        
        top_affected_files = sorted(
            affected_files_stats.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10]
        
        return {
            "total_records": len(self._history),
            "unique_tests": len(unique_tests),
            "failure_types": dict(failure_types),
            "exception_types": dict(exception_types),
            "time_range": time_range,
            "collection_stats": {
                "total_collected": self._collection_stats["total_collected"],
                "duplicates_skipped": self._collection_stats["duplicates_skipped"],
                "invalid_skipped": self._collection_stats["invalid_skipped"],
                "sources": dict(self._collection_stats["sources"])
            },
            "source_distribution": dict(source_distribution),
            "top_affected_files": top_affected_files
        }
    
    def clear_history(self) -> None:
        """清空历史数据
        
        删除所有历史记录和去重索引。
        """
        self._history = []
        self._dedup_index = {}
        self._collection_stats = {
            "total_collected": 0,
            "duplicates_skipped": 0,
            "invalid_skipped": 0,
            "sources": defaultdict(int)
        }
        self._save_history()
        self._save_dedup_index()
        logger.info("历史数据已清空")
    
    def export_history(self, output_path: str, format: str = "json") -> None:
        """导出历史数据到文件
        
        支持多种导出格式：JSON、CSV
        
        Args:
            output_path: 输出文件路径
            format: 导出格式 (json/csv)
        """
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(self._history, f, ensure_ascii=False, indent=2)
        elif format == "csv":
            import csv
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                if not self._history:
                    return
                writer = csv.DictWriter(f, fieldnames=[
                    "record_id", "timestamp", "test_name", "failure_type",
                    "error_message", "exception_type", "source"
                ])
                writer.writeheader()
                for record in self._history:
                    writer.writerow({
                        k: record.get(k, "") for k in [
                            "record_id", "timestamp", "test_name", "failure_type",
                            "error_message", "exception_type", "source"
                        ]
                    })
        else:
            raise ValueError(f"不支持的导出格式: {format}")
        
        logger.info(f"历史数据已导出到: {output_path}")


class PatternKnowledgeBase:
    """失败模式知识库
    
    管理失败模式的知识库，提供模式存储、检索、相似度计算和聚类功能。
    
    功能特性：
    - 模式存储和检索：持久化存储模式，支持快速检索
    - 模式相似度计算：基于多种特征计算模式间的相似度
    - 模式聚类：自动聚类相似模式，发现隐藏关联
    - 模式演化追踪：追踪模式随时间的变化趋势
    """
    
    DEFAULT_PATTERNS = {
        "null_pointer": {
            "category": PatternCategory.SEMANTIC,
            "name": "空指针引用",
            "description": "尝试访问None对象的属性或方法",
            "root_cause_template": "空值引用错误: {variable} 为 None",
            "fix_templates": [
                {
                    "title": "添加空值检查",
                    "template": "if {variable} is not None:\n    {original_code}\nelse:\n    # 处理空值情况"
                }
            ],
            "tags": ["null", "none", "attribute"]
        },
        "type_mismatch": {
            "category": PatternCategory.SEMANTIC,
            "name": "类型不匹配",
            "description": "操作数类型不兼容",
            "root_cause_template": "类型不匹配: 期望 {expected_type}, 实际 {actual_type}",
            "fix_templates": [
                {
                    "title": "类型转换",
                    "template": "{variable} = {target_type}({variable})"
                }
            ],
            "tags": ["type", "conversion"]
        },
        "index_out_of_bounds": {
            "category": PatternCategory.SEMANTIC,
            "name": "索引越界",
            "description": "访问超出序列范围的索引",
            "root_cause_template": "索引越界: 索引 {index} 超出范围 [0, {length})",
            "fix_templates": [
                {
                    "title": "边界检查",
                    "template": "if 0 <= {index} < len({container}):\n    {original_code}"
                }
            ],
            "tags": ["index", "bounds", "list"]
        },
        "missing_key": {
            "category": PatternCategory.DATA,
            "name": "字典键缺失",
            "description": "访问不存在的字典键",
            "root_cause_template": "字典键缺失: 键 '{key}' 不存在",
            "fix_templates": [
                {
                    "title": "使用get方法",
                    "template": "value = {dict_name}.get('{key}', {default_value})"
                }
            ],
            "tags": ["key", "dict", "dictionary"]
        },
        "import_error": {
            "category": PatternCategory.ENVIRONMENTAL,
            "name": "模块导入失败",
            "description": "无法导入所需的模块",
            "root_cause_template": "模块导入失败: {module_name}",
            "fix_templates": [
                {
                    "title": "安装模块",
                    "template": "pip install {module_name}"
                }
            ],
            "tags": ["import", "module", "dependency"]
        },
        "assertion_failure": {
            "category": PatternCategory.BEHAVIORAL,
            "name": "断言失败",
            "description": "测试断言条件不满足",
            "root_cause_template": "断言失败: {assertion}",
            "fix_templates": [
                {
                    "title": "检查预期值",
                    "template": "# 调试输出\nprint(f'实际值: {actual}')\nprint(f'预期值: {expected}')"
                }
            ],
            "tags": ["assert", "test", "expectation"]
        },
        "timeout": {
            "category": PatternCategory.PERFORMANCE,
            "name": "操作超时",
            "description": "操作执行时间超过限制",
            "root_cause_template": "操作超时: {operation} 超过 {timeout}秒",
            "fix_templates": [
                {
                    "title": "增加超时时间",
                    "template": "# 增加超时设置\ntimeout = {new_timeout}"
                }
            ],
            "tags": ["timeout", "performance", "slow"]
        },
        "file_not_found": {
            "category": PatternCategory.ENVIRONMENTAL,
            "name": "文件未找到",
            "description": "尝试访问不存在的文件",
            "root_cause_template": "文件未找到: {file_path}",
            "fix_templates": [
                {
                    "title": "检查文件路径",
                    "template": "from pathlib import Path\nfile_path = Path('{file_path}')\nif file_path.exists():\n    {original_code}"
                }
            ],
            "tags": ["file", "path", "notfound"]
        }
    }
    
    def __init__(self, knowledge_dir: Optional[Path] = None):
        self.knowledge_dir = knowledge_dir or Path("./failure_knowledge")
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        
        self._knowledge_file = self.knowledge_dir / "patterns.json"
        self._patterns: Dict[str, PatternKnowledge] = {}
        
        self._initialize_default_patterns()
        self._load_knowledge()
    
    def _initialize_default_patterns(self) -> None:
        for pattern_id, config in self.DEFAULT_PATTERNS.items():
            self._patterns[pattern_id] = PatternKnowledge(
                pattern_id=pattern_id,
                category=config["category"],
                name=config["name"],
                description=config["description"],
                root_cause_template=config["root_cause_template"],
                fix_templates=config["fix_templates"],
                tags=config.get("tags", []),
                status=LearningStatus.LEARNED,
                confidence_score=0.8,
                last_updated=datetime.now().isoformat()
            )
    
    def _load_knowledge(self) -> None:
        if self._knowledge_file.exists():
            try:
                with open(self._knowledge_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for pattern_id, pattern_data in data.items():
                    if pattern_id not in self.DEFAULT_PATTERNS:
                        self._patterns[pattern_id] = PatternKnowledge(
                            pattern_id=pattern_id,
                            category=PatternCategory(pattern_data.get("category", "behavioral")),
                            name=pattern_data.get("name", ""),
                            description=pattern_data.get("description", ""),
                            root_cause_template=pattern_data.get("root_cause_template", ""),
                            fix_templates=pattern_data.get("fix_templates", []),
                            confidence_score=pattern_data.get("confidence_score", 0.5),
                            occurrence_count=pattern_data.get("occurrence_count", 0),
                            success_rate=pattern_data.get("success_rate", 0.0),
                            last_updated=pattern_data.get("last_updated", ""),
                            status=LearningStatus(pattern_data.get("status", "new")),
                            tags=pattern_data.get("tags", []),
                            related_patterns=pattern_data.get("related_patterns", [])
                        )
                
                logger.info(f"加载知识库: {len(self._patterns)} 个模式")
            except Exception as e:
                logger.warning(f"加载知识库失败: {e}")
    
    def _save_knowledge(self) -> None:
        try:
            data = {}
            for pattern_id, pattern in self._patterns.items():
                data[pattern_id] = {
                    "category": pattern.category.value,
                    "name": pattern.name,
                    "description": pattern.description,
                    "root_cause_template": pattern.root_cause_template,
                    "fix_templates": pattern.fix_templates,
                    "confidence_score": pattern.confidence_score,
                    "occurrence_count": pattern.occurrence_count,
                    "success_rate": pattern.success_rate,
                    "last_updated": pattern.last_updated,
                    "status": pattern.status.value,
                    "tags": pattern.tags,
                    "related_patterns": pattern.related_patterns
                }
            
            with open(self._knowledge_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存知识库失败: {e}")
    
    def add_pattern(self, pattern: PatternKnowledge) -> None:
        self._patterns[pattern.pattern_id] = pattern
        self._save_knowledge()
        logger.info(f"添加模式: {pattern.pattern_id}")
    
    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> None:
        if pattern_id in self._patterns:
            pattern = self._patterns[pattern_id]
            
            for key, value in updates.items():
                if hasattr(pattern, key):
                    setattr(pattern, key, value)
            
            pattern.last_updated = datetime.now().isoformat()
            self._save_knowledge()
    
    def get_pattern(self, pattern_id: str) -> Optional[PatternKnowledge]:
        return self._patterns.get(pattern_id)
    
    def get_all_patterns(self) -> List[PatternKnowledge]:
        return list(self._patterns.values())
    
    def find_matching_patterns(
        self,
        error_message: str,
        exception_type: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[Tuple[PatternKnowledge, float]]:
        matches = []
        
        error_lower = error_message.lower()
        
        for pattern in self._patterns.values():
            score = 0.0
            
            for tag in pattern.tags:
                if tag in error_lower:
                    score += 0.2
            
            if exception_type and exception_type.lower() in pattern.name.lower():
                score += 0.3
            
            if tags:
                common_tags = set(tags) & set(pattern.tags)
                score += 0.1 * len(common_tags)
            
            for sig in pattern.signatures:
                if re.search(sig.error_pattern, error_message, re.IGNORECASE):
                    score += 0.3
                    break
            
            if score > 0:
                matches.append((pattern, min(score, 1.0)))
        
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def record_pattern_occurrence(self, pattern_id: str, success: bool) -> None:
        if pattern_id in self._patterns:
            pattern = self._patterns[pattern_id]
            pattern.occurrence_count += 1
            
            if success:
                current_successes = pattern.success_rate * (pattern.occurrence_count - 1)
                pattern.success_rate = (current_successes + 1) / pattern.occurrence_count
            else:
                current_successes = pattern.success_rate * (pattern.occurrence_count - 1)
                pattern.success_rate = current_successes / pattern.occurrence_count
            
            if pattern.occurrence_count >= 5 and pattern.success_rate >= 0.7:
                pattern.status = LearningStatus.LEARNED
            elif pattern.occurrence_count >= 2:
                pattern.status = LearningStatus.LEARNING
            
            self._save_knowledge()
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取知识库统计信息
        
        返回知识库的详细统计信息，包括：
        - 模式总数和各状态模式数
        - 类别分布
        - 平均置信度
        - 高频模式
        
        Returns:
            统计信息字典
        """
        total_patterns = len(self._patterns)
        learned_patterns = len([p for p in self._patterns.values() if p.status == LearningStatus.LEARNED])
        
        category_counts: Dict[str, int] = defaultdict(int)
        for pattern in self._patterns.values():
            category_counts[pattern.category.value] += 1
        
        top_patterns = sorted(
            self._patterns.values(),
            key=lambda p: p.occurrence_count,
            reverse=True
        )[:5]
        
        return {
            "total_patterns": total_patterns,
            "learned_patterns": learned_patterns,
            "learning_patterns": len([p for p in self._patterns.values() if p.status == LearningStatus.LEARNING]),
            "new_patterns": len([p for p in self._patterns.values() if p.status == LearningStatus.NEW]),
            "category_distribution": dict(category_counts),
            "average_confidence": sum(p.confidence_score for p in self._patterns.values()) / total_patterns if total_patterns > 0 else 0,
            "top_patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "name": p.name,
                    "occurrence_count": p.occurrence_count,
                    "success_rate": p.success_rate
                }
                for p in top_patterns
            ]
        }
    
    def calculate_similarity(self, pattern1: PatternKnowledge, pattern2: PatternKnowledge) -> float:
        """计算两个模式之间的相似度
        
        基于多种特征计算相似度：
        - 标签重叠度
        - 类别相同性
        - 签名相似性
        - 根因模板相似性
        
        Args:
            pattern1: 第一个模式
            pattern2: 第二个模式
            
        Returns:
            相似度分数 (0.0-1.0)
        """
        score = 0.0
        
        if pattern1.category == pattern2.category:
            score += 0.2
        
        tags1 = set(pattern1.tags)
        tags2 = set(pattern2.tags)
        if tags1 or tags2:
            jaccard = len(tags1 & tags2) / len(tags1 | tags2) if (tags1 | tags2) else 0
            score += 0.3 * jaccard
        
        if pattern1.signatures and pattern2.signatures:
            sig_sim = self._calculate_signature_similarity(
                pattern1.signatures, pattern2.signatures
            )
            score += 0.3 * sig_sim
        
        if pattern1.root_cause_template and pattern2.root_cause_template:
            text_sim = self._calculate_text_similarity(
                pattern1.root_cause_template, pattern2.root_cause_template
            )
            score += 0.2 * text_sim
        
        return min(score, 1.0)
    
    def _calculate_signature_similarity(
        self, 
        signatures1: List[FailureSignature], 
        signatures2: List[FailureSignature]
    ) -> float:
        """计算签名集合的相似度
        
        Args:
            signatures1: 第一个签名集合
            signatures2: 第二个签名集合
            
        Returns:
            签名相似度
        """
        if not signatures1 or not signatures2:
            return 0.0
        
        patterns1 = set(s.error_pattern for s in signatures1)
        patterns2 = set(s.error_pattern for s in signatures2)
        
        common = patterns1 & patterns2
        total = patterns1 | patterns2
        
        return len(common) / len(total) if total else 0.0
    
    def _calculate_text_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度（基于词重叠）
        
        Args:
            text1: 第一个文本
            text2: 第二个文本
            
        Returns:
            文本相似度
        """
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        common = words1 & words2
        total = words1 | words2
        
        return len(common) / len(total) if total else 0.0
    
    def find_similar_patterns(self, pattern_id: str, threshold: float = 0.5) -> List[Tuple[PatternKnowledge, float]]:
        """查找与指定模式相似的其他模式
        
        Args:
            pattern_id: 目标模式ID
            threshold: 相似度阈值
            
        Returns:
            相似模式列表，包含模式和相似度分数
        """
        if pattern_id not in self._patterns:
            return []
        
        target = self._patterns[pattern_id]
        similar = []
        
        for pid, pattern in self._patterns.items():
            if pid == pattern_id:
                continue
            
            similarity = self.calculate_similarity(target, pattern)
            if similarity >= threshold:
                similar.append((pattern, similarity))
        
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar
    
    def cluster_patterns(self, threshold: float = 0.6) -> Dict[str, List[str]]:
        """聚类相似模式
        
        基于相似度对模式进行聚类，发现相关联的模式组。
        
        Args:
            threshold: 聚类阈值
            
        Returns:
            聚类结果，{聚类ID: [模式ID列表]}
        """
        patterns = list(self._patterns.values())
        n = len(patterns)
        
        if n == 0:
            return {}
        
        parent = list(range(n))
        
        def find(x: int) -> int:
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x: int, y: int) -> None:
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        for i in range(n):
            for j in range(i + 1, n):
                similarity = self.calculate_similarity(patterns[i], patterns[j])
                if similarity >= threshold:
                    union(i, j)
        
        clusters: Dict[int, List[str]] = defaultdict(list)
        for i in range(n):
            root = find(i)
            clusters[root].append(patterns[i].pattern_id)
        
        result = {}
        for idx, (_, pattern_ids) in enumerate(clusters.items()):
            if len(pattern_ids) > 1:
                result[f"cluster_{idx + 1}"] = pattern_ids
        
        return result
    
    def track_pattern_evolution(self, pattern_id: str) -> Dict[str, Any]:
        """追踪模式的演化历史
        
        分析模式随时间的变化趋势，包括：
        - 出现频率变化
        - 成功率变化
        - 状态变化
        
        Args:
            pattern_id: 模式ID
            
        Returns:
            演化历史数据
        """
        if pattern_id not in self._patterns:
            return {"error": "模式不存在"}
        
        pattern = self._patterns[pattern_id]
        
        evolution = {
            "pattern_id": pattern_id,
            "name": pattern.name,
            "current_status": pattern.status.value,
            "current_confidence": pattern.confidence_score,
            "current_success_rate": pattern.success_rate,
            "occurrence_count": pattern.occurrence_count,
            "created_at": pattern.last_updated,
            "milestones": []
        }
        
        if pattern.occurrence_count >= 5 and pattern.success_rate >= 0.7:
            evolution["milestones"].append({
                "event": "达到学习状态",
                "description": f"出现{pattern.occurrence_count}次，成功率{pattern.success_rate:.0%}"
            })
        
        similar = self.find_similar_patterns(pattern_id, threshold=0.5)
        if similar:
            evolution["related_patterns"] = [
                {"pattern_id": p.pattern_id, "name": p.name, "similarity": s}
                for p, s in similar[:3]
            ]
        
        return evolution
    
    def merge_patterns(self, pattern_ids: List[str], merged_name: Optional[str] = None) -> Optional[PatternKnowledge]:
        """合并多个相似模式
        
        将多个相似模式合并为一个新模式，整合它们的签名和统计数据。
        
        Args:
            pattern_ids: 要合并的模式ID列表
            merged_name: 合并后的模式名称
            
        Returns:
            合并后的新模式
        """
        if len(pattern_ids) < 2:
            return None
        
        patterns_to_merge = []
        for pid in pattern_ids:
            if pid in self._patterns:
                patterns_to_merge.append(self._patterns[pid])
        
        if len(patterns_to_merge) < 2:
            return None
        
        all_tags = set()
        all_signatures = []
        total_occurrence = 0
        total_success = 0
        
        for p in patterns_to_merge:
            all_tags.update(p.tags)
            all_signatures.extend(p.signatures)
            total_occurrence += p.occurrence_count
            if p.occurrence_count > 0:
                total_success += p.success_rate * p.occurrence_count
        
        merged_id = f"merged_{hashlib.md5('|'.join(pattern_ids).encode()).hexdigest()[:8]}"
        
        avg_success_rate = total_success / total_occurrence if total_occurrence > 0 else 0
        
        merged_pattern = PatternKnowledge(
            pattern_id=merged_id,
            category=patterns_to_merge[0].category,
            name=merged_name or f"合并模式 ({len(patterns_to_merge)}个)",
            description=f"由 {', '.join(pattern_ids)} 合并而成",
            signatures=all_signatures[:20],
            root_cause_template=patterns_to_merge[0].root_cause_template,
            fix_templates=patterns_to_merge[0].fix_templates,
            confidence_score=sum(p.confidence_score for p in patterns_to_merge) / len(patterns_to_merge),
            occurrence_count=total_occurrence,
            success_rate=avg_success_rate,
            status=LearningStatus.LEARNED if avg_success_rate >= 0.7 else LearningStatus.LEARNING,
            tags=list(all_tags),
            related_patterns=pattern_ids,
            last_updated=datetime.now().isoformat()
        )
        
        for pid in pattern_ids:
            if pid in self._patterns and pid not in self.DEFAULT_PATTERNS:
                del self._patterns[pid]
        
        self._patterns[merged_id] = merged_pattern
        self._save_knowledge()
        
        logger.info(f"合并模式 {pattern_ids} -> {merged_id}")
        return merged_pattern


class KnowledgeApplicator:
    """知识应用器
    
    将知识库中的模式知识应用到新的诊断场景，提供智能化的诊断建议。
    
    功能特性：
    - 模式匹配：基于错误消息、异常类型等多维度匹配模式
    - 上下文感知：考虑代码上下文、环境信息等
    - 修复建议排序：根据置信度和历史成功率排序建议
    - 反馈学习：根据用户反馈优化知识库
    """
    
    def __init__(self, knowledge_base: PatternKnowledgeBase):
        self.knowledge_base = knowledge_base
        self._application_counter = 0
        self._application_history: List[LearningRecord] = []
        self._context_cache: Dict[str, Any] = {}
    
    def apply_knowledge(
        self,
        error_message: str,
        exception_type: Optional[str] = None,
        stack_trace: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[KnowledgeApplicationResult]:
        """应用知识到诊断场景
        
        基于错误信息匹配知识库中的模式，生成诊断建议和修复方案。
        
        Args:
            error_message: 错误消息
            exception_type: 异常类型
            stack_trace: 堆栈跟踪
            context: 上下文信息（代码片段、环境变量等）
            
        Returns:
            知识应用结果列表，按置信度排序
        """
        results = []
        
        enhanced_context = self._build_enhanced_context(
            error_message, exception_type, stack_trace, context
        )
        
        tags = self._extract_tags(error_message, stack_trace)
        
        matches = self.knowledge_base.find_matching_patterns(
            error_message, exception_type, tags
        )
        
        matches = self._enhance_matching_with_context(matches, enhanced_context)
        
        for pattern, confidence in matches[:5]:
            self._application_counter += 1
            
            root_cause = self._generate_root_cause(pattern, error_message, enhanced_context)
            fixes = self._generate_fixes(pattern, error_message, enhanced_context)
            fixes = self._rank_fixes(fixes, pattern, enhanced_context)
            evidence = self._generate_evidence(pattern, error_message)
            warnings = self._generate_warnings(pattern, confidence)
            
            result = KnowledgeApplicationResult(
                application_id=f"APP-{self._application_counter:03d}",
                pattern_id=pattern.pattern_id,
                confidence=confidence * pattern.confidence_score,
                suggested_root_cause=root_cause,
                suggested_fixes=fixes,
                evidence=evidence,
                warnings=warnings
            )
            results.append(result)
        
        self._record_application(error_message, exception_type, results)
        
        return results
    
    def _build_enhanced_context(
        self,
        error_message: str,
        exception_type: Optional[str],
        stack_trace: Optional[List[Dict[str, Any]]],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """构建增强的上下文信息
        
        整合错误信息、堆栈跟踪和用户提供的上下文，生成完整的诊断上下文。
        
        Args:
            error_message: 错误消息
            exception_type: 异常类型
            stack_trace: 堆栈跟踪
            context: 用户提供的上下文
            
        Returns:
            增强的上下文字典
        """
        enhanced = {
            "error_message": error_message,
            "exception_type": exception_type,
            "stack_trace": stack_trace or [],
            "timestamp": datetime.now().isoformat()
        }
        
        if context:
            enhanced.update(context)
        
        if stack_trace:
            enhanced["top_frame"] = stack_trace[0] if stack_trace else None
            enhanced["affected_files"] = [
                frame.get("file_path") for frame in stack_trace
                if frame.get("file_path") and "site-packages" not in frame.get("file_path", "")
            ]
            
            function_names = [
                frame.get("function_name") for frame in stack_trace
                if frame.get("function_name")
            ]
            enhanced["function_context"] = function_names[:3] if function_names else []
        
        variables = self._extract_variables_from_error(error_message)
        if variables:
            enhanced["extracted_variables"] = variables
        
        return enhanced
    
    def _extract_variables_from_error(self, error_message: str) -> Dict[str, str]:
        """从错误消息中提取变量名和值
        
        解析错误消息，提取可能的变量名和值。
        
        Args:
            error_message: 错误消息
            
        Returns:
            提取的变量字典
        """
        variables = {}
        
        name_patterns = [
            r"name '(\w+)' is not defined",
            r"'(\w+)' (?:has no|is not|cannot)",
            r"(\w+) = ",
            r"variable '(\w+)'",
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, error_message, re.IGNORECASE)
            for match in matches:
                if match and len(match) > 1:
                    variables["variable"] = match
                    break
        
        type_match = re.search(r"expected (\w+), got (\w+)", error_message, re.IGNORECASE)
        if type_match:
            variables["expected_type"] = type_match.group(1)
            variables["actual_type"] = type_match.group(2)
        
        key_match = re.search(r"key ['\"]?(\w+)['\"]?", error_message, re.IGNORECASE)
        if key_match:
            variables["key"] = key_match.group(1)
        
        index_match = re.search(r"index (\d+)", error_message)
        if index_match:
            variables["index"] = index_match.group(1)
        
        return variables
    
    def _enhance_matching_with_context(
        self,
        matches: List[Tuple[PatternKnowledge, float]],
        context: Dict[str, Any]
    ) -> List[Tuple[PatternKnowledge, float]]:
        """使用上下文增强模式匹配
        
        根据上下文信息调整匹配置信度。
        
        Args:
            matches: 原始匹配结果
            context: 上下文信息
            
        Returns:
            增强后的匹配结果
        """
        enhanced_matches = []
        
        for pattern, confidence in matches:
            adjusted_confidence = confidence
            
            affected_files = context.get("affected_files", [])
            for file_path in affected_files:
                for sig in pattern.signatures:
                    if sig.file_pattern and sig.file_pattern in file_path:
                        adjusted_confidence += 0.1
                        break
            
            function_context = context.get("function_context", [])
            for func_name in function_context:
                for sig in pattern.signatures:
                    if sig.function_pattern and sig.function_pattern in func_name:
                        adjusted_confidence += 0.05
                        break
            
            if pattern.category == PatternCategory.ENVIRONMENTAL:
                if any(kw in context.get("error_message", "").lower() 
                       for kw in ["import", "module", "environment", "config"]):
                    adjusted_confidence += 0.1
            
            enhanced_matches.append((pattern, min(adjusted_confidence, 1.0)))
        
        enhanced_matches.sort(key=lambda x: x[1], reverse=True)
        return enhanced_matches
    
    def _rank_fixes(
        self,
        fixes: List[Dict[str, str]],
        pattern: PatternKnowledge,
        context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """对修复建议进行排序
        
        根据多种因素对修复建议进行智能排序：
        - 历史成功率
        - 上下文相关性
        - 修复复杂度
        
        Args:
            fixes: 修复建议列表
            pattern: 匹配的模式
            context: 上下文信息
            
        Returns:
            排序后的修复建议列表
        """
        if not fixes:
            return fixes
        
        scored_fixes = []
        for fix in fixes:
            score = 0.0
            
            if pattern.success_rate > 0.7:
                score += 0.3
            elif pattern.success_rate > 0.5:
                score += 0.2
            
            code = fix.get("code", "")
            
            if context.get("extracted_variables"):
                for var in context["extracted_variables"].values():
                    if var in code:
                        score += 0.2
                        break
            
            if "if " in code and "else:" in code:
                score += 0.1
            
            if len(code.split("\n")) <= 3:
                score += 0.1
            
            scored_fixes.append((fix, score))
        
        scored_fixes.sort(key=lambda x: x[1], reverse=True)
        
        return [fix for fix, _ in scored_fixes]
    
    def _extract_tags(
        self,
        error_message: str,
        stack_trace: Optional[List[Dict[str, Any]]]
    ) -> List[str]:
        tags = []
        message_lower = error_message.lower()
        
        tag_keywords = {
            "null": ["none", "null", "nonetype"],
            "type": ["type", "typeerror"],
            "index": ["index", "range", "bounds"],
            "key": ["key", "dict", "dictionary"],
            "import": ["import", "module", "notfound"],
            "file": ["file", "path", "directory"],
            "timeout": ["timeout", "timed out"],
            "assert": ["assert", "assertion"],
            "connection": ["connection", "connect", "network"],
            "permission": ["permission", "access", "denied"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(kw in message_lower for kw in keywords):
                tags.append(tag)
        
        if stack_trace:
            for frame in stack_trace:
                file_path = frame.get("file_path", "")
                if "database" in file_path.lower():
                    tags.append("database")
                if "api" in file_path.lower():
                    tags.append("api")
                if "test" in file_path.lower():
                    tags.append("test")
        
        return tags
    
    def _generate_root_cause(
        self,
        pattern: PatternKnowledge,
        error_message: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        template = pattern.root_cause_template
        
        variables = {
            "variable": "value",
            "expected_type": "ExpectedType",
            "actual_type": "ActualType",
            "index": "index",
            "length": "length",
            "key": "key",
            "module_name": "module",
            "assertion": error_message[:50],
            "operation": "operation",
            "timeout": "timeout",
            "file_path": "path"
        }
        
        if context:
            variables.update(context)
        
        try:
            return template.format(**variables)
        except KeyError:
            return template
    
    def _generate_fixes(
        self,
        pattern: PatternKnowledge,
        error_message: str,
        context: Optional[Dict[str, Any]]
    ) -> List[Dict[str, str]]:
        fixes = []
        
        variables = {
            "variable": "value",
            "original_code": "# original code",
            "target_type": "str",
            "index": "index",
            "container": "items",
            "dict_name": "data",
            "key": "key",
            "default_value": "None",
            "module_name": "module",
            "actual": "actual",
            "expected": "expected",
            "new_timeout": "60",
            "file_path": "path"
        }
        
        if context:
            variables.update(context)
        
        for fix_template in pattern.fix_templates:
            try:
                code = fix_template["template"].format(**variables)
            except KeyError:
                code = fix_template["template"]
            
            fixes.append({
                "title": fix_template["title"],
                "code": code
            })
        
        return fixes
    
    def _generate_evidence(
        self,
        pattern: PatternKnowledge,
        error_message: str
    ) -> List[str]:
        evidence = []
        
        evidence.append(f"匹配模式: {pattern.name}")
        
        for tag in pattern.tags:
            if tag in error_message.lower():
                evidence.append(f"检测到关键词: {tag}")
        
        if pattern.occurrence_count > 0:
            evidence.append(f"历史出现次数: {pattern.occurrence_count}")
        
        if pattern.success_rate > 0:
            evidence.append(f"历史成功率: {pattern.success_rate:.0%}")
        
        return evidence
    
    def _generate_warnings(
        self,
        pattern: PatternKnowledge,
        confidence: float
    ) -> List[str]:
        warnings = []
        
        if confidence < 0.5:
            warnings.append("匹配置信度较低，建议人工验证")
        
        if pattern.status == LearningStatus.NEW:
            warnings.append("这是新模式，建议谨慎应用")
        
        if pattern.occurrence_count < 3:
            warnings.append("该模式历史数据较少")
        
        return warnings
    
    def _record_application(
        self,
        error_message: str,
        exception_type: Optional[str],
        results: List[KnowledgeApplicationResult]
    ) -> None:
        record = LearningRecord(
            record_id=f"LR-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            timestamp=datetime.now().isoformat(),
            source="direct",
            failure_info={
                "error_message": error_message,
                "exception_type": exception_type
            },
            matched_patterns=[r.pattern_id for r in results],
            applied_knowledge={
                "results_count": len(results),
                "top_confidence": results[0].confidence if results else 0
            }
        )
        
        self._application_history.append(record)
    
    def record_feedback(
        self,
        application_id: str,
        outcome: str,
        feedback: Optional[str] = None
    ) -> None:
        for record in self._application_history:
            if application_id in [r.application_id for r in self._application_history]:
                record.outcome = outcome
                record.feedback = feedback
                
                for pattern_id in record.matched_patterns:
                    self.knowledge_base.record_pattern_occurrence(
                        pattern_id,
                        outcome == "success"
                    )
                break
    
    def get_application_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取应用历史记录
        
        Args:
            limit: 返回记录数量限制
            
        Returns:
            应用历史记录列表
        """
        return [
            {
                "record_id": r.record_id,
                "timestamp": r.timestamp,
                "matched_patterns": r.matched_patterns,
                "outcome": r.outcome,
                "feedback": r.feedback
            }
            for r in self._application_history[-limit:]
        ]
    
    def get_application_statistics(self) -> Dict[str, Any]:
        """获取应用统计信息
        
        返回知识应用的详细统计信息，包括：
        - 总应用次数
        - 成功/失败率
        - 最常用模式
        - 反馈统计
        
        Returns:
            统计信息字典
        """
        total = len(self._application_history)
        if total == 0:
            return {
                "total_applications": 0,
                "success_rate": 0,
                "pattern_usage": {},
                "feedback_stats": {}
            }
        
        outcomes = {"success": 0, "failure": 0, "pending": 0}
        pattern_usage: Dict[str, int] = defaultdict(int)
        feedback_count = 0
        
        for record in self._application_history:
            if record.outcome:
                outcomes[record.outcome] = outcomes.get(record.outcome, 0) + 1
                if record.outcome in ["success", "failure"]:
                    feedback_count += 1
            
            for pattern_id in record.matched_patterns:
                pattern_usage[pattern_id] += 1
        
        success_rate = outcomes.get("success", 0) / feedback_count if feedback_count > 0 else 0
        
        top_patterns = sorted(pattern_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_applications": total,
            "success_rate": success_rate,
            "outcomes": outcomes,
            "pattern_usage": dict(pattern_usage),
            "top_used_patterns": [
                {"pattern_id": pid, "count": count}
                for pid, count in top_patterns
            ],
            "feedback_rate": feedback_count / total if total > 0 else 0
        }


class FailurePatternLearner:
    """失败模式学习器主类"""
    
    def __init__(
        self,
        storage_dir: Optional[Path] = None,
        knowledge_dir: Optional[Path] = None
    ):
        self.collector = HistoricalDataCollector(storage_dir)
        self.knowledge_base = PatternKnowledgeBase(knowledge_dir)
        self.applicator = KnowledgeApplicator(self.knowledge_base)
        
        self._learning_session_id = 0
    
    def collect_failures(self, source: str) -> List[str]:
        if Path(source).exists():
            return self.collector.collect_from_file(source)
        return []
    
    def learn_from_history(self) -> Dict[str, Any]:
        self._learning_session_id += 1
        
        history = self.collector.get_history(limit=1000)
        
        if not history:
            return {
                "status": "no_data",
                "message": "没有历史数据可供学习"
            }
        
        pattern_signatures: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        for record in history:
            signature = self._create_signature(record)
            pattern_signatures[signature].append(record)
        
        new_patterns = []
        updated_patterns = []
        
        for signature, records in pattern_signatures.items():
            if len(records) < 2:
                continue
            
            existing_pattern = self._find_existing_pattern(signature)
            
            if existing_pattern:
                self._update_pattern_from_records(existing_pattern, records)
                updated_patterns.append(existing_pattern.pattern_id)
            else:
                new_pattern = self._create_pattern_from_records(signature, records)
                if new_pattern:
                    self.knowledge_base.add_pattern(new_pattern)
                    new_patterns.append(new_pattern.pattern_id)
        
        return {
            "status": "success",
            "session_id": self._learning_session_id,
            "records_analyzed": len(history),
            "pattern_signatures_found": len(pattern_signatures),
            "new_patterns_created": len(new_patterns),
            "patterns_updated": len(updated_patterns),
            "new_pattern_ids": new_patterns,
            "updated_pattern_ids": updated_patterns
        }
    
    def _create_signature(self, record: Dict[str, Any]) -> str:
        error_message = record.get("error_message", "")
        exception_type = record.get("exception_type", "unknown")
        
        sig = re.sub(r'\d+', '#', error_message)
        sig = re.sub(r"'[^']*'", "'*'", sig)
        sig = re.sub(r'"[^"]*"', '"*"', sig)
        sig = re.sub(r'/[\w/]+/', '/*/', sig)
        
        return f"{exception_type}:{sig[:100]}"
    
    def _find_existing_pattern(self, signature: str) -> Optional[PatternKnowledge]:
        for pattern in self.knowledge_base.get_all_patterns():
            for sig in pattern.signatures:
                if sig.error_pattern in signature or signature in sig.error_pattern:
                    return pattern
        return None
    
    def _update_pattern_from_records(
        self,
        pattern: PatternKnowledge,
        records: List[Dict[str, Any]]
    ) -> None:
        pattern.occurrence_count += len(records)
        
        for record in records:
            sig = FailureSignature(
                signature_id=f"SIG-{hashlib.md5(record.get('error_message', '').encode()).hexdigest()[:8]}",
                error_pattern=self._create_signature(record),
                exception_type=record.get("exception_type", "unknown"),
                stack_pattern="",
                file_pattern="",
                function_pattern="",
                created_at=datetime.now().isoformat(),
                occurrence_count=1
            )
            
            existing_sigs = [s.error_pattern for s in pattern.signatures]
            if sig.error_pattern not in existing_sigs:
                pattern.signatures.append(sig)
        
        self.knowledge_base.update_pattern(
            pattern.pattern_id,
            {"occurrence_count": pattern.occurrence_count}
        )
    
    def _create_pattern_from_records(
        self,
        signature: str,
        records: List[Dict[str, Any]]
    ) -> Optional[PatternKnowledge]:
        if len(records) < 2:
            return None
        
        first_record = records[0]
        exception_type = first_record.get("exception_type", "unknown")
        error_message = first_record.get("error_message", "")
        
        pattern_id = f"learned_{hashlib.md5(signature.encode()).hexdigest()[:8]}"
        
        name = self._generate_pattern_name(exception_type, error_message)
        description = f"从 {len(records)} 个历史失败中学习的模式"
        category = self._determine_category(exception_type, error_message)
        root_cause_template = self._generate_root_cause_template(exception_type, error_message)
        fix_templates = self._generate_fix_templates(exception_type, error_message)
        tags = self._extract_tags_from_records(records)
        
        signatures = []
        for record in records[:10]:
            sig = FailureSignature(
                signature_id=f"SIG-{hashlib.md5(record.get('error_message', '').encode()).hexdigest()[:8]}",
                error_pattern=self._create_signature(record),
                exception_type=record.get("exception_type", "unknown"),
                stack_pattern="",
                file_pattern="",
                function_pattern="",
                created_at=datetime.now().isoformat(),
                occurrence_count=1
            )
            signatures.append(sig)
        
        return PatternKnowledge(
            pattern_id=pattern_id,
            category=category,
            name=name,
            description=description,
            signatures=signatures,
            root_cause_template=root_cause_template,
            fix_templates=fix_templates,
            confidence_score=0.5 + 0.1 * min(len(records), 5),
            occurrence_count=len(records),
            status=LearningStatus.LEARNING,
            tags=tags,
            last_updated=datetime.now().isoformat()
        )
    
    def _generate_pattern_name(self, exception_type: str, error_message: str) -> str:
        if exception_type and exception_type != "unknown":
            return f"{exception_type} 模式"
        
        keywords = re.findall(r'\b\w+\b', error_message.lower())
        significant = [w for w in keywords if len(w) > 3 and w not in ["the", "and", "for", "with"]]
        
        if significant:
            return f"{' '.join(significant[:2]).title()} 模式"
        
        return "未知模式"
    
    def _determine_category(self, exception_type: str, error_message: str) -> PatternCategory:
        message_lower = error_message.lower()
        
        if any(kw in message_lower for kw in ["import", "module", "package"]):
            return PatternCategory.ENVIRONMENTAL
        elif any(kw in message_lower for kw in ["file", "path", "directory"]):
            return PatternCategory.ENVIRONMENTAL
        elif any(kw in message_lower for kw in ["timeout", "slow", "performance"]):
            return PatternCategory.PERFORMANCE
        elif any(kw in message_lower for kw in ["connection", "network", "api"]):
            return PatternCategory.INTEGRATION
        elif any(kw in message_lower for kw in ["key", "value", "data"]):
            return PatternCategory.DATA
        elif any(kw in message_lower for kw in ["config", "setting"]):
            return PatternCategory.CONFIGURATION
        else:
            return PatternCategory.SEMANTIC
    
    def _generate_root_cause_template(self, exception_type: str, error_message: str) -> str:
        if exception_type:
            templates = {
                "TypeError": "类型错误: {error_detail}",
                "ValueError": "值错误: {error_detail}",
                "KeyError": "键错误: 键 '{key}' 不存在",
                "IndexError": "索引错误: 索引超出范围",
                "AttributeError": "属性错误: {error_detail}",
                "ImportError": "导入错误: {module_name}",
                "FileNotFoundError": "文件未找到: {file_path}",
            }
            return templates.get(exception_type, f"{exception_type}: {{error_detail}}")
        
        return f"错误: {{error_detail}}"
    
    def _generate_fix_templates(self, exception_type: str, error_message: str) -> List[Dict[str, str]]:
        templates = {
            "TypeError": [{"title": "类型检查", "template": "# 检查类型\nif isinstance({variable}, {expected_type}):\n    {original_code}"}],
            "ValueError": [{"title": "值验证", "template": "# 验证值\nif {condition}:\n    {original_code}"}],
            "KeyError": [{"title": "安全访问", "template": "value = {dict_name}.get('{key}', {default_value})"}],
            "IndexError": [{"title": "边界检查", "template": "if 0 <= {index} < len({container}):\n    {original_code}"}],
            "AttributeError": [{"title": "属性检查", "template": "if hasattr({object}, '{attribute}'):\n    {original_code}"}],
            "ImportError": [{"title": "安装模块", "template": "pip install {module_name}"}],
            "FileNotFoundError": [{"title": "检查路径", "template": "from pathlib import Path\nif Path('{file_path}').exists():\n    {original_code}"}],
        }
        
        return templates.get(exception_type, [{"title": "检查错误", "template": "# 分析并修复错误"}])
    
    def _extract_tags_from_records(self, records: List[Dict[str, Any]]) -> List[str]:
        tags = set()
        
        for record in records:
            error_message = record.get("error_message", "").lower()
            
            tag_keywords = {
                "null": ["none", "null"],
                "type": ["type", "typeerror"],
                "index": ["index", "range"],
                "key": ["key", "dict"],
                "import": ["import", "module"],
                "file": ["file", "path"],
            }
            
            for tag, keywords in tag_keywords.items():
                if any(kw in error_message for kw in keywords):
                    tags.add(tag)
        
        return list(tags)
    
    def apply_to_diagnosis(
        self,
        error_message: str,
        exception_type: Optional[str] = None,
        stack_trace: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        results = self.applicator.apply_knowledge(
            error_message, exception_type, stack_trace, context
        )
        
        if not results:
            return {
                "status": "no_match",
                "message": "没有找到匹配的模式知识"
            }
        
        return {
            "status": "success",
            "top_match": {
                "pattern_id": results[0].pattern_id,
                "confidence": results[0].confidence,
                "root_cause": results[0].suggested_root_cause,
                "fixes": results[0].suggested_fixes,
                "evidence": results[0].evidence,
                "warnings": results[0].warnings
            },
            "all_matches": [
                {
                    "pattern_id": r.pattern_id,
                    "confidence": r.confidence,
                    "root_cause": r.suggested_root_cause
                }
                for r in results
            ]
        }
    
    def provide_feedback(
        self,
        application_id: str,
        success: bool,
        feedback: Optional[str] = None
    ) -> None:
        outcome = "success" if success else "failure"
        self.applicator.record_feedback(application_id, outcome, feedback)
    
    def get_statistics(self) -> Dict[str, Any]:
        return {
            "collection_stats": self.collector.get_statistics(),
            "knowledge_stats": self.knowledge_base.get_statistics(),
            "application_stats": {
                "total_applications": len(self.applicator.get_application_history()),
                "recent_applications": self.applicator.get_application_history(10)
            }
        }
    
    def export_knowledge(self, output_path: str) -> None:
        """导出知识库到文件
        
        Args:
            output_path: 输出文件路径
        """
        data = {
            "exported_at": datetime.now().isoformat(),
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "category": p.category.value,
                    "name": p.name,
                    "description": p.description,
                    "root_cause_template": p.root_cause_template,
                    "fix_templates": p.fix_templates,
                    "confidence_score": p.confidence_score,
                    "occurrence_count": p.occurrence_count,
                    "success_rate": p.success_rate,
                    "status": p.status.value,
                    "tags": p.tags
                }
                for p in self.knowledge_base.get_all_patterns()
            ]
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"知识库已导出到: {output_path}")
    
    def learn_fix_patterns(self) -> Dict[str, Any]:
        """学习修复模式
        
        从历史应用记录中学习成功的修复模式，建立修复知识库。
        
        Returns:
            学习结果统计
        """
        fix_patterns: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "success_count": 0,
            "failure_count": 0,
            "fix_templates": [],
            "context_patterns": []
        })
        
        for record in self.applicator.get_application_history(1000):
            if not record.get("outcome"):
                continue
            
            pattern_ids = record.get("matched_patterns", [])
            outcome = record.get("outcome")
            feedback = record.get("feedback", "")
            
            for pattern_id in pattern_ids:
                pattern = self.knowledge_base.get_pattern(pattern_id)
                if not pattern:
                    continue
                
                key = f"{pattern.category.value}:{pattern.name}"
                
                if outcome == "success":
                    fix_patterns[key]["success_count"] += 1
                    if feedback:
                        fix_patterns[key]["fix_templates"].append({
                            "template": feedback,
                            "success": True
                        })
                else:
                    fix_patterns[key]["failure_count"] += 1
        
        learned_patterns = []
        for key, data in fix_patterns.items():
            total = data["success_count"] + data["failure_count"]
            if total >= 2:
                success_rate = data["success_count"] / total
                if success_rate >= 0.6:
                    learned_patterns.append({
                        "pattern_key": key,
                        "success_rate": success_rate,
                        "total_applications": total,
                        "recommended": success_rate >= 0.8
                    })
        
        learned_patterns.sort(key=lambda x: x["success_rate"], reverse=True)
        
        return {
            "status": "success",
            "total_patterns_analyzed": len(fix_patterns),
            "learned_patterns_count": len(learned_patterns),
            "learned_patterns": learned_patterns[:10]
        }
    
    def get_best_practices(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """获取最佳实践推荐
        
        基于历史数据推荐最佳实践。
        
        Args:
            category: 可选的类别过滤
            
        Returns:
            最佳实践列表
        """
        best_practices = []
        
        for pattern in self.knowledge_base.get_all_patterns():
            if category and pattern.category.value != category:
                continue
            
            if pattern.status != LearningStatus.LEARNED:
                continue
            
            if pattern.success_rate >= 0.7 and pattern.occurrence_count >= 3:
                practice = {
                    "pattern_id": pattern.pattern_id,
                    "name": pattern.name,
                    "category": pattern.category.value,
                    "description": pattern.description,
                    "success_rate": pattern.success_rate,
                    "occurrence_count": pattern.occurrence_count,
                    "confidence_score": pattern.confidence_score,
                    "recommended_fixes": pattern.fix_templates[:3] if pattern.fix_templates else [],
                    "tags": pattern.tags,
                    "recommendation_level": "high" if pattern.success_rate >= 0.9 else "medium"
                }
                best_practices.append(practice)
        
        best_practices.sort(key=lambda x: (x["success_rate"], x["occurrence_count"]), reverse=True)
        
        return best_practices[:20]
    
    def recommend_fix_for_error(
        self,
        error_message: str,
        exception_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """为错误推荐修复方案
        
        基于学习到的模式和历史数据，推荐最佳修复方案。
        
        Args:
            error_message: 错误消息
            exception_type: 异常类型
            context: 上下文信息
            
        Returns:
            修复推荐结果
        """
        diagnosis = self.apply_to_diagnosis(error_message, exception_type, context=context)
        
        if diagnosis.get("status") != "success":
            return {
                "status": "no_recommendation",
                "message": "没有找到匹配的修复模式",
                "suggestions": []
            }
        
        top_match = diagnosis.get("top_match", {})
        pattern_id = top_match.get("pattern_id")
        
        pattern = self.knowledge_base.get_pattern(pattern_id)
        if not pattern:
            return {
                "status": "error",
                "message": "无法获取模式详情"
            }
        
        recommendations = []
        
        for fix in top_match.get("fixes", []):
            recommendation = {
                "title": fix.get("title", ""),
                "code": fix.get("code", ""),
                "confidence": top_match.get("confidence", 0) * pattern.success_rate,
                "based_on": f"基于 {pattern.occurrence_count} 次历史应用",
                "success_rate": pattern.success_rate
            }
            recommendations.append(recommendation)
        
        best_practices = self.get_best_practices(pattern.category.value)
        related_practices = [
            {
                "pattern_id": bp["pattern_id"],
                "name": bp["name"],
                "success_rate": bp["success_rate"],
                "recommendation_level": bp["recommendation_level"]
            }
            for bp in best_practices
            if bp["pattern_id"] != pattern_id
        ][:5]
        
        return {
            "status": "success",
            "pattern_matched": {
                "pattern_id": pattern_id,
                "name": pattern.name,
                "category": pattern.category.value,
                "confidence": top_match.get("confidence", 0)
            },
            "recommendations": recommendations,
            "related_best_practices": related_practices,
            "warnings": top_match.get("warnings", []),
            "evidence": top_match.get("evidence", [])
        }
    
    def auto_improve_patterns(self) -> Dict[str, Any]:
        """自动改进模式
        
        基于反馈数据自动改进现有模式。
        
        Returns:
            改进结果统计
        """
        improvements = []
        
        for pattern in self.knowledge_base.get_all_patterns():
            if pattern.occurrence_count < 5:
                continue
            
            original_confidence = pattern.confidence_score
            original_success_rate = pattern.success_rate
            
            if pattern.success_rate >= 0.8:
                new_confidence = min(1.0, original_confidence + 0.05)
                if new_confidence > original_confidence:
                    self.knowledge_base.update_pattern(
                        pattern.pattern_id,
                        {"confidence_score": new_confidence}
                    )
                    improvements.append({
                        "pattern_id": pattern.pattern_id,
                        "type": "confidence_boost",
                        "from": original_confidence,
                        "to": new_confidence,
                        "reason": "高成功率模式"
                    })
            
            if pattern.success_rate < 0.3 and pattern.occurrence_count >= 10:
                new_status = LearningStatus.DEPRECATED
                self.knowledge_base.update_pattern(
                    pattern.pattern_id,
                    {"status": new_status}
                )
                improvements.append({
                    "pattern_id": pattern.pattern_id,
                    "type": "status_change",
                    "from": pattern.status.value,
                    "to": new_status.value,
                    "reason": "低成功率模式"
                })
        
        similar_clusters = self.knowledge_base.cluster_patterns(threshold=0.7)
        merged = []
        for cluster_id, pattern_ids in similar_clusters.items():
            if len(pattern_ids) >= 2:
                merged_pattern = self.knowledge_base.merge_patterns(pattern_ids)
                if merged_pattern:
                    merged.append({
                        "cluster_id": cluster_id,
                        "merged_patterns": pattern_ids,
                        "new_pattern_id": merged_pattern.pattern_id
                    })
        
        return {
            "status": "success",
            "improvements_count": len(improvements),
            "improvements": improvements,
            "merged_clusters": len(merged),
            "merges": merged
        }
    
    def generate_best_practices_report(self, output_path: str) -> None:
        """生成最佳实践报告
        
        Args:
            output_path: 输出文件路径
        """
        best_practices = self.get_best_practices()
        fix_patterns = self.learn_fix_patterns()
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_best_practices": len(best_practices),
                "high_confidence_count": len([bp for bp in best_practices if bp["recommendation_level"] == "high"]),
                "learned_fix_patterns": fix_patterns.get("learned_patterns_count", 0)
            },
            "best_practices": best_practices,
            "fix_patterns": fix_patterns.get("learned_patterns", []),
            "recommendations": self._generate_practice_recommendations(best_practices)
        }
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"最佳实践报告已生成: {output_path}")
    
    def _generate_practice_recommendations(self, best_practices: List[Dict[str, Any]]) -> List[str]:
        """生成实践建议
        
        Args:
            best_practices: 最佳实践列表
            
        Returns:
            建议列表
        """
        recommendations = []
        
        if not best_practices:
            recommendations.append("建议收集更多失败数据以建立有效的最佳实践库")
            return recommendations
        
        high_confidence = [bp for bp in best_practices if bp["recommendation_level"] == "high"]
        if high_confidence:
            recommendations.append(f"已有 {len(high_confidence)} 个高置信度最佳实践，建议优先应用")
        
        categories = defaultdict(int)
        for bp in best_practices:
            categories[bp["category"]] += 1
        
        for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            recommendations.append(f"类别 '{category}' 有 {count} 个最佳实践")
        
        low_success = [bp for bp in best_practices if bp["success_rate"] < 0.8]
        if low_success:
            recommendations.append(f"有 {len(low_success)} 个最佳实践成功率低于80%，建议持续监控")
        
        return recommendations
    
    def generate_report(
        self,
        output_path: str,
        format: str = "json",
        include_sections: Optional[List[str]] = None
    ) -> None:
        """生成学习系统报告
        
        生成详细的学习系统报告，包含多个可选章节：
        - 概览：整体统计信息
        - 收集分析：数据收集情况分析
        - 知识库分析：知识库状态分析
        - 应用分析：知识应用效果分析
        - 模式详情：各模式详细信息
        - 建议：改进建议
        
        Args:
            output_path: 输出文件路径
            format: 报告格式 (json/markdown/html)
            include_sections: 包含的章节列表，默认全部
        """
        all_sections = [
            "overview",
            "collection_analysis",
            "knowledge_analysis",
            "application_analysis",
            "pattern_details",
            "recommendations"
        ]
        sections = include_sections or all_sections
        
        report_data = {
            "report_title": "失败模式学习系统报告",
            "generated_at": datetime.now().isoformat(),
            "report_version": "1.0"
        }
        
        if "overview" in sections:
            report_data["overview"] = self._generate_overview_section()
        
        if "collection_analysis" in sections:
            report_data["collection_analysis"] = self._generate_collection_section()
        
        if "knowledge_analysis" in sections:
            report_data["knowledge_analysis"] = self._generate_knowledge_section()
        
        if "application_analysis" in sections:
            report_data["application_analysis"] = self._generate_application_section()
        
        if "pattern_details" in sections:
            report_data["pattern_details"] = self._generate_pattern_details_section()
        
        if "recommendations" in sections:
            report_data["recommendations"] = self._generate_recommendations_section()
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        if format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)
        elif format == "markdown":
            content = self._format_report_as_markdown(report_data)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        elif format == "html":
            content = self._format_report_as_html(report_data)
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
        else:
            raise ValueError(f"不支持的报告格式: {format}")
        
        logger.info(f"报告已生成: {output_path}")
    
    def _generate_overview_section(self) -> Dict[str, Any]:
        """生成概览章节
        
        Returns:
            概览数据
        """
        collection_stats = self.collector.get_statistics()
        knowledge_stats = self.knowledge_base.get_statistics()
        application_stats = self.applicator.get_application_statistics()
        
        return {
            "summary": {
                "total_failures_collected": collection_stats.get("total_records", 0),
                "total_patterns_learned": knowledge_stats.get("total_patterns", 0),
                "total_applications": application_stats.get("total_applications", 0),
                "overall_success_rate": application_stats.get("success_rate", 0)
            },
            "health_indicators": {
                "data_collection_health": "good" if collection_stats.get("total_records", 0) > 10 else "needs_attention",
                "knowledge_base_health": "good" if knowledge_stats.get("learned_patterns", 0) > 3 else "learning",
                "application_health": "good" if application_stats.get("success_rate", 0) > 0.5 else "needs_improvement"
            },
            "key_metrics": {
                "unique_tests": collection_stats.get("unique_tests", 0),
                "learned_patterns": knowledge_stats.get("learned_patterns", 0),
                "average_confidence": knowledge_stats.get("average_confidence", 0),
                "feedback_rate": application_stats.get("feedback_rate", 0)
            }
        }
    
    def _generate_collection_section(self) -> Dict[str, Any]:
        """生成收集分析章节
        
        Returns:
            收集分析数据
        """
        stats = self.collector.get_statistics()
        
        return {
            "statistics": stats,
            "insights": {
                "most_common_failure_type": max(
                    stats.get("failure_types", {}).items(),
                    key=lambda x: x[1],
                    default=("unknown", 0)
                )[0] if stats.get("failure_types") else "N/A",
                "most_common_exception": max(
                    stats.get("exception_types", {}).items(),
                    key=lambda x: x[1],
                    default=("unknown", 0)
                )[0] if stats.get("exception_types") else "N/A",
                "data_quality": {
                    "duplicate_rate": stats.get("collection_stats", {}).get("duplicates_skipped", 0) / 
                        max(stats.get("collection_stats", {}).get("total_collected", 1), 1),
                    "invalid_rate": stats.get("collection_stats", {}).get("invalid_skipped", 0) / 
                        max(stats.get("collection_stats", {}).get("total_collected", 1), 1)
                }
            },
            "time_analysis": {
                "time_range": stats.get("time_range"),
                "collection_trend": "stable"
            },
            "source_distribution": stats.get("source_distribution", {})
        }
    
    def _generate_knowledge_section(self) -> Dict[str, Any]:
        """生成知识库分析章节
        
        Returns:
            知识库分析数据
        """
        stats = self.knowledge_base.get_statistics()
        clusters = self.knowledge_base.cluster_patterns(threshold=0.6)
        
        return {
            "statistics": stats,
            "category_breakdown": stats.get("category_distribution", {}),
            "status_distribution": {
                "learned": stats.get("learned_patterns", 0),
                "learning": stats.get("learning_patterns", 0),
                "new": stats.get("new_patterns", 0)
            },
            "top_patterns": stats.get("top_patterns", []),
            "pattern_clusters": {
                "total_clusters": len(clusters),
                "clusters": clusters
            },
            "quality_metrics": {
                "average_confidence": stats.get("average_confidence", 0),
                "patterns_with_high_confidence": len([
                    p for p in self.knowledge_base.get_all_patterns()
                    if p.confidence_score >= 0.8
                ]),
                "patterns_with_good_success_rate": len([
                    p for p in self.knowledge_base.get_all_patterns()
                    if p.success_rate >= 0.7
                ])
            }
        }
    
    def _generate_application_section(self) -> Dict[str, Any]:
        """生成应用分析章节
        
        Returns:
            应用分析数据
        """
        stats = self.applicator.get_application_statistics()
        
        return {
            "statistics": stats,
            "effectiveness": {
                "success_rate": stats.get("success_rate", 0),
                "feedback_rate": stats.get("feedback_rate", 0),
                "most_used_patterns": stats.get("top_used_patterns", [])
            },
            "outcomes": stats.get("outcomes", {}),
            "recent_applications": self.applicator.get_application_history(10)
        }
    
    def _generate_pattern_details_section(self) -> Dict[str, Any]:
        """生成模式详情章节
        
        Returns:
            模式详情数据
        """
        patterns = self.knowledge_base.get_all_patterns()
        
        return {
            "total_patterns": len(patterns),
            "patterns": [
                {
                    "pattern_id": p.pattern_id,
                    "name": p.name,
                    "category": p.category.value,
                    "description": p.description,
                    "status": p.status.value,
                    "confidence_score": p.confidence_score,
                    "occurrence_count": p.occurrence_count,
                    "success_rate": p.success_rate,
                    "tags": p.tags,
                    "signature_count": len(p.signatures),
                    "fix_template_count": len(p.fix_templates),
                    "evolution": self.knowledge_base.track_pattern_evolution(p.pattern_id)
                }
                for p in sorted(patterns, key=lambda x: x.occurrence_count, reverse=True)
            ]
        }
    
    def _generate_recommendations_section(self) -> Dict[str, Any]:
        """生成建议章节
        
        Returns:
            建议数据
        """
        recommendations = []
        
        collection_stats = self.collector.get_statistics()
        if collection_stats.get("total_records", 0) < 10:
            recommendations.append({
                "priority": "high",
                "category": "data_collection",
                "recommendation": "增加失败数据收集量",
                "reason": "当前收集的失败数据较少，建议收集更多数据以提高学习效果",
                "action": "运行更多测试用例或导入历史失败数据"
            })
        
        knowledge_stats = self.knowledge_base.get_statistics()
        if knowledge_stats.get("learning_patterns", 0) > knowledge_stats.get("learned_patterns", 0):
            recommendations.append({
                "priority": "medium",
                "category": "knowledge_base",
                "recommendation": "加速模式学习进程",
                "reason": "有较多模式处于学习状态，需要更多数据来确认模式有效性",
                "action": "收集更多相关类型的失败数据，或手动验证学习中的模式"
            })
        
        application_stats = self.applicator.get_application_statistics()
        if application_stats.get("success_rate", 0) < 0.5:
            recommendations.append({
                "priority": "high",
                "category": "application",
                "recommendation": "改进知识应用策略",
                "reason": "知识应用成功率较低，可能需要调整匹配策略或修复模板",
                "action": "分析失败案例，优化修复模板，提高匹配精度"
            })
        
        if application_stats.get("feedback_rate", 0) < 0.3:
            recommendations.append({
                "priority": "medium",
                "category": "feedback",
                "recommendation": "增加用户反馈收集",
                "reason": "用户反馈率较低，影响知识库的持续优化",
                "action": "在应用知识后主动请求用户反馈，或集成自动验证机制"
            })
        
        clusters = self.knowledge_base.cluster_patterns(threshold=0.6)
        if len(clusters) > 3:
            recommendations.append({
                "priority": "low",
                "category": "optimization",
                "recommendation": "考虑合并相似模式",
                "reason": f"发现 {len(clusters)} 个模式聚类，合并相似模式可提高知识库效率",
                "action": "审查聚类结果，手动合并高度相似的模式"
            })
        
        return {
            "total_recommendations": len(recommendations),
            "high_priority_count": len([r for r in recommendations if r["priority"] == "high"]),
            "recommendations": recommendations
        }
    
    def _format_report_as_markdown(self, report_data: Dict[str, Any]) -> str:
        """将报告格式化为Markdown
        
        Args:
            report_data: 报告数据
            
        Returns:
            Markdown格式的报告内容
        """
        lines = []
        
        lines.append(f"# {report_data['report_title']}")
        lines.append(f"\n生成时间: {report_data['generated_at']}")
        lines.append(f"报告版本: {report_data['report_version']}")
        
        if "overview" in report_data:
            lines.append("\n## 概览")
            overview = report_data["overview"]
            summary = overview.get("summary", {})
            lines.append("\n### 总体统计")
            lines.append(f"- 收集失败数: {summary.get('total_failures_collected', 0)}")
            lines.append(f"- 学习模式数: {summary.get('total_patterns_learned', 0)}")
            lines.append(f"- 知识应用数: {summary.get('total_applications', 0)}")
            lines.append(f"- 整体成功率: {summary.get('overall_success_rate', 0):.1%}")
            
            health = overview.get("health_indicators", {})
            lines.append("\n### 健康指标")
            lines.append(f"- 数据收集状态: {health.get('data_collection_health', 'unknown')}")
            lines.append(f"- 知识库状态: {health.get('knowledge_base_health', 'unknown')}")
            lines.append(f"- 应用状态: {health.get('application_health', 'unknown')}")
        
        if "collection_analysis" in report_data:
            lines.append("\n## 数据收集分析")
            collection = report_data["collection_analysis"]
            stats = collection.get("statistics", {})
            lines.append(f"\n总记录数: {stats.get('total_records', 0)}")
            lines.append(f"唯一测试数: {stats.get('unique_tests', 0)}")
            
            failure_types = stats.get("failure_types", {})
            if failure_types:
                lines.append("\n### 失败类型分布")
                for ft, count in failure_types.items():
                    lines.append(f"- {ft}: {count}")
        
        if "knowledge_analysis" in report_data:
            lines.append("\n## 知识库分析")
            knowledge = report_data["knowledge_analysis"]
            stats = knowledge.get("statistics", {})
            lines.append(f"\n总模式数: {stats.get('total_patterns', 0)}")
            lines.append(f"已学习模式: {stats.get('learned_patterns', 0)}")
            lines.append(f"学习中模式: {stats.get('learning_patterns', 0)}")
            lines.append(f"平均置信度: {stats.get('average_confidence', 0):.2f}")
        
        if "application_analysis" in report_data:
            lines.append("\n## 知识应用分析")
            application = report_data["application_analysis"]
            stats = application.get("statistics", {})
            lines.append(f"\n总应用次数: {stats.get('total_applications', 0)}")
            lines.append(f"成功率: {stats.get('success_rate', 0):.1%}")
            lines.append(f"反馈率: {stats.get('feedback_rate', 0):.1%}")
        
        if "recommendations" in report_data:
            lines.append("\n## 改进建议")
            recs = report_data["recommendations"]
            for rec in recs.get("recommendations", []):
                lines.append(f"\n### [{rec['priority'].upper()}] {rec['recommendation']}")
                lines.append(f"- 原因: {rec['reason']}")
                lines.append(f"- 行动: {rec['action']}")
        
        return "\n".join(lines)
    
    def _format_report_as_html(self, report_data: Dict[str, Any]) -> str:
        """将报告格式化为HTML
        
        Args:
            report_data: 报告数据
            
        Returns:
            HTML格式的报告内容
        """
        html_parts = []
        
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html lang='zh-CN'>")
        html_parts.append("<head>")
        html_parts.append("<meta charset='UTF-8'>")
        html_parts.append(f"<title>{report_data['report_title']}</title>")
        html_parts.append("<style>")
        html_parts.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        html_parts.append("h1 { color: #333; }")
        html_parts.append("h2 { color: #666; border-bottom: 1px solid #ccc; }")
        html_parts.append("table { border-collapse: collapse; width: 100%; margin: 10px 0; }")
        html_parts.append("th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
        html_parts.append("th { background-color: #f2f2f2; }")
        html_parts.append(".good { color: green; }")
        html_parts.append(".warning { color: orange; }")
        html_parts.append(".error { color: red; }")
        html_parts.append(".priority-high { background-color: #ffebee; }")
        html_parts.append(".priority-medium { background-color: #fff3e0; }")
        html_parts.append(".priority-low { background-color: #e8f5e9; }")
        html_parts.append("</style>")
        html_parts.append("</head>")
        html_parts.append("<body>")
        
        html_parts.append(f"<h1>{report_data['report_title']}</h1>")
        html_parts.append(f"<p>生成时间: {report_data['generated_at']}</p>")
        
        if "overview" in report_data:
            overview = report_data["overview"]
            html_parts.append("<h2>概览</h2>")
            summary = overview.get("summary", {})
            html_parts.append("<table>")
            html_parts.append("<tr><th>指标</th><th>值</th></tr>")
            html_parts.append(f"<tr><td>收集失败数</td><td>{summary.get('total_failures_collected', 0)}</td></tr>")
            html_parts.append(f"<tr><td>学习模式数</td><td>{summary.get('total_patterns_learned', 0)}</td></tr>")
            html_parts.append(f"<tr><td>知识应用数</td><td>{summary.get('total_applications', 0)}</td></tr>")
            html_parts.append(f"<tr><td>整体成功率</td><td>{summary.get('overall_success_rate', 0):.1%}</td></tr>")
            html_parts.append("</table>")
        
        if "recommendations" in report_data:
            html_parts.append("<h2>改进建议</h2>")
            for rec in report_data["recommendations"].get("recommendations", []):
                priority_class = f"priority-{rec['priority']}"
                html_parts.append(f"<div class='{priority_class}' style='padding: 10px; margin: 10px 0; border-radius: 5px;'>")
                html_parts.append(f"<h3>[{rec['priority'].upper()}] {rec['recommendation']}</h3>")
                html_parts.append(f"<p><strong>原因:</strong> {rec['reason']}</p>")
                html_parts.append(f"<p><strong>行动:</strong> {rec['action']}</p>")
                html_parts.append("</div>")
        
        html_parts.append("</body>")
        html_parts.append("</html>")
        
        return "\n".join(html_parts)


def main():
    parser = argparse.ArgumentParser(
        description="失败模式学习器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 收集失败数据
  python failure_pattern_learner.py --collect --pytest-output test_output.txt
  
  # 从历史数据学习
  python failure_pattern_learner.py --learn
  
  # 应用知识到诊断
  python failure_pattern_learner.py --apply --error "TypeError: unsupported operand"
  
  # 导出知识库
  python failure_pattern_learner.py --export knowledge.json
  
  # 生成报告
  python failure_pattern_learner.py --report report.html --format html
  
  # 查看统计信息
  python failure_pattern_learner.py --statistics
        """
    )
    
    parser.add_argument(
        "--collect",
        action="store_true",
        help="收集失败数据"
    )
    
    parser.add_argument(
        "--pytest-output",
        help="pytest输出文件路径"
    )
    
    parser.add_argument(
        "--failures",
        help="失败信息JSON文件路径"
    )
    
    parser.add_argument(
        "--learn",
        action="store_true",
        help="从历史数据学习"
    )
    
    parser.add_argument(
        "--apply",
        action="store_true",
        help="应用知识到诊断"
    )
    
    parser.add_argument(
        "--error",
        help="要诊断的错误消息"
    )
    
    parser.add_argument(
        "--exception-type",
        help="异常类型"
    )
    
    parser.add_argument(
        "--export",
        help="导出知识库到文件"
    )
    
    parser.add_argument(
        "--report",
        help="生成学习系统报告"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "html"],
        default="json",
        help="报告格式 (json/markdown/html)"
    )
    
    parser.add_argument(
        "--statistics",
        action="store_true",
        help="显示统计信息"
    )
    
    parser.add_argument(
        "--storage-dir",
        help="历史数据存储目录"
    )
    
    parser.add_argument(
        "--knowledge-dir",
        help="知识库目录"
    )
    
    parser.add_argument(
        "--collect-dir",
        help="从目录批量收集失败数据"
    )
    
    parser.add_argument(
        "--pattern",
        default="*.json",
        help="批量收集时的文件匹配模式"
    )
    
    args = parser.parse_args()
    
    try:
        path_manager = PathConfigManager(auto_detect=True)
        
        if args.storage_dir:
            storage_dir = Path(args.storage_dir)
        else:
            storage_dir = path_manager.get_data_path() / "failure_history"
        
        if args.knowledge_dir:
            knowledge_dir = Path(args.knowledge_dir)
        else:
            knowledge_dir = path_manager.get_data_path() / "failure_knowledge"
        
        learner = FailurePatternLearner(storage_dir, knowledge_dir)
        
        if args.collect:
            source = args.pytest_output or args.failures
            if not source:
                parser.error("收集模式需要指定 --pytest-output 或 --failures")
            
            record_ids = learner.collect_failures(source)
            print(f"收集了 {len(record_ids)} 条失败记录")
        
        if args.collect_dir:
            record_ids = learner.collector.collect_from_directory(
                args.collect_dir, args.pattern
            )
            print(f"从目录收集了 {len(record_ids)} 条失败记录")
        
        if args.learn:
            result = learner.learn_from_history()
            print(f"学习完成:")
            print(f"  分析记录数: {result.get('records_analyzed', 0)}")
            print(f"  新建模式: {result.get('new_patterns_created', 0)}")
            print(f"  更新模式: {result.get('patterns_updated', 0)}")
        
        if args.apply:
            if not args.error:
                parser.error("应用模式需要指定 --error")
            
            result = learner.apply_to_diagnosis(
                args.error,
                args.exception_type
            )
            
            if result.get("status") == "success":
                top = result.get("top_match", {})
                print(f"最佳匹配: {top.get('pattern_id')}")
                print(f"置信度: {top.get('confidence', 0):.0%}")
                print(f"根因: {top.get('root_cause')}")
                print("\n建议修复:")
                for fix in top.get("fixes", []):
                    print(f"  - {fix['title']}")
            else:
                print(result.get("message", "没有找到匹配"))
        
        if args.export:
            learner.export_knowledge(args.export)
            print(f"知识库已导出到: {args.export}")
        
        if args.report:
            learner.generate_report(args.report, args.format)
            print(f"报告已生成: {args.report}")
        
        if args.statistics:
            stats = learner.get_statistics()
            print("统计信息:")
            print(f"  收集统计:")
            for key, value in stats["collection_stats"].items():
                print(f"    {key}: {value}")
            print(f"  知识库统计:")
            for key, value in stats["knowledge_stats"].items():
                print(f"    {key}: {value}")
        
        if not any([args.collect, args.collect_dir, args.learn, args.apply, args.export, args.report, args.statistics]):
            parser.print_help()
        
    except FileNotFoundError as e:
        logger.error(f"文件未找到: {e}")
        print(f"错误: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"执行错误: {e}")
        print(f"执行错误: {e}")
        import traceback as tb
        tb.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
