#!/usr/bin/env python3
"""Step 3 (IBL) runner, DESIGN.md v1 (stamped) with the code addendum. One session per call of `run_session`; one
JSON line per (region-session, label, row) in runs/rows.w<k>.jsonl; resumable by (eid, region, label).

  python run_ibl.py --order ../runs/ORDER.json --n-sessions N --out ../runs/rows.w<k>.jsonl --cache CACHE_k \
         --claims ../runs/claims            (one process per worker; sessions dispatched in order through claims)
  python run_ibl.py ... --out ../runs/pilot.w<k>.jsonl --pilot   (2 sessions, p values discarded; separate file)
  python run_ibl.py ... --requeue        (before a restart: release claims of sessions without a final row)

Per session (§2-§6): good units of every probe merged (load_good_units qc=1, revision 2024-05-06 fixed inside),
Beryl regions, region-sessions with >= 10 units; trials by load_trials_and_mask(min_rt 0.08, max_rt 2.0,
exclude_nochoice, exclude_unbiased, truncate_to_pass); sessions with < 250 kept trials skipped; counts in -600 to
-100 ms before stimulus onset (positive control: 0 to 100 ms). Pool of 220 pseudosessions per session
(generate_pseudo_session(trials, generate_choices=False) after numpy.random.seed([2026, 30, session_index, j])),
mask applied, p = 0.5 trials dropped. Spike files are deleted after counting (one session at a time).
"""
import argparse
import json
import os
import shutil
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

import ibl_core as C



def side_labels(pleft):
    """probabilityLeft 0.8 -> 1, 0.2 -> 0, 0.5 -> NaN."""
    out = np.full(len(pleft), np.nan)
    out[np.isclose(pleft, 0.8)] = 1
    out[np.isclose(pleft, 0.2)] = 0
    return out


def counts(spike_times, spike_clusters, n_clusters, t0, t1):
    """Spike counts (trials x clusters) in [t0, t1) per trial."""
    out = np.zeros((len(t0), n_clusters))
    order = np.argsort(spike_times, kind="stable")
    st, sc = spike_times[order], spike_clusters[order]
    for c in range(n_clusters):
        s = st[sc == c]
        out[:, c] = np.searchsorted(s, t1, side="left") - np.searchsorted(s, t0, side="left")
    return out


def pseudo_pool(trials, mask, session_index, n=220):
    """220 pseudosession side-label vectors and stimulus sides on the kept trials (NaN = dropped in that draw)."""
    from brainbox.task.closed_loop import generate_pseudo_session
    pool, stim = [], []
    for j in range(n):
        np.random.seed([2026, 30, session_index, j])
        ps = generate_pseudo_session(trials, generate_choices=False)
        lab = side_labels(ps["probabilityLeft"].to_numpy())[mask]
        pool.append(lab)
        right = ~np.isnan(ps["contrastRight"].to_numpy())
        con = np.where(right, ps["contrastRight"].to_numpy(), ps["contrastLeft"].to_numpy())
        s = np.where(con > 0, right.astype(float), np.nan)[mask]
        stim.append(s)
    return pool, stim


