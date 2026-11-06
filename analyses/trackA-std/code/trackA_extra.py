#!/usr/bin/env python3
"""Track A extra analyses (pre-registered in PREREG-trackA.md; read that first).

Runs, per (session, visual area), three analyses that the planned script
ephys-matched-null.py does not do. The planned primary analysis (P1) is NOT here:
it is ephys-matched-null.py itself, run unchanged with --good-only.

  P2  standard decoder: L2 logistic regression on the top-k units ranked by |d'|, k
      chosen by 5-fold cross-validation inside calibration from K_GRID with the ranking
      recomputed inside every training fold (nested); final ranking on all calibration
      trials; held-out accuracy. Specificity null: the same procedure on random unit
      orderings (the ranking step is replaced by the random order), NULL_DRAWS draws.
  P3  information null for the planned readout: the planned best-split procedure rerun
      after shuffling 0/90 labels within strata of (half x temporal frequency x Allen
      stimulus block), where presentation order is randomised.
  C   calibration on spontaneous activity (grey screen). The three longest spontaneous
      epochs (each >= 240 s; otherwise C is skipped) lose their first 1 s and are cut
      into 4 equal blocks each (12 blocks, none spanning a gap); 2-s pseudo-trials tile
      each block. Schemes:
        iid          labels random per pseudo-trial; odd pseudo-trials select, even validate
        segment      blocks 1-6 one label, 7-12 the other (one stretch of time per label);
                     odd/even split; block shuffle = all C(12,6) = 924 assignments
        random_blocks  calibration blocks 1,2,5,6,9,10, held-out blocks 3,4,7,8,11,12; the
                     labels are assigned to blocks at random (3 of 6 per label in each set,
                     one of the 400 assignments drawn with the area's stream 13); block
                     shuffle = all C(6,3)^2 = 400 assignments, so the test is exact by
                     randomisation
      Tests: Q2 (held-out correct count against the held-out majority, one-sided binomial),
      trial shuffle (iid and segment only; labels permuted across pseudo-trials), block
      shuffle (segment and random_blocks), specificity (random orderings). Every null reruns
      the selection. Null draws that are NaN count as reaching the observed score
      (conservative); their number is reported.

Units: Allen quality == "good", the 0.5 Hz rate rule on the trials of that analysis,
>= 20 units per area. All areas whose acronym starts with "VIS" are computed; the
summary script chooses the area set. Random streams are per (session, area, analysis).

  python3 trackA_extra.py --dir <nwb folder> --sessions <ids> --out extra.jsonl
  python3 trackA_extra.py ... --worker 0 --of 4      # independent processes; never Pool
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import sys
import time
import zlib
from pathlib import Path

import h5py
import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("emn", HERE / "ephys-matched-null.py")
emn = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(emn)

SEED = 20261014
NULL_DRAWS = 200
K_GRID = (5, 10, 20, 40)
CV_FOLDS = 5
L2 = 1.0
PSEUDO_TRIAL_S = 2.0
LONG_EPOCH_S = 240.0
EPOCH_SKIP_S = 1.0
BLOCKS_PER_EPOCH = 4
N_EPOCHS = 3
N_BLOCKS = N_EPOCHS * BLOCKS_PER_EPOCH
CAL_BLOCKS = (0, 1, 4, 5, 8, 9)          # blocks 1,2,5,6,9,10 (1-based)
TEST_BLOCKS = (2, 3, 6, 7, 10, 11)       # blocks 3,4,7,8,11,12
NONCONVERGED = [0]


def rng_for(session: str, area: str, stream: int) -> np.random.Generator:
    return np.random.default_rng([SEED, int(session), zlib.crc32(area.encode()), stream])


def unit_table(path: Path):
    with h5py.File(path, "r") as f:
        u = f["units"]
        q = np.array([x.decode() if isinstance(x, bytes) else str(x) for x in u["quality"][:]])
        pres = np.asarray(u["presence_ratio"]) if "presence_ratio" in u else np.full(len(q), np.nan)
    return q == "good", pres


def dg_strata(path: Path, keep_idx: np.ndarray):
    """Temporal frequency and Allen stimulus block of the kept drifting-grating trials."""
    with h5py.File(path, "r") as f:
        t = f["intervals"]["drifting_gratings_presentations"]  # same table as emn.load_session (standard-table rerun)
        tf = np.asarray(t["temporal_frequency"])[keep_idx] if "temporal_frequency" in t else np.zeros(len(keep_idx))
        blk = np.asarray(t["stimulus_block"])[keep_idx] if "stimulus_block" in t else np.zeros(len(keep_idx))
    return tf.astype(float), blk.astype(float)


def invalid_intervals(path: Path):
    with h5py.File(path, "r") as f:
        if "invalid_times" not in f["intervals"]:
            return np.zeros((0, 2))
        iv = f["intervals/invalid_times"]
        return np.column_stack([np.asarray(iv["start_time"]), np.asarray(iv["stop_time"])])


def n_overlap(onsets, inv):
    if len(inv) == 0 or len(onsets) == 0:
        return 0
    a, b = onsets[:, None], onsets[:, None] + emn.RESPONSE_WINDOW[1]
    return int(((a < inv[None, :, 1]) & (b > inv[None, :, 0])).any(axis=1).sum())


def running(path: Path):
    with h5py.File(path, "r") as f:
        g = f.get("processing/running/running_speed")
        if g is None or "data" not in g:
            return None
        d = np.asarray(g["data"])
        ts = np.asarray(g["timestamps"]) if "timestamps" in g else None
    return None if ts is None else (ts, d)


def mean_speed(run, t0, t1):
    if run is None:
        return None
    ts, d = run
    m = (ts >= t0) & (ts < t1)
    return float(np.nanmean(d[m])) if m.any() else None


def spontaneous_blocks(path: Path):
    """Pseudo-trial onsets and their block index (0..11), or (None, reason)."""
    with h5py.File(path, "r") as f:
        iv = f["intervals"]
        name = next((k for k in iv if k.startswith("spontaneous")), None)
        if name is None:
            return None, "no spontaneous table"
        st, en = np.asarray(iv[name]["start_time"]), np.asarray(iv[name]["stop_time"])
    dur = en - st
    long_idx = [i for i in np.argsort(-dur) if dur[i] >= LONG_EPOCH_S][:N_EPOCHS]
    if len(long_idx) < N_EPOCHS:
        return None, f"fewer than {N_EPOCHS} spontaneous epochs >= {LONG_EPOCH_S:.0f} s"
    long_idx = sorted(long_idx, key=lambda i: st[i])               # time order
    onsets, block, edges = [], [], []
    for e, i in enumerate(long_idx):
        a, b = st[i] + EPOCH_SKIP_S, en[i]
        cuts = np.linspace(a, b, BLOCKS_PER_EPOCH + 1)
        for k in range(BLOCKS_PER_EPOCH):
            t = cuts[k]
            edges.append((float(cuts[k]), float(cuts[k + 1])))
            while t + PSEUDO_TRIAL_S <= cuts[k + 1]:
                onsets.append(t)
                block.append(e * BLOCKS_PER_EPOCH + k)
                t += PSEUDO_TRIAL_S
    return (np.array(onsets), np.array(block), edges), None


def area_counts(spikes, sel, onsets):
    counts = np.array([emn.trial_counts(spikes[u], onsets) for u in sel])
    rate = counts.mean(axis=1) / (emn.RESPONSE_WINDOW[1] - emn.RESPONSE_WINDOW[0])
    return counts[rate >= emn.MIN_RATE_HZ], rate >= emn.MIN_RATE_HZ


def best_split_score(counts, labels, cal, test, order=None):
    """The planned readout: rank by signed calibration d', best cut on calibration,
    two-pool readout, held-out accuracy (%). order=None means the informed ranking."""
    z = emn.zscore(counts, cal)
    if order is None:
        seps = np.array([emn.dprime(counts[u][cal][labels[cal] == 0], counts[u][cal][labels[cal] == 1])
                         for u in range(counts.shape[0])])
        order = np.argsort(-seps)
    sc, _ = emn.best_division(z, order, labels, cal, test, 2)
    return sc


def majority(labels, test):
    return max((labels[test] == 0).mean(), (labels[test] == 1).mean()) * 100


def pval(null, obs):
    null = np.asarray(null, float)
    nan = np.isnan(null)
    return float((1 + (null[~nan] >= obs).sum() + nan.sum()) / (len(null) + 1)), int(nan.sum())


# ---------------------------------------------------------------- P2: standard decoder
def logistic_fit(X, y, lam=L2, iters=25):
    """L2-penalised logistic regression (0.5 * lam * ||w||^2, intercept unpenalised) by Newton steps."""
    n, p = X.shape
    Xb = np.hstack([np.ones((n, 1)), X])
    w = np.zeros(p + 1)
    pen = np.full(p + 1, lam)
    pen[0] = 0.0
    for _ in range(iters):
        eta = np.clip(Xb @ w, -30, 30)
        mu = 1.0 / (1.0 + np.exp(-eta))
        g = Xb.T @ (mu - y) + pen * w
        H = (Xb * (mu * (1 - mu))[:, None]).T @ Xb + np.diag(pen + 1e-9)
        step = np.linalg.solve(H, g)
        w -= step
        if np.max(np.abs(step)) < 1e-6:
            return w
    NONCONVERGED[0] += 1
    return w


def logistic_acc(Xtr, ytr, Xte, yte):
    w = logistic_fit(Xtr, ytr)
    pred = (np.hstack([np.ones((len(Xte), 1)), Xte]) @ w) > 0
    return float((pred.astype(int) == yte).mean() * 100)


def abs_rank(counts, labels, idx):
    seps = np.array([emn.dprime(counts[u][idx][labels[idx] == 0], counts[u][idx][labels[idx] == 1])
                     for u in range(counts.shape[0])])
    return np.argsort(-np.abs(seps))


def topk_decoder(counts, z, labels, cal, test, fixed_order=None):
    """k by 5-fold CV inside calibration (folds = calibration position mod 5). With
    fixed_order=None the ranking is recomputed on each training fold (nested) and finally
    on all calibration trials; with a fixed (random) order it is used as is. Ties go to
    the smaller k. Returns (held-out %, k)."""
    ks = [k for k in K_GRID if k <= counts.shape[0]]
    folds = np.arange(len(cal)) % CV_FOLDS
    y = labels.astype(float)
    best_k, best_cv = ks[0], -np.inf
    fold_orders = [fixed_order if fixed_order is not None else abs_rank(counts, labels, cal[folds != f])
                   for f in range(CV_FOLDS)]
    for k in ks:
        accs = []
        for f in range(CV_FOLDS):
            tr, va = cal[folds != f], cal[folds == f]
            X = z[fold_orders[f][:k]].T
            accs.append(logistic_acc(X[tr], y[tr], X[va], y[va]))
        cv = float(np.mean(accs))
        if cv > best_cv + 1e-12:
            best_cv, best_k = cv, k
    order = fixed_order if fixed_order is not None else abs_rank(counts, labels, cal)
    X = z[order[:best_k]].T
    return logistic_acc(X[cal], y[cal], X[test], y[test]), best_k


def run_p2(counts, labels, cal, test, rng):
    z = emn.zscore(counts, cal)
    obs, k = topk_decoder(counts, z, labels, cal, test)
    res = [topk_decoder(counts, z, labels, cal, test, fixed_order=rng.permutation(counts.shape[0]))
           for _ in range(NULL_DRAWS)]
    null = np.array([r[0] for r in res])
    p, nn = pval(null, obs)
    return {"obs": obs, "k": int(k), "null_mean": float(np.nanmean(null)), "p": p, "null_nan": nn,
            "null_k": np.bincount([r[1] for r in res], minlength=max(K_GRID) + 1)[list(K_GRID)].tolist(),
            "const": majority(labels, test)}


# ---------------------------------------------------------------- P3: information null
def shuffle_strata(labels, strata, rng):
    out = labels.copy()
    for s_ in np.unique(strata):
        idx = np.where(strata == s_)[0]
        out[idx] = rng.permutation(labels[idx])
    return out


def run_p3(counts, labels, cal, test, strata, rng):
    obs = best_split_score(counts, labels, cal, test)
    null = np.array([best_split_score(counts, shuffle_strata(labels, strata, rng), cal, test)
                     for _ in range(NULL_DRAWS)])
    p, nn = pval(null, obs)
    return {"obs": obs, "null_mean": float(np.nanmean(null)), "p": p, "null_nan": nn,
            "const": majority(labels, test), "n_strata": int(len(np.unique(strata)))}


# ---------------------------------------------------------------- C: calibration on grey screen
def labels_from_blocks(assign, block):
    return np.asarray(assign)[block].astype(int)


def run_c(counts, block, scheme, rng):
    n = counts.shape[1]
    if scheme == "random_blocks":
        cal = np.where(np.isin(block, CAL_BLOCKS))[0]
        test = np.where(np.isin(block, TEST_BLOCKS))[0]
        c1 = [CAL_BLOCKS[i] for i in rng.choice(6, 3, replace=False)]
        c2 = [TEST_BLOCKS[i] for i in rng.choice(6, 3, replace=False)]
        assign = [1 if (b in c1 or b in c2) else 0 for b in range(N_BLOCKS)]
    else:
        cal, test = np.arange(0, n, 2), np.arange(1, n, 2)
        assign = [0] * (N_BLOCKS // 2) + [1] * (N_BLOCKS // 2)
    if scheme == "iid":
        labels = rng.permutation(np.arange(n) % 2)
    else:
        labels = labels_from_blocks(assign, block)
    obs = best_split_score(counts, labels, cal, test)
    maj = majority(labels, test)
    correct = int(round(obs / 100 * len(test)))
    out = {"acc": obs, "const": maj, "n_cal": int(len(cal)), "n_test": int(len(test)),
           "q2_p": float(stats.binom.sf(correct - 1, len(test), maj / 100))}
    spec = [best_split_score(counts, labels, cal, test, order=rng.permutation(counts.shape[0])) for _ in range(NULL_DRAWS)]
    out["spec_p"], out["spec_nan"] = pval(spec, obs)
    if scheme in ("iid", "segment"):
        trial = [best_split_score(counts, rng.permutation(labels), cal, test) for _ in range(NULL_DRAWS)]
        out["full_p"], out["full_nan"] = pval(trial, obs)
    if scheme == "segment":
        scores = []
        for ones in itertools.combinations(range(N_BLOCKS), N_BLOCKS // 2):
            a = [1 if b in ones else 0 for b in range(N_BLOCKS)]
            scores.append(best_split_score(counts, labels_from_blocks(a, block), cal, test))
    elif scheme == "random_blocks":
        scores = []
        for c1 in itertools.combinations(CAL_BLOCKS, 3):
            for c2 in itertools.combinations(TEST_BLOCKS, 3):
                a = [1 if (b in c1 or b in c2) else 0 for b in range(N_BLOCKS)]
                scores.append(best_split_score(counts, labels_from_blocks(a, block), cal, test))
    if scheme != "iid":
        scores = np.asarray(scores, float)          # exact: includes the observed assignment
        nan = np.isnan(scores)
        out["block_p"] = float(((scores[~nan] >= obs).sum() + nan.sum()) / len(scores))
        out["block_n"], out["block_nan"] = int(len(scores)), int(np.isnan(scores).sum())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--sessions", required=True, help="comma-separated, in the order of sessions_trackA.csv")
    ap.add_argument("--out", required=True, help="JSON lines; existing (session, area) rows are skipped")
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--only", default="p2,p3,c", help="subset of p2,p3,c (for smoke tests)")
    args = ap.parse_args()
    only = set(args.only.split(","))
    out = Path(args.out)
    done = set()
    if out.exists():
        for ln in out.read_text(encoding="utf-8").splitlines():
            r = json.loads(ln)
            done.add((r["session"], r["area"]))
    for si, sid in enumerate(args.sessions.split(",")):
        if si % args.of != args.worker:
            continue
        path = Path(args.dir) / f"session_{sid}.nwb"
        if not path.exists():
            print(f"SESSION {sid}: FILE MISSING", flush=True)
            continue
        t0 = time.time()
        ids, spikes, area, onset, ori = emn.load_session(path)
        good, pres = unit_table(path)
        area = np.where(good, area, "excluded-quality")
        keep_idx = np.where(np.isin(ori, emn.ORIENTATIONS))[0]
        order = np.argsort(onset[keep_idx])
        keep_idx = keep_idx[order]
        onsets, labels = onset[keep_idx], (ori[keep_idx] == emn.ORIENTATIONS[1]).astype(int)
        tf, sblk = dg_strata(path, keep_idx)
        half = len(onsets) // 2
        cal, test = np.arange(half), np.arange(half, len(onsets))
        halfid = (np.arange(len(onsets)) >= half).astype(int)
        strata = np.array([f"{h}|{a}|{b}" for h, a, b in zip(halfid, tf, sblk)])
        inv = invalid_intervals(path)
        run = running(path)
        sp, why = spontaneous_blocks(path)
        sess_info = {"n_dg_trials": int(len(onsets)), "n_class1": int(labels.sum()),
                     "cal_end": float(onsets[half - 1]) if half else None,
                     "test_start": float(onsets[half]) if half < len(onsets) else None,
                     "dg_invalid_overlap": n_overlap(onsets, inv),
                     "run_cal": mean_speed(run, onsets[0], onsets[half - 1] + 2) if half else None,
                     "run_test": mean_speed(run, onsets[half], onsets[-1] + 2) if half < len(onsets) else None,
                     "c_skipped": why}
        if sp is not None:
            sp_on, sp_blk, edges = sp
            sess_info.update({"n_pseudo": int(len(sp_on)), "block_edges": edges,
                              "pseudo_invalid_overlap": n_overlap(sp_on, inv),
                              "run_blocks": [mean_speed(run, a, b) for a, b in edges]})
        for a in sorted(set(area)):
            if not a.startswith("VIS") or (sid, a) in done:
                continue
            NONCONVERGED[0] = 0
            sel = np.where(area == a)[0]
            row = {"session": sid, "area": a, **sess_info}
            dg, kept = area_counts(spikes, sel, onsets) if len(sel) else (np.zeros((0, len(onsets))), np.array([], bool))
            row["n_units_dg"] = int(dg.shape[0])
            row["n_low_presence"] = int((pres[sel][kept] < 0.9).sum()) if len(sel) else 0
            if dg.shape[0] >= emn.MIN_UNITS_PER_AREA:
                if "p3" in only:
                    row["p3"] = run_p3(dg, labels, cal, test, strata, rng_for(sid, a, 3))
                if "p2" in only:
                    row["p2"] = run_p2(dg, labels, cal, test, rng_for(sid, a, 2))
            if sp is not None and len(sel):
                spc, _ = area_counts(spikes, sel, sp_on)
                row["n_units_spont"] = int(spc.shape[0])
                if "c" in only and spc.shape[0] >= emn.MIN_UNITS_PER_AREA:
                    row["c_iid"] = run_c(spc, sp_blk, "iid", rng_for(sid, a, 11))
                    row["c_segment"] = run_c(spc, sp_blk, "segment", rng_for(sid, a, 12))
                    row["c_random_blocks"] = run_c(spc, sp_blk, "random_blocks", rng_for(sid, a, 13))
            row["logistic_nonconverged"] = NONCONVERGED[0]
            with out.open("a", encoding="utf-8") as fh:             # every VIS area gets a row
                fh.write(json.dumps(row) + "\n")
        print(f"SESSION {sid}: DONE in {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
