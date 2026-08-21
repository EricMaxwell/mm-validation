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

from validate_evidence_manifest import (
    LATEST_SCHEMA_VERSION,
    REQUIRED_GATES,
    SCHEMA_VERSION,
    _validate_manifest_v1_0,
    load_manifest,
    validate_manifest_detailed,
)


def _adjudicate_v1_0(data: dict[str, Any]) -> tuple[str, list[str]]:
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


def adjudicate_v1_1(
    data: dict[str, Any],
    report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the v1.1 PASS/WARN/FAIL result with evidence diagnostics."""
    report = report or validate_manifest_detailed(data)
    gates = data.get("gates") if isinstance(data.get("gates"), dict) else {}
    limitations = data.get("limitations") if isinstance(data.get("limitations"), list) else []

    fail_reasons: list[str] = []
    warn_reasons: list[str] = []
    failed_checks: list[str] = []

    for finding in report.get("errors", []):
        code = finding.get("code", "VALIDATION_ERROR")
        message = finding.get("message", "validation error")
        fail_reasons.append(f"{code}: {message}")
        failed_checks.append(code)
    for finding in report.get("warnings", []):
        code = finding.get("code", "VALIDATION_WARNING")
        message = finding.get("message", "validation warning")
        warn_reasons.append(f"{code}: {message}")

    for gate_name in REQUIRED_GATES:
        gate = gates.get(gate_name)
        if not isinstance(gate, dict):
            continue
        outcome = gate.get("outcome")
        if outcome == "fail":
            fail_reasons.append(f"GATE_FAILED: {gate_name}")
            failed_checks.append(f"GATE_FAILED:{gate_name}")
        elif outcome in {"pass_with_limits", "inconclusive", "not_applicable"}:
            warn_reasons.append(f"GATE_NOT_FULL_PASS: {gate_name}={outcome}")
        issues = gate.get("issues") if isinstance(gate.get("issues"), list) else []
        for issue in issues:
            if not isinstance(issue, dict):
                continue
            severity = issue.get("severity")
            message = issue.get("message", "unresolved issue")
            if severity == "high":
                fail_reasons.append(f"HIGH_ISSUE: {gate_name}: {message}")
                failed_checks.append(f"HIGH_ISSUE:{gate_name}")
            elif severity in {"medium", "low"}:
                warn_reasons.append(f"{severity.upper()}_ISSUE: {gate_name}: {message}")

    for limitation in limitations:
        if isinstance(limitation, dict):
            warn_reasons.append(
                f"MATERIAL_LIMITATION: {limitation.get('id', '<unknown>')}"
            )

    if fail_reasons:
        verdict = "FAIL"
        reasons = fail_reasons
        legacy_verdict = "fail"
    elif warn_reasons:
        verdict = "WARN"
        reasons = warn_reasons
        has_inconclusive_gate = any(
            isinstance(gates.get(name), dict)
            and gates[name].get("outcome") == "inconclusive"
            for name in REQUIRED_GATES
        )
        legacy_verdict = "inconclusive" if has_inconclusive_gate else "pass_with_limits"
    else:
        verdict = "PASS"
        reasons = ["all core claims are supported and all validation checks passed"]
        legacy_verdict = "pass"

    return {
        "schema_version": LATEST_SCHEMA_VERSION,
        "verdict": verdict,
        "legacy_verdict": legacy_verdict,
        "reasons": reasons,
        "failed_checks": list(dict.fromkeys(failed_checks)),
        "evidence_summary": report.get("evidence_summary", {}),
        "claim_assessments": report.get("claim_assessments", {}),
    }


def adjudicate(data: dict[str, Any]) -> tuple[str, list[str]]:
    """Backward-compatible tuple API, dispatched by schema_version."""
    if data.get("schema_version") == SCHEMA_VERSION:
        return _adjudicate_v1_0(data)
    result = adjudicate_v1_1(data)
    return result["verdict"], result["reasons"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="manifest JSON path, or - for stdin")
    args = parser.parse_args(argv)
    try:
        data = load_manifest(args.manifest)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": "manifest_load_failed", "details": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2

    if data.get("schema_version") == SCHEMA_VERSION:
        errors = _validate_manifest_v1_0(data)
        if errors:
            print(
                json.dumps(
                    {"error": "invalid_manifest", "details": errors},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 2
        verdict, reasons = _adjudicate_v1_0(data)
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

    report = validate_manifest_detailed(data)
    result = adjudicate_v1_1(data, report)
    declared = data.get("declared_verdict")
    matches_declared = declared is None or declared == result["verdict"]
    result["declared_verdict"] = declared
    result["matches_declared"] = matches_declared
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not matches_declared or result["verdict"] == "FAIL":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
