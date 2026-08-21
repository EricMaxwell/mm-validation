# Integration with mathmodel-skill

`mathmodel-skill` is the host workflow for CUMCM, MCM/ICM, and Diangong Cup work. `mm-validation` is its evidence and validation framework. It must not take over `current_stage`, numbered user decisions, competition rules, scoring thresholds, implementation, writing, or submission review. Schema v1.1 strengthens the sidecar evidence record; it does not replace Stage 5.

## Ownership

| Concern | Owner |
|---|---|
| Competition selection, problem state, deadlines, stage transitions, user confirmations | `mathmodel-skill` |
| Claim-evidence graph, provenance/lifecycle checks, six validation gates, contradiction detection, validation verdict | `mm-validation` |
| Statistical, ML, optimization, critique, and visualization method details | Routed specialist skills |
| Stage rubric and `score_artifact.py` workflow verdict | `mathmodel-skill` |

The mm-validation verdict and the mathmodel stage verdict answer different questions. Preserve both with explicit names; never overwrite one with the other.

## Stage mapping

### Stage 5: implemented subproblems

Stage 5 owns model formulation-to-code implementation, execution, and correction. `mm-validation` consumes the resulting artifacts and records validation evidence. For each affected Qi, validate or route inspection of:

- implementation correctness;
- fair baseline comparison;
- model-specific diagnostics that must precede interpretation;
- provenance for code, formula, inputs, saved results, and commands.

Do not ask `mm-validation` to write the algorithm, fit or train the model, generate the solution outputs, or repair the implementation. Those actions remain in Stage 5 or its routed implementation skill. Return evidence paths and unresolved issues to the existing Qi record. A v1.1 `FAIL` caused by implementation correctness or a high-severity issue maps to the host’s `block` behavior. Do not allow a high stage score to override it.

### Stage 6: global validation

Use the Stage 5 artifacts and Stage 3/4 assumptions to create explicit v1.1 evidence records and conduct:

- remaining model-specific diagnostics;
- sensitivity analysis;
- robustness analysis;
- conclusion stability;
- claim-evidence consistency and contradiction checks;
- the mm-validation verdict.

Map only concise, evidence-bounded summaries into existing Stage 6 fields:

| mm-validation result | Existing Stage 6 field |
|---|---|
| actual jointly varied parameters | `params_varied_jointly` |
| method, split, scenarios, ranges, sample budget, seeds | `method` |
| tested ranges or scenario IDs | `deltas` |
| actual intervals with domain and method | `robust_intervals` |
| evidence-derived core-claim assessments and mm verdict summary | `stability_verdict` |
| observed boundary or explicit untested region | `failure_warning` |
| challenged Stage 3/4/5 premise and action | `L2_backtrack` |
| figures actually generated from validation data | `figures` |

Do not put hypothetical values into these fields. Empty arrays, `null`, `not_run`, or an explicit evidence gap are preferable to invented completeness.

### Stage 7: evidence-bounded evaluation

Translate the v1.1 manifest without strengthening it:

- `supported` core claims may support a scoped strength;
- `conditional` claims become limitations and boundary language;
- `contradicted` core claims trigger revision or backtracking, not a rhetorical limitation;
- `unsupported` claims become evidence gaps, not claimed strengths;
- proposed improvements retain `observed_gain=null` until a real comparison is executed.

## Sidecar state

Use `<cwd>/state/mm_validation.json` as the canonical validation manifest unless the user or host project specifies another path. Use schema v1.1 for new records; validate existing v1.0 records through the legacy path rather than silently changing them. This avoids silently changing the `decision_log.json` schema.

The sidecar should contain only mm-validation data. Store pointers or summaries in `decision_log.json`; do not duplicate raw logs or large result tables. When a summary and sidecar conflict, stop with `inconclusive`, identify the mismatch, and ask the host workflow to reconcile it.

## Verdict bridge

| mm-validation v1.1 verdict | Host implication |
|---|---|
| `PASS` | Validation evidence can support progression, subject to the host rubric and user decision |
| `WARN` with `legacy_verdict=pass_with_limits` | Progress only if limitations and assumption dependencies are carried into Stage 7/8 and relevant L2 review |
| `WARN` with `legacy_verdict=inconclusive` | Remain in validation or explicitly carry an evidence gap; never translate to host `pass` |
| `FAIL` from correctness/high issue | Host `block`; repair or backtrack |
| `FAIL` from a challenged premise, contradiction, or unsupported core claim | Use Stage 6 L2 evidence to select the smallest Stage 3/4/5 backtrack |

The host may be stricter than mm-validation. A host stage pass cannot turn an mm-validation `FAIL` or unresolved `WARN` into validated evidence. For legacy v1.0 manifests, retain the original lowercase bridge described in `evidence-verdict-schema.md`.

## Standalone use

Outside `mathmodel-skill`, keep the same manifest and verdict rules. Do not create a ten-stage contest workflow, competition compliance system, or paper-writing process inside this skill.
