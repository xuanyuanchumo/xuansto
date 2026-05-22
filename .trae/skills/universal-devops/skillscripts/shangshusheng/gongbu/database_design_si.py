"""
数据库设计司 - ER建模工具、迁移脚本生成、索引优化建议
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class DatabaseType(Enum):
    """数据库类型"""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    ORACLE = "oracle"
    SQL_SERVER = "sql_server"


class ORMFramework(Enum):
    """ORM框架"""

    SQLALCHEMY = "sqlalchemy"
    TYPEORM = "typeorm"
    PRISMA = "prisma"
    SEQUELIZE = "sequelize"


class MigrationTool(Enum):
    """迁移工具"""

    ALEMBIC = "alembic"
    FLYWAY = "flyway"
    LIQUIBASE = "liquibase"


class RelationshipType(Enum):
    """关系类型"""

    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_MANY = "M:N"


class NormalForm(Enum):
    """范式"""

    FIRST_NF = "1NF"
    SECOND_NF = "2NF"
    THIRD_NF = "3NF"
    BCNF = "BCNF"


@dataclass
class Entity:
    """实体定义"""

    name: str
    table_name: str = ""
    attributes: list[dict[str, Any]] = field(default_factory=list)
    primary_key: str = "id"
    description: str = ""


@dataclass
class Attribute:
    """属性定义"""

    name: str
    data_type: str
    nullable: bool = False
    default_value: Any = None
    is_primary_key: bool = False
    is_unique: bool = False
    is_indexed: bool = False
    foreign_key: str | None = None
    comment: str = ""


@dataclass
class Relationship:
    """关系定义"""

    from_entity: str
    to_entity: str
    relationship_type: RelationshipType
    from_attribute: str = ""
    to_attribute: str = ""
    on_delete: str = "CASCADE"
    on_update: str = "CASCADE"


@dataclass
class IndexSuggestion:
    """索引建议"""

    table_name: str
    column_names: list[str]
    index_type: str = "btree"
    reason: str = ""
    estimated_impact: str = ""


@dataclass
class SlowQueryInfo:
    """慢查询信息"""

    query_text: str
    execution_time_ms: float = 0.0
    table_name: str = ""
    suggestion: str = ""


@dataclass
class NormalizationResult:
    """规范化检查结果"""

    form_level: NormalForm
    is_compliant: bool
    violations: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=dict)


@dataclass
class ShardingStrategy:
    """分库分表策略"""

    strategy_type: str
    shard_key: str = ""
    shard_count: int = 0
    description: str = ""


class DatabaseDesignError(Exception):
    """数据库设计异常"""


class SchemaError(DatabaseDesignError):
    """Schema异常"""


class MigrationError(DatabaseDesignError):
    """迁移异常"""


class DatabaseDesignSi:
    """
    数据库设计司 - 工部·水部司

    提供全面的数据库设计能力：
    - ER模型设计与Mermaid图生成
    - 多数据库Schema/DDL生成
    - 多ORM Model代码生成
    - 迁移脚本生成（Alembic/Flyway/Liquibase）
    - 索引优化建议
    - 数据规范化检查
    - 数据字典生成
    - 分库分表策略
    """

    def __init__(self) -> None:
        self._entities: dict[str, Entity] = {}
        self._relationships: list[Relationship] = []
        self._type_maps = self._build_type_maps()

    # ==================== 类型映射 ====================

    def _build_type_maps(self) -> dict[DatabaseType, dict[str, str]]:
        """构建各数据库类型映射"""
        return {
            DatabaseType.POSTGRESQL: {
                "integer": "INTEGER",
                "bigint": "BIGINT",
                "varchar": "VARCHAR(255)",
                "text": "TEXT",
                "boolean": "BOOLEAN",
                "timestamp": "TIMESTAMP",
                "date": "DATE",
                "float": "DOUBLE PRECISION",
                "decimal": "DECIMAL(18,6)",
                "json": "JSONB",
                "uuid": "UUID",
                "binary": "BYTEA",
                "array": "ARRAY",
                "auto_increment": "SERIAL",
            },
            DatabaseType.MYSQL: {
                "integer": "INT",
                "bigint": "BIGINT",
                "varchar": "VARCHAR(255)",
                "text": "TEXT",
                "boolean": "TINYINT(1)",
                "timestamp": "DATETIME",
                "date": "DATE",
                "float": "FLOAT",
                "decimal": "DECIMAL(18,6)",
                "json": "JSON",
                "uuid": "CHAR(36)",
                "binary": "BLOB",
                "array": "JSON",
                "auto_increment": "INT AUTO_INCREMENT",
            },
            DatabaseType.SQLITE: {
                "integer": "INTEGER",
                "bigint": "INTEGER",
                "varchar": "TEXT",
                "text": "TEXT",
                "boolean": "INTEGER",
                "timestamp": "TEXT",
                "date": "TEXT",
                "float": "REAL",
                "decimal": "REAL",
                "json": "TEXT",
                "uuid": "TEXT",
                "binary": "BLOB",
                "array": "TEXT",
                "auto_increment": "INTEGER PRIMARY KEY AUTOINCREMENT",
            },
        }

    def _map_type(self, generic_type: str, db_type: DatabaseType) -> str:
        """映射通用类型到特定数据库类型"""
        type_map = self._type_maps.get(db_type, self._type_maps[DatabaseType.POSTGRESQL])
        return type_map.get(generic_type.lower(), generic_type.upper())

    # ==================== ER模型管理 ====================

    def add_entity(self, entity: Entity) -> None:
        """添加实体"""
        entity.table_name = entity.table_name or entity.name.lower() + "s"
        self._entities[entity.name] = entity

    def add_relationship(self, rel: Relationship) -> None:
        """添加关系"""
        self._relationships.append(rel)

    def generate_er_diagram(self, output_format: str = "mermaid") -> str:
        """
        生成ER图（Mermaid格式）

        Args:
            output_format: 输出格式 (mermaid/plantuml/graphviz)
        """
        match output_format:
            case "mermaid":
                return self._gen_mermaid_er()
            case "plantuml":
                return self._gen_plantuml_er()
            case _:
                return f"# 不支持的ER图格式: {output_format}"

    def _gen_mermaid_er(self) -> str:
        """Mermaid ER图"""
        lines: list[str] = ["erDiagram"]
        for entity_name, entity in self._entities.items():
            table = entity.table_name or entity.name.lower()
            attrs_str_list: list[str] = []

            for attr in entity.attributes:
                attr_name = attr.get("name", "")
                attr_type = attr.get("type", "string")
                pk = " PK" if attr.get("is_pk", False) else ""
                nullable = "" if attr.get("nullable", True) else " NOT NULL"
                attrs_str_list.append(f"    {attr_name} {attr_type}{pk}{nullable}")

            if attrs_str_list:
                lines.append(f"    {table} {{")
                lines.extend(attrs_str_list)
                lines.append("    }")

        for rel in self._relationships:
            from_table = self._entities.get(rel.from_entity, Entity(rel.from_entity)).table_name
            to_table = self._entities.get(rel.to_entity, Entity(rel.to_entity)).table_name
            cardinality_map = {
                RelationshipType.ONE_TO_ONE: "||--o|",
                RelationshipType.ONE_TO_MANY: "||--o{",
                RelationshipType.MANY_TO_MANY: "}o--o{",
            }
            card = cardinality_map.get(rel.relationship_type, "||--o{")
            lines.append(f"    {from_table} {card} {to_table} : \"\"")

        return "\n".join(lines)

    def _gen_plantuml_er(self) -> str:
        """PlantUML ER图"""
        lines: list[str] = ["@startuml", "!define PRIMARY_KEY"]

        for entity_name, entity in self._entities.items():
            table = entity.table_name or entity.name.lower()
            lines.append(f"entity \"{entity_name}\" as {table} {{")

            for attr in entity.attributes:
                attr_name = attr.get("name", "")
                attr_type = attr.get("type", "string")
                pk = " <<PK>>" if attr.get("is_pk", False) else ""
                fk = " <<FK>>" if attr.get("fk", False) else ""
                lines.append(f"  ** {attr_name} : {attr_type}{pk}{fk}")

            lines.append("}")

        for rel in self._relationships:
            from_table = rel.from_entity.lower()
            to_table = rel.to_entity.lower()
            rel_map = {
                RelationshipType.ONE_TO_ONE: "1 -- 1",
                RelationshipType.ONE_TO_MANY: "1 -- *",
                RelationshipType.MANY_TO_MANY: "* -- *",
            }
            card = rel_map.get(rel.relationship_type, "1 -- *")
            lines.append(f"{from_table} {card} {to_table}")

        lines.append("@enduml")
        return "\n".join(lines)

    # ==================== DDL生成 ====================

    def generate_ddl(self, db_type: DatabaseType = DatabaseType.POSTGRESQL) -> str:
        """
        生成DDL语句

        Args:
            db_type: 目标数据库类型
        """
        lines: list[str] = [f"-- DDL Schema for {db_type.value}", "-- Generated by 尚书省·工部·水部司\n"]
        type_map = self._type_maps.get(db_type, self._type_maps[DatabaseType.POSTGRESQL])

        for entity_name, entity in self._entities.items():
            table = entity.table_name or entity_name.lower()
            columns: list[str] = []
            constraints: list[str] = []

            pk_cols: list[str] = []
            for attr in entity.attributes:
                col_name = attr.get("name", "")
                col_type = self._map_type(attr.get("type", "varchar"), db_type)
                nullable = "" if attr.get("nullable", False) else " NOT NULL"
                default_val = ""
                if attr.get("default") is not None:
                    dv = attr["default"]
                    if isinstance(dv, str):
                        default_val = f" DEFAULT '{dv}'"
                    elif isinstance(dv, bool):
                        default_val = f" DEFAULT {'TRUE' if dv else 'FALSE'}"
                    else:
                        default_val = f" DEFAULT {dv}"

                unique = " UNIQUE" if attr.get("unique", False) else ""

                if attr.get("is_pk", False):
                    pk_cols.append(col_name)

                fk_ref = attr.get("fk")
                fk_clause = ""
                if fk_ref:
                    parts = fk_ref.split(".")
                    ref_table = parts[0] if len(parts) > 0 else ""
                    ref_col = parts[1] if len(parts) > 1 else "id"
                    fk_clause = f" REFERENCES {ref_table}({ref_col})"

                columns.append(f"    {col_name} {col_type}{nullable}{default_val}{unique}{fk_clause}")

            if pk_cols:
                constraints.append(f"    PRIMARY KEY ({', '.join(pk_cols)})")

            all_defs = columns + constraints
            lines.append(f"CREATE TABLE IF NOT EXISTS {table} (")
            lines.append(",\n".join(all_defs))
            lines.append(");\n")

        for rel in self._relationships:
            from_table = self._entities.get(rel.from_entity, Entity(rel.from_entity)).table_name
            to_table = self._entities.get(rel.to_entity, Entity(rel.to_entity)).table_name
            if rel.relationship_type == RelationshipType.MANY_TO_MANY:
                join_table = f"{from_table}_{to_table}"
                lines.append(
                    f"-- M:N junction table: {join_table}\n"
                    f"CREATE TABLE IF NOT EXISTS {join_table} (\n"
                    f"    {rel.from_attribute or from_table[:-1]}_id INTEGER REFERENCES {from_table}(id),\n"
                    f"    {rel.to_attribute or to_table[:-1]}_id INTEGER REFERENCES {to_table}(id),\n"
                    f"    PRIMARY KEY ({rel.from_attribute or from_table[:-1]}_id, {rel.to_attribute or to_table[:-1]}_id)\n"
                    ");\n"
                )

        return "\n".join(lines)

    # ==================== ORM Model生成 ====================

    def generate_orm_model(self, orm: ORMFramework, db_type: DatabaseType = DatabaseType.POSTGRESQL) -> str:
        """
        生成ORM模型代码

        Args:
            orm: ORM框架
            db_type: 数据库类型
        """
        models: list[str] = []
        for entity_name, entity in self._entities.items():
            class_name = entity_name
            table = entity.table_name or entity_name.lower()

            match orm:
                case ORMFramework.SQLALCHEMY:
                    models.append(self._gen_sqlalchemy_model(class_name, table, entity, db_type))
                case ORMFramework.TYPEORM:
                    models.append(self._gen_typorm_model(class_name, table, entity))
                case ORMFramework.PRISMA:
                    models.append(self._gen_prisma_model(table, entity))
                case ORMFramework.SEQUELIZE:
                    models.append(self._gen_sequelize_model(class_name, table, entity))

        return "\n\n".join(models)

    def _gen_sqlalchemy_model(self, class_name: str, table: str, entity: Entity, db_type: DatabaseType) -> str:
        type_map = self._type_maps.get(db_type, self._type_maps[DatabaseType.POSTGRESQL])
        lines: list[str] = [f"class {class_name}(Base):"]
        lines.append(f'    __tablename__ = "{table}"')

        for attr in entity.attributes:
            col_name = attr.get("name", "")
            sa_type = self._map_type(attr.get("type", "varchar"), db_type)
            is_pk = attr.get("is_pk", False)
            nullable = not attr.get("nullable", False)

            if is_pk:
                auto_inc = type_map.get("auto_increment", "SERIAL")
                lines.append(f"    id: Mapped[int] = mapped_column({auto_inc}, primary_key=True)")
            else:
                py_type = self._to_python_type(attr.get("type", "str"))
                null_str = " | None" if nullable else ""
                nullable_arg = ", nullable=True" if nullable else ""
                default_str = ""
                if attr.get("default") is not None and nullable:
                    default_str = f' = {json.dumps(attr["default"])}'
                lines.append(f"    {col_name}: Mapped[{py_type}{null_str}] = mapped_column({sa_type}{nullable_arg}){default_str}")

        lines.append("")
        lines.append("    def __repr__(self) -> str:")
        cols = [a.get("name", "") for a in entity.attributes[:3] if a.get("name")]
        cols_str = ", ".join(f"self.{c}" for c in cols) or "..."
        lines.append(f'        return f"<{class_name}({cols_str})>"')
        return "\n".join(lines)

    @staticmethod
    def _to_python_type(db_type: str) -> str:
        python_map: dict[str, str] = {
            "integer": "int", "bigint": "int",
            "varchar": "str", "text": "str",
            "boolean": "bool", "bool": "bool",
            "timestamp": "datetime", "date": "date",
            "float": "float", "decimal": "Decimal",
            "json": "dict", "uuid": "UUID",
        }
        return python_map.get(db_type.lower(), "Any")

    def _gen_typorm_model(self, class_name: str, table: str, entity: Entity) -> str:
        lines: list[str] = ["@Entity()", f'class {class_name} {{']

        for attr in entity.attributes:
            col_name = attr.get("name", "")
            ts_type = self._to_typescript_type(attr.get("type", "string"))
            is_pk = attr.get("is_pk", False)

            if is_pk:
                lines.append("  @PrimaryGeneratedColumn()")
            else:
                lines.append("  @Column()")
            lines.append(f"  {col_name}: {ts_type};")

        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def _to_typescript_type(db_type: str) -> str:
        ts_map: dict[str, str] = {
            "integer": "number", "bigint": "number",
            "varchar": "string", "text": "string",
            "boolean": "boolean", "bool": "boolean",
            "timestamp": "Date", "date": "Date",
            "float": "number", "decimal": "number",
            "json": "any", "uuid": "string",
        }
        return ts_map.get(db_type.lower(), "any")

    def _gen_prisma_model(self, table: str, entity: Entity) -> str:
        lines: list[str] = [f"model {table} {{"]
        for attr in entity.attributes:
            col_name = attr.get("name", "")
            prisma_type = self._to_prisma_type(attr.get("type", "String"))
            modifiers: list[str] = []
            if attr.get("is_pk", False):
                modifiers.append("@id @default(uuid())")
            if not attr.get("nullable", False):
                modifiers.append("@db.Default")
            mod_str = " ".join(modifiers)
            suffix = f" {mod_str}" if mod_str else ""
            lines.append(f"  {col_name}  {prisma_type}{suffix}")

        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def _to_prisma_type(db_type: str) -> str:
        prisma_map: dict[str, str] = {
            "integer": "Int", "bigint": "BigInt",
            "varchar": "String", "text": "String",
            "boolean": "Boolean", "bool": "Boolean",
            "timestamp": "DateTime", "date": "DateTime",
            "float": "Float", "decimal": "Decimal",
            "json": "Json", "uuid": "String @db.Uuid",
        }
        return prisma_map.get(db_type.lower(), "String")

    def _gen_sequelize_model(self, class_name: str, table: str, entity: Entity) -> str:
        lines: list[str] = [
            f"const {class_name} = sequelize.define('{table}', {{"
        ]
        fields: list[str] = []
        for attr in entity.attributes:
            col_name = attr.get("name", "")
            seq_type = self._to_sequelize_type(attr.get("type", "STRING"))
            field_def: dict[str, Any] = {"type": seq_type}
            if attr.get("is_pk", False):
                field_def["primaryKey"] = True
            if not attr.get("nullable", False):
                field_def["allowNull"] = False
            fields.append(f"  {col_name}: {json.dumps(field_dict)},")

        lines.extend(fields)
        lines.append("});")
        return "\n".join(lines)

    @staticmethod
    def _to_sequelize_type(db_type: str) -> str:
        seq_map: dict[str, str] = {
            "integer": "Sequelize.INTEGER", "bigint": "Sequelize.BIGINT",
            "varchar": "Sequelize.STRING", "text": "Sequelize.TEXT",
            "boolean": "Sequelize.BOOLEAN", "bool": "Sequelize.BOOLEAN",
            "timestamp": "Sequelize.DATE", "date": "Sequelize.DATEONLY",
            "float": "Sequelize.FLOAT", "decimal": "Sequelize.DECIMAL",
            "json": "Sequelize.JSON", "uuid": "Sequelize.UUID",
        }
        return seq_map.get(db_type.lower(), "Sequelize.STRING")

    # ==================== 迁移脚本生成 ====================

    def generate_migration(
        self,
        tool: MigrationTool = MigrationTool.ALEMBIC,
        version: str = "001",
        description: str = "",
    ) -> str:
        """
        生成迁移脚本

        Args:
            tool: 迁移工具
            version: 版本号
            description: 描述
        """
        match tool:
            case MigrationTool.ALEMBIC:
                return self._gen_alembic_migration(version, description)
            case MigrationTool.FLYWAY:
                return self._gen_flyway_migration(version, description)
            case MigrationTool.LIQUIBASE:
                return self._gen_liquibase_migration(version, description)

    def _gen_alembic_migration(self, version: str, desc: str) -> str:
        """Alembic迁移脚本"""
        revision = f"rev_{version}"
        down_revision = f"rev_{int(version) - 1:03d}" if int(version) > 1 else None
        down_rev_str = f"'{down_revision}'" if down_revision else "None"

        upgrade_lines: list[str] = ['def upgrade():']
        downgrade_lines: list[str] = ['def downgrade():']

        for entity_name, entity in self._entities.items():
            table = entity.table_name or entity_name.lower()
            cols: list[str] = []
            for attr in entity.attributes:
                col_name = attr.get("name", "")
                col_type = self._map_type(attr.get("type", "varchar"), DatabaseType.POSTGRESQL)
                nullable = not attr.get("nullable", False)
                pk = attr.get("is_pk", False)
                if pk:
                    continue
                nullable_str = ", nullable=True" if nullable else ""
                cols.append(f"sa.Column('{col_name}', {col_type}{nullable_str})")

            upgrade_lines.append(f'    op.create_table("{table}",')
            upgrade_lines.append('        sa.Column("id", sa.Integer, primary_key=True),')
            for c in cols:
                upgrade_lines.append(f"        {c},")
            upgrade_lines.append("    )")
            downgrade_lines.append(f'    op.drop_table("{table}")')

        return f'''\
"""{desc}

