---
name: copasi-model-values
description: Inspects or changes existing values in an SBML (.xml/.sbml) or COPASI (.cps) model with copasi-basico. Use when reading or setting initial or current values of global quantities, species, or compartments. Not for structural model edits, simulation, steady-state analysis, fitting, optimization, parameter sweeps, or evaluating objective functions.
license: BSD-2-Clause
compatibility: Requires Python 3.10+
metadata:
  author: "Frank T. Bergmann"
  version: "1.0"
---

# Inspecting and changing COPASI model values

Requires the `.venv` from `copasi-setup`. This skill changes values of existing model objects; it does not change model structure or equations. Load the exact model the user named. Keep edits in memory unless the user explicitly asks to save model changes.

## Workflow

1. Confirm the model file exists, then load it with `basico.load_model(model_file)`.
2. Inspect the relevant model table before changing anything. Use `basico.get_parameters()` for global quantities, `basico.get_species()` for species, and `basico.get_compartments()` for compartments. Prefer the exact `display_name` present in the loaded model. The forms below are examples of valid COPASI display names, not a promise that every model has every reference.
3. Check the element's type and meaning. Values with assignment or ODE status are determined by their defining expression or dynamics; setting them will generally fail. Do not try to set them or change their expressions/statuses as part of a value edit. Fluxes, rates, and model time are read-only.
4. Read the selected value with `basico.get_value(display_name, initial=True)` for its initial value, or `initial=False` for its current value. Record which reference is being changed so the result is unambiguous.
5. Set the requested value with `basico.set_value(display_name, new_value, initial=True)` for an initial value, or `initial=False` for a current value. `set_value` returns `None` on success as well as on lookup failure. Always read the same reference back and compare it with the requested value. If the read returns `None` or differs, stop and re-check the display name, reference, and whether the object is writable.
6. Keep changes in memory by default. If the user explicitly asks to persist them, save to a separate output path with `basico.save_model(output_path)`, then reload that file and verify the requested values. Replace the source file only when explicitly requested.

## Verified example: Himmelblau model

The display names below are specific to `HimmelblauFunction.cps`; discover names from each target model rather than reusing them.

```python
from basico import get_value, load_model, set_value

load_model("HimmelblauFunction.cps")
assert get_value("Values[x1]", initial=True) == 0.0
set_value("Values[x1]", 3.0, initial=True)
assert get_value("Values[x1]", initial=True) == 3.0
```

The `set_value` call returning `None` is expected; the read-back is the success check. For this model, `x1` and `Values[x1].InitialValue` are not the display names accepted by these generic APIs.

## Display-name reference

These are possible COPASI display names. Availability depends on the loaded model and the object/reference it defines. Use only names present for that model.

| Display name | Meaning | Access |
|---|---|---|
| `Time` | Model time | Read-only |
| `D3.ParticleNumber` | Particle number of metabolite `D3` | Read; set only if the model exposes it as an independent writable value |
| `I2.InitialParticleNumber` | Initial particle number of metabolite `I2` | Read; set only if the model exposes it as an independent writable value |
| `R3.Rate` | Concentration rate of metabolite `R3` | Read-only |
| `V.ParticleNumberRate` | Particle-number rate of metabolite `V` | Read-only |
| `[I]_0` | Initial concentration of metabolite `I` | Read; set only if the species is independently writable |
| `[T]` | Current concentration of metabolite `T` | Read; set only if the species is independently writable |
| `Values[alpha]` | Value of parameter `alpha` | Read; set only if the parameter is independent and writable |
| `Values[alpha_pop].InitialValue` | Initial value of parameter `alpha_pop` | Read; set only if the parameter is independent and writable |
| `Values[beta].Rate` | Rate of change of parameter `beta` | Read-only |
| `Compartments[compartment].InitialVolume` | Initial volume of a compartment | Read; set only if the compartment is independent and writable |
| `Compartments[compartment].Rate` | Rate of change of compartment volume | Read-only |
| `Compartments[compartment].Volume` | Current compartment volume | Read; set only if the compartment is independent and writable |
| `(contagion_A).Flux` | Flux of reaction `contagion_A` | Read-only |
| `(contagion_A).ParticleFlux` | Particle flux of reaction `contagion_A` | Read-only |
| `(R1).k1` | Local parameter `k1` of reaction `R1` | Read; set only if the parameter is independent and writable |

## Gotchas

- An unknown display name can make `get_value` return `None`; inspect `get_parameters()` or `get_species()` and use the matching `display_name`.
- `initial=True` selects the initial-value reference; it does not make an assignment value independently writable.
- A value with assignment or ODE status is not a valid write target; change an independent value only when requested and when doing so does not change model structure.
- Model time, reaction fluxes, particle fluxes, and rate references are read-only. Do not pass them to `set_value`.
- Assignment values are derived from expressions. Edit an independent input only when that input is the requested value; this skill does not evaluate objectives or other derived results.
- Parameter-table APIs and generic `get_value`/`set_value` APIs can accept different name forms. Follow the API-specific documentation and verify changes rather than assuming one naming convention works everywhere.

## Completion checks

- Each requested value was changed through the intended initial or current reference and read back successfully.
- Assignment values and model structure were not directly modified.
- The source model remains unchanged unless persistence was explicitly requested; persisted output was reloaded and checked.