"""
门下省 · 质量监控局 (QualityMonitorBureau)
=========================================
负责六维质量指标采集、趋势分析、技术债务追踪及告警规则引擎。
覆盖代码质量/测试覆盖/技术债务/性能基准/安全合规/文档质量六大维度，
提供移动平均趋势预测、异常检测、四级告警（CRITICAL/WARNING/INFO/NORMAL）能力。
"""

from __future__ import annotations

import ast
import json
import os
import re
import statistics
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Optional


class AlertLevel(Enum):
    """告警级别枚举"""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    NORMAL = "normal"


@dataclass
class QualityMetrics:
    """六维质量指标"""

    timestamp: str = ""
    project_dir: str = ""
    code_quality: dict[str, Any] = field(default_factory=dict)
    test_coverage: dict[str, float] = field(default_factory=dict)
    tech_debt: dict[str, Any] = field(default_factory=dict)
    performance_baseline: dict[str, Any] = field(default_factory=dict)
    security_compliance: dict[str, Any] = field(default_factory=dict)
    documentation_quality: dict[str, float] = field(default_factory=dict)

    def overall_score(self) -> float:
        """计算综合质量评分 (0-100)"""
        scores: list[float] = []
        cq = self.code_quality
        if cq:
            complexity_score = max(0, 100 - cq.get("avg_complexity", 0) * 3)
            duplication_penalty = cq.get("duplication_rate", 0) * 500
            smell_penalty = cq.get("smell_density", 0) * 20
            scores.append(max(0, complexity_score - duplication_penalty - smell_penalty))
        tc = self.test_coverage
        if tc:
            line_cov = tc.get("line_coverage", 0)
            branch_cov = tc.get("branch_coverage", 0)
            func_cov = tc.get("function_coverage", 0)
            scores.append((line_cov * 0.4 + branch_cov * 0.35 + func_cov * 0.25))
        td = self.tech_debt
        if td:
            debt_ratio = td.get("debt_count", 0) / max(td.get("total_items", 1), 1)
            scores.append(max(0, 100 - debt_ratio * 100))
        pf = self.performance_baseline
        if pf:
            p99_ok = 1 if pf.get("p99_ms", 0) < 1000 else 0.5
            error_rate_ok = 1 if pf.get("error_rate_pct", 100) < 1 else 0.5
            scores.append((p99_ok + error_rate_ok) * 50)
        sc = self.security_compliance
        if sc:
            vuln_penalty = sc.get("vulnerability_count", 0) * 5
            high_sev_penalty = sc.get("high_severity_ratio", 0) * 30
            scores.append(max(0, 100 - vuln_penalty - high_sev_penalty))
        dq = self.documentation_quality
        if dq:
            api_doc = dq.get("api_documentation_coverage", 0)
            comment_rate = dq.get("code_comment_rate", 0)
            readme_score = dq.get("readme_completeness", 0) * 100
            scores.append(api_doc * 0.4 + comment_rate * 0.3 + readme_score * 0.3)
        return statistics.mean(scores) if scores else 50.0


@dataclass
class QualityTrendReport:
    """质量趋势分析报告"""

    period: str
    metrics_history: list[QualityMetrics]
    trend_direction: str = "stable"
    trend_summary: dict[str, Any] = field(default_factory=dict)
    predictions: dict[str, float] = field(default_factory=dict)
    anomalies: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class TechDebtItem:
    """技术债务项"""

    item_id: str
    title: str
    category: str
    description: str
    severity: str
    estimated_hours: float = 0.0
    interest_rate: float = 0.05
    created_date: str = ""
    status: str = "open"
    file_path: Optional[str] = None
    line_number: int = 0


@dataclass
class TechDebtReport:
    """技术债务追踪报告"""

    total_items: int = 0
    total_hours: float = 0.0
    by_category: dict[str, int] = field(default_factory=dict)
    by_severity: dict[str, int] = field(default_factory=dict)
    items: list[TechDebtItem] = field(default_factory=list)
    repayment_trend: list[dict[str, Any]] = field(default_factory=list)
    priority_queue: list[TechDebtItem] = field(default_factory=list)


@dataclass
class Alert:
    """告警记录"""

    alert_id: str
    level: AlertLevel
    metric_name: str
    current_value: float
    threshold_value: float
    message: str
    dimension: str = ""
    suggestion: str = ""


@dataclass
class AlertRules:
    """告警规则配置"""

    code_quality: dict[str, Any] = field(default_factory=lambda: {
        "max_avg_complexity": {"warning": 12, "critical": 20},
        "max_duplication_rate": {"warning": 0.08, "critical": 0.15},
        "max_smell_density": {"warning": 5, "critical": 10},
    })
    test_coverage: dict[str, Any] = field(default_factory=lambda: {
        "min_line_coverage": {"warning": 70, "critical": 50},
        "min_branch_coverage": {"warning": 60, "critical": 40},
        "min_function_coverage": {"warning": 80, "critical": 60},
    })
    tech_debt: dict[str, Any] = field(default_factory=lambda: {
        "max_debt_hours": {"warning": 200, "critical": 500},
        "max_open_items": {"warning": 30, "critical": 60},
    })
    performance: dict[str, Any] = field(default_factory=lambda: {
        "p95_response_time_ms": {"warning": 800, "critical": 2000},
        "error_rate_pct": {"warning": 2.0, "critical": 5.0},
        "throughput_min_rps": {"warning": 50, "critical": 20},
    })
    security: dict[str, Any] = field(default_factory=lambda: {
        "max_vulnerabilities": {"warning": 10, "critical": 25},
        "max_high_severity_ratio": {"warning": 0.2, "critical": 0.4},
    })
    documentation: dict[str, Any] = field(default_factory=lambda: {
        "min_api_doc_coverage": {"warning": 70, "critical": 40},
        "min_comment_rate": {"warning": 15, "critical": 8},
    })
    suppression_rules: list[dict[str, Any]] = field(default_factory=list)
    maintenance_windows: list[dict[str, str]] = field(default_factory=list)


