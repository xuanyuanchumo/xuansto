import os
import re
import pytest
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional


SKILL_ROOT = Path(__file__).parent.parent
SKILLS_ROOT = SKILL_ROOT.parent


def find_all_skill_files(root_path: Path) -> List[Path]:
    skill_files = []
    for path in root_path.rglob("SKILL.md"):
        skill_files.append(path)
    return skill_files


def extract_all_references(content: str) -> List[Tuple[str, str]]:
    patterns = [
        (r'subskills/([a-zA-Z0-9_]+\.md)', 'subskill'),
        (r'scripts/([a-zA-Z0-9_]+\.py)', 'script'),
        (r'resources/([a-zA-Z0-9_/]+\.md)', 'resource'),
        (r'([a-zA-Z0-9_]+)/SKILL\.md', 'skill'),
        (r'`([a-zA-Z0-9_/]+\.md)`', 'inline_md'),
        (r'`([a-zA-Z0-9_/]+\.py)`', 'inline_py'),
        (r'\[([^\]]+)\]\(([^)]+)\)', 'markdown_link'),
    ]
    
    references = []
    for pattern, ref_type in patterns:
        if ref_type == 'markdown_link':
            matches = re.findall(pattern, content)
            for text, link in matches:
                if not link.startswith('http') and not link.startswith('#'):
                    references.append((link, 'markdown_link'))
        else:
            matches = re.findall(pattern, content)
            for match in matches:
                references.append((match, ref_type))
    
    return references


def extract_external_skill_references(content: str) -> List[str]:
    patterns = [
        r'\.trae/skills/([a-zA-Z0-9_-]+)/SKILL\.md',
        r'\.trae/skills/([a-zA-Z0-9_-]+)/',
    ]
    
    references = []
    for pattern in patterns:
        matches = re.findall(pattern, content)
        references.extend(matches)
    
    return list(set(references))


