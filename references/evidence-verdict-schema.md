# Evidence Manifest and Verdict Schema

The manifest is a control record. It points to validation evidence; it does not replace raw outputs, logs, code, data, or human inspection. Schema v1.1 is the current format. Schema v1.0 remains accepted for backward compatibility.

## v1.1 top-level shape

```json
{
  "schema_version": "1.1",
  "validation_id": "<stable validation identifier>",
  "model": {
    "family": "prediction | regression | classification | optimization | ranking | simulation | hybrid",
    "name": "<implemented model name>",
    "artifacts": ["<inspectable formula, code, config, data, log, or result identifier>"]
  },
  "claims": [],
  "evidence": [],
  "gates": {},
  "limitations": [],
  "declared_verdict": "PASS | WARN | FAIL",
  "metadata": {}
}
```

`declared_verdict` and `metadata` are optional. Unknown top-level fields are rejected. The declared verdict, when present, must match adjudication.

## Claims and bidirectional mapping

```json
{
  "id": "C1",
  "statement": "<bounded, testable competition conclusion>",
  "core": true,
  "evidence_ids": ["E1"],
  "requires_comparator": false
}
```

Claim IDs are unique. `core` is required; `requires_comparator` is optional. Every referenced evidence ID must exist and its `claim_id` must point back to the same claim. Conversely, every evidence item must be listed by its named claim. The validator reports:

- `MISSING_CORE_EVIDENCE` when a core claim has no active evidence;
- `UNSUPPORTED_CORE_CLAIM` when it has evidence but no support;
- `ORPHAN_EVIDENCE` when evidence names no known claim or is not listed by that claim;
- `CLAIM_EVIDENCE_MISMATCH` when the two mapping directions disagree.

Non-core missing or unsupported claims produce warnings. Core failures produce `FAIL`.

## Evidence entries

Every v1.1 evidence item requires at least `id`, `claim_id`, `type`, `source`, `description`, `provenance`, and `confidence`:

```json
{
  "id": "E1",
  "claim_id": "C1",
  "type": "observed | derived | assumed",
  "source": "<artifact, record, input, or authority identifier>",
  "description": "<what exists and how it bears on the claim>",
  "provenance": {
    "origin": "<where the evidence came from>",
    "generation_method": "<inspection, command, derivation, or assumption declaration>",
    "timestamp": "<ISO 8601 timestamp with timezone>",
    "responsible_party": "<person, team, or system>"
  },
  "confidence": "high | medium | low",
  "stance": "supports | contradicts | neutral",
  "gate_ids": ["implementation_correctness"],
  "derived_from": [],
  "lifecycle_status": "active | superseded | invalidated"
}
```

When no responsible party applies, replace `responsible_party` with a nonempty `responsibility_not_applicable_reason`. Timestamps without a timezone are rejected. `stance` and a nonempty gate mapping are required. `lifecycle_status` defaults to `active` when omitted.

Evidence types:

- `observed`: a direct inspection, measurement, or executed check. Its source must identify the preserved record; the validator does not open or certify that record.
- `derived`: a reproducible computation or logical derivation. It requires a nonempty, acyclic `derived_from` list whose IDs exist.
- `assumed`: a human-declared premise, parameter condition, or scenario assumption. It is not observed support.

A derived chain may include observed and assumed ancestors. It can support a passing gate only if its lineage is structurally valid and at least one ancestor is observed. An assumption-only chain is legal but warns and makes claim support conditional. This rule preserves real modeling workflows without allowing assumptions alone to establish a validated result.

Lifecycle behavior:

- `active` evidence participates in mappings, contradiction checks, claim assessments, and gate support;
- `superseded` evidence remains for history but does not participate in current adjudication;
- `invalidated` evidence remains auditable but cannot support or contradict the current claim.

If active supporting and active contradicting evidence both map to one claim, the validator reports `EVIDENCE_CONTRADICTION`. A sole active contradiction also contradicts the claim. The framework detects declared semantic conflict; it does not infer contradictions from arbitrary prose or numeric artifacts.

## Gates

The manifest must contain exactly:

- `implementation_correctness`
- `baseline_comparison`
- `model_specific_diagnostics`
- `sensitivity_analysis`
- `robustness_analysis`
- `conclusion_stability`

Each gate has:

```json
{
  "outcome": "pass | pass_with_limits | inconclusive | fail | not_applicable",
  "criterion": "<predeclared criterion and source>",
  "summary": "<evidence-bounded finding; no invented values>",
  "evidence_ids": ["E1"],
  "not_applicable_reason": null,
  "issues": [
    {
      "severity": "high | medium | low",
      "message": "<unresolved issue>",
      "evidence_ids": ["E1"]
    }
  ]
}
```

Gate-to-evidence mappings are bidirectional. A `pass` or `pass_with_limits` gate requires active supporting observed evidence, or valid derived evidence with an observed ancestor, specifically mapped to that gate. Assumptions cannot independently satisfy this rule. A failed gate requires an issue; every issue must cite evidence. A limited pass requires an issue or material limitation.

Only `baseline_comparison` may be `not_applicable`, and it requires a reason. It produces `WARN` in v1.1 because no full comparison was executed. If any claim sets `requires_comparator=true`, the baseline cannot be not applicable.

The conclusion gate is checked against core-claim assessments derived from evidence:

- any core claim `contradicted` or `unsupported` -> gate `fail`;
- otherwise any core claim `conditional` -> gate `pass_with_limits`;
- otherwise -> gate `pass`.

This is a one-way consistency rule. The declared gate outcome never changes the evidence-derived assessment.

## Limitations

```json
{
  "id": "L1",
  "description": "<tested boundary or remaining material limitation>",
  "affects_claims": ["C1"]
}
```

Limitation IDs are unique, affected claim IDs must exist, and the affected-claims list cannot be empty. Any material limitation produces `WARN` unless a harder rule already produces `FAIL`.

## v1.1 verdict precedence and output

Adjudicate without averaging:

1. `FAIL` if schema/provenance/mapping validation has any error, an applicable gate fails, or a high-severity issue remains.
2. Otherwise `WARN` if any validator warning remains, a gate is not a full pass, a medium/low issue remains, or a material limitation exists.
3. Otherwise `PASS`.

The adjudicator returns:

```json
{
  "schema_version": "1.1",
  "verdict": "PASS | WARN | FAIL",
  "legacy_verdict": "pass | pass_with_limits | inconclusive | fail",
  "reasons": [],
  "failed_checks": [],
  "evidence_summary": {},
  "claim_assessments": {}
}
```

`failed_checks` lists hard-rule codes. `evidence_summary` is descriptive metadata about the manifest, not a model-performance result. The legacy bridge is `inconclusive` when a v1.1 warning includes an inconclusive gate; other warnings map to `pass_with_limits`.

## v1.0 compatibility

Manifests with `schema_version: "1.0"` continue to use the original evidence statuses `observed`, `derived`, `reported`, `not_run`, `unavailable`, and `not_applicable`, original claim stability values, and lowercase verdicts `pass`, `pass_with_limits`, `inconclusive`, and `fail`. Their validation and CLI output remain on the v1.0 path. New manifests should use v1.1; the validator does not silently migrate records.

## Script behavior

```text
python scripts/validate_evidence_manifest.py manifest.json
python scripts/adjudicate_verdict.py manifest.json
```

Pass `-` instead of a path to read JSON from standard input. Invalid JSON or a non-object root exits as a load error. The validator checks declared structure and control logic only. The scripts never calculate RMSE, VIF, Sobol indices, Pareto fronts, figures, or any other model result.
