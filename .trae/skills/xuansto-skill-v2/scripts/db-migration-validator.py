#!/usr/bin/env python3
"""
数据库迁移验证脚本
功能：验证迁移脚本的正确性
"""

import argparse
import sys
import json
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='数据库迁移验证脚本 - 验证迁移脚本的正确性'
    )
    parser.add_argument(
        '--migrations-dir',
        type=str,
        default='migrations',
        help='迁移脚本目录（默认：migrations）'
    )
    parser.add_argument(
        '--db-type',
        type=str,
        choices=['postgresql', 'mysql', 'sqlite', 'auto'],
        default='auto',
        help='数据库类型（默认：auto自动检测）'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='migration-report',
        help='输出目录名称（默认：migration-report）'
    )
    parser.add_argument(
        '--check-order',
        action='store_true',
        help='检查迁移文件顺序是否正确'
    )
    return parser.parse_args()


class MigrationValidator:
    """迁移验证器类"""
    
    def __init__(self, migrations_dir: str, db_type: str):
        """
        初始化验证器
        
        参数:
            migrations_dir: 迁移脚本目录
            db_type: 数据库类型
        """
        self.migrations_dir = Path(migrations_dir)
        self.db_type = db_type
        self.errors = []
        self.warnings = []
        self.info = []
    
    def validate_all(self) -> Dict[str, Any]:
        """
        执行所有验证
        
        返回:
            验证结果字典
        """
        results = {
            'timestamp': datetime.now().isoformat(),
            'migrations_dir': str(self.migrations_dir),
            'db_type': self.db_type,
            'valid': True,
            'errors': [],
            'warnings': [],
            'info': [],
            'migrations': []
        }
        
        if not self.migrations_dir.exists():
            results['errors'].append(f"迁移目录不存在: {self.migrations_dir}")
            results['valid'] = False
            return results
        
        migrations = self._find_migration_files()
        
        if not migrations:
            results['warnings'].append("未找到迁移文件")
            return results
        
        for migration in migrations:
            migration_result = self._validate_single_migration(migration)
            results['migrations'].append(migration_result)
            
            if not migration_result['valid']:
                results['valid'] = False
        
        results['errors'].extend(self.errors)
        results['warnings'].extend(self.warnings)
        results['info'].extend(self.info)
        
        return results
    
    def _find_migration_files(self) -> List[Path]:
        """
        查找所有迁移文件
        
        返回:
            迁移文件路径列表
        """
        patterns = ['*.sql', '*.py']
        migrations = []
        
        for pattern in patterns:
            migrations.extend(self.migrations_dir.glob(f'**/{pattern}'))
        
        return sorted(migrations)
    
    def _validate_single_migration(self, migration_path: Path) -> Dict[str, Any]:
        """
        验证单个迁移文件
        
        参数:
            migration_path: 迁移文件路径
        
        返回:
            验证结果字典
        """
        result = {
            'file': str(migration_path),
            'name': migration_path.name,
            'valid': True,
            'errors': [],
            'warnings': [],
            'checks': {}
        }
        
        if migration_path.suffix == '.sql':
            result['checks'] = self._validate_sql_migration(migration_path)
        elif migration_path.suffix == '.py':
            result['checks'] = self._validate_python_migration(migration_path)
        
        if result['checks'].get('errors'):
            result['errors'].extend(result['checks']['errors'])
            result['valid'] = False
        
        if result['checks'].get('warnings'):
            result['warnings'].extend(result['checks']['warnings'])
        
        return result
    
    def _validate_sql_migration(self, migration_path: Path) -> Dict[str, Any]:
        """
        验证SQL迁移文件
        
        参数:
            migration_path: 迁移文件路径
        
        返回:
            验证结果字典
        """
        checks = {
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        try:
            content = migration_path.read_text(encoding='utf-8')
        except Exception as e:
            checks['errors'].append(f"无法读取文件: {e}")
            return checks
        
        checks['details']['file_size'] = len(content)
        checks['details']['line_count'] = len(content.splitlines())
        
        if not content.strip():
            checks['errors'].append("文件为空")
            return checks
        
        name_check = self._check_migration_naming(migration_path.name)
        if not name_check['valid']:
            checks['warnings'].extend(name_check['issues'])
        checks['details']['naming'] = name_check
        
        syntax_check = self._check_sql_syntax(content)
        if not syntax_check['valid']:
            checks['errors'].extend(syntax_check['issues'])
        checks['details']['syntax'] = syntax_check
        
        transaction_check = self._check_transaction_wrapping(content)
        checks['details']['transaction'] = transaction_check
        if not transaction_check['has_transaction']:
            checks['warnings'].append("建议使用事务包装迁移语句")
        
        rollback_check = self._check_rollback_support(content, migration_path)
        checks['details']['rollback'] = rollback_check
        if not rollback_check['has_rollback']:
            checks['warnings'].append("建议提供回滚脚本")
        
        dangerous_patterns = self._check_dangerous_operations(content)
        if dangerous_patterns:
            checks['warnings'].extend([f"检测到危险操作: {p}" for p in dangerous_patterns])
        checks['details']['dangerous_operations'] = dangerous_patterns
        
        return checks
    
    def _check_migration_naming(self, filename: str) -> Dict[str, Any]:
        """
        检查迁移文件命名规范
        
        参数:
            filename: 文件名
        
        返回:
            检查结果字典
        """
        result = {
            'valid': True,
            'issues': [],
            'pattern_matched': None
        }
        
        patterns = [
            r'^\d{14}_[a-z_]+\.sql$',
            r'^V\d+__[a-z_]+\.sql$',
            r'^\d{4}_\d{2}_\d{2}_\d{6}_[a-z_]+\.sql$',
        ]
        
        for pattern in patterns:
            if re.match(pattern, filename):
                result['pattern_matched'] = pattern
                return result
        
        result['valid'] = False
        result['issues'].append(f"文件命名不符合规范: {filename}")
        
        return result
    
    def _check_sql_syntax(self, content: str) -> Dict[str, Any]:
        """
        检查SQL语法
        
        参数:
            content: SQL内容
        
        返回:
            检查结果字典
        """
        result = {
            'valid': True,
            'issues': []
        }
        
        open_parens = content.count('(')
        close_parens = content.count(')')
        
        if open_parens != close_parens:
            result['valid'] = False
            result['issues'].append(f"括号不匹配: 开括号 {open_parens} 个, 闭括号 {close_parens} 个")
        
        statements = re.split(r';\s*', content)
        for i, stmt in enumerate(statements):
            stmt = stmt.strip()
            if not stmt:
                continue
            
            keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'TRUNCATE']
            has_keyword = any(stmt.upper().startswith(kw) for kw in keywords)
            
            if not has_keyword and stmt:
                result['valid'] = False
                result['issues'].append(f"语句 {i+1} 可能缺少关键字")
        
        return result
    
    def _check_transaction_wrapping(self, content: str) -> Dict[str, Any]:
        """
        检查事务包装
        
        参数:
            content: SQL内容
        
        返回:
            检查结果字典
        """
        has_begin = bool(re.search(r'\bBEGIN\b', content, re.IGNORECASE))
        has_commit = bool(re.search(r'\bCOMMIT\b', content, re.IGNORECASE))
        
        return {
            'has_transaction': has_begin and has_commit,
            'has_begin': has_begin,
            'has_commit': has_commit
        }
    
    def _check_rollback_support(self, content: str, migration_path: Path) -> Dict[str, Any]:
        """
        检查回滚支持
        
        参数:
            content: SQL内容
            migration_path: 迁移文件路径
        
        返回:
            检查结果字典
        """
        rollback_patterns = [
            r'\bROLLBACK\b',
            r'--\s*@rollback',
            r'--\s*DOWN'
        ]
        
        has_rollback = any(re.search(p, content, re.IGNORECASE) for p in rollback_patterns)
        
        rollback_file = migration_path.parent / f"{migration_path.stem}_rollback.sql"
        has_rollback_file = rollback_file.exists()
        
        return {
            'has_rollback': has_rollback or has_rollback_file,
            'inline_rollback': has_rollback,
            'separate_file': has_rollback_file
        }
    
    def _check_dangerous_operations(self, content: str) -> List[str]:
        """
        检查危险操作
        
        参数:
            content: SQL内容
        
        返回:
            危险操作列表
        """
        dangerous = []
        
        patterns = [
            (r'\bDROP\s+TABLE\b', 'DROP TABLE'),
            (r'\bDROP\s+DATABASE\b', 'DROP DATABASE'),
            (r'\bTRUNCATE\s+TABLE\b', 'TRUNCATE TABLE'),
            (r'\bDELETE\s+FROM\b(?!.+WHERE)', 'DELETE without WHERE'),
            (r'\bUPDATE\b(?!.+WHERE)', 'UPDATE without WHERE'),
        ]
        
        for pattern, name in patterns:
            if re.search(pattern, content, re.IGNORECASE):
                dangerous.append(name)
        
        return dangerous
    
    def _validate_python_migration(self, migration_path: Path) -> Dict[str, Any]:
        """
        验证Python迁移文件
        
        参数:
            migration_path: 迁移文件路径
        
        返回:
            验证结果字典
        """
        checks = {
            'errors': [],
            'warnings': [],
            'details': {}
        }
        
        try:
            content = migration_path.read_text(encoding='utf-8')
        except Exception as e:
            checks['errors'].append(f"无法读取文件: {e}")
            return checks
        
        checks['details']['file_size'] = len(content)
        
        has_upgrade = 'def upgrade' in content or 'def up' in content
        has_downgrade = 'def downgrade' in content or 'def down' in content
        
        if not has_upgrade:
            checks['errors'].append("缺少upgrade函数")
        
        if not has_downgrade:
            checks['warnings'].append("建议添加downgrade函数以支持回滚")
        
        checks['details']['has_upgrade'] = has_upgrade
        checks['details']['has_downgrade'] = has_downgrade
        
        return checks
    
    def check_migration_order(self) -> Dict[str, Any]:
        """
        检查迁移文件顺序
        
        返回:
            检查结果字典
        """
        result = {
            'valid': True,
            'issues': [],
            'order': []
        }
        
        migrations = self._find_migration_files()
        
        for i, migration in enumerate(migrations):
            result['order'].append(migration.name)
        
        for i in range(1, len(migrations)):
            prev_name = migrations[i-1].name
            curr_name = migrations[i].name
            
            prev_nums = re.findall(r'\d+', prev_name)
            curr_nums = re.findall(r'\d+', curr_name)
            
            if prev_nums and curr_nums:
                if int(prev_nums[0]) >= int(curr_nums[0]):
                    result['valid'] = False
                    result['issues'].append(
                        f"迁移顺序错误: {prev_name} 应在 {curr_name} 之后"
                    )
        
        return result


