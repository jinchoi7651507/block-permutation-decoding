#!/usr/bin/env python3
"""Extended Data figures from the summary outputs only (no row file is read). Prints every plotted value with its
source. Same style and colours as make_bc_figures.py (validated categorical slots; marker shape and legend carry
identity). Run: python3 make_ed_figures.py [ED numbers]   (default: all that are implemented)
"""
import json
import sys
import tarfile
from pathlib import Path

import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

R = Path(__file__).resolve().parents[1] / "analyses"   # public layout: the analyses/ folder of this repository
OUT = Path(__file__).resolve().parent
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#d9d8d2"
SIM, MOUSE, EEG = "#2a78d6", "#eb6834", "#1baf7a"
plt.rcParams.update({"font.family": "sans-serif", "font.size": 7, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": INK, "pdf.fonttype": 42})
META = {"Creator": None, "Producer": None, "CreationDate": None}


def style(ax, xlabel, xmax=102):
    ax.axvline(5, color=MUTED, lw=0.8, ls=(0, (3, 2)), zorder=1)
    ax.set_xlim(0, xmax)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)


def dot(ax, y, m, ci, color, marker, filled=True, label=None):
    ax.plot([100 * ci[0], 100 * ci[1]], [y, y], color=color, lw=1.2, solid_capstyle="round", zorder=2)
    ax.plot(100 * m, y, marker, ms=4.5, color=color, mfc=color if filled else "white", mec=color if not filled else "white",
            mew=0.9, zorder=3, label=label)


def ed1():
    """Real drifting-grating trials against spontaneous activity, mouse, shared blocks, the four tests of Fig. 1."""
    s1 = json.load(open(R / "step1-decomposition/results/results.json"))["new/std6"]
    al = json.load(open(R / "step2-comparison/results/allen_summary.json"))["new"]
    rows = [("Trial-level permutation\n(scikit-learn rule)", "P2"), ("Block permutation,\ndecoder held fixed", None),
            ("Training-label permutation\n(PyMVPA)", "P4"), ("Block permutation test", "P5")]
    conds = [("Spontaneous activity", "shared24", True, -0.13), ("Drifting-grating trials", "dg_shared24", False, 0.13)]
    fig, ax = plt.subplots(figsize=(3.7, 2.4))
    for i, (lab, rule) in enumerate(rows):
        for name, key, filled, off in conds:
            if rule is None:
                d = s1[f"{key}/lr_topk/blk_fixed"]
                m, ci, src = d["mean"], d["ci"], f"step1 results.json new/std6 {key}/lr_topk/blk_fixed"
            else:
                d = al[f"{key}/main"][rule]
                m, ci, src = d["mean"], d["ci95"], f"allen_summary new {key}/main {rule}"
            dot(ax, i + off, m, ci, MOUSE, "o", filled, label=name if i == 0 else None)
            print("ED1 row %d %-24s %.3f [%.3f, %.3f]  %s" % (i, name, m, ci[0], ci[1], src))
    ax.set_yticks(range(4))
    ax.set_yticklabels([r[0] for r in rows])
    ax.invert_yaxis()
    style(ax, "Labels with no information called decodable (%)")
    ax.text(6, -0.45, "5%", color=MUTED, fontsize=6, va="center")
    ax.legend(frameon=False, loc="lower right", fontsize=6, handletextpad=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "ed1.pdf", metadata=META)
    fig.savefig(OUT / "ed1.png", dpi=300)


def ed2():
    """Step 1, mouse spontaneous activity: (a) block permutation with the decoder fixed or refit, by readout, shared
    or separate blocks; (b) every test by block scheme, top-20 logistic readout; (c) separate calibration and
    held-out blocks (12 blocks): binomial test by readout, and the circular-shift null by scheme."""
    s1 = json.load(open(R / "step1-decomposition/results/results.json"))["new/std6"]
    wt = json.load(open(R / "step1-decomposition/results/within_train.json"))["new/std6"]

    def get(key):
        src, d = ("within_train.json", wt) if key.split("/")[-1].startswith("trn_") else ("results.json", s1)
        v = d[key]
        return v["mean"], v["ci"], f"step1 {src} new/std6 {key}"

    fig = plt.figure(figsize=(7.2, 5.2))
    gs = fig.add_gridspec(2, 2, left=0.235, right=0.985, top=0.95, bottom=0.08, wspace=1.02, hspace=0.42)
    a, b, c, leg = (fig.add_subplot(gs[i, j]) for i, j in ((0, 0), (0, 1), (1, 0), (1, 1)))
    leg.axis("off")
    readouts = [("nosel0", "Random pools, no label use"), ("nosel", "Random pools, class mapping"), ("rank", "Ranked units, fixed cut"),
                ("sel", "Ranked units, cut chosen"), ("lr_topk", "Top-20 logistic"), ("lr_all", "All units, logistic")]
    for i, (r, _) in enumerate(readouts):
        for key, col, mk, filled, off, name in ((f"shared24/{r}/blk_fixed", MOUSE, "o", True, -0.2, "Decoder fixed, shared blocks"),
                                                (f"sep24/{r}/blk_fixed", MOUSE, "o", False, 0.0, "Decoder fixed, separate blocks"),
                                                (f"shared24/{r}/blk_rerun", INK, "D", False, 0.2, "Decoder refit, shared blocks")):
            if key not in s1:
                print("ED2a %-28s not run (design: no refit null for this readout)" % key)
                continue
            m, ci, src = get(key)
            dot(a, i + off, m, ci, col, mk, filled)
            print("ED2a %-28s %.3f [%.3f, %.3f]  %s" % (key, m, ci[0], ci[1], src))
    a.set_yticks(range(len(readouts))); a.set_yticklabels([r[1] for r in readouts], fontsize=6); a.invert_yaxis()
    style(a, "Labels with no information called decodable (%)")
    a.set_title("a  Block permutation, by decoder", loc="left", fontsize=7)
    ha = [plt.Line2D([], [], ls="", marker="o", color=MOUSE, ms=4, label="Decoder fixed, shared blocks"),
          plt.Line2D([], [], ls="", marker="o", color=MOUSE, mfc="white", ms=4, label="Decoder fixed, separate blocks"),
          plt.Line2D([], [], ls="", marker="D", color=INK, mfc="white", ms=4, label="Decoder refit, shared blocks")]
    l1 = leg.legend(handles=ha, frameon=False, loc="upper left", bbox_to_anchor=(-0.55, 1.0), fontsize=6, handletextpad=0.3,
                    title="Panel a", title_fontsize=6, alignment="left")
    leg.add_artist(l1)

    tests = [("binom", "Binomial test"), ("trl_rerun", "Trial-level permutation, refit"), ("trn_trl", "Training labels only, trial-level"),
             ("trn_blk", "Training labels only, by block"), ("blk_fixed", "Block permutation, decoder fixed"), ("blk_rerun", "Block permutation test")]
    schemes = [("shared24", "Shared blocks", "o", True), ("half24", "Shared, first vs second half", "^", True),
               ("paired24", "Separate blocks, dependent labels", "s", False), ("sep24", "Separate blocks", "o", False)]
    for i, (t, _) in enumerate(tests):
        for j, (sch, name, mk, filled) in enumerate(schemes):
            m, ci, src = get(f"{sch}/lr_topk/{t}")
            dot(b, i - 0.27 + 0.18 * j, m, ci, MOUSE, mk, filled, label=name if i == 0 else None)
            print("ED2b %-30s %.3f [%.3f, %.3f]  %s" % (f"{sch}/lr_topk/{t}", m, ci[0], ci[1], src))
    b.set_yticks(range(len(tests))); b.set_yticklabels([t[1] for t in tests], fontsize=6); b.invert_yaxis()
    style(b, "Labels with no information\ncalled decodable (%)")
    b.set_title("b  Top-20 logistic, by block scheme", loc="left", fontsize=7)
    hb, lb = b.get_legend_handles_labels()
    l2 = leg.legend(hb, lb, frameon=False, loc="upper left", bbox_to_anchor=(-0.55, 0.62), fontsize=6, handletextpad=0.3,
                    title="Panel b", title_fontsize=6, alignment="left")
    leg.add_artist(l2)
    hc = [plt.Line2D([], [], ls="", marker="o", color=MOUSE, ms=4, label="Binomial test"),
          plt.Line2D([], [], ls="", marker="D", color=INK, mfc="white", ms=4, label="Circular-shift null")]
    leg.legend(handles=hc, frameon=False, loc="upper left", bbox_to_anchor=(-0.55, 0.2), fontsize=6, handletextpad=0.3,
               title="Panel c", title_fontsize=6, alignment="left")

    rows = [(f"sep/{r}/binom", lab) for r, lab in readouts[:4]]
    rows += [(f"{s}/sel/circ_rerun", lab) for s, lab in (("iid", "Labels per trial"), ("shared", "Shared blocks (12)"),
                                                          ("shared24", "Shared blocks (24)"), ("segment", "One stretch per label"))]
    ys = [0, 1, 2, 3, 5, 6, 7, 8]
    for y, (key, _) in zip(ys, rows):
        m, ci, src = get(key)
        dot(c, y, m, ci, MOUSE if "binom" in key else INK, "o" if "binom" in key else "D", "binom" in key)
        print("ED2c %-24s %.3f [%.3f, %.3f]  %s" % (key, m, ci[0], ci[1], src))
    c.set_yticks(ys); c.set_yticklabels([r[1] for r in rows], fontsize=6); c.set_ylim(8.6, -1.4)
    import matplotlib.transforms as mt
    tr = mt.blended_transform_factory(c.transAxes, c.transData)
    c.text(-0.04, -0.9, "Binomial, separate blocks", fontsize=6, color=INK, weight="bold", ha="right", transform=tr)
    c.text(-0.04, 4.1, "Circular shift, cut chosen", fontsize=6, color=INK, weight="bold", ha="right", transform=tr)
    style(c, "Labels with no information called decodable (%)")
    c.set_title("c  Other tests", loc="left", fontsize=7)
    fig.savefig(OUT / "ed2.pdf", metadata=META)
    fig.savefig(OUT / "ed2.png", dpi=300)


def _sim():
    return json.load(open(R / "step2-comparison/results/sim_summary.json"))


def ed5():
    """Fixed block orders: simulation (P2, P5 per cell) and EEG (P2, P5 per pattern and split)."""
    import re
    c = _sim()["cells"]
    eeg = json.load(open(R / "step2b-eeg/results/summary_2b.json"))["cells"]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.1, 1]})
    y, labels = 0, []
    for pat in ("ABAB", "ABBA", "AABB"):
        for k in sorted(k for k in c if f"_{pat}_" in k):
            B, tau, tr = re.match(r"c\d+_\w+?_B(\d+)_tau(\d+)_d[\d.]+_t([\d.]+)_main", k).groups()
            for rule, col, mk, off in (("P2", SIM, "s", -0.15), ("P5", INK, "o", 0.15)):
                d = c[k][rule]
                dot(a, y + off, d["rate"], d["wilson95"], col, mk, rule == "P2", label=None)
                print("ED5a %-34s %s %.3f [%.3f, %.3f]  sim_summary %s" % (k, rule, d["rate"], *d["wilson95"], k))
            labels.append(f"{pat}  {B} blocks, \u03c4 {tau}, trend {tr}")
            y += 1
    a.set_yticks(range(y)); a.set_yticklabels(labels, fontsize=5.5); a.invert_yaxis()
    style(a, "Rejection rate (%)")
    a.plot([], [], "s", color=SIM, ms=4, label="Trial-level permutation (simulation)"); a.plot([], [], "o", color=INK, mfc="white", ms=4, label="Block permutation test")
    a.set_title("a  Simulation, fixed orders (500 replicates)", loc="left", fontsize=7)
    y, labels = 0, []
    for pat, name in (("fixed_half", "First vs second half"), ("fixed_aabb", "AABB in runs of four"), ("fixed_abba", "ABBA")):
        for split, sname in (("main", "shuffled 5-fold"), ("tool", "default folds"), ("block", "whole blocks out")):
            cell = eeg[f"{pat}/{split}/main/cleaned_s5"]
            for rule, col, mk, off in (("P2", EEG, "D", -0.15), ("P5", INK, "o", 0.15)):
                d = cell[rule]
                dot(b, y + off, d["rate"], d["wilson95"], col, mk, rule == "P2")
                print("ED5b %-12s %-6s %s %.3f [%.3f, %.3f]  summary_2b %s/%s/main/cleaned_s5" % (pat, split, rule, d["rate"], *d["wilson95"], pat, split))
            labels.append(f"{name}, {sname}")
            y += 1
    b.set_yticks(range(y)); b.set_yticklabels(labels, fontsize=5.5); b.invert_yaxis()
    style(b, "Participants rejecting (%)")
    b.plot([], [], "D", color=EEG, ms=4, label="Trial-level permutation (EEG)")
    b.set_title("b  Human EEG, fixed orders (n = 38)", loc="left", fontsize=7)
    h = a.get_legend_handles_labels()[0] + b.get_legend_handles_labels()[0]
    fig.legend(handles=h, loc="upper center", ncol=3, frameon=False, fontsize=6)
    fig.tight_layout(rect=(0, 0, 1, 0.92)); fig.savefig(OUT / "ed5.pdf", metadata=META); fig.savefig(OUT / "ed5.png", dpi=300)


