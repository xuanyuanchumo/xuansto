#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本化文档自动归档器 (VersionedArchiver)
========================================

将报告、日志、快照等文件按类型分类存储到正确的版本化目录。
支持自动分类、索引管理和批量操作。

特性:
- 智能类别识别（报告/日志/快照/知识）
- 自动版本化目录创建
- 归档索引维护
- 批量归档支持
- 冲突处理策略

使用示例:
    >>> from skillscripts.core.versioned_archiver import VersionedArchiver
    >>> archiver = VersionedArchiver()
    >>> target = archiver.archive(Path('report.md'), 'report', 'v3.3.0')
    >>> print(target)
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class VersionedArchiver:
    """
    版本化文档自动归档器

    将各类文档自动分类并归档到对应的版本化目录中，
    保持清晰的文档组织结构和完整的归档历史。

    Attributes:
        CATEGORY_MAP: 文档类别到目录的映射表
    """

    CATEGORY_MAP: Dict[str, str] = {
        'report': 'reports',
        'test_report': 'reports',
        'quality_report': 'reports',
        'path_validation': 'reports',
        'integration_report': 'reports',
        'log': 'logs',
        'execution_log': 'logs',
        'error_log': 'logs',
        'snapshot': 'snapshots',
        'state_snapshot': 'snapshots',
        'config_snapshot': 'snapshots',
        'knowledge': 'knowledge',
        'best_practice': 'knowledge',
        'pattern': 'knowledge',
        'api': 'api',
        'workflow': 'workflow'
    }

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化归档器

        Args:
            logger: 可选的日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)
        self._setup_logging()

        try:
            from skillscripts.core.path_config_center import PathConfigCenter
            self.pcc = PathConfigCenter.instance()
        except Exception as e:
            self.logger.warning(f"无法初始化PathConfigCenter: {e}")
            self.pcc = None

        self.logger.info("VersionedArchiver 初始化完成")

    def _setup_logging(self):
        """配置日志"""
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def archive(
        self,
        source: Path,
        category: str,
        version: Optional[str] = None,
        conflict_strategy: str = 'rename'
    ) -> Path:
        """
        归档文件到版本化目录

        将源文件复制到对应版本的归档目录中，
        并更新归档索引。

        Args:
            source: 源文件路径
            category: 文档类别（如 'report', 'log', 'snapshot' 等）
            version: 目标版本号，默认使用当前版本
            conflict_strategy: 冲突处理策略
                - 'rename': 自动重命名（默认）
                - 'overwrite': 覆盖已存在文件
                - 'skip': 跳过已存在文件

        Returns:
            归档后的目标路径

        Raises:
            FileNotFoundError: 如果源文件不存在
            ValueError: 如果参数无效

        示例:
            >>> archiver = VersionedArchiver()
            >>> target = archiver.archive(
            ...     Path('test_report.md'),
            ...     'test_report',
            ...     'v3.3.0'
            ... )
            >>> print(target)
            PosixPath('.../v3.3.0/reports/test_report.md')
        """
        if not source.exists():
            raise FileNotFoundError(f"源文件不存在: {source}")

        if not source.is_file():
            raise ValueError(f"源路径不是文件: {source}")

        if not category:
            raise ValueError("文档类别不能为空")

        version = version or (self.pcc.get_current_version() if self.pcc else "v0.0.0")

        target_dir_name = self.CATEGORY_MAP.get(category.lower(), 'reports')

        if self.pcc:
            target_dir = self.pcc.ensure_output_directory(target_dir_name, version)
        else:
            target_dir = Path(f"docs/迭代版本/{version}/{target_dir_name}")
            target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / source.name

        if target_file.exists():
            target_file = self._handle_conflict(target_file, conflict_strategy)

        try:
            shutil.copy2(source, target_file)
            self.logger.info(f"文件已归档: {source} -> {target_file}")

            self._update_index(target_file, category, version, source)

            return target_file

        except Exception as e:
            self.logger.error(f"归档失败: {e}")
            raise

    def batch_archive(
        self,
        files: List[Tuple[Path, str]],
        version: Optional[str] = None,
        conflict_strategy: str = 'rename'
    ) -> Dict[str, Path]:
        """
        批量归档多个文件

        Args:
            files: 文件列表，每个元素为 (源路径, 类别) 元组
            version: 目标版本号
            conflict_strategy: 冲突处理策略

        Returns:
            字典：{源文件路径字符串: 目标路径}

        示例:
            >>> files = [
            ...     (Path('report1.md'), 'report'),
            ...     (Path('log.txt'), 'log'),
            ... ]
            >>> results = archiver.batch_archive(files, 'v3.3.0')
        """
        results = {}
        success_count = 0
        error_count = 0

        for source, category in files:
            try:
                target = self.archive(source, category, version, conflict_strategy)
                results[str(source)] = target
                success_count += 1
            except Exception as e:
                self.logger.error(f"批量归档失败 [{source}]: {e}")
                results[str(source)] = None
                error_count += 1

        self.logger.info(
            f"批量归档完成: 成功 {success_count}, 失败 {error_count}, 总计 {len(files)}"
        )

        return results

    def list_archived(
        self,
        category: Optional[str] = None,
        version: Optional[str] = None
    ) -> List[Dict]:
        """
        列出已归档的文件

        Args:
            category: 文档类别过滤
            version: 版本号过滤

        Returns:
            归档文件信息列表

        示例:
            >>> archived = archiver.list_archived('report', 'v3.3.0')
            >>> for item in archived:
            ...     print(item['file'], item['archived_at'])
        """
        if not self.pcc:
            self.logger.warning("PathConfigCenter未初始化")
            return []

        version = version or self.pcc.get_current_version()

        results = []

        categories_to_search = [category] if category else list(set(self.CATEGORY_MAP.values()))

        for cat in categories_to_search:
            try:
                archive_dir = self.pcc.ensure_output_directory(cat, version)
                index_file = archive_dir / ".archive_index.json"

                if index_file.exists():
                    try:
                        index_data = json.loads(index_file.read_text(encoding='utf-8'))
                        results.extend(index_data)
                    except json.JSONDecodeError:
                        self.logger.warning(f"无法解析索引文件: {index_file}")

                else:
                    for file_path in archive_dir.iterdir():
                        if file_path.is_file() and file_path.name != ".archive_index.json":
                            results.append({
                                'file': file_path.name,
                                'category': cat,
                                'archived_at': file_path.stat().st_mtime,
                                'size': file_path.stat().st_size
                            })

            except Exception as e:
                self.logger.warning(f"读取归档目录失败 [{cat}]: {e}")

        results.sort(key=lambda x: x.get('archived_at', 0), reverse=True)

        return results

    def get_archive_stats(self, version: Optional[str] = None) -> Dict:
        """
        获取归档统计信息

        Args:
            version: 版本号，默认使用当前版本

        Returns:
            统计信息字典
        """
        if not self.pcc:
            return {'error': 'PathConfigCenter未初始化'}

        version = version or self.pcc.get_current_version()

        all_archived = self.list_archived(version=version)

        stats = {
            'version': version,
            'total_files': len(all_archived),
            'by_category': {},
            'total_size_bytes': 0,
            'oldest_archive': None,
            'newest_archive': None
        }

        for item in all_archived:
            cat = item.get('category', 'unknown')
            stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1
            stats['total_size_bytes'] += item.get('size', 0)

        if all_archived:
            timestamps = [item.get('archived_at', 0) for item in all_archived]
            stats['oldest_archive'] = min(timestamps)
            stats['newest_archive'] = max(timestamps)

        return stats

    def _handle_conflict(self, target: Path, strategy: str) -> Path:
        """
        处理文件冲突

        Args:
            target: 目标文件路径
            strategy: 冲突处理策略

        Returns:
            最终的目标路径
        """
        if strategy == 'overwrite':
            self.logger.debug(f"覆盖已存在文件: {target}")
            return target

        elif strategy == 'skip':
            self.logger.info(f"跳过已存在文件: {target}")
            raise FileExistsError(f"文件已存在且选择跳过: {target}")

        elif strategy == 'rename':
            counter = 1
            stem = target.stem
            suffix = target.suffix
            parent = target.parent

            while True:
                new_name = f"{stem}_{counter}{suffix}"
                new_target = parent / new_name

                if not new_target.exists():
                    self.logger.debug(f"重命名以避免冲突: {target} -> {new_target}")
                    return new_target

                counter += 1

        else:
            raise ValueError(f"未知的冲突处理策略: {strategy}")

    def _update_index(
        self,
        file_path: Path,
        category: str,
        version: str,
        source: Path
    ) -> None:
        """
        更新归档索引

        Args:
            file_path: 归档后的文件路径
            category: 文档类别
            version: 版本号
            source: 源文件路径
        """
        index_file = file_path.parent / ".archive_index.json"

        index = []
        if index_file.exists():
            try:
                index = json.loads(index_file.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                self.logger.warning(f"解析现有索引失败，将创建新索引")

        index.append({
            'file': file_path.name,
            'category': category,
            'version': version,
            'archived_at': datetime.now().isoformat(),
            'size': file_path.stat().st_size,
            'source': str(source),
            'source_size': source.stat().st_size if source.exists() else 0
        })

        try:
            index_file.write_text(
                json.dumps(index, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
            self.logger.debug(f"已更新归档索引: {index_file}")
        except Exception as e:
            self.logger.error(f"更新索引失败: {e}")


def main():
    """测试版本化归档功能"""
    import tempfile
    from datetime import datetime

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=" * 80)
    print("📦 版本化自动归档器测试")
    print("=" * 80)

    archiver = VersionedArchiver()

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        test_files = [
            ('test_report.md', 'report', '# 测试报告'),
            ('quality_report.md', 'quality_report', '# 质量报告'),
            ('execution.log', 'log', '执行日志内容'),
            ('snapshot_state.json', 'snapshot', '{"state": "test"}'),
        ]

        print("\n📂 创建测试文件:")
        for filename, category, content in test_files:
            file_path = temp_path / filename
            file_path.write_text(content, encoding='utf-8')
            print(f"  ✅ 创建: {filename} (类别: {category})")

        print("\n📦 执行归档:")
        archived_files = []
        for filename, category, _ in test_files:
            source = temp_path / filename
            try:
                target = archiver.archive(source, category, 'v3.3.0')
                archived_files.append((str(source), target))
                print(f"  ✅ 归档: {filename} -> {target.name}")
            except Exception as e:
                print(f"  ❌ 失败: {filename} - {e}")

        print("\n📊 归档统计:")
        stats = archiver.get_archive_stats('v3.3.0')
        for key, value in stats.items():
            if key != 'by_category':
                print(f"  {key}: {value}")
            else:
                print(f"  {key}:")
                for cat, count in value.items():
                    print(f"    - {cat}: {count} 个文件")

        print("\n📋 已归档文件列表:")
        archived_list = archiver.list_archived(version='v3.3.0')
        for item in archived_list[:10]:
            print(f"  📄 {item['file']} ({item['category']}) - {item['size']} bytes")

    print("\n✅ 测试完成!")


if __name__ == "__main__":
    main()
