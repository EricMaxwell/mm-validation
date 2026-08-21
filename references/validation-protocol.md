# Contest-Grade Validation Protocol

Use this protocol after a model has an executable or otherwise inspectable implementation. Validation is claim-centered: every check must challenge a stated competition conclusion, an implementation invariant, or a known failure mode. Schema v1.1 adds evidence provenance, lifecycle, claim binding, and deterministic `PASS` / `WARN` / `FAIL` adjudication; it does not execute the underlying statistical, machine-learning, optimization, or simulation method.

## 1. Intake and precommitment

Record before judging results:

- competition and problem context;
- model family and model name;
- formula, code, configuration, data, saved result, and run-entry paths actually available;
- core claims and the decision each claim supports;
- the target population, period, region, operating regime, or scenario;
- primary metrics with units and direction;
- acceptance criteria and their source;
- comparison budget, constraints, information set, data split, and random-seed policy;
- time or compute limits that constrain validation.

Give every core claim a stable ID and mark it `core=true`. Predeclare whether a claim depends on comparison with a baseline. Evidence may be attached only after its source, generation method, timestamp, and responsible party are known; absence of that information is a validation failure, not an invitation to reconstruct a plausible record.

If an acceptance threshold lacks a problem, domain, policy, or user source, do not manufacture one. Report the observed value and mark the judgment criterion as unavailable.

## 2. Implementation correctness — hard gate

Establish that the implementation corresponds to the stated model before interpreting performance.

Cover the applicable checks:

- formula, objective, constraints, parameter transformations, units, signs, index ranges, and boundary conditions match code;
- inputs come from the declared files and columns, with exclusions and missing-data handling recorded;
- the stated run entry executes in the recorded environment;
- a hand-checkable, analytical, exhaustive small case, trusted fixture, or independent recomputation supplies an oracle where feasible;
- invariants, conservation rules, feasibility conditions, probability bounds, or accounting identities hold;
- reported objective values and summary metrics can be recomputed from saved outputs;
- stochastic behavior records seeds and nondeterministic components;
- errors, solver statuses, warnings, failed samples, and fallback behavior are retained rather than hidden.

An observed formula-code mismatch, invalid constraint, wrong data path, unit error, unreproducible central run, or false reported output is a failure. Missing evidence is `inconclusive`; it is not evidence of correctness.

## 3. Baseline comparison

Define a baseline that is simpler, conventional, previously used, analytically available, or operationally current. A comparison is fair only when the candidate and baseline share all decision-relevant conditions:

- the same data availability and leakage boundary;
- the same train/validation/test or scenario partition;
- the same objective, outcome definition, constraints, and evaluation horizon;
- equivalent preprocessing access and tuning budget;
- compatible computation or runtime limits when efficiency is claimed;
- the same metric implementation and units.

Record both absolute results and decision-relevant differences. A candidate need not dominate every baseline metric when the claimed benefit is a documented trade-off, but it must not be described as superior outside the compared criteria.

Use `not_applicable` only when no meaningful comparator exists. State the search and reasoning, and compensate with stronger oracle, invariant, or independent-reproduction evidence. Do not create a deliberately weak baseline.

## 4. Model-specific diagnostics

Select obligations from `model-family-routing.md`. The validation layer records why each diagnostic is needed and what claim it challenges; the routed specialist skill supplies method-level guidance.

At minimum, check:

- assumptions that can invalidate the selected model;
- data leakage, target leakage, look-ahead, grouping, or dependence where applicable;
- errors or failures hidden by aggregate performance;
- convergence, calibration, residual, feasibility, rank, or simulation diagnostics appropriate to the family;
- whether tuning, model selection, and final evaluation are separated;
- whether uncertainty and subgroup or scenario behavior affect the recommended decision.

Do not require diagnostics that do not apply merely to make a checklist look complete.

## 5. Sensitivity analysis

Sensitivity analysis asks how outputs and decisions respond to controlled changes in inputs, parameters, weights, thresholds, assumptions, or discretization choices.

Define:

- the parameter or assumption changed;
- the tested range and its source;
- whether changes are local, joint, structural, or scenario-based;
- the output metric and decision-change measure;
- the predeclared condition that would challenge a claim.

