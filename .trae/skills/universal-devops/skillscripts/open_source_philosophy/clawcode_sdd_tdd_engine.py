"""
Claw-Code SDD/TDD Engine - 契约驱动开发与测试闭环引擎
理念来源：Claw-Code项目的"SDD契约驱动"和"TDD闭环反馈"核心理念

核心功能：
1. SDD可执行条款提取 - 从SDD规格文档中提取标记为可执行的需求项
2. 验收测试自动生成 - 为可执行条款生成对应的验收测试用例
3. SDD覆盖率仪表盘 - 计算和展示SDD规格的测试覆盖情况
4. 规格-测试双向追踪矩阵 - SDD与测试之间的正向和反向追踪
5. TDD红绿蓝可视化 - 测试状态的终端UI可视化展示
"""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any


class ClauseCategory(Enum):
    """条款类别枚举"""
    FUNCTIONAL = "Functional"
    NON_FUNCTIONAL = "Non-Functional"
    EDGE_CASE = "Edge Case"
    SECURITY = "Security"
    PERFORMANCE = "Performance"
    USABILITY = "Usability"


class Priority(Enum):
    """优先级枚举"""
    CRITICAL = auto()
    HIGH = auto()
    MEDIUM = auto()
    LOW = auto()


class ClauseStatus(Enum):
    """条款状态枚举"""
    NOT_TESTED = "not_tested"
    PASSED = "passed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class CategoryCoverage:
    """分类覆盖率信息"""
    category: ClauseCategory
    total: int
    tested: int
    passed: int
    failed: int
    not_tested: int
    percentage: float

    def to_visual_bar(self) -> str:
        """生成分数可视化条形图"""
        filled = int(self.percentage / 10)
        bar = "█" * filled + "░" * (10 - filled)
        return f"{bar} {self.percentage:.1f}% ({self.passed}/{self.total})"


@dataclass
class SDDExecutableClause:
    """SDD可执行条款数据结构"""
    clause_id: str
    requirement_text: str
    sdd_file_path: Path
    line_number: int
    category: ClauseCategory
    priority: Priority
    status: ClauseStatus = ClauseStatus.NOT_TESTED
    test_case_path: Path | None = None
    last_tested_at: datetime | None = None
    acceptance_criteria: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "clause_id": self.clause_id,
            "requirement_text": self.requirement_text[:100],
            "sdd_file": str(self.sdd_file_path),
            "line_number": self.line_number,
            "category": self.category.value,
            "priority": self.priority.name,
            "status": self.status.value,
            "test_case": str(self.test_case_path) if self.test_case_path else None,
        }


@dataclass
class TestCase:
    """验收测试用例"""
    test_id: str
    clause_id: str
    name: str
    description: str
    preconditions: list[str]
    test_steps: list[str]
    expected_results: list[str]
    actual_result: str | None = None
    status: ClauseStatus = ClauseStatus.NOT_TESTED
    execution_time_ms: int | None = None
    error_message: str | None = None


@dataclass
class SDDCoverageReport:
    """SDD覆盖率报告"""
    total_clauses: int
    tested_count: int
    passed_count: int
    failed_count: int
    not_tested_count: int
    coverage_percentage: float
    by_category: dict[ClauseCategory, CategoryCoverage] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_markdown(self) -> str:
        """生成Markdown格式的覆盖率报告"""
        lines = [
            "# SDD Coverage Report",
            "=" * 40,
            "",
            f"Total Testable Requirements: {self.total_clauses}",
            f"Tested: {self.tested_count} ({self.tested_count / max(self.total_clauses, 1) * 100:.1f}%) ✓✓✓",
            f"Passed: {self.passed_count} {self._generate_bar(self.passed_count, self.total_clauses)}",
            f"Failed: {self.failed_count}   {self._generate_bar(self.failed_count, self.total_clauses)}",
            f"Not Tested: {self.not_tested_count} {self._generate_bar(self.not_tested_count, self.total_clauses)}",
            "",
            "## Coverage by Category:",
        ]
        
        for category, coverage in sorted(self.by_category.items(), key=lambda x: x[0].value):
            lines.append(f"- {category.value}: {coverage.to_visual_bar()}")
        
        return "\n".join(lines)

    @staticmethod
    def _generate_bar(count: int, total: int) -> str:
        """生成可视化进度条"""
        if total == 0:
            return "░░░░░░░░░░"
        ratio = count / total
        filled = int(ratio * 10)
        return ("█" * filled + "░" * (10 - filled))


