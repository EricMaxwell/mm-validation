#!/usr/bin/env python3
"""Adjudicate an mm-validation verdict from a valid evidence manifest.

The script applies hard precedence only. It computes no model metrics and
creates no validation evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from validate_evidence_manifest import REQUIRED_GATES, load_manifest, validate_manifest


def adjudicate(data: dict[str, Any]) -> tuple[str, list[str]]:
    gates = data["gates"]
    claims = data["claims"]

    fail_reasons: list[str] = []
    inconclusive_reasons: list[str] = []
    limit_reasons: list[str] = []

    for gate_name in REQUIRED_GATES:
        gate = gates[gate_name]
        outcome = gate["outcome"]
        if outcome == "fail":
            fail_reasons.append(f"gate failed: {gate_name}")
        elif outcome == "inconclusive":
            inconclusive_reasons.append(f"gate inconclusive: {gate_name}")
        elif outcome == "pass_with_limits":
            limit_reasons.append(f"gate passed with limits: {gate_name}")
        for issue in gate["issues"]:
            severity = issue["severity"]
            reason = f"{severity} issue in {gate_name}: {issue['message']}"
            if severity == "high":
                fail_reasons.append(reason)
            else:
                limit_reasons.append(reason)

    for claim in claims:
        stability = claim["stability"]
        if stability == "unstable":
            fail_reasons.append(f"unstable claim: {claim['id']}")
        elif stability == "untested":
            inconclusive_reasons.append(f"untested claim: {claim['id']}")
        elif stability == "conditional":
            limit_reasons.append(f"conditional claim: {claim['id']}")

    for limitation in data["limitations"]:
        limit_reasons.append(f"material limitation: {limitation['id']}")

    if fail_reasons:
        return "fail", fail_reasons
    if inconclusive_reasons:
        return "inconclusive", inconclusive_reasons
    if limit_reasons:
        return "pass_with_limits", limit_reasons
    return "pass", ["all applicable gates passed with observed-supported evidence"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="manifest JSON path, or - for stdin")
    args = parser.parse_args(argv)
    try:
        data = load_manifest(args.manifest)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": "manifest_load_failed", "details": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2

    errors = validate_manifest(data)
    if errors:
        print(
            json.dumps(
                {"error": "invalid_manifest", "details": errors},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    verdict, reasons = adjudicate(data)
    declared = data.get("declared_verdict")
    matches_declared = declared is None or declared == verdict
    result = {
        "verdict": verdict,
        "reasons": reasons,
        "declared_verdict": declared,
        "matches_declared": matches_declared,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if matches_declared else 1


if __name__ == "__main__":
    raise SystemExit(main())
