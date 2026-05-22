import json
import logging
import re
import sqlite3
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

logger = logging.getLogger("knowledge-server")

OFFICIAL_SOURCES = {
    "javascript": {"base_url": "https://developer.mozilla.org", "name": "MDN"},
    "typescript": {"base_url": "https://www.typescriptlang.org/docs", "name": "TypeScript Official"},
    "python": {"base_url": "https://docs.python.org", "name": "Python Official"},
    "rust": {"base_url": "https://doc.rust-lang.org", "name": "Rust Docs"},
    "go": {"base_url": "https://go.dev/doc", "name": "Go Official"},
    "react": {"base_url": "https://react.dev", "name": "React Official"},
    "vue": {"base_url": "https://vuejs.org/guide", "name": "Vue Official"},
    "nextjs": {"base_url": "https://nextjs.org/docs", "name": "Next.js Official"},
}

_OFFICIAL_DOMAINS = set()
for _src in OFFICIAL_SOURCES.values():
    parsed = urllib.parse.urlparse(_src["base_url"])
    _OFFICIAL_DOMAINS.add(parsed.netloc)

_OFFICIAL_ORG_GITHUB = {
    "facebook", "reactjs", "vuejs", "vitejs", "microsoft", "typescript-eslint",
    "python", "rust-lang", "golang", "nextjs", "vercel", "nodejs",
}

_AUTHORITY_COMMUNITY_DOMAINS = {
    "stackoverflow.com", "stackexchange.com", "rfc-editor.org", "w3.org",
    "ietf.org", "ecma-international.org",
}

_GENERAL_COMMUNITY_DOMAINS = {
    "medium.com", "dev.to", "hashnode.com", "freecodecamp.org",
    "css-tricks.com", "smashingmagazine.com", "sitepoint.com",
}

_SEARCH_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; KnowledgeBot/1.0; +https://github.com/xuansto)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

_REQUEST_TIMEOUT = 15


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._pieces = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "nav", "footer", "header"):
            self._skip = True

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "header"):
            self._skip = False

    def handle_data(self, data):
        if not self._skip:
            self._pieces.append(data)

    def get_text(self):
        return " ".join(self._pieces)


def classify_source_rating(url: str) -> int:
    try:
        parsed = urllib.parse.urlparse(url)
        domain = parsed.netloc.lower()
    except Exception:
        return 1

    for official_domain in _OFFICIAL_DOMAINS:
        if domain == official_domain or domain.endswith("." + official_domain):
            return 5

    if domain == "github.com":
        parts = parsed.path.strip("/").split("/")
        if len(parts) >= 1:
            org = parts[0].lower()
            if org in _OFFICIAL_ORG_GITHUB:
                return 4
        return 2

    for auth_domain in _AUTHORITY_COMMUNITY_DOMAINS:
        if domain == auth_domain or domain.endswith("." + auth_domain):
            return 3

    for gen_domain in _GENERAL_COMMUNITY_DOMAINS:
        if domain == gen_domain or domain.endswith("." + gen_domain):
            return 2

    if domain.endswith(".org") or domain.endswith(".dev"):
        return 3

    return 1


def _fetch_url(url: str, timeout: int = _REQUEST_TIMEOUT) -> Optional[str]:
    try:
        req = urllib.request.Request(url, headers=_SEARCH_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status >= 400:
                return None
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type and "text/plain" not in content_type:
                return None
            raw = resp.read(_REQUEST_TIMEOUT * 1024)
            charset = "utf-8"
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip()
            try:
                return raw.decode(charset)
            except (UnicodeDecodeError, LookupError):
                return raw.decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, TimeoutError) as e:
        logger.debug("operation=fetch_url, url=%s, error=%s", url, e)
        return None


def _extract_text_from_html(html: str) -> str:
    try:
        extractor = _HTMLTextExtractor()
        extractor.feed(html)
        text = extractor.get_text()
        text = re.sub(r"\s+", " ", text).strip()
        return text
    except Exception:
        return re.sub(r"<[^>]+>", " ", html)


