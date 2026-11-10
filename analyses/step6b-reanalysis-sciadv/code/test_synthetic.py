"""Checks of every piece of the reanalysis code on synthetic data with known answers (no real data used).

  python test_synthetic.py [--quick] [--n-jobs 6]  > ../test_synthetic.out

Exit status 1 if any check fails. The calibration part (T9) uses reduced settings for speed (1 bin, 30 cells,
10 folds, R = 1, D = 50 trial-shuffle draws); the reduced settings are printed with the results.
"""
from __future__ import annotations

import argparse
import itertools
import sys
import time
import warnings

import numpy as np
from joblib import Parallel, delayed
from scipy.stats import norm
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.model_selection import KFold, cross_val_score
from sklearn.svm import SVC

import decode as dc
import matlab_port as mp
from blockperm import block_permutation_test_score

FAILS = []


def check(name, ok, detail=""):
    print("%-4s %s%s" % ("ok" if ok else "FAIL", name, ("  [" + detail + "]") if detail else ""))
    if not ok:
        FAILS.append(name)


# ---------------------------------------------------------------- T1-T4: MATLAB port
def t_matlab_conventions():
    check("T1 prctile([1 2 3 4],50) = 2.5 (MATLAB)", mp.matlab_prctile([1, 2, 3, 4], 50) == 2.5)
    check("T1 prctile([1 2 3 4],25) = 1.5 (MATLAB)", mp.matlab_prctile([1, 2, 3, 4], 25) == 1.5)
    check("T1 prctile([1 2 3 4 5],10) = 1 (MATLAB clamps)", mp.matlab_prctile([1, 2, 3, 4, 5], 10) == 1.0)
    check("T1 movmean([1..5],5) = [2 2.5 3 3.5 4]", np.allclose(mp.matlab_movmean([1, 2, 3, 4, 5], 5), [2, 2.5, 3, 3.5, 4]))
    x = np.array([1.0, 2, 3, 4])
    check("T1 zscore uses N-1", np.allclose(mp.matlab_zscore(x), (x - 2.5) / np.std(x, ddof=1)))


def t_df_and_filter():
    Ls = 30 * 300
    F = np.full(Ls, 100.0)
    F[1000:1010] = 150.0                        # +50 % transient
    F[5000:5010] = 150.0
    df, mb = mp.df_anya(F)
    check("T2 dF/F: flat baseline 100 gives 0 outside transients", np.allclose(np.delete(df, np.r_[1000:1010, 5000:5010]), 0))
    check("T2 dF/F: 150 on baseline 100 gives 50 %", np.allclose(df[1000:1010], 50) and mb == 100)
    t = np.arange(1, Ls + 1, dtype=float)
    G = 100 + 100 * (t - 1) / (Ls - 1)          # slow ramp; the deposited code places each window's median at
    dg, _ = mp.df_anya(G)                        # the window start, so the baseline leads the trace by 900 frames
    lead = 100 + 100 * (t + 900 - 1) / (Ls - 1)
    expect = (G - lead) / lead * 100
    check("T2 dF/F: ramp gives the half-window lead of the deposited baseline", np.allclose(dg[:7000], expect[:7000], atol=0.05),
          "max |diff| %.3f; residual of the ramp %.1f %%" % (np.max(np.abs(dg[:7000] - expect[:7000])), np.min(dg)))
    dn, _ = mp.df_anya(np.full(Ls, -5.0))
    check("T2 dF/F: negative baseline gives all NaN", np.all(np.isnan(dn)))
    check("T2 Figure 4 filter keeps two 50 % transients", mp.fig4_keep_cell(df))
    one = df.copy()
    one[5000:5010] = 0
    check("T2 Figure 4 filter drops a cell with one crossing", not mp.fig4_keep_cell(one))
    big = df.copy()
    big[7000:7003] = 600
    check("T2 Figure 4 filter drops a cell with a 600 % event", not mp.fig4_keep_cell(big))
    check("T2 Figure 4 filter drops NaN cells", not mp.fig4_keep_cell(dn))


