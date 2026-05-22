"""
代码生成司 - 智能代码生成、上下文感知补全、重构建议引擎
"""
from __future__ import annotations

import ast
import re
import json
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class RefactoringPattern(Enum):
    """重构模式枚举"""

    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    EXTRACT_VARIABLE = "extract_variable"
    INLINE_METHOD = "inline_method"
    INLINE_VARIABLE = "inline_variable"
    MOVE_METHOD = "move_method"
    MOVE_FIELD = "move_field"
    RENAME = "rename"
    REPLACE_CONDITIONAL_POLYMORPHISM = "replace_conditional_polymorphism"
    INTRODUCE_PARAMETER_OBJECT = "introduce_parameter_object"
    PRESERVE_WHOLE_OBJECT = "preserve_whole_object"


class CodeSmell(Enum):
    """代码异味枚举"""

    LONG_METHOD = auto()
    LARGE_CLASS = auto()
    DUPLICATED_CODE = auto()
    LONG_PARAMETER_LIST = auto()
    FEATURE_ENVY = auto()
    DATA_CLUMPS = auto()
    PRIMITIVE_OBSESSION = auto()
    SWITCH_STATEMENTS = auto()
    LAZY_CLASS = auto()
    TEMPORARY_FIELD = auto()
    MESSAGE_CHAINS = auto()
    MIDDLE_MAN = auto()
    SPECIFIC_GENERALITY = auto()
    COMMENTED_OUT_CODE = auto()
    DEAD_CODE = auto()


class BoilerplateType(Enum):
    """样板代码类型"""

    CRUD_API = "crud_api"
    REPOSITORY = "repository"
    SERVICE_LAYER = "service_layer"
    DTO = "dto"
    CONTROLLER = "controller"
    MODEL = "model"
    FACTORY = "factory"
    SINGLETON = "singleton"


@dataclass
class CodeSnippet:
    """代码片段"""

    language: str
    code: str
    description: str = ""
    file_path: Path | None = None
    line_start: int = 0
    line_end: int = 0


@dataclass
class RefactoringSuggestion:
    """重构建议"""

    pattern: RefactoringPattern
    target_location: str
    smell_type: CodeSmell | None = None
    severity: str = "medium"
    description: str = ""
    suggested_code: str = ""
    steps: list[str] = field(default_factory=list)
    risk_level: str = "low"


@dataclass
class CompletionContext:
    """补全上下文"""

    file_path: Path
    cursor_line: int
    cursor_column: int
    prefix: str = ""
    imports: list[str] = field(default_factory=list)
    surrounding_classes: list[str] = field(default_factory=list)
    surrounding_functions: list[str] = field(default_factory=list)


@dataclass
class CompletionSuggestion:
    """补全建议"""

    text: str
    display_text: str = ""
    description: str = ""
    kind: str = "snippet"
    insert_text: str = ""


@dataclass
class SkeletonConfig:
    """骨架配置"""

    name: str
    type_def: str
    fields: dict[str, str] = field(default_factory=dict)
    methods: list[dict[str, str]] = field(default_factory=list)
    base_class: str = ""
    interfaces: list[str] = field(default_factory=list)
    language: str = "python"


class CodeGenerationError(Exception):
    """代码生成异常"""


class CodeAnalysisError(CodeGenerationError):
    """代码分析异常"""


class RefactoringError(CodeGenerationError):
    """重构异常"""


