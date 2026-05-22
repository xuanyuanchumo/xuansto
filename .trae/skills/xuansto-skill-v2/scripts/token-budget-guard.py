#!/usr/bin/env python3
"""Token Budget Guard - Token预算门禁运行时强制执行脚本

读取.skill-config.yaml配置，按Phase/Agent维度追踪Token消耗，
在超过阈值时触发压缩或阻断执行。

用法:
    python token-budget-guard.py [--config .skill-config.yaml] [--check] [--report]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".skill-config.yaml")

PHASES = [f"phase_{i}" for i in range(9)]
AGENT_LAYERS = [
    "orchestrator", "product", "design", "engineering",
    "cross_platform", "database", "testing", "security",
    "devops", "quality", "documentation"
]


def _simple_yaml_load(text):
    result = {}
    stack = [(result, -1)]
    for line in text.splitlines():
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(stripped)
        while stack and stack[-1][1] >= indent:
            stack.pop()
        if ":" not in stripped:
            continue
        key, _, value = stripped.partition(":")
        key = key.strip()
        value = value.strip()
        parent, _ = stack[-1]
        if value == "":
            new_dict = {}
            parent[key] = new_dict
            stack.append((new_dict, indent))
        else:
            if value.lower() == "true":
                parsed = True
            elif value.lower() == "false":
                parsed = False
            elif value.lower() in ("null", "~"):
                parsed = None
            else:
                try:
                    parsed = int(value)
                except ValueError:
                    try:
                        parsed = float(value)
                    except ValueError:
                        parsed = value.strip('"').strip("'")
            parent[key] = parsed
    return result


def load_config(config_path):
    if not os.path.exists(config_path):
        print(f"[WARN] Config not found: {config_path}, using defaults")
        return get_default_config()
    with open(config_path, "r", encoding="utf-8") as f:
        content = f.read()
    if yaml:
        return yaml.safe_load(content)
    print("[WARN] pyyaml not installed, using simple YAML parser. Install pyyaml for full support: pip install pyyaml")
    return _simple_yaml_load(content)


def get_default_config():
    return {
        "token_budget": {
            "default": 100000,
            "warning_threshold": 0.7,
            "compression_threshold": 0.8,
            "block_threshold": 1.0,
        },
        "logging": {
            "dir": ".skill-logs",
            "gate_exceptions_file": "gate-exceptions.jsonl",
        }
    }


def _get_log_dir(config):
    log_cfg = config.get("logging", {})
    return log_cfg.get("dir", ".skill-logs")


def _get_jsonl_path(config):
    return os.path.join(_get_log_dir(config), "token-usage.jsonl")


def _ensure_log_dir(config):
    log_dir = _get_log_dir(config)
    os.makedirs(log_dir, exist_ok=True)


def load_consumption_from_jsonl(jsonl_path):
    consumption = {
        "total": 0,
        "by_phase": {p: 0 for p in PHASES},
        "by_agent": {},
    }
    if not os.path.exists(jsonl_path):
        return consumption
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                tokens = entry.get("tokens", 0)
                phase = entry.get("phase")
                agent = entry.get("agent")
                consumption["total"] += tokens
                if phase and phase in consumption["by_phase"]:
                    consumption["by_phase"][phase] += tokens
                if agent:
                    consumption["by_agent"][agent] = consumption["by_agent"].get(agent, 0) + tokens
            except json.JSONDecodeError:
                continue
    return consumption


def append_record_to_jsonl(jsonl_path, tokens, phase, agent):
    entry = {
        "timestamp": datetime.now().isoformat(),
        "tokens": tokens,
        "phase": phase,
        "agent": agent,
    }
    with open(jsonl_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class TokenTracker:
    def __init__(self, config):
        self.config = config
        self.budget_config = config.get("token_budget", {})
        self.total_budget = self.budget_config.get("default", 100000)
        self.warning_threshold = self.budget_config.get("warning_threshold", 0.7)
        self.compression_threshold = self.budget_config.get("compression_threshold", 0.8)
        self.block_threshold = self.budget_config.get("block_threshold", 1.0)
        self.phase_budgets = self.budget_config.get("per_phase", {})
        self.jsonl_path = _get_jsonl_path(config)
        self.consumption = load_consumption_from_jsonl(self.jsonl_path)

    def record(self, tokens, phase=None, agent=None):
        self.consumption["total"] += tokens
        if phase and phase in self.consumption["by_phase"]:
            self.consumption["by_phase"][phase] += tokens
        if agent:
            self.consumption["by_agent"][agent] = self.consumption["by_agent"].get(agent, 0) + tokens
        _ensure_log_dir(self.config)
        append_record_to_jsonl(self.jsonl_path, tokens, phase, agent)

    def check_status(self):
        ratio = self.consumption["total"] / self.total_budget if self.total_budget > 0 else 0
        if ratio >= self.block_threshold:
            return "BLOCK", ratio
        elif ratio >= self.compression_threshold:
            return "COMPRESS", ratio
        elif ratio >= self.warning_threshold:
            return "WARN", ratio
        return "OK", ratio

    def check_phase(self, phase):
        phase_budget = self.phase_budgets.get(phase, self.total_budget / 9)
        phase_consumed = self.consumption["by_phase"].get(phase, 0)
        ratio = phase_consumed / phase_budget if phase_budget > 0 else 0
        if ratio >= self.block_threshold:
            return "BLOCK", ratio
        elif ratio >= self.compression_threshold:
            return "COMPRESS", ratio
        elif ratio >= self.warning_threshold:
            return "WARN", ratio
        return "OK", ratio

    def generate_report(self):
        status, ratio = self.check_status()
        lines = [
            "=" * 60,
            "Token Budget Guard Report",
            "=" * 60,
            f"Total Budget:  {self.total_budget:,}",
            f"Total Used:    {self.consumption['total']:,} ({ratio:.1%})",
            f"Status:        {status}",
            "-" * 60,
            "Phase Distribution:",
        ]
        for phase in PHASES:
            budget = self.phase_budgets.get(phase, self.total_budget // 9)
            consumed = self.consumption["by_phase"].get(phase, 0)
            pct = consumed / budget if budget > 0 else 0
            bar_len = int(pct * 20)
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  {phase:10s} [{bar}] {consumed:>8,}/{budget:>8,} ({pct:.1%})")
        lines.append("-" * 60)
        lines.append("Top Agent Consumers:")
        sorted_agents = sorted(
            self.consumption["by_agent"].items(), key=lambda x: x[1], reverse=True
        )[:5]
        for agent, consumed in sorted_agents:
            pct = consumed / self.total_budget if self.total_budget > 0 else 0
            lines.append(f"  {agent:25s} {consumed:>8,} ({pct:.1%})")
        lines.append("=" * 60)
        return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Token Budget Guard")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH, help="Path to .skill-config.yaml")
    parser.add_argument("--check", action="store_true", help="Check current budget status")
    parser.add_argument("--report", action="store_true", help="Generate budget report")
    parser.add_argument("--record", nargs=3, metavar=("TOKENS", "PHASE", "AGENT"), help="Record token usage")
    args = parser.parse_args()

    config = load_config(args.config)
    tracker = TokenTracker(config)

    if args.record:
        tokens, phase, agent = args.record
        tracker.record(int(tokens), phase, agent)
        status, ratio = tracker.check_status()
        if status == "BLOCK":
            print(f"[BLOCK] Token budget exceeded: {ratio:.1%} of budget")
            sys.exit(1)
        elif status == "COMPRESS":
            print(f"[COMPRESS] Token budget compression triggered: {ratio:.1%}")
        elif status == "WARN":
            print(f"[WARN] Token budget warning: {ratio:.1%}")
        else:
            print(f"[OK] Token budget status: {ratio:.1%}")

    if args.check:
        status, ratio = tracker.check_status()
        print(f"Status: {status} | Usage: {ratio:.1%}")

    if args.report:
        print(tracker.generate_report())

    if not (args.record or args.check or args.report):
        print(tracker.generate_report())


if __name__ == "__main__":
    main()