def ed6():
    """Toolboxes as shipped (CoSMoMVPA, PyMVPA), their block-level option, the ported rules and the block permutation
    test in the four simulated layouts of addendum 3 (500 replicates each; rate over usable replicates, Wilson 95%)."""
    import math
    txt = (R / "step2-comparison/runs_add3/tools/SUMMARY-TOOLS.md").read_text().splitlines()
    tab = {}
    for ln in txt:
        c = [x.strip() for x in ln.strip("|").split("|")]
        if len(c) == 11 and c[0].startswith("L") and c[0][1:].isdigit():
            tab[(c[0], c[1].replace(" **(headline)**", ""))] = (int(c[3]), int(c[4]), float(c[5].rstrip("%")) / 100)

    def wil(p, n, z=1.96):
        d = 1 + z * z / n
        cc = (p + z * z / (2 * n)) / d
        w = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
        return [cc - w, cc + w]

    rows = [("CoSMoMVPA main", "CoSMoMVPA"), ("CoSMoMVPA zscore", "CoSMoMVPA, z-scored per run"), ("PyMVPA main", "PyMVPA"),
            ("PyMVPA zscore", "PyMVPA, z-scored per run"), ("PyMVPA chunks", "PyMVPA, whole blocks permuted"),
            ("P3 port", "Port: within-run permutation"), ("P4 port", "Port: training labels only"), ("P5", "Block permutation test")]
    lays = [("L1", "Random 12-block design, runs of 3 blocks", "^", False), ("L2", "Fixed order AABB", "s", False),
            ("L3", "Labels varying trial by trial, no drift", "o", False), ("L4", "Balanced runs (as in Fig. 2a)", "o", True)]
    fig, ax = plt.subplots(figsize=(5.4, 3.3))
    for i, (key, _) in enumerate(rows):
        for j, (L, name, mk, filled) in enumerate(lays):
            if (L, key) not in tab:
                print("ED6 %-3s %-17s not defined" % (L, key))
                continue
            usable, err, r = tab[(L, key)][0], tab[(L, key)][1], tab[(L, key)][2]
            ci = wil(r, usable)
            dot(ax, i - 0.27 + 0.18 * j, r, ci, INK if key == "P5" else MUTED if key.endswith("port") else SIM, mk, filled,
                label=name if i == 0 else None)
            print("ED6 %-3s %-17s %.3f [%.3f, %.3f] usable %d errors %d  SUMMARY-TOOLS.md %s | %s" % (L, key, r, ci[0], ci[1], usable, err, L, key))
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[1] for r in rows], fontsize=6.5); ax.invert_yaxis()
    style(ax, "Labels with no information called decodable (%)", xmax=80)
    ax.legend(frameon=False, loc="lower right", fontsize=6, handletextpad=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "ed6.pdf", metadata=META)
    fig.savefig(OUT / "ed6.png", dpi=300)


