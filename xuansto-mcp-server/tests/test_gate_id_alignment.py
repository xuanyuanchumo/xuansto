from __future__ import annotations

import pytest

from xuansto_mcp.tools.quality_gate_check import (
    DECLARED_GATE_IDS,
    INLINE_CHECKS,
)
from xuansto_mcp.core.config import QUALITY_GATES_PHASE_MAP


DECLARED_SET = set(DECLARED_GATE_IDS)


def test_inline_checks_subset_of_declared():
    inline_keys = set(INLINE_CHECKS.keys())
    missing = inline_keys - DECLARED_SET
    assert not missing, (
        f"INLINE_CHECKS keys not in DECLARED_GATE_IDS: {sorted(missing)}"
    )


def test_declared_has_inline_or_none():
    for gate_id in DECLARED_GATE_IDS:
        assert gate_id in INLINE_CHECKS, (
            f"DECLARED_GATE_IDS entry '{gate_id}' missing from INLINE_CHECKS"
        )


def test_design_review_split_complete():
    for suffix in ("PRODUCT", "TECH", "DESIGN"):
        gate_id = f"DESIGN-REVIEW-{suffix}"
        assert gate_id in DECLARED_SET, (
            f"'{gate_id}' missing from DECLARED_GATE_IDS"
        )
        assert gate_id in INLINE_CHECKS, (
            f"'{gate_id}' missing from INLINE_CHECKS"
        )
        assert INLINE_CHECKS[gate_id] is not None, (
            f"'{gate_id}' has None function in INLINE_CHECKS, expected a callable"
        )
        assert callable(INLINE_CHECKS[gate_id]), (
            f"'{gate_id}' value is not callable"
        )


def test_phase_map_uses_valid_ids():
    all_phase_ids: list[str] = []
    for phase, ids in QUALITY_GATES_PHASE_MAP.items():
        all_phase_ids.extend(ids)
    invalid = set(all_phase_ids) - DECLARED_SET
    assert not invalid, (
        f"QUALITY_GATES_PHASE_MAP references IDs not in DECLARED_GATE_IDS: {sorted(invalid)}"
    )


def test_no_orphan_design_review():
    assert "DESIGN-REVIEW" not in INLINE_CHECKS, (
        "Old 'DESIGN-REVIEW' key still exists in INLINE_CHECKS; "
        "should be replaced by DESIGN-REVIEW-PRODUCT/TECH/DESIGN"
    )
    assert "DESIGN-REVIEW" not in DECLARED_SET, (
        "Old 'DESIGN-REVIEW' key still exists in DECLARED_GATE_IDS; "
        "should be replaced by DESIGN-REVIEW-PRODUCT/TECH/DESIGN"
    )
