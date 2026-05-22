"""
子技能管理器模块
提供子技能注册、发现、解析和调用功能
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class SubskillState(Enum):
    UNREGISTERED = auto()
    REGISTERED = auto()
    ACTIVE = auto()
    INACTIVE = auto()
    ERROR = auto()


class SubskillCategory(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    ANALYSIS = "analysis"
    OPTIMIZATION = "optimization"
    DOCUMENTATION = "documentation"
    INTEGRATION = "integration"
    PLANNING = "planning"
    SECURITY = "security"
    OTHER = "other"


@dataclass
class SubskillInfo:
    name: str
    path: Path
    title: str
    description: str
    version: str
    sections: Dict[str, str]
    commands: List[str]
    templates: List[str]
    metadata: Dict[str, Any]
    state: SubskillState = SubskillState.UNREGISTERED
    category: SubskillCategory = SubskillCategory.OTHER
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_accessed: Optional[datetime] = None
    access_count: int = 0

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "title": self.title,
            "description": self.description,
            "version": self.version,
            "sections": self.sections,
            "commands": self.commands,
            "templates": self.templates,
            "metadata": self.metadata,
            "state": self.state.name,
            "category": self.category.value,
            "dependencies": self.dependencies,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_accessed": self.last_accessed.isoformat() if self.last_accessed else None,
            "access_count": self.access_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SubskillInfo':
        return cls(
            name=data['name'],
            path=Path(data['path']),
            title=data['title'],
            description=data['description'],
            version=data['version'],
            sections=data.get('sections', {}),
            commands=data.get('commands', []),
            templates=data.get('templates', []),
            metadata=data.get('metadata', {}),
            state=SubskillState[data.get('state', 'UNREGISTERED')],
            category=SubskillCategory(data.get('category', 'other')),
            dependencies=data.get('dependencies', []),
            tags=data.get('tags', []),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            updated_at=datetime.fromisoformat(data['updated_at']) if data.get('updated_at') else None,
            last_accessed=datetime.fromisoformat(data['last_accessed']) if data.get('last_accessed') else None,
            access_count=data.get('access_count', 0)
        )


class SubskillParser:
    SECTION_PATTERN = re.compile(r'^##\s+(.+)$', re.MULTILINE)
    SUBSECTION_PATTERN = re.compile(r'^###\s+(.+)$', re.MULTILINE)
    COMMAND_PATTERN = re.compile(r'```(?:bash|shell|cmd|powershell)?\s*\n(.*?)```', re.DOTALL)
    TEMPLATE_PATTERN = re.compile(r'(?:调用|引用|参考)\s*[`\'"]?([^`\'"\s]+\.(?:md|yaml|json|txt))[`\'"]?', re.IGNORECASE)
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    YAML_FRONTMATTER_PATTERN = re.compile(r'^---\s*\n(.*?)\n---\s*\n', re.DOTALL)
    CODE_BLOCK_PATTERN = re.compile(r'```(\w*)\s*\n(.*?)```', re.DOTALL)

    def __init__(self):
        self._cache: Dict[str, Tuple[str, SubskillInfo]] = {}

    def parse_subskill_content(self, content: str, path: Path) -> SubskillInfo:
        file_hash = str(hash(content))
        cache_key = str(path)
        if cache_key in self._cache:
            cached_hash, cached_info = self._cache[cache_key]
            if cached_hash == file_hash:
                return cached_info

        metadata = self._parse_frontmatter(content)
        sections = self.extract_sections(content)
        commands = self.extract_commands(content)
        templates = self.extract_templates(content)
        title = self._extract_title(content, metadata)
        description = metadata.get('description', '')
        version = metadata.get('version', '1.0.0')
        category = self._determine_category(metadata, content)
        dependencies = self._extract_dependencies(content)
        tags = self._extract_tags(metadata, content)

        info = SubskillInfo(
            name=metadata.get('name', path.stem),
            path=path,
            title=title,
            description=description,
            version=version,
            sections=sections,
            commands=commands,
            templates=templates,
            metadata=metadata,
            category=category,
            dependencies=dependencies,
            tags=tags
        )

        self._cache[cache_key] = (file_hash, info)
        return info

    def _parse_frontmatter(self, content: str) -> Dict[str, Any]:
        match = self.YAML_FRONTMATTER_PATTERN.match(content)
        if not match:
            return {}

        frontmatter = match.group(1)
        metadata = {}

        for line in frontmatter.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                if value.startswith('[') and value.endswith(']'):
                    value = [v.strip().strip('\'"') for v in value[1:-1].split(',')]
                metadata[key] = value

        return metadata

    def _extract_title(self, content: str, metadata: Dict[str, Any]) -> str:
        if 'title' in metadata:
            return metadata['title']

        match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if match:
            return match.group(1).strip()

        return metadata.get('name', 'Unknown')

    def extract_sections(self, content: str) -> Dict[str, str]:
        sections = {}
        lines = content.split('\n')
        current_section = None
        current_content = []

        for line in lines:
            section_match = self.SECTION_PATTERN.match(line)
            if section_match:
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                current_section = section_match.group(1).strip()
                current_content = []
            elif current_section:
                current_content.append(line)

        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()

        return sections

    def extract_commands(self, content: str) -> List[str]:
        commands = []
        for match in self.COMMAND_PATTERN.finditer(content):
            command = match.group(1).strip()
            if command and not command.startswith('#'):
                commands.append(command)
        return commands

    def extract_templates(self, content: str) -> List[str]:
        templates = set()
        for match in self.TEMPLATE_PATTERN.finditer(content):
            template = match.group(1).strip()
            if template:
                templates.add(template)

        for match in self.LINK_PATTERN.finditer(content):
            link = match.group(2).strip()
            if link.endswith(('.md', '.yaml', '.json', '.txt')):
                templates.add(link)

        return list(templates)

    def _determine_category(self, metadata: Dict[str, Any], content: str) -> SubskillCategory:
        if 'category' in metadata:
            try:
                return SubskillCategory(metadata['category'].lower())
            except ValueError:
                pass

        content_lower = content.lower()
        category_keywords = {
            SubskillCategory.TESTING: ['测试', 'test', 'tdd', '验收', '单元测试', '集成测试'],
            SubskillCategory.DEPLOYMENT: ['部署', 'deploy', 'docker', 'kubernetes', '发布'],
            SubskillCategory.ANALYSIS: ['分析', 'analysis', '检查', '检测', '扫描'],
            SubskillCategory.OPTIMIZATION: ['优化', 'optimize', '重构', 'refactor', '性能'],
            SubskillCategory.DOCUMENTATION: ['文档', 'document', 'readme', '说明'],
            SubskillCategory.INTEGRATION: ['集成', 'integration', 'api', '接口'],
            SubskillCategory.PLANNING: ['规划', 'plan', '设计', 'design', '架构'],
            SubskillCategory.SECURITY: ['安全', 'security', '漏洞', 'vulnerability'],
            SubskillCategory.DEVELOPMENT: ['开发', 'develop', '编码', 'code', '实现']
        }

        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return category

        return SubskillCategory.OTHER

    def _extract_dependencies(self, content: str) -> List[str]:
        dependencies = set()
        dep_patterns = [
            r'调用\s+[`\'"]?([^`\'"\s]+\.(?:md|py|sh))[`\'"]?',
            r'依赖\s+[`\'"]?([^`\'"\s]+)[`\'"]?',
            r'requires?\s*:\s*([^\n]+)',
        ]

        for pattern in dep_patterns:
            for match in re.finditer(pattern, content, re.IGNORECASE):
                dep = match.group(1).strip()
                if dep:
                    dependencies.add(dep)

        return list(dependencies)

    def _extract_tags(self, metadata: Dict[str, Any], content: str) -> List[str]:
        tags = set()
        if 'tags' in metadata:
            if isinstance(metadata['tags'], list):
                tags.update(metadata['tags'])
            else:
                tags.add(str(metadata['tags']))

        tag_patterns = [
            r'#(\w+)',
            r'标签\s*:\s*([^\n]+)',
        ]

        for pattern in tag_patterns:
            for match in re.finditer(pattern, content):
                tag = match.group(1).strip()
                if tag and len(tag) > 1:
                    tags.add(tag)

        return list(tags)

    def clear_cache(self) -> None:
        self._cache.clear()


class SubskillDiscovery:
    def __init__(self, base_path: Path, parser: Optional[SubskillParser] = None):
        self.base_path = base_path
        self.parser = parser or SubskillParser()
        self._discovered: Dict[str, SubskillInfo] = {}
        self._file_mtimes: Dict[str, float] = {}

    def discover_subskills(self, incremental: bool = True) -> Dict[str, SubskillInfo]:
        subskills_dir = self.base_path / "subskills"

        if not subskills_dir.exists():
            return {}

        if not incremental:
            self._discovered.clear()
            self._file_mtimes.clear()

        for md_file in subskills_dir.glob("*.md"):
            file_path = str(md_file)
            current_mtime = md_file.stat().st_mtime

            if incremental and file_path in self._file_mtimes:
                if self._file_mtimes[file_path] == current_mtime:
                    continue

            try:
                content = md_file.read_text(encoding='utf-8')
                info = self.parser.parse_subskill_content(content, md_file)
                info.state = SubskillState.REGISTERED
                self._discovered[info.name] = info
                self._file_mtimes[file_path] = current_mtime
            except Exception:
                continue

        return self._discovered.copy()

    def get_discovered(self) -> Dict[str, SubskillInfo]:
        return self._discovered.copy()

    def refresh(self) -> Dict[str, SubskillInfo]:
        return self.discover_subskills(incremental=False)

    def get_subskills_by_category(self, category: SubskillCategory) -> List[SubskillInfo]:
        return [
            info for info in self._discovered.values()
            if info.category == category
        ]

    def get_subskills_by_tag(self, tag: str) -> List[SubskillInfo]:
        return [
            info for info in self._discovered.values()
            if tag in info.tags
        ]

    def search_subskills(self, query: str) -> List[SubskillInfo]:
        query_lower = query.lower()
        results = []

        for info in self._discovered.values():
            if (query_lower in info.name.lower() or
                query_lower in info.title.lower() or
                query_lower in info.description.lower() or
                any(query_lower in tag.lower() for tag in info.tags)):
                results.append(info)

        return results


class SubskillManager:
    _instance: Optional['SubskillManager'] = None

    def __new__(cls, base_path: Path = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, base_path: Path = None):
        if self._initialized:
            return

        self._initialized = True
        self.base_path = base_path or self._get_default_base_path()
        self._subskills: Dict[str, SubskillInfo] = {}
        self._parser = SubskillParser()
        self._discovery = SubskillDiscovery(self.base_path, self._parser)
        self._hooks: Dict[str, List[Callable]] = {
            'pre_register': [],
            'post_register': [],
            'pre_unregister': [],
            'post_unregister': [],
            'pre_call': [],
            'post_call': [],
            'on_error': []
        }
        self._context_cache: Dict[str, Any] = {}

    def _get_default_base_path(self) -> Path:
        return Path(__file__).parent.parent.parent

    @classmethod
    def get_instance(cls, base_path: Path = None) -> 'SubskillManager':
        if cls._instance is None:
            cls._instance = cls(base_path)
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    def register_subskill(
        self,
        name: str,
        path: Path,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        self._execute_hooks('pre_register', name)

        if name in self._subskills:
            return False

        try:
            if not path.exists():
                return False

            content = path.read_text(encoding='utf-8')
            info = self._parser.parse_subskill_content(content, path)

            if metadata:
                info.metadata.update(metadata)
                if 'version' in metadata:
                    info.version = metadata['version']
                if 'description' in metadata:
                    info.description = metadata['description']

            info.name = name
            info.state = SubskillState.REGISTERED
            self._subskills[name] = info

            self._execute_hooks('post_register', name)
            return True

        except Exception as e:
            self._execute_hooks('on_error', name, e)
            return False

    def unregister_subskill(self, name: str) -> bool:
        if name not in self._subskills:
            return False

        self._execute_hooks('pre_unregister', name)

        info = self._subskills[name]
        info.state = SubskillState.UNREGISTERED
        del self._subskills[name]

        self._execute_hooks('post_unregister', name)
        return True

    def get_subskill(self, name: str) -> Optional[SubskillInfo]:
        return self._subskills.get(name)

    def list_subskills(
        self,
        category: Optional[SubskillCategory] = None,
        state: Optional[SubskillState] = None
    ) -> List[SubskillInfo]:
        results = list(self._subskills.values())

        if category:
            results = [info for info in results if info.category == category]

        if state:
            results = [info for info in results if info.state == state]

        return results

    def discover_subskills(self, incremental: bool = True) -> Dict[str, SubskillInfo]:
        discovered = self._discovery.discover_subskills(incremental)

        for name, info in discovered.items():
            if name not in self._subskills:
                self._subskills[name] = info

        return discovered

    def parse_subskill_content(self, content: str, path: Path = None) -> SubskillInfo:
        if path is None:
            path = Path.cwd() / "temp_subskill.md"
        return self._parser.parse_subskill_content(content, path)

    def extract_sections(self, content: str) -> Dict[str, str]:
        return self._parser.extract_sections(content)

    def extract_commands(self, content: str) -> List[str]:
        return self._parser.extract_commands(content)

    def extract_templates(self, content: str) -> List[str]:
        return self._parser.extract_templates(content)

    def call_subskill(
        self,
        name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        self._execute_hooks('pre_call', name, context)

        info = self._subskills.get(name)
        if not info:
            raise ValueError(f"子技能未注册: {name}")

        try:
            if not info.path.exists():
                raise FileNotFoundError(f"子技能文件不存在: {info.path}")

            content = info.path.read_text(encoding='utf-8')
            sections = self.extract_sections(content)
            commands = self.extract_commands(content)
            templates = self.extract_templates(content)

            info.last_accessed = datetime.now()
            info.access_count += 1

            result = {
                "name": name,
                "title": info.title,
                "description": info.description,
                "sections": sections,
                "commands": commands,
                "templates": templates,
                "metadata": info.metadata,
                "context": context or {}
            }

            self._execute_hooks('post_call', name, result)
            return result

        except Exception as e:
            info.state = SubskillState.ERROR
            self._execute_hooks('on_error', name, e)
            raise

    def get_guidance(self, name: str, topic: str) -> Optional[str]:
        info = self._subskills.get(name)
        if not info:
            return None

        topic_lower = topic.lower()
        for section_name, section_content in info.sections.items():
            if topic_lower in section_name.lower():
                return section_content

        content = info.path.read_text(encoding='utf-8') if info.path.exists() else ""
        lines = content.split('\n')
        found = False
        guidance_lines = []

        for line in lines:
            if topic_lower in line.lower() and line.startswith('#'):
                found = True
                guidance_lines = [line]
                continue

            if found:
                if line.startswith('#') and not topic_lower in line.lower():
                    break
                guidance_lines.append(line)

        return '\n'.join(guidance_lines).strip() if guidance_lines else None

    def execute_subskill_command(
        self,
        name: str,
        command: str,
        executor: Optional[Callable[[str], Any]] = None
    ) -> Any:
        info = self._subskills.get(name)
        if not info:
            raise ValueError(f"子技能未注册: {name}")

        if command not in info.commands:
            content = info.path.read_text(encoding='utf-8') if info.path.exists() else ""
            commands = self.extract_commands(content)
            if command not in commands:
                raise ValueError(f"子技能 '{name}' 中未找到命令: {command}")

        if executor:
            return executor(command)

        return {
            "subskill": name,
            "command": command,
            "status": "ready",
            "message": f"命令已准备执行: {command}"
        }

    def add_hook(self, event: str, callback: Callable) -> None:
        if event in self._hooks:
            self._hooks[event].append(callback)

    def remove_hook(self, event: str, callback: Callable) -> bool:
        if event in self._hooks and callback in self._hooks[event]:
            self._hooks[event].remove(callback)
            return True
        return False

    def _execute_hooks(self, event: str, *args, **kwargs) -> None:
        if event in self._hooks:
            for callback in self._hooks[event]:
                try:
                    callback(*args, **kwargs)
                except Exception:
                    pass

    def get_status_report(self) -> Dict[str, Any]:
        state_counts = {}
        for state in SubskillState:
            state_counts[state.name] = len([
                info for info in self._subskills.values()
                if info.state == state
            ])

        category_counts = {}
        for category in SubskillCategory:
            category_counts[category.value] = len([
                info for info in self._subskills.values()
                if info.category == category
            ])

        return {
            "generated_at": datetime.now().isoformat(),
            "total_subskills": len(self._subskills),
            "state_summary": state_counts,
            "category_summary": category_counts,
            "subskills": [name for name in self._subskills.keys()]
        }

    def export_registry(self, output_path: Path) -> bool:
        try:
            import json

            data = {
                "exported_at": datetime.now().isoformat(),
                "base_path": str(self.base_path),
                "subskills": {
                    name: info.to_dict()
                    for name, info in self._subskills.items()
                }
            }

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True
        except Exception:
            return False

    def import_registry(self, input_path: Path) -> bool:
        try:
            import json

            input_path = Path(input_path)

            with open(input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for name, subskill_data in data.get('subskills', {}).items():
                info = SubskillInfo.from_dict(subskill_data)
                self._subskills[name] = info

            return True
        except Exception:
            return False

    def clear_cache(self) -> None:
        self._parser.clear_cache()
        self._context_cache.clear()


@lru_cache(maxsize=128)
def get_subskill_manager(base_path: str = None) -> SubskillManager:
    path = Path(base_path) if base_path else None
    return SubskillManager.get_instance(path)


def register_subskill(
    name: str,
    path: Path,
    metadata: Optional[Dict[str, Any]] = None
) -> bool:
    return get_subskill_manager().register_subskill(name, path, metadata)


def unregister_subskill(name: str) -> bool:
    return get_subskill_manager().unregister_subskill(name)


def get_subskill(name: str) -> Optional[SubskillInfo]:
    return get_subskill_manager().get_subskill(name)


def list_subskills(
    category: Optional[SubskillCategory] = None,
    state: Optional[SubskillState] = None
) -> List[SubskillInfo]:
    return get_subskill_manager().list_subskills(category, state)


def discover_subskills(incremental: bool = True) -> Dict[str, SubskillInfo]:
    return get_subskill_manager().discover_subskills(incremental)


def call_subskill(
    name: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    return get_subskill_manager().call_subskill(name, context)


def get_guidance(name: str, topic: str) -> Optional[str]:
    return get_subskill_manager().get_guidance(name, topic)