def region_rows(X, y_real, pool, stim_real, stim_pool, X_stim, si, ri, pilot):
    """All rows of one region-session (§6). Label vectors are full length over the session's kept trials with NaN
    for trials outside that vector's own set; every statistic is computed on its own trials (observed and each null).
    The label-independent null statistics (PS-refit S-main and S-block, SEL-repeat) are computed once per pool
    member (cache) and reused by every scored label vector (results unchanged)."""
    est = C.decoder(X.shape[1])
    fm = C.smain_folds(len(y_real), si)
    cache = {}

    def nulls(kind, ks):
        out = []
        for k in ks:
            if (kind, k) not in cache:
                cache[(kind, k)] = (C.null_sel_repeat(X, pool[k]) if kind == "sel"
                                    else C.null_refit(est, X, pool[k], kind, fm))
            out.append(cache[(kind, k)])
        return out

    def rs(li, rule):
        return np.random.RandomState([2026, 32, si, ri, li, rule])

    def main_rows(y, li, ks, block):
        """block: None (Q1 fake: S-block P2 and PS-refit), 'all' (Q2 real: every row under S-block too)."""
        r = {}
        ko = ~np.isnan(y)
        yo, Xo, folds = y[ko].astype(int), X[ko], C.subset_folds(fm, ko)
        _, pred = C.cv_score(est, Xo, yo, folds, "main")
        r["P1"] = C.p1_z(yo, pred)
        r["P2"] = C.p2(est, Xo, yo, folds, "main", rs(li, 2))[0]
        r["P4"] = C.p4(est, Xo, yo, folds, "main", rs(li, 4))[0]
        r["PS-refit"], r["PS-fixed"] = C.ps_rows(est, X, y, nulls("main", ks), [pool[k] for k in ks], "main", fm)
        fb = C.sblock_folds(yo)
        r["P2-block"] = C.p2(est, Xo, yo, fb, "pooled", rs(li, 12))[0]
        if block == "all":
            r["PS-refit-block"], r["PS-fixed-block"] = C.ps_rows(est, X, y, nulls("pooled", ks), [pool[k] for k in ks],
                                                               "pooled", fm)
            _, pb = C.cv_score(est, Xo, yo, fb, "pooled")
            r["P1-block"] = C.p1_z(yo, pb)
            r["P4-block"] = C.p4(est, Xo, yo, fb, "pooled", rs(li, 14))[0]
        else:
            r["PS-refit-block"], _ = C.ps_rows(est, X, y, nulls("pooled", ks), [pool[k] for k in ks], "pooled", fm,
                                               fixed=False)
        r["SEL-repeat"], r["SEL-fixed"] = C.sel_rows(X, y, nulls("sel", ks), [pool[k] for k in ks])
        return r

    out = []
    for j in range(20):                                   # Q1: fake draw j, nulls = first 200 members other than j
        ks = [k for k in range(len(pool)) if k != j][:200]
        r = main_rows(pool[j], j, ks, None)
        ko = ~np.isnan(pool[j])
        y, Xl, folds = pool[j][ko].astype(int), X[ko], C.subset_folds(fm, ko)
        yi = y[np.random.default_rng([2026, 33, si, j]).permutation(len(y))]     # i.i.d. control
        r["IID-SEL-repeat"], r["IID-SEL-fixed"] = C.sel_iid_rows(Xl, yi, C.calib_split(y),
                                                                  np.random.RandomState([2026, 34, si, ri, j]))
        _, pi = C.cv_score(est, Xl, yi, folds, "main")
        r["IID-P1"] = C.p1_z(yi, pi)
        r["IID-P2"] = C.p2(est, Xl, yi, folds, "main", rs(j, 22))[0]
        r["IID-P4"] = C.p4(est, Xl, yi, folds, "main", rs(j, 24))[0]
        out.append({"label": f"fake{j}", **r})
    out.append({"label": "real", **main_rows(y_real, 20, list(range(20, 220)), "all")})   # Q2
    # positive control: observed on real-mask trials with non-zero contrast in the real session; each null on the
    # real-mask trials with non-zero contrast in that pseudosession (§6), scored on its own stimulus sides
    est_s = C.decoder(X_stim.shape[1])
    null_s = [C.null_refit(est_s, X_stim, stim_pool[k], "main", fm) for k in range(20, 220)]
    pr, _ = C.ps_rows(est_s, X_stim, stim_real, null_s, None, "main", fm, fixed=False)
    out.append({"label": "stim", "PS-refit": pr})
    if pilot:
        for r in out:
            for k in list(r):
                if k != "label":
                    r[k] = None                                  # timing pilot: p values discarded unread
    return out


def check_trials(trials, mask):
    """§9 checks at run time (any failure -> session skipped with the reason)."""
    pl = trials["probabilityLeft"].to_numpy()
    if len(mask) != len(trials):
        return "trials and mask lengths differ"
    if np.isnan(pl).any():
        return "NaN probabilityLeft in the trials table"
    if not np.allclose(pl[:90], 0.5) or np.isclose(pl[90], 0.5) or np.any(np.isclose(pl[90:], 0.5)):
        return "first 90 trials not exactly the unbiased block"
    b = pl[90:]
    sides = b[np.r_[0, np.where(np.diff(b) != 0)[0] + 1]]
    if np.any(sides[1:] == sides[:-1]) or not set(np.round(np.unique(b), 2)) <= {0.2, 0.8}:
        return "biased blocks do not alternate strictly between 0.2 and 0.8"
    if not np.isfinite(trials["stimOn_times"].to_numpy()[mask]).all():
        return "NaN stimulus onset on a kept trial"
    return None


