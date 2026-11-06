#!/usr/bin/env python3
"""Step 5 runner (DESIGN.md §4-§8). Per included subject (s = subject number - 101): 30 fake-label assignments
(3 of each run's 6 blocks in class 1), splits main, tool, block (fold = block mod 4), rules P1-P5
(../../step4-fmri-haxby/code/engine.py); and the injected-signal positive control (delta 0.5 and 1.0 SD on 6 seeded
features, class-1 windows) under main. One JSON line per (subject, arm, assignment, split) in
../runs/rows.step5.<subject>.jsonl. Resumable with a check of stored labels and seeds. --test: 2 assignments, 20 draws,
rows marked (the summary rejects them).

  python run_pamap2.py --features <dir> --subject subject101 --out-dir ../runs
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "step4-fmri-haxby" / "code"))
import engine  # noqa: E402

N_ASSIGN = 30
STREAM_ASSIGN, STREAM_INJECT, STREAM_SEED, STREAM_RULES = 51, 52, 53, 54
SPLITS = ("main", "tool", "block")
BLOCK_FOLDS = 4
DELTAS = (0.5, 1.0)
N_SIG = 6


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--subject", required=True, choices=[f"subject{i}" for i in range(101, 110)])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if not a.test:
        assert engine.VERSIONS["scikit-learn"] == "1.7.2" and engine.VERSIONS["numpy"] == "2.5.4", engine.VERSIONS
    info = json.loads((Path(a.features) / f"{a.subject}.json").read_text())
    if not info.get("included"):
        raise SystemExit(f"{a.subject} excluded: {info.get('reason')}")
    s = int(a.subject[7:]) - 101
    n_assign = 2 if a.test else N_ASSIGN
    if a.test:
        engine.N_PERM = 20
    out = Path(a.out_dir) / f"rows.step5.{a.subject}{'.test' if a.test else ''}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    z = np.load(Path(a.features) / f"{a.subject}.npz")
    X0, blk, run, b_run = z["X"], z["block"], z["run"], z["block_run"]
    sd = X0.std(axis=0)                                     # over the retained, block-assigned windows
    assigns = engine.within_run_assignments(b_run, n_assign, STREAM_ASSIGN, s)
    jobs = [("fake", 0.0, v_i, sp, v) for v_i, v in enumerate(assigns) for sp in SPLITS]
    jobs += [(f"pos_delta{d}", d, v_i, "main", v) for d in DELTAS for v_i, v in enumerate(assigns)]
    prev = {(r["subject"], r["arm"], r["assignment"], r["split"]): r for r in engine.read_rows(out)}
    for arm, delta, v_i, sp, v in jobs:
        si = SPLITS.index(sp)
        seed = int(np.random.default_rng([2026, STREAM_SEED, s, v_i, si]).integers(2**31 - 1))
        key = (a.subject, arm, v_i, sp)
        if key in prev:
            assert (prev[key]["labels"] == v.tolist() and prev[key]["seed"] == seed and prev[key]["n_perm"] == engine.N_PERM
                    and prev[key]["delta"] == delta), f"stored row differs: {key}"
            continue
        t0 = time.time()
        y = v[blk]
        X, cols = X0, []
        if delta > 0:
            cols = np.random.default_rng([2026, STREAM_INJECT, s, v_i]).choice(X0.shape[1], N_SIG, replace=False)
            X = X0.copy()
            X[np.ix_(y == 1, cols)] += delta * sd[cols]
        rng = np.random.default_rng([2026, STREAM_RULES, s, v_i, si, int(round(10 * delta))])
        fl = engine.folds_for(sp, X, y, blk, run, seed, BLOCK_FOLDS)
        row = {"step": 5, "subject": a.subject, "subject_index": s, "arm": arm, "prep": "windows2s", "delta": delta,
               "signal_features": [int(c) for c in cols], "assignment": v_i, "split": sp, "labels": v.tolist(),
               "n_samples": int(len(y)), "n_features": int(X.shape[1]), "seed": seed, "test": bool(a.test)}
        row.update(engine.run_rules(engine.sim.pipeline(), X, y, blk, run, fl, b_run, rng, seed))
        engine.write_row(out, row, t0)


if __name__ == "__main__":
    main()
