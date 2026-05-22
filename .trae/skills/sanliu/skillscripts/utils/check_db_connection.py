#!/usr/bin/env python3
"""
数据库连接检查工具
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

def check_db_connection(db_path: str = './backend/backend_test.db') -> Dict[str, Any]:
    """检查数据库连接"""
    db_file = Path(db_path)
    
    result = {
        'db_path': str(db_file),
        'exists': db_file.exists(),
        'connection': False,
        'tables': []
    }
    
    if db_file.exists():
        try:
            import sqlite3
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            result['tables'] = [row[0] for row in cursor.fetchall()]
            result['connection'] = True
            conn.close()
        except Exception as e:
            result['error'] = str(e)
    
    return result

def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description='数据库连接检查')
    parser.add_argument('--db-path', type=str, default='./backend/backend_test.db',
                       help='数据库路径')
    
    args = parser.parse_args()
    
    result = check_db_connection(args.db_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