def _ibl():
    import re
    summ = (R / "step3-ibl/runs/SUMMARY.md").read_text()
    q1 = summ.split("## Q1 fake labels")[1].split("## Primary contrasts")[0]
    q2 = summ.split("## Q2 real labels")[1].split("## Positive control")[0]

    def rate(block, row):
        m = re.search(r"^\| " + re.escape(row) + r"(?: \([^|]*\))? \| ([\d.]+)% \(95% ([\d.]+) to ([\d.]+)\)", block, re.M)
        return None if m is None else (float(m.group(1)) / 100, [float(m.group(2)) / 100, float(m.group(3)) / 100])
    return summ, q1, q2, rate


def _wilson(k, n, z=1.96):
    import math
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    w = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - w, c + w]


def _null_row(ax, y, obs, null, marker, col, label_obs=None):
    """One row: filled observed marker, open marker with central 95% for the null; values in the data unit given."""
    lo, hi = np.percentile(null, [2.5, 97.5])
    m = float(np.mean(null))
    ax.plot([lo, hi], [y, y], color=col, lw=1.2, solid_capstyle="round", zorder=2)
    ax.plot(m, y, marker, ms=4.5, color=col, mfc="white", mec=col, mew=0.9, zorder=3)
    ax.plot(obs, y, "o", ms=4.2, color=INK, mec="white", mew=0.5, zorder=4)
    return m, lo, hi


