# Evidence Manifest and Verdict Schema

The manifest is a control record. It points to validation evidence; it does not replace raw outputs, logs, code, data, or human inspection.

## Top-level shape

```json
{
  "schema_version": "1.0",
  "validation_id": "<stable run identifier>",
  "model": {
    "family": "prediction | regression | classification | optimization | ranking | simulation | hybrid",
    "name": "<implemented model name>",
    "artifacts": ["<formula, code, config, data, or result path>"]
  },
  "claims": [
    {
      "id": "C1",
      "statement": "<core competition claim>",
      "stability": "stable | conditional | unstable | untested"
    }
  ],
  "evidence": [],
  "gates": {},
  "limitations": [],
  "declared_verdict": "pass | pass_with_limits | inconclusive | fail"
}
```

`declared_verdict` is optional. When present, it must equal the deterministic adjudication result.

## Evidence entries

Every evidence entry has:

```json
{
  "id": "E1",
  "status": "observed | derived | reported | not_run | unavailable | not_applicable",
  "description": "<what this item establishes>",
  "artifact_path": null,
  "command": null,
  "run_id": null,
  "source": null,
  "derived_from": [],
  "reason": null,
  "metadata": {}
}
```

Rules by status:

- `observed`: an actual inspection or run occurred. Require `artifact_path`, or both `command` and `run_id`. The artifact should preserve the output, check record, or independently inspectable result.
- `derived`: the item is reproducibly calculated from other evidence. Require nonempty `derived_from`; every dependency must eventually trace only to `observed` evidence.
- `reported`: the item is asserted by the user, paper, or another record but not independently verified. Require `source`.
- `not_run`: the check was planned but not executed. Require `reason`.
- `unavailable`: a required input, tool, artifact, or authority was unavailable. Require `reason`.
- `not_applicable`: the item genuinely does not apply. Require `reason`; do not use it to hide a missing check.

Evidence IDs are unique. Derived links must exist, cannot reference themselves, and cannot form cycles. `reported`, `not_run`, `unavailable`, and `not_applicable` evidence cannot support a passing gate.

The optional `metadata` object may hold units, versions, seeds, hashes, tested ranges, or structured result locations. It must not be used to bypass provenance requirements.

## Gate records

The manifest must contain exactly these six gate keys:

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
  "criterion": "<predeclared criterion and its source>",
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

Gate rules:

- A `pass` or `pass_with_limits` gate requires at least one supporting `observed` item or a `derived` item whose complete ancestry is observed.
- `not_applicable` is allowed only for `baseline_comparison` and requires `not_applicable_reason`.
- A failed gate requires at least one unresolved issue.
- Keep only unresolved issues in `issues`; preserve resolved issues in the project’s normal event or history mechanism.
- `implementation_correctness` is always applicable and is a hard gate.
- The conclusion gate must agree with claim states: any `unstable` claim means `fail`; otherwise any `untested` claim means `inconclusive`; otherwise any `conditional` claim means `pass_with_limits`; otherwise all claims are `stable` and the gate is `pass`.

## Limitations

Each material limitation has:

```json
{
  "id": "L1",
  "description": "<tested boundary or remaining limitation>",
  "affects_claims": ["C1"]
}
```

Claim IDs must exist. Empty limitations are valid when no material limit remains; never add decorative limitations.

## Verdict precedence

Adjudicate without averaging:

1. `fail` if any applicable gate failed, any unresolved issue is high severity, or any claim is unstable.
2. Otherwise `inconclusive` if any applicable gate is inconclusive or any claim is untested.
3. Otherwise `pass_with_limits` if any gate passed with limits, any claim is conditional, any unresolved medium/low issue remains, or any material limitation is recorded.
4. Otherwise `pass`.

A justified `baseline_comparison=not_applicable` does not automatically lower the verdict. The baseline gate was still covered: its applicability was explicitly adjudicated and documented.

## Script behavior

```text
python scripts/validate_evidence_manifest.py manifest.json
python scripts/adjudicate_verdict.py manifest.json
```

Pass `-` instead of a path to read JSON from standard input. The validator checks declared structure and provenance links, not whether an artifact’s scientific content is true. The adjudicator refuses an invalid manifest and reports a mismatch when `declared_verdict` conflicts with the hard rules.
