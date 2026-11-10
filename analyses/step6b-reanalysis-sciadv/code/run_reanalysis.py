"""Stage 2 driver (not run in stage 1). See DESIGN.md.

  python run_reanalysis.py inspect --data-dir DIR [--out OUT]
  python run_reanalysis.py gate  --data-dir DIR [--out OUT] [--n-jobs 6]
  python run_reanalysis.py tests --data-dir DIR [--out OUT] [--n-jobs 6]

inspect: manifest check and the field names, types and shapes of the 2p structure; writes OUT/fields.txt; no
        decoding (DESIGN.md 3.2). gate refuses to run without it.
gate  : manifest check, counts, behaviour numbers, clusters, and the Figure 4D port with the authors'
        settings (one subsample, 20 folds, 50 shuffles); writes OUT/gate.json with pass/fail per item, and a
        time-stamped copy of every gate run (OUT/gate-runs/), all of which are reported (DESIGN.md 3.5).
tests : refuses to run unless OUT/gate.json says "pass"; runs tests (a)-(c), the controls and the secondary
        analyses with the seeds and draws of DESIGN.md; writes OUT/tests.json.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import zlib
from pathlib import Path

import numpy as np

import decode as dc
import loader
import matlab_port as mp

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE.parent / "out"
MANIFEST = HERE.parent / "manifest-zenodo-16333867.tsv"
FILES = {"2p": "Data Structures/Switching_2p_Struc_Main.mat",
         "behav": "Data Structures/Switching_Behav_Struc.mat",
         "clusters": "Data Structures/clusters_fig2.mat"}

PUBLISHED = dict(n_neurons=1261, n_neurons_methods=1271, clusters=(118, 868, 275), n_mice=6,
                 rt=(0.30, 6.0), rt_p=0.03, press=(16.9, 16.0), press_p=0.69, reward=(7.49, 7.0),
                 reward_p=0.84, ratio=(0.49, 0.45), ratio_p=0.68)
LAYOUT = [2, 1, 2, 1, 2, 1]
PLOT_LO, PLOT_HI = 59, 90          # 0-based slice of MATLAB bins 60-90 (Figure4.m Panel D, xl = [60, 90])


def means_match(mean, published, nd):
    """Means agree at the printed precision: |mean - published| <= half a unit of the last printed digit (review v2 S4;
    avoids round() ties on binary floats)."""
    return all(abs(m - e) <= 0.5 * 10 ** -d + 1e-9 for m, e, d in zip(mean, published, nd))


def crc32_of(path):
    c = 0
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 22), b""):
            c = zlib.crc32(chunk, c)
    return "%08x" % (c & 0xFFFFFFFF)


def check_manifest(data_dir):
    rows = {r["name"]: r for r in csv.DictReader(open(MANIFEST), delimiter="\t")}
    out = {}
    for k, name in FILES.items():
        p = Path(data_dir) / name
        r = rows[name]
        out[k] = dict(member=name, size_ok=p.stat().st_size == int(r["file_size"]), crc_ok=crc32_of(p) == r["crc32"])
    return out


def mouse_trials(m, mode="fig4", include_go=False, binned=True):
    cells, _ = mp.preprocess_cells(m["cells"], mode)
    return mp.build_trials(cells, m["event_id"], m["event_ts"], m["block_type"], include_go, binned,
                           matlab_label_lag=(mode == "fig2"))


def clean(tr):
    """Drop artefact trials (NaN rows) before subsampling; MATLAB kept them as NaN rows (DESIGN.md 3.4)."""
    k = ~tr["artefact"]
    return {key: (v[k] if key in ("X", "ttype", "block", "ts", "artefact") else v) for key, v in tr.items()}


def block_layout(tr):
    blocks = np.unique(tr["block"])
    lab = np.array([np.unique(tr["ttype"][tr["block"] == b])[0] for b in blocks])
    return blocks, lab


def fig4d_port(tr, s, n_shuffles=50):
    """Authors' Panel D with their settings: one balanced subsample, per bin 20-fold, 50 shuffles."""
    X, y = tr["X"], tr["ttype"]
    rng = dc.rng_for("fig4d", s)
    sub = dc.balanced_subsample(y, rng)
    real, shuf = [], []
    for w in range(mp.N_BINS):
        real.append(dc.window_stat(X[sub], y[sub], [w], ("fig4d", s, w), R=1, subsample=False))
        sh = [dc.window_stat(X[sub], dc.rng_for("fig4d-perm", s, w, b).permutation(y[sub]), [w],
                             ("fig4d", s, w, b), R=1, subsample=False) for b in range(n_shuffles)]
        shuf.append(float(np.mean(sh)))
    return real, shuf


