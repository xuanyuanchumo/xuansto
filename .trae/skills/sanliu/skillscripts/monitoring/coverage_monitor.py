#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
覆盖率监控器 (增强版)

实现覆盖率计算、覆盖率变化追踪和覆盖率下降预警。
支持多种覆盖率报告格式（Python coverage.py, JavaScript istanbul/nyc, LCOV等）。
支持生成JSON、HTML、Markdown格式的报告。

使用示例:
    python coverage_monitor.py --report coverage.json
    python coverage_monitor.py --report coverage.xml --threshold 80 --warn-threshold 5
    python coverage_monitor.py --report lcov.info --history-days 30 --output html
    python coverage_monitor.py --report coverage-final.json --format istanbul
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
from typing import Any, Dict, List, Optional, Tuple, Set
from xml.etree import ElementTree
from collections import defaultdict
import statistics


class CoverageFormat(Enum):
    """覆盖率报告格式"""
    COVERAGE_XML = "coverage_xml"
    COVERAGE_JSON = "coverage_json"
    LCOV = "lcov"
    ISTANBUL = "istanbul"
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
class FunctionCoverage:
    """函数覆盖率数据"""
    name: str
    start_line: int
    end_line: int
    executed: bool
    execution_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "executed": self.executed,
            "execution_count": self.execution_count
        }


@dataclass
class BranchCoverage:
    """分支覆盖率数据"""
    line: int
    branch_id: int
    taken: bool
    count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line": self.line,
            "branch_id": self.branch_id,
            "taken": self.taken,
            "count": self.count
        }


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
    covered_functions: int
    total_functions: int
    missing_lines: List[int] = field(default_factory=list)
    functions: List[FunctionCoverage] = field(default_factory=list)
    branches: List[BranchCoverage] = field(default_factory=list)
    timestamp: str = ""
    module: str = ""

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
            "functions": [f.to_dict() for f in self.functions[:10]],
            "branches": [b.to_dict() for b in self.branches[:10]],
            "timestamp": self.timestamp,
            "module": self.module
        }


@dataclass
class ModuleCoverage:
    """模块覆盖率数据"""
    module_name: str
    line_rate: float
    branch_rate: float
    function_rate: float
    file_count: int
    covered_files: int
    files: List[FileCoverageData] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "module_name": self.module_name,
            "line_rate": round(self.line_rate, 2),
            "branch_rate": round(self.branch_rate, 2),
            "function_rate": round(self.function_rate, 2),
            "file_count": self.file_count,
            "covered_files": self.covered_files,
            "files": [f.to_dict() for f in self.files[:20]]
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
    module: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "file_path": self.file_path,
            "change_type": self.change_type.value,
            "old_line_rate": round(self.old_line_rate, 2),
            "new_line_rate": round(self.new_line_rate, 2),
            "delta": round(self.delta, 2),
            "timestamp": self.timestamp,
            "details": self.details,
            "module": self.module
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
    module: str = ""

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
            "module": self.module
        }


@dataclass
class CoverageHistory:
    """覆盖率历史记录"""
    timestamp: str
    total_line_rate: float
    total_branch_rate: float
    total_function_rate: float
    file_count: int
    covered_files: int
    modules: List[ModuleCoverage] = field(default_factory=list)
    files: List[FileCoverageData] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_line_rate": round(self.total_line_rate, 2),
            "total_branch_rate": round(self.total_branch_rate, 2),
            "total_function_rate": round(self.total_function_rate, 2),
            "file_count": self.file_count,
            "covered_files": self.covered_files,
            "modules": [m.to_dict() for m in self.modules],
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
    modules: List[ModuleCoverage]
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
            "modules": [m.to_dict() for m in self.modules],
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
    """Coverage XML格式解析器 (Python coverage.py)"""

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
                    module = self._extract_module(file_path_str)

                    line_rate = float(cls.get("line-rate", 0)) * 100
                    branch_rate = float(cls.get("branch-rate", 0)) * 100

                    lines = cls.findall("lines/line")
                    covered_lines = sum(1 for l in lines if l.get("hits", "0") != "0")
                    total_lines = len(lines)
                    missing_lines = [int(l.get("number", 0)) for l in lines if l.get("hits", "0") == "0"]

                    branches = [l for l in lines if l.get("branch") == "true"]
                    covered_branches = sum(1 for b in branches if b.get("condition-coverage", "").startswith("100%"))
                    total_branches = len(branches)

                    functions = self._parse_functions(cls)
                    covered_functions = sum(1 for f in functions if f.executed)
                    total_functions = len(functions)
                    function_rate = (covered_functions / total_functions * 100) if total_functions > 0 else line_rate

                    coverage_data[file_path_str] = FileCoverageData(
                        file_path=file_path_str,
                        line_rate=line_rate,
                        branch_rate=branch_rate,
                        function_rate=function_rate,
                        covered_lines=covered_lines,
                        total_lines=total_lines,
                        covered_branches=covered_branches,
                        total_branches=total_branches,
                        covered_functions=covered_functions,
                        total_functions=total_functions,
                        missing_lines=missing_lines,
                        functions=functions,
                        timestamp=timestamp,
                        module=module
                    )
        except Exception as e:
            self.logger.error(f"解析Coverage XML失败: {e}")

        return coverage_data

    def _parse_functions(self, cls: ElementTree.Element) -> List[FunctionCoverage]:
        functions: List[FunctionCoverage] = []
        for method in cls.findall("methods/method"):
            name = method.get("name", "")
            start_line = 0
            end_line = 0
            executed = False
            exec_count = 0

            lines = method.findall("lines/line")
            if lines:
                start_line = int(lines[0].get("number", 0))
                end_line = int(lines[-1].get("number", 0))
                hits = [int(l.get("hits", 0)) for l in lines]
                exec_count = sum(hits)
                executed = exec_count > 0

            functions.append(FunctionCoverage(
                name=name,
                start_line=start_line,
                end_line=end_line,
                executed=executed,
                execution_count=exec_count
            ))
        return functions

    def _extract_module(self, file_path: str) -> str:
        parts = file_path.replace("\\", "/").split("/")
        if len(parts) > 1:
            return parts[0]
        return "root"


