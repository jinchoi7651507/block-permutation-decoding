#!/usr/bin/env python3
"""Step 2 addendum 3 §2c agreement gate, Python part (G1 structure, G1b port error, G4 rule-level rates).
Reads the permutations the tools produced on L2 replicates 0-49 (CoSMoMVPA: L2_rXXX_perm.mat, index vectors,
1-based; PyMVPA: L2_rXXX_pymvpa_perm.npy, draws x folds x trials targets) and the replicate files.

  python add3_gate.py --data ../runs_add3/tools/data --gate ../runs_add3/tools/gate --cosmo-error-check <file>

G1: every CoSMoMVPA permutation keeps each sample in its chunk and the multiset of targets of every chunk.
G1b: on the constructed replicate (chunk 1 single-class) the CoSMoMVPA call failed (file written by the Octave
check) and sim.p3_within_run returns None. G4 (exact, P4 rule; computed in add3_pymvpa.py --gate, same Python 3.9 environment):
on L2 replicates 0..exact_reps-1 PyMVPA's MCNullDist with SKLLearnerAdapter(stamped pipeline) gives the same null
errors as a plain scikit-learn loop over the regenerated draws. Here: fold order asserted (test chunks 1, 2, 3, 4).
The PyMVPA draws are regenerated from the replicate's seed (the same sequence as in the tool run, not read from it).
Descriptive (no pass): paired p of the P3 and P4 ports with the tools' draws vs with the ports' own draws
(rng [2029002, rep, 9]). Writes gate/GATE-RESULT.json.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from scipy.io import loadmat
from sklearn.base import clone

import sim
from add3_reference import load, loro_folds


def p_from_null(est, X, y, fl, null_labels):
    _, obs = sim.cv_correct(est, X, y, fl)
    null = [sim.cv_correct(est, X, yp, fl)[1] for yp in null_labels]
    return sim.p_mc(null, obs)


def p4_null(est, X, y, fl, draws):
    """P4 null accuracies with given training-partition label vectors (draws x folds x trials, fold order = runs)."""
    null = []
    for d in draws:
        accs = []
        for (tr, te), yf in zip(fl, d):
            m = clone(est).fit(X[tr], yf[tr])
            accs.append(float(np.mean(m.predict(X[te]) == y[te])))
        null.append(float(np.mean(accs)))
    return np.array(null)


def p4_with_draws(est, X, y, fl, draws):
    _, obs = sim.cv_correct(est, X, y, fl)
    return sim.p_mc(p4_null(est, X, y, fl, draws), obs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--gate", required=True)
    ap.add_argument("--cosmo-error-check", required=True, help="file written by the Octave single-class check")
    ap.add_argument("--n-perm", type=int, default=200)
    ap.add_argument("--exact-reps", type=int, default=10)
    ap.add_argument("--gate-reps", type=int, default=50, help="synthetic tests only; the study gate uses 50")
    args = ap.parse_args()
    g = Path(args.gate)
    res = {"G1_checked": 0, "G1_fail": 0}
    rates = {"P3_tool_draws": 0, "P3_port_draws": 0, "P4_tool_draws": 0, "P4_port_draws": 0, "n": 0}
    for rep in range(args.gate_reps):
        X, y, runs, blocks = load(Path(args.data) / f"L2_r{rep:03d}.mat")
        est, fl = sim.pipeline(), loro_folds(runs)
        perms = loadmat(g / f"L2_r{rep:03d}_perm.mat")["perms"].astype(int) - 1      # trials x draws, 0-based
        null3 = []
        for i in range(perms.shape[1]):
            idx = perms[:, i]
            res["G1_checked"] += 1
            same_chunk = np.array_equal(runs[idx], runs)
            yp = y[idx]
            ms = all(np.array_equal(np.sort(yp[runs == r]), np.sort(y[runs == r])) for r in np.unique(runs))
            res["G1_fail"] += int(not (same_chunk and ms))
            null3.append(yp)
        rates["P3_tool_draws"] += p_from_null(est, X, y, fl, null3) < 0.05
        rates["P3_port_draws"] += sim.p3_within_run(est, X, y, fl, runs, args.n_perm,
                                                    np.random.default_rng([2029002, rep, 9])) < 0.05
        d4 = np.array(np.load(g / f"L2_r{rep:03d}_pymvpa_perm.npy"), dtype=int) - 1      # PyMVPA targets 1/2
        tc = np.load(g / f"L2_r{rep:03d}_pymvpa_testchunk.npy")
        assert np.all(tc == np.arange(1, len(fl) + 1)), "PyMVPA fold order differs from loro_folds"
        rates["P4_tool_draws"] += p4_with_draws(est, X, y, fl, d4) < 0.05
        rates["P4_port_draws"] += sim.p4_train_only(est, X, y, fl, args.n_perm,
                                                    np.random.default_rng([2029002, rep, 9])) < 0.05
        rates["n"] += 1
    y1 = np.repeat([0, 1], 40)
    runs1 = np.repeat([0, 1], 40)                       # chunk 0 holds only class 0
    X1 = np.random.default_rng(0).poisson(5, (80, 30)).astype(float)
    res["G1b_port_returns_none"] = sim.p3_within_run(sim.pipeline(), X1, y1, loro_folds(runs1), runs1, 5,
                                                     np.random.default_rng(1)) is None
    res["G1b_tool_error"] = "error" in Path(args.cosmo_error_check).read_text().lower()
    res["G4"] = {k: int(v) for k, v in rates.items()}
    pm = json.loads((g / "pymvpa_gate.json").read_text())
    res["G2"] = {"checked": pm["G2_checked"], "fail": pm["G2_fail"]}
    res["G3"] = {"checked": pm["G3_checked"], "max_abs_diff": pm["G3_maxdiff"]}
    res["pass"] = {"G1": res["G1_fail"] == 0, "G1b": res["G1b_port_returns_none"] and res["G1b_tool_error"],
                   "G2": pm["G2_fail"] == 0, "G3": pm["G3_maxdiff"] <= 1e-12,
                   "G4_exact": pm.get("G4_exact_maxdiff", 1.0) <= 1e-12 and pm.get("G4_exact_obsdiff", 1.0) <= 1e-12}
    res["G4_exact"] = {k: pm.get(k) for k in ("G4_exact_reps", "G4_exact_maxdiff", "G4_exact_obsdiff")}
    res["G4_descriptive_rates"] = res.pop("G4")
    (g / "GATE-RESULT.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res["pass"]))


if __name__ == "__main__":
    main()
