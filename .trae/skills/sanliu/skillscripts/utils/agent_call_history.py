#!/usr/bin/env python3
"""
Agent调用历史记录系统 - 记录、追踪和分析Agent调用

功能：
1. 记录Agent调用历史
2. 追踪调用链路
3. 性能分析
4. 调用统计
"""

import json
import sqlite3
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager

from skillscripts.core.path_config_center import get_path_config

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "utils"))
from path_config_manager import PathConfigManager

logger = logging.getLogger(__name__)


@dataclass
class AgentCallRecord:
    """Agent调用记录"""
    call_id: str
    timestamp: str
    caller: str
    agent_name: str
    task: str
    context: Dict[str, Any]
    status: str
    result: Optional[Dict[str, Any]] = None
    duration_ms: Optional[int] = None
    quality_score: Optional[float] = None
    error_message: Optional[str] = None
    trace_id: Optional[str] = None


class AgentCallHistory:
    """Agent调用历史记录系统"""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            path_manager = PathConfigManager()
            db_path = str(path_manager.get_data_path() / "agent_calls.db")
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    @contextmanager
    def _get_connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_database(self):
        """初始化数据库"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_calls (
                    call_id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    caller TEXT NOT NULL,
                    agent_name TEXT NOT NULL,
                    task TEXT NOT NULL,
                    context TEXT,
                    status TEXT NOT NULL,
                    result TEXT,
                    duration_ms INTEGER,
                    quality_score REAL,
                    error_message TEXT,
                    trace_id TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agent_name ON agent_calls(agent_name)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_timestamp ON agent_calls(timestamp)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON agent_calls(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_caller ON agent_calls(caller)
            """)
            
            conn.commit()
    
    def record_call(self, record: AgentCallRecord) -> str:
        """记录Agent调用"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO agent_calls 
                (call_id, timestamp, caller, agent_name, task, context, status, 
                 result, duration_ms, quality_score, error_message, trace_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.call_id,
                record.timestamp,
                record.caller,
                record.agent_name,
                record.task,
                json.dumps(record.context, ensure_ascii=False),
                record.status,
                json.dumps(record.result, ensure_ascii=False) if record.result else None,
                record.duration_ms,
                record.quality_score,
                record.error_message,
                record.trace_id
            ))
            
            conn.commit()
            
            logger.info(f"Recorded agent call: {record.call_id} - {record.agent_name}")
            return record.call_id
    
    def get_call(self, call_id: str) -> Optional[Dict]:
        """获取调用记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM agent_calls WHERE call_id = ?
            """, (call_id,))
            
            row = cursor.fetchone()
            
            if row:
                return self._row_to_dict(row)
            return None
    
    def get_calls_by_agent(self, agent_name: str, limit: int = 100) -> List[Dict]:
        """获取指定Agent的调用记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM agent_calls 
                WHERE agent_name = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (agent_name, limit))
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_calls_by_caller(self, caller: str, limit: int = 100) -> List[Dict]:
        """获取指定调用者的调用记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM agent_calls 
                WHERE caller = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (caller, limit))
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_recent_calls(self, limit: int = 100) -> List[Dict]:
        """获取最近的调用记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM agent_calls 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return [self._row_to_dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """获取调用统计"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_calls,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_calls,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_calls,
                    AVG(duration_ms) as avg_duration_ms,
                    AVG(quality_score) as avg_quality_score
                FROM agent_calls
            """)
            
            stats = dict(cursor.fetchone())
            
            cursor.execute("""
                SELECT agent_name, COUNT(*) as call_count
                FROM agent_calls
                GROUP BY agent_name
                ORDER BY call_count DESC
                LIMIT 10
            """)
            
            stats['top_agents'] = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT caller, COUNT(*) as call_count
                FROM agent_calls
                GROUP BY caller
                ORDER BY call_count DESC
                LIMIT 10
            """)
            
            stats['top_callers'] = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("""
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as call_count
                FROM agent_calls
                GROUP BY DATE(timestamp)
                ORDER BY date DESC
                LIMIT 7
            """)
            
            stats['daily_calls'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    def get_performance_report(self, agent_name: str = None) -> Dict:
        """获取性能报告"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            if agent_name:
                cursor.execute("""
                    SELECT 
                        agent_name,
                        COUNT(*) as total_calls,
                        AVG(duration_ms) as avg_duration_ms,
                        MIN(duration_ms) as min_duration_ms,
                        MAX(duration_ms) as max_duration_ms,
                        AVG(quality_score) as avg_quality_score,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) * 100.0 / COUNT(*) as success_rate
                    FROM agent_calls
                    WHERE agent_name = ?
                    GROUP BY agent_name
                """, (agent_name,))
            else:
                cursor.execute("""
                    SELECT 
                        agent_name,
                        COUNT(*) as total_calls,
                        AVG(duration_ms) as avg_duration_ms,
                        MIN(duration_ms) as min_duration_ms,
                        MAX(duration_ms) as max_duration_ms,
                        AVG(quality_score) as avg_quality_score,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) * 100.0 / COUNT(*) as success_rate
                    FROM agent_calls
                    GROUP BY agent_name
                    ORDER BY total_calls DESC
                """)
            
            return {
                "agent_name": agent_name,
                "performance": [dict(row) for row in cursor.fetchall()]
            }
    
    def cleanup_old_records(self, days: int = 30) -> int:
        """清理旧记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM agent_calls
                WHERE date(timestamp) < date('now', ?)
            """, (f'-{days} days',))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Cleaned up {deleted_count} old records")
            return deleted_count
    
    def _row_to_dict(self, row: sqlite3.Row) -> Dict:
        """将数据库行转换为字典"""
        result = dict(row)
        
        if result.get('context'):
            result['context'] = json.loads(result['context'])
        
        if result.get('result'):
            result['result'] = json.loads(result['result'])
        
        return result


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Agent调用历史记录系统")
    parser.add_argument("--stats", "-s", action="store_true", help="显示调用统计")
    parser.add_argument("--recent", "-r", type=int, help="显示最近的N条调用记录")
    parser.add_argument("--agent", "-a", help="查询指定Agent的调用记录")
    parser.add_argument("--caller", "-c", help="查询指定调用者的调用记录")
    parser.add_argument("--performance", "-p", help="显示性能报告（可指定Agent）")
    parser.add_argument("--cleanup", type=int, help="清理N天前的旧记录")
    parser.add_argument("--output", "-o", help="输出文件路径")
    
    args = parser.parse_args()
    
    history = AgentCallHistory()
    
    result = {}
    
    if args.stats:
        result = history.get_statistics()
    elif args.recent:
        result = {
            "recent_calls": history.get_recent_calls(args.recent)
        }
    elif args.agent:
        result = {
            "agent": args.agent,
            "calls": history.get_calls_by_agent(args.agent)
        }
    elif args.caller:
        result = {
            "caller": args.caller,
            "calls": history.get_calls_by_caller(args.caller)
        }
    elif args.performance is not None:
        result = history.get_performance_report(args.performance if args.performance else None)
    elif args.cleanup:
        result = {
            "cleanup": {
                "days": args.cleanup,
                "deleted_count": history.cleanup_old_records(args.cleanup)
            }
        }
    else:
        result = {
            "statistics": history.get_statistics(),
            "recent_calls": history.get_recent_calls(10)
        }
    
    output_json = json.dumps(result, ensure_ascii=False, indent=2)
    
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output_json)
        print(f"结果已保存到: {args.output}")
    else:
        print(output_json)


if __name__ == "__main__":
    main()
