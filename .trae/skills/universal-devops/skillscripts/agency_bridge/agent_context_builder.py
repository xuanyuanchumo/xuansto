"""
上下文构建器

为 AI 智能体构建完整的执行上下文，包括项目信息、任务背景、
相关文件、代码片段、前置结果和约束条件等。
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class AgentContext:
    """Agent 执行上下文"""

    project_info: dict[str, str] = field(default_factory=dict)
    task_background: dict[str, str] = field(default_factory=dict)
    relevant_files: list[dict[str, str]] = field(default_factory=list)
    code_snippets: list[dict[str, str]] = field(default_factory=list)
    previous_results: list[dict[str, Any]] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)
    built_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_info": self.project_info,
            "task_background": self.task_background,
            "relevant_files_count": len(self.relevant_files),
            "code_snippets_count": len(self.code_snippets),
            "previous_results_count": len(self.previous_results),
            "constraints": self.constraints,
            "built_at": self.built_at,
        }


class AgentContextBuilder:
    """
    上下文构建器

    从项目环境和任务描述中提取并组装完整的 Agent 执行上下文。
    """

    PROJECT_FILES = {
        "package.json": ("node", "javascript"),
        "pyproject.toml": ("python", "python"),
        "setup.py": ("python", "python"),
        "Cargo.toml": ("rust", "rust"),
        "go.mod": ("go", "go"),
        "pom.xml": ("java", "java"),
        "Gemfile": ("ruby", "ruby"),
        "composer.json": ("php", "php"),
    }

    def __init__(self, project_root: Path | str | None = None) -> None:
        self._project_root = Path(project_root) if project_root else Path.cwd()
        self._context_cache: dict[int, AgentContext] = {}

    def build_base_context(self) -> dict[str, str]:
        """
        构建基础项目上下文（从项目根目录读取 package.json / pyproject.toml 等）

        Returns:
            项目基本信息字典
        """
        project_info: dict[str, str] = {
            "project_name": self._project_root.name,
            "root_path": str(self._project_root),
            "detected_at": datetime.now().isoformat(),
        }

        for filename, (lang_key, lang_val) in self.PROJECT_FILES.items():
            file_path = self._project_root / filename
            if file_path.exists():
                try:
                    content = file_path.read_text(encoding="utf-8")[:2000]
                    project_info[f"{lang_key}_file"] = filename
                    project_info["language"] = lang_val
                    project_info[f"{lang_key}_preview"] = content[:300]
                    name_match = re.search(r'"name"\s*:\s*"([^"]+)"', content)
                    if name_match:
                        project_info["package_name"] = name_match.group(1)
                    version_match = re.search(r'"version"\s*:\s*"([^"]+)"', content)
                    if version_match:
                        project_info["version"] = version_match.group(1)
                    break
                except OSError:
                    continue

        git_dir = self._project_root / ".git"
        if git_dir.is_dir():
            project_info["vcs"] = "git"

        readme_file = self._project_root / "README.md"
        if readme_file.exists():
            try:
                readme_content = readme_file.read_text(encoding="utf-8")[:500]
                project_info["readme_preview"] = readme_content
            except OSError:
                pass

        return project_info

    def extract_task_background(self, task_description: str) -> dict[str, str]:
        """
        提取任务背景（解析用户输入的任务描述）

        Args:
            task_description: 用户输入的任务描述文本

        Returns:
            结构化的任务背景信息
        """
        background: dict[str, str] = {
            "raw_task": task_description,
            "extracted_at": datetime.now().isoformat(),
        }

        intent_patterns = {
            "intent_development": [r"开发|实现|编写|新建|create|develop|implement|build"],
            "intent_fix": [r"修复|fix|bug|错误|问题|解决|debug"],
            "intent_refactor": [r"重构|优化|改善|refactor|optimize|improve"],
            "intent_review": [r"审查|review|检查|check|audit"],
            "intent_test": [r"测试|test|验证|validate|单元|集成"],
            "intent_design": [r"设计|design|UI|UX|界面|原型"],
        }

        detected_intents: list[str] = []
        for intent_key, patterns in intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, task_description, re.IGNORECASE):
                    detected_intents.append(intent_key.split("_")[1])
                    break

        background["intents"] = ", ".join(detected_intents) if detected_intents else "general"

        tech_patterns = {
            "language": [r"(Python|JavaScript|TypeScript|Java|Go|Rust|PHP|Ruby|C\+\+)"],
            "framework": [r"(React|Vue|Angular|FastAPI|Django|Flask|Spring|Express|Rails)"],
            "database": [r"(MySQL|PostgreSQL|MongoDB|Redis|SQLite|Oracle)"],
            "tool": [r"(Docker|Kubernetes|Git|CI/CD|Webpack|Vite)"],
        }
        extracted_tech: list[str] = []
        for tech_key, patterns in tech_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, task_description, re.IGNORECASE)
                if match:
                    extracted_tech.append(match.group(1))
                    background[tech_key] = match.group(1)

        background["tech_stack"] = ", ".join(extracted_tech) if extracted_tech else "unspecified"

        file_matches = re.findall(r'[\w\-./]+\.(py|js|ts|jsx|tsx|java|go|rs|md|json|yaml|yml)', task_description)
        if file_matches:
            background["mentioned_files"] = ", ".join(file_matches[:5])

        background["estimated_complexity"] = (
            "high" if len(task_description) > 200
            else "low" if len(task_description) < 50
            else "medium"
        )

        return background

    def gather_relevant_files(
        self,
        task_type: str = "",
        extensions: list[str] | None = None,
        max_files: int = 10,
    ) -> list[dict[str, str]]:
        """
        收集相关文件（基于任务类型确定文件范围）

        Args:
            task_type: 任务类型关键词
            extensions: 文件扩展名过滤列表
            max_files: 最大文件数量

        Returns:
            文件信息列表，每个元素包含 path, extension, size 等字段
        """
        files: list[dict[str, str]] = []

        ext_set = set(extensions) if extensions else {".py", ".js", ".ts", ".md", ".json"}

        exclude_dirs = {
            "__pycache__", ".git", "node_modules", ".venv", "venv",
            "dist", "build", ".tox", ".mypy_cache", ".cache",
        }

        try:
            for file_path in sorted(self._project_root.rglob("*")):
                if not file_path.is_file():
                    continue

                if any(part in exclude_dirs for part in file_path.parts):
                    continue

                if file_path.suffix.lower() not in ext_set:
                    continue

                relative = file_path.relative_to(self._project_root)
                files.append({
                    "path": str(relative),
                    "absolute_path": str(file_path),
                    "extension": file_path.suffix.lower(),
                    "size_bytes": str(file_path.stat().st_size),
                })

                if len(files) >= max_files:
                    break
        except OSError:
            pass

        if task_type:
            keyword_patterns = {
                "frontend": {".html", ".css", ".vue", ".jsx", ".tsx", ".scss"},
                "backend": {".py", ".js", ".ts", ".java", ".go", ".rs"},
                "test": {"_test.py", "_spec.py", ".test.js", ".spec.ts"},
                "config": {".yaml", ".yml", ".toml", ".ini", ".conf", ".json"},
                "doc": {".md", ".rst", ".txt", ".adoc"},
            }
            for type_key, type_exts in keyword_patterns.items():
                if type_key in task_type.lower():
                    ext_set.update(type_exts)

        return files

    def prepare_code_context(
        self,
        file_paths: list[str],
        max_lines_per_file: int = 50,
    ) -> list[dict[str, str]]:
        """
        准备代码上下文（读取关键代码片段）

        Args:
            file_paths: 文件路径列表（相对路径）
            max_lines_per_file: 每个文件最大读取行数

        Returns:
            代码片段列表，每个元素包含 path, content, language 等字段
        """
        snippets: list[dict[str, str]] = []

        ext_lang_map: dict[str, str] = {
            ".py": "python", ".js": "javascript", ".ts": "typescript",
            ".jsx": "jsx", ".tsx": "tsx", ".java": "java", ".go": "go",
            ".rs": "rust", ".html": "html", ".css": "css", ".md": "markdown",
            ".json": "json", ".yaml": "yaml", ".yml": "yaml",
        }

        for rel_path in file_paths[:5]:
            full_path = self._project_root / rel_path
            if not full_path.exists() or not full_path.is_file():
                continue

            try:
                content = full_path.read_text(encoding="utf-8")
                lines = content.split("\n")
                preview_lines = lines[:max_lines_per_file]
                preview = "\n".join(preview_lines)

                if len(lines) > max_lines_per_file:
                    preview += f"\n... (共 {len(lines)} 行)"

                snippets.append({
                    "path": rel_path,
                    "language": ext_lang_map.get(full_path.suffix.lower(), "text"),
                    "content": preview,
                    "total_lines": str(len(lines)),
                    "size_bytes": str(len(content.encode("utf-8"))),
                })
            except OSError:
                continue

        return snippets

    def include_previous_results(
        self,
        results: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        包含前置 agent 的结果（用于 agent 链式调用）

        Args:
            results: 前置 agent 的执行结果列表

        Returns:
            处理后的结果列表（截断过大的内容）
        """
        processed: list[dict[str, Any]] = []

        for result in results:
            processed_result: dict[str, Any] = {
                "agent_id": result.get("agent_id", "unknown"),
                "status": result.get("status", "unknown"),
                "timestamp": result.get("timestamp", datetime.now().isoformat()),
            }

            output = result.get("output", "")
            if isinstance(output, str) and len(output) > 2000:
                processed_result["output_summary"] = output[:2000] + f"... (截断, 共 {len(output)} 字符)"
                processed_result["output_truncated"] = True
            else:
                processed_result["output"] = output

            artifacts = result.get("artifacts", {})
            if isinstance(artifacts, dict):
                processed_result["artifact_types"] = list(artifacts.keys())[:10]

            metrics = result.get("metrics", {})
            if isinstance(metrics, dict):
                processed_result["metrics_summary"] = {k: v for k, v in list(metrics.items())[:5]}

            processed.append(processed_result)

        return processed

    def apply_constraints(
        self,
        constraints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        应用约束条件（安全限制、权限范围等）

        Args:
            constraints: 约束条件字典

        Returns:
            合并后的完整约束字典
        """
        base_constraints: dict[str, Any] = {
            "max_response_length": 8000,
            "allowed_operations": ["read", "analyze", "suggest"],
            "forbidden_operations": ["delete", "modify_system", "execute_arbitrary"],
            "timeout_seconds": 300,
            "safe_mode": True,
            "require_confirmation_for": ["file_write", "install_package", "run_command"],
        }

        if constraints:
            base_constraints.update(constraints)

        return base_constraints

    def build_full_context(
        self,
        task_description: str,
        previous_results: list[dict[str, Any]] | None = None,
        constraints: dict[str, Any] | None = None,
        file_extensions: list[str] | None = None,
    ) -> AgentContext:
        """
        构建完整上下文（组合以上所有部分）

        Args:
            task_description: 任务描述
            previous_results: 前置 agent 结果
            constraints: 自定义约束
            file_extensions: 要收集的文件扩展名

        Returns:
            完整的 AgentContext 对象
        """
        context = AgentContext()

        context.project_info = self.build_base_context()
        context.task_background = self.extract_task_background(task_description)

        task_type = context.task_background.get("intents", "")
        context.relevant_files = self.gather_relevant_files(
            task_type=task_type,
            extensions=file_extensions,
        )

        rel_paths = [f["path"] for f in context.relevant_files[:5]]
        context.code_snippets = self.prepare_code_context(rel_paths)

        if previous_results:
            context.previous_results = self.include_previous_results(previous_results)

        context.constraints = self.apply_constraints(constraints)

        cache_key = hash(task_description)
        self._context_cache[cache_key] = context

        return context

    def format_context_for_agent(
        self,
        context: AgentContext,
        format_type: str = "markdown",
    ) -> str:
        """
        格式化上下文为 agent 友好的格式

        Args:
            context: AgentContext 对象
            format_type: 输出格式 ('markdown', 'json', 'text')

        Returns:
            格式化后的上下文字符串
        """
        if format_type == "json":
            import json
            return json.dumps(context.to_dict(), ensure_ascii=False, indent=2)

        sections: list[str] = [
            "# 📋 Agent 执行上下文",
            f"\n> **构建时间**: {context.built_at}\n",
            "## 项目信息\n",
        ]

        for key, value in context.project_info.items():
            if key.endswith("_preview"):
                display_value = value[:150] + "..." if len(value) > 150 else value
                sections.append(f"- **{key}**: ```{display_value}```")
            else:
                sections.append(f"- **{key}**: {value}")

        sections.extend(["\n## 任务背景\n"])
        for key, value in context.task_background.items():
            if key == "raw_task":
                sections.append(f"- **{key}**: {value[:200]}...")
            else:
                sections.append(f"- **{key}**: {value}")

        if context.code_snippets:
            sections.append("\n## 代码上下文\n")
            for snippet in context.code_snippets[:3]:
                sections.append(f"### {snippet['path']} ({snippet['language']})")
                sections.append(f"```{snippet['language']}")
                sections.append(snippet["content"][:300])
                sections.append("```")

        if context.previous_results:
            sections.append("\n## 前置结果\n")
            for prev in context.previous_results[:3]:
                sections.append(f"- **{prev.get('agent_id')}**: {prev.get('status')}")

        if context.constraints:
            safe_ops = context.constraints.get("allowed_operations", [])
            sections.append(f"\n## 约束条件\n- 允许操作: {', '.join(safe_ops)}")

        return "\n".join(sections)

    def get_cached_context(self, cache_key: int) -> AgentContext | None:
        """获取缓存的上下文"""
        return self._context_cache.get(cache_key)

    def clear_cache(self) -> None:
        """清空上下文缓存"""
        self._context_cache.clear()


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 上下文构建器测试")
    print("=" * 60)

    builder = AgentContextBuilder()

    print("\n--- 基础项目上下文 ---")
    project_info = builder.build_base_context()
    print(f"✅ 项目名: {project_info.get('project_name')}")
    print(f"✅ 语言: {project_info.get('language', '未检测到')}")
    print(f"✅ VCS: {project_info.get('vcs', '无')}")
    print(f"✅ 信息项: {list(project_info.keys())}")

    print("\n--- 任务背景提取 ---")
    task_bg = builder.extract_task_background(
        "使用 Python FastAPI 开发一个用户认证 REST API，支持 JWT 和 OAuth2，需要连接 PostgreSQL 数据库"
    )
    print(f"✅ 意图: {task_bg.get('intents')}")
    print(f"✅ 技术栈: {task_bg.get('tech_stack')}")
    print(f"✅ 语言: {task_bg.get('language')}")
    print(f"✅ 框架: {task_bg.get('framework')}")
    print(f"✅ 数据库: {task_bg.get('database')}")
    print(f"✅ 复杂度: {task_bg.get('estimated_complexity')}")

    print("\n--- 相关文件收集 ---")
    files = builder.gather_relevant_files(extensions=[".py"], max_files=5)
    print(f"✅ 收集到 {len(files)} 个文件")
    for f in files[:3]:
        print(f"   {f['path']} ({f['extension']})")

    print("\n--- 完整上下文构建 ---")
    full_ctx = builder.build_full_context(
        task_description="重构用户认证模块，添加双因素认证支持",
        file_extensions=[".py", ".md"],
    )
    print(f"✅ 上下文构建完成")
    print(f"   项目信息项: {len(full_ctx.project_info)}")
    print(f"   相关文件: {len(full_ctx.relevant_files)}")
    print(f"   代码片段: {len(full_ctx.code_snippets)}")
    print(f"   约束条件: {list(full_ctx.constraints.keys())}")

    print("\n--- 格式化输出 (预览) ---")
    formatted = builder.format_context_for_agent(full_ctx, "markdown")
    print(formatted[:600])

    print("\n✅ 上下文构建器测试通过!")
