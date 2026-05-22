# -*- coding: utf-8 -*-
"""
三省六部技能文档质量检查工具
功能：
1. 检测所有.md文件的编码格式（UTF-8无BOM）
2. 检测BOM标记
3. 检测乱码字符
4. 检测Markdown格式问题
5. 提取并验证脚本路径引用
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class DocumentQualityChecker:
    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.subskills_dir = self.base_dir / "subskills"
        self.skill_md_path = self.base_dir / "SKILL.md"
        self.skillscripts_dir = self.base_dir / "skillscripts"
        
        # 存储检测结果
        self.encoding_results = {}
        self.format_issues = []
        self.script_references = []
        self.path_validation_results = []
    
    def detect_file_encoding(self, file_path: Path) -> Dict:
        """检测文件编码"""
        result = {
            'file': str(file_path),
            'encoding': None,
            'has_bom': False,
            'is_utf8': True,
            'error': None,
            'file_size': 0
        }
        
        try:
            result['file_size'] = file_path.stat().st_size
            
            with open(file_path, 'rb') as f:
                raw = f.read(4)
                
                # 检测BOM
                if raw.startswith(b'\xef\xbb\xbf'):
                    result['has_bom'] = True
                    result['encoding'] = 'UTF-8-BOM'
                elif raw.startswith(b'\xff\xfe'):
                    result['encoding'] = 'UTF-16-LE'
                    result['is_utf8'] = False
                elif raw.startswith(b'\xfe\xff'):
                    result['encoding'] = 'UTF-16-BE'
                    result['is_utf8'] = False
                else:
                    result['encoding'] = 'UTF-8'
                
                # 读取全部内容验证是否为有效UTF-8
                f.seek(0)
                content = f.read()
                try:
                    content.decode('utf-8')
                except UnicodeDecodeError as e:
                    result['is_utf8'] = False
                    result['error'] = f"非UTF-8编码: {str(e)}"
                    
        except Exception as e:
            result['error'] = str(e)
            result['is_utf8'] = False
            
        return result
    
    def check_garbled_characters(self, file_path: Path) -> List[Dict]:
        """检测乱码字符"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # 检测不可打印字符（排除常见空白字符）
                    for char_pos, char in enumerate(line):
                        if ord(char) > 127 and not (char.isprintable() or char in '\n\r\t'):
                            if ord(char) < 32 or ord(char) > 126:  # 控制字符或特殊字符
                                if char not in '\n\r\t':
                                    issues.append({
                                        'line': line_num,
                                        'pos': char_pos + 1,
                                        'char': repr(char),
                                        'char_code': ord(char),
                                        'type': '不可打印字符',
                                        'context': line[max(0, char_pos-20):char_pos+20]
                                    })
                    
                    # 检测常见的乱码模式
                    garbled_patterns = [
                        r'ï¿½',  # 常见乱码
                        r'Ã[Â][©®]',  # Latin-1到UTF-8转换错误
                        r'ä»€',  # GBK/GB2312到UTF-8转换错误
                        r'æ–‡',  # 另一种乱码
                        r'â€™',  # 引号乱码
                        r'â€œ',  # 左引号乱码
                        r'â€',  # 右引号乱码
                        r'â€"',  # 破折号乱码
                    ]
                    
                    for pattern in garbled_patterns:
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            issues.append({
                                'line': line_num,
                                'pos': match.start() + 1,
                                'char': match.group(),
                                'char_code': None,
                                'type': '乱码字符',
                                'context': line[max(0, match.start()-20):match.end()+20]
                            })
                    
                    # 检测连续的问号（可能表示解码失败）
                    if '???' in line or '????' in line:
                        issues.append({
                            'line': line_num,
                            'pos': line.index('???') + 1 if '???' in line else line.index('????') + 1,
                            'char': '???',
                            'char_code': None,
                            'type': '可疑连续问号',
                            'context': line
                        })
                        
        except Exception as e:
            issues.append({
                'line': 0,
                'pos': 0,
                'char': '',
                'char_code': None,
                'type': '读取错误',
                'context': str(e)
            })
            
        return issues
    
    def check_markdown_format(self, file_path: Path) -> List[Dict]:
        """检查Markdown格式问题"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                # 检查标题层级
                prev_heading_level = 0
                for line_num, line in enumerate(lines, 1):
                    stripped = line.strip()
                    
                    # 标题层级检查
                    if stripped.startswith('#'):
                        heading_match = re.match(r'^(#{1,6})\s', stripped)
                        if heading_match:
                            current_level = len(heading_match.group(1))
                            
                            # 检查标题跳跃（超过一级）
                            if prev_heading_level > 0 and current_level > prev_heading_level + 1:
                                issues.append({
                                    'line': line_num,
                                    'type': '标题层级跳跃',
                                    'severity': 'warning',
                                    'detail': f"从H{prev_heading_level}跳到H{current_level}",
                                    'content': stripped[:80]
                                })
                                
                            prev_heading_level = current_level
                    
                    # 表格格式检查
                    if '|' in stripped and '---' in stripped:
                        # 检查表格分隔符
                        if not re.match(r'^[\s|:-]+$', stripped):
                            col_count = stripped.count('|')
                            # 检查相邻行列数是否一致
                            if line_num > 1:
                                prev_line = lines[line_num - 2] if line_num >= 2 else ''
                                if '|' in prev_line:
                                    prev_cols = prev_line.count('|')
                                    if abs(col_count - prev_cols) > 1:
                                        issues.append({
                                            'line': line_num,
                                            'type': '表格列数不一致',
                                            'severity': 'error',
                                            'detail': f"当前{col_count}列，前一行{prev_cols}列",
                                            'content': stripped[:80]
                                        })
                    
                    # 代码块检查
                    if stripped.startswith('```'):
                        code_block_start = line_num
                        # 寻找结束标记
                        found_end = False
                        for i in range(line_num, min(line_num + 100, len(lines))):
                            if lines[i].strip() == '```' and i != line_num - 1:
                                found_end = True
                                break
                        
                        if not found_end and line_num == len(lines) - len(lines[line_num:]) + sum(1 for l in lines[line_num:] if l.strip().startswith('```')):
                            pass  # 可能是文件末尾
                    
                    # 链接格式检查
                    link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
                    for match in re.finditer(link_pattern, stripped):
                        link_text = match.group(1)
                        link_url = match.group(2)
                        
                        # 检查空链接文本
                        if not link_text.strip():
                            issues.append({
                                'line': line_num,
                                'type': '空链接文本',
                                'severity': 'warning',
                                'detail': f"链接URL: {link_url}",
                                'content': stripped[:80]
                            })
                        
                        # 检查空链接URL
                        if not link_url.strip():
                            issues.append({
                                'line': line_num,
                                'type': '空链接URL',
                                'severity': 'error',
                                'detail': f"链接文本: {link_text}",
                                'content': stripped[:80]
                            })
                    
                    # 图片链接检查
                    img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
                    for match in re.finditer(img_pattern, stripped):
                        alt_text = match.group(1)
                        img_url = match.group(2)
                        
                        # 检查图片是否存在（相对路径）
                        if not img_url.startswith(('http://', 'https://', 'data:')):
                            img_path = file_path.parent / img_url
                            if not img_path.exists():
                                issues.append({
                                    'line': line_num,
                                    'type': '图片路径不存在',
                                    'severity': 'warning',
                                    'detail': f"路径: {img_url}",
                                    'content': stripped[:80]
                                })
                                
        except Exception as e:
            issues.append({
                'line': 0,
                'type': '读取错误',
                'severity': 'error',
                'detail': str(e),
                'content': ''
            })
            
        return issues
    
    def extract_script_references(self, file_path: Path) -> List[Dict]:
        """提取脚本路径引用"""
        references = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    # 匹配各种脚本路径格式
                    patterns = [
                        # python skillscripts/xxx.py
                        (r'(?:python|python3)\s+([^\s`]+\.(?:py|sh|bat|ps1))', '命令行调用'),
                        # `skillscripts/xxx.py`
                        (r'`([^`]*\.(?:py|sh|bat|ps1)[^`]*)`', '代码块引用'),
                        # skillscripts/xxx.py (不在代码块中)
                        (r'(?<!`)(skillscripts[\\/][^\s`]*\.(?:py|sh|bat|ps1))', '直接路径'),
                        # ${SCRIPTS_DIR}/xxx.py 或其他变量
                        (r'\$\{[^}]+\}[\\/]*([^\s`]*\.(?:py|sh|bat|ps1))', '动态路径变量'),
                        # 相对路径 ../scripts/xxx.py
                        (r'\.\.[\\/](?:scripts?|skillscripts)[\\/][^\s`]*\.(?:py|sh|bat|ps1)', '相对路径'),
                    ]
                    
                    for pattern, ref_type in patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            ref_path = match.group(1) if '${' not in pattern else match.group(0)
                            
                            references.append({
                                'file': file_path.name,
                                'line': line_num,
                                'reference': ref_path,
                                'type': ref_type,
                                'full_line': line.strip()[:100],
                                'uses_variable': '${' in match.group(0) if '${' in pattern else False
                            })
                        
        except Exception as e:
            print(f"  ⚠️  提取脚本引用时出错 {file_path.name}: {e}")
            
        return references
    
    def validate_script_path(self, reference: Dict) -> Dict:
        """验证脚本路径"""
        result = {
            **reference,
            'exists': False,
            'accessible': False,
            'suggested_fix': None,
            'issue_type': None
        }
        
        ref_path = reference['reference']
        
        # 处理动态路径变量
        if reference.get('uses_variable', False):
            result['exists'] = True  # 动态路径假设存在
            result['accessible'] = True
            result['issue_type'] = 'dynamic_path'
            return result
        
        # 尝试多种基础路径组合
        possible_paths = [
            self.base_dir / ref_path,
            self.base_dir / "skillscripts" / Path(ref_path).name,
            self.skillscripts_dir / ref_path.replace('skillscripts/', '').replace('skillscripts\\', ''),
        ]
        
        # 如果是相对路径，尝试相对于不同位置解析
        if ref_path.startswith('../') or ref_path.startswith('..\\'):
            from pathlib import Path as P
            ref_file = self.base_dir / reference['file']
            possible_paths.insert(0, (ref_file.parent / ref_path).resolve())
        
        for path in possible_paths:
            if path.exists():
                result['exists'] = True
                try:
                    # 测试可读性
                    with open(path, 'r', encoding='utf-8') as f:
                        f.read(1024)
                    result['accessible'] = True
                except Exception:
                    result['accessible'] = False
                break
        
        if not result['exists']:
            result['issue_type'] = 'path_not_found'
            
            # 生成建议修复
            filename = Path(ref_path).name
            similar_files = list(self.skillscripts_dir.rglob(f"*{filename}*"))
            if similar_files:
                rel_path = similar_files[0].relative_to(self.base_dir)
                result['suggested_fix'] = str(rel_path).replace('\\', '/')
            else:
                result['suggested_fix'] = f"请确认路径或使用 ${{SCRIPTS_DIR}}/{filename}"
        
        return result
    
    def run_full_check(self) -> Dict:
        """运行完整检查"""
        print("=" * 80)
        print("📋 三省六部技能文档质量检查报告")
        print("=" * 80)
        print(f"\n📁 技能根目录: {self.base_dir}")
        print(f"📂 子技能目录: {self.subskills_dir}")
        print(f"📜 SKILL.md: {self.skill_md_path}")
        print(f"💻 脚本目录: {self.skillscripts_dir}\n")
        
        all_md_files = []
        
        # 收集所有.md文件
        if self.skill_md_path.exists():
            all_md_files.append(self.skill_md_path)
        
        if self.subskills_dir.exists():
            all_md_files.extend(self.subskills_dir.glob("*.md"))
        
        total_files = len(all_md_files)
        print(f"🔍 发现 {total_files} 个.md文件待检查\n")
        
        # 统计数据
        stats = {
            'total_files': total_files,
            'utf8_compliant': 0,
            'with_bom': 0,
            'encoding_errors': 0,
            'garbled_files': 0,
            'total_garbled_chars': 0,
            'format_issues': 0,
            'script_refs': 0,
            'valid_paths': 0,
            'invalid_paths': 0,
            'dynamic_paths': 0,
            'hardcoded_paths': 0,
        }
        
        # Part 1: 编码和格式检查
        print("-" * 80)
        print("📊 Part 1: 文件编码与格式检查")
        print("-" * 80)
        
        for idx, md_file in enumerate(sorted(all_md_files), 1):
            relative_path = md_file.relative_to(self.base_dir)
            print(f"\n[{idx}/{total_files}] 📄 {relative_path}")
            
            # 1.1 编码检测
            enc_result = self.detect_file_encoding(md_file)
            self.encoding_results[str(relative_path)] = enc_result
            
            if enc_result['is_utf8']:
                stats['utf8_compliant'] += 1
                bom_status = "⚠️ 有BOM" if enc_result['has_bom'] else "✅ UTF-8无BOM"
                print(f"   编码: {enc_result['encoding']} | {bom_status} | 大小: {enc_result['file_size']} bytes")
                
                if enc_result['has_bom']:
                    stats['with_bom'] += 1
            else:
                stats['encoding_errors'] += 1
                print(f"   ❌ 编码错误: {enc_result.get('error', '未知错误')}")
            
            # 1.2 乱码检测
            garbled = self.check_garbled_characters(md_file)
            if garbled:
                stats['garbled_files'] += 1
                stats['total_garbled_chars'] += len(garbled)
                print(f"   ⚠️  发现 {len(garbled)} 个乱码/异常字符:")
                for issue in garbled[:5]:  # 只显示前5个
                    print(f"      行{issue['line']}: [{issue['type']}] {issue.get('char', '')} - {issue.get('context', '')[:50]}")
                if len(garbled) > 5:
                    print(f"      ... 还有 {len(garbled) - 5} 个问题")
            
            # 1.3 格式检测
            format_issues = self.check_markdown_format(md_file)
            if format_issues:
                stats['format_issues'] += len(format_issues)
                self.format_issues.extend([{**issue, 'file': str(relative_path)} for issue in format_issues])
                print(f"   ⚠️  发现 {len(format_issues)} 个格式问题:")
                for issue in format_issues[:3]:  # 只显示前3个
                    print(f"      行{issue['line']}: [{issue['type']}] {issue.get('detail', '')} - {issue.get('content', '')[:60]}")
                if len(format_issues) > 3:
                    print(f"      ... 还有 {len(format_issues) - 3} 个问题")
            
            # 2. 脚本路径提取
            refs = self.extract_script_references(md_file)
            if refs:
                stats['script_refs'] += len(refs)
                self.script_references.extend(refs)
                print(f"   🔗 发现 {len(refs)} 个脚本路径引用")
        
        # Part 2: 路径验证
        print("\n" + "-" * 80)
        print("🔗 Part 2: 脚本路径引用验证")
        print("-" * 80)
        
        print(f"\n共发现 {stats['script_refs']} 个脚本路径引用，正在验证...\n")
        
        for ref in self.script_references:
            validation = self.validate_script_path(ref)
            self.path_validation_results.append(validation)
            
            if validation['exists']:
                stats['valid_paths'] += 1
                if validation.get('issue_type') == 'dynamic_path':
                    stats['dynamic_paths'] += 1
                else:
                    stats['hardcoded_paths'] += 1
            else:
                stats['invalid_paths'] += 1
                stats['hardcoded_paths'] += 1
        
        # 输出统计摘要
        print("\n" + "=" * 80)
        print("📈 检查结果统计")
        print("=" * 80)
        
        print(f"""
