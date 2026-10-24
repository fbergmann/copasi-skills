---
name: copasi-parameter-estimation-evaluation
description: Evaluates a finished parameter estimation of a COPASI (.cps) or SBML model with copasi-basico, running the current-solution statistics with calculate statistics enabled and analysing the fit statistic, correlation matrix, and Fisher information matrix (eigenvalues, condition number). If the Fisher matrix is singular, suggests which fit parameter to drop. Use when asked whether a fit is identifiable, how well parameters are determined, or to check correlations or parameter uncertainty. Not for running the fit itself (use copasi-parameter-estimation).
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
| update_model | false | Leave the stored parameter values unchanged |

## Steps

1. Load the model: `from basico import *; load_model(model_file)`. Check that `get_fit_parameters()` and `get_experiment_names()` are non-empty.
2. Evaluate the stored solution without changing it, with statistics enabled:
   `run_parameter_estimation(method=PE.CURRENT_SOLUTION, calculate_statistics=True)`.
   Warnings about other tasks (scan, optimization, Lyapunov, LNA) are unrelated and can be ignored.
3. Read the full statistic:
   `stat = get_fit_statistic(include_parameters=True, include_experiments=True, include_fitted=True, include_validation=True)`.
   - Global: `obj`, `rms`, `sd`, `data_points`, `valid_data_points`, `failed_evals_*`.
   - `pd.DataFrame(stat['parameters'])`: `value`, `lower`, `upper`, `std_dev`, `coeff_of_variation`, `gradient`.
   - `stat['experiments']` and `stat['variables']`: per-experiment and per-observable `obj`, `rms`, `error_mean`.
   - With `n = valid_data_points` and `p = len(stat['parameters'])`: `rms = sqrt(obj/n)`, `sd = sqrt(obj/(n-p))`. Warn if `n <= p`.
4. Check that the point is a stationary point: gradients should be near zero relative to `obj`. Flag parameters at a bound (`value` equal to `lower` or `upper`).
5. Get the correlation matrix: `corr = get_correlation_matrix()`. List every off-diagonal pair with `abs(corr) > corr_threshold`, sorted by magnitude.
6. Get the Fisher information matrix, scaled and unscaled:
   `fim_s = get_fisher_information_matrix(scaled=True)`, `fim = get_fisher_information_matrix(scaled=False)`.
   Check for NaN/inf entries and an all-zero row or column (a parameter with no effect on any fitted observable).
7. Get the eigen-decomposition of the scaled matrix: `get_fisher_information_eigenvalues(scaled=True)` and `get_fisher_information_eigenvectors(scaled=True)`. Convert to arrays with `.iloc[:, 0].to_numpy(dtype=float)` for the eigenvalues.
   - Condition number = `max / min` eigenvalue; `sqrt(condition)` is the uncertainty ratio between the worst and best determined directions.
   - The eigenvector of the smallest eigenvalue shows which parameters move together in the least determined direction: the largest absolute components are the parameters involved.
8. Optionally cross-check: `sd**2 * np.linalg.inv(fim)` should reproduce the reported `std_dev` (square root of the diagonal) and the correlation matrix.
9. If the Fisher matrix is not invertible (see below), propose which parameter to drop. Otherwise classify the fit as well determined, weakly determined (flagged correlations, CV above `cv_threshold`, or condition number above `condition_threshold`), or non-identifiable.
10. Save tables to CSV: `fit_parameters.csv`, `correlation.csv`, `fisher_scaled.csv`, `fisher_unscaled.csv`, `fisher_eigen.csv`.
11. Report: `obj`, `rms`, `sd`, the parameter table, flagged correlations, eigenvalues and condition number, the weakest direction, and any parameter drop recommendation.

## Fisher matrix not invertible

Treat the matrix as not invertible when any of these hold: `std_dev` or the matrix contains NaN/inf, `np.linalg.inv` raises `LinAlgError`, the smallest scaled eigenvalue is `<= 1e-12 * largest` (or is non-positive), or `np.linalg.matrix_rank(fim_s) < p`.

Choose the parameter(s) to drop in this order:
1. A parameter whose scaled Fisher row/column is all zero (or near zero): it has no effect on the fitted data. Drop it.
2. Otherwise, take the eigenvector of the smallest eigenvalue. Among its components with `abs > 0.3`, those are the parameters that form the non-identifiable combination. Among them, drop the one that:
   - has the largest `coeff_of_variation`, or `std_dev` NaN/inf, or sits on a bound; and
   - is least biologically or structurally important (e.g. a rate constant redundant with another, a parameter that only appears as a product or ratio with another).
   Fix it at its current value (or at a literature value).
3. For a pair with `abs(corr)` near 1 (e.g. `k1` and `k2` appearing only as `k1*k2` or `k1/k2`), drop one of the pair, or reparametrize as the identifiable combination.
4. After dropping, remove the item from the fit (`set_fit_parameters` with the remaining items), rerun the estimation (`copasi-parameter-estimation`), and repeat this evaluation. If the rank deficiency is larger than one, repeat the elimination for each remaining small eigenvalue.

State clearly that a drop is a suggestion; list the candidates with the evidence (eigenvector components, CV, correlation) so the user can choose.

Done when all of these hold:
- `run_parameter_estimation(method=PE.CURRENT_SOLUTION, calculate_statistics=True)` completed and `get_fit_statistic` returned parameter entries.
- Correlation matrix, Fisher matrices, and eigenvalues were retrieved (or the failure was reported).
- The CSV files exist and are non-empty.
- The report states the identifiability verdict and, if singular, a named parameter to drop.

## Gotchas

- `PE.CURRENT_SOLUTION` leaves the parameter values unchanged; it does not refit. Do not use another method here.
- `calculate_statistics` must be true or the matrices and `std_dev` are not populated.
- Use the scaled Fisher matrix to compare parameters of different magnitude; use the unscaled one to recover standard deviations.
- Standard deviations and correlations are a local quadratic approximation. When a correlation is about ±1 or an eigenvalue is orders of magnitude below the rest, the parameters are practically non-identifiable; recommend a profile likelihood (https://basico.readthedocs.io/en/latest/notebooks/Profile_likelihood.html) for a global view.
- Mean-square weighting has no separate measurement-error column, so `sd` is the residual scale, not a chi-square test against known measurement variance.
- Parameters appearing only through a product or ratio are structurally non-identifiable regardless of data quality; reparametrize instead of refitting.
- Eigenvalue and eigenvector rows are matched by index; the eigenvector columns are named after the fit parameters.
