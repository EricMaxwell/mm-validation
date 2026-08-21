# Contest-Grade Validation Protocol

Use this protocol after a model has an executable or otherwise inspectable implementation. Validation is claim-centered: every check must challenge a stated competition conclusion, an implementation invariant, or a known failure mode.

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

## 7. Conclusion stability

Map every core claim to the evidence capable of changing it. Classify each claim:

- `stable`: the claim remains supported over its declared validation domain;
- `conditional`: it holds only under explicitly recorded conditions or material limits;
- `unstable`: an executed validation contradicts or reverses it;
- `untested`: required evidence is missing or not reproducible.

Test the conclusion actually used in the paper or recommendation, not only a surrogate metric. Relevant decision changes include sign reversal, material error increase, loss of feasibility, selected-solution switching, Top-k or rank reversal, threshold reclassification, policy change, or failure of an asserted mechanism.

## 8. Verdict and stopping

Apply `evidence-verdict-schema.md` and the adjudication script. Do not average across gates.

- Stop and return `fail` when implementation correctness fails or executed evidence invalidates a core claim.
- Return `inconclusive` when required evidence is missing, unavailable, unsupported by provenance, or not reproducible.
- Return `pass_with_limits` when all required gates are supported but a claim is conditional or a material limitation remains.
- Return `pass` only when all applicable gates and core claims are supported without unresolved material limits.

After a fail or inconclusive result, recommend the smallest next action that can resolve the blocking evidence gap. Do not silently broaden scope or compute budget.
