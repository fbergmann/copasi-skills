"""Evaluate the stored parameter estimation of a COPASI model: statistics, correlations, Fisher information."""
import argparse
import contextlib
import io
import json
import os
import sys

import numpy as np
import pandas as pd
from basico import *  # noqa: F401,F403
import basico


def norm(name):
    return name.strip("'").removesuffix(".InitialValue")


def on_bound(value, lower, upper):
    # bounds come back as CN objects whose string form is the number
    value, lower, upper = float(str(value)), float(str(lower)), float(str(upper))
    if lower > 0 and value > 0:
        return abs(np.log10(value / lower)) < 0.01 or (upper > 0 and abs(np.log10(upper / value)) < 0.01)
    span = upper - lower
    return span > 0 and (abs(value - lower) <= 1e-3 * span or abs(upper - value) <= 1e-3 * span)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model_file")
    ap.add_argument("--out", default=None, help="output directory (default: eval_<model name> next to the model)")
    ap.add_argument("--corr", type=float, default=0.9)
    ap.add_argument("--cv", type=float, default=50.0)
    ap.add_argument("--cond", type=float, default=1e6)
    ap.add_argument("--tol", type=float, default=1e-12, help="relative eigenvalue cutoff for singular")
    a = ap.parse_args()

    base = os.path.splitext(os.path.abspath(a.model_file))[0]
    out = a.out or base.replace(os.path.basename(base), "eval_" + os.path.basename(base))
    os.makedirs(out, exist_ok=True)

    # COPASI writes warnings from unrelated tasks (scan, LNA, ...) to stderr
    with contextlib.redirect_stderr(io.StringIO()):
        basico.load_model(a.model_file)
        basico.run_parameter_estimation(method=basico.PE.CURRENT_SOLUTION, calculate_statistics=True)
    stat = basico.get_fit_statistic(include_parameters=True, include_experiments=True,
                                    include_fitted=True, include_validation=True)
    params = pd.DataFrame(stat["parameters"])
    params["name"] = params["name"].map(norm)
    names = list(params["name"])
    n, p = stat["valid_data_points"], len(names)

    res = {"obj": stat["obj"], "rms": stat["rms"], "sd": stat["sd"], "n": n, "p": p,
           "failed_evals": stat["failed_evals_exception"] + stat["failed_evals_nan"],
           "failed_constraint_evals": stat["failed_constraint_evals"]}
    exps = pd.DataFrame(stat["experiments"]).drop(columns="dependent_data")
    vars_ = pd.DataFrame(stat["variables"])
    params["on_bound"] = [on_bound(r.value, r.lower, r.upper) for r in params.itertuples()]
    params.to_csv(f"{out}/fit_parameters.csv", index=False)
    exps.to_csv(f"{out}/experiments.csv", index=False)
    vars_.to_csv(f"{out}/observables.csv", index=False)

    corr = basico.get_correlation_matrix()
    fim_s = basico.get_fisher_information_matrix(scaled=True)
    fim_u = basico.get_fisher_information_matrix(scaled=False)
    ev = basico.get_fisher_information_eigenvalues(scaled=True)
    evec = basico.get_fisher_information_eigenvectors(scaled=True)
    corr.to_csv(f"{out}/correlation.csv")
    fim_s.to_csv(f"{out}/fisher_scaled.csv")
    fim_u.to_csv(f"{out}/fisher_unscaled.csv")
    ev.to_csv(f"{out}/fisher_eigen.csv")

    F = fim_s.to_numpy(float)
    C = corr.to_numpy(float)
    e = ev.iloc[:, 0].to_numpy(float)
    V = evec.to_numpy(float)
    vcols = [norm(c) for c in evec.columns]

    zero_rows = [names[i] for i in range(len(F)) if np.nan_to_num(np.abs(F[i])).max() < 1e-12]
    finite = bool(np.isfinite(F).all()) and bool(np.isfinite(e).all())
    rank = int(np.linalg.matrix_rank(np.nan_to_num(F)))
    singular = (not finite) or rank < p or e.min() <= a.tol * e.max()
    cond = float(e.max() / e.min()) if e.min() > 0 else float("inf")

    pairs = []
    for i in range(len(C)):
        for j in range(i):
            if np.isfinite(C[i, j]) and abs(C[i, j]) > a.corr:
                pairs.append((names[i], names[j], round(float(C[i, j]), 4)))
    pairs.sort(key=lambda t: -abs(t[2]))

    # Weakest directions: eigenvectors of the smallest eigenvalues with components above 0.3
    weak = []
    for k in np.argsort(e)[:3]:
        comps = {vcols[i]: round(float(V[k, i]), 3) for i in range(V.shape[1]) if abs(V[k, i]) > 0.3}
        weak.append({"eigenvalue": float(e[k]), "components": comps})

    # Drop suggestions: no-effect parameters first, then members of the singular direction
    cv = dict(zip(params["name"], params["coeff_of_variation"]))
    bound = dict(zip(params["name"], params["on_bound"]))
    drop = [{"name": z, "reason": "zero Fisher row: no effect on any fitted observable"} for z in zero_rows]
    if singular:
        tol_ev = max(a.tol * e.max(), 1e-12)
        for k in np.argsort(e):
            if e[k] > tol_ev and finite:
                break
            comps = [vcols[i] for i in range(V.shape[1]) if abs(V[k, i]) > 0.3 and vcols[i] not in zero_rows]
            if comps:
                comps.sort(key=lambda s: (not bound[s], -(cv[s] if np.isfinite(cv[s]) else 1e300)))
                drop.append({"name": comps[0], "reason": f"in singular direction with {comps}; on bound / largest CV"})
                break

    res.update({"finite": finite, "rank": rank, "singular": bool(singular), "condition": cond,
                "zero_rows": zero_rows, "high_corr": pairs, "weak_directions": weak, "drop_suggestions": drop,
                "on_bound": [n_ for n_ in names if bound[n_]],
                "high_cv": [n_ for n_ in names if np.isfinite(cv[n_]) and cv[n_] > a.cv]})
    ill = singular or cond > a.cond or bool(pairs)
    res["verdict"] = ("singular" if singular else "ill-conditioned" if ill else "ok")
    json.dump(res, open(f"{out}/summary.json", "w"), indent=2, default=float)

    print(f"obj={res['obj']:.6g} rms={res['rms']:.4g} sd={res['sd']:.4g} n={n} p={p} failed_evals={res['failed_evals']}")
    print(params[["name", "lower", "value", "upper", "std_dev", "coeff_of_variation", "gradient", "on_bound"]].to_string())
    print("experiments (rms, mean residual):")
    print(exps[["name", "rms", "error_mean"]].to_string())
    print("observables (rms, mean residual):")
    print(vars_[["name", "rms", "error_mean"]].to_string())
    print(f"fisher: finite={finite} rank={rank}/{p} condition={cond:.3g} verdict={res['verdict']}")
    print("weakest directions:", json.dumps(weak))
    print("correlation pairs above threshold:", pairs)
    print("on bound:", res["on_bound"], "| CV above threshold:", res["high_cv"])
    print("drop suggestions:", json.dumps(drop))
    print("files:", out)


if __name__ == "__main__":
    sys.exit(main())
