"""Diagnose why an SBML/COPASI model has no steady state: runs the steady-state task, a long time course, and classifies each species."""
import argparse

import numpy as np
import basico


def classify(time, values, tol):
    tail = slice(int(0.75 * len(values)), None)
    t, v = time[tail], values[tail]
    mean = max(abs(v.mean()), 1e-12)
    slope = np.polyfit(t, v, 1)[0]
    drift = slope * (t[-1] - t[0]) / mean
    sign_changes = int(np.sum(np.diff(np.sign(np.diff(v))) != 0))
    if values[-1] < 1e-6 * max(values.max(), 1e-12) and values.max() > 1e-6:
        label = "DEPLETED"
    elif abs(v.max() - v.min()) / mean > 1e-3 and sign_changes >= 4:
        label = "OSCILLATING"
    elif abs(drift) > tol:
        label = "DRIFTING-UP" if slope > 0 else "DRIFTING-DOWN"
    else:
        label = "settled"
    return label, slope


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("model_file")
    p.add_argument("--duration", type=float, default=1e4, help="time-course length")
    p.add_argument("--intervals", type=int, default=200)
    p.add_argument("--tol", type=float, default=1e-3, help="relative drift over the last quarter that counts as not settled")
    a = p.parse_args()

    basico.load_model(a.model_file)
    s0 = basico.run_steadystate(update_model=False, use_initial_values=True)
    print(f"steady state from initial values: status {s0} (0 = not found, 1/2 = found, 3 = negative)")

    res = basico.run_time_course(start_time=0, duration=a.duration, intervals=a.intervals,
                                 use_initial_values=True, update_model=True)
    time = res.index.to_numpy(dtype=float)
    s1 = basico.run_steadystate(update_model=True, use_initial_values=False)
    print(f"steady state from end of time course (t={a.duration:g}): status {s1}")

    print("\nspecies trend over the last quarter of the time course")
    print(f"{'species':<14}{'final':>12}{'slope':>14}  class")
    for col in res.columns:
        label, slope = classify(time, res[col].to_numpy(dtype=float), a.tol)
        print(f"{col:<14}{res[col].iloc[-1]:>12.4g}{slope:>14.4g}  {label}")

    rx = basico.get_reactions()
    boundary = rx[rx["scheme"].str.strip().str.startswith("->") | rx["scheme"].str.strip().str.endswith("->")]
    print("\nboundary reactions (source/sink) and their flux at the end state")
    print(boundary[["scheme", "flux"]].to_string())
    print("\nlargest fluxes at the end state")
    print(rx.reindex(rx["flux"].abs().sort_values(ascending=False).index)[["scheme", "flux"]].head(10).to_string())


if __name__ == "__main__":
    main()
