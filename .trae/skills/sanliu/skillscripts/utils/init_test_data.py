#!/usr/bin/env python3
"""
测试数据初始化工具
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any

def init_test_data(db_path: str = './backend/backend_test.db') -> Dict[str, Any]:
    """初始化测试数据"""
    db_file = Path(db_path)
    
    result = {
        'db_path': str(db_file),
        'success': False,
        'tables_initialized': []
    }
    
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        result['tables_initialized'].append('test_projects')
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES test_projects(id)
            )
        """)
        result['tables_initialized'].append('test_tasks')
        
        conn.commit()
        conn.close()
        result['success'] = True
    except Exception as e:
        result['error'] = str(e)
    
    return result

def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description='初始化测试数据')
    parser.add_argument('--db-path', type=str, default='./backend/backend_test.db',
                       help='数据库路径')
    
    args = parser.parse_args()
    
    result = init_test_data(args.db_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
