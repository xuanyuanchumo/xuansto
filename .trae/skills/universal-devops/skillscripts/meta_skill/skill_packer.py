"""
技能打包器 - 将universal-devops技能打包为标准.skill格式
提供依赖收集、清单生成、版本元数据管理、技能导出四大能力
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import tarfile
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class PackingError(Exception):
    """打包异常"""
    pass


class PackFormat(str, Enum):
    SKILL = "skill"
    TAR_GZ = "tar.gz"
    ZIP = "ZIP"


@dataclass
class DependencyInfo:
    """依赖信息"""
    name: str
    version: str = "*"
    dep_type: str = "internal"
    resolved_path: str | None = None
    is_optional: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "dep_type": self.dep_type,
            "resolved_path": self.resolved_path,
            "is_optional": self.is_optional,
        }


@dataclass
class ManifestEntry:
    """清单条目"""
    path: str
    size_bytes: int = 0
    sha256: str = ""
    file_type: str = "unknown"
    last_modified: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "size_bytes": self.size_bytes,
            "sha256": self.sha256,
            "file_type": self.file_type,
            "last_modified": self.last_modified,
        }


@dataclass
class SkillManifest:
    """技能包清单"""
    manifest_version: str = "1.0"
    skill_name: str = "universal-devops"
    skill_version: str = "1.0.0"
    description: str = ""
    author: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    total_files: int = 0
    total_size_bytes: int = 0
    entries: list[ManifestEntry] = field(default_factory=list)
    dependencies: list[DependencyInfo] = field(default_factory=list)
    entry_point: str = "skillscripts/main.py"
    skill_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "manifest_version": self.manifest_version,
            "skill_name": self.skill_name,
            "skill_version": self.skill_version,
            "description": self.description,
            "author": self.author,
            "created_at": self.created_at,
            "total_files": self.total_files,
            "total_size_bytes": self.total_size_bytes,
            "entries": [e.to_dict() for e in self.entries],
            "dependencies": [d.to_dict() for d in self.dependencies],
            "entry_point": self.entry_point,
            "skill_metadata": self.skill_metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


@dataclass
class VersionInfo:
    """版本信息（SemVer）"""
    major: int = 1
    minor: int = 0
    patch: int = 0
    pre_release: str = ""
    build_metadata: str = ""
    release_notes: str = ""
    changed_files: list[str] = field(default_factory=list)
    changed_dependencies: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def version_string(self) -> str:
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.pre_release:
            v += f"-{self.pre_release}"
        if self.build_metadata:
            v += f"+{self.build_metadata}"
        return v

    def bump_major(self) -> VersionInfo:
        return VersionInfo(
            major=self.major + 1, minor=0, patch=0,
            release_notes=f"Breaking changes from {self.version_string}",
        )

    def bump_minor(self) -> VersionInfo:
        return VersionInfo(
            major=self.major, minor=self.minor + 1, patch=0,
            release_notes=f"New features added (from {self.version_string})",
        )

    def bump_patch(self) -> VersionInfo:
        return VersionInfo(
            major=self.major, minor=self.minor, patch=self.patch + 1,
            release_notes=f"Bug fixes (from {self.version_string})",
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "version": self.version_string,
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
            "pre_release": self.pre_release,
            "build_metadata": self.build_metadata,
            "release_notes": self.release_notes,
            "changed_files": self.changed_files,
            "changed_dependencies": self.changed_dependencies,
            "timestamp": self.timestamp,
        }


class DependencyCollector:
    """
    依赖收集器

    扫描所有Python文件的import语句，收集内部依赖关系，
    构建完整的依赖图。
    """

    IMPORT_PATTERNS: list[tuple[re.Pattern, str]] = [
        (re.compile(r'^import\s+([\w.]+)'), "standard"),
        (re.compile(r'^from\s+([\w.]+)\s+import'), "from"),
        (re.compile(r'^\s*import\s+([\w.]+)'), "standard_indented"),
    ]

    SKIP_MODULES: set[str] = {
        "os", "sys", "json", "re", "io", "pathlib", "datetime",
        "dataclasses", "enum", "typing", "collections", "functools",
        "itertools", "copy", "hashlib", "uuid", "time", "abc",
        "contextlib", "warnings", "inspect", "textwrap", "string",
        "math", "random", "threading", "multiprocessing", "asyncio",
        "subprocess", "tempfile", "shutil", "glob", "fnmatch",
        "argparse", "configparser", "logging", "unittest", "pprint",
        "__future__",
    }

    def __init__(self, skill_root: Path | str | None = None) -> None:
        self._skill_root: Path = (
            Path(skill_root).resolve() if skill_root
            else Path(__file__).parent.parent.parent.resolve()
        )
        self._dependency_graph: dict[str, set[str]] = {}
        self._external_deps: set[str] = set()
        self._internal_deps: dict[str, DependencyInfo] = {}

    def scan_directory(self, directory: Path | str | None = None) -> dict[str, Any]:
        """
        扫描目录下所有Python文件，构建依赖关系图

        Args:
            directory: 要扫描的目录（默认为skillscripts）

        Returns:
            包含依赖图和统计信息的字典
        """
        base_dir = Path(directory) if directory else self._skill_root / "skillscripts"
        if not base_dir.exists():
            raise PackingError(f"扫描目录不存在: {base_dir}")

        py_files: list[Path] = []
        for py_file in base_dir.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                py_files.append(py_file)

        self._dependency_graph.clear()
        self._external_deps.clear()
        self._internal_deps.clear()

        for py_file in py_files:
            rel_path = py_file.relative_to(base_dir)
            module_key = str(rel_path).replace(os.sep, ".").removesuffix(".py")
            imports = self._extract_imports(py_file)

            internal: set[str] = set()
            external: set[str] = set()

            for imp in imports:
                top_level = imp.split(".")[0]
                if top_level in self.SKIP_MODULES or imp.startswith("."):
                    continue

                is_internal = any(
                    str(p).endswith(imp.replace(".", os.sep) + ".py") or
                    (p / "__init__.py").exists() and imp.replace(".", os.sep) in str(p)
                    for p in [base_dir]
                ) or any(
                    f"{imp}." == str(rel_path).replace(os.sep, ".")[len(module_key):].lstrip(".")[:len(f"{imp}.")]
                    for _ in [None]
                )

                rel_check = (base_dir / imp.replace(".", os.sep))
                init_check = (base_dir / imp.replace(".", os.sep) / "__init__.py")

                if rel_check.with_suffix(".py").exists() or init_check.exists():
                    internal.add(imp)
                else:
                    external.add(top_level)

            self._dependency_graph[module_key] = internal
            self._external_deps.update(external)

        for mod, deps in self._dependency_graph.items():
            for dep in deps:
                clean_dep = dep.split(".")[0]
                if clean_dep not in self._internal_deps:
                    dep_path = base_dir / clean_dep.replace(".", os.sep)
                    self._internal_deps[clean_dep] = DependencyInfo(
                        name=clean_dep,
                        dep_type="internal",
                        resolved_path=str(dep_path) if dep_path.exists() else None,
                    )

        total_modules = len(self._dependency_graph)
        avg_deps = sum(len(d) for d in self._dependency_graph.values()) / max(total_modules, 1)

        return {
            "scanned_directory": str(base_dir),
            "total_python_files": len(py_files),
            "total_modules": total_modules,
            "total_external_dependencies": len(self._external_deps),
            "total_internal_dependencies": len(self._internal_deps),
            "average_dependencies_per_module": round(avg_deps, 2),
            "external_dependencies": sorted(self._external_deps),
            "dependency_graph": {
                k: sorted(v) for k, v in sorted(self._dependency_graph.items())
            },
        }

    def _extract_imports(self, py_file: Path) -> list[str]:
        """从Python文件中提取所有import"""
        imports: list[str] = []
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    for pattern, ptype in self.IMPORT_PATTERNS:
                        m = pattern.match(line)
                        if m:
                            imports.append(m.group(1))
                            break
        except (OSError, UnicodeDecodeError):
            pass
        return imports

    def get_dependency_tree(self, root_module: str = "") -> dict[str, Any]:
        """
        获取依赖树结构

        Args:
            root_module: 根模块名（为空则返回完整树）

        Returns:
            嵌套的依赖树字典
        """
        if root_module:
            direct_deps = self._dependency_graph.get(root_module, set())
            tree = {"module": root_module, "dependencies": []}
            for dep in sorted(direct_deps):
                sub_tree = self.get_dependency_tree(dep)
                tree["dependencies"].append(sub_tree)
            return tree

        roots = [
            m for m in self._dependency_graph
            if not any(m in deps for deps in self._dependency_graph.values())
        ]
        return {
            "root_modules": sorted(roots),
            "trees": [self.get_dependency_tree(r) for r in sorted(roots)],
        }

    def get_circular_dependencies(self) -> list[list[str]]:
        """检测循环依赖"""
        cycles: list[list[str]] = []
        visited: set[str] = set()
        rec_stack: set[str] = set()

        def dfs(node: str, path: list[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in self._dependency_graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, list(path))
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor) if neighbor in path else -1
                    if cycle_start >= 0:
                        cycles.append(path[cycle_start:] + [neighbor])

            rec_stack.discard(node)

        for node in sorted(self._dependency_graph.keys()):
            if node not in visited:
                dfs(node, [])

        unique_cycles: list[list[str]] = []
        seen_cycle_sets: set[frozenset[str]] = set()
        for cycle in cycles:
            cycle_set = frozenset(cycle[:-1])
            if cycle_set not in seen_cycle_sets and len(cycle_set) > 1:
                seen_cycle_sets.add(cycle_set)
                unique_cycles.append(cycle)

        return unique_cycles


class ManifestGenerator:
    """
    清单生成器

    生成.skill包的manifest清单文件，
    记录所有包含的文件、哈希值和元数据。
    """

    EXCLUDE_PATTERNS: list[str] = [
        "__pycache__", "*.pyc", ".pyo", "*.pyd",
        ".git", ".svn", ".hg",
        "*.egg-info", "dist", "build", ".tox",
        ".env", ".venv", "venv", "node_modules",
        "*.log", ".DS_Store", "Thumbs.db",
        ".trae/cache", ".trae/temp",
    ]

    def __init__(self, skill_root: Path | str | None = None) -> None:
        self._skill_root: Path = (
            Path(skill_root).resolve() if skill_root
            else Path(__file__).parent.parent.parent.resolve()
        )

    def generate_manifest(
        self,
        source_dir: Path | str | None = None,
        version_info: VersionInfo | None = None,
        dependencies: list[DependencyInfo] | None = None,
        skill_name: str = "universal-devops",
        description: str = "",
    ) -> SkillManifest:
        """
        生成完整的技能包清单

        Args:
            source_dir: 源目录路径
            version_info: 版本信息对象
            dependencies: 依赖列表
            skill_name: 技能名称
            description: 技能描述

        Returns:
            完整的SkillManifest对象
        """
        base = Path(source_dir) if source_dir else self._skill_root
        if not base.exists():
            raise PackingError(f"源目录不存在: {base}")

        entries: list[ManifestEntry] = []
        total_size: int = 0

        for file_path in self._iter_files(base):
            try:
                stat = file_path.stat()
                size = stat.st_size
                sha = self._compute_sha256(file_path)
                rel_path = str(file_path.relative_to(base)).replace(os.sep, "/")
                ftype = self._detect_type(file_path)
                mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()

                entry = ManifestEntry(
                    path=rel_path,
                    size_bytes=size,
                    sha256=sha,
                    file_type=ftype,
                    last_modified=mtime,
                )
                entries.append(entry)
                total_size += size
            except OSError as e:
                print(f"⚠️ 无法读取文件 {file_path}: {e}")

        ver_str = version_info.version_string if version_info else "1.0.0"

        manifest = SkillManifest(
            skill_name=skill_name,
            skill_version=ver_str,
            description=description or f"{skill_name} - Universal DevOps技能集",
            author="skiller-meta",
            total_files=len(entries),
            total_size_bytes=total_size,
            entries=sorted(entries, key=lambda e: e.path),
            dependencies=dependencies or [],
            skill_metadata={
                "total_subskills": 32,
                "architecture": "二十四司三省制",
                "python_version": "3.10+",
                "generated_by": "meta_skill/skill_packer",
            },
        )

        if version_info:
            manifest.skill_metadata["version_info"] = version_info.to_dict()

        return manifest

    def _iter_files(self, base: Path):
        """遍历目录下的所有文件，排除不需要的文件"""
        for item in base.rglob("*"):
            if not item.is_file():
                continue
            rel_str = str(item.relative_to(base))

            skip = False
            for pattern in self.EXCLUDE_PATTERNS:
                if pattern.startswith("*"):
                    if item.match(pattern) or item.suffix == pattern[1:]:
                        skip = True
                        break
                elif pattern in rel_str or pattern in item.name:
                    skip = True
                    break

            parts = Path(rel_str).parts
            if any(p.startswith(".") or p == "__pycache__" for p in parts):
                skip = True

            if not skip:
                yield item

    @staticmethod
    def _compute_sha256(file_path: Path) -> str:
        """计算文件的SHA256哈希值"""
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    @staticmethod
    def _detect_type(file_path: Path) -> str:
        """检测文件类型"""
        suffix_map = {
            ".py": "python",
            ".md": "markdown",
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".txt": "text",
            ".cfg": "config",
            ".ini": "config",
            ".toml": "config",
            ".html": "html",
            ".css": "css",
            ".js": "javascript",
            ".sh": "shell",
            ".bat": "batch",
        }
        return suffix_map.get(file_path.suffix.lower(), "binary")


class VersionMetaManager:
    """
    版本元数据管理器

    基于SemVer规范进行版本号管理、变更追踪和发布记录。
    """

    VERSION_FILE_NAME: str = "VERSION.json"
    CHANGELOG_FILE_NAME: str = "CHANGELOG.md"

    def __init__(self, meta_dir: Path | str | None = None) -> None:
        self._meta_dir: Path = (
            Path(meta_dir).resolve() if meta_dir
            else Path(__file__).parent.resolve()
        )
        self._version_history: list[VersionInfo] = []
        self._current_version: VersionInfo = VersionInfo()
        self._load_version_data()

    def _load_version_data(self) -> None:
        """加载已有的版本数据"""
        version_file = self._meta_dir / self.VERSION_FILE_NAME
        if version_file.exists():
            try:
                with open(version_file, "r", encoding="utf-8") as f:
                    data: dict[str, Any] = json.load(f)
                current = data.get("current", {})
                ver_parts = current.get("version", "1.0.0").split(".")
                self._current_version = VersionInfo(
                    major=int(ver_parts[0]) if len(ver_parts) > 0 else 1,
                    minor=int(ver_parts[1]) if len(ver_parts) > 1 else 0,
                    patch=int(ver_parts[2].split("-")[0]) if len(ver_parts) > 2 else 0,
                    pre_release=current.get("pre_release", ""),
                    build_metadata=current.get("build_metadata", ""),
                    release_notes=current.get("release_notes", ""),
                )
                for hist in data.get("history", []):
                    h_parts = hist.get("version", "1.0.0").split(".")
                    self._version_history.append(VersionInfo(
                        major=int(h_parts[0]) if len(h_parts) > 0 else 1,
                        minor=int(h_parts[1]) if len(h_parts) > 1 else 0,
                        patch=int(h_parts[2].split("-")[0]) if len(h_parts) > 2 else 0,
                        pre_release=hist.get("pre_release", ""),
                        build_metadata=hist.get("build_metadata", ""),
                        release_notes=hist.get("release_notes", ""),
                        changed_files=hist.get("changed_files", []),
                        changed_dependencies=hist.get("changed_dependencies", []),
                        timestamp=hist.get("timestamp", ""),
                    ))
            except (OSError, json.JSONDecodeError, ValueError, IndexError):
                pass

    @property
    def current_version(self) -> VersionInfo:
        return self._current_version

    @property
    def version_string(self) -> str:
        return self._current_version.version_string

    def bump_version(
        self, level: str = "patch", notes: str = "", files: list[str] | None = None
    ) -> VersionInfo:
        """
        执行版本升级

        Args:
            level: 升级级别 ('major', 'minor', 'patch')
            notes: 变更说明
            files: 变更的文件列表

        Returns:
            新的VersionInfo对象
        """
        old_version = self._current_version

        match level.lower():
            case "major":
                new_version = old_version.bump_major()
            case "minor":
                new_version = old_version.bump_minor()
            case "patch":
                new_version = old_version.bump_patch()
            case _:
                raise PackingError(f"不支持的版本升级级别: {level}")

        if notes:
            new_version.release_notes = notes
        if files:
            new_version.changed_files = files

        self._version_history.append(old_version)
        self._current_version = new_version
        self._save_version_data()

        print(f"📦 版本升级: {old_version.version_string} → {new_version.version_string}")
        return new_version

    def add_change_record(
        self, change_type: str, description: str, files: list[str] | None = None
    ) -> None:
        """
        添加变更记录

        Args:
            change_type: 变更类型 ('added', 'changed', 'deprecated', 'removed', 'fixed', 'security')
            description: 变更描述
            files: 涉及的文件列表
        """
        changelog_path = self._meta_dir / self.CHANGELOG_FILE_NAME
        entry_date = datetime.now().strftime("%Y-%m-%d")
        entry = f"### [{change_type.upper()}] - {entry_date}\n- {description}\n"
        if files:
            entry += f"  文件: {', '.join(files)}\n"

        mode = "a" if changelog_path.exists() else "w"
        with open(changelog_path, mode, encoding="utf-8") as f:
            if mode == "w":
                f.write("# Changelog\n\n")
            f.write(entry + "\n")

    def get_version_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取版本历史"""
        history = list(reversed(self._version_history[-limit:]))
        history.insert(0, self._current_version)
        return [v.to_dict() for v in history]

    def _save_version_data(self) -> None:
        """保存版本数据到文件"""
        version_file = self._meta_dir / self.VERSION_FILE_NAME
        data: dict[str, Any] = {
            "current": self._current_version.to_dict(),
            "history": [v.to_dict() for v in self._version_history[-50:]],
            "last_updated": datetime.now().isoformat(),
        }
        version_file.parent.mkdir(parents=True, exist_ok=True)
        with open(version_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


class SkillExporter:
    """
    技能导出器

    将整个技能目录打包为标准.skill格式（基于zip/tar.gz）。
    """

    SUPPORTED_FORMATS: dict[str, tuple[str, str]] = {
        "skill": (".skill", "application/vnd.universal-devops+zip"),
        "tar.gz": (".tar.gz", "application/gzip"),
        "zip": (".zip", "application/zip"),
    }

    def __init__(self, skill_root: Path | str | None = None) -> None:
        self._skill_root: Path = (
            Path(skill_root).resolve() if skill_root
            else Path(__file__).parent.parent.parent.resolve()
        )
        self._export_history: list[dict[str, Any]] = []

    def pack(
        self,
        output_path: Path | str,
        version: str = "1.0.0",
        format_type: str = "skill",
        include_meta: bool = True,
        exclude_patterns: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        将技能目录打包为指定格式的文件

        Args:
            output_path: 输出文件路径
            version: 版本号
            format_type: 打包格式 ('skill', 'tar.gz', 'zip')
            include_meta: 是否包含元数据文件（manifest, version等）
            exclude_patterns: 额外的排除模式列表

        Returns:
            打包结果字典
        """
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        if format_type not in self.SUPPORTED_FORMATS:
            supported = ", ".join(self.SUPPORTED_FORMATS.keys())
            raise PackingError(f"不支持的打包格式: {format_type}。支持: {supported}")

        ext, mime = self.SUPPORTED_FORMATS[format_type]
        if output.suffix != ext:
            output = output.with_suffix(ext)

        dc = DependencyCollector(self._skill_root)
        dep_result = dc.scan_directory()

        mg = ManifestGenerator(self._skill_root)
        vm = VersionMetaManager(self._skill_root / "skillscripts" / "meta_skill")

        version_info = vm.current_version
        if version != "auto" and version != vm.version_string:
            parsed = self._parse_version(version)
            if parsed:
                version_info = VersionInfo(
                    major=parsed[0], minor=parsed[1], patch=parsed[2],
                )

        deps = [
            DependencyInfo(name=k, **v.to_dict())
            for k, v in dc._internal_deps.items()
        ]

        manifest = mg.generate_manifest(
            source_dir=self._skill_root,
            version_info=version_info,
            dependencies=deps,
            skill_name="universal-devops",
            description="Universal DevOps - 二十四司三省制DevOps全流程技能体系",
        )

        match format_type:
            case "skill":
                self._pack_zip(output, manifest, include_meta, exclude_patterns)
            case "zip":
                self._pack_zip(output, manifest, include_meta, exclude_patterns)
            case "tar.gz":
                self._pack_tar_gz(output, manifest, include_meta, exclude_patterns)

        result: dict[str, Any] = {
            "output_path": str(output),
            "format": format_type,
            "size_bytes": output.stat().st_size if output.exists() else 0,
            "version": version_info.version_string,
            "total_files": manifest.total_files,
            "total_size_uncompressed": manifest.total_size_bytes,
            "manifest": manifest.to_dict(),
            "dependency_summary": {
                "internal": len(deps),
                "external": len(dep_result.get("external_dependencies", [])),
            },
            "packed_at": datetime.now().isoformat(),
        }

        self._export_history.append(result)
        print(f"✅ 打包完成: {output} ({result['size_bytes']} bytes)")
        return result

    def _pack_zip(
        self, output: Path, manifest: SkillManifest,
        include_meta: bool, exclude_patterns: list[str] | None,
    ) -> None:
        """使用zip格式打包"""
        all_exclude = list(ManifestGenerator.EXCLUDE_PATTERNS) + (exclude_patterns or [])

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in self._iter_packable_files(all_exclude):
                arc_name = file_path.relative_to(self._skill_root)
                zf.write(file_path, arc_name)

            if include_meta:
                manifest_content = manifest.to_json().encode("utf-8")
                zf.writestr("META-INF/manifest.json", manifest_content)

                version_content = json.dumps({
                    "version": manifest.skill_version,
                    "packed_at": manifest.created_at,
                    "generator": "meta_skill/skill_packer",
                }, indent=2, ensure_ascii=False).encode("utf-8")
                zf.writestr("META-INF/version.json", version_content)

    def _pack_tar_gz(
        self, output: Path, manifest: SkillManifest,
        include_meta: bool, exclude_patterns: list[str] | None,
    ) -> None:
        """使用tar.gz格式打包"""
        all_exclude = list(ManifestGenerator.EXCLUDE_PATTERNS) + (exclude_patterns or [])

        with tarfile.open(output, "w:gz") as tf:
            for file_path in self._iter_packable_files(all_exclude):
                arc_name = file_path.relative_to(self._skill_root)
                tf.add(file_path, arcname)

            if include_meta:
                manifest_bytes = manifest.to_json().encode("utf-8")
                info = tarfile.TarInfo(name="META-INF/manifest.json")
                info.size = len(manifest_bytes)
                info.mtime = int(datetime.now().timestamp())
                tf.addfile(info, io.BytesIO(manifest_bytes))

    def _iter_packable_files(self, extra_exclude: list[str]):
        """迭代可打包的文件"""
        for item in self._skill_root.rglob("*"):
            if not item.is_file():
                continue
            rel_str = str(item.relative_to(self._skill_root))

            skip = False
            for pattern in ManifestGenerator.EXCLUDE_PATTERNS + extra_exclude:
                if pattern.startswith("*"):
                    if item.name.endswith(pattern[1:]) or item.suffix == pattern[1:]:
                        skip = True
                        break
                elif pattern in rel_str:
                    skip = True
                    break

            parts = Path(rel_str).parts
            if any(p.startswith(".") or p == "__pycache__" for p in parts):
                skip = True

            if not skip:
                yield item

    @staticmethod
    def _parse_version(version_str: str) -> tuple[int, int, int] | None:
        """解析版本字符串"""
        match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version_str.strip())
        if match:
            return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        return None

    def get_export_history(self, limit: int = 10) -> list[dict[str, Any]]:
        """获取导出历史"""
        return list(reversed(self._export_history[-limit:]))

    def verify_package(self, package_path: Path | str) -> dict[str, Any]:
        """
        验证已打包的.skill文件完整性

        Args:
            package_path: 打包文件路径

        Returns:
            验证结果字典
        """
        pkg = Path(package_path)
        if not pkg.exists():
            return {"valid": False, "error": f"文件不存在: {pkg}"}

        result: dict[str, Any] = {
            "valid": True,
            "package_path": str(pkg),
            "size_bytes": pkg.stat().st_size,
            "contains_manifest": False,
            "contains_version": False,
            "file_count": 0,
            "errors": [],
            "warnings": [],
        }

        try:
            if pkg.suffix == ".skill" or pkg.suffix == ".zip":
                with zipfile.ZipFile(pkg, "r") as zf:
                    names = zf.namelist()
                    result["file_count"] = len(names)
                    result["contains_manifest"] = "META-INF/manifest.json" in names
                    result["contains_version"] = "META-INF/version.json" in names

                    bad = zf.testzip()
                    if bad:
                        result["valid"] = False
                        result["errors"].append(f"损坏的文件: {bad}")

            elif pkg.name.endswith(".tar.gz") or pkg.suffixes == [".tar", ".gz"]:
                with tarfile.open(pkg, "r:gz") as tf:
                    members = tf.getmembers()
                    result["file_count"] = len(members)
                    result["contains_manifest"] = any(
                        m.name == "META-INF/manifest.json" for m in members
                    )

            else:
                result["valid"] = False
                result["errors"].append(f"不支持的文件格式: {pkg.suffix}")

        except (zipfile.BadZipFile, tarfile.TarError, OSError) as e:
            result["valid"] = False
            result["errors"].append(str(e))

        if not result["contains_manifest"]:
            result["warnings"].append("缺少META-INF/manifest.json清单文件")

        return result


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 技能打包器 - 功能演示")
    print("=" * 60)

    skill_root = Path(__file__).parent.parent.parent

    print("\n--- 依赖收集 ---\n")
    dc = DependencyCollector(skill_root)
    scan_result = dc.scan_directory()
    print(f"   扫描目录: {scan_result['scanned_directory']}")
    print(f"   Python文件数: {scan_result['total_python_files']}")
    print(f"   模块总数: {scan_result['total_modules']}")
    print(f"   内部依赖: {scan_result['total_internal_dependencies']}")
    print(f"   外部依赖: {scan_result['total_external_dependencies']}")
    print(f"   平均依赖/模块: {scan_result['average_dependencies_per_module']}")
    print(f"   外部依赖列表: {scan_result['external_dependencies'][:10]}...")

    print("\n--- 依赖树 ---\n")
    dep_tree = dc.get_dependency_tree()
    print(f"   根模块 ({len(dep_tree['root_modules'])}): {dep_tree['root_modules'][:5]}")

    print("\n--- 循环依赖检测 ---\n")
    cycles = dc.get_circular_dependencies()
    print(f"   发现循环依赖: {len(cycles)} 组")
    for c in cycles[:3]:
        print(f"      {' → '.join(c)}")

    print("\n--- 清单生成 ---\n")
    mg = ManifestGenerator(skill_root)
    manifest = mg.generate_manifest(description="Universal DevOps技能集演示版")
    print(f"   技能名: {manifest.skill_name}")
    print(f"   版本: {manifest.skill_version}")
    print(f"   文件数: {manifest.total_files}")
    print(f"   总大小: {manifest.total_size_bytes:,} bytes")
    print(f"   条目示例:")
    for entry in manifest.entries[:5]:
        print(f"      [{entry.file_type}] {entry.path} ({entry.size_bytes:,}B)")

    print("\n--- 版本管理 ---\n")
    vm = VersionMetaManager(skill_root / "skillscripts" / "meta_skill")
    print(f"   当前版本: {vm.version_string}")
    v1 = vm.bump_version("patch", "修复了演示问题", ["meta_skill/*.py"])
    print(f"   升级后: {vm.version_string}")
    v2 = vm.bump_version("minor", "新增自扩展能力", ["self_extender.py"])
    print(f"   再升级: {vm.version_string}")
    vm.add_change_record("added", "新增元技能层模块", ["meta_skill/"])
    history = vm.get_version_history(5)
    print(f"   版本历史 ({len(history)} 条):")
    for h in history:
        print(f"      {h['version']}: {h['release_notes'][:40]}")

    print("\n--- 技能导出 ---\n")
    exporter = SkillExporter(skill_root)
    output_base = skill_root / "output" / "packed_skills"

    pack_result = exporter.pack(
        output_path=output_base / "universal-devops-demo",
        version=v2.version_string,
        format_type="skill",
    )
    print(f"   格式: {pack_result['format']}")
    print(f"   路径: {pack_result['output_path']}")
    print(f"   大小: {pack_result['size_bytes']:,} bytes")
    print(f"   文件数: {pack_result['total_files']}")

    verification = exporter.verify_package(pack_result["output_path"])
    print(f"\n--- 包验证 ---\n")
    print(f"   有效: {verification['valid']}")
    print(f"   文件数: {verification['file_count']}")
    print(f"   含清单: {verification['contains_manifest']}")
    print(f"   含版本: {verification['contains_version']}")
    if verification["errors"]:
        for err in verification["errors"]:
            print(f"   ❌ 错误: {err}")
    if verification["warnings"]:
        for warn in verification["warnings"]:
            print(f"   ⚠️ 警告: {warn}")

    print("\n✅ 所有演示通过!")
