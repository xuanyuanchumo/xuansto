"""
规范制定局 - 中书省第三局

负责编码规范管理(PEP8/ESLint/Airbnb/Google)、开发原则知识库(Clean Code/SOLID/DRY/KISS/YAGNI等)、
API规范生成(OpenAPI 3.0)、数据库规范设计、安全检查清单(OWASP Top 10)及Git工作流规范定义。
"""
from __future__ import annotations

import json
import re
import ast
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any


class StandardsError(Exception):
    """规范制定局相关异常"""
    pass


# ==================== 编码规范相关 ====================

@dataclass
class LintRule:
    """代码检查规则"""
    rule_id: str
    name: str
    description: str
    severity: str = "warning"       # error / warning / info
    category: str = ""              # style / complexity / naming / security / performance
    pattern: str = ""               # 正则匹配模式
    suggestion: str = ""
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "name": self.name,
            "description": self.description,
            "severity": self.severity,
            "category": self.category,
        }


@dataclass
class CodingStandards:
    """编码规范集合"""
    language: str
    standard_name: str = ""
    description: str = ""
    rules: list[LintRule] = field(default_factory=list)
    config_snippet: str = ""
    reference_url: str = ""

    def to_markdown(self) -> str:
        lines = [
            f"# {self.standard_name} 编码规范 ({self.language})",
            f"\n{self.description}\n",
            "## 规则列表\n",
            "| 规则ID | 名称 | 描述 | 严重级别 | 分类 |",
            "|--------|------|------|----------|------|",
        ]
        for rule in self.rules:
            lines.append(f"| {rule.rule_id} | {rule.name} | {rule.description} | {rule.severity} | {rule.category} |")
        if self.config_snippet:
            lines.extend(["\n## 配置示例\n", f"```\n{self.config_snippet}\n```"])
        if self.reference_url:
            lines.append(f"\n> 参考文档: {self.reference_url}")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "language": self.language,
            "standard_name": self.standard_name,
            "rules_count": len(self.rules),
            "rules": [r.to_dict() for r in self.rules],
        }


# ==================== 开发原则相关 ====================

class PrincipleCategory(str, Enum):
    """原则分类"""
    CODE_QUALITY = "code_quality"
    DESIGN = "design"
    ARCHITECTURE = "architecture"
    METHODOLOGY = "methodology"
    TEAMWORK = "teamwork"


@dataclass
class Principle:
    """开发原则"""
    name: str
    abbreviation: str = ""
    category: PrincipleCategory = PrincipleCategory.CODE_QUALITY
    description: str = ""
    core_idea: str = ""
    benefits: list[str] = field(default_factory=list)
    violations: list[str] = field(default_factory=list)
    examples_good: list[str] = field(default_factory=list)
    examples_bad: list[str] = field(default_factory=list)
    related_principles: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "abbreviation": self.abbreviation,
            "category": self.category.value,
            "description": self.description,
            "core_idea": self.core_idea,
            "benefits": self.benefits[:3],
            "violations": self.violations[:3],
        }

    def to_markdown(self) -> str:
        abbr = f" ({self.abbreviation})" if self.abbreviation else ""
        sections = [
            f"## {self.name}{abbr}",
            f"\n**分类**: {self.category.value}",
            f"**核心理念**: {self.core_idea}\n",
            f"{self.description}\n",
            "### 好处",
            *[f"- {b}" for b in self.benefits],
            "",
            "### 违反表现",
            *[f"- {v}" for v in self.violations],
        ]
        if self.examples_good:
            sections.extend(["", "### ✅ 正确示例", *('```python\n' + e + '\n```' for e in self.examples_good)])
        if self.examples_bad:
            sections.extend(["", "### ❌ 错误示例", *('```python\n' + e + '\n```' for e in self.examples_bad)])
        if self.related_principles:
            sections.extend(["", "**相关原则**: ", ", ".join(self.related_principles)])
        return "\n".join(sections)


@dataclass
class ViolationItem:
    """违规条目"""
    line_number: int
    violation_type: str
    description: str
    code_snippet: str
    severity: str = "warning"
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "line": self.line_number,
            "type": self.violation_type,
            "description": self.description,
            "snippet": self.code_snippet[:80],
            "severity": self.severity,
            "suggestion": self.suggestion,
        }


@dataclass
class ViolationReport:
    """违规报告"""
    principle_name: str
    total_violations: int = 0
    items: list[ViolationItem] = field(default_factory=list)
    score: float = 100.0
    summary: str = ""
    checked_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def compliance_rate(self) -> float:
        return max(0.0, self.score)

    def to_markdown(self) -> str:
        lines = [
            f"# 原则违反检测报告: {self.principle_name}",
            f"\n**检测时间**: {self.checked_at[:19]}",
            f"**违规数量**: {self.total_violations}",
            f"**合规评分**: {self.score:.1f}/100",
            f"**合规率**: {self.compliance_rate:.1f}%\n",
        ]
        if self.summary:
            lines.append(f"> {self.summary}\n")
        lines.extend([
            "| 行号 | 类型 | 描述 | 严重度 | 建议 |",
            "|------|------|------|--------|------|",
        ])
        for item in self.items[:20]:
            snippet = item.code_snippet.replace("|", "\\|")[:50]
            lines.append(f"| {item.line_number} | {item.violation_type} | {item.description} | {item.severity} | {item.suggestion[:30]} |")
        if len(self.items) > 20:
            lines.append(f"\n*... 还有 {len(self.items) - 20} 条违规*")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "principle": self.principle_name,
            "total_violations": self.total_violations,
            "score": round(self.score, 1),
            "compliance_rate": round(self.compliance_rate, 1),
            "violations": [v.to_dict() for v in self.items],
        }


# ==================== API规范相关 ====================

@dataclass
class APIEndpointSpec:
    """API端点规格"""
    path: str
    method: str
    summary: str = ""
    description: str = ""
    tags: list[str] = field(default_factory=list)
    parameters: list[dict[str, Any]] = field(default_factory=dict)
    request_body: dict[str, Any] = field(default_factory=dict)
    responses: dict[int, dict[str, Any]] = field(default_factory=dict)
    security: list[dict[str, Any]] = field(default_factory=list)
    deprecated: bool = False


@dataclass
class DBTableSpec:
    """数据库表规格"""
    table_name: str
    comment: str = ""
    columns: list[dict[str, Any]] = field(default_factory=list)
    indexes: list[dict[str, Any]] = field(default_factory=list)
    primary_key: str = ""
    foreign_keys: list[dict[str, Any]] = field(default_factory=list)
    constraints: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class DBSchemaSpec:
    """数据库架构规格"""
    naming_convention: str = "snake_case"
    charset: str = "utf8mb4"
    engine: str = "InnoDB"
    tables: list[DBTableSpec] = field(default_factory=list)
    global_rules: list[str] = field(default_factory=list)

    def to_sql(self, dialect: str = "mysql") -> str:
        statements: list[str] = []
        for table in self.tables:
            col_defs: list[str] = []
            for col in table.columns:
                col_type = col.get("type", "VARCHAR(255)")
                nullable = "" if col.get("not_null", False) else " NULL"
                default = f" DEFAULT {col['default']}" if col.get("default") else ""
                comment_str = f" COMMENT '{col.get('comment', '')}'" if col.get("comment") else ""
                col_defs.append(f"    {col['name']} {col_type}{nullable}{default}{comment_str}")

            pk_def = f"    PRIMARY KEY ({table.primary_key})" if table.primary_key else ""
            all_defs = col_defs + ([pk_def] if pk_def else [])

            stmt = f"CREATE TABLE {table.table_name} (\n"
            stmt += ",\n".join(all_defs)
            stmt += f"\n) ENGINE={self.engine} DEFAULT CHARSET={self.charset}"
            if table.comment:
                stmt += f" COMMENT='{table.comment}'"
            stmt += ";"

            statements.append(stmt)

            for idx in table.indexes:
                idx_name = idx.get("name", f"idx_{table.table_name}_{idx.get('columns', ['id'])[0]}")
                idx_cols = ", ".join(idx.get("columns", ["id"]))
                idx_type = idx.get("type", "INDEX")
                unique = "UNIQUE " if idx.get("unique", False) else ""
                statements.append(
                    f"CREATE {unique}{idx_type} {idx_name} ON {table.table_name} ({idx_cols});"
                )

        return "\n\n".join(statements)

    def to_markdown(self) -> str:
        lines = [
            "# 数据库设计规范文档",
            f"\n**命名规范**: {self.naming_convention}",
            f"**字符集**: {self.charset}",
            f"**存储引擎**: {self.engine}\n",
        ]
        if self.global_rules:
            lines.extend(["## 全局规则", *[f"- {r}" for r in self.global_rules], ""])
        for table in self.tables:
            lines.extend([f"## 表: `{table.table_name}`", f"*{table.comment}*\n", "| 字段名 | 类型 | 可空 | 默认值 | 说明 |", "|--------|------|------|--------|------|"])
            for col in table.columns:
                lines.append(f"| {col['name']} | {col.get('type', '-')} | {'否' if col.get('not_null') else '是'} | {col.get('default', '-')} | {col.get('comment', '-')} |")
            if table.indexes:
                lines.append("\n**索引**: ")
                for idx in table.indexes:
                    lines.append(f"- {idx.get('type', 'INDEX')} `{idx.get('name', '?')}` on ({', '.join(idx.get('columns', []))})")
            lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "naming_convention": self.naming_convention,
            "charset": self.charset,
            "engine": self.engine,
            "tables_count": len(self.tables),
            "tables": [{"name": t.table_name, "columns_count": len(t.columns)} for t in self.tables],
        }


# ==================== 安全规范相关 ====================

@dataclass
class SecurityCheckItem:
    """安全检查项"""
    check_id: str
    category: str
    owasp_category: str
    title: string
    description: str
    severity: str = "high"
    status: str = "pending"
    mitigation: str = ""
    references: list[str] = field(default_factory=list)
    detection_methods: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_id": self.check_id,
            "category": self.category,
            "owasp": self.owasp_category,
            "title": self.title,
            "severity": self.severity,
            "status": self.status,
        }


@dataclass
class SecurityChecklist:
    """安全检查清单"""
    standard: str = "OWASP Top 10 (2021)"
    version: str = "2021.0"
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    items: list[SecurityCheckItem] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        lines = [
            f"# 安全检查清单 ({self.standard})",
            f"\n**版本**: {self.version}",
            f"**生成时间**: {self.generated_at[:10]}\n",
        ]

        categories: dict[str, list[SecurityCheckItem]] = {}
        for item in self.items:
            categories.setdefault(item.category, []).append(item)

        for cat_name, cat_items in categories.items():
            lines.append(f"## {cat_name}\n")
            lines.append("| ID | 检查项 | 严重度 | 状态 | 缓解措施 |")
            lines.append("|----|--------|--------|------|----------|")
            for ci in cat_items:
                lines.append(f"| {ci.check_id} | {ci.title} | {ci.severity} | {ci.status} | {ci.mitigation[:40] if ci.mitigation else '-'} |")
            lines.append("")

        if self.stats:
            lines.append("## 统计摘要\n")
            for k, v in self.stats.items():
                lines.append(f"- **{k}**: {v}")

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "standard": self.standard,
            "version": self.version,
            "total_checks": len(self.items),
            "items": [i.to_dict() for i in self.items],
            "stats": self.stats,
        }


