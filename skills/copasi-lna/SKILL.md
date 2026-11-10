---
name: copasi-lna
description: Computes the Linear Noise Approximation (LNA) for an SBML (.xml/.sbml) or COPASI (.cps) model with copasi-basico, returning covariance and reduced matrices for fluctuations around a steady state. Use when asked for linear-noise approximation, intrinsic fluctuation covariance, or LNA matrices. Not for stochastic trajectories, parameter sensitivities, or metabolic control analysis.
license: BSD-2-Clause
compatibility: Requires Python 3.10+
metadata:
  author: "Frank T. Bergmann"
  version: "1.0"
---

# Linear Noise Approximation for an SBML / COPASI model

Requires the `.venv` from `copasi-setup`. Reference: https://basico.readthedocs.io/en/latest/notebooks/LinearNoiseApproximation.html

## Inputs

Required: `model_file` (`.cps`, `.xml`, or `.sbml`).

## Steps

1. Check that `model_file` exists and `basico` is available in `.venv`.
2. Load the exact model: `basico.load_model(model_file)`.
3. Run `status, covariance, reduced_covariance, reduced_b = basico.run_lna(return_results=True)`. `return_results=True` returns the full result tuple; without it, `run_lna()` returns only the task status. Alternatively, run `basico.run_lna()` and retrieve the outputs with `get_lna_status()`, `get_lna_covariance_matrix()`, `get_lna_reduced_covariance_matrix()`, and `get_lna_reduced_b_matrix()`.
4. Verify that the status indicates a steady state was found before interpreting the matrices. If it does not, report the status and stop; do not report stale matrices as current results.
5. Save the three matrices as `lna_covariance.csv`, `lna_reduced_covariance.csv`, and `lna_reduced_b.csv`, using each DataFrame's `to_csv(...)` with its index.
6. Report the status, model, and files. Summarize the covariance matrix by naming the species with the largest diagonal variances and strongest absolute off-diagonal covariances, retaining units and signs where available.

## Completion checks

- The model file and result status are reported, and the status confirms the LNA run found a steady state.
- All three matrices are non-empty, contain no NaN, and are exported with row and column labels.
- The covariance matrix is symmetric within numerical tolerance; flag any material asymmetry rather than silently correcting it.
- The three CSV files exist and are non-empty.

## Gotchas

- LNA describes local fluctuations around a steady state; it is not a stochastic time course and does not describe large deviations or switching between states.
- A steady state is required. If the task fails to find one, the covariance results are not valid for interpretation. A limit cycle or chaotic trajectory is not represented by this steady-state approximation.
- `run_lna()` returns only task status by default. Use `return_results=True` or the getters to obtain matrices, and check the status before using them.
- The reduced covariance and reduced B matrices are COPASI's reduced representations. Keep their names and labels when exporting; do not present them as the full species covariance matrix.
- Do not modify or save the source model unless explicitly requested.