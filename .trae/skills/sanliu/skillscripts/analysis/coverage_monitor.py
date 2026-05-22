#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
覆盖率监控器

实现覆盖率计算、覆盖率变化追踪和覆盖率下降预警。
支持多种覆盖率报告格式（coverage.xml, coverage.json, lcov）。

使用示例:
    python coverage_monitor.py
    python coverage_monitor.py --threshold 80 --warn-threshold 5
    python coverage_monitor.py --history-days 30 --output json
"""

import json
import logging
import sys
import argparse
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from xml.etree import ElementTree
import statistics


class CoverageFormat(Enum):
    """覆盖率报告格式"""
    COVERAGE_XML = "coverage_xml"
    COVERAGE_JSON = "coverage_json"
    LCOV = "lcov"
    JACOCO_XML = "jacoco_xml"
    CLOVER_XML = "clover_xml"


class CoverageChangeType(Enum):
    """覆盖率变化类型"""
    INCREASED = "increased"
    DECREASED = "decreased"
    UNCHANGED = "unchanged"
    NEW_FILE = "new_file"
    REMOVED_FILE = "removed_file"


class AlertLevel(Enum):
    """预警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class FileCoverageData:
    """文件覆盖率数据"""
    file_path: str
    line_rate: float
    branch_rate: float
    function_rate: float
    covered_lines: int
    total_lines: int
    covered_branches: int
    total_branches: int
    covered_functions: int = 0
    total_functions: int = 0
    missing_lines: List[int] = field(default_factory=list)
    missing_branches: List[Tuple[int, int]] = field(default_factory=list)
    missing_functions: List[str] = field(default_factory=list)
    timestamp: str = ""
    complexity: float = 0.0
    risk_score: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "line_rate": round(self.line_rate, 2),
            "branch_rate": round(self.branch_rate, 2),
            "function_rate": round(self.function_rate, 2),
            "covered_lines": self.covered_lines,
            "total_lines": self.total_lines,
            "covered_branches": self.covered_branches,
            "total_branches": self.total_branches,
            "covered_functions": self.covered_functions,
            "total_functions": self.total_functions,
            "missing_lines": self.missing_lines[:20],
            "missing_branches": self.missing_branches[:10],
            "missing_functions": self.missing_functions[:10],
            "timestamp": self.timestamp,
            "complexity": round(self.complexity, 2),
            "risk_score": round(self.risk_score, 4)
        }


@dataclass
class CoverageChange:
    """覆盖率变化记录"""
    file_path: str
    change_type: CoverageChangeType
    old_line_rate: float
    new_line_rate: float
    delta: float
    timestamp: str
    details: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "change_type": self.change_type.value,
            "old_line_rate": round(self.old_line_rate, 2),
            "new_line_rate": round(self.new_line_rate, 2),
            "delta": round(self.delta, 2),
            "timestamp": self.timestamp,
            "details": self.details
        }


@dataclass
class CoverageAlert:
    """覆盖率预警"""
    alert_level: AlertLevel
    file_path: str
    current_coverage: float
    threshold: float
    delta: float
    message: str
    timestamp: str
    suggestions: List[str] = field(default_factory=list)
    coverage_type: str = "line"
    trend: str = "stable"
    priority_score: float = 0.0
    affected_tests: List[str] = field(default_factory=list)
    historical_pattern: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alert_level": self.alert_level.value,
            "file_path": self.file_path,
            "current_coverage": round(self.current_coverage, 2),
            "threshold": self.threshold,
            "delta": round(self.delta, 2),
            "message": self.message,
            "timestamp": self.timestamp,
            "suggestions": self.suggestions,
            "coverage_type": self.coverage_type,
            "trend": self.trend,
            "priority_score": round(self.priority_score, 4),
            "affected_tests": self.affected_tests,
            "historical_pattern": self.historical_pattern
        }


@dataclass
class CoverageHistory:
    """覆盖率历史记录"""
    timestamp: str
    total_line_rate: float
    total_branch_rate: float
    file_count: int
    covered_files: int
    files: List[FileCoverageData] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_line_rate": round(self.total_line_rate, 2),
            "total_branch_rate": round(self.total_branch_rate, 2),
            "file_count": self.file_count,
            "covered_files": self.covered_files,
            "files": [f.to_dict() for f in self.files[:50]]
        }


@dataclass
class CoverageMonitorReport:
    """覆盖率监控报告"""
    timestamp: str
    project: str
    current_coverage: float
    previous_coverage: float
    coverage_delta: float
    threshold: float
    threshold_met: bool
    files: List[FileCoverageData]
    changes: List[CoverageChange]
    alerts: List[CoverageAlert]
    history: List[CoverageHistory]
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "project": self.project,
            "current_coverage": round(self.current_coverage, 2),
            "previous_coverage": round(self.previous_coverage, 2),
            "coverage_delta": round(self.coverage_delta, 2),
            "threshold": self.threshold,
            "threshold_met": self.threshold_met,
            "files": [f.to_dict() for f in self.files],
            "changes": [c.to_dict() for c in self.changes],
            "alerts": [a.to_dict() for a in self.alerts],
            "history": [h.to_dict() for h in self.history],
            "summary": self.summary
        }


class ICoverageParser(ABC):
    """覆盖率解析器接口"""

    @abstractmethod
    def parse(self, file_path: Path) -> Dict[str, FileCoverageData]:
        pass

    @abstractmethod
    def supports_format(self, format_type: CoverageFormat) -> bool:
        pass


