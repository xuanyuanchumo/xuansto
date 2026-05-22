#!/usr/bin/env python3
from __future__ import annotations
"""
OWASP Agentic AI Top 10 (2026) 安全合规扫描器
扫描目标目录中的代码文件，检测 Agentic AI 常见安全风险
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}

SCAN_EXTENSIONS = {".py", ".js", ".ts", ".yaml", ".yml", ".json", ".md"}


def severity_gte(actual: str, threshold: str) -> bool:
    """判断实际严重级别是否达到或超过阈值"""
    return SEVERITY_ORDER.get(actual, 0) >= SEVERITY_ORDER.get(threshold, 0)


def collect_files(target: str) -> list[str]:
    """递归收集目标目录下所有可扫描文件"""
    result = []
    for root, _dirs, files in os.walk(target):
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext in SCAN_EXTENSIONS:
                result.append(os.path.join(root, fname))
    return result


def read_lines(filepath: str) -> list[str]:
    """安全读取文件行，忽略二进制文件和不可读文件"""
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.readlines()
    except OSError:
        return []


def _match_patterns(lines: list[str], patterns: list[re.Pattern]) -> list[str]:
    hits: list[str] = []
    for idx, line in enumerate(lines, start=1):
        for pat in patterns:
            if pat.search(line):
                hits.append(f"{idx}")
                break
    return hits


# ---------------------------------------------------------------------------
# 以下为 OWASP Agentic Top 10 各项检查实现（旧版 AG 编号）
# ---------------------------------------------------------------------------

def check_ag01_prompt_injection(filepath: str, lines: list[str]) -> list[str]:
    """AG-01: 提示注入 — 检测未过滤的用户输入直接拼接到 Agent 提示词中"""
    patterns = [
        re.compile(r"(?i)f['\"].*\{.*user.*input.*\}.*(?:prompt|system|instruction)"),
        re.compile(r"(?i)(?:prompt|system_message|instruction)\s*[+=].*(?:user_input|user\.input|request\.(?:body|params|query))"),
        re.compile(r"(?i)format_prompt\([^)]*(?:user_input|user\.input)"),
        re.compile(r"(?i)(?:system|user|assistant)\s*[:=]\s*f['\"].*\{.*(?:input|query|message)"),
        re.compile(r"(?i)template.*=.*(?:user_input|request\.body|request\.params)"),
    ]
    return _match_patterns(lines, patterns)


def check_ag02_sensitive_data_disclosure(filepath: str, lines: list[str]) -> list[str]:
    """AG-02: 敏感数据泄露 — 检测硬编码的密钥、令牌和 API Key"""
    patterns = [
        re.compile(r"(?i)(?:api_key|apikey|api_secret|secret_key|access_key|private_key)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
        re.compile(r"(?i)(?:password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{4,}['\"]"),
        re.compile(r"(?i)(?:token|bearer|auth_token|session_id)\s*[:=]\s*['\"][A-Za-z0-9_\-\.]{16,}['\"]"),
        re.compile(r"(?i)-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----"),
        re.compile(r"(?i)(?:sk|pk|ghp|gho|ghs|ghc|github_pat)_[A-Za-z0-9]{20,}"),
        re.compile(r"(?i)AIza[A-Za-z0-9_\-]{35}"),
    ]
    return _match_patterns(lines, patterns)


def check_ag03_supply_chain(filepath: str, lines: list[str]) -> list[str]:
    """AG-03: 供应链安全 — 检测未经验证的外部工具/包依赖"""
    patterns = [
        re.compile(r"(?i)pip install\s+(?!--require-hashes)[^\s]*(?:\s+--no-verify)?"),
        re.compile(r"(?i)npm install\s+(?:--force|--legacy-peer-deps)"),
        re.compile(r"(?i)curl\s+[^\s]*\|\s*(?:sh|bash|python)"),
        re.compile(r"(?i)(?:import|from)\s+\w+_tool\s+import"),
        re.compile(r"(?i)tool_registry\.register\([^)]*(?:url|endpoint|remote)"),
        re.compile(r"(?i)load_plugin\([^)]*http[s]?://"),
    ]
    return _match_patterns(lines, patterns)


def check_ag04_insecure_output_handling(filepath: str, lines: list[str]) -> list[str]:
    """AG-04: 不安全的输出处理 — 检测 Agent 输出未经验证即被使用"""
    patterns = [
        re.compile(r"(?i)(?:agent|llm|model|ai)\.(?:response|output|result|content)\s*(?:\.|\[)"),
        re.compile(r"(?i)(?:agent|llm|model)\.(?:run|execute|call|invoke)\(.*\)\.(?:text|content)\s*(?:\.|\[)"),
        re.compile(r"(?i)eval\s*\(\s*(?:agent|llm|model|ai)\.(?:response|output|result)"),
        re.compile(r"(?i)(?:agent|llm|model)\.(?:response|output|result|content)\s*(?:\+|\bformat\b|\bfstring)"),
        re.compile(r"(?i)(?:write|open)\(.*(?:agent|llm|model)\.(?:response|output|content)"),
    ]
    return _match_patterns(lines, patterns)


def check_ag05_excessive_agency(filepath: str, lines: list[str]) -> list[str]:
    """AG-05: 过度授权 — 检测 Agent 拥有不受限权限或危险工具访问"""
    patterns = [
        re.compile(r"(?i)(?:tools|functions|capabilities)\s*[:=]\s*\[.*(?:shell|exec|delete|drop|rm|sudo|admin)"),
        re.compile(r"(?i)(?:allow_dangerous|dangerously_allow|unsafe_mode)\s*[:=]\s*True"),
        re.compile(r"(?i)(?:permission|auth|scope)\s*[:=]\s*['\"](?:all|\*|full|unlimited|root)['\"]"),
        re.compile(r"(?i)(?:agent|bot|assistant).*(?:sudo|root|admin|superuser)"),
        re.compile(r"(?i)(?:tool|function).*(?:execute_shell|run_command|system_call|os_command)"),
    ]
    return _match_patterns(lines, patterns)


def check_ag06_insecure_authentication(filepath: str, lines: list[str]) -> list[str]:
    """AG-06: 不安全的身份认证 — 检测端点/API 缺少认证机制"""
    patterns = [
        re.compile(r"(?i)@(?:app|router)\.(?:route|get|post|put|delete|patch)\([^)]*\)\s*$"),
        re.compile(r"(?i)(?:endpoint|api|route)\s*[:=]\s*['\"/][^'\"]*['\"].*(?:#\s*(?:no\s*auth|public|unprotected))"),
        re.compile(r"(?i)(?:auth_required|require_auth|authenticate)\s*[:=]\s*False"),
        re.compile(r"(?i)(?:middleware|guard|interceptor).*skip.*auth"),
        re.compile(r"(?i)(?:cors)\s*[:=]\s*\*"),
    ]
    return _match_patterns(lines, patterns)


def check_ag07_insecure_communication(filepath: str, lines: list[str]) -> list[str]:
    """AG-07: 不安全的通信 — 检测 Agent 间未加密的通信模式"""
    patterns = [
        re.compile(r"(?i)http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)[^\s'\"]+"),
        re.compile(r"(?i)(?:agent|service|peer)\.(?:connect|send|call|invoke)\s*\(\s*['\"]http://"),
        re.compile(r"(?i)(?:grpc|rpc)\.(?:connect|dial|call)\s*\(\s*['\"]http://"),
        re.compile(r"(?i)(?:ssl_verify|verify_ssl|tls_verify)\s*[:=]\s*False"),
        re.compile(r"(?i)(?:insecure|skip_verify|no_tls|disable_ssl)\s*[:=]\s*True"),
    ]
    return _match_patterns(lines, patterns)


def check_ag08_model_poisoning(filepath: str, lines: list[str]) -> list[str]:
    """AG-08: 模型投毒 — 检测不受信任的模型来源或配置"""
    patterns = [
        re.compile(r"(?i)(?:model|checkpoint|weights)\s*[:=]\s*['\"](?:http|ftp)://[^'\"]+['\"]"),
        re.compile(r"(?i)(?:load_model|from_pretrained)\s*\(\s*['\"](?:http|ftp)://"),
        re.compile(r"(?i)(?:model|llm)\s*[:=]\s*['\"][^'\"]*(?:huggingface|hf\.co|civitai)[^'\"]*['\"]"),
        re.compile(r"(?i)(?:trust_remote_code|remote_code)\s*[:=]\s*True"),
        re.compile(r"(?i)(?:revision|variant)\s*[:=]\s*['\"](?:main|master)['\"].*trust"),
    ]
    return _match_patterns(lines, patterns)


def check_ag09_insecure_plugin_design(filepath: str, lines: list[str]) -> list[str]:
    """AG-09: 不安全的插件设计 — 检测插件缺少沙箱或资源限制"""
    patterns = [
        re.compile(r"(?i)(?:plugin|extension|addon)\s*[:=]\s*\{[^}]*(?:exec|eval|system|popen)"),
        re.compile(r"(?i)(?:sandbox|isolation|container)\s*[:=]\s*(?:False|None|['\"]disabled['\"])"),
        re.compile(r"(?i)(?:max_tokens|timeout|rate_limit|resource_limit)\s*[:=]\s*(?:None|Infinity|inf|-1|0)"),
        re.compile(r"(?i)(?:plugin|tool|extension).*(?:os\.|subprocess|sys\.)"),
        re.compile(r"(?i)(?:allow_network|network_access|internet_access)\s*[:=]\s*True"),
    ]
    return _match_patterns(lines, patterns)


def check_ag10_insufficient_monitoring(filepath: str, lines: list[str]) -> list[str]:
    """AG-10: 监控不足 — 检测缺少审计日志配置"""
    patterns = [
        re.compile(r"(?i)(?:logging|logger|audit)\s*[:=]\s*(?:None|False|['\"]disabled['\"])"),
        re.compile(r"(?i)(?:log_level|logging_level)\s*[:=]\s*['\"](?:CRITICAL|OFF|NONE)['\"]"),
        re.compile(r"(?i)(?:agent|llm|model).*(?:no_log|skip_log|disable_log|log_disabled)"),
        re.compile(r"(?i)(?:audit|trace|observability)\s*[:=]\s*(?:False|None|disabled)"),
        re.compile(r"(?i)(?:monitoring|telemetry)\s*[:=]\s*(?:False|None|disabled)"),
    ]
    return _match_patterns(lines, patterns)


# ---------------------------------------------------------------------------
# 以下为 OWASP Agentic Top 10 2026 ASI 编号检查实现
# ---------------------------------------------------------------------------

def check_asi01_goal_hijack(filepath: str, lines: list[str]) -> list[str]:
    """ASI01: 目标劫持 — 检测Agent目标可被外部输入覆盖或修改的风险"""
    patterns = [
        re.compile(r"(?i)(?:goal|objective|target|mission)\s*[:=]\s*(?:user_input|request\.(?:body|params|query)|external_input)"),
        re.compile(r"(?i)(?:system_prompt|system_message)\s*[+=]\s*(?:user_input|user\.input|request\.(?:body|params))"),
        re.compile(r"(?i)(?:ignore|forget|override|bypass)\s+(?:previous|prior|above|all)\s+(?:instruction|prompt|directive|rule)"),
        re.compile(r"(?i)(?:new_goal|updated_goal|change_goal)\s*[:=]"),
        re.compile(r"(?i)goal\s*=\s*.*(?:user_message|chat_input|conversation\[\-1\])"),
    ]
    return _match_patterns(lines, patterns)


def check_asi02_tool_misuse(filepath: str, lines: list[str]) -> list[str]:
    """ASI02: 工具滥用与利用 — 检测工具调用缺少参数验证或权限控制"""
    patterns = [
        re.compile(r"(?i)(?:tool|function)_call\s*\([^)]*(?:user_input|raw_input|unvalidated)"),
        re.compile(r"(?i)(?:execute_tool|call_tool|invoke_tool)\s*\(\s*(?:user_input|request\.body)"),
        re.compile(r"(?i)(?:tool|function)_params\s*[:=]\s*(?:user_input|request\.(?:body|params))"),
        re.compile(r"(?i)(?:rate_limit|throttle|max_calls)\s*[:=]\s*(?:None|Infinity|inf|-1|0)"),
        re.compile(r"(?i)(?:tool_chain|chain_depth|max_chain)\s*[:=]\s*(?:None|Infinity|inf|-1|0|100)"),
    ]
    return _match_patterns(lines, patterns)


def check_asi03_identity_privilege_abuse(filepath: str, lines: list[str]) -> list[str]:
    """ASI03: 身份权限滥用 — 检测Agent身份冒充、委派链滥用和凭证缓存风险"""
    patterns = [
        re.compile(r"(?i)(?:delegate|impersonate|act_as)\s*\(\s*(?:user|admin|root|superuser)"),
        re.compile(r"(?i)(?:api_key|token|credential|secret)\s*[:=]\s*(?:context|memory|session)\["),
        re.compile(r"(?i)(?:permission|role|scope)\s*[:=]\s*['\"](?:admin|root|superuser|god)['\"]"),
        re.compile(r"(?i)(?:delegation_depth|max_delegate)\s*[:=]\s*(?:None|Infinity|inf|-1|0)"),
        re.compile(r"(?i)(?:cache|store|persist).*?(?:credential|token|api_key|secret)"),
    ]
    return _match_patterns(lines, patterns)


def check_asi04_supply_chain(filepath: str, lines: list[str]) -> list[str]:
    """ASI04: Agentic供应链漏洞 — 检测不可信的模型、工具、插件来源"""
    patterns = [
        re.compile(r"(?i)(?:load_model|from_pretrained)\s*\(\s*['\"](?:http|ftp)://[^'\"]+['\"].*trust_remote_code\s*=\s*True"),
        re.compile(r"(?i)(?:plugin|tool|extension)_registry\.register\([^)]*(?:url|endpoint|remote|http)"),
        re.compile(r"(?i)(?:mcp_server|tool_server)\s*[:=]\s*\{[^}]*(?:url|endpoint)[^}]*(?:no_auth|auth\s*[:=]\s*False)"),
        re.compile(r"(?i)(?:component|dependency)\s*[:=]\s*['\"](?:http|ftp)://[^'\"]+['\"].*(?:no_verify|skip_verify|verify\s*[:=]\s*False)"),
        re.compile(r"(?i)(?:prompt_template|agent_description)\s*[:=]\s*['\"](?:http|ftp)://"),
    ]
    return _match_patterns(lines, patterns)


def check_asi05_unexpected_code_execution(filepath: str, lines: list[str]) -> list[str]:
    """ASI05: 意外代码执行 — 检测Agent输出被直接执行或代码注入风险"""
    patterns = [
        re.compile(r"(?i)eval\s*\(\s*(?:agent|llm|model|ai)\.(?:response|output|result|content)"),
        re.compile(r"(?i)exec\s*\(\s*(?:agent|llm|model|ai)\.(?:response|output|result|content)"),
        re.compile(r"(?i)(?:subprocess|os\.system|os\.popen)\s*\(\s*(?:agent|llm|model|ai)\.(?:response|output)"),
        re.compile(r"(?i)(?:sandbox|isolation|container)\s*[:=]\s*(?:False|None|['\"]disabled['\"])"),
        re.compile(r"(?i)(?:auto_execute|auto_run|self_heal|auto_fix)\s*[:=]\s*True"),
    ]
    return _match_patterns(lines, patterns)


def check_asi06_memory_context_poisoning(filepath: str, lines: list[str]) -> list[str]:
    """ASI06: 记忆与上下文污染 — 检测记忆写入缺少验证或RAG存储投毒风险"""
    patterns = [
        re.compile(r"(?i)(?:memory|long_term_memory|persistent_memory)\.(?:write|store|save|update)\s*\(\s*(?:user_input|raw_input)"),
        re.compile(r"(?i)(?:vector_db|embedding_store|rag_store)\.(?:insert|add|upsert)\s*\(\s*(?:user_input|raw_content)"),
        re.compile(r"(?i)(?:context|conversation_history)\.(?:append|add|push)\s*\(\s*(?:user_input|raw_input)"),
        re.compile(r"(?i)(?:memory|knowledge_base|rag).*?(?:no_validation|skip_validate|validate\s*[:=]\s*False)"),
        re.compile(r"(?i)(?:max_context|context_window|context_size)\s*[:=]\s*(?:None|Infinity|inf|-1)"),
    ]
    return _match_patterns(lines, patterns)


def check_asi07_insecure_inter_agent_comm(filepath: str, lines: list[str]) -> list[str]:
    """ASI07: 不安全Agent间通信 — 检测Agent间通信缺少加密、签名或防重放机制"""
    patterns = [
        re.compile(r"(?i)(?:agent|peer|node)\.(?:send|broadcast|emit)\s*\([^)]*(?:http://|unencrypted|plaintext)"),
        re.compile(r"(?i)(?:message|msg)\s*[:=]\s*\{[^}]*(?:no_sign|unsigned|skip_verify)"),
        re.compile(r"(?i)(?:nonce|replay_protection|anti_replay)\s*[:=]\s*(?:False|None|disabled)"),
        re.compile(r"(?i)(?:channel|connection)\.(?:establish|connect)\s*\([^)]*(?:no_tls|no_encryption|plaintext)"),
        re.compile(r"(?i)(?:a2a|agent_to_agent|inter_agent).*?(?:no_auth|auth\s*[:=]\s*False|skip_verify)"),
    ]
    return _match_patterns(lines, patterns)


def check_asi08_cascading_failures(filepath: str, lines: list[str]) -> list[str]:
    """ASI08: 级联故障 — 检测缺少熔断、检查点或故障隔离机制"""
    patterns = [
        re.compile(r"(?i)(?:circuit_breaker|breaker)\s*[:=]\s*(?:False|None|disabled)"),
        re.compile(r"(?i)(?:checkpoint|rollback|recovery)\s*[:=]\s*(?:False|None|disabled)"),
        re.compile(r"(?i)(?:retry|max_retries|retry_limit)\s*[:=]\s*(?:None|Infinity|inf|-1|100)"),
        re.compile(r"(?i)(?:isolation|bulkhead|fault_zone)\s*[:=]\s*(?:False|None|disabled)"),
        re.compile(r"(?i)(?:shared_memory|shared_state|global_state).*?(?:no_lock|no_mutex|no_sync)"),
    ]
    return _match_patterns(lines, patterns)


def check_asi09_excessive_agency(filepath: str, lines: list[str]) -> list[str]:
    """ASI09: 过度自主 — 检测Agent拥有不受限权限或缺少人工审批机制"""
    patterns = [
        re.compile(r"(?i)(?:auto_approve|self_approve|skip_approval|no_human_review)\s*[:=]\s*True"),
        re.compile(r"(?i)(?:permission|capability|scope)\s*[:=]\s*['\"](?:all|\*|full|unlimited|root|god)['\"]"),
        re.compile(r"(?i)(?:human_in_the_loop|human_review|approval_required)\s*[:=]\s*False"),
        re.compile(r"(?i)(?:agent|bot|assistant).*(?:delete|drop|remove|destroy|format|wipe)"),
        re.compile(r"(?i)(?:max_autonomy|autonomy_level)\s*[:=]\s*(?:None|Infinity|inf|10|100|'full')"),
    ]
    return _match_patterns(lines, patterns)


def check_asi10_observability_gaps(filepath: str, lines: list[str]) -> list[str]:
    """ASI10: 可观测性缺失 — 检测缺少审计日志、监控或可追溯性机制"""
    patterns = [
        re.compile(r"(?i)(?:audit_log|audit_trail|audit_logger)\s*[:=]\s*(?:False|None|disabled)"),
        re.compile(r"(?i)(?:logging|log_level)\s*[:=]\s*(?:False|None|['\"](?:OFF|NONE|CRITICAL)['\"])"),
        re.compile(r"(?i)(?:trace|tracing|distributed_trace)\s*[:=]\s*(?:False|None|disabled)"),
        re.compile(r"(?i)(?:monitoring|telemetry|metrics)\s*[:=]\s*(?:False|None|disabled)"),
        re.compile(r"(?i)(?:alert|alerting|notification)\s*[:=]\s*(?:False|None|disabled)"),
    ]
    return _match_patterns(lines, patterns)


# ---------------------------------------------------------------------------
# 检查定义注册表
# ---------------------------------------------------------------------------

CHECKS = [
    {
        "id": "AG-01",
        "risk": "Prompt Injection",
        "severity": "critical",
        "checker": check_ag01_prompt_injection,
        "remediation": "对用户输入进行严格的验证和转义，使用参数化提示模板而非字符串拼接，实施输入长度限制和内容过滤",
    },
    {
        "id": "AG-02",
        "risk": "Sensitive Data Disclosure",
        "severity": "critical",
        "checker": check_ag02_sensitive_data_disclosure,
        "remediation": "使用环境变量或密钥管理服务存储敏感信息，禁止硬编码密钥，实施 .gitignore 排除敏感文件",
    },
    {
        "id": "AG-03",
        "risk": "Supply Chain",
        "severity": "high",
        "checker": check_ag03_supply_chain,
        "remediation": "使用锁文件和哈希校验固定依赖版本，验证外部工具来源完整性，禁止运行时从远程加载未验证的插件",
    },
    {
        "id": "AG-04",
        "risk": "Insecure Output Handling",
        "severity": "high",
        "checker": check_ag04_insecure_output_handling,
        "remediation": "对 Agent 输出进行结构化验证和清洗，禁止直接将输出用于代码执行或文件写入，实施输出长度和格式限制",
    },
    {
        "id": "AG-05",
        "risk": "Excessive Agency",
        "severity": "high",
        "checker": check_ag05_excessive_agency,
        "remediation": "遵循最小权限原则限制 Agent 工具访问，禁用危险操作（如 shell 执行），实施人工审批机制",
    },
    {
        "id": "AG-06",
        "risk": "Insecure Authentication",
        "severity": "high",
        "checker": check_ag06_insecure_authentication,
        "remediation": "为所有 API 端点强制实施身份认证，使用标准认证中间件，禁止 CORS 通配符配置",
    },
    {
        "id": "AG-07",
        "risk": "Insecure Communication",
        "severity": "medium",
        "checker": check_ag07_insecure_communication,
        "remediation": "强制使用 HTTPS/TLS 加密所有 Agent 间通信，启用证书验证，禁止跳过 SSL 验证",
    },
    {
        "id": "AG-08",
        "risk": "Model Poisoning",
        "severity": "high",
        "checker": check_ag08_model_poisoning,
        "remediation": "仅从受信任的源加载模型，验证模型文件完整性和签名，禁止启用 trust_remote_code",
    },
    {
        "id": "AG-09",
        "risk": "Insecure Plugin Design",
        "severity": "medium",
        "checker": check_ag09_insecure_plugin_design,
        "remediation": "为插件启用沙箱隔离，设置资源使用上限（令牌、超时、速率），禁止插件直接访问系统调用",
    },
    {
        "id": "AG-10",
        "risk": "Insufficient Monitoring",
        "severity": "medium",
        "checker": check_ag10_insufficient_monitoring,
        "remediation": "为所有 Agent 操作启用审计日志，配置合理的日志级别，实施实时监控和告警机制",
    },
    {
        "id": "ASI01",
        "risk": "Goal Hijack",
        "severity": "critical",
        "checker": check_asi01_goal_hijack,
        "remediation": "使用不可变目标封装(ImmutableGoal)，对所有用户输入执行注入模式检测和清理，实施目标偏离监控和RAG检索验证",
    },
    {
        "id": "ASI02",
        "risk": "Tool Misuse & Exploitation",
        "severity": "critical",
        "checker": check_asi02_tool_misuse,
        "remediation": "对所有工具调用参数进行白名单校验和注入模式检测，实施调用频率限制和调用链深度控制",
    },
    {
        "id": "ASI03",
        "risk": "Identity & Privilege Abuse",
        "severity": "high",
        "checker": check_asi03_identity_privilege_abuse,
        "remediation": "维护细粒度权限矩阵，限制委派链深度和范围，使用SAGA访问控制令牌，禁止凭证写入上下文或长期记忆",
    },
    {
        "id": "ASI04",
        "risk": "Agentic Supply Chain Vulnerabilities",
        "severity": "high",
        "checker": check_asi04_supply_chain,
        "remediation": "对所有外部组件进行哈希校验和数字签名验证，为模型注册唯一指纹，扫描MCP服务器安全配置",
    },
    {
        "id": "ASI05",
        "risk": "Unexpected Code Execution",
        "severity": "critical",
        "checker": check_asi05_unexpected_code_execution,
        "remediation": "所有代码在受限沙箱中执行，执行前分析代码内容检测恶意模式，高风险代码执行需人工审批",
    },
    {
        "id": "ASI06",
        "risk": "Memory & Context Poisoning",
        "severity": "high",
        "checker": check_asi06_memory_context_poisoning,
        "remediation": "对所有写入持久化记忆的内容进行污染模式检测，实施上下文完整性检查和RAG存储安全控制",
    },
    {
        "id": "ASI07",
        "risk": "Insecure Inter-Agent Communication",
        "severity": "high",
        "checker": check_asi07_insecure_inter_agent_comm,
        "remediation": "所有Agent间通信使用端到端加密，每条消息附带数字签名，使用Nonce机制防止重放攻击",
    },
    {
        "id": "ASI08",
        "risk": "Cascading Failures",
        "severity": "high",
        "checker": check_asi08_cascading_failures,
        "remediation": "实施Circuit Breaker熔断机制，在关键节点创建检查点，使用Runtime Supervisor监控Agent健康状态",
    },
    {
        "id": "ASI09",
        "risk": "Excessive Agency",
        "severity": "high",
        "checker": check_asi09_excessive_agency,
        "remediation": "为每个Agent定义明确权限边界，根据操作风险等级实施分层审批，高风险操作必须人工确认",
    },
    {
        "id": "ASI10",
        "risk": "Observability & Monitoring Gaps",
        "severity": "medium",
        "checker": check_asi10_observability_gaps,
        "remediation": "使用哈希链保证审计日志不可篡改，确保所有Agent和通信通道在监控范围内，实施异常检测和分级告警",
    },
]


def run_scan(target: str, severity_threshold: str) -> list[dict]:
    """执行全部安全检查，返回发现列表"""
    files = collect_files(target)
    findings: list[dict] = []

    for check in CHECKS:
        affected_files: list[str] = []
        for filepath in files:
            lines = read_lines(filepath)
            if not lines:
                continue
            matched_line_nums = check["checker"](filepath, lines)
            for ln in matched_line_nums:
                affected_files.append(f"{filepath}:{ln}")

        if affected_files:
            findings.append({
                "id": check["id"],
                "risk": check["risk"],
                "severity": check["severity"],
                "status": "failed",
                "detail": f"检测到 {check['risk']} 风险：在 {len(affected_files)} 处发现潜在问题",
                "files": affected_files,
                "remediation": check["remediation"],
            })
        else:
            findings.append({
                "id": check["id"],
                "risk": check["risk"],
                "severity": check["severity"],
                "status": "passed",
                "detail": f"未检测到 {check['risk']} 风险",
                "files": [],
                "remediation": check["remediation"],
            })

    return findings


def filter_findings(findings: list[dict], severity_threshold: str) -> list[dict]:
    """根据严重级别阈值过滤发现项，仅保留达到阈值级别的失败项"""
    filtered = []
    for f in findings:
        if f["status"] == "failed" and severity_gte(f["severity"], severity_threshold):
            filtered.append(f)
    return filtered


def build_report(target: str, findings: list[dict], severity_threshold: str) -> dict:
    """构建扫描报告"""
    total = len(CHECKS)
    passed = sum(1 for f in findings if f["status"] == "passed")
    failed_findings = [f for f in findings if f["status"] == "failed"]
    failed = len(failed_findings)
    warnings = sum(1 for f in failed_findings if not severity_gte(f["severity"], severity_threshold))
    compliance_rate = round(passed / total, 2) if total > 0 else 0.0

    report_findings = []
    for f in findings:
        if f["status"] == "passed":
            report_findings.append(f)
        elif severity_gte(f["severity"], severity_threshold):
            report_findings.append(f)
        else:
            warning_entry = {**f, "status": "warning"}
            report_findings.append(warning_entry)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "target": os.path.abspath(target),
        "summary": {
            "total_checks": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "compliance_rate": compliance_rate,
        },
        "findings": report_findings,
    }


def format_text_report(report: dict) -> str:
    """将报告格式化为可读文本"""
    lines = []
    lines.append("=" * 70)
    lines.append("OWASP Agentic AI Top 10 (2026) 安全合规扫描报告")
    lines.append("=" * 70)
    lines.append(f"扫描时间: {report['timestamp']}")
    lines.append(f"扫描目标: {report['target']}")
    lines.append("")

    s = report["summary"]
    lines.append(f"总检查项: {s['total_checks']}  通过: {s['passed']}  "
                 f"失败: {s['failed']}  警告: {s['warnings']}  "
                 f"合规率: {s['compliance_rate']:.0%}")
    lines.append("-" * 70)

    for f in report["findings"]:
        status_icon = {"passed": "[PASS]", "failed": "[FAIL]", "warning": "[WARN]"}[f["status"]]
        lines.append(f"{status_icon} {f['id']} {f['risk']} [{f['severity'].upper()}]")
        lines.append(f"  {f['detail']}")
        if f["files"]:
            for file_ref in f["files"][:10]:
                lines.append(f"    -> {file_ref}")
            if len(f["files"]) > 10:
                lines.append(f"    ... 还有 {len(f['files']) - 10} 处")
        lines.append(f"  修复建议: {f['remediation']}")
        lines.append("")

    lines.append("=" * 70)
    return "\n".join(lines)


def main() -> int:
    """主入口函数"""
    parser = argparse.ArgumentParser(
        description="OWASP Agentic AI Top 10 (2026) 安全合规扫描器"
    )
    parser.add_argument(
        "--target",
        default=".",
        help="目标扫描目录（默认: 当前目录）",
    )
    parser.add_argument(
        "--severity-threshold",
        choices=["critical", "high", "medium", "low"],
        default="medium",
        help="最低报告严重级别（默认: medium）",
    )
    parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="输出格式（默认: json）",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出文件路径（默认: 标准输出）",
    )

    args = parser.parse_args()

    target_path = Path(args.target).resolve()
    if not target_path.is_dir():
        print(f"错误: 目标路径不存在或不是目录: {target_path}", file=sys.stderr)
        return 2

    try:
        findings = run_scan(str(target_path), args.severity_threshold)
        report = build_report(str(target_path), findings, args.severity_threshold)
    except Exception as exc:
        print(f"扫描过程中发生错误: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        output_content = json.dumps(report, ensure_ascii=False, indent=2)
    else:
        output_content = format_text_report(report)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(output_content)
                fh.write("\n")
        except OSError as exc:
            print(f"无法写入输出文件: {exc}", file=sys.stderr)
            return 2
    else:
        sys.stdout.buffer.write(output_content.encode("utf-8"))
        sys.stdout.buffer.write(b"\n")

    above_threshold = filter_findings(findings, args.severity_threshold)
    return 1 if above_threshold else 0


if __name__ == "__main__":
    sys.exit(main())