def _build_search_url(query: str, site: Optional[str] = None) -> str:
    q = query
    if site:
        q = f"site:{site} {query}"
    params = urllib.parse.urlencode({"q": q})
    return f"https://html.duckduckgo.com/html/?{params}"


def _parse_ddg_results(html: str, max_results: int = 5) -> list:
    results = []
    pattern = re.compile(
        r'<a[^>]+class="result__a"[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>[^<]+)</a>'
        r'.*?<a[^>]+class="result__snippet"[^>]*>(?P<snippet>[^<]*)</a>',
        re.DOTALL,
    )
    for match in pattern.finditer(html):
        url = urllib.parse.unquote(match.group("url").strip())
        title = re.sub(r"<[^>]+>", "", match.group("title")).strip()
        snippet = re.sub(r"<[^>]+>", "", match.group("snippet")).strip()
        if url and title:
            results.append({
                "title": title,
                "url": url,
                "snippet": snippet,
            })
        if len(results) >= max_results:
            break
    return results


def search_official_docs(query: str, tech_stack: Optional[list] = None) -> list:
    results = []
    sources_to_search = {}

    if tech_stack:
        for tech in tech_stack:
            tech_lower = tech.lower().strip()
            if tech_lower in OFFICIAL_SOURCES:
                sources_to_search[tech_lower] = OFFICIAL_SOURCES[tech_lower]
    else:
        sources_to_search = OFFICIAL_SOURCES

    for tech_key, source_info in sources_to_search.items():
        parsed = urllib.parse.urlparse(source_info["base_url"])
        site = parsed.netloc

        search_url = _build_search_url(query, site=site)
        html = _fetch_url(search_url)
        if html is None:
            logger.debug("operation=search_official_docs, tech=%s, status=fetch_failed", tech_key)
            continue

        ddg_results = _parse_ddg_results(html, max_results=3)
        for r in ddg_results:
            source_rating = classify_source_rating(r["url"])
            results.append({
                "title": r["title"],
                "url": r["url"],
                "content": r["snippet"],
                "source_name": source_info["name"],
                "source_rating": source_rating,
                "tech": tech_key,
            })

    results.sort(key=lambda x: x["source_rating"], reverse=True)
    return results


def _fetch_and_extract_content(url: str) -> Optional[str]:
    html = _fetch_url(url)
    if html is None:
        return None
    text = _extract_text_from_html(html)
    if len(text) > 4000:
        text = text[:4000]
    return text


def extract_and_structure(web_results: list, existing_entry: Optional[dict] = None) -> dict:
    if not web_results:
        return {}

    best = web_results[0]
    for r in web_results:
        if r.get("source_rating", 0) >= 4:
            best = r
            break

    content = best.get("content", "")
    if not content or len(content) < 50:
        fetched = _fetch_and_extract_content(best.get("url", ""))
        if fetched:
            content = fetched

    title = best.get("title", "")
    url = best.get("url", "")
    source_name = best.get("source_name", "")
    source_rating = best.get("source_rating", 3)
    tech = best.get("tech", "")

    tags = []
    if tech:
        tags.append(tech)
    for r in web_results:
        for t in r.get("tech", "").split(","):
            t = t.strip()
            if t and t not in tags:
                tags.append(t)

    changes = []
    additions = []
    if existing_entry:
        existing_content = existing_entry.get("content", "")
        existing_tags = existing_entry.get("tags", [])
        if content and existing_content:
            content_words = set(content.lower().split())
            existing_words = set(existing_content.lower().split())
            new_words = content_words - existing_words
            if new_words:
                additions.append(f"新增关键词: {', '.join(list(new_words)[:10])}")
            removed_words = existing_words - content_words
            if removed_words:
                changes.append(f"移除关键词: {', '.join(list(removed_words)[:10])}")
        new_tags = [t for t in tags if t not in existing_tags]
        if new_tags:
            additions.append(f"新增标签: {', '.join(new_tags)}")

    summary_parts = []
    if source_name:
        summary_parts.append(f"来源: {source_name}")
    if url:
        summary_parts.append(f"URL: {url}")
    if changes:
        summary_parts.append(f"变更: {'; '.join(changes)}")
    if additions:
        summary_parts.append(f"新增: {'; '.join(additions)}")
    summary = " | ".join(summary_parts) if summary_parts else None

    entry_data = {
        "title": title,
        "content": content,
        "scope": "general",
        "tags": tags,
        "source_path": url,
        "source_rating": source_rating,
        "type": "standard",
        "category": tech if tech else "uncategorized",
        "summary": summary,
        "confidence": 0.6,
    }

    if existing_entry:
        entry_data["id"] = existing_entry.get("id")
        if existing_entry.get("confidence", 0) > 0.6:
            entry_data["confidence"] = existing_entry["confidence"]

    return entry_data