class CoverageXmlParser(ICoverageParser):
    """Coverage XML格式解析器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def supports_format(self, format_type: CoverageFormat) -> bool:
        return format_type == CoverageFormat.COVERAGE_XML

    def parse(self, file_path: Path) -> Dict[str, FileCoverageData]:
        if not file_path.exists():
            self.logger.warning(f"XML报告不存在: {file_path}")
            return {}

        coverage_data: Dict[str, FileCoverageData] = {}
        timestamp = datetime.now().isoformat()

        try:
            tree = ElementTree.parse(file_path)
            root = tree.getroot()

            for package in root.findall(".//package"):
                package_name = package.get("name", "")

                for cls in package.findall("classes/class"):
                    file_name = cls.get("filename", "")
                    if not file_name:
                        continue

                    file_path_str = f"{package_name}/{file_name}" if package_name else file_name

                    line_rate = float(cls.get("line-rate", 0)) * 100
                    branch_rate = float(cls.get("branch-rate", 0)) * 100

                    lines = cls.findall("lines/line")
                    covered_lines = sum(1 for l in lines if l.get("hits", "0") != "0")
                    total_lines = len(lines)
                    missing_lines = [int(l.get("number", 0)) for l in lines if l.get("hits", "0") == "0"]

                    branches = [l for l in lines if l.get("branch") == "true"]
                    covered_branches = sum(1 for b in branches if b.get("condition-coverage", "").startswith("100%"))
                    total_branches = len(branches)

                    coverage_data[file_path_str] = FileCoverageData(
                        file_path=file_path_str,
                        line_rate=line_rate,
                        branch_rate=branch_rate,
                        function_rate=line_rate,
                        covered_lines=covered_lines,
                        total_lines=total_lines,
                        covered_branches=covered_branches,
                        total_branches=total_branches,
                        missing_lines=missing_lines,
                        timestamp=timestamp
                    )
        except Exception as e:
            self.logger.error(f"解析Coverage XML失败: {e}")

        return coverage_data


class CoverageJsonParser(ICoverageParser):
    """Coverage JSON格式解析器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def supports_format(self, format_type: CoverageFormat) -> bool:
        return format_type == CoverageFormat.COVERAGE_JSON

    def parse(self, file_path: Path) -> Dict[str, FileCoverageData]:
        if not file_path.exists():
            self.logger.warning(f"JSON报告不存在: {file_path}")
            return {}

        coverage_data: Dict[str, FileCoverageData] = {}
        timestamp = datetime.now().isoformat()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            files_data = data.get("files", {})

            for file_path_str, file_info in files_data.items():
                summary = file_info.get("summary", {})
                executed_lines = file_info.get("executed_lines", [])
                missing_lines = file_info.get("missing_lines", [])

                covered_lines = len(executed_lines)
                total_lines = covered_lines + len(missing_lines)
                line_rate = (covered_lines / total_lines * 100) if total_lines > 0 else 0

                coverage_data[file_path_str] = FileCoverageData(
                    file_path=file_path_str,
                    line_rate=line_rate,
                    branch_rate=summary.get("covered_branches", 0) / max(summary.get("num_branches", 1), 1) * 100,
                    function_rate=line_rate,
                    covered_lines=covered_lines,
                    total_lines=total_lines,
                    covered_branches=summary.get("covered_branches", 0),
                    total_branches=summary.get("num_branches", 0),
                    missing_lines=missing_lines,
                    timestamp=timestamp
                )
        except Exception as e:
            self.logger.error(f"解析Coverage JSON失败: {e}")

        return coverage_data


class LcovParser(ICoverageParser):
    """LCOV格式解析器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def supports_format(self, format_type: CoverageFormat) -> bool:
        return format_type == CoverageFormat.LCOV

    def parse(self, file_path: Path) -> Dict[str, FileCoverageData]:
        if not file_path.exists():
            self.logger.warning(f"LCOV报告不存在: {file_path}")
            return {}

        coverage_data: Dict[str, FileCoverageData] = {}
        timestamp = datetime.now().isoformat()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            current_file = ""
            line_data: Dict[int, int] = {}
            branch_data: Dict[int, List[bool]] = {}

            for line in content.split('\n'):
                if line.startswith('SF:'):
                    current_file = line[3:].strip()
                    line_data = {}
                    branch_data = {}
                elif line.startswith('DA:'):
                    parts = line[3:].split(',')
                    if len(parts) >= 2:
                        line_num = int(parts[0])
                        hits = int(parts[1])
                        line_data[line_num] = hits
                elif line.startswith('BRDA:'):
                    parts = line[5:].split(',')
                    if len(parts) >= 4:
                        line_num = int(parts[0])
                        taken = parts[3].strip() != '0' and parts[3].strip() != '-'
                        if line_num not in branch_data:
                            branch_data[line_num] = []
                        branch_data[line_num].append(taken)
                elif line.startswith('end_of_record'):
                    if current_file:
                        total_lines = len(line_data)
                        covered_lines = sum(1 for h in line_data.values() if h > 0)
                        line_rate = (covered_lines / total_lines * 100) if total_lines > 0 else 0

                        total_branches = sum(len(branches) for branches in branch_data.values())
                        covered_branches = sum(sum(1 for b in branches if b) for branches in branch_data.values())
                        branch_rate = (covered_branches / total_branches * 100) if total_branches > 0 else 0

                        missing_lines = [ln for ln, hits in line_data.items() if hits == 0]

                        coverage_data[current_file] = FileCoverageData(
                            file_path=current_file,
                            line_rate=line_rate,
                            branch_rate=branch_rate,
                            function_rate=line_rate,
                            covered_lines=covered_lines,
                            total_lines=total_lines,
                            covered_branches=covered_branches,
                            total_branches=total_branches,
                            missing_lines=missing_lines,
                            timestamp=timestamp
                        )
                    current_file = ""
                    line_data = {}
                    branch_data = {}
        except Exception as e:
            self.logger.error(f"解析LCOV失败: {e}")

        return coverage_data


class CoverageCalculator:
    """覆盖率计算器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.parsers: List[ICoverageParser] = [
            CoverageXmlParser(logger),
            CoverageJsonParser(logger),
            LcovParser(logger)
        ]

    def calculate(self, coverage_data: Dict[str, FileCoverageData]) -> Tuple[float, float, float]:
        """计算总体覆盖率（行覆盖率、分支覆盖率、函数覆盖率）"""
        if not coverage_data:
            return 0.0, 0.0, 0.0

        total_covered_lines = sum(f.covered_lines for f in coverage_data.values())
        total_lines = sum(f.total_lines for f in coverage_data.values())
        total_covered_branches = sum(f.covered_branches for f in coverage_data.values())
        total_branches = sum(f.total_branches for f in coverage_data.values())
        total_covered_functions = sum(f.covered_functions for f in coverage_data.values())
        total_functions = sum(f.total_functions for f in coverage_data.values())

        line_rate = (total_covered_lines / total_lines * 100) if total_lines > 0 else 0
        branch_rate = (total_covered_branches / total_branches * 100) if total_branches > 0 else 0
        function_rate = (total_covered_functions / total_functions * 100) if total_functions > 0 else 0

        for file_data in coverage_data.values():
            file_data.risk_score = self._calculate_file_risk_score(file_data)

        return line_rate, branch_rate, function_rate

    def _calculate_file_risk_score(self, file_data: FileCoverageData) -> float:
        """计算文件风险评分"""
        line_risk = max(0, (80 - file_data.line_rate) / 80)
        branch_risk = max(0, (70 - file_data.branch_rate) / 70) if file_data.total_branches > 0 else 0
        function_risk = max(0, (85 - file_data.function_rate) / 85) if file_data.total_functions > 0 else 0
        complexity_factor = min(file_data.complexity / 20, 1.0) if file_data.complexity > 0 else 0.5
        return (line_risk * 0.4 + branch_risk * 0.3 + function_risk * 0.2 + complexity_factor * 0.1) * 100

    def parse_report(self, report_path: Path) -> Dict[str, FileCoverageData]:
        """解析覆盖率报告"""
        format_type = self._detect_format(report_path)

        for parser in self.parsers:
            if parser.supports_format(format_type):
                self.logger.info(f"使用 {parser.__class__.__name__} 解析报告")
                return parser.parse(report_path)

        self.logger.warning(f"未找到支持 {report_path} 格式的解析器")
        return {}

    def _detect_format(self, report_path: Path) -> CoverageFormat:
        """检测报告格式"""
        file_name = report_path.name.lower()

        if file_name == "coverage.xml" or file_name.endswith(".xml"):
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    content = f.read(500)
                    if '<coverage' in content:
                        return CoverageFormat.COVERAGE_XML
                    elif '<report' in content and 'jacoco' in content.lower():
                        return CoverageFormat.JACOCO_XML
                    elif '<coverage' in content and 'clover' in content.lower():
                        return CoverageFormat.CLOVER_XML
            except Exception:
                pass
            return CoverageFormat.COVERAGE_XML

        if file_name.endswith('.json'):
            return CoverageFormat.COVERAGE_JSON

        if file_name.endswith('.info') or 'lcov' in file_name:
            return CoverageFormat.LCOV

        return CoverageFormat.COVERAGE_XML


