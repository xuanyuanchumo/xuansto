#!/usr/bin/env python3
"""
Review Aggregator - Aggregates review results from multiple sub-agents.
Deduplicates findings by file+line+issue_type, sorts by severity.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
}


def load_review_file(filepath: str) -> dict:
    path = Path(filepath)
    if not path.exists():
        return {"error": f"File not found: {filepath}", "findings": []}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON in {filepath}: {e}", "findings": []}


def extract_findings(review_data: dict, source_file: str) -> list:
    findings = review_data.get("findings", [])
    if not isinstance(findings, list):
        findings = []
    for finding in findings:
        finding["_source_file"] = source_file
        if "_agent" not in finding:
            finding["_agent"] = review_data.get("agent", "unknown")
    return findings


def make_dedup_key(finding: dict) -> str:
    file_path = finding.get("file", "")
    line = str(finding.get("line", ""))
    issue_type = finding.get("type", finding.get("category", ""))
    return f"{file_path}:{line}:{issue_type}"


def deduplicate_findings(all_findings: list) -> list:
    seen = {}
    for finding in all_findings:
        key = make_dedup_key(finding)
        if key not in seen:
            seen[key] = finding
        else:
            existing = seen[key]
            existing_sev = SEVERITY_ORDER.get(existing.get("severity", "").lower(), 99)
            new_sev = SEVERITY_ORDER.get(finding.get("severity", "").lower(), 99)
            if new_sev < existing_sev:
                seen[key] = finding
            elif new_sev == existing_sev:
                agents = existing.get("_agents", [existing.get("_agent", "unknown")])
                if isinstance(agents, str):
                    agents = [agents]
                new_agent = finding.get("_agent", "unknown")
                if new_agent not in agents:
                    agents.append(new_agent)
                existing["_agents"] = agents
    return list(seen.values())


def sort_by_severity(findings: list) -> list:
    return sorted(
        findings,
        key=lambda f: SEVERITY_ORDER.get(f.get("severity", "").lower(), 99),
    )


def compute_statistics(findings: list) -> dict:
    stats = {"critical": 0, "high": 0, "medium": 0, "low": 0, "total": len(findings)}
    for f in findings:
        sev = f.get("severity", "").lower()
        if sev in stats:
            stats[sev] += 1
    return stats


def parse_args():
    parser = argparse.ArgumentParser(
        description="Review Aggregator - Aggregate and deduplicate multi-agent review results"
    )
    parser.add_argument(
        "--reviews",
        type=str,
        nargs="+",
        required=True,
        help="Paths to JSON review result files from sub-agents",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    all_findings = []
    sources = []

    for review_path in args.reviews:
        review_data = load_review_file(review_path)
        if "error" in review_data:
            sources.append({
                "file": review_path,
                "status": "error",
                "error": review_data["error"],
            })
            continue
        findings = extract_findings(review_data, review_path)
        all_findings.extend(findings)
        sources.append({
            "file": review_path,
            "status": "loaded",
            "finding_count": len(findings),
            "agent": review_data.get("agent", "unknown"),
        })

    deduped = deduplicate_findings(all_findings)
    sorted_findings = sort_by_severity(deduped)
    stats = compute_statistics(sorted_findings)

    for f in sorted_findings:
        f.pop("_source_file", None)
        f.pop("_agent", None)
        f.pop("_agents", None)

    output = {
        "timestamp": datetime.now().isoformat(),
        "sources": sources,
        "statistics": stats,
        "findings": sorted_findings,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
