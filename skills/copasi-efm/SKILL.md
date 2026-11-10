---
name: copasi-efm
description: Computes the elementary flux modes of an SBML (.xml/.sbml) or COPASI (.cps) model with copasi-basico, giving each minimal steady-state reaction set with its coefficients, reversibility, net conversion, and balanced internal species. Use when asked for elementary modes, minimal pathways, futile cycles, or which reaction combinations can carry a steady-state flux. Not for computing a steady state (use copasi-steadystate).
license: BSD-2-Clause
compatibility: Requires Python 3.10+
metadata:
  author: "Frank T. Bergmann"
  version: "1.0"
---

# Elementary flux modes of an SBML / COPASI model

Requires the `.venv` from the `copasi-setup` skill. Reference: https://basico.readthedocs.io/en/latest/notebooks/ComputeElementaryModes.html

## Inputs

Required: `model_file`.

## Steps

1. Check that `model_file` exists.
2. Load the model: `basico.load_model(model_file)`. Fixed species (boundary) and reaction stoichiometry define the network, so check `basico.get_reactions()[["scheme"]]` first.
3. Run `modes = basico.get_elementary_flux_modes()`. It compiles the model, runs the task, and returns one dict per mode with the keys `index`, `reaction_name`, `reversible`, `net_reaction`, `internal_species`. `reaction_name` is a list of strings `"<coefficient> * <reaction>"`.
4. Build a table with one row per mode: split each `reaction_name` entry into coefficient and reaction, and join them as `reactions`. Write it with `pandas.DataFrame(...).to_csv("efm_modes.csv", index=False)`.
5. Classify every mode:
   - `net_reaction` empty (` -> `): a futile cycle, with no net conversion of boundary species.
   - `net_reaction` non-empty: a pathway that converts boundary species, e.g. `A -> E` or `2 * NAD+ -> 2 * NADH`.
   - `reversible` True: the mode can run in both directions.
6. Report the number of modes, the modes grouped by class, and for each pathway its reactions, coefficients, and net reaction. State which reactions appear in no mode.

Done when all of these hold:
- The mode count and the CSV rows agree.
- Every reaction named in a mode is a reaction of the model (`basico.get_reactions().index`).
- Every mode is classified and reported with its net reaction.

## Gotchas

- Any steady-state flux is a non-negative combination of the irreversible modes (a signed one for reversible ones); a negative coefficient on a reaction means it runs backwards in that mode.
- Fixed species (the boundary) never count as internal; they appear only in `net_reaction`. If a species you expect in a mode is missing, check that it is not set to `fixed`.
- Futile cycles are expected whenever a reaction and its reverse both exist as separate reactions (for example two reactions converting the same pair of metabolites in opposite directions).
- A reaction that appears in no mode cannot carry a steady-state flux; it points to a dead end or a missing source or sink in the model, which `copasi-reach-steadystate` can diagnose.
- The number of modes can grow very fast with network size; for large models expect long run times and many modes, and report the count before listing all of them.
- This task needs no settings; the model is compiled each time, so run it after changing reactions.