def detect_stale_entries(db_path: str, days: int = 90) -> list:
    db_file = Path(db_path)
    if not db_file.exists():
        logger.warning("operation=detect_stale_entries, db_path=%s, status=not_found", db_path)
        return []

    threshold_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = sqlite3.connect(str(db_file))
        conn.row_factory = sqlite3.Row
        cur = conn.execute(
            "SELECT * FROM knowledge_entries "
            "WHERE status != 'archived' AND status != 'deleted' "
            "AND (last_validated IS NULL OR last_validated < ?) "
            "ORDER BY updated ASC",
            (threshold_date,),
        )
        rows = cur.fetchall()
        results = []
        for row in rows:
            d = dict(row)
            if "tags" in d and isinstance(d["tags"], str):
                try:
                    d["tags"] = json.loads(d["tags"])
                except json.JSONDecodeError:
                    d["tags"] = []
            results.append(d)
        conn.close()
        logger.info("operation=detect_stale_entries, found=%d, days=%d", len(results), days)
        return results
    except Exception as e:
        logger.warning("operation=detect_stale_entries, error=%s", e)
        return []


def _detect_package_managers(project_path: str) -> list:
    project = Path(project_path)
    managers = []
    if (project / "package.json").exists():
        managers.append("npm")
    if (project / "pyproject.toml").exists() or (project / "requirements.txt").exists() or (project / "Pipfile").exists():
        managers.append("pip")
    if (project / "Cargo.toml").exists():
        managers.append("cargo")
    if (project / "go.mod").exists():
        managers.append("go")
    return managers


