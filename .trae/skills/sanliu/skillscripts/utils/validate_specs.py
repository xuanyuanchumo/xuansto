#!/usr/bin/env python3
"""
验证规范工具 - 验证技能规范
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

def validate_specs(spec_path: str) -> Dict[str, Any]:
    """验证规范文件"""
    spec_file = Path(spec_path)
    
    if not spec_file.exists():
        return {
            'valid': False,
            'error': '规范文件不存在',
            'path': spec_path
        }
    
    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            spec = json.load(f)
    except json.JSONDecodeError as e:
        return {
            'valid': False,
            'error': f'JSON格式错误: {str(e)}',
            'path': spec_path
        }
    
    errors = []
    warnings = []
    
    if 'name' not in spec:
        errors.append('缺少name字段')
    
    if 'version' not in spec:
        warnings.append('缺少version字段')
    
    if 'description' not in spec:
        warnings.append('缺少description字段')
    
    return {
        'valid': len(errors) == 0,
        'path': spec_path,
        'errors': errors,
        'warnings': warnings,
        'spec': spec
    }

def main():
    """命令行入口"""
    import argparse
    parser = argparse.ArgumentParser(description='验证规范工具')
    parser.add_argument('spec_path', type=str, help='规范文件路径')
    parser.add_argument('--format', choices=['json', 'yaml'], default='json', help='输出格式')
    
    args = parser.parse_args()
    
    result = validate_specs(args.spec_path)
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == '__main__':
    main()
