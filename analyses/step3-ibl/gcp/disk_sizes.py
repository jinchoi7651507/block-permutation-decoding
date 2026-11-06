#!/usr/bin/env python3
"""Step 3 disk limit (code addendum 1 §3: "workers × the largest session's good-unit files must stay below 60 GB, so
the number of parallel workers is set from the metadata sizes before the run"). Metadata only: for every session of
ORDER.json, the ONE datasets table (file_size column; no file is downloaded) summed over the spike-sorting datasets
the runner can load (rel_path with 'spikes.', 'clusters.' or 'channels.'), over every collection and revision listed
for the session, so the sum is an upper bound of what one worker holds on disk for that session. Writes per-session
sizes in GB, the largest, and the worker limit: stamped form floor(60 / largest) and, stricter (review), floor(60 /
(largest + this worker's ONE cache tables + trials allowance)); the stricter one is used. A missing file_size, an empty
listing or a zero largest size stops the script.

  python disk_sizes.py --order ../runs/ORDER.json --out ../runs/DISK-SIZES.json
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
        keep = rel.str.contains(r"(?:^|/)(?:spikes|clusters|channels)\.", regex=True)
        n_missing = int(d.loc[keep, "file_size"].isna().sum())
        if n_missing:
            raise SystemExit(f"session {si}: {n_missing} spike-sorting dataset(s) without file_size, stop")
        gb = float(d.loc[keep, "file_size"].sum()) / 1e9
        rows.append({"session_index": si, "eid": s["eid"], "n_datasets": int(keep.sum()), "n_missing_size": n_missing,
                     "gb": round(gb, 4)})
    largest = max(rows, key=lambda r: r["gb"])
    if largest["gb"] <= 0:
        raise SystemExit("largest session size is 0, stop")
    import one as one_pkg
    cache = Path(one.cache_dir)
    overhead = sum(f.stat().st_size for f in cache.glob("*.pqt")) / 1e9   # this worker's ONE cache tables
    trials_gb = 0.01                                                     # trials tables (< 1 MB, rounded up)
    per_worker = largest["gb"] + overhead + trials_gb
    out = {"rule": "sum of file_size over spikes.*, clusters.*, channels.* datasets of the session (all collections and "
                   "revisions listed; upper bound)", "sessions": rows, "largest_gb": largest["gb"],
           "largest_session_index": largest["session_index"], "cache_tables_gb": round(overhead, 4),
           "trials_gb_allowance": trials_gb, "per_worker_gb": round(per_worker, 4),
           "worker_limit_stamped": math.floor((60 - 1e-9) / largest["gb"]),
           "worker_limit_with_overhead": math.floor((60 - 1e-9) / per_worker),
           "one_version": one_pkg.__version__, "written_utc": time.strftime("%Y-%m-%d %H:%M", time.gmtime())}
    Path(args.out).write_text(json.dumps(out, indent=1))
    print("largest", largest["gb"], "GB at session", largest["session_index"], "-> worker limit", out["worker_limit_stamped"],
          "(with cache overhead", out["worker_limit_with_overhead"], ")")


if __name__ == "__main__":
    main()
