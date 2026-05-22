#!/usr/bin/env python3
"""
技能注册器 - 技能注册与发现
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

class SkillRegistry:
    """技能注册器"""
    
    def __init__(self, registry_path: str = './data/skill_registry.json'):
        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()
    
    def _load_registry(self) -> Dict[str, Any]:
        """加载注册表"""
        if self.registry_path.exists():
            with open(self.registry_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'skills': {}}
    
    def register(self, skill_id: str, skill_path: str, interfaces: List[Dict]) -> Dict[str, Any]:
        """注册新技能"""
        self.registry['skills'][skill_id] = {
            'id': skill_id,
            'path': skill_path,
            'interfaces': interfaces,
            'registered_at': str(Path.cwd()),
            'status': 'active'
        }
        self._save_registry()
        return {'success': True, 'skill_id': skill_id}
    
    def unregister(self, skill_id: str) -> Dict[str, Any]:
        """注销技能"""
        if skill_id in self.registry['skills']:
            del self.registry['skills'][skill_id]
            self._save_registry()
            return {'success': True, 'skill_id': skill_id}
        return {'success': False, 'error': '技能不存在'}
    
    def list_skills(self) -> List[Dict[str, Any]]:
        """列出所有技能"""
        return list(self.registry['skills'].values())
    
    def get_skill_info(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """获取技能详情"""
        return self.registry['skills'].get(skill_id)
    
    def health_check(self, skill_id: str) -> Dict[str, Any]:
        """健康检查"""
        skill_info = self.get_skill_info(skill_id)
        if not skill_info:
            return {'healthy': False, 'error': '技能不存在'}
        
        skill_path = Path(skill_info['path'])
        return {
            'healthy': skill_path.exists(),
            'skill_id': skill_id,
            'path_exists': skill_path.exists()
        }
    
    def _save_registry(self):
        """保存注册表"""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)

def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description='技能注册器')
    parser.add_argument('command', choices=['register', 'unregister', 'list', 'info', 'health', 'stats'],
                       help='命令')
    parser.add_argument('--skill-id', type=str, help='技能ID')
    parser.add_argument('--skill-path', type=str, help='技能路径')
    parser.add_argument('--interfaces', type=str, help='接口列表（JSON格式）')
    
    args = parser.parse_args()
    
    registry = SkillRegistry()
    
    if args.command == 'register':
        interfaces = json.loads(args.interfaces) if args.interfaces else []
        result = registry.register(args.skill_id, args.skill_path, interfaces)
    elif args.command == 'unregister':
        result = registry.unregister(args.skill_id)
    elif args.command == 'list':
        result = registry.list_skills()
    elif args.command == 'info':
        result = registry.get_skill_info(args.skill_id)
    elif args.command == 'health':
        result = registry.health_check(args.skill_id)
    elif args.command == 'stats':
        result = {'total_skills': len(registry.registry['skills'])}
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