class CoverageChangeTracker:
    """覆盖率变化追踪器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._history: List[CoverageHistory] = []

    def track_changes(
        self,
        current: Dict[str, FileCoverageData],
        previous: Dict[str, FileCoverageData]
    ) -> List[CoverageChange]:
        """追踪覆盖率变化"""
        changes: List[CoverageChange] = []
        timestamp = datetime.now().isoformat()

        current_files = set(current.keys())
        previous_files = set(previous.keys())

        for file_path in current_files - previous_files:
            changes.append(CoverageChange(
                file_path=file_path,
                change_type=CoverageChangeType.NEW_FILE,
                old_line_rate=0.0,
                new_line_rate=current[file_path].line_rate,
                delta=current[file_path].line_rate,
                timestamp=timestamp,
                details="新增文件"
            ))

        for file_path in previous_files - current_files:
            changes.append(CoverageChange(
                file_path=file_path,
                change_type=CoverageChangeType.REMOVED_FILE,
                old_line_rate=previous[file_path].line_rate,
                new_line_rate=0.0,
                delta=-previous[file_path].line_rate,
                timestamp=timestamp,
                details="文件已删除"
            ))

        for file_path in current_files & previous_files:
            current_rate = current[file_path].line_rate
            previous_rate = previous[file_path].line_rate
            delta = current_rate - previous_rate

            if abs(delta) < 0.01:
                change_type = CoverageChangeType.UNCHANGED
            elif delta > 0:
                change_type = CoverageChangeType.INCREASED
            else:
                change_type = CoverageChangeType.DECREASED

            if change_type != CoverageChangeType.UNCHANGED:
                changes.append(CoverageChange(
                    file_path=file_path,
                    change_type=change_type,
                    old_line_rate=previous_rate,
                    new_line_rate=current_rate,
                    delta=delta,
                    timestamp=timestamp,
                    details=f"覆盖率{'上升' if delta > 0 else '下降'} {abs(delta):.2f}%"
                ))

        return changes

    def load_history(self, history_path: Path, days: int = 30) -> List[CoverageHistory]:
        """加载历史记录"""
        if not history_path.exists():
            self.logger.info(f"历史记录文件不存在: {history_path}")
            return []

        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cutoff_date = datetime.now() - timedelta(days=days)
            history: List[CoverageHistory] = []

            for item in data.get("history", []):
                try:
                    item_time = datetime.fromisoformat(item["timestamp"])
                    if item_time >= cutoff_date:
                        files = [
                            FileCoverageData(**f) for f in item.get("files", [])
                        ]
                        history.append(CoverageHistory(
                            timestamp=item["timestamp"],
                            total_line_rate=item["total_line_rate"],
                            total_branch_rate=item["total_branch_rate"],
                            file_count=item["file_count"],
                            covered_files=item["covered_files"],
                            files=files
                        ))
                except Exception as e:
                    self.logger.warning(f"解析历史记录失败: {e}")

            self._history = history
            return history
        except Exception as e:
            self.logger.error(f"加载历史记录失败: {e}")
            return []

    def save_history(
        self,
        history: List[CoverageHistory],
        history_path: Path
    ) -> bool:
        """保存历史记录"""
        try:
            history_path.parent.mkdir(parents=True, exist_ok=True)

            existing_data: Dict[str, Any] = {"history": []}
            if history_path.exists():
                with open(history_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)

            existing_data["history"].extend([h.to_dict() for h in history])
            existing_data["last_updated"] = datetime.now().isoformat()

            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"历史记录已保存到 {history_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存历史记录失败: {e}")
            return False

    def get_trend(self, history: List[CoverageHistory]) -> Dict[str, Any]:
        """获取覆盖率趋势"""
        if len(history) < 2:
            return {
                "trend": "insufficient_data",
                "slope": 0.0,
                "direction": "unknown"
            }

        sorted_history = sorted(history, key=lambda h: h.timestamp)
        values = [h.total_line_rate for h in sorted_history]
        timestamps = [datetime.fromisoformat(h.timestamp) for h in sorted_history]

        x = [(t - timestamps[0]).total_seconds() / 86400 for t in timestamps]
        y = values

        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi ** 2 for xi in x)

        denominator = n * sum_x2 - sum_x ** 2
        if denominator == 0:
            slope = 0
        else:
            slope = (n * sum_xy - sum_x * sum_y) / denominator

        if abs(slope) < 0.01:
            direction = "stable"
        elif slope > 0:
            direction = "improving"
        else:
            direction = "declining"

        return {
            "trend": "calculated",
            "slope": round(slope, 4),
            "direction": direction,
            "start_coverage": values[0],
            "end_coverage": values[-1],
            "data_points": n
        }


class CoverageAlertManager:
    """覆盖率预警管理器"""

    def __init__(
        self,
        threshold: float = 80.0,
        branch_threshold: float = 70.0,
        function_threshold: float = 85.0,
        warn_threshold: float = 5.0,
        logger: Optional[logging.Logger] = None
    ):
        self.threshold = threshold
        self.branch_threshold = branch_threshold
        self.function_threshold = function_threshold
        self.warn_threshold = warn_threshold
        self.logger = logger or logging.getLogger(__name__)
        self._alert_history: List[CoverageAlert] = []

    def check_alerts(
        self,
        coverage_data: Dict[str, FileCoverageData],
        changes: List[CoverageChange],
        history: Optional[List[CoverageHistory]] = None
    ) -> List[CoverageAlert]:
        """检查并生成预警"""
        alerts: List[CoverageAlert] = []
        timestamp = datetime.now().isoformat()

        for file_path, data in coverage_data.items():
            if data.line_rate < self.threshold:
                alert_level = self._determine_alert_level(data.line_rate, self.threshold)
                trend = self._determine_trend(file_path, history)
                historical_pattern = self._analyze_historical_pattern(file_path, history)
                priority_score = self._calculate_priority_score(data, alert_level, trend)

                alerts.append(CoverageAlert(
                    alert_level=alert_level,
                    file_path=file_path,
                    current_coverage=data.line_rate,
                    threshold=self.threshold,
                    delta=self.threshold - data.line_rate,
                    message=f"文件覆盖率 {data.line_rate:.1f}% 低于阈值 {self.threshold}%",
                    timestamp=timestamp,
                    suggestions=self._generate_suggestions(data),
                    coverage_type="line",
                    trend=trend,
                    priority_score=priority_score,
                    historical_pattern=historical_pattern
                ))

            if data.total_branches > 0 and data.branch_rate < self.branch_threshold:
                alert_level = self._determine_alert_level(data.branch_rate, self.branch_threshold)
                alerts.append(CoverageAlert(
                    alert_level=alert_level,
                    file_path=file_path,
                    current_coverage=data.branch_rate,
                    threshold=self.branch_threshold,
                    delta=self.branch_threshold - data.branch_rate,
                    message=f"分支覆盖率 {data.branch_rate:.1f}% 低于阈值 {self.branch_threshold}%",
                    timestamp=timestamp,
                    suggestions=self._generate_branch_suggestions(data),
                    coverage_type="branch",
                    trend=self._determine_trend(file_path, history, "branch"),
                    priority_score=self._calculate_priority_score(data, alert_level, "stable") * 0.8
                ))

            if data.total_functions > 0 and data.function_rate < self.function_threshold:
                alert_level = self._determine_alert_level(data.function_rate, self.function_threshold)
                alerts.append(CoverageAlert(
                    alert_level=alert_level,
                    file_path=file_path,
                    current_coverage=data.function_rate,
                    threshold=self.function_threshold,
                    delta=self.function_threshold - data.function_rate,
                    message=f"函数覆盖率 {data.function_rate:.1f}% 低于阈值 {self.function_threshold}%",
                    timestamp=timestamp,
                    suggestions=self._generate_function_suggestions(data),
                    coverage_type="function",
                    trend=self._determine_trend(file_path, history, "function"),
                    priority_score=self._calculate_priority_score(data, alert_level, "stable") * 0.9
                ))

        for change in changes:
            if change.change_type == CoverageChangeType.DECREASED:
                if abs(change.delta) >= self.warn_threshold:
                    historical_pattern = self._analyze_change_pattern(change)
                    alerts.append(CoverageAlert(
                        alert_level=AlertLevel.WARNING,
                        file_path=change.file_path,
                        current_coverage=change.new_line_rate,
                        threshold=self.threshold,
                        delta=change.delta,
                        message=f"覆盖率下降 {abs(change.delta):.1f}%，超过预警阈值 {self.warn_threshold}%",
                        timestamp=timestamp,
                        suggestions=[
                            "检查最近的代码变更",
                            "确保新增代码有对应测试",
                            "运行测试确认测试用例正确执行"
                        ],
                        coverage_type="line",
                        trend="declining",
                        priority_score=abs(change.delta) * 2,
                        historical_pattern=historical_pattern
                    ))

        critical_files = self._detect_critical_files(coverage_data)
        for file_path, risk_score in critical_files:
            data = coverage_data[file_path]
            alerts.append(CoverageAlert(
                alert_level=AlertLevel.CRITICAL,
                file_path=file_path,
                current_coverage=data.line_rate,
                threshold=self.threshold,
                delta=self.threshold - data.line_rate,
                message=f"高风险文件: 风险评分 {risk_score:.1f}",
                timestamp=timestamp,
                suggestions=[
                    "优先处理此文件的覆盖率问题",
                    "考虑重构以降低复杂度",
                    "添加关键路径测试"
                ],
                coverage_type="combined",
                trend="critical",
                priority_score=risk_score
            ))

        for alert in alerts:
            alert.affected_tests = self._identify_affected_tests(alert.file_path, coverage_data)

        self._alert_history.extend(alerts)

        return sorted(alerts, key=lambda a: (-a.priority_score, a.alert_level.value))

    def _determine_alert_level(self, coverage: float, threshold: float) -> AlertLevel:
        """确定预警级别"""
        gap = threshold - coverage
        if gap >= 30:
            return AlertLevel.CRITICAL
        elif gap >= 20:
            return AlertLevel.ERROR
        elif gap >= 10:
            return AlertLevel.WARNING
        else:
            return AlertLevel.INFO

    def _determine_trend(
        self,
        file_path: str,
        history: Optional[List[CoverageHistory]],
        coverage_type: str = "line"
    ) -> str:
        """确定趋势"""
        if not history or len(history) < 2:
            return "unknown"

        values = []
        for h in history:
            for f in h.files:
                if f.file_path == file_path:
                    if coverage_type == "line":
                        values.append(f.line_rate)
                    elif coverage_type == "branch":
                        values.append(f.branch_rate)
                    elif coverage_type == "function":
                        values.append(f.function_rate)
                    break

        if len(values) < 2:
            return "unknown"

        if values[-1] > values[-2] + 1:
            return "improving"
        elif values[-1] < values[-2] - 1:
            return "declining"
        else:
            return "stable"

    def _analyze_historical_pattern(self, file_path: str, history: Optional[List[CoverageHistory]]) -> str:
        """分析历史模式"""
        if not history or len(history) < 3:
            return "insufficient_data"

        values = []
        for h in history:
            for f in h.files:
                if f.file_path == file_path:
                    values.append(f.line_rate)
                    break

        if len(values) < 3:
            return "insufficient_data"

        increasing = sum(1 for i in range(1, len(values)) if values[i] > values[i-1])
        decreasing = sum(1 for i in range(1, len(values)) if values[i] < values[i-1])

        if increasing > decreasing * 2:
            return "consistently_improving"
        elif decreasing > increasing * 2:
            return "consistently_declining"
        elif values[-1] < values[0]:
            return "overall_declining"
        else:
            return "fluctuating"

    def _analyze_change_pattern(self, change: CoverageChange) -> str:
        """分析变化模式"""
        similar_changes = sum(
            1 for a in self._alert_history
            if a.file_path == change.file_path and a.delta < 0
        )
        if similar_changes >= 3:
            return "recurring_decline"
        elif similar_changes >= 1:
            return "previous_declines"
        return "first_decline"

    def _calculate_priority_score(
        self,
        data: FileCoverageData,
        alert_level: AlertLevel,
        trend: str
    ) -> float:
        """计算优先级评分"""
        level_scores = {
            AlertLevel.CRITICAL: 100,
            AlertLevel.ERROR: 75,
            AlertLevel.WARNING: 50,
            AlertLevel.INFO: 25
        }
        base_score = level_scores.get(alert_level, 25)
        trend_factor = {"declining": 1.3, "stable": 1.0, "improving": 0.7, "unknown": 1.0}.get(trend, 1.0)
        coverage_factor = max(0, (self.threshold - data.line_rate) / self.threshold)
        return base_score * trend_factor * (1 + coverage_factor)

    def _detect_critical_files(self, coverage_data: Dict[str, FileCoverageData]) -> List[Tuple[str, float]]:
        """检测高风险文件"""
        critical = []
        for file_path, data in coverage_data.items():
            if data.risk_score > 50:
                critical.append((file_path, data.risk_score))
        return sorted(critical, key=lambda x: -x[1])[:10]

    def _identify_affected_tests(self, file_path: str, coverage_data: Dict[str, FileCoverageData]) -> List[str]:
        """识别受影响的测试"""
        test_patterns = ["test_", "_test", "tests/", "spec/"]
        affected = []
        for other_path in coverage_data:
            if any(p in other_path.lower() for p in test_patterns):
                base_name = Path(file_path).stem
                if base_name in other_path:
                    affected.append(other_path)
        return affected[:5]

    def _generate_suggestions(self, data: FileCoverageData) -> List[str]:
        """生成改进建议"""
        suggestions = []

        if data.line_rate < 50:
            suggestions.append("覆盖率严重不足，建议优先编写基础测试")
        elif data.line_rate < self.threshold:
            suggestions.append(f"需要增加测试用例以达到 {self.threshold}% 覆盖率")

        if data.total_lines > 200:
            suggestions.append("文件较大，考虑拆分以提高可测试性")

        if data.missing_lines:
            suggestions.append(f"有 {len(data.missing_lines)} 行代码未被覆盖")

        if data.risk_score > 50:
            suggestions.append("高风险文件，建议优先处理")

        if not suggestions:
            suggestions.append("继续完善测试用例")

        return suggestions

    def _generate_branch_suggestions(self, data: FileCoverageData) -> List[str]:
        """生成分支覆盖率改进建议"""
        suggestions = []
        if data.branch_rate < 50:
            suggestions.append("分支覆盖率严重不足，添加边界条件测试")
        else:
            suggestions.append("添加更多边界条件测试用例")
        if data.missing_branches:
            suggestions.append(f"有 {len(data.missing_branches)} 个分支未被覆盖")
        return suggestions

    def _generate_function_suggestions(self, data: FileCoverageData) -> List[str]:
        """生成函数覆盖率改进建议"""
        suggestions = []
        if data.function_rate < 50:
            suggestions.append("函数覆盖率严重不足，确保所有函数被调用")
        else:
            suggestions.append("添加缺失函数的测试用例")
        if data.missing_functions:
            suggestions.append(f"有 {len(data.missing_functions)} 个函数未被覆盖")
        return suggestions


class CoverageMonitor:
    """覆盖率监控器主类"""

    def __init__(
        self,
        threshold: float = 80.0,
        branch_threshold: float = 70.0,
        function_threshold: float = 85.0,
        warn_threshold: float = 5.0,
        history_days: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        self.threshold = threshold
        self.branch_threshold = branch_threshold
        self.function_threshold = function_threshold
        self.warn_threshold = warn_threshold
        self.history_days = history_days
        self.logger = logger or logging.getLogger(__name__)

        self.calculator = CoverageCalculator(logger)
        self.change_tracker = CoverageChangeTracker(logger)
        self.alert_manager = CoverageAlertManager(
            threshold, branch_threshold, function_threshold, warn_threshold, logger
        )

        self._current_coverage: Dict[str, FileCoverageData] = {}
        self._previous_coverage: Dict[str, FileCoverageData] = {}
        self._history: List[CoverageHistory] = []

    def monitor(
        self,
        report_path: Path,
        history_path: Optional[Path] = None,
        project: str = "default"
    ) -> CoverageMonitorReport:
        """执行覆盖率监控"""
        self.logger.info(f"开始监控覆盖率: {report_path}")

        self._current_coverage = self.calculator.parse_report(report_path)

        if history_path:
            self._history = self.change_tracker.load_history(history_path, self.history_days)
            if self._history:
                latest = max(self._history, key=lambda h: h.timestamp)
                for file_data in latest.files:
                    self._previous_coverage[file_data.file_path] = file_data

        changes = self.change_tracker.track_changes(
            self._current_coverage,
            self._previous_coverage
        )

        alerts = self.alert_manager.check_alerts(self._current_coverage, changes, self._history)

        current_line_rate, current_branch_rate, current_function_rate = self.calculator.calculate(self._current_coverage)
        previous_line_rate, _, _ = self.calculator.calculate(self._previous_coverage)

        current_history = CoverageHistory(
            timestamp=datetime.now().isoformat(),
            total_line_rate=current_line_rate,
            total_branch_rate=current_branch_rate,
            file_count=len(self._current_coverage),
            covered_files=sum(1 for f in self._current_coverage.values() if f.line_rate >= self.threshold)
        )

        if history_path:
            self.change_tracker.save_history([current_history], history_path)

        trend = self.change_tracker.get_trend(self._history + [current_history])

        summary = self._generate_summary(
            current_line_rate,
            current_branch_rate,
            current_function_rate,
            previous_line_rate,
            changes,
            alerts,
            trend
        )

        return CoverageMonitorReport(
            timestamp=datetime.now().isoformat(),
            project=project,
            current_coverage=current_line_rate,
            previous_coverage=previous_line_rate,
            coverage_delta=current_line_rate - previous_line_rate,
            threshold=self.threshold,
            threshold_met=current_line_rate >= self.threshold,
            files=list(self._current_coverage.values()),
            changes=changes,
            alerts=alerts,
            history=self._history[-10:],
            summary=summary
        )

    def _generate_summary(
        self,
        current_line_rate: float,
        current_branch_rate: float,
        current_function_rate: float,
        previous_rate: float,
        changes: List[CoverageChange],
        alerts: List[CoverageAlert],
        trend: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成摘要"""
        increased = sum(1 for c in changes if c.change_type == CoverageChangeType.INCREASED)
        decreased = sum(1 for c in changes if c.change_type == CoverageChangeType.DECREASED)
        new_files = sum(1 for c in changes if c.change_type == CoverageChangeType.NEW_FILE)

        critical_alerts = sum(1 for a in alerts if a.alert_level == AlertLevel.CRITICAL)
        error_alerts = sum(1 for a in alerts if a.alert_level == AlertLevel.ERROR)

        high_risk_files = sum(1 for f in self._current_coverage.values() if f.risk_score > 50)

        return {
            "total_files": len(self._current_coverage),
            "current_coverage": round(current_line_rate, 2),
            "current_branch_coverage": round(current_branch_rate, 2),
            "current_function_coverage": round(current_function_rate, 2),
            "previous_coverage": round(previous_rate, 2),
            "coverage_delta": round(current_line_rate - previous_rate, 2),
            "trend": trend,
            "changes_summary": {
                "increased": increased,
                "decreased": decreased,
                "new_files": new_files,
                "total_changes": len(changes)
            },
            "alerts_summary": {
                "critical": critical_alerts,
                "error": error_alerts,
                "warning": sum(1 for a in alerts if a.alert_level == AlertLevel.WARNING),
                "info": sum(1 for a in alerts if a.alert_level == AlertLevel.INFO),
                "total_alerts": len(alerts)
            },
            "risk_summary": {
                "high_risk_files": high_risk_files,
                "avg_risk_score": round(
                    sum(f.risk_score for f in self._current_coverage.values()) / len(self._current_coverage), 2
                ) if self._current_coverage else 0
            },
            "health_status": self._determine_health_status(current_line_rate, critical_alerts, error_alerts)
        }

    def _determine_health_status(
        self,
        coverage: float,
        critical: int,
        errors: int
    ) -> str:
        """确定健康状态"""
        if critical > 0 or coverage < 50:
            return "critical"
        elif errors > 0 or coverage < self.threshold:
            return "warning"
        elif coverage < self.threshold + 10:
            return "moderate"
        else:
            return "healthy"

    def save_report(self, report: CoverageMonitorReport, output_path: Path) -> bool:
        """保存报告"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)

            self.logger.info(f"报告已保存到 {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
            return False

    def generate_html_report(self, report: CoverageMonitorReport) -> str:
        """生成HTML报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>覆盖率监控报告 - {report.project}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
        h2 {{ color: #555; margin-top: 30px; }}
        .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .card {{ background: #f9f9f9; padding: 20px; border-radius: 8px; text-align: center; }}
        .card h3 {{ margin: 0 0 10px 0; color: #666; font-size: 14px; }}
        .card .value {{ font-size: 32px; font-weight: bold; color: #333; }}
        .card.healthy .value {{ color: #4CAF50; }}
        .card.warning .value {{ color: #FF9800; }}
        .card.critical .value {{ color: #f44336; }}
        .progress-bar {{ background: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden; margin: 10px 0; }}
        .progress-bar .fill {{ height: 100%; transition: width 0.3s; }}
        table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f5f5f5; }}
        tr:hover {{ background: #f9f9f9; }}
        .alert {{ padding: 15px; margin: 10px 0; border-radius: 4px; }}
        .alert.critical {{ background: #ffebee; border-left: 4px solid #f44336; }}
        .alert.error {{ background: #fff3e0; border-left: 4px solid #ff9800; }}
        .alert.warning {{ background: #fffde7; border-left: 4px solid #ffeb3b; }}
        .alert.info {{ background: #e3f2fd; border-left: 4px solid #2196f3; }}
        .badge {{ display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .badge.healthy {{ background: #4CAF50; color: white; }}
        .badge.warning {{ background: #FF9800; color: white; }}
        .badge.critical {{ background: #f44336; color: white; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 覆盖率监控报告</h1>
        <p><strong>项目:</strong> {report.project} | <strong>时间:</strong> {report.timestamp}</p>
        
        <div class="summary">
            <div class="card {'healthy' if report.threshold_met else 'critical'}">
                <h3>行覆盖率</h3>
                <div class="value">{report.current_coverage:.1f}%</div>
                <div class="progress-bar">
                    <div class="fill" style="width: {min(report.current_coverage, 100)}%; background: {'#4CAF50' if report.threshold_met else '#f44336'}"></div>
                </div>
            </div>
            <div class="card">
                <h3>分支覆盖率</h3>
                <div class="value">{report.summary.get('current_branch_coverage', 0):.1f}%</div>
            </div>
            <div class="card">
                <h3>函数覆盖率</h3>
                <div class="value">{report.summary.get('current_function_coverage', 0):.1f}%</div>
            </div>
            <div class="card {'healthy' if report.coverage_delta >= 0 else 'critical'}">
                <h3>覆盖率变化</h3>
                <div class="value">{'+' if report.coverage_delta >= 0 else ''}{report.coverage_delta:.1f}%</div>
            </div>
        </div>

        <h2>📁 文件覆盖率详情</h2>
        <table>
            <thead>
                <tr>
                    <th>文件</th>
                    <th>行覆盖率</th>
                    <th>分支覆盖率</th>
                    <th>函数覆盖率</th>
                    <th>风险评分</th>
                    <th>状态</th>
                </tr>
            </thead>
            <tbody>
"""
        for f in sorted(report.files, key=lambda x: x.line_rate)[:20]:
            status_class = 'healthy' if f.line_rate >= self.threshold else 'critical'
            status_text = '✓ 达标' if f.line_rate >= self.threshold else '✗ 未达标'
            html += f"""
                <tr>
                    <td>{f.file_path}</td>
                    <td>{f.line_rate:.1f}%</td>
                    <td>{f.branch_rate:.1f}%</td>
                    <td>{f.function_rate:.1f}%</td>
                    <td>{f.risk_score:.1f}</td>
                    <td><span class="badge {status_class}">{status_text}</span></td>
                </tr>
"""
        html += """
            </tbody>
        </table>

        <h2>⚠️ 预警信息</h2>
"""
        for alert in report.alerts[:10]:
            html += f"""
        <div class="alert {alert.alert_level.value}">
            <strong>[{alert.alert_level.value.upper()}]</strong> {alert.file_path}<br>
            {alert.message}<br>
            <small>建议: {', '.join(alert.suggestions[:2])}</small>
        </div>
"""
        html += """
    </div>
</body>
</html>
"""
        return html

    def generate_markdown_report(self, report: CoverageMonitorReport) -> str:
        """生成Markdown报告"""
        md = f"""# 覆盖率监控报告

**项目:** {report.project}  
**时间:** {report.timestamp}  
**健康状态:** {report.summary['health_status'].upper()}

## 📊 覆盖率概览

| 指标 | 当前值 | 阈值 | 状态 |
|------|--------|------|------|
| 行覆盖率 | {report.current_coverage:.1f}% | {report.threshold}% | {'✅ 达标' if report.threshold_met else '❌ 未达标'} |
| 分支覆盖率 | {report.summary.get('current_branch_coverage', 0):.1f}% | {self.branch_threshold}% | {'✅ 达标' if report.summary.get('current_branch_coverage', 0) >= self.branch_threshold else '❌ 未达标'} |
| 函数覆盖率 | {report.summary.get('current_function_coverage', 0):.1f}% | {self.function_threshold}% | {'✅ 达标' if report.summary.get('current_function_coverage', 0) >= self.function_threshold else '❌ 未达标'} |
| 覆盖率变化 | {'+' if report.coverage_delta >= 0 else ''}{report.coverage_delta:.1f}% | - | {'📈 上升' if report.coverage_delta > 0 else '📉 下降' if report.coverage_delta < 0 else '➡️ 稳定'} |

## 📁 文件覆盖率 (前20个)

| 文件 | 行覆盖率 | 分支覆盖率 | 函数覆盖率 | 风险评分 |
|------|----------|------------|------------|----------|
"""
        for f in sorted(report.files, key=lambda x: x.line_rate)[:20]:
            md += f"| {f.file_path} | {f.line_rate:.1f}% | {f.branch_rate:.1f}% | {f.function_rate:.1f}% | {f.risk_score:.1f} |\n"

        md += "\n## ⚠️ 预警信息\n\n"
        for alert in report.alerts[:10]:
            level_emoji = {"critical": "🔴", "error": "🟠", "warning": "🟡", "info": "🔵"}.get(alert.alert_level.value, "⚪")
            md += f"### {level_emoji} [{alert.alert_level.value.upper()}] {alert.file_path}\n\n"
            md += f"- **消息:** {alert.message}\n"
            md += f"- **当前覆盖率:** {alert.current_coverage:.1f}%\n"
            md += f"- **建议:** {', '.join(alert.suggestions)}\n\n"

        md += f"""
## 📈 统计摘要

- **总文件数:** {report.summary['total_files']}
- **高风险文件:** {report.summary.get('risk_summary', {}).get('high_risk_files', 0)}
- **预警总数:** {report.summary['alerts_summary']['total_alerts']}
  - 严重: {report.summary['alerts_summary']['critical']}
  - 错误: {report.summary['alerts_summary']['error']}
  - 警告: {report.summary['alerts_summary']['warning']}
  - 信息: {report.summary['alerts_summary']['info']}

---
*报告由覆盖率监控器自动生成*
"""
        return md

    def print_report(self, report: CoverageMonitorReport) -> None:
        """打印报告"""
        print("\n" + "=" * 80)
        print("覆盖率监控报告")
        print("=" * 80)
        print(f"项目: {report.project}")
        print(f"时间: {report.timestamp}")
        print(f"\n当前覆盖率: {report.current_coverage:.2f}%")
        print(f"上次覆盖率: {report.previous_coverage:.2f}%")
        print(f"覆盖率变化: {'+' if report.coverage_delta >= 0 else ''}{report.coverage_delta:.2f}%")
        print(f"阈值: {report.threshold}%")
        print(f"达标: {'✅ 是' if report.threshold_met else '❌ 否'}")

        summary = report.summary
        print(f"\n健康状态: {summary['health_status'].upper()}")
        print(f"分支覆盖率: {summary.get('current_branch_coverage', 0):.2f}%")
        print(f"函数覆盖率: {summary.get('current_function_coverage', 0):.2f}%")

        trend = summary.get("trend", {})
        if trend.get("trend") == "calculated":
            direction_icons = {
                "improving": "📈",
                "declining": "📉",
                "stable": "➡️"
            }
            icon = direction_icons.get(trend["direction"], "❓")
            print(f"趋势: {icon} {trend['direction']} (斜率: {trend['slope']:.4f})")

        changes = summary.get("changes_summary", {})
        if changes.get("total_changes", 0) > 0:
            print(f"\n变化统计:")
            print(f"  上升: {changes.get('increased', 0)} 个文件")
            print(f"  下降: {changes.get('decreased', 0)} 个文件")
            print(f"  新增: {changes.get('new_files', 0)} 个文件")

        alerts = summary.get("alerts_summary", {})
        if alerts.get("total_alerts", 0) > 0:
            print(f"\n预警统计:")
            print(f"  严重: {alerts.get('critical', 0)}")
            print(f"  错误: {alerts.get('error', 0)}")
            print(f"  警告: {alerts.get('warning', 0)}")
            print(f"  信息: {alerts.get('info', 0)}")

        if report.alerts:
            print(f"\n预警详情 (前10个):")
            for i, alert in enumerate(report.alerts[:10], 1):
                level_icons = {
                    AlertLevel.CRITICAL: "🔴",
                    AlertLevel.ERROR: "🟠",
                    AlertLevel.WARNING: "🟡",
                    AlertLevel.INFO: "🔵"
                }
                icon = level_icons.get(alert.alert_level, "⚪")
                print(f"\n{i}. {icon} [{alert.alert_level.value.upper()}] {alert.file_path}")
                print(f"   当前: {alert.current_coverage:.1f}% | 阈值: {alert.threshold}%")
                print(f"   {alert.message}")

        low_coverage_files = sorted(
            [f for f in report.files if f.line_rate < self.threshold],
            key=lambda x: x.line_rate
        )[:10]

        if low_coverage_files:
            print(f"\n低覆盖率文件 (前10个):")
            for f in low_coverage_files:
                print(f"  - {f.file_path}: {f.line_rate:.1f}% (风险: {f.risk_score:.1f})")


def setup_logger(verbose: bool = False) -> logging.Logger:
    """配置日志记录器"""
    logger = logging.getLogger("CoverageMonitor")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="覆盖率监控器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python coverage_monitor.py --report coverage.xml
  python coverage_monitor.py --report coverage.json --threshold 80
  python coverage_monitor.py --report lcov.info --history-days 30
        """
    )

    parser.add_argument(
        "--report",
        type=str,
        required=True,
        help="覆盖率报告文件路径"
    )

    parser.add_argument(
        "--threshold",
        type=float,
        default=80.0,
        help="覆盖率阈值 (默认: 80)"
    )

    parser.add_argument(
        "--warn-threshold",
        type=float,
        default=5.0,
        help="覆盖率下降预警阈值 (默认: 5)"
    )

    parser.add_argument(
        "--history-days",
        type=int,
        default=30,
        help="历史数据天数 (默认: 30)"
    )

    parser.add_argument(
        "--history-file",
        type=str,
        help="历史记录文件路径"
    )

    parser.add_argument(
        "--project",
        type=str,
        default="default",
        help="项目名称 (默认: default)"
    )

    parser.add_argument(
        "--output",
        choices=["console", "json"],
        default="console",
        help="输出格式 (默认: console)"
    )

    parser.add_argument(
        "--output-file",
        type=str,
        help="输出文件路径"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="启用详细日志输出"
    )

    args = parser.parse_args()

    logger = setup_logger(args.verbose)

    print("=" * 80)
    print("覆盖率监控器")
    print("=" * 80)

    monitor = CoverageMonitor(
        threshold=args.threshold,
        warn_threshold=args.warn_threshold,
        history_days=args.history_days,
        logger=logger
    )

    report_path = Path(args.report)
    history_path = Path(args.history_file) if args.history_file else None

    report = monitor.monitor(report_path, history_path, args.project)

    if args.output == "console":
        monitor.print_report(report)

    if args.output == "json" or args.output_file:
        output_data = report.to_dict()
        output_json = json.dumps(output_data, ensure_ascii=False, indent=2)

        if args.output_file:
            output_path = Path(args.output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(output_json)
            print(f"\n报告已保存到: {output_path}")
        else:
            print("\nJSON 输出:")
            print(output_json)

    return 0 if report.threshold_met else 1


if __name__ == "__main__":
    sys.exit(main())
