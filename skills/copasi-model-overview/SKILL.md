---
name: copasi-model-overview
description: Compile a COPASI (.cps) or SBML model overview by inspecting the model and running its configured time-course, steady-state, metabolic-control, and parameter-estimation tasks. Use when the user asks for a model overview, behavior report, comprehensive COPASI analysis, or a Markdown report with plots and result statistics.
---

# COPASI model overview

Create a self-contained Markdown report describing a model, its simulated behavior, and the results of applicable COPASI tasks. Use `copasi-basico` from the repository `.venv`; if it is unavailable, follow `copasi-setup` first. This skill coordinates the relevant model tasks. It does not replace focused analysis when the user requests only one specific result.

## Inputs

Required: `model_file` (`.cps`, `.xml`, or `.sbml`).

Optional: report path, simulation time range, whether to re-estimate parameters, and specific output species or fluxes. Prefer task settings stored in the model when the user does not override them.

## Workflow

1. **Inspect the model.** Confirm the file exists and load it with `basico.load_model`. Use an XML parser for `.cps` or SBML metadata, not ad hoc text scraping. Record model name, COPASI/SBML format and version when available, compartments, units, species, reaction names, model comment, citations, license links, and MIRIAM identifiers. For `.cps`, inventory every `Task` by name, type, and `scheduled` flag. For scheduled tasks, inspect enough of the problem configuration to flag visibly missing required targets or inputs; scheduled status alone does not prove the task is runnable. Identify scheduled tasks without assuming they should be executed. Resolve external identifiers as `https://identifiers.org/{namespace}:{identifier}`. Include links present in model annotations, including license and publication URLs.

2. **Choose an output location.** Unless the user specified a path, create a directory named `{model_stem}_overview` beside the model. Write `{model_stem}_overview.md` there and keep all CSVs and plot images in that directory. Keep the source model unchanged; run tasks in memory and do not save modified model values back to the `.cps` file.

3. **Run the time-course task.** Read the model's configured Time-Course settings and use them unless the user supplied a range or method. If no usable time range is configured and the user supplied none, ask for the range or clearly mark time-course analysis as skipped. Use `basico.run_time_course_with_output` for selected species and fluxes, including `Time`; use COPASI selection names such as `[X]` and `(reaction).Flux`. Export the trajectory with time as a column. Plot representative dynamic species and reaction fluxes against time and save PNGs. State the method, time bounds, intervals, initial/fixed conditions, row count, and any non-finite values.

4. **Run the steady-state task.** Call `basico.run_steadystate(update_model=True, use_initial_values=True)` in memory. Record the status: `0` means no state found, `1` a steady state, `2` an all-zero-flux equilibrium, and `3` a solution with negative concentrations. For statuses 1–3, export `basico.get_species()` and `basico.get_reactions()` to CSV and summarize representative concentrations, species rates, and reaction fluxes. Report status 3 as nonphysical; do not describe it as a valid biological state. Do not claim stability unless the Jacobian/eigenvalues were explicitly evaluated.

5. **Run MCA when possible.** Only proceed if steady state returned status 1 or 2. Call `basico.run_mca()` and export scaled elasticities, concentration-control coefficients, and flux-control coefficients. Check summation rows and `Summation Error`; report the reactions ranked by absolute flux-control coefficient for key pathway outputs. Explain that the coefficients are local to the analyzed steady state and that negative control means increasing a reaction rate lowers the selected output flux. If the steady state failed, omit control coefficients and explain why.

6. **Inspect parameter estimation when configured.** Use `get_experiment_names()`, `get_experiment_mapping(name)`, and `get_fit_parameters()` to establish what the model is set up to fit. Resolve relative experiment paths from the model's directory and verify that the mapped time, dependent, and independent columns load correctly. If data are missing or mappings are invalid, report the issue and skip fitting results without blocking other analyses. By default, evaluate the stored/current solution with `run_parameter_estimation(method="Statistics", update_model=False)` and `get_fit_statistic()`; report `obj`, `rms`, `sd`, data/valid point counts, and failed evaluation counts. Obtain current simulations with `get_simulation_results()` and make measured-versus-simulated plots per experiment and per dependent variable. Do not optimize parameters unless the user explicitly asks to fit or re-fit. If asked, use the method configured in the model, compare the final objective to the Statistics baseline, and preserve the original model file.

7. **Inspect optimization setup when configured.** Read `basico.get_opt_settings()`, `basico.get_opt_parameters()`, and `basico.get_opt_constraints()`. When an objective expression is defined, report the exact expression, whether it is minimized or maximized, subtask, method, and relevant method settings. Report each optimization item (`opt_parameters`) with its name, bounds, and start value, plus configured constraints. If the objective references an assigned model value, include that value's defining expression separately so the mathematical objective is clear. Handle an empty parameter or constraint list as absent, not as an error. Do not run the optimizer unless the user explicitly asks; report configuration separately from any current or newly calculated optimization result.

8. **Write the report.** Use the sections below, omitting only sections whose task was unavailable or failed; explain each omission and its reason.

## Report sections

- Summary and model identity
- Model structure, units, fixed pools, and relevant initial conditions
- Notes embedded in the model, provenance, citations, license, and linked identifiers
- COPASI task inventory with task type and scheduled status; explicitly identify scheduled tasks and any visibly incomplete configuration
- Time-course setup, observed transient, and plots
- Steady-state status, representative concentrations/rates/fluxes, and CSV links
- MCA findings and validity checks, when available
- Parameter-estimation setup, mappings, current-solution statistic, measured-versus-simulated plots, and CSV links, when available
- Optimization objective, definition, minimize/maximize direction, optimized parameters and bounds, constraints, method, and schedule status, when configured
- Reproduction details, assumptions, limitations, and skipped tasks

Keep model-authored notes distinct from computed findings. Explicitly distinguish configured example conditions from the conditions actually analyzed. Label units, distinguish transient values from steady-state values, and explain reaction flux direction relative to the model's reaction scheme. Link all local outputs with report-relative paths and make cited MIRIAM identifiers clickable through Identifiers.org.

## Completion checks

- The Markdown report exists and every embedded image and local CSV link resolves.
- For COPASI files, all tasks are accounted for by name, type, and scheduled flag; scheduled status is not presented as evidence that a task was executed.
- Each task's status, method, conditions, and relevant failure/skip reason are stated.
- Time-course output has the expected time bounds and `intervals + 1` rows unless configured output points differ; non-finite values are reported.
- Steady-state data are presented only for a returned status, with status 3 clearly warned.
- MCA claims are made only after a valid steady state and its summation checks are reviewed.
- Parameter-estimation statistics identify whether they describe the stored/current solution or a newly optimized solution. The source `.cps` file remains unchanged.
- When an optimization objective or optimization items are configured, their expression, definition, direction, variables, bounds, and start values are recorded; an optimizer run is reported only if it was explicitly requested and performed.