class CoverageJsonParser(ICoverageParser):
    """Coverage JSON格式解析器 (Python coverage.py)"""

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
                functions_data = file_info.get("functions", {})

                covered_lines = len(executed_lines)
                total_lines = covered_lines + len(missing_lines)
                line_rate = (covered_lines / total_lines * 100) if total_lines > 0 else 0

                num_branches = summary.get("num_branches", 0)
                covered_branches = summary.get("covered_branches", 0)
                branch_rate = (covered_branches / num_branches * 100) if num_branches > 0 else 0

                functions = self._parse_functions(functions_data)
                covered_functions = sum(1 for f in functions if f.executed)
                total_functions = len(functions)
                function_rate = (covered_functions / total_functions * 100) if total_functions > 0 else line_rate

                module = self._extract_module(file_path_str)

                coverage_data[file_path_str] = FileCoverageData(
                    file_path=file_path_str,
                    line_rate=line_rate,
                    branch_rate=branch_rate,
                    function_rate=function_rate,
                    covered_lines=covered_lines,
                    total_lines=total_lines,
                    covered_branches=covered_branches,
                    total_branches=num_branches,
                    covered_functions=covered_functions,
                    total_functions=total_functions,
                    missing_lines=missing_lines,
                    functions=functions,
                    timestamp=timestamp,
                    module=module
                )
        except Exception as e:
            self.logger.error(f"解析Coverage JSON失败: {e}")

        return coverage_data

    def _parse_functions(self, functions_data: Dict[str, Any]) -> List[FunctionCoverage]:
        functions: List[FunctionCoverage] = []
        for func_name, func_info in functions_data.items():
            if isinstance(func_info, dict):
                functions.append(FunctionCoverage(
                    name=func_name,
                    start_line=func_info.get("start_line", 0),
                    end_line=func_info.get("end_line", 0),
                    executed=func_info.get("executed", False),
                    execution_count=func_info.get("count", 0)
                ))
        return functions

    def _extract_module(self, file_path: str) -> str:
        parts = file_path.replace("\\", "/").split("/")
        if len(parts) > 1:
            return parts[0]
        return "root"


