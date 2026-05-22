import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger("knowledge-server")

_FRAMEWORK_MAP = {
    "react": "React",
    "react-dom": "React",
    "vue": "Vue",
    "@vue/cli": "Vue",
    "nuxt": "Nuxt",
    "@angular/core": "Angular",
    "@angular/cli": "Angular",
    "svelte": "Svelte",
    "next": "Next.js",
    "nestjs": "NestJS",
    "express": "Express",
    "fastapi": "FastAPI",
    "flask": "Flask",
    "django": "Django",
    "pydantic": "Pydantic",
    "starlette": "Starlette",
    "actix-web": "Actix Web",
    "rocket": "Rocket",
    "axum": "Axum",
    "gin": "Gin",
    "echo": "Echo",
    "fiber": "Fiber",
    "flutter": "Flutter",
    "cupertino_icons": "Flutter",
}

_RUNTIME_MAP = {
    "react": "Node.js",
    "react-dom": "Node.js",
    "vue": "Node.js",
    "@vue/cli": "Node.js",
    "nuxt": "Node.js",
    "@angular/core": "Node.js",
    "svelte": "Node.js",
    "next": "Node.js",
    "express": "Node.js",
    "nestjs": "Node.js",
    "fastapi": "Python",
    "flask": "Python",
    "django": "Python",
    "pydantic": "Python",
    "actix-web": "Rust",
    "rocket": "Rust",
    "axum": "Rust",
    "gin": "Go",
    "echo": "Go",
    "fiber": "Go",
    "flutter": "Dart",
    "cupertino_icons": "Dart",
}

_PLATFORM_INDICATORS = {
    "desktop": ["electron", "tauri", "@electron/", "electron-builder", "pyqt", "pyside", "tkinter"],
    "mobile": ["react-native", "expo", "flutter", "capacitor", "@capacitor/", "ionic", "swiftui", "kotlinx"],
    "web": ["react", "react-dom", "vue", "@angular/core", "svelte", "next", "nuxt", "vite", "webpack"],
}


def detect_tech_stack(project_path: str) -> dict:
    root = Path(project_path).resolve()
    result = {
        "languages": [],
        "frameworks": [],
        "runtimes": [],
        "platform": "web",
    }

    if not root.is_dir():
        logger.warning("operation=detect_tech_stack, path=%s, status=not_a_directory", project_path)
        return result

    _detect_package_json(root, result)
    _detect_cargo_toml(root, result)
    _detect_go_mod(root, result)
    _detect_python(root, result)
    _detect_pubspec_yaml(root, result)

    result["languages"] = list(dict.fromkeys(result["languages"]))
    result["frameworks"] = _deduplicate_frameworks(result["frameworks"])
    result["runtimes"] = _deduplicate_runtimes(result["runtimes"])
    result["platform"] = _infer_platform(result)

    return result


