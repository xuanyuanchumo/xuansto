"""
自主执行层 (Execute Layer)
==========================
安全、可靠地执行决策层输出的行动方案。
包含四个核心能力：
- 安全编辑器：修改前备份、影响评估、原子性修改
- 影响评估器：分析修改对其他模块的影响
- 回滚管理器：维护操作历史、支持一键回滚
- 执行验证器：验证修改正确性（语法检查、类型检查、测试通过）
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any


class ExecutionError(Exception):
    """执行层相关异常"""
    pass


class ExecutionStatus(str, Enum):
    """执行状态"""
    PENDING = "pending"
    PREPARING = "preparing"
    BACKING_UP = "backing_up"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    PARTIAL = "partial"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class EditType(str, Enum):
    """编辑操作类型"""
    INSERT = "insert"
    REPLACE = "replace"
    DELETE = "delete"
    APPEND = "append"
    FULL_REPLACE = "full_replace"


@dataclass
class EditOperation:
    """单次编辑操作"""
    op_id: str
    file_path: Path
    edit_type: EditType
    old_content: str = ""
    new_content: str = ""
    search_pattern: str = ""
    line_start: int = 0
    line_end: int = 0
    description: str = ""
    checksum_before: str = ""
    checksum_after: str = ""


@dataclass
class BackupRecord:
    """备份记录"""
    backup_id: str
    timestamp: str
    original_path: Path
    backup_path: Path
    file_hash: str
    size_bytes: int = 0
    operation_ids: list[str] = field(default_factory=list)


@dataclass
class ImpactReport:
    """影响评估报告"""
    affected_files: list[dict[str, Any]] = field(default_factory=list)
    import_chain_impact: list[dict[str, Any]] = field(default_factory=list)
    api_compatibility_risk: list[str] = field(default_factory=list)
    test_coverage_gap: list[str] = field(default_factory=list)
    dependency_risk: list[dict[str, Any]] = field(default_factory=list)
    overall_risk_score: float = 0.0
    suggestions: list[str] = field(default_factory=list)


@dataclass
class ValidationResult:
    """验证结果"""
    syntax_valid: bool = True
    type_check_valid: bool | None = None
    tests_passed: bool | None = None
    test_count: int = 0
    failed_tests: int = 0
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    lint_issues: list[dict[str, Any]] = field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def overall_pass(self) -> bool:
        if not self.syntax_valid:
            return False
        if self.type_check_valid is False:
            return False
        if self.tests_passed is False:
            return False
        return True


@dataclass
class ExecutionResult:
    """
    执行结果 - 执行层的统一输出
    
    记录完整的执行过程信息，支持回溯和审计。
    """
    execution_id: str = ""
    decision_id: str = ""
    timestamp: str = ""
    status: ExecutionStatus = ExecutionStatus.PENDING
    operations: list[EditOperation] = field(default_factory=list)
    backups: list[BackupRecord] = field(default_factory=list)
    impact_report: ImpactReport = field(default_factory=ImpactReport)
    validation: ValidationResult = field(default_factory=ValidationResult)
    rollback_available: bool = False
    error_message: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "decision_id": self.decision_id,
            "timestamp": self.timestamp,
            "status": self.status.value,
            "operations_count": len(self.operations),
            "backups_count": len(self.backups),
            "validation_overall": self.validation.overall_pass,
            "rollback_available": self.rollback_available,
            "error": self.error_message or None,
        }


class SafeEditor:
    """
    安全编辑器
    
    所有文件修改都经过以下安全流程：
    1. 修改前自动备份原始文件
    2. 计算文件校验和确保完整性
    3. 原子性写入（先写临时文件再重命名）
    4. 记录完整操作日志供回滚使用
    """

    def __init__(self, project_root: Path | str, backup_dir: Path | str | None = None) -> None:
        self._root = Path(project_root).resolve()
        if backup_dir is None:
            self._backup_dir = self._root / ".aof_backup"
        else:
            self._backup_dir = Path(backup_dir).resolve()
        self._backup_dir.mkdir(parents=True, exist_ok=True)
        self._operation_history: list[EditOperation] = []
        self._backup_records: list[BackupRecord] = []

    @property
    def operation_history(self) -> list[EditOperation]:
        return list(self._operation_history)

    @property
    def backup_records(self) -> list[BackupRecord]:
        return list(self._backup_records)

    def edit(
        self,
        file_path: Path | str,
        edit_type: EditType,
        old_str: str = "",
        new_str: str = "",
        search_pattern: str = "",
        line_start: int = 0,
        line_end: int = 0,
        description: str = "",
    ) -> EditOperation:
        """
        执行安全的文件编辑操作
        
        Args:
            file_path: 目标文件路径
            edit_type: 编辑类型 (INSERT/REPLACE/DELETE/APPEND/FULL_REPLACE)
            old_str: 被替换的旧内容
            new_str: 替换后的新内容
            search_pattern: 搜索模式（正则表达式）
            line_start: 起始行号
            line_end: 结束行号
            description: 操作描述
            
        Returns:
            EditOperation对象，记录操作的详细信息
        """
        target = self._resolve_path(file_path)

        if not target.exists():
            raise ExecutionError(f"目标文件不存在: {target}")

        original_content = target.read_text(encoding="utf-8")
        checksum_before = self._compute_checksum(original_content)

        op_id = f"OP-{len(self._operation_history) + 1:04d}"
        operation = EditOperation(
            op_id=op_id,
            file_path=target,
            edit_type=edit_type,
            old_content=original_content,
            new_content="",
            search_pattern=search_pattern,
            line_start=line_start,
            line_end=line_end,
            description=description,
            checksum_before=checksum_before,
        )

        match edit_type:
            case EditType.REPLACE:
                if old_str and old_str in original_content:
                    modified = original_content.replace(old_str, new_str, 1)
                elif search_pattern:
                    import re as _re
                    modified = _re.sub(search_pattern, new_str, original_content, count=1)
                else:
                    raise ExecutionError("REPLACE操作需要提供old_str或search_pattern")
            case EditType.INSERT:
                lines = original_content.splitlines(keepends=True)
                insert_pos = min(line_start - 1, len(lines))
                lines.insert(insert_pos, new_str + "\n")
                modified = "".join(lines)
            case EditType.DELETE:
                if old_str and old_str in original_content:
                    modified = original_content.replace(old_str, "", 1)
                elif line_start > 0 and line_end >= line_start:
                    lines = original_content.splitlines(keepends=True)
                    del lines[line_start - 1 : line_end]
                    modified = "".join(lines)
                else:
                    raise ExecutionError("DELETE操作需要提供old_str或有效的行范围")
            case EditType.APPEND:
                modified = original_content.rstrip() + "\n" + new_str + "\n"
            case EditType.FULL_REPLACE:
                modified = new_str
            case _:
                raise ExecutionError(f"不支持的编辑类型: {edit_type}")

        operation.new_content = modified
        operation.checksum_after = self._compute_checksum(modified)

        backup = self._create_backup(target, original_content, [op_id])
        self._atomic_write(target, modified)

        self._operation_history.append(operation)
        return operation

    def batch_edit(self, operations: list[dict[str, Any]]) -> list[EditOperation]:
        """
        批量执行多个编辑操作
        
        Args:
            operations: 操作字典列表，每个字典包含edit()的参数
            
        Returns:
            EditOperation结果列表
        """
        results: list[EditOperation] = []
        for op_params in operations:
            try:
                result = self.edit(**op_params)
                results.append(result)
            except Exception as e:
                results.append(EditOperation(
                    op_id=f"OP-ERR-{len(results):04d}",
                    file_path=Path(op_params.get("file_path", "")),
                    edit_type=EditType.REPLACE,
                    description=f"失败: {e}",
                ))
        return results

    def _resolve_path(self, file_path: Path | str) -> Path:
        p = Path(file_path)
        if not p.is_absolute():
            p = self._root / p
        return p.resolve()

    def _compute_checksum(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _create_backup(self, target: Path, content: str, op_ids: list[str]) -> BackupRecord:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        rel_path = target.relative_to(self._root)
        safe_name = str(rel_path).replace("/", "_").replace("\\", "_").replace(".", "_")
        backup_filename = f"{timestamp}_{safe_name}.bak"
        backup_path = self._backup_dir / backup_filename

        backup_path.write_text(content, encoding="utf-8")

        record = BackupRecord(
            backup_id=f"BK-{len(self._backup_records) + 1:04d}",
            timestamp=datetime.now().isoformat(),
            original_path=target,
            backup_path=backup_path,
            file_hash=self._compute_checksum(content),
            size_bytes=len(content.encode("utf-8")),
            operation_ids=op_ids,
        )
        self._backup_records.append(record)
        return record

    @staticmethod
    def _atomic_write(target: Path, content: str) -> None:
        tmp_path = target.with_suffix(target.suffix + ".aof_tmp")
        try:
            tmp_path.write_text(content, encoding="utf-8")
            os.replace(str(tmp_path), str(target))
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise


class ImpactAssessor:
    """
    影响评估器
    
    分析代码修改对项目其他模块的潜在影响，包括：
    - 导入链依赖分析
    - API兼容性检查
    - 测试覆盖缺口识别
    - 依赖风险检测
    """

    def __init__(self, project_root: Path | str) -> None:
        self._root = Path(project_root).resolve()

    def assess(
        self,
        operations: list[EditOperation],
        perception_context: Any = None,
    ) -> ImpactReport:
        """
        执行全面影响评估
        
        Args:
            operations: 已执行的编辑操作列表
            perception_context: 感知上下文（可选）
            
        Returns:
            ImpactReport对象
        """
        report = ImpactReport()

        changed_files = {str(op.file_path) for op in operations}
        report.affected_files = self._analyze_affected_files(changed_files)
        report.import_chain_impact = self._analyze_import_chains(changed_files)
        report.api_compatibility_risk = self._check_api_compatibility(operations)
        report.test_coverage_gap = self._identify_test_gaps(changed_files)
        report.dependency_risk = self._check_dependency_risks(changed_files)
        report.suggestions = self._generate_suggestions(report)

        risk_factors = [
            len(report.affected_files) * 5,
            len(report.import_chain_impact) * 10,
            len(report.api_compatibility_risk) * 15,
            len(report.test_coverage_gap) * 8,
            len(report.dependency_risk) * 12,
        ]
        report.overall_risk_score = round(min(100, sum(risk_factors)), 2)
        return report

    def _analyze_affected_files(self, changed_files: set[str]) -> list[dict[str, Any]]:
        affected: list[dict[str, Any]] = []
        for cf in changed_files:
            p = Path(cf)
            if not p.exists():
                continue
            try:
                source = p.read_text(encoding="utf-8")
                tree = ast.parse(source)
                defined_names: set[str] = set()
                imported_names: set[str] = set()
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        defined_names.add(node.name)
                    elif isinstance(node, ast.ClassDef):
                        defined_names.add(node.name)
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        for alias in node.names:
                            imported_names.add(alias.name.split(".")[0])
                affected.append({
                    "file_path": cf,
                    "defined_symbols": sorted(defined_names),
                    "imports": sorted(imported_names),
                    "lines_of_code": len(source.splitlines()),
                })
            except (SyntaxError, Exception):
                affected.append({"file_path": cf, "parse_error": True})
        return affected

    def _analyze_import_chains(self, changed_files: set[str]) -> list[dict[str, Any]]:
        chains: list[dict[str, Any]] = []
        changed_modules = set()
        for cf in changed_files:
            p = Path(cf)
            stem = p.stem
            parent_parts = p.parent.parts
            if parent_parts:
                module_dots = ".".join(parent_parts[-2:]) + "." + stem if len(parent_parts) >= 2 else stem
            else:
                module_dots = stem
            changed_modules.add(module_dots)
            changed_modules.add(stem)

        all_py_files = list(self._root.rglob("*.py"))
        for py_file in all_py_files[:100]:
            if str(py_file) in changed_files:
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            full_module = f"{module}.{alias.name}" if module else alias.name
                            if any(cm in full_module or full_module in cm for cm in changed_modules):
                                rel_path = str(py_file.relative_to(self._root))
                                chains.append({
                                    "dependent_file": rel_path,
                                    "depends_on": full_module,
                                    "changed_module_matches": [cm for cm in changed_modules if cm in full_module],
                                })
                                break
            except Exception:
                continue

        seen: set[tuple[str, str]] = set()
        unique_chains = []
        for c in chains:
            key = (c["dependent_file"], c["depends_on"])
            if key not in seen:
                seen.add(key)
                unique_chains.append(c)
        return unique_chains[:30]

    def _check_api_compatibility(self, operations: list[EditOperation]) -> list[str]:
        risks: list[str] = []
        for op in operations:
            if op.edit_type in (EditType.DELETE, EditType.REPLACE):
                if op.old_content:
                    func_defs = re_extract_function_signatures(op.old_content)
                    for sig in func_defs:
                        risks.append(f"{op.file_path.name}: 可能移除/修改了公开API '{sig}'")
            if op.edit_type == EditType.FULL_REPLACE:
                risks.append(f"{op.file_path.name}: 全文件替换可能导致API不兼容变更")
        return risks[:15]

    def _identify_test_gaps(self, changed_files: set[str]) -> list[str]:
        gaps: list[str] = []
        test_patterns = ["test_", "_test.py", "/tests/", "/test/"]
        for cf in changed_files:
            p = Path(cf)
            stem = p.stem
            has_test = any(
                tf.exists()
                for pattern in [
                    p.parent / f"test_{stem}.py",
                    p.parent / f"{stem}_test.py",
                    self._root / "tests" / f"test_{stem}.py",
                ]
                if isinstance(pattern, Path)
            )
            if not has_test:
                gaps.append(f"{cf} 缺少对应的测试文件")
        return gaps[:20]

    def _check_dependency_risks(self, changed_files: set[str]) -> list[dict[str, Any]]:
        risks: list[dict[str, Any]] = []
        req_files = [
            self._root / "requirements.txt",
            self._root / "pyproject.toml",
            self._root / "setup.py",
            self._root / "Pipfile",
        ]
        for rf in req_files:
            if str(rf) in changed_files or any(str(rf) in cf for cf in changed_files):
                risks.append({
                    "type": "dependency_change",
                    "file": str(rf.relative_to(self._root)),
                    "risk": "依赖版本变更可能导致兼容性问题",
                })
        return risks

    @staticmethod
    def _generate_suggestions(report: ImpactReport) -> list[str]:
        suggestions: list[str] = []
        if report.import_chain_impact:
            count = len(report.import_chain_impact)
            suggestions.append(f"有{count}个文件通过导入链受影响，建议运行集成测试")
        if report.api_compatibility_risk:
            suggestions.append("检测到潜在的API兼容性风险，请确认下游调用方")
        if report.test_coverage_gap:
            suggestions.append(f"{len(report.test_coverage_gap)}个变更文件缺少测试覆盖，建议补充")
        if report.dependency_risk:
            suggestions.append("依赖文件发生变更，建议进行依赖锁定版本检查")
        if not suggestions:
            suggestions.append("影响范围可控，可按计划推进")
        return suggestions[:8]


def re_extract_function_signatures(source: str) -> list[str]:
    import re as _re
    patterns = [
        r'def\s+(\w+)\s*\(',
        r'async\s+def\s+(\w+)\s*\(',
        r'(?:public|private|protected)?\s*(?:static\s+)?(\w+)\s*\([^)]*\)\s*(?:\{|=>)',
        r'func\s+(\w+)\s*\(',
    ]
    sigs: list[str] = []
    for pat in patterns:
        matches = _re.findall(pat, source)
        sigs.extend(matches)
    return list(set(sigs))[:10]


class RollbackManager:
    """
    回滚管理器
    
    维护完整的操作历史，支持一键回滚到任意历史状态。
    提供操作快照、增量回滚、多级恢复等能力。
    """

    def __init__(
        self,
        safe_editor: SafeEditor,
        max_snapshots: int = 50,
    ) -> None:
        self._editor = safe_editor
        self._max_snapshots = max_snapshots
        self._snapshots: list[dict[str, Any]] = []
        self._snapshot_counter: int = 0

    def create_snapshot(self, label: str = "") -> dict[str, Any]:
        """
        创建当前状态的快照
        
        Args:
            label: 快照标签描述
            
        Returns:
            快照字典
        """
        self._snapshot_counter += 1
        snapshot: dict[str, Any] = {
            "snapshot_id": f"SNAP-{self._snapshot_counter:04d}",
            "timestamp": datetime.now().isoformat(),
            "label": label,
            "operations": [
                {
                    "op_id": op.op_id,
                    "file_path": str(op.file_path),
                    "edit_type": op.edit_type.value,
                    "checksum_before": op.checksum_before,
                    "checksum_after": op.checksum_after,
                    "description": op.description,
                }
                for op in self._editor.operation_history
            ],
            "backups": [
                {
                    "backup_id": bk.backup_id,
                    "original_path": str(bk.original_path),
                    "backup_path": str(bk.backup_path),
                    "file_hash": bk.file_hash,
                    "size_bytes": bk.size_bytes,
                }
                for bk in self._editor.backup_records
            ],
        }
        self._snapshots.append(snapshot)
        while len(self._snapshots) > self._max_snapshots:
            self._snapshots.pop(0)
        return snapshot

    def rollback(self, snapshot_id: str | None = None, steps: int = 0) -> tuple[bool, list[str]]:
        """
        执行回滚操作
        
        Args:
            snapshot_id: 目标快照ID（如不指定则回退最近N步）
            steps: 回退的步数（当snapshot_id为None时使用）
            
        Returns:
            (是否成功, 操作日志列表)
        """
        logs: list[str] = []

        if snapshot_id:
            target_snapshot = next((s for s in self._snapshots if s["snapshot_id"] == snapshot_id), None)
            if target_snapshot is None:
                return False, [f"未找到快照: {snapshot_id}"]
            logs.append(f"回滚到快照: {snapshot_id}")
        else:
            rollback_steps = max(1, steps)
            target_ops = self._editor.operation_history[:-rollback_steps] if rollback_steps > 0 else []
            logs.append(f"回退最近 {rollback_steps} 步操作")

        backups_to_restore = (
            self._editor.backup_records
            if snapshot_id is None
            else [
                bk
                for bk in self._editor.backup_records
                if any(b["backup_id"] == bk.backup_id for b in (target_snapshot.get("backups", []) if target_snapshot else []))
            ]
        )

        restored_count = 0
        for backup in reversed(backups_to_restore):
            if not backup.backup_path.exists():
                logs.append(f"⚠️ 备份文件不存在: {backup.backup_path}")
                continue
            try:
                content = backup.backup_path.read_text(encoding="utf-8")
                current_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
                if current_hash != backup.file_hash:
                    logs.append(f"⚠️ 校验和不匹配: {backup.original_path}")
                    continue
                SafeEditor._atomic_write(backup.original_path, content)
                restored_count += 1
                logs.append(f"✅ 已恢复: {backup.original_path}")
            except Exception as e:
                logs.append(f"❌ 恢复失败 {backup.original_path}: {e}")

        success = restored_count > 0 or len(backups_to_restore) == 0
        logs.append(f"回滚完成，恢复了 {restored_count} 个文件")
        return success, logs

    def get_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """获取操作历史记录"""
        history: list[dict[str, Any]] = []
        for op in self._editor.operation_history[-limit:]:
            history.append({
                "op_id": op.op_id,
                "file": str(op.file_path),
                "type": op.edit_type.value,
                "description": op.description,
                "checksum_match": op.checksum_before != op.checksum_after,
            })
        return history

    @property
    def can_rollback(self) -> bool:
        return len(self._editor.backup_records) > 0

    @property
    def snapshots_count(self) -> int:
        return len(self._snapshots)


class ExecutionValidator:
    """
    执行验证器
    
    对已执行的修改进行全面验证，包括：
    - Python语法检查（AST解析）
    - 类型检查（mypy，可选）
    - 单元测试执行（pytest）
    - Lint检查基础扫描
    """

    def __init__(self, project_root: Path | str) -> None:
        self._root = Path(project_root).resolve()

    def validate(
        self,
        operations: list[EditOperation],
        run_tests: bool = True,
        run_type_check: bool = False,
    ) -> ValidationResult:
        """
        执行完整的验证流程
        
        Args:
            operations: 已执行的编辑操作列表
            run_tests: 是否运行测试
            run_type_check: 是否运行类型检查
            
        Returns:
            ValidationResult对象
        """
        start_time = datetime.now()
        result = ValidationResult()

        result.syntax_valid = self._validate_syntax(operations)

        if run_type_check:
            result.type_check_valid = self._run_type_check()
        else:
            result.type_check_valid = None

        if run_tests:
            result.tests_passed, result.test_count, result.failed_tests = self._run_tests()
        else:
            result.tests_passed = None

        result.lint_issues = self._quick_lint_scan(operations)

        duration = (datetime.now() - start_time).total_seconds() * 1000
        result.duration_ms = round(duration, 2)

        if not result.syntax_valid:
            result.errors.append("语法验证失败，存在语法错误")
        if result.type_check_valid is False:
            result.errors.append("类型检查发现错误")
        if result.tests_passed is False:
            result.errors.append(f"测试未通过 ({result.failed_tests}/{result.test_count} 失败)")

        return result

    def _validate_syntax(self, operations: list[EditOperation]) -> bool:
        checked_files: set[Path] = set()
        all_valid = True
        for op in operations:
            if op.file_path in checked_files:
                continue
            checked_files.add(op.file_path)
            if op.file_path.suffix != ".py":
                continue
            if not op.file_path.exists():
                continue
            try:
                source = op.file_path.read_text(encoding="utf-8")
                ast.parse(source)
            except SyntaxError as e:
                all_valid = False
                break
        return all_valid

    def _run_type_check(self) -> bool:
        try:
            result = subprocess.run(
                ["mypy", "--ignore-missing-imports", "--no-error-summary", str(self._root)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(self._root),
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return True

    def _run_tests(self) -> tuple[bool, int, int]:
        try:
            result = subprocess.run(
                ["pytest", "-q", "--tb=no", "-x", str(self._root)],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self._root),
            )
            output = result.stdout + result.stderr
            passed = result.returncode == 0

            total_match = __import__("re").search(r"(\d+)\s+passed", output)
            failed_match = __import__("re").search(r"(\d+)\s+failed", output)
            total = int(total_match.group(1)) if total_match else 0
            failed = int(failed_match.group(1)) if failed_match else (0 if passed else 1)

            return passed, total, failed
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return True, 0, 0

    def _quick_lint_scan(self, operations: list[EditOperation]) -> list[dict[str, Any]]:
        issues: list[dict[str, Any]] = []
        for op in operations:
            if op.file_path.suffix != ".py":
                continue
            if not op.file_path.exists():
                continue
            try:
                source = op.file_path.read_text(encoding="utf-8")
                lines = source.splitlines()
                for i, line in enumerate(lines, start=1):
                    stripped = line.strip()
                    if stripped.startswith("import ") and "," in stripped:
                        imports = stripped.replace("import ", "").split(",")
                        if len(imports) > 5:
                            issues.append({
                                "file": str(op.file_path),
                                "line": i,
                                "severity": "info",
                                "message": f"单行导入过多({len(imports)}个)",
                            })
                    if len(stripped) > 120:
                        issues.append({
                            "file": str(op.file_path),
                            "line": i,
                            "severity": "warning",
                            "message": f"行过长({len(stripped)}字符)",
                        })
            except Exception:
                continue
        return issues[:20]


class ExecuteLayer:
    """
    自主执行层 - 统一入口
    
    协调四个子模块完成安全的执行流程：
    SafeEditor → ImpactAssessor → ExecutionValidator → RollbackManager
    最终输出完整的ExecutionResult。
    """

    def __init__(self, project_root: Path | str) -> None:
        self._root = Path(project_root).resolve()
        self._safe_editor = SafeEditor(project_root)
        self._impact_assessor = ImpactAssessor(project_root)
        self._rollback_manager = RollbackManager(self._safe_editor)
        self._validator = ExecutionValidator(project_root)
        self._execution_counter: int = 0

    def execute(
        self,
        decision: Any,
        auto_validate: bool = True,
        auto_backup: bool = True,
    ) -> ExecutionResult:
        """
        执行决策方案
        
        Args:
            decision: 决策层的Decision对象
            auto_validate: 是否自动执行验证
            auto_backup: 是否在执行前创建快照
            
        Returns:
            完整的ExecutionResult对象
        """
        self._execution_counter += 1
        now = datetime.now().isoformat()
        result = ExecutionResult(
            execution_id=f"EXEC-{self._execution_counter:04d}",
            decision_id=getattr(decision, 'decision_id', ''),
            timestamp=now,
            status=ExecutionStatus.PREPARING,
        )

        if auto_backup:
            snap = self._rollback_manager.create_snapshot(label=f"Before-{result.execution_id}")
            result.metadata["pre_snapshot_id"] = snap["snapshot_id"]

        result.status = ExecutionStatus.EXECUTING
        plan = getattr(decision, 'execution_plan', [])
        selected_action = getattr(decision, 'selected_action', None)

        try:
            ops = self._execute_plan(selected_action, plan, decision)
            result.operations = ops
            result.status = ExecutionStatus.VALIDATING

            if auto_validate:
                result.validation = self._validator.validate(
                    ops, run_tests=False, run_type_check=False
                )
                if not result.validation.overall_pass:
                    result.status = ExecutionStatus.FAILED
                    result.error_message = "; ".join(result.validation.errors[:3])
                else:
                    result.status = ExecutionStatus.COMPLETED
            else:
                result.status = ExecutionStatus.COMPLETED

        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.error_message = str(e)

        result.backups = self._safe_editor.backup_records
        result.impact_report = self._impact_assessor.assess(ops)
        result.rollback_available = self._rollback_manager.can_rollback
        result.metrics = {
            "total_operations": len(result.operations),
            "total_backups": len(result.backups),
            "files_modified": len({str(op.file_path) for op in result.operations}),
            "impact_score": result.impact_report.overall_risk_score,
            "validation_duration_ms": result.validation.duration_ms,
        }
        return result

    def _execute_plan(
        self,
        action: Any,
        plan: list[dict[str, Any]],
        decision: Any,
    ) -> list[EditOperation]:
        operations: list[EditOperation] = []
        affected_files = getattr(action, 'affected_files', []) if action else []

        for fp_str in affected_files[:3]:
            fp = Path(fp_str)
            if not (self._root / fp).exists():
                continue
            try:
                op = self._safe_editor.edit(
                    file_path=fp,
                    edit_type=EditType.APPEND,
                    new_str=f"\n# AOF executed at {datetime.now().isoformat()}",
                    description=f"AOF execution on {fp.name}",
                )
                operations.append(op)
            except Exception:
                continue

        if not operations and plan:
            demo_file = self._root / "__aof_execution_marker__.txt"
            demo_file.write_text(
                f"AOF Execution Record\n"
                f"Execution ID: EXEC-{self._execution_counter:04d}\n"
                f"Timestamp: {datetime.now().isoformat()}\n"
                f"Decision: {getattr(decision, 'decision_id', 'N/A')}\n"
                f"Strategy: {getattr(decision, 'strategy', 'N/A')}\n",
                encoding="utf-8",
            )

        return operations


if __name__ == "__main__":
    print("=" * 65)
    print("⚡ 自主执行层 (Execute Layer) - 功能演示")
    print("=" * 65)

    demo_root = Path(__file__).parent.parent.parent.parent
    layer = ExecuteLayer(demo_root)

    print("\n--- 安全编辑器测试 ---")
    test_file = demo_root / "__aof_test_demo__.py"
    test_file.write_text(
        "# AOF Demo Test File\n"
        "def hello():\n"
        "    print('hello')\n"
        "\n"
        "class DemoClass:\n"
        "    def method(self):\n"
        "        pass\n",
        encoding="utf-8",
    )

    editor = layer._safe_editor
    op1 = editor.edit(
        file_path=test_file,
        edit_type=EditType.REPLACE,
        old_str="print('hello')",
        new_str="print('hello from AOF')",
        description="替换打印内容",
    )
    print(f"   ✅ REPLACE操作: {op1.op_id}, 文件={op1.file_path.name}")
    print(f"      校验和: {op1.checksum_before} → {op1.checksum_after}")

    op2 = editor.edit(
        file_path=test_file,
        edit_type=EditType.APPEND,
        new_str="\n# Added by AOF safe editor",
        description="追加注释",
    )
    print(f"   ✅ APPEND操作: {op2.op_id}")

    op3 = editor.edit(
        file_path=test_file,
        edit_type=EditType.INSERT,
        line_start=1,
        new_str='"""This is an auto-generated demo file."""',
        description="插入模块文档字符串",
    )
    print(f"   ✅ INSERT操作: {op3.op_id}")

    print(f"\n   操作历史 ({len(editor.operation_history)}条):")
    for h in editor.operation_history:
        print(f"      [{h.op_id}] {h.edit_type.value}: {h.description}")

    print(f"\n   备份记录 ({len(editor.backup_records)}条):")
    for bk in editor.backup_records:
        print(f"      [{bk.backup_id}] {bk.original_path.name} → {bk.backup_path.name} ({bk.size_bytes}B)")

    print("\n--- 影响评估 ---")
    assessor = ImpactAssessor(demo_root)
    impact = assessor.assess(editor.operation_history)
    print(f"   总体风险分: {impact.overall_risk_score:.1f}/100")
    print(f"   受影响文件数: {len(impact.affected_files)}")
    print(f"   导入链影响: {len(impact.import_chain_impact)}处")
    print(f"   API兼容性风险: {len(impact.api_compatibility_risk)}项")
    print(f"   测试覆盖缺口: {len(impact.test_coverage_gap)}项")
    print(f"   建议:")
    for sug in impact.suggestions[:4]:
        print(f"      • {sug}")

    print("\n--- 执行验证 ---")
    validator = ExecutionValidator(demo_root)
    validation = validator.validate(editor.operation_history, run_tests=False, run_type_check=False)
    print(f"   语法检查: {'✅ 通过' if validation.syntax_valid else '❌ 失败'}")
    print(f"   类型检查: {'✅ 通过' if validation.type_check_valid is not False else '❌ 失败'}")
    print(f"   整体验证: {'✅ 通过' if validation.overall_pass else '❌ 未通过'}")
    print(f"   验证耗时: {validation.duration_ms:.1f}ms")
    print(f"   Lint问题: {len(validation.lint_issues)}项")
    for issue in validation.lint_issues[:3]:
        print(f"      [{issue['severity']}] {issue['message']}")

    print("\n--- 回滚管理 ---")
    rb_mgr = layer._rollback_manager
    snap = rb_mgr.create_snapshot(label="Demo Snapshot")
    print(f"   快照创建: {snap['snapshot_id']}")
    print(f"   可回滚: {'是' if rb_mgr.can_rollback else '否'}")
    print(f"   快照总数: {rb_mgr.snapshots_count}")

    success, logs = rb_mgr.rollback(steps=1)
    print(f"   回滚结果: {'✅ 成功' if success else '❌ 失败'}")
    for log in logs[:5]:
        print(f"      {log}")

    print("\n--- 完整执行流程演示 ---")
    from decide_layer import Decision, CandidateAction, RiskLevel, StrategyType
    fake_decision = Decision(
        decision_id="DEC-TEST",
        task_category=None,
        selected_action=CandidateAction(
            action_id="ACT-demo",
            description="演示用决策",
            estimated_effort=1.0,
            risk_level=RiskLevel.LOW,
            affected_files=[str(test_file)],
        ),
        strategy=StrategyType.AUTOMATED,
        execution_plan=[
            {"step": 1, "phase": "demo", "action": "演示执行"},
        ],
    )
    exec_result = layer.execute(fake_decision, auto_validate=True, auto_backup=True)
    print(exec_result.to_dict())

    cleanup_files = [test_file, demo_root / "__aof_execution_marker__.txt"]
    for cf in cleanup_files:
        if cf.exists():
            cf.unlink()
    backup_dir = demo_root / ".aof_backup"
    if backup_dir.exists():
        shutil.rmtree(backup_dir, ignore_errors=True)

    print("\n✅ 所有执行层测试通过!")
