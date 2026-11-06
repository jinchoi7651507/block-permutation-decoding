#!/usr/bin/env python3
"""Step 1 decomposition of the fake-label pass rate, design v2 (post hoc; read ../DESIGN.md).

Per (session, visual area in STD6) it computes, for several label schemes and readouts, the
p values of held-out validation (binomial), block-label permutations with the readout refit
in every draw (rerun) or held fixed (fixed), trial-label permutations (rerun/fixed), circular
shifts (rerun), and random unit orders (spec); a positive control with injected signal; the
same schemes on real drifting-grating trials; and the block-number sweep with three
predictions of the binomial test's false-positive rate.

For iid, sep (= Track A random_blocks) and segment the sel readout consumes Track A's streams
(11, 13, 12) in Track A's order, so its binom / spec / trl_rerun / blk_rerun reproduce
trackA-std/runs/extra.jsonl exactly (gate in summarize.py).

  python3 decompose.py --dir <nwb folder> --sessions <ids> --out rows.jsonl [--worker i --of n]
"""
from __future__ import annotations

import argparse
import importlib.util
import itertools
import json
import math
import time
from pathlib import Path

import h5py
import numpy as np
from scipy import stats

HERE = Path(__file__).resolve().parent
TA = HERE.parents[1] / "trackA-std" / "code"
_spec = importlib.util.spec_from_file_location("tax", TA / "trackA_extra.py")
tax = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tax)
emn = tax.emn

STD6 = ("VISp", "VISl", "VISal", "VISrl", "VISam", "VISpm")
N_TRL = 200           # trial permutations (all readouts)
N_SPEC = 200          # random unit orders (sel, gate schemes)
N_CIRC = 200
N_BLK_MC = 1000       # Monte Carlo block assignments, cheap readouts
N_BLK_MC_LR = 200     # Monte Carlo block assignments, logistic readouts (rerun only)
N_COND_MC = 20000
LR_K = 20
DELTAS = (0.1, 0.2, 0.4)
INJ_FRAC = 0.10
ALPHA = 0.05
CHEAP = ("sel", "rank", "nosel", "nosel0")
LOGISTIC = ("lr_topk", "lr_all")


# ================================================================ readouts
def division_pred(z, order, k, labels, cal, sign=None):
    """Predicted class (0/1) on all trials. Mapping fixed on calibration (as emn.division_score)
    or, if sign is given, by that label-free rule (sign True: higher pool a -> class 0)."""
    a, b = order[:k], order[k:]
    diff = z[a].mean(axis=0) - z[b].mean(axis=0)
    hi0 = sign if sign is not None else diff[cal][labels[cal] == 0].mean() > diff[cal][labels[cal] == 1].mean()
    return np.where((diff > 0) if hi0 else (diff <= 0), 0, 1)


def acc(pred, labels, test):
    return float((pred[test] == labels[test]).mean() * 100)


