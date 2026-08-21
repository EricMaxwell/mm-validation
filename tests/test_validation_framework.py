from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from adjudicate_verdict import adjudicate, adjudicate_v1_1  # noqa: E402
from validate_evidence_manifest import (  # noqa: E402
    REQUIRED_GATES,
    validate_manifest,
    validate_manifest_detailed,
)


def _provenance(evidence_id: str) -> dict:
    return {
        "origin": f"control fixture {evidence_id}",
        "generation_method": "unit-test fixture construction",
        "timestamp": "2026-08-21T00:00:00+08:00",
        "responsible_party": "mm-validation unittest",
    }


def build_v1_1_manifest() -> dict:
    evidence = []
    gates = {}
    evidence_ids = []
    for index, gate_name in enumerate(REQUIRED_GATES, start=1):
        evidence_id = f"E{index}"
        evidence_ids.append(evidence_id)
        evidence.append(
            {
                "id": evidence_id,
                "claim_id": "C1",
                "type": "observed",
                "source": f"control://unit-test/{evidence_id}",
                "description": f"Control evidence for {gate_name}; no model result.",
                "provenance": _provenance(evidence_id),
                "confidence": "high",
                "stance": "supports",
                "gate_ids": [gate_name],
                "derived_from": [],
                "lifecycle_status": "active",
            }
        )
        gates[gate_name] = {
            "outcome": "pass",
            "criterion": "Control-only criterion for validator behavior.",
            "summary": "Control-only summary; no model result is asserted.",
            "evidence_ids": [evidence_id],
            "not_applicable_reason": None,
            "issues": [],
        }
    return {
        "schema_version": "1.1",
        "validation_id": "control-v1.1-pass",
        "model": {
            "family": "simulation",
            "name": "Control fixture, not a model validation",
            "artifacts": ["control://implementation"],
        },
        "claims": [
            {
                "id": "C1",
                "statement": "Control claim used only to test framework decisions.",
                "core": True,
                "evidence_ids": evidence_ids,
                "requires_comparator": False,
            }
        ],
        "evidence": evidence,
        "gates": gates,
        "limitations": [],
    }


def build_v1_0_manifest() -> dict:
    gates = {
        gate_name: {
            "outcome": "pass",
            "criterion": "Legacy control criterion.",
            "summary": "Legacy control summary.",
            "evidence_ids": ["E1"],
            "not_applicable_reason": None,
            "issues": [],
        }
        for gate_name in REQUIRED_GATES
    }
    return {
        "schema_version": "1.0",
        "validation_id": "control-v1.0-pass",
        "model": {
            "family": "simulation",
            "name": "Legacy control fixture",
            "artifacts": [],
        },
        "claims": [
            {
                "id": "C1",
                "statement": "Legacy control claim.",
                "stability": "stable",
            }
        ],
        "evidence": [
            {
                "id": "E1",
                "status": "observed",
                "description": "Legacy control evidence.",
                "artifact_path": None,
                "command": "legacy-control-test",
                "run_id": "control-v1.0-pass",
                "source": None,
                "derived_from": [],
                "reason": None,
                "metadata": {},
            }
        ],
        "gates": gates,
        "limitations": [],
    }


