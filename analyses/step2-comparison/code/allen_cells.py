#!/usr/bin/env python3
"""Step 2 Allen cells (DESIGN.md §15 "Allen cells", §5b positive control; addendum DESIGN-v2-ADDENDUM.md).

Per (session, visual area in STD6) and per label scheme, the five permutation rules of sim.py (P1 binomial,
P2 scikit-learn permutation_test_score, P3 within-run, P4 training labels only, P5 block permutation with refit)
with the one step 2 pipeline (sim.pipeline: StandardScaler, SelectKBest f_classif k = 20, LogisticRegression C = 1,
max_iter 1000), under two splits: S-main (shuffled KFold 5) and S-tool (unshuffled StratifiedKFold 5, re-split for
every permuted label vector). 200 permutation draws per rule.

Schemes (fake labels follow 24 recording blocks; data and blocks as step 1, ../../step1-decomposition):
  shared24, sep24        spontaneous activity, 2-s pseudo-trials, 3 epochs x 8 blocks (step 1 spont_onsets(path, 8))
  dg_shared24, dg_sep24  drifting-grating trials in time order cut into 24 blocks (step 1 dg layout)
  Label vectors: shared = 12 of 24 blocks label 1; sep = 6 of the 12 calibration-pair blocks and 6 of the 12
  held-out-pair blocks label 1 (step 1 pair split). Under S-main and S-tool both are block designs whose blocks are
  shared by training and test folds; sep differs from shared only in this balance constraint (addendum §2).
  P5 null set = the scheme's own assignment set (exact by randomisation; sanity cell).
  Positive control pos_dg24 (§5b): real 0 vs 90 degree labels; the 0-degree trials (time order) are cut into 12
  chunks and the 90-degree trials into 12 chunks, and the chunks alternate (0, 90, 0, ...) as 24 blocks; P5 null
  set = all balanced assignments of the 24 blocks.
Extra splits beyond §15 (addendum 1 §2): S-block = GroupKFold(5) by the 24 blocks (deterministic); for sep24 and
dg_sep24 also "pair" = the step 1 pair split, one direction (train on calibration-pair blocks, test on held-out-pair
blocks), as step 1.
P3 runs = the recording's natural runs: the 3 spontaneous epochs (8 blocks each) for shared24/sep24, the Allen
stimulus blocks of the drifting-grating trials for dg_*; pos_dg24 (reordered trials) uses 4 runs of 6 blocks.
Area inclusion as step 1: spontaneous schemes need >= 20 units in both the 12-block and the 24-block counts; a
session is skipped if it has fewer than 3 long spontaneous epochs; every scheme asserts 24 blocks.
LogisticRegression non-convergence warnings are counted per row (n_nonconverged), not shown.
Seeds: labels tax.rng_for(session, area, STREAM + 200) with step 1 streams (shared24 24, sep24 22; dg + 90);
rules and folds tax.rng_for(session, area, STREAM + 1000 * (split_index + 1)) (split_index main 0, tool 1, block 2,
pair 3); the same label vector is used under every split (paired on labels);
pos_dg24 stream 470. One JSON line per (session, area, scheme, split) with the p of every rule, the observed
accuracy (mean of fold accuracies), and the P5 null accuracies (for the group-level column).

  python allen_cells.py --dir <allen nwb folder> --out ../runs_allen/rows.w0.jsonl --worker 0 --of 1
"""
from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import time
import warnings
from pathlib import Path

import numpy as np

import sim

HERE = Path(__file__).resolve().parent
S1 = HERE.parents[1] / "step1-decomposition"
_spec = importlib.util.spec_from_file_location("dec", S1 / "code" / "decompose.py")
dec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dec)
tax, emn = dec.tax, dec.emn
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)

