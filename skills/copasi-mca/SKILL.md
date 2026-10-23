---
name: copasi-mca
description: Runs metabolic control analysis of an SBML (.xml/.sbml) or COPASI (.cps) model with copasi-basico, giving elasticities and concentration and flux control coefficients at steady state. Use when asked which reactions control a flux or concentration, or for control coefficients or elasticities. Not for sensitivities to parameters (use copasi-sensitivity).
---

# Metabolic control analysis of an SBML / COPASI model

Requires the `.venv` from the `copasi-setup` skill. Reference: https://basico.readthedocs.io/en/latest/notebooks/MCA.html

## Inputs

Required: `model_file`.

| Name | Default | Description |
|---|---|---|
| scaled | true | Scaled (dimensionless) or unscaled coefficients |
| use_initial_values | false | Start the steady-state search from the initial values |
| update_model | false | Whether the task updates the model state |

## Steps

1. Check that the model file exists.
2. Load the model: `from basico import *; load_model(model_file)`.
3. Run `run_mca()` once. All matrices are then available. Alternatively, pass `run_first=True` to the first getter only.
4. Read:
   - `get_elasticities(scaled=...)`: effect of species concentrations on reaction rates; always available.
   - `get_concentration_control_coefficients(scaled=...)`: effect of reaction rates on steady-state concentrations.
   - `get_flux_control_coefficients(scaled=...)`: effect of reaction rates on steady-state fluxes.
5. Write `mca_elasticities.csv`, `mca_concentration_control.csv`, and `mca_flux_control.csv` with `to_csv(...)`, keeping the index.
6. Report the reactions ranked by absolute flux control coefficient for each flux, the summation-theorem check, and the files.

Done when all of these hold:
- A steady state was found (check `run_steadystate()` status 1 or 2), so both control tables exist.
- Concentration control rows sum to 0 and flux control rows sum to 1, with the `Summation Error` column near 0 (scaled results).
- No NaN in the tables.
- The CSV files exist and are non-empty.

## Gotchas

- Control coefficients exist only at a steady state. If none is found (oscillating, chaotic, unbounded), report that only elasticities are valid and stop.
- Reactions and species are the row and column names: `(R1)` for reactions, `X` for species.
- A `Summation Error` far from 0 means the steady state is not converged; rerun with `use_initial_values` toggled or a time course first.
- Scaled coefficients compare across reactions; unscaled depend on units.
- A negative flux control coefficient means that increasing that reaction's rate lowers the flux.
