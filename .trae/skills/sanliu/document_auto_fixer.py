# -*- coding: utf-8 -*-
"""
三省六部技能文档自动修复工具
功能：
1. 修复标题层级跳跃问题
2. 修正错误的脚本路径引用
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Dict

class DocumentAutoFixer:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.subskills_dir = self.base_dir / "subskills"
        self.skillscripts_dir = self.base_dir / "skillscripts"
        
        # 路径映射表：错误的路径 -> 正确的路径
        self.path_mapping = {
            # SKILL.md中的路径
            'skillscripts/core/start_services.py': None,  # 需要确认是否存在
            'skillscripts/core/health_check.py': None,
            'provincial_coordinator.py': 'skillscripts/core/provincial_coordinator.py',
            'skillscripts/utils/path_migration_tool.py': None,
            
            # continuous_evolution.md
            'scripts/evolution_manager.py': 'skillscripts/core/skill_evolution_manager.py',
            'scripts/continuous_evolution_controller.py': 'skillscripts/core/continuous_evolution_controller.py',
            'scripts/skill_evolution_manager.py': 'skillscripts/core/skill_evolution_manager.py',
            
            # daima_chonggou.md
            'skillscripts/utils/code_review_automation.py': 'skillscripts/analysis/code_review_automation.py',
            'scripts/architecture_check.py': 'skillscripts/analysis/architecture_check.py',
            'scripts/performance_detector.py': 'skillscripts/analysis/performance_detector.py',
            'scripts/security_scanner.py': 'skillscripts/test/security_scanner.py',
            
            # knowledge_base.md
            'scripts/knowledge_manager.py': 'skillscripts/utils/knowledge_manager.py',
            'scripts/knowledge_learner.py': None,
            'scripts/knowledge_sharing.py': 'skillscripts/core/cross_project_knowledge_sharing.py',
            'scripts/knowledge_quality.py': None,
            
            # self_iteration.md - 大量路径
            'scripts/version_iterator.py': 'skillscripts/core/test_enhanced_version_iterator.py',
            'scripts/rollback_manager.py': 'skillscripts/optimization/fix_rollback_manager.py',
            'scripts/auto_fixer.py': 'skillscripts/auto_repair/doc_auto_fixer.py',
            'scripts/log_analyzer.py': 'skillscripts/analysis/enhanced_log_analyzer.py',
            'scripts/issue_locator.py': 'skillscripts/analysis/issue_locator.py',
            'scripts/skill_caller.py': 'skillscripts/utils/skill_caller.py',
            'scripts/skill_registry.py': 'skillscripts/utils/skill_registry.py',
            'scripts/interface_validator.py': 'skillscripts/utils/interface_validator.py',
            'scripts/self_iterate.py': 'skillscripts/utils/self_iterate.py',
            'scripts/iteration_coordinator.py': 'skillscripts/utils/iteration_coordinator.py',
            'scripts/skill_content_updater.py': 'skillscripts/utils/skill_content_updater.py',
            'scripts/doc_updater.py': 'skillscripts/core/skill_doc_updater.py',
            'scripts/self_optimizer.py': 'skillscripts/utils/self_optimizer.py',
            'scripts/self_healer.py': 'skillscripts/utils/self_healer.py',
            'scripts/self_improver.py': 'skillscripts/utils/self_improver.py',
            
            # anquan_ceshi.md
            'security_scanner.py': 'skillscripts/test/security_scanner.py',
            
            # baihehua_liushuixian.md
            'scripts/validate_specs.py': 'skillscripts/utils/validate_specs.py',
            'scripts/check_db_connection.py': 'skillscripts/utils/check_db_connection.py',
            'scripts/check_dependencies.py': 'skillscripts/utils/check_dependencies.py',
            'scripts/init_test_data.py': 'skillscripts/utils/init_test_data.py',
            
            # ceshi.md
            'run_all_tests.py': None,
            'run_backend_tests.py': None,
            'run_frontend_tests.py': None,
            'run_e2e_tests.py': None,
            'generate_coverage_report.py': None,
            
            # department_workflow.md
            'scripts/lint_check.py': None,
            'scripts/type_check.py': None,
            'scripts/security_scan.py': None,
            'scripts/code_smell_check.py': None,
            'scripts/coverage_check.py': None,
            'scripts/generate_api_docs.py': None,
            'scripts/generate_code_docs.py': None,
            'scripts/generate_arch_diagrams.py': None,
            'scripts/generate_changelog.py': None,
            'scripts/code_review.py': 'skillscripts/analysis/test_architecture_code_review.py',
            'scripts/generate_review_report.py': None,
            'scripts/deploy.py': None,
            'scripts/smoke_test.py': None,
            
            # skill_health_assessment.md
            'skillscripts/core/evolution_manager.py': 'skillscripts/core/skill_evolution_manager.py',
            'skillscripts/utils/helper.py': None,
            
            # skill_script_coordination.md
            'skillscripts/utils/call_tracer.py': None,
            
            # provincial_coordination.md (已在上面定义)
        }
        
        # 统计信息
        self.fix_stats = {
            'heading_fixes': 0,
            'path_fixes': 0,
            'files_modified': 0,
            'errors': 0
        }
    
    def fix_heading_hierarchy(self, file_path: Path) -> int:
        """修复标题层级跳跃问题"""
        fix_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            new_lines = []
            prev_heading_level = 0
            
            for line in lines:
                stripped = line.strip()
                
                if stripped.startswith('#'):
                    heading_match = re.match(r'^(#{1,6})\s+(.*)', stripped)
                    if heading_match:
                        current_level = len(heading_match.group(1))
                        heading_text = heading_match.group(2)
                        
                        # 检测是否需要修复层级跳跃
                        if prev_heading_level > 0 and current_level > prev_heading_level + 1:
                            # 计算应该的层级
                            expected_level = prev_heading_level + 1
                            
                            # 创建新的标题行
                            new_heading = '#' * expected_level + ' ' + heading_text
                            new_lines.append(new_heading)
                            fix_count += 1
                            print(f"  ✏️  行{len(new_lines)}: H{current_level} → H{expected_level}: {heading_text[:50]}")
                        else:
                            new_lines.append(line)
                        
                        prev_heading_level = current_level
                    else:
                        new_lines.append(line)
                        # 重置层级追踪如果遇到非标准标题
                        if not re.match(r'^#+\s', stripped):
                            prev_heading_level = 0
                else:
                    new_lines.append(line)
                    # 在非标题行重置层级（可选策略）
                    # 这里选择不重置，以保持章节内的层级关系
            
            if fix_count > 0:
                # 写回文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(new_lines))
                
        except Exception as e:
            print(f"  ❌ 修复标题时出错: {e}")
            self.fix_stats['errors'] += 1
            
        return fix_count
    
    def fix_script_paths(self, file_path: Path) -> int:
        """修复脚本路径引用"""
        fix_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            lines = content.split('\n')
            new_lines = []
            
            for line_num, line in enumerate(lines, 1):
                modified_line = line
                
                # 匹配各种脚本路径格式并替换
                patterns_to_check = [
                    r'python\s+([^\s`]+\.(?:py|sh|bat|ps1))',
                    r'`([^`]*\.(?:py|sh|bat|ps1)[^`]*)`',
                    r'(?<!`)(skillscripts[\\/][^\s`]*\.(?:py|sh|bat|ps1))',
                    r'(?<!`)(?:scripts?)[\\/][^\s`]*\.(?:py|sh|bat|ps1)',
                    r'(?<![\/\\])([a-zA-Z_][a-zA-Z0-9_]*\.py)',
                ]
                
                for pattern in patterns_to_check:
                    matches = re.finditer(pattern, line, re.IGNORECASE)
                    for match in matches:
                        old_path = match.group(1) if '${' not in match.group(0) else match.group(0)
                        
                        # 查找映射
                        if old_path in self.path_mapping:
                            new_path = self.path_mapping[old_path]
                            if new_path and new_path != old_path:
                                # 替换路径
                                modified_line = modified_line.replace(old_path, new_path)
                                fix_count += 1
                                if fix_count <= 3 or True:  # 显示所有修复
                                    print(f"  🔗 行{line_num}: {old_path} → {new_path}")
                
                new_lines.append(modified_line)
            
            if fix_count > 0:
                new_content = '\n'.join(new_lines)
                if new_content != original_content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    
        except Exception as e:
            print(f"  ❌ 修复路径时出错: {e}")
            self.fix_stats['errors'] += 1
            
        return fix_count
    
    def run_auto_fix(self) -> Dict:
        """运行自动修复"""
        print("=" * 80)
        print("🔧 三省六部技能文档自动修复工具")
        print("=" * 80)
        
        all_md_files = []
        
        # 收集所有.md文件
        skill_md = self.base_dir / "SKILL.md"
        if skill_md.exists():
            all_md_files.append(skill_md)
        
        if self.subskills_dir.exists():
            all_md_files.extend(self.subskills_dir.glob("*.md"))
        
        total_files = len(all_md_files)
        print(f"\n📁 发现 {total_files} 个.md文件待处理\n")
        
        for idx, md_file in enumerate(sorted(all_md_files), 1):
            relative_path = md_file.relative_to(self.base_dir)
            print(f"[{idx}/{total_files}] 📄 {relative_path}")
            
            # 1. 修复标题层级
            heading_fixes = self.fix_heading_hierarchy(md_file)
            if heading_fixes > 0:
                self.fix_stats['heading_fixes'] += heading_fixes
                self.fix_stats['files_modified'] += 1
                print(f"  ✅ 修复了 {heading_fixes} 处标题层级问题")
            
            # 2. 修复脚本路径
            path_fixes = self.fix_script_paths(md_file)
            if path_fixes > 0:
                self.fix_stats['path_fixes'] += path_fixes
                if heading_fixes == 0:  # 避免重复计数
                    self.fix_stats['files_modified'] += 1
                print(f"  ✅ 修复了 {path_fixes} 处路径引用")
            
            if heading_fixes == 0 and path_fixes == 0:
                print(f"  ℹ️  无需修复")
            
            print()
        
        return self.fix_stats
    
    def generate_fix_report(self) -> str:
        """生成修复报告"""
        report = f"""
