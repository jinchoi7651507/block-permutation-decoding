#!/usr/bin/env python3
"""Step 2 power: choose delta from the P5-only pilot (addendum 1 §1b; DESIGN §15 "Power"). Fixed before the pilot runs.

Pilot: runs/pp*_delta*.w*.jsonl (primary-cell layout, 50 replicates per delta in {0.1, 0.2, 0.3, 0.5, 0.8}).
P5 power per delta = share of p < 0.05. d_mid = the smallest delta with power in [0.20, 0.50]; d_large = the smallest
delta with power in [0.70, 0.90]. If no delta falls in a band, take the delta whose power is closest to the band
(ties: the smaller delta); if both bands pick the same delta, d_large = the next larger delta. Prints "d_mid,d_large"
for `run_sim_cells.py --power`. Size-adjusted power (summary): threshold of each rule = its 5% quantile of p in the
delta = 0 primary cell (c000), randomised at the tie so that the expected size is exactly 5% (summarize_sim.size_adjusted).
If d_mid is the largest delta, d_large equals it and the output flags "same_delta".
"""
import json
from pathlib import Path

import numpy as np

RUNS = Path(__file__).resolve().parent.parent / "runs"
cells = json.loads((RUNS / "POWER_PILOT_CELLS.json").read_text())
power = {}
for c in cells:
    ps = [json.loads(l)["P5"] for f in RUNS.glob(f"{c['name']}.w*.jsonl") for l in f.read_text().splitlines()]
    ps = [p for p in ps if p is not None and np.isfinite(p)]
    power[c["delta"]] = float(np.mean([p < 0.05 for p in ps])) if ps else None
ds = sorted(d for d in power if power[d] is not None)


def pick(lo, hi):
    inb = [d for d in ds if lo <= power[d] <= hi]
    if inb:
        return inb[0]
    return min(ds, key=lambda d: (min(abs(power[d] - lo), abs(power[d] - hi)), d))


d_mid, d_large = pick(0.20, 0.50), pick(0.70, 0.90)
if d_large == d_mid:
    bigger = [d for d in ds if d > d_mid]
    d_large = bigger[0] if bigger else d_mid
out = {"power": power, "d_mid": d_mid, "d_large": d_large, "same_delta": d_mid == d_large}
(RUNS / "POWER_CHOICE.json").write_text(json.dumps(out, indent=1))
print(f"{d_mid},{d_large}")
