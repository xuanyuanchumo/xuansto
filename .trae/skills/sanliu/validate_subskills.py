#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
子技能文档验证工具
验证所有子技能文档的路径引用、格式和内容完整性
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class SubskillValidator:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "total_files": 0,
            "valid_files": 0,
            "invalid_files": 0,
            "warnings": 0,
            "details": []
        }
    
    def validate_all(self) -> Dict:
        """验证所有子技能文档"""
        print("开始验证子技能文档...")
        
        # 验证subskills目录
        subskills_path = self.base_path / "subskills"
        if subskills_path.exists():
            self._validate_directory(subskills_path, "subskills")
        
        # 验证三省目录
        for province in ["zhongshusheng", "menxiasheng", "shangshusheng"]:
            province_path = self.base_path / province
            if province_path.exists():
                self._validate_directory(province_path, province)
        
        # 验证六部目录
        shangshusheng_path = self.base_path / "shangshusheng"
        if shangshusheng_path.exists():
            for dept in ["bingbu", "gongbu", "hubu", "libu", "liibu", "xingbu"]:
                dept_path = shangshusheng_path / dept
                if dept_path.exists():
                    self._validate_directory(dept_path, f"shangshusheng/{dept}")
        
        # 生成摘要
        self._generate_summary()
        
        return self.results
    
    def _validate_directory(self, dir_path: Path, category: str):
        """验证目录中的所有MD文件"""
        for md_file in dir_path.glob("*.md"):
            if ".bak." in md_file.name:
                continue
            
            self.results["total_files"] += 1
            file_result = self._validate_file(md_file, category)
            
            if file_result["valid"]:
                self.results["valid_files"] += 1
            else:
                self.results["invalid_files"] += 1
            
            self.results["warnings"] += len(file_result.get("warnings", []))
            self.results["details"].append(file_result)
    
    def _validate_file(self, file_path: Path, category: str) -> Dict:
        """验证单个文件"""
        result = {
            "file": str(file_path.relative_to(self.base_path)),
            "category": category,
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查YAML前置信息
            if not content.startswith('---'):
                result["warnings"].append("缺少YAML前置信息")
            
            # 检查name字段
            if 'name:' not in content[:200]:
                result["warnings"].append("缺少name字段")
            
            # 检查description字段
            if 'description:' not in content[:200]:
                result["warnings"].append("缺少description字段")
            
            # 检查路径引用
            path_refs = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', content)
            for text, path in path_refs:
                if path.startswith('http') or path.startswith('#'):
                    continue
                
                # 检查相对路径
                if not path.startswith('/'):
                    ref_path = file_path.parent / path
                    if not ref_path.exists():
                        result["warnings"].append(f"路径引用不存在: {path}")
            
            # 检查MD格式
            if '```' in content:
                code_blocks = content.count('```')
                if code_blocks % 2 != 0:
                    result["errors"].append("代码块未正确闭合")
                    result["valid"] = False
            
            # 检查表格格式
            tables = re.findall(r'\|[^\n]+\|', content)
            for table in tables:
                if table.count('|') < 2:
                    result["warnings"].append("表格格式可能有问题")
        
        except Exception as e:
            result["errors"].append(f"读取文件失败: {str(e)}")
            result["valid"] = False
        
        return result
    
    def _generate_summary(self):
        """生成验证摘要"""
        print(f"\n验证完成!")
        print(f"总文件数: {self.results['total_files']}")
        print(f"有效文件: {self.results['valid_files']}")
        print(f"无效文件: {self.results['invalid_files']}")
        print(f"警告数量: {self.results['warnings']}")
    
    def save_report(self, output_path: str):
        """保存验证报告"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n验证报告已保存: {output_file}")

def main():
    base_path = Path(__file__).parent
    validator = SubskillValidator(str(base_path))
    
    results = validator.validate_all()
    
    output_path = base_path / "reports" / "subskill_validation_report.json"
    validator.save_report(str(output_path))
    
    if results["invalid_files"] > 0:
        print("\n发现无效文件，请检查详细报告")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
