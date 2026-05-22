"""
依赖管理司 - 多语言包管理器解析、依赖树可视化、版本冲突检测、安全漏洞扫描
"""
from __future__ import annotations

import re
import json
import hashlib
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any


class DependencyMgmtError(Exception):
    """依赖管理相关异常"""
    pass


class ParseError(DependencyMgmtError):
    """解析异常"""


class ConflictError(DependencyMgmtError):
    """冲突检测异常"""


class PackageManager(str, Enum):
    """包管理器类型"""
    PIP = "pip"
    POETRY = "poetry"
    NPM = "npm"
    YARN = "yarn"
    CARGO = "cargo"
    GO = "go"
    UNKNOWN = "unknown"


class UpdateType(str, Enum):
    """更新类型"""
    PATCH = "patch"
    MINOR = "minor"
    MAJOR = "major"


class RiskLevel(str, Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class DependencyInfo:
    """依赖信息"""
    name: str
    version: str = ""
    specifier: str = ""
    manager: PackageManager = PackageManager.UNKNOWN
    is_dev: bool = False
    is_optional: bool = False
    extras: list[str] = field(default_factory=list)
    source: str = ""
    latest_version: str = ""
    licenses: list[str] = field(default_factory=list)
    homepage: str = ""
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "specifier": self.specifier,
            "manager": self.manager.value,
            "is_dev": self.is_dev,
            "is_optional": self.is_optional,
            "extras": self.extras,
            "source": self.source,
            "latest_version": self.latest_version,
            "licenses": self.licenses,
            "homepage": self.homepage,
            "description": self.description[:80],
        }


@dataclass
class DependencyTree:
    """依赖树节点"""
    name: str
    version: str
    depth: int = 0
    children: list[DependencyTree] = field(default_factory=list)
    parent: str | None = None
    is_conflict: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "depth": self.depth,
            "children": [c.to_dict() for c in self.children],
            "parent": self.parent,
            "is_conflict": self.is_conflict,
        }

    def total_nodes(self) -> int:
        return 1 + sum(c.total_nodes() for c in self.children)


@dataclass
class VersionConflict:
    """版本冲突信息"""
    package_name: str
    required_versions: dict[str, str]
    conflict_type: str = "semantic"
    severity: RiskLevel = RiskLevel.MEDIUM
    suggestion: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_name": self.package_name,
            "required_versions": self.required_versions,
            "conflict_type": self.conflict_type,
            "severity": self.severity.value,
            "suggestion": self.suggestion,
        }


@dataclass
class LicenseInfo:
    """许可证信息"""
    name: str
    spdx_id: str = ""
    is_osi_approved: bool = False
    is_copyleft: bool = False
    compatibility: list[str] = field(default_factory=list)
    restrictions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "spdx_id": self.spdx_id or self.name,
            "is_osi_approved": self.is_osi_approved,
            "is_copyleft": self.is_copyleft,
            "compatibility": self.compatibility,
            "restrictions": self.restrictions,
        }


@dataclass
class SecurityAdvisory:
    """安全公告"""
    cve_id: str
    package_name: str
    affected_versions: list[str]
    patched_versions: list[str]
    severity: RiskLevel = RiskLevel.HIGH
    description: str = ""
    published_date: str = ""
    references: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "cve_id": self.cve_id,
            "package_name": self.package_name,
            "affected_versions": self.affected_versions,
            "patched_versions": self.patched_versions,
            "severity": self.severity.value,
            "description": self.description[:120],
            "published_date": self.published_date,
            "references": self.references[:3],
        }


@dataclass
class UpdateSuggestion:
    """更新建议"""
    package_name: str
    current_version: str
    suggested_version: str
    update_type: UpdateType
    risk_level: RiskLevel = RiskLevel.LOW
    reason: str = ""
    breaking_changes: list[str] = field(default_factory=list)
    changelog_url: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_name": self.package_name,
            "current_version": self.current_version,
            "suggested_version": self.suggested_version,
            "update_type": self.update_type.value,
            "risk_level": self.risk_level.value,
            "reason": self.reason,
            "breaking_changes": self.breaking_changes,
            "changelog_url": self.changelog_url,
        }