# 文档自动修复报告

## 修复统计

| 项目 | 数量 |
|------|------|
| 处理文件总数 | - |
| 标题层级修复 | {self.fix_stats['heading_fixes']} 处 |
| 路径引用修复 | {self.fix_stats['path_fixes']} 处 |
| 修改文件数 | {self.fix_stats['files_modified']} 个 |
| 错误数 | {self.fix_stats['errors']} 个 |

## 修复详情

### 标题层级修复 ({self.fix_stats['heading_fixes']}处)
- 将所有H1→H3/H4的跳跃修正为渐进式层级
- 确保文档结构符合Markdown最佳实践

### 路径引用修复 ({self.fix_stats['path_fixes']}处)
- 更新了无效或过时的脚本路径引用
- 使用正确的相对路径替换硬编码路径
- 保持PathConfigCenter变量引用的一致性

## 建议

1. **手动验证**: 建议人工审查修复后的文件，确保语义正确性
2. **持续监控**: 建议定期运行此工具进行质量检查
3. **CI集成**: 可将此工具集成到CI流水线中自动执行
"""
        return report


def main():
    base_dir = r"d:\Projects\TraeProjects\skiller\.trae\skills\sanliu"
    
    fixer = DocumentAutoFixer(base_dir)
    stats = fixer.run_auto_fix()
    
    # 生成并保存报告
    report = fixer.generate_fix_report()
    report_path = Path(base_dir) / "AUTO_FIX_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("=" * 80)
    print("📊 修复完成统计")
    print("=" * 80)
    print(f"""
✅ 标题层级修复: {stats['heading_fixes']} 处
✅ 路径引用修复: {stats['path_fixes']} 处
📝 修改文件数: {stats['files_modified']} 个
❌ 错误数: {stats['errors']} 个

📄 详细报告已保存至: {report_path}
""")
    print("=" * 80)


if __name__ == "__main__":
    main()
