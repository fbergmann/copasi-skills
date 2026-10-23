---
name: copasi-lyapunov
description: Computes Lyapunov exponents for an SBML (.xml/.sbml) or COPASI (.cps) model using Basico's COPASI Lyapunov Exponents task. Use when asked about trajectory divergence, convergence, neutral directions, or possible chaotic dynamics. Not for time-course plots, steady-state values, sensitivities, or metabolic control analysis.
---

# Computing Lyapunov exponents

Requires the `.venv` from `copasi-setup`. Lyapunov exponents estimate the average exponential rates at which nearby trajectories separate or converge. They are dynamical evidence, not by themselves proof of chaos or a complete characterization of a model.

## Inputs

Required: `model_file` (`.cps`, `.xml`, or `.sbml`).

Optional Basico arguments:

| Name | Default | Description |
|---|---|---|
| `num_exponents` | 3 | Number of exponents to calculate; request enough for the state-space directions of interest. |
| `calculate_divergence` | true | Whether to calculate average divergence of the model equations. |
| `start_averaging_after` | 0 | Time after which exponent averaging begins; use to exclude an initial transient. |
| `use_initial_values` | true | Whether to start from model initial values. |
| `settings` | none | Task settings to apply for this run. |

## Workflow

1. Confirm the file exists and `basico` is available in `.venv`. Load the exact model with `basico.load_model(model_file)`.
2. Inspect the stored task with `basico.get_task_settings("Lyapunov Exponents", basic_only=False)`. Record the configured method, total integration time, transient, requested exponent count, and numerical settings. Do not assume the task is scheduled or that a stored result is current.
3. Select `num_exponents` based on the model's dynamic state dimension and the user's question. The Basico default is 3; it may be incomplete or inappropriate for a particular model. State how many exponents were calculated and whether this is the full spectrum.
4. If the model has an initial transient, choose `start_averaging_after` after it settles and before the integration ends. Do not guess the cutoff; use a user value or justify it from the model's configured time horizon and behavior. The default `0` starts averaging from the beginning.
5. Run `exponents, sum_of_exponents, divergence = basico.run_lyapunov(...)`, passing only requested overrides. The call uses initial values by default. It returns all three values; if divergence calculation is disabled, do not report a divergence value as computed.
6. To retrieve the last calculated results without running the integration again, call `basico.get_lyapunov_exponents()`; it returns the exponent list, sum, and average divergence from the latest run.
7. Interpret each exponent with its value and sign: positive indicates average exponential divergence and may indicate chaos; approximately zero indicates a neutral direction, which is typical along a limit cycle; negative indicates average convergence. For a limit cycle, one near-zero exponent and remaining negative exponents are consistent with an attracting cycle. A fully negative spectrum is consistent with an attracting steady state when the full spectrum and asymptotic behavior support that conclusion.
8. Compare the sum of exponents with the average divergence only when the full spectrum was calculated and divergence was requested. They should agree within numerical error; a truncated spectrum is not expected to sum to the full divergence.
9. Report the model, method and relevant task settings, initial-value choice, exponent count, averaging start time, exponents, sum, divergence (if calculated), interpretation, and limitations. Do not save or modify the source model unless explicitly requested.

## Example

The Basico Brusselator example has two independent dynamic directions, so the notebook requests two exponents:

```python
from basico import load_example, run_lyapunov

load_example("brusselator")
exponents, sum_of_exponents, divergence = run_lyapunov(num_exponents=2)
```

For a supplied model, load its file with `load_model(model_file)` instead. Choose the exponent count for that model rather than copying the example's value.

## Gotchas

- `get_lyapunov_exponents()` reads the previous result; it does not recompute it.
- `start_averaging_after` excludes the earlier interval from averaging; it does not shorten the integration or remove the transient from the model dynamics.
- A positive exponent is evidence of exponential divergence, not conclusive proof of chaos. Check that the model is bounded, the averaging window is adequate, and results are stable to reasonable numerical settings.
- A near-zero exponent is approximate and depends on integration and averaging accuracy.
- The sum/divergence comparison is meaningful as a full-spectrum check only when all exponents are included and divergence was calculated.
- Lyapunov exponents describe local average trajectory stability; they do not replace time-course, steady-state, or bifurcation analysis.

## Completion checks

- The exact model and stored Lyapunov task settings were identified.
- The requested exponent count and averaging interval are reported.
- The output tuple is reported accurately; divergence is omitted when not calculated.
- Interpretation is qualified by spectrum completeness, integration interval, and numerical limitations.
- The source model remains unchanged unless saving was explicitly requested.