#!/usr/bin/env python3
"""知识库数据库模式迁移工具

对 SQLite 知识库执行增量模式迁移，支持事务回滚、
试运行预览和 JSON/文本格式输出。
"""

import argparse
import json
import logging
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

LATEST_SCHEMA_VERSION = 8

BUILTIN_MIGRATIONS = {
    (1, 2): {
        "description": "Add occurrences and content_hash columns",
        "sql": [
            "ALTER TABLE knowledge_entries ADD COLUMN occurrences INTEGER NOT NULL DEFAULT 1",
            "ALTER TABLE knowledge_entries ADD COLUMN content_hash TEXT",
        ],
    },
    (2, 3): {
        "description": "Add knowledge_fts virtual table using FTS5",
        "sql": [
            "CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5("
            "  content, "
            "  content='knowledge_entries', "
            "  content_rowid=id"
            ")",
            "INSERT INTO knowledge_fts(rowid, content) "
            "SELECT id, content FROM knowledge_entries",
        ],
    },
    (3, 4): {
        "description": "Add dedup_log table for tracking dedup operations",
        "sql": [
            "CREATE TABLE IF NOT EXISTS dedup_log ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "  new_entry_id TEXT NOT NULL, "
            "  existing_entry_id TEXT NOT NULL, "
            "  similarity_score REAL NOT NULL, "
            "  action TEXT NOT NULL CHECK(action IN ('skip', 'merge', 'keep_both')), "
            "  merged_at TEXT, "
            "  FOREIGN KEY (new_entry_id) REFERENCES knowledge_entries(id), "
            "  FOREIGN KEY (existing_entry_id) REFERENCES knowledge_entries(id)"
            ")",
            "CREATE INDEX IF NOT EXISTS idx_dedup_new ON dedup_log(new_entry_id)",
        ],
    },
    (4, 5): {
        "description": "Add backup_history table for tracking backup operations",
        "sql": [
            "CREATE TABLE IF NOT EXISTS backup_history ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "  backup_path TEXT NOT NULL, "
            "  backup_size INTEGER NOT NULL DEFAULT 0, "
            "  entry_count INTEGER NOT NULL DEFAULT 0, "
            "  created_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "  status TEXT NOT NULL DEFAULT 'pending'"
            ")",
        ],
    },
    (5, 6): {
        "description": "Add type/category/summary/content_path/last_validated/success_count/failure_count/version/embedding_status fields to knowledge_entries, rename created_at→created and updated_at→updated",
        "sql_builder": "_build_v5_to_v6_sql",
    },
    (6, 7): {
        "description": "Add knowledge_tags and reconciliation_log tables",
        "sql": [
            "CREATE TABLE IF NOT EXISTS knowledge_tags (entry_id TEXT NOT NULL, tag TEXT NOT NULL, PRIMARY KEY (entry_id, tag), FOREIGN KEY (entry_id) REFERENCES knowledge_entries(id) ON DELETE CASCADE)",
            "CREATE INDEX IF NOT EXISTS idx_tags_tag ON knowledge_tags(tag)",
            "CREATE TABLE IF NOT EXISTS reconciliation_log (id INTEGER PRIMARY KEY AUTOINCREMENT, check_time TEXT NOT NULL, sqlite_ready_count INTEGER, chroma_vector_count INTEGER, missing_in_chroma INTEGER DEFAULT 0, orphan_in_chroma INTEGER DEFAULT 0, fixed_count INTEGER DEFAULT 0, details TEXT)",
        ],
    },
    (7, 8): {
        "description": "Rebuild FTS5 with external content table and triggers, add missing indexes, update version_history with change_type and content_snapshot",
        "sql": [
            "DROP TABLE IF EXISTS knowledge_fts",
            "CREATE VIRTUAL TABLE knowledge_fts USING fts5(id UNINDEXED, summary, type, category, content='knowledge_entries', content_rowid='rowid', tokenize='unicode61')",
            "INSERT INTO knowledge_fts(rowid, id, summary, type, category) SELECT rowid, id, COALESCE(summary, title), type, category FROM knowledge_entries",
            "CREATE TRIGGER IF NOT EXISTS knowledge_entries_ai AFTER INSERT ON knowledge_entries BEGIN INSERT INTO knowledge_fts(rowid, id, summary, type, category) VALUES (new.rowid, new.id, new.summary, new.type, new.category); END",
            "CREATE TRIGGER IF NOT EXISTS knowledge_entries_ad AFTER DELETE ON knowledge_entries BEGIN INSERT INTO knowledge_fts(knowledge_fts, rowid, id, summary, type, category) VALUES ('delete', old.rowid, old.id, old.summary, old.type, old.category); END",
            "CREATE TRIGGER IF NOT EXISTS knowledge_entries_au AFTER UPDATE ON knowledge_entries BEGIN INSERT INTO knowledge_fts(knowledge_fts, rowid, id, summary, type, category) VALUES ('delete', old.rowid, old.id, old.summary, old.type, old.category); INSERT INTO knowledge_fts(rowid, id, summary, type, category) VALUES (new.rowid, new.id, new.summary, new.type, new.category); END",
            "CREATE INDEX IF NOT EXISTS idx_entries_type ON knowledge_entries(type)",
            "CREATE INDEX IF NOT EXISTS idx_entries_category ON knowledge_entries(category)",
            "CREATE INDEX IF NOT EXISTS idx_entries_created ON knowledge_entries(created)",
            "CREATE INDEX IF NOT EXISTS idx_entries_updated ON knowledge_entries(updated)",
            "CREATE INDEX IF NOT EXISTS idx_version_entry2 ON version_history(entry_id, version)",
            "ALTER TABLE version_history ADD COLUMN change_type TEXT DEFAULT 'update'",
            "ALTER TABLE version_history ADD COLUMN content_snapshot TEXT",
        ],
    },
}