def run_session(one, row, si, args):
    from brainwidemap.bwm_loading import load_good_units, load_trials_and_mask
    from iblatlas.regions import BrainRegions
    t = time.time()
    eid, pids = row["eid"], row["pids"]
    trials, mask = load_trials_and_mask(one, eid, min_rt=0.08, max_rt=2.0, exclude_nochoice=True,
                                        exclude_unbiased=True, truncate_to_pass=True)
    trials = trials.reset_index(drop=True)
    mask = mask.to_numpy()
    base = {"eid": eid, "session_index": si, "subject": row["subject"], "n_kept": int(mask.sum())}
    if mask.sum() < 250:
        return [{**base, "skipped": "fewer than 250 kept trials"}]
    why = check_trials(trials, mask)
    if why:
        return [{**base, "skipped": why}]
    assert len(pids) <= 2, "more than 2 probes (the merge is checked for <= 2)"
    sp, cl = [], []
    for pid in pids:
        s, c = load_good_units(one, pid, qc=1)
        assert len(c) == 0 or s["clusters"].max() < len(c), "spike cluster index outside the clusters table"
        assert list(c.index) == list(range(len(c))), "clusters table not indexed 0..n-1"
        sp.append(s)
        cl.append(c)
    n_spk = sum(len(s["times"]) for s in sp)
    if len(sp) > 1:                                               # merge with cumulative offsets len(previous tables)
        off = np.cumsum([0] + [len(c) for c in cl[:-1]])
        spikes = {k: np.concatenate([s[k] + (o if k == "clusters" else 0) for s, o in zip(sp, off)]) for k in sp[0]}
        o = np.argsort(spikes["times"], kind="stable")
        spikes = {k: v[o] for k, v in spikes.items()}
        clusters = pd.concat(cl, ignore_index=True)
    else:
        spikes, clusters = sp[0], cl[0]
    assert len(spikes["times"]) == n_spk and spikes["clusters"].max() < len(clusters), "probe merge mismatch"
    assert np.array_equal(np.bincount(spikes["clusters"], minlength=len(clusters)),
                          np.concatenate([np.bincount(s["clusters"], minlength=len(c)) for s, c in zip(sp, cl)])), \
        "per-cluster spike counts changed by the merge"
    assert clusters["acronym"].notna().all(), "cluster without an acronym"
    beryl = BrainRegions().acronym2acronym(np.asarray(clusters["acronym"]), mapping="Beryl")
    on = trials["stimOn_times"].to_numpy()[mask]
    Xall = counts(spikes["times"], spikes["clusters"], len(clusters), on - 0.6, on - 0.1)
    Xstim = counts(spikes["times"], spikes["clusters"], len(clusters), on, on + 0.1)
    y_real = side_labels(trials["probabilityLeft"].to_numpy())[mask]
    right = ~np.isnan(trials["contrastRight"].to_numpy())
    con = np.where(right, trials["contrastRight"].to_numpy(), trials["contrastLeft"].to_numpy())
    stim_real = np.where(con > 0, right.astype(float), np.nan)[mask]
    pool, stim_pool = pseudo_pool(trials, mask, si)
    freed = delete_session(one, eid, args.cache)                  # spike files of this session deleted (§2)
    out = []
    for ri, reg in enumerate(sorted(set(beryl))):                 # region_index counts excluded regions too
        u = np.where(beryl == reg)[0]
        b = {**base, "region": str(reg), "n_units": int(len(u))}
        if reg in ("void", "root") or len(u) < 10:
            out.append({**b, "excluded": "void/root" if reg in ("void", "root") else "fewer than 10 units"})
            continue
        try:                                                      # one failing region does not lose the session
            for r in region_rows(Xall[:, u], y_real, pool, stim_real, stim_pool, Xstim[:, u], si, ri, args.pilot):
                out.append({**b, **r, "pilot": bool(args.pilot)})
        except Exception:
            out.append({**b, "region_error": traceback.format_exc()[-1500:], "pilot": bool(args.pilot)})
    du = shutil.disk_usage(args.cache)
    out.append({**base, "session_seconds": round(time.time() - t, 1), "pilot": bool(args.pilot),
                "disk_used_gb": round((du.total - du.free) / 1e9, 1), "freed_gb": round(freed / 1e9, 2), "loader_revisions": {"trials": "default MODIFIED_BEFORE",
                                                                                         "spikes": "2024-05-06"}})
    return out


