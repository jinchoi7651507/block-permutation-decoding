#!/usr/bin/env python3
"""Step 3 (IBL) label-free preparation, DESIGN.md v1 §2, §6, §9, run in this order after the code addendum is stamped:

  python prep_ibl.py order    --out ../runs/ORDER.json
      bwm_query(freeze='2023_12_bwm_release') reads the package fixture (no network; 699 insertions); probes merged
      per session (eid); eids sorted, ordered by numpy.random.default_rng(20261023).permutation. Writes eid, pids,
      subject per session and the SHA-256 of the fixture file.
  python prep_ibl.py regions  --region-info <paper repo>/brainwidemap/meta/region_info.csv --out ../runs/STIM-REGIONS.json
      Reads only the columns Beryl and stim_dec_sig (pandas usecols); no other column is read or printed.
  python prep_ibl.py budget-meta --order ../runs/ORDER.json --out ../runs/BUDGET-META.json
      Unit counts only, first 60 sessions of the order: good units (label >= 1) per Beryl region per session from the
      clusters tables (clusters.metrics / channels, no spike times), r = mean number of region-sessions with >= 10
      units (void/root excluded).
  python prep_ibl.py realism  --order ../runs/ORDER.json --out ../runs/REALISM.json
      Trials tables only (no spikes), first 30 sessions: block lengths (censored last block left out), number of
      blocks, class share of the real session vs its 220-pseudosession pool (same seeds as the run); strict side
      alternation and the first 90 trials at probabilityLeft 0.5 asserted (a failing session is listed and
      excluded); pooled two-sample KS of block lengths with a permutation p (ties reported). Pre-set response
      (§9): KS p < 0.01 -> PS-refit on real labels reported as approximate and Q2 descriptive only.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def cmd_order(args):
    import brainwidemap
    from brainwidemap.bwm_loading import bwm_query
    df = bwm_query(freeze="2023_12_bwm_release")
    fx = Path(brainwidemap.__file__).parent / "fixtures" / "2023_12_bwm_release.csv"
    sess = {}
    for _, r in df.iterrows():
        s = sess.setdefault(r["eid"], {"eid": r["eid"], "pids": [], "subject": r["subject"]})
        s["pids"].append(r["pid"])
    eids = sorted(sess)
    order = [eids[i] for i in np.random.default_rng(20261023).permutation(len(eids))]
    out = {"freeze": "2023_12_bwm_release", "fixture_sha256": hashlib.sha256(fx.read_bytes()).hexdigest(),
           "n_insertions": int(len(df)), "n_sessions": len(eids), "n_mice": len({s["subject"] for s in sess.values()}),
           "sessions": [{**sess[e], "pids": sorted(sess[e]["pids"])} for e in order]}
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(out["n_insertions"], "insertions,", out["n_sessions"], "sessions,", out["n_mice"], "mice")


def cmd_regions(args):
    import pandas as pd
    ri = pd.read_csv(args.region_info, usecols=["Beryl", "stim_dec_sig"])
    vals = set(ri["stim_dec_sig"].dropna().unique())
    assert vals <= {0, 1, 0.0, 1.0, True, False}, f"unexpected stim_dec_sig coding {vals}"
    sig = sorted(ri.loc[ri["stim_dec_sig"] == 1, "Beryl"].astype(str))
    nov = sorted(ri.loc[ri["stim_dec_sig"].isna(), "Beryl"].astype(str))   # regions absent from the file: also "no value"
    out = {"source_sha256": hashlib.sha256(Path(args.region_info).read_bytes()).hexdigest(),
           "stim_significant": sig, "no_value": nov, "n_rows": int(len(ri))}
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(len(sig), "stimulus-significant regions;", len(nov), "without a value")


def one_public():
    from one.api import ONE
    return ONE(base_url="https://openalyx.internationalbrainlab.org", password="international", silent=True)


def cmd_budget_meta(args):
    from iblatlas.regions import BrainRegions
    one = one_public()
    br = BrainRegions()
    order = json.loads(Path(args.order).read_text())["sessions"][:60]
    per = []
    for s in order:
        counts = {}
        for pid in s["pids"]:
            from brainbox.io.one import SpikeSortingLoader
            ssl = SpikeSortingLoader(pid=pid, one=one)
            clusters = ssl.load_spike_sorting_object("clusters", revision="2024-05-06",
                                                     attribute=["metrics", "channels"])     # metadata only
            channels = ssl.load_channels()
            metrics = clusters["metrics"]
            good = np.asarray(metrics["label"]) >= 1
            acr = br.acronym2acronym(np.asarray(channels["acronym"])[np.asarray(clusters["channels"])], mapping="Beryl")
            for a in acr[good]:
                counts[str(a)] = counts.get(str(a), 0) + 1
        n_rs = sum(1 for a, c in counts.items() if c >= 10 and a not in ("void", "root"))
        per.append({"eid": s["eid"], "region_sessions": n_rs, "units": counts})
    r = float(np.mean([p["region_sessions"] for p in per]))
    Path(args.out).write_text(json.dumps({"r": r, "sessions": per}, indent=1))
    print("r =", round(r, 2))


def block_lengths(pl):
    """Lengths of the biased blocks after the first 90 trials; the last (censored) block is left out."""
    b = pl[90:]
    change = np.where(np.diff(b) != 0)[0]
    edges = np.r_[0, change + 1, len(b)]
    return np.diff(edges)[:-1], b[edges[:-1]]


def cmd_realism(args):
    from brainbox.task.closed_loop import generate_pseudo_session
    from brainwidemap.bwm_loading import load_trials_and_mask
    from scipy import stats
    one = one_public()
    order = json.loads(Path(args.order).read_text())["sessions"]
    real_len, pseudo_len, rows, excluded = [], [], [], []
    for si, s in enumerate(order[:30]):
        trials, mask = load_trials_and_mask(one, s["eid"], min_rt=0.08, max_rt=2.0, exclude_nochoice=True,
                                            exclude_unbiased=True, truncate_to_pass=True)
        from run_ibl import check_trials
        trials = trials.reset_index(drop=True)
        pl = trials["probabilityLeft"].to_numpy()
        why = check_trials(trials, mask.to_numpy())             # the same checks as the run (90 trials, alternation)
        if why:
            excluded.append({"eid": s["eid"], "reason": why})
            continue
        lens, sides = block_lengths(pl)
        alt = bool(np.all(sides[1:] != sides[:-1]))
        real_len += list(lens)
        share = float(np.mean(np.isclose(pl[mask.to_numpy()], 0.8)))
        ps_share, ps_nblocks = [], []
        for j in range(220):
            np.random.seed([2026, 30, si, j])
            ps = generate_pseudo_session(trials, generate_choices=False)["probabilityLeft"].to_numpy()
            l2, _ = block_lengths(ps)
            pseudo_len += list(l2)
            ps_share.append(float(np.mean(np.isclose(ps[mask.to_numpy()], 0.8))))
            ps_nblocks.append(len(l2))
        rows.append({"eid": s["eid"], "n_blocks": int(len(lens)), "pseudo_n_blocks_median": float(np.median(ps_nblocks)),
                     "share_left_block": share, "pseudo_share_q": float(np.mean(np.array(ps_share) <= share)),
                     "strict_alternation": alt})
    real_len, pseudo_len = np.array(real_len), np.array(pseudo_len)
    ks = stats.ks_2samp(real_len, pseudo_len).statistic
    rng = np.random.default_rng(20261024)
    pooled = np.r_[real_len, pseudo_len]
    null = []
    for _ in range(2000):
        rng.shuffle(pooled)
        null.append(stats.ks_2samp(pooled[: len(real_len)], pooled[len(real_len):]).statistic)
    p = float((1 + np.sum(np.array(null) >= ks - 1e-12)) / 2001)
    out = {"ks": float(ks), "ks_perm_p": p, "n_real_blocks": int(len(real_len)), "n_pseudo_blocks": int(len(pseudo_len)),
           "ties_real": int(len(real_len) - len(np.unique(real_len))), "excluded": excluded, "sessions": rows,
           "response": "Q2 descriptive only; PS-refit on real labels approximate" if p < 0.01 else "none"}
    Path(args.out).write_text(json.dumps(out, indent=1))
    print("KS", round(ks, 3), "perm p", round(p, 4), "->", out["response"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("order", "regions", "budget-meta", "realism"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--order")
    ap.add_argument("--region-info")
    args = ap.parse_args()
    {"order": cmd_order, "regions": cmd_regions, "budget-meta": cmd_budget_meta, "realism": cmd_realism}[args.cmd](args)


if __name__ == "__main__":
    main()
