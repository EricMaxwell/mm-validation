# Changelog

## v1.1.0

Added:

- schema v1.1 evidence types, explicit provenance, confidence, stance, gate mappings, and lifecycle states;
- bidirectional claim-evidence and gate-evidence validation;
- missing, orphaned, unsupported, assumption-dependent, and contradictory evidence detection;
- evidence-derived core-claim assessments and conclusion-gate consistency checks;
- deterministic `PASS` / `WARN` / `FAIL` results with reasons, failed checks, evidence summary, and a legacy verdict bridge;
- automated tests for missing evidence, invalid provenance, claim mismatch, contradiction, passing input, and v1.0 compatibility.

Changed:

- passing gates now require gate-specific active observed-supported evidence;
- baseline `not_applicable` is a v1.1 warning and is forbidden for comparator-dependent claims;
- documentation now defines the v1.1 lifecycle, validation flow, verdict meanings, and Stage 5 boundary.

Compatibility:

- schema v1.0 manifests retain their original status values, lowercase four-state verdicts, validator path, and CLI response shape.

## v1.0.0-architecture

Initial architecture baseline.

Added:

- validation skill structure;
- evidence manifest;
- verdict adjudication framework;
- validation references.

Known limitations:

- evidence constraints required strengthening;
- automatic pass required stricter verification rules.



