---
name: copasi-parameter-estimation
description: Fits parameters of an SBML (.xml/.sbml) or COPASI (.cps) model to experimental data with copasi-basico, using time-course or steady-state data, multiple experiments, and optional constraints. Use when asked to estimate, fit, or calibrate parameters against measured data. Not for optimizing an objective without data (use copasi-optimization).
---

# Parameter estimation of an SBML / COPASI model

Requires the `.venv` from the `copasi-setup` skill. References: https://basico.readthedocs.io/en/latest/notebooks/Setting_up_Parameter_Estimation.html and https://basico.readthedocs.io/en/latest/notebooks/Parameter_Estimation_Example.html

## Inputs

Required:
- `model_file`
- `data`: one or more experiment tables (CSV paths or data frames), each with a `Time` column for time-course data. Other columns are mapped by name (see step 4).
- `parameters`: list of `{name, lower, upper, start?, affected?}`. `affected` is a list of experiment names; empty means all.

| Name | Default | Description |
|---|---|---|
| method | Levenberg - Marquardt | Global: `Random Search`, `Simulated Annealing`, `Differential Evolution`, `Scatter Search`, `Genetic Algorithm`, `Evolutionary Programming`, `Genetic Algorithm SR`, `Evolution Strategy (SRES)`, `Particle Swarm`. Local: `Levenberg - Marquardt`, `Hooke & Jeeves`, `Nelder - Mead`, `Steepest Descent`, `NL2SOL`, `Praxis`, `Truncated Newton`. `Statistics` evaluates the current fit without changing it |
| experiment_names | file/frame names | Name per data set |
| experiment_type | Time Course | `Time Course` or `Steady State` |
| constraints | none | List of `{name, lower, upper}` |
| update_model | true | Write the estimate back into the model |
| plot | true | Save fit plots |

If the `.cps` file already has estimation set up, skip steps 3 to 5 and inspect it with `get_fit_parameters()`, `get_experiment_names()`, and `get_experiment_mapping(name)`.

## Steps

1. Check that the model and data files exist, every parameter has `lower < upper`, and each data set has a `Time` column.
2. Load the model: `from basico import *; load_model(model_file)`.
3. Prepare each data set as a data frame whose columns are named after the model elements they map to: `Time`, species as `[X]`, global parameters as `Values[X]`, and independent (per-experiment initial-value) columns as `[X]_0`. Call `reset_index()` so `Time` is a column. Add each with `add_experiment(name, data)`.
4. Verify the mapping: `get_experiment_mapping(name)` must show `time`, `dependent`, and, where used, `independent` for the intended columns. For unmapped columns, fix the column names and re-add the experiment.
5. Set the fit items with `set_fit_parameters([{"name": "(R1).k1", "lower": 0.001, "upper": 2}, ...])` and verify them with `get_fit_parameters()`. Add constraints with `set_fit_constraints([{"name": "Y", "lower": 0, "upper": 10}])` if given.
6. Evaluate the starting fit with `run_parameter_estimation(method="Statistics")`, then `get_fit_statistic()`.
7. Run the estimation: `solution = run_parameter_estimation(method=method, update_model=True)`. It returns a data frame with `lower`, `upper`, `sol`, `affected`; `get_parameters_solution()` returns the last one.
8. Read `stats = get_fit_statistic()`. Fields: `obj`, `rms`, `sd`, `f_evals`, `failed_evals_exception`, `failed_evals_nan`, `constraint_evals`, `failed_constraint_evals`, `data_points`, `valid_data_points`, `cpu_time`.
9. Export `solution.to_csv("estimation_results.csv")` and, for the fit, `exp, sim = get_simulation_results()`, saving each pair to CSV. Keep the index.
10. With `plot`, call `plot_per_dependent_variable()` and `plot_per_experiment()` and save the figures.
11. Report the estimated parameters with bounds, `obj` and `rms`, the starting versus final `obj`, the files, and the method.

Done when all of these hold:
- `sol` has one value per fit item, and each lies within its bounds.
- Final `obj` is lower than the `Statistics` value from step 6.
- `valid_data_points` equals `data_points`, and `failed_constraint_evals` is 0.
- `estimation_results.csv` exists and is non-empty.

## Gotchas

- A column that is mapped wrongly is silently ignored, so always check the mapping in step 4. `get_experiment_data_from_model()` and `get_data_from_experiment(name)` return the data basico actually uses.
- `add_experiment` writes a text file next to the model (e.g. `exp1.txt`); mention it and delete it on request.
- Names: reaction-local parameters are `(R1).k1`; globals are `Values[X]`; species are `[X]`.
- A parameter that applies to one experiment only needs `affected` set, e.g. a per-experiment offset.
- A solution on a bound means the bounds may be too tight; widen them and rerun.
- Local methods can stick in local optima. Run a global method first (`Evolution Strategy (SRES)`, `Particle Swarm`), then refine with `Levenberg - Marquardt`.
- High `failed_evals_*` or `failed_constraint_evals`: loosen the constraint bounds (a too-narrow constraint rejects valid solutions), tighten parameter bounds, or change start values.
- Poorly identifiable parameters (hitting both bounds across runs, or large `sd`) should be flagged to the user as not determined by the data.
- Use `update_model=False` to keep the model's original values.
