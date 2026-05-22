#!/usr/bin/env python3
import argparse
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

COMPRESSION_BASELINE_TOKENS = 1000
TPM_BASELINE = 50


def parse_args():
    parser = argparse.ArgumentParser(description="Token Consumption Monitoring Dashboard")
    parser.add_argument("--task-id", default=None, help="View specific task")
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (default: text)")
    parser.add_argument("--knowledge-dir", default=".knowledge", help="Path to .knowledge directory (default: .knowledge)")
    return parser.parse_args()


def load_token_logs(knowledge_dir):
    token_dir = os.path.join(knowledge_dir, "token-usage")
    if not os.path.isdir(token_dir):
        return []
    logs = []
    for fname in os.listdir(token_dir):
        fpath = os.path.join(token_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        logs.append(entry)
                    except json.JSONDecodeError:
                        continue
        except (OSError, UnicodeDecodeError):
            continue
    return logs


def load_checkpoints(knowledge_dir):
    cp_dir = os.path.join(knowledge_dir, "checkpoints")
    if not os.path.isdir(cp_dir):
        return {}
    checkpoints = {}
    for fname in os.listdir(cp_dir):
        fpath = os.path.join(cp_dir, fname)
        if not os.path.isfile(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                task_id = data.get("task_id", fname)
                checkpoints[task_id] = data
        except (json.JSONDecodeError, OSError, UnicodeDecodeError):
            continue
    return checkpoints


def filter_logs(logs, task_id):
    if task_id is None:
        return logs
    return [l for l in logs if l.get("task_id") == task_id]


def compute_task_metrics(logs):
    metrics = {}
    task_logs = defaultdict(list)
    for l in logs:
        tid = l.get("task_id", "unknown")
        task_logs[tid].append(l)
    for tid, entries in task_logs.items():
        total_in = sum(e.get("tokens_in", 0) for e in entries)
        total_out = sum(e.get("tokens_out", 0) for e in entries)
        phase_dist = defaultdict(lambda: {"tokens_in": 0, "tokens_out": 0})
        for e in entries:
            phase = e.get("phase", "unknown")
            phase_dist[phase]["tokens_in"] += e.get("tokens_in", 0)
            phase_dist[phase]["tokens_out"] += e.get("tokens_out", 0)
        metrics[tid] = {
            "total_tokens": total_in + total_out,
            "tokens_in": total_in,
            "tokens_out": total_out,
            "phase_distribution": dict(phase_dist),
        }
    return metrics


def compute_agent_metrics(logs):
    metrics = {}
    agent_logs = defaultdict(list)
    for l in logs:
        aid = l.get("agent_id", "unknown")
        agent_logs[aid].append(l)
    for aid, entries in agent_logs.items():
        total_in = sum(e.get("tokens_in", 0) for e in entries)
        total_out = sum(e.get("tokens_out", 0) for e in entries)
        invocations = len(entries)
        avg_tokens = (total_in + total_out) / invocations if invocations > 0 else 0
        metrics[aid] = {
            "total_tokens": total_in + total_out,
            "tokens_in": total_in,
            "tokens_out": total_out,
            "invocations": invocations,
            "avg_tokens_per_invocation": round(avg_tokens, 2),
        }
    return metrics


def compute_phase_metrics(logs):
    metrics = {}
    phase_logs = defaultdict(list)
    for l in logs:
        phase = l.get("phase", "unknown")
        phase_logs[phase].append(l)
    for phase, entries in phase_logs.items():
        total_in = sum(e.get("tokens_in", 0) for e in entries)
        total_out = sum(e.get("tokens_out", 0) for e in entries)
        timestamps = []
        for e in entries:
            ts = e.get("timestamp")
            if ts:
                try:
                    timestamps.append(datetime.fromisoformat(ts))
                except (ValueError, TypeError):
                    pass
        duration = None
        if len(timestamps) >= 2:
            duration = (max(timestamps) - min(timestamps)).total_seconds()
        metrics[phase] = {
            "total_tokens": total_in + total_out,
            "tokens_in": total_in,
            "tokens_out": total_out,
            "entry_count": len(entries),
            "duration_seconds": duration,
        }
    return metrics


def compute_system_metrics(logs, checkpoints):
    total_in = sum(l.get("tokens_in", 0) for l in logs)
    total_out = sum(l.get("tokens_out", 0) for l in logs)
    compression_events = sum(l.get("compression_events", 0) for l in logs if isinstance(l.get("compression_events"), (int, float)))
    total_tasks = len(set(l.get("task_id") for l in logs if l.get("task_id")))
    budget = 0
    for cp in checkpoints.values():
        budget = max(budget, cp.get("token_budget", 0))
    budget_util = 0
    if budget > 0:
        budget_util = round((total_in + total_out) / budget * 100, 2)
    return {
        "total_tokens": total_in + total_out,
        "total_tokens_in": total_in,
        "total_tokens_out": total_out,
        "compression_events": compression_events,
        "total_tasks": total_tasks,
        "token_budget": budget,
        "budget_utilization_pct": budget_util,
    }


def compute_tes(system_metrics, task_metrics, logs, checkpoints):
    quality_gate_pass = 0
    quality_gate_total = 0
    for cp in checkpoints.values():
        gates = cp.get("quality_gates", [])
        if isinstance(gates, list):
            quality_gate_total += len(gates)
            quality_gate_pass += sum(1 for g in gates if g.get("passed", False))
    quality_score = (quality_gate_pass / quality_gate_total * 100) if quality_gate_total > 0 else 100

    completed_tasks = 0
    total_tasks_count = len(task_metrics)
    for cp in checkpoints.values():
        if cp.get("status") == "completed":
            completed_tasks += 1
    if total_tasks_count == 0 and len(checkpoints) > 0:
        total_tasks_count = len(checkpoints)
    completion_score = (completed_tasks / total_tasks_count * 100) if total_tasks_count > 0 else 100

    compression_events = system_metrics["compression_events"]
    total_tokens = system_metrics["total_tokens"]
    if compression_events > 0 and total_tokens > 0:
        compression_ratio = min(total_tokens / (compression_events * COMPRESSION_BASELINE_TOKENS), 1.0) * 100
    else:
        compression_ratio = 100
    compression_score = compression_ratio

    budget_util = system_metrics["budget_utilization_pct"]
    if budget_util <= 80:
        budget_score = 100
    elif budget_util <= 95:
        budget_score = max(0, 100 - (budget_util - 80) * 4)
    else:
        budget_score = max(0, 100 - (budget_util - 80) * 6)
    budget_score = min(100, max(0, budget_score))

    timestamps = []
    for l in logs:
        ts = l.get("timestamp")
        if ts:
            try:
                timestamps.append(datetime.fromisoformat(ts))
            except (ValueError, TypeError):
                pass
    time_score = 0
    if len(timestamps) >= 2:
        duration_minutes = (max(timestamps) - min(timestamps)).total_seconds() / 60
        if duration_minutes > 0:
            tpm = total_tokens / duration_minutes
            time_score = min(100, tpm / TPM_BASELINE * 100)
        else:
            time_score = 100
    else:
        time_score = 100

    weights = {
        "output_quality": 0.30,
        "task_completion": 0.25,
        "compression_efficiency": 0.20,
        "budget_adherence": 0.15,
        "time_efficiency": 0.10,
    }
    scores = {
        "output_quality": quality_score,
        "task_completion": completion_score,
        "compression_efficiency": compression_score,
        "budget_adherence": budget_score,
        "time_efficiency": time_score,
    }
    tes = sum(scores[k] * weights[k] for k in weights)
    tes = round(min(100, max(0, tes)), 2)

    return {
        "tes": tes,
        "dimensions": {k: round(v, 2) for k, v in scores.items()},
        "weights": weights,
    }


def tes_grade(tes):
    if tes >= 90:
        return "A"
    elif tes >= 80:
        return "B"
    elif tes >= 70:
        return "C"
    elif tes >= 60:
        return "D"
    else:
        return "F"


def budget_gate_status(utilization_pct):
    if utilization_pct <= 80:
        return "normal"
    elif utilization_pct <= 95:
        return "warning"
    else:
        return "critical"


def ascii_bar(value, max_value, width=30):
    if max_value <= 0:
        return ""
    filled = int(value / max_value * width)
    filled = min(filled, width)
    return "█" * filled + "░" * (width - filled)


def render_text(task_metrics, agent_metrics, phase_metrics, system_metrics, tes_data, task_id, logs):
    lines = []
    lines.append("=" * 70)
    lines.append("  TOKEN CONSUMPTION MONITORING DASHBOARD")
    if task_id:
        lines.append(f"  Task Filter: {task_id}")
    lines.append("=" * 70)

    lines.append("")
    lines.append("── SYSTEM OVERVIEW ──")
    lines.append(f"  Total Tokens:        {system_metrics['total_tokens']:,}")
    lines.append(f"  Tokens In:           {system_metrics['total_tokens_in']:,}")
    lines.append(f"  Tokens Out:          {system_metrics['total_tokens_out']:,}")
    lines.append(f"  Compression Events:  {system_metrics['compression_events']}")
    lines.append(f"  Total Tasks:         {system_metrics['total_tasks']}")
    lines.append(f"  Token Budget:        {system_metrics['token_budget']:,}" if system_metrics['token_budget'] else "  Token Budget:        N/A")
    lines.append(f"  Budget Utilization:  {system_metrics['budget_utilization_pct']}%")

    lines.append("")
    lines.append("── PHASE DISTRIBUTION ──")
    if phase_metrics:
        max_phase_tokens = max(p["total_tokens"] for p in phase_metrics.values())
        sorted_phases = sorted(phase_metrics.items(), key=lambda x: x[1]["total_tokens"], reverse=True)
        for phase_name, pm in sorted_phases:
            bar = ascii_bar(pm["total_tokens"], max_phase_tokens, 25)
            dur = f"{pm['duration_seconds']:.0f}s" if pm["duration_seconds"] is not None else "N/A"
            lines.append(f"  {phase_name:<12} {bar} {pm['total_tokens']:>8,} tokens  ({dur})")
    else:
        lines.append("  No phase data available")

    lines.append("")
    lines.append("── TOP 5 AGENTS BY TOKEN CONSUMPTION ──")
    if agent_metrics:
        sorted_agents = sorted(agent_metrics.items(), key=lambda x: x[1]["total_tokens"], reverse=True)[:5]
        for rank, (aid, am) in enumerate(sorted_agents, 1):
            lines.append(f"  {rank}. {aid:<25} {am['total_tokens']:>8,} tokens  (avg {am['avg_tokens_per_invocation']:,.0f}/call, {am['invocations']} calls)")
    else:
        lines.append("  No agent data available")

    lines.append("")
    lines.append("── RECENT COMPRESSION EVENTS ──")
    comp_entries = []
    for l in sorted(
        [l for l in logs if l.get("compression_events", 0) > 0],
        key=lambda x: x.get("timestamp", ""),
        reverse=True,
    )[:5]:
        comp_entries.append(l)
    if comp_entries:
        for ce in comp_entries:
            ts = ce.get("timestamp", "N/A")
            tid = ce.get("task_id", "N/A")
            cev = ce.get("compression_events", 0)
            lines.append(f"  [{ts}] Task={tid} Events={cev}")
    else:
        lines.append("  No compression events recorded")

    lines.append("")
    lines.append("── TOKEN EFFICIENCY SCORE (TES) ──")
    tes = tes_data["tes"]
    grade = tes_grade(tes)
    dims = tes_data["dimensions"]
    weights = tes_data["weights"]
    lines.append(f"  TES: {tes:.2f} / 100  Grade: {grade}")
    lines.append(f"  ┌──────────────────────────┬──────────┬────────┬──────────┐")
    lines.append(f"  │ Dimension                │ Score    │ Weight │ Weighted │")
    lines.append(f"  ├──────────────────────────┼──────────┼────────┼──────────┤")
    dim_labels = {
        "output_quality": "Output Quality",
        "task_completion": "Task Completion",
        "compression_efficiency": "Compression Eff.",
        "budget_adherence": "Budget Adherence",
        "time_efficiency": "Time Efficiency",
    }
    for k in weights:
        label = dim_labels.get(k, k)
        weighted = round(dims[k] * weights[k], 2)
        lines.append(f"  │ {label:<24} │ {dims[k]:>6.2f}   │ {weights[k]:>5.0%} │ {weighted:>6.2f}   │")
    lines.append(f"  └──────────────────────────┴──────────┴────────┴──────────┘")

    lines.append("")
    lines.append("── BUDGET GATE STATUS ──")
    status = budget_gate_status(system_metrics["budget_utilization_pct"])
    status_icon = {"normal": "✅", "warning": "⚠️", "critical": "🔴"}.get(status, "?")
    lines.append(f"  Status: {status_icon} {status.upper()}")
    lines.append(f"  Utilization: {system_metrics['budget_utilization_pct']}%")
    if status == "normal":
        lines.append(f"  Within safe operating range (≤80%)")
    elif status == "warning":
        lines.append(f"  Approaching budget limit (80-95%)")
    else:
        lines.append(f"  Exceeding safe budget threshold (>95%)")

    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


def render_json(task_metrics, agent_metrics, phase_metrics, system_metrics, tes_data):
    return json.dumps({
        "task_metrics": task_metrics,
        "agent_metrics": agent_metrics,
        "phase_metrics": phase_metrics,
        "system_metrics": system_metrics,
        "tes": tes_data,
        "budget_gate": {
            "status": budget_gate_status(system_metrics["budget_utilization_pct"]),
            "utilization_pct": system_metrics["budget_utilization_pct"],
        },
    }, indent=2, ensure_ascii=False)


def main():
    args = parse_args()
    knowledge_dir = args.knowledge_dir

    if not os.path.isdir(knowledge_dir):
        print(f"Error: Knowledge directory not found: {knowledge_dir}", file=sys.stderr)
        sys.exit(1)

    logs = load_token_logs(knowledge_dir)
    checkpoints = load_checkpoints(knowledge_dir)

    filtered_logs = filter_logs(logs, args.task_id)

    task_m = compute_task_metrics(filtered_logs)
    agent_m = compute_agent_metrics(filtered_logs)
    phase_m = compute_phase_metrics(filtered_logs)
    system_m = compute_system_metrics(filtered_logs, checkpoints)
    tes_data = compute_tes(system_m, task_m, filtered_logs, checkpoints)

    if args.format == "json":
        print(render_json(task_m, agent_m, phase_m, system_m, tes_data))
    else:
        print(render_text(task_m, agent_m, phase_m, system_m, tes_data, args.task_id, filtered_logs))

    sys.exit(0)


if __name__ == "__main__":
    main()