logger = logging.getLogger("kb-migrate")


def _sqlite_supports_rename_column(conn: sqlite3.Connection) -> bool:
    version_tuple = tuple(int(x) for x in sqlite3.sqlite_version.split(".")[:3])
    return version_tuple >= (3, 25, 0)


def _rebuild_table_rename_columns(conn: sqlite3.Connection, table_name: str, column_renames: dict[str, str]) -> list[str]:
    cur = conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    row = cur.fetchone()
    if not row:
        return []
    original_sql = row[0]
    temp_name = f"{table_name}__rename_tmp"
    new_sql = original_sql.replace(f"CREATE TABLE {table_name}", f"CREATE TABLE {temp_name}", 1)
    for old_name, new_name in column_renames.items():
        new_sql = re.sub(rf'\b{re.escape(old_name)}\b', new_name, new_sql)
    cur2 = conn.execute(f"PRAGMA table_info({table_name})")
    col_names = [col[1] for col in cur2.fetchall()]
    select_cols = ", ".join(
        f"{c} AS {column_renames[c]}" if c in column_renames else c
        for c in col_names
    )
    return [
        new_sql,
        f"INSERT INTO {temp_name} SELECT {select_cols} FROM {table_name}",
        f"DROP TABLE {table_name}",
        f"ALTER TABLE {temp_name} RENAME TO {table_name}",
    ]


def _build_v5_to_v6_sql(conn: sqlite3.Connection) -> list[str]:
    stmts = [
        "ALTER TABLE knowledge_entries ADD COLUMN type TEXT NOT NULL DEFAULT 'unknown'",
        "ALTER TABLE knowledge_entries ADD COLUMN category TEXT NOT NULL DEFAULT 'uncategorized'",
        "ALTER TABLE knowledge_entries ADD COLUMN summary TEXT",
        "ALTER TABLE knowledge_entries ADD COLUMN content_path TEXT",
        "ALTER TABLE knowledge_entries ADD COLUMN last_validated TEXT",
        "ALTER TABLE knowledge_entries ADD COLUMN success_count INTEGER DEFAULT 0",
        "ALTER TABLE knowledge_entries ADD COLUMN failure_count INTEGER DEFAULT 0",
        "ALTER TABLE knowledge_entries ADD COLUMN version INTEGER DEFAULT 1",
        "ALTER TABLE knowledge_entries ADD COLUMN embedding_status TEXT DEFAULT 'ready' CHECK(embedding_status IN ('pending','ready'))",
    ]
    if _sqlite_supports_rename_column(conn):
        stmts.append("ALTER TABLE knowledge_entries RENAME COLUMN created_at TO created")
        stmts.append("ALTER TABLE knowledge_entries RENAME COLUMN updated_at TO updated")
    else:
        stmts.extend(_rebuild_table_rename_columns(
            conn, "knowledge_entries", {"created_at": "created", "updated_at": "updated"}
        ))
    return stmts


