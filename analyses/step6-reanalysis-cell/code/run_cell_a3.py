"""Addendum 3 (2026-11-09): fills two quantities the design promised and the stamped code did not save.

(1) qualifying sessions and neurons per region for every labelling of the five tests: each labelling is replayed from its
    stamped seed (permutation only, no decoder), and its design counts are compared with the saved n_prog and n_neurons;
(2) the z-test of DESIGN 5a on the true-template gate draws (the G11 draws, same purpose code and seeds).
No test, window, seed, P, D, gate, decision rule or prediction changes. No stamped file changes.

    python -I run_cell_a3.py fill --extract-root ROOT --prior PRIOR_OUT --out OUT [--workers N] [--cache]
PRIOR_OUT is the output folder of the Addendum 2 run (select.json, gate.json, test-*.json); it is only read.
"""
import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cell_env  # noqa: E402,F401  (must come before numpy: it sets the thread variables)

import numpy as np  # noqa: E402

import cell_gate as cg  # noqa: E402
import cell_tests as ct  # noqa: E402
import cellport as cp  # noqa: E402
import run_cell as rc  # noqa: E402

KIND_CODE = {"obs": 0, "block": 1, "trial": 2, "block_adjacent": 3, "sequence": 4}     # as in cell_tests.one_labelling


def permuted_bins(kind, i, sessions, bins, purpose):
    """The labelling that cell_tests.one_labelling uses for (kind, i): same stream, permutation only."""
    rng = ct.rng_for(purpose, KIND_CODE[kind], i)
    if kind == "block":
        return [ct.permute_blocks(s, b, rng) for s, b in zip(sessions, bins)]
    if kind == "block_adjacent":
        return [ct.permute_blocks(s, b, rng, match_adjacent=True) for s, b in zip(sessions, bins)]
    if kind == "sequence":
        return [ct.permute_block_sequences(s, b, rng) for s, b in zip(sessions, bins)]
    if kind == "trial":
        return [ct.permute_trials(s, b, rng) for s, b in zip(sessions, bins)]
    return bins


def _design_job(args):
    kind, i, sessions, bins, rois, rs, purpose = args
    d = cp.build_design(sessions, permuted_bins(kind, i, sessions, bins, purpose), rois, rs)
    return i, d["n_prog"], d["n_neurons"], d["n_qual"], {r: sorted({si for si, _ in d["qual"][r]}) for r in rois}


def replay_design(sessions, rs, name, n_perm, workers, rois=None):
    """(n_prog, n_neurons, n_qual, qualifying sessions) of the observed labelling (index 0) and of permutations 1..n_perm of test `name`."""
    kind, window, labels, purpose, _ = rc.TESTS[name]
    rois = rois or cg.ROIS
    s = cp.with_window(sessions, window)
    bins = [x.true_bin if labels == "true" else x.belief_bin for x in s]
    jobs = [("obs" if i == 0 else kind, i, s, bins, rois, rs, purpose) for i in range(n_perm + 1)]
    if workers > 1:
        from concurrent.futures import ProcessPoolExecutor
        with ProcessPoolExecutor(workers) as ex:
            return list(ex.map(_design_job, jobs, chunksize=4))
    return [_design_job(j) for j in jobs]


def compare_design(replayed, test_rec, rois=None):
    """Replayed counts against the saved design_obs and design_null of a test-*.json record."""
    rois = rois or cg.ROIS
    obs, null = replayed[0], replayed[1:]
    saved = test_rec["design_null"]
    same = sum(1 for r, s in zip(null, saved) if [r[1], r[2]] == [s[0], s[1]])
    return {"observed_matches": [obs[1], obs[2]] == [test_rec["design_obs"]["n_prog"], test_rec["design_obs"]["n_neurons"]],
            "permutations_matching": same, "permutations": len(saved),
            "n_qual_observed": {r: obs[3][r] for r in rois},
            "n_qual_null": {r: [x[3][r] for x in null] for r in rois},
            "qualifying_sessions_observed": {r: obs[4][r] for r in rois},
            "qualifying_sessions_null": {r: [x[4][r] for x in null] for r in rois}}


def z_table(acc, rois=None):
    """Mean, SD and z-test (cellport.z_test, against 1/3) per region and progression level, from draws x 3 accuracies."""
    out = {}
    for r in rois or cg.ROIS:
        a = np.asarray(acc[r], float)
        out[r] = {"mean": a.mean(0).tolist(), "sd": a.std(0, ddof=1).tolist(), "p": [float(cp.z_test(a[:, k])) for k in range(3)]}
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["fill"])
    ap.add_argument("--extract-root", required=True)
    ap.add_argument("--prior", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--cache", action="store_true")
    a = ap.parse_args(argv)
    cell_env.require_platform_fixed(None)
    cell_env.check_environment()
    prior, o = Path(a.prior), Path(a.out)
    o.mkdir(parents=True, exist_ok=True)
    sel, gate = rc.jload(prior / "select.json"), rc.jload(prior / "gate.json")
    now = cell_env.platform_record()
    diff = [k for k in ("platform", "versions") if gate["platform"].get(k) != now.get(k)]
    if diff:
        raise SystemExit("refused: %s differ from the Addendum 2 run" % ", ".join(diff))
    os.environ["CELL_VAL_RULE"] = sel["val_rule"]
    g1 = cg.g1_integrity(HERE.parent / "data-members.tsv", a.extract_root)
    if not g1["passed"]:
        raise SystemExit("G1 failed: %s" % g1["detail"])
    sessions, rs = rc.load_sessions(a, o)
    rec = {"addendum": "ADDENDUM-3-2026-11-09", "platform": now, "python_build_same_as_a2": gate["platform"].get("python_build") == now.get("python_build"),
           "g1": g1, "blas": __import__("threadpoolctl").threadpool_info()}
    design = {}
    for name in rc.TESTS:
        test = rc.jload(prior / ("test-%s.json" % name))
        design[name] = compare_design(replay_design(sessions, rs, name, test["P"], a.workers), test)
        print("%s: observed matches %s; %d of %d permutations match the saved design counts" % (
            name, design[name]["observed_matches"], design[name]["permutations_matching"], design[name]["permutations"]))
    rec["design_replay"] = design
    spec = dict(cg.VARIANTS)[sel["variant_for_tests"]]
    acc, hp, des = cg.gate_draws(sessions, rs, [s.true_bin for s in sessions], rc.D_GATE, rc.GATE_PURPOSE["true"], spec, a.workers)
    g11 = gate["extra"]["true_template_descriptive_G11"]
    rec["true_template_z"] = z_table(acc)
    rec["g11_largest_difference_of_level_means"] = max(float(np.max(np.abs(np.mean(acc[r], 0) - np.array(g11["mean_per_region_level"][r])))) for r in cg.ROIS)
    rec["true_template_draws"] = {r: acc[r].tolist() for r in cg.ROIS}
    rc.jdump(rec, o / "a3_fill.json")
    print("G11 level means, largest difference from the saved gate.json:", rec["g11_largest_difference_of_level_means"])
    print("true-template z-test p:", {r: rec["true_template_z"][r]["p"] for r in cg.ROIS})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