def _ed3_style(ax, xlabel, chance=None):
    if chance is not None:
        ax.axvline(chance, color=MUTED, lw=0.6, ls=(0, (2, 2)))
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", color=GRID, lw=0.5); ax.set_axisbelow(True)
    for sd in ("top", "right"):
        ax.spines[sd].set_visible(False)


def _sum_null(lists):
    """Exact null of the mean over mice: convolution of each mouse's null on a 0.001-point grid (descriptive quantiles)."""
    d = np.ones(1)
    lo = 0
    for x in lists:
        v = np.rint(np.asarray(x) * 1000).astype(int)
        m = v.min()
        h = np.bincount(v - m) / len(v)
        d = np.convolve(d, h)
        lo += m
    return d, lo, len(lists)


def _quant(d, lo, n, q):
    k = int(np.searchsorted(np.cumsum(d), q))
    return (lo + k) / 1000 / n


def ed3():
    """Reanalyses of published data. (a) rat auditory cortex (Yaron et al. 2025, post hoc; yaron-panel). (b) Jahn et al. 2024,
    true template, 900 ms, observed and permutation nulls (step 6 outputs). (c) Klee et al. 2026, group mean over 6 mice,
    observed and nulls (step 6b outputs). Every plotted value is printed with its source."""
    s = json.load(open(R / "yaron-panel/results/fixed_vs_repeated.json"))
    cell = {}
    with tarfile.open(R / "step6-reanalysis-cell/vm-out-a2/a2-out.tgz") as z:
        for n in ("primary", "trial"):
            cell[n] = json.load(z.extractfile("out-a2/test-%s.json" % n))
    sa = json.load(open(R / "step6b-reanalysis-sciadv/out/tests.json"))
    fig, axes = plt.subplots(3, 1, figsize=(4.6, 5.0), gridspec_kw={"height_ratios": [1.5, 6, 4]})
    ax = axes[0]
    obs, arms = s["observed"], s["arms"]
    rows = [("repeated", "Unit selection repeated", INK, "D"), ("fixed", "Selected units held fixed", INK, "s")]
    for i, (key, _, col, mk) in enumerate(rows):
        m = arms[key]
        ax.plot([m["q025"], m["q975"]], [i, i], color=col, lw=1.2, solid_capstyle="round", zorder=2)
        ax.plot(m["null_mean"], i, mk, ms=4.5, color=col, mfc="white", mec=col, mew=0.9, zorder=3)
        print("ED3a %-8s mean %.4f, 95%% %.3f to %.3f  yaron-panel/results/fixed_vs_repeated.json arms.%s" % (key, m["null_mean"], m["q025"], m["q975"], key))
    ax.axvline(obs, color=INK, lw=1)
    ax.text(obs - 0.006, -0.72, "observed %.3f" % obs, ha="right", va="center", fontsize=6, color=INK)
    print("ED3a observed %.4f  fixed_vs_repeated.json observed" % obs)
    ax.set_yticks(range(2)); ax.set_yticklabels([r[1] for r in rows]); ax.set_ylim(1.5, -1.1); ax.set_xlim(-0.2, 0.4)
    _ed3_style(ax, "Held-out correlation", 0.0)
    ax = axes[1]
    labels = []
    y = 0
    for reg in ("LIP", "FEF", "LPFC"):
        for test, name, mk, col in (("trial", "trial-level shuffle", "o", MUTED), ("primary", "block permutation", "D", INK)):
            r = cell[test]["regions"][reg]
            m, lo, hi = _null_row(ax, y, 100 * r["observed"], 100 * np.array(r["null"], float), mk, col)
            labels.append("%s, %s" % (reg, name))
            print("ED3b %s %s: observed %.2f, null mean %.2f, 95%% %.2f to %.2f, p %.4f  step 6 test-%s.json" % (reg, test, 100 * r["observed"], m, lo, hi, r["p"], test))
            y += 1
        y += 0.5
    ax.set_yticks([0, 1, 2.5, 3.5, 5, 6]); ax.set_yticklabels(labels); ax.set_ylim(6.7, -0.7); ax.set_xlim(25, 95)
    _ed3_style(ax, "Decoding accuracy of the template bin (%)", 100 / 3)
    ax = axes[2]
    labels = []
    y = 0
    rng = np.random.default_rng(20261109)
    for wn, wname in (("ITI", "intertrial"), ("PERI", "peri-movement")):
        obs = sa["group"][wn]["block"]["T"]
        tr = np.array([rng.choice(np.array(mo["windows"][wn]["trial"]["null"], float), 100000) for mo in sa["mice"]]).mean(0)
        m, lo, hi = _null_row(ax, y, obs, tr, "o", MUTED)
        print("ED3c %s trial: observed %.2f, null mean %.2f, 95%% %.2f to %.2f  tests.json mice[].windows.%s.trial.null (100,000 random combinations)" % (wn, obs, m, lo, hi, wn))
        labels.append("%s, trial-level shuffle" % wname); y += 1
        d, l0, n = _sum_null([mo["windows"][wn]["block"]["null"] for mo in sa["mice"]])
        lo, hi = _quant(d, l0, n, 0.025), _quant(d, l0, n, 0.975)
        m = float(np.sum(d * (l0 + np.arange(len(d))))) / 1000 / n
        ax.plot([lo, hi], [y, y], color=INK, lw=1.2, solid_capstyle="round", zorder=2)
        ax.plot(m, y, "D", ms=4.5, color=INK, mfc="white", mec=INK, mew=0.9, zorder=3)
        ax.plot(obs, y, "o", ms=4.2, color=INK, mec="white", mew=0.5, zorder=4)
        print("ED3c %s block: observed %.2f, null mean %.2f, 95%% %.2f to %.2f, p %.3g  tests.json group.%s.block; exact null by convolution" % (wn, obs, m, lo, hi, sa["group"][wn]["block"]["p"], wn))
        labels.append("%s, group block test" % wname); y += 1.5
    ax.set_yticks([0, 1, 2.5, 3.5]); ax.set_yticklabels(labels); ax.set_ylim(4.2, -0.7); ax.set_xlim(44, 72)
    _ed3_style(ax, "Decoding accuracy of context, mean over 6 mice (%)", 50.0)
    h = [plt.Line2D([], [], marker="o", ls="", ms=4.2, color=INK, label="observed"),
         plt.Line2D([], [], marker="o", ls="-", lw=1, ms=4.5, color=MUTED, mfc="white", label="trial-level null"),
         plt.Line2D([], [], marker="D", ls="-", lw=1, ms=4.5, color=INK, mfc="white", label="block null")]
    fig.legend(handles=h, loc="upper center", ncol=3, frameon=False, fontsize=6)
    for a, c in zip(axes, "abc"):
        a.text(-0.42, 1.02, c, transform=a.transAxes, fontweight="bold", fontsize=8, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97), h_pad=0.8)
    fig.savefig(OUT / "ed3.pdf", metadata=META)
    fig.savefig(OUT / "ed3.png", dpi=300)


