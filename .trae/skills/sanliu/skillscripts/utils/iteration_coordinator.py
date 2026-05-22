#!/usr/bin/env python3
"""
迭代协调器 - 协调多个技能的迭代过程
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class IterationCoordinator:
    """迭代协调器"""
    
    def __init__(self, project_root: str = './'):
        self.project_root = Path(project_root)
        self.state_file = self.project_root / 'data' / 'iteration_state.json'
        self.state = self._load_state()
    
    def _load_state(self) -> Dict[str, Any]:
        """加载状态"""
        if self.state_file.exists():
            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'status': 'idle', 'iterations': []}
    
    def start(self, skills: List[str], mode: str = 'sequential') -> Dict[str, Any]:
        """启动迭代协调"""
        iteration_id = f"COORD-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self.state = {
            'iteration_id': iteration_id,
            'status': 'running',
            'mode': mode,
            'skills': skills,
            'started_at': datetime.now().isoformat()
        }
        self._save_state()
        return self.state
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        return self.state
    
    def pause(self) -> Dict[str, Any]:
        """暂停"""
        self.state['status'] = 'paused'
        self._save_state()
        return self.state
    
    def resume(self) -> Dict[str, Any]:
        """恢复"""
        self.state['status'] = 'running'
        self._save_state()
        return self.state
    
    def _save_state(self):
        """保存状态"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(self.state, f, indent=2, ensure_ascii=False)

def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description='迭代协调器')
    parser.add_argument('command', choices=['start', 'status', 'pause', 'resume'],
                       help='命令')
    parser.add_argument('--skills', type=str, help='技能列表（JSON格式）')
    parser.add_argument('--mode', type=str, default='sequential', help='协调模式')
    
    args = parser.parse_args()
    
    coordinator = IterationCoordinator()
    
    if args.command == 'start':
        skills = json.loads(args.skills) if args.skills else []
        result = coordinator.start(skills, args.mode)
    elif args.command == 'status':
        result = coordinator.get_status()
    elif args.command == 'pause':
        result = coordinator.pause()
    elif args.command == 'resume':
        result = coordinator.resume()
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
