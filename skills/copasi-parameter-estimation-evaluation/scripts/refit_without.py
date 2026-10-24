"""Remove fit items from a COPASI parameter estimation, optionally change bounds, refit, and save a new model."""
import argparse
import contextlib
import io

import basico


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model_file")
    ap.add_argument("out_file", help="new .cps; the input is never overwritten")
    ap.add_argument("--drop", default="", help="comma-separated fit item names, e.g. 'Values[k_d],Values[K_p]'")
    ap.add_argument("--bound", action="append", default=[], help="name:lower:upper, repeatable")
    ap.add_argument("--global-method", default="Evolution Strategy (SRES)", help="'none' to skip")
    ap.add_argument("--local-method", default="Levenberg - Marquardt")
    a = ap.parse_args()
    if a.out_file == a.model_file:
        ap.error("out_file must differ from model_file")

    drop = {d.strip().removesuffix(".InitialValue") for d in a.drop.split(",") if d.strip()}
    bounds = {}
    for b in a.bound:
        n, lo, up = b.rsplit(":", 2)
        bounds[n] = (float(lo), float(up))

    with contextlib.redirect_stderr(io.StringIO()):
        basico.load_model(a.model_file)
        fp = basico.get_fit_parameters().reset_index()
    unknown = (drop | set(bounds)) - set(fp["name"])
    if unknown:
        raise SystemExit(f"unknown fit items: {sorted(unknown)}; available: {list(fp['name'])}")
    items = []
    for r in fp.itertuples():
        if r.name in drop:
            continue
        lo, up = bounds.get(r.name, (r.lower, r.upper))
        items.append({"name": r.name, "lower": lo, "upper": up, "start": r.start})
    with contextlib.redirect_stderr(io.StringIO()):
        basico.set_fit_parameters(items)
        basico.run_parameter_estimation(method=basico.PE.CURRENT_SOLUTION)
        print("start obj", basico.get_fit_statistic()["obj"])
        if a.global_method.lower() != "none":
            basico.run_parameter_estimation(method=a.global_method, update_model=True)
            print(a.global_method, "obj", basico.get_fit_statistic()["obj"])
        sol = basico.run_parameter_estimation(method=a.local_method, update_model=True)
        print(a.local_method, "obj", basico.get_fit_statistic()["obj"])
        basico.save_model(a.out_file)
    print(sol.to_string())
    print("saved", a.out_file, "| dropped:", sorted(drop), "| next: evaluate_fit.py", a.out_file)


if __name__ == "__main__":
    main()