def ed8():
    """IBL brain-wide map: every test row on fake block sequences (open) and on the real block side (filled),
    mouse-weighted rates with mouse-cluster BCa 95% intervals (runs/SUMMARY.md)."""
    _, q1, q2, rate = _ibl()
    rows = [("P1", "Binomial-type z test"), ("P2", "Trial-level permutation (scikit-learn rule)"), ("P4", "Training labels only"),
            ("PS-fixed", "Pseudosessions, decoder fitted once"), ("PS-refit", "Pseudosession test (decoder refit)"),
            ("P1-block", "Binomial-type z test, whole blocks out"), ("P2-block", "Trial-level permutation, whole blocks out"),
            ("P4-block", "Training labels only, whole blocks out"), ("PS-fixed-block", "Pseudosessions fitted once, whole blocks out"),
            ("PS-refit-block", "Pseudosession test, whole blocks out"), ("SEL-fixed", "Selected units fixed in the pseudosessions"),
            ("SEL-repeat", "Unit selection repeated in each pseudosession"), ("IID-P1", "Labels per trial: binomial-type z test"),
            ("IID-P2", "Labels per trial: trial-level permutation"), ("IID-P4", "Labels per trial: training labels only"),
            ("IID-SEL-fixed", "Labels per trial: selected units fixed"), ("IID-SEL-repeat", "Labels per trial: selection repeated")]
    fig, ax = plt.subplots(figsize=(5.6, 4.4))
    for i, (key, _) in enumerate(rows):
        for blk, name, filled, off in ((q1, "Fake block sequences", False, -0.17), (q2, "Real block side", True, 0.17)):
            v = rate(blk, key)
            if v is None:
                print("ED8 %-15s %-20s not run" % (key, name))
                continue
            dot(ax, i + off, v[0], v[1], MOUSE, "o", filled, label=name if i == 0 else None)
            print("ED8 %-15s %-20s %.3f [%.3f, %.3f]  runs/SUMMARY.md %s" % (key, name, v[0], v[1][0], v[1][1], name))
    ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[1] for r in rows], fontsize=6.3); ax.invert_yaxis()
    for y in (4.5, 9.5, 11.5):
        ax.axhline(y, color=GRID, lw=0.6)
    style(ax, "Brain regions called decodable, per session (%)")
    ax.legend(frameon=False, loc="lower right", fontsize=6, handletextpad=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "ed8.pdf", metadata=META)
    fig.savefig(OUT / "ed8.png", dpi=300)


