"""Checks of the Addendum 3 wrapper without data (synthetic sessions only). Run: python -I test_run_cell_a3.py"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("CELL_MIN_TRIALS", "18")
os.environ.setdefault("CELL_VAL_RULE", "round")
import json  # noqa: E402
import tempfile  # noqa: E402

import cell_env  # noqa: E402,F401
import numpy as np  # noqa: E402
import cell_gate as cg  # noqa: E402
import cell_tests as ct  # noqa: E402
import cellport as cp  # noqa: E402
import run_cell as rc  # noqa: E402
import run_cell_a3 as a3  # noqa: E402
from synthetic_data import make_sessions  # noqa: E402


def main():
    S, rs = make_sessions(43, n_sess=5, n_blocks=9, rois=list(cg.ROIS))
    checks = {}
    for name in rc.TESTS:
        kind, window, labels, purpose, _ = rc.TESTS[name]
        s = cp.with_window(S, window)
        bins = [x.true_bin if labels == "true" else x.belief_bin for x in s]
        got = a3.replay_design(S, rs, name, 4, workers=1)
        want = [ct.one_labelling(("obs" if i == 0 else kind, i, s, bins, cg.ROIS, rs, 1, "fast", True, purpose, "coarse")) for i in range(5)]
        checks["%s: replayed design counts equal the decoder path for the observed labelling and 4 permutations" % name] = all(
            [g[1], g[2]] == [w[2], w[3]] for g, w in zip(got, want))
        rec = {"design_obs": {"n_prog": want[0][2], "n_neurons": want[0][3]}, "design_null": [[w[2], w[3]] for w in want[1:]]}
        cmp1 = a3.compare_design(got, rec)
        checks["%s: compare_design reports all matches" % name] = cmp1["observed_matches"] and cmp1["permutations_matching"] == 4
        rec["design_null"][0][0] = -1
        checks["%s: compare_design counts a mismatch" % name] = a3.compare_design(got, rec)["permutations_matching"] == 3
        checks["%s: n_qual has one list per region" % name] = all(len(cmp1["n_qual_null"][r]) == 4 for r in cg.ROIS)
    acc = {r: np.tile(np.array([[0.5, 0.6, 0.7]]), (100, 1)) + np.linspace(-.02, .02, 100)[:, None] for r in cg.ROIS}
    z = a3.z_table(acc)
    checks["z_table uses cellport.z_test (ddof 1, against 1/3)"] = abs(z["LIP"]["p"][0] - float(cp.z_test(acc["LIP"][:, 0]))) < 1e-15
    checks["z_table mean per level"] = abs(z["LIP"]["mean"][1] - 0.6) < 1e-12
    d0 = cg.gate_draws(S, rs, [x.true_bin for x in S], 4, 22, {"as_written": True, "grid": "coarse"}, workers=1, chunk=2, variant="fast")[0]
    d1 = cg.gate_draws(S, rs, [x.true_bin for x in S], 4, 22, {"as_written": True, "grid": "coarse"}, workers=1, chunk=2, variant="fast")[0]
    checks["gate draws with the same purpose code repeat exactly"] = all(np.array_equal(d0[r], d1[r]) for r in cg.ROIS)
    src = (Path(__file__).resolve().parent / "run_cell_a3.py").read_text()
    checks["the wrapper imports cell_env before numpy"] = src.index("import cell_env") < src.index("import numpy")
    checks["replay does not depend on the number of workers"] = a3.replay_design(S, rs, "primary", 4, workers=1) == a3.replay_design(S, rs, "primary", 4, workers=2)
    rep = a3.replay_design(S, rs, "primary", 2, workers=1)
    checks["qualifying sessions are saved per region"] = all(isinstance(rep[0][4][r], list) and len(rep[0][4][r]) >= 1 for r in cg.ROIS)
    n_sess = {r: len(rep[0][4][r]) for r in cg.ROIS}
    checks["qualifying neurons equal the neurons of the qualifying sessions"] = all(rep[0][3][r] == sum(S[i].feat[r].shape[0] for i in rep[0][4][r]) for r in cg.ROIS)

    # end-to-end main() on synthetic sessions with a fabricated prior run
    prior, out = Path(tempfile.mkdtemp()), Path(tempfile.mkdtemp())
    platform_now = cell_env.platform_record()
    for name in rc.TESTS:
        g = a3.replay_design(S, rs, name, 3, workers=1)
        (prior / ("test-%s.json" % name)).write_text(json.dumps({"P": 3, "design_obs": {"n_prog": g[0][1], "n_neurons": g[0][2]}, "design_null": [[x[1], x[2]] for x in g[1:]]}))
    (prior / "select.json").write_text(json.dumps({"val_rule": "round", "variant_for_tests": "as_written"}))
    g11 = {"mean_per_region_level": {r: [0.5, 0.5, 0.5] for r in cg.ROIS}}
    (prior / "gate.json").write_text(json.dumps({"platform": platform_now, "extra": {"true_template_descriptive_G11": g11}}))
    saved = cell_env.require_platform_fixed, cell_env.check_environment, rc.load_sessions, rc.D_GATE, cg.g1_integrity
    cell_env.require_platform_fixed = lambda *x, **k: None
    cell_env.check_environment = lambda: None
    rc.load_sessions = lambda a, o: (S, rs)
    rc.D_GATE = 4
    cg.g1_integrity = lambda *x, **k: {"passed": True, "detail": "synthetic"}
    argv = ["fill", "--extract-root", "x", "--prior", str(prior), "--out", str(out), "--workers", "1"]
    a3.main(argv)
    rec = json.loads((out / "a3_fill.json").read_text())
    checks["main(): design replay of the five tests matches the prior"] = all(rec["design_replay"][n]["observed_matches"] and rec["design_replay"][n]["permutations_matching"] == 3 for n in rc.TESTS)
    checks["main(): true-template z-test, draws, G1 and BLAS state are saved"] = set(rec["true_template_z"]) == set(cg.ROIS) and np.array(rec["true_template_draws"]["LIP"]).shape == (4, 3) and rec["g1"]["passed"] and "blas" in rec
    bad = json.loads((prior / "gate.json").read_text())
    bad["platform"]["versions"]["numpy"] = "0.0"
    (prior / "gate.json").write_text(json.dumps(bad))
    try:
        a3.main(argv)
        checks["main(): refuses other package versions than the Addendum 2 run"] = False
    except SystemExit as e:
        checks["main(): refuses other package versions than the Addendum 2 run"] = "differ" in str(e)
    cg.g1_integrity = lambda *x, **k: {"passed": False, "detail": "synthetic failure"}
    (prior / "gate.json").write_text(json.dumps({"platform": platform_now, "extra": {"true_template_descriptive_G11": g11}}))
    try:
        a3.main(argv)
        checks["main(): stops when G1 fails"] = False
    except SystemExit as e:
        checks["main(): stops when G1 fails"] = "G1 failed" in str(e)
    cell_env.require_platform_fixed, cell_env.check_environment, rc.load_sessions, rc.D_GATE, cg.g1_integrity = saved
    for k, v in checks.items():
        print("%s %s" % ("PASS" if v else "FAIL", k))
    assert all(checks.values())
    print("all checks passed")


if __name__ == "__main__":
    main()
