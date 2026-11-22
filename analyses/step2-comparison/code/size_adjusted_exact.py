#!/usr/bin/env python3
"""Step 2: size-adjusted power of the five tests in the two power cells (Extended Data Fig. 10a).

Threshold q = 5% quantile ('lower') of each test's p in the primary cell (delta = 0; P3 errors and NaN count as
p = 1). A p value is tied with q only if it equals q (relative tolerance 1e-9). Ties are randomised so that the
expected size is exactly 5%: reject if p < q, and if p = q with probability g = (0.05 - P0(p < q)) / P0(p = q).
Size-adjusted power = P1(p < q) + g P1(p = q).

sim_summary.json (`power`) holds the same quantity with ties defined as |p - q| <= 1e-12. For the binomial test,
whose threshold is about 1e-32, that definition also counts every smaller p as tied; the values here count only
equal p values. For the four permutation tests both definitions give the same values.

  python size_adjusted_exact.py --runs ../runs --out ../results
"""
import argparse
import json
from pathlib import Path

import numpy as np

from summarize_sim import RULES, finite, load


def size_adjusted(null_rows, alt_rows, rule):
    def ps(rows):
        return np.array([r[rule] if finite(r.get(rule)) else 1.0 for r in rows])
    p0, p1 = ps(null_rows), ps(alt_rows)
    q = float(np.quantile(p0, 0.05, method="lower"))
    tie0, tie1 = np.isclose(p0, q, rtol=1e-9, atol=0.0), np.isclose(p1, q, rtol=1e-9, atol=0.0)
    lt0, eq0 = float(np.mean((p0 < q) & ~tie0)), float(np.mean(tie0))
    g = 0.0 if eq0 == 0 else min(1.0, max(0.0, (0.05 - lt0) / eq0))
    lt1, eq1 = float(np.mean((p1 < q) & ~tie1)), float(np.mean(tie1))
    return {"raw_power": float(np.mean(p1 < 0.05)), "threshold_q": q, "p0_below_q": lt0, "p0_tied": eq0, "tie_prob_g": g,
            "size_adjusted_power": lt1 + g * eq1, "n_null": int(len(p0)), "n_alt": int(len(p1))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default=str(Path(__file__).resolve().parent.parent / "runs"))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "results"))
    args = ap.parse_args()
    runs, out = Path(args.runs), Path(args.out)
    out.mkdir(exist_ok=True)
    prim = json.loads((runs / "CELLS.json").read_text())[0]
    null_rows = load(runs, prim)
    res = {"primary_cell": prim["name"], "tie_rule": "p equal to q, relative tolerance 1e-9"}
    for c in json.loads((runs / "POWER_CELLS.json").read_text()):
        rows = load(runs, c)
        res[c["name"]] = {"delta": c["delta"], "n_reps": len(rows), **{r: size_adjusted(null_rows, rows, r) for r in RULES}}
    (out / "size_adjusted_exact.json").write_text(json.dumps(res, indent=1))
    for k, v in res.items():
        if isinstance(v, dict):
            print(k, " ".join(f"{r} {100 * v[r]['size_adjusted_power']:.1f}" for r in RULES))


if __name__ == "__main__":
    main()
