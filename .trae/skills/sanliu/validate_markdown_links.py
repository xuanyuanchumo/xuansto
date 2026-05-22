#!/usr/bin/env python3
"""
Markdown链接验证工具
扫描所有.md文件，检查断裂的链接和代码块引用
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple, Set

class MarkdownLinkValidator:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.broken_links = []
        self.broken_code_refs = []
        self.orphan_subskills = []
        self.all_links = []
        self.existing_files = set()
        
    def scan_all_files(self):
        """扫描所有.md和.py文件"""
        print("正在扫描所有文件...")
        
        # 扫描所有.md文件
        for md_file in self.root_dir.rglob("*.md"):
            self.existing_files.add(md_file.relative_to(self.root_dir))
        
        # 扫描所有.py文件
        for py_file in self.root_dir.rglob("*.py"):
            self.existing_files.add(py_file.relative_to(self.root_dir))
            
        print(f"找到 {len(self.existing_files)} 个文件")
    
    def extract_markdown_links(self, content: str, file_path: Path) -> List[Dict]:
        """提取Markdown链接"""
        # 匹配 [text](url) 格式的链接
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        links = []
        
        for match in re.finditer(pattern, content):
            text = match.group(1)
            url = match.group(2)
            
            # 跳过外部链接、锚点链接、file:///链接
            if url.startswith(('http://', 'https://', '#', 'file:///')):
                continue
                
            links.append({
                'text': text,
                'url': url,
                'line': content[:match.start()].count('\n') + 1,
                'file': file_path
            })
        
        return links
    
    def extract_code_refs(self, content: str, file_path: Path) -> List[Dict]:
        """提取代码块引用"""
        # 匹配 ```language\npath 格式的代码块引用
        pattern = r'```[\w]*\n([^\n]+\.(py|js|ts|vue|json))\n```'
        refs = []
        
        for match in re.finditer(pattern, content):
            path = match.group(1)
            refs.append({
                'path': path,
                'line': content[:match.start()].count('\n') + 1,
                'file': file_path
            })
        
        return refs
    
    def validate_link(self, link: Dict) -> bool:
        """验证链接是否有效"""
        source_file = link['file']
        url = link['url']
        
        # 处理相对路径
        if url.startswith('../'):
            # 计算目标路径
            target_path = (source_file.parent / url).resolve()
            try:
                target_rel = target_path.relative_to(self.root_dir)
                return target_rel in self.existing_files
            except ValueError:
                return False
        elif url.startswith('./') or not url.startswith('/'):
            # 相对于当前文件的路径
            target_path = (source_file.parent / url).resolve()
            try:
                target_rel = target_path.relative_to(self.root_dir)
                return target_rel in self.existing_files
            except ValueError:
                return False
        
        return True
    
    def validate_code_ref(self, ref: Dict) -> bool:
        """验证代码引用是否有效"""
        source_file = ref['file']
        path = ref['path']
        
        # 计算目标路径
        target_path = (source_file.parent / path).resolve()
        try:
            target_rel = target_path.relative_to(self.root_dir)
            return target_rel in self.existing_files
        except ValueError:
            return False
    
    def scan_file(self, md_file: Path):
        """扫描单个.md文件"""
        try:
            content = md_file.read_text(encoding='utf-8')
            
            # 提取并验证Markdown链接
            links = self.extract_markdown_links(content, md_file)
            for link in links:
                self.all_links.append(link)
                if not self.validate_link(link):
                    self.broken_links.append(link)
            
            # 提取并验证代码引用
            refs = self.extract_code_refs(content, md_file)
            for ref in refs:
                if not self.validate_code_ref(ref):
                    self.broken_code_refs.append(ref)
                    
        except Exception as e:
            print(f"处理文件 {md_file} 时出错: {e}")
    
    def find_orphan_subskills(self):
        """查找孤儿子技能（未被引用的子技能）"""
        print("\n正在查找孤儿子技能...")
        
        # 获取所有子技能文件
        subskill_dir = self.root_dir / "subskills"
        if not subskill_dir.exists():
            print("未找到subskills目录")
            return
        
        all_subskills = set()
        for subskill_file in subskill_dir.glob("*.md"):
            all_subskills.add(subskill_file.name)
        
        # 获取所有被引用的子技能
        referenced_subskills = set()
        for link in self.all_links:
            if 'subskills/' in link['url']:
                # 提取子技能文件名
                parts = link['url'].split('subskills/')
                if len(parts) > 1:
                    subskill_name = parts[1].split('#')[0]  # 去除锚点
                    referenced_subskills.add(subskill_name)
        
        # 找出孤儿子技能
        self.orphan_subskills = list(all_subskills - referenced_subskills)
    
    def scan_all_markdown_files(self):
        """扫描所有.md文件"""
        print("\n正在扫描所有Markdown文件...")
        
        md_files = list(self.root_dir.rglob("*.md"))
        print(f"找到 {len(md_files)} 个Markdown文件")
        
        for md_file in md_files:
            self.scan_file(md_file)
    
    def generate_report(self) -> Dict:
        """生成验证报告"""
        report = {
            'summary': {
                'total_files_scanned': len(list(self.root_dir.rglob("*.md"))),
                'total_links_found': len(self.all_links),
                'broken_links_count': len(self.broken_links),
                'broken_code_refs_count': len(self.broken_code_refs),
                'orphan_subskills_count': len(self.orphan_subskills)
            },
            'broken_links': [
                {
                    'file': str(link['file'].relative_to(self.root_dir)),
                    'line': link['line'],
                    'text': link['text'],
                    'url': link['url']
                }
                for link in self.broken_links
            ],
            'broken_code_refs': [
                {
                    'file': str(ref['file'].relative_to(self.root_dir)),
                    'line': ref['line'],
                    'path': ref['path']
                }
                for ref in self.broken_code_refs
            ],
            'orphan_subskills': self.orphan_subskills
        }
        
        return report
    
    def print_report(self, report: Dict):
        """打印报告"""
        print("\n" + "="*80)
        print("Markdown链接验证报告")
        print("="*80)
        
        print(f"\n📊 扫描统计:")
        print(f"  - 扫描文件数: {report['summary']['total_files_scanned']}")
        print(f"  - 发现链接数: {report['summary']['total_links_found']}")
        print(f"  - 断裂链接数: {report['summary']['broken_links_count']}")
        print(f"  - 断裂代码引用数: {report['summary']['broken_code_refs_count']}")
        print(f"  - 孤儿子技能数: {report['summary']['orphan_subskills_count']}")
        
        if report['broken_links']:
            print(f"\n❌ 断裂的Markdown链接 ({len(report['broken_links'])}个):")
            for i, link in enumerate(report['broken_links'][:20], 1):  # 只显示前20个
                print(f"  {i}. [{link['file']}:{link['line']}] [{link['text']}]({link['url']})")
            if len(report['broken_links']) > 20:
                print(f"  ... 还有 {len(report['broken_links']) - 20} 个断裂链接")
        
        if report['broken_code_refs']:
            print(f"\n❌ 断裂的代码引用 ({len(report['broken_code_refs'])}个):")
            for i, ref in enumerate(report['broken_code_refs'][:10], 1):
                print(f"  {i}. [{ref['file']}:{ref['line']}] {ref['path']}")
        
        if report['orphan_subskills']:
            print(f"\n⚠️  孤儿子技能 ({len(report['orphan_subskills'])}个):")
            for i, subskill in enumerate(report['orphan_subskills'], 1):
                print(f"  {i}. {subskill}")
        
        print("\n" + "="*80)

def main():
    root_dir = Path(__file__).parent
    
    validator = MarkdownLinkValidator(str(root_dir))
    
    # 扫描所有文件
    validator.scan_all_files()
    
    # 扫描所有Markdown文件
    validator.scan_all_markdown_files()
    
    # 查找孤儿子技能
    validator.find_orphan_subskills()
    
    # 生成报告
    report = validator.generate_report()
    
    # 打印报告
    validator.print_report(report)
    
    # 保存JSON报告
    report_file = root_dir / "link_validation_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 详细报告已保存到: {report_file}")
    
    return report

if __name__ == "__main__":
    main()
