import json
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger("knowledge-server")

try:
    import httpx
    httpx_available = True
except ImportError:
    httpx_available = False

try:
    import requests
    requests_available = True
except ImportError:
    requests_available = False


class KnowledgeBaseClient:
    def __init__(self, project_path: str, api_base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.project_path = Path(project_path).resolve()
        self.api_base_url = api_base_url or "http://127.0.0.1:8765"
        self.api_key = api_key
        self.mode = "mcp"
        self._knowledge_dir = self.project_path / ".knowledge"

    def search(self, query: str, **kwargs) -> list:
        top_k = kwargs.get("top_k", 5)
        strategy = kwargs.get("strategy", "hybrid")
        scope = kwargs.get("scope")
        min_confidence = kwargs.get("min_confidence", 0.0)
        type_filters = kwargs.get("type_filters")
        category_filters = kwargs.get("category_filters")
        tag_filters = kwargs.get("tag_filters")

        for method in (self._search_via_mcp, self._search_via_rest, self._search_via_filesystem):
            try:
                result = method(
                    query=query,
                    top_k=top_k,
                    strategy=strategy,
                    scope=scope,
                    min_confidence=min_confidence,
                    type_filters=type_filters,
                    category_filters=category_filters,
                    tag_filters=tag_filters,
                )
                if result is not None:
                    return result
            except Exception as e:
                mode_name = method.__name__
                logger.warning("operation=kb_client_search, method=%s, error=%s, falling_back", mode_name, e)
                continue

        logger.warning("operation=kb_client_search, all_methods_failed, query=%s", query)
        return []

    def add(self, **kwargs) -> dict:
        for method in (self._add_via_mcp, self._add_via_rest, self._add_via_filesystem):
            try:
                result = method(**kwargs)
                if result is not None:
                    return result
            except Exception as e:
                mode_name = method.__name__
                logger.warning("operation=kb_client_add, method=%s, error=%s, falling_back", mode_name, e)
                continue

        return {"status": "error", "message": "所有添加方式均失败"}

    def update(self, entry_id: str, **kwargs) -> dict:
        for method in (self._update_via_mcp, self._update_via_rest):
            try:
                result = method(entry_id=entry_id, **kwargs)
                if result is not None:
                    return result
            except Exception as e:
                mode_name = method.__name__
                logger.warning("operation=kb_client_update, method=%s, error=%s, falling_back", mode_name, e)
                continue

        return {"status": "error", "message": "所有更新方式均失败"}

    def _search_via_mcp(self, query: str, **kwargs) -> Optional[list]:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            return None

        server_params = StdioServerParameters(
            command="python",
            args=["-m", "knowledge_server.main", "--transport", "mcp"],
            env=None,
        )

        try:
            import asyncio

            async def _do_search():
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(
                            "knowledge_search",
                            arguments={
                                "query": query,
                                "top_k": kwargs.get("top_k", 5),
                                "search_type": kwargs.get("strategy", "hybrid"),
                                "filters": {
                                    "min_confidence": kwargs.get("min_confidence", 0.0),
                                    "type": kwargs.get("type_filters"),
                                    "category": kwargs.get("category_filters"),
                                    "tags": kwargs.get("tag_filters"),
                                },
                            },
                        )
                        return result

            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, _do_search())
                    raw = future.result(timeout=30)
            else:
                raw = asyncio.run(_do_search())

            if raw and hasattr(raw, "content"):
                for item in raw.content:
                    if hasattr(item, "text"):
                        data = json.loads(item.text)
                        if data.get("status") == "ok" and data.get("data", {}).get("results"):
                            self.mode = "mcp"
                            return data["data"]["results"]
            return None
        except Exception as e:
            logger.debug("operation=mcp_search_failed, error=%s", e)
            return None

    def _search_via_rest(self, query: str, **kwargs) -> Optional[list]:
        url = f"{self.api_base_url}/v1/knowledge/search"
        payload = {
            "query": query,
            "top_k": kwargs.get("top_k", 5),
            "strategy": kwargs.get("strategy", "hybrid"),
        }
        if kwargs.get("scope"):
            payload["scope"] = kwargs["scope"]
        if kwargs.get("min_confidence", 0.0) > 0:
            payload["filters"] = {"min_confidence": kwargs["min_confidence"]}
            if kwargs.get("type_filters"):
                payload["filters"]["type"] = kwargs["type_filters"]
            if kwargs.get("category_filters"):
                payload["filters"]["category"] = kwargs["category_filters"]
            if kwargs.get("tag_filters"):
                payload["filters"]["tags"] = kwargs["tag_filters"]

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        try:
            if httpx_available:
                resp = httpx.post(url, json=payload, headers=headers, timeout=10.0)
            elif requests_available:
                resp = requests.post(url, json=payload, headers=headers, timeout=10.0)
            else:
                import urllib.request
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp_obj:
                    data = json.loads(resp_obj.read().decode("utf-8"))
                if data.get("status") == "ok" and data.get("data", {}).get("results"):
                    self.mode = "rest"
                    return data["data"]["results"]
                return None

            if resp.status_code == 200:
                data = resp.json() if hasattr(resp, "json") else json.loads(resp.text)
                if data.get("status") == "ok" and data.get("data", {}).get("results"):
                    self.mode = "rest"
                    return data["data"]["results"]
            return None
        except Exception as e:
            logger.debug("operation=rest_search_failed, error=%s", e)
            return None

    def _search_via_filesystem(self, query: str, **kwargs) -> Optional[list]:
        if not self._knowledge_dir.is_dir():
            return None

        query_lower = query.lower()
        query_terms = set(re.findall(r'\w+', query_lower))
        if not query_terms:
            return None

        results = []
        top_k = kwargs.get("top_k", 5)
        min_confidence = kwargs.get("min_confidence", 0.0)

        for scope in ("general", "workspace", "experience"):
            scope_dir = self._knowledge_dir / scope
            if not scope_dir.is_dir():
                continue
            for md_file in scope_dir.rglob("*.md"):
                try:
                    text = md_file.read_text(encoding="utf-8", errors="ignore")
                    text_lower = text.lower()
                    match_count = sum(1 for term in query_terms if term in text_lower)
                    if match_count == 0:
                        continue

                    score = match_count / len(query_terms) if query_terms else 0
                    if score < min_confidence:
                        continue

                    meta, body = self._parse_frontmatter(text)
                    title = meta.get("title", md_file.stem) if meta else md_file.stem
                    content = body.strip() if body else text.strip()

                    entry = {
                        "id": meta.get("id", f"file:{md_file.relative_to(self._knowledge_dir)}") if meta else f"file:{md_file.relative_to(self._knowledge_dir)}",
                        "title": title,
                        "content": content[:2000],
                        "scope": scope,
                        "source_path": str(md_file.relative_to(self._knowledge_dir)),
                        "confidence": round(score, 2),
                        "tags": meta.get("tags", []) if meta else [],
                        "type": meta.get("type", "unknown") if meta else "unknown",
                        "category": meta.get("category", "uncategorized") if meta else "uncategorized",
                        "status": "active",
                        "updated": meta.get("updated", "") if meta else "",
                        "summary": meta.get("summary", "") if meta else "",
                    }

                    type_filters = kwargs.get("type_filters")
                    if type_filters and entry["type"] not in type_filters:
                        continue
                    category_filters = kwargs.get("category_filters")
                    if category_filters and entry["category"] not in category_filters:
                        continue

                    results.append(entry)
                except Exception:
                    continue

        results.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        self.mode = "filesystem"
        return results[:top_k]

    def _add_via_mcp(self, **kwargs) -> Optional[dict]:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            return None

        content = kwargs.get("content", "")
        title = kwargs.get("title", "")
        tags = kwargs.get("tags", [])

        server_params = StdioServerParameters(
            command="python",
            args=["-m", "knowledge_server.main", "--transport", "mcp"],
        )

        try:
            import asyncio

            async def _do_add():
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(
                            "knowledge_add",
                            arguments={
                                "content": content,
                                "metadata": {
                                    "title": title,
                                    "tags": tags,
                                    "type": kwargs.get("type", "unknown"),
                                    "category": kwargs.get("category", "uncategorized"),
                                    "confidence": kwargs.get("confidence", 0.6),
                                },
                            },
                        )
                        return result

            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, _do_add())
                    raw = future.result(timeout=30)
            else:
                raw = asyncio.run(_do_add())

            if raw and hasattr(raw, "content"):
                for item in raw.content:
                    if hasattr(item, "text"):
                        data = json.loads(item.text)
                        if data.get("status") in ("ok", "conflict"):
                            self.mode = "mcp"
                            return data.get("data", data)
            return None
        except Exception as e:
            logger.debug("operation=mcp_add_failed, error=%s", e)
            return None

    def _add_via_rest(self, **kwargs) -> Optional[dict]:
        url = f"{self.api_base_url}/v1/knowledge/add"
        payload = {
            "title": kwargs.get("title", ""),
            "content": kwargs.get("content", ""),
            "scope": kwargs.get("scope", "workspace"),
            "tags": kwargs.get("tags", []),
            "type": kwargs.get("type", "unknown"),
            "category": kwargs.get("category", "uncategorized"),
        }
        if kwargs.get("source_path"):
            payload["source_path"] = kwargs["source_path"]
        if kwargs.get("summary"):
            payload["summary"] = kwargs["summary"]

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        try:
            if httpx_available:
                resp = httpx.post(url, json=payload, headers=headers, timeout=10.0)
            elif requests_available:
                resp = requests.post(url, json=payload, headers=headers, timeout=10.0)
            else:
                import urllib.request
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=10) as resp_obj:
                    data = json.loads(resp_obj.read().decode("utf-8"))
                if data.get("status") == "ok":
                    self.mode = "rest"
                    return data.get("data", {})
                return None

            if resp.status_code in (200, 201):
                data = resp.json() if hasattr(resp, "json") else json.loads(resp.text)
                if data.get("status") == "ok":
                    self.mode = "rest"
                    return data.get("data", {})
            return None
        except Exception as e:
            logger.debug("operation=rest_add_failed, error=%s", e)
            return None

    def _add_via_filesystem(self, **kwargs) -> Optional[dict]:
        content = kwargs.get("content", "")
        title = kwargs.get("title", "untitled")
        scope = kwargs.get("scope", "workspace")
        category = kwargs.get("category", "uncategorized")
        tags = kwargs.get("tags", [])

        scope_dir = self._knowledge_dir / scope / category
        scope_dir.mkdir(parents=True, exist_ok=True)

        safe_title = "".join(c if c.isalnum() or c in ("-", "_", " ") else "_" for c in title).strip()
        if not safe_title:
            safe_title = "untitled"
        filepath = scope_dir / f"{safe_title}.md"

        import hashlib
        entry_id = hashlib.sha256(f"{scope}:{category}:{title}".encode()).hexdigest()[:16]

        meta = {
            "id": entry_id,
            "type": kwargs.get("type", "unknown"),
            "category": category,
            "tags": tags,
            "scope": scope,
            "confidence": kwargs.get("confidence", 0.6),
        }
        if title:
            meta["title"] = title

        try:
            from .config import yaml_available
            if yaml_available:
                import yaml
                rendered = yaml.dump(meta, default_flow_style=False, allow_unicode=True, sort_keys=False)
            else:
                rendered = json.dumps(meta, ensure_ascii=False, indent=2)
        except ImportError:
            rendered = json.dumps(meta, ensure_ascii=False, indent=2)

        frontmatter = f"---\n{rendered}---\n"
        try:
            filepath.write_text(frontmatter + content, encoding="utf-8")
            self.mode = "filesystem"
            return {"id": entry_id, "status": "created", "dedup_status": "new"}
        except OSError as e:
            logger.warning("operation=filesystem_add_failed, error=%s", e)
            return None

    def _update_via_mcp(self, entry_id: str, **kwargs) -> Optional[dict]:
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError:
            return None

        server_params = StdioServerParameters(
            command="python",
            args=["-m", "knowledge_server.main", "--transport", "mcp"],
        )

        metadata = {}
        if kwargs.get("tags"):
            metadata["tags"] = kwargs["tags"]
        if kwargs.get("confidence") is not None:
            metadata["confidence"] = kwargs["confidence"]
        if kwargs.get("type"):
            metadata["type"] = kwargs["type"]
        if kwargs.get("category"):
            metadata["category"] = kwargs["category"]

        try:
            import asyncio

            async def _do_update():
                async with stdio_client(server_params) as (read, write):
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        result = await session.call_tool(
                            "knowledge_update",
                            arguments={
                                "id": entry_id,
                                "content": kwargs.get("content"),
                                "metadata": metadata,
                            },
                        )
                        return result

            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    future = pool.submit(asyncio.run, _do_update())
                    raw = future.result(timeout=30)
            else:
                raw = asyncio.run(_do_update())

            if raw and hasattr(raw, "content"):
                for item in raw.content:
                    if hasattr(item, "text"):
                        data = json.loads(item.text)
                        if data.get("status") == "ok":
                            self.mode = "mcp"
                            return data.get("data", {})
            return None
        except Exception as e:
            logger.debug("operation=mcp_update_failed, error=%s", e)
            return None

    def _update_via_rest(self, entry_id: str, **kwargs) -> Optional[dict]:
        url = f"{self.api_base_url}/v1/knowledge/update/{entry_id}"
        updates = {}
        if kwargs.get("content"):
            updates["content"] = kwargs["content"]
        if kwargs.get("tags") is not None:
            updates["tags"] = kwargs["tags"]
        if kwargs.get("confidence") is not None:
            updates["confidence"] = kwargs["confidence"]
        if kwargs.get("type"):
            updates["type"] = kwargs["type"]
        if kwargs.get("category"):
            updates["category"] = kwargs["category"]

        if not updates:
            return None

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-API-Key"] = self.api_key

        try:
            if httpx_available:
                resp = httpx.put(url, json=updates, headers=headers, timeout=10.0)
            elif requests_available:
                resp = requests.put(url, json=updates, headers=headers, timeout=10.0)
            else:
                import urllib.request
                req = urllib.request.Request(
                    url,
                    data=json.dumps(updates).encode("utf-8"),
                    headers=headers,
                    method="PUT",
                )
                with urllib.request.urlopen(req, timeout=10) as resp_obj:
                    data = json.loads(resp_obj.read().decode("utf-8"))
                if data.get("status") == "ok":
                    self.mode = "rest"
                    return data.get("data", {})
                return None

            if resp.status_code == 200:
                data = resp.json() if hasattr(resp, "json") else json.loads(resp.text)
                if data.get("status") == "ok":
                    self.mode = "rest"
                    return data.get("data", {})
            return None
        except Exception as e:
            logger.debug("operation=rest_update_failed, error=%s", e)
            return None

    @staticmethod
    def _parse_frontmatter(text: str):
        match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.DOTALL)
        if not match:
            return None, text
        raw, body = match.group(1), match.group(2)
        try:
            from .config import yaml_available
            if yaml_available:
                import yaml
                meta = yaml.safe_load(raw)
            else:
                meta = json.loads(raw)
            if not isinstance(meta, dict):
                return None, text
            return meta, body
        except Exception:
            return None, text
