import os
import re
import pytest
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict


SKILL_ROOT = Path(__file__).parent.parent


def find_all_skill_files(root_path: Path) -> List[Path]:
    skill_files = []
    for path in root_path.rglob("SKILL.md"):
        skill_files.append(path)
    return skill_files


def extract_relative_references(content: str) -> List[str]:
    patterns = [
        r'\.\./subskills/([a-zA-Z0-9_]+\.md)',
        r'\.\./scripts/([a-zA-Z0-9_]+\.py)',
        r'\.\./resources/([a-zA-Z0-9_/]+\.md)',
        r'\.\./([a-zA-Z0-9_]+)/SKILL\.md',
        r'subskills/([a-zA-Z0-9_]+\.md)',
        r'scripts/([a-zA-Z0-9_]+\.py)',
    ]
    
    references = []
    for pattern in patterns:
        matches = re.findall(pattern, content)
        references.extend(matches)
    
    return references


def extract_skill_references(content: str) -> List[str]:
    pattern = r'调用\s+`?([a-zA-Z0-9_]+/SKILL\.md)`?'
    matches = re.findall(pattern, content)
    return matches


def extract_file_references(content: str) -> List[str]:
    patterns = [
        r'`([a-zA-Z0-9_]+/[a-zA-Z0-9_]+\.py)`',
        r'`([a-zA-Z0-9_]+/[a-zA-Z0-9_]+\.md)`',
        r'python\s+([a-zA-Z0-9_/]+\.py)',
        r'python3\s+([a-zA-Z0-9_/]+\.py)',
    ]
    
    references = []
    for pattern in patterns:
        matches = re.findall(pattern, content)
        references.extend(matches)
    
    return references


def build_dependency_graph(root_path: Path) -> Dict[str, Set[str]]:
    skill_files = find_all_skill_files(root_path)
    graph = defaultdict(set)
    
    for skill_file in skill_files:
        relative_path = str(skill_file.relative_to(root_path))
        content = skill_file.read_text(encoding='utf-8')
        
        refs = extract_relative_references(content)
        refs.extend(extract_skill_references(content))
        
        for ref in refs:
            graph[relative_path].add(ref)
    
    return graph


def detect_cycles(graph: Dict[str, Set[str]]) -> List[List[str]]:
    def dfs(node: str, visited: Set[str], rec_stack: Set[str], path: List[str]) -> Optional[List[str]]:
        visited.add(node)
        rec_stack.add(node)
        path.append(node)
        
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                cycle = dfs(neighbor, visited, rec_stack, path)
                if cycle:
                    return cycle
            elif neighbor in rec_stack:
                cycle_start = path.index(neighbor)
                return path[cycle_start:] + [neighbor]
        
        path.pop()
        rec_stack.remove(node)
        return None
    
    visited = set()
    cycles = []
    
    for node in graph:
        if node not in visited:
            cycle = dfs(node, visited, set(), [])
            if cycle:
                cycles.append(cycle)
    
    return cycles


