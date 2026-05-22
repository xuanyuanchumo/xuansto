"""
脚本依赖管理模块
提供依赖声明、检查、安装和版本管理功能
"""

import importlib
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class DependencyType(Enum):
    PYTHON_PACKAGE = "python_package"
    SYSTEM_PACKAGE = "system_package"
    NODE_PACKAGE = "node_package"
    CUSTOM = "custom"


class DependencyStatus(Enum):
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    VERSION_MISMATCH = "version_mismatch"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class DependencyVersion:
    major: int
    minor: int
    patch: int
    prerelease: Optional[str] = None
    
    def __str__(self) -> str:
        version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            version += f"-{self.prerelease}"
        return version
    
    def __lt__(self, other: 'DependencyVersion') -> bool:
        if (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch):
            return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)
        if self.prerelease and not other.prerelease:
            return True
        if not self.prerelease and other.prerelease:
            return False
        return (self.prerelease or "") < (other.prerelease or "")
    
    def __le__(self, other: 'DependencyVersion') -> bool:
        return self == other or self < other
    
    def __gt__(self, other: 'DependencyVersion') -> bool:
        return not self <= other
    
    def __ge__(self, other: 'DependencyVersion') -> bool:
        return not self < other
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, DependencyVersion):
            return False
        return (
            self.major == other.major and
            self.minor == other.minor and
            self.patch == other.patch and
            self.prerelease == other.prerelease
        )
    
    @classmethod
    def parse(cls, version_str: str) -> 'DependencyVersion':
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-(.+))?$'
        match = re.match(pattern, version_str.strip())
        if not match:
            raise ValueError(f"无效的版本格式: {version_str}")
        
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            prerelease=match.group(4)
        )


@dataclass
class VersionConstraint:
    operator: str
    version: DependencyVersion
    
    def check(self, actual_version: DependencyVersion) -> bool:
        ops = {
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
            '<': lambda a, b: a < b,
            '<=': lambda a, b: a <= b,
            '>': lambda a, b: a > b,
            '>=': lambda a, b: a >= b,
            '~=': lambda a, b: a.major == b.major and a >= b,
            '^': lambda a, b: a.major == b.major and a >= b
        }
        
        op_func = ops.get(self.operator)
        if not op_func:
            raise ValueError(f"不支持的操作符: {self.operator}")
        
        return op_func(actual_version, self.version)
    
    @classmethod
    def parse(cls, constraint_str: str) -> 'VersionConstraint':
        pattern = r'^(~=|==|!=|<=|>=|<|>|\^)(.+)$'
        match = re.match(pattern, constraint_str.strip())
        if not match:
            raise ValueError(f"无效的版本约束格式: {constraint_str}")
        
        return cls(
            operator=match.group(1),
            version=DependencyVersion.parse(match.group(2))
        )


@dataclass
class Dependency:
    name: str
    type: DependencyType
    version_constraints: List[VersionConstraint] = field(default_factory=list)
    optional: bool = False
    description: str = ""
    install_command: Optional[str] = None
    check_command: Optional[str] = None
    import_name: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.import_name:
            self.import_name = self.name
    
    def check_version_satisfied(self, version: DependencyVersion) -> bool:
        if not self.version_constraints:
            return True
        return all(constraint.check(version) for constraint in self.version_constraints)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.type.value,
            "version_constraints": [f"{c.operator}{c.version}" for c in self.version_constraints],
            "optional": self.optional,
            "description": self.description,
            "install_command": self.install_command,
            "check_command": self.check_command,
            "import_name": self.import_name,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Dependency':
        return cls(
            name=data['name'],
            type=DependencyType(data['type']),
            version_constraints=[
                VersionConstraint.parse(vc) for vc in data.get('version_constraints', [])
            ],
            optional=data.get('optional', False),
            description=data.get('description', ''),
            install_command=data.get('install_command'),
            check_command=data.get('check_command'),
            import_name=data.get('import_name'),
            metadata=data.get('metadata', {})
        )


@dataclass
class DependencyCheckResult:
    dependency: Dependency
    status: DependencyStatus
    installed_version: Optional[DependencyVersion] = None
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "dependency": self.dependency.to_dict(),
            "status": self.status.value,
            "installed_version": str(self.installed_version) if self.installed_version else None,
            "message": self.message,
            "details": self.details
        }


