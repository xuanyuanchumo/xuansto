import os
import re
import pytest
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import yaml


SKILL_ROOT = Path(__file__).parent.parent
SANLIU_ROOT = SKILL_ROOT


def find_all_skill_files(root_path: Path) -> List[Path]:
    skill_files = []
    for path in root_path.rglob("SKILL.md"):
        skill_files.append(path)
    return skill_files


def parse_yaml_frontmatter(content: str) -> Tuple[Optional[Dict], str]:
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)
    
    if match:
        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except yaml.YAMLError:
            return None, content
    
    return None, content


def get_expected_skill_files() -> List[str]:
    expected = [
        "SKILL.md",
        "zhongshusheng/SKILL.md",
        "menxiasheng/SKILL.md",
        "shangshusheng/SKILL.md",
        "shangshusheng/libu/SKILL.md",
        "shangshusheng/hubu/SKILL.md",
        "shangshusheng/liibu/SKILL.md",
        "shangshusheng/bingbu/SKILL.md",
        "shangshusheng/xingbu/SKILL.md",
        "shangshusheng/gongbu/SKILL.md",
    ]
    
    departments = ["libu", "hubu", "liibu", "bingbu", "xingbu", "gongbu"]
    for dept in departments:
        dept_path = SKILL_ROOT / "shangshusheng" / dept
        if dept_path.exists():
            for si_path in dept_path.iterdir():
                if si_path.is_dir() and (si_path / "SKILL.md").exists():
                    relative = si_path.relative_to(SKILL_ROOT)
                    expected.append(str(relative / "SKILL.md").replace("\\", "/"))
    
    return expected


