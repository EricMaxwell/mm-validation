# Model-Family Obligations and Skill Routing

This reference defines minimum validation obligations, not implementations. Load only the specialist skills relevant to the current model and installed in the environment. If a required capability is unavailable, record the gap and do not pretend the check was completed.

## Routing matrix

| Family | Minimum diagnostic obligations | Baseline candidates | Primary skill routing |
|---|---|---|---|
| Prediction and time series | chronological or grouped leakage boundary; rolling or external holdout where applicable; residual dependence; interval coverage or uncertainty; horizon-specific error; drift and regime behavior | naive persistence, seasonal naive, historical mean, or current operational forecast under the same horizon | `statsmodels` for time-series structure and residual diagnostics; `scikit-learn` for pipeline-based predictive evaluation; `statistical-analysis` for uncertainty or comparison design |
| Regression | functional-form and outcome alignment; residual structure; heteroskedasticity; dependence; multicollinearity; influential cases; out-of-sample behavior; inference versus prediction distinction | intercept-only, simple domain model, reduced specification, or incumbent method using identical data and target | `statsmodels` for regression inference and diagnostics; `statistical-analysis` for test choice, uncertainty, and effect interpretation; `scikit-learn` when prediction is the goal |
| Classification | split strategy; class and subgroup representation; confusion structure; calibration; threshold and cost sensitivity; imbalance; leakage; tuning/evaluation separation | majority or stratified dummy, simple logistic or rule baseline, or incumbent classifier under the same threshold policy | `scikit-learn` for pipelines, cross-validation, metrics, calibration, and threshold evaluation; `statsmodels` for inferential logistic models; `statistical-analysis` for uncertainty and group comparisons |
| Optimization | objective and constraint recomputation; variable domains; feasibility; solver status; hand-checkable or exhaustive small case; incumbent heuristic or alternative solver; seed and budget convergence; alternative optima; decision stability | feasible greedy or rule solution, incumbent plan, relaxation, exact small instance, or alternative algorithm under equivalent evaluation budget | `pymoo` for evolutionary, constrained, Pareto, and MCDM mechanics; use the actual solver’s documented checks for non-pymoo models; `statistical-analysis` for repeated-run comparison when needed |
| Evaluation and ranking | indicator direction and units; normalization; weight provenance; consistency requirements; missing and tied values; dominance and compensation behavior; rank reversal; Top-k stability; weight and threshold sensitivity | equal weights, single transparent indicator, unweighted rank, incumbent rubric, or another justified weighting scheme | `pymoo` only for applicable Pareto/MCDM workflows; `statistical-analysis` for uncertainty or rank comparisons; `scientific-critical-thinking` for construct validity and unsupported weighting claims |
| Simulation | state-update correctness; invariants or conservation; simplified or analytical case; initialization and boundary conditions; replication seeds; Monte Carlo or trajectory convergence; calibration or backtesting when observations exist; scenario and discretization sensitivity | analytical or limiting case, deterministic version, coarse model, historical observation, or current operational simulation | `statistical-analysis` for replication and uncertainty design; `scientific-critical-thinking` for mechanism and claim validity; `scientific-visualization` only for truthful display of actual trajectories and uncertainty |

For hybrid models, validate each component and every interface that transports data, parameters, uncertainty, or decisions between components. A component passing alone does not validate the assembled chain.

## Cross-cutting routes

- Use `scientific-critical-thinking` when the main risk is construct validity, unsupported causal language, confounding, proxy outcomes, or unjustified generalization. It evaluates the claim; it does not run the computational model.
- Use `scientific-visualization` only after real validation outputs exist and a figure materially improves inspection or communication. Pass the data provenance, missingness, uncertainty definition, and tested domain. A plot is not validation evidence by itself.
- Do not invoke `peer-review` as a routine validation dependency. Use it only for an explicitly requested, authorized manuscript or proposal review under its confidentiality rules.
- When `mathmodel-skill` is active, it remains the host workflow. Follow `mathmodel-integration.md`.

## Family-specific conclusion stability

### Prediction and regression

Track whether the claimed direction, magnitude, forecast ordering, usable horizon, interval reliability, or downstream decision survives the executed checks. A small average error does not establish stability for every horizon or subgroup.

### Classification

Track whether the selected threshold, class-specific error, subgroup behavior, calibration, and decision cost support the stated use. A ranking metric alone does not validate a deployed threshold decision.

### Optimization

Track feasibility, objective value, decision variables, active constraints, Pareto choice, and near-optimal alternatives. Objective stability does not imply decision stability, and a solver termination message does not prove global optimality.

### Evaluation and ranking

Track complete ranking, Top-k membership, ties, dominance violations, and the recommended selection. Weight stability must be assessed against plausible preference changes rather than arbitrary perturbations.

### Simulation

Track the mechanism-dependent conclusion, distribution or trajectory summaries, boundary events, tail outcomes, and policy decisions. More replications reduce Monte Carlo error but do not repair a wrong mechanism or uncalibrated structure.
