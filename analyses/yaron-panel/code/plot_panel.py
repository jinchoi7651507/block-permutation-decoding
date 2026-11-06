"""Panel (Extended Data Fig. 3 of the paper): null mean and central 95% range of the held-out score under the block permutation,
with the selection held fixed or repeated in every permutation, against the observed score.

    python plot_panel.py --summary ../results/fixed_vs_repeated.json --out ../results/panel.pdf
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

INK, MUTED, REPEATED, FIXED = "#1f1e1c", "#898781", "#1c5cab", "#52514e"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    s = json.loads(a.summary.read_text())
    obs, arms = s["observed"], s["arms"]

    plt.rcParams.update({"font.size": 8, "font.family": "DejaVu Sans", "axes.edgecolor": MUTED, "pdf.fonttype": 42})
    fig, ax = plt.subplots(figsize=(4.8, 2.0))
    rows = [("Selection repeated\nin every permutation", "repeated", REPEATED),
            ("Selection fixed\n(units chosen on the real labels)", "fixed", FIXED)]
    for y, (label, key, color) in enumerate(rows):
        m = arms[key]
        ax.plot([m["q025"], m["q975"]], [y, y], color=color, lw=2, solid_capstyle="round")
        ax.plot(m["null_mean"], y, "o", ms=6, color=color, mec="white", mew=1.5, zorder=3)
        ax.text(m["null_mean"], y + 0.22, f"mean {m['null_mean']:.3f}", ha="center", va="bottom", fontsize=7, color=INK)
    ax.axvline(obs, color=INK, lw=1)
    ax.text(obs - 0.01, 1.62, f"observed {obs:.2f}", ha="right", va="center", fontsize=7, color=INK)
    ax.axvline(0, color=MUTED, lw=0.6, ls=(0, (2, 2)))
    ax.set_yticks([0, 1], [r[0] for r in rows])
    ax.set_ylim(-0.5, 1.8)
    ax.set_xlim(-0.2, 0.4)
    ax.set_xlabel("Held-out correlation in 1,000 block permutations\n(dot, mean; line, central 95%)")
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.tight_layout()
    a.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(a.out, metadata={"Creator": None, "Producer": None, "CreationDate": None})
    fig.savefig(a.out.with_suffix(".png"), dpi=300, metadata={"Software": None})
    for key in ("repeated", "fixed"):                     # read the drawn values back from the figure
        m = arms[key]
        print(f"{key}: mean {m['null_mean']:.4f}, 95% {m['q025']:.3f} to {m['q975']:.3f}")
    print(f"observed {obs:.4f}")


if __name__ == "__main__":
    main()