class TestSkillStructure:
    
    def test_all_skill_files_exist(self):
        expected_files = get_expected_skill_files()
        missing_files = []
        
        for expected in expected_files:
            skill_path = SKILL_ROOT / expected
            if not skill_path.exists():
                missing_files.append(expected)
        
        assert len(missing_files) == 0, f"Missing SKILL.md files: {missing_files}"
    
    def test_yaml_frontmatter_format(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        invalid_files = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            frontmatter, body = parse_yaml_frontmatter(content)
            
            if frontmatter is None:
                relative_path = skill_file.relative_to(SKILL_ROOT)
                invalid_files.append(str(relative_path))
        
        assert len(invalid_files) == 0, f"Files with invalid YAML frontmatter: {invalid_files}"
    
    def test_required_fields_exist(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        missing_fields = []
        required_fields = ['name', 'description']
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            frontmatter, body = parse_yaml_frontmatter(content)
            
            if frontmatter is not None:
                for field in required_fields:
                    if field not in frontmatter:
                        relative_path = skill_file.relative_to(SKILL_ROOT)
                        missing_fields.append(f"{relative_path}: missing '{field}'")
        
        assert len(missing_fields) == 0, f"Files missing required fields: {missing_fields}"
    
    def test_name_field_not_empty(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        empty_names = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            frontmatter, body = parse_yaml_frontmatter(content)
            
            if frontmatter is not None:
                name = frontmatter.get('name', '')
                if not name or not name.strip():
                    relative_path = skill_file.relative_to(SKILL_ROOT)
                    empty_names.append(str(relative_path))
        
        assert len(empty_names) == 0, f"Files with empty 'name' field: {empty_names}"
    
    def test_description_field_not_empty(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        empty_descriptions = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            frontmatter, body = parse_yaml_frontmatter(content)
            
            if frontmatter is not None:
                description = frontmatter.get('description', '')
                if not description or not description.strip():
                    relative_path = skill_file.relative_to(SKILL_ROOT)
                    empty_descriptions.append(str(relative_path))
        
        assert len(empty_descriptions) == 0, f"Files with empty 'description' field: {empty_descriptions}"
    
    def test_document_length_reasonable(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        unreasonable_files = []
        min_length = 100
        max_length = 100000
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            length = len(content)
            
            if length < min_length or length > max_length:
                relative_path = skill_file.relative_to(SKILL_ROOT)
                unreasonable_files.append(f"{relative_path}: {length} chars (expected {min_length}-{max_length})")
        
        assert len(unreasonable_files) == 0, f"Files with unreasonable length: {unreasonable_files}"
    
    def test_document_has_content_after_frontmatter(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        empty_content_files = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            frontmatter, body = parse_yaml_frontmatter(content)
            
            if frontmatter is not None:
                if not body or not body.strip():
                    relative_path = skill_file.relative_to(SKILL_ROOT)
                    empty_content_files.append(str(relative_path))
        
        assert len(empty_content_files) == 0, f"Files with no content after frontmatter: {empty_content_files}"
    
    def test_skill_naming_convention(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        invalid_names = []
        
        valid_pattern = re.compile(r'^[a-z][a-z0-9_]*$')
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            frontmatter, body = parse_yaml_frontmatter(content)
            
            if frontmatter is not None:
                name = frontmatter.get('name', '')
                if name and not valid_pattern.match(name):
                    relative_path = skill_file.relative_to(SKILL_ROOT)
                    invalid_names.append(f"{relative_path}: name '{name}' doesn't match pattern '[a-z][a-z0-9_]*'")
        
        assert len(invalid_names) == 0, f"Files with invalid naming convention: {invalid_names}"
    
    def test_main_skill_structure(self):
        main_skill = SKILL_ROOT / "SKILL.md"
        assert main_skill.exists(), "Main SKILL.md not found"
        
        content = main_skill.read_text(encoding='utf-8')
        frontmatter, body = parse_yaml_frontmatter(content)
        
        assert frontmatter is not None, "Main SKILL.md missing YAML frontmatter"
        assert 'name' in frontmatter, "Main SKILL.md missing 'name' field"
        assert frontmatter['name'] == 'sanliu', f"Main skill name should be 'sanliu', got '{frontmatter.get('name')}'"
    
    def test_three_provinces_exist(self):
        provinces = ['zhongshusheng', 'menxiasheng', 'shangshusheng']
        missing_provinces = []
        
        for province in provinces:
            province_skill = SKILL_ROOT / province / "SKILL.md"
            if not province_skill.exists():
                missing_provinces.append(province)
        
        assert len(missing_provinces) == 0, f"Missing province directories: {missing_provinces}"
    
    def test_six_ministries_exist(self):
        ministries = ['libu', 'hubu', 'liibu', 'bingbu', 'xingbu', 'gongbu']
        missing_ministries = []
        
        for ministry in ministries:
            ministry_skill = SKILL_ROOT / "shangshusheng" / ministry / "SKILL.md"
            if not ministry_skill.exists():
                missing_ministries.append(ministry)
        
        assert len(missing_ministries) == 0, f"Missing ministry directories: {missing_ministries}"
    
    def test_subskills_directory_exists(self):
        subskills_dir = SKILL_ROOT / "subskills"
        assert subskills_dir.exists(), "subskills directory not found"
        assert subskills_dir.is_dir(), "subskills should be a directory"
    
    def test_scripts_directory_exists(self):
        scripts_dir = SKILL_ROOT / "scripts"
        assert scripts_dir.exists(), "scripts directory not found"
        assert scripts_dir.is_dir(), "scripts should be a directory"
    
    def test_resources_directory_exists(self):
        resources_dir = SKILL_ROOT / "resources"
        assert resources_dir.exists(), "resources directory not found"
        assert resources_dir.is_dir(), "resources should be a directory"


class TestSkillContentQuality:
    
    def test_no_duplicate_skill_names(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        names = []
        duplicates = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            frontmatter, body = parse_yaml_frontmatter(content)
            
            if frontmatter is not None:
                name = frontmatter.get('name', '')
                if name in names:
                    duplicates.append(name)
                else:
                    names.append(name)
        
        assert len(duplicates) == 0, f"Duplicate skill names found: {duplicates}"
    
    def test_description_quality(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        poor_descriptions = []
        min_description_length = 20
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            frontmatter, body = parse_yaml_frontmatter(content)
            
            if frontmatter is not None:
                description = frontmatter.get('description', '')
                if len(description) < min_description_length:
                    relative_path = skill_file.relative_to(SKILL_ROOT)
                    poor_descriptions.append(f"{relative_path}: description too short ({len(description)} chars)")
        
        assert len(poor_descriptions) == 0, f"Poor quality descriptions: {poor_descriptions}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