def t_trials():
    nf = 30 * 400
    cells = np.tile(np.arange(nf, dtype=float) / 1e4, (3, 1))     # value = 0-based frame index / 1e4
    cells[:, 6990:7000] = 50.0                                     # artefact inside the Hit at 7000
    ev_id = np.array(["ITI", "Go", "Hit", "Hit", "ITI", "Hit", "Hit", "Hit"])
    ev_ts = np.array([100, 2000, 2010, 3000, 4000, 6000, 7000, nf - 100])   # last Hit too close to the end
    bt = np.array([2, 2, 2, 2, 1, 1, 1, 1])
    tr = mp.build_trials(cells, ev_id, ev_ts, bt, binned=True)
    check("T3 trials: Hits only, cued first, edge trial excluded", list(tr["ttype"]) == [2, 2, 1, 1])
    # 1-based TS: frames TS-149..TS+150 -> 0-based TS-150..TS+149; bin 1 = mean of 0-based TS-150 and TS-149
    exp_bin1 = ((2010 - 150) + 0.5) / 1e4
    check("T3 trials: window and binning orientation", tr["X"].shape == (4, 3, 150) and np.isclose(tr["X"][0, 0, 0], exp_bin1)
          and np.isclose(tr["X"][0, 0, 149], ((2010 + 148) + 0.5) / 1e4))
    check("T3 trials: block ids from BlockType changes", list(tr["block"]) == [0, 0, 1, 1])
    check("T3 trials: artefact flag (mean over cells > 10) only on the Hit at 7000",
          list(tr["artefact"]) == [False, False, False, True] and np.all(np.isnan(tr["X"][3])))
    check("T4 bin 45 centre is -2.02 s (movement baseline)", abs(mp.bin_centre_s(45) + 2.0167) < 1e-3)
    check("T4 ITI window = MATLAB bins 16-44, -3.95 to -2.08 s",
          dc.WINDOWS["ITI"][0] == 15 and dc.WINDOWS["ITI"][-1] == 43 and
          abs(mp.bin_centre_s(16) + 3.95) < 1e-2 and abs(mp.bin_centre_s(44) + 2.083) < 1e-2)
    check("T4 PERI window = MATLAB bins 73-81, -0.15 to +0.38 s",
          abs(mp.bin_centre_s(73) + 0.15) < 1e-2 and abs(mp.bin_centre_s(81) - 0.383) < 1e-2)


