---
name: copasi-optimization
description: Optimizes parameters of an SBML (.xml/.sbml) or COPASI (.cps) model with copasi-basico, minimizing or maximizing an objective by varying parameters within bounds, with optional constraints. Use when asked to minimize, maximize, or fit model quantities. Not for plain simulation or steady state.
license: BSD-2-Clause
---

# Parameter optimization of an SBML / COPASI model

Requires the `.venv` from the `copasi-setup` skill. Reference: https://basico.readthedocs.io/en/latest/notebooks/Optimization.html

## Inputs

Required:
- `model_file`
- `objective_function`: expression of model elements, e.g. `Values[f].InitialValue`
- `parameters`: list of `{name, lower, upper, start?}`

| Name | Default | Description |
|---|---|---|
| minimize | true | false to maximize |
| method | Levenberg - Marquardt | A `PE.` constant: `CURRENT_SOLUTION`, `RANDOM_SEARCH`, `SIMULATED_ANNEALING`, `DIFFERENTIAL_EVOLUTION`, `SCATTER_SEARCH`, `GENETIC_ALGORITHM`, `EVOLUTIONARY_PROGRAMMING`, `GENETIC_ALGORITHM_SR`, `EVOLUTIONARY_STRATEGY_SRES`, `PARTICLE_SWARM`, `LEVENBERG_MARQUARDT`, `HOOKE_JEEVES`, `NELDER_MEAD`, `STEEPEST_DESCENT`, `NL2SOL`, `PRAXIS`, `TRUNCATED_NEWTON` |
| method_settings | method defaults | e.g. `{"Iteration Limit": 2000, "Tolerance": 1e-6}` |
| subtask | Time-Course | Task evaluated for the objective (`T.` constant) |
| constraints | none | List of `{name, lower, upper}` |
| output | none | Extra real-valued CNs collected each iteration |
| update_model | false | Write the optimum back into the model |
| use_template | false | If `parameters` is omitted, use all globals via `get_opt_item_template(include_global=True, default_lb=...)` |

## Steps

1. Check that the model file exists and every parameter has `lower < upper`, with `start` inside the bounds.
2. Load the model: `from basico import *; load_model(model_file)`.
3. `set_opt_parameters([{"name": "Values[x].InitialValue", "lower": -1, "upper": 1000, "start": 0.0}, ...])`
4. `set_objective_function(expression="Values[f].InitialValue", minimize=True)`
5. `set_opt_settings(settings={"subtask": T.TIME_COURSE, "method": {"name": PE.LEVENBERG_MARQUARDT, "Iteration Limit": 2000, "Tolerance": 1e-6}})`
6. With constraints: `set_opt_constraints([{"name": "Values[f]", "lower": 170, "upper": 200}])`
7. Verify the setup with `get_opt_parameters()`, `get_opt_settings()`, and `get_opt_constraints()`.
8. `solution = run_optimization()`. It returns a data frame with `lower`, `upper`, `sol`.
   - For a one-off override, edit `settings = get_opt_settings()` (e.g. `settings["problem"]["Maximize"] = True`) and call `run_optimization(settings=settings)`.
   - To collect per-iteration values, pass `output=[...]`; it then returns that history table instead.
9. `stats = get_opt_statistic()` and `solution.to_csv("optimization_results.csv")`, keeping the index because it holds the parameter names.
10. Report best parameters, objective, statistics, file, and method.

Done when all of these hold:
- `sol` has one value per requested parameter, each within its bounds.
- `stats["obj"]` is reported and better than the objective at the start values.
- Constraints, if any, are satisfied by the final values.
- The CSV exists and is non-empty.

## Gotchas

- For direct edits to existing model values outside the optimizer, use `copasi-model-values` to resolve display names and verify the requested initial or current value.
- Gradient-based methods (Levenberg - Marquardt, Steepest Descent, Truncated Newton) can stick in local optima. Rerun with other `start` values or a global method (Particle Swarm, Differential Evolution, SRES), then refine locally.
- A solution on a bound means the bounds may be too tight; suggest widening them.
- High `failed_evals_exception` or `failed_evals_nan`: tighten bounds or change start values or the subtask.
- If constraints stop the search from converging, relax or remove them and retry.
- Unknown method: use `Levenberg - Marquardt` and tell the user.
- Missing `parameters`: use the template and state that to the user.
- Unknown element names: list `get_parameters()` and `get_species()` and ask.
- Custom `output` accepts only real-valued CNs.
- The model keeps its original values unless `update_model` is true.