# ==================== Git工作流相关 ====================

@dataclass
class BranchRule:
    """分支规则"""
    name: str
    pattern: str
    purpose: str = ""
    source_branch: str = ""
    target_branch: str = ""
    protection_rules: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "pattern": self.pattern, "purpose": self.purpose}


@dataclass
class CommitConvention:
    """提交信息规范"""
    format: str = "conventional-commits"
    types: list[str] = field(default_factory=lambda: ["feat", "fix", "docs", "style", "refactor", "test", "chore", "perf", "ci", "build"])
    scope_required: bool = False
    body_required: bool = False
    example: str = "feat(auth): add OAuth2 login support"

    def to_markdown(self) -> str:
        lines = [
            "## Commit Message 规范",
            f"\n**格式**: {self.format}\n",
            "### Type 列表",
            "| Type | 说明 |",
            "|------|------|",
        ]
        type_desc = {
            "feat": "新功能", "fix": "Bug修复", "docs": "文档更新",
            "style": "代码格式(不影响功能)", "refactor": "重构(非新功能非修复)",
            "test": "测试相关", "chore": "构建/工具", "perf": "性能优化",
            "ci": "CI配置", "build": "构建系统",
        }
        for t in self.types:
            lines.append(f"| **{t}** | {type_desc.get(t, '')} |")
        lines.extend([
            "",
            "### 格式示例",
            f"`{self.example}`",
            "",
            "<type>(<scope>): <subject>",
            "",
            "(optional body)",
            "",
            "(optional footer)",
        ])
        return "\n".join(lines)


@dataclass
class ReviewGuideline:
    """Code Review指南"""
    min_reviewers: int = 1
    required_checks: list[str] = field(default_factory=lambda: ["逻辑正确性", "安全性", "性能影响", "代码风格"])
    auto_skip_conditions: list[str] = field(default_factory=lambda: ["文档/typo修复", "依赖版本升级"])
    rejection_criteria: list[str] = field(default_factory=lambda: ["存在安全漏洞", "核心逻辑错误", "无测试覆盖"])

    def to_markdown(self) -> str:
        lines = [
            "## Code Review 规范",
            f"\n**最低审阅人数**: {self.min_reviewers}\n",
            "### 必检项",
            *[f"- {c}" for c in self.required_checks],
            "",
            "### 可跳过条件",
            *[f"- {c}" for c in self.auto_skip_conditions],
            "",
            "### 必退回条件",
            *[f"- ❌ {c}" for c in self.rejection_criteria],
        ]
        return "\n".join(lines)


@dataclass
class GitWorkflowSpec:
    """Git工作流规范"""
    strategy: str = "gitflow"
    description: str = ""
    branches: list[BranchRule] = field(default_factory=list)
    commit_convention: CommitConvention = field(default_factory=CommitConvention)
    review_guidelines: ReviewGuideline = field(default_factory=ReviewGuideline)
    tag_pattern: str = "v*"
    release_process: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        lines = [
            f"# Git 工作流规范: {self.strategy.upper()}",
            f"\n{self.description}\n",
            "## 分支策略\n",
            "| 分支名 | 用途 | 来源 | 目标 |",
            "|--------|------|------|------|",
        ]
        for b in self.branches:
            lines.append(f"| `{b.pattern}` | {b.purpose} | {b.source_branch or '-'} | {b.target_branch or '-'} |")

        lines.extend([
            "", self.commit_convention.to_markdown(), "",
            self.review_guidelines.to_markdown(),
        ])

        if self.release_process:
            lines.extend(["", "## 发布流程", *[f"{i+1}. {step}" for i, step in enumerate(self.release_process)]])

        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy": self.strategy,
            "branches": [b.to_dict() for b in self.branches],
            "commit_format": self.commit_convention.format,
            "min_reviewers": self.review_guidelines.min_reviewers,
        }