class Readouts:
    """All readouts for one (counts, cal, test). fit(name, labels) -> (held-out %, predictions)."""

    def __init__(self, counts, cal, test, rnd_order, rnd_sign):
        self.counts, self.cal, self.test = counts, cal, test
        self.z = emn.zscore(counts, cal)
        self.n = counts.shape[0]
        self.rnd_order, self.rnd_sign = rnd_order, rnd_sign

    def _dprime(self, labels):
        c, cal = self.counts, self.cal
        return np.array([emn.dprime(c[u][cal][labels[cal] == 0], c[u][cal][labels[cal] == 1]) for u in range(self.n)])

    def _logistic(self, units, labels):
        X = self.z[units].T
        w = tax.logistic_fit(X[self.cal], labels[self.cal].astype(float))
        return ((np.hstack([np.ones((X.shape[0], 1)), X]) @ w) > 0).astype(int)

    def fit(self, name, labels):
        cal, test = self.cal, self.test
        if name == "sel":                                   # planned readout: d' ranking + cut search
            order = np.argsort(-self._dprime(labels))
            sc, k = emn.best_division(self.z, order, labels, cal, test, 2)
            pred = division_pred(self.z, order, k, labels, cal)
            assert not np.isfinite(sc) or abs(acc(pred, labels, test) - sc) < 1e-9
            return sc, pred
        if name == "rank":                                  # d' ranking, cut fixed at n//2
            order = np.argsort(-self._dprime(labels))
            pred = division_pred(self.z, order, self.n // 2, labels, cal)
        elif name == "nosel":                               # label-free pools, mapping fitted on calibration
            pred = division_pred(self.z, self.rnd_order, self.n // 2, labels, cal)
        elif name == "nosel0":                              # label-free pools and mapping
            pred = division_pred(self.z, self.rnd_order, self.n // 2, labels, cal, sign=self.rnd_sign)
        elif name == "lr_topk":                             # top-20 |d'| on calibration, L2 logistic
            units = np.argsort(-np.abs(self._dprime(labels)))[:min(LR_K, self.n)]
            pred = self._logistic(units, labels)
        elif name == "lr_all":                              # all units, L2 logistic
            pred = self._logistic(np.arange(self.n), labels)
        else:
            raise ValueError(name)
        return acc(pred, labels, test), pred

    def spec_score(self, labels, order):
        return tax.best_split_score(self.counts, labels, self.cal, self.test, order=order)


# ================================================================ p values
def mc_p(null, obs):
    """(1 + #{null >= obs} + #NaN) / (N + 1), and the NaN count."""
    s = np.asarray(null, float)
    nan = np.isnan(s)
    return float((1 + (s[~nan] >= obs).sum() + nan.sum()) / (len(s) + 1)), int(nan.sum())


def exact_p(null, obs):
    """Enumerated assignments including the observed one."""
    s = np.asarray(null, float)
    nan = np.isnan(s)
    return float(((s[~nan] >= obs).sum() + nan.sum()) / len(s)), int(nan.sum())


def binom_p(pred, labels, test):
    maj = tax.majority(labels, test)
    correct = int((pred[test] == labels[test]).sum())
    return float(stats.binom.sf(correct - 1, len(test), maj / 100))


# ================================================================ label schemes
def pair_split(K):
    """Blocks paired in time order; pairs alternate calibration / held-out (Track A layout)."""
    pair = (np.arange(K) // 2) % 2
    return np.where(pair == 0)[0], np.where(pair == 1)[0]


class Scheme:
    """labels, cal, test, block; assignments(): label vectors of the admissible block null."""

    def __init__(self, kind, block, rng, n_trials):
        self.kind, self.block, self.rng = kind, block, rng
        K = int(block.max()) + 1
        self.K = K
        n = n_trials
        odd_even = (np.arange(0, n, 2), np.arange(1, n, 2))
        if kind == "iid":
            self.cal, self.test = odd_even
            self.labels = rng.permutation(np.arange(n) % 2)
            self.exact = None
        elif kind == "sep":                                  # Track A random_blocks (K = 12)
            self.cal = np.where(np.isin(block, tax.CAL_BLOCKS))[0]
            self.test = np.where(np.isin(block, tax.TEST_BLOCKS))[0]
            c1 = [tax.CAL_BLOCKS[i] for i in rng.choice(6, 3, replace=False)]
            c2 = [tax.TEST_BLOCKS[i] for i in rng.choice(6, 3, replace=False)]
            self.assign = np.array([1 if (b in c1 or b in c2) else 0 for b in range(K)])
            self.exact = [np.array([1 if (b in a1 or b in a2) else 0 for b in range(K)])
                          for a1 in itertools.combinations(tax.CAL_BLOCKS, 3) for a2 in itertools.combinations(tax.TEST_BLOCKS, 3)]
        elif kind == "segment":
            self.cal, self.test = odd_even
            self.assign = np.array([0] * (K // 2) + [1] * (K // 2))
            self.exact = [np.isin(np.arange(K), ones).astype(int) for ones in itertools.combinations(range(K), K // 2)]
        elif kind == "shared":                               # K = 12, odd/even inside every block
            self.cal, self.test = odd_even
            self.assign = np.isin(np.arange(K), rng.choice(K, K // 2, replace=False)).astype(int)
            self.exact = [np.isin(np.arange(K), ones).astype(int) for ones in itertools.combinations(range(K), K // 2)]
        elif kind in ("sep24", "paired24", "shared24", "half24"):
            cb, tb = pair_split(K)
            self.cb, self.tb = cb, tb
            if kind in ("sep24", "paired24"):
                self.cal, self.test = np.where(np.isin(block, cb))[0], np.where(np.isin(block, tb))[0]
            elif kind == "shared24":
                self.cal, self.test = odd_even
            else:                                            # half24: first half of each block calibrates, second half held out
                pos = np.zeros(n, int)
                for b in range(K):
                    idx = np.where(block == b)[0]
                    pos[idx] = (np.arange(len(idx)) >= len(idx) / 2).astype(int)
                self.cal, self.test = np.where(pos == 0)[0], np.where(pos == 1)[0]
            self.assign = self._draw()
            self.exact = None
        else:
            raise ValueError(kind)
        if kind != "iid":
            self.labels = self.assign[block].astype(int)

    def _draw(self):
        K, rng = self.K, self.rng
        a = np.zeros(K, int)
        if self.kind == "sep24":
            a[rng.choice(self.cb, len(self.cb) // 2, replace=False)] = 1
            a[rng.choice(self.tb, len(self.tb) // 2, replace=False)] = 1
        elif self.kind == "paired24":                        # held-out block inherits the label of the calibration block two before it
            a[rng.choice(self.cb, len(self.cb) // 2, replace=False)] = 1
            a[self.tb] = a[self.tb - 2]
        else:
            a[rng.choice(K, K // 2, replace=False)] = 1
        return a

    def block_null(self, n_mc):
        """List of label vectors and whether the list is the exact enumeration."""
        if self.exact is not None:
            return [a[self.block].astype(int) for a in self.exact], True
        return [self._draw()[self.block].astype(int) for _ in range(n_mc)], False


def circ_shifts(n, block):
    m = int(np.bincount(block).max())
    lo, hi = m, n - m
    return np.unique(np.linspace(lo, hi, N_CIRC).round().astype(int)) if hi > lo else np.array([], int)


# ================================================================ one scheme
def run_scheme(counts, block, kind, rng, rnd_order, rnd_sign, readouts=CHEAP + LOGISTIC, circ=False, spec=False,
               lr_tests=True):
    n = counts.shape[1]
    S = Scheme(kind, block, rng, n)
    labels, cal, test = S.labels, S.cal, S.test
    R = Readouts(counts, cal, test, rnd_order, rnd_sign)
    out = {"n_cal": int(len(cal)), "n_test": int(len(test)), "const": tax.majority(labels, test)}
    fits = {name: R.fit(name, labels) for name in readouts}
    for name, (sc, pred) in fits.items():
        out[name] = {"acc": sc, "binom": binom_p(pred, labels, test)}
    if spec:                                                 # Track A order: spec orders before trial permutations
        null = [R.spec_score(labels, rng.permutation(counts.shape[0])) for _ in range(N_SPEC)]
        out["sel"]["spec"], out["sel"]["spec_nan"] = mc_p(null, fits["sel"][0])
    perms = [rng.permutation(labels) for _ in range(N_TRL)]
    blk, is_exact = (S.block_null(N_BLK_MC) if kind != "iid" else ([], True))
    out["n_blk"], out["blk_exact"] = len(blk), is_exact
    for name, (sc, pred) in fits.items():
        o = out[name]
        if name in LOGISTIC and not lr_tests:
            continue
        o["trl_fixed"], _ = mc_p([acc(pred, lp, test) for lp in perms], sc)
        if name != "nosel0":
            o["trl_rerun"], o["trl_rerun_nan"] = mc_p([R.fit(name, lp)[0] for lp in perms], sc)
        if blk:
            pf = exact_p if is_exact else mc_p
            o["blk_fixed"], _ = pf([acc(pred, lb, test) for lb in blk], sc)
            if name != "nosel0":
                if name in LOGISTIC:                         # logistic rerun: first 200 Monte Carlo assignments (or 200 random of the enumeration)
                    idx = np.arange(len(blk)) if len(blk) <= N_BLK_MC_LR else rng.choice(len(blk), N_BLK_MC_LR, replace=False)
                    o["blk_rerun"], o["blk_rerun_nan"] = mc_p([R.fit(name, blk[i])[0] for i in idx], sc)
                    o["blk_rerun_mc"] = True
                else:
                    o["blk_rerun"], o["blk_rerun_nan"] = pf([R.fit(name, lb)[0] for lb in blk], sc)
    if circ:
        shifts = circ_shifts(n, block)
        out["n_circ"] = int(len(shifts))
        if len(shifts):
            out["sel"]["circ_rerun"], _ = mc_p([R.fit("sel", np.roll(labels, s))[0] for s in shifts], fits["sel"][0])
    return out


# ================================================================ positive control
def inject(counts, labels, rng, delta):
    """Add Poisson(delta * mean count) spikes on label-1 trials to 10% of units (at least 2)."""
    n_u = counts.shape[0]
    units = rng.choice(n_u, max(2, int(round(INJ_FRAC * n_u))), replace=False)
    out = counts.copy()
    mu = counts[units].mean(axis=1, keepdims=True)
    one = labels == 1
    out[np.ix_(units, np.where(one)[0])] += rng.poisson(delta * mu, (len(units), int(one.sum())))
    return out


def run_positive(counts, block, kind, base_stream, sid, area, rnd_order, rnd_sign):
    res = {}
    for i, d in enumerate(DELTAS):
        rng = tax.rng_for(sid, area, base_stream + i)
        S = Scheme(kind, block, rng, counts.shape[1])
        c = inject(counts, S.labels, rng, d)
        R = Readouts(c, S.cal, S.test, rnd_order, rnd_sign)
        blk, _ = S.block_null(N_BLK_MC_LR)
        perms = [rng.permutation(S.labels) for _ in range(N_TRL)]
        r = {}
        for name in ("sel", "lr_topk"):
            sc, pred = R.fit(name, S.labels)
            r[name] = {"acc": sc, "binom": binom_p(pred, S.labels, S.test),
                       "blk_fixed": mc_p([acc(pred, lb, S.test) for lb in blk], sc)[0],
                       "blk_rerun": mc_p([R.fit(name, lb)[0] for lb in blk], sc)[0],
                       "trl_rerun": mc_p([R.fit(name, lp)[0] for lp in perms], sc)[0]}
        res[str(d)] = r
    return res


# ================================================================ block-number sweep
def spont_onsets(path, B):
    with h5py.File(path, "r") as f:
        iv = f["intervals"]
        name = next((k for k in iv if k.startswith("spontaneous")), None)
        st, en = np.asarray(iv[name]["start_time"]), np.asarray(iv[name]["stop_time"])
    dur = en - st
    long_idx = sorted([i for i in np.argsort(-dur) if dur[i] >= tax.LONG_EPOCH_S][:tax.N_EPOCHS], key=lambda i: st[i])
    onsets, block = [], []
    for e, i in enumerate(long_idx):
        cuts = np.linspace(st[i] + tax.EPOCH_SKIP_S, en[i], B + 1)
        for k in range(B):
            t = cuts[k]
            while t + tax.PSEUDO_TRIAL_S <= cuts[k + 1]:
                onsets.append(t)
                block.append(e * B + k)
                t += tax.PSEUDO_TRIAL_S
    return np.array(onsets), np.array(block)


def icc_oneway(x, groups):
    gs = [x[groups == g].astype(float) for g in np.unique(groups)]
    gs = [g for g in gs if len(g) > 1]
    k, N = len(gs), sum(len(g) for g in gs)
    if k < 2:
        return np.nan
    grand = np.concatenate(gs).mean()
    msb = sum(len(g) * (g.mean() - grand) ** 2 for g in gs) / (k - 1)
    msw = sum(((g - g.mean()) ** 2).sum() for g in gs) / (N - k)
    m0 = (N - sum(len(g) ** 2 for g in gs) / N) / (k - 1)
    den = msb + (m0 - 1) * msw
    return float((msb - msw) / den) if den > 0 else np.nan


def deff_pred(rho, sizes):
    if rho is None or not np.isfinite(rho):
        return None, None
    mk = float((sizes ** 2).sum() / sizes.sum())                  # Kish
    deff = 1 + (mk - 1) * max(rho, 0.0)
    return deff, float(stats.norm.sf(stats.norm.isf(ALPHA) / math.sqrt(deff)))


def cond_pass(pred, block, test_blocks, test, rng):
    """Exact (or Monte Carlo) probability that the binomial test passes, over the admissible
    held-out labelings (half of the held-out blocks per label), with the predictions fixed."""
    tbl = list(test_blocks)
    h = len(tbl) // 2
    combos = math.comb(len(tbl), h)
    if combos <= N_COND_MC:
        draws = (set(c) for c in itertools.combinations(tbl, h))
    else:
        draws = (set(rng.choice(tbl, h, replace=False).tolist()) for _ in range(N_COND_MC))
    hits = tot = 0
    for ones in draws:
        lab = np.isin(block, list(ones)).astype(int)
        hits += binom_p(pred, lab, test) < ALPHA
        tot += 1
    return hits / tot


def run_sweep(counts_fn, path, sid, area, rnd_seed):
    out = {}
    variants = [(4, None), (8, None), (16, None), (8, 2), (16, 4)]          # (blocks per epoch, keep every k-th block)
    for B, thin in variants:
        on, blk = spont_onsets(path, B)
        if thin:
            keep = (blk % B) % thin == 0
            on, blk = on[keep], blk[keep]
            blk = np.unique(blk, return_inverse=True)[1]
        counts, _ = counts_fn(on)
        if counts.shape[0] < emn.MIN_UNITS_PER_AREA:
            continue
        K = int(blk.max()) + 1
        cb, tb = pair_split(K)
        rng = tax.rng_for(sid, area, 50 + B + (100 if thin else 0))
        a = np.zeros(K, int)
        a[rng.choice(cb, len(cb) // 2, replace=False)] = 1
        a[rng.choice(tb, len(tb) // 2, replace=False)] = 1
        labels = a[blk]
        cal, test = np.where(np.isin(blk, cb))[0], np.where(np.isin(blk, tb))[0]
        ro = tax.rng_for(sid, area, rnd_seed)
        R = Readouts(counts, cal, test, ro.permutation(counts.shape[0]), bool(ro.integers(2)))
        sizes = np.bincount(blk[test], minlength=K)[tb].astype(float)
        res = {"K": K, "block_s": None, "n_test": int(len(test)), "n_test_blocks": int(len(tb)),
               "kish_m": float((sizes ** 2).sum() / sizes.sum()), "const": tax.majority(labels, test)}
        res["block_s"] = float(np.mean(np.bincount(blk)) * tax.PSEUDO_TRIAL_S)
        crng = tax.rng_for(sid, area, 60 + B + (100 if thin else 0))
        for name in ("sel", "nosel0"):
            sc, pred = R.fit(name, labels)
            r = {"acc": sc, "binom": binom_p(pred, labels, test),
                 "cond_pass": cond_pass(pred, blk, tb, test, crng)}
            rho_ho = icc_oneway(pred[test], blk[test])                      # held-out predictions, labels unused
            r["rho_ho"] = rho_ho
            r["deff_ho"], r["pred_ho"] = deff_pred(rho_ho, sizes)
            # cross-fit on calibration: fit on alternate calibration blocks, ICC on the others
            rh = []
            for part in (0, 1):
                fit_b, eval_b = cb[part::2], cb[1 - part::2]
                fc, ec = np.where(np.isin(blk, fit_b))[0], np.where(np.isin(blk, eval_b))[0]
                Rx = Readouts(counts, fc, ec, R.rnd_order, R.rnd_sign)
                _, px = Rx.fit(name, labels)
                rh.append(icc_oneway(px[ec], blk[ec]))
            rho_x = float(np.nanmean(rh)) if np.isfinite(rh).any() else np.nan
            r["rho_xfit"] = rho_x
            r["deff_xfit"], r["pred_xfit"] = deff_pred(rho_x, sizes)
            res[name] = r
        out[f"{B}" + (f"t{thin}" if thin else "")] = res
    return out


# ================================================================ main
STREAMS = {"iid": 11, "segment": 12, "sep": 13, "shared": 21, "sep24": 22, "paired24": 23, "shared24": 24, "half24": 25}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--sessions", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    ap.add_argument("--areas", default="std6", choices=("std6", "allvis"))
    ap.add_argument("--parts", default="spont,pos,sweep,dg")
    args = ap.parse_args()
    parts = set(args.parts.split(","))
    out = Path(args.out)
    done = {(json.loads(l)["session"], json.loads(l)["area"]) for l in out.read_text().splitlines()} if out.exists() else set()
    for si, sid in enumerate(args.sessions.split(",")):
        if si % args.of != args.worker:
            continue
        path = Path(args.dir) / f"session_{sid}.nwb"
        if not path.exists():
            print(f"SESSION {sid}: FILE MISSING", flush=True)
            continue
        t0 = time.time()
        ids, spikes, area, onset, ori = emn.load_session(path)
        good, _ = tax.unit_table(path)
        area = np.where(good, area, "excluded-quality")
        sp, why = tax.spontaneous_blocks(path)
        if sp is None:
            print(f"SESSION {sid}: skipped ({why})", flush=True)
            continue
        sp_on, sp_blk, _ = sp
        on24, blk24 = spont_onsets(path, 8)
        dg_on = np.sort(onset)
        dg_blk = np.concatenate([np.full(len(c), i) for i, c in enumerate(np.array_split(np.arange(len(dg_on)), 24))])
        for a in sorted(set(area)):
            if not a.startswith("VIS") or (args.areas == "std6" and a not in STD6) or (sid, a) in done:
                continue
            ta = time.time()
            sel = np.where(area == a)[0]
            spc, _ = tax.area_counts(spikes, sel, sp_on)
            row = {"session": sid, "area": a, "n_units": int(spc.shape[0])}
            if spc.shape[0] >= emn.MIN_UNITS_PER_AREA:
                ro = tax.rng_for(sid, a, 31)
                rnd_order, rnd_sign = ro.permutation(spc.shape[0]), bool(ro.integers(2))
                if "spont" in parts:
                    for k in ("iid", "sep", "segment", "shared"):
                        row[k] = run_scheme(spc, sp_blk, k, tax.rng_for(sid, a, STREAMS[k]), rnd_order, rnd_sign,
                                            circ=k in ("iid", "segment", "shared"), spec=k != "shared",
                                            lr_tests=k != "sep")
                c24, _ = tax.area_counts(spikes, sel, on24)
                if c24.shape[0] >= emn.MIN_UNITS_PER_AREA:
                    ro24 = tax.rng_for(sid, a, 33)
                    o24, s24 = ro24.permutation(c24.shape[0]), bool(ro24.integers(2))
                    if "spont" in parts:
                        for k in ("sep24", "paired24", "shared24", "half24"):
                            row[k] = run_scheme(c24, blk24, k, tax.rng_for(sid, a, STREAMS[k]), o24, s24,
                                                circ=k == "shared24")
                    if "pos" in parts:
                        row["pos_sep24"] = run_positive(c24, blk24, "sep24", 70, sid, a, o24, s24)
                        row["pos_shared24"] = run_positive(c24, blk24, "shared24", 80, sid, a, o24, s24)
                if "sweep" in parts:
                    row["sweep"] = run_sweep(lambda on: tax.area_counts(spikes, sel, on), path, sid, a, 34)
            if "dg" in parts:
                dgc, _ = tax.area_counts(spikes, sel, dg_on)
                row["n_units_dg"] = int(dgc.shape[0])
                if dgc.shape[0] >= emn.MIN_UNITS_PER_AREA:
                    rd = tax.rng_for(sid, a, 35)
                    od, sd = rd.permutation(dgc.shape[0]), bool(rd.integers(2))
                    for k in ("iid", "sep24", "shared24"):
                        row[f"dg_{k}"] = run_scheme(dgc, dg_blk, k, tax.rng_for(sid, a, 90 + STREAMS[k]), od, sd,
                                                    readouts=("sel", "nosel0", "lr_topk"))
            row["seconds"] = round(time.time() - ta, 1)
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            print(f"  {sid} {a}: {row['seconds']} s", flush=True)
        print(f"SESSION {sid}: DONE in {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
