#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化的嵌套分析脚本

分析Python代码的嵌套层级，识别过深的嵌套结构。

使用示例:
    python simple_nesting_check.py              # 分析后端代码
    python simple_nesting_check.py --max 4      # 设置最大嵌套深度为4
    python simple_nesting_check.py --json       # JSON 格式输出
    python simple_nesting_check.py --all        # 分析所有代码

退出码:
    0 - 成功（无深层嵌套）
    1 - 错误（存在深层嵌套）
"""

import os
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any

from skillscripts.utils.script_utils import (
    ScriptBase, ScriptResult, ScriptLogger, ExitCode, create_result
)


@dataclass
class NestingIssue:
    file: str
    line: int
    level: int
    code: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "file": self.file,
            "line": self.line,
            "level": self.level,
            "code": self.code
        }


class SimpleNestingCheckScript(ScriptBase):
    DEFAULT_DESCRIPTION = "简化的嵌套分析脚本"
    DEFAULT_EPILOG = """
示例:
  python simple_nesting_check.py              # 分析后端代码
  python simple_nesting_check.py --max 4      # 设置最大嵌套深度为4
  python simple_nesting_check.py --json       # JSON 格式输出
  python simple_nesting_check.py --all        # 分析所有代码

退出码:
  0 - 成功（无深层嵌套）
  1 - 错误（存在深层嵌套）
"""
    
    def _add_arguments(self):
        self.parser.add_argument(
            "--max",
            type=int,
            default=3,
            help="最大允许嵌套深度 (默认: 3)"
        )
        self.parser.add_argument(
            "--all",
            action="store_true",
            help="分析所有代码（包括前端和脚本）"
        )
    
    def analyze_python_file(self, file_path: str, max_depth: int) -> List[NestingIssue]:
        issues = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception:
            return issues
        
        for line_num, line in enumerate(lines, 1):
            indent = len(line) - len(line.lstrip())
            nesting_level = indent // 4
            
            control_keywords = ['if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 'try:', 'except ']
            for keyword in control_keywords:
                if keyword in line and nesting_level > max_depth:
                    issues.append(NestingIssue(
                        file=file_path,
                        line=line_num,
                        level=nesting_level,
                        code=line.strip()[:80]
                    ))
                    break
        
        return issues
    
    def run(self) -> int:
        base_dir = Path(__file__).parent.parent
        all_issues: List[NestingIssue] = []
        files_scanned = 0
        
        directories = [base_dir / "backend"]
        if self.args.all:
            directories.extend([
                base_dir / "frontend" / "src",
                base_dir / "scripts"
            ])
        
        for directory in directories:
            if not directory.exists():
                continue
            
            for py_file in directory.rglob("*.py"):
                if "__pycache__" in str(py_file) or ".pytest_cache" in str(py_file):
                    continue
                files_scanned += 1
                issues = self.analyze_python_file(str(py_file), self.args.max)
                all_issues.extend(issues)
        
        success = len(all_issues) == 0
        
        if success:
            message = f"所有代码的嵌套层级都符合要求（≤{self.args.max}层）"
            self.logger.success(message)
        else:
            message = f"发现 {len(all_issues)} 处深层嵌套问题（>{self.args.max}层）"
            self.logger.warning(message)
        
        result = create_result(
            success=success,
            message=message,
            data={
                "files_scanned": files_scanned,
                "max_depth": self.args.max,
                "issues_count": len(all_issues),
                "issues": [i.to_dict() for i in all_issues[:50]]
            },
            warnings=[f"{i.file}:{i.line} (层级:{i.level})" for i in all_issues[:10]],
            duration_ms=self.get_duration_ms()
        )
        
        if self.args.json:
            self.output_json(result)
        elif self.args.markdown:
            self.output_markdown(result)
        else:
            self.output_console(result)
            
            if all_issues:
                print("\n深层嵌套位置:")
                for issue in all_issues[:20]:
                    print(f"  {issue.file}:{issue.line} (层级:{issue.level})")
                    print(f"    {issue.code}\n")
        
        return ExitCode.EXIT_CODE_SUCCESS.value if success else ExitCode.EXIT_CODE_ERROR.value


def main():
    script = SimpleNestingCheckScript()
    return script.execute()


if __name__ == "__main__":
    exit(main())