class TestDependencies:
    
    def test_subskill_files_exist(self):
        subskills_dir = SKILL_ROOT / "subskills"
        if not subskills_dir.exists():
            pytest.skip("subskills directory not found")
        
        skill_files = find_all_skill_files(SKILL_ROOT)
        missing_subskills = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            
            subskill_refs = re.findall(r'subskills/([a-zA-Z0-9_]+\.md)', content)
            
            for ref in subskill_refs:
                subskill_path = SKILL_ROOT / "subskills" / ref
                if not subskill_path.exists():
                    relative_skill = skill_file.relative_to(SKILL_ROOT)
                    missing_subskills.append(f"{relative_skill} -> subskills/{ref}")
        
        assert len(missing_subskills) == 0, f"Missing subskill files: {missing_subskills}"
    
    def test_script_files_exist(self):
        scripts_dir = SKILL_ROOT / "scripts"
        if not scripts_dir.exists():
            pytest.skip("scripts directory not found")
        
        skill_files = find_all_skill_files(SKILL_ROOT)
        missing_scripts = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            
            script_refs = re.findall(r'scripts/([a-zA-Z0-9_]+\.py)', content)
            
            for script in script_refs:
                script_path = SKILL_ROOT / "scripts" / script
                if not script_path.exists():
                    relative_skill = skill_file.relative_to(SKILL_ROOT)
                    missing_scripts.append(f"{relative_skill} -> scripts/{script}")
        
        assert len(missing_scripts) == 0, f"Missing script files: {missing_scripts}"
    
    def test_child_skill_files_exist(self):
        skill_files = find_all_skill_files(SKILL_ROOT)
        missing_children = []
        
        external_skill_parts = {'global-chinese', 'mcp-builder', 'chinese', 'builder', 'max'}
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            
            child_refs = re.findall(r'([a-zA-Z0-9_]+(?:/[a-zA-Z0-9_]+)*)/SKILL\.md', content)
            
            for child in child_refs:
                child_name = child.split('/')[-1]
                if child_name in external_skill_parts or child in external_skill_parts:
                    continue
                
                parent_dir = skill_file.parent
                child_path = parent_dir / child / "SKILL.md"
                
                if not child_path.exists():
                    relative_skill = skill_file.relative_to(SKILL_ROOT)
                    missing_children.append(f"{relative_skill} -> {child}/SKILL.md")
        
        assert len(missing_children) == 0, f"Missing child skill files: {missing_children}"
    
    def test_no_circular_dependencies(self):
        graph = build_dependency_graph(SKILL_ROOT)
        cycles = detect_cycles(graph)
        
        assert len(cycles) == 0, f"Circular dependencies detected: {cycles}"
    
    def test_main_skill_dependencies_valid(self):
        main_skill = SKILL_ROOT / "SKILL.md"
        if not main_skill.exists():
            pytest.skip("Main SKILL.md not found")
        
        content = main_skill.read_text(encoding='utf-8')
        
        expected_deps = ['zhongshusheng', 'menxiasheng', 'shangshusheng']
        missing_deps = []
        
        for dep in expected_deps:
            if f"{dep}/SKILL.md" not in content and f"{dep}/" not in content:
                missing_deps.append(dep)
        
        assert len(missing_deps) == 0, f"Main skill missing dependencies to: {missing_deps}"
    
    def test_shangshusheng_dependencies_valid(self):
        shangshusheng = SKILL_ROOT / "shangshusheng" / "SKILL.md"
        if not shangshusheng.exists():
            pytest.skip("shangshusheng/SKILL.md not found")
        
        content = shangshusheng.read_text(encoding='utf-8')
        
        expected_deps = ['libu', 'hubu', 'liibu', 'bingbu', 'xingbu', 'gongbu']
        missing_deps = []
        
        for dep in expected_deps:
            if f"{dep}/SKILL.md" not in content:
                missing_deps.append(dep)
        
        assert len(missing_deps) == 0, f"shangshusheng missing dependencies to: {missing_deps}"
    
    def test_zhongshusheng_dependencies_valid(self):
        zhongshusheng = SKILL_ROOT / "zhongshusheng" / "SKILL.md"
        if not zhongshusheng.exists():
            pytest.skip("zhongshusheng/SKILL.md not found")
        
        content = zhongshusheng.read_text(encoding='utf-8')
        
        expected_subskills = ['xuqiu_fenxi', 'xiangmu_guihua', 'xitong_sheji']
        missing_deps = []
        
        for subskill in expected_subskills:
            if subskill not in content:
                missing_deps.append(subskill)
        
        assert len(missing_deps) == 0, f"zhongshusheng missing references to: {missing_deps}"
    
    def test_menxiasheng_dependencies_valid(self):
        menxiasheng = SKILL_ROOT / "menxiasheng" / "SKILL.md"
        if not menxiasheng.exists():
            pytest.skip("menxiasheng/SKILL.md not found")
        
        content = menxiasheng.read_text(encoding='utf-8')
        
        expected_subskills = ['daima_shencha']
        missing_deps = []
        
        for subskill in expected_subskills:
            if subskill not in content:
                missing_deps.append(subskill)
        
        assert len(missing_deps) == 0, f"menxiasheng missing references to: {missing_deps}"
    
    def test_resource_files_exist(self):
        resources_dir = SKILL_ROOT / "resources"
        if not resources_dir.exists():
            pytest.skip("resources directory not found")
        
        skill_files = find_all_skill_files(SKILL_ROOT)
        missing_resources = []
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            
            resource_refs = re.findall(r'resources/([a-zA-Z0-9_/]+\.md)', content)
            
            for resource in resource_refs:
                resource_path = SKILL_ROOT / "resources" / resource
                if not resource_path.exists():
                    relative_skill = skill_file.relative_to(SKILL_ROOT)
                    missing_resources.append(f"{relative_skill} -> resources/{resource}")
        
        assert len(missing_resources) == 0, f"Missing resource files: {missing_resources}"
    
    def test_dependency_depth_reasonable(self):
        def get_depth(skill_file: Path, visited: Set[str] = None) -> int:
            if visited is None:
                visited = set()
            
            relative_path = str(skill_file.relative_to(SKILL_ROOT))
            if relative_path in visited:
                return 0
            
            visited.add(relative_path)
            content = skill_file.read_text(encoding='utf-8')
            
            child_refs = re.findall(r'([a-zA-Z0-9_]+)/SKILL\.md', content)
            
            if not child_refs:
                return 1
            
            max_child_depth = 0
            for child in child_refs:
                child_path = skill_file.parent / child / "SKILL.md"
                if child_path.exists():
                    child_depth = get_depth(child_path, visited.copy())
                    max_child_depth = max(max_child_depth, child_depth)
            
            return 1 + max_child_depth
        
        main_skill = SKILL_ROOT / "SKILL.md"
        if not main_skill.exists():
            pytest.skip("Main SKILL.md not found")
        
        depth = get_depth(main_skill)
        max_allowed_depth = 5
        
        assert depth <= max_allowed_depth, f"Dependency depth {depth} exceeds maximum {max_allowed_depth}"