class IstanbulParser(ICoverageParser):
    """Istanbul/NYC JSON格式解析器 (JavaScript)"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def supports_format(self, format_type: CoverageFormat) -> bool:
        return format_type == CoverageFormat.ISTANBUL

    def parse(self, file_path: Path) -> Dict[str, FileCoverageData]:
        if not file_path.exists():
            self.logger.warning(f"Istanbul报告不存在: {file_path}")
            return {}

        coverage_data: Dict[str, FileCoverageData] = {}
        timestamp = datetime.now().isoformat()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for file_path_str, file_info in data.items():
                if not isinstance(file_info, dict):
                    continue

                line_map = file_info.get("l", {})
                branch_map = file_info.get("b", {})
                function_map = file_info.get("f", {})
                fn_map = file_info.get("fnMap", {})

                total_lines = len(line_map)
                covered_lines = sum(1 for count in line_map.values() if count > 0)
                line_rate = (covered_lines / total_lines * 100) if total_lines > 0 else 0

                total_branches = 0
                covered_branches = 0
                branches: List[BranchCoverage] = []
                for branch_id, counts in branch_map.items():
                    if isinstance(counts, list):
                        for i, count in enumerate(counts):
                            total_branches += 1
                            if count > 0:
                                covered_branches += 1
                            branches.append(BranchCoverage(
                                line=0,
                                branch_id=int(branch_id) * 100 + i,
                                taken=count > 0,
                                count=count
                            ))
                branch_rate = (covered_branches / total_branches * 100) if total_branches > 0 else 0

                functions: List[FunctionCoverage] = []
                for func_id, func_info in fn_map.items():
                    count = function_map.get(func_id, 0)
                    functions.append(FunctionCoverage(
                        name=func_info.get("name", f"func_{func_id}"),
                        start_line=func_info.get("loc", {}).get("start", {}).get("line", 0),
                        end_line=func_info.get("loc", {}).get("end", {}).get("line", 0),
                        executed=count > 0,
                        execution_count=count
                    ))

                total_functions = len(functions)
                covered_functions = sum(1 for f in functions if f.executed)
                function_rate = (covered_functions / total_functions * 100) if total_functions > 0 else 0

                missing_lines = [int(line) for line, count in line_map.items() if count == 0]

                module = self._extract_module(file_path_str)

                coverage_data[file_path_str] = FileCoverageData(
                    file_path=file_path_str,
                    line_rate=line_rate,
                    branch_rate=branch_rate,
                    function_rate=function_rate,
                    covered_lines=covered_lines,
                    total_lines=total_lines,
                    covered_branches=covered_branches,
                    total_branches=total_branches,
                    covered_functions=covered_functions,
                    total_functions=total_functions,
                    missing_lines=missing_lines,
                    functions=functions,
                    branches=branches,
                    timestamp=timestamp,
                    module=module
                )
        except Exception as e:
            self.logger.error(f"解析Istanbul JSON失败: {e}")

        return coverage_data

    def _extract_module(self, file_path: str) -> str:
        parts = file_path.replace("\\", "/").split("/")
        for i, part in enumerate(parts):
            if part in ("src", "lib", "dist", "app", "components", "pages"):
                if i + 1 < len(parts):
                    return parts[i + 1]
                return part
        if len(parts) > 1:
            return parts[-2]
        return "root"


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
            function_data: Dict[str, Tuple[int, int]] = {}

            for line in content.split('\n'):
                if line.startswith('SF:'):
                    current_file = line[3:].strip()
                    line_data = {}
                    branch_data = {}
                    function_data = {}
                elif line.startswith('FN:'):
                    parts = line[3:].split(',')
                    if len(parts) >= 2:
                        line_num = int(parts[0])
                        func_name = parts[1].strip()
                        function_data[func_name] = (line_num, 0)
                elif line.startswith('FNDA:'):
                    parts = line[5:].split(',')
                    if len(parts) >= 2:
                        count = int(parts[0])
                        func_name = parts[1].strip()
                        if func_name in function_data:
                            start_line, _ = function_data[func_name]
                            function_data[func_name] = (start_line, count)
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

                        functions: List[FunctionCoverage] = []
                        for func_name, (start_line, count) in function_data.items():
                            functions.append(FunctionCoverage(
                                name=func_name,
                                start_line=start_line,
                                end_line=0,
                                executed=count > 0,
                                execution_count=count
                            ))

                        total_functions = len(functions)
                        covered_functions = sum(1 for f in functions if f.executed)
                        function_rate = (covered_functions / total_functions * 100) if total_functions > 0 else 0

                        missing_lines = [ln for ln, hits in line_data.items() if hits == 0]

                        module = self._extract_module(current_file)

                        coverage_data[current_file] = FileCoverageData(
                            file_path=current_file,
                            line_rate=line_rate,
                            branch_rate=branch_rate,
                            function_rate=function_rate,
                            covered_lines=covered_lines,
                            total_lines=total_lines,
                            covered_branches=covered_branches,
                            total_branches=total_branches,
                            covered_functions=covered_functions,
                            total_functions=total_functions,
                            missing_lines=missing_lines,
                            functions=functions,
                            timestamp=timestamp,
                            module=module
                        )
                    current_file = ""
                    line_data = {}
                    branch_data = {}
                    function_data = {}
        except Exception as e:
            self.logger.error(f"解析LCOV失败: {e}")

        return coverage_data

    def _extract_module(self, file_path: str) -> str:
        parts = file_path.replace("\\", "/").split("/")
        if len(parts) > 1:
            return parts[0]
        return "root"


class CoverageCalculator:
    """覆盖率计算器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.parsers: List[ICoverageParser] = [
            CoverageXmlParser(logger),
            CoverageJsonParser(logger),
            IstanbulParser(logger),
            LcovParser(logger)
        ]

    def calculate(self, coverage_data: Dict[str, FileCoverageData]) -> Tuple[float, float, float]:
        """计算总体覆盖率 (行覆盖率, 分支覆盖率, 函数覆盖率)"""
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

        return line_rate, branch_rate, function_rate

    def parse_report(self, report_path: Path, format_type: Optional[CoverageFormat] = None) -> Dict[str, FileCoverageData]:
        """解析覆盖率报告"""
        if format_type is None:
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

        if file_name.endswith('.json'):
            try:
                with open(report_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        if "files" in data:
                            return CoverageFormat.COVERAGE_JSON
                        for key in data.keys():
                            if "/" in key or "\\" in key or key.endswith(".js") or key.endswith(".ts"):
                                return CoverageFormat.ISTANBUL
            except Exception:
                pass
            return CoverageFormat.COVERAGE_JSON

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

        if file_name.endswith('.info') or 'lcov' in file_name:
            return CoverageFormat.LCOV

        return CoverageFormat.COVERAGE_XML

    def aggregate_by_module(self, coverage_data: Dict[str, FileCoverageData]) -> List[ModuleCoverage]:
        """按模块聚合覆盖率"""
        modules: Dict[str, List[FileCoverageData]] = defaultdict(list)

        for file_data in coverage_data.values():
            modules[file_data.module].append(file_data)

        result: List[ModuleCoverage] = []
        for module_name, files in modules.items():
            total_covered_lines = sum(f.covered_lines for f in files)
            total_lines = sum(f.total_lines for f in files)
            total_covered_branches = sum(f.covered_branches for f in files)
            total_branches = sum(f.total_branches for f in files)
            total_covered_functions = sum(f.covered_functions for f in files)
            total_functions = sum(f.total_functions for f in files)

            line_rate = (total_covered_lines / total_lines * 100) if total_lines > 0 else 0
            branch_rate = (total_covered_branches / total_branches * 100) if total_branches > 0 else 0
            function_rate = (total_covered_functions / total_functions * 100) if total_functions > 0 else 0

            result.append(ModuleCoverage(
                module_name=module_name,
                line_rate=line_rate,
                branch_rate=branch_rate,
                function_rate=function_rate,
                file_count=len(files),
                covered_files=sum(1 for f in files if f.line_rate >= 80),
                files=files
            ))

        return sorted(result, key=lambda m: m.module_name)


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
                details="新增文件",
                module=current[file_path].module
            ))

        for file_path in previous_files - current_files:
            changes.append(CoverageChange(
                file_path=file_path,
                change_type=CoverageChangeType.REMOVED_FILE,
                old_line_rate=previous[file_path].line_rate,
                new_line_rate=0.0,
                delta=-previous[file_path].line_rate,
                timestamp=timestamp,
                details="文件已删除",
                module=previous[file_path].module
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
                    details=f"覆盖率{'上升' if delta > 0 else '下降'} {abs(delta):.2f}%",
                    module=current[file_path].module
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
                            FileCoverageData(
                                file_path=f.get("file_path", ""),
                                line_rate=f.get("line_rate", 0),
                                branch_rate=f.get("branch_rate", 0),
                                function_rate=f.get("function_rate", 0),
                                covered_lines=f.get("covered_lines", 0),
                                total_lines=f.get("total_lines", 0),
                                covered_branches=f.get("covered_branches", 0),
                                total_branches=f.get("total_branches", 0),
                                covered_functions=f.get("covered_functions", 0),
                                total_functions=f.get("total_functions", 0),
                                missing_lines=f.get("missing_lines", []),
                                module=f.get("module", "")
                            ) for f in item.get("files", [])
                        ]
                        modules = [
                            ModuleCoverage(
                                module_name=m.get("module_name", ""),
                                line_rate=m.get("line_rate", 0),
                                branch_rate=m.get("branch_rate", 0),
                                function_rate=m.get("function_rate", 0),
                                file_count=m.get("file_count", 0),
                                covered_files=m.get("covered_files", 0)
                            ) for m in item.get("modules", [])
                        ]
                        history.append(CoverageHistory(
                            timestamp=item["timestamp"],
                            total_line_rate=item.get("total_line_rate", 0),
                            total_branch_rate=item.get("total_branch_rate", 0),
                            total_function_rate=item.get("total_function_rate", 0),
                            file_count=item.get("file_count", 0),
                            covered_files=item.get("covered_files", 0),
                            modules=modules,
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
            "data_points": n,
            "average": round(statistics.mean(values), 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2)
        }

    def get_module_changes(
        self,
        current_modules: List[ModuleCoverage],
        previous_modules: List[ModuleCoverage]
    ) -> Dict[str, Dict[str, Any]]:
        """获取模块级别的覆盖率变化"""
        current_map = {m.module_name: m for m in current_modules}
        previous_map = {m.module_name: m for m in previous_modules}

        changes: Dict[str, Dict[str, Any]] = {}

        for module_name in set(current_map.keys()) | set(previous_map.keys()):
            current = current_map.get(module_name)
            previous = previous_map.get(module_name)

            if current and previous:
                changes[module_name] = {
                    "line_rate_delta": current.line_rate - previous.line_rate,
                    "branch_rate_delta": current.branch_rate - previous.branch_rate,
                    "function_rate_delta": current.function_rate - previous.function_rate,
                    "file_count_delta": current.file_count - previous.file_count,
                    "current": current.to_dict(),
                    "previous": previous.to_dict()
                }
            elif current:
                changes[module_name] = {
                    "line_rate_delta": current.line_rate,
                    "branch_rate_delta": current.branch_rate,
                    "function_rate_delta": current.function_rate,
                    "file_count_delta": current.file_count,
                    "current": current.to_dict(),
                    "previous": None,
                    "status": "new"
                }
            else:
                changes[module_name] = {
                    "line_rate_delta": -previous.line_rate,
                    "branch_rate_delta": -previous.branch_rate,
                    "function_rate_delta": -previous.function_rate,
                    "file_count_delta": -previous.file_count,
                    "current": None,
                    "previous": previous.to_dict(),
                    "status": "removed"
                }

        return changes


class CoverageAlertManager:
    """覆盖率预警管理器"""

    def __init__(
        self,
        threshold: float = 80.0,
        warn_threshold: float = 5.0,
        logger: Optional[logging.Logger] = None
    ):
        self.threshold = threshold
        self.warn_threshold = warn_threshold
        self.logger = logger or logging.getLogger(__name__)

    def check_alerts(
        self,
        coverage_data: Dict[str, FileCoverageData],
        changes: List[CoverageChange]
    ) -> List[CoverageAlert]:
        """检查并生成预警"""
        alerts: List[CoverageAlert] = []
        timestamp = datetime.now().isoformat()

        for file_path, data in coverage_data.items():
            if data.line_rate < self.threshold:
                alert_level = self._determine_alert_level(data.line_rate)
                alerts.append(CoverageAlert(
                    alert_level=alert_level,
                    file_path=file_path,
                    current_coverage=data.line_rate,
                    threshold=self.threshold,
                    delta=self.threshold - data.line_rate,
                    message=f"文件覆盖率 {data.line_rate:.1f}% 低于阈值 {self.threshold}%",
                    timestamp=timestamp,
                    suggestions=self._generate_suggestions(data),
                    module=data.module
                ))

        for change in changes:
            if change.change_type == CoverageChangeType.DECREASED:
                if abs(change.delta) >= self.warn_threshold:
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
                        module=change.module
                    ))

        return sorted(alerts, key=lambda a: (a.alert_level.value, -a.delta))

    def _determine_alert_level(self, coverage: float) -> AlertLevel:
        """确定预警级别"""
        gap = self.threshold - coverage
        if gap >= 30:
            return AlertLevel.CRITICAL
        elif gap >= 20:
            return AlertLevel.ERROR
        elif gap >= 10:
            return AlertLevel.WARNING
        else:
            return AlertLevel.INFO

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

        if data.branch_rate < 50 and data.total_branches > 0:
            suggestions.append("分支覆盖率较低，建议增加边界条件测试")

        if data.function_rate < 50 and data.total_functions > 0:
            suggestions.append("函数覆盖率较低，建议为未测试函数编写测试")

        if not suggestions:
            suggestions.append("继续完善测试用例")

        return suggestions


