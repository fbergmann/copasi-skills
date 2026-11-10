---
name: copasi-scan
description: Inspects, configures, and runs the COPASI Parameter Scan task in an SBML (.xml/.sbml) or COPASI (.cps) model with copasi-basico. Use when asked to scan model elements over ranges or explicit values, repeat a COPASI subtask, sample values from a distribution, or run a configured scan task. Not for parameter optimization or fitting.
license: BSD-2-Clause
---

# COPASI parameter scans

Requires the `.venv` from `copasi-setup`. This skill operates the COPASI Scan task, so configurations can remain in the model and be run later in COPASI. It is not a replacement for an optimizer or a hand-written Python loop.

## Inputs

Required: `model_file`.

Optional:
- `scan_items`: ordered list of scan, repeat, or random items; omit to use the scan items already stored in the model.
- `subtask`: COPASI task to run for each scan point; omit to keep the configured subtask.
- `output`: list of display names or CNs to collect from each subtask run.
- `output_file`: CSV path for returned output.

## Workflow

1. Confirm the model file exists and the `.venv` can import `basico`. Load the exact model with `basico.load_model(model_file)`.
2. Inspect `basico.get_scan_settings()` and `basico.get_scan_items()`. Report the configured subtask, scan items, and relevant settings such as `scheduled`, `update_model`, `output_during_subtask`, `continue_from_current_state`, and `continue_on_error`. Do not assume that a configured task is scheduled or that a scheduled task was run.
3. If the user did not request a new scan design, keep the stored scan items and settings. If they did, resolve each `item` from names available in the model and validate the requested ranges, values, and distributions.
4. Configure scan items with `basico.set_scan_items(scan_items)` when replacing the list. Use `basico.add_scan_item(...)` only when adding to the existing list is intended. `set_scan_settings(...)` can change task settings; when its dictionary includes `scan_items`, the list is replaced. Re-read the settings and items to verify the configuration before running.
5. For each item, preserve list order:
   - `scan`: vary one model element through explicit `values`, or over `min` to `max` with `num_steps`; `log` selects logarithmic spacing when applicable. Specify the model element with `item` (display name) or `cn`.
   - `repeat`: repeat the selected subtask `num_steps` times without defining a model-element range.
   - `random`: sample the specified `item` from a `distribution` (`uniform`, `normal`, `poisson`, or `gamma`). The distribution parameters are represented by `min` and `max`: uniform uses lower/upper bounds; normal uses mean/standard deviation; poisson uses mean (`max` is unused); gamma uses shape/scale. Use a `repeat` item to request a number of random draws.
6. Explain nested ordering before running: for each value of scan item 1, COPASI processes all values of scan item 2, and so on. This determines the output row order and total run count.
7. Run only when requested. To use the model's configured subtask, call `basico.run_scan(output=output)`; to override settings for this run, pass `settings={...}`. For example, the documentation uses `settings={"subtask": T.STEADY_STATE}`. `output` is optional: without it, `run_scan` returns `None`; with it, the call returns a pandas DataFrame containing the selected outputs from the scan.
8. If a DataFrame is returned and an output file was requested, write it to CSV with `index=False`. Report the file, row count, output columns, subtask, scan design, and any non-finite values. If no output was requested, report that the task ran without returning a result table.
9. Keep model changes in memory by default. If the user explicitly requests persistence of scan settings, save to a separate path with `basico.save_model(output_path)`, reload it, and verify `get_scan_settings()` and `get_scan_items()`; replace the input model only when explicitly requested.

## Examples

Scan a local reaction parameter at explicit values:

```python
from basico import load_model, run_scan, set_scan_items

load_model("model.cps")
set_scan_items([
    {"item": "(R1).k1", "values": [0.5, 1.0, 2.0]},
])
result = run_scan(output=["(R1).Flux"])
```

Repeat a steady-state scan task five times while sampling an initial concentration from a normal distribution:

```python
from basico import T, load_model, run_scan, set_scan_items

load_model("model.cps")
set_scan_items([
    {"type": "repeat", "num_steps": 5},
    {
        "item": "[A]_0",
        "type": "random",
        "distribution": "normal",
        "min": 2.0,
        "max": 0.1,
    },
])
result = run_scan(
    settings={"subtask": T.STEADY_STATE},
    output=["[A]_0", "[X]", "[Y]"],
)
```

The examples use model-specific names; inspect the loaded model and use valid display names or CNs. The documented random example uses a repeat item before the random item.

## Gotchas

- `set_scan_items` replaces the scan item list. Use `add_scan_item` only when appending is intended.
- Multiple scan items are nested in list order, not zipped together.
- A random item describes a distribution; the repeat item controls how many repetitions/draws are requested.
- `run_scan` with no `output` selection returns `None`, even though the task runs.
- Changing scan settings in memory does not persist them to the source model. Save only when explicitly requested.
- A scan runs the configured or selected COPASI subtask at each point; it does not search for an optimum.

## Completion checks

- The loaded model, scan settings, scan items, and subtask are identified.
- Requested changes to scan items/settings are read back and verified before execution.
- Output is reported as a DataFrame/CSV only when `output` was selected and returned.
- Persisted settings are saved to the requested path and verified after reload; otherwise the source model remains unchanged.