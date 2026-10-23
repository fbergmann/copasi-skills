"""Find parameter changes that give a model a steady state: minimize the sum of squared species rates at the end of a time course while one essential flux stays above a minimum, then prune the changes to the smallest set that still works."""
import argparse
import math

import basico
from basico import *


def fresh(model_file, additions):
    load_model(model_file)
    for name, scheme, k in additions:
        add_reaction(name, scheme)
        set_reaction_parameters(f"({name}).k1", value=k)


def reaches_steady_state(model_file, additions, params, flux, min_flux):
    fresh(model_file, additions)
    for n, v in params.items():
        set_reaction_parameters(n, value=v)
    run_time_course(start_time=0, duration=20000, intervals=20, use_initial_values=True, update_model=True)
    if run_steadystate(update_model=True, use_initial_values=False) not in (1, 2):
        return False
    fl = get_reactions()["flux"]
    return float(fl[flux]) >= min_flux and float(get_species()["concentration"].min()) >= -1e-9


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("model_file")
    p.add_argument("--flux", required=True, help="reaction whose flux must stay >= --min-flux (e.g. an outflow)")
    p.add_argument("--min-flux", type=float, required=True)
    p.add_argument("--params", nargs="*", help="local parameters to vary, e.g. '(R1).k1' (default: all positive ones)")
    p.add_argument("--fixed", nargs="*", default=[], help="parameters that must not change")
    p.add_argument("--lower", type=float, default=1e-3, help="absolute lower bound; set to the model's rate-constant scale")
    p.add_argument("--upper", type=float, default=10.0)
    p.add_argument("--duration", type=float, default=3000, help="time at which the rates are evaluated")
    p.add_argument("--add-reaction", action="append", default=[], metavar="NAME|SCHEME|K1",
                   help="structural change, e.g. 'ATPase|ATP -> ADP|0.1'")
    p.add_argument("--iterations", type=int, default=300)
    p.add_argument("--swarm", type=int, default=40)
    p.add_argument("--output", help="write the fixed model here")
    a = p.parse_args()

    additions = []
    for spec in a.add_reaction:
        name, scheme, k = spec.split("|")
        additions.append((name.strip(), scheme.strip(), float(k)))

    fresh(a.model_file, additions)
    rp = get_reaction_parameters()
    original = {n: float(rp.loc[n, "value"]) for n in rp.index}
    names = a.params or [n for n, v in original.items() if v > 0]
    names = [n for n in names if n not in a.fixed]
    sp = get_species()
    species = [n for n in sp.index if sp.loc[n, "type"] == "reactions"]

    set_objective_function(expression=" + ".join(f"{{{n}.Rate}}^2" for n in species), minimize=True)
    set_opt_parameters([{"name": n, "lower": a.lower, "upper": a.upper,
                         "start": min(max(original[n], a.lower), a.upper)} for n in names])
    set_opt_constraints([{"name": f"({a.flux}).Flux", "lower": a.min_flux, "upper": 1e12}])
    set_task_settings(T.TIME_COURSE, {"problem": {"Duration": a.duration, "StepNumber": 10}})
    set_opt_settings({"subtask": T.TIME_COURSE,
                      "method": {"name": PE.PARTICLE_SWARM, "Iteration Limit": a.iterations, "Swarm Size": a.swarm}})
    solution = run_optimization()
    stats = get_opt_statistic()
    print(f"optimizer: objective {stats['obj']:.3g}, failed constraint evaluations {stats['failed_constraint_evals']}")

    candidate = {n: float(v) for n, v in solution["sol"].items()}
    if not reaches_steady_state(a.model_file, additions, candidate, a.flux, a.min_flux):
        print("RESULT: optimizer solution does NOT reach a steady state "
              "(a small objective is not enough). Consider a structural change such as a missing sink.")
        return

    current = dict(candidate)
    by_change = sorted((n for n in current if original[n] > 0 and current[n] != original[n]),
                       key=lambda n: abs(math.log(current[n] / original[n])))
    for n in by_change:
        trial = dict(current)
        trial[n] = original[n]
        if reaches_steady_state(a.model_file, additions, trial, a.flux, a.min_flux):
            current = trial
    changed = {n: (original[n], v) for n, v in current.items() if v != original[n]}
    print(f"RESULT: steady state reached with {len(changed)} parameter change(s) after pruning:")
    for n, (old, new) in changed.items():
        print(f"  {n}: {old:g} -> {new:g}")

    if a.output:
        fresh(a.model_file, additions)
        for n, v in current.items():
            set_reaction_parameters(n, value=v)
        save_model(a.output)
        print(f"saved {a.output}")


if __name__ == "__main__":
    main()