class ReportGenerator:
    """报告生成器"""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)

    def generate_json(self, report: CoverageMonitorReport) -> str:
        """生成JSON格式报告"""
        return json.dumps(report.to_dict(), ensure_ascii=False, indent=2)

    def generate_html(self, report: CoverageMonitorReport) -> str:
        """生成HTML格式覆盖率可视化报告"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>覆盖率监控报告 - {report.project}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            color: #1a1a2e;
            font-size: 2em;
            margin-bottom: 10px;
        }}
        .header .meta {{
            color: #666;
            font-size: 0.9em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        .stat-card .value {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-card .label {{
            color: #666;
            font-size: 0.9em;
        }}
        .stat-card.coverage .value {{
            color: {'#10b981' if report.threshold_met else '#ef4444'};
        }}
        .stat-card.delta .value {{
            color: {'#10b981' if report.coverage_delta >= 0 else '#ef4444'};
        }}
        .stat-card.files .value {{
            color: #3b82f6;
        }}
        .stat-card.alerts .value {{
            color: {self._get_alerts_color(report.summary.get('alerts_summary', {}))};
        }}
        .progress-bar {{
            background: #e5e7eb;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin-top: 15px;
        }}
        .progress-bar .fill {{
            height: 100%;
            background: linear-gradient(90deg, #10b981, #34d399);
            border-radius: 10px;
            transition: width 0.5s ease;
        }}
        .progress-bar .fill.warning {{
            background: linear-gradient(90deg, #f59e0b, #fbbf24);
        }}
        .progress-bar .fill.danger {{
            background: linear-gradient(90deg, #ef4444, #f87171);
        }}
        .section {{
            background: white;
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #1a1a2e;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e5e7eb;
        }}
        .module-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
        }}
        .module-card {{
            background: #f9fafb;
            border-radius: 12px;
            padding: 20px;
            border-left: 4px solid #3b82f6;
        }}
        .module-card h3 {{
            color: #1a1a2e;
            margin-bottom: 10px;
        }}
        .module-card .rates {{
            display: flex;
            gap: 15px;
            margin-top: 10px;
        }}
        .module-card .rate {{
            text-align: center;
        }}
        .module-card .rate-value {{
            font-weight: bold;
            font-size: 1.2em;
        }}
        .module-card .rate-label {{
            font-size: 0.8em;
            color: #666;
        }}
        .file-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .file-table th, .file-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}
        .file-table th {{
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
        }}
        .file-table tr:hover {{
            background: #f9fafb;
        }}
        .coverage-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .coverage-badge.high {{
            background: #d1fae5;
            color: #065f46;
        }}
        .coverage-badge.medium {{
            background: #fef3c7;
            color: #92400e;
        }}
        .coverage-badge.low {{
            background: #fee2e2;
            color: #991b1b;
        }}
        .alert-list {{
            list-style: none;
        }}
        .alert-item {{
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            display: flex;
            align-items: flex-start;
            gap: 15px;
        }}
        .alert-item.critical {{
            background: #fee2e2;
            border-left: 4px solid #ef4444;
        }}
        .alert-item.error {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
        }}
        .alert-item.warning {{
            background: #fef9c3;
            border-left: 4px solid #eab308;
        }}
        .alert-item.info {{
            background: #dbeafe;
            border-left: 4px solid #3b82f6;
        }}
        .alert-icon {{
            font-size: 1.5em;
        }}
        .alert-content {{
            flex: 1;
        }}
        .alert-content h4 {{
            margin-bottom: 5px;
        }}
        .alert-content p {{
            color: #666;
            font-size: 0.9em;
        }}
        .suggestions {{
            margin-top: 10px;
            padding-left: 20px;
        }}
        .suggestions li {{
            color: #666;
            font-size: 0.85em;
            margin-bottom: 3px;
        }}
        .trend-chart {{
            height: 200px;
            display: flex;
            align-items: flex-end;
            gap: 5px;
            padding: 20px 0;
        }}
        .trend-bar {{
            flex: 1;
            background: linear-gradient(180deg, #3b82f6, #60a5fa);
            border-radius: 4px 4px 0 0;
            min-height: 10px;
            position: relative;
            transition: height 0.3s ease;
        }}
        .trend-bar:hover {{
            background: linear-gradient(180deg, #2563eb, #3b82f6);
        }}
        .trend-bar .tooltip {{
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: #1a1a2e;
            color: white;
            padding: 5px 10px;
            border-radius: 4px;
            font-size: 0.75em;
            white-space: nowrap;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}
        .trend-bar:hover .tooltip {{
            opacity: 1;
        }}
        .footer {{
            text-align: center;
            color: white;
            padding: 20px;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 覆盖率监控报告</h1>
            <div class="meta">
                <span>项目: <strong>{report.project}</strong></span> |
                <span>生成时间: {report.timestamp}</span> |
                <span>阈值: {report.threshold}%</span>
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card coverage">
                <div class="value">{report.current_coverage:.1f}%</div>
                <div class="label">当前覆盖率</div>
                <div class="progress-bar">
                    <div class="fill {'danger' if report.current_coverage < 50 else 'warning' if report.current_coverage < report.threshold else ''}" style="width: {min(report.current_coverage, 100)}%"></div>
                </div>
            </div>
            <div class="stat-card delta">
                <div class="value">{'+' if report.coverage_delta >= 0 else ''}{report.coverage_delta:.1f}%</div>
                <div class="label">覆盖率变化</div>
            </div>
            <div class="stat-card files">
                <div class="value">{len(report.files)}</div>
                <div class="label">文件数量</div>
            </div>
            <div class="stat-card alerts">
                <div class="value">{report.summary.get('alerts_summary', {}).get('total_alerts', 0)}</div>
                <div class="label">预警数量</div>
            </div>
        </div>

        <div class="section">
            <h2>📈 覆盖率趋势</h2>
            <div class="trend-chart">
                {self._generate_trend_bars(report.history)}
            </div>
        </div>

        <div class="section">
            <h2>📦 模块覆盖率</h2>
            <div class="module-grid">
                {self._generate_module_cards(report.modules)}
            </div>
        </div>

        <div class="section">
            <h2>📁 文件覆盖率详情</h2>
            <table class="file-table">
                <thead>
                    <tr>
                        <th>文件路径</th>
                        <th>模块</th>
                        <th>行覆盖率</th>
                        <th>分支覆盖率</th>
                        <th>函数覆盖率</th>
                        <th>状态</th>
                    </tr>
                </thead>
                <tbody>
                    {self._generate_file_rows(report.files, report.threshold)}
                </tbody>
            </table>
        </div>

        {self._generate_alerts_section(report.alerts)}

        <div class="footer">
            <p>覆盖率监控报告 | 由 Coverage Monitor 生成</p>
        </div>
    </div>
</body>
</html>"""
        return html

    def _get_alerts_color(self, alerts_summary: Dict[str, int]) -> str:
        if alerts_summary.get("critical", 0) > 0:
            return "#ef4444"
        elif alerts_summary.get("error", 0) > 0:
            return "#f59e0b"
        elif alerts_summary.get("warning", 0) > 0:
            return "#eab308"
        return "#10b981"

    def _generate_trend_bars(self, history: List[CoverageHistory]) -> str:
        if not history:
            return "<div style='text-align: center; color: #666;'>暂无历史数据</div>"

        max_rate = max(h.total_line_rate for h in history) if history else 100
        bars = []
        for h in history[-20:]:
            height = (h.total_line_rate / max_rate * 150) if max_rate > 0 else 0
            bars.append(f"""<div class="trend-bar" style="height: {height}px">
                <div class="tooltip">{h.timestamp[:10]}: {h.total_line_rate:.1f}%</div>
            </div>""")
        return "\n".join(bars)

    def _generate_module_cards(self, modules: List[ModuleCoverage]) -> str:
        if not modules:
            return "<div style='text-align: center; color: #666;'>暂无模块数据</div>"

        cards = []
        for m in modules[:12]:
            line_class = "high" if m.line_rate >= 80 else "medium" if m.line_rate >= 50 else "low"
            cards.append(f"""<div class="module-card">
                <h3>{m.module_name}</h3>
                <div class="rates">
                    <div class="rate">
                        <div class="rate-value {line_class}">{m.line_rate:.1f}%</div>
                        <div class="rate-label">行覆盖率</div>
                    </div>
                    <div class="rate">
                        <div class="rate-value">{m.branch_rate:.1f}%</div>
                        <div class="rate-label">分支覆盖率</div>
                    </div>
                    <div class="rate">
                        <div class="rate-value">{m.function_rate:.1f}%</div>
                        <div class="rate-label">函数覆盖率</div>
                    </div>
                </div>
                <div style="margin-top: 10px; color: #666; font-size: 0.85em;">
                    {m.file_count} 文件 | {m.covered_files} 达标
                </div>
            </div>""")
        return "\n".join(cards)

    def _generate_file_rows(self, files: List[FileCoverageData], threshold: float) -> str:
        if not files:
            return "<tr><td colspan='6' style='text-align: center; color: #666;'>暂无文件数据</td></tr>"

        rows = []
        sorted_files = sorted(files, key=lambda f: f.line_rate)[:50]
        for f in sorted_files:
            badge_class = "high" if f.line_rate >= threshold else "medium" if f.line_rate >= 50 else "low"
            status = "✅ 达标" if f.line_rate >= threshold else "⚠️ 未达标"
            rows.append(f"""<tr>
                <td style="font-family: monospace; font-size: 0.85em;">{f.file_path}</td>
                <td>{f.module}</td>
                <td><span class="coverage-badge {badge_class}">{f.line_rate:.1f}%</span></td>
                <td>{f.branch_rate:.1f}%</td>
                <td>{f.function_rate:.1f}%</td>
                <td>{status}</td>
            </tr>""")
        return "\n".join(rows)

    def _generate_alerts_section(self, alerts: List[CoverageAlert]) -> str:
        if not alerts:
            return ""

        alert_items = []
        for a in alerts[:10]:
            suggestions = "\n".join(f"<li>{s}</li>" for s in a.suggestions[:3])
            alert_items.append(f"""<li class="alert-item {a.alert_level.value}">
                <div class="alert-icon">{self._get_alert_icon(a.alert_level)}</div>
                <div class="alert-content">
                    <h4>{a.file_path}</h4>
                    <p>{a.message}</p>
                    <ul class="suggestions">{suggestions}</ul>
                </div>
            </li>""")

        return f"""<div class="section">
            <h2>🚨 预警列表</h2>
            <ul class="alert-list">
                {"".join(alert_items)}
            </ul>
        </div>"""

    def _get_alert_icon(self, level: AlertLevel) -> str:
        icons = {
            AlertLevel.CRITICAL: "🔴",
            AlertLevel.ERROR: "🟠",
            AlertLevel.WARNING: "🟡",
            AlertLevel.INFO: "🔵"
        }
        return icons.get(level, "⚪")

    def generate_markdown(self, report: CoverageMonitorReport) -> str:
        """生成Markdown格式趋势报告"""
        md = f"""# 覆盖率监控报告

## 📊 概览

| 指标 | 值 |
|------|-----|
| **项目** | {report.project} |
| **生成时间** | {report.timestamp} |
| **当前覆盖率** | {report.current_coverage:.2f}% |
| **上次覆盖率** | {report.previous_coverage:.2f}% |
| **覆盖率变化** | {'+' if report.coverage_delta >= 0 else ''}{report.coverage_delta:.2f}% |
| **阈值** | {report.threshold}% |
| **达标状态** | {'✅ 已达标' if report.threshold_met else '❌ 未达标'} |

## 📈 趋势分析

{self._generate_trend_section(report.summary.get('trend', {}))}

## 📦 模块覆盖率

{self._generate_module_table(report.modules)}

## 📁 文件覆盖率 (覆盖率最低的20个文件)

{self._generate_file_table(report.files, report.threshold)}

## 🔄 变化统计

{self._generate_changes_section(report.summary.get('changes_summary', {}))}

## 🚨 预警信息

{self._generate_alerts_md(report.alerts)}

## 💡 改进建议

{self._generate_suggestions(report)}

---
*报告由 Coverage Monitor 自动生成*
"""
        return md

    def _generate_trend_section(self, trend: Dict[str, Any]) -> str:
        if trend.get("trend") == "insufficient_data":
            return "暂无足够历史数据进行分析。"

        direction = trend.get("direction", "unknown")
        direction_text = {
            "improving": "📈 上升",
            "declining": "📉 下降",
            "stable": "➡️ 稳定"
        }.get(direction, "❓ 未知")

        return f"""| 趋势指标 | 值 |
|----------|-----|
| **方向** | {direction_text} |
| **斜率** | {trend.get('slope', 0):.4f} |
| **起始覆盖率** | {trend.get('start_coverage', 0):.2f}% |
| **结束覆盖率** | {trend.get('end_coverage', 0):.2f}% |
| **平均覆盖率** | {trend.get('average', 0):.2f}% |
| **最高覆盖率** | {trend.get('max', 0):.2f}% |
| **最低覆盖率** | {trend.get('min', 0):.2f}% |
| **数据点数** | {trend.get('data_points', 0)} |"""

    def _generate_module_table(self, modules: List[ModuleCoverage]) -> str:
        if not modules:
            return "暂无模块数据。"

        rows = ["| 模块 | 行覆盖率 | 分支覆盖率 | 函数覆盖率 | 文件数 | 达标文件 |",
                "|------|----------|------------|------------|--------|----------|"]
        for m in modules:
            rows.append(f"| {m.module_name} | {m.line_rate:.1f}% | {m.branch_rate:.1f}% | {m.function_rate:.1f}% | {m.file_count} | {m.covered_files} |")
        return "\n".join(rows)

    def _generate_file_table(self, files: List[FileCoverageData], threshold: float) -> str:
        if not files:
            return "暂无文件数据。"

        sorted_files = sorted(files, key=lambda f: f.line_rate)[:20]
        rows = ["| 文件 | 模块 | 行覆盖率 | 分支覆盖率 | 函数覆盖率 | 状态 |",
                "|------|------|----------|------------|------------|------|"]
        for f in sorted_files:
            status = "✅" if f.line_rate >= threshold else "⚠️"
            rows.append(f"| `{f.file_path}` | {f.module} | {f.line_rate:.1f}% | {f.branch_rate:.1f}% | {f.function_rate:.1f}% | {status} |")
        return "\n".join(rows)

    def _generate_changes_section(self, changes: Dict[str, int]) -> str:
        return f"""| 变化类型 | 数量 |
|----------|------|
| 📈 覆盖率上升 | {changes.get('increased', 0)} |
| 📉 覆盖率下降 | {changes.get('decreased', 0)} |
| 🆕 新增文件 | {changes.get('new_files', 0)} |
| **总计** | {changes.get('total_changes', 0)} |"""

    def _generate_alerts_md(self, alerts: List[CoverageAlert]) -> str:
        if not alerts:
            return "✅ 无预警信息。"

        lines = []
        for a in alerts[:15]:
            icon = {
                AlertLevel.CRITICAL: "🔴",
                AlertLevel.ERROR: "🟠",
                AlertLevel.WARNING: "🟡",
                AlertLevel.INFO: "🔵"
            }.get(a.alert_level, "⚪")
            lines.append(f"### {icon} [{a.alert_level.value.upper()}] {a.file_path}")
            lines.append(f"- **当前覆盖率**: {a.current_coverage:.1f}%")
            lines.append(f"- **消息**: {a.message}")
            if a.suggestions:
                lines.append(f"- **建议**:")
                for s in a.suggestions[:3]:
                    lines.append(f"  - {s}")
            lines.append("")

        return "\n".join(lines)

    def _generate_suggestions(self, report: CoverageMonitorReport) -> str:
        suggestions = []

        if not report.threshold_met:
            suggestions.append(f"1. 当前覆盖率 {report.current_coverage:.1f}% 未达到阈值 {report.threshold}%，需要增加测试用例")

        if report.coverage_delta < 0:
            suggestions.append(f"2. 覆盖率下降了 {abs(report.coverage_delta):.1f}%，请检查最近的代码变更")

        low_coverage_files = [f for f in report.files if f.line_rate < 50]
        if low_coverage_files:
            suggestions.append(f"3. 有 {len(low_coverage_files)} 个文件覆盖率低于 50%，建议优先处理")

        critical_alerts = report.summary.get('alerts_summary', {}).get('critical', 0)
        if critical_alerts > 0:
            suggestions.append(f"4. 有 {critical_alerts} 个严重预警，需要立即处理")

        if not suggestions:
            suggestions.append("✅ 覆盖率状况良好，继续保持！")

        return "\n".join(suggestions)