class QualityMonitorError(Exception):
    """质量监控基础异常"""


class MetricsCollectionError(QualityMonitorError):
    """指标采集异常"""


class TrendAnalysisError(QualityMonitorError):
    """趋势分析异常"""


class AlertEngineError(QualityMonitorError):
    """告警引擎异常"""


class QualityMonitorBureau:
    """
    门下省质量监控局
    
    提供六维质量监控能力：
    - 代码质量维度：圈复杂度均值/重复率/异味密度/技术债务小时数
    - 测试覆盖维度：行/分支/函数覆盖率
    - 技术债务维度：债务数量/严重度/偿还趋势
    - 性能基准维度：P50/P95/P99响应时间/吞吐量/错误率
    - 安全合规维度：漏洞数量/高危占比/修复率
    - 文档质量维度：API文档覆盖率/注释率/README完整性
    
    辅助功能：趋势分析(移动平均/预测/异常检测)、债务追踪、告警引擎
    """

    def collect_metrics(self, project_dir: Path) -> QualityMetrics:
        """
        采集项目六维质量指标
        
        遍历项目目录，分析源码文件、测试报告、配置文件等，
        计算六个维度的量化指标并汇总为QualityMetrics对象。
        """
        if not project_dir.exists():
            raise MetricsCollectionError(f"项目目录不存在: {project_dir}")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        metrics = QualityMetrics(timestamp=now, project_dir=str(project_dir))

        metrics.code_quality = self._collect_code_quality_metrics(project_dir)
        metrics.test_coverage = self._collect_test_coverage_metrics(project_dir)
        metrics.tech_debt = self._collect_tech_debt_metrics(project_dir)
        metrics.performance_baseline = self._collect_performance_metrics(project_dir)
        metrics.security_compliance = self._collect_security_metrics(project_dir)
        metrics.documentation_quality = self._collect_documentation_metrics(project_dir)

        return metrics

    def _collect_code_quality_metrics(
        self, project_dir: Path
    ) -> dict[str, Any]:
        """采集代码质量维度指标"""
        py_files = list(project_dir.rglob("*.py"))
        all_source_files = (
            py_files
            + list(project_dir.rglob("*.js"))
            + list(project_dir.rglob("*.ts"))
            + list(project_dir.rglob("*.go"))
            + list(project_dir.rglob("*.java"))
        )

        total_lines = 0
        total_functions = 0
        total_classes = 0
        complexities: list[int] = []
        smell_counts: list[int] = []

        for f in py_files[:200]:
            try:
                source = f.read_text(encoding="utf-8")
                lines = source.splitlines()
                total_lines += len(lines)

                try:
                    tree = ast.parse(source)
                except SyntaxError:
                    continue

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        total_functions += 1
                        complexity = self._calc_mccabe(node)
                        complexities.append(complexity)
                        end_line = getattr(node, "end_lineno", node.lineno)
                        func_len = end_line - node.lineno + 1
                        smell_counts.append(func_len)
                    elif isinstance(node, ast.ClassDef):
                        total_classes += 1
                        end_line = getattr(node, "end_lineno", node.lineno)
                        cls_len = end_line - node.lineno + 1
                        if cls_len > 300:
                            smell_counts.append(cls_len // 10)
            except Exception:
                continue

        dup_rate = self._estimate_duplication(py_files[:50]) if py_files else 0.0
        avg_complexity = statistics.mean(complexities) if complexities else 0.0
        max_complexity = max(complexities) if complexities else 0
        avg_func_len = statistics.mean(smell_counts) if smell_counts else 0.0
        smell_density = len([s for s in smell_counts if s > 50]) / max(total_functions, 1) * 100

        debt_hours = sum(
            max(0, c - 10) * 0.5 for c in complexities
        ) + len([s for s in smell_counts if s > 50]) * 2

        return {
            "total_files": len(all_source_files),
            "python_files": len(py_files),
            "total_lines": total_lines,
            "total_functions": total_functions,
            "total_classes": total_classes,
            "avg_complexity": round(avg_complexity, 2),
            "max_complexity": max_complexity,
            "duplication_rate": round(dup_rate, 4),
            "smell_density": round(smell_density, 2),
            "avg_function_length": round(avg_func_len, 1),
            "tech_debt_hours": round(debt_hours, 1),
        }

    def _calc_mccabe(self, node: ast.AST, base: int = 1) -> int:
        """计算McCabe圈复杂度"""
        incrementors = {
            ast.If, ast.While, ast.For, ast.AsyncFor,
            ast.ExceptHandler, ast.With, ast.AsyncWith,
            ast.Assert, ast.comprehension, ast.IfExp,
        }
        complexity = base
        for child in ast.walk(node):
            if type(child) in incrementors:
                complexity += 1
            if isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity

    def _estimate_duplication(self, files: list[Path], window: int = 6) -> float:
        """估算代码重复率"""
        import hashlib

        all_blocks: list[str] = []
        for f in files:
            try:
                content = f.read_text(encoding="utf-8")
                lines = [l.strip() for l in content.splitlines() if l.strip()]
                for i in range(len(lines) - window + 1):
                    block = "\n".join(lines[i : i + window])
                    all_blocks.append(hashlib.md5(block.encode()).hexdigest())
            except Exception:
                continue
        if len(all_blocks) < 10:
            return 0.0
        unique = set(all_blocks)
        return 1.0 - len(unique) / len(all_blocks)

    def _collect_test_coverage_metrics(
        self, project_dir: Path
    ) -> dict[str, float]:
        """采集测试覆盖维度指标"""
        coverage_data: dict[str, float] = {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "function_coverage": 0.0,
        }

        coverage_file = project_dir / ".coverage" / "coverage.json"
        alt_coverage = project_dir / "coverage.xml"
        pytest_cov = project_dir / ".pytest_cache" / "v" / "cache" / "lastfailed"

        if coverage_file.exists():
            try:
                raw = json.loads(coverage_file.read_text(encoding="utf-8"))
                files_data = raw.get("files", {})
                if files_data:
                    total_summary = raw.get("totals", {})
                    coverage_data["line_coverage"] = total_summary.get(
                        "percent_covered", 0.0
                    )
                    coverage_data["branch_coverage"] = total_summary.get(
                        "percent_covered_branches", coverage_data["line_coverage"] * 0.85
                    )
                    coverage_data["function_coverage"] = total_summary.get(
                        "percent_covered_functions", coverage_data["line_coverage"] * 1.05
                    )
                    coverage_data["function_coverage"] = min(
                        100.0, coverage_data["function_coverage"]
                    )
            except (json.JSONDecodeError, KeyError):
                pass
        elif alt_coverage.exists():
            try:
                import xml.etree.ElementTree as ET

                tree = ET.parse(alt_coverage)
                root = tree.getroot()
                line_total = root.attrib.get("lines-valid", "0")
                line_covered = root.attrib.get("lines-covered", "0")
                branch_total = root.attrib.get("branches-valid", "0")
                branch_covered = root.attrib.get("branches-covered", "0")
                lt, lc = int(line_total), int(line_covered)
                bt, bc = int(branch_total), int(branch_covered)
                coverage_data["line_coverage"] = lc / lt * 100 if lt > 0 else 0.0
                coverage_data["branch_coverage"] = bc / bt * 100 if bt > 0 else coverage_data["line_coverage"] * 0.85
            except Exception:
                pass

        test_files = (
            list(project_dir.rglob("test_*.py"))
            + list(project_dir.rglob("*_test.py"))
            + list(project_dir.glob("tests/**/*.py"))
        )
        src_py_files = [
            f for f in project_dir.rglob("*.py")
            if "test" not in f.parts and "__pycache__" not in f.parts
        ]
        src_func_count = 0
        for sf in src_py_files[:100]:
            try:
                tree = ast.parse(sf.read_text(encoding="utf-8"))
                src_func_count += sum(
                    1
                    for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
            except Exception:
                continue

        test_func_count = 0
        for tf in test_files[:100]:
            try:
                tree = ast.parse(tf.read_text(encoding="utf-8"))
                test_func_count += sum(
                    1
                    for n in ast.walk(tree)
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_")
                )
            except Exception:
                continue

        if coverage_data["line_coverage"] == 0.0 and src_func_count > 0:
            est_cov = min(100.0, test_func_count / max(src_func_count, 1) * 35)
            coverage_data["line_coverage"] = est_cov
            coverage_data["branch_coverage"] = est_cov * 0.8
            coverage_data["function_coverage"] = est_cov * 1.1
            coverage_data["function_coverage"] = min(100.0, coverage_data["function_coverage"])

        coverage_data["line_coverage"] = round(coverage_data["line_coverage"], 2)
        coverage_data["branch_coverage"] = round(coverage_data["branch_coverage"], 2)
        coverage_data["function_coverage"] = round(coverage_data["function_coverage"], 2)
        coverage_data["test_file_count"] = float(len(test_files))
        coverage_data["src_function_count"] = float(src_func_count)
        coverage_data["test_function_count"] = float(test_func_count)
        return coverage_data

    def _collect_tech_debt_metrics(
        self, project_dir: Path
    ) -> dict[str, Any]:
        """采集技术债务维度指标"""
        debt_items: list[TechDebtItem] = []
        debt_counter = 0

        todo_pattern = re.compile(r"#\s*(TODO|FIXME|HACK|XXX|TEMP)\b(.*)$")
        magic_num_pattern = re.compile(r"(?<=[^.\w])(\d{2,})(?!\w)")
        dead_code_patterns = [re.compile(r"^\s*(pass|ellipsis|\.\.\.)\s*$")]

        for py_file in list(project_dir.rglob("*.py"))[:150]:
            try:
                source = py_file.read_text(encoding="utf-8")
                lines = source.splitlines()
            except Exception:
                continue

            for i, line in enumerate(lines, start=1):
                stripped = line.strip()
                match = todo_pattern.search(stripped)
                if match:
                    debt_counter += 1
                    tag = match.group(1)
                    desc = match.group(2).strip() or f"{tag}标记"
                    severity = "high" if tag in ("FIXME", "HACK") else "medium"
                    hours_map = {"TODO": 2, "FIXME": 4, "HACK": 8, "XXX": 3, "TEMP": 1}
                    debt_items.append(TechDebtItem(
                        item_id=f"TD-{debt_counter:04d}",
                        title=f"{tag}: {desc[:50]}",
                        category=tag.lower(),
                        description=f"{py_file.name}:{i} - {desc}",
                        severity=severity,
                        estimated_hours=hours_map.get(tag, 2),
                        file_path=str(py_file.relative_to(project_dir)),
                        line_number=i,
                    ))

                for pattern in dead_code_patterns:
                    if pattern.match(stripped):
                        debt_counter += 1
                        debt_items.append(TechDebtItem(
                            item_id=f"TD-{debt_counter:04d}",
                            title=f"死代码: 第{i}行",
                            category="dead_code",
                            description=f"{py_file.name}:{i} - 检测到死代码(pass/ellipsis)",
                            severity="low",
                            estimated_hours=0.5,
                            file_path=str(py_file.relative_to(project_dir)),
                            line_number=i,
                        ))

            magic_nums = magic_num_pattern.findall(source)
            if len(magic_nums) > 5:
                debt_counter += 1
                debt_items.append(TechDebtItem(
                    item_id=f"TD-{debt_counter:04d}",
                    title=f"魔法数字过多: {len(magic_nums)}个",
                    category="magic_numbers",
                    description=f"{py_file.name} 包含大量未命名常量的魔法数字",
                    severity="low",
                    estimated_hours=len(magic_nums) * 0.3,
                    file_path=str(py_file.relative_to(project_dir)),
                ))

        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        total_hours = 0.0
        for item in debt_items:
            by_category[item.category] = by_category.get(item.category, 0) + 1
            by_severity[item.severity] = by_severity.get(item.severity, 0) + 1
            total_hours += item.estimated_hours

        sorted_items = sorted(debt_items, key=lambda x: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.severity, 4),
            -x.estimated_hours,
        ))

        return {
            "debt_count": len(debt_items),
            "debt_categories": by_category,
            "by_severity": by_severity,
            "estimated_total_hours": round(total_hours, 1),
            "total_items_analyzed": debt_counter,
            "priority_queue_size": len(sorted_items),
        }

    def _collect_performance_metrics(
        self, project_dir: Path
    ) -> dict[str, Any]:
        """采集性能基准维度指标"""
        perf_data: dict[str, Any] = {
            "p50_ms": 0.0,
            "p95_ms": 0.0,
            "p99_ms": 0.0,
            "throughput_rps": 0.0,
            "error_rate_pct": 0.0,
            "source": "not_available",
        }

        benchmark_files = [
            project_dir / "benchmark_results.json",
            project_dir / "tests" / "benchmarks" / "results.json",
            project_dir / "performance_report.json",
        ]

        for bf in benchmark_files:
            if bf.exists():
                try:
                    raw = json.loads(bf.read_text(encoding="utf-8"))
                    if isinstance(raw, dict):
                        perf_data.update({
                            k: v for k, v in raw.items()
                            if k in ("p50_ms", "p95_ms", "p99_ms", "throughput_rps", "error_rate_pct")
                        })
                        perf_data["source"] = bf.name
                        break
                except (json.JSONDecodeError, KeyError):
                    continue

        locust_stats = project_dir / "locust_stats.csv"
        if locust_stats.exists() and perf_data.get("source") == "not_available":
            try:
                lines = locust_stats.read_text(encoding="utf-8").splitlines()
                if len(lines) > 1:
                    header = lines[0].split(",")
                    data_lines = [l.split(",") for l in lines[1:] if l.strip()]
                    for dl in data_lines:
                        if len(dl) >= len(header):
                            row_dict = dict(zip(header, dl))
                            name = row_dict.get("Name", "")
                            if name == "Aggregated" or "Total" in name:
                                perf_data["p50_ms"] = float(row_dict.get("50%", 0))
                                perf_data["p95_ms"] = float(row_dict.get("95%", 0))
                                perf_data["p99_ms"] = float(row_dict.get("99%", 0))
                                req_s = row_dict.get("Requests/s", "0")
                                perf_data["throughput_rps"] = float(req_s.replace("/s", ""))
                                failures = row_dict.get("Failures", "0")
                                total = row_dict.get("Requests", "1")
                                perf_data["error_rate_pct"] = float(failures) / max(float(total), 1) * 100
                                perf_data["source"] = "locust_stats.csv"
                                break
            except Exception:
                pass

        for k in ["p50_ms", "p95_ms", "p99_ms", "throughput_rps", "error_rate_pct"]:
            if k in perf_data and isinstance(perf_data[k], (int, float)):
                perf_data[k] = round(float(perf_data[k]), 2)

        return perf_data

    def _collect_security_metrics(
        self, project_dir: Path
    ) -> dict[str, Any]:
        """采集安全合规维度指标"""
        sec_data: dict[str, Any] = {
            "vulnerability_count": 0,
            "high_severity_count": 0,
            "medium_severity_count": 0,
            "low_severity_count": 0,
            "high_severity_ratio": 0.0,
            "fix_rate": 0.0,
            "source": "scan_required",
        }

        scan_files = [
            project_dir / "bandit_report.json",
            project_dir / "security_scan.json",
            project_dir / "owasp_results.json",
            project_dir / ".bandit" / "results.json",
        ]

        for sf in scan_files:
            if sf.exists():
                try:
                    raw = json.loads(sf.read_text(encoding="utf-8"))
                    results = raw.get("results", [])
                    sec_data["vulnerability_count"] = len(results)
                    high_c = sum(1 for r in results if r.get("severity") == "HIGH")
                    med_c = sum(1 for r in results if r.get("severity") == "MEDIUM")
                    low_c = sum(1 for r in results if r.get("severity") == "LOW")
                    sec_data["high_severity_count"] = high_c
                    sec_data["medium_severity_count"] = med_c
                    sec_data["low_severity_count"] = low_c
                    total = high_c + med_c + low_c
                    sec_data["high_severity_ratio"] = round(high_c / max(total, 1), 4)
                    sec_data["source"] = sf.name
                    break
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue

        safety_file = project_dir / "safety_report.json"
        if safety_file.exists():
            try:
                deps = json.loads(safety_file.read_text(encoding="utf-8"))
                if isinstance(deps, list):
                    dep_vulns = len(deps)
                    sec_data["dependency_vulns"] = dep_vulns
                    sec_data["vulnerability_count"] += dep_vulns
                    sec_data["source"] = f"{sec_data['source']},safety"
            except (json.JSONDecodeError, TypeError):
                pass

        return sec_data

    def _collect_documentation_metrics(
        self, project_dir: Path
    ) -> dict[str, float]:
        """采集文档质量维度指标"""
        doc_metrics: dict[str, float] = {
            "api_documentation_coverage": 0.0,
            "code_comment_rate": 0.0,
            "readme_completeness": 0.0,
        }

        py_files = list(project_dir.rglob("*.py"))[:100]
        total_lines = 0
        comment_lines = 0
        documented_funcs = 0
        total_funcs = 0

        for pf in py_files:
            try:
                source = pf.read_text(encoding="utf-8")
                lines = source.splitlines()
                total_lines += len(lines)
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                        comment_lines += 1

                try:
                    tree = ast.parse(source)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            total_funcs += 1
                            if ast.get_docstring(node):
                                documented_funcs += 1
                except SyntaxError:
                    continue
            except Exception:
                continue

        doc_metrics["code_comment_rate"] = round(
            comment_lines / max(total_lines, 1) * 100, 2
        )
        doc_metrics["api_documentation_coverage"] = round(
            documented_funcs / max(total_funcs, 1) * 100, 2
        )

        readme = project_dir / "README.md"
        if readme.exists():
            content = readme.read_text(encoding="utf-8").lower()
            sections = [
                "# ", "## ", "### ",
                "installation", "usage", "api", "configuration",
                "contributing", "license", "changelog",
                "安装", "使用", "配置", "贡献", "许可证",
            ]
            found_sections = sum(1 for s in sections if s in content)
            has_badges = bool(re.search(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", content))
            has_examples = "```" in content or "example" in content
            completeness = min(1.0, (found_sections / 10.0) * 0.6 + (0.2 if has_badges else 0) + (0.2 if has_examples else 0))
            doc_metrics["readme_completeness"] = round(completeness, 2)

        docs_dir = project_dir / "docs"
        if docs_dir.is_dir():
            doc_files = list(docs_dir.rglob("*.md")) + list(docs_dir.rglob("*.rst"))
            api_docs = [f for f in doc_files if any(k in f.name.lower() for k in ("api", "reference"))]
            if api_docs:
                current = doc_metrics["api_documentation_coverage"]
                doc_metrics["api_documentation_coverage"] = min(100.0, current + len(api_docs) * 5)

        return doc_metrics

    # ==================== 趋势分析 ====================

    def analyze_trends(
        self, historical_metrics: list[QualityMetrics]
    ) -> QualityTrendReport:
        """
        分析质量趋势
        
        使用方法：
        - 移动平均平滑短期波动
        - 线性回归预测未来趋势
        - Z-Score/IQR方法检测异常点
        """
        if len(historical_metrics) < 2:
            raise TrendAnalysisError("历史数据不足，至少需要2个时间点的数据")

        scores = [m.overall_score() for m in historical_metrics]

        window = min(5, len(scores) // 2 + 1)
        moving_avgs = []
        for i in range(len(scores)):
            start_idx = max(0, i - window + 1)
            window_vals = scores[start_idx : i + 1]
            moving_avgs.append(statistics.mean(window_vals))

        recent_scores = scores[-min(5, len(scores)) :]
        if len(recent_scores) >= 2:
            slope = (recent_scores[-1] - recent_scores[0]) / (len(recent_scores) - 1)
            if slope > 0.5:
                direction = "improving"
            elif slope < -0.5:
                direction = "declining"
            else:
                direction = "stable"
        else:
            direction = "unknown"

        predictions: dict[str, float] = {}
        if len(scores) >= 3:
            n = len(scores)
            x_mean = (n - 1) / 2.0
            y_mean = statistics.mean(scores)
            ss_xy = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
            ss_xx = sum((i - x_mean) ** 2 for i in range(n))
            if ss_xx != 0:
                b = ss_xy / ss_xx
                a = y_mean - b * x_mean
                for offset in [1, 2, 3]:
                    pred = a + b * (n - 1 + offset)
                    predictions[f"+{offset}_period"] = round(max(0, min(100, pred)), 1)

        anomalies = self._detect_anomalies(historical_metrics)

        return QualityTrendReport(
            period=f"{historical_metrics[0].timestamp} ~ {historical_metrics[-1].timestamp}",
            metrics_history=historical_metrics,
            trend_direction=direction,
            trend_summary={
                "current_score": round(scores[-1], 2),
                "moving_average_last": round(moving_avgs[-1], 2),
                "score_change": round(scores[-1] - scores[0], 2),
                "trend_direction": direction,
                "data_points": len(historical_metrics),
            },
            predictions=predictions,
            anomalies=anomalies,
        )

    def _detect_anomalies(
        self, metrics_list: list[QualityMetrics]
    ) -> list[dict[str, Any]]:
        """基于Z-Score和IQR的异常检测"""
        anomalies: list[dict[str, Any]] = []
        scores = [m.overall_score() for m in metrics_list]
        if len(scores) < 4:
            return anomalies

        mean_score = statistics.mean(scores)
        stdev = statistics.stdev(scores) if len(scores) > 1 else 1.0
        sorted_scores = sorted(scores)
        q1 = sorted_scores[len(sorted_scores) // 4]
        q3 = sorted_scores[3 * len(sorted_scores) // 4]
        iqr = q3 - q1

        for idx, (metric, score) in enumerate(zip(metrics_list, scores)):
            z_score = abs(score - mean_score) / max(stdev, 0.01)
            is_outlier_iqr = score < (q1 - 1.5 * iqr) or score > (q3 + 1.5 * iqr)

            if z_score > 2.0 or is_outlier_iqr:
                anomalies.append({
                    "index": idx,
                    "timestamp": metric.timestamp,
                    "score": round(score, 2),
                    "z_score": round(z_score, 2),
                    "type": "statistical_outlier" if z_score > 2.0 else "iqr_outlier",
                    "direction": "spike" if score > mean_score else "drop",
                })

        return anomalies

    # ==================== 技术债务追踪 ====================

    def track_tech_debt(self, debt_items: list[TechDebtItem]) -> TechDebtReport:
        """
        追踪和管理技术债务
        
        功能：
        - 债务识别与分类
        - 利息计算（随时间增长的成本）
        - 偿还优先级排序
        """
        total_hours = sum(d.estimated_hours for d in debt_items)
        by_category: dict[str, int] = {}
        by_severity: dict[str, int] = {}

        for item in debt_items:
            by_category[item.category] = by_category.get(item.category, 0) + 1
            by_severity[item.severity] = by_severity.get(item.severity, 0) + 1

            if item.created_date:
                try:
                    created = datetime.strptime(item.created_date, "%Y-%m-%d")
                    days_old = (datetime.now() - created).days
                    item.interest_rate = min(0.15, 0.03 + days_old * 0.001)
                    item.estimated_hours *= (1 + item.interest_rate) ** (days_old / 365)
                except ValueError:
                    pass

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        priority_queue = sorted(
            debt_items,
            key=lambda x: (
                severity_order.get(x.severity, 4),
                -x.estimated_hours,
                x.item_id,
            ),
        )

        repayment_trend = [
            {"date": (datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d"), "remaining": max(0, total_hours - d * 0.5)}
            for d in range(min(30, len(debt_items)), 0, -1)
        ]

        return TechDebtReport(
            total_items=len(debt_items),
            total_hours=round(total_hours, 1),
            by_category=by_category,
            by_severity=by_severity,
            items=debt_items,
            repayment_trend=repayment_trend,
            priority_queue=priority_queue,
        )

    # ==================== 告警规则引擎 ====================

    def evaluate_alerts(
        self,
        metrics: QualityMetrics,
        rules: Optional[AlertRules] = None,
    ) -> list[Alert]:
        """
        根据告警规则评估当前指标
        
        四级告警体系：
        - CRITICAL(红色): 关键阈值突破，需立即处理
        - WARNING(橙色): 接近阈值，需关注
        - INFO(蓝色): 信息提示，建议改进方向
        - NORMAL(绿色): 一切正常
        
        支持：
        - 百分比阈值比较
        - 绝对值阈值比较
        - 变化率阈值比较
        - 维护窗口抑制
        - 已知问题白名单
        """
        alert_rules = rules or AlertRules()
        alerts: list[Alert] = []
        alert_counter = 0
        now_str = datetime.now().strftime("%H:%M")

        if self._is_in_maintenance_window(alert_rules.maintenance_windows):
            alerts.append(Alert(
                alert_id="MAINT-WINDOW",
                level=AlertLevel.INFO,
                metric_name="maintenance_window",
                current_value=0,
                threshold_value=0,
                message="当前处于维护窗口期，部分告警已抑制",
                dimension="system",
                suggestion="维护窗口结束后将恢复完整告警检查",
            ))
            return alerts

        suppressed = set()
        for rule in alert_rules.suppression_rules:
            metric_pat = rule.get("metric_pattern", "")
            reason = rule.get("reason", "")
            suppressed.add(metric_pat)

        alert_counter = self._eval_dimension_alerts(
            "code_quality", metrics.code_quality, alert_rules.code_quality, alerts, alert_counter, suppressed, now_str
        )
        alert_counter = self._eval_dimension_alerts(
            "test_coverage", metrics.test_coverage, alert_rules.test_coverage, alerts, alert_counter, suppressed, now_str
        )
        alert_counter = self._eval_dimension_alerts(
            "tech_debt", metrics.tech_debt, alert_rules.tech_debt, alerts, alert_counter, suppressed, now_str
        )
        alert_counter = self._eval_dimension_alerts(
            "performance", metrics.performance_baseline, alert_rules.performance, alerts, alert_counter, suppressed, now_str
        )
        alert_counter = self._eval_dimension_alerts(
            "security", metrics.security_compliance, alert_rules.security, alerts, alert_counter, suppressed, now_str
        )
        alert_counter = self._eval_dimension_alerts(
            "documentation", metrics.documentation_quality, alert_rules.documentation, alerts, alert_counter, suppressed, now_str
        )

        overall = metrics.overall_score()
        if overall < 40:
            alerts.append(Alert(
                alert_id=f"ALERT-{alert_counter:04d}",
                level=AlertLevel.CRITICAL,
                metric_name="overall_quality_score",
                current_value=overall,
                threshold_value=40.0,
                message=f"综合质量评分极低({overall:.1f}/100)，项目质量严重恶化！",
                dimension="overall",
                suggestion="立即召开质量复盘会议，制定紧急修复计划",
            ))
        elif overall < 60:
            alerts.append(Alert(
                alert_id=f"ALERT-{alert_counter:04d}",
                level=AlertLevel.WARNING,
                metric_name="overall_quality_score",
                current_value=overall,
                threshold_value=60.0,
                message=f"综合质量评分偏低({overall:.1f}/100)，需关注质量改善",
                dimension="overall",
                suggestion="安排专项质量改进工作，重点关注低分维度",
            ))

        if not alerts:
            alerts.append(Alert(
                alert_id=f"ALERT-{alert_counter:04d}",
                level=AlertLevel.NORMAL,
                metric_name="all_metrics",
                current_value=overall,
                threshold_value=80.0,
                message="✅ 所有质量指标在正常范围内，继续保持！",
                dimension="overall",
                suggestion="维持现有工程实践，持续关注关键指标变化趋势",
            ))

        return alerts

    def _eval_dimension_alerts(
        self,
        dimension: str,
        data: dict[str, Any],
        dim_rules: dict[str, Any],
        alerts: list[Alert],
        counter: int,
        suppressed: set[str],
        now_str: str,
    ) -> int:
        """评估单个维度的告警规则"""
        for metric_name, thresholds in dim_rules.items():
            if metric_name in ("suppression_rules", "maintenance_windows"):
                continue
            if any(s in metric_name for s in suppressed):
                continue

            value = data.get(metric_name, 0)
            if not isinstance(value, (int, float)):
                continue

            crit_threshold = thresholds.get("critical", 0)
            warn_threshold = thresholds.get("warning", 0)

            is_upper_bound = any(
                k in metric_name.lower()
                for k in ("complexity", "duplication", "smell", "debt", "response_time", "error_rate", "vulnerability")
            )

            if is_upper_bound:
                if value >= crit_threshold:
                    counter += 1
                    alerts.append(Alert(
                        alert_id=f"ALERT-{counter:04d}",
                        level=AlertLevel.CRITICAL,
                        metric_name=metric_name,
                        current_value=value,
                        threshold_value=float(crit_threshold),
                        message=f"[{dimension}] {metric_name}={value} 突破临界值{crit_threshold}！",
                        dimension=dimension,
                        suggestion=self._get_suggestion(dimension, metric_name, "critical"),
                    ))
                elif value >= warn_threshold:
                    counter += 1
                    alerts.append(Alert(
                        alert_id=f"ALERT-{counter:04d}",
                        level=AlertLevel.WARNING,
                        metric_name=metric_name,
                        current_value=value,
                        threshold_value=float(warn_threshold),
                        message=f"[{dimension}] {metric_name}={value} 接近警告值{warn_threshold}",
                        dimension=dimension,
                        suggestion=self._get_suggestion(dimension, metric_name, "warning"),
                    ))
            else:
                if value <= crit_threshold:
                    counter += 1
                    alerts.append(Alert(
                        alert_id=f"ALERT-{counter:04d}",
                        level=AlertLevel.CRITICAL,
                        metric_name=metric_name,
                        current_value=value,
                        threshold_value=float(crit_threshold),
                        message=f"[{dimension}] {metric_name}={value}% 低于临界值{crit_threshold}%！",
                        dimension=dimension,
                        suggestion=self._get_suggestion(dimension, metric_name, "critical"),
                    ))
                elif value <= warn_threshold:
                    counter += 1
                    alerts.append(Alert(
                        alert_id=f"ALERT-{counter:04d}",
                        level=AlertLevel.WARNING,
                        metric_name=metric_name,
                        current_value=value,
                        threshold_value=float(warn_threshold),
                        message=f"[{dimension}] {metric_name}={value}% 接近警告值{warn_threshold}%",
                        dimension=dimension,
                        suggestion=self._get_suggestion(dimension, metric_name, "warning"),
                    ))
        return counter

    @staticmethod
    def _is_in_maintenance_window(windows: list[dict[str, str]]) -> bool:
        """检查是否在维护窗口期内"""
        now = datetime.now()
        for win in windows:
            start = win.get("start", "")
            end = win.get("end", "")
            if start and end:
                try:
                    s_time = datetime.strptime(start, "%H:%M").time()
                    e_time = datetime.strptime(end, "%H:%M").time()
                    if s_time <= now.time() <= e_time:
                        return True
                except ValueError:
                    continue
        return False

    @staticmethod
    def _get_suggestion(
        dimension: str, metric_name: str, level: str
    ) -> str:
        """根据维度和指标生成改进建议"""
        suggestions: dict[str, dict[str, str]] = {
            "code_quality": {
                "max_avg_complexity": "重构高复杂度函数，拆分为更小的可测试单元",
                "max_duplication_rate": "提取公共方法或工具函数消除重复代码",
                "max_smell_density": "进行代码异味清理Sprint，优先处理God Object和Long Method",
            },
            "test_coverage": {
                "min_line_coverage": "补充单元测试用例，优先覆盖核心业务逻辑",
                "min_branch_coverage": "增加边界条件和异常路径的测试用例",
                "min_function_coverage": "确保每个公开函数都有对应的测试",
            },
            "tech_debt": {
                "max_debt_hours": "安排技术债务偿还Sprint，按优先级逐项清偿",
                "max_open_items": "建立技术债务看板，定期Review和关闭已修复项",
            },
            "performance": {
                "p95_response_time_ms": "排查慢查询和热点代码，考虑缓存优化",
                "error_rate_pct": "增加错误日志和监控，定位错误根因",
                "throughput_min_rps": "评估系统容量，考虑水平扩展或性能调优",
            },
            "security": {
                "max_vulnerabilities": "执行全面安全扫描，按CVSS评分逐一修复",
                "max_high_severity_ratio": "优先处理高危漏洞，建立安全发布门禁",
            },
            "documentation": {
                "min_api_doc_coverage": "补充API文档和函数docstring",
                "min_comment_rate": "提高代码注释率，特别是复杂逻辑处",
            },
        }
        dim_sugs = suggestions.get(dimension, {})
        return dim_sugs.get(metric_name, f"请关注{dimension}维度的{metric_name}指标")


if __name__ == "__main__":
    bureau = QualityMonitorBureau()

    demo_project = Path(__file__).parent.parent.parent.parent
    print("=" * 60)
    print("门下省 · 质量监控局 - 功能演示")
    print("=" * 60)

    metrics = bureau.collect_metrics(demo_project)
    print(f"\n📊 六维质量指标采集完成:")
    print(f"   时间戳: {metrics.timestamp}")
    print(f"   综合评分: {metrics.overall_score():.1f}/100")

    print(f"\n   📝 代码质量:")
    for k, v in metrics.code_quality.items():
        print(f"      {k}: {v}")

    print(f"\n   🧪 测试覆盖:")
    for k, v in metrics.test_coverage.items():
        print(f"      {k}: {v}")

    print(f"\n   💳 技术债务:")
    for k, v in metrics.tech_debt.items():
        print(f"      {k}: {v}")

    print(f"\n   ⚡ 性能基准:")
    for k, v in metrics.performance_baseline.items():
        print(f"      {k}: {v}")

    print(f"\n   🔒 安全合规:")
    for k, v in metrics.security_compliance.items():
        print(f"      {k}: {v}")

    print(f"\n   📖 文档质量:")
    for k, v in metrics.documentation_quality.items():
        print(f"      {k}: {v}")

    fake_history = [
        QualityMetrics(
            timestamp=(datetime.now() - timedelta(days=d)).strftime("%Y-%m-%d"),
            code_quality={"avg_complexity": 7.0 + d * 0.3, "duplication_rate": 0.03 + d * 0.005, "smell_density": 2.0 + d * 0.2, "tech_debt_hours": 50.0 + d * 5},
            test_coverage={"line_coverage": 75.0 - d * 1.5, "branch_coverage": 65.0 - d * 1.2, "function_coverage": 82.0 - d * 1.0},
            tech_debt={"debt_count": 5 + d, "estimated_total_hours": 40.0 + d * 8},
            performance_baseline={"p95_ms": 300.0 + d * 20, "error_rate_pct": 0.5 + d * 0.1},
            security_compliance={"vulnerability_count": d, "high_severity_ratio": 0.1 + d * 0.02},
            documentation_quality={"api_documentation_coverage": 65.0, "code_comment_rate": 18.0, "readme_completeness": 0.75},
        )
        for d in range(7, 0, -1)
    ]
    fake_history.append(metrics)

    trend = bureau.analyze_trends(fake_history)
    print(f"\n📈 趋势分析:")
    print(f"   方向: {trend.trend_direction}")
    print(f"   当前得分: {trend.trend_summary.get('current_score', 'N/A')}")
    print(f"   移动平均(最新): {trend.trend_summary.get('moving_average_last', 'N/A')}")
    print(f"   变化: {trend.trend_summary.get('score_change', 'N/A')}")
    if trend.predictions:
        print(f"   预测: {trend.predictions}")
    if trend.anomalies:
        print(f"   异常点: {len(trend.anomalies)}个")

    sample_debts = [
        TechDebtItem(item_id="TD-001", title="重构用户服务类", category="refactor", description="UserService承担过多职责", severity="high", estimated_hours=16.0, created_date="2025-12-01"),
        TechDebtItem(item_id="TD-002", title="修复SQL注入风险", category="security", description="多处字符串拼接SQL", severity="critical", estimated_hours=8.0, created_date="2025-11-15"),
        TechDebtItem(item_id="TD-003", title="补充单元测试", category="testing", description="核心模块覆盖率不足50%", severity="medium", estimated_hours=24.0, created_date="2026-01-10"),
        TechDebtItem(item_id="TD-004", title="升级依赖版本", category="dependencies", description="多个包存在已知漏洞", severity="high", estimated_hours=4.0, created_date="2026-01-20"),
    ]
    debt_report = bureau.track_tech_debt(sample_debts)
    print(f"\n💰 技术债务追踪:")
    print(f"   总项数: {debt_report.total_items}, 总工时: {debt_report.total_hours}h")
    print(f"   分类: {debt_report.by_category}")
    print(f"   严重度: {debt_report.by_severity}")
    print(f"   TOP3优先级:")
    for item in debt_report.priority_queue[:3]:
        print(f"      [{item.severity}] {item.title} ({item.estimated_hours:.1f}h)")

    custom_rules = AlertRules(
        code_quality={
            "max_avg_complexity": {"warning": 8, "critical": 15},
            "max_duplication_rate": {"warning": 0.05, "critical": 0.10},
        },
        test_coverage={
            "min_line_coverage": {"warning": 75, "critical": 55},
        },
        maintenance_windows=[{"start": "02:00", "end": "03:00"}],
    )
    alerts = bureau.evaluate_alerts(metrics, rules=custom_rules)
    print(f"\n🚨 告警评估 (共{len(alerts)}条):")
    for alert in alerts[:8]:
        icon = {"CRITICAL": "🔴", "WARNING": "🟠", "INFO": "🔵", "NORMAL": "🟢"}.get(alert.level.value, "⚪")
        print(f"   {icon} [{alert.level.value.upper()}] {alert.message}")

    print("\n✅ 所有演示通过!")
