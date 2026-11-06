#!/usr/bin/env python3
"""BC figures from the summary outputs only (no row file is read). Prints every plotted value with its source.

Fig. 1: rate of p < 0.05 on labels with no information, training and test trials sharing blocks, for four tests
(rows) in three datasets (markers). Fig. 2a: real toolboxes run with their tutorials' split and permutation
(simulated balanced-run layout L4) against the block test. Fig. 2b (IBL) is added after the IBL results note.
Colors: validated categorical slots 1-3 (dataviz reference palette, light surface; CVD and normal-vision checks
pass, aqua below 3:1 contrast -> distinct marker shapes and a legend carry identity).
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("pdf")
import matplotlib.pyplot as plt

R = Path(__file__).resolve().parents[1] / "analyses"   # public layout: the analyses/ folder of this repository
OUT = Path(__file__).resolve().parent
INK, MUTED, GRID = "#1f1f1e", "#6b6a64", "#d9d8d2"
COL = {"Simulation": "#2a78d6", "Mouse (Neuropixels)": "#eb6834", "Human EEG": "#1baf7a",
       "fMRI (post hoc)": "#6b6a64", "Body-worn sensors (post hoc)": "#6b6a64"}
MARK = {"Simulation": "s", "Mouse (Neuropixels)": "o", "Human EEG": "D", "fMRI (post hoc)": "^",
        "Body-worn sensors (post hoc)": "v"}
OPEN = {"fMRI (post hoc)", "Body-worn sensors (post hoc)"}   # post hoc datasets: open neutral markers, identity by shape and legend
plt.rcParams.update({"font.family": "sans-serif", "font.size": 7, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
                     "xtick.color": MUTED, "ytick.color": INK, "pdf.fonttype": 42})


def wilson(h, n, z=1.96):
    p = h / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    w = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - w, c + w]


sim = json.load(open(R / "step2-comparison/results/sim_summary.json"))["cells"]
prim = next(v for k, v in sim.items() if k.startswith("c000_random_B12_tau20_d1_t0_main"))
allen = json.load(open(R / "step2-comparison/results/allen_summary.json"))["new"]["shared24/main"]
eeg = json.load(open(R / "step2b-eeg/results/summary_2b.json"))["cells"]["balanced/main/main/cleaned_s5"]
s1 = json.load(open(R / "step1-decomposition/results/results.json"))["new/std6"]["shared24/lr_topk/blk_fixed"]
fmri = json.load(open(R / "step4-fmri-haxby/results/summary.json"))["cells"]
sens = json.load(open(R / "step5-pamap2/results/summary.json"))["cells"]


def simval(rule):
    d = prim[rule]
    return d["rate"], d["wilson95"]


rows = [
    ("1  Trial-level permutation\n(scikit-learn rule)", "P2", "single trials", "yes"),
    ("2  Block permutation,\nfixed decoder", None, "whole blocks", "no"),
    ("3  Training-label permutation\n(PyMVPA)", "P4", "training trials", "yes"),
    ("4  Block permutation test", "P5", "all trials, by block", "yes"),
]
vals = []
for i, (lab, rule, _perm, _refit) in enumerate(rows):
    if rule is None:
        vals.append((i, "Mouse (Neuropixels)", s1["mean"], s1["ci"], "step1 results.json shared24/lr_topk/blk_fixed"))
        continue
    r, ci = simval(rule)
    vals.append((i, "Simulation", r, ci, "sim_summary c000 %s (Wilson)" % rule))
    vals.append((i, "Mouse (Neuropixels)", allen[rule]["mean"], allen[rule]["ci95"], "allen_summary new shared24/main %s" % rule))
    vals.append((i, "Human EEG", eeg[rule]["mean"], eeg[rule]["ci95"], "summary_2b balanced/main/main/cleaned_s5 %s" % rule))
    c4 = fmri["fake/detrended/main/%s" % rule]
    vals.append((i, "fMRI (post hoc)", c4["mean"], c4["ci95"], "step4 summary fake/detrended/main %s" % rule))
    c5 = sens["fake/windows2s/main/%s" % rule]
    vals.append((i, "Body-worn sensors (post hoc)", c5["mean"], c5["ci95"], "step5 summary fake/windows2s/main %s" % rule))

fig, ax = plt.subplots(figsize=(3.5, 2.7))
off = {"Simulation": -0.3, "Mouse (Neuropixels)": -0.15, "Human EEG": 0.0, "fMRI (post hoc)": 0.15,
       "Body-worn sensors (post hoc)": 0.3}
for i, ds, m, ci, src in vals:
    y = i + off[ds]
    ax.plot([100 * ci[0], 100 * ci[1]], [y, y], color=COL[ds], lw=1.2, solid_capstyle="round", zorder=2)
    if ds in OPEN:
        ax.plot(100 * m, y, MARK[ds], ms=4.0, color=COL[ds], mfc="white", mec=COL[ds], mew=0.9, zorder=3, label=ds)
    else:
        ax.plot(100 * m, y, MARK[ds], ms=4.5, color=COL[ds], mec="white", mew=0.8, zorder=3, label=ds)
    print("Fig1 row %d %-20s %.3f [%.3f, %.3f]  %s" % (i, ds, m, ci[0], ci[1], src))
ax.axvline(5, color=MUTED, lw=0.8, ls=(0, (3, 2)), zorder=1)
ax.text(6, 0.5, "5%", color=MUTED, va="center", fontsize=6)
ax.set_yticks(range(4))
ax.set_yticklabels([r[0] for r in rows])
# what each test permutes and whether it refits the decoder, as two columns between the labels and the plot
for i, r in enumerate(rows):
    ax.text(-0.25, i, r[2], transform=ax.get_yaxis_transform(), ha="center", va="center", fontsize=6, color=INK)
    ax.text(-0.06, i, r[3], transform=ax.get_yaxis_transform(), ha="center", va="center", fontsize=6, color=INK)
ax.text(-0.25, -0.75, "Labels permuted", transform=ax.get_yaxis_transform(), ha="center", va="center", fontsize=6, color=MUTED)
ax.text(-0.06, -0.75, "Refit", transform=ax.get_yaxis_transform(), ha="center", va="center", fontsize=6, color=MUTED)
ax.tick_params(axis="y", pad=88)
ax.invert_yaxis()
ax.set_xlim(0, 102)
ax.set_xlabel("Labels with no information called decodable (%)")
ax.grid(axis="x", color=GRID, lw=0.5)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
h, l = ax.get_legend_handles_labels()
uniq = dict(zip(l, h))
ax.legend(uniq.values(), uniq.keys(), frameon=False, fontsize=6, loc="upper center", bbox_to_anchor=(0.4, -0.2),
          ncol=3, handletextpad=0.3, columnspacing=0.8)  # five entries: two rows, below the axis label
fig.savefig(OUT / "fig1.pdf", bbox_inches="tight", metadata={"Creator": None, "Producer": None, "CreationDate": None})

# Fig. 2a: toolboxes as shipped (layout L4, 500 replicates each; rates from SUMMARY-TOOLS.md)
tools = [("CoSMoMVPA", 0.202), ("CoSMoMVPA, z-scored", 0.208), ("PyMVPA", 0.184), ("PyMVPA, z-scored", 0.214),
         ("Block permutation test", 0.044)]
txt = (R / "step2-comparison/runs_add3/tools/SUMMARY-TOOLS.md").read_text()
for name, key in [("CoSMoMVPA", "| L4 | CoSMoMVPA main **(headline)** | 500 | 500 | 0 | 20.2%"),
                  ("CoSMoMVPA, z-scored", "| L4 | CoSMoMVPA zscore **(headline)** | 500 | 500 | 0 | 20.8%"),
                  ("PyMVPA", "| L4 | PyMVPA main **(headline)** | 500 | 500 | 0 | 18.4%"),
                  ("PyMVPA, z-scored", "| L4 | PyMVPA zscore **(headline)** | 500 | 500 | 0 | 21.4%"),
                  ("Block permutation test", "| L4 | P5 | 500 | 500 | 0 | 4.4%")]:
    assert key in txt, key
fig, ax = plt.subplots(figsize=(3.3, 1.6))
for i, (name, r) in enumerate(tools):
    ci = wilson(round(r * 500), 500)
    c = "#52514e"  # one neutral ink: identity is in the row labels (no clash with Fig. 1 dataset colors)
    ax.plot([100 * ci[0], 100 * ci[1]], [i, i], color=c, lw=1.2, zorder=2)
    ax.plot(100 * r, i, "o" if i < 4 else "D", ms=4.5, color=c, mfc=c if i < 4 else "white", mec=c if i == 4 else "white", mew=0.8, zorder=3)
    ax.text(100 * ci[1] + 1.2, i, "%.0f%%" % (100 * r), va="center", fontsize=6, color=INK)
    print("Fig2a %-26s %.3f [%.3f, %.3f]  SUMMARY-TOOLS.md L4 (Wilson, n 500)" % (name, r, ci[0], ci[1]))
ax.axvline(5, color=MUTED, lw=0.8, ls=(0, (3, 2)))
ax.set_yticks(range(len(tools)))
ax.set_yticklabels([t[0] for t in tools])
ax.invert_yaxis()
ax.set_xlim(0, 30)
ax.set_xlabel("Labels with no information called decodable (%)")
ax.grid(axis="x", color=GRID, lw=0.5)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
fig.savefig(OUT / "fig2a.pdf", bbox_inches="tight", metadata={"Creator": None, "Producer": None, "CreationDate": None})
print("written fig1.pdf fig2a.pdf")

# Fig. 2b: IBL brain-wide recordings (values parsed from the stamped summary output runs/SUMMARY.md)
import re
summ = (R / "step3-ibl/runs/SUMMARY.md").read_text()
q1 = summ.split("## Q1 fake labels")[1].split("## Primary contrasts")[0]
q2 = summ.split("## Q2 real labels")[1].split("## Positive control")[0]


def rate(block, row):
    pat = r"^\| " + re.escape(row) + r"(?: \([^|]*\))? \| ([\d.]+)% \(95% ([\d.]+) to ([\d.]+)\)"
    m = re.search(pat, block, re.M)
    return float(m.group(1)) / 100, [float(m.group(2)) / 100, float(m.group(3)) / 100]


ibl = [("Fake block sequences", "scikit-learn rule", rate(q1, "P2")),
       ("Fake block sequences", "Pseudosession test", rate(q1, "PS-refit")),
       ("Real block side", "scikit-learn rule", rate(q2, "P2")),
       ("Real block side", "Pseudosession test", rate(q2, "PS-refit"))]
fig, ax = plt.subplots(figsize=(3.3, 1.5))
for i, (lab, test, (m, ci)) in enumerate(ibl):
    filled = test == "scikit-learn rule"
    ax.plot([100 * ci[0], 100 * ci[1]], [i, i], color="#52514e", lw=1.2, zorder=2)
    ax.plot(100 * m, i, "o" if filled else "D", ms=4.5, color="#52514e", mfc="#52514e" if filled else "white",
            mec="#52514e" if not filled else "white", mew=0.8, zorder=3)
    ax.text(100 * ci[1] + 3, i, "%.0f%%" % (100 * m), va="center", fontsize=6, color=INK)
    print("Fig2b %-22s %-20s %.3f [%.3f, %.3f]  runs/SUMMARY.md" % (lab, test, m, ci[0], ci[1]))
ax.axvline(5, color=MUTED, lw=0.8, ls=(0, (3, 2)))
ax.set_yticks(range(4))
ax.set_yticklabels(["%s: %s" % (a, b) for a, b, _ in ibl])
ax.invert_yaxis()
ax.set_xlim(0, 100)
ax.set_xlabel("Brain regions called decodable, per session (%)")
ax.grid(axis="x", color=GRID, lw=0.5)
ax.set_axisbelow(True)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
both = re.search(r"\| P2 sig \| (\d+) \| (\d+) \|", q2).groups()
neither = re.search(r"\| P2 not \| (\d+) \| (\d+) \|", q2).groups()
print("Fig2b verdicts: both %s, P2 only %s, PS-refit only %s, neither %s" % (both[0], both[1], neither[0], neither[1]))
fig.savefig(OUT / "fig2b.pdf", bbox_inches="tight", metadata={"Creator": None, "Producer": None, "CreationDate": None})
print("written fig2b.pdf")