def _read_npm_deps(project_path: str) -> dict:
    pkg_path = Path(project_path) / "package.json"
    if not pkg_path.exists():
        return {}
    try:
        with open(pkg_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        deps = {}
        for section in ("dependencies", "devDependencies"):
            for name, version in data.get(section, {}).items():
                deps[name] = version.lstrip("^~>=<")
        return deps
    except Exception as e:
        logger.debug("operation=read_npm_deps, error=%s", e)
        return {}


def _read_python_deps(project_path: str) -> dict:
    project = Path(project_path)
    deps = {}

    req_path = project / "requirements.txt"
    if req_path.exists():
        try:
            with open(req_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or line.startswith("-"):
                        continue
                    match = re.match(r"^([a-zA-Z0-9_.-]+)\s*([>=<~!]+.*)?$", line)
                    if match:
                        name = match.group(1).lower()
                        version = (match.group(2) or "").lstrip(">=<~!")
                        deps[name] = version
        except Exception:
            pass

    pyproject_path = project / "pyproject.toml"
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()
            in_deps = False
            for line in content.splitlines():
                stripped = line.strip()
                if stripped.startswith("[project.dependencies]") or stripped.startswith("[tool.poetry.dependencies]"):
                    in_deps = True
                    continue
                if stripped.startswith("[") and in_deps:
                    in_deps = False
                    continue
                if in_deps and "=" in stripped:
                    name = stripped.split("=")[0].strip().lower()
                    version_match = re.search(r'["\']?(\d+[^"\'\)]*)', stripped)
                    version = version_match.group(1) if version_match else ""
                    deps[name] = version
        except Exception:
            pass

    return deps


def _read_cargo_deps(project_path: str) -> dict:
    cargo_path = Path(project_path) / "Cargo.toml"
    if not cargo_path.exists():
        return {}
    deps = {}
    try:
        with open(cargo_path, "r", encoding="utf-8") as f:
            content = f.read()
        in_deps = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped == "[dependencies]":
                in_deps = True
                continue
            if stripped.startswith("[") and in_deps:
                in_deps = False
                continue
            if in_deps and "=" in stripped:
                name = stripped.split("=")[0].strip()
                version_match = re.search(r'"(\d+[^"]*)"', stripped)
                version = version_match.group(1) if version_match else ""
                deps[name] = version
    except Exception:
        pass
    return deps


def _read_go_deps(project_path: str) -> dict:
    go_mod_path = Path(project_path) / "go.mod"
    if not go_mod_path.exists():
        return {}
    deps = {}
    try:
        with open(go_mod_path, "r", encoding="utf-8") as f:
            in_require = False
            for line in f:
                stripped = line.strip()
                if stripped.startswith("require ("):
                    in_require = True
                    continue
                if stripped == ")" and in_require:
                    in_require = False
                    continue
                if in_require or stripped.startswith("require "):
                    match = re.match(r"^\s*(\S+)\s+(v[\d.]+)", stripped)
                    if match:
                        pkg = match.group(1)
                        version = match.group(2)
                        short_name = pkg.split("/")[-1]
                        deps[short_name] = version
    except Exception:
        pass
    return deps


_NPM_TECH_MAP = {
    "react": "react", "react-dom": "react", "next": "nextjs",
    "vue": "vue", "@vue/compiler-sfc": "vue", "typescript": "typescript", "ts-node": "typescript",
    "svelte": "svelte", "angular": "angular", "@angular/core": "angular",
    "express": "express", "fastify": "fastify", "koa": "koa",
    "tailwindcss": "tailwindcss", "eslint": "eslint",
}

_PYTHON_TECH_MAP = {
    "django": "django", "flask": "flask", "fastapi": "fastapi",
    "pydantic": "pydantic", "sqlalchemy": "sqlalchemy", "numpy": "numpy",
    "pandas": "pandas", "scikit-learn": "scikit-learn", "pytest": "pytest",
    "celery": "celery", "redis": "redis",
}

_CARGO_TECH_MAP = {
    "tokio": "tokio", "serde": "serde", "actix-web": "actix",
    "warp": "warp", "reqwest": "reqwest", "clap": "clap",
}

_GO_TECH_MAP = {
    "gin": "gin", "echo": "echo", "fiber": "fiber",
}


def _map_deps_to_tech(all_deps: dict) -> list:
    tech_list = []
    seen = set()

    for dep_name in all_deps:
        mapped = _NPM_TECH_MAP.get(dep_name) or _PYTHON_TECH_MAP.get(dep_name) or _CARGO_TECH_MAP.get(dep_name) or _GO_TECH_MAP.get(dep_name)
        if mapped and mapped not in seen:
            tech_list.append({"name": mapped, "dep_name": dep_name, "version": all_deps[dep_name]})
            seen.add(mapped)

    for dep_name in all_deps:
        dep_lower = dep_name.lower()
        for tech_key in OFFICIAL_SOURCES:
            if tech_key in dep_lower and tech_key not in seen:
                tech_list.append({"name": tech_key, "dep_name": dep_name, "version": all_deps[dep_name]})
                seen.add(tech_key)

    return tech_list


def detect_new_tech_dependencies(project_path: str, db_path: str) -> list:
    managers = _detect_package_managers(project_path)
    if not managers:
        return []

    all_deps = {}
    for mgr in managers:
        if mgr == "npm":
            all_deps.update(_read_npm_deps(project_path))
        elif mgr == "pip":
            all_deps.update(_read_python_deps(project_path))
        elif mgr == "cargo":
            all_deps.update(_read_cargo_deps(project_path))
        elif mgr == "go":
            all_deps.update(_read_go_deps(project_path))

    if not all_deps:
        return []

    tech_list = _map_deps_to_tech(all_deps)
    if not tech_list:
        return []

    db_file = Path(db_path)
    known_techs = set()
    if db_file.exists():
        try:
            conn = sqlite3.connect(str(db_file))
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT DISTINCT category FROM knowledge_entries WHERE category IS NOT NULL AND category != 'uncategorized'"
            )
            for row in cur.fetchall():
                known_techs.add(row["category"].lower())
            cur2 = conn.execute(
                "SELECT tags FROM knowledge_entries WHERE tags IS NOT NULL AND tags != '[]'"
            )
            for row in cur2.fetchall():
                try:
                    tags = json.loads(row["tags"]) if isinstance(row["tags"], str) else row["tags"]
                    for t in tags:
                        known_techs.add(t.lower())
                except json.JSONDecodeError:
                    pass
            conn.close()
        except Exception as e:
            logger.warning("operation=detect_new_tech_deps, db_error=%s", e)

    missing = []
    for tech in tech_list:
        tech_name_lower = tech["name"].lower()
        if tech_name_lower not in known_techs:
            missing.append(tech)

    logger.info("operation=detect_new_tech_deps, total_deps=%d, tech_mapped=%d, known=%d, missing=%d",
                len(all_deps), len(tech_list), len(known_techs), len(missing))
    return missing


def auto_ingest_tech_knowledge(tech_name: str, tech_version: Optional[str] = None) -> dict:
    tech_lower = tech_name.lower().strip()
    query = tech_name
    if tech_version:
        query = f"{tech_name} {tech_version}"

    source_info = OFFICIAL_SOURCES.get(tech_lower)
    search_results = []

    try:
        search_results = search_official_docs(query, tech_stack=[tech_lower] if tech_lower in OFFICIAL_SOURCES else None)
    except Exception as e:
        logger.warning("operation=auto_ingest, tech=%s, search_error=%s", tech_name, e)

    if not search_results:
        try:
            search_url = _build_search_url(f"{tech_name} official documentation best practices")
            html = _fetch_url(search_url)
            if html:
                ddg_results = _parse_ddg_results(html, max_results=5)
                for r in ddg_results:
                    search_results.append({
                        "title": r["title"],
                        "url": r["url"],
                        "content": r["snippet"],
                        "source_name": "Web Search",
                        "source_rating": classify_source_rating(r["url"]),
                        "tech": tech_lower,
                    })
        except Exception as e:
            logger.warning("operation=auto_ingest, tech=%s, fallback_search_error=%s", tech_name, e)

    if not search_results:
        logger.info("operation=auto_ingest, tech=%s, status=no_results", tech_name)
        return {
            "status": "no_results",
            "tech_name": tech_name,
            "tech_version": tech_version,
            "message": f"未找到 {tech_name} 的相关文档",
        }

    structured = extract_and_structure(search_results)
    if not structured:
        return {
            "status": "no_results",
            "tech_name": tech_name,
            "tech_version": tech_version,
            "message": f"无法从搜索结果中提取 {tech_name} 的有效内容",
        }

    structured["scope"] = "general"
    structured["type"] = "standard"
    structured["category"] = tech_lower if tech_lower in OFFICIAL_SOURCES else tech_name.lower()
    structured["confidence"] = 0.6

    if tech_lower not in (t.lower() for t in structured.get("tags", [])):
        structured.setdefault("tags", []).append(tech_lower)

    source_rating = structured.get("source_rating", 3)
    if source_rating >= 4:
        structured["confidence"] = min(structured.get("confidence", 0.6) + 0.1, 0.8)

    logger.info("operation=auto_ingest, tech=%s, version=%s, sources=%d, source_rating=%d",
                tech_name, tech_version, len(search_results), source_rating)

    return {
        "status": "ready_for_review",
        "tech_name": tech_name,
        "tech_version": tech_version,
        "entry_data": structured,
        "sources_found": len(search_results),
        "best_source_rating": source_rating,
    }