class CoverageMonitor:
    """覆盖率监控器主类"""

    def __init__(
        self,
        threshold: float = 80.0,
        warn_threshold: float = 5.0,
        history_days: int = 30,
        logger: Optional[logging.Logger] = None
    ):
        self.threshold = threshold
        self.warn_threshold = warn_threshold
        self.history_days = history_days
        self.logger = logger or logging.getLogger(__name__)

        self.calculator = CoverageCalculator(logger)
        self.change_tracker = CoverageChangeTracker(logger)
        self.alert_manager = CoverageAlertManager(threshold, warn_threshold, logger)
        self.report_generator = ReportGenerator(logger)

        self._current_coverage: Dict[str, FileCoverageData] = {}
        self._previous_coverage: Dict[str, FileCoverageData] = {}
        self._history: List[CoverageHistory] = []

    def monitor(
        self,
        report_path: Path,
        history_path: Optional[Path] = None,
        project: str = "default",
        format_type: Optional[CoverageFormat] = None
    ) -> CoverageMonitorReport:
        """执行覆盖率监控"""
        self.logger.info(f"开始监控覆盖率: {report_path}")

        self._current_coverage = self.calculator.parse_report(report_path, format_type)

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

        alerts = self.alert_manager.check_alerts(self._current_coverage, changes)

        current_line_rate, current_branch_rate, current_function_rate = self.calculator.calculate(self._current_coverage)
        previous_line_rate, _, _ = self.calculator.calculate(self._previous_coverage)

        current_modules = self.calculator.aggregate_by_module(self._current_coverage)
        previous_modules = self.calculator.aggregate_by_module(self._previous_coverage)

        current_history = CoverageHistory(
            timestamp=datetime.now().isoformat(),
            total_line_rate=current_line_rate,
            total_branch_rate=current_branch_rate,
            total_function_rate=current_function_rate,
            file_count=len(self._current_coverage),
            covered_files=sum(1 for f in self._current_coverage.values() if f.line_rate >= self.threshold),
            modules=current_modules,
            files=list(self._current_coverage.values())
        )

        if history_path:
            self.change_tracker.save_history([current_history], history_path)

        trend = self.change_tracker.get_trend(self._history + [current_history])

        summary = self._generate_summary(
            current_line_rate,
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
            modules=current_modules,
            changes=changes,
            alerts=alerts,
            history=self._history[-10:],
            summary=summary
        )

    def _generate_summary(
        self,
        current_rate: float,
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

        return {
            "total_files": len(self._current_coverage),
            "current_coverage": round(current_rate, 2),
            "previous_coverage": round(previous_rate, 2),
            "coverage_delta": round(current_rate - previous_rate, 2),
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
            "health_status": self._determine_health_status(current_rate, critical_alerts, error_alerts)
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

    def save_report(self, report: CoverageMonitorReport, output_path: Path, format_type: str = "json") -> bool:
        """保存报告"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            if format_type == "json":
                content = self.report_generator.generate_json(report)
            elif format_type == "html":
                content = self.report_generator.generate_html(report)
            elif format_type == "markdown":
                content = self.report_generator.generate_markdown(report)
            else:
                content = self.report_generator.generate_json(report)

            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)

            self.logger.info(f"报告已保存到 {output_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存报告失败: {e}")
            return False

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

        trend = summary.get("trend", {})
        if trend.get("trend") == "calculated":
            direction_icons = {
                "improving": "📈",
                "declining": "📉",
                "stable": "➡️"
            }
            icon = direction_icons.get(trend["direction"], "❓")
            print(f"趋势: {icon} {trend['direction']} (斜率: {trend['slope']:.4f})")

        if report.modules:
            print(f"\n模块覆盖率:")
            for m in report.modules[:10]:
                print(f"  - {m.module_name}: {m.line_rate:.1f}% ({m.file_count} 文件)")

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
                print(f"  - {f.file_path}: {f.line_rate:.1f}%")


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
        description="覆盖率监控器 (增强版)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python coverage_monitor.py --report coverage.xml
  python coverage_monitor.py --report coverage.json --threshold 80
  python coverage_monitor.py --report coverage-final.json --format istanbul
  python coverage_monitor.py --report lcov.info --history-days 30 --output html
        """
    )

    parser.add_argument(
        "--report",
        type=str,
        required=True,
        help="覆盖率报告文件路径"
    )

    parser.add_argument(
        "--format",
        type=str,
        choices=["coverage_xml", "coverage_json", "istanbul", "lcov"],
        help="覆盖率报告格式 (自动检测时无需指定)"
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
        choices=["console", "json", "html", "markdown"],
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
    print("覆盖率监控器 (增强版)")
    print("=" * 80)

    format_type = CoverageFormat(args.format) if args.format else None

    monitor = CoverageMonitor(
        threshold=args.threshold,
        warn_threshold=args.warn_threshold,
        history_days=args.history_days,
        logger=logger
    )

    report_path = Path(args.report)
    history_path = Path(args.history_file) if args.history_file else None

    report = monitor.monitor(report_path, history_path, args.project, format_type)

    if args.output == "console":
        monitor.print_report(report)

    if args.output in ["json", "html", "markdown"] or args.output_file:
        output_format = args.output if args.output in ["json", "html", "markdown"] else "json"

        if args.output_file:
            output_path = Path(args.output_file)
        else:
            ext = {"json": ".json", "html": ".html", "markdown": ".md"}[output_format]
            output_path = Path(f"coverage_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}")

        monitor.save_report(report, output_path, output_format)
        print(f"\n报告已保存到: {output_path}")

    return 0 if report.threshold_met else 1


if __name__ == "__main__":
    sys.exit(main())
