# mm-validation

Evidence-bounded validation framework for mathematical-modeling competition workflows.

## Status

Current version: v1.1.

v1.1 provides:

- structured observed, derived, and assumed evidence;
- complete provenance and evidence lifecycle checks;
- bidirectional claim-evidence and gate-evidence mapping;
- contradiction and conclusion-stability checks;
- deterministic `PASS` / `WARN` / `FAIL` adjudication with reasons, failed checks, and evidence summary;
- schema v1.0 compatibility.

## Scope

mm-validation owns validation protocol, evidence provenance, claim verification, conclusion stability, specialist-skill orchestration, and verdict generation. It does not select or implement models, analyze source data, train models, calculate validation metrics, generate figures, or replace `mathmodel-skill` Stage 5.

## Commands

```text
python scripts/validate_evidence_manifest.py manifest.json
python scripts/adjudicate_verdict.py manifest.json
python -m unittest discover -s tests -p "test_*.py" -v
```

The scripts validate JSON declarations and hard decision rules. They never generate model evidence or certify that referenced scientific results are true.

See `references/evidence-verdict-schema.md` for the v1.1 input and output contract and the v1.0 compatibility policy.



