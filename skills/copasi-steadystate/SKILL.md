---
name: copasi-steadystate
description: Computes the steady state (equilibrium, fixed point) of an SBML (.xml/.sbml) or COPASI (.cps) model with copasi-basico and exports concentrations, fluxes, and optionally the Jacobian. Use when asked for steady-state values or whether a model has one. Not for trajectories or parameter fitting.
---

# Steady state of an SBML / COPASI model

Requires the `.venv` from the `copasi-setup` skill.

## Inputs

Required: `model_file`.

| Name | Default | Description |
|---|---|---|
| use_initial_values | false | Start from model initial values |
| update_model | true | Keep true; results are read back from the model |
| criterion | COPASI default | `Distance and Rate`, `Distance`, or `Rate` |
| settings | none | Format of `basico.get_task_settings` |
| include_jacobian | false | Also export the Jacobian |

## Steps

1. Check that `model_file` exists.
2. Load the model: `basico.load_model(model_file)`.
3. Run `status = basico.run_steadystate(update_model=True, use_initial_values=..., criterion=..., settings=...)`, passing only the options given.
4. Read the status code:
   - `0`: not found
   - `1`: steady state
   - `2`: equilibrium (all net fluxes zero)
   - `3`: found with negative concentrations
5. For status 1, 2, or 3, read `basico.get_species()`, `basico.get_parameters()`, and `basico.get_reactions()`. With `include_jacobian`, also read `basico.get_jacobian_matrix()`.
6. Write `species.to_csv("steadystate_species.csv")` and `reactions.to_csv("steadystate_reactions.csv")`, keeping the index because it holds the element names.
7. Report the status with its meaning, the files, and the values.

Done when all of these hold:
- The status is an integer, and it is 1 or 2 (3 is reported as a warning).
- Both CSVs exist and are non-empty.
- Values contain no NaN.
- Absolute species rates are near 0 for status 1 or 2.

## Gotchas

- Status 0: present no results. Retry with `use_initial_values` toggled, another `criterion`, or a time course first to approach the steady state. If it still fails, report that none was found; the model may oscillate, be chaotic (Lorenz-type systems have only unstable fixed points), or grow unboundedly.
- Status 3: values are non-physical; warn and do not present them as a valid biological steady state.
- A found steady state may be unstable. If stability matters, export the Jacobian and check that all eigenvalue real parts are negative.
- Events and assignments are ignored; only the continuous dynamics count.
- `update_model=False` resets the model, so read-back returns initial values.