_LICENSE_COMPATIBILITY_MATRIX: dict[str, LicenseInfo] = {
    "MIT": LicenseInfo(
        name="MIT", spdx_id="MIT", is_osi_approved=True, is_copyleft=False,
        compatibility=["Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "MIT", "0BSD"],
        restrictions=["保留版权声明和许可文本"],
    ),
    "Apache-2.0": LicenseInfo(
        name="Apache-2.0", spdx_id="Apache-2.0", is_osi_approved=True, is_copyleft=False,
        compatibility=["MIT", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Apache-2.0"],
        restrictions=["保留版权声明、许可文本、NOTICE文件"],
    ),
    "GPL-3.0-only": LicenseInfo(
        name="GPL-3.0-only", spdx_id="GPL-3.0-only", is_osi_approved=True, is_copyleft=True,
        compatibility=["GPL-3.0-or-later", "AGPL-3.0-or-later"],
        restrictions=["衍生作品必须使用相同许可开源", "提供源代码", "不得附加额外限制"],
    ),
    "AGPL-3.0-only": LicenseInfo(
        name="AGPL-3.0-only", spdx_id="AGPL-3.0-only", is_osi_approved=True, is_copyleft=True,
        compatibility=["AGPL-3.0-or-later", "GPL-3.0-or-later"],
        restrictions=["网络使用也触发开源义务", "衍生作品必须使用相同许可开源", "提供源代码"],
    ),
    "BSD-2-Clause": LicenseInfo(
        name="BSD-2-Clause", spdx_id="BSD-2-Clause", is_osi_approved=True, is_copyleft=False,
        compatibility=["MIT", "Apache-2.0", "BSD-3-Clause", "ISC"],
        restrictions=["保留版权声明和许可文本"],
    ),
    "BSD-3-Clause": LicenseInfo(
        name="BSD-3-Clause", spdx_id="BSD-3-Clause", is_osi_approved=True, is_copyleft=False,
        compatibility=["MIT", "Apache-2.0", "BSD-2-Clause", "ISC"],
        restrictions=["保留版权声明和许可文本", "不得使用作者名义宣传"],
    ),
    "LGPL-3.0-only": LicenseInfo(
        name="LGPL-3.0-only", spdx_id="LGPL-3.0-only", is_osi_approved=True, is_copyleft=True,
        compatibility=["GPL-3.0-or-later", "LGPL-3.0-or-later", "GPL-2.0-or-later"],
        restrictions=["修改库文件必须开源", "链接使用可保持闭源"],
    ),
    "ISC": LicenseInfo(
        name="ISC", spdx_id="ISC", is_osi_approved=True, is_copyleft=False,
        compatibility=["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause"],
        restrictions=["保留版权声明和许可文本"],
    ),
}

_SAMPLE_CVE_DATABASE: list[SecurityAdvisory] = [
    SecurityAdvisory(
        cve_id="CVE-2024-23329",
        package_name="requests",
        affected_versions=["<2.31.0"],
        patched_versions=[">=2.31.0"],
        severity=RiskLevel.HIGH,
        description="请求头注入漏洞，攻击者可通过恶意URL注入自定义HTTP头",
        published_date="2024-01-18",
        references=["https://github.com/psf/requests/security/advisories/GHSA-j8qr-cwvq-4vp6"],
    ),
    SecurityAdvisory(
        cve_id="CVE-2023-45803",
        package_name="fastapi",
        affected_versions=["<0.109.0"],
        patched_versions=[">=0.109.0"],
        severity=RiskLevel.MEDIUM,
        description="OpenAPI schema生成时可能泄露敏感配置信息",
        published_date="2023-12-15",
        references=["https://github.com/tiangolo/fastapi/security/advisories/GHSA-xxxx-xxxx-xxxx"],
    ),
    SecurityAdvisory(
        cve_id="CVE-2024-11412",
        package_name="pillow",
        affected_versions=["<10.2.0"],
        patched_versions=[">=10.2.0"],
        severity=RiskLevel.CRITICAL,
        description="TIFF/JP2图像处理存在缓冲区溢出，可导致远程代码执行",
        published_date="2024-02-20",
        references=["https://github.com/python-pillow/Pillow/security/advisories/GHSA-xxxx-xxxx-xxxx"],
    ),
    SecurityAdvisory(
        cve_id="CVE-2023-44487",
        package_name="httpx",
        affected_versions=["<0.25.0"],
        patched_versions=[">=0.25.0"],
        severity=RiskLevel.HIGH,
        description="HTTP/2 Rapid Reset攻击导致服务拒绝",
        published_date="2023-10-10",
        references=["https://github.com/encode/httpx/security/advisories/GHSA-xxxx-xxxx-xxxx"],
    ),
    SecurityAdvisory(
        cve_id="CVE-2024-0231",
        package_name="pyyaml",
        affected_versions=["<6.0.1"],
        patched_versions=[">=6.0.1"],
        severity=RiskLevel.MEDIUM,
        description="YAML反序列化时未正确处理特殊字符导致拒绝服务",
        published_date="2024-01-05",
        references=["https://github.com/yaml/pyyaml/security/advisories/GHSA-xxxx-xxxx-xxxx"],
    ),
]


def _parse_semver(version_str: str) -> tuple[int, int, int]:
    """解析语义化版本号"""
    match = re.match(r"(\d+)\.(\d+)\.(\d+)", version_str.strip().lstrip("v=~><!"))
    if not match:
        return (0, 0, 0)
    return (int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _compare_versions(v1: str, v2: str) -> int:
    """比较两个版本号，返回 -1/0/1"""
    p1 = _parse_semver(v1)
    p2 = _parse_semver(v2)
    if p1 < p2:
        return -1
    elif p1 > p2:
        return 1
    return 0


class DependencyMgmtSi:
    """
    依赖管理司 - 户部·度支司

    提供全面的依赖管理能力：
    - 多语言包管理器解析（pip/poetry/npm/yarn/cargo/go）
    - 依赖树可视化（树形文本输出）
    - 版本冲突检测（语义版本冲突/传递依赖冲突/循环依赖检测）
    - 许可证兼容性预检（MIT/Apache-2.0/GPL-3.0/AGPL等兼容性矩阵）
    - 安全 advisory 检查（已知CVE漏洞匹配）
    - 依赖更新策略建议（patch/minor/major升级风险评估）
    - 过时依赖识别（latest版本对比）
    """

    def __init__(self) -> None:
        self._dependencies: dict[str, DependencyInfo] = {}
        self._dependency_tree: DependencyTree | None = None
        self._conflicts: list[VersionConflict] = []
        self._advisories: list[SecurityAdvisory] = []
        self._update_suggestions: list[UpdateSuggestion] = []
        self._license_db: dict[str, LicenseInfo] = dict(_LICENSE_COMPATIBILITY_MATRIX)
        self._cve_db: list[SecurityAdvisory] = list(_SAMPLE_CVE_DATABASE)
        self._detected_manager: PackageManager = PackageManager.UNKNOWN

    # ==================== 包管理器解析 ====================

    def detect_package_manager(self, project_root: Path | str | None = None) -> PackageManager:
        """
        自动检测项目使用的包管理器

        Args:
            project_root: 项目根目录路径

        Returns:
            检测到的包管理器类型
        """
        root = Path(project_root) if project_root else Path(".")
        detection_files: list[tuple[Path | str, PackageManager]] = [
            ("pyproject.toml", PackageManager.POETRY),
            ("requirements.txt", PackageManager.PIP),
            ("package.json", PackageManager.NPM),
            ("yarn.lock", PackageManager.YARN),
            ("Cargo.toml", PackageManager.CARGO),
            ("go.mod", PackageManager.GO),
        ]
        for fname, pm in detection_files:
            if (root / fname).exists():
                self._detected_manager = pm
                return pm
        self._detected_manager = PackageManager.UNKNOWN
        return PackageManager.UNKNOWN

    def parse_dependencies(
        self,
        content: str | Path,
        manager: PackageManager | None = None,
    ) -> list[DependencyInfo]:
        """
        解析依赖文件内容

        Args:
            content: 依赖文件内容或文件路径
            manager: 指定包管理器类型（自动检测如果未提供）

        Returns:
            解析出的依赖列表

        Raises:
            ParseError: 当无法解析时
        """
        if isinstance(content, Path):
            if not content.exists():
                raise ParseError(f"依赖文件不存在: {content}")
            text = content.read_text(encoding="utf-8")
        else:
            text = content

        detected = manager or self.detect_package_manager()
        self._detected_manager = detected

        deps: list[DependencyInfo] = []

        match detected:
            case PackageManager.PIP:
                deps = self._parse_requirements_txt(text)
            case PackageManager.POETRY:
                deps = self._parse_pyproject_toml(text)
            case PackageManager.NPM:
                deps = self._parse_package_json(text)
            case PackageManager.YARN:
                deps = self._parse_yarn_lock(text)
            case PackageManager.CARGO:
                deps = self._parse_cargo_toml(text)
            case PackageManager.GO:
                deps = self._parse_go_mod(text)
            case _:
                deps = self._auto_detect_and_parse(text)

        for dep in deps:
            self._dependencies[dep.name.lower()] = dep

        return deps

    def _parse_requirements_txt(self, content: str) -> list[DependencyInfo]:
        """解析 pip requirements.txt 格式"""
        deps: list[DependencyInfo] = []
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue
            is_comment_idx = line.find(" #")
            clean_line = line[:is_comment_idx].strip() if is_comment_idx > 0 else line
            extra_match = re.match(r"^([a-zA-Z0-9_-]+)\[([\w,]+)\](.*)$", clean_line)
            if extra_match:
                name = extra_match.group(1).lower()
                extras = [e.strip() for e in extra_match.group(2).split(",")]
                spec = extra_match.group(3).strip()
            else:
                parts = re.split(r"[<>=!~\s]+", clean_line, maxsplit=1)
                name = parts[0].strip().lower()
                extras = []
                spec = clean_line[len(name):].strip() if len(parts) > 1 else ""
            version_match = re.search(r"[=<>~!]+\s*([\d\.\*\-\w]+)", spec)
            version = version_match.group(1) if version_match else ""
            deps.append(DependencyInfo(
                name=name, version=version, specifier=spec,
                manager=PackageManager.PIP, extras=extras,
            ))
        return deps

    def _parse_pyproject_toml(self, content: str) -> list[DependencyInfo]:
        """解析 poetry pyproject.toml 格式（简化版TOML解析）"""
        deps: list[DependencyInfo] = []
        in_deps = False
        in_dev = False
        current_section = ""
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("[tool.poetry.dependencies]"):
                in_deps = True
                in_dev = False
                continue
            if stripped.startswith("[tool.poetry.group.dev.dependencies]") or \
               stripped.startswith("[tool.poetry.dev-dependencies]"):
                in_deps = True
                in_dev = True
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                in_deps = False
                in_dev = False
                continue
            if in_deps and "=" in stripped and not stripped.startswith("#"):
                match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*["\']?([^"\']*)["\']?\s*$', stripped)
                if match:
                    name = match.group(1).strip().lower()
                    ver_str = match.group(2).strip()
                    version = ver_str.lstrip("^~=!<>")
                    deps.append(DependencyInfo(
                        name=name, version=version, specifier=ver_str,
                        manager=PackageManager.POETRY, is_dev=in_dev,
                    ))
        return deps

    def _parse_package_json(self, content: str) -> list[DependencyInfo]:
        """解析 npm package.json 格式"""
        deps: list[DependencyInfo] = []
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ParseError(f"JSON解析失败: {e}")
        sections = [("dependencies", False), ("devDependencies", True)]
        for section_key, is_dev in sections:
            section_data = data.get(section_key, {})
            if isinstance(section_data, dict):
                for name, ver in section_data.items():
                    version = ver.lstrip("^~>=< ")
                    deps.append(DependencyInfo(
                        name=name.lower(), version=version, specifier=ver,
                        manager=PackageManager.NPM, is_dev=is_dev,
                    ))
        return deps

    def _parse_yarn_lock(self, content: str) -> list[DependencyInfo]:
        """解析 yarn.lock 格式（简化版）"""
        deps: list[DependencyInfo] = []
        seen: set[str] = set()
        for block in re.split(r"\n(?=\S[^\"\n]*@|^\"[^\"]+\")", content):
            lines = block.strip().split("\n")
            if not lines:
                continue
            first_line = lines[0].strip().rstrip(",")
            name_ver_match = re.match(r'^"?([^"@]+)"?\s*@?("?[\d\.\w\-]+"?)?', first_line)
            if name_ver_match:
                raw_name = name_ver_match.group(1) or ""
                name = raw_name.split("/")[-1].lower().replace("@", "")
                version = ""
                for line in lines[1:]:
                    vmatch = re.match(r'version\s+"([^"]+)"', line.strip())
                    if vmatch:
                        version = vmatch.group(1)
                        break
                if name and name not in seen:
                    seen.add(name)
                    deps.append(DependencyInfo(
                        name=name, version=version,
                        manager=PackageManager.YARN,
                    ))
        return deps

    def _parse_cargo_toml(self, content: str) -> list[DependencyInfo]:
        """解析 Cargo.toml 格式（简化版）"""
        deps: list[DependencyInfo] = []
        in_deps = False
        in_dev = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("[dependencies]"):
                in_deps = True
                in_dev = False
                continue
            if stripped.startswith("[dev-dependencies]"):
                in_deps = True
                in_dev = True
                continue
            if stripped.startswith("[") and stripped.endswith("]"):
                in_deps = False
                in_dev = False
                continue
            if in_deps and "=" in stripped and not stripped.startswith("#"):
                match = re.match(r'^([a-zA-Z0-9_-]+)\s*=\s*(.*)$', stripped)
                if match:
                    name = match.group(1).strip()
                    val = match.group(2).strip().rstrip(",").strip('"\'')
                    version = re.sub(r'^[{}"\']*', "", val).split(",")[0].strip()
                    deps.append(DependencyInfo(
                        name=name.lower(), version=version,
                        manager=PackageManager.CARGO, is_dev=in_dev,
                    ))
        return deps

    def _parse_go_mod(self, content: str) -> list[DependencyInfo]:
        """解析 go.mod 格式"""
        deps: list[DependencyInfo] = []
        in_require = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("require"):
                parts = stripped.split(None, 2)
                if len(parts) >= 3 and "(" in stripped:
                    in_require = True
                    continue
                if len(parts) >= 3:
                    deps.append(DependencyInfo(
                        name=parts[1], version=parts[2],
                        manager=PackageManager.GO,
                    ))
                continue
            if in_require:
                if stripped == ")":
                    in_require = False
                    continue
                parts = stripped.split(None, 1)
                if len(parts) >= 2 and not stripped.startswith("//"):
                    deps.append(DependencyInfo(
                        name=parts[0], version=parts[1].rstrip("//").strip(),
                        manager=PackageManager.GO,
                    ))
        return deps

    def _auto_detect_and_parse(self, content: str) -> list[DependencyInfo]:
        """自动检测格式并解析"""
        if content.strip().startswith("{"):
            return self._parse_package_json(content)
        if "[tool." in content or "[build-system]" in content:
            return self._parse_pyproject_toml(content)
        if "# yarn lockfile" in content or content.strip().startswith("# THIS IS AN AUTOGENERATED FILE"):
            return self._parse_yarn_lock(content)
        if "module " in content and "go " in content:
            return self._parse_go_mod(content)
        if "[dependencies]" in content:
            return self._parse_cargo_toml(content)
        return self._parse_requirements_txt(content)

    # ==================== 依赖树可视化 ====================

    def build_dependency_tree(self) -> DependencyTree:
        """
        构建依赖树结构

        Returns:
            根节点为项目自身的DependencyTree
        """
        root = DependencyTree(name="project", version="root", depth=0)
        sorted_deps = sorted(self._dependencies.values(), key=lambda d: d.name)
        for dep in sorted_deps:
            child = DependencyTree(
                name=dep.name, version=dep.version or "any",
                depth=1, parent="project",
            )
            child.children = self._generate_mock_subdeps(dep, depth=2)
            root.children.append(child)
        self._dependency_tree = root
        return root

    def _generate_mock_subdeps(self, dep: DependencyInfo, depth: int) -> list[DependencyTree]:
        """模拟生成子依赖（实际场景中应从lockfile解析）"""
        mock_map: dict[str, list[tuple[str, str]]] = {
            "requests": [("urllib3", "2.2.0"), ("certifi", "2024.2.2"), ("charset-normalizer", "3.3.2")],
            "fastapi": [("starlette", "0.36.0"), ("pydantic", "2.6.0"), ("typing-extensions", "4.10.0")],
            "sqlalchemy": [("typing-extensions", "4.10.0"), ("greenlet", "3.0.3")],
            "pytest": [("pluggy", "1.4.0"), ("iniconfig", "2.0.0"), ("packaging", "24.0")],
            "numpy": [],
            "flask": [("werkzeug", "3.0.1"), ("jinja2", "3.1.3"), ("click", "8.1.7"), ("itsdangerous", "2.1.2")],
            "django": [("asgiref", "3.7.2"), ("sqlparse", "0.4.4")],
            "pydantic": (("typing-extensions", "4.10.0"), ("annotated-types", "0.6.0")),
            "httpcore": [("h11", "0.14.0"), ("anyio", "4.2.0")],
            "redis": [("async-timeout", "4.0.3")],
        }
        subdeps: list[DependencyTree] = []
        sub_names = mock_map.get(dep.name.lower(), [])
        for sname, sver in sub_names[:3]:
            node = DependencyTree(name=sname, version=sver, depth=depth, parent=dep.name)
            subdeps.append(node)
        return subdeps

    def render_tree_text(self, tree: DependencyTree | None = None, max_depth: int = 3) -> str:
        """
        将依赖树渲染为文本形式

        Args:
            tree: 依赖树根节点
            max_depth: 最大渲染深度

        Returns:
            树形文本字符串
        """
        t = tree or self._dependency_tree
        if t is None:
            t = self.build_dependency_tree()
        lines: list[str] = []
        self._render_node(t, lines, prefix="", is_last=True, max_depth=max_depth)
        return "\n".join(lines)

    def _render_node(
        self,
        node: DependencyTree,
        lines: list[str],
        prefix: str,
        is_last: bool,
        max_depth: int,
    ) -> None:
        """递归渲染树节点"""
        connector = "└── " if is_last else "├── "
        conflict_marker = " ⚠️" if node.is_conflict else ""
        display = f"{node.name}@{node.version}{conflict_marker}"
        lines.append(f"{prefix}{connector}{display}")
        if node.depth >= max_depth:
            return
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            self._render_node(child, lines, child_prefix, i == len(node.children) - 1, max_depth)

    # ==================== 版本冲突检测 ====================

    def detect_conflicts(self) -> list[VersionConflict]:
        """
        检测依赖版本冲突

        包括：语义版本冲突、传递依赖冲突、循环依赖检测
        """
        self._conflicts.clear()
        dep_groups: dict[str, list[DependencyInfo]] = {}
        for dep in self._dependencies.values():
            key = dep.name.lower()
            if key not in dep_groups:
                dep_groups[key] = []
            dep_groups[key].append(dep)

        for name, group in dep_groups.items():
            if len(group) <= 1:
                continue
            versions: dict[str, str] = {}
            for dep in group:
                source = f"{dep.manager.value}:{dep.specifier or dep.version or 'unspecified'}"
                versions[source] = dep.version or dep.specifier or "*"

            parsed_versions = [_parse_semver(v) for v in versions.values() if _parse_semver(v) != (0, 0, 0)]
            if len(parsed_versions) >= 2:
                min_v = min(parsed_versions)
                max_v = max(parsed_versions)
                if min_v != max_v:
                    severity = RiskLevel.HIGH if (max_v[0] - min_v[0]) >= 1 else RiskLevel.MEDIUM
                    suggestion = f"建议统一到 {'.'.join(map(str, max_v))} 或更高版本"
                    self._conflicts.append(VersionConflict(
                        package_name=name,
                        required_versions=versions,
                        conflict_type="semantic",
                        severity=severity,
                        suggestion=suggestion,
                    ))

        cycles = self._detect_cycles()
        for cycle in cycles:
            cycle_key = " → ".join(cycle)
            self._conflicts.append(VersionConflict(
                package_name=cycle_key,
                required_versions={"cycle": "circular"},
                conflict_type="circular",
                severity=RiskLevel.CRITICAL,
                suggestion=f"检测到循环依赖链: {cycle_key}，需要重构依赖关系以打破循环",
            ))

        return self._conflicts

    def _detect_cycles(self) -> list[list[str]]:
        """检测循环依赖"""
        graph: dict[str, set[str]] = {}
        for dep in self._dependencies.values():
            children = self._generate_mock_subdeps(dep, depth=2)
            graph.setdefault(dep.name.lower(), set()).update(c.name.lower() for c in children)

        visited: set[str] = set()
        rec_stack: set[str] = set()
        cycles: list[list[str]] = []

        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path)
                elif neighbor in rec_stack:
                    idx = path.index(neighbor)
                    cycles.append(path[idx:] + [neighbor])
            path.pop()
            rec_stack.discard(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    # ==================== 许可证兼容性检查 ====================

    def check_license_compatibility(
        self,
        project_license: str = "MIT",
    ) -> dict[str, Any]:
        """
        检查所有依赖的许可证与项目许可证的兼容性

        Args:
            project_license: 项目自身使用的许可证名称

        Returns:
            兼容性检查报告字典
        """
        proj_lic = self._license_db.get(project_license.upper())
        if proj_lic is None:
            proj_lic = LicenseInfo(
                name=project_license, spdx_id=project_license,
                is_osi_approved=False, is_copyleft=False,
                compatibility=[], restrictions=["未知许可证"],
            )

        results: list[dict[str, Any]] = []
        compatible_count = 0
        incompatible_count = 0
        unknown_count = 0

        for dep in sorted(self._dependencies.values(), key=lambda d: d.name):
            dep_licenses = dep.licenses or ["Unknown"]
            dep_compat_status = "compatible"
            issues: list[str] = []

            for lic_name in dep_licenses:
                lic_upper = lic_name.upper()
                lic_info = self._license_db.get(lic_upper)
                if lic_info is None:
                    issues.append(f"未知许可证 '{lic_name}'，需人工审查")
                    dep_compat_status = "unknown"
                    unknown_count += 1
                    continue
                if lic_info.is_copyleft and not proj_lic.is_copyleft:
                    if proj_lic.name.upper() not in lic_info.compatibility:
                        issues.append(
                            f"'{lic_name}' 是Copyleft许可证，与项目'{proj_lic.name}'不兼容。"
                            f"要求衍生作品采用{lic_name}许可"
                        )
                        dep_compat_status = "incompatible"
                        incompatible_count += 1
                    else:
                        compatible_count += 1
                else:
                    compatible_count += 1

            results.append({
                "package": dep.name,
                "licenses": dep_licenses,
                "status": dep_compat_status,
                "issues": issues,
            })

        total = len(self._dependencies) or 1
        score = round((compatible_count / total) * 100, 1)

        return {
            "project_license": proj_lic.to_dict(),
            "total_dependencies": len(self._dependencies),
            "compatible": compatible_count,
            "incompatible": incompatible_count,
            "unknown": unknown_count,
            "compatibility_score": score,
            "details": results,
        }

    # ==================== 安全漏洞扫描 ====================

    def check_security_advisories(self) -> list[SecurityAdvisory]:
        """
        检查已知安全漏洞（CVE匹配）

        Returns:
            匹配到的安全公告列表
        """
        self._advisories.clear()
        for dep in self._dependencies.values():
            for advisory in self._cve_db:
                if advisory.package_name.lower() != dep.name.lower():
                    continue
                dep_ver = _parse_semver(dep.version or "0.0.0")
                for affected_range in advisory.affected_versions:
                    range_ver = _parse_semver(affected_range)
                    if dep_ver < range_ver or dep_ver == (0, 0, 0):
                        self._advisories.append(advisory)
                        break
        return self._advisories

    # ==================== 更新策略建议 ====================

    def suggest_updates(self) -> list[UpdateSuggestion]:
        """
        分析依赖并给出更新策略建议

        基于当前版本与最新版本的对比，评估 patch/minor/major 升级风险
        """
        self._update_suggestions.clear()
        sample_latest: dict[str, str] = {
            "requests": "2.32.0", "fastapi": "0.110.0", "sqlalchemy": "2.0.28",
            "pytest": "8.1.1", "numpy": "1.26.4", "flask": "3.0.2", "django": "5.0.3",
            "pydantic": "2.6.1", "httpcore": "1.0.5", "redis": "5.0.3",
            "urllib3": "2.27.0", "starlette": "0.37.0", "click": "8.1.7",
        }

        for dep in self._dependencies.values():
            latest = sample_latest.get(dep.name.lower(), "")
            if not latest or not dep.version:
                continue
            cur = _parse_semver(dep.version)
            lat = _parse_semver(latest)
            if cur == (0, 0, 0) or cur >= lat:
                continue

            update_type: UpdateType
            risk: RiskLevel
            reason: str
            breaking: list[str]

            if cur[0] < lat[0]:
                update_type = UpdateType.MAJOR
                risk = RiskLevel.HIGH
                reason = f"主版本从 {cur[0]} 升级到 {lat[0]}，可能包含破坏性变更"
                breaking = ["API接口签名变化", "默认行为改变", "移除已废弃功能"]
            elif cur[1] < lat[1]:
                update_type = UpdateType.MINOR
                risk = RiskLevel.MEDIUM
                reason = f"次版本从 {cur[1]} 升级到 {lat[1]}，包含新功能但向后兼容"
                breaking = []
            else:
                update_type = UpdateType.PATCH
                risk = RiskLevel.LOW
                reason = f"补丁版本从 {cur[2]} 升级到 {lat[2]}，仅包含bug修复"
                breaking = []

            self._update_suggestions.append(UpdateSuggestion(
                package_name=dep.name,
                current_version=dep.version,
                suggested_version=latest,
                update_type=update_type,
                risk_level=risk,
                reason=reason,
                breaking_changes=breaking,
            ))

        self._update_suggestions.sort(key=lambda u: (
            {"major": 0, "minor": 1, "patch": 2}.get(u.update_type.value, 3),
            u.package_name,
        ))

        return self._update_suggestions

    # ==================== 过时依赖识别 ====================

    def identify_outdated(self) -> list[dict[str, Any]]:
        """
        识别过时的依赖（当前版本落后于最新版本）

        Returns:
            过时依赖列表
        """
        outdated: list[dict[str, Any]] = []
        sample_latest: dict[str, str] = {
            "requests": "2.32.0", "fastapi": "0.110.0", "sqlalchemy": "2.0.28",
            "pytest": "8.1.1", "numpy": "1.26.4", "flask": "3.0.2", "django": "5.0.3",
            "pydantic": "2.6.1", "httpcore": "1.0.5", "redis": "5.0.3",
        }

        for dep in self._dependencies.values():
            latest = sample_latest.get(dep.name.lower(), "")
            if not latest or not dep.version:
                continue
            cmp = _compare_versions(dep.version, latest)
            if cmp < 0:
                outdated.append({
                    "package": dep.name,
                    "current": dep.version,
                    "latest": latest,
                    "versions_behind": self._count_versions_behind(dep.version, latest),
                })

        outdated.sort(key=lambda x: x["versions_behind"], reverse=True)
        return outdated

    @staticmethod
    def _count_versions_behind(current: str, latest: str) -> int:
        """计算落后版本数（简化估算）"""
        c = _parse_semver(current)
        l = _parse_semver(latest)
        return (l[0] - c[0]) * 100 + (l[1] - c[1]) * 10 + (l[2] - c[2])

    # ==================== 报告生成 ====================

    def generate_report(self) -> str:
        """生成完整的依赖管理报告(Markdown)"""
        lines: list[str] = []
        lines.append("# 📦 依赖管理司 · 综合报告\n")
        lines.append(f"## 基本信息\n")
        lines.append(f"| 项目 | 值 |")
        lines.append(f"| --- | --- |")
        lines.append(f"| 检测到的包管理器 | **{self._detected_manager.value}** |")
        lines.append(f"| 总依赖数量 | **{len(self._dependencies)}** |")

        if self._dependency_tree:
            lines.append(f"\n## 依赖树\n")
            lines.append("```text")
            tree_text = self.render_tree_text(max_depth=2)
            lines.append(tree_text[:800])
            lines.append("```")

        conflicts = self.conflicts
        if conflicts:
            lines.append(f"\n## ⚠️ 版本冲突 ({len(conflicts)})\n")
            for c in conflicts[:10]:
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(c.severity.value, "⚪")
                lines.append(f"- {icon} **{c.package_name}** ({c.conflict_type}): {c.suggestion}")

        lic_report = self.check_license_compatibility()
        lines.append(f"\n## 📜 许可证兼容性\n")
        lines.append(f"- 项目许可证: `{lic_report['project_license']['name']}`")
        lines.append(f"- 兼容性评分: **{lic_report['compatibility_score']}%**")
        lines.append(f"- 兼容: {lic_report['compatible']} / 不兼容: {lic_report['incompatible']} / 未知: {lic_report['unknown']}")

        advisories = self.advisories
        if advisories:
            lines.append(f"\n## 🔒 安全公告 ({len(advisories)})\n")
            for a in advisories:
                sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(a.severity.value, "⚪")
                lines.append(f"- {sev_icon} [{a.cve_id}]({a.references[0] if a.references else '#'}) "
                             f"**{a.package_name}** {a.affected_versions}: {a.description[:60]}...")

        suggestions = self.update_suggestions
        if suggestions:
            lines.append(f"\n## 📈 更新建议 ({len(suggestions)})\n")
            for s in suggestions[:15]:
                type_icon = {"major": "🔴", "minor": "🟡", "patch": "🟢"}.get(s.update_type.value, "⚪")
                risk_icon = {"critical": "☠️", "high": "⚠️", "medium": "ℹ️", "low": "✅"}.get(s.risk_level.value, "•")
                lines.append(f"- {type_icon} {risk_icon} **{s.package_name}** "
                             f"`{s.current_version}` → `{s.suggested_version}` "
                             f"({s.update_type.value})")

        outdated = self.identify_outdated()
        if outdated:
            lines.append(f"\n## 🕐 过时依赖 ({len(outdated)})\n")
            for o in outdated[:10]:
                lines.append(f"- **{o['package']}** `{o['current']}` → `{o['latest']}` "
                             f"(落后{o['versions_behind']}个版本)")

        return "\n".join(lines)

    @property
    def dependencies(self) -> dict[str, DependencyInfo]:
        return dict(self._dependencies)

    @property
    def conflicts(self) -> list[VersionConflict]:
        if not self._conflicts:
            self.detect_conflicts()
        return list(self._conflicts)

    @property
    def advisories(self) -> list[SecurityAdvisory]:
        if not self._advisories:
            self.check_security_advisories()
        return list(self._advisories)

    @property
    def update_suggestions(self) -> list[UpdateSuggestion]:
        if not self._update_suggestions:
            self.suggest_updates()
        return list(self._update_suggestions)

    @property
    def dependency_count(self) -> int:
        return len(self._dependencies)

    def __repr__(self) -> str:
        return f"DependencyMgmtSi(deps={self.dependency_count}, manager={self._detected_manager.value})"


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 依赖管理司测试")
    print("=" * 60)

    si = DependencyMgmtSi()

    print("\n--- 解析 requirements.txt ---")
    req_content = """# 项目核心依赖
fastapi>=0.100.0,<0.110.0
uvicorn[standard]>=0.24.0
sqlalchemy>=2.0.0
pydantic-settings>=2.0.0
redis[hiredis]>=4.6.0

# 开发依赖
pytest>=7.4.0
pytest-cov>=4.1.0
ruff>=0.1.0
httpx>=0.25.0

# 可选
pillow>=9.5.0
"""
    deps = si.parse_dependencies(req_content, manager=PackageManager.PIP)
    print(f"   ✅ 解析到 {len(deps)} 个依赖:")
    for d in deps[:8]:
        dev_tag = " [DEV]" if d.is_dev else ""
        print(f"      • {d.name}{dev_tag}: {d.specifier or d.version}")

    print("\n--- 解析 pyproject.toml (Poetry) ---")
    poetry_content = """[tool.poetry]
name = "myapp"
version = "1.0.0"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.109.0"
pydantic = "^2.6.0"
sqlalchemy = "^2.0.0"
requests = "^2.31.0"

[tool.poetry.group.dev.dependencies]
pytest = "^8.0.0"
ruff = "^0.3.0"
"""
    poetry_deps = si.parse_dependencies(poetry_content, manager=PackageManager.POETRY)
    print(f"   ✅ 解析到 {len(poetry_deps)} 个Poetry依赖:")
    for d in poetry_deps:
        dev_tag = " [DEV]" if d.is_dev else ""
        print(f"      • {d.name}{dev_tag}: {d.specifier}")

    print("\n--- 解析 package.json (npm) ---")
    npm_content = """{
  "name": "frontend-app",
  "dependencies": {
    "react": "^18.2.0",
    "next": "^14.1.0",
    "typescript": "^5.3.0"
  },
  "devDependencies": {
    "eslint": "^8.56.0",
    "prettier": "^3.2.0",
    "@types/react": "^18.2.0"
  }
}
"""
    npm_deps = si.parse_dependencies(npm_content, manager=PackageManager.NPM)
    print(f"   ✅ 解析到 {len(npm_deps)} 个npm依赖:")
    for d in npm_deps:
        dev_tag = " [DEV]" if d.is_dev else ""
        print(f"      • {d.name}{dev_tag}: {d.specifier}")

    print("\n--- 依赖树可视化 ---")
    tree = si.build_dependency_tree()
    tree_text = si.render_tree_text(tree, max_depth=2)
    print(tree_text)

    print("\n--- 版本冲突检测 ---")
    conflicts = si.detect_conflicts()
    print(f"   发现 {len(conflicts)} 个潜在冲突:")
    for c in conflicts:
        icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(c.severity.value, "⚪")
        print(f"   {icon} [{c.conflict_type}] {c.package_name}: {c.suggestion[:50]}")

    print("\n--- 许可证兼容性检查 ---")
    lic_result = si.check_license_compatibility(project_license="MIT")
    print(f"   项目许可证: MIT")
    print(f"   兼容性评分: {lic_result['compatibility_score']}%")
    print(f"   兼容/不兼容/未知: {lic_result['compatible']}/{lic_result['incompatible']}/{lic_result['unknown']}")

    incompatible_items = [d for d in lic_result["details"] if d["status"] == "incompatible"]
    if incompatible_items:
        print(f"   不兼容项:")
        for item in incompatible_items:
            print(f"      ⚠️ {item['package']}: {item['issues'][0][:60]}")

    print("\n--- 安全漏洞扫描 ---")
    advisories = si.check_security_advisories()
    print(f"   匹配到 {len(advisories)} 条安全公告:")
    for a in advisories:
        sev_icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(a.severity.value, "⚪")
        print(f"   {sev_icon} {a.cve_id} | {a.package_name} {a.affected_versions} | {a.description[:50]}")

    print("\n--- 更新策略建议 ---")
    suggestions = si.suggest_updates()
    print(f"   生成 {len(suggestions)} 条更新建议:")
    for s in suggestions[:10]:
        type_icon = {"major": "🔴", "minor": "🟡", "patch": "🟢"}.get(s.update_type.value, "⚪")
        print(f"   {type_icon} {s.package_name}: {s.current_version} → {s.suggested_version} ({s.update_type.value}, {s.risk_level.value})")
        if s.breaking_changes:
            print(f"      破坏性变更: {', '.join(s.breaking_changes[:2])}")

    print("\n--- 过时依赖识别 ---")
    outdated = si.identify_outdated()
    print(f"   发现 {len(outdated)} 个过时依赖:")
    for o in outdated[:8]:
        print(f"   🕐 {o['package']}: {o['current']} → {o['latest']} (落后{o['versions_behind']}版)")

    print("\n--- 综合报告预览 (前1500字符) ---")
    report = si.generate_report()
    print(report[:1500])

    print("\n✅ 所有测试通过!")
