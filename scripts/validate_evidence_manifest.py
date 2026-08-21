#!/usr/bin/env python3
"""Validate an mm-validation evidence manifest using only the standard library.

This checks declared structure, evidence states, provenance links, and gate
consistency. It does not inspect model artifacts or certify scientific validity.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "1.0"
LATEST_SCHEMA_VERSION = "1.1"
SUPPORTED_SCHEMA_VERSIONS = {SCHEMA_VERSION, LATEST_SCHEMA_VERSION}
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
EVIDENCE_TYPES = {"observed", "derived", "assumed"}
EVIDENCE_STANCES = {"supports", "contradicts", "neutral"}
CONFIDENCE_LEVELS = {"high", "medium", "low"}
EVIDENCE_LIFECYCLE = {"active", "superseded", "invalidated"}
V1_1_VERDICTS = {"PASS", "WARN", "FAIL"}
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


def _validate_manifest_v1_0(data: dict[str, Any]) -> list[str]:
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


def _finding(
    code: str,
    message: str,
    path: str | None = None,
    **context: Any,
) -> dict[str, Any]:
    item: dict[str, Any] = {"code": code, "message": message}
    if path is not None:
        item["path"] = path
    item.update(context)
    return item


def _timestamp_has_timezone(value: Any) -> bool:
    if not _nonempty_string(value):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def _v1_1_evidence_summary(
    evidence: list[dict[str, Any]],
    report: dict[str, Any],
) -> dict[str, Any]:
    by_type = {name: 0 for name in sorted(EVIDENCE_TYPES)}
    by_confidence = {name: 0 for name in sorted(CONFIDENCE_LEVELS)}
    active = 0
    supporting = 0
    contradicting = 0
    provenance_complete = 0
    for item in evidence:
        if not isinstance(item, dict):
            continue
        evidence_type = item.get("type")
        confidence = item.get("confidence")
        lifecycle = item.get("lifecycle_status", "active")
        if evidence_type in by_type:
            by_type[evidence_type] += 1
        if confidence in by_confidence:
            by_confidence[confidence] += 1
        if lifecycle == "active":
            active += 1
            if item.get("stance") == "supports":
                supporting += 1
            elif item.get("stance") == "contradicts":
                contradicting += 1
        provenance = item.get("provenance")
        if isinstance(provenance, dict):
            responsible = provenance.get("responsible_party")
            responsibility_ok = _nonempty_string(responsible) or _nonempty_string(
                provenance.get("responsibility_not_applicable_reason")
            )
            if (
                _nonempty_string(provenance.get("origin"))
                and _nonempty_string(provenance.get("generation_method"))
                and _timestamp_has_timezone(provenance.get("timestamp"))
                and responsibility_ok
            ):
                provenance_complete += 1
    return {
        "total": len(evidence),
        "active": active,
        "by_type": by_type,
        "by_confidence": by_confidence,
        "supporting": supporting,
        "contradicting": contradicting,
        "provenance_complete": provenance_complete,
        "missing_core_claims": len(report["missing_evidence"]),
        "unsupported_core_claims": len(report["unsupported_claims"]),
        "orphan_evidence": len(report["orphan_evidence"]),
        "contradictions": len(report["contradictions"]),
    }


def _validate_manifest_v1_1(data: dict[str, Any]) -> dict[str, Any]:
    report: dict[str, Any] = {
        "schema_version": LATEST_SCHEMA_VERSION,
        "valid": False,
        "errors": [],
        "warnings": [],
        "missing_evidence": [],
        "orphan_evidence": [],
        "unsupported_claims": [],
        "contradictions": [],
        "claim_assessments": {},
        "evidence_summary": {},
    }
    errors: list[dict[str, Any]] = report["errors"]
    warnings: list[dict[str, Any]] = report["warnings"]

    allowed_top = {
        "schema_version",
        "validation_id",
        "model",
        "claims",
        "evidence",
        "gates",
        "limitations",
        "declared_verdict",
        "metadata",
    }
    for key in data:
        if key not in allowed_top:
            errors.append(_finding("UNKNOWN_FIELD", f"unknown top-level field {key!r}", key))

    if data.get("schema_version") != LATEST_SCHEMA_VERSION:
        errors.append(
            _finding(
                "INVALID_SCHEMA_VERSION",
                f"schema_version must be {LATEST_SCHEMA_VERSION!r}",
                "schema_version",
            )
        )
    if not _nonempty_string(data.get("validation_id")):
        errors.append(
            _finding(
                "MISSING_FIELD",
                "validation_id must be a non-empty string",
                "validation_id",
            )
        )

    model = data.get("model")
    if not isinstance(model, dict):
        errors.append(_finding("INVALID_TYPE", "model must be an object", "model"))
    else:
        if model.get("family") not in MODEL_FAMILIES:
            errors.append(_finding("INVALID_ENUM", "model.family is invalid", "model.family"))
        if not _nonempty_string(model.get("name")):
            errors.append(
                _finding("MISSING_FIELD", "model.name must be a non-empty string", "model.name")
            )
        artifacts = model.get("artifacts")
        if (
            not isinstance(artifacts, list)
            or not artifacts
            or not all(_nonempty_string(value) for value in artifacts)
        ):
            errors.append(
                _finding(
                    "MISSING_MODEL_ARTIFACT",
                    "model.artifacts must be a non-empty list of artifact identifiers",
                    "model.artifacts",
                )
            )

    claims = data.get("claims")
    claim_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(claims, list) or not claims:
        errors.append(_finding("MISSING_FIELD", "claims must be a non-empty list", "claims"))
        claims = []
    for index, claim in enumerate(claims):
        path = f"claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(_finding("INVALID_TYPE", "claim must be an object", path))
            continue
        claim_id = claim.get("id")
        if not _nonempty_string(claim_id):
            errors.append(_finding("MISSING_FIELD", "claim.id is required", f"{path}.id"))
            continue
        if claim_id in claim_by_id:
            errors.append(
                _finding("DUPLICATE_ID", f"duplicate claim id {claim_id!r}", f"{path}.id")
            )
            continue
        claim_by_id[claim_id] = claim
        if not _nonempty_string(claim.get("statement")):
            errors.append(
                _finding("MISSING_FIELD", "claim.statement is required", f"{path}.statement")
            )
        if not isinstance(claim.get("core"), bool):
            errors.append(
                _finding("INVALID_TYPE", "claim.core must be boolean", f"{path}.core")
            )
        evidence_ids = claim.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not all(
            _nonempty_string(value) for value in evidence_ids
        ):
            errors.append(
                _finding(
                    "INVALID_TYPE",
                    "claim.evidence_ids must be a list of evidence IDs",
                    f"{path}.evidence_ids",
                )
            )
        elif len(evidence_ids) != len(set(evidence_ids)):
            errors.append(
                _finding(
                    "DUPLICATE_REFERENCE",
                    "claim.evidence_ids contains duplicates",
                    f"{path}.evidence_ids",
                )
            )
        if "requires_comparator" in claim and not isinstance(
            claim.get("requires_comparator"), bool
        ):
            errors.append(
                _finding(
                    "INVALID_TYPE",
                    "claim.requires_comparator must be boolean",
                    f"{path}.requires_comparator",
                )
            )

    evidence = data.get("evidence")
    evidence_by_id: dict[str, dict[str, Any]] = {}
    evidence_path_by_id: dict[str, str] = {}
    if not isinstance(evidence, list):
        errors.append(_finding("INVALID_TYPE", "evidence must be a list", "evidence"))
        evidence = []
    for index, item in enumerate(evidence):
        path = f"evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(_finding("INVALID_TYPE", "evidence item must be an object", path))
            continue
        evidence_id = item.get("id")
        if not _nonempty_string(evidence_id):
            errors.append(_finding("MISSING_FIELD", "evidence.id is required", f"{path}.id"))
            continue
        if evidence_id in evidence_by_id:
            errors.append(
                _finding("DUPLICATE_ID", f"duplicate evidence id {evidence_id!r}", f"{path}.id")
            )
            continue
        evidence_by_id[evidence_id] = item
        evidence_path_by_id[evidence_id] = path
        claim_id = item.get("claim_id")
        if not _nonempty_string(claim_id):
            errors.append(
                _finding("MISSING_FIELD", "evidence.claim_id is required", f"{path}.claim_id")
            )
        elif claim_id not in claim_by_id:
            finding = _finding(
                "ORPHAN_EVIDENCE",
                f"evidence {evidence_id!r} references unknown claim {claim_id!r}",
                f"{path}.claim_id",
                evidence_id=evidence_id,
                claim_id=claim_id,
            )
            errors.append(finding)
            report["orphan_evidence"].append(finding)
        if item.get("type") not in EVIDENCE_TYPES:
            errors.append(_finding("INVALID_ENUM", "evidence.type is invalid", f"{path}.type"))
        if not _nonempty_string(item.get("source")):
            errors.append(
                _finding("MISSING_FIELD", "evidence.source is required", f"{path}.source")
            )
        if not _nonempty_string(item.get("description")):
            errors.append(
                _finding(
                    "MISSING_FIELD",
                    "evidence.description is required",
                    f"{path}.description",
                )
            )
        if item.get("confidence") not in CONFIDENCE_LEVELS:
            errors.append(
                _finding("INVALID_ENUM", "evidence.confidence is invalid", f"{path}.confidence")
            )
        if item.get("stance") not in EVIDENCE_STANCES:
            errors.append(
                _finding("INVALID_ENUM", "evidence.stance is invalid", f"{path}.stance")
            )
        lifecycle = item.get("lifecycle_status", "active")
        if lifecycle not in EVIDENCE_LIFECYCLE:
            errors.append(
                _finding(
                    "INVALID_ENUM",
                    "evidence.lifecycle_status is invalid",
                    f"{path}.lifecycle_status",
                )
            )
        gate_ids = item.get("gate_ids")
        if (
            not isinstance(gate_ids, list)
            or not gate_ids
            or not all(_nonempty_string(value) for value in gate_ids)
        ):
            errors.append(
                _finding(
                    "MISSING_GATE_MAPPING",
                    "evidence.gate_ids must be a non-empty list",
                    f"{path}.gate_ids",
                )
            )
            gate_ids = []
        elif len(gate_ids) != len(set(gate_ids)):
            errors.append(
                _finding(
                    "DUPLICATE_REFERENCE",
                    "evidence.gate_ids contains duplicates",
                    f"{path}.gate_ids",
                )
            )
        for gate_id in gate_ids:
            if gate_id not in REQUIRED_GATES:
                errors.append(
                    _finding(
                        "UNKNOWN_GATE",
                        f"evidence references unknown gate {gate_id!r}",
                        f"{path}.gate_ids",
                    )
                )
        derived_from = item.get("derived_from", [])
        if not isinstance(derived_from, list) or not all(
            _nonempty_string(value) for value in derived_from
        ):
            errors.append(
                _finding(
                    "INVALID_TYPE",
                    "evidence.derived_from must be a list",
                    f"{path}.derived_from",
                )
            )
            derived_from = []
        elif len(derived_from) != len(set(derived_from)):
            errors.append(
                _finding(
                    "DUPLICATE_REFERENCE",
                    "evidence.derived_from contains duplicates",
                    f"{path}.derived_from",
                )
            )
        if item.get("type") == "derived" and not derived_from:
            errors.append(
                _finding(
                    "MISSING_DERIVATION_INPUT",
                    "derived evidence requires derived_from",
                    f"{path}.derived_from",
                )
            )
        if item.get("type") != "derived" and derived_from:
            errors.append(
                _finding(
                    "INVALID_DERIVATION_INPUT",
                    "only derived evidence may declare derived_from",
                    f"{path}.derived_from",
                )
            )
        provenance = item.get("provenance")
        provenance_errors: list[str] = []
        if not isinstance(provenance, dict):
            provenance_errors.append("provenance must be an object")
        else:
            if not _nonempty_string(provenance.get("origin")):
                provenance_errors.append("origin is required")
            if not _nonempty_string(provenance.get("generation_method")):
                provenance_errors.append("generation_method is required")
            if not _timestamp_has_timezone(provenance.get("timestamp")):
                provenance_errors.append("timestamp must be ISO 8601 with a timezone")
            if not (
                _nonempty_string(provenance.get("responsible_party"))
                or _nonempty_string(provenance.get("responsibility_not_applicable_reason"))
            ):
                provenance_errors.append(
                    "responsible_party or responsibility_not_applicable_reason is required"
                )
        if provenance_errors:
            errors.append(
                _finding(
                    "INVALID_PROVENANCE",
                    "; ".join(provenance_errors),
                    f"{path}.provenance",
                    evidence_id=evidence_id,
                )
            )

    for evidence_id, item in evidence_by_id.items():
        path = evidence_path_by_id[evidence_id]
        for parent_id in item.get("derived_from", []):
            if parent_id == evidence_id:
                errors.append(
                    _finding(
                        "EVIDENCE_CYCLE",
                        "evidence cannot derive from itself",
                        f"{path}.derived_from",
                        evidence_id=evidence_id,
                    )
                )
            elif parent_id not in evidence_by_id:
                errors.append(
                    _finding(
                        "UNKNOWN_EVIDENCE",
                        f"derived evidence references unknown evidence {parent_id!r}",
                        f"{path}.derived_from",
                    )
                )

    lineage_memo: dict[str, tuple[bool, bool, bool]] = {}
    lineage_active: set[str] = set()

    def lineage(evidence_id: str) -> tuple[bool, bool, bool]:
        """Return (valid, has_observed, has_assumed) for active provenance ancestry."""
        if evidence_id in lineage_memo:
            return lineage_memo[evidence_id]
        if evidence_id in lineage_active:
            return False, False, False
        item = evidence_by_id.get(evidence_id)
        if item is None:
            return False, False, False
        evidence_type = item.get("type")
        if evidence_type == "observed":
            result = (True, True, False)
        elif evidence_type == "assumed":
            result = (True, False, True)
        elif evidence_type == "derived":
            parents = item.get("derived_from", [])
            if not parents:
                result = (False, False, False)
            else:
                lineage_active.add(evidence_id)
                parent_results = [lineage(parent_id) for parent_id in parents]
                lineage_active.remove(evidence_id)
                result = (
                    all(parent[0] for parent in parent_results),
                    any(parent[1] for parent in parent_results),
                    any(parent[2] for parent in parent_results),
                )
        else:
            result = (False, False, False)
        lineage_memo[evidence_id] = result
        return result

    for evidence_id, item in evidence_by_id.items():
        if item.get("type") == "derived":
            valid_lineage, has_observed, _ = lineage(evidence_id)
            if not valid_lineage:
                errors.append(
                    _finding(
                        "INVALID_DERIVATION_LINEAGE",
                        "derived evidence has an invalid or cyclic lineage",
                        f"{evidence_path_by_id[evidence_id]}.derived_from",
                        evidence_id=evidence_id,
                    )
                )
            elif not has_observed:
                warnings.append(
                    _finding(
                        "ASSUMPTION_ONLY_DERIVATION",
                        "derived evidence has no observed ancestor",
                        f"{evidence_path_by_id[evidence_id]}.derived_from",
                        evidence_id=evidence_id,
                    )
                )

    for claim_id, claim in claim_by_id.items():
        evidence_ids = claim.get("evidence_ids", [])
        if not isinstance(evidence_ids, list):
            continue
        for evidence_id in evidence_ids:
            item = evidence_by_id.get(evidence_id)
            if item is None:
                errors.append(
                    _finding(
                        "UNKNOWN_EVIDENCE",
                        f"claim references unknown evidence {evidence_id!r}",
                        f"claims.{claim_id}.evidence_ids",
                        claim_id=claim_id,
                    )
                )
            elif item.get("claim_id") != claim_id:
                errors.append(
                    _finding(
                        "CLAIM_EVIDENCE_MISMATCH",
                        f"evidence {evidence_id!r} maps to claim {item.get('claim_id')!r}",
                        f"claims.{claim_id}.evidence_ids",
                        claim_id=claim_id,
                        evidence_id=evidence_id,
                    )
                )

    for evidence_id, item in evidence_by_id.items():
        claim_id = item.get("claim_id")
        claim = claim_by_id.get(claim_id)
        if claim is None:
            continue
        claim_evidence = claim.get("evidence_ids", [])
        if isinstance(claim_evidence, list) and evidence_id not in claim_evidence:
            finding = _finding(
                "ORPHAN_EVIDENCE",
                f"evidence {evidence_id!r} is not listed by claim {claim_id!r}",
                f"{evidence_path_by_id[evidence_id]}.claim_id",
                evidence_id=evidence_id,
                claim_id=claim_id,
            )
            errors.append(finding)
            report["orphan_evidence"].append(finding)

    gates = data.get("gates")
    gate_by_id: dict[str, dict[str, Any]] = {}
    if not isinstance(gates, dict):
        errors.append(_finding("INVALID_TYPE", "gates must be an object", "gates"))
        gates = {}
    missing_gates = [name for name in REQUIRED_GATES if name not in gates]
    extra_gates = [name for name in gates if name not in REQUIRED_GATES]
    if missing_gates:
        errors.append(
            _finding(
                "MISSING_GATE",
                f"missing required gates: {', '.join(missing_gates)}",
                "gates",
            )
        )
    if extra_gates:
        errors.append(
            _finding(
                "UNKNOWN_GATE",
                f"unknown gates: {', '.join(extra_gates)}",
                "gates",
            )
        )
    for gate_name in REQUIRED_GATES:
        gate = gates.get(gate_name)
        path = f"gates.{gate_name}"
        if not isinstance(gate, dict):
            if gate_name in gates:
                errors.append(_finding("INVALID_TYPE", "gate must be an object", path))
            continue
        gate_by_id[gate_name] = gate
        outcome = gate.get("outcome")
        if outcome not in GATE_OUTCOMES:
            errors.append(_finding("INVALID_ENUM", "gate outcome is invalid", f"{path}.outcome"))
        if not _nonempty_string(gate.get("criterion")):
            errors.append(
                _finding("MISSING_FIELD", "gate criterion is required", f"{path}.criterion")
            )
        if not _nonempty_string(gate.get("summary")):
            errors.append(_finding("MISSING_FIELD", "gate summary is required", f"{path}.summary"))
        evidence_ids = gate.get("evidence_ids")
        if not isinstance(evidence_ids, list) or not all(
            _nonempty_string(value) for value in evidence_ids
        ):
            errors.append(
                _finding(
                    "INVALID_TYPE",
                    "gate.evidence_ids must be a list",
                    f"{path}.evidence_ids",
                )
            )
            evidence_ids = []
        elif len(evidence_ids) != len(set(evidence_ids)):
            errors.append(
                _finding(
                    "DUPLICATE_REFERENCE",
                    "gate.evidence_ids contains duplicates",
                    f"{path}.evidence_ids",
                )
            )
        supporting_for_gate = []
        for evidence_id in evidence_ids:
            item = evidence_by_id.get(evidence_id)
            if item is None:
                errors.append(
                    _finding(
                        "UNKNOWN_EVIDENCE",
                        f"gate references unknown evidence {evidence_id!r}",
                        f"{path}.evidence_ids",
                    )
                )
                continue
            if gate_name not in item.get("gate_ids", []):
                errors.append(
                    _finding(
                        "GATE_EVIDENCE_MISMATCH",
                        f"evidence {evidence_id!r} is not mapped back to gate {gate_name!r}",
                        f"{path}.evidence_ids",
                        evidence_id=evidence_id,
                        gate_id=gate_name,
                    )
                )
            if item.get("lifecycle_status", "active") != "active":
                continue
            valid_lineage, has_observed, _ = lineage(evidence_id)
            if (
                item.get("stance") == "supports"
                and item.get("type") != "assumed"
                and valid_lineage
                and has_observed
            ):
                supporting_for_gate.append(evidence_id)
        if outcome in {"pass", "pass_with_limits"} and not supporting_for_gate:
            errors.append(
                _finding(
                    "UNSUPPORTED_GATE",
                    "passing gate lacks gate-specific observed-supported evidence",
                    path,
                    gate_id=gate_name,
                )
            )
        if outcome == "not_applicable":
            if gate_name != "baseline_comparison":
                errors.append(
                    _finding("INVALID_NOT_APPLICABLE", "only baseline may be not_applicable", path)
                )
            if not _nonempty_string(gate.get("not_applicable_reason")):
                errors.append(
                    _finding(
                        "MISSING_FIELD",
                        "not_applicable_reason is required",
                        f"{path}.not_applicable_reason",
                    )
                )
            else:
                warnings.append(
                    _finding(
                        "BASELINE_NOT_APPLICABLE",
                        "baseline comparison is not applicable; PASS is not available",
                        path,
                    )
                )
        issues = gate.get("issues")
        if not isinstance(issues, list):
            errors.append(_finding("INVALID_TYPE", "gate.issues must be a list", f"{path}.issues"))
            issues = []
        if outcome == "fail" and not issues:
            errors.append(
                _finding("MISSING_ISSUE", "failed gate requires an issue", f"{path}.issues")
            )
        if outcome == "pass_with_limits" and not issues and not data.get("limitations"):
            errors.append(
                _finding(
                    "MISSING_LIMITATION",
                    "pass_with_limits requires an issue or material limitation",
                    path,
                )
            )
        for issue_index, issue in enumerate(issues):
            issue_path = f"{path}.issues[{issue_index}]"
            if not isinstance(issue, dict):
                errors.append(_finding("INVALID_TYPE", "issue must be an object", issue_path))
                continue
            if issue.get("severity") not in SEVERITIES:
                errors.append(
                    _finding("INVALID_ENUM", "issue severity is invalid", f"{issue_path}.severity")
                )
            if not _nonempty_string(issue.get("message")):
                errors.append(
                    _finding("MISSING_FIELD", "issue message is required", f"{issue_path}.message")
                )
            issue_evidence = issue.get("evidence_ids")
            if (
                not isinstance(issue_evidence, list)
                or not issue_evidence
                or not all(_nonempty_string(value) for value in issue_evidence)
            ):
                errors.append(
                    _finding(
                        "MISSING_ISSUE_EVIDENCE",
                        "issue.evidence_ids must be a non-empty list",
                        f"{issue_path}.evidence_ids",
                    )
                )
            else:
                for evidence_id in issue_evidence:
                    if evidence_id not in evidence_by_id:
                        errors.append(
                            _finding(
                                "UNKNOWN_EVIDENCE",
                                f"issue references unknown evidence {evidence_id!r}",
                                f"{issue_path}.evidence_ids",
                            )
                        )

    for evidence_id, item in evidence_by_id.items():
        if item.get("lifecycle_status", "active") != "active":
            continue
        for gate_id in item.get("gate_ids", []):
            gate = gate_by_id.get(gate_id)
            if gate is not None and evidence_id not in gate.get("evidence_ids", []):
                errors.append(
                    _finding(
                        "GATE_EVIDENCE_MISMATCH",
                        f"active evidence {evidence_id!r} is not listed by gate {gate_id!r}",
                        f"{evidence_path_by_id[evidence_id]}.gate_ids",
                        evidence_id=evidence_id,
                        gate_id=gate_id,
                    )
                )

    limitations = data.get("limitations")
    if not isinstance(limitations, list):
        errors.append(_finding("INVALID_TYPE", "limitations must be a list", "limitations"))
        limitations = []
    limitation_ids: set[str] = set()
    for index, limitation in enumerate(limitations):
        path = f"limitations[{index}]"
        if not isinstance(limitation, dict):
            errors.append(_finding("INVALID_TYPE", "limitation must be an object", path))
            continue
        limitation_id = limitation.get("id")
        if not _nonempty_string(limitation_id):
            errors.append(_finding("MISSING_FIELD", "limitation.id is required", f"{path}.id"))
        elif limitation_id in limitation_ids:
            errors.append(
                _finding("DUPLICATE_ID", "duplicate limitation id", f"{path}.id")
            )
        else:
            limitation_ids.add(limitation_id)
        if not _nonempty_string(limitation.get("description")):
            errors.append(
                _finding("MISSING_FIELD", "limitation.description is required", f"{path}.description")
            )
        affects = limitation.get("affects_claims")
        if (
            not isinstance(affects, list)
            or not affects
            or not all(_nonempty_string(value) for value in affects)
        ):
            errors.append(
                _finding(
                    "MISSING_CLAIM_MAPPING",
                    "limitation.affects_claims must be a non-empty list",
                    f"{path}.affects_claims",
                )
            )
        else:
            for claim_id in affects:
                if claim_id not in claim_by_id:
                    errors.append(
                        _finding(
                            "UNKNOWN_CLAIM",
                            f"limitation references unknown claim {claim_id!r}",
                            f"{path}.affects_claims",
                        )
                    )

    for claim_id, claim in claim_by_id.items():
        evidence_ids = claim.get("evidence_ids", [])
        active_items = [
            evidence_by_id[evidence_id]
            for evidence_id in evidence_ids
            if evidence_id in evidence_by_id
            and evidence_by_id[evidence_id].get("lifecycle_status", "active") == "active"
        ]
        supporting = [item for item in active_items if item.get("stance") == "supports"]
        contradicting = [item for item in active_items if item.get("stance") == "contradicts"]
        strong_support = []
        assumed_support = []
        for item in supporting:
            evidence_id = item.get("id")
            valid_lineage, has_observed, has_assumed = lineage(evidence_id)
            if item.get("type") == "assumed" or has_assumed:
                assumed_support.append(evidence_id)
            if item.get("type") != "assumed" and valid_lineage and has_observed:
                strong_support.append(evidence_id)
        core = claim.get("core") is True
        assessment = "supported"
        if supporting and contradicting:
            assessment = "contradicted"
            finding = _finding(
                "EVIDENCE_CONTRADICTION",
                f"claim {claim_id!r} has both supporting and contradicting evidence",
                f"claims.{claim_id}",
                claim_id=claim_id,
                supporting_evidence=[item.get("id") for item in supporting],
                contradicting_evidence=[item.get("id") for item in contradicting],
            )
            errors.append(finding)
            report["contradictions"].append(finding)
        elif contradicting:
            assessment = "contradicted"
            finding = _finding(
                "CONTRADICTED_CORE_CLAIM" if core else "CONTRADICTED_NON_CORE_CLAIM",
                f"claim {claim_id!r} is contradicted by active evidence",
                f"claims.{claim_id}",
                claim_id=claim_id,
                contradicting_evidence=[item.get("id") for item in contradicting],
            )
            if core:
                errors.append(finding)
            else:
                warnings.append(finding)
        elif not active_items:
            assessment = "unsupported"
            finding = _finding(
                "MISSING_CORE_EVIDENCE" if core else "MISSING_NON_CORE_EVIDENCE",
                f"claim {claim_id!r} has no active evidence",
                f"claims.{claim_id}.evidence_ids",
                claim_id=claim_id,
            )
            if core:
                errors.append(finding)
                report["missing_evidence"].append(finding)
            else:
                warnings.append(finding)
        elif not supporting:
            assessment = "unsupported"
            finding = _finding(
                "UNSUPPORTED_CORE_CLAIM" if core else "UNSUPPORTED_NON_CORE_CLAIM",
                f"claim {claim_id!r} has no supporting evidence",
                f"claims.{claim_id}.evidence_ids",
                claim_id=claim_id,
            )
            if core:
                errors.append(finding)
                report["unsupported_claims"].append(finding)
            else:
                warnings.append(finding)
        elif not strong_support:
            assessment = "conditional"
            finding = _finding(
                "ASSUMPTION_DEPENDENCY",
                f"claim {claim_id!r} depends on assumed or non-observed support",
                f"claims.{claim_id}.evidence_ids",
                claim_id=claim_id,
                evidence_ids=[item.get("id") for item in supporting],
            )
            warnings.append(finding)
        elif assumed_support:
            assessment = "conditional"
            warnings.append(
                _finding(
                    "ASSUMPTION_DEPENDENCY",
                    f"claim {claim_id!r} includes assumption-dependent support",
                    f"claims.{claim_id}.evidence_ids",
                    claim_id=claim_id,
                    evidence_ids=assumed_support,
                )
            )
        if any(item.get("confidence") == "low" for item in supporting):
            assessment = "conditional" if assessment == "supported" else assessment
            warnings.append(
                _finding(
                    "LOW_CONFIDENCE_EVIDENCE",
                    f"claim {claim_id!r} relies on low-confidence supporting evidence",
                    f"claims.{claim_id}.evidence_ids",
                    claim_id=claim_id,
                )
            )
        report["claim_assessments"][claim_id] = assessment

    baseline = gate_by_id.get("baseline_comparison")
    if baseline and baseline.get("outcome") == "not_applicable":
        comparator_claims = [
            claim_id
            for claim_id, claim in claim_by_id.items()
            if claim.get("requires_comparator") is True
        ]
        if comparator_claims:
            errors.append(
                _finding(
                    "BASELINE_REQUIRED",
                    "baseline cannot be not_applicable for comparator-dependent claims",
                    "gates.baseline_comparison",
                    claim_ids=comparator_claims,
                )
            )

    expected_conclusion = "pass"
    assessments = {
        report["claim_assessments"][claim_id]
        for claim_id, claim in claim_by_id.items()
        if claim.get("core") is True and claim_id in report["claim_assessments"]
    }
    if "contradicted" in assessments or "unsupported" in assessments:
        expected_conclusion = "fail"
    elif "conditional" in assessments:
        expected_conclusion = "pass_with_limits"
    conclusion_gate = gate_by_id.get("conclusion_stability")
    if conclusion_gate and conclusion_gate.get("outcome") != expected_conclusion:
        errors.append(
            _finding(
                "CONCLUSION_GATE_MISMATCH",
                f"conclusion_stability must be {expected_conclusion!r} from claim assessments",
                "gates.conclusion_stability.outcome",
            )
        )

    declared = data.get("declared_verdict")
    if declared is not None and declared not in V1_1_VERDICTS:
        errors.append(
            _finding(
                "INVALID_ENUM",
                "declared_verdict must be PASS, WARN, or FAIL",
                "declared_verdict",
            )
        )

    report["valid"] = not errors
    report["evidence_summary"] = _v1_1_evidence_summary(evidence, report)
    return report


def validate_manifest_detailed(data: dict[str, Any]) -> dict[str, Any]:
    version = data.get("schema_version")
    if version == SCHEMA_VERSION:
        legacy_errors = _validate_manifest_v1_0(data)
        return {
            "schema_version": SCHEMA_VERSION,
            "valid": not legacy_errors,
            "errors": [
                _finding("LEGACY_VALIDATION_ERROR", message) for message in legacy_errors
            ],
            "warnings": [],
            "missing_evidence": [],
            "orphan_evidence": [],
            "unsupported_claims": [],
            "contradictions": [],
            "claim_assessments": {},
            "evidence_summary": {},
        }
    if version == LATEST_SCHEMA_VERSION:
        return _validate_manifest_v1_1(data)
    return {
        "schema_version": version,
        "valid": False,
        "errors": [
            _finding(
                "UNSUPPORTED_SCHEMA_VERSION",
                f"schema_version must be one of {sorted(SUPPORTED_SCHEMA_VERSIONS)!r}",
                "schema_version",
            )
        ],
        "warnings": [],
        "missing_evidence": [],
        "orphan_evidence": [],
        "unsupported_claims": [],
        "contradictions": [],
        "claim_assessments": {},
        "evidence_summary": {},
    }


def validate_manifest(data: dict[str, Any]) -> list[str]:
    """Backward-compatible validation API returning error strings."""
    report = validate_manifest_detailed(data)
    return [f"{item['code']}: {item['message']}" for item in report["errors"]]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", help="manifest JSON path, or - for stdin")
    args = parser.parse_args(argv)
    try:
        data = load_manifest(args.manifest)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"valid": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    if data.get("schema_version") == SCHEMA_VERSION:
        errors = _validate_manifest_v1_0(data)
        print(json.dumps({"valid": not errors, "errors": errors}, ensure_ascii=False, indent=2))
        return 0 if not errors else 1
    report = validate_manifest_detailed(data)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