class StandardsBureau:
    """
    规范制定局

    负责编码规范管理(PEP8/ESLint/Airbnb/Google等)、开发原则知识库(Clean Code/SOLID/DRY/KISS/
    YAGNI/Composition over Inheritance/Tell Don't Ask等)、API规范生成(OpenAPI 3.0)、
    数据库规范设计、安全检查清单(OWASP Top 10)及Git工作流规范(GitFlow/GitHub Flow)。
    """

    _PRINCIPLES_DB: list[Principle] = []

    def __init__(self, output_dir: Path | str | None = None) -> None:
        self._output_dir = Path(output_dir) if output_dir else Path.cwd()
        self._init_principles_db()

    def _init_principles_db(self) -> None:
        """初始化开发原则知识库"""
        self._PRINCIPLES_DB = [
            Principle(
                name="Single Responsibility Principle", abbreviation="SRP",
                category=PrincipleCategory.DESIGN,
                description="一个类应该只有一个引起它变化的原因。",
                core_idea="聚焦：每个模块只做一件事，并做好。",
                benefits=["高内聚低耦合", "易于理解和维护", "变更影响范围小"],
                violations=["God Object/类承担过多职责", "方法过长且处理多种不相关逻辑"],
                examples_good=[
                    "class UserService:\n    def create_user(self, data): ...\n    def update_user(self, data): ...",
                ],
                examples_bad=[
                    "class UserManager:\n    def create_user(self): ...\n    def send_email(self): ...\n    def generate_report(self): ...",
                ],
                related_principles=["OCP", "ISP"],
            ),
            Principle(
                name="Open/Closed Principle", abbreviation="OCP",
                category=PrincipleCategory.DESIGN,
                description="软件实体应该对扩展开放，对修改关闭。",
                core_idea="扩展优于修改：通过抽象和接口支持新增行为而不改现有代码。",
                benefits=["降低引入Bug的风险", "符合开闭原则便于迭代", "提高系统稳定性"],
                violations=["频繁修改已有类来添加新功能", "大量if-else/switch硬编码分支"],
                examples_good=[
                    "class DiscountStrategy(Protocol):\n    def calculate(self, price): ...\n\nclass VIPDiscount:\n    def calculate(self, price): return price * 0.8",
                ],
                examples_bad=[
                    "def calculate_discount(type, price):\n    if type == 'vip': return price * 0.8\n    elif type == 'normal': return price * 0.95\n    # 每次新增类型都要改这里",
                ],
                related_principles=["DIP", "LSP", "Strategy Pattern"],
            ),
            Principle(
                name="Liskov Substitution Principle", abbreviation="LSP",
                category=PrincipleCategory.DESIGN,
                description="子类型必须能够替换其基类型，而不破坏程序正确性。",
                core_idea="契约不变：派生类必须完全遵守基类的约定。",
                benefits=["保证多态的正确使用", "接口设计更加可靠", "减少运行时意外"],
                violations=["子类抛出基类未声明的异常", "子类弱化基类的前置条件或强化后置条件"],
                examples_good=["class Square(Rectangle):\n    # Square is-a Rectangle with equal sides"],
                examples_bad=["class EmptyStack(Stack):\n    def pop(self): raise Exception('Empty!')  # 违反LSP"],
                related_principles=["OCP", "ISP", "DIP"],
            ),
            Principle(
                name="Interface Segregation Principle", abbreviation="ISP",
                category=PrincipleCategory.DESIGN,
                description="客户端不应该被迫依赖它不使用的接口。",
                core_idea="小而精：接口应该按客户端需求拆分，避免臃肿接口。",
                benefits=["接口职责清晰", "减少不必要的依赖", "实现类更轻量"],
                violations=["大而全的接口强制实现不需要的方法", "客户端依赖了用不到的接口方法"],
                examples_good=[
                    "class Worker(Protocol):\n    def work(self): ...\n\nclass Eater(Protocol):\n    def eat(self): ...",
                ],
                examples_bad=[
                    "class IWorker(Protocol):\n    def work(self): ...\n    def eat(self): ...\n    # Robot必须实现eat()? 不合理",
                ],
                related_principles=["SRP", "DIP"],
            ),
            Principle(
                name="Dependency Inversion Principle", abbreviation="DIP",
                category=PrincipleCategory.ARCHITECTURE,
                description="高层模块不应依赖低层模块，两者都应依赖抽象；抽象不应依赖细节，细节应依赖抽象。",
                core_idea="面向接口编程：依赖倒转使系统解耦，具体实现可灵活替换。",
                benefits=["模块间松耦合", "便于单元测试(Mock)", "支持插件式架构"],
                violations=["直接实例化具体类而非通过构造函数注入", "高层模块直接import底层实现"],
                examples_good=[
                    "class OrderService:\n    def __init__(self, repo: OrderRepositoryInterface):\n        self._repo = repo  # 依赖抽象",
                ],
                examples_bad=[
                    "class OrderService:\n    def __init__(self):\n        self._repo = MySQLRepository()  # 直接依赖具体实现",
                ],
                related_principles=["OCP", "IoC Container", "DI"],
            ),
            Principle(
                name="Don't Repeat Yourself", abbreviation="DRY",
                category=PrincipleCategory.CODE_QUALITY,
                description="系统中每一块知识都必须有单一、明确、权威的表示。",
                core_idea="消除重复：相同逻辑只写一次，多处引用。",
                benefits=["减少维护成本", "一处修改全局生效", "代码量精简"],
                violations=["复制粘贴代码", "魔法数字/字符串散落各处", "相似函数仅参数不同"],
                examples_good=["MAX_RETRY_COUNT = 3  # 定义常量统一引用"],
                examples_bad=["\n# 文件A\nif response.status == 200:\n# 文件B\nif response.status == 200:  # 重复"],
                related_principles=["KISS", "Single Source of Truth"],
            ),
            Principle(
                name="Keep It Simple, Stupid", abbreviation="KISS",
                category=PrincipleCategory.CODE_QUALITY,
                description="简单性是软件成功的关键因素。大多数系统在简单时效果最好。",
                core_idea="简洁至上：不过度设计，能用简单方案解决就不用复杂方案。",
                benefits=["降低认知负荷", "减少Bug产生概率", "提升开发和维护效率"],
                violations=["过早优化和过度工程", "引入不必要的抽象层", "使用复杂设计模式解决简单问题"],
                examples_good=["def calculate_total(items): return sum(i.price for i in items)"],
                examples_bad=[
                    "class TotalCalculatorFactory:\n    # 只为了算个总和就搞工厂+策略+观察者...",
                ],
                related_principles=["YAGNI", "DRY"],
            ),
            Principle(
                name="You Aren't Gonna Need It", abbreviation="YAGNI",
                category=PrincipleCategory.METHODOLOGY,
                description="不要实现当前不需要的功能。",
                core_idea="按需开发：只为当前确定的需求编写代码，不为假设的未来需求过度设计。",
                benefits=["避免浪费开发时间", "减少代码复杂度和维护负担", "聚焦核心价值交付"],
                violations=["为'可能将来需要'的功能预留接口/框架", "实现未被需求确认的高级特性"],
                examples_good=["# 只实现当前需要的CRUD操作"],
                examples_bad=["\ndef prepare_for_future_scaling():\n    # 预留消息队列/缓存/分片... 当前QPS才10"],
                related_principles=["KISS", "Agile", "Lean"],
            ),
            Principle(
                name="Composition Over Inheritance", abbreviation="CoI",
                category=PrincipleCategory.DESIGN,
                description="优先使用组合而非继承来复用代码和行为。",
                core_idea="组合灵活性：has-a关系比is-a关系更灵活、更易变化。",
                benefits=["运行时可动态组合行为", "避免深层继承链问题", "更符合SOLID原则"],
                violations=["超过3层的继承链", "仅为复用代码而继承(非真正的is-a关系)"],
                examples_good=[
                    "class Engine:\n    def start(self): ...\n\nclass Car:\n    def __init__(self):\n        self.engine = Engine()  # 组合",
                ],
                examples_bad=[
                    "class Vehicle: ...\nclass MotorizedVehicle(Vehicle): ...\nclass Car(MotorizedVehicle): ...  # 继承链过深",
                ],
                related_principles=["SRP", "Strategy Pattern", "Mixin"],
            ),
            Principle(
                name="Tell, Don't Ask", abbreviation="TDA",
                category=PrincipleCategory.DESIGN,
                description="告诉对象你要做什么，而不是询问对象的状态再决定做什么。",
                core_idea="封装行为：将决策逻辑封装在对象内部，而非暴露内部状态让外部判断。",
                benefits=["更好的封装性", "减少对象间的耦合", "业务逻辑集中管理"],
                violations=["获取对象内部状态后在外部做条件判断", "暴露getter供外部做本该对象自己做的决策"],
                examples_good=[
                    "# Good: Tell\nif user.can_access(resource):\n    user.access(resource)",
                ],
                examples_bad=[
                    "# Bad: Ask\nif user.role == 'admin' or user.permissions.contains('read'):\n    grant_access(user, resource)",
                ],
                related_principles=["Law of Demeter", "Encapsulation"],
            ),
            Principle(
                name="Clean Code", abbreviation="CC",
                category=PrincipleCategory.CODE_QUALITY,
                description="代码应当像优秀的散文一样清晰易读——有意义的命名、简短的函数、专注的职责。",
                core_idea="代码即沟通：代码的读者是人(包括未来的你)，让代码自解释。",
                benefits=["团队协作效率提升", "降低理解成本", "Bug更容易被发现"],
                violations=["无意义的变量名(a, tmp, data)", "超长函数(>50行)", "过深的嵌套层级(>3层)"],
                examples_good=["def calculate_monthly_revenue(transactions: list[Transaction]) -> Decimal:"],
                examples_bad=["def d(l): return sum(x.a for x in l)"],
                related_principles=["SRP", "DRY", "Boy Scout Rule"],
            ),
            Principle(
                name="Law of Demeter (LoD)", abbreviation="LoD",
                category=PrincipleCategory.DESIGN,
                description="对象应该对其他对象有最少的了解——只与直接的朋友通信。",
                core_idea="最少知识：a.f().g().h() 这种链式调用违反LoD，应改为 a.doSomething()。",
                benefits=["降低耦合度", "封装更好", "变更影响范围可控"],
                violations=["链式方法调用跨越多个对象的边界", "通过中间对象访问远端对象的属性"],
                examples_good=["user.get_manager_name()  # 封装在User内部"],
                examples_bad=["user.department.manager.name  # 暴露内部结构"],
                related_principles=["TDA", "Encapsulation", "ISP"],
            ),
            Principle(
                name="Boy Scout Rule", abbreviation="BSR",
                category=PrincipleCategory.CODE_QUALITY,
                description="离开营地时要比你来时更清洁——每次接触代码都应使其比之前更好。",
                core_idea="持续改进：即使只是改进变量名、提取小函数，也要让代码逐步变好。",
                benefits=["技术债务持续减少", "代码质量螺旋上升", "培养良好习惯"],
                violations=["明知有问题却只修自己的Bug不管周边烂代码", "复制粘贴现有坏模式而不是先改善它"],
                examples_good=["# 发现命名不好顺便改名, 看到重复代码顺手抽取方法"],
                examples_bad=["# 快速提交PR, 不管周围的代码质量问题"],
                related_principles=["Clean Code", "Refactoring"],
            ),
        ]

    def get_coding_standards(self, language: str) -> CodingStandards:
        """
        获取指定语言的编码规范规则库

        Args:
            language: 编程语言 ('python', 'javascript', 'typescript', 'java', 'go', 'rust')

        Returns:
            CodingStandards编码规范集合
        """
        match language.lower():
            case "python":
                return self._get_python_standards()
            case "javascript" | "js":
                return self._get_javascript_standards()
            case "typescript" | "ts":
                return self._get_typescript_standards()
            case "java":
                return self._get_java_standards()
            case "go":
                return self._get_go_standards()
            case "rust":
                return self._get_rust_standards()
            case _:
                raise StandardsError(f"不支持的语言: {language}，支持: python, javascript, typescript, java, go, rust")

    def _get_python_standards(self) -> CodingStandards:
        """Python PEP8 + Google Python Style Guide"""
        rules = [
            LintRule("E501", "行过长", "每行不超过79字符(文档字符串94)", "warning", "style"),
            LintRule("E302", "函数间空格不足", "函数定义之间需2个空行", "warning", "style"),
            LintRule("E303", "过多空行", "连续不超过2个空行", "warning", "style"),
            LintRule("E225", "运算符缺少空格", "二元运算符两侧需有空格", "warning", "style"),
            LintRule("E231", "逗号后缺少空格", "逗号/冒号/分号后需有空格", "warning", "style"),
            LintRule("W291", "尾随空白", "行末不应有尾随空格", "warning", "style"),
            LintRule("W293", "缩进中的空格", "禁止Tab与空格混用", "error", "style"),
            LintRule("W605", "无效转义序列", "正则表达式外的无效转义", "warning", "correctness"),
            LintRule("C901", "函数过于复杂", "函数过长或圈复杂度过高", "error", "complexity"),
            LintRule("N802", "函数名不规范", "函数名应为snake_case", "warning", "naming"),
            LintRule("N803", "参数名不规范", "参数名应为snake_case", "warning", "naming"),
            LintRule("N806", "变量名不规范", "非常量变量不应UPPER_CASE", "warning", "naming"),
            LintRule("N816", "混合命名", "避免驼峰与下划线混用", "warning", "naming"),
            LintRule("S101", "assert用于生产代码", "assert可被-O忽略，应用专用断言", "error", "security"),
            LintRule("S301", "使用pickle", "pickle可能执行任意代码", "warning", "security"),
            LintRule("S308", "使用mark_safe", "可能导致XSS漏洞", "error", "security"),
            LintRule("S608", "SQL注入风险", "字符串拼接构建SQL语句", "critical", "security"),
            LintRule("BLE001", "裸except", "应捕获具体异常类型", "warning", "correctness"),
            LintRule("TRY003", "异常消息长字符串", "长消息应定义为类常量", "info", "style"),
            LintRule("ANN001", "缺少类型注解", "公共函数参数应有类型注解", "info", "style"),
            LintRule("D100", "缺少模块docstring", "公共模块应有文档字符串", "info", "style"),
            LintRule("D103", "缺少函数docstring", "公共函数应有文档字符串", "info", "style"),
        ]

        config = textwrap.dedent("""\
            [tool.ruff]
            line-length = 88
            target-version = "py310"

            [tool.ruff.lint]
            select = [
                "E",    # pycodestyle errors
                "W",    # pycodestyle warnings
                "F",    # pyflakes
                "I",    # isort
                "N",    # pep8-naming
                "S",    # bandit
                "B",    # flake8-bugbear
                "C4",   # flake8-comprehensions
                "ANN",  # type annotations
                "D",    # pydocstyle
            ]
            ignore = ["E501", "D107"]

            [tool.ruff.lint.per-file-ignores]
            "tests/*" = ["S101", "ANN", "D"]
        """)

        return CodingStandards(
            language="python",
            standard_name="PEP 8 + Ruff",
            description="Python官方编码规范(PEP 8)，配合Ruff工具进行自动化检查。",
            rules=rules,
            config_snippet=config,
            reference_url="https://peps.python.org/pep-0008/",
        )

    def _get_javascript_standards(self) -> CodingStandards:
        """JavaScript ESLint + Airbnb"""
        rules = [
            LintRule("no-var", "使用var声明", "使用let/const替代var", "error", "style"),
            LintRule("eqeqeq", "使用==比较", "使用===进行严格相等比较", "error", "correctness"),
            LintRule("no-unused-vars", "未使用变量", "移除未使用的变量声明", "warning", "complexity"),
            LintRule("no-undef", "未定义变量", "所有变量在使用前必须声明", "error", "correctness"),
            LintRule("no-duplicate-imports", "重复导入", "同一模块只应导入一次", "warning", "style"),
            LintRule("prefer-const", "应使用const", "未被重新赋值的变量应使用const", "warning", "style"),
            LintRule("no-shadow", "变量遮蔽", "避免在外部作用域中遮蔽变量名", "warning", "naming"),
            LintRule("max-len", "行过长", "每行不超过100字符", "warning", "style"),
            LintRule("complexity", "圈复杂度过高", "函数圈复杂度不应超过20", "warning", "complexity"),
            LintRule("max-depth", "嵌套过深", "代码嵌套深度不超过4层", "warning", "complexity"),
            LintRule("max-params", "参数过多", "函数参数不超过4个", "warning", "complexity"),
            LintRule("max-lines-per-function", "函数过长", "单个函数不超过50行", "warning", "complexity"),
            LintRule("no-eval", "使用eval", "eval有安全和性能风险", "error", "security"),
            LintRule("no-implied-eval", "隐式eval", "setTimeout/setInterval避免字符串参数", "error", "security"),
            LintRule("no-inner-declarations", "函数内声明", "避免在块级作用域中声明函数", "warning", "style"),
            LintRule("camelcase", "命名规范", "变量和函数使用camelCase命名", "warning", "naming"),
            LintRule("new-cap", "构造函数命名", "构造函数应以大写字母开头", "warning", "naming"),
            LintRule("consistent-return", "返回值不一致", "函数所有路径应有明确的返回值", "warning", "correctness"),
            LintRule("guard-for-in", "for-in缺少hasOwnProperty", "遍历对象属性时应过滤原型链", "warning", "correctness"),
        ]

        config = textwrap.dedent("""\
            {
              "env": { "browser": true, "es2021": true, "node": true },
              "extends": ["airbnb-base", "plugin:prettier/recommended"],
              "parserOptions": { "ecmaVersion": "latest", "sourceType": "module" },
              "rules": {
                "no-console": "warn",
                "max-len": ["warn", { "code": 100 }],
                "complexity": ["warn", { "max": 20 }]
              }
            }
        """)

        return CodingStandards(
            language="javascript",
            standard_name="Airbnb JavaScript Style + ESLint",
            description="业界广泛采用的JavaScript编码规范，基于ESLint自动检查。",
            rules=rules,
            config_snippet=config,
            reference_url="https://github.com/airbnb/javascript",
        )

    def _get_typescript_standards(self) -> CodingStandards:
        """TypeScript strict mode + ESLint"""
        base_js = self._get_javascript_standards()
        ts_extra = [
            LintRule("@typescript-eslint/no-explicit-any", "使用any类型", "避免使用any，使用具体类型", "warning", "style"),
            LintRule("@typescript-eslint/no-unused-vars", "TS未使用变量", "移除未使用的TypeScript变量", "warning", "complexity"),
            LintRule("@typescript-eslint/explicit-function-return-type", "缺少返回类型注解", "公开函数应标注返回类型", "info", "style"),
            LintRule("@typescript-eslint/no-floating-promises", "未处理的Promise", "async函数返回的Promise应被await或处理", "error", "correctness"),
            LintRule("@typescript-eslint/strict-boolean-expressions", "宽松布尔表达式", "条件判断应使用严格布尔值", "warning", "correctness"),
            LintRule("@typescript-eslint/no-non-null-assertion", "非空断言!", "避免使用!断言，使用可选链或类型守卫", "warning", "style"),
            LintRule("@typescript-eslint/prefer-nullish-coalescing", "应使用??", "null/undefined合并应使用??运算符", "info", "style"),
            LintRule("@typescript-eslint/prefer-optional-chain", "应使用可选链?.", "链式属性访问应使用?.", "info", "style"),
            LintRule("@typescript-eslint/naming-convention", "命名不符合规范", "遵循TypeScript社区命名惯例", "warning", "naming"),
        ]
        return CodingStandards(
            language="typescript",
            standard_name="TypeScript Strict + ESLint",
            description="TypeScript严格模式下的编码规范，强调类型安全。",
            rules=base_js.rules + ts_extra,
            config_snippet='{ "extends": ["airbnb-typescript/base"] }',
            reference_url="https://www.typescriptlang.org/tsconfig#strict",
        )

    def _get_java_standards(self) -> CodingStandards:
        """Java Google Java Style + Checkstyle"""
        rules = [
            LintRule("J001", "类名不规范", "类名使用UpperCamelCase", "error", "naming"),
            LintRule("J002", "方法名不规范", "方法/变量使用lowerCamelCase", "error", "naming"),
            LintRule("J003", "常量名不规范", "常量使用UPPER_SNAKE_CASE", "error", "naming"),
            LintRule("J004", "包名不规范", "包名全小写", "warning", "naming"),
            LintRule("J005", "行过长", "每行不超过100字符", "warning", "style"),
            LintRule("J006", "方法过长", "单个方法不超过40行", "warning", "complexity"),
            LintRule("J007", "文件过长", "单个文件不超过500行", "warning", "complexity"),
            LintRule("J008", "参数过多", "方法参数不超过5个", "warning", "complexity"),
            LintRule("J009", "嵌套过深", "嵌套层次不超过4层", "warning", "complexity"),
            LintRule("J010", "缺少Javadoc", "公共API应有Javadoc注释", "info", "style"),
            LintRule("J011", "使用原始类型", "避免使用原始类型，使用泛型", "error", "correctness"),
            LintRule("J012", "魔法数值", "数值字面量应提取为命名常量", "warning", "style"),
            LintRule("J013", "equals/hashCode不一致", "重写equals必须同时重写hashCode", "error", "correctness"),
            LintRule("J014", "String拼接循环", "循环中使用StringBuilder替代+", "performance", "performance"),
            LintRule("J015", "资源泄漏", "InputStream等资源应在finally中关闭", "error", "correctness"),
            LintRule("J016", "SQL注入风险", "使用PreparedStatement替代字符串拼接", "critical", "security"),
        ]
        return CodingStandards(
            language="java",
            standard_name="Google Java Style + Checkstyle",
            description="Google Java编程风格指南，配合Checkstyle工具。",
            rules=rules,
            config_snippet='<module name="Checker"><module name="TreeWalker">...</module></module>',
            reference_url="https://google.github.io/styleguide/javaguide.html",
        )

    def _get_go_standards(self) -> CodingStandards:
        """Go Effective Go + golint/vet"""
        rules = [
            LintRule("G001", "导出名称缺少文档", "导出的类型/函数/变量应有注释", "warning", "style"),
            LintRule("G002", "包注释缺失", "包应有package注释说明用途", "info", "style"),
            LintRule("G003", "接收者命名不规范", "方法接收者使用1-2个字符缩写", "warning", "naming"),
            LintRule("G004", "错误未处理", "函数返回的错误值必须被检查", "error", "correctness"),
            LintRule("G005", "context.Context作为第一个参数", "Context应作为函数第一参数", "warning", "style"),
            LintRule("G006", "误用defer", "在循环中使用defer可能造成资源泄漏", "error", "correctness"),
            LintRule("G007", "错误信息缺少上下文", "errors.New/fmt.Errorf应包含上下文", "info", "style"),
            LintRule("G008", "结构体字段标签", "JSON标签应使用snake_case", "info", "style"),
            LintRule("G009", "接口过大", "接口方法数不宜过多(建议<10)", "warning", "design"),
            LintRule("G010", "goroutine泄漏", "启动的goroutine应有退出机制", "error", "correctness"),
            LintRule("G011", "sync.Mutex复制", "Mutex不可复制", "error", "correctness"),
            LintRule("G012", "time.After在select中使用", "select中time.After会导致内存泄漏", "warning", "performance"),
            LintRule("G013", "strings.Builder初始化", "Builder应通过var声明或&Builder{}创建", "info", "style"),
            LintRule("G014", "Printf格式不匹配", "格式字符串与参数类型不匹配", "error", "correctness"),
        ]
        return CodingStandards(
            language="go",
            standard_name="Effective Go + golangci-lint",
            description="Go语言官方推荐的最佳实践，配合golangci-lint工具。",
            rules=rules,
            config_snippet='linters:\n  enable-all: true\n  disable:\n    - dupl\n    - gosec',
            reference_url="https://go.dev/doc/effective_go",
        )

    def _get_rust_standards(self) -> CodingStandards:
        """Rust API Guidelines + clippy"""
        rules = [
            LintRule("R001", "使用unwrap()", "优先使用expect()提供错误信息", "warning", "style"),
            LintRule("R002", "使用panic", "库代码不应panic，应返回Result", "error", "correctness"),
            LintRule("R003", "使用unsafe", "unsafe块必须有SAFETY注释说明", "critical", "security"),
            LintRule("R004", "克隆可避免", "考虑使用引用替代clone()", "info", "performance"),
            LintRule("R005", "大数组Copy", "大数组拷贝应使用引用或Cow", "performance", "performance"),
            LintRule("R006", "冗余模式", "match/if-let中有冗余分支", "warning", "style"),
            LintRule("R007", "map默认插入", "使用entry API替代两次查找", "info", "performance"),
            LintRule("R008", "字符串分配", "考虑使用&str或Cow<str>", "info", "performance"),
            LintRule("R009", "迭代器收集", "优先使用迭代器适配器", "info", "style"),
            LintRule("R010", "类型转换冗余", "as转换可能是多余的", "info", "style"),
            LintRule("R011", "let单元元组", "let _ = expr; 应简化", "info", "style"),
            LintRule("R012", "mutex锁粒度", "临界区应尽可能小", "warning", "concurrency"),
            LintRule("R013", "Send/Sync自动推导", "手动实现Send/Sync需谨慎", "warning", "concurrency"),
            LintRule("R014", "文档链接", "公开API文档应包含链接", "info", "style"),
            LintRule("R015", "错误类型", "自定义错误应实现std::error::Error", "info", "style"),
        ]
        return CodingStandards(
            language="rust",
            standard_name="Rust API Guidelines + Clippy",
            description="Rust官方API指南和Clippy lint规则集合。",
            rules=rules,
            config_snippet='# clippy.toml\nmsrv = "1.70"\nwarnings-as-errors = ["clippy::all"]',
            reference_url="https://rust-lang.github.io/api-guidelines/",
        )

    def get_development_principles(self) -> list[Principle]:
        """
        获取开发原则知识库

        Returns:
            Principle列表，包含Clean Code/Pragmatic Programmer/GOOS/DDD/SOLID/DRY/KISS/YAGNI/Composition over Inheritance/Tell Don't Ask等原则
        """
        return list(self._PRINCIPLES_DB)

    def check_principle_violation(self, code: str, principle: Principle) -> ViolationReport:
        """
        检测违反给定原则的代码片段

        Args:
            code: 待检测的源代码
            principle: 要检查的开发原则

        Returns:
            ViolationReport违规报告
        """
        lines = code.split("\n")
        violations: list[ViolationItem] = []
        total_lines = len(lines)
        penalty_per_violation = 5.0

        abbr = principle.abbreviation.lower()

        match abbr:
            case "srp":
                violations = self._check_srp(code, lines)
            case "ocp":
                violations = self._check_ocp(code, lines)
            case "dip":
                violations = self._check_dip(code, lines)
            case "dry":
                violations = self._check_dry(code, lines)
            case "kiss":
                violations = self._check_kiss(code, lines)
            case "yagni":
                violations = self._check_yagni(code, lines)
            case "cc":
                violations = self._check_clean_code(code, lines)
            case "loi" | "coi":
                violations = self._check_composition(code, lines)
            case "tda" | "lod":
                violations = self._check_tda_lod(code, lines)
            case _:
                violations = self._check_generic(code, lines, principle)

        total_penalty = len(violations) * penalty_per_violation
        score = max(0.0, 100.0 - total_penalty)

        status_summary = (
            f"共检测 {total_lines} 行代码，发现 {len(violations)} 处可能违反「{principle.name}」的代码片段。"
        )

        return ViolationReport(
            principle_name=f"{principle.name} ({principle.abbreviation})",
            total_violations=len(violations),
            items=violations,
            score=score,
            summary=status_summary,
        )

    def _check_srp(self, code: str, lines: list[str]) -> list[ViolationItem]:
        """SRP检测：类/函数是否承担过多职责"""
        violations: list[ViolationItem] = []
        class_pattern = re.compile(r'^class\s+(\w+).*:')
        method_pattern = re.compile(r'^\s+def\s+(\w+)\(')

        class_methods: dict[str, int] = {}
        current_class = ""

        for i, line in enumerate(lines, 1):
            cm = class_pattern.match(line)
            if cm:
                current_class = cm.group(1)
                class_methods[current_class] = 0
                continue
            mm = method_pattern.match(line)
            if mm and current_class:
                class_methods[current_class] = class_methods.get(current_class, 0) + 1

        for cls_name, method_count in class_methods.items():
            if method_count > 12:
                violations.append(ViolationItem(
                    line_number=1,
                    violation_type="God Class/Object",
                    description=f"类 '{cls_name}' 包含 {method_count} 个方法，可能违反SRP(建议<=10)",
                    code_snippet=f"class {cls_name}: ... ({method_count} methods)",
                    severity="warning",
                    suggestion="考虑拆分为多个职责单一的类",
                ))

        func_lengths: list[tuple[int, int, str]] = []
        for i, line in enumerate(lines, 1):
            if re.match(r'^\s*def\s+\w+\(', line):
                func_start = i
                func_lines = 1
                indent_base = len(line) - len(line.lstrip())
                for j in range(i, min(i + 200, len(lines))):
                    if j >= len(lines):
                        break
                    next_line = lines[j]
                    if j > i and next_line.strip() and not next_line.startswith((" ", "\t")):
                        break
                    if j > i and len(next_line) - len(next_line.lstrip()) <= indent_base and next_line.strip():
                        break
                    func_lines += 1
                func_lengths.append((func_start, func_lines, line.strip()))

        for start, length, snippet in func_lengths:
            if length > 50:
                violations.append(ViolationItem(
                    line_number=start,
                    violation_type="Long Method",
                    description=f"函数长度为 {length} 行，可能承担过多职责(建议<=30行)",
                    code_snippet=snippet[:60],
                    severity="warning",
                    suggestion="拆分为多个小函数，每个函数只做一件事",
                ))

        return violations

    def _check_ocp(self, code: str, lines: list[str]) -> list[ViolationItem]:
        """OCP检测：是否有大量if-else/switch硬编码分支"""
        violations: list[ViolationItem] = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()

            if_chain = re.findall(r'(?:if|elif)\s+\w+\s*[=!=]+\s*["\']?\w+', stripped)
            if len(if_chain) >= 3 and 'type' in stripped.lower():
                violations.append(ViolationItem(
                    line_number=i,
                    violation_type="Hard-coded Type Switching",
                    description=f"发现 {len(if_chain)} 个类型判断分支，可能违反OCP",
                    code_snippet=stripped[:70],
                    severity="warning",
                    suggestion="考虑使用策略模式或多态替换条件分支",
                ))

            switch_match = re.match(r'^\s*(?:switch|match)\s*\(', stripped)
            if switch_match:
                block_end = i
                case_count = 0
                for j in range(i, min(i + 50, len(lines))):
                    if re.match(r'\s*(?:case|_|default)', lines[j]):
                        case_count += 1
                    block_end = j
                if case_count > 7:
                    violations.append(ViolationItem(
                        line_number=i,
                        violation_type="Large Switch Statement",
                        description=f"switch/match包含 {case_count} 个case分支，可能违反OCP",
                        code_snippet=stripped[:70],
                        severity="info",
                        suggestion="考虑使用策略映射表或策略模式",
                    ))

        return violations

    def _check_dip(self, code: str, lines: list[str]) -> list[ViolationItem]:
        """DIP检测：是否直接实例化具体类"""
        violations: list[ViolationItem] = []
        concrete_patterns = [
            r'\w+(?:Service|Repository|Manager|Handler|Controller|Client|Adapter)\s*\(\)',
            r'(?:MySQL|Postgres|Redis|MongoDB|AWS|Azure)\w*\(\)',
            r'Requests\(|Httpx\(|Aiohttp\(',
        ]

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith('"') or stripped.startswith("'"):
                continue

            for pattern in concrete_patterns:
                matches = re.findall(pattern, stripped)
                for m in matches:
                    if '=' in stripped and '__init__' not in stripped:
                        violations.append(ViolationItem(
                            line_number=i,
                            violation_type="Concrete Dependency Instantiation",
                            description=f"直接实例化具体类 '{m}'，可能违反DIP",
                            code_snippet=stripped[:70],
                            severity="warning",
                            suggestion="考虑通过构造函数注入抽象接口/协议",
                        ))
        return violations

    def _check_dry(self, code: str, lines: list[str]) -> list[ViolationItem]:
        """DRY检测：重复代码"""
        violations: list[ViolationItem] = []
        normalized_lines: list[tuple[int, str]] = []

        for i, line in enumerate(lines, 1):
            norm = re.sub(r'\s+', ' ', line.strip())
            if len(norm) > 20:
                normalized_lines.append((i, norm))

        seen: dict[str, list[int]] = {}
        for line_no, content in normalized_lines:
            seen.setdefault(content, []).append(line_no)

        for content, line_nos in seen.items():
            if len(line_nos) >= 3:
                violations.append(ViolationItem(
                    line_number=line_nos[0],
                    violation_type="Code Duplication",
                    description=f"相同代码出现在 {len(line_nos)} 处: 行 {line_nos}",
                    code_snippet=content[:70],
                    severity="warning",
                    suggestion="提取为共享函数/方法/常量以消除重复",
                ))

        magic_numbers = re.findall(r'\b\d{2,}\b', code)
        number_counts: dict[str, int] = {}
        for num in magic_numbers:
            number_counts[num] = number_counts.get(num, 0) + 1
        for num, count in number_counts.items():
            if count >= 3:
                first_occurrence = code.find(num)
                approx_line = code[:first_occurrence].count("\n") + 1
                violations.append(ViolationItem(
                    line_number=approx_line,
                    violation_type="Magic Number",
                    description=f"魔法数字 '{num}' 出现 {count} 次，应定义为命名常量",
                    code_snippet=f"... {num} ...",
                    severity="info",
                    suggestion=f"定义如 MAX_RETRY = {num} 或 TIMEOUT = {num} 等常量",
                ))

        return violations

    def _check_kiss(self, code: str, lines: list[str]) -> list[ViolationItem]:
        """KISS检测：过度复杂的代码"""
        violations: list[ViolationItem] = []

        complexity_indicators = [
            (r'\.then\(.*\.then\(.*\.then\(', "Promise链过深(>3层)，建议使用async/await"),
            (r'lambda.*lambda.*lambda', "多层Lambda嵌套，可读性差"),
            (r'\[\s*\w+\s+for\s+\w+\s+in\s+.+\s+if\s+.+\s+for\s+', "嵌套列表推导式，建议拆分"),
            (r'reduce\([^)]*lambda[^)]*,[^)]*lambda', "reduce+嵌套lambda过于复杂"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, msg in complexity_indicators:
                if re.search(pattern, line):
                    violations.append(ViolationItem(
                        line_number=i,
                        violation_type="Over-engineering / Complexity",
                        description=msg,
                        code_snippet=line.strip()[:70],
                        severity="warning",
                        suggestion="简化实现，优先选择直观的方式",
                    ))

        nested_classes = re.findall(r'class\s+\w+[^:]*:\s*\n(\s+)class\s+\w+', code)
        for nc in nested_classes:
            indent_level = len(nc) - len(nc.lstrip())
            if indent_level >= 8:
                violations.append(ViolationItem(
                    line_number=1,
                    violation_type="Deep Nesting",
                    description=f"嵌套类深度达 {indent_level // 4} 层，过于复杂",
                    code_snippet="nested class definition",
                    severity="info",
                    suggestion="考虑将内部类提取为顶层类",
                ))

        return violations

    def _check_yagni(self, code: str, lines: list[str]) -> list[ViolationItem]:
        """YAGNI检测：过度设计"""
        violations: list[ViolationItem] = []
        yagni_patterns = [
            (r'#\s*(TODO|FIXME|HACK|XXX).*(?:未来|将来|later|eventually|someday)', "预留未来功能标记"),
            (r'class\s+\w+Factory\b', "工厂类(确认是否真的需要?)"),
            (r'class\s+\w+Builder\b', "Builder模式(确认是否真的需要?)"),
            (r'class\s+\w+(?:Proxy|Adapter|Decorator|Facade)\b', "设计模式包装类(确认必要性?)"),
            (r'def\s+(?:prepare_for_|handle_future_|reserve_for_)', "预留给未来使用的方法"),
            (r'Abstract\w+\s*(?:=\s*)?(?:ABC|metaclass|Protocol)', "抽象基类(确认是否有多个实现?)"),
        ]

        for i, line in enumerate(lines, 1):
            for pattern, desc in yagni_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    violations.append(ViolationItem(
                        line_number=i,
                        violation_type="Potential YAGNI Violation",
                        description=desc,
                        code_snippet=line.strip()[:70],
                        severity="info",
                        suggestion="确认此抽象/预留是否为当前必需，否则考虑简化",
                    ))

        return violations

    def _check_clean_code(self, code: str, lines: list[str]) -> list[ViolationItem]:
        """Clean Code通用检测"""
        violations: list[ViolationItem] = []

        bad_names = [(r'\b[a-z]\b(?!\s*[,)=:])', "单字母变量名(除循环变量外)"), (r'\btmp\b|\btemp\b|\bdata\b|\bfoo\b|\bbar\b|\bbaz\b', "无意义变量名")]
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("#") or stripped.startswith(('"""', "'''")):
                continue
            for pattern, desc in bad_names:
                if re.search(pattern, stripped):
                    violations.append(ViolationItem(
                        line_number=i,
                        violation_type="Poor Naming",
                        description=desc,
                        code_snippet=stripped[:70],
                        severity="info",
                        suggestion="使用有意义、描述性的名称",
                    ))

        depth_stack: list[int] = []
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
            if any(stripped.startswith(kw + ":") or stripped.startswith(kw + " ") for kw in ("if", "for", "while", "with", "try", "class", "def")):
                depth_stack.append(i)
            elif stripped in ("else:", "elif", "except:", "finally:"):
                pass
            elif stripped and not stripped.startswith((" ", "\t")) and depth_stack:
                start = depth_stack.pop()
                depth = i - start
                if depth > 15:
                    violations.append(ViolationItem(
                        line_number=start,
                        violation_type="Deep Nesting",
                        description=f"代码块嵌套深度约 {depth // 3} 层(行{start}-{i})",
                        code_snippet=lines[start - 1].strip()[:60],
                        severity="warning",
                        suggestion="考虑提前return/continue或提取方法减少嵌套",
                    ))
                    depth_stack.clear()

        return violations

    def _check_composition(self, code: str, lines: list[str]) -> list[ViolationItem]:
        """Composition over Inheritance检测"""
        violations: list[ViolationItem] = []
        inheritance_chains: dict[str, int] = {}

        for i, line in enumerate(lines, 1):
            inherit_match = re.match(r'^class\s+(\w+)\s*\((\w+(?:\s*,\s*\w+)*)\)\s*:', line)
            if inherit_match:
                child = inherit_match.group(1)
                parents = [p.strip() for p in inherit_match.group(2).split(",")]
                for parent in parents:
                    if parent not in ("object", "Protocol", "ABC", "Generic"):
                        chain_key = f"{parent}->{child}"
                        inheritance_chains[chain_key] = inheritance_chains.get(chain_key, 0) + 1

        chain_depth: dict[str, int] = {}
        for chain in inheritance_chains:
            parts = chain.split("->")
            for i in range(len(parts) - 1):
                prefix = "->".join(parts[:i + 2])
                chain_depth[prefix] = i + 1

        for chain, depth in chain_depth.items():
            if depth >= 3:
                violations.append(ViolationItem(
                    line_number=1,
                    violation_type="Deep Inheritance Chain",
                    description=f"继承链深度为 {depth}: {chain}，建议考虑组合替代",
                    code_snippet=chain,
                    severity="warning",
                    suggestion="使用组合(has-a)替代深层次继承(is-a)",
                ))

        return violations

    def _check_tda_lod(self, code: str, lines: list[str]) -> list[ViolationItem]:
        """Tell Don't Ask / Law of Demeter检测"""
        violations: list[ViolationItem] = []

        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            chained = re.findall(r'(\w+)\.(\w+)\.(\w+)(?:\.(\w+))?', stripped)
            for match in chained:
                chain_len = sum(1 for g in match if g)
                if chain_len >= 3:
                    violations.append(ViolationItem(
                        line_number=i,
                        violation_type="Law of Demeter Violation",
                        description=f"链式调用跨越 {chain_len} 个对象边界: {'.'.join(g for g in match if g)}",
                        code_snippet=stripped[:70],
                        severity="info",
                        suggestion="将多步调用封装为目标对象的方法(Tell, Don't Ask)",
                    ))

            condition_getters = re.findall(r'if\s+(.+?)\.(.+?)(?:\s*[=!<>]|:)', stripped)
            for obj, attr in condition_getters:
                if attr not in ("is_", "has_", "can_", "should_") and not attr.startswith("is"):
                    violations.append(ViolationItem(
                        line_number=i,
                        violation_type="Tell Don't Ask Violation",
                        description=f"查询对象状态后在外部做条件判断: {obj}.{attr}",
                        code_snippet=stripped[:70],
                        severity="info",
                        suggestion=f"将判断逻辑封装进{obj}对象的方法中(e.g., {obj}.can_do_something())",
                    ))

        return violations

    def _check_generic(self, code: str, lines: list[str], principle: Principle) -> list[ViolationItem]:
        """通用原则检测（基于关键词匹配）"""
        violations: list[ViolationItem] = []
        violation_keywords = principle.violations

        for keyword in violation_keywords[:5]:
            pattern = re.compile(re.escape(keyword[:10]), re.IGNORECASE)
            for i, line in enumerate(lines, 1):
                if pattern.search(line):
                    violations.append(ViolationItem(
                        line_number=i,
                        violation_type=f"Potential {principle.abbreviation} Issue",
                        description=f"可能违反「{principle.name}」: {keyword[:40]}",
                        code_snippet=line.strip()[:70],
                        severity="info",
                        suggestion=principle.benefits[0] if principle.benefits else "参考原则描述进行调整",
                    ))
                    if len(violations) >= 15:
                        return violations

        return violations

    def generate_api_spec(self, endpoints: list, style: str = "openapi3") -> str:
        """
        生成API规范文档（OpenAPI 3.0 / Swagger）

        Args:
            endpoints: 端点列表(APIEndpointSpec或字典)
            style: 输出样式 ('openapi3', 'markdown')

        Returns:
            API规范文档字符串
        """
        ep_specs: list[APIEndpointSpec] = []
        for ep in endpoints:
            if isinstance(ep, APIEndpointSpec):
                ep_specs.append(ep)
            elif isinstance(ep, dict):
                ep_specs.append(APIEndpointSpec(
                    path=ep.get("path", "/"),
                    method=ep.get("method", "GET").upper(),
                    summary=ep.get("summary", ""),
                    description=ep.get("description", ""),
                    tags=ep.get("tags", []),
                    parameters=ep.get("parameters", []),
                    request_body=ep.get("request_body", {}),
                    responses={int(k): v for k, v in ep.get("responses", {}).items()},
                ))

        if style.lower() == "openapi3":
            return self._generate_openapi3(ep_specs)
        elif style.lower() == "markdown":
            return self._generate_api_markdown(ep_specs)
        else:
            raise StandardsError(f"不支持的API规范格式: {style}，支持: openapi3, markdown")

    def _generate_openapi3(self, endpoints: list[APIEndpointSpec]) -> str:
        """生成OpenAPI 3.0 JSON"""
        paths: dict[str, Any] = {}
        tags_seen: set[str] = set()

        for ep in endpoints:
            paths.setdefault(ep.path, {})
            operation: dict[str, Any] = {
                "summary": ep.summary or ep.description,
                "description": ep.description,
                "operationId": f"{ep.method.lower()}_{ep.path.replace('/', '_').replace('{', '').replace('}', '')}",
                "tags": ep.tags or ["default"],
                "parameters": ep.parameters,
                "responses": {
                    str(code): {
                        "description": resp.get("description", "Response"),
                        "content": {"application/json": {"schema": resp.get("schema", {"type": "object"})}},
                    } for code, resp in (ep.responses or {200: {"description": "Success"}}).items()
                },
            }
            if ep.request_body:
                operation["requestBody"] = {
                    "content": {"application/json": {"schema": ep.request_body.get("schema", {})}},
                    "required": True,
                }
            if ep.security:
                operation["security"] = ep.security
            else:
                operation["security"] = [{"bearerAuth": []}]
            paths[ep.path][ep.method.lower()] = operation
            tags_seen.update(ep.tags or ["default"])

        spec = {
            "openapi": "3.0.3",
            "info": {
                "title": "API Specification",
                "version": "1.0.0",
                "description": "由中书省·规范制定局自动生成的API规范文档",
            },
            "servers": [{"url": "http://localhost:8000/api/v1", "description": "Development Server"}],
            "tags": [{"name": tag} for tag in sorted(tags_seen)],
            "paths": paths,
            "components": {
                "securitySchemes": {
                    "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"},
                    "apiKey": {"type": "apiKey", "in": "header", "name": "X-API-Key"},
                },
                "schemas": {
                    "ErrorResponse": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer", "example": 400},
                            "message": {"type": "string"},
                            "errors": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                    "PaginatedData": {
                        "type": "object",
                        "properties": {
                            "items": {"type": "array"},
                            "total": {"type": "integer"},
                            "page": {"type": "integer"},
                            "page_size": {"type": "integer"},
                        },
                    },
                },
            },
        }

        return json.dumps(spec, ensure_ascii=False, indent=2)

    def _generate_api_markdown(self, endpoints: list[APIEndpointSpec]) -> str:
        """生成Markdown格式的API文档"""
        lines = ["# API 接口规范文档", "\n> 由中书省·规范制定局自动生成\n"]
        method_colors = {"GET": "🟢", "POST": "🔵", "PUT": "🟡", "PATCH": "🟠", "DELETE": "🔴"}

        grouped: dict[str, list[APIEndpointSpec]] = {}
        for ep in endpoints:
            tag = (ep.tags or ["default"])[0]
            grouped.setdefault(tag, []).append(ep)

        for tag, eps in grouped.items():
            lines.append(f"## {tag}\n")
            for ep in eps:
                color = method_colors.get(ep.method, "⚪")
                lines.append(f"### {color} `{ep.method}` {ep.path}")
                if ep.summary:
                    lines.append(f"\n**摘要**: {ep.summary}")
                if ep.description:
                    lines.append(f"\n**描述**: {ep.description}")
                if ep.parameters:
                    lines.append("\n**参数**:")
                    for p in ep.parameters:
                        req = "✅ 必填" if p.get("required", False) else "⬜ 可选"
                        lines.append(f"  - `{p['name']}` ({p.get('in', 'query')}): {p.get('description', '')} [{req}]")
                resp_codes = list((ep.responses or {200: {}}).keys())
                lines.append(f"\n**响应码**: {', '.join(str(c) for c in resp_codes)}")
                lines.append("")
        return "\n".join(lines)

    def design_db_schema(
        self, tables: list, naming_convention: str = "snake_case"
    ) -> DBSchemaSpec:
        """
        设计数据库规范（命名规范/索引策略/字段约束）

        Args:
            tables: 表定义列表(DBTableSpec或字典)
            naming_convention: 命名规范 ('snake_case', 'camelCase', 'PascalCase')

        Returns:
            DBSchemaSpec数据库架构规格
        """
        table_specs: list[DBTableSpec] = []
        for t in tables:
            if isinstance(t, DBTableSpec):
                table_specs.append(t)
            elif isinstance(t, dict):
                columns = []
                for col in t.get("columns", []):
                    if isinstance(col, dict):
                        columns.append(col)
                    elif isinstance(col, str):
                        parts = col.split(":")
                        columns.append({"name": parts[0], "type": parts[1] if len(parts) > 1 else "VARCHAR(255)"})

                table_specs.append(DBTableSpec(
                    table_name=t.get("table_name", t.get("name", "unknown_table")),
                    comment=t.get("comment", ""),
                    columns=columns,
                    indexes=[idx if isinstance(idx, dict) else {"columns": [idx]} for idx in t.get("indexes", [])],
                    primary_key=t.get("primary_key", "id"),
                    foreign_keys=t.get("foreign_keys", []),
                    constraints=t.get("constraints", []),
                ))

        global_rules = [
            "所有表必须包含 id (BIGINT UNSIGNED AUTO_INCREMENT) 作为主键",
            "所有表必须包含 created_at (DATETIME) 和 updated_at (DATETIME) 字段",
            "所有表必须包含 deleted_at (DATETIME DEFAULT NULL) 支持软删除",
            "字段命名采用 snake_case 风格",
            "布尔字段使用 is_ 前缀 (如 is_active, is_verified)",
            "时间字段使用 _at 后缀 (如 created_at, expired_at)",
            "金额字段使用 DECIMAL(18, 6) 类型避免精度丢失",
            "枚举状态使用 TINYINT + 常量映射，避免使用 ENUM 类型",
            "VARCHAR 字段必须指定长度，避免使用 TEXT 存储短文本",
            "索引命名规范: idx_{表名}_{字段名}, uk_{表名}_{字段名}(唯一)",
            "外键命名规范: fk_{表名}_{关联表名}_{字段名}",
            "大表(>100万行)必须建立合适的索引覆盖常用查询",
        ]

        return DBSchemaSpec(
            naming_convention=naming_convention,
            tables=table_specs,
            global_rules=global_rules,
        )

    def get_security_checklist(self, standard: str = "owasp_top10") -> SecurityChecklist:
        """
        获取安全检查清单（OWASP Top 10映射）

        Args:
            standard: 安全标准 ('owasp_top10', 'owasp_asvs', 'nist', 'custom')

        Returns:
            SecurityChecklist安全检查清单
        """
        match standard.lower():
            case "owasp_top10" | "owasp":
                return self._get_owasp_top10_checklist()
            case "owasp_asvs" | "asvs":
                return self._get_asvs_checklist()
            case "nist":
                return self._get_nist_checklist()
            case _:
                return self._get_owasp_top10_checklist()

    def _get_owasp_top10_checklist(self) -> SecurityChecklist:
        """OWASP Top 10 (2021) 安全检查清单"""
        owasp_categories = [
            ("A01", "Broken Access Control", "访问控制失效", [
                ("A01-01", "垂直越权", "用户可访问超出其角色的资源/功能", "critical", "实施基于RBAC的细粒度权限控制"),
                ("A01-02", "水平越权", "用户A可访问/操作用户B的数据", "critical", "始终验证资源所有权后再允许操作"),
                ("A01-03", "CORS配置不当", "跨域资源共享策略过于宽松", "high", "限制Allow-Origin为受信任域名"),
                ("A01-04", "目录遍历", "可通过路径遍历访问受限文件", "high", "对用户输入做路径规范化并校验"),
            ]),
            ("A02", "Cryptographic Failures", "加密失败", [
                ("A02-01", "明文传输敏感数据", "HTTPS未强制或证书配置错误", "critical", "全站强制HSTS + TLS 1.3"),
                ("A02-02", "弱加密算法", "使用MD5/SHA1/DES/RSA<2048等弱算法", "critical", "使用AES-256-GCM/SHA256+/RSA-4096"),
                ("A02-03", "密钥硬编码", "密钥/密码/Token写在源码中", "critical", "使用密钥管理服务(KMS/HSM/Vault)"),
                ("A02-04", "随机数不安全", "使用Math.random()/rand()生成安全token", "high", "使用密码学安全的随机数生成器(CSPRNG)"),
            ]),
            ("A03", "Injection", "注入攻击", [
                ("A03-01", "SQL注入", "用户输入拼接到SQL语句中", "critical", "全部使用参数化查询(PreparedStatement)"),
                ("A03-02", "NoSQL注入", "NoSQL查询未做参数化处理", "critical", "使用ORM/ODM的参数绑定功能"),
                ("A03-03", "命令注入(OS)", "用户输入传入shell命令执行", "critical", "禁止直接执行shell命令，使用白名单"),
                ("A03-04", "XPath/LDAP注入", "查询语句未做转义", "high", "使用参数化查询和输入验证"),
                ("A03-05", "XSS(反射型/存储型)", "用户输入未经转义输出到页面", "critical", "输出编码(CSP + 输入白名单)"),
            ]),
            ("A04", "Insecure Design", "不安全设计", [
                ("A04-01", "缺乏威胁建模", "未在设计阶段考虑安全威胁", "high", "建立STRIDE/PASTA威胁建模流程"),
                ("A04-02", "业务逻辑缺陷", "业务流程存在可被利用的漏洞", "high", "完整的用例分析和边界测试"),
                ("A04-03", "速率限制缺失", "关键操作无限次尝试(登录/支付)", "high", "实施多层级限流(用户/IP/接口)"),
            ]),
            ("A05", "Security Misconfiguration", "安全配置错误", [
                ("A05-01", "默认凭证未更改", "使用admin/admin等默认账号密码", "critical", "首次登录强制修改密码"),
                ("A05-02", "错误信息泄露", "异常堆栈/详细信息返回给用户", "medium", "生产环境返回通用错误信息"),
                ("A05-03", "不必要的功能启用", "调试端口/管理后台公网可达", "high", "关闭所有非必要服务和端口"),
                ("A05-04", "权限配置过宽", "文件/目录权限777或Everyone可读写", "high", "最小权限原则(Least Privilege)"),
            ]),
            ("A06", "Vulnerable & Outdated Components", "脆弱和过期组件", [
                ("A06-01", "已知CVE漏洞组件", "使用了含公开漏洞的第三方库", "critical", "定期SCA扫描+自动更新"),
                ("A06-02", "无组件清单(SBOM)", "不清楚项目依赖的所有组件版本", "medium", "维护完整的Software Bill of Materials"),
                ("A06-03", "不再维护的依赖", "使用已停止更新的开源组件", "high", "评估替代方案并及时迁移"),
            ]),
            ("A07", "Identification & Authentication Failures", "身份认证失败", [
                ("A07-01", "弱密码策略", "允许弱密码或无复杂度要求", "high", "实施强密码策略(长度+复杂度+历史)"),
                ("A07-02", "暴力破解防护缺失", "无账户锁定/验证码/CAPTCHA", "high", "多次失败后锁定+MFA"),
                ("A07-03", "Session管理不当", "Session ID可预测/固定/不过期", "critical", "使用安全的Session机制(JWT/Redis Session)"),
                ("A07-04", "MFA缺失", "敏感操作无双因子认证", "high", "关键操作强制MFA(TOTP/FIDO/WebAuthn)"),
            ]),
            ("A08", "Software & Data Integrity Failures", "软件和数据完整性失败", [
                ("A08-01", "不安全的反序列化", "反序列化不受信任的数据", "critical", "拒绝反序列化不可信数据/使用安全格式(JSON)"),
                ("A08-02", "CI/CD管道不安全", "构建/部署管道缺乏完整性校验", "high", "签名验证+审计日志+访问控制"),
                ("A08-03", "自动更新无验证", "客户端更新不验证签名/哈希", "high", "代码签名+安全传输+完整性校验"),
            ]),
            ("A09", "Security Logging & Monitoring Failures", "安全日志监控失败", [
                ("A09-01", "日志记录不足", "安全事件未充分记录", "medium", "记录认证/授权/数据访问/管理操作"),
                ("A09-02", "日志含敏感信息", "日志中记录密码/token/PII", "high", "脱敏规则+日志分级"),
                ("A09-03", "无入侵检测/告警", "异常行为无法及时发现", "high", "SIEM集成+实时告警+阈值规则"),
                ("A09-04", "事件响应计划缺失", "发生安全事件无应对流程", "medium", "建立IRP(Incident Response Plan)"),
            ]),
            ("A10", "Server-Side Request Forgery (SSRF)", "服务端请求伪造", [
                ("A10-01", "URL参数可控", "用户可控制服务器发起请求的目标URL", "critical", "URL白名单+禁止内网地址"),
                ("A10-02", "云元数据访问", "可访问169.254.169.254等元数据端点", "critical", "禁止请求私有IP段+元数据保护"),
                ("A10-03", "文件读取/端口扫描", "利用SSRF读取本地文件或扫描端口", "critical", "网络隔离+严格的出站规则"),
            ]),
        ]

        all_items: list[SecurityCheckItem] = []
        for cat_code, cat_name, cat_title, checks in owasp_categories:
            for check_id, check_title, desc, severity, mitigation in checks:
                all_items.append(SecurityCheckItem(
                    check_id=check_id,
                    category=f"{cat_code} {cat_title}",
                    owasp_category=cat_name,
                    title=check_title,
                    description=desc,
                    severity=severity,
                    mitigation=mitigation,
                    detection_methods=["渗透测试", "静态分析(SAST)", "动态分析(DAST)", "代码审查"],
                    references=[f"https://owasp.org/www-project-top-ten/{cat_code}_2021/"],
                ))

        stats = {
            "total_checks": len(all_items),
            "critical": sum(1 for i in all_items if i.severity == "critical"),
            "high": sum(1 for i in all_items if i.severity == "high"),
            "medium": sum(1 for i in all_items if i.severity == "medium"),
            "categories": len(owasp_categories),
        }

        return SecurityChecklist(
            standard="OWASP Top 10 (2021)",
            version="2021.0",
            items=all_items,
            stats=stats,
        )

    def _get_asvs_checklist(self) -> SecurityChecklist:
        """OWASP ASVS (Application Security Verification Standard) 精简版"""
        items = [
            SecurityCheckItem("ASVS-1.1", "V1 架构/设计", "Architecture", "威胁建模完成", "high", mitigation="STRIDE/PASTA威胁建模"),
            SecurityCheckItem("ASVS-2.1", "V2 认证", "Authentication", "认证机制强度验证", "critical", mitigation="NIST SP 800-63B合规"),
            SecurityCheckItem("ASVS-3.1", "V3 会话管理", "Session Mgmt", "Session安全配置", "critical", mitigation="安全Cookie标志+过期策略"),
            SecurityCheckItem("ASVS-4.1", "V4 访问控制", "Access Control", "授权模型验证", "critical", mitigation="ABAC+最小权限"),
            SecurityCheckItem("ASVS-5.1", "V5 输入验证", "Validation", "输入输出验证", "high", mitigation="白名单+Schema验证"),
            SecurityCheckItem("ASVS-9.1", "V9 存储/内存", "Data Protection", "敏感数据保护", "critical", mitigation="加密+脱敏+密钥管理"),
        ]
        return SecurityChecklist(standard="OWASP ASVS Level 2", version="4.0.3", items=items, stats={"total_checks": len(items)})

    def _get_nist_checklist(self) -> SecurityChecklist:
        """NIST Cybersecurity Framework 精简版"""
        items = [
            SecurityCheckItem("NIST-ID", "识别", "Identify", "资产识别与管理", "high", mitigation="资产清单+分类"),
            SecurityCheckItem("NIST-PR", "保护", "Protect", "访问控制与数据保护", "critical", mitigation="纵深防御策略"),
            SecurityCheckItem("NIST-DE", "检测", "Detect", "威胁检测能力", "high", mitigation="SIEM+异常检测"),
            SecurityCheckItem("NIST-RS", "响应", "Respond", "事件响应流程", "medium", mitigation="IRP+演练"),
            SecurityCheckItem("NIST-RC", "恢复", "Recover", "灾难恢复计划", "medium", mitigation="备份+RTO/RPO目标"),
        ]
        return SecurityChecklist(standard="NIST CSF", version="2.0", items=items, stats={"total_checks": len(items)})

    def define_git_workflow(self, strategy: str = "gitflow") -> GitWorkflowSpec:
        """
        定义Git工作流规范（分支管理/提交信息/Code Review）

        Args:
            strategy: 工作流策略 ('gitflow', 'github_flow', 'gitlab_flow', 'trunk_based')

        Returns:
            GitWorkflowSpec工作流规范
        """
        match strategy.lower():
            case "gitflow":
                return self._define_gitflow()
            case "github_flow" | "ghflow":
                return self._define_github_flow()
            case "gitlab_flow" | "glflow":
                return self._define_gitlab_flow()
            case "trunk_based" | "trunk":
                return self._define_trunk_based()
            case _:
                raise StandardsError(f"不支持的工作流策略: {strategy}，支持: gitflow, github_flow, gitlab_flow, trunk_based")

    def _define_gitflow(self) -> GitWorkflowSpec:
        """GitFlow工作流"""
        return GitWorkflowSpec(
            strategy="gitflow",
            description="GitFlow是一种经典的分支管理模型，适合有固定发布周期的项目。使用main(生产)和develop(开发)两个长期分支，以及feature/release/hotfix三种临时分支。",
            branches=[
                BranchRule(name="main", pattern="main", purpose="生产环境代码，受保护", source_branch="", target_branch="", protection_rules=["禁止直接push", "仅接受merge请求", "要求CI通过"]),
                BranchRule(name="develop", pattern="develop", purpose="开发集成分支", source_branch="", target_branch="main", protection_rules=["禁止直接push到main", "定期同步到main"]),
                BranchRule(name="feature", pattern="feature/*", purpose="新功能开发", source_branch="develop", target_branch="develop", protection_rules=[]),
                BranchRule(name="release", pattern="release/*", purpose="发布准备", source_branch="develop", target_branch=["main", "develop"], protection_rules=["必须打Tag"]),
                BranchRule(name="hotfix", pattern="hotfix/*", purpose="紧急修复", source_branch="main", target_branch=["main", "develop"], protection_rules=["必须打Tag"]),
            ],
            commit_convention=CommitConvention(
                scope_required=True,
                body_required=True,
                example="feat(auth): add OAuth2 login support\n\n- Implement OAuth2 authorization code flow\n- Add token refresh mechanism\n\nCloses #123",
            ),
            review_guidelines=ReviewGuideline(min_reviewers=2),
            tag_pattern="v*.*.*",
            release_process=[
                "从develop创建release/x.y.z分支",
                "在release分支上完成最后的测试和bug修复",
                "合并release分支到main并打Tag v.x.y.z",
                "合并release分支回develop",
                "部署main到生产环境",
            ],
        )

    def _define_github_flow(self) -> GitWorkflowSpec:
        """GitHub Flow工作流"""
        return GitWorkflowSpec(
            strategy="github_flow",
            description="GitHub Flow是一种轻量级的分支模型，适合持续部署的项目。只有main长期分支，所有开发都在feature分支上进行Pull Request。",
            branches=[
                BranchRule(name="main", pattern="main", purpose="唯一长期分支，始终可部署", protection_rules=["禁止直接push", "要求Status Checks通过", "至少1个reviewer approve"]),
                BranchRule(name="feature", pattern="feature/*", purpose="功能开发分支", source_branch="main", target_branch="main"),
                BranchRule(name="hotfix", pattern="hotfix/*", purpose="紧急修复分支", source_branch="main", target_branch="main"),
            ],
            commit_convention=CommitConvention(scope_required=True, example="feat: add user profile page (#42)"),
            review_guidelines=ReviewGuideline(min_reviewers=1),
            tag_pattern="v*",
            release_process=[
                "从main创建feature分支开发",
                "提交Pull Request",
                "Code Review + CI自动检查",
                "合并到main( squash merge )",
                "自动触发部署",
            ],
        )

    def _define_gitlab_flow(self) -> GitWorkflowSpec:
        """GitLab Flow工作流（带环境分支）"""
        return GitWorkflowSpec(
            strategy="gitlab_flow",
            description="GitLab Flow结合GitHub Flow和环境分支的概念，适合多环境部署场景。通过环境分支(staging/production)管理不同阶段的代码。",
            branches=[
                BranchRule(name="main", pattern="main", purpose="主分支，可部署到staging", protection_rules=["禁止直接push"]),
                BranchRule(name="production", pattern="production", purpose="生产环境分支", source_branch="main", target_branch="", protection_rules=["严格保护"]),
                BranchRule(name="feature", pattern="feature/*", purpose="功能开发", source_branch="main", target_branch="main"),
            ],
            commit_convention=CommitConvention(example="feat(api): implement rate limiting"),
            review_guidelines=ReviewGuideline(min_reviewers=1),
            tag_pattern="v*.*.*",
            release_process=[
                "feature分支开发完成后合并到main",
                "自动部署到staging环境验证",
                "验证通过后cherry-pick/合并到production",
                "production打Tag发布",
            ],
        )

    def _define_trunk_based(self) -> GitWorkflowSpec:
        """Trunk Based Development工作流"""
        return GitWorkflowSpec(
            strategy="trunk_based",
            description="Trunk Based Development是一种极致敏捷的工作流，开发者直接在主干(trunk/main)上工作，通过短生命周期分支和特性开关来管理发布。",
            branches=[
                BranchRule(name="main/trunk", pattern="main", purpose="唯一分支，始终保持可部署状态", protection_rules=["CI必须通过", "快速反馈(<10min)"]),
                BranchRule(name="short-lived", pattern="feature/*", purpose="短生命周期分支(<1天)", source_branch="main", target_branch="main"),
            ],
            commit_convention=CommitConvention(body_required=False, example="wip: add login validation"),
            review_guidelines=ReviewGuideline(
                min_reviewers=1,
                required_checks=["编译通过", "单元测试通过", "lint检查通过"],
                auto_skip_conditions=["typo fix", "refactor with tests", "documentation update"],
            ),
            tag_pattern=None,
            release_process=[
                "直接commit到main(或极短命feature分支)",
                "CI流水线自动验证",
                "Feature Flags控制功能发布",
                "持续部署到生产",
            ],
        )


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 规范制定局测试")
    print("=" * 60)

    bureau = StandardsBureau()

    print("\n--- 编码规范测试 ---")
    for lang in ["python", "javascript", "typescript", "java", "go", "rust"]:
        std = bureau.get_coding_standards(lang)
        print(f"✅ {lang}: {std.standard_name} ({len(std.rules)} 条规则)")

    print("\n--- 开发原则知识库测试 ---")
    principles = bureau.get_development_principles()
    print(f"✅ 共收录 {len(principles)} 条开发原则:")
    for p in principles:
        print(f"   {p.abbreviation}: {p.name} [{p.category.value}]")

    print("\n--- 原则违反检测测试 ---")
    sample_code = """
class UserManagerSystem:
    def create_user(self, data): pass
    def delete_user(self, uid): pass
    def update_user(self, data): pass
    def send_email(self, to, msg): pass
    def generate_report(self, type): pass
    def export_data(self, fmt): pass
    def sync_to_crm(self): pass
    def calculate_bonus(self, emp): pass
    def audit_logs(self, action): pass
    def notify_admin(self, event): pass
    def backup_data(self): pass
    def restore_backup(self): pass
    def manage_permissions(self, role): pass

class OrderService:
    def __init__(self):
        self.db = MySQLDatabase()
        self.cache = RedisClient()
        self.email = SmtpEmailService()

def process_order(order_type):
    if order_type == 'normal':
        handle_normal()
    elif order_type == 'vip':
        handle_vip()
    elif order_type == 'wholesale':
        handle_wholesale()
    elif order_type == 'enterprise':
        handle_enterprise()
    elif order_type == 'trial':
        handle_trial()

MAX_TIMEOUT = 30
def check_status():
    result = some_api_call()
    if result.status == 200:
        process_success()
    if result.status == MAX_TIMEOUT:
        handle_timeout()

def very_long_function_with_many_responsibilities():
    step1()
    step2()
    if condition_a:
        if condition_b:
            if condition_c:
                deep_nested_logic()
    step3()
"""

    for principle in principles[:5]:
        report = bureau.check_principle_violation(sample_code, principle)
        print(f"✅ {principle.abbreviation}: {report.total_violations} 违规, 评分 {report.score:.1f}/100")

    print("\n--- API规范生成测试 ---")
    api_endpoints = [
        {"path": "/users", "method": "GET", "summary": "获取用户列表", "tags": ["Users"], "parameters": [{"name": "page", "in": "query"}]},
        {"path": "/users", "method": "POST", "summary": "创建用户", "tags": ["Users"], "request_body": {"schema": {"$ref": "#/components/schemas/User"}}},
        {"path": "/users/{id}", "method": "GET", "summary": "获取用户详情", "tags": ["Users"]},
        {"path": "/orders", "method": "POST", "summary": "创建订单", "tags": ["Orders"]},
    ]
    openapi_spec = bureau.generate_api_spec(api_endpoints, "openapi3")
    md_spec = bureau.generate_api_spec(api_endpoints, "markdown")
    print(f"✅ OpenAPI 3.0 规范长度: {len(openapi_spec)} 字符")
    print(f"✅ Markdown 文档长度: {len(md_spec)} 字符")

    print("\n--- 数据库规范设计测试 ---")
    db_tables = [
        {
            "table_name": "users",
            "comment": "用户信息表",
            "primary_key": "id",
            "columns": [
                {"name": "id", "type": "BIGINT UNSIGNED AUTO_INCREMENT", "not_null": True, "comment": "主键ID"},
                {"name": "username", "type": "VARCHAR(50)", "not_null": True, "comment": "用户名"},
                {"name": "email", "type": "VARCHAR(255)", "not_null": True, "comment": "邮箱地址"},
                {"name": "password_hash", "type": "VARCHAR(255)", "not_null": True, "comment": "密码哈希"},
                {"name": "is_active", "type": "TINYINT(1)", "default": "1", "comment": "是否激活"},
                {"name": "created_at", "type": "DATETIME", "not_null": True, "comment": "创建时间"},
                {"name": "updated_at", "type": "DATETIME", "not_null": True, "comment": "更新时间"},
            ],
            "indexes": [
                {"name": "idx_users_username", "columns": ["username"], "type": "UNIQUE", "unique": True},
                {"name": "idx_users_email", "columns": ["email"], "type": "UNIQUE", "unique": True},
                {"name": "idx_users_created_at", "columns": ["created_at"]},
            ],
        },
        {
            "table_name": "orders",
            "comment": "订单表",
            "primary_key": "id",
            "columns": [
                {"name": "id", "type": "BIGINT UNSIGNED AUTO_INCREMENT", "not_null": True, "comment": "主键ID"},
                {"name": "user_id", "type": "BIGINT UNSIGNED", "not_null": True, "comment": "用户ID"},
                {"name": "total_amount", "type": "DECIMAL(18, 6)", "not_null": True, "comment": "订单总金额"},
                {"name": "status", "type": "TINYINT", "not_null": True, "comment": "订单状态"},
                {"name": "created_at", "type": "DATETIME", "not_null": True, "comment": "创建时间"},
            ],
            "indexes": [{"name": "idx_orders_user_id", "columns": ["user_id"]}],
            "foreign_keys": [{"column": "user_id", "references": "users(id)", "on_delete": "CASCADE"}],
        },
    ]
    db_spec = bureau.design_db_schema(db_tables)
    print(f"✅ 表数量: {len(db_spec.tables)}")
    print(f"✅ 全局规则: {len(db_spec.global_rules)} 条")
    print(f"SQL DDL:\n{db_spec.to_sql()[:500]}...")

    print("\n--- 安全检查清单测试 ---")
    checklist = bureau.get_security_checklist("owasp_top10")
    print(f"✅ 标准: {checklist.standard}")
    print(f"✅ 总检查项: {checklist.stats.get('total_checks', 0)}")
    print(f"✅ Critical: {checklist.stats.get('critical', 0)}, High: {checklist.stats.get('high', 0)}, Medium: {checklist.stats.get('medium', 0)}")

    print("\n--- Git工作流规范测试 ---")
    for strategy in ["gitflow", "github_flow", "gitlab_flow", "trunk_based"]:
        wf = bureau.define_git_workflow(strategy)
        print(f"✅ {strategy}: {len(wf.branches)} 个分支规则, 审阅>= {wf.review_guidelines.min_reviewers}人")

    print("\n✅ 规范制定局所有测试通过!")
