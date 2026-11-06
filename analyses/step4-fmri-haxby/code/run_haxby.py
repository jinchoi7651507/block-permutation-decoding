#!/usr/bin/env python3
"""Step 4 runner (DESIGN.md §4-§8). Per included subject (s = subject number - 1): 30 fake-label assignments
(half of each run's blocks in class 1), two preprocessings (detrended, raw), four splits (main, tool, run, block with
fold = block mod 5), rules P1-P5 (engine.py); and the positive control (face vs house blocks only, detrended) under
main and run. One JSON line per (subject, arm, preprocessing, assignment, split) in ../runs/rows.step4.<subject>.jsonl.
Resumable: rows already written are checked against the recomputed labels and seed, then skipped. --test runs 2
assignments with 20 draws and marks the rows (the summary rejects them).

  python run_haxby.py --features <dir> --subject subj1 --out-dir ../runs
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np

import engine

N_ASSIGN = 30
STREAM_ASSIGN, STREAM_SEED, STREAM_RULES = 41, 42, 43
SPLITS = ("main", "tool", "run", "block")
BLOCK_FOLDS = 5
PREPS = ("detrended", "raw")


def jobs_for(b_run, b_cat, s, n_assign):
    jobs = []
    for v_i, v in enumerate(engine.within_run_assignments(b_run, n_assign, STREAM_ASSIGN, s)):
        for prep in PREPS:
            for sp in SPLITS:
                jobs.append(("fake", prep, v_i, sp, v))
    for sp in ("main", "run"):
        jobs.append(("pos_face_house", "detrended", 0, sp, (b_cat == "face").astype(int)))
    return jobs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--features", required=True)
    ap.add_argument("--subject", required=True, choices=[f"subj{i}" for i in range(1, 7)])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if not a.test:
        assert engine.VERSIONS["scikit-learn"] == "1.7.2" and engine.VERSIONS["numpy"] == "2.5.4", engine.VERSIONS
    info = json.loads((Path(a.features) / f"{a.subject}.json").read_text())
    if not info.get("included"):
        raise SystemExit(f"{a.subject} excluded: {info.get('reason')}")
    s = int(a.subject[4:]) - 1
    n_assign = 2 if a.test else N_ASSIGN
    if a.test:
        engine.N_PERM = 20
    out = Path(a.out_dir) / f"rows.step4.{a.subject}{'.test' if a.test else ''}.jsonl"
    out.parent.mkdir(parents=True, exist_ok=True)
    z = np.load(Path(a.features) / f"{a.subject}.npz", allow_pickle=False)
    blk, run, b_run, b_cat = z["block"], z["run"], z["block_run"], z["block_category"]
    prev = {(r["subject"], r["arm"], r["prep"], r["assignment"], r["split"]): r for r in engine.read_rows(out)}
    for arm, prep, v_i, sp, v in jobs_for(b_run, b_cat, s, n_assign):
        X = z["X_detrended"] if prep == "detrended" else z["X_raw"]
        bb, rr, br = blk, run, b_run
        if arm == "pos_face_house":                       # keep face and house blocks only, renumbered 0..K'-1
            keepb = np.where(np.isin(b_cat, ("face", "house")))[0]
            m = np.isin(blk, keepb)
            remap = -np.ones(len(b_run), int)
            remap[keepb] = np.arange(len(keepb))
            X, bb, rr, br, v = X[m], remap[blk[m]], run[m], b_run[keepb], v[keepb]
        si = SPLITS.index(sp)
        seed = int(np.random.default_rng([2026, STREAM_SEED, s, v_i, si]).integers(2**31 - 1))
        key = (a.subject, arm, prep, v_i, sp)
        if key in prev:
            assert prev[key]["labels"] == v.tolist() and prev[key]["seed"] == seed and prev[key]["n_perm"] == engine.N_PERM, \
                f"stored row differs: {key}"
            continue
        t0 = time.time()
        y = v[bb]
        rng = np.random.default_rng([2026, STREAM_RULES, s, v_i, si, int(arm != "fake"), PREPS.index(prep)])
        fl = engine.folds_for(sp, X, y, bb, rr, seed, BLOCK_FOLDS)
        row = {"step": 4, "subject": a.subject, "subject_index": s, "arm": arm, "prep": prep, "assignment": v_i,
               "split": sp, "labels": v.tolist(), "n_samples": int(len(y)), "n_features": int(X.shape[1]), "seed": seed,
               "test": bool(a.test)}
        row.update(engine.run_rules(engine.sim.pipeline(), X, y, bb, rr, fl, br, rng, seed))
        engine.write_row(out, row, t0)


if __name__ == "__main__":
    main()
