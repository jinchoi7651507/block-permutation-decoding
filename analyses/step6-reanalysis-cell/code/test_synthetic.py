"""Synthetic checks for the Cell reanalysis port (no real data). Run: python test_synthetic.py [quick]
Output is saved by the caller to test_synthetic.out. Scaled-down sizes (MIN_TRIALS lowered) so the suite runs on a laptop."""
from __future__ import annotations

import sys as _sys
from pathlib import Path as _P
_sys.path.insert(0, str(_P(__file__).resolve().parent))   # also works under python -I
import cell_env  # noqa: F401  (thread variables = 1 before numpy)
import os
os.environ["CELL_MIN_TRIALS"] = "18"      # inherited by worker processes (scaled-down sizes)

import sys
import time

import numpy as np
from scipy.stats import norm

import cellport as cp
import cell_tests as ct
import cell_gate as cg
import cell_select as cs
from synthetic_data import make_sessions

QUICK = len(sys.argv) > 1 and sys.argv[1] == "quick"
cp.MIN_TRIALS = 18
ROIS = ["A", "B", "C"]
RES = []
REAL = ["LIP", "FEF", "LPFC"]


def check(name, ok, detail=""):
    RES.append((name, bool(ok)))
    print("%-4s %s %s" % ("PASS" if ok else "FAIL", name, detail), flush=True)


