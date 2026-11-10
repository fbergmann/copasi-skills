---
name: copasi-parameter-estimation-evaluation
description: Evaluates a finished parameter estimation of a COPASI (.cps) or SBML model with copasi-basico, running the current-solution statistics with calculate statistics enabled and analysing the fit statistic, correlation matrix, and Fisher information matrix (eigenvalues, condition number). Flags parameters on bounds, parameters with no effect on the fit, and residual bias; if the Fisher matrix is singular, suggests which fit parameter to drop and can refit without it. Use when asked whether a fit is identifiable, how well parameters are determined, or to check correlations or parameter uncertainty. Not for running the first fit (use copasi-parameter-estimation).
license: BSD-2-Clause
compatibility: Requires Python 3.10+
metadata:
  author: "Frank T. Bergmann"
  version: "1.0"
---

# Evaluating parameter estimation results

Requires the `.venv` from the `copasi-setup` skill and a model that already has a parameter estimation set up (fit items and experiments) with the fitted values stored. Reference: https://basico.readthedocs.io/en/latest/notebooks/EvaluateParameterEstimationResults.html

## Inputs

Required:
- `model_file`: a `.cps` (or SBML) with fit items and experiments defined. If none exist, use `copasi-parameter-estimation` first.

| Name | Default | Description |
|---|---|---|
| corr_threshold | 0.9 | Absolute correlation above which a pair is flagged |
| cv_threshold | 50 | Coefficient of variation (%) above which a parameter is flagged |
| condition_threshold | 1e6 | Condition number of the scaled Fisher matrix above which the fit is flagged as ill-conditioned |
| tol | 1e-12 | Smallest eigenvalue relative to the largest below which the matrix counts as singular |

## Steps

1. Run `scripts/evaluate_fit.py <model_file> [--out DIR] [--corr 0.9] [--cv 50] [--cond 1e6]` with the venv Python. It loads the model, runs `run_parameter_estimation(method=PE.CURRENT_SOLUTION, calculate_statistics=True)` (the stored values are not changed), and writes `fit_parameters.csv`, `experiments.csv`, `observables.csv`, `correlation.csv`, `fisher_scaled.csv`, `fisher_unscaled.csv`, `fisher_eigen.csv`, and `summary.json` to `DIR` (default `eval_<model name>` next to the model). Warnings from unrelated tasks (scan, optimization, LNA) are suppressed.
2. Read the printed report and `summary.json`:
   - `obj`, `rms`, `sd`, `n`, `p`. Warn if `n <= p`. `rms = sqrt(obj/n)`, `sd = sqrt(obj/(n-p))`.
   - Per parameter: `value`, bounds, `std_dev`, `coeff_of_variation`, `gradient`, `on_bound`.
   - Fisher: `rank` against `p`, `condition`, `verdict` (`ok`, `ill-conditioned`, `singular`), `weak_directions` (eigenvectors of the three smallest eigenvalues, components above 0.3), `high_corr` pairs, `zero_rows`, `on_bound`, `high_cv`, `drop_suggestions`.
3. Check the point is stationary: gradients near zero relative to `obj`. Large gradients mean the fit has not converged; refit before interpreting the matrices.
4. Check bound hits: a parameter on a bound distorts the Fisher analysis. Widen the bound and refit before calling it non-identifiable, and report if it still runs to the bound.
5. Check residual bias in `experiments.csv` and `observables.csv`: `error_mean` large relative to `rms`, or the same sign across an experiment, indicates a systematic misfit and probably model-structure error, not a parameter problem. Report it.
6. Classify: well determined, weakly determined (flagged correlations, CV above `cv_threshold`, or condition above `condition_threshold`), or non-identifiable (singular).
7. If the verdict is not `ok`, run the loop below. Otherwise report and finish.
8. Report: fit quality, the parameter table, flagged correlations, weakest directions, bound hits, residual bias, drop recommendations, and the files written.

## Making the fit identifiable

Present the drop candidates with their evidence and let the user choose before changing the fit. Then:

1. `scripts/refit_without.py <model_file> <new_file.cps> --drop "Values[a],Values[b]" [--bound "Values[c]:lower:upper"] [--global-method none]` removes the fit items, optionally changes bounds, refits with `Evolution Strategy (SRES)` then `Levenberg - Marquardt`, and saves a new model. The input is never overwritten. The dropped parameters keep their stored values.
2. Run `evaluate_fit.py` on the new model.
3. Repeat until the verdict is `ok`, no pair exceeds `|corr| > 0.99`, and no parameter is on a bound, or until the user stops. Keep a table per iteration of `obj`, `p`, rank, condition, and the determined parameters. The objective should barely change when you drop a parameter the data do not constrain; a clear increase means the dropped parameter mattered.

Choosing what to drop, in this order:
1. A parameter with an all-zero Fisher row and gradient exactly 0: it has no effect on any fitted observable (for example it only appears in a reaction whose substrate is a fixed species, or it is overridden by an assignment). Drop it.
2. Otherwise, take the eigenvector of the smallest eigenvalue. Among its components with `abs > 0.3`, drop the one that is on a bound or has the largest `coeff_of_variation`, and is least important structurally. Fix it at its current value or a literature value.
3. For a pair with `abs(corr)` near 1 (for example parameters that appear only as a product or ratio), drop one of the pair or reparametrize as the identifiable combination. Which member to fix is arbitrary; say so.

## Failure handling

The matrix counts as singular when it contains NaN/inf, `np.linalg.matrix_rank` is below `p`, or the smallest scaled eigenvalue is at most `tol` times the largest (or negative). In that case `std_dev` and the correlation matrix are NaN, so use the Fisher matrix, its eigen-decomposition, and the gradients instead.

Done when all of these hold:
- `evaluate_fit.py` completed and `summary.json` exists.
- The report states the verdict, bound hits, residual bias, and, if not `ok`, named parameters to drop.
- If refits were done, the per-iteration table and the new model files are listed, and the original model is unchanged.

## Gotchas

- `PE.CURRENT_SOLUTION` leaves the parameter values unchanged; it does not refit. Use `refit_without.py` to refit.
- `calculate_statistics` must be true or the matrices and `std_dev` are not populated.
- Parameter names in the fit statistic carry `.InitialValue` (`Values[K_s].InitialValue`), while `get_fit_parameters()` uses `Values[K_s]`. The scripts normalize this; do the same in your own code.
- In the fit statistic the bounds are CN objects; convert with `float(str(x))`.
- Use the scaled Fisher matrix to compare parameters of different magnitude; use the unscaled one to recover standard deviations (`covariance = sd**2 * inv(F)`).
- Standard deviations and correlations are a local quadratic approximation. When a correlation is about ±1 or an eigenvalue is orders of magnitude below the rest, the parameters are practically non-identifiable; recommend a profile likelihood (https://basico.readthedocs.io/en/latest/notebooks/Profile_likelihood.html).
- Mean-square weighting has no separate measurement-error column, so `sd` is the residual scale, not a chi-square test against known measurement variance.
- Fixing a parameter at its refit value is only exploratory. A literature value is better.
- COPASI messages from other tasks go to stderr, which makes PowerShell report exit code 1. The scripts suppress them; in your own scripts redirect stderr.