class TestRelativePathReferences:
    
    def test_subskill_references_valid(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        broken_refs = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            
            subskill_refs = re.findall(r'subskills/([a-zA-Z0-9_]+\.md)', content)
            
            for subskill in subskill_refs:
                subskill_path = SKILL_ROOT / "subskills" / subskill
                if not subskill_path.exists():
                    relative_skill = skill_file.relative_to(SKILL_ROOT)
                    broken_refs.append(f"{relative_skill} -> subskills/{subskill}")
        
        assert len(broken_refs) == 0, f"Broken subskill references: {broken_refs}"
    
    def test_script_references_valid(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        broken_refs = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            
            script_refs = re.findall(r'scripts/([a-zA-Z0-9_]+\.py)', content)
            
            for script in script_refs:
                script_path = SKILL_ROOT / "scripts" / script
                if not script_path.exists():
                    relative_skill = skill_file.relative_to(SKILL_ROOT)
                    broken_refs.append(f"{relative_skill} -> scripts/{script}")
        
        assert len(broken_refs) == 0, f"Broken script references: {broken_refs}"
    
    def test_resource_references_valid(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        broken_refs = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            
            resource_refs = re.findall(r'resources/([a-zA-Z0-9_/]+\.md)', content)
            
            for resource in resource_refs:
                resource_path = SKILL_ROOT / "resources" / resource
                local_resource_path = skill_file.parent / "resources" / resource
                
                if not resource_path.exists() and not local_resource_path.exists():
                    relative_skill = skill_file.relative_to(SKILL_ROOT)
                    broken_refs.append(f"{relative_skill} -> resources/{resource}")
        
        assert len(broken_refs) == 0, f"Broken resource references: {broken_refs}"


class TestExternalSkillReferences:
    
    def test_external_skill_references_valid(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        broken_refs = []
        
        external_skills_dir = SKILLS_ROOT
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            external_refs = extract_external_skill_references(content)
            
            for ext_skill in external_refs:
                if ext_skill == 'sanliu':
                    continue
                
                ext_skill_path = external_skills_dir / ext_skill / "SKILL.md"
                if not ext_skill_path.exists():
                    relative_skill = skill_file.relative_to(SKILL_ROOT)
                    broken_refs.append(f"{relative_skill} -> external skill '{ext_skill}'")
        
        assert len(broken_refs) == 0, f"Broken external skill references: {broken_refs}"
    
    def test_known_external_skills_exist(self):
        known_external_skills = ['global-chinese', 'mcp-builder']
        missing_skills = []
        
        for skill_name in known_external_skills:
            skill_path = SKILLS_ROOT / skill_name / "SKILL.md"
            if not skill_path.exists():
                missing_skills.append(skill_name)
        
        assert len(missing_skills) == 0, f"Missing known external skills: {missing_skills}"
    
    def test_external_skill_reference_format(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        invalid_formats = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            
            invalid_patterns = [
                r'\.trae/skills/([a-zA-Z0-9_-]+)/[^S][^K][^I][^L][^L]',
            ]
            
            for pattern in invalid_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    relative_skill = skill_file.relative_to(SKILL_ROOT)
                    invalid_formats.append(f"{relative_skill}: potentially invalid external skill reference")
        
        assert len(invalid_formats) == 0, f"Invalid external skill reference formats: {invalid_formats}"


class TestMarkdownLinks:
    
    def test_markdown_links_valid(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        broken_links = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            
            link_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
            matches = re.findall(link_pattern, content)
            
            for text, link in matches:
                if link.startswith('http://') or link.startswith('https://'):
                    continue
                
                if link.startswith('#'):
                    continue
                
                if link.startswith('/'):
                    target_path = SKILL_ROOT / link[1:]
                else:
                    target_path = skill_file.parent / link
                
                target_path = target_path.resolve()
                
                if not target_path.exists():
                    relative_skill = skill_file.relative_to(SKILL_ROOT)
                    broken_links.append(f"{relative_skill}: link '{link}' -> {target_path}")
        
        assert len(broken_links) == 0, f"Broken markdown links: {broken_links}"
    
    def test_no_empty_link_text(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        empty_links = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            
            empty_link_pattern = r'\[\s*\]\(([^)]+)\)'
            matches = re.findall(empty_link_pattern, content)
            
            if matches:
                relative_skill = skill_file.relative_to(SKILL_ROOT)
                empty_links.append(f"{relative_skill}: {len(matches)} empty link text(s)")
        
        assert len(empty_links) == 0, f"Empty link texts found: {empty_links}"


class TestCodeBlockReferences:
    
    def test_code_block_file_references_valid(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        broken_refs = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            
            code_block_pattern = r'```[a-zA-Z]*\n(.*?)```'
            code_blocks = re.findall(code_block_pattern, content, re.DOTALL)
            
            for block in code_blocks:
                file_refs = re.findall(r'#\s*([a-zA-Z0-9_/]+\.(py|ts|js|vue|json))', block)
                
                for file_ref, ext in file_refs:
                    potential_path = SKILL_ROOT / file_ref
                    if not potential_path.exists():
                        relative_skill = skill_file.relative_to(SKILL_ROOT)
                        broken_refs.append(f"{relative_skill}: code block references '{file_ref}'")
        
        assert len(broken_refs) == 0, f"Broken code block file references: {broken_refs}"


class TestCrossReferences:
    
    def test_skill_cross_references_consistent(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        inconsistencies = []
        
        external_skill_parts = {'chinese', 'builder', 'max'}
        
        for skill_file in skill_files:
            relative_path = str(skill_file.relative_to(SKILL_ROOT))
            content = skill_file.read_text(encoding='utf-8')
            
            single_level_refs = re.findall(r'(?<![a-zA-Z0-9_/])([a-zA-Z0-9_]+)/SKILL\.md', content)
            
            for ref in single_level_refs:
                if ref in external_skill_parts:
                    continue
                    
                source_dir = skill_file.parent
                ref_path = source_dir / ref / "SKILL.md"
                
                if not ref_path.exists():
                    inconsistencies.append(f"{relative_path} references non-existent {ref}/SKILL.md")
        
        assert len(inconsistencies) == 0, f"Inconsistent cross-references: {inconsistencies}"
    
    def test_no_orphan_subskills(self):
        subskills_dir = SKILL_ROOT / "subskills"
        if not subskills_dir.exists():
            pytest.skip("subskills directory not found")
        
        subskill_files = list(subskills_dir.glob("*.md"))
        subskill_names = {f.stem for f in subskill_files}
        
        skill_files = find_all_skill_files(SKILL_ROOT)
        referenced_subskills = set()
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            refs = re.findall(r'subskills/([a-zA-Z0-9_]+)\.md', content)
            referenced_subskills.update(refs)
        
        orphan_subskills = subskill_names - referenced_subskills
        
        assert len(orphan_subskills) == 0, f"Orphan subskills (not referenced): {orphan_subskills}"
    
    def test_reference_count_reasonable(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        excessive_refs = []
        max_refs = 100
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            refs = extract_all_references(content)
            
            if len(refs) > max_refs:
                relative_skill = skill_file.relative_to(SKILL_ROOT)
                excessive_refs.append(f"{relative_skill}: {len(refs)} references (max: {max_refs})")
        
        assert len(excessive_refs) == 0, f"Excessive references: {excessive_refs}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