# ----------------------------------------------------------------------------- unit checks
def unit_checks():
    ang = np.array([0.0, 2 * np.pi / 3 - 1e-9, 2 * np.pi / 3, 4 * np.pi / 3, 2 * np.pi - 1e-9, 2 * np.pi, np.nan, -0.1])
    b = cp.color_bin(ang)
    check("color_bin boundaries (lower inclusive, wrap, NaN=0)", list(b) == [1, 1, 2, 3, 3, 1, 0, 3], str(list(b)))
    pm = cp.progression_membership(np.array([1 / 3, 0.5, 2 / 3, 1.0, np.nan, 0.1]))
    check("progression levels as written (2/3 in levels 2 and 3, NaN none)",
          pm.tolist() == [[1, 0, 0], [0, 1, 0], [0, 1, 1], [0, 0, 1], [0, 0, 0], [1, 0, 0]], str(pm.astype(int).tolist()))
    bel = np.zeros((100, 3)); bel[10, 0] = 1; bel[99, 1] = 2
    pa = cp.peak_belief_angle(bel)
    check("peak belief angle and all-zero NaN", np.isclose(pa[0], 10 * 2 * np.pi / 100) and np.isclose(pa[1], 99 * 2 * np.pi / 100) and np.isnan(pa[2]))
    # column shift and NaN rule
    rng = np.random.default_rng(0)
    n_tr = 6
    wins = [rng.normal(size=(3, n_tr)) for _ in range(27)]
    wins[0][1, 2] = np.nan            # window 1 NaN but others present -> filled with 0, neuron kept
    for w in range(27):
        wins[w][2, 3 if w < 7 else 4] = np.nan   # neuron 2 all-NaN in one column -> window 1 NaN -> dropped
    raw, kept = cp.assemble_columns(wins)
    ok_shift = np.allclose(raw[0, :, 0], wins[0][0, :5]) and np.allclose(raw[0, :, 7], wins[7][0, 1:])
    check("column shift (reward_end trial j, target trial j+1)", ok_shift)
    check("NaN fill and neuron drop rule", list(kept) == [True, True, False] and raw[1, 2, 0] == 0.0, str(list(kept)))
    # linear-kernel KernelScale equivalence
    from sklearn.svm import SVC
    X = rng.normal(size=(60, 8)); y = (X[:, 0] + 0.5 * rng.normal(size=60) > 0).astype(int)
    s, c = 7.0, 0.3
    f1 = SVC(kernel="linear", C=c).fit(X / s, y).decision_function(X / s)
    f2 = SVC(kernel="linear", C=c / s ** 2).fit(X, y).decision_function(X)
    check("KernelScale s equals C/s^2 for the linear kernel", np.allclose(f1, f2, atol=1e-6), "max diff %.2e" % np.abs(f1 - f2).max())
    # Platt
    f = np.concatenate([rng.normal(1.5, 1, 200), rng.normal(-1.5, 1, 200)]); yy = np.r_[np.ones(200), np.zeros(200)].astype(int)
    A, B = cp._platt(f, yy)
    p = 1 / (1 + np.exp(A * f + B))
    check("Platt scaling: monotone in the score, calibrated (mean p near 0.5, A<0)", A < 0 and abs(p.mean() - 0.5) < 0.03, "A=%.2f B=%.2f mean p=%.3f" % (A, B, p.mean()))
    # as-written training set
    Xtt = rng.normal(size=(4, 8, 3, 3)) + 5
    idx = np.array([0, 2, 4, 6])
    Xw, yw = cp._svm_training_set(Xtt, 0, 8, idx, True, [0, 1, 2])
    Xi, yi = cp._svm_training_set(Xtt, 0, 8, idx, False, [0, 1, 2])
    other_w = Xw[len(yw) // 2:]
    first_half = np.concatenate([other_w[g * 8: g * 8 + 4] for g in range(3)])
    check("as-written 'other' block: first half zero except neuron 1; second half equals the second other bin",
          np.all(first_half[:, 1:] == 0) and np.all(first_half[:, 0] != 0) and np.allclose(other_w[4:8], Xtt[:, idx, 0, 2].T)
          and np.all(Xi[len(yi) // 2:][:4] == Xtt[:, idx, 0, 1].T), "")
    check("training set shapes (3 levels x 8 this + 3 x 8 other)", Xw.shape == (48, 4) and yw.sum() == 24)


def block_perm_unit():
    sessions, rs = make_sessions(1, n_sess=2, n_blocks=7)
    rng = np.random.default_rng(3)
    s = sessions[0]
    nb = cp.Session  # noqa
    new = ct.permute_blocks(s, s.true_bin, rng)
    ub, lab = ct.block_labels(s.block, s.true_bin)
    ub2, lab2 = ct.block_labels(s.block, new)
    check("block permutation keeps bin counts per session and constant labels within blocks", sorted(lab) == sorted(lab2))
    tn = ct.permute_trials(s, s.true_bin, rng)
    check("trial permutation keeps trial counts per bin", np.array_equal(np.bincount(s.true_bin), np.bincount(tn)))
    # unlabeled block stays unlabeled
    b0 = s.true_bin.copy(); b0[s.block == 1] = 0
    nb0 = ct.permute_blocks(s, b0, rng)
    check("unlabelled block stays unlabelled", np.all(nb0[s.block == 1] == 0))
    # adjacent-pair matching
    sA, _ = make_sessions(4, n_sess=1, n_blocks=9)
    sA = sA[0]
    manual = np.array([1, 1, 2, 3, 3, 2, 1, 2, 3])
    sA.true_bin = manual[sA.block - 1]
    _, labA = ct.block_labels(sA.block, sA.true_bin)
    adj0 = ct._adjacent_same(labA)
    okadj = True
    for _ in range(30):
        nb_ = ct.permute_blocks(sA, sA.true_bin, rng, match_adjacent=True)
        _, l2 = ct.block_labels(sA.block, nb_)
        okadj &= (ct._adjacent_same(l2) == adj0) and sorted(l2) == sorted(labA)
    check("adjacent-pair matching keeps the number of adjacent same-bin pairs and the counts", okadj, "observed pairs %d" % adj0)
    # block-sequence permutation (estimated template)
    seq = sA.true_bin.copy()
    for b in np.unique(sA.block):
        m = np.where(sA.block == b)[0]
        seq[m[: len(m) // 2]] = (seq[m[0]] % 3) + 1       # label changes halfway through the block
    sq = ct.permute_block_sequences(sA, seq, rng)
    first_ok = all(len(np.unique(sq[sA.block == b])) <= 2 for b in np.unique(sA.block))
    check("block-sequence permutation keeps within-block structure (two labels per block) and every column labelled",
          first_ok and np.all(sq > 0), "")
    # arrangement counts and smallest p
    check("n_arrangements 5 blocks (2,2,1) = 30; 8 blocks (3,3,2) = 560", ct.n_arrangements([2, 2, 1]) == 30 and ct.n_arrangements([3, 3, 2]) == 560)
    pm, n, tw = ct.min_p_session([2, 2, 2])
    check("min p with relabel twins: (2,2,2): 6 twins in 90 arrangements", abs(pm - 6 / 90) < 1e-12 and n == 90 and tw == 6, "%.4f" % pm)
    pm2, n2, tw2 = ct.min_p_session([3, 2, 1])
    check("min p without twins (3,2,1): 1/60", abs(pm2 - 1 / 60) < 1e-12 and tw2 == 1)
    check("joint arrangements log10 for 17 sessions of 8-11 blocks is large", ct.log10_joint_arrangements([[3, 3, 2]] * 8 + [[4, 4, 3]] * 9) > 50,
          "%.1f" % ct.log10_joint_arrangements([[3, 3, 2]] * 8 + [[4, 4, 3]] * 9))
    # exact enumeration with a relabel-invariant statistic reproduces the twin floor
    import itertools
    rngx = np.random.default_rng(5)
    labs = np.array([1, 1, 2, 2, 3, 3])
    means = np.array([0.0, 0.1, 5.0, 5.1, 10.0, 10.1])      # block means perfectly separate the labelled bins
    def stat(l):
        return sum(((means[l == c] - means[l == c].mean()) ** 2).sum() for c in (1, 2, 3)) * -1.0   # within-bin SS, negated
    arr = set(itertools.permutations(labs))
    vals = np.array([stat(np.array(a)) for a in arr])
    obs = stat(labs)
    p_exact = np.mean(vals >= obs - 1e-12)
    check("exact enumeration: p_min equals twins/arrangements (6/90) for a relabel-invariant statistic", abs(p_exact - 6 / 90) < 1e-12 and len(arr) == 90, "p=%.4f" % p_exact)
    # undefined designs count as exceedances
    check("mc_p: undefined null values count as exceedances, undefined observed gives NaN",
          abs(ct.mc_p(0.5, [0.1, np.nan, 0.2, 0.3]) - 2 / 5) < 1e-12 and np.isnan(ct.mc_p(np.nan, [0.1])))
    check("Holm", np.allclose(ct.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06]))
    # design with unqualified permutation
    sess2, rs2 = make_sessions(2, n_sess=2, n_blocks=3, block_len=(25, 30))
    des = cp.build_design(sess2, [s.true_bin for s in sess2], ROIS, rs2)
    check("design returns None n_prog when no session qualifies", des["n_prog"] is None and des["n_neurons"] == 0)


def qual_design():
    sessions, rs = make_sessions(11, n_sess=5, n_blocks=9)
    des = cp.build_design(sessions, [s.true_bin for s in sessions], ROIS, rs)
    cnt = [min(len(v) for v in c.values()) for c in des["cells"]]
    check("design counts: N_progression is the minimum cell count over qualifying sessions; N_neurons the smallest ROI count",
          des["n_prog"] == min(c for c in cnt if c >= cp.MIN_TRIALS) and des["n_neurons"] == min(des["n_qual"].values()),
          "n_prog=%s n_neurons=%s" % (des["n_prog"], des["n_neurons"]))
    rng = np.random.default_rng(0)
    Xtt, Xva = cp.draw_pseudopop(rng, sessions, des, "A")
    npg = des["n_prog"]
    check("pseudo-population shapes and 80/20 split", Xtt.shape == (des["n_neurons"], npg - int(round(0.2 * npg)), 3, 3) and Xva.shape[1] == int(round(0.2 * npg)), str(Xtt.shape))


# ----------------------------------------------------------------------------- decoder
def decoder_checks():
    t0 = time.time()
    rng = np.random.default_rng(0)
    S1, rs = make_sessions(21, n_sess=5, n_blocks=9, signal=0.0, block_sd=0.0, drift=0.0, walk=0.0, n_neur=6)
    r0 = cp.run_decoder(S1, [s.true_bin for s in S1], ["A"], rs, 4, rng)
    a0 = r0["acc"]["A"].mean()
    S2, rs = make_sessions(22, n_sess=5, n_blocks=9, signal=1.0, block_sd=0.0, drift=0.0, walk=0.0, n_neur=6)
    r1 = cp.run_decoder(S2, [s.true_bin for s in S2], ["A"], rs, 4, rng)
    a1 = r1["acc"]["A"].mean()
    print("     full decoder (SVM grid + Platt + MLP): no information %.3f, positive control %.3f, %.0f s for 8 draws" % (a0, a1, time.time() - t0))
    check("full decoder: no information gives accuracy near 1/3 (0.25-0.42)", 0.25 <= a0 <= 0.42, "%.3f" % a0)
    check("full decoder: positive control well above chance (> 0.55)", a1 > 0.55, "%.3f" % a1)
    rw = cp.run_decoder(S2, [s.true_bin for s in S2], ["A"], rs, 2, rng, variant="within")
    check("within-level variant runs and detects the positive control (> 0.5)", rw["acc"]["A"].mean() > 0.5, "%.3f" % rw["acc"]["A"].mean())
    ri = cp.run_decoder(S2, [s.true_bin for s in S2], ["A"], rs, 2, rng, as_written=False)
    check("'intended' other-class placement variant runs and detects the positive control (> 0.55)", ri["acc"]["A"].mean() > 0.55, "%.3f" % ri["acc"]["A"].mean())
    # z-test
    d = np.random.default_rng(1).normal(0.40, 0.03, 100)
    p = cp.z_test(d)
    check("z-test equals 1 - normcdf((mean-1/3)/std) with ddof=1", abs(p - (1 - norm.cdf((d.mean() - 1 / 3) / d.std(ddof=1)))) < 1e-12, "p=%.2e" % p)


# ----------------------------------------------------------------------------- size and power with the cheap decoder
def size_study(n_data, n_perm, drift_kwargs, label, signal=0.0, workers=6):
    """Per dataset: block permutation p and trial-shuffle p (cheap decoder, 1 ROI, 3 draws), the authors' z-test p
    from 30 draws of the observed labelling."""
    from concurrent.futures import ProcessPoolExecutor
    jobs = [(seed, n_perm, drift_kwargs, signal) for seed in range(n_data)]
    with ProcessPoolExecutor(workers) as ex:
        out = list(ex.map(_one_dataset, jobs, chunksize=4))
    pb = np.array([o[0] for o in out]); pt = np.array([o[1] for o in out]); pz = np.array([o[2] for o in out])
    f = lambda p: np.mean(p <= 0.05)
    print("     %-34s block test %.3f | trial shuffle %.3f | authors' z-test %.3f   (n=%d datasets, %d perms)" % (label, f(pb), f(pt), f(pz), n_data, n_perm))
    return f(pb), f(pt), f(pz), pb


def _one_dataset(args):
    seed, n_perm, kw, signal = args
    S, rs = make_sessions(1000 + seed, signal=signal, rois=["A"], **kw)
    bins = [s.true_bin for s in S]
    res_b = ct.permutation_test(S, bins, ["A"], rs, n_perm, 3, kind="block", variant="fast", purpose=10 + seed)
    res_t = ct.permutation_test(S, bins, ["A"], rs, n_perm, 3, kind="trial", variant="fast", purpose=10 + seed)
    rng = np.random.default_rng(seed)
    r = cp.run_decoder(S, bins, ["A"], rs, 30, rng, variant="fast")
    pz = cp.z_test(r["acc"]["A"].mean(1))
    return res_b["A"]["p"], res_t["A"]["p"], pz


def _one_full(args):
    seed, P = args
    S, rs = make_sessions(5000 + seed, n_sess=5, n_blocks=9, signal=0.0, block_sd=0.4, drift=0.02, walk=0.02, n_neur=5, rois=["A"])
    r = ct.permutation_test(S, [s.true_bin for s in S], ["A"], rs, P, 2, kind="block", variant="across", purpose=100 + seed, workers=1)
    return r["A"]["p"]


def full_null_study(n):
    """Full pipeline (grid SVM, Platt, MLP), P = 19 permutations, D = 2 draws, datasets in parallel."""
    from concurrent.futures import ProcessPoolExecutor
    t0 = time.time()
    with ProcessPoolExecutor(6) as ex:
        ps = np.array(list(ex.map(_one_full, [(i, 19) for i in range(n)], chunksize=1)))
    rate = float(np.mean(ps <= 0.05 + 1e-12))
    print("     full pipeline, no information, block offsets + drift: rejection at 0.05 = %.3f in %d datasets (P=19, floor 0.05), %.0f s" % (rate, n, time.time() - t0))
    return rate


# ----------------------------------------------------------------------------- v2 additions (review-v1 MUSTs 1, 3, 6, 7, 8)
def _refused(fn, text):
    try:
        fn()
    except SystemExit as e:
        if text not in str(e):
            print("   (refused with another message: %s)" % str(e)[:150])
        return text in str(e)
    return False


def _raises(fn):
    try:
        fn()
    except ValueError:
        return True
    return False


def new_checks():
    import json
    import os
    import subprocess
    import tempfile
    from pathlib import Path
    import run_cell as rc
    import summarize_cell as sc
    print("--- v2 additions: grid, labels, undefined design, gate, select, loader, environment, determinism, summary")
    # grid (D6)
    check("D6 grid: coarse 7 settings, fine (V2) 22 settings from log10 C -6 to 1, no standardisation grid",
          len(cp.GRIDS["coarse"]) == 7 and len(cp.GRIDS["fine"]) == 22 and cp.GRIDS["fine"][0] == -6.0 and cp.GRIDS["fine"][-1] == 1.0
          and not hasattr(cp, "STANDARDIZE_GRID"), "")
    S, rs = make_sessions(41, n_sess=5, n_blocks=9, n_neur=5, signal=0.0, block_sd=0.0, drift=0.0, walk=0.0)
    r = cp.run_decoder(S, [s.true_bin for s in S], ["A"], rs, 3, np.random.default_rng(1))
    hc = ct.hp_counts(r["hp"])
    check("chosen C recorded for every SVM fit (3 SVMs per draw) and edge count available", hc["A"][0] == 9 and 0 <= hc["A"][1] <= 9, str(hc))
    rf = cp.run_decoder(S, [s.true_bin for s in S], ["A"], rs, 1, np.random.default_rng(1), grid="fine")
    check("fine grid (V2) runs and records chosen C within the grid", all(x in cp.GRIDS["fine"] for x in rf["hp"]["A"]), "")
    # G8 / labels constant within blocks
    ok1, _ = ct.check_true_labels(S, [s.true_bin for s in S])
    bad = [S[0].true_bin.copy()] + [s.true_bin for s in S[1:]]
    bad[0][np.where(S[0].block == 1)[0][0]] = 1 if bad[0][np.where(S[0].block == 1)[0][0]] != 1 else 2
    ok2, msg2 = ct.check_true_labels(S, bad)
    check("G8 label check: constant labels pass, a block with two labels fails", ok1 and not ok2, msg2[:60])
    # undefined observed design: no test, reported as such
    Sx, rsx = make_sessions(42, n_sess=2, n_blocks=3, block_len=(25, 30), rois=["A"])
    rx = ct.permutation_test(Sx, [s.true_bin for s in Sx], ["A"], rsx, 3, 1, kind="block", variant="fast", purpose=3)
    check("undefined observed design gives no test (p NaN, status says so)", np.isnan(rx["A"]["p"]) and rx["A"]["status"] == "no test: observed design undefined", rx["A"]["status"])
    # summary sentence for the undefined case
    check("summary sentence for an undefined design says 'no test'", "no test" in sc.verdict_sentence("LIP", None, "no test: observed design undefined", True))
    # gate items
    rng = np.random.default_rng(0)
    pub_ok = {r: np.round(rng.uniform(0.35, 0.6, (3, 100)) * 36) / 36 for r in cg.ROIS}
    g9 = cg.g9_validation_size(pub_ok)
    pub_bad = {r: np.round(rng.uniform(0.35, 0.6, (3, 100)) * 35) / 35 for r in cg.ROIS}
    g9b = cg.g9_validation_size(pub_bad)
    check("G9 validation size: multiples of 1/36 pass; multiples of 1/35 fail and report the implied n_val", g9["passed"] and not g9b["passed"] and "n_val = 35" in g9b["detail"], g9b["detail"][-40:])
    tmp = Path(tempfile.mkdtemp())
    (tmp / "Data").mkdir()
    (tmp / "Data" / "a.mat").write_bytes(b"abc123")
    import zlib
    good = "%08x" % (zlib.crc32(b"abc123") & 0xFFFFFFFF)
    def tsv(rows):
        p = tmp / "m.tsv"
        p.write_text("zip\tmember\tfile_size\tcompress_size\tcrc32\trole\n" + "".join("Data.zip\t%s\t6\t6\t%s\tminimum\n" % r for r in rows))
        return p
    check("G1: right CRC passes", cg.g1_integrity(tsv([("Data/a.mat", good)]), tmp)["passed"])
    check("G1 negative tests: wrong CRC, missing member and a malformed hash all fail (none skipped)",
          not cg.g1_integrity(tsv([("Data/a.mat", "00000000")]), tmp)["passed"] and not cg.g1_integrity(tsv([("Data/b.mat", good)]), tmp)["passed"]
          and not cg.g1_integrity(tsv([("Data/a.mat", "xyz")]), tmp)["passed"])
    # accuracy items
    port_ok = {r: np.clip(pub_ok[r].T[:100] + rng.normal(0, 0.02, (100, 3)), 0, 1) for r in cg.ROIS}
    its = cg.accuracy_items(port_ok, {r: np.clip(pub_ok[r] + 0.3, 0, 1) for r in cg.ROIS})
    port_far = {r: np.full((100, 3), 0.34) + rng.normal(0, 0.01, (100, 3)) for r in cg.ROIS}
    pub_hi = {r: np.full((3, 100), 0.6) + rng.normal(0, 0.01, (3, 100)) for r in cg.ROIS}
    its_far = cg.accuracy_items(port_far, pub_hi)
    pub_hi2 = {r: np.full((3, 100), 0.5) + rng.normal(0, 0.03, (3, 100)) for r in cg.ROIS}
    port_hi = {r: np.full((100, 3), 0.5) + rng.normal(0, 0.03, (100, 3)) for r in cg.ROIS}
    its_hi = cg.accuracy_items(port_hi, pub_hi2)
    check("G4/G5: matching accuracies pass; a port at chance against a published 0.6 fails both", its_hi[0]["passed"] and its_hi[1]["passed"] and not its_far[0]["passed"] and not its_far[1]["passed"],
          its_far[0]["detail"][:60])
    # design-count gates on synthetic sessions (compare to the PUB numbers, patched to the observed to see the pass path)
    Sg, rsg = make_sessions(43, n_sess=5, n_blocks=9, rois=REAL)
    dg = cg.design_counts(Sg, rsg, "true")
    saved = dict(cg.PUB)
    g3f, g7f, g2f = cg.g3_estimated_counts(Sg, rsg), cg.g7_s3g_counts(Sg, rsg), cg.g2_sessions(Sg)
    cg.PUB.update(est_neurons=dg["n_neurons"], est_prog=cg.design_counts(Sg, rsg, "estimated")["n_prog"], s3g_neurons=dg["n_neurons"],
                  s3g_prog=dg["n_prog"], sessions=5, blocks=45, templates_per_session=(9, 9))
    # n_val must be 15 for G7; synthetic n_prog is not 76, so G7 is checked on its two parts separately
    g3p, g2p = cg.g3_estimated_counts(Sg, rsg), cg.g2_sessions(Sg)
    g7p = cg.g7_s3g_counts(Sg, rsg)
    cg.PUB.clear(); cg.PUB.update(saved)
    check("G2/G3/G7 fail on counts that differ from the published ones and G2/G3 pass when they match",
          not g3f["passed"] and not g7f["passed"] and not g2f["passed"] and g3p["passed"] and g2p["passed"], "G7 needs 76 and 15: %s" % g7p["passed"])
    g8 = cg.g8_true_labels(Sg, rsg)
    check("G8 passes on constant labels with a defined design", g8["passed"], g8["detail"][:70])
    # gate draws independent of the number of workers
    a1, h1, d1 = cg.gate_draws(Sg, rsg, [s.true_bin for s in Sg], 4, 9, {"as_written": True, "grid": "coarse"}, workers=1, chunk=2, variant="fast")
    a2, h2, d2 = cg.gate_draws(Sg, rsg, [s.true_bin for s in Sg], 4, 9, {"as_written": True, "grid": "coarse"}, workers=2, chunk=3, variant="fast")
    check("gate draws identical for 1 and 2 workers and any chunk size", all(np.array_equal(a1[r], a2[r]) for r in cg.ROIS), "")
    # select
    def its_(a, b): return [{"name": "G4", "core": True, "stops": False, "passed": a}, {"name": "G5", "core": True, "stops": False, "passed": b}]
    st_ok = [{"name": "G9 x", "core": True, "stops": True, "passed": True, "val_rule": "round"}, {"name": "G1 x", "core": True, "stops": True, "passed": True}, {"name": "G7 x", "core": True, "stops": False, "passed": True}, {"name": "G8 x", "core": True, "stops": False, "passed": True}]
    s1 = cs.decide(st_ok, {"as_written": its_(True, True)})
    s2 = cs.decide(st_ok, {"as_written": its_(True, False), "V1_intended": its_(True, True)})
    s3 = cs.decide(st_ok, {"as_written": its_(False, True), "V1_intended": its_(False, False), "V2_fine_grid": its_(True, True)})
    s4 = cs.decide(st_ok, {"as_written": its_(False, True), "V1_intended": its_(False, False), "V2_fine_grid": its_(False, False)})
    st_stop = [dict(st_ok[0], passed=False)] + st_ok[1:]
    s5 = cs.decide(st_stop, {})
    st_g8 = st_ok[:2] + [dict(st_ok[2], passed=False)]
    s6 = cs.decide(st_g8, {"as_written": its_(True, True)})
    check("select: first passing variant adopted in the order as_written, V1, V2",
          (s1["adopted"], s2["adopted"], s3["adopted"], s4["adopted"]) == ("as_written", "V1_intended", "V2_fine_grid", None), str([s1["adopted"], s2["adopted"], s3["adopted"], s4["adopted"]]))
    check("select: none adopted gives 'not interpretable' with as_written for the tests; a stopping item blocks all tests; G8 blocks only the true-template tests",
          not s4["interpretable"] and s4["variant_for_tests"] == "as_written" and "not interpretable" in s4["label"] and s5["allowed_tests"] == [] and s6["allowed_tests"] == ["estimated"] and s1["allowed_tests"] == list(cs.ALL_TESTS), "")
    selp = tmp / "select.json"
    selp.write_text(json.dumps(s2))
    refused = []
    for name, test in (("as_written", "primary"), ("V2_fine_grid", "primary")):
        try:
            cs.require_variant(selp, name, test)
            refused.append(False)
        except SystemExit:
            refused.append(True)
    selp.write_text(json.dumps(s6))
    try:
        cs.require_variant(selp, "as_written", "primary"); r3 = False
    except SystemExit:
        r3 = True
    bad_sel = dict(s3, tried=[s3["tried"][1], s3["tried"][0]])
    try:
        cs.verify(bad_sel); r4 = False
    except SystemExit:
        r4 = True
    check("select refuses a variant other than the adopted one, a test blocked by the gate, and a tried list out of order", refused == [True, True] and r3 and r4,
          "refused %s %s %s" % (refused, r3, r4))
    # loader: v5 and v7.3 on the same synthetic session
    from scipy.io import savemat
    import h5py
    from cell_loader import load_session, window_dir, read_mat
    rngl = np.random.default_rng(3)
    n_tr, nn = 40, 4
    block_nb = np.repeat(np.arange(1, 5), 10)
    tib = np.tile(np.arange(1, 11), 4)
    rule = np.repeat(rngl.uniform(0, 2 * np.pi, 4), 10)
    belief = np.abs(rngl.normal(size=(100, n_tr)))
    wdata = {w: {v: rngl.normal(5, 1, (nn, n_tr)) for v in ("LIP", "FEF", "PFC")} for w in range(27)}
    r5, r73 = tmp / "v5", tmp / "v73"
    for w in range(27):
        d5, d73 = window_dir(r5, w), window_dir(r73, w)
        d5.mkdir(parents=True); d73.mkdir(parents=True)
        cond = {"block_nb": block_nb.astype(float), "trial_in_block": tib.astype(float), "rule": rule, "belief": belief}
        savemat(str(d5 / "ID_3.mat"), dict(Conditions=cond, **wdata[w]))
        with h5py.File(str(d73 / "ID_3.mat"), "w") as f:
            g = f.create_group("Conditions")
            for k, v in cond.items():
                g.create_dataset(k, data=np.atleast_2d(v).T if v.ndim == 1 else v.T)
            for k, v in wdata[w].items():
                f.create_dataset(k, data=v.T)
    s5_, s73_ = load_session(r5, 3), load_session(r73, 3)
    same = (np.array_equal(s5_.block, s73_.block) and np.array_equal(s5_.true_bin, s73_.true_bin) and np.array_equal(s5_.belief_bin, s73_.belief_bin)
            and all(np.allclose(s5_.feat_by_window[k][r], s73_.feat_by_window[k][r]) for k in ("900", "600") for r in REAL))
    check("loader: a v5 .mat tree and the same data as v7.3 (HDF5) give identical sessions (blocks, bins, 900 and 600 ms features)", same, "")
    check("loader: 600 ms window is the mean of windows 8 and 14, 900 ms of windows 8, 14 and 20 (before the NaN rule changes nothing here)",
          np.allclose(s5_.feat_by_window["600"]["LIP"][:, :5], np.mean([wdata[7]["LIP"][:, 1:6], wdata[13]["LIP"][:, 1:6]], axis=0))
          and np.allclose(s5_.feat_by_window["900"]["LIP"][:, :5], np.mean([wdata[7]["LIP"][:, 1:6], wdata[13]["LIP"][:, 1:6], wdata[19]["LIP"][:, 1:6]], axis=0)), "")
    try:
        with h5py.File(str(tmp / "ref.mat"), "w") as f:
            f.create_dataset("Conditions", data=np.array([f.create_dataset("x", data=1).ref], dtype=h5py.ref_dtype))
        read_mat(tmp / "ref.mat"); ref_ok = False
    except SystemExit:
        ref_ok = True
    check("loader: a v7.3 struct array (object references) stops with a message", ref_ok, "")
    # environment
    p = cell_env.environment_problems()
    check("environment: pinned versions match in this environment", p == [] , str(p))
    fake = dict(cell_env.versions(), numpy="0.0.0")
    check("environment: a differing version is reported", len(cell_env.environment_problems(fake)) == 1)
    env = dict(os.environ, OMP_NUM_THREADS="8", OPENBLAS_NUM_THREADS="8", VECLIB_MAXIMUM_THREADS="8", MKL_NUM_THREADS="8")
    out = subprocess.run([sys.executable, "-c", "import cell_env,os;print([os.environ[v] for v in cell_env.THREAD_VARS])"], env=env, capture_output=True, text=True, cwd=str(Path(__file__).parent)).stdout.strip()
    check("environment: BLAS thread variables are forced to 1 on import, even when set to 8 outside", out == "['1', '1', '1', '1']", out)
    rec = cell_env.platform_record()
    check("platform recorded (name, versions, threads, seed)", rec["platform"] and rec["master_seed"] == 20261107 and rec["threads"]["OMP_NUM_THREADS"] == "1", rec["platform"] + ", default platform: %s" % rec["is_default_platform"])
    # determinism of three labellings
    t0 = time.time()
    check("determinism: three synthetic labellings (observed, block, trial) rerun give identical output, serial and in 2 workers", rc.stage_determinism(None) == 0, "%.0f s" % (time.time() - t0))
    # runner end to end on synthetic sessions (data loader replaced), resume, summary
    Sr, rsr = make_sessions(44, n_sess=5, n_blocks=9, n_neur=5, signal=0.8, rois=REAL)
    o = tmp / "out"; o.mkdir()
    sel = cs.decide(st_ok, {"as_written": its_(True, True)})
    (o / "select.json").write_text(json.dumps(sel))
    rc.load_sessions = lambda a, oo: (Sr, rsr)
    import argparse
    ADD = "2026-11-08-synthetic-test"
    ns = argparse.Namespace(name="primary", perms=3, draws=1, workers=1, variant=None, out=str(o), extract_root="x", cache=False, addendum=ADD)
    # Addendum 1 (2026-11-08): the platform is fixed (N2). Every data stage must refuse another platform without a dated
    # addendum (F1); checked by pointing DEFAULT_PLATFORM at a platform this process is not on, then restoring it
    fixed = cell_env.DEFAULT_PLATFORM
    cell_env.DEFAULT_PLATFORM = "Other-OS other-arch"
    ns_plain = argparse.Namespace(**dict(vars(ns), addendum=None))
    refused_other = all(_refused(lambda f=f: f(ns_plain), "the design fixes") for f in (rc.stage_inspect, rc.stage_gate, rc.stage_select, rc.stage_test))
    cell_env.DEFAULT_PLATFORM = fixed
    check("platform fixed to 'Linux x86_64' in cell_env, and every data stage (inspect, gate, select, test) refuses another platform without a dated addendum",
          fixed == "Linux x86_64" and refused_other)
    cell_env.DEFAULT_PLATFORM = cell_env.platform_record()["platform"]
    try:
        cell_env.check_environment(); lowered_refused = False
    except SystemExit:
        lowered_refused = True
    check("environment: a lowered 60-trial rule (CELL_MIN_TRIALS) is refused by the run-time check", lowered_refused)
    os.environ["CELL_MIN_TRIALS"] = "60"       # the runner's own check must pass; sizes stay scaled down in this process (workers=1)
    # Addendum 1 (2026-11-08): stage_test compares the platform with gate.json (F1); the suite now writes a synthetic gate.json
    (o / "gate.json").write_text(json.dumps({"platform": dict(cell_env.platform_record(), platform="Other-OS other-arch")}))
    ns_f1 = argparse.Namespace(**dict(vars(ns), perms=1000, draws=10, addendum=None))
    check("test stage refused when gate.json records another platform (F1)", _refused(lambda: rc.stage_test(ns_f1), "different platform"))
    (o / "gate.json").write_text(json.dumps({"platform": cell_env.platform_record()}))
    rc.stage_test(ns)
    r1 = (o / "test-primary.json").read_text()
    (o / "test-primary.json").unlink()
    rc.stage_test(ns)           # resumes from the partial file: nothing recomputed, same JSON
    r2 = (o / "test-primary.json").read_text()
    os.environ["CELL_MIN_TRIALS"] = "18"
    check("runner: test stage writes JSON with platform, p, Holm and edge counts, and a rerun resumes to identical output", r1 == r2 and '"p_holm"' in r1 and '"platform"' in r1 and '"chosen_C_at_upper_edge"' in r1, "")
    ns2 = argparse.Namespace(name="primary", perms=3, draws=1, workers=1, variant="V1_intended", out=str(o), extract_root="x", cache=False, addendum=ADD)
    os.environ["CELL_MIN_TRIALS"] = "60"
    try:
        rc.stage_test(ns2); ref2 = False
    except SystemExit as e:
        ref2 = "refused" in str(e)
    os.environ["CELL_MIN_TRIALS"] = "18"
    check("runner refuses a variant other than the adopted one", ref2)
    # N1: header on the resume file; mismatch, wrong P or D, matching resume
    part = o / "primary.partial.jsonl"
    lines = part.read_text().splitlines()
    hdr = json.loads(lines[0])["header"]
    need = {"test", "variant", "grid", "window", "P", "D", "master_seed", "platform", "code_sha256", "addendum", "val_rule"}
    check("resume file starts with a header (test, variant, grid, window, P, D, seed, platform, sha256 of every code file used)",
          need <= set(hdr) and set(hdr["code_sha256"]) == set(rc.CODE_FILES) and all(len(v) == 64 for v in hdr["code_sha256"].values())
          and hdr["P"] == 3 and hdr["D"] == 1 and hdr["addendum"] == ADD and len(lines) == 1 + 4, "%d lines" % len(lines))
    os.environ["CELL_MIN_TRIALS"] = "60"
    saved_part = part.read_text()
    # matching header resumes (done above: r1 == r2). Mismatching header: change one field at a time
    for key, val in (("D", 2), ("master_seed", 1), ("variant", "V1_intended"), ("window", "600"), ("grid", "fine"),
                     ("platform", dict(hdr["platform"], platform="other")), ("code_sha256", dict(hdr["code_sha256"], **{"cellport.py": "0" * 64}))):
        bad = dict(hdr); bad[key] = val
        part.write_text(json.dumps({"header": bad}) + "\n" + "\n".join(lines[1:]) + "\n")
        okk = _refused(lambda: rc.stage_test(ns), "header of primary.partial.jsonl differs")
        if not okk:
            check("resume refused when header field %s differs" % key, False)
            break
    else:
        check("resume refused when the header differs in D, seed, variant, window, grid, platform or a code hash (one at a time)", True)
    part.write_text("\n".join(lines[1:]) + "\n")
    check("resume refused when the file has no header line", _refused(lambda: rc.stage_test(ns), "no header"))
    part.write_text(saved_part)
    ns3 = argparse.Namespace(**dict(vars(ns), perms=999))
    ns4 = argparse.Namespace(**dict(vars(ns), draws=9))
    ns5 = argparse.Namespace(**dict(vars(ns), addendum="no date here"))
    ns6 = argparse.Namespace(**dict(vars(ns), perms=1000, draws=10, addendum=None))
    ns7 = argparse.Namespace(**dict(vars(ns), perms=999, addendum=None))
    check("wrong P or D refused without an addendum; accepted P = 1,000 and D = 10 pass the check; an undated addendum is refused",
          _refused(lambda: rc.stage_test(ns7), "differ from the design") and _refused(lambda: rc.check_pd(1000, 9, None), "differ from the design")
          and _refused(lambda: rc.check_pd(500, 10, None), "differ from the design") and _refused(lambda: rc.stage_test(ns5), "dated name")
          and rc.check_pd(1000, 10, None) is None and rc.check_pd(500, 5, ADD) is None, "")
    check("a header with another P in the file is refused even with an addendum (P 3 in file, 4 asked)",
          _refused(lambda: rc.stage_test(argparse.Namespace(**dict(vars(ns), perms=4))), "header of primary.partial.jsonl differs"))
    os.environ["CELL_MIN_TRIALS"] = "18"
    check("addendum recorded in the output", json.loads((o / "test-primary.json").read_text())["addendum"] == ADD)
    # N3: validation size rule from the gate values
    pub36 = {r: np.round(rng.uniform(0.35, 0.6, (3, 100)) * 36) / 36 for r in cg.ROIS}
    pub39 = {r: np.round(rng.uniform(0.35, 0.6, (3, 100)) * 39) / 39 for r in cg.ROIS}
    pub35 = {r: np.round(rng.uniform(0.35, 0.6, (3, 100)) * 35) / 35 for r in cg.ROIS}
    pub3 = {r: np.round(rng.uniform(0, 1, (3, 100)) * 3) / 3 for r in cg.ROIS}
    a36, a39, a35, a3 = (cg.g9_validation_size(x) for x in (pub36, pub39, pub35, pub3))
    check("G9 rule: multiples of 1/36 give round, of 1/39 give ceil, neither grid stops, values fitting both take round",
          (a36["passed"], a36["val_rule"], a39["passed"], a39["val_rule"], a35["passed"], a35["val_rule"], a3["val_rule"]) == (True, "round", True, "ceil", False, None, "round"),
          "%s / %s / %s" % (a36["val_rule"], a39["val_rule"], a35["val_rule"]))
    check("validation size: round(0.2 x 61) = 12, ceil = 13; round(0.2 x 76) = 15, ceil = 16; unknown rule refused",
          (cp.n_val(61, "round"), cp.n_val(61, "ceil"), cp.n_val(76, "round"), cp.n_val(76, "ceil")) == (12, 13, 15, 16) and _raises(lambda: cp.n_val(61, "floor")))
    Sv, rsv = make_sessions(45, n_sess=5, n_blocks=9, n_neur=5, rois=REAL)
    dv = cg.design_counts(Sv, rsv, "true")
    saved = dict(cg.PUB)
    results = {}
    for rule in ("round", "ceil"):
        cg.PUB.update(s3g_neurons=dv["n_neurons"], s3g_prog=dv["n_prog"])
        cg.PUB["n_val_s3g"] = {"round": cp.n_val(dv["n_prog"], "round"), "ceil": cp.n_val(dv["n_prog"], "ceil")}
        results[rule] = cg.g7_s3g_counts(Sv, rsv, rule)
    cg.PUB.clear(); cg.PUB.update(saved)
    g7r = cg.g7_s3g_counts(Sv, rsv, "ceil")
    check("G7 uses the rule: with synthetic counts patched in, expected validation size follows round and ceil; a failure quotes the S3G legend wording",
          results["round"]["passed"] and results["ceil"]["passed"] and not g7r["passed"] and '"estimated template color bin"' in g7r["detail"]
          and '"estimated template color bin"' not in results["round"]["detail"], g7r["detail"][-50:])
    os.environ["CELL_VAL_RULE"] = "round"
    d_r = cp.draw_pseudopop(np.random.default_rng(3), Sv, cg.cp.build_design(Sv, [s.true_bin for s in Sv], REAL, rsv), REAL[0])
    os.environ["CELL_VAL_RULE"] = "ceil"
    d_c = cp.draw_pseudopop(np.random.default_rng(3), Sv, cg.cp.build_design(Sv, [s.true_bin for s in Sv], REAL, rsv), REAL[0])
    os.environ.pop("CELL_VAL_RULE")
    check("the port draws the validation size by the rule (ceil gives one more validation trial when 0.2 N is not an integer)",
          d_r[1].shape[1] == cp.n_val(dv["n_prog"], "round") and d_c[1].shape[1] == cp.n_val(dv["n_prog"], "ceil"), "%d and %d" % (d_r[1].shape[1], d_c[1].shape[1]))
    nsx = argparse.Namespace(**dict(vars(ns)))
    (o / "select.json").write_text(json.dumps(dict(sel, val_rule=None)))
    os.environ["CELL_MIN_TRIALS"] = "60"
    check("test stage refused when select.json carries no validation size rule", _refused(lambda: rc.stage_test(nsx), "no validation size rule"))
    os.environ["CELL_MIN_TRIALS"] = "18"
    (o / "select.json").write_text(json.dumps(sel))
    # summary: marks
    mk = lambda ps, kind: {"test": kind, "P": 1000, "regions": {r: {"p": p, "p_holm": min(1, 3 * p), "status": "tested"} for r, p in zip(sc.ROIS, ps)},
                           "design_obs": {"n_prog": 76, "n_neurons": 113}, "design_null": [[76, 113]] * 5 + [[70, 113]],
                           "chosen_C_at_upper_edge": {r: [10, 2] for r in sc.ROIS}}
    gate_ = {"variant_items": {"as_written": [{"name": "G5 verdict", "passed": True}]}}
    sel_ = {"tried": [{"variant": "as_written"}], "adopted": "as_written", "interpretable": True}
    tests_ = {"primary": mk([0.005, 0.2, 0.5], "primary"), "trial": mk([1 / 1001] * 3, "trial"), "estimated": mk([0.3, 0.4, 0.5], "estimated"),
              "adjacent": mk([0.004, 0.1, 0.6], "adjacent")}
    pm = sc.mark_predictions(sel_, gate_, tests_)
    exp = {"P1": "held", "P2": "held", "P3": "held", "P4": "held", "P5": "held", "P6": "held", "P7": "held"}
    check("predictions P1 to P7 marked held on a crafted case", {k: v[0] for k, v in pm.items()} == exp, str({k: v[0] for k, v in pm.items()}))
    tests2 = dict(tests_, primary=mk([0.5, 0.2, 0.9], "primary"), trial=mk([0.02, 0.5, 1 / 1001], "trial"))
    tests2["primary"]["design_null"] = [[76, 113]] * 6
    pm2 = sc.mark_predictions(dict(sel_, adopted="V1_intended"), gate_, tests2)
    nt = sc.mark_predictions({"tried": [], "adopted": None, "interpretable": False}, gate_, {})
    check("predictions: not held cases and not tested cases", [pm2[k][0] for k in ("P1", "P3", "P4", "P6")] == ["not held"] * 4 and all(v[0] == "not tested" for v in nt.values()), str({k: v[0] for k, v in pm2.items()}))
    (o / "gate.json").write_text(json.dumps({"static_items": st_ok, "variant_items": {"as_written": [dict(i, detail="") for i in its_(True, True)]}}))
    sc.main(["--out", str(o)])
    txt = (o / "summary.md").read_text()
    check("summary writes tables and sentences; no em dash in generated text", "Primary" in txt and "—" not in txt, "")


def main():
    t0 = time.time()
    print("Synthetic checks, cellport / cell_tests (scaled down: MIN_TRIALS=%d)" % cp.MIN_TRIALS)
    unit_checks(); block_perm_unit(); qual_design(); decoder_checks(); new_checks()
    nd, npm = (40, 49) if QUICK else (240, 99)
    print("--- size under no information (rejection rate at 0.05; expected about 0.05 for a valid test)")
    sb0 = size_study(nd, npm, dict(block_sd=0.0, drift=0.0, walk=0.0), "no drift, no block offsets")
    sb1 = size_study(nd, npm, dict(block_sd=0.6, drift=0.05, walk=0.03), "block offsets + drift + random walk")
    check("block test size near 0.05 without drift (0.01-0.11)", 0.01 <= sb0[0] <= 0.11, "%.3f" % sb0[0])
    check("block test size near or below 0.05 with block offsets and drift (<= 0.11)", sb1[0] <= 0.11, "%.3f" % sb1[0])
    check("authors' z-test inflated under block offsets and drift (> 0.5)", sb1[2] > 0.5, "%.3f" % sb1[2])
    check("trial-level shuffle inflated under block offsets and drift (> 0.3)", sb1[1] > 0.3, "%.3f" % sb1[1])
    print("--- power with a template signal (cheap decoder)")
    sp = size_study(nd // 2, npm, dict(block_sd=0.6, drift=0.05, walk=0.03), "signal 0.8 + block offsets + drift", signal=0.8)
    check("positive control detected by the block test (rejection >= 0.6)", sp[0] >= 0.6, "%.3f" % sp[0])
    print("--- full pipeline, small permutation test (one dataset each; p floor 1/(P+1))")
    P = 9 if QUICK else 19
    S, rs = make_sessions(77, n_sess=5, n_blocks=9, signal=1.0, block_sd=0.4, drift=0.02, walk=0.02, n_neur=5, rois=["A"])
    t1 = time.time()
    r = ct.permutation_test(S, [s.true_bin for s in S], ["A"], rs, P, 2, kind="block", variant="across", purpose=5, workers=6)
    print("     positive control, full pipeline: observed %.3f, null mean %.3f, p %.3f (floor %.3f), %.0f s" % (r["A"]["observed"], np.nanmean(r["A"]["null"]), r["A"]["p"], 1 / (P + 1), time.time() - t1))
    check("full pipeline block test: positive control reaches the p floor", r["A"]["p"] <= 2 / (P + 1) + 1e-12)
    nfull = 12 if QUICK else 60
    pf = full_null_study(nfull)
    check("full pipeline block test: rejection rate under no information with block offsets and drift (<= 0.15)", pf <= 0.15, "%.3f" % pf)
    fails = [n for n, ok in RES if not ok]
    print("\n%d checks, %d failed%s; total %.0f s" % (len(RES), len(fails), (": " + "; ".join(fails)) if fails else "", time.time() - t0))


if __name__ == "__main__":
    main()
