#!/usr/bin/env python3
"""
知识管理器 - 管理知识库
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class KnowledgeManager:
    """知识管理器"""
    
    def __init__(self, knowledge_path: str = './data/knowledge'):
        self.knowledge_path = Path(knowledge_path)
        self.knowledge_file = self.knowledge_path / 'knowledge_base.json'
        self.knowledge = self._load_knowledge()
    
    def _load_knowledge(self) -> Dict[str, Any]:
        """加载知识库"""
        if self.knowledge_file.exists():
            with open(self.knowledge_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'entries': {}}
    
    def add(self, entry_type: str, title: str, content: Dict[str, Any],
            tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """添加知识条目"""
        entry_id = f"KB-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        entry = {
            'id': entry_id,
            'type': entry_type,
            'title': title,
            'content': content,
            'tags': tags or [],
            'created_at': datetime.now().isoformat()
        }
        self.knowledge['entries'][entry_id] = entry
        self._save_knowledge()
        return entry
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索知识"""
        results = []
        for entry in self.knowledge['entries'].values():
            if query.lower() in entry['title'].lower() or \
               query.lower() in entry.get('content', {}).get('description', '').lower():
                results.append(entry)
        return results[:limit]
    
    def get(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """获取知识条目"""
        return self.knowledge['entries'].get(entry_id)
    
    def update(self, entry_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新知识条目"""
        if entry_id in self.knowledge['entries']:
            self.knowledge['entries'][entry_id].update(updates)
            self.knowledge['entries'][entry_id]['updated_at'] = datetime.now().isoformat()
            self._save_knowledge()
            return self.knowledge['entries'][entry_id]
        return {'error': '条目不存在'}
    
    def delete(self, entry_id: str) -> Dict[str, Any]:
        """删除知识条目"""
        if entry_id in self.knowledge['entries']:
            del self.knowledge['entries'][entry_id]
            self._save_knowledge()
            return {'success': True, 'entry_id': entry_id}
        return {'success': False, 'error': '条目不存在'}
    
    def backup(self, backup_path: str) -> Dict[str, Any]:
        """备份知识库"""
        backup_file = Path(backup_path)
        backup_file.parent.mkdir(parents=True, exist_ok=True)
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, indent=2, ensure_ascii=False)
        return {'success': True, 'backup_path': str(backup_file)}
    
    def restore(self, backup_path: str) -> Dict[str, Any]:
        """恢复知识库"""
        backup_file = Path(backup_path)
        if backup_file.exists():
            with open(backup_file, 'r', encoding='utf-8') as f:
                self.knowledge = json.load(f)
            self._save_knowledge()
            return {'success': True}
        return {'success': False, 'error': '备份文件不存在'}
    
    def _save_knowledge(self):
        """保存知识库"""
        self.knowledge_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.knowledge_file, 'w', encoding='utf-8') as f:
            json.dump(self.knowledge, f, indent=2, ensure_ascii=False)

def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description='知识管理器')
    parser.add_argument('command', choices=['add', 'search', 'get', 'update', 'delete', 'backup', 'restore'],
                       help='命令')
    parser.add_argument('--type', type=str, help='条目类型')
    parser.add_argument('--title', type=str, help='标题')
    parser.add_argument('--content', type=str, help='内容（JSON格式）')
    parser.add_argument('--tags', type=str, help='标签（逗号分隔）')
    parser.add_argument('--query', type=str, help='搜索查询')
    parser.add_argument('--id', type=str, help='条目ID')
    parser.add_argument('--limit', type=int, default=10, help='结果数量限制')
    parser.add_argument('--path', type=str, help='路径')
    
    args = parser.parse_args()
    
    manager = KnowledgeManager()
    
    if args.command == 'add':
        content = json.loads(args.content) if args.content else {}
        tags = args.tags.split(',') if args.tags else []
        result = manager.add(args.type, args.title, content, tags)
    elif args.command == 'search':
        result = manager.search(args.query, args.limit)
    elif args.command == 'get':
        result = manager.get(args.id)
    elif args.command == 'update':
        updates = json.loads(args.content) if args.content else {}
        result = manager.update(args.id, updates)
    elif args.command == 'delete':
        result = manager.delete(args.id)
    elif args.command == 'backup':
        result = manager.backup(args.path)
    elif args.command == 'restore':
        result = manager.restore(args.path)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
