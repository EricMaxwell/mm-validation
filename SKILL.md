---
name: mm-validation
description: Orchestrate evidence-bounded validation of implemented mathematical-modeling competition models. Use for claim-evidence mapping, provenance checks, implementation checks, fair baselines, model-specific diagnostics, sensitivity, robustness, conclusion stability, and deterministic validation verdicts. Do not use for model selection, model implementation or training, generic data analysis, plotting, or manuscript peer review.
---

# MM Validation

Act as the validation framework and orchestration layer for an already implemented mathematical-modeling competition solution. Define what must be checked, route method-level work to available specialist skills, bind claims to evidence, preserve provenance, and issue only an evidence-supported verdict.

## Boundary

Own:

- the contest-grade validation protocol;
- routing among statistical, machine-learning, optimization, scientific-critique, and visualization skills;
- evidence provenance, lifecycle, and claim-evidence consistency rules;
- contradiction and conclusion-stability checks;
- deterministic validation verdict generation.

Do not own model selection, algorithm implementation, data analysis, model fitting or training, statistical or optimization methods, figure production, contest-stage control, paper writing, or formal peer review. In particular, do not replace `mathmodel-skill` Stage 5 implementation work. Do not run checks merely to populate a checklist; select checks that can challenge actual claims.

## Required operation

1. Identify the model family, implemented artifacts, core claims, fair comparison conditions, acceptance criteria, and available compute budget.
2. Read [references/validation-protocol.md](references/validation-protocol.md) before planning or judging validation.
3. Read the applicable row and guidance in [references/model-family-routing.md](references/model-family-routing.md), then load only the specialist skills needed for the current model.
4. Read [references/evidence-verdict-schema.md](references/evidence-verdict-schema.md) before recording evidence, mapping a claim, or issuing a verdict.
5. If the task is inside `mathmodel-skill`, also read [references/mathmodel-integration.md](references/mathmodel-integration.md). Keep `mathmodel-skill` in control of stages and user decisions.
6. Cover implementation correctness, baseline comparison, model-specific diagnostics, sensitivity analysis, robustness analysis, and conclusion stability.
7. For a v1.1 manifest, validate its claim-evidence graph and adjudicate exactly one framework verdict: `PASS`, `WARN`, or `FAIL`. Preserve the v1.0 lowercase verdict behavior when reading a v1.0 manifest.

## Non-negotiable evidence rules

- Never invent a validation result, metric, threshold, interval, improvement, failure boundary, command, artifact, or run.
- In schema v1.1, record evidence type only as `observed`, `derived`, or `assumed`; retain v1.0 status values only for legacy manifests.
- Every v1.1 evidence item must name its claim, source, generation method, timestamp with timezone, and responsible party or an explicit reason why responsibility is not applicable.
- A passing gate requires active supporting `observed` evidence or valid `derived` evidence with an observed ancestor. Assumptions may make a claim conditional but cannot independently support a passing gate.
- Never hide conflicting evidence. Active support and active contradiction for the same claim are a hard failure until reconciled through the evidence lifecycle.
- Treat implementation correctness as a hard gate. No score or performance result can override its failure.
- Predeclare comparison conditions and acceptance criteria before inspecting comparison results when feasible.
- If required validation was not executed or cannot be reproduced, record the gap and do not claim `PASS`.
- Limit every positive conclusion to the tested data, parameter domain, scenarios, seeds, and model specification.

## Control scripts

Use `scripts/validate_evidence_manifest.py` to check manifest structure, provenance, lifecycle, claim-evidence mappings, gate mappings, contradictions, and conclusion consistency. Use `scripts/adjudicate_verdict.py` to apply hard verdict precedence and return reasons, failed checks, and an evidence summary. These scripts validate declarations and control logic; they do not inspect artifact content, compute model metrics, or establish scientific correctness.

## Handoff

Return the validation scope, checks actually executed, missing checks, baseline fairness assessment, diagnostic findings, sensitivity and robustness boundaries, per-claim assessment, evidence paths, limitations, and the adjudicated verdict. Keep assumptions separate from observations and derived evidence.
