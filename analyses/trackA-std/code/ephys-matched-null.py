#!/usr/bin/env python3
"""Does the matched-null correction transfer outside our own simulator?

Pre-registered in paper-experiment/prereg-electrophysiology.md, written before
any analysis. Read that first: it fixes the decision rule and the exclusions.

The manuscript's methodological claim is that a SEARCHED read-out score must be
compared with a null that repeats the identical search, and that a constant
decoder overstates the effect. This script asks whether that holds in public
electrophysiology (Allen Visual Coding Neuropixels), where nothing about our
simulator is involved.

Isomorphism with the connectome test:
  candidate pool   all recorded units in one (session, visual area)
  two classes      drifting-grating direction, 0 deg against 90 deg
  calibration      the first half of trials in time order
  held-out         the second half
  free read-out    best class separation (d-prime) on calibration, scored held-out
  constant decoder always answer the held-out majority class
  matched null     the SAME two-step procedure over randomly chosen units,
                   from a pool of the same size, repeated for a distribution

The null repeats the selection step. Picking the best random unit using held-out
data would be an oracle, and the median over already-informed candidates is not a
null at all; both mistakes were made in the connectome analysis first.

  python3 experiments/ephys-matched-null.py --sessions 715093703,719161530 --seed 1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np

# --- pre-registered constants -------------------------------------------------
ORIENTATIONS = (0.0, 90.0)     # the two classes
MIN_RATE_HZ = 0.5              # unit exclusion
MIN_UNITS_PER_AREA = 20        # area exclusion
NULL_DRAWS = 200               # random draws for the matched null
RESPONSE_WINDOW = (0.0, 2.0)   # seconds after stimulus onset


def load_session(path: Path):
    """Spike times per unit, unit areas, and the drifting-gratings table."""
    with h5py.File(path, "r") as f:
        units = f["units"]
        ids = np.asarray(units["id"])
        idx = np.asarray(units["spike_times_index"])
        times = np.asarray(units["spike_times"])
        starts = np.concatenate([[0], idx[:-1]])
        spikes = [times[s:e] for s, e in zip(starts, idx)]

        def decode(arr):
            return np.array([x.decode() if isinstance(x, bytes) else str(x) for x in np.asarray(arr)])

        # The area may sit on the units table directly, or only on the electrodes
        # table, in which case units are joined to it through the peak channel.
        area = None
        for key in ("ecephys_structure_acronym", "location", "structure_acronym"):
            if key in units:
                area = decode(units[key])
                break
        if area is None:
            elec = None
            for elec_path in ("general/extracellular_ephys/electrodes",
                              "general/extracellular_ephys/electrode_group/electrodes"):
                if elec_path in f:
                    elec = f[elec_path]
                    break
            chan_key = next((k for k in ("peak_channel_id", "electrode_id", "electrodes")
                             if k in units), None)
            if elec is None or chan_key is None:
                raise SystemExit(f"cannot resolve unit areas; units columns: {list(units.keys())}")
            loc_key = next((k for k in ("location", "ecephys_structure_acronym", "structure_acronym")
                            if k in elec), None)
            if loc_key is None:
                raise SystemExit(f"electrodes table has no location; columns: {list(elec.keys())}")
            eid = np.asarray(elec["id"])
            eloc = decode(elec[loc_key])
            lookup = {int(i): a for i, a in zip(eid, eloc)}
            area = np.array([lookup.get(int(c), "unknown") for c in np.asarray(units[chan_key])])

        intervals = f["intervals"]
        name = "drifting_gratings_presentations" if "drifting_gratings_presentations" in intervals else None  # Track A standard-table rerun (2026-10-18): the first match was the contrast table in 8 sessions
        if name is None:
            raise SystemExit("no drifting_gratings interval table")
        tbl = intervals[name]
        onset = np.asarray(tbl["start_time"])
        ori_raw = np.asarray(tbl["orientation"])
        ori = np.array([x.decode() if isinstance(x, bytes) else x for x in ori_raw], dtype=object)

    def as_float(v):
        try:
            return float(v)
        except (TypeError, ValueError):
            return np.nan

    ori = np.array([as_float(v) for v in ori])
    return ids, spikes, area, onset, ori


def trial_counts(spikes_u: np.ndarray, onsets: np.ndarray) -> np.ndarray:
    """Spikes per trial in the response window, for one unit."""
    lo = np.searchsorted(spikes_u, onsets + RESPONSE_WINDOW[0])
    hi = np.searchsorted(spikes_u, onsets + RESPONSE_WINDOW[1])
    return (hi - lo).astype(float)


def dprime(a: np.ndarray, b: np.ndarray) -> float:
    """Class separation for one unit. Sign carries which class it prefers."""
    va, vb = a.var(ddof=1), b.var(ddof=1)
    pooled = np.sqrt(0.5 * (va + vb))
    if pooled == 0:
        return 0.0
    return float((a.mean() - b.mean()) / pooled)


def zscore(counts: np.ndarray, cal: np.ndarray) -> np.ndarray:
    """Per unit, standardised by its own calibration mean and s.d., so units can
    be pooled into a population read-out without the loudest one dominating."""
    mu = counts[:, cal].mean(axis=1, keepdims=True)
    sd = counts[:, cal].std(axis=1, keepdims=True)
    sd[sd == 0] = 1.0
    return (counts - mu) / sd


def division_score(z: np.ndarray, order: np.ndarray, k: int, labels: np.ndarray,
                   cal: np.ndarray, test: np.ndarray) -> float:
    """A division puts the first k ranked units in one pool and the rest in the
    other, and answers with whichever pool is more active on that trial. Which
    pool means which class is fixed on calibration; accuracy is read held-out.
    This mirrors the connectome test, where a division splits the read-out
    population into two clusters and the louder cluster wins."""
    a, b = order[:k], order[k:]
    if len(a) == 0 or len(b) == 0:
        return np.nan
    diff = z[a].mean(axis=0) - z[b].mean(axis=0)
    hi_is_class0 = diff[cal][labels[cal] == 0].mean() > diff[cal][labels[cal] == 1].mean()
    pred = (diff[test] > 0) if hi_is_class0 else (diff[test] <= 0)
    return float((pred.astype(int) == (labels[test] == 0).astype(int)).mean() * 100)


def best_division(z: np.ndarray, order: np.ndarray, labels: np.ndarray,
                  cal: np.ndarray, test: np.ndarray, min_pool: int):
    """Select the split point on CALIBRATION only, then score it held-out."""
    n = len(order)
    best_k, best_cal = min_pool, -np.inf
    for k in range(min_pool, n - min_pool + 1):
        sc = division_score(z, order, k, labels, cal, cal)
        if np.isfinite(sc) and sc > best_cal:
            best_cal, best_k = sc, k
    return division_score(z, order, best_k, labels, cal, test), best_k


def analyse_area(counts: np.ndarray, labels: np.ndarray, cal: np.ndarray,
                 test: np.ndarray, rng: np.random.Generator, min_pool: int = 2):
    """Isomorphic to experiments/readout-agnostic.ts.

    free   units ranked by calibration d-prime, every split of that ranking
           scored on calibration, winner evaluated held-out.
    null   the SAME sweep and the SAME selection over a RANDOM ranking, so the
           candidate pool and the cluster sizes match and only the information
           in the ranking is removed. Random pools still contain genuinely
           responsive units, exactly as random divisions do in the connectome,
           which is what makes this a matched null rather than a no-signal one.
    """
    z = zscore(counts, cal)
    n_units = counts.shape[0]

    seps = np.array([dprime(counts[u][cal][labels[cal] == 0],
                            counts[u][cal][labels[cal] == 1]) for u in range(n_units)])
    order = np.argsort(-seps)                       # most class-0 preferring first
    free, free_k = best_division(z, order, labels, cal, test, min_pool)

    maj = max((labels[test] == 0).mean(), (labels[test] == 1).mean()) * 100

    nulls = []
    for _ in range(NULL_DRAWS):
        rand_order = rng.permutation(n_units)       # same pool, ranking uninformed
        sc, _ = best_division(z, rand_order, labels, cal, test, min_pool)
        nulls.append(sc)
    nulls = np.array(nulls, dtype=float)
    return free, maj, float(np.nanmean(nulls)), nulls, free_k


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sessions", default="715093703,719161530")
    ap.add_argument("--dir", default="/tmp/allen")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--dump-draws", default=None,
                    help="optional JSON path for each unit's null draws; does not change the printed output")
    ap.add_argument("--good-only", action="store_true",
                    help="optional: keep only units whose NWB units/quality is 'good' (applied before the rate "
                         "filter); without it every sorted unit is kept, as planned")
    ap.add_argument("--sdk-qc", action="store_true",
                    help="optional: keep only units passing the AllenSDK default unit filter (quality 'good', "
                         "isi_violations < 0.5, amplitude_cutoff < 0.1, presence_ratio > 0.9), applied before the "
                         "rate filter; without it every sorted unit is kept, as planned")
    ap.add_argument("--conventional-draws", default=None,
                    help="optional JSON path: per unit, held-out accuracy of size-matched random divisions "
                         "without the cut search (separate random stream; does not change the printed output)")
    args = ap.parse_args()
    rng = np.random.default_rng(args.seed)

    print(f"Pre-registered: paper-experiment/prereg-electrophysiology.md. seed {args.seed}, "
          f"{NULL_DRAWS} null draws, window {RESPONSE_WINDOW[0]}-{RESPONSE_WINDOW[1]} s, "
          f"orientations {ORIENTATIONS[0]:.0f} vs {ORIENTATIONS[1]:.0f} deg.")
    print(f"Exclusions: unit < {MIN_RATE_HZ} Hz, area < {MIN_UNITS_PER_AREA} units.\n")
    print(f"{'session':>11} {'area':>7} {'units':>6} {'trials':>7} "
          f"{'free':>6} {'const':>6} {'null':>6} {'gap_const':>10} {'gap_null':>9}")

    rows = []
    draws = []
    conventional = []
    crng = np.random.default_rng([args.seed, 7])   # separate stream, so the main draws are untouched
    for sid in args.sessions.split(","):
        path = Path(args.dir) / f"session_{sid}.nwb"
        if not path.exists():
            print(f"  {sid}: file missing, skipped", file=sys.stderr)
            continue
        ids, spikes, area, onset, ori = load_session(path)
        if args.good_only:
            with h5py.File(path, "r") as f:
                q = np.array([x.decode() if isinstance(x, bytes) else str(x) for x in f["units"]["quality"][:]])
            area = np.where(q == "good", area, "excluded-quality")
        if args.sdk_qc:
            with h5py.File(path, "r") as f:
                u = f["units"]
                q = np.array([x.decode() if isinstance(x, bytes) else str(x) for x in u["quality"][:]])
                ok = ((q == "good") & (np.asarray(u["isi_violations"]) < 0.5)
                      & (np.asarray(u["amplitude_cutoff"]) < 0.1) & (np.asarray(u["presence_ratio"]) > 0.9))
            area = np.where(ok, area, "excluded-quality")

        keep = np.isin(ori, ORIENTATIONS)
        if keep.sum() == 0 or len(np.unique(ori[keep])) < 2:
            print(f"  {sid}: both orientations not present, session excluded", file=sys.stderr)
            continue
        onsets, labels = onset[keep], (ori[keep] == ORIENTATIONS[1]).astype(int)
        order = np.argsort(onsets)
        onsets, labels = onsets[order], labels[order]
        half = len(onsets) // 2
        cal = np.arange(half)
        test = np.arange(half, len(onsets))

        for a in sorted(set(area)):
            if not a.startswith("VIS"):
                continue
            sel = np.where(area == a)[0]
            counts = np.array([trial_counts(spikes[u], onsets) for u in sel])
            if counts.size == 0:
                continue
            rate = counts.mean(axis=1) / (RESPONSE_WINDOW[1] - RESPONSE_WINDOW[0])
            counts = counts[rate >= MIN_RATE_HZ]
            if counts.shape[0] < MIN_UNITS_PER_AREA:
                continue
            free, const, null, null_draws, _k = analyse_area(counts, labels, cal, test, rng)
            draws.append({"session": sid, "area": a, "free": free, "const": const,
                          "null_draws": [float(x) for x in null_draws]})
            if args.conventional_draws:
                z = zscore(counts, cal)
                conv = [division_score(z, crng.permutation(counts.shape[0]), _k, labels, cal, test)
                        for _ in range(NULL_DRAWS)]
                conventional.append({"session": sid, "area": a, "free": free, "const": const, "k": int(_k),
                                     "n_units": int(counts.shape[0]), "conventional_draws": [float(x) for x in conv]})
            rows.append((sid, a, counts.shape[0], len(onsets), free, const, null))
            print(f"{sid:>11} {a:>7} {counts.shape[0]:>6} {len(onsets):>7} "
                  f"{free:>6.1f} {const:>6.1f} {null:>6.1f} "
                  f"{free - const:>+10.1f} {free - null:>+9.1f}")

    if args.dump_draws:
        import json
        Path(args.dump_draws).write_text(json.dumps(draws, indent=1))
    if args.conventional_draws:
        import json
        Path(args.conventional_draws).write_text(json.dumps(conventional, indent=1))

    if not rows:
        print("\nNo (session, area) unit survived the pre-registered exclusions.")
        return
    gc = np.array([r[4] - r[5] for r in rows])
    gn = np.array([r[4] - r[6] for r in rows])
    smaller = int((gn < gc).sum())
    print(f"\n{len(rows)} (session, area) units analysed.")
    print(f"  mean gap against the constant decoder {gc.mean():+.1f}")
    print(f"  mean gap against the matched null     {gn.mean():+.1f}")
    print(f"  matched null gives the smaller gap in {smaller}/{len(rows)} units.")

    # How much the constant decoder overstates it, per unit. The pre-registered
    # rule says "clearly smaller"; this puts a number on "clearly". It is the
    # same comparison, summarised, not an additional analysis, and it cannot
    # change the branch the rule selected.
    d = gc - gn
    boot = np.array([rng.choice(d, size=len(d), replace=True).mean() for _ in range(4000)])
    lo, hi = np.percentile(boot, [2.5, 97.5])
    print(f"  overstatement per unit: mean {d.mean():+.1f}, median {np.median(d):+.1f}, "
          f"range {d.min():+.1f} to {d.max():+.1f}")
    print(f"  95% bootstrap interval on the mean overstatement [{lo:+.1f}, {hi:+.1f}] "
          f"(4,000 percentile resamples); above zero in {(d > 0).sum()}/{len(d)} units.")
    print("\nDecision rule (fixed in advance): adopt only if two or more units show a")
    print("clearly smaller gap against the matched null AND the direction is consistent")
    print("in every unit analysed; otherwise omit entirely, with no qualitative mention.")


if __name__ == "__main__":
    main()
