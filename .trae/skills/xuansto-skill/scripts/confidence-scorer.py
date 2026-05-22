#!/usr/bin/env python3
"""
Confidence Scorer - Multi-Agent Code Review confidence scoring script
Scores review findings on a 0-100 scale (5 levels: 0/25/50/75/100)
based on code context relevance, issue reproducibility, and rule match.
"""

import argparse
import json
import sys
from datetime import datetime


VALID_SCORES = [0, 25, 50, 75, 100]

SEVERITY_WEIGHTS = {
    "critical": 1.0,
    "high": 0.9,
    "medium": 0.7,
    "low": 0.5,
}


def compute_context_relevance(finding: dict) -> float:
    score = 0.0
    if finding.get("file") and finding.get("line"):
        score += 0.4
    elif finding.get("file"):
        score += 0.2
    if finding.get("code_snippet"):
        score += 0.3
    if finding.get("surrounding_context"):
        score += 0.3
    return min(score, 1.0)


def compute_reproducibility(finding: dict) -> float:
    score = 0.0
    if finding.get("steps_to_reproduce"):
        score += 0.4
    if finding.get("expected_behavior") and finding.get("actual_behavior"):
        score += 0.3
    if finding.get("test_case"):
        score += 0.3
    return min(score, 1.0)


def compute_rule_match(finding: dict) -> float:
    score = 0.0
    if finding.get("rule_id"):
        score += 0.3
    if finding.get("rule_source"):
        score += 0.2
    if finding.get("category"):
        score += 0.2
    severity = finding.get("severity", "").lower()
    if severity in SEVERITY_WEIGHTS:
        score += 0.3 * SEVERITY_WEIGHTS[severity]
    return min(score, 1.0)


def quantize_score(raw_score: float) -> int:
    best = VALID_SCORES[0]
    for s in VALID_SCORES:
        if abs(s - raw_score) < abs(best - raw_score):
            best = s
    return best


def score_finding(finding: dict) -> dict:
    context = compute_context_relevance(finding)
    reproducibility = compute_reproducibility(finding)
    rule_match = compute_rule_match(finding)

    raw_score = (context * 35 + reproducibility * 35 + rule_match * 30)
    score = quantize_score(raw_score)

    reasoning_parts = []
    reasoning_parts.append(f"context_relevance={context:.2f}")
    reasoning_parts.append(f"reproducibility={reproducibility:.2f}")
    reasoning_parts.append(f"rule_match={rule_match:.2f}")
    reasoning_parts.append(f"raw_score={raw_score:.2f}")

    if score >= 75:
        reasoning_parts.append("high_confidence")
    elif score >= 50:
        reasoning_parts.append("moderate_confidence")
    elif score >= 25:
        reasoning_parts.append("low_confidence")
    else:
        reasoning_parts.append("very_low_confidence")

    return {
        "id": finding.get("id", "unknown"),
        "score": score,
        "reasoning": "; ".join(reasoning_parts),
    }


def parse_args():
    parser = argparse.ArgumentParser(
        description="Confidence Scorer - Score review findings by confidence level"
    )
    parser.add_argument(
        "--findings",
        type=str,
        required=True,
        help="JSON string containing list of review findings",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=0,
        help="Minimum confidence threshold (0-100). Findings below this are filtered out.",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    try:
        findings = json.loads(args.findings)
    except json.JSONDecodeError as e:
        print(json.dumps({
            "error": f"Invalid JSON in --findings: {e}",
            "timestamp": datetime.now().isoformat(),
        }))
        sys.exit(1)

    if not isinstance(findings, list):
        print(json.dumps({
            "error": "--findings must be a JSON array of finding objects",
            "timestamp": datetime.now().isoformat(),
        }))
        sys.exit(1)

    scored = []
    for finding in findings:
        result = score_finding(finding)
        scored.append(result)

    if args.threshold > 0:
        filtered = [s for s in scored if s["score"] >= args.threshold]
    else:
        filtered = scored

    output = {
        "timestamp": datetime.now().isoformat(),
        "total_findings": len(findings),
        "scored_findings": len(scored),
        "filtered_findings": len(filtered),
        "threshold": args.threshold,
        "results": filtered,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
