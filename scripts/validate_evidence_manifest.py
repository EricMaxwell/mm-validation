#!/usr/bin/env python3
"""Validate an mm-validation evidence manifest using only the standard library.

This checks declared structure, evidence states, provenance links, and gate
consistency. It does not inspect model artifacts or certify scientific validity.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
EVIDENCE_STATUSES = {
    "observed",
    "derived",
    "reported",
    "not_run",
    "unavailable",
    "not_applicable",
}
MODEL_FAMILIES = {
    "prediction",
    "regression",
    "classification",
    "optimization",
    "ranking",
    "simulation",
    "hybrid",
}
CLAIM_STABILITIES = {"stable", "conditional", "unstable", "untested"}
GATE_OUTCOMES = {
    "pass",
    "pass_with_limits",
    "inconclusive",
    "fail",
    "not_applicable",
}
VERDICTS = {"pass", "pass_with_limits", "inconclusive", "fail"}
SEVERITIES = {"high", "medium", "low"}
REQUIRED_GATES = (
    "implementation_correctness",
    "baseline_comparison",
    "model_specific_diagnostics",
    "sensitivity_analysis",
    "robustness_analysis",
    "conclusion_stability",
)


def _nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load_manifest(source: str) -> dict[str, Any]:
    if source == "-":
        raw = sys.stdin.read()
    else:
        raw = Path(source).read_text(encoding="utf-8")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("manifest root must be a JSON object")
    return data


def _support_map(evidence_by_id: dict[str, dict[str, Any]]) -> dict[str, bool]:
    memo: dict[str, bool] = {}
    active: set[str] = set()

    def supports(evidence_id: str) -> bool:
        if evidence_id in memo:
            return memo[evidence_id]
        if evidence_id in active:
            memo[evidence_id] = False
            return False
        item = evidence_by_id.get(evidence_id)
        if item is None:
            return False
        status = item.get("status")
        if status == "observed":
            memo[evidence_id] = True
            return True
        if status != "derived":
            memo[evidence_id] = False
            return False
        parents = item.get("derived_from")
        if not isinstance(parents, list) or not parents:
            memo[evidence_id] = False
            return False
        active.add(evidence_id)
        result = all(isinstance(parent, str) and supports(parent) for parent in parents)
        active.remove(evidence_id)
        memo[evidence_id] = result
        return result

    for item_id in evidence_by_id:
        supports(item_id)
    return memo


def validate_manifest(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if data.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION!r}")
    if not _nonempty_string(data.get("validation_id")):
        errors.append("validation_id must be a non-empty string")

    model = data.get("model")
    if not isinstance(model, dict):
        errors.append("model must be an object")
    else:
        if model.get("family") not in MODEL_FAMILIES:
            errors.append("model.family is invalid")
        if not _nonempty_string(model.get("name")):
            errors.append("model.name must be a non-empty string")
        artifacts = model.get("artifacts")
        if not isinstance(artifacts, list) or not all(_nonempty_string(x) for x in artifacts):
            errors.append("model.artifacts must be a list of non-empty strings")

    claims = data.get("claims")
    claim_ids: set[str] = set()
    claim_stabilities: list[str] = []
    if not isinstance(claims, list) or not claims:
        errors.append("claims must be a non-empty list")
    else:
        for index, claim in enumerate(claims):
            prefix = f"claims[{index}]"
            if not isinstance(claim, dict):
                errors.append(f"{prefix} must be an object")
                continue
            claim_id = claim.get("id")
            if not _nonempty_string(claim_id):
                errors.append(f"{prefix}.id must be a non-empty string")
            elif claim_id in claim_ids:
                errors.append(f"{prefix}.id duplicates {claim_id!r}")
            else:
                claim_ids.add(claim_id)
            if not _nonempty_string(claim.get("statement")):
                errors.append(f"{prefix}.statement must be a non-empty string")
            stability = claim.get("stability")
            if stability not in CLAIM_STABILITIES:
                errors.append(f"{prefix}.stability is invalid")
            else:
                claim_stabilities.append(stability)

    evidence = data.get("evidence")
    evidence_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(evidence, list):
        errors.append("evidence must be a list")
        evidence = []
    for index, item in enumerate(evidence):
        prefix = f"evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be an object")
            continue
        evidence_id = item.get("id")
        if not _nonempty_string(evidence_id):
            errors.append(f"{prefix}.id must be a non-empty string")
        elif evidence_id in evidence_by_id:
            errors.append(f"{prefix}.id duplicates {evidence_id!r}")
        else:
            evidence_by_id[evidence_id] = item
        status = item.get("status")
        if status not in EVIDENCE_STATUSES:
            errors.append(f"{prefix}.status is invalid")
            continue
        if not _nonempty_string(item.get("description")):
            errors.append(f"{prefix}.description must be a non-empty string")
        artifact_path = item.get("artifact_path")
        command = item.get("command")
        run_id = item.get("run_id")
        source = item.get("source")
        reason = item.get("reason")
        derived_from = item.get("derived_from", [])
        metadata = item.get("metadata", {})
        if not isinstance(derived_from, list) or not all(_nonempty_string(x) for x in derived_from):
            errors.append(f"{prefix}.derived_from must be a list of non-empty strings")
            derived_from = []
        if not isinstance(metadata, dict):
            errors.append(f"{prefix}.metadata must be an object when present")
        if status == "observed" and not (
            _nonempty_string(artifact_path)
            or (_nonempty_string(command) and _nonempty_string(run_id))
        ):
            errors.append(
                f"{prefix} observed evidence requires artifact_path or both command and run_id"
            )
        if status == "derived" and not derived_from:
            errors.append(f"{prefix} derived evidence requires derived_from")
        if status == "reported" and not _nonempty_string(source):
            errors.append(f"{prefix} reported evidence requires source")
        if status in {"not_run", "unavailable", "not_applicable"} and not _nonempty_string(reason):
            errors.append(f"{prefix} {status} evidence requires reason")

    for evidence_id, item in evidence_by_id.items():
        parents = item.get("derived_from", [])
        if not isinstance(parents, list):
            continue
        for parent in parents:
            if parent == evidence_id:
                errors.append(f"evidence {evidence_id!r} cannot derive from itself")
            elif parent not in evidence_by_id:
                errors.append(f"evidence {evidence_id!r} references unknown evidence {parent!r}")

    support_map = _support_map(evidence_by_id)
    for evidence_id, item in evidence_by_id.items():
        if item.get("status") == "derived" and not support_map.get(evidence_id, False):
            errors.append(
                f"derived evidence {evidence_id!r} must trace exclusively to observed evidence"
            )

    limitations = data.get("limitations")
    if not isinstance(limitations, list):
        errors.append("limitations must be a list")
        limitations = []
    limitation_ids: set[str] = set()
    for index, limitation in enumerate(limitations):
        prefix = f"limitations[{index}]"
        if not isinstance(limitation, dict):
            errors.append(f"{prefix} must be an object")
            continue
        limitation_id = limitation.get("id")
        if not _nonempty_string(limitation_id):
            errors.append(f"{prefix}.id must be a non-empty string")
        elif limitation_id in limitation_ids:
            errors.append(f"{prefix}.id duplicates {limitation_id!r}")
        else:
            limitation_ids.add(limitation_id)
        if not _nonempty_string(limitation.get("description")):
            errors.append(f"{prefix}.description must be a non-empty string")
        affects = limitation.get("affects_claims")
        if not isinstance(affects, list) or not all(_nonempty_string(x) for x in affects):
            errors.append(f"{prefix}.affects_claims must be a list of claim IDs")
        else:
            for claim_id in affects:
                if claim_id not in claim_ids:
                    errors.append(f"{prefix} references unknown claim {claim_id!r}")

    gates = data.get("gates")
    gate_records: dict[str, dict[str, Any]] = {}
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
        gates = {}
    missing_gates = [name for name in REQUIRED_GATES if name not in gates]
    extra_gates = [name for name in gates if name not in REQUIRED_GATES]
    if missing_gates:
        errors.append(f"gates missing required keys: {', '.join(missing_gates)}")
    if extra_gates:
        errors.append(f"gates contains unknown keys: {', '.join(extra_gates)}")

    for gate_name in REQUIRED_GATES:
        gate = gates.get(gate_name)
        prefix = f"gates.{gate_name}"
        if not isinstance(gate, dict):
            if gate_name in gates:
                errors.append(f"{prefix} must be an object")
            continue
        gate_records[gate_name] = gate
        outcome = gate.get("outcome")
        if outcome not in GATE_OUTCOMES:
            errors.append(f"{prefix}.outcome is invalid")
        if not _nonempty_string(gate.get("criterion")):
            errors.append(f"{prefix}.criterion must be a non-empty string")
        if not _nonempty_string(gate.get("summary")):
            errors.append(f"{prefix}.summary must be a non-empty string")
        evidence_ids = gate.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not all(_nonempty_string(x) for x in evidence_ids):
            errors.append(f"{prefix}.evidence_ids must be a list of evidence IDs")
            evidence_ids = []
        for evidence_id in evidence_ids:
            if evidence_id not in evidence_by_id:
                errors.append(f"{prefix} references unknown evidence {evidence_id!r}")
        if outcome in {"pass", "pass_with_limits"} and not any(
            support_map.get(evidence_id, False) for evidence_id in evidence_ids
        ):
            errors.append(f"{prefix} passing outcome lacks observed-supported evidence")
        if outcome == "not_applicable":
            if gate_name != "baseline_comparison":
                errors.append(f"{prefix} cannot be not_applicable")
            if not _nonempty_string(gate.get("not_applicable_reason")):
                errors.append(f"{prefix}.not_applicable_reason is required")
        issues = gate.get("issues")
        if not isinstance(issues, list):
            errors.append(f"{prefix}.issues must be a list")
            issues = []
        if outcome == "fail" and not issues:
            errors.append(f"{prefix} failed outcome requires at least one issue")
        for index, issue in enumerate(issues):
            issue_prefix = f"{prefix}.issues[{index}]"
            if not isinstance(issue, dict):
                errors.append(f"{issue_prefix} must be an object")
                continue
            if issue.get("severity") not in SEVERITIES:
                errors.append(f"{issue_prefix}.severity is invalid")
            if not _nonempty_string(issue.get("message")):
                errors.append(f"{issue_prefix}.message must be a non-empty string")
            issue_evidence = issue.get("evidence_ids")
            if not isinstance(issue_evidence, list) or not all(
                _nonempty_string(x) for x in issue_evidence
            ):
                errors.append(f"{issue_prefix}.evidence_ids must be a list")
            else:
                for evidence_id in issue_evidence:
                    if evidence_id not in evidence_by_id:
                        errors.append(
                            f"{issue_prefix} references unknown evidence {evidence_id!r}"
                        )

    conclusion = gate_records.get("conclusion_stability")
    if conclusion and claim_stabilities:
        expected = "pass"
        if "unstable" in claim_stabilities:
            expected = "fail"
        elif "untested" in claim_stabilities:
            expected = "inconclusive"
        elif "conditional" in claim_stabilities:
            expected = "pass_with_limits"
        if conclusion.get("outcome") != expected:
            errors.append(
                "gates.conclusion_stability.outcome must agree with claim stability "
                f"(expected {expected!r})"
            )

    declared = data.get("declared_verdict")
    if declared is not None and declared not in VERDICTS:
        errors.append("declared_verdict is invalid")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="manifest JSON path, or - for stdin")
    args = parser.parse_args(argv)
    try:
        data = load_manifest(args.manifest)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    errors = validate_manifest(data)
    print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