def ed9():
    """IBL: (a) per region (at least 3 sessions, real block side), share of its region-sessions called decodable by
    the scikit-learn rule against the pseudosession test; (b) positive control, stimulus side 0-100 ms after onset,
    pseudosession test, by the region's mark in the published map (region_info.csv)."""
    import re
    summ, _, _, _ = _ibl()
    reg = re.findall(r"^- (.+?): P2 (\d+)/(\d+), PS-refit (\d+)/(\d+)$", summ, re.M)
    pc = summ.split("## Positive control")[1].split("## Extended Data")[0]
    groups = [(lab, *map(int, re.search(r"^\| " + lab + r" \| (\d+) \| (\d+) \| (\d+) \|", pc, re.M).groups()))
              for lab in ("stimulus-significant", "other", "no value")]
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 3.0), gridspec_kw={"width_ratios": [1, 1.1]})
    for name, k2, n2, kp, n in reg:
        x, y = 100 * int(kp) / int(n), 100 * int(k2) / int(n2)
        a.plot(x, y, "o", ms=2 + 0.12 * int(n), color=MOUSE, mfc="none", mew=0.7, alpha=0.9)
        print("ED9a %-8s P2 %s/%s  PS-refit %s/%s  runs/SUMMARY.md Extended Data list" % (name, k2, n2, kp, n))
    a.plot([0, 100], [0, 100], color=MUTED, lw=0.6, ls=(0, (3, 2)))
    a.set_xlim(-2, 102); a.set_ylim(-2, 102); a.set_aspect("equal")
    a.set_xlabel("Pseudosession test (%)"); a.set_ylabel("Trial-level permutation (%)")
    a.grid(color=GRID, lw=0.5); a.set_axisbelow(True)
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.set_title("a  Real block side, %d regions" % len(reg), loc="left", fontsize=7)
    a.plot([], [], "o", color=MOUSE, mfc="none", ms=3.2, label="10 sessions"); a.plot([], [], "o", color=MOUSE, mfc="none", ms=8.0, label="50 sessions")
    a.legend(frameon=False, loc="lower right", fontsize=6, title="Marker size", title_fontsize=6)
    labels = {"stimulus-significant": "Stimulus-significant\nin the published map", "other": "Other regions", "no value": "No value in the map"}
    for i, (lab, k, m, mice) in enumerate(groups):
        ci = _wilson(k, k + m)
        dot(b, i, k / (k + m), ci, MOUSE, "o", True)
        b.text(100 * ci[1] + 2, i, "%d of %d (%d mice)" % (k, k + m, mice), va="center", fontsize=6, color=INK)
        print("ED9b %-22s %d of %d, mice %d, Wilson %.3f-%.3f  runs/SUMMARY.md positive control" % (lab, k, k + m, mice, ci[0], ci[1]))
    b.set_yticks(range(3)); b.set_yticklabels([labels[g[0]] for g in groups]); b.invert_yaxis()
    style(b, "Brain regions significant per session, stimulus side (%)", xmax=100)
    b.set_ylim(2.6, -0.6)
    b.set_title("b  Positive control (pseudosession test)", loc="left", fontsize=7)
    fig.tight_layout(w_pad=2.5)
    fig.savefig(OUT / "ed9.pdf", metadata=META)
    fig.savefig(OUT / "ed9.png", dpi=300)


