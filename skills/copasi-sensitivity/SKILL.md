---
name: copasi-sensitivity
description: Runs a sensitivity analysis of an SBML (.xml/.sbml) or COPASI (.cps) model with copasi-basico, reporting how chosen effects (concentrations, fluxes, steady state, time series) respond to parameter or initial-value changes, scaled and unscaled. Use when asked which parameters most influence a result, or for sensitivities or control coefficients. Not for fitting or simulation.
license: BSD-2-Clause
compatibility: Requires Python 3.10+
metadata:
  author: "Frank T. Bergmann"
  version: "1.0"
---

# Sensitivity analysis of an SBML / COPASI model

Requires the `.venv` from the `copasi-setup` skill. Reference: https://basico.readthedocs.io/en/latest/notebooks/Sensitivity_Analysis.html

## Inputs

Required: `model_file`.

| Name | Default | Description |
|---|---|---|
| sub_task | Steady State | Task evaluated: `Evaluation`, `Steady State`, `Time Series`, `Parameter Estimation`, `Optimization`, `Cross Section`. Constants are in `SENS_ST` |
| effect | Non-Constant Concentrations of Species | Observed element: a display name, a CN, or a `SENS` constant |
| cause | All Parameter Values | Element varied: a display name (e.g. `[A]_0`), a CN, or a `SENS` constant |
| secondary_cause | Not Set | Second varied element, for second-order sensitivities |
| method | basico defaults | e.g. `{"Delta factor": 0.001, "Delta minimum": 1e-12}` |

## Steps

1. Check that the model file exists.
2. Load the model: `from basico import *; load_model(model_file)`.
3. Inspect the current settings with `get_sensitivity_settings()` and the available names with `get_reactions()`, `get_species()`, and `get_parameters()`.
4. Set the analysis: `set_sensitivity_settings(settings={"sub_task": SENS_ST.STEADY_STATE, "effect": "[X]", "cause": "[A]_0"})`. Omit anything left at its default.
5. Run `run_sensitivities()`. A single call such as `get_scaled_sensitivities(run_first=True, settings={...})` also runs it, and the settings persist afterwards.
6. Read the results:
   - `get_scaled_sensitivities()`: dimensionless, comparable across parameters (use this for ranking).
   - `get_unscaled_sensitivities()`: raw derivatives.
   - `get_summarized_sensitivities()`: one aggregate value per cause.
7. Write `sensitivities_scaled.csv`, `sensitivities_unscaled.csv`, and `sensitivities_summary.csv` with `to_csv(...)`, keeping the index. A single value (not a table) is reported as text.
8. Report the settings used, the parameters ranked by absolute scaled sensitivity (top five at least), and the files.

Done when all of these hold:
- A status check showed that steady state was reached, for a `Steady State` subtask (run `run_steadystate()` first; status 0 means the results are invalid).
- Result tables are non-empty and contain no NaN.
- The settings reported match `get_sensitivity_settings()`.
- The CSV files exist.

## Gotchas

- The settings persist across runs and are written to the model, so reset `cause`, `effect`, and `secondary_cause` explicitly when changing the question.
- For a `Steady State` subtask on a model without a steady state (oscillating, chaotic, unbounded), the sensitivities are not meaningful; report that and stop.
- A large absolute value means the effect is highly sensitive to that parameter. Check the sign: positive increases the effect, negative decreases it.
- If a specific cause or effect name is not found, list the model's names and ask or suggest the closest match.
- Scaled values are relative changes and independent of units; compare unscaled values only within one effect.
- `update_model` stays `False` by default, so the model's values are not changed.
