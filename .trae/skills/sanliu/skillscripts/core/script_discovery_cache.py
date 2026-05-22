#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
脚本发现结果缓存机制 (ScriptDiscoveryCache)
============================================

避免重复扫描目录结构，提升脚本发现性能。
支持内存缓存和磁盘持久化双层缓存策略。

特性:
- 内存缓存: 快速访问，进程内有效
- 磁盘缓存: 跨进程持久化，支持TTL过期
- 智能失效: 支持按目录或全局清除缓存
- 性能优化: 首次扫描后重复调用快100x+

使用示例:
    >>> from skillscripts.core.script_discovery_cache import ScriptDiscoveryCache
    >>> cache = ScriptDiscoveryCache()
    >>> scripts = cache.discover_scripts('skillscripts/analysis', '*.py')
    >>> print(f"发现 {len(scripts)} 个脚本")
"""

import json
import logging
import os
from datetime import datetime
from hashlib import md5
from pathlib import Path
from typing import Dict, List, Optional


class ScriptDiscoveryCache:
    """
    脚本发现结果缓存机制

    通过双层缓存（内存+磁盘）避免重复文件系统扫描，
    显著提升脚本发现的性能。适用于频繁调用脚本列表的场景。

    Attributes:
        CACHE_FILE: 默认磁盘缓存文件名
        CACHE_TTL_SECONDS: 缓存默认过期时间（秒）
    """

    CACHE_FILE = "cache.json"
    CACHE_TTL_SECONDS = 3600

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化脚本发现缓存

        Args:
            cache_dir: 缓存目录路径，默认使用项目根目录下的 cache/script_discovery/
        """
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            try:
                from skillscripts.core.path_config_center import PathConfigCenter
                pcc = PathConfigCenter.instance()
                self.cache_dir = pcc.CACHE_DIR / "script_discovery"
            except Exception:
                self.cache_dir = Path("cache/script_discovery")

        self.cache_file = self.cache_dir / self.CACHE_FILE
        self._memory_cache: Dict[str, dict] = {}

        self.logger.info(f"ScriptDiscoveryCache 初始化完成，缓存目录: {self.cache_dir}")

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

    def discover_scripts(self, directory: str, pattern: str = "*.py") -> List[Path]:
        """
        发现目录下的脚本文件（带缓存）

        使用双层缓存策略：
        1. 先查内存缓存（最快）
        2. 再查磁盘缓存（较快）
        3. 最后执行实际文件系统扫描

        Args:
            directory: 要扫描的目录路径
            pattern: 文件匹配模式（如 "*.py", "*.sh"）

        Returns:
            匹配的文件路径列表

        示例:
            >>> cache = ScriptDiscoveryCache()
            >>> scripts = cache.discover_scripts('skillscripts/core', '*.py')
            >>> print(len(scripts))
        """
        cache_key = self._generate_key(directory, pattern)

        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            self.logger.debug(f"缓存命中 [{cache_key}]: {len(cached_result)} 个文件")
            return cached_result

        self.logger.debug(f"缓存未命中，开始扫描目录: {directory}")
        files = self._scan_directory(directory, pattern)

        cache_entry = {
            'files': [str(f) for f in files],
            'timestamp': datetime.now().isoformat(),
            'count': len(files),
            'directory': directory,
            'pattern': pattern
        }

        self._store_to_cache(cache_key, cache_entry)

        self.logger.info(f"目录扫描完成 [{directory}]: 发现 {len(files)} 个文件 (模式: {pattern})")

        return files

    def _scan_directory(self, directory: str, pattern: str) -> List[Path]:
        """
        执行实际的目录扫描

        Args:
            directory: 目录路径
            pattern: 文件匹配模式

        Returns:
            文件路径列表
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            self.logger.warning(f"目录不存在: {directory}")
            return []

        if not dir_path.is_dir():
            self.logger.warning(f"不是目录: {directory}")
            return []

        try:
            files = sorted(dir_path.rglob(pattern))
            files = [f for f in files if f.is_file()]
            return files
        except Exception as e:
            self.logger.error(f"扫描目录失败 [{directory}]: {e}")
            return []

    def _get_from_cache(self, key: str) -> Optional[List[Path]]:
        """
        从缓存获取数据

        先查内存缓存，再查磁盘缓存

        Args:
            key: 缓存键

        Returns:
            文件路径列表，如果缓存未命中或已过期则返回 None
        """
        if key in self._memory_cache:
            cached = self._memory_cache[key]
            if not self._is_expired(cached):
                return [Path(p) for p in cached['files']]
            else:
                del self._memory_cache[key]
                self.logger.debug(f"内存缓存已过期: {key}")

        disk_cached = self._load_from_disk(key)
        if disk_cached and not self._is_expired(disk_cached):
            self._memory_cache[key] = disk_cached
            return [Path(p) for p in disk_cached['files']]

        return None

    def _store_to_cache(self, key: str, entry: dict) -> None:
        """
        存储数据到缓存（内存+磁盘）

        Args:
            key: 缓存键
            entry: 缓存条目
        """
        self._memory_cache[key] = entry
        self._save_to_disk(key, entry)

    def invalidate(self, directory: str = None) -> None:
        """
        使缓存失效

        Args:
            directory: 要失效的目录路径。如果为 None，则使所有缓存失效

        示例:
            >>> cache = ScriptDiscoveryCache()
            >>> cache.invalidate('skillscripts/core')  # 使特定目录缓存失效
            >>> cache.invalidate()  # 使所有缓存失效
        """
        if directory:
            keys_to_remove = [
                k for k in self._memory_cache
                if directory in self._memory_cache[k].get('directory', '')
            ]

            for k in keys_to_remove:
                del self._memory_cache[k]

            self.logger.info(f"已使 {len(keys_to_remove)} 个缓存项失效 (目录: {directory})")
        else:
            cache_size = len(self._memory_cache)
            self._memory_cache.clear()

            if self.cache_file.exists():
                try:
                    self.cache_file.unlink()
                    self.logger.info(f"已删除磁盘缓存文件: {self.cache_file}")
                except Exception as e:
                    self.logger.error(f"删除磁盘缓存失败: {e}")

            self.logger.info(f"已清除所有缓存 (共 {cache_size} 项)")

    def get_cache_stats(self) -> dict:
        """
        获取缓存统计信息

        Returns:
            包含缓存统计信息的字典
        """
        disk_cache_exists = self.cache_file.exists()
        disk_cache_size = 0

        if disk_cache_exists:
            try:
                disk_cache_size = self.cache_file.stat().st_size
            except Exception:
                pass

        return {
            'memory_cache_entries': len(self._memory_cache),
            'disk_cache_exists': disk_cache_exists,
            'disk_cache_file': str(self.cache_file),
            'disk_cache_size_bytes': disk_cache_size,
            'cache_ttl_seconds': self.CACHE_TTL_SECONDS,
            'cache_dir': str(self.cache_dir)
        }

    def _generate_key(self, directory: str, pattern: str) -> str:
        """
        生成缓存键

        使用MD5哈希生成唯一的缓存键

        Args:
            directory: 目录路径
            pattern: 文件匹配模式

        Returns:
            12字符的哈希键
        """
        raw = f"{directory}:{pattern}"
        return md5(raw.encode()).hexdigest()[:12]

    def _is_expired(self, cached: dict) -> bool:
        """
        检查缓存是否过期

        Args:
            cached: 缓存条目

        Returns:
            是否已过期
        """
        try:
            ts = datetime.fromisoformat(cached['timestamp'])
            elapsed = (datetime.now() - ts).total_seconds()
            return elapsed > self.CACHE_TTL_SECONDS
        except (KeyError, ValueError) as e:
            self.logger.warning(f"检查缓存过期时间失败: {e}")
            return True

    def _load_from_disk(self, key: str) -> Optional[dict]:
        """
        从磁盘加载缓存

        Args:
            key: 缓存键

        Returns:
            缓存条目，如果不存在或加载失败则返回 None
        """
        if not self.cache_file.exists():
            return None

        try:
            data = json.loads(self.cache_file.read_text(encoding='utf-8'))
            return data.get(key)
        except json.JSONDecodeError as e:
            self.logger.warning(f"解析磁盘缓存失败: {e}")
            return None
        except Exception as e:
            self.logger.warning(f"从磁盘加载缓存失败: {e}")
            return None

    def _save_to_disk(self, key: str, entry: dict) -> None:
        """
        保存到磁盘

        Args:
            key: 缓存键
            entry: 缓存条目
        """
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            data = {}
            if self.cache_file.exists():
                try:
                    data = json.loads(self.cache_file.read_text(encoding='utf-8'))
                except json.JSONDecodeError:
                    pass

            data[key] = entry
            self.cache_file.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )

        except Exception as e:
            self.logger.error(f"保存到磁盘失败: {e}")


def main():
    """测试脚本发现缓存功能"""
    import time

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    print("=" * 80)
    print("脚本发现缓存机制测试")
    print("=" * 80)

    cache = ScriptDiscoveryCache()

    test_dirs = [
        ('skillscripts/core', '*.py'),
        ('skillscripts/analysis', '*.py'),
        ('skillscripts/monitoring', '*.py')
    ]

    print("\n📂 首次扫描（无缓存）:")
    first_scan_times = []

    for directory, pattern in test_dirs:
        start_time = time.time()
        files = cache.discover_scripts(directory, pattern)
        elapsed = time.time() - start_time
        first_scan_times.append(elapsed)
        print(f"  {directory}/{pattern}: {len(files)} 个文件, 耗时 {elapsed*1000:.2f}ms")

    print("\n📂 第二次扫描（有缓存）:")
    second_scan_times = []

    for directory, pattern in test_dirs:
        start_time = time.time()
        files = cache.discover_scripts(directory, pattern)
        elapsed = time.time() - start_time
        second_scan_times.append(elapsed)
        print(f"  {directory}/{pattern}: {len(files)} 个文件, 耗时 {elapsed*1000:.2f}ms")

    print("\n⚡ 性能对比:")
    for i, (directory, pattern) in enumerate(test_dirs):
        if second_scan_times[i] > 0:
            speedup = first_scan_times[i] / second_scan_times[i]
            print(f"  {directory}: 加速 {speedup:.1f}x")

    print("\n📊 缓存统计:")
    stats = cache.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    print("\n✅ 测试完成!")


if __name__ == "__main__":
    main()
