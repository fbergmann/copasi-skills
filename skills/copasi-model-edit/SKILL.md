---
name: copasi-model-edit
description: Creates or structurally modifies an SBML (.xml/.sbml) or COPASI (.cps) model with copasi-basico, adding species, reactions, kinetic functions, global parameters, events, and notes/MIRIAM annotations. Use when asked to build a new model, add or change reactions, change rate laws, add events, or annotate a model. Not for only changing existing values (use copasi-model-values), nor for running analyses.
---

# Creating and editing COPASI models

Requires the `.venv` from `copasi-setup`. Keep edits in memory; save with `basico.save_model(path)` (or `save_model(path, type='sbml')`) only to a new path unless the user asks to overwrite. After saving, reload the file and verify the edits.

```python
from basico import *
```

## Contents

- [Create a model](#create-a-model)
- [Reactions](#reactions)
- [Species, compartments, global parameters](#species-compartments-global-parameters)
- [Editing reaction kinetics](#editing-reaction-kinetics)
- [Custom kinetic functions](#custom-kinetic-functions)
- [Events](#events)
- [Annotations](#annotations)
- [Workflow](#workflow)
- [Gotchas](#gotchas)

## Create a model

```python
new_model(name='Simple Model', notes='optional notes')
# optional units: quantity_unit, volume_unit, time_unit, area_unit, length_unit
# defaults: mol, l, s
```

Or edit an existing one with `load_model(path)`. `new_model` replaces the current model.

## Reactions

`add_reaction(name, scheme, **set_reaction_kwargs)` creates the reaction and automatically assigns mass action kinetics to it (irreversible or reversible mass action, matching the scheme), with local parameters `(R1).k1 = 0.1` (and `k2` for reversible); no `function` argument is needed for mass action. Species in the scheme that do not exist yet are created automatically (initial concentration 1, in the first compartment, or in a new unit compartment named `compartment` if the model has none). It accepts the same kwargs as `set_reaction` (`function`, `mapping`, `notes`), so kinetics can be given at creation.

To control species placement or initial values, create species first with `add_compartment` / `add_species` (below), then add reactions.

```python
add_reaction('R1', 'A -> B')
add_reaction('R2', 'B = C')            # '=' reversible, '->' irreversible
add_reaction('R3', 'A -> B; C D')      # text after ';' lists modifiers, space separated
```

Inspect: `get_reactions()` (columns `scheme`, `function`, `mapping`), `get_reaction_parameters()`, `get_species()`.

Modify with `set_reaction(name, scheme=..., function=..., mapping=..., new_name=...)`. Remove with `remove_reaction(name)`.

## Species, compartments, global parameters

Signatures (all accept `model=` to target a specific data model; each `add_*` also accepts every kwarg of the matching `set_*`):

- `add_compartment(name, initial_size=1.0, **set_compartment_kwargs)`
- `add_species(name, compartment_name='', initial_concentration=1.0, **set_species_kwargs)`; `compartment_name` is optional: when omitted, the species is placed in the first compartment of the model (a unit `compartment` is created if none exists). Pass it only to use a different compartment.
- `add_parameter(name, initial_value=1.0, **set_parameters_kwargs)`

```python
add_compartment('cell', initial_size=2.0)
add_species('A', compartment_name='cell', initial_concentration=10)
add_species('B')                                   # no compartment_name: goes into the first compartment
add_parameter('global_k', initial_value=0.2)       # global quantity, type 'fixed' by default
```

Common `set_*` kwargs usable in `add_*` and `set_*`:

| Function | Kwargs |
|---|---|
| `set_compartment` | `new_name`, `initial_size`/`initial_value`, `size`/`value`, `initial_expression`, `type`/`status` (`fixed`, `assignment`, `ode`), `expression`, `dimensionality` (1-3), `notes` |
| `set_species` | `new_name`, `initial_concentration`, `initial_particle_number`, `initial_expression`, `concentration`, `particle_number`, `type`/`status` (`fixed`, `assignment`, `ode`; COPASI `reactions` is the default), `expression`, `notes` |
| `set_parameters` | `new_name`, `unit`, `initial_value`, `value`, `initial_expression`, `type`/`status` (`fixed`, `assignment`, `ode`), `expression`, `notes` |

`expression` is only valid for `assignment` / `ode` types. Expressions reference display names in braces, e.g. `{Values[x].InitialValue}`, `{[A]}`, `{Time}`.

```python
add_parameter('f', type='assignment', expression='{Values[global_k].InitialValue}*2')
set_species('A', initial_particle_number=100)
set_reaction_parameters('(R1).k1', value=1)         # local reaction parameter
```

Remove with `remove_compartment`, `remove_species`, `remove_parameter`, each accepting a name or list of names. `remove_compartment` deletes everything inside it; `remove_parameter` also deletes elements whose expressions use it, so check dependencies first.

Rename any element with `set_element_name(element, new_name)` or the `new_name` kwarg of the matching `set_*`.

Stochastic methods need small particle numbers: either set `initial_particle_number` or change units with `set_model_unit(quantity_unit=..., volume_unit=...)` (also `time_unit`, `length_unit`, `area_unit`); `get_model_units()` shows the current ones.

Arbitrary ODEs: `add_equation('d[X]/dt = k1 * exp({Time})')` creates missing entities and the ODE (optional `time_symbol='t'`).

For value-only edits on existing objects, use `copasi-model-values`.

## Editing reaction kinetics

1. Find suitable functions: `get_functions(suitable_for='R1')` (filter by `reversible=False/True`); filter the dataframe index with `str.contains('inhibition')` etc. Inspect one with `as_dict(df)[0]` to see `formula` and `mapping` roles (`substrate`, `product`, `modifier`, `parameter`).
2. Assign it: `set_reaction('R1', function='Henri-Michaelis-Menten (irreversible)')`. This creates local parameters (e.g. `(R1).Km`, `(R1).V`, default 0.1).
3. Functions that use modifiers require the modifiers in the scheme (`'A -> B; C'`). If several modifiers exist, map explicitly:

```python
set_reaction('R1', scheme='A -> B; C D', function='Allosteric inhibition (MWC)',
             mapping={'Inhibitor': 'D'})
```

4. Map a function parameter to a global quantity instead of a local value:

```python
add_parameter('global_k', initial_value=0.2)
set_reaction('R1', mapping={'k1': 'global_k'})
```

5. Verify with `get_reactions()[['scheme','function','mapping']]`. A mapping that is a number means a local parameter; a name means a global quantity or species.

If the function/mapping is invalid, basico logs an error (`the mapping for reaction ... is not valid`) and leaves the previous kinetics, so always re-read `get_reactions()` after the call.

## Custom kinetic functions

If no built-in function fits, define one and assign it to a reaction:

```python
add_function('my_mm', 'V * S / (K + S)', type='irreversible',
             mapping={'S': 'substrate', 'V': 'parameter', 'K': 'parameter'})
set_reaction('R1', function='my_mm')
```

`add_function(name, infix, type='general', mapping=None)`: `type` is `reversible`, `irreversible` or `general`; `mapping` assigns each symbol a role (`substrate`, `product`, `modifier`, `parameter`, `volume`, `time`), defaulting to `parameter`. It does nothing if a function with that name already exists. Remove with `remove_function(name)`.

## Events

```python
add_event('e0', 'Time > 30', [['X', '10']])
# add_event(name, trigger_expression, [[target, expression], ...])
get_events()    # columns: trigger, delay, assignments, key, sbml_id
```

Assignments are a list of `(target, expression)` pairs. For species in specific compartments, use display-name syntax such as `X{compartment[2,2]}`. Optional kwargs for `add_event` / `set_event`: `delay`, `priority`, `persistent` (bool), `delay_calculation` (bool), `fire_at_initial_time` (bool), `new_name`.

- `add_event_assignment(name, (target, expression))` adds assignments to an existing event (`name` may be a substring unless `exact=True`).
- `set_event(name, trigger=..., assignments=...)` modifies an event; `remove_event(name)` / `remove_all_events()` delete.
- Events fire during `run_time_course`; test by simulating and checking the jump.

## Annotations

Notes and MIRIAM annotations apply to the model by default, or to an element via `name=`.

```python
set_notes('text or HTML')            # get_notes() reads them; new_model(notes=...) also works
get_miriam_annotation()              # model; get_miriam_annotation(name='NADH') for an element

import datetime
set_miriam_annotation(
    creators=[{'first_name': 'A', 'last_name': 'B', 'email': 'a@b.org', 'organization': 'Org'}],
    references=[{'id': '10951190', 'resource': 'PubMed'}],
    descriptions=[{'qualifier': 'is', 'resource': 'BioModels Database', 'id': 'MODEL6623915522'}],
    modifications=[datetime.datetime.now(datetime.timezone.utc)],
    replace=True)   # False appends to existing entries; default True replaces
```

- `creators`: dicts with `first_name`, `last_name`, `email`, `organization`.
- `references`: `id`, `resource`, optional `uri`, `description`.
- `descriptions`: `qualifier` (e.g. `is`, `is homolog to`, `has taxon`), `resource`, `id`.
- `created`: a datetime; `modifications`: list of datetimes.
- Valid `resource` names: `get_miriam_resources()` (filter `is_citation == True` for citations). If it is empty (`have_miriam_resources()` is False), run `update_miriam_resources()`.
- Use `name='<element>'` in `set_miriam_annotation` to annotate a species or reaction; verify with `get_miriam_annotation(name=...)`.

## Workflow

1. Load or create the model; inspect it first (`overview()`, `get_species()`, `get_reactions()`, `get_parameters()`, `get_events()`).
2. Apply edits in small steps; after each, read back the relevant table.
3. Sanity check with a short `run_time_course(duration=...)` (and `get_species()` for unexpected auto-created species from typos in schemes).
4. Save only when requested, to a new path; reload and re-verify.

## Gotchas

- Typos in a reaction scheme silently create new species; check `get_species()`.
- `set_*` and `add_*` calls often return nothing on failure beyond a log message; always read back.
- Changing `scheme` or `function` can reset mapped local parameters to defaults; re-set values afterwards.
- Species names are case sensitive; reaction parameters are addressed as `(Reaction).param`.
- Avoid the plotting examples from the docs (matplotlib) unless the user asks for plots.
