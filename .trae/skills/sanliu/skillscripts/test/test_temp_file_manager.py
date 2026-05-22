#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三省六部协同开发系统 - 临时文件管理器单元测试
"""

import os
import sys
import time
import tempfile
import threading
from pathlib import Path
from datetime import datetime, timedelta

from skillscripts.utils.temp_file_manager import (
    TempFileManager,
    TempFileResult,
    TempFileInfo,
    create_temp_file,
    atomic_replace,
    is_file_in_use,
    wait_for_release,
    cleanup_temp_files
)


class TestTempFileManager:
    def __init__(self):
        self.test_dir = None
        self.manager = None
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def setup(self):
        self.test_dir = tempfile.mkdtemp(prefix="temp_file_test_")
        self.manager = TempFileManager(temp_dir=self.test_dir)
        print(f"✓ 测试环境初始化: {self.test_dir}")
    
    def teardown(self):
        if self.test_dir and Path(self.test_dir).exists():
            import shutil
            shutil.rmtree(self.test_dir, ignore_errors=True)
        print("✓ 测试环境清理完成")
    
    def assert_true(self, condition: bool, message: str):
        if condition:
            self.passed += 1
            print(f"  ✓ {message}")
        else:
            self.failed += 1
            self.errors.append(message)
            print(f"  ✗ {message}")
    
    def assert_equal(self, actual, expected, message: str):
        if actual == expected:
            self.passed += 1
            print(f"  ✓ {message}")
        else:
            self.failed += 1
            error_msg = f"{message} (期望: {expected}, 实际: {actual})"
            self.errors.append(error_msg)
            print(f"  ✗ {error_msg}")
    
    def assert_not_equal(self, actual, expected, message: str):
        if actual != expected:
            self.passed += 1
            print(f"  ✓ {message}")
        else:
            self.failed += 1
            error_msg = f"{message} (不应等于: {expected})"
            self.errors.append(error_msg)
            print(f"  ✗ {error_msg}")
    
    def assert_contains(self, text: str, substring: str, message: str):
        if substring in text:
            self.passed += 1
            print(f"  ✓ {message}")
        else:
            self.failed += 1
            error_msg = f"{message} (未找到: {substring})"
            self.errors.append(error_msg)
            print(f"  ✗ {error_msg}")
    
    def test_generate_temp_filename(self):
        print("\n[测试] 临时文件命名策略")
        
        original_path = str(Path(self.test_dir) / "script.py")
        temp_path = self.manager._generate_temp_filename(original_path)
        
        self.assert_contains(temp_path, "_temp_", "包含 _temp_ 标识")
        self.assert_contains(temp_path, ".py", "保留原扩展名")
        self.assert_true(
            Path(temp_path).name.startswith("script_temp_"),
            "文件名格式正确"
        )
    
    def test_create_temp_file(self):
        print("\n[测试] 创建临时文件")
        
        original_path = str(Path(self.test_dir) / "test_file.txt")
        Path(original_path).write_text("original content", encoding='utf-8')
        
        result = self.manager.create_temp_file(original_path)
        
        self.assert_true(result.success, "创建成功")
        self.assert_true(result.temp_path is not None, "返回临时文件路径")
        self.assert_true(
            Path(result.temp_path).exists(),
            "临时文件实际存在"
        )
        self.assert_contains(
            result.temp_path,
            "_temp_",
            "临时文件名格式正确"
        )
    
    def test_create_temp_file_with_content(self):
        print("\n[测试] 创建带内容的临时文件")
        
        original_path = str(Path(self.test_dir) / "content_test.txt")
        test_content = "Hello, Temp File Manager!"
        
        result = self.manager.create_temp_file(
            original_path,
            content=test_content
        )
        
        self.assert_true(result.success, "创建成功")
        
        actual_content = Path(result.temp_path).read_text(encoding='utf-8')
        self.assert_equal(actual_content, test_content, "内容正确写入")
    
    def test_create_temp_file_copy_original(self):
        print("\n[测试] 复制原文件创建临时文件")
        
        original_path = str(Path(self.test_dir) / "copy_test.txt")
        original_content = "original content for copy"
        Path(original_path).write_text(original_content, encoding='utf-8')
        
        result = self.manager.create_temp_file(
            original_path,
            copy_original=True
        )
        
        self.assert_true(result.success, "创建成功")
        
        temp_content = Path(result.temp_path).read_text(encoding='utf-8')
        self.assert_equal(temp_content, original_content, "内容复制正确")
    
    def test_create_temp_file_not_found(self):
        print("\n[测试] 原文件不存在时的错误处理")
        
        non_existent = str(Path(self.test_dir) / "non_existent.txt")
        result = self.manager.create_temp_file(non_existent, copy_original=True)
        
        self.assert_true(not result.success, "创建失败")
        self.assert_equal(result.error, "FILE_NOT_FOUND", "错误码正确")
    
    def test_atomic_replace(self):
        print("\n[测试] 原子性文件替换")
        
        original_path = str(Path(self.test_dir) / "replace_test.txt")
        Path(original_path).write_text("old content", encoding='utf-8')
        
        temp_result = self.manager.create_temp_file(
            original_path,
            content="new content"
        )
        
        replace_result = self.manager.atomic_replace(
            temp_result.temp_path,
            original_path
        )
        
        self.assert_true(replace_result.success, "替换成功")
        self.assert_true(
            not Path(temp_result.temp_path).exists(),
            "临时文件已删除"
        )
        
        final_content = Path(original_path).read_text(encoding='utf-8')
        self.assert_equal(final_content, "new content", "内容替换正确")
    
    def test_atomic_replace_with_backup(self):
        print("\n[测试] 带备份的原子替换")
        
        original_path = str(Path(self.test_dir) / "backup_test.txt")
        Path(original_path).write_text("original", encoding='utf-8')
        
        temp_result = self.manager.create_temp_file(
            original_path,
            content="updated"
        )
        
        replace_result = self.manager.atomic_replace(
            temp_result.temp_path,
            original_path,
            backup=True
        )
        
        self.assert_true(replace_result.success, "替换成功")
        self.assert_true(
            not Path(str(original_path) + ".bak").exists(),
            "备份文件已清理"
        )
    
    def test_atomic_replace_temp_not_found(self):
        print("\n[测试] 临时文件不存在时的替换错误")
        
        original_path = str(Path(self.test_dir) / "target.txt")
        non_existent_temp = str(Path(self.test_dir) / "not_exist_temp.txt")
        
        result = self.manager.atomic_replace(non_existent_temp, original_path)
        
        self.assert_true(not result.success, "替换失败")
        self.assert_equal(result.error, "TEMP_FILE_NOT_FOUND", "错误码正确")
    
    def test_is_file_in_use(self):
        print("\n[测试] 文件使用状态检测")
        
        file_path = str(Path(self.test_dir) / "usage_test.txt")
        Path(file_path).write_text("test", encoding='utf-8')
        
        in_use = self.manager.is_file_in_use(file_path)
        self.assert_true(not in_use, "未锁定文件返回 False")
        
        non_existent = str(Path(self.test_dir) / "not_exist.txt")
        in_use = self.manager.is_file_in_use(non_existent)
        self.assert_true(not in_use, "不存在文件返回 False")
    
    def test_wait_for_release(self):
        print("\n[测试] 等待文件释放")
        
        file_path = str(Path(self.test_dir) / "wait_test.txt")
        Path(file_path).write_text("test", encoding='utf-8')
        
        start_time = time.time()
        released = self.manager.wait_for_release(file_path, timeout=2)
        elapsed = time.time() - start_time
        
        self.assert_true(released, "文件释放成功")
        self.assert_true(elapsed < 1, "快速返回")
    
    def test_register_unregister_temp_file(self):
        print("\n[测试] 临时文件注册和注销")
        
        self.manager._registered_files.clear()
        
        temp_path = str(Path(self.test_dir) / "registered_temp.txt")
        original_path = str(Path(self.test_dir) / "original.txt")
        
        registered = self.manager.register_temp_file(temp_path, original_path)
        self.assert_true(registered, "注册成功")
        
        registered_files = self.manager.get_registered_temp_files()
        self.assert_equal(len(registered_files), 1, "注册列表包含1个文件")
        
        unregistered = self.manager.unregister_temp_file(temp_path)
        self.assert_true(unregistered, "注销成功")
        
        registered_files = self.manager.get_registered_temp_files()
        self.assert_equal(len(registered_files), 0, "注册列表为空")
        
        double_unregister = self.manager.unregister_temp_file(temp_path)
        self.assert_true(not double_unregister, "重复注销返回 False")
    
    def test_cleanup_temp_files(self):
        print("\n[测试] 清理过期临时文件")
        
        old_temp = str(Path(self.test_dir) / "old_temp_20260101_000000.txt")
        Path(old_temp).write_text("old", encoding='utf-8')
        
        os.utime(old_temp, (time.time() - 7200, time.time() - 7200))
        
        new_temp = str(Path(self.test_dir) / "new_temp_20260330_120000.txt")
        Path(new_temp).write_text("new", encoding='utf-8')
        
        result = self.manager.cleanup_temp_files(
            self.test_dir,
            expire_seconds=3600
        )
        
        self.assert_true(old_temp in result["cleaned"], "旧文件被清理")
        self.assert_true(new_temp in result["skipped"], "新文件被跳过")
        self.assert_true(not Path(old_temp).exists(), "旧文件已删除")
        self.assert_true(Path(new_temp).exists(), "新文件仍存在")
    
    def test_cleanup_temp_files_dry_run(self):
        print("\n[测试] 模拟清理（dry run）")
        
        old_temp = str(Path(self.test_dir) / "dry_old_temp_20260101.txt")
        Path(old_temp).write_text("old", encoding='utf-8')
        os.utime(old_temp, (time.time() - 7200, time.time() - 7200))
        
        result = self.manager.cleanup_temp_files(
            self.test_dir,
            expire_seconds=3600,
            dry_run=True
        )
        
        self.assert_true(old_temp in result["cleaned"], "记录在清理列表")
        self.assert_true(Path(old_temp).exists(), "文件实际未删除")
    
    def test_cleanup_all_registered(self):
        print("\n[测试] 清理所有注册的临时文件")
        
        self.manager._registered_files.clear()
        
        for i in range(3):
            temp_path = str(Path(self.test_dir) / f"registered_{i}_temp.txt")
            Path(temp_path).write_text(f"content {i}", encoding='utf-8')
            self.manager.register_temp_file(temp_path)
        
        result = self.manager.cleanup_all_registered()
        
        self.assert_equal(len(result["cleaned"]), 3, "清理3个文件")
        self.assert_equal(len(self.manager.get_registered_temp_files()), 0, "注册列表清空")
    
    def test_temp_file_context(self):
        print("\n[测试] 上下文管理器")
        
        original_path = str(Path(self.test_dir) / "context_test.txt")
        Path(original_path).write_text("original", encoding='utf-8')
        
        try:
            with self.manager.temp_file_context(
                original_path,
                content="updated content"
            ) as temp_path:
                self.assert_true(Path(temp_path).exists(), "临时文件存在")
                self.assert_contains(temp_path, "_temp_", "临时文件名格式正确")
            
            final_content = Path(original_path).read_text(encoding='utf-8')
            self.assert_equal(final_content, "updated content", "自动替换成功")
            
        except Exception as e:
            self.failed += 1
            self.errors.append(f"上下文管理器异常: {e}")
            print(f"  ✗ 上下文管理器异常: {e}")
    
    def test_temp_file_context_exception(self):
        print("\n[测试] 上下文管理器异常处理")
        
        original_path = str(Path(self.test_dir) / "exception_test.txt")
        Path(original_path).write_text("original", encoding='utf-8')
        
        temp_path_used = None
        try:
            with self.manager.temp_file_context(
                original_path,
                content="should not appear"
            ) as temp_path:
                temp_path_used = temp_path
                raise ValueError("模拟异常")
        except ValueError:
            pass
        
        self.assert_true(
            not Path(temp_path_used).exists(),
            "异常时临时文件被清理"
        )
        
        original_content = Path(original_path).read_text(encoding='utf-8')
        self.assert_equal(original_content, "original", "原文件未被修改")
    
    def test_convenience_functions(self):
        print("\n[测试] 便捷函数")
        
        original_path = str(Path(self.test_dir) / "convenience_test.txt")
        Path(original_path).write_text("test", encoding='utf-8')
        
        result = create_temp_file(original_path)
        self.assert_true(result.success, "create_temp_file 函数工作正常")
        
        in_use = is_file_in_use(result.temp_path)
        self.assert_true(not in_use, "is_file_in_use 函数工作正常")
        
        released = wait_for_release(result.temp_path, timeout=1)
        self.assert_true(released, "wait_for_release 函数工作正常")
        
        replace_result = atomic_replace(result.temp_path, original_path)
        self.assert_true(replace_result.success, "atomic_replace 函数工作正常")
    
    def test_thread_safety(self):
        print("\n[测试] 线程安全性")
        
        results = []
        errors = []
        
        def worker(worker_id: int):
            try:
                for i in range(5):
                    temp_name = f"thread_{worker_id}_temp_{i}.txt"
                    temp_path = str(Path(self.test_dir) / temp_name)
                    Path(temp_path).write_text(f"worker {worker_id}", encoding='utf-8')
                    
                    self.manager.register_temp_file(temp_path)
                    time.sleep(0.01)
                    self.manager.unregister_temp_file(temp_path)
                    
                results.append(worker_id)
            except Exception as e:
                errors.append((worker_id, str(e)))
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        self.assert_equal(len(results), 5, "所有线程完成")
        self.assert_equal(len(errors), 0, "无线程错误")
    
    def run_all_tests(self):
        print("=" * 60)
        print("临时文件管理器单元测试")
        print("=" * 60)
        
        self.setup()
        
        try:
            self.test_generate_temp_filename()
            self.test_create_temp_file()
            self.test_create_temp_file_with_content()
            self.test_create_temp_file_copy_original()
            self.test_create_temp_file_not_found()
            self.test_atomic_replace()
            self.test_atomic_replace_with_backup()
            self.test_atomic_replace_temp_not_found()
            self.test_is_file_in_use()
            self.test_wait_for_release()
            self.test_register_unregister_temp_file()
            self.test_cleanup_temp_files()
            self.test_cleanup_temp_files_dry_run()
            self.test_cleanup_all_registered()
            self.test_temp_file_context()
            self.test_temp_file_context_exception()
            self.test_convenience_functions()
            self.test_thread_safety()
        finally:
            self.teardown()
        
        print("\n" + "=" * 60)
        print(f"测试结果: 通过 {self.passed}, 失败 {self.failed}")
        print("=" * 60)
        
        if self.errors:
            print("\n失败详情:")
            for error in self.errors:
                print(f"  - {error}")
        
        return self.failed == 0


if __name__ == "__main__":
    tester = TestTempFileManager()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
