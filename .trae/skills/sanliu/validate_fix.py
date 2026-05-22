#!/usr/bin/env python3
"""
验证路径修复效果
"""
import re
import json
from pathlib import Path
from typing import Dict, List, Any

def extract_script_paths(content: str) -> List[str]:
    """提取文档中的脚本路径"""
    pattern = r'python\s+([^\s]+\.py)'
    matches = re.findall(pattern, content)
    return list(set(matches))

def validate_path(path: str, skill_root: Path) -> Dict[str, Any]:
    """验证单个路径"""
    full_path = skill_root / path
    
    return {
        'path': path,
        'full_path': str(full_path),
        'exists': full_path.exists(),
        'is_valid': full_path.exists()
    }

def validate_document(doc_path: Path, skill_root: Path) -> Dict[str, Any]:
    """验证单个文档"""
    with open(doc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    paths = extract_script_paths(content)
    results = []
    valid_count = 0
    invalid_count = 0
    
    for path in paths:
        result = validate_path(path, skill_root)
        results.append(result)
        if result['is_valid']:
            valid_count += 1
        else:
            invalid_count += 1
    
    return {
        'document': doc_path.name,
        'total_paths': len(paths),
        'valid_paths': valid_count,
        'invalid_paths': invalid_count,
        'health_score': (valid_count / len(paths) * 100) if paths else 100,
        'details': results
    }

def main():
    """主函数"""
    skill_root = Path(__file__).parent
    subskills_dir = skill_root / 'subskills'
    
    documents = [
        'self_iteration.md',
        'continuous_evolution.md',
        'knowledge_base.md',
        'baihehua_liushuixian.md',
        'daima_chonggou.md',
        'skill_path_management.md',
        'skill_script_coordination.md'
    ]
    
    print("=" * 80)
    print("路径修复效果验证报告")
    print("=" * 80)
    print()
    
    total_paths = 0
    total_valid = 0
    total_invalid = 0
    
    for doc_name in documents:
        doc_path = subskills_dir / doc_name
        if doc_path.exists():
            result = validate_document(doc_path, skill_root)
            
            total_paths += result['total_paths']
            total_valid += result['valid_paths']
            total_invalid += result['invalid_paths']
            
            print(f"文档: {doc_name}")
            print(f"  总路径数: {result['total_paths']}")
            print(f"  有效路径: {result['valid_paths']}")
            print(f"  无效路径: {result['invalid_paths']}")
            print(f"  健康分数: {result['health_score']:.1f}%")
            
            if result['invalid_paths'] > 0:
                print(f"  无效路径详情:")
                for detail in result['details']:
                    if not detail['is_valid']:
                        print(f"    - {detail['path']}")
            print()
    
    print("=" * 80)
    print("总体统计")
    print("=" * 80)
    print(f"扫描文档数: {len(documents)}")
    print(f"总路径数: {total_paths}")
    print(f"有效路径: {total_valid}")
    print(f"无效路径: {total_invalid}")
    
    overall_health = (total_valid / total_paths * 100) if total_paths > 0 else 100
    print(f"总体健康分数: {overall_health:.1f}%")
    print()
    
    if overall_health >= 95:
        print("✓ 路径健康分数达标 (≥95%)")
    else:
        print(f"✗ 路径健康分数未达标，需要继续修复")
    
    print("=" * 80)
    
    return {
        'total_documents': len(documents),
        'total_paths': total_paths,
        'valid_paths': total_valid,
        'invalid_paths': total_invalid,
        'health_score': overall_health,
        'passed': overall_health >= 95
    }

if __name__ == '__main__':
    result = main()
    
    output_file = Path(__file__).parent / 'reports' / 'path_fix_validation_report.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n报告已保存到: {output_file}")
