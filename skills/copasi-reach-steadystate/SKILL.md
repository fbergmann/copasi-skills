---
name: copasi-reach-steadystate
description: Diagnoses why an SBML (.xml/.sbml) or COPASI (.cps) model has no steady state and finds the smallest parameter or structural changes that give one, with copasi-basico. Use when run_steadystate fails (status 0), species grow without bound or deplete, or the user asks how to make a model reach steady state. Not for models that already have one (use copasi-steadystate).
license: BSD-2-Clause
compatibility: Requires Python 3.10+
metadata:
  author: "Frank T. Bergmann"
  version: "1.0"
---

# Bring a model to steady state

Requires the `.venv` from the `copasi-setup` skill. Start from `copasi-steadystate`; use this skill when it returns status 0.

## Inputs

Required: `model_file`.
Optional: `allow_structural` (default ask), `max_changes` (default 3), `output_file` (default `<model>_steadystate.cps`).

## Steps

1. Run `scripts/diagnose_steadystate.py <model_file> [--duration T]` with the venv Python. It reports the steady-state status from initial values and from the end of a long time course, a class per species, boundary fluxes, and the largest fluxes. Try `--duration` 10x larger once before concluding.
2. If the end-of-time-course status is 1 or 2, the model only needed a better starting point. Report that and stop.
3. Read the species classes:
   - `DRIFTING-UP` with a constant slope equal to a source flux: matter enters faster than it can leave (a capacity or sink problem, step 4a).
   - `DEPLETED` cofactor (ATP, NADH, ...): the cofactor is consumed with no regeneration (step 4b), or regenerated beyond use.
   - `OSCILLATING`: a limit cycle, which has no fixed point to reach; report it and ask whether another stable regime is wanted.
   - A species piling up behind a very slow step: a bottleneck (step 4c).
4. Find the cause with the model's own numbers (`basico.get_reaction_parameters()`, `basico.get_reactions()`):
   - a. Capacity: for each step compute the required flux from stoichiometry and the source flux (a step after a split carries a multiple of it), and compare with its maximum rate (`vf`, `vmax`). A required flux above the maximum rate can never be carried; lower the source or raise the rates along the path.
   - b. Cofactor balance: sum the net stoichiometry of a conserved pair (ATP/ADP, NAD+/NADH) over the pathway. A non-zero net with no sink or source of the pair means no steady state at positive flux; any such pair needs a consuming or regenerating reaction, which is a structural change. Parameters cannot fix an irreversible producer, since it stays positive.
   - c. Bottleneck: a reversible step whose maximum rate is orders of magnitude below its neighbours (e.g. a typo such as 3.2e-5 vs 0.1) caps the pathway flux.
5. Let an optimizer search for the changes with `scripts/optimize_to_steadystate.py <model_file> --flux <reaction> --min-flux <value> [--add-reaction "NAME|SCHEME|K1"] [--output file]`. It minimizes the sum of squared species rates (`{species.Rate}^2` terms) at the end of a time course while the flux of `<reaction>` stays above `<value>`, then reverts each parameter to its original value if the steady state survives, leaving the smallest set of changes. Pick the essential flux as an outflow or main pathway flux: without it the optimizer drives the source to zero, a trivial steady state. Set `--lower`/`--upper` to the scale of the model's rate constants.
   - If the script reports that the optimizer solution does not reach a steady state, a small objective was only a slow drift. Parameters alone cannot fix the model; add the missing structure (step 4b) with `--add-reaction`.
6. Alternatively, or to explain a result, try one change at a time. For each candidate reload the model, apply the change, run a long time course with `update_model=True`, then `basico.run_steadystate(update_model=True, use_initial_values=False)`. Parameters: `basico.set_reaction_parameters("(R).k", value=...)`; new reaction: `basico.add_reaction("ATPase", "ATP -> ADP")` followed by setting its `k1`. Keep a table of tried changes and their status.
7. Prefer parameter changes. Use structural changes (new reactions) only with `allow_structural` set, and tell the user they change what the model represents.
8. Write the fixed model with `basico.save_model(output_file)`, reload it, and confirm steady state there. Never overwrite the original.
9. Report the diagnosis, every change with old and new value, the steady-state concentrations and fluxes, and what did not work.

Done when all of these hold:
- The reloaded `output_file` gives status 1 or 2 with no negative concentrations.
- Source and sink fluxes agree with the stoichiometry (e.g. glucose influx 0.01 gives pyruvate efflux 0.02).
- The largest real Jacobian eigenvalue from `basico.get_jacobian_matrix()` is at most about 1e-9 (a zero from a conserved moiety is expected).
- Each change is shown to be needed, by a run without it that fails.

## Gotchas

- Run the steady-state task after a time course, from the end state (`use_initial_values=False`), and not from raw initial values; the solver often fails from far away.
- If decreasing the source alone fails, the cause is a cofactor or bottleneck, not capacity; do not keep lowering it.
- Values near the lower bound (1e-17) after a long run mean exhausted, not settling; read them as depleted.
- A status 3 (negative concentrations) result is a failure; discard it.
- Report untested ranges as untested (e.g. which source values between a failing and a working one work).
- Judge an optimizer result by `run_steadystate`, not by the objective: parameter-only runs on a model with an ATP surplus reached objectives of 1e-15 to 1e-29 and still had no steady state.
- The optimizer is stochastic (particle swarm); repeated runs give different solutions. Pruning removes most of the variation; rerun if the pruned set looks implausible.
- The minimum flux sets the scale of the solution: with `--min-flux 0.01` on a pathway whose outflow is twice the source, the source ends near 0.005.
