#!/usr/bin/env python3
"""VERSION 2 (2026-10-27, author decision A after version 1 gave an upper bound about 11 times the pilot's measured
disk use): counts only what the runner downloads. load_good_units (brainwidemap 118fc36) calls
SpikeSortingLoader.load_spike_sorting(revision="2024-05-06", good_units=True) (ibllib 4.1.0, brainbox/io/one.py
l. 906-960), which downloads the objects passingSpikes (all attributes), clusters (attributes channels, depths,
metrics, uuids; SPIKES/CLUSTERS_ATTRIBUTES l. 45-46) and channels from the probe's spike-sorting collection. For each
(collection, dataset name) the largest file_size over the listed revisions is taken (conservative where the revision
choice is unclear). Version 1 (all spikes.*, clusters.*, channels.* over every revision) is kept as DISK-SIZES-v1.json.
Prints the two pilot sessions beside their measured freed_gb for the check.

Step 3 disk limit (code addendum 1 §3: "workers × the largest session's good-unit files must stay below 60 GB, so
the number of parallel workers is set from the metadata sizes before the run"). Metadata only: for every session of
ORDER.json, the ONE datasets table (file_size column; no file is downloaded) summed over the datasets the runner
downloads (version 2 rule above; optional ALF namespace prefixes included; both iblsorter and pykilosort counted
when both exist, an upper bound), so the sum bounds what one worker holds on disk for that session. Writes per-session
sizes in GB, the largest, and the worker limit: stamped form floor(60 / largest) and, stricter (review), floor(60 /
(largest + this worker's ONE cache tables + trials allowance)); the stricter one is used. A missing file_size, an empty
listing or a zero largest size stops the script.

  python disk_sizes_v2.py --order ../runs/ORDER.json --out ../runs/DISK-SIZES.json
"""
import argparse
import json
import math
import time
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from one.api import ONE
    one = ONE(base_url="https://openalyx.internationalbrainlab.org", password="international", silent=True)
    order = json.loads(Path(args.order).read_text())["sessions"]
    rows = []
    for si, s in enumerate(order):
        for attempt in range(4):
            try:
                d = one.list_datasets(s["eid"], details=True, query_type="remote")
                break
            except Exception:
                if attempt == 3:
                    raise
                time.sleep(30 * 2 ** attempt)
        if d is None or len(d) == 0 or "rel_path" not in d or "file_size" not in d:
            raise SystemExit(f"session {si}: empty dataset listing or missing columns, stop")
        rel = d["rel_path"].astype(str)
        name = rel.str.split("/").str[-1]
        coll = rel.str.replace(r"/#[^/]+#/", "/", regex=True).str.rsplit("/", n=1).str[0]
        insort = coll.str.contains(r"^alf/[^/]+/(?:iblsorter|pykilosort)$", regex=True)
        keep = insort & (name.str.match(r"^(?:_[^_]+_)?passingSpikes\.") | name.str.match(r"^(?:_[^_]+_)?clusters\.(?:channels|depths|metrics|uuids)\.")
                         | name.str.match(r"^(?:_[^_]+_)?channels\."))
        n_missing = int(d.loc[keep, "file_size"].isna().sum())
        if n_missing:
            raise SystemExit(f"session {si}: {n_missing} spike-sorting dataset(s) without file_size, stop")
        sub = d.loc[keep].assign(_coll=coll[keep], _name=name[keep])
        gb = float(sub.groupby(["_coll", "_name"])["file_size"].max().sum()) / 1e9
        probes_with_sorting = set(coll[insort].str.split("/").str[1])
        rows.append({"session_index": si, "eid": s["eid"], "n_datasets": int(keep.sum()), "n_missing_size": n_missing,
                     "gb": round(gb, 4), "n_probes_with_sorting_collection": len(probes_with_sorting),
                     "n_pids": len(s["pids"]),
                     "flag_fewer_sorting_collections_than_pids": len(probes_with_sorting) < len(s["pids"])})
    largest = max(rows, key=lambda r: r["gb"])
    if largest["gb"] <= 0:
        raise SystemExit("largest session size is 0, stop")
    import one as one_pkg
    cache = Path(one.cache_dir)
    overhead = sum(f.stat().st_size for f in cache.glob("*.pqt")) / 1e9   # this worker's ONE cache tables
    trials_gb = 0.05                                                     # trials tables and probe-level channel files (each < 1 MB; allowance)
    per_worker = largest["gb"] + overhead + trials_gb
    out = {"rule": "version 2: passingSpikes.*, clusters.{channels,depths,metrics,uuids}.*, channels.* in alf/<probe>/(iblsorter|pykilosort), "
                   "largest file_size per (collection, name) over revisions", "sessions": rows, "largest_gb": largest["gb"],
           "largest_session_index": largest["session_index"], "cache_tables_gb": round(overhead, 4),
           "trials_gb_allowance": trials_gb, "per_worker_gb": round(per_worker, 4),
           "worker_limit_stamped": math.floor((60 - 1e-9) / largest["gb"]),
           "worker_limit_with_overhead": math.floor((60 - 1e-9) / per_worker),
           "one_version": one_pkg.__version__, "written_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime())}
    Path(args.out).write_text(json.dumps(out, indent=1))
    for e, f in (("64e3fb86", 0.01), ("fece187f", 0.67)):
        r = [x for x in rows if x["eid"].startswith(e)]
        print("pilot check", e, "estimate", r[0]["gb"] if r else None, "GB; measured freed", f, "GB")
    print("largest", largest["gb"], "GB at session", largest["session_index"], "-> worker limit", out["worker_limit_stamped"],
          "(with cache overhead", out["worker_limit_with_overhead"], ")")


if __name__ == "__main__":
    main()
