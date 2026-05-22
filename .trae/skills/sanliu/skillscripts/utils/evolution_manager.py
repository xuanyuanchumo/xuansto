#!/usr/bin/env python3
"""
演化管理器 - 管理技能演化过程
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class EvolutionManager:
    """演化管理器"""
    
    def __init__(self, project_root: str = './'):
        self.project_root = Path(project_root)
        self.history_file = self.project_root / 'data' / 'evolution_history.json'
        self.history = self._load_history()
    
    def _load_history(self) -> Dict[str, Any]:
        """加载演化历史"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'evolutions': []}
    
    def get_status(self) -> Dict[str, Any]:
        """获取演化状态"""
        return {
            'total_evolutions': len(self.history['evolutions']),
            'last_evolution': self.history['evolutions'][-1] if self.history['evolutions'] else None,
            'status': 'active'
        }
    
    def trigger(self, evolution_type: str, reason: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """触发演化"""
        evolution_id = f"EVOL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        evolution = {
            'id': evolution_id,
            'type': evolution_type,
            'reason': reason,
            'params': params or {},
            'status': 'triggered',
            'triggered_at': datetime.now().isoformat()
        }
        self.history['evolutions'].append(evolution)
        self._save_history()
        return evolution
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取演化历史"""
        return self.history['evolutions'][-limit:]
    
    def pause(self) -> Dict[str, Any]:
        """暂停演化"""
        return {'success': True, 'status': 'paused'}
    
    def resume(self) -> Dict[str, Any]:
        """恢复演化"""
        return {'success': True, 'status': 'resumed'}
    
    def cancel(self) -> Dict[str, Any]:
        """取消演化"""
        return {'success': True, 'status': 'cancelled'}
    
    def _save_history(self):
        """保存历史"""
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description='演化管理器')
    parser.add_argument('command', choices=['status', 'trigger', 'history', 'pause', 'resume', 'cancel'],
                       help='命令')
    parser.add_argument('--type', type=str, help='演化类型')
    parser.add_argument('--reason', type=str, help='演化原因')
    parser.add_argument('--params', type=str, help='参数（JSON格式）')
    parser.add_argument('--limit', type=int, default=10, help='历史记录数量')
    
    args = parser.parse_args()
    
    manager = EvolutionManager()
    
    if args.command == 'status':
        result = manager.get_status()
    elif args.command == 'trigger':
        params = json.loads(args.params) if args.params else None
        result = manager.trigger(args.type, args.reason, params)
    elif args.command == 'history':
        result = manager.get_history(args.limit)
    elif args.command == 'pause':
        result = manager.pause()
    elif args.command == 'resume':
        result = manager.resume()
    elif args.command == 'cancel':
        result = manager.cancel()
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