# ---------------------------------------------------------------- T5: decoders
def t_decoders():
    rng = np.random.default_rng(1)
    n, d = 2000, 1.5
    y = np.repeat([1, 2], n // 2)
    x = rng.normal(size=(n, 5))
    x[:, 0] += np.where(y == 2, d, 0)
    bayes = norm.cdf(d / 2)
    folds = list(KFold(10, shuffle=True, random_state=0).split(x))
    acc_svm = dc.cv_accuracy_bins(x[:, :, None], y, [0], folds) / 100
    acc_lda = dc.cv_accuracy_bins(x[:, :, None], y, [0], folds, LinearDiscriminantAnalysis) / 100
    check("T5 SVM accuracy near Bayes %.3f" % bayes, abs(acc_svm - bayes) < 0.03, "%.3f" % acc_svm)
    check("T5 LDA accuracy near Bayes %.3f" % bayes, abs(acc_lda - bayes) < 0.03, "%.3f" % acc_lda)
    x2 = x[np.r_[0:200, 1000:1200]]
    y2 = y[np.r_[0:200, 1000:1200]]
    ref = cross_val_score(SVC(kernel="linear", C=1.0), x2, y2, cv=KFold(10, shuffle=True, random_state=3)).mean()
    ours = dc.cv_accuracy_bins(x2[:, :, None], y2, [0], list(KFold(10, shuffle=True, random_state=3).split(x2))) / 100
    check("T5 cv_accuracy_bins equals sklearn cross_val_score (same folds)", np.isclose(ref, ours), "%.4f vs %.4f" % (ref, ours))
    yy = np.array([1] * 30 + [2] * 50)
    idx = dc.balanced_subsample(yy, np.random.default_rng(0))
    check("T5 balanced subsample keeps all of the smaller class", np.sum(yy[idx] == 1) == 30 and np.sum(yy[idx] == 2) == 30)


# ---------------------------------------------------------------- synthetic recordings
def sim_mouse(rng, block_labels, n_cells=30, per_block=30, n_bins=3, drift_sd=0.25, event=0.0, event_bins=None,
              noise=1.0, unequal=True):
    """Trials in time order; a per-cell random walk across trials (slow drift, shared by all bins of a trial),
    plus independent noise. event: amplitude of a fixed pattern added to cued (label 2) trials in event_bins."""
    sizes = [per_block + (int(rng.integers(-5, 6)) if unequal else 0) for _ in block_labels]
    n = sum(sizes)
    walk = np.cumsum(rng.normal(0, drift_sd, size=(n, n_cells)), axis=0)
    tb = np.repeat(np.arange(len(block_labels)), sizes)
    y = np.asarray(block_labels)[tb]
    X = walk[:, :, None] + rng.normal(0, noise, size=(n, n_cells, n_bins))
    if event:
        pat = rng.normal(size=n_cells)
        pat /= np.linalg.norm(pat)
        for b in (event_bins or range(n_bins)):
            X[y == 2, :, b] += event * pat * np.sqrt(n_cells) / 3
    return X, y, tb


def run_mouse(seed, assignment, drift_sd, event, D, n_folds, R, bins):
    rng = np.random.default_rng(seed)
    if assignment == "random":
        comb = list(itertools.combinations(range(6), 3))[int(rng.integers(20))]
        lab = np.full(6, 1)
        lab[list(comb)] = 2
    else:
        lab = np.array([2, 1, 2, 1, 2, 1])
    X, y, tb = sim_mouse(rng, lab, drift_sd=drift_sd, event=event)
    bt = dc.block_test(X, tb, lab, bins, ("sim", seed), R=R, n_folds=n_folds)
    tt = dc.trial_shuffle_test(X, y, bins, ("simt", seed), D=D, R=R, n_folds=n_folds, observed=bt["observed"])
    return bt, tt


def calibrate(n_groups, assignment, drift_sd, event, D, n_jobs, n_folds=10, R=1, bins=(0,), seed0=0):
    jobs = [(seed0 + 1000 * g + m) for g in range(n_groups) for m in range(6)]
    res = Parallel(n_jobs=n_jobs)(delayed(run_mouse)(s, assignment, drift_sd, event, D, n_folds, R, list(bins)) for s in jobs)
    rej_trial_mouse = np.mean([tt["p"] < 0.05 for _, tt in res])
    rej_block_mouse = np.mean([bt["p"] < 0.05 for bt, _ in res])
    rej_group_block, rej_group_trial, accs = [], [], []
    for g in range(n_groups):
        rr = res[6 * g:6 * g + 6]
        obs = [bt["observed"] for bt, _ in rr]
        accs.append(np.mean(obs))
        rej_group_block.append(dc.group_block_p(obs, [bt["null"] for bt, _ in rr])["p"] < 0.05)
        rej_group_trial.append(dc.group_trial_p(obs, [tt["null"] for _, tt in rr], n_combo=20000, key=("g", g))["p"] < 0.05)
    return dict(trial_mouse=rej_trial_mouse, block_mouse=rej_block_mouse, group_block=np.mean(rej_group_block),
                group_trial=np.mean(rej_group_trial), mean_acc=float(np.mean(accs)), n_groups=n_groups,
                min_block_p=min(bt["p"] for bt, _ in res))


def ci(p, n):
    from scipy.stats import binomtest
    k = int(round(p * n))
    c = binomtest(k, n).proportion_ci(method="exact")
    return "%d/%d = %.1f%% (95%% CI %.1f-%.1f%%)" % (k, n, 100 * p, 100 * c.low, 100 * c.high)


def t_arrangements():
    lab = np.array([2, 1, 2, 1, 2, 1])
    arrs, canon, uniq = dc.canonical_partitions(lab)
    check("T6 20 balanced arrangements of C S C S C S, 10 class-swap pairs", len(arrs) == 20 and len(uniq) == 10)
    rng = np.random.default_rng(5)
    X, y, tb = sim_mouse(rng, lab, n_bins=1)
    # swap invariance computed directly: score an arrangement and its swap with the same seed key
    a = arrs[3]
    sw = np.where(a == 1, 2, 1)
    s1 = dc.window_stat(X, a[tb], [0], ("swap",), R=2)
    s2 = dc.window_stat(X, sw[tb], [0], ("swap",), R=2)
    check("T6 class swap leaves the refit accuracy unchanged", np.isclose(s1, s2), "%.4f vs %.4f" % (s1, s2))
    bt = dc.block_test(X, tb, lab, [0], ("arr",), R=1)
    check("T6 smallest per-mouse block p = 0.1", np.isclose(bt["p_min"], 0.1) and bt["p"] >= 0.1 - 1e-12)


def t_group_exact():
    rng = np.random.default_rng(2)
    nulls = [np.round(rng.uniform(40, 70, 20), 1) for _ in range(3)]
    obs = [nulls[0][0], nulls[1][5], nulls[2][7]]
    T = np.mean(obs)
    brute = np.mean([np.mean(c) >= T - 1e-9 for c in itertools.product(*nulls)])
    ours = dc.group_block_p(obs, nulls)["p"]
    check("T7 exact group null equals brute-force enumeration (3 mice, 8000 combinations)", np.isclose(brute, ours),
          "%.6f vs %.6f" % (brute, ours))
    six = [np.r_[np.full(2, 60.0), np.full(18, 50.0)]] * 6
    check("T7 group p minimum (2/20)^6 = 1e-6", np.isclose(dc.group_block_p([60.0] * 6, six)["p"], 1e-6))
    # review M3: unrounded float nulls with every mouse at the top must give exactly the minimum
    rngf = np.random.default_rng(7)
    fl = []
    for _ in range(6):
        v = rngf.uniform(40, 70, 10)
        fl.append(np.r_[v, v])                      # 10 class-swap pairs
    top = [float(np.max(n)) for n in fl]
    r = dc.group_block_p(top, fl)
    check("T7 unrounded nulls, every mouse at the top: p = (2/20)^6 = 1e-6", np.isclose(r["p"], 1e-6) and np.isclose(r["p_min"], 1e-6),
          "p %.3g, min %.3g" % (r["p"], r["p_min"]))
    from summarize import verdict
    v1 = verdict("ITI", 0.001, 0.3, drift_acc=65.0)
    v2 = verdict("ITI", 0.001, 0.3, drift_acc=55.0)
    v3 = verdict("PERI", 0.001, 0.01)
    check("T13 verdict sentences: drift clause, not-distinguishable clause, exchangeability sentence",
          "uninformative under drift" in v1 and "not distinguishable" in v2 and "above the block-arrangement null" in v3
          and all("exchangeability model" in v for v in (v1, v2, v3)))


def t_v2_fixes():
    """Review v2: S1 (missing drift accuracy), S3 (seed keys), S4 (mean comparison), M1 (Fig. 4D peak range)."""
    from summarize import verdict
    vn, vf = verdict("ITI", 0.001, 0.3, drift_acc=None), verdict("ITI", 0.001, 0.3, drift_acc=float("nan"))
    vp = verdict("PERI", 0.001, 0.3, drift_acc=None)
    check("T16 verdict: None or NaN drift accuracy gives '(drift check not available)' in both windows",
          "(drift check not available)" in vn and "(drift check not available)" in vf and "(drift check not available)" in vp
          and "uninformative" not in vn and "uninformative" not in vf)
    vq = verdict("PERI", 0.001, 0.3, drift_acc=65.0)
    vr = verdict("PERI", 0.001, 0.3, drift_acc=55.0)
    vs = verdict("PERI", 0.001, 0.01, drift_acc=65.0)
    v_iti = verdict("ITI", 0.001, 0.3, drift_acc=65.0)
    check("T21 PERI drift rule (2026-11-08): uninformative at drift >= 60%, not-distinguishable below, rejection unaffected",
          "uninformative under drift" in vq and "(drift accuracy measured in the ITI window)" in vq and "measured in the ITI" not in v_iti and "not distinguishable" in vr and "above the block-arrangement null" in vs)
    _, _, uniq = dc.canonical_partitions(np.array([2, 1, 2, 1, 2, 1]))
    txt = "|".join(map(str, uniq))
    check("T17 partition keys are Python ints (no 'np.int64' in the seed key text)",
          "np.int64" not in txt and all(type(i) is int for u in uniq for i in u), txt[:40])
    from run_reanalysis import means_match, PLOT_LO, PLOT_HI
    check("T18 mean comparison on a rounding boundary: 0.285 vs 0.28 and 0.29 at 2 digits, 0.35 vs 0.3 at 1 digit",
          means_match([0.285, 0.0], [0.28, 0.0], (2, 1)) and means_match([0.285, 0.0], [0.29, 0.0], (2, 1))
          and means_match([0.35, 0.0], [0.3, 0.0], (1, 1)) and means_match([0.35, 0.0], [0.4, 0.0], (1, 1))
          and not means_match([0.2851, 0.0], [0.28, 0.0], (2, 1)) and not means_match([0.30, 0.0], [0.28, 0.0], (2, 1)))
    # M1: peak searched only in MATLAB bins 60-90 (0-based 59..89)
    curve = np.zeros(150)
    curve[72:81] = 1.0                 # in-range peak at MATLAB bins 73-81
    curve[100] = 5.0                   # higher value outside the plotted range
    pk = PLOT_LO + int(np.argmax(curve[PLOT_LO:PLOT_HI]))
    check("T19 Fig. 4D peak search ignores a higher value outside bins 60-90; in-range peak passes 73-81",
          int(np.argmax(curve)) == 100 and 72 <= pk <= 80 and (PLOT_LO, PLOT_HI) == (59, 90), "peak bin %d (MATLAB)" % (pk + 1))


def t_gate_helpers():
    """Behaviour-gate signed rank (review stat M4, domain M3) and the pinned environment (review S8)."""
    from run_reanalysis import signrank_pairs
    up = np.c_[np.arange(1, 7) + 1.0, np.zeros(6)]                      # all six differences positive
    p, n, nz, nt = signrank_pairs(up)
    check("T14 signed rank, n = 6, all differences one sign: two-sided exact p = 2/64 = 1/32",
          np.isclose(p, 1 / 32) and n == 6 and nz == 0 and nt == 0, "p %.5f" % p)
    nan_row = np.vstack([up, [np.nan, 1.0]])
    p2, n2, _, _ = signrank_pairs(nan_row)
    check("T14 signed rank drops a NaN pair, as MATLAB signrank does", np.isclose(p2, p) and n2 == 6)
    tie = np.c_[[1.0, 1.0, 2.0, 3.0, 4.0, 5.5], np.zeros(6)]
    _, _, _, nt2 = signrank_pairs(tie)
    check("T14 tied absolute differences are counted", nt2 == 1, "ties %d" % nt2)
    env = dc.check_environment(strict=True)
    check("T15 pinned blockperm hash and package versions match", env["blockperm_sha256"] == dc.BLOCKPERM_SHA256,
          str(env["versions"]))


def t_blockperm_equivalence():
    rng = np.random.default_rng(4)
    lab = np.array([2, 1, 2, 1, 2, 1])
    X, y, tb = sim_mouse(rng, lab, n_bins=1, unequal=False, drift_sd=0.15)
    folds = list(KFold(5, shuffle=True, random_state=0).split(X))
    ours = dc.block_test(X, tb, lab, [0], ("eq",), R=1, subsample=False, fixed_folds=folds)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        s, null, p = block_permutation_test_score(SVC(kernel="linear", C=1.0), X[:, :, 0], y, blocks=tb, cv=folds,
                                                  exact=True)
    check("T8 block test equals blockperm.block_permutation_test_score (exact, fixed folds, no subsample)",
          np.isclose(ours["p"], p) and np.isclose(ours["observed"], 100 * s) and
          np.allclose(np.sort(ours["null"]), np.sort(100 * null)), "p %.3f vs %.3f" % (ours["p"], p))


def t_movement():
    rng = np.random.default_rng(7)
    n, c = 120, 30
    X = rng.normal(size=(n, c, 150))
    pat = rng.normal(size=c)
    for b in dc.WINDOWS["PERI"]:
        X[:, :, b] += 0.6 * pat
    r = dc.movement_test(X, dc.WINDOWS["PERI"][:3], dc.BASELINE_BIN, ("mv",), D=30, R=1, n_folds=10)
    check("T11 movement decoder (press vs baseline) detects a press-locked pattern", r["p"] <= 1 / 31 + 1e-9 and r["observed"] > 75,
          "acc %.1f, p %.3f" % (r["observed"], r["p"]))
    Xn = rng.normal(size=(n, c, 150))
    r0 = dc.movement_test(Xn, dc.WINDOWS["PERI"][:3], dc.BASELINE_BIN, ("mv0",), D=30, R=1, n_folds=10)
    check("T11 movement decoder near chance without a pattern", 35 < r0["observed"] < 65, "acc %.1f" % r0["observed"])


def t_timing():
    rng = np.random.default_rng(0)
    Xf = rng.normal(size=(171, 210))
    yf = np.repeat([1, 2], [86, 85])
    t0 = time.perf_counter()
    for _ in range(50):
        SVC(kernel="linear", C=1.0).fit(Xf, yf).predict(Xf[:9])
    dt = (time.perf_counter() - t0) / 50
    fits_iti = 29 * 20
    fits_peri = 9 * 20
    per_mouse = (10 * 4 + 1000 * 4) * (fits_iti + fits_peri)
    print("T12 timing: one linear SVM fit (171 trials x 210 cells, noise) = %.1f ms; primary tests per mouse "
          "about %.2g fits, %.1f CPU-hours (both windows, R = 4, D = 1000); 6 mice about %.0f CPU-hours (primary part)"
          % (1000 * dt, per_mouse, per_mouse * dt / 3600, 6 * per_mouse * dt / 3600))
    # per mouse fits: primary 3,070,400; drift 932,640; S2 487,200; movement 36,360; S1 4,560 (review v2, section 3);
    # gate 918,000 fits for six mice
    other = 932640 + 487200 + 36360 + 4560
    gate = 918000
    tot = (6 * (per_mouse + other) + gate) * dt / 3600
    print("T12 total: controls and secondary about %.1f CPU-hours, gate about %.1f CPU-hours, whole design about %.0f "
          "CPU-hours at this fit time" % (6 * other * dt / 3600, gate * dt / 3600, tot))


T10_REFERENCE = {0.05: "20/20 = 100.0% (95% CI 83.2-100.0%)", 0.25: "5/20 = 25.0% (95% CI 8.7-49.1%)"}   # test_synthetic.out, full run of 2026-11-07


def t20_fixed_order_power(Ge, D, n_jobs):
    """T20 (descriptive only; no decision rule, gate or prediction depends on it): T10's event-locked signal with the
    fixed order C S C S C S of the study. Same seeds, amplitude and drift levels as T10."""
    print("T20 event-locked context signal (fixed pattern added to cued trials, amplitude 1.0), fixed order C S C S C S, "
          "%d groups of 6 mice per drift level (T10 numbers, random assignment, same seeds, from test_synthetic.out in brackets)" % Ge)
    for drift, label in ((0.05, "weak drift (sd 0.05)"), (0.25, "strong drift as in T9 (sd 0.25)")):
        r = calibrate(Ge, "fixed", drift, 1.0, D, n_jobs, seed0=777777)
        print("  %s: mean accuracy %.1f%%; group block test rejects %s [T10: %s]; group trial shuffle rejects %s"
              % (label, r["mean_acc"], ci(r["group_block"], Ge), T10_REFERENCE[drift], ci(r["group_trial"], Ge)))
    print("  (descriptive, no pass/fail)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--only-t20", action="store_true", help="run only T20 (fixed-order power), 20 groups per level")
    ap.add_argument("--n-jobs", type=int, default=6)
    a = ap.parse_args()
    t_start = time.time()
    if a.only_t20:
        t20_fixed_order_power(20, 50, a.n_jobs)
        print("total time %.0f s (T20 only)" % (time.time() - t_start))
        return
    t_matlab_conventions()
    t_df_and_filter()
    t_trials()
    t_decoders()
    t_arrangements()
    t_group_exact()
    t_gate_helpers()
    t_v2_fixes()
    t_blockperm_equivalence()
    G = 20 if a.quick else 60
    D = 50
    print("T9 calibration (reduced settings: 1 bin, 30 cells, 6 blocks of 25-35 trials, 10 folds, R = 1, "
          "D = %d trial-shuffle draws, %d groups of 6 mice; labels carry no information; slow drift)" % (D, G))
    for assign in ("random", "fixed CSCSCS"):
        r = calibrate(G, "random" if assign == "random" else "fixed", 0.25, 0.0, D, a.n_jobs)
        print("  %s assignment: mean accuracy %.1f%%" % (assign, r["mean_acc"]))
        print("    per mouse, trial shuffle rejects  %s" % ci(r["trial_mouse"], 6 * G))
        print("    per mouse, block test rejects     %s (smallest attainable p = 0.1)" % ci(r["block_mouse"], 6 * G))
        print("    group, trial shuffle rejects      %s" % ci(r["group_trial"], G))
        print("    group, block test rejects         %s" % ci(r["group_block"], G))
        if assign == "random":
            check("T9 trial shuffle inflated per mouse (> 20%)", r["trial_mouse"] > 0.20)
            check("T9 per-mouse block test never below 0.1", r["min_block_p"] >= 0.1 - 1e-12 and r["block_mouse"] == 0)
            from scipy.stats import binomtest
            k = int(round(r["group_block"] * G))
            check("T9 group block test consistent with 5% under random assignment (exact binomial, two-sided p > 0.01)",
                  binomtest(k, G, 0.05).pvalue > 0.01)
    Ge = 10 if a.quick else 20
    print("T10 event-locked context signal (fixed pattern added to cued trials, amplitude 1.0), random assignment, "
          "%d groups per drift level" % Ge)
    for drift, label in ((0.05, "weak drift (sd 0.05)"), (0.25, "strong drift as in T9 (sd 0.25)")):
        r = calibrate(Ge, "random", drift, 1.0, D, a.n_jobs, seed0=777777)
        print("  %s: mean accuracy %.1f%%; group block test detects %s; group trial shuffle detects %s"
              % (label, r["mean_acc"], ci(r["group_block"], Ge), ci(r["group_trial"], Ge)))
        if drift == 0.05:
            check("T10 group block test detects the event-locked signal with weak drift in >= 90% of groups",
                  r["group_block"] >= 0.9)
        else:
            print("  (descriptive, no pass/fail: with strong block-level drift every arrangement decodes well, so the "
                  "block test has little power for a moderate event-locked signal)")
    t20_fixed_order_power(Ge, D, a.n_jobs)
    t_movement()
    t_timing()
    print("total time %.0f s; failures: %d %s" % (time.time() - t_start, len(FAILS), FAILS))
    sys.exit(1 if FAILS else 0)


if __name__ == "__main__":
    main()
