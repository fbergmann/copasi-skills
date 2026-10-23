---
name: copasi-timecourse
description: Simulates the time course of an SBML (.xml/.sbml) or COPASI (.cps) model with copasi-basico, deterministic or stochastic, and exports the trajectory to CSV. Use when asked to simulate, run, or get dynamics of species, parameters, fluxes, or rates over time. Not for steady state or parameter fitting.
---

# Time course of an SBML / COPASI model

Requires the `.venv` from the `copasi-setup` skill.

## Inputs

Required: `model_file`, `start_time`, `end_time`.

Optional (basico keyword arguments of the same name unless noted):

| Name | Default | Description |
|---|---|---|
| output_selection | none | Display names or CNs to report (list) |
| intervals | 1000 | Output intervals |
| method | deterministic | One of `deterministic`, `lsoda`, `stochastic`, `directMethod`, `hybrid`, `hybridode45`, `hybridlsoda`, `adaptivesa`, `tauleap`, `radau5`, `sde` |
| use_initial_values | false | Start from model initial values |
| update_model | false | Simulation updates the model state |
| seed, use_seed | none, false | Reproducible stochastic runs |
| automatic, output_event, values, stepsize | none | Alter the output points |
| a_tol, r_tol, max_steps | none | Integrator settings |

## Steps

1. Check that `model_file` exists and `end_time > start_time`; otherwise stop and ask.
2. Load the model: `basico.load_model(model_file)`.
3. Pass `duration = end_time - start_time`, never `end_time`.
4. With `output_selection`, call `basico.run_time_course_with_output(output_selection, start_time=..., duration=..., intervals=..., method=...)`. Otherwise call `basico.run_time_course(start_time=..., duration=..., intervals=..., method=...)`. Forward any other given optional inputs as keyword arguments.
5. Call `result = result.reset_index()` when `Time` is the index, so `Time` is an explicit column, then write `result.to_csv("simulation_results.csv", index=False)`.
6. Report the file, row count, columns, and method used.

Done when all of these hold:
- The CSV exists and is non-empty, with `Time` as its first column.
- Rows equal `intervals + 1`, unless `values`, `stepsize`, `automatic`, or `output_event` change the output points.
- The first `Time` is `start_time` and the last is `end_time`.
- Every `output_selection` entry is a column.
- No NaN or infinite values, or they are reported with where they first occur.

## Gotchas

- Names: species are `[X]`, global parameters `Values[X]`, fluxes `(reaction).Flux`, species rates are `X.Rate`. For an unknown name, list `basico.get_species()`, `get_parameters()`, `get_reactions()` and ask or suggest the closest match.
- Unsupported method: use `deterministic` and tell the user.
- Stiff, chaotic, or slow runs: try `radau5` or `lsoda`, tighten `a_tol`/`r_tol`, or raise `max_steps`.
- Stochastic methods: set `use_seed=True` with `seed` for reproducibility.
- Load failure: report the error and stop; do not substitute another model.