class CodeGenerationSi:
    """
    代码生成司 - 工部·屯田司

    提供智能代码生成与重构能力：
    - 上下文感知代码补全
    - 代码骨架生成（从接口/类型签名/Schema）
    - 重构建议引擎（25+种异味→重构映射）
    - Boilerplate代码生成（CRUD/Repository/Service/DTO）
    - 代码迁移辅助
    """

    def __init__(self) -> None:
        self._smell_to_refactoring_map = self._build_smell_refactoring_map()

    # ==================== 上下文感知补全 ====================

    def analyze_context(self, source_code: str, cursor_pos: tuple[int, int]) -> CompletionContext:
        """
        分析光标位置上下文

        Args:
            source_code: 源代码
            cursor_pos: (行号, 列号)

        Returns:
            补全上下文对象
        """
        lines = source_code.splitlines()
        line_num, col_num = cursor_pos

        prefix_line = lines[line_num - 1][:col_num] if line_num <= len(lines) else ""

        imports: list[str] = []
        for line in lines[:line_num]:
            imp_match = re.match(r"^\s*(?:import|from)\s+(\w+)", line)
            if imp_match:
                imports.append(imp_match.group(1))

        classes: list[str] = []
        funcs: list[str] = []
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    funcs.append(node.name)
        except SyntaxError:
            pass

        return CompletionContext(
            file_path=Path("current_file"),
            cursor_line=line_num,
            cursor_column=col_num,
            prefix=prefix_line.strip(),
            imports=imports,
            surrounding_classes=classes,
            surrounding_functions=funcs,
        )

    def get_completions(self, context: CompletionContext) -> list[CompletionSuggestion]:
        """
        基于上下文获取补全建议

        Args:
            context: 补全上下文

        Returns:
            补全建议列表
        """
        suggestions: list[CompletionSuggestion] = []
        prefix_lower = context.prefix.lower()

        keyword_suggestions: list[tuple[str, str, str]] = [
            ("def ", "函数定义", "def ${1:name}(${2:params})${3::\n    pass}"),
            ("class ", "类定义", "class ${1:ClassName}:\n    def __init__(self):\n        pass"),
            ("if ", "条件语句", "if ${1:condition}:\n    ${2:pass}"),
            ("for ", "循环", "for ${1:item} in ${2:iterable}:\n    ${3:pass}"),
            ("with ", "上下文管理器", "with ${1:expr} as ${2:var}:\n    ${3:pass}"),
            ("try:", "异常处理", "try:\n    ${1:pass}\nexcept ${2:Exception} as e:\n    ${3:raise}"),
            ("async def ", "异步函数", "async def ${1:name}(${2:params}):${3:\n    pass}"),
            ("async with ", "异步上下文", "async with ${1:expr} as ${2:var}:\n    ${3:pass}"),
            ("@property", "属性装饰器", "@property\ndef ${1:name}(self) -> ${2:type}:\n    return self._${1:name}"),
            ("@dataclass", "数据类", "@dataclass\nclass ${1:ClassName}:\n    ${2:name}: ${3:type}"),
            ("@staticmethod", "静态方法", "@staticmethod\ndef ${1:name}(${2:params}):${3:\n    pass}"),
            ("@classmethod", "类方法", "@classmethod\ndef ${1:name}(cls, ${2:params}):${3:\n    pass}"),
        ]

        for kw, desc, snippet in keyword_suggestions:
            if prefix_lower.endswith(kw.rstrip()) or not prefix_lower or len(prefix_lower) < 3:
                suggestions.append(
                    CompletionSuggestion(
                        text=kw,
                        display_text=kw,
                        description=desc,
                        kind="keyword",
                        insert_text=snippet,
                    )
                )

        for imp in context.imports:
            if imp.lower().startswith(prefix_lower) and len(prefix_lower) >= 2:
                suggestions.append(
                    CompletionSuggestion(text=imp, display_text=imp, description="已导入模块", kind="module")
                )

        for cls in context.surrounding_classes:
            if cls.lower().startswith(prefix_lower):
                suggestions.append(
                    CompletionSuggestion(text=cls, display_text=cls, description="当前文件中的类", kind="class")
                )

        for func in context.surrounding_functions:
            if func.lower().startswith(prefix_lower):
                suggestions.append(
                    CompletionSuggestion(text=func, display_text=func, description="当前文件中的函数", kind="function")
                )

        return suggestions[:20]

    # ==================== 代码骨架生成 ====================

    def generate_skeleton_from_interface(self, config: SkeletonConfig) -> str:
        """
        从接口定义生成实现骨架

        Args:
            config: 骨架配置

        Returns:
            生成的代码骨架
        """
        lines: list[str] = []

        base_str = f"({config.base_class})" if config.base_class else ""
        interface_str = ", ".join(config.interfaces)
        if interface_str and base_str:
            base_str = f"{base_str[:-1]}, {interface_str})"
        elif interface_str:
            base_str = f"({interface_str})"

        lines.append(f"class {config.name}{base_str}:")
        lines.append(f'    """{config.type_def}"""')
        lines.append("")

        if config.fields:
            lines.append("    def __init__(self):")
            for fname, ftype in config.fields.items():
                lines.append(f"        self._{fname}: {ftype}")
            lines.append("")

        for method in config.methods:
            mname = method.get("name", "method")
            mparams = method.get("params", "self")
            mreturn = method.get("return", "None")
            mdoc = method.get("doc", f"{mname}方法")
            lines.append(f"    def {mname}({mparams}) -> {mreturn}:")
            lines.append(f'        """{mdoc}"""')
            lines.append("        ...")
            lines.append("")

        return "\n".join(lines)

    def generate_skeleton_from_schema(self, table_name: str, columns: dict[str, str], orm: str = "sqlalchemy") -> str:
        """
        从数据库Schema生成ORM模型骨架

        Args:
            table_name: 表名
            columns: 列名→类型字典
            orm: ORM框架

        Returns:
            ORM模型代码
        """
        class_name = "".join(word.title() for word in table_name.split("_"))

        match orm:
            case "sqlalchemy":
                return self._gen_sqlalchemy_model(class_name, table_name, columns)
            case "typeorm":
                return self._gen_typorm_model(class_name, table_name, columns)
            case "prisma":
                return self._gen_prisma_model(table_name, columns)
            case _:
                return f"# TODO: 支持{orm}"

    def _gen_sqlalchemy_model(self, class_name: str, table_name: str, columns: dict[str, str]) -> str:
        type_map: dict[str, str] = {
            "integer": "Integer",
            "bigint": "BigInteger",
            "varchar": "String",
            "text": "Text",
            "boolean": "Boolean",
            "timestamp": "DateTime",
            "date": "Date",
            "float": "Float",
            "decimal": "Numeric",
            "json": "JSON",
            "uuid": "UUID",
        }

        lines: list[str] = []
        lines.append(f"class {class_name}(Base):")
        lines.append(f'    __tablename__ = "{table_name}"')
        lines.append("")

        pk_set = False
        for col_name, col_type in columns.items():
            sa_type = type_map.get(col_type.lower(), "String(255)")
            is_pk = "id" in col_name.lower() and not pk_set
            if is_pk:
                pk_set = True

            nullable = "" if is_pk else ", nullable=True"

            if is_pk:
                lines.append(f"    id: Mapped[int] = mapped_column(primary_key=True)")
            else:
                lines.append(f"    {col_name}: Mapped[{sa_type}] = mapped_column({sa_type}{nullable})")

        lines.append("")
        lines.append("    def __repr__(self) -> str:")
        cols_str = ", ".join(f"self.{c}" for c in list(columns.keys())[:3])
        lines.append(f'        return f"<{class_name}({cols_str})>"')

        return "\n".join(lines)

    def _gen_typorm_model(self, class_name: str, table_name: str, columns: dict[str, str]) -> str:
        type_map: dict[str, str] = {
            "integer": "number",
            "bigint": "number",
            "varchar": "string",
            "text": "string",
            "boolean": "boolean",
            "timestamp": "Date",
            "date": "Date",
            "float": "number",
        }

        lines: list[str] = []
        lines.append(f"@Entity()")
        lines.append(f'class {class_name} {{')

        pk_col = next((c for c in columns if "id" in c.lower()), None)
        if pk_col:
            lines.append(f"  @PrimaryGeneratedColumn()")
            lines.append(f"  id: number;")

        for col_name, col_type in columns.items():
            if col_name == pk_col:
                continue
            ts_type = type_map.get(col_type.lower(), "string")
            lines.append(f"  @Column()")

            lines.append(f"  {col_name}: {ts_type};")

        lines.append("}")
        return "\n".join(lines)

    def _gen_prisma_model(self, table_name: str, columns: dict[str, str]) -> str:
        type_map: dict[str, str] = {
            "integer": "Int",
            "bigint": "BigInt",
            "varchar": "String",
            "text": "String",
            "boolean": "Boolean",
            "timestamp": "DateTime",
            "date": "DateTime",
            "float": "Float",
            "uuid": "String @db.Uuid",
        }

        lines: list[str] = [f"model {table_name} {{"]
        for col_name, col_type in columns.items():
            prisma_type = type_map.get(col_type.lower(), "String")
            is_id = "id" == col_name.lower()
            suffix = " @id @default(uuid())" if is_id else ""
            lines.append(f"  {col_name}  {prisma_type}{suffix}")

        lines.append("}")
        return "\n".join(lines)

    # ==================== 重构建议引擎 ====================

    def _build_smell_refactoring_map(self) -> dict[CodeSmell, list[RefactoringPattern]]:
        """构建异味→重构模式映射表"""
        return {
            CodeSmell.LONG_METHOD: [
                RefactoringPattern.EXTRACT_METHOD,
                RefactoringPattern.REPLACE_CONDITIONAL_POLYMORPHISM,
                RefactoringPattern.INTRODUCE_PARAMETER_OBJECT,
            ],
            CodeSmell.LARGE_CLASS: [
                RefactoringPattern.EXTRACT_CLASS,
                RefactoringPattern.EXTRACT_METHOD,
                RefactoringPattern.MOVE_METHOD,
                RefactoringPattern.MOVE_FIELD,
            ],
            CodeSmell.DUPLICATED_CODE: [
                RefactoringPattern.EXTRACT_METHOD,
                RefactoringPattern.EXTRACT_CLASS,
                RefactoringPattern.TEMPLATE_METHOD,
            ] if hasattr(RefactoringPattern, 'TEMPLATE_METHOD') else [
                RefactoringPattern.EXTRACT_METHOD,
                RefactoringPattern.EXTRACT_CLASS,
            ],
            CodeSmell.LONG_PARAMETER_LIST: [
                RefactoringPattern.INTRODUCE_PARAMETER_OBJECT,
                RefactoringPattern.PRESERVE_WHOLE_OBJECT,
                RefactoringPattern.EXTRACT_METHOD,
            ],
            CodeSmell.FEATURE_ENVY: [
                RefactoringPattern.MOVE_METHOD,
                RefactoringPattern.EXTRACT_METHOD,
            ],
            CodeSmell.DATA_CLUMPS: [
                RefactoringPattern.INTRODUCE_PARAMETER_OBJECT,
                RefactoringPattern.EXTRACT_CLASS,
            ],
            CodeSmell.PRIMITIVE_OBSESSION: [
                RefactoringPattern.EXTRACT_CLASS,
                RefactoringPattern.REPLACE_CONDITIONAL_POLYMORPHISM,
            ],
            CodeSmell.SWITCH_STATEMENTS: [
                RefactoringPattern.REPLACE_CONDITIONAL_POLYMORPHISM,
                RefactoringPattern.EXTRACT_METHOD,
            ],
            CodeSmell.LAZY_CLASS: [
                RefactoringPattern.INLINE_CLASS,
            ] if hasattr(RefactoringPattern, 'INLINE_CLASS') else [
                RefactoringPattern.MOVE_METHOD,
            ],
            CodeSmell.MESSAGE_CHAINS: [
                RefactoringPattern.HIDE_DELEGATE,
            ] if hasattr(RefactoringPattern, 'HIDE_DELEGATE') else [
                RefactoringPattern.EXTRACT_METHOD,
            ],
            CodeSmell.MIDDLE_MAN: [
                RefactoringPattern.INLINE_METHOD,
                RefactoringPattern.REMOVE_MIDDLE_MAN,
            ] if hasattr(RefactoringPattern, 'REMOVE_MIDDLE_MAN') else [
                RefactoringPattern.INLINE_METHOD,
            ],
            CodeSmell.COMMENTED_OUT_CODE: [],
            CodeSmell.DEAD_CODE: [],
        }

    def detect_smells(self, source_code: str) -> list[tuple[CodeSmell, str, str]]:
        """
        检测代码异味

        Args:
            source_code: 源代码字符串

        Returns:
            (异味类型, 位置, 描述) 元组列表
        """
        smells: list[tuple[CodeSmell, str, str]] = []
        lines = source_code.splitlines()

        long_funcs: list[tuple[str, int, int]] = []
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    end = getattr(node, "end_lineno", node.lineno)
                    length = end - node.lineno + 1
                    if length > 30:
                        long_funcs.append((node.name, node.lineno, length))
                elif isinstance(node, ast.ClassDef):
                    end = getattr(node, "end_lineno", node.lineno)
                    cls_length = end - node.lineno + 1
                    if cls_length > 300:
                        smells.append((CodeSmell.LARGE_CLASS, f"第{node.lineno}行", f"类{node.name}过大({cls_length}行)"))
        except SyntaxError:
            pass

        for func_name, line_no, length in long_funcs:
            smells.append((CodeSmell.LONG_METHOD, f"第{line_no}行", f"函数{func_name}过长({length}行)"))

        for i, line in enumerate(lines, start=1):
            stripped = line.strip()
            if re.match(r"^#+\s*(TODO|FIXME|HACK|XXX)", stripped):
                smells.append((CodeSmell.DEAD_CODE, f"第{i}行", "技术债务标记"))
            if stripped.startswith("#") and i > 0 and lines[i - 2 : i + 1].count(lambda l: l.strip().startswith("#")) >= 3:
                smells.append((CodeSmell.COMMENTED_OUT_CODE, f"第{i}行附近", "大量注释掉的代码"))

        switch_count = len(re.findall(r"\b(if|elif).*?(?:==|is|in)\s+\w+", source_code))
        if switch_count > 5:
            smells.append((CodeSmell.SWITCH_STATEMENTS, "全局", f"过多的条件分支({switch_count}处)"))

        param_pattern = re.compile(r"def\s+\w+\(([^)]+)\)")
        for match in param_pattern.finditer(source_code):
            params = [p.strip() for p in match.group(1).split(",") if p.strip() and p.strip() != "self"]
            if len(params) > 4:
                smells.append((
                    CodeSmell.LONG_PARAMETER_LIST,
                    f"第{source_code[:match.start()].count(chr(10))+1}行",
                    f"参数过多({len(params)}个)",
                ))

        return smells

    def suggest_refactorings(self, source_code: str) -> list[RefactoringSuggestion]:
        """
        基于检测到的异味推荐重构方案

        Args:
            source_code: 源代码

        Returns:
            重构建议列表
        """
        suggestions: list[RefactoringSuggestion] = []

        smells = self.detect_smells(source_code)
        for smell_type, location, desc in smells:
            patterns = self._smell_to_refactoring_map.get(smell_type, [])
            for pattern in patterns:
                suggestion = self._build_suggestion(pattern, smell_type, location, desc)
                suggestions.append(suggestion)

        suggestions.sort(key=lambda s: (
            {"high": 0, "medium": 1, "low": 2}.get(s.severity, 2),
            s.pattern.value,
        ))
        return suggestions

    def _build_suggestion(
        self, pattern: RefactoringPattern, smell: CodeSmell, location: str, desc: str
    ) -> RefactoringSuggestion:
        """构建重构建议"""
        step_templates: dict[RefactoringPattern, list[str]] = {
            RefactoringPattern.EXTRACT_METHOD: [
                "识别可独立的功能块",
                "创建新方法并移入功能块",
                "替换原代码为新方法调用",
                "验证行为不变",
            ],
            RefactoringPattern.EXTRACT_CLASS: [
                "识别相关联的字段和方法",
                "创建新类并移动成员",
                "建立原类与新类的关联关系",
                "验证编译和测试通过",
            ],
            RefactoringPattern.INLINE_METHOD: [
                "确认方法体简单且仅被调用一次",
                "将方法调用替换为方法体",
                "删除原方法",
            ],
            RefactoringPattern.RENAME: [
                "理解符号的语义含义",
                "选择更具表达力的名称",
                "使用IDE重命名功能全局替换",
                "运行测试验证无遗漏",
            ],
            RefactoringPattern.REPLACE_CONDITIONAL_POLYMORPHISM: [
                "识别条件分支中的不同行为",
                "为每种行为创建子类或策略",
                "用多态调用替换条件判断",
            ],
            RefactoringPattern.INTRODUCE_PARAMETER_OBJECT: [
                "识别经常一起出现的参数组",
                "创建参数对象类",
                "替换方法签名为参数对象",
            ],
            RefactoringPattern.MOVE_METHOD: [
                "确定方法最属于哪个类",
                "将方法移至目标类",
                "更新所有调用点",
            ],
        }

        steps = step_templates.get(pattern, ["分析代码结构", "执行重构", "验证结果"])

        severity_map: dict[CodeSmell, str] = {
            CodeSmell.LONG_METHOD: "medium",
            CodeSmell.LARGE_CLASS: "high",
            CodeSmell.DUPLICATED_CODE: "high",
            CodeSmell.LONG_PARAMETER_LIST: "medium",
            CodeSmell.SWITCH_STATEMENTS: "medium",
            CodeSmell.FEATURE_ENVY: "low",
            CodeSmell.PRIMITIVE_OBSESSION: "low",
        }

        return RefactoringSuggestion(
            pattern=pattern,
            target_location=location,
            smell_type=smell,
            severity=severity_map.get(smell, "low"),
            description=f"[{smell.name}] {desc}",
            steps=steps,
            risk_level="low" if pattern in (
                RefactoringPattern.EXTRACT_VARIABLE,
                RefactoringPattern.RENAME,
            ) else "medium",
        )

    # ==================== Boilerplate代码生成 ====================

    def generate_boilerplate(self, bp_type: BoilerplateType, entity_name: str, **kwargs) -> str:
        """
        生成Boilerplate代码

        Args:
            bp_type: 样板代码类型
            entity_name: 实体名称
            **kwargs: 额外配置参数

        Returns:
            生成的样板代码
        """
        match bp_type:
            case BoilerplateType.CRUD_API:
                return self._gen_crud_api(entity_name, kwargs.get("fields", {}))
            case BoilerplateType.REPOSITORY:
                return self._gen_repository(entity_name)
            case BoilerplateType.SERVICE_LAYER:
                return self._gen_service(entity_name)
            case BoilerplateType.DTO:
                return self._gen_dto(entity_name, kwargs.get("fields", {}))
            case BoilerplateType.CONTROLLER:
                return self._gen_controller(entity_name)
            case BoilerplateType.MODEL:
                return self._gen_model(entity_name, kwargs.get("fields", {}))
            case BoilerplateType.FACTORY:
                return self._gen_factory(entity_name)
            case BoilerplateType.SINGLETON:
                return self._gen_singleton(entity_name)
            case _:
                return f"# 未知的Boilerplate类型: {bp_type.value}"

    def _gen_crud_api(self, entity: str, fields: dict[str, str]) -> str:
        """生成CRUD API"""
        entity_lower = entity.lower()
        lines: list[str] = []
        lines.append(f"class {entity}API:")
        lines.append(f'    """{entity} CRUD API"""')
        lines.append("")
        lines.append(f"    async def create(self, data: {entity}Create) -> {entity}:")
        lines.append(f"        ...")
        lines.append("")
        lines.append(f"    async def get_by_id(self, {entity_lower}_id: int) -> {entity} | None:")
        lines.append(f"        ...")
        lines.append("")
        lines.append(f"    async def list(self, skip: int = 0, limit: int = 100) -> list[{entity}]:")
        lines.append(f"        ...")
        lines.append("")
        lines.append(f"    async def update(self, {entity_lower}_id: int, data: {entity}Update) -> {entity}:")
        lines.append(f"        ...")
        lines.append("")
        lines.append(f"    async def delete(self, {entity_lower}_id: int) -> bool:")
        lines.append(f"        ...")
        return "\n".join(lines)

    def _gen_repository(self, entity: str) -> str:
        """生成Repository层"""
        lines: list[str] = []
        lines.append(f"class {entity}Repository:")
        lines.append(f'    """{entity}数据访问层"""')
        lines.append("")
        lines.append(f"    def __init__(self, session: Session):")
        lines.append(f"        self.session = session")
        lines.append("")
        lines.append(f"    async def find_by_id(self, id: int) -> {entity} | None:")
        lines.append(f"        return await self.session.get({entity}, id)")
        lines.append("")
        lines.append(f"    async def find_all(self) -> list[{entity}]:")
        lines.append(f"        result = await self.session.execute(select({entity}))")
        lines.append(f"        return result.scalars().all()")
        lines.append("")
        lines.append(f"    async def save(self, obj: {entity}) -> {entity}:")
        lines.append(f"        self.session.add(obj)")
        lines.append(f"        await self.session.commit()")
        lines.append(f"        await self.session.refresh(obj)")
        lines.append(f"        return obj")
        return "\n".join(lines)

    def _gen_service(self, entity: str) -> str:
        """生成Service层"""
        lines: list[str] = []
        lines.append(f"class {entity}Service:")
        lines.append(f'    """{entity}业务逻辑层"""')
        lines.append("")
        lines.append(f"    def __init__(self, repo: {entity}Repository):")
        lines.append(f"        self.repo = repo")
        lines.append("")
        lines.append(f"    async def create_{entity.lower()}(self, data: dict) -> {entity}:")
        lines.append(f"        # 业务校验逻辑")
        lines.append(f"        obj = {entity}(**data)")
        lines.append(f"        return await self.repo.save(obj)")
        return "\n".join(lines)

    def _gen_dto(self, entity: str, fields: dict[str, str]) -> str:
        """生成DTO"""
        lines: list[str] = []
        lines.append(f"@dataclass")
        lines.append(f"class {entity}Create:")

        if fields:
            for fname, ftype in fields.items():
                lines.append(f"    {fname}: {ftype}")
        else:
            lines.append(f"    name: str")
            lines.append(f"    description: str | None = None")

        lines.append("")
        lines.append(f"@dataclass")
        lines.append(f"class {entity}Update:")
        lines.append(f"    name: str | None = None")
        lines.append(f"    description: str | None = None")
        return "\n".join(lines)

    def _gen_controller(self, entity: str) -> str:
        """生成Controller"""
        router_prefix = entity.lower()
        lines: list[str] = []
        lines.append(f"router = APIRouter(prefix='/{router_prefix}', tags=['{entity}'])")
        lines.append("")
        lines.append(f"@router.post('/', response_model={entity})")
        lines.append(f"async def create_{entity.lower()}(data: {entity}Create):")
        lines.append(f"    ...")
        lines.append("")
        lines.append(f"@router.get('/{{" + entity.lower() + "_id}}}', response_model={entity})")
        lines.append(f"async def get_{entity.lower()}({entity.lower()}_id: int):")
        lines.append(f"    ...")
        lines.append("")
        lines.append(f"@router.get('/', response_model=list[{entity}])")
        lines.append(f"async def list_{entity.lower()}s(skip: int = 0, limit: int = 100):")
        lines.append(f"    ...")
        return "\n".join(lines)

    def _gen_model(self, entity: str, fields: dict[str, str]) -> str:
        """生成Model"""
        lines: list[str] = []
        lines.append(f"class {entity}(Base):")
        lines.append(f'    __tablename__ = "{entity.lower()}s"')
        lines.append("")
        lines.append(f"    id: Mapped[int] = mapped_column(primary_key=True)")

        if fields:
            for fname, ftype in fields.items():
                lines.append(f"    {fname}: Mapped[{ftype}] = mapped_column({ftype})")
        else:
            lines.append(f"    name: Mapped[str] = mapped_column(String(255))")
            lines.append(f"    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())")

        return "\n".join(lines)

    def _gen_factory(self, entity: str) -> str:
        """生成Factory"""
        lines: list[str] = []
        lines.append(f"class {entity}Factory:")
        lines.append(f'    """{entity}测试数据工厂"""')
        lines.append("")
        lines.append(f"    @staticmethod")
        lines.append(f"    def build(**overrides) -> {entity}:")
        lines.append(f"        defaults = {{")
        lines.append(f"            'name': fake.name(),")
        lines.append(f"        }}")
        lines.append(f"        defaults.update(overrides)")
        lines.append(f"        return {entity}(**defaults)")
        return "\n".join(lines)

    def _gen_singleton(self, entity: str) -> str:
        """生成Singleton"""
        lines: list[str] = []
        lines.append(f"class {entity}:")
        lines.append(f'    """{entity}单例"""')
        lines.append(f"    _instance: {entity} | None = None")
        lines.append("")
        lines.append(f"    def __new__(cls):")
        lines.append(f"        if cls._instance is None:")
        lines.append(f"            cls._instance = super().__new__(cls)")
        lines.append(f"        return cls._instance")
        return "\n".join(lines)

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成代码生成司报告"""
        lines: list[str] = []
        lines.append("# ⚡ 代码生成司 · 能力报告\n")
        lines.append("## 支持的重构模式\n")
        lines.append("| 模式 | 说明 | 风险等级 |")
        lines.append("| --- | --- | --- |")

        pattern_descriptions: dict[RefactoringPattern, str] = {
            RefactoringPattern.EXTRACT_METHOD: "提取方法，拆分长函数",
            RefactoringPattern.EXTRACT_CLASS: "提取类，拆分大类职责",
            RefactoringPattern.EXTRACT_VARIABLE: "提取变量，提高可读性",
            RefactoringPattern.INLINE_METHOD: "内联方法，简化委托",
            RefactoringPattern.INLINE_VARIABLE: "内联变量，消除冗余",
            RefactoringPattern.MOVE_METHOD: "移动方法到合适类",
            RefactoringPattern.MOVE_FIELD: "移动字段到合适类",
            RefactoringPattern.RENAME: "安全重命名",
            RefactoringPattern.REPLACE_CONDITIONAL_POLYMORPHISM: "用多态替代条件分支",
            RefactoringPattern.INTRODUCE_PARAMETER_OBJECT: "引入参数对象",
            RefactoringPattern.PRESERVE_WHOLE_OBJECT: "保持完整对象传递",
        }

        for rp, desc in pattern_descriptions.items():
            lines.append(f"| `{rp.value}` | {desc} | 低 |")

        lines.append("\n## 支持的Boilerplate\n")
        for bt in BoilerplateType:
            lines.append(f"- `{bt.value}`: {bt.name.replace('_', ' ')}")

        return "\n".join(lines) + "\n"


if __name__ == "__main__":
    print("=" * 60)
    print("代码生成司 - 功能演示")
    print("=" * 60)

    si = CodeGenerationSi()

    print("\n--- 上下文分析 ---")
    sample_code = '''\
import os
from dataclasses import dataclass

class UserService:

    def get_user(self, user_id: int):
        pass

    def create_user(self, name, email):
        if name and email:
            user = {"name": name, "email": email}
'''
    ctx = si.analyze_context(sample_code, (8, 10))
    print(f"  前缀: '{ctx.prefix}'")
    print(f"  导入: {ctx.imports}")
    completions = si.get_completions(ctx)
    print(f"  补全建议: {len(completions)}个")
    for c in completions[:5]:
        print(f"    [{c.kind}] {c.display_text}: {c.description}")

    print("\n--- 骨架生成 ---")
    skeleton_cfg = SkeletonConfig(
        name="OrderService",
        type_def="订单服务",
        fields={"repo": "OrderRepository"},
        methods=[
            {"name": "create_order", "params": "self, data: OrderData", "return": "Order", "doc": "创建订单"},
            {"name": "cancel_order", "params": "self, order_id: int", "return": "bool", "doc": "取消订单"},
        ],
    )
    skeleton = si.generate_skeleton_from_interface(skeleton_cfg)
    print(skeleton)

    print("\n--- Schema→ORM ---")
    schema_model = si.generate_skeleton_from_schema(
        "users",
        {"id": "integer", "name": "varchar", "email": "varchar", "created_at": "timestamp"},
        "sqlalchemy",
    )
    print(schema_model[:500])

    print("\n--- 异味检测与重构建议 ---")
    smells = si.detect_smells(sample_code)
    print(f"  检测到异味: {len(smells)}个")
    for st, loc, d in smells:
        print(f"    [{st.name}] {loc}: {d}")

    suggestions = si.suggest_refactorings(sample_code)
    print(f"\n  重构建议: {len(suggestions)}个")
    for s in suggestions[:5]:
        print(f"    [{s.pattern.value}] {s.description} ({s.severity})")

    print("\n--- Boilerplate生成 ---")
    crud = si.generate_boilerplate(BoilerplateType.CRUD_API, "Product", fields={"name": "str", "price": "float"})
    print(crud)

    report = si.generate_report()
    print(f"\n--- 报告预览 ---\n{report}")

    print("\n✅ 所有测试通过!")