SESSIONS = HERE.parents[1] / "trackA-std" / "sessions_trackA.csv"
SCHEMES = ("shared24", "sep24", "dg_shared24", "dg_sep24", "pos_dg24")
SPLITS = ("main", "tool", "block", "pair")   # block and pair: addendum 1 §2, cells beyond §15 (author 2026-10-21)
N_PERM = 200
STREAM = {"shared24": 24 + 200, "sep24": 22 + 200, "dg_shared24": 90 + 24 + 200, "dg_sep24": 90 + 22 + 200,
          "pos_dg24": 470}


def balanced(idx_sets, K):
    """Draw function: in each index set, half of the blocks get label 1."""
    def draw(rng):
        a = np.zeros(K, int)
        for s in idx_sets:
            a[rng.choice(s, len(s) // 2, replace=False)] = 1
        return a
    return draw


def pos_control(dgc, ori, on):
    """Positive control: counts reordered into 24 alternating blocks of real 0- and 90-degree trials."""
    K = 24
    i0 = np.where(ori == 0)[0]
    i9 = np.where(ori == 90)[0]
    c0, c9 = np.array_split(i0[np.argsort(on[i0])], 12), np.array_split(i9[np.argsort(on[i9])], 12)
    order, block = [], []
    for j in range(12):
        order += list(c0[j]); block += [2 * j] * len(c0[j])
        order += list(c9[j]); block += [2 * j + 1] * len(c9[j])
    return dgc[:, np.array(order)], np.array(block), np.arange(K) % 2, balanced([np.arange(K)], K)


def labels_for(kind, block, rng):
    K = int(block.max()) + 1
    if kind.endswith("shared24"):
        sets = [np.arange(K)]
    else:
        cb, tb = dec.pair_split(K)
        sets = [cb, tb]
    draw = balanced(sets, K)
    return draw(rng), draw


def run_one(counts, block, lab, draw, split, rng, seed_int, runs, kind="shared24"):
    X = counts.T.astype(float)
    y = lab[block]
    est = sim.pipeline()
    assert int(block.max()) + 1 == 24
    if split == "main":
        fl = sim.folds("main", X, y, block, seed=seed_int)
    elif split == "tool":
        fl = sim.Resplit(sim.splitter("tool", seed_int), block)
    elif split == "block":
        fl = sim.folds("block", X, y, block, seed=seed_int, n_block_folds=5)
    elif split == "pair":
        cb, tb = dec.pair_split(24)
        a, b = np.where(np.isin(block, cb))[0], np.where(np.isin(block, tb))[0]
        fl = [(a, b)]                                     # calibration pairs -> held-out pairs, as step 1
    else:
        raise ValueError(split)
    out = {}
    out["acc"] = sim.cv_correct(est, X, y, fl)[1]
    if split == "pair":
        # one held-out fold: sim.p1_binomial counts all trials; use the held-out trials as n (review, final check)
        from scipy import stats as _st
        c, _ = sim.cv_correct(est, X, y, fl)
        out["P1"] = float("nan") if not np.isfinite(c) else float(_st.binom.sf(c - 1, len(fl[0][1]), 0.5))
    else:
        out["P1"] = sim.p1_binomial(est, X, y, fl)
    out["P2"] = sim.p2_sklearn(est, X, y, fl, N_PERM, seed_int)
    p3 = sim.p3_within_run(est, X, y, fl, runs, N_PERM, rng)
    out["P3"], out["P3_error"] = (None, True) if p3 is None else (p3, False)
    out["P4"] = sim.p4_train_only(est, X, y, fl, N_PERM, rng)
    _, null5, out["P5"] = sim.block_permutation_test_score(est, X, y, block, fl, N_PERM, rng, draw=draw)
    out["P5_null_acc"] = [None if not np.isfinite(v) else round(float(v), 6) for v in null5]
    return out


def run_counted(*a, **k):
    from sklearn.exceptions import ConvergenceWarning
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always", ConvergenceWarning)
        out = run_one(*a, **k)
    out["n_nonconverged"] = sum(1 for x in w if issubclass(x.category, ConvergenceWarning))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--sessions", default=None, help="comma-separated session ids (default: all 32)")
    ap.add_argument("--schemes", default=",".join(SCHEMES))
    ap.add_argument("--max-areas", type=int, default=None, help="timing tests only")
    args = ap.parse_args()
    sess = [r["session_id"] for r in csv.DictReader(SESSIONS.open(encoding="utf-8"))]
    if args.sessions:
        sess = args.sessions.split(",")
    schemes = args.schemes.split(",")
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        for l in out.read_text().splitlines():
            r = json.loads(l)
            done.add((r["session"], r["area"], r["scheme"], r["split"]))
    n_area = 0
    for si, sid in enumerate(sess):
        if si % args.of != args.worker:
            continue
        path = Path(args.dir) / f"session_{sid}.nwb"
        if not path.exists():
            print(f"SESSION {sid}: FILE MISSING", flush=True)
            continue
        ids, spikes, area, onset, ori = emn.load_session(path)
        good, _ = tax.unit_table(path)
        area = np.where(good, area, "excluded-quality")
        sp, why = tax.spontaneous_blocks(path)
        if sp is None:
            print(f"SESSION {sid}: skipped ({why})", flush=True)
            continue
        sp_on = sp[0]
        on24, blk24 = dec.spont_onsets(path, 8)
        assert int(blk24.max()) + 1 == 24
        o = np.argsort(onset)
        dg_on, dg_ori = np.asarray(onset)[o], np.asarray(ori)[o]
        _, dg_sblk = tax.dg_strata(path, o)
        dg_runs = np.unique(dg_sblk, return_inverse=True)[1]
        dg_blk = np.concatenate([np.full(len(c), i) for i, c in enumerate(np.array_split(np.arange(len(dg_on)), 24))])
        for a in sorted(set(area)):
            if a not in dec.STD6:
                continue
            if args.max_areas is not None and n_area >= args.max_areas:
                return
            sel = np.where(area == a)[0]
            spc, _ = tax.area_counts(spikes, sel, sp_on)
            c24, _ = tax.area_counts(spikes, sel, on24)
            dgc, _ = tax.area_counts(spikes, sel, dg_on)
            n_area += 1
            for kind in schemes:
                if kind in ("shared24", "sep24"):
                    counts, block, runs = c24, blk24, blk24 // 8
                    if spc.shape[0] < emn.MIN_UNITS_PER_AREA:
                        continue
                else:
                    counts, block, runs = dgc, dg_blk, dg_runs
                if counts.shape[0] < emn.MIN_UNITS_PER_AREA:
                    continue
                if kind == "pos_dg24":
                    counts, block, lab, draw = pos_control(dgc, dg_ori, dg_on)
                    runs = block // 6
                else:
                    lab, draw = labels_for(kind, block, tax.rng_for(sid, a, STREAM[kind]))
                for s_i, split in enumerate(SPLITS):
                    if split == "pair" and kind not in ("sep24", "dg_sep24"):
                        continue
                    if (sid, a, kind, split) in done:
                        continue
                    t = time.time()
                    rng = tax.rng_for(sid, a, STREAM[kind] + 1000 * (s_i + 1))
                    seed_int = int(rng.integers(2**31 - 1))
                    row = {"session": sid, "area": a, "scheme": kind, "split": split, "n_units": int(counts.shape[0]),
                           "n_trials": int(counts.shape[1]), "labels": [int(v) for v in lab],
                           "n_p3_runs": int(len(np.unique(runs)))}
                    row.update(run_counted(counts, block, lab, draw, split, rng, seed_int, runs, kind))
                    row["seconds"] = round(time.time() - t, 1)
                    with out.open("a", encoding="utf-8") as fh:
                        fh.write(json.dumps(row) + "\n")
                    print(f"  {sid} {a} {kind} {split}: {row['seconds']} s", flush=True)


if __name__ == "__main__":
    main()