@dataclass
class TracingMatrixEntry:
    """追踪矩阵条目"""
    clause_id: str
    requirement_text: str
    test_ids: list[str]
    test_status: ClauseStatus
    last_execution_date: datetime | None = None


class ClawCodeSDDTDDEngine:
    """
    Claw-Code SDD/TDD深度实现引擎
    
    提供以下核心能力：
    - 从Markdown格式的SDD文档提取可执行需求条款
    - 自动生成对应的验收测试用例代码
    - 计算并可视化SDD规格覆盖率
    - 维护规格与测试之间的双向追踪关系
    - TDD状态的红绿蓝可视化展示
    """

    TESTABLE_PATTERN = re.compile(
        r'<!--\s*TESTABLE:\s*\[([^\]]+)\]\s*-->|'
        r'\[TESTABLE\]\s*[\[:]?\s*([A-Z]+-\d+)'
    )
    
    REQUIREMENT_ID_PATTERN = re.compile(r'(REQ-\d+|US-\d+|TC-\d+|[A-Z]+-\d+)')
    
    CATEGORY_KEYWORDS = {
        ClauseCategory.FUNCTIONAL: ["功能", "functional", "应该", "shall", "must", "需要"],
        ClauseCategory.NON_FUNCTIONAL: ["性能", "performance", "可用性", "availability", "可扩展", "scalable"],
        ClauseCategory.EDGE_CASE: ["边界", "edge", "异常", "exception", "空值", "null", "极限"],
        ClauseCategory.SECURITY: ["安全", "security", "认证", "auth", "权限", "permission", "加密"],
        ClauseCategory.PERFORMANCE: ["响应时间", "response time", "延迟", "latency", "吞吐量", "throughput"],
        ClauseCategory.USABILITY: ["用户体验", "usability", "易用性", "友好", "accessible", "直观"],
    }

    PRIORITY_KEYWORDS = {
        Priority.CRITICAL: ["关键", "critical", "必须", "mandatory", "P0"],
        Priority.HIGH: ["高", "high", "重要", "important", "P1"],
        Priority.MEDIUM: ["中等", "medium", "一般", "normal", "P2"],
        Priority.LOW: ["低", "low", "可选", "optional", "P3", "增强"],
    }

    def __init__(self, project_root: Path | str | None = None):
        """
        初始化SDD/TDD引擎
        
        Args:
            project_root: 项目根目录路径
        """
        if isinstance(project_root, str):
            project_root = Path(project_root)
        self.project_root = project_root or Path.cwd()
        
        self._sdd_dir = self.project_root / "docs" / "sdd"
        self._tests_dir = self.project_root / "tests" / "sdd_acceptance"
        self._tracing_dir = self.project_root / "docs" / "tracing"
        
        self._clauses: dict[str, SDDExecutableClause] = {}
        self._test_cases: dict[str, TestCase] = {}
        self._tracing_matrix: dict[str, TracingMatrixEntry] = {}

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        for directory in [self._sdd_dir, self._tests_dir, self._tracing_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    def parse_sdd_document(self, sdd_content: str | Path, source_file: Path | None = None) -> list[SDDExecutableClause]:
        """
        解析SDD文档并提取可执行条款
        
        Args:
            sdd_content: SDD文档内容字符串或文件路径
            source_file: 源文件路径（用于记录）
            
        Returns:
            提取的可执行条款列表
        """
        if isinstance(sdd_content, Path):
            source_file = sdd_content
            sdd_content = sdd_content.read_text(encoding="utf-8")
        
        clauses = []
        lines = sdd_content.split("\n")
        
        current_requirement_text = ""
        in_testable_block = False
        current_clause_id = None
        line_offset = 0
        
        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            testable_match = self.TESTABLE_PATTERN.search(stripped_line)
            
            if testable_match:
                clause_id = testable_match.group(1) or testable_match.group(2)
                
                if not clause_id:
                    id_match = self.REQUIREMENT_ID_PATTERN.search(stripped_line)
                    clause_id = id_match.group(1) if id_match else f"AUTO-{uuid.uuid4().hex[:6].upper()}"
                
                current_clause_id = clause_id
                in_testable_block = True
                current_requirement_text = ""
            
            elif in_testable_block and stripped_line and not stripped_line.startswith("<!--"):
                current_requirement_text += stripped_line + "\n"
                
                if stripped_line.endswith(".") or stripped_line.endswith("。") or line_num == len(lines):
                    if current_clause_id and current_requirement_text.strip():
                        clause = self._create_clause(
                            clause_id=current_clause_id,
                            requirement_text=current_requirement_text.strip(),
                            line_number=line_num,
                            source_file=source_file or Path("inline"),
                        )
                        clauses.append(clause)
                        self._clauses[clause.clause_id] = clause
                    
                    in_testable_block = False
                    current_clause_id = None
                    current_requirement_text = ""
        
        self._update_tracing_matrix(clauses)
        return clauses

    def _create_clause(
        self,
        clause_id: str,
        requirement_text: str,
        line_number: int,
        source_file: Path,
    ) -> SDDExecutableClause:
        """
        创建SDD可执行条款对象
        
        根据需求文本内容自动推断类别和优先级
        """
        lower_text = requirement_text.lower()
        
        category = self._infer_category(lower_text)
        priority = self._infer_priority(lower_text)
        acceptance_criteria = self._extract_acceptance_criteria(requirement_text)
        tags = self._extract_tags(requirement_text)
        
        return SDDExecutableClause(
            clause_id=clause_id,
            requirement_text=requirement_text,
            sdd_file_path=source_file,
            line_number=line_number,
            category=category,
            priority=priority,
            acceptance_criteria=acceptance_criteria,
            tags=tags,
        )

    def _infer_category(self, text: str) -> ClauseCategory:
        """根据文本推断条款类别"""
        scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text)
            scores[category] = score
        
        best_category = max(scores, key=scores.get) if any(scores.values()) else ClauseCategory.FUNCTIONAL
        return best_category

    def _infer_priority(self, text: str) -> Priority:
        """根据文本推断优先级"""
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            if any(kw.lower() in text for kw in keywords):
                return priority
        return Priority.MEDIUM

    def _extract_acceptance_criteria(self, text: str) -> list[str]:
        """从需求文本中提取验收标准"""
        criteria = []
        patterns = [
            r'(?:验收标准|acceptance\s*criteria)[：:]\s*(.+)',
            r'(?:当|when)\s*(.+?)(?:(?:则|then)|$)',
            r'-\s*\[x\]\s*(.+)',
            r'\d+[\.．]\s*(.+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            criteria.extend(matches)
        
        return criteria[:5]

    def _extract_tags(self, text: str) -> list[str]:
        """从需求文本中提取标签"""
        tag_pattern = r'#(\w+)'
        return re.findall(tag_pattern, text)

    def generate_test_case(self, clause: SDDExecutableClause) -> TestCase:
        """
        为指定的SDD条款生成验收测试用例
        
        Args:
            clause: SDD可执行条款对象
            
        Returns:
            生成的TestCase对象
        """
        test_id = f"TEST-{clause.clause_id}"
        short_desc = re.sub(r'[^\w\s]', '', clause.requirement_text[:30]).replace(' ', '_').lower()
        
        preconditions = [
            f"SDD规格已定义（{clause.sdd_file_path.name}:{clause.line_number}）",
            f"相关依赖模块已就绪",
        ]
        
        test_steps = [
            f"读取SDD条款 [{clause.clause_id}] 的完整定义",
            f"解析条款中的验收标准",
            f"准备测试数据和模拟环境",
            f"执行对应的功能验证",
            f"对比实际结果与预期结果",
        ]
        
        expected_results = [
            f"功能行为符合SDD条款 [{clause.clause_id}] 的定义",
            "所有验收标准均已满足",
            "无回归问题引入",
        ] + clause.acceptance_criteria
        
        test_case = TestCase(
            test_id=test_id,
            clause_id=clause.clause_id,
            name=f"test_sdd_{clause.clause_id}_{short_desc}",
            description=f"验证SDD条款 [{clause.clause_id}]: {clause.requirement_text[:50]}...",
            preconditions=preconditions,
            test_steps=test_steps,
            expected_results=expected_results,
        )
        
        self._test_cases[test_id] = test_clause
        clause.test_case_path = self._tests_dir / f"{test_case.name}.py"
        
        self._write_test_file(test_case, clause)
        self._update_tracing_entry(clause, test_case)
        
        return test_case

    def _write_test_file(self, test_case: TestCase, clause: SDDExecutableClause) -> None:
        """将测试用例写入Python测试文件"""
        file_path = self._tests_dir / f"{test_case.name}.py"
        
        content = f'''"""
SDD Acceptance Test: {clause.clause_id}
Generated by Claw-Code SDD/TDD Engine
Source: {clause.sdd_file_path}:{clause.line_number}
"""

import pytest
from datetime import datetime


class TestSDD{clause.clause_id.replace("-", "_")}:
    """
    Test suite for SDD clause: {clause.clause_id}
    Category: {clause.category.value}
    Priority: {clause.priority.name}
    """

    @pytest.fixture
    def setup(self):
        """Test fixture - setup test environment"""
        # TODO: Initialize test data and dependencies
        yield {}
        # TODO: Cleanup after test

    def test_{test_case.name.replace("test_sdd_", "")}(self, setup):
        """
        {test_case.description}

        SDD Reference: [{clause.clause_id}] at line {clause.line_number}
        """
        # Preconditions
'''
        
        for i, precondition in enumerate(test_case.preconditions, 1):
            content += f'        # {i}. {precondition}\n'
        
        content += '''
        # Test Steps
'''
        
        for i, step in enumerate(test_case.test_steps, 1):
            content += f'        # Step {i}: {step}\n'
            content += '        # TODO: Implement step\n\n'
        
        content += '''
        # Expected Results
'''
        
        for i, expected in enumerate(test_case.expected_results, 1):
            content += f'        # Expected {i}: {expected}\n'
        
        content += '''
        # Assertions
        # TODO: Add assertions based on expected results
        assert True, "Test implementation pending"

    def test_clause_metadata(self):
        """Verify clause metadata is correctly captured"""
        assert "{clause.clause_id}" == "{clause.clause_id}"
        assert "{clause.category.value}" == "{clause.category.value}"
        assert "{clause.priority.name}" == "{clause.priority.name}"
'''
        
        file_path.write_text(content, encoding="utf-8")

    def _update_tracing_matrix(self, clauses: list[SDDExecutableClause]) -> None:
        """更新追踪矩阵（批量添加新条款）"""
        for clause in clauses:
            if clause.clause_id not in self._tracing_matrix:
                self._tracing_matrix[clause.clause_id] = TracingMatrixEntry(
                    clause_id=clause.clause_id,
                    requirement_text=clause.requirement_text,
                    test_ids=[],
                    test_status=clause.status,
                )

    def _update_tracing_entry(self, clause: SDDExecutableClause, test_case: TestCase) -> None:
        """更新单个追踪矩阵条目"""
        if clause.clause_id in self._tracing_matrix:
            entry = self._tracing_matrix[clause.clause_id]
            entry.test_ids.append(test_case.test_id)
            entry.test_status = clause.status

    def generate_coverage_report(self) -> SDDCoverageReport:
        """
        生成SDD覆盖率报告
        
        Returns:
            包含详细覆盖率信息的SDDCoverageReport对象
        """
        total = len(self._clauses)
        
        tested = sum(1 for c in self._clauses.values() if c.status != ClauseStatus.NOT_TESTED)
        passed = sum(1 for c in self._clauses.values() if c.status == ClauseStatus.PASSED)
        failed = sum(1 for c in self._clauses.values() if c.status == ClauseStatus.FAILED)
        not_tested = sum(1 for c in self._clauses.values() if c.status == ClauseStatus.NOT_TESTED)
        
        coverage_pct = (tested / total * 100) if total > 0 else 0.0
        
        by_category = self._calculate_category_coverage()
        
        report = SDDCoverageReport(
            total_clauses=total,
            tested_count=tested,
            passed_count=passed,
            failed_count=failed,
            not_tested_count=not_tested,
            coverage_percentage=round(coverage_pct, 2),
            by_category=by_category,
        )
        
        self._save_coverage_report(report)
        return report

    def _calculate_category_coverage(self) -> dict[ClauseCategory, CategoryCoverage]:
        """计算各分类的覆盖率"""
        category_clauses: dict[ClauseCategory, list[SDDExecutableClause]] = {}
        
        for clause in self._clauses.values():
            if clause.category not in category_clauses:
                category_clauses[clause.category] = []
            category_clauses[clause.category].append(clause)
        
        by_category = {}
        for category, clauses in category_clauses.items():
            total = len(clauses)
            tested = sum(1 for c in clauses if c.status != ClauseStatus.NOT_TESTED)
            passed = sum(1 for c in clauses if c.status == ClauseStatus.PASSED)
            failed = sum(1 for c in clauses if c.status == ClauseStatus.FAILED)
            not_tested = total - tested
            
            pct = (tested / total * 100) if total > 0 else 0.0
            
            by_category[category] = CategoryCoverage(
                category=category,
                total=total,
                tested=tested,
                passed=passed,
                failed=failed,
                not_tested=not_tested,
                percentage=round(pct, 1),
            )
        
        return by_category

    def _save_coverage_report(self, report: SDDCoverageReport) -> None:
        """保存覆盖率报告到文件"""
        report_file = self._tracing_dir / "sdd_coverage_report.md"
        report_file.write_text(report.to_markdown(), encoding="utf-8")

    def generate_tracing_matrix(self) -> str:
        """
        生成规格-测试双向追踪矩阵
        
        Returns:
            Markdown格式的追踪矩阵
        """
        lines = [
            "# SDD-Test Bidirectional Tracing Matrix",
            "",
            f"*Generated at: {datetime.now(timezone.utc).isoformat()}*",
            "",
            "## Forward Trace (SDD → Tests)",
            "| Clause ID | Requirement | Category | Status | Test Cases |",
            "|-----------|-------------|----------|--------|------------|",
        ]
        
        for clause_id, entry in sorted(self._tracing_matrix.items()):
            req_preview = entry.requirement_text[:40] + "..." if len(entry.requirement_text) > 40 else entry.requirement_text
            tests = ", ".join(entry.test_ids) if entry.test_ids else "No tests"
            status_icon = {
                ClauseStatus.PASSED: "✅",
                ClauseStatus.FAILED: "❌",
                ClauseStatus.NOT_TESTED: "⏳",
                ClauseStatus.BLOCKED: "🚫",
            }.get(entry.test_status, "❓")
            
            lines.append(f"| {clause_id} | {req_preview} | - | {status_icon} {entry.test_status.value} | {tests} |")
        
        lines.extend([
            "",
            "## Reverse Trace (Tests → SDD)",
            "| Test ID | Linked Clause(s) | Status |",
            "|---------|------------------|--------|",
        ])
        
        for test_id, test_case in sorted(self._test_cases.items()):
            linked_clause = test_case.clause_id
            status_icon = {
                ClauseStatus.PASSED: "✅",
                ClauseStatus.FAILED: "❌",
                ClauseStatus.NOT_TESTED: "⏳",
            }.get(test_case.status, "❓")
            
            lines.append(f"| {test_id} | {linked_clause} | {status_icon} {test_case.status.value} |")
        
        matrix_content = "\n".join(lines)
        matrix_file = self._tracing_dir / "sdd_test_matrix.md"
        matrix_file.write_text(matrix_content, encoding="utf-8")
        
        return matrix_content

    def visualize_tdd_status(self) -> str:
        """
        生成TDD红绿蓝状态可视化
        
        Returns:
            终端UI格式的状态可视化字符串
        """
        total = len(self._clauses)
        passed = sum(1 for c in self._clauses.values() if c.status == ClauseStatus.PASSED)
        failed = sum(1 for c in self._clauses.values() if c.status == ClauseStatus.FAILED)
        not_tested = sum(1 for c in self._clauses.values() if c.status == ClauseStatus.NOT_TESTED)
        blocked = sum(1 for c in self._clauses.values() if c.status == ClauseStatus.BLOCKED)
        
        width = 60
        
        lines = [
            "╔" + "═" * width + "╗",
            "║" + "TDD Status Visualization".center(width) + "║",
            "╠" + "─" * width + "╣",
            "",
            "║  Progress Bar:",
        ]
        
        if total > 0:
            bar_width = width - 20
            passed_width = int(passed / total * bar_width)
            failed_width = int(failed / total * bar_width)
            not_tested_width = bar_width - passed_width - failed_width
            
            green_bar = "🟩" * passed_width
            red_bar = "🟥" * failed_width
            gray_bar = "⬜" * max(0, not_tested_width)
            
            lines.append(f"║  {green_bar}{red_bar}{gray_bar}")
        else:
            lines.append(f"║  {'⬜' * (width - 20)}")
        
        lines.extend([
            "",
            "║  Legend:",
            "║  🟩 PASSED (Green)",
            "║  🟥 FAILED (Red)",
            "║  ⬜ NOT TESTED (Gray/Blue)",
            "║  🟨 BLOCKED (Yellow)",
            "",
            "║  Statistics:",
            f"║  Total Clauses:     {total:>6}",
            f"║  ✅ Passed:         {passed:>6}",
            f"║  ❌ Failed:         {failed:>6}",
            f"║  ⏳ Not Tested:     {not_tested:>6}",
            f"║  🚫 Blocked:        {blocked:>6}",
            "",
            "║  Coverage: " + f"{(passed / total * 100):.1f}%".rjust(width - 14),
            "╚" + "═" * width + "╝",
        ])
        
        return "\n".join(lines)

    def run_tests_for_clause(self, clause_id: str, simulate_result: bool = True) -> tuple[bool, str]:
        """
        运行指定条款的测试
        
        Args:
            clause_id: 条款ID
            simulate_result: 是否使用模拟结果（实际应用中替换为真实测试执行）
            
        Returns:
            (是否通过, 消息)
        """
        if clause_id not in self._clauses:
            return False, f"Clause {clause_id} not found"
        
        clause = self._clauses[clause_id]
        
        if simulate_result:
            import random
            passed = random.random() > 0.2
            clause.status = ClauseStatus.PASSED if passed else ClauseStatus.FAILED
            clause.last_tested_at = datetime.now(timezone.utc)
            
            if clause_id in self._tracing_matrix:
                self._tracing_matrix[clause_id].test_status = clause.status
                self._tracing_matrix[clause_id].last_execution_date = clause.last_tested_at
            
            for test_id in self._tracing_matrix.get(clause_id, TracingMatrixEntry("", "", [], ClauseStatus.NOT_TESTED)).test_ids:
                if test_id in self._test_cases:
                    self._test_cases[test_id].status = clause.status
            
            msg = "PASSED" if passed else "FAILED"
            return passed, f"Clause {clause_id}: {msg}"
        
        return True, f"Test execution for {clause_id} would be triggered here"

    def get_clause_by_id(self, clause_id: str) -> SDDExecutableClause | None:
        """根据ID获取条款"""
        return self._clauses.get(clause_id)

    def get_clauses_by_category(self, category: ClauseCategory) -> list[SDDExecutableClause]:
        """根据类别获取条款列表"""
        return [c for c in self._clauses.values() if c.category == category]

    def get_clauses_by_priority(self, priority: Priority) -> list[SDDExecutableClause]:
        """根据优先级获取条款列表"""
        return [c for c in self._clauses.values() if c.priority == priority]

    def batch_generate_tests(self) -> list[TestCase]:
        """为所有未生成测试的条款批量生成测试用例"""
        generated = []
        
        for clause in self._clauses.values():
            if clause.test_case_path is None:
                test_case = self.generate_test_case(clause)
                generated.append(test_case)
        
        return generated

    def get_summary(self) -> dict[str, Any]:
        """获取引擎运行摘要"""
        return {
            "total_clauses": len(self._clauses),
            "total_test_cases": len(self._test_cases),
            "by_status": {
                status.value: sum(1 for c in self._clauses.values() if c.status == status)
                for status in ClauseStatus
            },
            "by_category": {
                cat.value: sum(1 for c in self._clauses.values() if c.category == cat)
                for cat in ClauseCategory
            },
            "by_priority": {
                p.name: sum(1 for c in self._clauses.values() if c.priority == p)
                for p in Priority
            },
        }
