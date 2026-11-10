"""Tables of RESULTS.md 1.3-1.4 not printed by summarize_cell.py, and the post hoc design-count check of 1.6 (descriptive, not a test).
Run: python -I note_tables.py vm-out-a2/x/out-a2 > vm-out-a2/note_tables.out"""
import json
import sys
from pathlib import Path

import numpy as np

out = Path(sys.argv[1])
for t in ["primary", "trial", "win600", "adjacent", "estimated"]:
    d = json.loads((out / ("test-%s.json" % t)).read_text())
    dn = np.array(d["design_null"], float)
    print("%s obs design %s; null N_progression %d/%d/%d, N_neurons %d/%d/%d (min/median/max)" % (
        t, d["design_obs"], dn[:, 0].min(), np.median(dn[:, 0]), dn[:, 0].max(), dn[:, 1].min(), np.median(dn[:, 1]), dn[:, 1].max()))
    for reg, v in d["regions"].items():
        nu = np.array(v["null"], float)
        print("  %s obs %.4f null mean %.4f sd %.4f q5 %.4f q95 %.4f p %.4f holm %.4f" % (
            reg, v["observed"], nu.mean(), nu.std(ddof=1), *np.quantile(nu, [.05, .95]), v["p"], v["p_holm"]))
d = json.loads((out / "test-primary.json").read_text())
dn = np.array(d["design_null"], float)
ob = d["design_obs"]
print("post hoc, primary: P(null N_prog >= 76) %.3f, P(null N_neurons >= 113) %.3f" % ((dn[:, 0] >= ob["n_prog"]).mean(), (dn[:, 1] >= ob["n_neurons"]).mean()))
X = np.c_[np.ones(len(dn)), dn]
for reg, v in d["regions"].items():
    y = np.array(v["null"], float)
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    fit = b @ [1, ob["n_prog"], ob["n_neurons"]]
    adj = y - X @ b + fit
    near = (abs(dn[:, 0] - ob["n_prog"]) <= 8) & (abs(dn[:, 1] - ob["n_neurons"]) <= 15)
    print("  %s slope per trial %.4f per neuron %.4f; fitted null at observed design %.4f (null mean %.4f, difference %.4f); raw p as run %.3f, linear design adjustment %.3f, near observed design (n=%d) %.3f; 98.3rd percentile %.3f" % (
        reg, b[1], b[2], fit, y.mean(), fit - y.mean(), v["p"], (1 + (adj >= v["observed"]).sum()) / (len(y) + 1), near.sum(), (1 + (y[near] >= v["observed"]).sum()) / (near.sum() + 1), np.quantile(y, 1 - .05 / 3)))

# Addendum 3 (2026-11-09): design replay and true-template z-test, from a3_fill.json (second argument)
if len(sys.argv) > 2:
    a3 = json.loads(Path(sys.argv[2]).read_text())
    print("\nAddendum 3: G1 passed %s; python build same as Addendum 2 %s; G11 level-mean largest difference %s" % (a3["g1"]["passed"], a3["python_build_same_as_a2"], a3["g11_largest_difference_of_level_means"]))
    for t, v in a3["design_replay"].items():
        print("%s: observed matches %s; %d of %d permutations match" % (t, v["observed_matches"], v["permutations_matching"], v["permutations"]))
        for r in v["n_qual_observed"]:
            ns = np.array([len(x) for x in v["qualifying_sessions_null"][r]])
            nq = np.array(v["n_qual_null"][r])
            print("  %s observed sessions %d, neurons %d; null sessions min/median/max %d/%d/%d, neurons %d/%d/%d" % (r, len(v["qualifying_sessions_observed"][r]), v["n_qual_observed"][r], ns.min(), np.median(ns), ns.max(), nq.min(), np.median(nq), nq.max()))
    for r, v in a3["true_template_z"].items():
        print("true-template z-test %s: mean per level %s; SD %s; p %s" % (r, np.round(v["mean"], 3).tolist(), np.round(v["sd"], 3).tolist(), ["%.1e" % x for x in v["p"]]))