def ed7():
    """Group-level tests on labels with no information: t-test and sign-flip against a group null built from the
    block permutation test's null accuracies (mouse: 200 fake-label experiments; EEG: 50 assignment indices)."""
    al = json.load(open(R / "step2-comparison/results/allen_summary.json"))["new"]
    eeg = json.load(open(R / "step2b-eeg/results/summary_2b.json"))["group_level"]
    rows = [("Mouse, shuffled 5-fold", al["shared24/main"]), ("Mouse, default folds", al["shared24/tool"]),
            ("Mouse, whole blocks out", al["shared24/block"]), ("Mouse, grating trials, shuffled 5-fold", al["dg_shared24/main"])]
    fig, ax = plt.subplots(figsize=(4.4, 2.4))
    for i, (lab, d) in enumerate(rows):
        r = d["group_level"]["rate_over_null_experiments"]
        for key, name, mk, col, off in (("t_test", "t-test against chance", "s", MOUSE, -0.18), ("sign_flip", "Sign-flip test", "^", MOUSE, 0.0),
                                        ("valid_group", "Group null from block permutations", "o", INK, 0.18)):
            ax.plot(100 * r[key], i + off, mk, ms=4.5, color=col, mfc=col if key != "valid_group" else "white", mew=0.9, label=name if i == 0 else None)
            print("ED7 %-40s %-12s %.3f  allen_summary new %s" % (lab, key, r[key], "group_level"))
    i = len(rows)
    ax.plot(100 * eeg["t_test_share"], i - 0.18, "s", ms=4.5, color=EEG)
    ax.plot(100 * eeg["group_null_share"], i + 0.18, "o", ms=4.5, color=INK, mfc="white", mew=0.9)
    print("ED7 EEG t-test %.3f, group null %.3f  summary_2b group_level" % (eeg["t_test_share"], eeg["group_null_share"]))
    ax.set_yticks(range(i + 1)); ax.set_yticklabels([r[0] for r in rows] + ["Human EEG, shuffled 5-fold"]); ax.invert_yaxis()
    style(ax, "Experiments with p < 0.05 (%)")
    fig.legend(*ax.get_legend_handles_labels(), loc="upper center", ncol=3, frameon=False, fontsize=5.5)
    fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(OUT / "ed7.pdf", metadata=META); fig.savefig(OUT / "ed7.png", dpi=300)


