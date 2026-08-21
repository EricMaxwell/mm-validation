# Integration with mathmodel-skill

`mathmodel-skill` is the host workflow for CUMCM, MCM/ICM, and Diangong Cup work. `mm-validation` is a specialist validation protocol. It must not take over `current_stage`, numbered user decisions, competition rules, scoring thresholds, writing, or submission review.

## Ownership

| Concern | Owner |
|---|---|
| Competition selection, problem state, deadlines, stage transitions, user confirmations | `mathmodel-skill` |
| Validation plan, evidence provenance, six validation gates, claim stability, validation verdict | `mm-validation` |
| Statistical, ML, optimization, critique, and visualization method details | Routed specialist skills |
| Stage rubric and `score_artifact.py` workflow verdict | `mathmodel-skill` |

The mm-validation verdict and the mathmodel stage verdict answer different questions. Preserve both with explicit names; never overwrite one with the other.

## Stage mapping

### Stage 5: implemented subproblems

For each affected Qi, run or inspect:

- implementation correctness;
- fair baseline comparison;
- model-specific diagnostics that must precede interpretation;
- provenance for code, formula, inputs, saved results, and commands.

Return evidence paths and unresolved issues to the existing Qi record. A high-severity correctness issue maps to the host’s `block` behavior. Do not allow a high stage score to override it.

### Stage 6: global validation

Use the Stage 5 artifacts and Stage 3/4 assumptions to conduct:

- remaining model-specific diagnostics;
- sensitivity analysis;
- robustness analysis;
- conclusion stability;
- the mm-validation verdict.

Map only concise, evidence-bounded summaries into existing Stage 6 fields:

| mm-validation result | Existing Stage 6 field |
|---|---|
| actual jointly varied parameters | `params_varied_jointly` |
| method, split, scenarios, ranges, sample budget, seeds | `method` |
| tested ranges or scenario IDs | `deltas` |
| actual intervals with domain and method | `robust_intervals` |
| claim stability and mm verdict summary | `stability_verdict` |
| observed boundary or explicit untested region | `failure_warning` |
| challenged Stage 3/4/5 premise and action | `L2_backtrack` |
| figures actually generated from validation data | `figures` |

Do not put hypothetical values into these fields. Empty arrays, `null`, `not_run`, or an explicit evidence gap are preferable to invented completeness.

### Stage 7: evidence-bounded evaluation

Translate the manifest without strengthening it:

- `stable` evidence may support a scoped strength;
- `conditional` claims become limitations and boundary language;
- `unstable` claims trigger revision or backtracking, not a rhetorical limitation;
- `untested` claims become evidence gaps, not claimed strengths;
- proposed improvements retain `observed_gain=null` until a real comparison is executed.

## Sidecar state

Use `<cwd>/state/mm_validation.json` as the canonical validation manifest unless the user or host project specifies another path. This avoids silently changing the `decision_log.json` schema.

The sidecar should contain only mm-validation data. Store pointers or summaries in `decision_log.json`; do not duplicate raw logs or large result tables. When a summary and sidecar conflict, stop with `inconclusive`, identify the mismatch, and ask the host workflow to reconcile it.

## Verdict bridge

| mm-validation verdict | Host implication |
|---|---|
| `pass` | Validation evidence can support progression, subject to the host rubric and user decision |
| `pass_with_limits` | Progress only with limitations carried into Stage 7/8 and relevant L2 review |
| `inconclusive` | Remain in validation or explicitly carry an evidence gap; never translate to host `pass` |
| `fail` from correctness/high issue | Host `block`; repair or backtrack |
| `fail` from a challenged premise or unstable core claim | Use Stage 6 L2 evidence to select the smallest Stage 3/4/5 backtrack |

The host may be stricter than mm-validation. A host stage pass cannot turn an mm-validation `fail` or `inconclusive` into validated evidence.

## Standalone use

Outside `mathmodel-skill`, keep the same manifest and verdict rules. Do not create a ten-stage contest workflow, competition compliance system, or paper-writing process inside this skill.
