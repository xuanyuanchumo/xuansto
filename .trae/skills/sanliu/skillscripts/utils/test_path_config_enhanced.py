#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径配置管理器增强功能测试脚本

测试内容：
1. 脚本路径注册表功能
2. 脚本路径获取方法
3. 路径验证功能
4. 动态路径解析功能
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(get_path_config().SCRIPTS_DIR / "utils"))

from path_config_manager import (
from skillscripts.core.path_config_center import get_path_config
    PathConfigManager,
    PathMode,
    ScriptPathRegistry,
    ScriptInfo,
    DynamicPathResolver
)


class PathConfigEnhancedTest:
    """路径配置增强功能测试类"""
    
    def __init__(self):
        self.manager = PathConfigManager()
        self.test_results: List[Dict[str, Any]] = []
    
    def run_all_tests(self) -> Dict[str, Any]:
        """运行所有测试"""
        print("=" * 80)
        print("路径配置管理器增强功能测试")
        print("=" * 80)
        print()
        
        self.test_script_registry_initialization()
        self.test_script_path_methods()
        self.test_script_search_functionality()
        self.test_script_validation()
        self.test_dynamic_path_resolver()
        self.test_all_paths_includes_scripts()
        
        return self._generate_report()
    
    def test_script_registry_initialization(self) -> None:
        """测试脚本路径注册表初始化"""
        print("测试 1: 脚本路径注册表初始化")
        print("-" * 80)
        
        try:
            registry_info = self.manager.get_script_registry_info()
            
            assert registry_info["initialized"] == True, "脚本注册表应该已初始化"
            assert registry_info["total_scripts"] > 0, "应该有注册的脚本"
            assert len(registry_info["categories"]) > 0, "应该有脚本类别"
            
            print(f"✓ 脚本注册表已初始化")
            print(f"✓ 总脚本数: {registry_info['total_scripts']}")
            print(f"✓ 脚本类别数: {len(registry_info['categories'])}")
            print()
            
            for category, count in registry_info["categories"].items():
                print(f"  - {category}: {count} 个脚本")
            
            self.test_results.append({
                "test": "脚本路径注册表初始化",
                "status": "PASS",
                "details": registry_info
            })
            
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            self.test_results.append({
                "test": "脚本路径注册表初始化",
                "status": "FAIL",
                "error": str(e)
            })
        
        print()
    
    def test_script_path_methods(self) -> None:
        """测试脚本路径获取方法"""
        print("测试 2: 脚本路径获取方法")
        print("-" * 80)
        
        try:
            paths = {
                "core": self.manager.get_scripts_core_path(),
                "analysis": self.manager.get_scripts_analysis_path(),
                "optimization": self.manager.get_scripts_optimization_path(),
                "test": self.manager.get_scripts_test_path(),
                "pipeline": self.manager.get_scripts_pipeline_path(),
                "learning": self.manager.get_scripts_learning_path(),
                "auto_repair": self.manager.get_scripts_auto_repair_path(),
                "iteration": self.manager.get_scripts_iteration_path(),
                "requirements": self.manager.get_scripts_requirements_path(),
                "sdd_tdd": self.manager.get_scripts_sdd_tdd_path(),
                "monitoring": self.manager.get_scripts_monitoring_path(),
                "utils": self.manager.get_scripts_utils_path()
            }
            
            for category, path in paths.items():
                print(f"✓ {category}: {path}")
                assert path.exists(), f"{category} 路径应该存在"
            
            self.test_results.append({
                "test": "脚本路径获取方法",
                "status": "PASS",
                "details": {k: str(v) for k, v in paths.items()}
            })
            
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            self.test_results.append({
                "test": "脚本路径获取方法",
                "status": "FAIL",
                "error": str(e)
            })
        
        print()
    
    def test_script_search_functionality(self) -> None:
        """测试脚本搜索功能"""
        print("测试 3: 脚本搜索功能")
        print("-" * 80)
        
        try:
            print("测试按类别获取脚本:")
            core_scripts = self.manager.get_scripts_by_category("core")
            print(f"✓ core 类别脚本数: {len(core_scripts)}")
            
            if core_scripts:
                sample_script = core_scripts[0]
                print(f"  示例: {sample_script.name} - {sample_script.relative_path}")
            
            print()
            print("测试按名称搜索脚本:")
            script_info = self.manager.get_script_by_name("auto_iterator.py")
            if script_info:
                print(f"✓ 找到脚本: {script_info.name}")
                print(f"  类别: {script_info.category}")
                print(f"  相对路径: {script_info.relative_path}")
            
            print()
            print("测试关键词搜索:")
            search_results = self.manager.search_scripts("optimizer")
            print(f"✓ 搜索 'optimizer' 找到 {len(search_results)} 个脚本")
            
            for script in search_results[:5]:
                print(f"  - {script.category}/{script.name}")
            
            self.test_results.append({
                "test": "脚本搜索功能",
                "status": "PASS",
                "details": {
                    "core_scripts_count": len(core_scripts),
                    "search_results_count": len(search_results)
                }
            })
            
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            self.test_results.append({
                "test": "脚本搜索功能",
                "status": "FAIL",
                "error": str(e)
            })
        
        print()
    
    def test_script_validation(self) -> None:
        """测试脚本验证功能"""
        print("测试 4: 脚本验证功能")
        print("-" * 80)
        
        try:
            print("验证所有脚本是否存在:")
            validation_results = self.manager.validate_all_scripts()
            
            total_scripts = len(validation_results)
            existing_scripts = sum(1 for exists in validation_results.values() if exists)
            missing_scripts = total_scripts - existing_scripts
            
            print(f"✓ 总脚本数: {total_scripts}")
            print(f"✓ 存在的脚本: {existing_scripts}")
            print(f"✓ 缺失的脚本: {missing_scripts}")
            
            if missing_scripts > 0:
                print()
                print("缺失的脚本列表:")
                missing_list = self.manager.get_missing_scripts()
                for script_id in missing_list[:10]:
                    print(f"  - {script_id}")
                if len(missing_list) > 10:
                    print(f"  ... 还有 {len(missing_list) - 10} 个")
            
            print()
            print("验证单个脚本:")
            test_script_id = "core/auto_iterator.py"
            exists = self.manager.validate_script_exists(test_script_id)
            print(f"✓ {test_script_id}: {'存在' if exists else '不存在'}")
            
            script_path = self.manager.get_script_path(test_script_id)
            if script_path:
                print(f"  完整路径: {script_path}")
            
            self.test_results.append({
                "test": "脚本验证功能",
                "status": "PASS",
                "details": {
                    "total_scripts": total_scripts,
                    "existing_scripts": existing_scripts,
                    "missing_scripts": missing_scripts
                }
            })
            
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            self.test_results.append({
                "test": "脚本验证功能",
                "status": "FAIL",
                "error": str(e)
            })
        
        print()
    
    def test_dynamic_path_resolver(self) -> None:
        """测试动态路径解析功能"""
        print("测试 5: 动态路径解析功能")
        print("-" * 80)
        
        try:
            resolver = DynamicPathResolver(base_path=self.manager.get_base_path())
            
            test_paths = [
                "${PROJECT_ROOT}/docs",
                "${PROJECT_ROOT}/skillscripts/core",
                "${DATE}/report.md",
                "${DATETIME}/test.log"
            ]
            
            print("测试路径模板解析:")
            for template in test_paths:
                resolved = resolver.resolve(template)
                print(f"✓ {template}")
                print(f"  -> {resolved}")
            
            print()
            print("测试内置变量:")
            context = {
                "version": "1.0.0",
                "mode": "self_iteration"
            }
            resolver.update_context(context)
            
            version_path = resolver.resolve("${PROJECT_ROOT}/version_${VERSION}.json")
            print(f"✓ 版本路径: {version_path}")
            
            self.test_results.append({
                "test": "动态路径解析功能",
                "status": "PASS",
                "details": {
                    "test_paths_count": len(test_paths)
                }
            })
            
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            self.test_results.append({
                "test": "动态路径解析功能",
                "status": "FAIL",
                "error": str(e)
            })
        
        print()
    
    def test_all_paths_includes_scripts(self) -> None:
        """测试 get_all_paths 包含脚本路径"""
        print("测试 6: get_all_paths 包含脚本路径")
        print("-" * 80)
        
        try:
            all_paths = self.manager.get_all_paths()
            
            script_path_keys = [
                "scripts_core",
                "scripts_analysis",
                "scripts_optimization",
                "scripts_test",
                "scripts_pipeline",
                "scripts_learning",
                "scripts_auto_repair",
                "scripts_iteration",
                "scripts_requirements",
                "scripts_sdd_tdd",
                "scripts_monitoring",
                "scripts_utils"
            ]
            
            print("验证脚本路径是否包含在 get_all_paths 中:")
            for key in script_path_keys:
                assert key in all_paths, f"{key} 应该在 all_paths 中"
                print(f"✓ {key}: {all_paths[key]}")
            
            self.test_results.append({
                "test": "get_all_paths 包含脚本路径",
                "status": "PASS",
                "details": {
                    "script_paths_count": len(script_path_keys)
                }
            })
            
        except Exception as e:
            print(f"✗ 测试失败: {e}")
            self.test_results.append({
                "test": "get_all_paths 包含脚本路径",
                "status": "FAIL",
                "error": str(e)
            })
        
        print()
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成测试报告"""
        print("=" * 80)
        print("测试报告")
        print("=" * 80)
        print()
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "PASS")
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"通过率: {passed_tests / total_tests * 100:.1f}%")
        print()
        
        print("测试结果详情:")
        for result in self.test_results:
            status_symbol = "✓" if result["status"] == "PASS" else "✗"
            print(f"{status_symbol} {result['test']}: {result['status']}")
        
        return {
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "pass_rate": f"{passed_tests / total_tests * 100:.1f}%"
            },
            "results": self.test_results
        }


def main():
    """主函数"""
    test = PathConfigEnhancedTest()
    results = test.run_all_tests()
    
    report_path = Path(__file__).parent / "test_path_config_enhanced_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print()
    print(f"测试报告已保存到: {report_path}")
    
    if results["summary"]["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
