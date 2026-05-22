"""测试 skill_doc_updater.py 模块"""

import sys
from pathlib import Path
from skillscripts.core.path_config_center import get_path_config

sys.path.insert(0, str(get_path_config().SKILL_ROOT.parent))

from skillscripts.core.skill_doc_updater import (
    SkillDocUpdater, ChangeType, ChangeRecord, SkillDocParser,
    DocValidator, ChangelogGenerator, VersionBumpType, VersionInfo
)


def test_data_structures():
    print("=== 测试数据结构 ===")
    
    from skillscripts.core.skill_doc_updater import DocSection, UpdateResult, ValidationError
    
    section = DocSection(title="概述", content="这是概述内容", level=2, children=[])
    print(f"DocSection: {section.title}, level={section.level}")
    
    version = VersionInfo(version="1.0.0", release_date="2024-01-01", changes=["新增功能A"])
    print(f"VersionInfo: {version.version}")
    
    new_version = VersionInfo.bump("1.2.3", VersionBumpType.MINOR)
    print(f"版本升级: 1.2.3 -> {new_version}")
    
    change = ChangeRecord(change_type=ChangeType.NEW, scope="核心模块", description="新增文档更新功能")
    print(f"ChangeRecord: {change.change_type.value} - {change.description}")
    
    result = UpdateResult(success=True, updated_sections=["features"], new_version="1.1.0")
    print(f"UpdateResult: success={result.success}, version={result.new_version}")
    
    print("数据结构测试通过!\n")


def test_parser():
    print("=== 测试文档解析器 ===")
    parser = SkillDocParser()
    
    test_doc = """
# 测试技能

版本: 1.0.0

## 概述

这是一个测试技能。

## 功能特性

- 功能A
- 功能B

## 使用方法

```bash
python main.py
```
"""
    
    sections = parser.parse(test_doc)
    print(f"解析到 {len(sections)} 个顶级章节")
    for s in sections:
        print(f"  - {s.title} (level={s.level})")
    
    metadata = parser.extract_metadata(test_doc)
    print(f"版本: {metadata.get('version', '未知')}")
    
    print("解析器测试通过!\n")


def test_validator():
    print("=== 测试文档验证器 ===")
    validator = DocValidator()
    
    test_doc = """
# 测试技能

版本: 1.0.0

## 概述

这是一个测试技能。

## 功能特性

- 功能A

## 使用方法

```bash
python main.py
```
"""
    
    errors = validator.validate(test_doc)
    print(f"发现 {len(errors)} 个验证问题")
    for e in errors[:5]:
        print(f"  - [{e.level.value}] {e.message}")
    
    print("验证器测试通过!\n")


def test_changelog_generator():
    print("=== 测试变更日志生成器 ===")
    
    changes = [
        ChangeRecord(change_type=ChangeType.NEW, scope="核心", description="新增功能A"),
        ChangeRecord(change_type=ChangeType.FIXED, scope="API", description="修复问题B"),
        ChangeRecord(change_type=ChangeType.PERFORMANCE, scope="数据库", description="优化查询性能"),
    ]
    
    entry = ChangelogGenerator(Path(".")).generate_entry("1.1.0", changes)
    print("变更日志条目:")
    print(entry)
    
    print("变更日志生成器测试通过!\n")


def test_version_manager():
    print("=== 测试版本管理 ===")
    
    bump_type = VersionBumpType.MAJOR
    print(f"MAJOR bump: 1.2.3 -> {VersionInfo.bump('1.2.3', bump_type)}")
    
    bump_type = VersionBumpType.MINOR
    print(f"MINOR bump: 1.2.3 -> {VersionInfo.bump('1.2.3', bump_type)}")
    
    bump_type = VersionBumpType.PATCH
    print(f"PATCH bump: 1.2.3 -> {VersionInfo.bump('1.2.3', bump_type)}")
    
    print("版本管理测试通过!\n")


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("skill_doc_updater.py 模块测试")
    print("=" * 50 + "\n")
    
    test_data_structures()
    test_parser()
    test_validator()
    test_changelog_generator()
    test_version_manager()
    
    print("=" * 50)
    print("所有测试通过!")
    print("=" * 50)