def delete_session(one, eid, cache):
    """Delete this session's folder inside the worker's own cache; returns bytes freed (0 if nothing to delete)."""
    path = one.eid2path(eid)
    if path is None:
        return 0
    path, root = Path(path).resolve(), Path(cache).resolve()
    if root not in path.parents or not path.exists():
        return 0
    n = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    shutil.rmtree(path)
    return n


def dummy_load(stop_file):
    """Timing pilot (§3): keeps one vCPU busy with synthetic region-sessions (same code path) until stop_file exists,
    so that the 2 pilot sessions are timed with the planned number of workers running at once."""
    rng = np.random.default_rng(0)
    n = 400
    X = rng.poisson(3.0, (n, 30)).astype(float)
    y = np.repeat([0.0, 1.0, 0.0, 1.0], n // 4)
    pool = [np.roll(y, k) for k in range(220)]
    while not Path(stop_file).exists():
        region_rows(X, y, pool, y, pool, X, 0, 0, pilot=True)


def is_network_error(ex):
    """Retry only network failures: requests connection/timeout errors and HTTP 5xx (also when wrapped)."""
    import requests
    e = ex
    while e is not None:
        if isinstance(e, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
            return True
        r = getattr(e, "response", None)
        if isinstance(e, requests.exceptions.HTTPError) and r is not None and 500 <= r.status_code < 600:
            return True
        e = e.__cause__ or e.__context__
    return False


def claim(claims, si):
    """Shared in-order dispatch: a worker claims session si by creating claims/si atomically."""
    try:
        os.close(os.open(str(Path(claims) / f"{si:04d}"), os.O_CREAT | os.O_EXCL | os.O_WRONLY))
        return True
    except FileExistsError:
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", required=True)
    ap.add_argument("--n-sessions", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", required=True, help="per-worker ONE cache directory (never shared)")
    ap.add_argument("--claims", required=True, help="shared directory for in-order session dispatch")
    ap.add_argument("--pilot", action="store_true")
    ap.add_argument("--dummy-load", default=None, help="timing pilot only: run synthetic load until this file exists")
    ap.add_argument("--requeue", action="store_true",
                    help="before a restart (no worker running): release claims of sessions without a final row")
    args = ap.parse_args()
    if args.requeue:
        done = set()
        for f in Path(args.out).parent.glob("rows.w*.jsonl"):
            for r in map(json.loads, f.read_text().splitlines()):
                if not r.get("pilot") and any(k in r for k in ("session_seconds", "skipped", "error")):
                    done.add(r["session_index"])
        stale = [c for c in Path(args.claims).glob("*") if int(c.name) not in done]
        for c in stale:
            c.unlink()
        print("released", len(stale), "claims")
        return
    if args.dummy_load:
        dummy_load(args.dummy_load)
        return
    if args.pilot:
        if "pilot" not in Path(args.out).name or "pilot" not in Path(args.claims).name:
            raise SystemExit("pilot output and pilot claims must be separate, with 'pilot' in their names")
        args.n_sessions = 2
    elif "pilot" in Path(args.out).name or "pilot" in Path(args.claims).name:
        raise SystemExit("run output and claims must not be pilot paths")
    elif not args.requeue and Path(args.claims).exists() and any(Path(args.claims).iterdir()) \
            and not any(Path(args.out).parent.glob("rows.w*.jsonl")):
        raise SystemExit("claims directory not empty at the first start of the run")
    from one.api import ONE
    Path(args.cache).mkdir(parents=True, exist_ok=True)
    Path(args.claims).mkdir(parents=True, exist_ok=True)
    one = ONE(base_url="https://openalyx.internationalbrainlab.org", password="international", silent=True,
              cache_dir=args.cache)
    order = json.loads(Path(args.order).read_text())["sessions"]
    out = Path(args.out)
    for si, row in enumerate(order[: args.n_sessions]):
        if not claim(args.claims, si):
            continue
        rows = None
        for attempt in range(4):                                  # network errors: retry with backoff
            try:
                rows = run_session(one, row, si, args)
                break
            except Exception as ex:
                err = traceback.format_exc()
                if attempt < 3 and is_network_error(ex):
                    time.sleep(60 * 2 ** attempt)
                    continue
                rows = [{"eid": row["eid"], "session_index": si, "error": err[-2000:], "pilot": bool(args.pilot)}]
                break
            finally:
                try:                                              # every path: this session's files deleted
                    delete_session(one, row["eid"], args.cache)
                except Exception:
                    pass
        with out.open("a") as fh:
            for r in rows:
                fh.write(json.dumps(r) + "\n")


if __name__ == "__main__":
    main()