def _detect_package_json(root: Path, result: dict):
    pkg_path = root / "package.json"
    if not pkg_path.is_file():
        return

    try:
        data = json.loads(pkg_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("operation=detect_package_json, path=%s, error=%s", pkg_path, e)
        return

    if "TypeScript" not in result["languages"]:
        tsconfig = root / "tsconfig.json"
        ts_files = list(root.glob("*.ts")) + list(root.glob("src/**/*.ts"))
        if tsconfig.is_file() or ts_files:
            result["languages"].append("TypeScript")

    if "JavaScript" not in result["languages"] and "TypeScript" not in result["languages"]:
        result["languages"].append("JavaScript")

    all_deps = {}
    for dep_key in ("dependencies", "devDependencies", "peerDependencies"):
        all_deps.update(data.get(dep_key, {}))

    node_version = _extract_node_version(root)
    for dep_name, dep_version in all_deps.items():
        framework_name = _FRAMEWORK_MAP.get(dep_name)
        if framework_name:
            _add_framework(result, framework_name, dep_version)

        runtime = _RUNTIME_MAP.get(dep_name)
        if runtime and runtime == "Node.js":
            _add_runtime(result, "Node.js", node_version or _strip_version(dep_version))

    if "Node.js" not in [r["name"] for r in result["runtimes"]]:
        _add_runtime(result, "Node.js", node_version or "unknown")


def _extract_node_version(root: Path) -> Optional[str]:
    nvmrc = root / ".nvmrc"
    if nvmrc.is_file():
        try:
            v = nvmrc.read_text(encoding="utf-8").strip()
            if v:
                return v
        except OSError:
            pass

    node_version_file = root / ".node-version"
    if node_version_file.is_file():
        try:
            v = node_version_file.read_text(encoding="utf-8").strip()
            if v:
                return v
        except OSError:
            pass

    pkg_path = root / "package.json"
    if pkg_path.is_file():
        try:
            data = json.loads(pkg_path.read_text(encoding="utf-8"))
            engines = data.get("engines", {})
            node_spec = engines.get("node", "")
            if node_spec:
                match = re.search(r'(\d+)', node_spec)
                if match:
                    return f"{match.group(1)}.x"
        except (json.JSONDecodeError, OSError):
            pass

    return None


def _detect_cargo_toml(root: Path, result: dict):
    cargo_path = root / "Cargo.toml"
    if not cargo_path.is_file():
        return

    if "Rust" not in result["languages"]:
        result["languages"].append("Rust")

    try:
        content = cargo_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("operation=detect_cargo_toml, path=%s, error=%s", cargo_path, e)
        return

    rust_version = None
    version_match = re.search(r'rust-version\s*=\s*"([^"]+)"', content)
    if version_match:
        rust_version = version_match.group(1)

    _add_runtime(result, "Rust", rust_version or "stable")

    for dep_match in re.finditer(r'^(\w[\w-]*)\s*=\s*"?([^"\s,\]}]+)', content, re.MULTILINE):
        dep_name = dep_match.group(1)
        dep_version = dep_match.group(2)
        framework_name = _FRAMEWORK_MAP.get(dep_name)
        if framework_name:
            _add_framework(result, framework_name, dep_version)


def _detect_go_mod(root: Path, result: dict):
    go_mod_path = root / "go.mod"
    if not go_mod_path.is_file():
        return

    if "Go" not in result["languages"]:
        result["languages"].append("Go")

    try:
        content = go_mod_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("operation=detect_go_mod, path=%s, error=%s", go_mod_path, e)
        return

    go_version = None
    version_match = re.search(r'^go\s+(\S+)', content, re.MULTILINE)
    if version_match:
        go_version = version_match.group(1)

    _add_runtime(result, "Go", go_version or "unknown")

    for dep_match in re.finditer(r'^\s+(\S+)\s+(v[\d.]+)', content, re.MULTILINE):
        dep_name = dep_match.group(1)
        dep_version = dep_match.group(2)
        short_name = dep_name.split("/")[-1]
        framework_name = _FRAMEWORK_MAP.get(short_name) or _FRAMEWORK_MAP.get(dep_name)
        if framework_name:
            _add_framework(result, framework_name, dep_version)


def _detect_python(root: Path, result: dict):
    pyproject_path = root / "pyproject.toml"
    requirements_path = root / "requirements.txt"
    setup_cfg_path = root / "setup.cfg"  # legacy
    setup_py_path = root / "setup.py"  # legacy

    python_version = None
    found = False

    if pyproject_path.is_file():
        found = True
        try:
            content = pyproject_path.read_text(encoding="utf-8")
            py_ver_match = re.search(r'python_requires\s*=\s*["\']?([^"\']+)', content)
            if py_ver_match:
                match = re.search(r'(\d+\.\d+)', py_ver_match.group(1))
                if match:
                    python_version = match.group(1)

            for dep_match in re.finditer(r'^(\w[\w.-]*)\s*([><=!~]+\s*[\d.]+)?', content, re.MULTILINE):
                dep_name = dep_match.group(1).lower()
                dep_version = dep_match.group(2).strip() if dep_match.group(2) else None
                framework_name = _FRAMEWORK_MAP.get(dep_name)
                if framework_name:
                    ver = re.search(r'(\d+\.\d+[\d.]*)', dep_version) if dep_version else None
                    _add_framework(result, framework_name, ver.group(1) if ver else None)
        except OSError as e:
            logger.warning("operation=detect_pyproject, path=%s, error=%s", pyproject_path, e)

    if requirements_path.is_file():
        found = True
        try:
            content = requirements_path.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                match = re.match(r'^([A-Za-z][\w.-]*)\s*([><=!~]+\s*[\d.]+)?', line)
                if match:
                    dep_name = match.group(1).lower()
                    dep_version = match.group(2).strip() if match.group(2) else None
                    framework_name = _FRAMEWORK_MAP.get(dep_name)
                    if framework_name:
                        ver = re.search(r'(\d+\.\d+[\d.]*)', dep_version) if dep_version else None
                        _add_framework(result, framework_name, ver.group(1) if ver else None)
        except OSError as e:
            logger.warning("operation=detect_requirements, path=%s, error=%s", requirements_path, e)

    if setup_cfg_path.is_file():
        found = True
        try:
            content = setup_cfg_path.read_text(encoding="utf-8")
            py_ver_match = re.search(r'python_requires\s*=\s*([^\n]+)', content)
            if py_ver_match and not python_version:
                match = re.search(r'(\d+\.\d+)', py_ver_match.group(1))
                if match:
                    python_version = match.group(1)
        except OSError:
            pass

    if setup_py_path.is_file():
        found = True

    py_files = list(root.glob("*.py")) + list(root.glob("src/**/*.py"))
    if py_files:
        found = True

    if found and "Python" not in result["languages"]:
        result["languages"].append("Python")
        _add_runtime(result, "Python", python_version or "3.x")


def _detect_pubspec_yaml(root: Path, result: dict):
    pubspec_path = root / "pubspec.yaml"
    if not pubspec_path.is_file():
        return

    if "Dart" not in result["languages"]:
        result["languages"].append("Dart")

    try:
        content = pubspec_path.read_text(encoding="utf-8")
    except OSError as e:
        logger.warning("operation=detect_pubspec, path=%s, error=%s", pubspec_path, e)
        return

    sdk_match = re.search(r'sdk:\s*["\']?flutter', content)
    if sdk_match:
        _add_framework(result, "Flutter", None)
        _add_runtime(result, "Dart", "stable")

    for dep_match in re.finditer(r'^\s+(\w[\w_-]*):\s*\^?([\d.]+)', content, re.MULTILINE):
        dep_name = dep_match.group(1)
        dep_version = dep_match.group(2)
        framework_name = _FRAMEWORK_MAP.get(dep_name)
        if framework_name:
            _add_framework(result, framework_name, dep_version)


def _add_framework(result: dict, name: str, version: Optional[str]):
    for fw in result["frameworks"]:
        if fw["name"] == name:
            if version and (not fw["version"] or version != "unknown"):
                fw["version"] = version
            return
    result["frameworks"].append({"name": name, "version": version or "unknown"})


def _add_runtime(result: dict, name: str, version: Optional[str]):
    for rt in result["runtimes"]:
        if rt["name"] == name:
            if version and (not rt["version"] or rt["version"] == "unknown"):
                rt["version"] = version
            return
    result["runtimes"].append({"name": name, "version": version or "unknown"})


def _strip_version(version_str: str) -> Optional[str]:
    match = re.search(r'(\d+\.\d+[\d.]*)', version_str)
    return match.group(1) if match else None


def _deduplicate_frameworks(frameworks: list) -> list:
    seen = {}
    for fw in frameworks:
        if fw["name"] not in seen:
            seen[fw["name"]] = fw
        else:
            existing = seen[fw["name"]]
            if fw["version"] and fw["version"] != "unknown":
                if not existing["version"] or existing["version"] == "unknown":
                    seen[fw["name"]] = fw
    return list(seen.values())


def _deduplicate_runtimes(runtimes: list) -> list:
    seen = {}
    for rt in runtimes:
        if rt["name"] not in seen:
            seen[rt["name"]] = rt
        else:
            existing = seen[rt["name"]]
            if rt["version"] and rt["version"] != "unknown":
                if not existing["version"] or existing["version"] == "unknown":
                    seen[rt["name"]] = rt
    return list(seen.values())


def _infer_platform(result: dict) -> str:
    all_names = [fw["name"].lower() for fw in result["frameworks"]]
    all_names += [rt["name"].lower() for rt in result["runtimes"]]

    scores = {"desktop": 0, "mobile": 0, "web": 0}
    for platform, indicators in _PLATFORM_INDICATORS.items():
        for indicator in indicators:
            if indicator.lower() in all_names:
                scores[platform] += 1

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "web"
    return best
