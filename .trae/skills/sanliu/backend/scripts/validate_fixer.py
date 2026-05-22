#!/usr/bin/env python3
"""
修复成功率验证脚本
验证智能修复器的修复成功率 >= 95%
"""

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from scripts.auto_fixer import AutoFixer, SecurityPatternDetector, CodeSmellDetector
from scripts.rollback_manager import RollbackManager


def validate_success_rate():
    temp_dir = tempfile.mkdtemp()
    backup_dir = os.path.join(temp_dir, 'backups')
    
    try:
        fixer = AutoFixer(backup_dir=backup_dir)
        
        test_cases = [
            ('password = "secret123"\n', 'hardcoded_password'),
            ('api_key = "key123"\n', 'hardcoded_api_key'),
            ('token = "token123"\n', 'hardcoded_token'),
            ('passwd = "pass123"\n', 'hardcoded_password'),
            ('secret = "mysecret"\n', 'hardcoded_secret'),
            ('import unused_module\n\ndef test():\n    pass\n', 'unused_import'),
        ]
        
        total_issues = 0
        fixed_issues = 0
        results = []
        
        for i, (content, expected_type) in enumerate(test_cases):
            test_file = os.path.join(temp_dir, f'test_{i}.py')
            with open(test_file, 'w') as f:
                f.write(content)
            
            issues = fixer.scan_file(test_file)
            total_issues += len(issues)
            
            for issue in issues:
                result = fixer.apply_fix(test_file, issue)
                if result.success:
                    fixed_issues += 1
                    results.append((issue.issue_type, True, None))
                else:
                    results.append((issue.issue_type, False, result.error_message))
        
        success_rate = (fixed_issues / total_issues * 100) if total_issues > 0 else 0
        
        print('=' * 60)
        print('智能修复成功率验证报告')
        print('=' * 60)
        print(f'\n总问题数: {total_issues}')
        print(f'成功修复: {fixed_issues}')
        print(f'修复失败: {total_issues - fixed_issues}')
        print(f'修复成功率: {success_rate:.2f}%')
        print(f'目标成功率: 95%')
        
        if success_rate >= 95:
            print('\n状态: ✅ 达标 - 修复成功率 >= 95%')
        else:
            print('\n状态: ❌ 未达标 - 修复成功率 < 95%')
        
        print('\n修复详情:')
        for issue_type, success, error in results:
            status = '✅' if success else '❌'
            print(f'  {status} {issue_type}')
            if error:
                print(f'      错误: {error}')
        
        return success_rate >= 95
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def validate_rollback():
    temp_dir = tempfile.mkdtemp()
    backup_dir = os.path.join(temp_dir, 'backups')
    
    try:
        manager = RollbackManager(backup_base_dir=backup_dir)
        
        test_file = os.path.join(temp_dir, 'test.py')
        with open(test_file, 'w') as f:
            f.write('original content\n')
        
        record = manager.create_backup(test_file)
        
        with open(test_file, 'w') as f:
            f.write('modified content\n')
        
        result = manager.rollback(record.backup_id)
        
        print('\n' + '=' * 60)
        print('回滚机制验证报告')
        print('=' * 60)
        
        if result.success and result.verification_passed:
            print('\n状态: ✅ 回滚机制正常工作')
            
            with open(test_file, 'r') as f:
                content = f.read()
            
            if content == 'original content\n':
                print('验证: ✅ 文件内容正确恢复')
            else:
                print('验证: ❌ 文件内容恢复不正确')
        else:
            print('\n状态: ❌ 回滚机制异常')
        
        return result.success
    
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def main():
    print('\n' + '=' * 60)
    print('三省六部技能 - 智能修复执行机制验证')
    print('=' * 60)
    
    fix_success = validate_success_rate()
    rollback_success = validate_rollback()
    
    print('\n' + '=' * 60)
    print('最终验证结果')
    print('=' * 60)
    
    if fix_success and rollback_success:
        print('\n✅ 所有验证通过 - 智能修复执行机制可用')
        print('   - 修复成功率 >= 95%')
        print('   - 回滚机制正常工作')
        return 0
    else:
        print('\n❌ 验证失败')
        if not fix_success:
            print('   - 修复成功率未达标')
        if not rollback_success:
            print('   - 回滚机制异常')
        return 1


if __name__ == '__main__':
    exit(main())