class TestDependencyIntegrity:
    
    def test_all_subskills_referenced(self):
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
        
        unreferenced = subskill_names - referenced_subskills
        
        assert len(unreferenced) == 0, f"Unreferenced subskills: {unreferenced}"
    
    def test_all_scripts_referenced(self):
        scripts_dir = SKILL_ROOT / "scripts"
        if not scripts_dir.exists():
            pytest.skip("scripts directory not found")
        
        internal_scripts = {
            'test_integration_1', 'test_integration_2', 'test_integration_3', 'test_integration_4',
            'test_agent_history', 'init_db', 'performance_benchmark_test',
            'analyze_composable', 'analyze_core_nesting', 'analyze_frontend_nesting',
            'detect_long_functions', 'detect_frontend_long_functions', 'simple_nesting_check',
            'nesting_analyzer', 'coverage_analyzer', 'code_problem_scanner',
            'benchmark_updater', 'priority_evaluator', 'performance_detector',
            'service_dependency_manager', 'report_generator', 'history_tracker',
            'generate_test_report', 'check_coverage', 'validate_test_coverage',
            'agent_selector', 'agent_call_history'
        }
        
        script_files = list(scripts_dir.glob("*.py"))
        script_names = {f.stem for f in script_files}
        
        skill_files = find_all_skill_files(SKILL_ROOT)
        referenced_scripts = set()
        
        for skill_file in skill_files:
            content = skill_file.read_text(encoding='utf-8')
            refs = re.findall(r'scripts/([a-zA-Z0-9_]+)\.py', content)
            referenced_scripts.update(refs)
        
        unreferenced = script_names - referenced_scripts - internal_scripts
        
        assert len(unreferenced) == 0, f"Unreferenced scripts: {unreferenced}"
    
    def test_ministry_subdirectories_valid(self):
        ministries = ['libu', 'hubu', 'liibu', 'bingbu', 'xingbu', 'gongbu']
        
        for ministry in ministries:
            ministry_path = SKILL_ROOT / "shangshusheng" / ministry
            if not ministry_path.exists():
                continue
            
            subdirs = [d for d in ministry_path.iterdir() if d.is_dir()]
            
            for subdir in subdirs:
                skill_file = subdir / "SKILL.md"
                assert skill_file.exists(), f"Missing SKILL.md in {subdir.relative_to(SKILL_ROOT)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
