#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""最终语法验证"""
import py_compile
from pathlib import Path

SKILLSCRIPTS_DIR = Path(r'd:\Projects\TraeProjects\skiller\.trae\skills\sanliu\skillscripts')

errors = []
success_count = 0

for f in sorted(SKILLSCRIPTS_DIR.rglob('*.py')):
    if f.name == 'path_config_center.py' or '__pycache__' in str(f):
        continue
    
    try:
        py_compile.compile(str(f), doraise=True)
        success_count += 1
    except py_compile.PyCompileError as e:
        errors.append(str(f.relative_to(SKILLSCRIPTS_DIR)))

print("=" * 80)
print("Final Syntax Validation Report")
print("=" * 80)
print(f"Total files validated: {success_count + len(errors)}")
print(f"Files passed: {success_count}")
print(f"Files with errors: {len(errors)}")

if errors:
    print("\nFiles with syntax errors:")
    for err in errors:
        print(f"  [ERROR] {err}")
else:
    print("\n[SUCCESS] All files passed syntax validation!")

print("=" * 80)