def generate_report(output_dir: str, results: Dict[str, Any]):
    """
    生成验证报告
    
    参数:
        output_dir: 输出目录
        results: 验证结果
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    json_file = output_path / f'migration-validation-{timestamp}.json'
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n报告已保存: {json_file}")


def print_summary(results: Dict[str, Any]):
    """打印验证摘要"""
    print(f"\n{'='*60}")
    print("数据库迁移验证结果")
    print(f"{'='*60}")
    print(f"迁移目录: {results['migrations_dir']}")
    print(f"数据库类型: {results['db_type']}")
    print(f"验证状态: {'✅ 通过' if results['valid'] else '❌ 失败'}")
    print(f"迁移文件数: {len(results['migrations'])}")
    
    if results['errors']:
        print(f"\n错误 ({len(results['errors'])}):")
        for err in results['errors']:
            print(f"  ❌ {err}")
    
    if results['warnings']:
        print(f"\n警告 ({len(results['warnings'])}):")
        for warn in results['warnings']:
            print(f"  ⚠️ {warn}")
    
    print(f"{'='*60}")


def main():
    """主函数"""
    args = parse_args()
    
    validator = MigrationValidator(args.migrations_dir, args.db_type)
    
    results = validator.validate_all()
    
    if args.check_order:
        order_result = validator.check_migration_order()
        results['order_check'] = order_result
        if not order_result['valid']:
            results['valid'] = False
            results['errors'].extend(order_result['issues'])
    
    generate_report(args.output, results)
    print_summary(results)
    
    if not results['valid']:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