class ValidationFrameworkTests(unittest.TestCase):
    def test_missing_evidence(self) -> None:
        manifest = build_v1_1_manifest()
        manifest["claims"].append(
            {
                "id": "C2",
                "statement": "Second core control claim with no evidence.",
                "core": True,
                "evidence_ids": [],
                "requires_comparator": False,
            }
        )
        report = validate_manifest_detailed(manifest)
        self.assertIn("MISSING_CORE_EVIDENCE", {item["code"] for item in report["errors"]})
        self.assertEqual(adjudicate_v1_1(manifest, report)["verdict"], "FAIL")

    def test_invalid_provenance(self) -> None:
        manifest = build_v1_1_manifest()
        del manifest["evidence"][0]["provenance"]["origin"]
        report = validate_manifest_detailed(manifest)
        self.assertIn("INVALID_PROVENANCE", {item["code"] for item in report["errors"]})
        self.assertEqual(adjudicate_v1_1(manifest, report)["verdict"], "FAIL")

    def test_claim_mismatch(self) -> None:
        manifest = build_v1_1_manifest()
        manifest["evidence"][0]["claim_id"] = "UNKNOWN_CLAIM"
        report = validate_manifest_detailed(manifest)
        codes = {item["code"] for item in report["errors"]}
        self.assertIn("ORPHAN_EVIDENCE", codes)
        self.assertIn("CLAIM_EVIDENCE_MISMATCH", codes)
        self.assertEqual(adjudicate_v1_1(manifest, report)["verdict"], "FAIL")

    def test_contradiction(self) -> None:
        manifest = build_v1_1_manifest()
        contradiction = {
            "id": "E7",
            "claim_id": "C1",
            "type": "observed",
            "source": "control://unit-test/E7",
            "description": "Control contradiction used only to test decision logic.",
            "provenance": _provenance("E7"),
            "confidence": "high",
            "stance": "contradicts",
            "gate_ids": ["conclusion_stability"],
            "derived_from": [],
            "lifecycle_status": "active",
        }
        manifest["evidence"].append(contradiction)
        manifest["claims"][0]["evidence_ids"].append("E7")
        conclusion = manifest["gates"]["conclusion_stability"]
        conclusion["outcome"] = "fail"
        conclusion["evidence_ids"].append("E7")
        conclusion["issues"] = [
            {
                "severity": "high",
                "message": "Control contradiction is unresolved.",
                "evidence_ids": ["E7"],
            }
        ]
        report = validate_manifest_detailed(manifest)
        self.assertIn("EVIDENCE_CONTRADICTION", {item["code"] for item in report["errors"]})
        result = adjudicate_v1_1(manifest, report)
        self.assertEqual(result["verdict"], "FAIL")
        self.assertIn("EVIDENCE_CONTRADICTION", result["failed_checks"])

    def test_pass_case(self) -> None:
        manifest = build_v1_1_manifest()
        report = validate_manifest_detailed(manifest)
        self.assertTrue(report["valid"], report["errors"])
        result = adjudicate_v1_1(manifest, report)
        self.assertEqual(result["verdict"], "PASS")
        self.assertEqual(result["failed_checks"], [])
        self.assertEqual(result["evidence_summary"]["total"], len(REQUIRED_GATES))

    def test_derived_evidence_with_observed_ancestor(self) -> None:
        manifest = build_v1_1_manifest()
        derived = {
            "id": "E7",
            "claim_id": "C1",
            "type": "derived",
            "source": "control://unit-test/E7",
            "description": "Control derivation used only to test provenance lineage.",
            "provenance": _provenance("E7"),
            "confidence": "high",
            "stance": "supports",
            "gate_ids": ["conclusion_stability"],
            "derived_from": ["E6"],
            "lifecycle_status": "active",
        }
        manifest["evidence"].append(derived)
        manifest["claims"][0]["evidence_ids"].append("E7")
        manifest["gates"]["conclusion_stability"]["evidence_ids"].append("E7")
        report = validate_manifest_detailed(manifest)
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(adjudicate_v1_1(manifest, report)["verdict"], "PASS")

    def test_assumption_dependency_warn(self) -> None:
        manifest = build_v1_1_manifest()
        assumption = {
            "id": "E7",
            "claim_id": "C1",
            "type": "assumed",
            "source": "control://unit-test/E7",
            "description": "Control assumption used only to test WARN adjudication.",
            "provenance": _provenance("E7"),
            "confidence": "medium",
            "stance": "supports",
            "gate_ids": ["conclusion_stability"],
            "derived_from": [],
            "lifecycle_status": "active",
        }
        manifest["evidence"].append(assumption)
        manifest["claims"][0]["evidence_ids"].append("E7")
        conclusion = manifest["gates"]["conclusion_stability"]
        conclusion["outcome"] = "pass_with_limits"
        conclusion["evidence_ids"].append("E7")
        manifest["limitations"].append(
            {
                "id": "L1",
                "description": "Control-only assumption dependency.",
                "affects_claims": ["C1"],
            }
        )
        report = validate_manifest_detailed(manifest)
        self.assertTrue(report["valid"], report["errors"])
        self.assertEqual(report["claim_assessments"]["C1"], "conditional")
        self.assertEqual(adjudicate_v1_1(manifest, report)["verdict"], "WARN")

    def test_v1_0_compatibility(self) -> None:
        manifest = build_v1_0_manifest()
        self.assertEqual(validate_manifest(manifest), [])
        verdict, reasons = adjudicate(manifest)
        self.assertEqual(verdict, "pass")
        self.assertTrue(reasons)


if __name__ == "__main__":
    unittest.main()