def ed10():
    """Power: simulation (two effect sizes, raw and size-adjusted) and EEG graded control (post hoc)."""
    pw = _sim()["power"]
    eeg = json.load(open(R / "step2b-eeg/results/summary_2b.json"))["size_adjusted_power_pos_graded"]
    rules = ("P1", "P2", "P3", "P4", "P5")
    names = {"P1": "Binomial test", "P2": "Trial-level permutation", "P3": "Within-run permutation", "P4": "Training labels only", "P5": "Block permutation test"}
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.6))
    for j, (key, lab) in enumerate((("pw0_delta0.2", "smaller effect"), ("pw1_delta0.5", "larger effect"))):
        for i, r in enumerate(rules):
            d = pw[key][r]
            y = i - 0.15 + 0.3 * j
            a.plot(100 * d["raw_power"], y, "s", ms=4, color=SIM, mfc=SIM if j else "white", mew=0.9)
            a.plot(100 * d["size_adjusted_power"], y, "o", ms=4, color=INK, mfc=INK if j else "white", mew=0.9)
            print("ED10a %s %-4s raw %.3f size-adjusted %.3f  sim_summary power %s" % (lab, r, d["raw_power"], d["size_adjusted_power"], key))
    a.set_yticks(range(5)); a.set_yticklabels([names[r] for r in rules]); a.invert_yaxis()
    style(a, "Power (%)"); a.set_title("a  Simulation (upper: smaller effect, open;\n    lower: larger effect, filled)", loc="left", fontsize=6.5)
    for i, r in enumerate(rules):
        d = eeg[r]
        b.plot(100 * d["raw_power"], i - 0.15, "D", ms=4, color=EEG)
        dot(b, i + 0.15, d["size_adjusted_power"], d["ci95"], INK, "o", False)
        print("ED10b %-4s raw %.3f size-adjusted %.3f [%.3f, %.3f]  summary_2b size_adjusted_power_pos_graded" % (r, d["raw_power"], d["size_adjusted_power"], *d["ci95"]))
    b.set_yticks(range(5)); b.set_yticklabels([names[r] for r in rules]); b.invert_yaxis()
    style(b, "Power (%)"); b.set_title("b  Human EEG, graded control (post hoc)", loc="left", fontsize=7)
    h = [plt.Line2D([], [], ls="", marker="s", color=SIM, ms=4, label="Raw power (simulation)"),
         plt.Line2D([], [], ls="", marker="D", color=EEG, ms=4, label="Raw power (EEG)"),
         plt.Line2D([], [], ls="", marker="o", color=INK, mfc="white", ms=4, label="Size-adjusted power (EEG: 95% interval)")]
    fig.legend(handles=h, loc="upper center", ncol=3, frameon=False, fontsize=6)
    fig.tight_layout(rect=(0, 0, 1, 0.9)); fig.savefig(OUT / "ed10.pdf", metadata=META); fig.savefig(OUT / "ed10.png", dpi=300)


def ed4():
    """Simulation grid, random block design: trial-level permutation (P2) and the block permutation test (P5) by drift
    time constant, drift strength and number of blocks, for the three splits."""
    import re
    c = _sim()["cells"]
    fig, axes = plt.subplots(3, 3, figsize=(7.2, 5.4), sharex=True, sharey=True)
    taus = [7, 20, 67, 160]
    for r, (split, sname) in enumerate((("main", "shuffled 5-fold"), ("tool", "default folds"), ("block", "whole blocks out"))):
        for col, B in enumerate((4, 12, 24)):
            ax = axes[r, col]
            for drift, ls in (("0", ":"), ("1", "-"), ("2", "--")):
                for rule, color, mk in (("P2", SIM, "s"), ("P5", INK, "o")):
                    ys = []
                    for tau in taus:
                        k = next((k for k in c if re.match(rf"c\d+_random_B{B}_tau{tau}_d{drift}_t0_{split}$", k)), None)
                        ys.append(100 * c[k][rule]["rate"] if k else float("nan"))
                        if k:
                            print("ED4 %-5s B%-2s tau%-3s drift %s %s %.3f  sim_summary %s" % (split, B, tau, drift, rule, c[k][rule]["rate"], k))
                    ax.plot(range(4), ys, ls=ls, color=color, marker=mk, ms=2.5, lw=0.9)
            ax.axhline(5, color=MUTED, lw=0.6, ls=(0, (3, 2)))
            ax.set_ylim(-3, 103); ax.set_xticks(range(4), [str(t) for t in taus])
            ax.grid(axis="y", color=GRID, lw=0.4)
            for s in ("top", "right"):
                ax.spines[s].set_visible(False)
            if r == 0:
                ax.set_title(f"{B} blocks", fontsize=7)
            if col == 0:
                ax.set_ylabel(f"{sname}\nrejection rate (%)")
            if r == 2:
                ax.set_xlabel("Drift time constant (trials)")
    h = [plt.Line2D([], [], color=SIM, marker="s", ms=3, lw=0.9, label="Trial-level permutation"),
         plt.Line2D([], [], color=INK, marker="o", ms=3, lw=0.9, label="Block permutation test"),
         plt.Line2D([], [], color=MUTED, ls=":", lw=0.9, label="no slow drift"), plt.Line2D([], [], color=MUTED, ls="-", lw=0.9, label="drift 1"),
         plt.Line2D([], [], color=MUTED, ls="--", lw=0.9, label="drift 2")]
    fig.legend(handles=h, loc="upper center", ncol=5, frameon=False, fontsize=6)
    fig.tight_layout(rect=(0, 0, 1, 0.95)); fig.savefig(OUT / "ed4.pdf", metadata=META); fig.savefig(OUT / "ed4.png", dpi=300)


FIGS = {n: globals()[f"ed{n}"] for n in range(1, 11)}

if __name__ == "__main__":
    want = [int(a) for a in sys.argv[1:]] or sorted(FIGS)
    for n in want:
        FIGS[n]()