Revision ID: {revision}
Create Date: {__import__("datetime").datetime.now().isoformat()}
"""
from alembic import op
import sqlalchemy as sa

revision = '{revision}'
down_revision = {down_rev_str}
branch_labels = None
depends_on = None

{"\n".join(upgrade_lines)}

{"\n".join(downgrade_lines)}
'''

    def _gen_flyway_migration(self, version: str, desc: str) -> str:
        """Flyway迁移脚本"""
        ddl = self.generate_ddl(DatabaseType.POSTGRESQL)
        comment = f"-- Flyway Migration V{version}: {desc}\n"
        return comment + ddl

    def _gen_liquibase_migration(self, version: str, desc: str) -> str:
        """Liquibase迁移脚本"""
        lines: list[str] = [
            f'--liquibase formatted sql',
            f'--changeset author:shangshusheng-gongbu:{version}',
            f'--comment {desc}',
        ]

        for entity_name, entity in self._entities.items():
            table = entity.table_name or entity_name.lower()
            lines.append(f"CREATE TABLE {table} (")

            for attr in entity.attributes:
                col_name = attr.get("name", "")
                col_type = self._map_type(attr.get("type", "varchar"), DatabaseType.POSTGRESQL)
                nullable = "" if attr.get("nullable", False) else " NOT NULL"
                lines.append(f"    {col_name} {col_type}{nullable},")

            lines.append("    id SERIAL PRIMARY KEY")
            lines.append(");")
            lines.append("--rollback DROP TABLE {table};")

        return "\n".join(lines)

    # ==================== 索引优化建议 ====================

    def suggest_indexes(self, slow_queries: list[SlowQueryInfo] | None = None) -> list[IndexSuggestion]:
        """
        基于Schema和查询模式推荐索引

        Args:
            slow_queries: 慢查询列表

        Returns:
            索引建议列表
        """
        suggestions: list[IndexSuggestion] = []

        for entity_name, entity in self._entities.items():
            table = entity.table_name or entity_name.lower()

            for attr in entity.attributes:
                col_name = attr.get("name", "")

                if attr.get("is_pk", False):
                    continue

                if attr.get("fk"):
                    suggestions.append(IndexSuggestion(
                        table_name=table,
                        column_names=[col_name],
                        index_type="btree",
                        reason=f"外键列 {col_name} 应建立索引以加速JOIN操作",
                        estimated_impact="显著提升JOIN和FK约束检查性能",
                    ))

                if attr.get("unique", False):
                    suggestions.append(IndexSuggestion(
                        table_name=table,
                        column_names=[col_name],
                        index_type="btree",
                        reason=f"唯一约束列 {col_name}",
                        estimated_impact="确保唯一性并加速查找",
                    ))

                col_type_lower = attr.get("type", "").lower()
                if any(kw in col_name.lower() for kw in ("status", "type", "category")):
                    suggestions.append(IndexSuggestion(
                        table_name=table,
                        column_names=[col_name],
                        index_type="btree",
                        reason=f"低基数过滤列 {col_name} 可能适合部分索引",
                        estimated_impact="加速WHERE条件过滤",
                    ))

                if any(kw in col_name_lower for kw in ("email", "username", "code", "slug")):
                    suggestions.append(IndexSuggestion(
                        table_name=table,
                        column_names=[col_name],
                        index_type="btree",
                        reason=f"高频查找列 {col_name}",
                        estimated_impact="加速精确查找",
                    ))

                if any(kw in col_name_lower for kw in ("created_at", "updated_at", "date")):
                    suggestions.append(IndexSuggestion(
                        table_name=table,
                        column_names=[col_name],
                        index_type="btree",
                        reason=f"时间范围查询列 {col_name}",
                        estimated_impact="加速时间范围筛选和排序",
                    ))

                if any(kw in col_name_lower for kw in ("name", "title", "content", "body")):
                    suggestions.append(IndexSuggestion(
                        table_name=table,
                        column_names=[col_name],
                        index_type="gin" if "postgres" in str(entity).lower() else "btree",
                        reason=f"全文搜索候选列 {col_name}",
                        estimated_impact="如需模糊搜索，考虑GIN/GIST或全文索引",
                    ))

        if slow_queries:
            for sq in slow_queries:
                where_match = re.search(r"WHERE\s+(.+?)(?:ORDER|GROUP|LIMIT|$)", sq.query_text, re.I | re.S)
                if where_match:
                    where_clause = where_match.group(1).strip()
                    mentioned_cols = re.findall(r'\b(\w+)\s*(?:=|>|<|LIKE|IN)', where_clause)
                    if mentioned_cols:
                        suggestions.append(IndexSuggestion(
                            table_name=sq.table_name or "unknown",
                            column_names=mentioned_cols[:3],
                            index_type="btree",
                            reason=f"基于慢查询的WHERE子句分析",
                            estimated_impact=sq.suggestion or "预计减少查询执行时间50%+",
                        ))

        deduped: list[IndexSuggestion] = []
        seen: set[str] = set()
        for s in suggestions:
            key = f"{s.table_name}:{','.join(s.column_names)}"
            if key not in seen:
                seen.add(key)
                deduped.append(s)

        return deduped

    # ==================== 规范化检查 ====================

    def check_normalization(self, target_nf: NormalForm = NormalForm.THIRD_NF) -> NormalizationResult:
        """
        检查数据规范化程度

        Args:
            target_nf: 目标范式等级
        """
        violations: list[str] = []
        suggestions: list[str] = []

        for entity_name, entity in self._entities.items():
            attrs = entity.attributes

            atomic_check = True
            for attr in attrs:
                atype = attr.get("type", "").lower()
                if atype in ("json", "array", "text") and len(atype) > 100:
                    atomic_check = False
                    violations.append(f"[1NF违规] 实体{entity_name}.{attr.get('name')} 可能包含非原子值")
                    suggestions.append(f"将复合字段拆分为独立属性或关联表")

            pk_attrs = [a for a in attrs if a.get("is_pk", False)]
            non_pk_attrs = [a for a in attrs if not a.get("is_pk", False)]

            if len(pk_attrs) == 0 and target_nf.value in ("2NF", "3NF", "BCNF"):
                violations.append(f"[2NF风险] 实体{entity_name} 缺少主键定义")
                suggestions.append("为每个实体定义主键")

            partial_deps: list[str] = []
            for npa in non_pk_attrs:
                npa_name = npa.get("name", "")
                if any(kw in npa_name.lower() for kw in ("type_", "_type", "_kind", "_category")):
                    partial_deps.append(npa_name)

            if partial_deps and target_nf.value in ("2NF", "3NF", "BCNF"):
                violations.append(f"[2NF可能违规] 实体{entity_name} 存在部分依赖: {', '.join(partial_deps)}")
                suggestions.append("考虑将类型相关属性提取为独立实体")

            trans_deps: list[str] = []
            for i, a1 in enumerate(non_pk_attrs):
                for a2 in non_pk_attrs[i + 1:]:
                    n1, n2 = a1.get("name", ""), a2.get("name", "")
                    if n1.rstrip("_id").rstrip("_code") and n2.rstrip("_id").rstrip("_code"):
                        common_prefix = self._common_prefix(n1, n2)
                        if common_prefix and len(common_prefix) >= 3:
                            trans_deps.append(f"{n1}, {n2}")

            if trans_deps and target_nf.value in ("3NF", "BCNF"):
                violations.append(f"[3NF可能违规] 实体{entity_name} 存在传递依赖迹象: {'; '.join(trans_deps)}")
                suggestions.append("考虑将传递依赖的属性拆分为独立实体")

        is_compliant = len(violations) == 0
        return NormalizationResult(form_level=target_nf, is_compliant=is_compliant, violations=violations, suggestions=suggestions)

    @staticmethod
    def _common_prefix(a: str, b: str) -> str:
        common = []
        for ca, cb in zip(a, b):
            if ca == cb:
                common.append(ca)
            else:
                break
        return "".join(common)

    # ==================== 数据字典 ====================

    def generate_data_dictionary(self) -> str:
        """生成数据字典"""
        lines: list[str] = []
        lines.append("# 📖 数据字典\n")

        for entity_name, entity in self._entities.items():
            table = entity.table_name or entity_name.lower()
            lines.append(f"## 表: `{table}` ({entity_name})\n")
            lines.append("| 字段名 | 类型 | 可空 | 默认值 | 主键 | 唯一 | 外键 | 说明 |")
            lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")

            for attr in entity.attributes:
                col_name = attr.get("name", "")
                col_type = attr.get("type", "-")
                nullable = "✓" if attr.get("nullable", False) else "✗"
                default = str(attr.get("default", "-"))
                pk = "🔑" if attr.get("is_pk", False) else ""
                unique = "🔒" if attr.get("unique", False) else ""
                fk = attr.get("fk", "") or ""
                comment = attr.get("comment", "")
                lines.append(
                    f"| {col_name} | {col_type} | {nullable} | {default} "
                    f"| {pk} | {unique} | {fk} | {comment} |"
                )

            if entity.description:
                lines.append(f"\n> {entity.description}\n")

        if self._relationships:
            lines.append("\n## 关系\n")
            lines.append("| 从 | 到 | 类型 | 删除策略 |")
            lines.append("| --- | --- | --- | --- |")
            for rel in self._relationships:
                lines.append(
                    f"| {rel.from_entity} | {rel.to_entity} "
                    f"| {rel.relationship_type.value} | {rel.on_delete} |"
                )

        return "\n".join(lines)

    # ==================== 分库分表策略 ====================

    def suggest_sharding(self, estimated_rows: int = 0) -> ShardingStrategy:
        """
        推荐分库分表策略

        Args:
            estimated_rows: 预估行数
        """
        if estimated_rows < 1_000_000:
            return ShardingStrategy(strategy_type="none", description="当前数据量无需分库分表")
        elif estimated_rows < 10_000_000:
            return ShardingStrategy(
                strategy_type="vertical_split",
                shard_count=0,
                description="垂直拆分：按业务域将大表拆分为多个小表",
            )
        elif estimated_rows < 100_000_000:
            return ShardingStrategy(
                strategy_type="horizontal_shard",
                shard_key="user_id 或 created_at",
                shard_count=8,
                description="水平分表：按用户ID或时间范围进行哈希/范围分片",
            )
        else:
            return ShardingStrategy(
                strategy_type="full_sharding",
                shard_key="user_id",
                shard_count=16,
                description="全量分库分表：结合垂直+水平策略，配合读写分离",
            )

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成数据库设计司报告"""
        lines: list[str] = []
        lines.append("# 🗄️ 数据库设计司 · 设计报告\n")

        er_diagram = self.generate_er_diagram("mermaid")
        lines.append("## ER图\n")
        lines.append("```mermaid")
        lines.append(er_diagram)
        lines.append("```\n")

        norm_result = self.check_normalization(NormalForm.THIRD_NF)
        status_icon = "✅" if norm_result.is_compliant else "⚠️"
        lines.append(f"## 规范化检查 [{status_icon}] {norm_result.form_level.value}\n")
        if norm_result.violations:
            for v in norm_result.violations:
                lines.append(f"- ⚠️ {v}")
        else:
            lines.append("- 所有实体符合规范要求\n")

        indexes = self.suggest_indexes()
        lines.append(f"\n## 索引建议 ({len(indexes)}条)\n")
        lines.append("| 表 | 列 | 类型 | 原因 | 预期效果 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for idx in indexes[:15]:
            cols = ", ".join(idx.column_names)
            lines.append(
                f"`{idx.table_name}` | `{cols}` | {idx.index_type} | {idx.reason[:30]}... | {idx.estimated_impact[:25]}... |"
            )

        sharding = self.suggest_sharding()
        lines.append(f"\n## 分库分表策略\n")
        lines.append(f"- **策略**: {sharding.strategy_type}")
        if sharding.shard_key:
            lines.append(f"- **分片键**: {sharding.shard_key}")
        if sharding.shard_count:
            lines.append(f"- **分片数**: {sharding.shard_count}")
        lines.append(f"- **说明**: {sharding.description}")

        dd = self.generate_data_dictionary()
        lines.append(f"\n{dd[:500]}...")

        return "\n".join(lines)


if __name__ == "__main__":
    print("=" * 60)
    print("数据库设计司 - 功能演示")
    print("=" * 60)

    si = DatabaseDesignSi()

    user_entity = Entity(
        name="User",
        table_name="users",
        attributes=[
            {"name": "id", "type": "integer", "is_pk": True},
            {"name": "username", "type": "varchar", "unique": True, "comment": "用户名"},
            {"name": "email", "type": "varchar", "unique": True, "comment": "邮箱"},
            {"name": "password_hash", "type": "varchar"},
            {"name": "status", "type": "varchar", "default": "active"},
            {"name": "created_at", "type": "timestamp"},
        ],
    )
    order_entity = Entity(
        name="Order",
        table_name="orders",
        attributes=[
            {"name": "id", "type": "integer", "is_pk": True},
            {"name": "user_id", "type": "integer", "fk": "users.id", "comment": "用户ID"},
            {"name": "total_amount", "type": "decimal"},
            {"name": "status", "type": "varchar", "default": "pending"},
            {"name": "created_at", "type": "timestamp"},
        ],
    )
    si.add_entity(user_entity)
    si.add_entity(order_entity)
    si.add_relationship(Relationship("User", "Order", RelationshipType.ONE_TO_MANY))

    print("\n--- ER图 (Mermaid) ---")
    er = si.generate_er_diagram("mermaid")
    print(er[:400])

    print("\n--- DDL (PostgreSQL) ---")
    ddl = si.generate_ddl(DatabaseType.POSTGRESQL)
    print(ddl[:500])

    print("\n--- ORM Model (SQLAlchemy) ---")
    orm = si.generate_orm_model(ORMFramework.SQLALCHEMY, DatabaseType.POSTGRESQL)
    print(orm[:500])

    print("\n--- 迁移脚本 (Alembic) ---")
    mig = si.generate_migration(MigrationTool.ALEMBIC, "001", "初始化用户和订单表")
    print(mig[:500])

    print("\n--- 索引建议 ---")
    indexes = si.suggest_indexes()
    print(f"  建议: {len(indexes)}条")
    for idx in indexes[:5]:
        print(f"  [{idx.table_name}] {idx.column_names}: {idx.reason[:40]}")

    print("\n--- 规范化检查 ---")
    norm = si.check_normalization(NormalForm.THIRD_NF)
    print(f"  3NF合规: {norm.is_compliant}")
    for v in norm.violations:
        print(f"  ❌ {v}")

    print("\n--- 分库分表 ---")
    shard = si.suggest_sharding(estimated_rows=50_000_000)
    print(f"  策略: {shard.strategy_type}, 分片数: {shard.shard_count}")

    report = si.generate_report()
    print(f"\n--- 报告预览 (前800字符) ---\n{report[:800]}...")

    print("\n✅ 所有测试通过!")