class DependencyChecker:
    def __init__(self):
        self._checkers: Dict[DependencyType, Callable] = {
            DependencyType.PYTHON_PACKAGE: self._check_python_package,
            DependencyType.SYSTEM_PACKAGE: self._check_system_package,
            DependencyType.NODE_PACKAGE: self._check_node_package,
            DependencyType.CUSTOM: self._check_custom
        }
    
    def check(self, dependency: Dependency) -> DependencyCheckResult:
        checker = self._checkers.get(dependency.type)
        if not checker:
            return DependencyCheckResult(
                dependency=dependency,
                status=DependencyStatus.UNKNOWN,
                message=f"不支持的依赖类型: {dependency.type}"
            )
        
        try:
            return checker(dependency)
        except Exception as e:
            return DependencyCheckResult(
                dependency=dependency,
                status=DependencyStatus.ERROR,
                message=f"检查依赖时发生错误: {str(e)}"
            )
    
    def check_all(self, dependencies: List[Dependency]) -> List[DependencyCheckResult]:
        return [self.check(dep) for dep in dependencies]
    
    def _check_python_package(self, dependency: Dependency) -> DependencyCheckResult:
        try:
            module = importlib.import_module(dependency.import_name)
            version_str = getattr(module, '__version__', None)
            
            if version_str:
                installed_version = DependencyVersion.parse(version_str)
                
                if dependency.check_version_satisfied(installed_version):
                    return DependencyCheckResult(
                        dependency=dependency,
                        status=DependencyStatus.INSTALLED,
                        installed_version=installed_version,
                        message=f"已安装版本 {installed_version}"
                    )
                else:
                    return DependencyCheckResult(
                        dependency=dependency,
                        status=DependencyStatus.VERSION_MISMATCH,
                        installed_version=installed_version,
                        message=f"版本不匹配: 已安装 {installed_version}"
                    )
            else:
                return DependencyCheckResult(
                    dependency=dependency,
                    status=DependencyStatus.INSTALLED,
                    message="已安装 (版本未知)"
                )
                
        except ImportError:
            return DependencyCheckResult(
                dependency=dependency,
                status=DependencyStatus.NOT_INSTALLED,
                message="未安装"
            )
    
    def _check_system_package(self, dependency: Dependency) -> DependencyCheckResult:
        check_cmd = dependency.check_command or f"which {dependency.name}"
        
        try:
            result = subprocess.run(
                check_cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return DependencyCheckResult(
                    dependency=dependency,
                    status=DependencyStatus.INSTALLED,
                    message=f"已安装: {result.stdout.strip()}"
                )
            else:
                return DependencyCheckResult(
                    dependency=dependency,
                    status=DependencyStatus.NOT_INSTALLED,
                    message="未安装"
                )
        except subprocess.TimeoutExpired:
            return DependencyCheckResult(
                dependency=dependency,
                status=DependencyStatus.ERROR,
                message="检查超时"
            )
    
    def _check_node_package(self, dependency: Dependency) -> DependencyCheckResult:
        try:
            result = subprocess.run(
                ["npm", "list", dependency.name, "--json"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if dependency.name in data.get('dependencies', {}):
                    version_str = data['dependencies'][dependency.name].get('version', '')
                    if version_str:
                        installed_version = DependencyVersion.parse(version_str.lstrip('^~'))
                        return DependencyCheckResult(
                            dependency=dependency,
                            status=DependencyStatus.INSTALLED,
                            installed_version=installed_version,
                            message=f"已安装版本 {installed_version}"
                        )
            
            return DependencyCheckResult(
                dependency=dependency,
                status=DependencyStatus.NOT_INSTALLED,
                message="未安装"
            )
        except Exception as e:
            return DependencyCheckResult(
                dependency=dependency,
                status=DependencyStatus.ERROR,
                message=f"检查失败: {str(e)}"
            )
    
    def _check_custom(self, dependency: Dependency) -> DependencyCheckResult:
        if not dependency.check_command:
            return DependencyCheckResult(
                dependency=dependency,
                status=DependencyStatus.UNKNOWN,
                message="未定义检查命令"
            )
        
        try:
            result = subprocess.run(
                dependency.check_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return DependencyCheckResult(
                    dependency=dependency,
                    status=DependencyStatus.INSTALLED,
                    message=f"检查通过: {result.stdout.strip()}"
                )
            else:
                return DependencyCheckResult(
                    dependency=dependency,
                    status=DependencyStatus.NOT_INSTALLED,
                    message="检查未通过"
                )
        except Exception as e:
            return DependencyCheckResult(
                dependency=dependency,
                status=DependencyStatus.ERROR,
                message=f"检查失败: {str(e)}"
            )


class DependencyInstaller:
    def __init__(self):
        self._installers: Dict[DependencyType, Callable] = {
            DependencyType.PYTHON_PACKAGE: self._install_python_package,
            DependencyType.SYSTEM_PACKAGE: self._install_system_package,
            DependencyType.NODE_PACKAGE: self._install_node_package,
            DependencyType.CUSTOM: self._install_custom
        }
    
    def install(
        self,
        dependency: Dependency,
        upgrade: bool = False,
        quiet: bool = False
    ) -> Tuple[bool, str]:
        installer = self._installers.get(dependency.type)
        if not installer:
            return False, f"不支持的依赖类型: {dependency.type}"
        
        try:
            return installer(dependency, upgrade=upgrade, quiet=quiet)
        except Exception as e:
            return False, f"安装失败: {str(e)}"
    
    def install_all(
        self,
        dependencies: List[Dependency],
        upgrade: bool = False,
        quiet: bool = False,
        skip_optional: bool = False
    ) -> Dict[str, Tuple[bool, str]]:
        results = {}
        
        for dep in dependencies:
            if skip_optional and dep.optional:
                results[dep.name] = (True, "跳过可选依赖")
                continue
            
            success, message = self.install(dep, upgrade=upgrade, quiet=quiet)
            results[dep.name] = (success, message)
        
        return results
    
    def _install_python_package(
        self,
        dependency: Dependency,
        upgrade: bool = False,
        quiet: bool = False
    ) -> Tuple[bool, str]:
        cmd = [sys.executable, "-m", "pip", "install"]
        
        if upgrade:
            cmd.append("--upgrade")
        if quiet:
            cmd.append("--quiet")
        
        if dependency.version_constraints:
            version_spec = ",".join(
                f"{c.operator}{c.version}" for c in dependency.version_constraints
            )
            cmd.append(f"{dependency.name}{version_spec}")
        else:
            cmd.append(dependency.name)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return True, "安装成功"
        else:
            return False, f"安装失败: {result.stderr}"
    
    def _install_system_package(
        self,
        dependency: Dependency,
        upgrade: bool = False,
        quiet: bool = False
    ) -> Tuple[bool, str]:
        if dependency.install_command:
            cmd = dependency.install_command
        else:
            return False, "未定义安装命令"
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return True, "安装成功"
        else:
            return False, f"安装失败: {result.stderr}"
    
    def _install_node_package(
        self,
        dependency: Dependency,
        upgrade: bool = False,
        quiet: bool = False
    ) -> Tuple[bool, str]:
        cmd = ["npm", "install"]
        
        if upgrade:
            cmd.append("--upgrade")
        
        if dependency.version_constraints:
            version_spec = dependency.version_constraints[0].operator + str(dependency.version_constraints[0].version)
            cmd.append(f"{dependency.name}@{version_spec}")
        else:
            cmd.append(dependency.name)
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            return True, "安装成功"
        else:
            return False, f"安装失败: {result.stderr}"
    
    def _install_custom(
        self,
        dependency: Dependency,
        upgrade: bool = False,
        quiet: bool = False
    ) -> Tuple[bool, str]:
        if not dependency.install_command:
            return False, "未定义安装命令"
        
        result = subprocess.run(
            dependency.install_command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            return True, "安装成功"
        else:
            return False, f"安装失败: {result.stderr}"


class DependencyManager:
    def __init__(self):
        self._dependencies: Dict[str, Dependency] = {}
        self._checker = DependencyChecker()
        self._installer = DependencyInstaller()
        self._check_cache: Dict[str, DependencyCheckResult] = {}
    
    def declare(self, dependency: Dependency) -> None:
        self._dependencies[dependency.name] = dependency
        if dependency.name in self._check_cache:
            del self._check_cache[dependency.name]
    
    def declare_many(self, dependencies: List[Dependency]) -> None:
        for dep in dependencies:
            self.declare(dep)
    
    def remove(self, name: str) -> bool:
        if name in self._dependencies:
            del self._dependencies[name]
            if name in self._check_cache:
                del self._check_cache[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[Dependency]:
        return self._dependencies.get(name)
    
    def list_all(self) -> List[Dependency]:
        return list(self._dependencies.values())
    
    def check(self, name: str, use_cache: bool = True) -> DependencyCheckResult:
        dependency = self._dependencies.get(name)
        if not dependency:
            raise KeyError(f"未声明的依赖: {name}")
        
        if use_cache and name in self._check_cache:
            return self._check_cache[name]
        
        result = self._checker.check(dependency)
        self._check_cache[name] = result
        return result
    
    def check_all(self, use_cache: bool = True) -> Dict[str, DependencyCheckResult]:
        results = {}
        for name in self._dependencies:
            results[name] = self.check(name, use_cache=use_cache)
        return results
    
    def install(
        self,
        name: str,
        upgrade: bool = False,
        quiet: bool = False
    ) -> Tuple[bool, str]:
        dependency = self._dependencies.get(name)
        if not dependency:
            raise KeyError(f"未声明的依赖: {name}")
        
        success, message = self._installer.install(dependency, upgrade=upgrade, quiet=quiet)
        
        if success and name in self._check_cache:
            del self._check_cache[name]
        
        return success, message
    
    def install_missing(
        self,
        upgrade: bool = False,
        quiet: bool = False,
        skip_optional: bool = False
    ) -> Dict[str, Tuple[bool, str]]:
        check_results = self.check_all()
        missing = []
        
        for name, result in check_results.items():
            if result.status in [DependencyStatus.NOT_INSTALLED, DependencyStatus.VERSION_MISMATCH]:
                if skip_optional and self._dependencies[name].optional:
                    continue
                missing.append(self._dependencies[name])
        
        return self._installer.install_all(
            missing,
            upgrade=upgrade,
            quiet=quiet,
            skip_optional=skip_optional
        )
    
    def ensure(
        self,
        name: str,
        auto_install: bool = True,
        upgrade: bool = False
    ) -> bool:
        result = self.check(name)
        
        if result.status == DependencyStatus.INSTALLED:
            return True
        
        if auto_install:
            success, _ = self.install(name, upgrade=upgrade)
            return success
        
        return False
    
    def ensure_all(
        self,
        auto_install: bool = True,
        upgrade: bool = False,
        skip_optional: bool = False
    ) -> Tuple[bool, Dict[str, bool]]:
        check_results = self.check_all()
        results = {}
        all_satisfied = True
        
        for name, result in check_results.items():
            if result.status == DependencyStatus.INSTALLED:
                results[name] = True
            elif auto_install:
                if skip_optional and self._dependencies[name].optional:
                    results[name] = True
                else:
                    success, _ = self.install(name, upgrade=upgrade)
                    results[name] = success
                    if not success:
                        all_satisfied = False
            else:
                results[name] = False
                all_satisfied = False
        
        return all_satisfied, results
    
    def export_requirements(self, output_path: str, format: str = "txt") -> bool:
        try:
            path = Path(output_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "txt":
                lines = []
                for dep in self._dependencies.values():
                    if dep.type == DependencyType.PYTHON_PACKAGE:
                        if dep.version_constraints:
                            version_spec = ",".join(
                                f"{c.operator}{c.version}" for c in dep.version_constraints
                            )
                            lines.append(f"{dep.name}{version_spec}")
                        else:
                            lines.append(dep.name)
                
                with open(path, 'w', encoding='utf-8') as f:
                    f.write("\n".join(lines))
            
            elif format == "json":
                data = {
                    "generated_at": datetime.now().isoformat(),
                    "dependencies": [dep.to_dict() for dep in self._dependencies.values()]
                }
                with open(path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            else:
                raise ValueError(f"不支持的导出格式: {format}")
            
            return True
        except Exception as e:
            print(f"导出依赖失败: {e}")
            return False
    
    def import_requirements(self, input_path: str) -> int:
        try:
            path = Path(input_path)
            
            if path.suffix == '.txt':
                with open(path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                count = 0
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        match = re.match(r'^([a-zA-Z0-9_-]+)(.*)$', line)
                        if match:
                            name = match.group(1)
                            version_spec = match.group(2)
                            
                            constraints = []
                            if version_spec:
                                for spec in version_spec.split(','):
                                    spec = spec.strip()
                                    if spec:
                                        constraints.append(VersionConstraint.parse(spec))
                            
                            self.declare(Dependency(
                                name=name,
                                type=DependencyType.PYTHON_PACKAGE,
                                version_constraints=constraints
                            ))
                            count += 1
                
                return count
            
            elif path.suffix == '.json':
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                deps_data = data.get('dependencies', [])
                for dep_data in deps_data:
                    self.declare(Dependency.from_dict(dep_data))
                
                return len(deps_data)
            
            else:
                raise ValueError(f"不支持的导入格式: {path.suffix}")
                
        except Exception as e:
            print(f"导入依赖失败: {e}")
            return 0
    
    def get_status_report(self) -> Dict[str, Any]:
        check_results = self.check_all()
        
        status_counts = {}
        for status in DependencyStatus:
            status_counts[status.value] = 0
        
        for result in check_results.values():
            status_counts[result.status.value] += 1
        
        return {
            "generated_at": datetime.now().isoformat(),
            "total_dependencies": len(self._dependencies),
            "status_summary": status_counts,
            "details": {
                name: result.to_dict()
                for name, result in check_results.items()
            }
        }


def create_python_dependency(
    name: str,
    version: Optional[str] = None,
    optional: bool = False,
    description: str = ""
) -> Dependency:
    constraints = []
    if version:
        constraints.append(VersionConstraint.parse(version))
    
    return Dependency(
        name=name,
        type=DependencyType.PYTHON_PACKAGE,
        version_constraints=constraints,
        optional=optional,
        description=description
    )


def create_system_dependency(
    name: str,
    install_command: str,
    check_command: Optional[str] = None,
    optional: bool = False,
    description: str = ""
) -> Dependency:
    return Dependency(
        name=name,
        type=DependencyType.SYSTEM_PACKAGE,
        install_command=install_command,
        check_command=check_command or f"which {name}",
        optional=optional,
        description=description
    )