Prefer ranges grounded in measurement precision, confidence or credible intervals, historical ranges, physical bounds, rules, or documented scenarios. Label unsupported ranges as `scenario_assumption`. Report nonlinearity, threshold crossings, sign changes, rank changes, active-constraint changes, and untested regions. Do not interpret a single arbitrary ± percentage as global robustness.

## 6. Robustness analysis

Robustness asks whether performance and decisions persist across plausible sources of uncertainty or reasonable validation choices.

Choose applicable challenges:

- alternative legitimate data splits, grouped or rolling evaluation, and distribution shift;
- repeated seeds, resampling, or independent simulation replications;
- reasonable preprocessing, specification, solver, or stopping-rule alternatives;
- normal, stress, boundary, and extreme scenarios with documented meaning;
- missingness, noise, outliers, or measurement-error mechanisms;
- alternative optimal or near-optimal solutions and decision degeneracy;
- increased simulation or optimization budget to assess convergence stability.

Track both performance and the actual decision. Record failed runs, infeasible cases, switching points, and regions not tested. “No failure observed in the tested domain” is acceptable; “universally robust” is not.

## 7. Evidence lifecycle and claim binding

Record evidence through the following lifecycle:

1. Create the evidence item after an observation, derivation, or explicit assumption exists. Do not create placeholder results.
2. Bind the evidence to exactly one claim with `claim_id`, and list the evidence ID from that claim.
3. Bind the evidence to every gate for which it is used, in both the evidence and gate records.
4. Record whether it `supports`, `contradicts`, or is `neutral` toward the claim.
5. Keep it `active` while it participates in adjudication. Mark replaced evidence `superseded`, or evidence shown invalid `invalidated`; retain both for traceability.
6. Revalidate the complete manifest whenever a claim, evidence item, gate, limitation, or lifecycle state changes.

An `observed` item records a direct inspection or executed result. A `derived` item names all upstream evidence IDs and records its reproducible generation method. An `assumed` item records an input premise or scenario condition. A derived chain may include assumptions, but it supports a passing gate only when it has an observed ancestor; assumption-only support is conditional. Active evidence that supports and contradicts the same claim is an unresolved contradiction and must not be averaged away.

## 8. Conclusion stability

Map every core claim to the evidence capable of changing it. In schema v1.1, derive the assessment from active evidence rather than declaring it independently:

- `supported`: active, observed-supported evidence supports the claim without active contradiction;
- `conditional`: support depends on assumptions, non-observed ancestry, or low-confidence evidence;
- `contradicted`: active evidence contradicts the claim, including unresolved support-versus-contradiction conflicts;
- `unsupported`: no active supporting evidence is present.

Test the conclusion actually used in the paper or recommendation, not only a surrogate metric. Relevant decision changes include sign reversal, material error increase, loss of feasibility, selected-solution switching, Top-k or rank reversal, threshold reclassification, policy change, or failure of an asserted mechanism.

The `conclusion_stability` gate is derived from core-claim assessments: contradicted or unsupported means `fail`; conditional means `pass_with_limits`; otherwise it is `pass`. This one-way derivation prevents a declared gate outcome from manufacturing claim stability.

## 9. Verdict and stopping

Apply `evidence-verdict-schema.md` and the adjudication script. Do not average across gates.

- Return `FAIL` when schema/provenance/mapping validation fails, an applicable gate fails, a high-severity issue remains, a core claim is unsupported, or active evidence contradicts a core claim.
- Return `WARN` when hard checks pass but assumptions, low confidence, non-core evidence gaps, a non-full-pass gate, a medium/low issue, or a material limitation remains.
- Return `PASS` only when all applicable gates fully pass, all core claims have active observed-supported evidence, provenance is complete, no contradiction remains, and no warning condition is present.

The v1.1 engine also emits a lowercase `legacy_verdict` bridge for consumers that still use the four v1.0 states. After `FAIL` or `WARN`, recommend the smallest next action that can resolve the blocking failure or limitation. Do not silently broaden scope or compute budget.