def signrank_pairs(d):
    """Two-sided exact signed-rank p of the paired columns of d (mice x 2), after dropping rows with NaN (MATLAB
    signrank drops NaN pairs; review stat M4). Also returns the number of pairs kept, of zero differences and of
    tied absolute differences (the exact grid of multiples of 1/32 for n = 6 holds only when both are 0)."""
    from scipy.stats import wilcoxon
    d = np.asarray(d, float)
    k = ~np.isnan(d).any(axis=1)
    diff = d[k, 0] - d[k, 1]
    nz = np.abs(diff[diff != 0])
    n_tied = int(len(nz) - len(np.unique(nz)))
    p = float(wilcoxon(d[k, 0], d[k, 1], method="exact").pvalue)
    return p, int(k.sum()), int(np.sum(diff == 0)), n_tied


def inspect(a):
    """Field names, types and shapes of the 2p structure, saved before any decoding (DESIGN.md 3.2)."""
    man = check_manifest(a.data_dir)
    mice = loader.load_2p(str(Path(a.data_dir) / FILES["2p"]))
    L = ["manifest: %s" % json.dumps(man), "reader: %s" % mice[0]["reader"], "mice: %d" % len(mice)]
    for m in mice:
        L.append("mouse %d: cells %s %s; event_id %d (%s); event_ts %s; block_type %s values %s; events %s" % (
            m["index"], m["cells"].shape, m["cells"].dtype, len(m["event_id"]), type(m["event_id"][0]).__name__,
            m["event_ts"].shape, m["block_type"].shape, sorted(set(m["block_type"].tolist())),
            dict(zip(*np.unique(m["event_id"], return_counts=True)))))
    (Path(a.out) / "fields.txt").write_text("\n".join(L) + "\n")
    print("\n".join(L))