def get_current_version(conn: sqlite3.Connection) -> int:
    """读取当前数据库模式版本号"""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version'"
    )
    if cursor.fetchone() is None:
        return 0
    row = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()
    return row[0] if row[0] is not None else 0


def ensure_schema_version_table(conn: sqlite3.Connection, current_version: int) -> None:
    """确保 schema_version 表存在并写入初始版本"""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_version (version INTEGER PRIMARY KEY, description TEXT)"
    )
    if current_version == 0:
        conn.execute("INSERT INTO schema_version (version, description) VALUES (0, 'initial')")
        conn.commit()


def load_external_migration(migrations_dir: Path, from_v: int, to_v: int) -> dict | None:
    """从外部目录加载迁移 SQL 文件"""
    filename = f"v{from_v}_to_v{to_v}.sql"
    filepath = migrations_dir / filename
    if not filepath.is_file():
        return None
    sql_text = filepath.read_text(encoding="utf-8")
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]
    return {
        "description": f"External migration {filename}",
        "sql": statements,
    }


def get_migration(migrations_dir: Path, from_v: int, to_v: int) -> dict | None:
    """获取迁移定义，优先使用内建迁移，回退到外部文件"""
    key = (from_v, to_v)
    if key in BUILTIN_MIGRATIONS:
        return BUILTIN_MIGRATIONS[key]
    return load_external_migration(migrations_dir, from_v, to_v)


def build_migration_plan(current_version: int, target_version: int, migrations_dir: Path) -> list[dict]:
    """构建从当前版本到目标版本的迁移计划"""
    plan = []
    v = current_version
    while v < target_version:
        next_v = v + 1
        migration = get_migration(migrations_dir, v, next_v)
        if migration is None:
            logger.error("找不到迁移定义: v%d -> v%d", v, next_v)
            break
        plan.append({
            "from_version": v,
            "to_version": next_v,
            "description": migration["description"],
            "sql": migration.get("sql"),
            "sql_builder": migration.get("sql_builder"),
        })
        v = next_v
    return plan


def execute_migration(conn: sqlite3.Connection, migration: dict, dry_run: bool) -> dict:
    """执行单次迁移，失败时自动回滚当前事务"""
    from_v = migration["from_version"]
    to_v = migration["to_version"]
    description = migration["description"]
    result = {
        "from_version": from_v,
        "to_version": to_v,
        "description": description,
    }

    if dry_run:
        result["status"] = "dry_run"
        result["duration_ms"] = 0
        return result

    start = time.monotonic()
    try:
        conn.execute("BEGIN IMMEDIATE")
        sql_builder_name = migration.get("sql_builder")
        if sql_builder_name:
            builder_fn = globals().get(sql_builder_name)
            if builder_fn is None:
                raise RuntimeError(f"sql_builder function not found: {sql_builder_name}")
            stmts = builder_fn(conn)
        else:
            stmts = migration["sql"]
        for stmt in stmts:
            conn.execute(stmt)
        conn.execute(
            "INSERT INTO schema_version (version, description) VALUES (?, ?)",
            (to_v, description),
        )
        conn.execute(
            "DELETE FROM schema_version WHERE version < ?", (to_v,)
        )
        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        if integrity[0] != "ok":
            raise RuntimeError(f"Integrity check failed after migration: {integrity[0]}")
        fk_check = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_check:
            raise RuntimeError(f"Foreign key check failed after migration: {len(fk_check)} violations")
        conn.commit()
        elapsed_ms = int((time.monotonic() - start) * 1000)
        result["status"] = "applied"
        result["duration_ms"] = elapsed_ms
        logger.info("迁移完成: v%d -> v%d (%dms)", from_v, to_v, elapsed_ms)
    except Exception as exc:
        conn.rollback()
        elapsed_ms = int((time.monotonic() - start) * 1000)
        result["status"] = "failed"
        result["duration_ms"] = elapsed_ms
        result["error"] = str(exc)
        logger.error("迁移失败: v%d -> v%d: %s", from_v, to_v, exc)
    return result


