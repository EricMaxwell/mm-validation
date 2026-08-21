---
name: mm-validation
description: Orchestrate evidence-bounded validation of implemented mathematical-modeling competition models. Use for implementation checks, fair baselines, model-specific diagnostics, sensitivity, robustness, conclusion stability, and a validation verdict. Do not use for model selection, generic statistics or machine-learning instruction, optimization tutorials, plotting, or manuscript peer review.
---

# MM Validation

Act as the validation control layer for an already implemented mathematical-modeling competition solution. Define what must be checked, route specialized work to the available skills, preserve evidence provenance, and issue only a verdict supported by actual artifacts.

## Boundary

Own:

- the contest-grade validation protocol;
- routing among statistical, machine-learning, optimization, scientific-critique, and visualization skills;
- evidence-state and verdict rules;
- mapping validation findings back to core competition conclusions.

Do not own model selection, model fitting tutorials, statistical or optimization methods, figure styling, contest-stage control, paper writing, or formal peer review. Do not rerun work merely to populate every possible diagnostic; select checks that can challenge the actual claims.

## Required operation

1. Identify the model family, implemented artifacts, core claims, fair comparison conditions, acceptance criteria, and available compute budget.
2. Read [references/validation-protocol.md](references/validation-protocol.md) before planning or judging validation.
3. Read the applicable row and guidance in [references/model-family-routing.md](references/model-family-routing.md), then load only the specialist skills needed for the current model.
4. Read [references/evidence-verdict-schema.md](references/evidence-verdict-schema.md) before recording evidence or issuing a verdict.
5. If the task is inside `mathmodel-skill`, also read [references/mathmodel-integration.md](references/mathmodel-integration.md). Keep `mathmodel-skill` in control of stages and user decisions.
6. Cover implementation correctness, baseline comparison, model-specific diagnostics, sensitivity analysis, robustness analysis, and conclusion stability. Then adjudicate exactly one verdict: `pass`, `pass_with_limits`, `inconclusive`, or `fail`.

## Non-negotiable evidence rules

- Never invent a validation result, metric, threshold, interval, improvement, failure boundary, command, artifact, or run.
- Record evidence only as `observed`, `derived`, `reported`, `not_run`, `unavailable`, or `not_applicable`.
- Only `observed` evidence and `derived` evidence traceable to observed evidence can support a passing gate.
- Treat implementation correctness as a hard gate. No score or performance result can override its failure.
- Predeclare comparison conditions and acceptance criteria before inspecting comparison results when feasible.
- If required validation was not executed or cannot be reproduced, provide the plan and gaps and return `inconclusive`, not a hypothetical result.
- Limit every positive conclusion to the tested data, parameter domain, scenarios, seeds, and model specification.

## Control scripts

Use `scripts/validate_evidence_manifest.py` to check manifest structure, evidence states, provenance links, and gate consistency. Use `scripts/adjudicate_verdict.py` to apply the hard verdict precedence. These scripts validate declarations and control logic; they do not establish that a model is scientifically correct.

## Handoff

Return the validation scope, checks actually executed, missing checks, baseline fairness assessment, diagnostic findings, sensitivity and robustness boundaries, per-claim stability, evidence paths, limitations, and the adjudicated verdict. Keep reported claims separate from independently observed results.
