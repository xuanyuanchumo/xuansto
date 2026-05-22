#!/usr/bin/env python3
"""
依赖检查工具
"""
import json
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List

def check_dependencies(requirements_path: str = './backend/requirements.txt') -> Dict[str, Any]:
    """检查依赖"""
    req_file = Path(requirements_path)
    
    result = {
        'requirements_path': str(req_file),
        'exists': req_file.exists(),
        'dependencies': [],
        'missing': [],
        'installed': []
    }
    
    if not req_file.exists():
        result['error'] = 'requirements.txt 不存在'
        return result
    
    with open(req_file, 'r', encoding='utf-8') as f:
        dependencies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    result['dependencies'] = dependencies
    
    for dep in dependencies:
        package_name = dep.split('==')[0].split('>=')[0].split('<=')[0].split('[')[0]
        try:
            __import__(package_name.replace('-', '_'))
            result['installed'].append(dep)
        except ImportError:
            result['missing'].append(dep)
    
    return result

def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description='依赖检查')
    parser.add_argument('--requirements', type=str, default='./backend/requirements.txt',
                       help='requirements.txt 路径')
    
    args = parser.parse_args()
    
    result = check_dependencies(args.requirements)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