def run_migrations(db_path: Path, target_version: int, dry_run: bool, migrations_dir: Path) -> dict:
    """执行完整的迁移流程"""
    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "migrations_applied": [],
    }

    if not db_path.is_file():
        output["status"] = "error"
        output["error"] = f"数据库文件不存在: {db_path}"
        output["current_version"] = 0
        output["target_version"] = target_version
        output["final_version"] = 0
        return output

    conn = sqlite3.Connection(str(db_path), isolation_level=None)
    try:
        current_version = get_current_version(conn)
        output["current_version"] = current_version
        output["target_version"] = target_version

        if current_version >= target_version:
            output["final_version"] = current_version
            output["status"] = "success"
            logger.info("当前版本 %d 已达到目标版本 %d，无需迁移", current_version, target_version)
            return output

        ensure_schema_version_table(conn, current_version)
        plan = build_migration_plan(current_version, target_version, migrations_dir)

        if not plan:
            output["final_version"] = current_version
            output["status"] = "error"
            output["error"] = "无法构建迁移计划"
            return output

        for step in plan:
            result = execute_migration(conn, step, dry_run)
            output["migrations_applied"].append(result)
            if result["status"] == "failed":
                output["final_version"] = step["from_version"]
                output["status"] = "migration_failed"
                return output

        output["final_version"] = target_version
        output["status"] = "success"
    except Exception as exc:
        output["status"] = "error"
        output["error"] = str(exc)
        output.setdefault("final_version", 0)
        logger.error("迁移过程异常: %s", exc)
    finally:
        conn.close()

    return output


def format_text_output(result: dict) -> str:
    """将迁移结果格式化为可读文本"""
    lines = []
    lines.append(f"知识库模式迁移报告")
    lines.append(f"{'=' * 40}")
    lines.append(f"时间: {result['timestamp']}")
    lines.append(f"当前版本: {result['current_version']}")
    lines.append(f"目标版本: {result['target_version']}")
    lines.append(f"试运行: {'是' if result['dry_run'] else '否'}")
    lines.append(f"最终版本: {result['final_version']}")
    lines.append(f"状态: {result['status']}")

    if result.get("error"):
        lines.append(f"错误: {result['error']}")

    applied = result.get("migrations_applied", [])
    if applied:
        lines.append(f"")
        lines.append(f"迁移步骤:")
        for m in applied:
            status_label = m["status"]
            duration = m.get("duration_ms", 0)
            lines.append(
                f"  v{m['from_version']} -> v{m['to_version']}: "
                f"{m['description']} [{status_label}] ({duration}ms)"
            )
            if m.get("error"):
                lines.append(f"    错误: {m['error']}")
    else:
        lines.append(f"无需迁移")

    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="知识库数据库模式迁移工具"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=Path(".knowledge/index/knowledge.db"),
        help="知识库 SQLite 数据库文件路径 (默认: .knowledge/index/knowledge.db)",
    )
    parser.add_argument(
        "--target-version",
        type=int,
        default=LATEST_SCHEMA_VERSION,
        help=f"目标模式版本号 (默认: {LATEST_SCHEMA_VERSION})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="试运行模式，仅预览迁移操作不实际执行",
    )
    parser.add_argument(
        "--migrations-dir",
        type=Path,
        default=Path(".knowledge/migrations"),
        help="外部迁移 SQL 文件目录 (默认: .knowledge/migrations)",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="输出格式: json 或 text (默认: json)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """主入口函数"""
    args = parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    db_path = args.db_path.resolve()
    migrations_dir = args.migrations_dir.resolve()
    target_version = args.target_version

    if target_version < 1 or target_version > LATEST_SCHEMA_VERSION:
        logger.error("目标版本 %d 超出有效范围 [1, %d]", target_version, LATEST_SCHEMA_VERSION)
        return 2

    result = run_migrations(db_path, target_version, args.dry_run, migrations_dir)

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(format_text_output(result))

    status = result.get("status", "error")
    if status == "success":
        return 0
    elif status == "migration_failed":
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())