def gate(a):
    if not (Path(a.out) / "fields.txt").exists():
        raise SystemExit("run the inspect stage first (DESIGN.md 3.2)")
    res = dict(items={}, notes=[], environment=dc.check_environment(), started=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    res["manifest"] = check_manifest(a.data_dir)
    mice = loader.load_2p(str(Path(a.data_dir) / FILES["2p"]))
    it = res["items"]
    it["n_mice"] = dict(value=len(mice), expected=6, ok=len(mice) == 6)
    # block structure
    lay = []
    for m in mice:
        bt = m["block_type"]
        blk = mp.block_ids(bt)
        seq = [int(bt[blk == b][0]) for b in np.unique(blk)]
        lay.append(seq)
    it["block_order"] = dict(value=lay, expected="[2,1,2,1,2,1] per mouse", ok=all(s == LAYOUT for s in lay),
                             fatal=False)
    res["mice_with_other_layout"] = [i for i, s in enumerate(lay) if s != LAYOUT]
    # neuron counts (Figure 2 pipeline: all cells with a valid dF/F)
    fig2 = [mouse_trials(m, "fig2", include_go=True, binned=False) for m in mice]
    n2 = int(sum(t["X"].shape[1] for t in fig2))
    slm = mp.fig2_self_lever_matrix(fig2)
    ours = mp.fig2_clusters(slm)
    ref_ids, _ = loader.load_clusters(str(Path(a.data_dir) / FILES["clusters"]))
    agree = np.nan
    if len(ref_ids) == len(ours):
        from itertools import permutations
        agree = max(np.mean(np.array([pp[c - 1] for c in ours]) == ref_ids) for pp in permutations([1, 2, 3]))
    sizes = sorted(np.bincount(ours)[1:].tolist())
    it["n_neurons"] = dict(value=n2, expected="1261 (or 1271, Methods) and equal to len(clusterIDs)=%d" % len(ref_ids),
                           ok=n2 in (1261, 1271) and n2 == len(ref_ids))
    it["clusters"] = dict(value=dict(sizes=sizes, agreement=float(agree)), expected="agreement >= 0.99; sizes "
                          "118/868/275 when n = 1261", ok=bool(agree >= 0.99) and (n2 != 1261 or sizes == [118, 275, 868]))
    # behaviour (Figure 1F-J)
    rows = loader.load_behav(str(Path(a.data_dir) / FILES["behav"]))

    def per_mouse(field):
        M = np.full((6, 2, 3), np.nan)
        for r in rows:
            if r["SessionDay"] == 1 and 1 <= r["AnimalID"] <= 6 and 1 <= r["SwitchSessionCounter"] <= 3:
                v = r[field]
                M[int(r["AnimalID"]) - 1, 0 if r["SwitchSessionType"] == 2 else 1, int(r["SwitchSessionCounter"]) - 1] = \
                    np.nan if np.isinf(v) else v
        d = M.mean(axis=2)                     # MATLAB mean (not nanmean) over the three blocks
        return (np.nanmean(d, axis=0),) + signrank_pairs(d)

    for nm, field, key, pkey, nd in (("rt", "ReactionTimeFromTrialStart", "rt", "rt_p", (2, 1)),
                                     ("press", "PressRate", "press", "press_p", (1, 1)),
                                     ("reward", "RewardRate", "reward", "reward_p", (2, 1)),
                                     ("ratio", "HitToPressRate", "ratio", "ratio_p", (2, 2))):
        mean, p, n_pairs, n_zero, n_tied = per_mouse(field)
        exp = PUBLISHED[key]
        # means at the printed precision (fatal); p fatal only if on the other side of 0.05 from the published p
        # (exact p for n = 6 are multiples of 1/32; the published 0.68 is not on that grid)
        ok = (means_match(mean, exp, nd)
              and (p < 0.05) == (PUBLISHED[pkey] < 0.05))
        it["behav_" + nm] = dict(value=[float(mean[0]), float(mean[1]), p, n_pairs],
                                 expected=[exp[0], exp[1], PUBLISHED[pkey], 6], ok=ok,
                                 p_abs_difference=abs(p - PUBLISHED[pkey]), n_zero_differences=n_zero,
                                 n_tied_abs_differences=n_tied)
    # Figure 4D port against digitised reference
    tr4 = [mouse_trials(m) for m in mice]
    res["fig4_cells_per_mouse"] = [int(t["X"].shape[1]) for t in tr4]
    res["artefact_trials_per_mouse"] = [int(t["artefact"].sum()) for t in tr4]
    res["trials_per_mouse"] = [dict(self=int(np.sum(t["ttype"] == 1)), cued=int(np.sum(t["ttype"] == 2))) for t in tr4]
    curves = [fig4d_port(clean(t), s) for s, t in enumerate(tr4)]
    real = np.mean([c[0] for c in curves], axis=0)
    shuf = np.mean([c[1] for c in curves], axis=0)
    res["fig4d_port"] = dict(real=real.tolist(), shuffle=shuf.tolist())
    real_m = np.array([c[0] for c in curves])
    shuf_m = np.array([c[1] for c in curves])
    peak_k = PLOT_LO + int(np.argmax(real_m.mean(axis=0)[PLOT_LO:PLOT_HI]))   # plotted range of Fig. 4D (review v2 M1)
    n_above = int(np.sum(real_m[:, peak_k] > shuf_m[:, peak_k]))
    it["fig4d"] = dict(value=dict(peak_bin_1based=peak_k + 1, n_mice_above_at_peak=n_above),
                       expected="peak of the six-mouse mean real curve within the plotted range (MATLAB bins 60-90) in bins 73-81; real above the mouse's "
                                "50-shuffle mean at that bin in at least 5 of 6 mice (not digitised; DESIGN 0.1)",
                       ok=(72 <= peak_k <= 80) and n_above >= 5)
    fatal = [k for k, v in it.items() if not v["ok"] and v.get("fatal", True)]
    res["manifest_ok"] = all(v["size_ok"] and v["crc_ok"] for v in res["manifest"].values())
    res["status"] = "pass" if not fatal and res["manifest_ok"] else "fail"
    res["failed"] = fatal
    return res


def tests(a):
    gp = Path(a.out) / "gate.json"
    g = json.load(open(gp)) if gp.exists() else {}
    if g.get("status") != "pass":
        raise SystemExit("reproduction gate not passed; no test is run (DESIGN.md 3)")
    mice = loader.load_2p(str(Path(a.data_dir) / FILES["2p"]))
    nj = a.n_jobs
    R, D = 4, 1000
    out = dict(R=R, D=D, seed=dc.MASTER_SEED, mice=[], environment=dc.check_environment(),
               started=time.strftime("%Y-%m-%d %H:%M:%S %Z"))
    for s, m in enumerate(mice):
        tr = clean(mouse_trials(m))
        blocks, lab = block_layout(tr)
        X, y, tb = tr["X"], tr["ttype"], np.searchsorted(blocks, tr["block"])
        standard = lab.tolist() == LAYOUT
        rec = dict(mouse=s, n_cells=int(X.shape[1]), n_trials=dict(self=int(np.sum(y == 1)), cued=int(np.sum(y == 2))),
                   block_labels=lab.tolist(), trials_per_block=np.bincount(tb).tolist(), windows={},
                   standard_layout=standard)
        for wname, bins in dc.WINDOWS.items():
            t0 = time.time()
            bt = dc.block_test(X, tb, lab, bins, ("primary", s, wname), R=R, n_jobs=nj)
            ts = dc.trial_shuffle_test(X, y, bins, ("trial", s, wname), D=D, R=R, n_jobs=nj, observed=bt["observed"])
            rec["windows"][wname] = dict(block=bt, trial=ts, seconds=time.time() - t0)
        # positive control: movement decoder on PERI bins vs baseline bin, balanced subsample of trials
        sub = dc.balanced_subsample(y, dc.rng_for("move-sub", s))
        rec["movement"] = dc.movement_test(X[sub], dc.WINDOWS["PERI"], dc.BASELINE_BIN, ("move", s), D=100, R=2, n_jobs=nj)
        rec["movement_failed"] = bool(rec["movement"]["p"] > 0.05)     # flagged; the mouse stays in every group test
        # drift control: same condition, first vs last block of that condition (ITI window), trial shuffle
        rec["drift"] = {}
        for nm, cl in ((("cued_first_vs_last", 2), ("self_first_vs_last", 1)) if standard else ()):
            bl = [i for i, l in enumerate(lab) if l == cl]
            if len(bl) >= 2:
                k = np.isin(tb, [bl[0], bl[-1]])
                yy = np.where(tb[k] == bl[0], 1, 2)
                rec["drift"][nm] = dc.trial_shuffle_test(X[k], yy, dc.WINDOWS["ITI"], ("drift", s, nm), D=200, R=R, n_jobs=nj)
        # S1: held-out set cross-validation (train on two cued/self-paced pairs, test on the third), block test
        if standard:                                   # pair the k-th cued with the k-th self-paced block
            cued_b = [i for i, l in enumerate(lab) if l == 2]
            self_b = [i for i, l in enumerate(lab) if l == 1]
            pair_of = {b: k for k, (c, sp) in enumerate(zip(cued_b, self_b)) for b in (c, sp)}
            pair = np.array([pair_of[b] for b in tb])
            rec["S1_heldout_set"] = {w: dc.block_test(X, tb, lab, b, ("S1", s, w), R=R, n_jobs=nj, group_folds=pair)
                                     for w, b in dc.WINDOWS.items()}
        # S2: ITI window restricted to trials whose previous Hit was at least 5 s earlier
        hits = np.sort(m["event_ts"][np.asarray(m["event_id"]) == "Hit"])      # all Hit events (review S6)
        i_prev = np.searchsorted(hits, tr["ts"]) - 1
        prev = np.where(i_prev >= 0, hits[np.maximum(i_prev, 0)], -10**9)
        k = (tr["ts"] - prev) >= 5 * mp.FS
        rec["S2_n_trials"] = dict(self=int(np.sum(y[k] == 1)), cued=int(np.sum(y[k] == 2)))
        if min(rec["S2_n_trials"].values()) >= 20:
            bl_k = np.unique(tb[k])
            lab_k = np.array([lab[b] for b in bl_k])
            tbk = np.searchsorted(bl_k, tb[k])
            b2 = dc.block_test(X[k], tbk, lab_k, dc.WINDOWS["ITI"], ("S2", s), R=R, n_jobs=nj)
            t2 = dc.trial_shuffle_test(X[k], y[k], dc.WINDOWS["ITI"], ("S2t", s), D=200, R=R, n_jobs=nj, observed=b2["observed"])
            rec["S2_iti_clean"] = dict(block=b2, trial=t2)
        out["mice"].append(rec)
        json.dump(out, open(Path(a.out) / "tests.partial.json", "w"))
    # group level
    out["group"] = {}
    for wname in dc.WINDOWS:
        obs = [r["windows"][wname]["block"]["observed"] for r in out["mice"]]
        bnull = [r["windows"][wname]["block"]["null"] for r in out["mice"]]
        tnull = [r["windows"][wname]["trial"]["null"] for r in out["mice"]]
        out["group"][wname] = dict(
            block=dc.group_block_p(obs, bnull),
            block_top_count=dc.group_top_count([r["windows"][wname]["block"]["p"] for r in out["mice"]],
                                               [r["windows"][wname]["block"]["p_min"] for r in out["mice"]]),
            trial=dc.group_trial_p(obs, tnull, key=("group-trial", wname)))
        s1 = [r["S1_heldout_set"][wname] for r in out["mice"] if "S1_heldout_set" in r]
        if s1:
            out["group"]["S1_" + wname] = dc.group_block_p([x["observed"] for x in s1], [x["null"] for x in s1])
    drift_acc = [r["drift"][k]["observed"] for r in out["mice"] for k in r["drift"]]
    out["group"]["drift_accuracy"] = float(np.mean(drift_acc)) if drift_acc else None    # percent, DESIGN 0.3
    s2 = [r["S2_iti_clean"] for r in out["mice"] if "S2_iti_clean" in r]
    if s2:
        out["group"]["S2_ITI"] = dict(block=dc.group_block_p([x["block"]["observed"] for x in s2], [x["block"]["null"] for x in s2]),
                                      trial=dc.group_trial_p([x["block"]["observed"] for x in s2], [x["trial"]["null"] for x in s2],
                                                             key=("group-trial", "S2")), n_mice=len(s2))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=["inspect", "gate", "tests"])
    ap.add_argument("--data-dir", required=True)
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--n-jobs", type=int, default=6)
    a = ap.parse_args()
    Path(a.out).mkdir(parents=True, exist_ok=True)
    if a.stage == "inspect":
        inspect(a)
    elif a.stage == "gate":
        r = gate(a)
        json.dump(r, open(Path(a.out) / "gate.json", "w"), indent=1, default=float)
        (Path(a.out) / "gate-runs").mkdir(exist_ok=True)
        json.dump(r, open(Path(a.out) / "gate-runs" / ("gate-%s.json" % time.strftime("%Y%m%dT%H%M%S")), "w"),
                  indent=1, default=float)
        print("gate:", r["status"], r["failed"])
    else:
        r = tests(a)
        json.dump(r, open(Path(a.out) / "tests.json", "w"), default=float)
        print("tests written")


if __name__ == "__main__":
    main()
