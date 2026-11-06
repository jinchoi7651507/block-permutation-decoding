#!/usr/bin/env python3
"""Step 1 addendum: training-label-only permutation (Within(Train)); read ../DESIGN-ADDENDUM-within-train.md.

Per (session, std6 area) it rebuilds the step 1 labels (same streams as decompose.py) and computes
  trn_trl  calibration labels permuted across calibration trials, readout refit, held-out labels kept
  trn_blk  calibration labels from a new block assignment of the scheme's null, readout refit, held-out labels kept
plus the observed held-out accuracy, which the summary checks against runs/rows.jsonl.

  python3 within_train.py --dir <nwb folder> --sessions <ids> --out rows.jsonl [--worker i --of n]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("dec", HERE / "decompose.py")
dec = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(dec)
tax, emn = dec.tax, dec.emn

N_DRAW = 200
SPONT = ("iid", "sep24", "paired24", "shared24", "half24")
REAL = ("iid", "sep24", "shared24")
RO_SPONT = ("sel", "rank", "nosel", "lr_topk", "lr_all")
RO_REAL = ("sel", "lr_topk")


def run(counts, block, kind, label_rng, null_rng, blk_rng, rnd_order, rnd_sign, readouts):
    S = dec.Scheme(kind, block, label_rng, counts.shape[1])
    labels, cal, test = S.labels, S.cal, S.test
    R = dec.Readouts(counts, cal, test, rnd_order, rnd_sign)
    trl, blk = [], []
    for _ in range(N_DRAW):
        lp = labels.copy()
        lp[cal] = null_rng.permutation(labels[cal])
        trl.append(lp)
    if kind != "iid":
        S.rng = blk_rng                                       # block-null draws on their own stream, not the label stream
        for _ in range(N_DRAW):
            lb = labels.copy()
            lb[cal] = S._draw()[block][cal]
            blk.append(lb)
    out = {}
    for name in readouts:
        sc, _ = R.fit(name, labels)
        o = {"acc": sc, "acc_nan": bool(not np.isfinite(sc))}
        o["trn_trl"], o["trn_trl_nan"] = dec.mc_p([R.fit(name, lp)[0] for lp in trl], sc)
        if blk:
            o["trn_blk"], o["trn_blk_nan"] = dec.mc_p([R.fit(name, lb)[0] for lb in blk], sc)
        out[name] = o
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--sessions", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--of", type=int, default=1)
    args = ap.parse_args()
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
        on24, blk24 = dec.spont_onsets(path, 8)
        dg_on = np.sort(onset)
        dg_blk = np.concatenate([np.full(len(c), i) for i, c in enumerate(np.array_split(np.arange(len(dg_on)), 24))])
        for a in sorted(set(area)):
            if a not in dec.STD6 or (sid, a) in done:
                continue
            ta = time.time()
            sel = np.where(area == a)[0]
            spc, _ = tax.area_counts(spikes, sel, sp_on)
            row = {"session": sid, "area": a, "n_units": int(spc.shape[0])}
            if spc.shape[0] >= emn.MIN_UNITS_PER_AREA:
                ro = tax.rng_for(sid, a, 31)
                o12, s12 = ro.permutation(spc.shape[0]), bool(ro.integers(2))
                row["iid"] = run(spc, sp_blk, "iid", tax.rng_for(sid, a, dec.STREAMS["iid"]),
                                 tax.rng_for(sid, a, 140 + dec.STREAMS["iid"]), None, o12, s12, RO_SPONT)
                c24, _ = tax.area_counts(spikes, sel, on24)
                if c24.shape[0] >= emn.MIN_UNITS_PER_AREA:
                    ro24 = tax.rng_for(sid, a, 33)
                    o24, s24 = ro24.permutation(c24.shape[0]), bool(ro24.integers(2))
                    for k in SPONT[1:]:
                        row[k] = run(c24, blk24, k, tax.rng_for(sid, a, dec.STREAMS[k]),
                                     tax.rng_for(sid, a, 140 + dec.STREAMS[k]),
                                     tax.rng_for(sid, a, 160 + dec.STREAMS[k]), o24, s24, RO_SPONT)
            dgc, _ = tax.area_counts(spikes, sel, dg_on)
            if dgc.shape[0] >= emn.MIN_UNITS_PER_AREA:
                rd = tax.rng_for(sid, a, 35)
                od, sd = rd.permutation(dgc.shape[0]), bool(rd.integers(2))
                for k in REAL:
                    row[f"dg_{k}"] = run(dgc, dg_blk, k, tax.rng_for(sid, a, 90 + dec.STREAMS[k]),
                                         tax.rng_for(sid, a, 190 + dec.STREAMS[k]),
                                         tax.rng_for(sid, a, 210 + dec.STREAMS[k]), od, sd, RO_REAL)
            row["seconds"] = round(time.time() - ta, 1)
            with out.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(row) + "\n")
            print(f"  {sid} {a}: {row['seconds']} s", flush=True)
        print(f"SESSION {sid}: DONE in {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