## 文件编码统计
- 总文件数: {stats['total_files']}
- ✅ UTF-8合规: {stats['utf8_compliant']} ({stats['utf8_compliant']/stats['total_files']*100:.1f}%)
- ⚠️  含BOM: {stats['with_bom']} ({stats['with_bom']/stats['total_files']*100:.1f}%)
- ❌ 编码错误: {stats['encoding_errors']} ({stats['encoding_errors']/stats['total_files']*100:.1f}%)

## 内容质量统计
- 🔤 乱码文件: {stats['garbled_files']} (含{stats['total_garbled_chars']}个异常字符)
- 📝 格式问题: {stats['format_issues']} 处

## 脚本路径统计
- 总引用数: {stats['script_refs']}
- ✅ 有效路径: {stats['valid_paths']} ({stats['valid_paths']/max(stats['script_refs'],1)*100:.1f}%)
- ❌ 无效路径: {stats['invalid_paths']} ({stats['invalid_paths']/max(stats['script_refs'],1)*100:.1f}%)
- 🔀 使用PathConfigCenter: {stats['dynamic_paths']} ({stats['dynamic_paths']/max(stats['script_refs'],1)*100:.1f}%)
- 🔒 硬编码路径: {stats['hardcoded_paths']} ({stats['hardcoded_paths']/max(stats['script_refs'],1)*100:.1f}%)
""")
        
        return {
            'stats': stats,
            'encoding_results': self.encoding_results,
            'format_issues': self.format_issues,
            'script_references': self.script_references,
            'path_validation': self.path_validation_results
        }
    
    def generate_report(self, results: Dict) -> str:
        """生成Markdown格式报告"""
        stats = results['stats']
        
        report = []
        report.append("# 三省六部技能文档质量检查报告\n")
        report.append(f"> 检查时间: 自动生成\n")
        report.append(f"> 检查范围: 所有.md文档及脚本路径引用\n\n")
        
        # 第一部分：编码检测结果
        report.append("---\n\n")
        report.append("# Part 1: 文件编码检测结果\n\n")
        report.append("## 统计信息\n\n")
        report.append(f"| 项目 | 数量 | 占比 |\n")
        report.append(f"|------|------|------|\n")
        report.append(f"| 总文件数 | {stats['total_files']} | 100% |\n")
        report.append(f"| UTF-8合规 | {stats['utf8_compliant']} | {stats['utf8_compliant']/max(stats['total_files'],1)*100:.1f}% |\n")
        report.append(f"| 含BOM标记 | {stats['with_bom']} | {stats['with_bom']/max(stats['total_files'],1)*100:.1f}% |\n")
        report.append(f"| 编码错误 | {stats['encoding_errors']} | {stats['encoding_errors']/max(stats['total_files'],1)*100:.1f}% |\n\n")
        
        report.append("## 各文件编码状态\n\n")
        report.append("| 文件名 | 编码 | BOM | 状态 | 文件大小 |\n")
        report.append("|--------|------|-----|------|----------|\n")
        
        for path, enc_data in sorted(results['encoding_results'].items()):
            status = "✅" if enc_data['is_utf8'] else "❌"
            bom = "有" if enc_data['has_bom'] else "无"
            report.append(f"| `{path}` | {enc_data['encoding']} | {bom} | {status} | {enc_data['file_size']} bytes |\n")
        
        # 第二部分：格式问题清单
        if results['format_issues']:
            report.append("\n---\n\n")
            report.append("# Part 2: Markdown格式问题清单\n\n")
            report.append(f"共发现 **{stats['format_issues']}** 处格式问题\n\n")
            report.append("| 文件 | 行号 | 问题类型 | 严重程度 | 详情 | 内容预览 |\n")
            report.append("|------|------|----------|----------|------|----------|\n")
            
            for issue in results['format_issues']:
                severity_icon = "🔴" if issue['severity'] == 'error' else "🟡"
                preview = issue.get('content', '')[:40].replace('|', '\\|')
                report.append(f"| `{issue['file']}` | {issue['line']} | {issue['type']} | {severity_icon}{issue['severity']} | {issue.get('detail', '')} | {preview} |\n")
        
        # 第三部分：乱码问题
        garbled_files_count = stats['garbled_files']
        if garbled_files_count > 0:
            report.append("\n---\n\n")
            report.append("# Part 3: 乱码/异常字符问题\n\n")
            report.append(f"⚠️ 共 **{garbled_files_count}** 个文件包含乱码或异常字符（共{stats['total_garbled_chars']}处）\n\n")
            report.append("**建议**: 这些文件可能需要人工审查或重新保存为UTF-8编码\n")
        
        # 第四部分：路径引用验证报告
        report.append("\n---\n\n")
        report.append("# Part 4: 脚本路径引用验证报告\n\n")
        report.append("## 统计信息\n\n")
        report.append("| 项目 | 数量 | 占比 |\n")
        report.append("|------|------|------|\n")
        report.append(f"| 总引用数 | {stats['script_refs']} | 100% |\n")
        report.append(f"| ✅ 正确引用 | {stats['valid_paths']} | {stats['valid_paths']/max(stats['script_refs'],1)*100:.1f}% |\n")
        report.append(f"| ❌ 错误引用 | {stats['invalid_paths']} | {stats['invalid_paths']/max(stats['script_refs'],1)*100:.1f}% |\n")
        report.append(f"| 🔀 使用PathConfigCenter | {stats['dynamic_paths']} | {stats['dynamic_paths']/max(stats['script_refs'],1)*100:.1f}% |\n")
        report.append(f"| 🔒 硬编码路径 | {stats['hardcoded_paths']} | {stats['hardcoded_paths']/max(stats['script_refs'],1)*100:.1f}% |\n\n")
        
        # 错误引用列表
        invalid_refs = [r for r in results['path_validation'] if not r['exists']]
        if invalid_refs:
            report.append("## ❌ 错误引用列表\n\n")
            report.append("| 文件 | 行号 | 引用路径 | 问题类型 | 建议修复 |\n")
            report.append("|------|------|----------|----------|----------|\n")
            
            for ref in invalid_refs:
                suggested = ref.get('suggested_fix', '需要人工检查')
                report.append(f"| `{ref['file']}` | {ref['line']} | `{ref['reference']}` | {ref.get('issue_type', '未知')} | {suggested} |\n")
        
        # 硬编码路径列表
        hardcoded_refs = [r for r in results['path_validation'] 
                         if r['exists'] and not r.get('uses_variable', False)]
        if hardcoded_refs:
            report.append("\n## 🔒 硬编码路径列表（建议优化）\n\n")
            report.append("| 文件 | 行号 | 硬编码路径 | 建议替换为 |\n")
            report.append("|------|------|------------|------------|\n")
            
            for ref in hardcoded_refs[:20]:  # 限制显示数量
                filename = Path(ref['reference']).name
                suggested_var = "${SCRIPTS_DIR}/" + filename
                report.append(f"| `{ref['file']}` | {ref['line']} | `{ref['reference']}` | `{suggested_var}` |\n")
            
            if len(hardcoded_refs) > 20:
                report.append(f"\n*... 还有 {len(hardcoded_refs) - 20} 个硬编码路径未显示*\n")
        
        # 第五部分：总结和建议
        report.append("\n---\n\n")
        report.append("# Part 5: 总结与建议\n\n")
        
        overall_score = 100
        overall_score -= stats['encoding_errors'] * 10
        overall_score -= stats['with_bom'] * 2
        overall_score -= min(stats['format_issues'] * 0.5, 15)
        overall_score -= stats['invalid_paths'] * 5
        overall_score = max(0, min(100, overall_score))
        
        report.append(f"## 🎯 整体评分: {overall_score:.1f}/100\n\n")
        
        recommendations = []
        
        if stats['encoding_errors'] > 0:
            recommendations.append(f"- 🔴 **紧急**: {stats['encoding_errors']}个文件编码错误，需立即转换为UTF-8")
        
        if stats['with_bom'] > 0:
            recommendations.append(f"- 🟡 **重要**: {stats['with_bom']}个文件含有BOM标记，建议移除BOM以保持一致性")
        
        if stats['garbled_files'] > 0:
            recommendations.append(f"- 🟡 **重要**: {stats['garbled_files']}个文件可能存在乱码，需人工审核")
        
        if stats['format_issues'] > 10:
            recommendations.append(f"- 🟠 **建议**: 存在较多格式问题（{stats['format_issues']}处），建议统一修正")
        
        if stats['invalid_paths'] > 0:
            recommendations.append(f"- 🔴 **紧急**: {stats['invalid_paths']}个脚本路径无效，将导致功能失败")
        
        if stats['dynamic_paths'] < stats['script_refs'] * 0.3 and stats['script_refs'] > 0:
            usage_rate = stats['dynamic_paths']/max(stats['script_refs'],1)*100
            recommendations.append(f"- 🔵 **优化**: PathConfigCenter使用率仅{usage_rate:.1f}%，建议增加动态路径使用以提高可移植性")
        
        if not recommendations:
            recommendations.append("- ✅ **优秀**: 文档质量良好，未发现重大问题")
        
        report.append("### 改进建议\n\n")
        for rec in recommendations:
            report.append(f"{rec}\n")
        
        return "\n".join(report)


def main():
    base_dir = r"d:\Projects\TraeProjects\skiller\.trae\skills\sanliu"
    
    checker = DocumentQualityChecker(base_dir)
    results = checker.run_full_check()
    
    # 生成报告
    report = checker.generate_report(results)
    
    # 保存报告
    report_path = Path(base_dir) / "DOCUMENT_QUALITY_REPORT.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n✅ 完整报告已保存至: {report_path}")
    print(f"\n{'=' * 80}")


if __name__ == "__main__":
    main()
