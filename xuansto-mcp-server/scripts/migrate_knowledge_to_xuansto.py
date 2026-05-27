#!/usr/bin/env python3
"""
Data migration script: migrate data from knowledge.db to xuansto.db.

This script reads all data from the knowledge.db SQLite database and inserts
it into the unified xuansto.db database. It handles schema differences between
the two databases, including:

- knowledge_entries: merges fields from both schemas into unified table
- reconciliation_log: knowledge.db version -> kb_reconciliation_log
- All other knowledge.db tables are migrated as-is

Usage:
    python -m scripts.migrate_knowledge_to_xuansto [--knowledge-db PATH] [--xuansto-db PATH] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


def _find_default_knowledge_db() -> Path:
    candidates = [
        Path.home() / ".trae" / "skills" / "xuansto-skill-v2" / "scripts" / "knowledge_server" / ".knowledge" / "index" / "knowledge.db",
        Path.cwd() / ".knowledge" / "index" / "knowledge.db",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _find_default_xuansto_db() -> Path:
    candidates = [
        Path.home() / ".xuansto" / "xuansto.db",
        Path.cwd() / ".xuansto" / "xuansto.db",
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def _get_table_names(conn: sqlite3.Connection) -> set[str]:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    return {row[0] for row in cur.fetchall()}


def _get_column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cur.fetchall()}


def _migrate_knowledge_entries(src: sqlite3.Connection, dst: sqlite3.Connection, dry_run: bool) -> int:
    src_columns = _get_column_names(src, "knowledge_entries")
    dst_columns = _get_column_names(dst, "knowledge_entries")

    field_map = {
        "id": "id",
        "title": "title",
        "content": "content",
        "scope": "scope",
        "confidence": "confidence",
        "source_path": "source_path",
        "source_rating": "source_rating",
        "occurrences": "occurrences",
        "content_hash": "content_hash",
        "type": "type",
        "category": "category",
        "summary": "summary",
        "content_path": "content_path",
        "source": "source",
        "last_validated": "last_validated",
        "success_count": "success_count",
        "failure_count": "failure_count",
        "version": "version",
        "embedding_status": "embedding_status",
        "embedding_retry_count": "embedding_retry_count",
        "status": "status",
        "last_accessed": "last_accessed",
    }

    if "tags" in src_columns and "tags_json" in dst_columns:
        field_map["tags"] = "tags_json"
    elif "tags_json" in src_columns and "tags_json" in dst_columns:
        field_map["tags_json"] = "tags_json"

    if "created" in src_columns and "created_at" in dst_columns:
        field_map["created"] = "created_at"
    elif "created_at" in src_columns and "created_at" in dst_columns:
        field_map["created_at"] = "created_at"

    if "updated" in src_columns and "updated_at" in dst_columns:
        field_map["updated"] = "updated_at"
    elif "updated_at" in src_columns and "updated_at" in dst_columns:
        field_map["updated_at"] = "updated_at"

    if "metadata_json" in src_columns and "metadata_json" in dst_columns:
        field_map["metadata_json"] = "metadata_json"

    if "sync_status" in src_columns and "sync_status" in dst_columns:
        field_map["sync_status"] = "sync_status"

    if "deleted_at" in src_columns and "deleted_at" in dst_columns:
        field_map["deleted_at"] = "deleted_at"

    src_select_cols = list(field_map.keys())
    dst_insert_cols = list(field_map.values())

    select_sql = f"SELECT {', '.join(src_select_cols)} FROM knowledge_entries"
    cur = src.execute(select_sql)
    rows = cur.fetchall()

    if dry_run:
        print(f"  [DRY RUN] Would migrate {len(rows)} knowledge_entries rows")
        return len(rows)

    count = 0
    for row in rows:
        values = list(row)
        for i, col in enumerate(src_select_cols):
            if col == "tags" and isinstance(values[i], str):
                pass
            if col == "tags" and isinstance(values[i], list):
                values[i] = json.dumps(values[i], ensure_ascii=False)

        placeholders = ", ".join(["?"] * len(dst_insert_cols))
        col_str = ", ".join(dst_insert_cols)
        update_sets = ", ".join(f"{col} = excluded.{col}" for col in dst_insert_cols if col != "id")
        upsert_sql = f"INSERT INTO knowledge_entries ({col_str}) VALUES ({placeholders}) ON CONFLICT(id) DO UPDATE SET {update_sets}"

        try:
            dst.execute(upsert_sql, values)
            count += 1
        except sqlite3.IntegrityError as exc:
            print(f"  WARNING: Skipping knowledge_entry due to integrity error: {exc}")

    return count


def _migrate_table_simple(src: sqlite3.Connection, dst: sqlite3.Connection,
                          src_table: str, dst_table: str, dry_run: bool) -> int:
    src_columns = _get_column_names(src, src_table)
    dst_columns = _get_column_names(dst, dst_table)
    common = src_columns & dst_columns

    if not common:
        print(f"  WARNING: No common columns between {src_table} and {dst_table}")
        return 0

    cols = sorted(common)
    select_sql = f"SELECT {', '.join(cols)} FROM {src_table}"
    cur = src.execute(select_sql)
    rows = cur.fetchall()

    if dry_run:
        print(f"  [DRY RUN] Would migrate {len(rows)} rows from {src_table} -> {dst_table}")
        return len(rows)

    count = 0
    for row in rows:
        placeholders = ", ".join(["?"] * len(cols))
        col_str = ", ".join(cols)
        insert_sql = f"INSERT OR IGNORE INTO {dst_table} ({col_str}) VALUES ({placeholders})"
        try:
            dst.execute(insert_sql, list(row))
            count += 1
        except sqlite3.IntegrityError:
            pass

    return count


def _migrate_knowledge_tags(src: sqlite3.Connection, dst: sqlite3.Connection, dry_run: bool) -> int:
    if "knowledge_tags" not in _get_table_names(src):
        return 0
    return _migrate_table_simple(src, dst, "knowledge_tags", "knowledge_tags", dry_run)


def _migrate_dedup_log(src: sqlite3.Connection, dst: sqlite3.Connection, dry_run: bool) -> int:
    if "dedup_log" not in _get_table_names(src):
        return 0
    return _migrate_table_simple(src, dst, "dedup_log", "dedup_log", dry_run)


def _migrate_version_history(src: sqlite3.Connection, dst: sqlite3.Connection, dry_run: bool) -> int:
    if "version_history" not in _get_table_names(src):
        return 0
    return _migrate_table_simple(src, dst, "version_history", "version_history", dry_run)


def _migrate_usage_logs(src: sqlite3.Connection, dst: sqlite3.Connection, dry_run: bool) -> int:
    if "usage_logs" not in _get_table_names(src):
        return 0
    return _migrate_table_simple(src, dst, "usage_logs", "usage_logs", dry_run)


def _migrate_backup_history(src: sqlite3.Connection, dst: sqlite3.Connection, dry_run: bool) -> int:
    if "backup_history" not in _get_table_names(src):
        return 0
    return _migrate_table_simple(src, dst, "backup_history", "backup_history", dry_run)


def _migrate_kb_reconciliation_log(src: sqlite3.Connection, dst: sqlite3.Connection, dry_run: bool) -> int:
    if "reconciliation_log" not in _get_table_names(src):
        return 0
    src_columns = _get_column_names(src, "reconciliation_log")
    if "check_time" not in src_columns:
        print("  INFO: Source reconciliation_log does not have kb schema, skipping")
        return 0
    return _migrate_table_simple(src, dst, "reconciliation_log", "kb_reconciliation_log", dry_run)


def _migrate_schema_version(src: sqlite3.Connection, dst: sqlite3.Connection, dry_run: bool) -> int:
    if "schema_version" not in _get_table_names(src):
        return 0
    return _migrate_table_simple(src, dst, "schema_version", "schema_version", dry_run)


def _verify_counts(src: sqlite3.Connection, dst: sqlite3.Connection) -> dict[str, Any]:
    tables_to_verify = ["knowledge_entries", "knowledge_tags", "dedup_log", "version_history", "usage_logs", "backup_history"]
    mismatches = []
    for table in tables_to_verify:
        if table not in _get_table_names(src):
            continue
        src_cur = src.execute(f"SELECT COUNT(*) FROM {table}")
        src_count = src_cur.fetchone()[0]
        dst_cur = dst.execute(f"SELECT COUNT(*) FROM {table}")
        dst_count = dst_cur.fetchone()[0]
        if src_count != dst_count:
            mismatches.append({"table": table, "source_count": src_count, "target_count": dst_count})
    return {"mismatches": mismatches, "all_match": len(mismatches) == 0}


def _verify_chroma_consistency(dst: sqlite3.Connection) -> dict[str, Any]:
    issues = []
    try:
        import chromadb
        chroma_client = chromadb.PersistentClient(path=str(Path.home() / ".xuansto" / "chroma_db"))
        collection = chroma_client.get_or_create_collection("knowledge_entries")
        chroma_ids = set(collection.get()["ids"])
        cur = dst.execute("SELECT id FROM knowledge_entries WHERE deleted_at IS NULL")
        sqlite_ids = {row[0] for row in cur.fetchall()}
        missing_in_chroma = sqlite_ids - chroma_ids
        orphan_in_chroma = chroma_ids - sqlite_ids
        if missing_in_chroma:
            issues.append({"type": "missing_in_chroma", "count": len(missing_in_chroma), "ids": sorted(missing_in_chroma)[:20]})
        if orphan_in_chroma:
            issues.append({"type": "orphan_in_chroma", "count": len(orphan_in_chroma), "ids": sorted(orphan_in_chroma)[:20]})
    except ImportError:
        return {"available": False, "reason": "chromadb not installed"}
    except Exception as exc:
        return {"available": False, "reason": str(exc)}
    return {"available": True, "issues": issues, "consistent": len(issues) == 0}


def migrate(knowledge_db_path: Path, xuansto_db_path: Path, dry_run: bool = False) -> dict:
    print("Migrating data from knowledge.db -> xuansto.db")
    print(f"  Source: {knowledge_db_path}")
    print(f"  Target: {xuansto_db_path}")
    print(f"  Dry run: {dry_run}")
    print()

    if not knowledge_db_path.exists():
        print(f"ERROR: Source database not found: {knowledge_db_path}")
        return {"error": "source_not_found"}

    if not xuansto_db_path.exists():
        print(f"WARNING: Target database not found: {xuansto_db_path}")
        print("  The xuansto.db will be created by the MCP server on startup.")
        print("  Please start the MCP server first, then re-run this migration.")
        return {"error": "target_not_found"}

    src = sqlite3.connect(str(knowledge_db_path))
    src.row_factory = sqlite3.Row
    src.execute("PRAGMA journal_mode=WAL")

    dst = sqlite3.connect(str(xuansto_db_path))
    dst.row_factory = sqlite3.Row
    dst.execute("PRAGMA journal_mode=WAL")
    dst.execute("PRAGMA busy_timeout=5000")
    dst.execute("PRAGMA foreign_keys=OFF")

    results = {}

    try:
        print("1. Migrating knowledge_entries...")
        results["knowledge_entries"] = _migrate_knowledge_entries(src, dst, dry_run)
        print(f"   -> {results['knowledge_entries']} rows migrated")

        print("2. Migrating knowledge_tags...")
        results["knowledge_tags"] = _migrate_knowledge_tags(src, dst, dry_run)
        print(f"   -> {results['knowledge_tags']} rows migrated")

        print("3. Migrating dedup_log...")
        results["dedup_log"] = _migrate_dedup_log(src, dst, dry_run)
        print(f"   -> {results['dedup_log']} rows migrated")

        print("4. Migrating version_history...")
        results["version_history"] = _migrate_version_history(src, dst, dry_run)
        print(f"   -> {results['version_history']} rows migrated")

        print("5. Migrating usage_logs...")
        results["usage_logs"] = _migrate_usage_logs(src, dst, dry_run)
        print(f"   -> {results['usage_logs']} rows migrated")

        print("6. Migrating backup_history...")
        results["backup_history"] = _migrate_backup_history(src, dst, dry_run)
        print(f"   -> {results['backup_history']} rows migrated")

        print("7. Migrating kb_reconciliation_log...")
        results["kb_reconciliation_log"] = _migrate_kb_reconciliation_log(src, dst, dry_run)
        print(f"   -> {results['kb_reconciliation_log']} rows migrated")

        print("8. Migrating schema_version...")
        results["schema_version"] = _migrate_schema_version(src, dst, dry_run)
        print(f"   -> {results['schema_version']} rows migrated")

        if not dry_run:
            print()
            print("Rebuilding FTS5 index...")
            try:
                dst.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES ('rebuild')")
                print("   -> FTS5 index rebuilt successfully")
                results["fts5_rebuild"] = "success"
            except Exception as exc:
                print(f"   -> FTS5 rebuild failed (non-fatal): {exc}")
                results["fts5_rebuild"] = f"failed: {exc}"

            dst.commit()

            print()
            print("9. Verifying source/target row counts...")
            count_result = _verify_counts(src, dst)
            results["count_verification"] = count_result
            if count_result["all_match"]:
                print("   -> All table counts match!")
            else:
                print("   -> WARNING: Count mismatches detected:")
                for m in count_result["mismatches"]:
                    print(f"      {m['table']}: source={m['source_count']}, target={m['target_count']}")

            print("10. Verifying ChromaDB vector ID consistency...")
            chroma_result = _verify_chroma_consistency(dst)
            results["chroma_verification"] = chroma_result
            if not chroma_result.get("available", False):
                print(f"   -> Skipped: {chroma_result.get('reason', 'unknown')}")
            elif chroma_result.get("consistent", False):
                print("   -> ChromaDB vectors are consistent with SQLite!")
            else:
                print("   -> WARNING: ChromaDB inconsistencies detected:")
                for issue in chroma_result.get("issues", []):
                    print(f"      {issue['type']}: count={issue['count']}")

    except Exception as exc:
        print(f"\nERROR: Migration failed: {exc}")
        if not dry_run:
            try:
                dst.rollback()
                print("   -> Transaction rolled back successfully")
            except Exception as rb_exc:
                print(f"   -> Rollback also failed: {rb_exc}")
        results["error"] = str(exc)
        dst.execute("PRAGMA foreign_keys=ON")
        src.close()
        dst.close()
        return results

    dst.execute("PRAGMA foreign_keys=ON")
    src.close()
    dst.close()

    print()
    total = sum(v for v in results.values() if isinstance(v, int))
    print(f"Migration complete! Total rows migrated: {total}")
    if not dry_run:
        print("NOTE: The original knowledge.db has NOT been modified or deleted.")
        print("      You can safely remove it after verifying the migration.")

    return results


def main():
    parser = argparse.ArgumentParser(description="Migrate data from knowledge.db to xuansto.db")
    parser.add_argument("--knowledge-db", type=Path, default=None,
                        help="Path to knowledge.db (default: auto-detect)")
    parser.add_argument("--xuansto-db", type=Path, default=None,
                        help="Path to xuansto.db (default: auto-detect)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be migrated without actually migrating")
    args = parser.parse_args()

    knowledge_db = args.knowledge_db or _find_default_knowledge_db()
    xuansto_db = args.xuansto_db or _find_default_xuansto_db()

    result = migrate(knowledge_db, xuansto_db, dry_run=args.dry_run)
    if "error" in result:
        sys.exit(1)


if __name__ == "__main__":
    main()
