import hashlib
import json
import logging
import os
import sqlite3
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import KnowledgeConfig, KB_VERSION
from .db_engine import SQLiteEngine

logger = logging.getLogger("knowledge-server")


class BackupManager:
    def __init__(self, config: KnowledgeConfig, sqlite_engine: SQLiteEngine):
        self.config = config
        self.sqlite = sqlite_engine
        self._ensure_dirs()

    def _ensure_dirs(self):
        root = self.config.knowledge_root
        for subdir in ("full", "incremental", "snapshot", "scheduled"):
            (root / "backup" / subdir).mkdir(parents=True, exist_ok=True)

    def _log_backup_history(self, backup_path: str, backup_size: int, entry_count: int, status: str = "completed"):
        conn = self.sqlite._get_conn()
        conn.execute(
            "INSERT INTO backup_history (backup_path, backup_size, entry_count, status) VALUES (?, ?, ?, ?)",
            (backup_path, backup_size, entry_count, status),
        )
        conn.commit()

    def _scheduled_sqlite_backup(self):
        try:
            conn = self.sqlite._get_conn()
            integrity = conn.execute("PRAGMA integrity_check").fetchone()
            if integrity[0] != "ok":
                logger.warning("operation=scheduled_sqlite_backup, integrity_check=%s", integrity[0])
                return
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")

            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_dir = self.config.knowledge_root / "backup" / "scheduled"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / f"sqlite-{timestamp}.db"

            dest_conn = sqlite3.connect(str(backup_path))
            conn.backup(dest_conn)
            dest_conn.close()

            entry_count = self.sqlite.count_entries().get("total", 0)
            backup_size = backup_path.stat().st_size
            self._log_backup_history(str(backup_path), backup_size, entry_count)
            logger.info("operation=scheduled_sqlite_backup, path=%s, size=%d", backup_path, backup_size)
        except Exception as e:
            logger.warning("operation=scheduled_sqlite_backup, status=failed, error=%s", e)
            try:
                self._log_backup_history(str(backup_path) if 'backup_path' in locals() else "", 0, 0, "failed")
            except Exception:
                pass

    def _scheduled_chroma_backup(self):
        chroma_path = self.config.chroma_path
        if not chroma_path.exists():
            return
        try:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup_dir = self.config.knowledge_root / "backup" / "scheduled"
            backup_dir.mkdir(parents=True, exist_ok=True)
            tar_path = backup_dir / f"chroma-{timestamp}.tar.gz"

            with tarfile.open(str(tar_path), "w:gz") as tar:
                tar.add(str(chroma_path), arcname=chroma_path.name)

            entry_count = self.sqlite.count_entries().get("total", 0)
            backup_size = tar_path.stat().st_size
            self._log_backup_history(str(tar_path), backup_size, entry_count)
            logger.info("operation=scheduled_chroma_backup, path=%s, size=%d", tar_path, backup_size)
        except Exception as e:
            logger.warning("operation=scheduled_chroma_backup, status=failed, error=%s", e)

    def _cleanup_old_backups(self):
        backup_dir = self.config.knowledge_root / "backup" / "scheduled"
        if not backup_dir.exists():
            return
        try:
            sqlite_backups = sorted(backup_dir.glob("sqlite-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
            for old in sqlite_backups[10:]:
                old.unlink(missing_ok=True)
                logger.info("operation=cleanup_sqlite_backup, removed=%s", old)

            chroma_backups = sorted(backup_dir.glob("chroma-*.tar.gz"), key=lambda p: p.stat().st_mtime, reverse=True)
            for old in chroma_backups[7:]:
                old.unlink(missing_ok=True)
                logger.info("operation=cleanup_chroma_backup, removed=%s", old)
        except Exception as e:
            logger.warning("operation=cleanup_old_backups, error=%s", e)

    def _encrypt_backup(self, backup_path: Path) -> Optional[Path]:
        backup_key = os.environ.get("KNOWLEDGE_BACKUP_KEY")
        if not backup_key:
            return None
        try:
            from cryptography.fernet import Fernet
            import base64
            key = base64.urlsafe_b64encode(hashlib.sha256(backup_key.encode()).digest())
            fernet = Fernet(key)
            data = backup_path.read_bytes()
            encrypted = fernet.encrypt(data)
            enc_path = backup_path.with_suffix(backup_path.suffix + ".enc")
            enc_path.write_bytes(encrypted)
            backup_path.unlink(missing_ok=True)
            logger.info("operation=encrypt_backup, path=%s", enc_path)
            return enc_path
        except ImportError:
            logger.warning("operation=encrypt_backup, status=skipped, reason=cryptography_not_installed")
            return None
        except Exception as e:
            logger.warning("operation=encrypt_backup, status=failed, error=%s", e)
            return None

    def create_backup(self, backup_type: str = "full", destination: Optional[str] = None) -> dict:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        root = self.config.knowledge_root

        if backup_type == "full":
            backup_dir = root / "backup" / "full"
        elif backup_type == "incremental":
            backup_dir = root / "backup" / "incremental"
        elif backup_type == "snapshot":
            backup_dir = root / "backup" / "snapshot"
        else:
            backup_dir = root / "backup" / "full"

        if destination:
            backup_dir = Path(destination)
        backup_dir.mkdir(parents=True, exist_ok=True)

        entries = self.sqlite.get_all_entries()
        json_path = backup_dir / f"kb-backup-{timestamp}.json"

        backup_data = {
            "version": KB_VERSION,
            "type": backup_type,
            "timestamp": timestamp,
            "entries_count": len(entries),
            "entries": entries,
        }
        json_path.write_text(
            json.dumps(backup_data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        tar_path = backup_dir / f"kb-backup-{timestamp}.tar.gz"
        with tarfile.open(str(tar_path), "w:gz") as tar:
            tar.add(str(json_path), arcname=json_path.name)
            db_path = self.config.sqlite_path
            if db_path.exists():
                tar.add(str(db_path), arcname="knowledge.db")

        size_bytes = tar_path.stat().st_size

        self._encrypt_backup(tar_path)

        self._log_backup_history(str(tar_path), size_bytes, len(entries))

        return {
            "status": "completed",
            "type": backup_type,
            "backup_path": str(tar_path),
            "entries_count": len(entries),
            "size_bytes": size_bytes,
            "timestamp": timestamp,
        }

    def rollback(self, backup_path: str, dry_run: bool = False) -> dict:
        tar_path = Path(backup_path)
        if not tar_path.exists():
            raise FileNotFoundError(f"备份文件不存在: {backup_path}")

        with tarfile.open(str(tar_path), "r:gz") as tar:
            json_members = [m for m in tar.getmembers() if m.name.endswith(".json")]
            if not json_members:
                raise ValueError("备份文件中未找到JSON数据")

            f = tar.extractfile(json_members[0])
            if f is None:
                raise ValueError("无法读取备份JSON")
            backup_data = json.loads(f.read().decode("utf-8"))

        entries = backup_data.get("entries", [])
        if dry_run:
            return {
                "status": "dry_run",
                "backup_path": backup_path,
                "entries_restored": len(entries),
                "entries_removed": 0,
            }

        current_entries = self.sqlite.get_all_entries()
        current_ids = {e["id"] for e in current_entries}
        backup_ids = {e["id"] for e in entries}
        removed_count = len(current_ids - backup_ids)

        conn = self.sqlite._get_conn()
        conn.execute("DELETE FROM knowledge_entries")
        conn.commit()

        restored = 0
        for entry in entries:
            try:
                self.sqlite.add_entry(entry)
                restored += 1
            except Exception as e:
                logger.warning("operation=restore_failed, entry_id=%s, error=%s", entry.get("id"), e)

        return {
            "status": "rolled_back",
            "backup_path": backup_path,
            "entries_restored": restored,
            "entries_removed": removed_count,
        }
