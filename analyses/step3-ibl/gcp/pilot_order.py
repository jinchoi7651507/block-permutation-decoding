#!/usr/bin/env python3
"""Step 3 timing pilot, attempt 2 (RUNNOTE 2026-10-26; deviation stated there): build the pilot's order file.

The stamped runner forces the pilot to the first 2 sessions of the order it is given, and in ORDER.json both were
skipped by the stamped 250-kept-trial rule. This script walks ORDER.json in its order and keeps the first 2 sessions
that (a) have at least one region-session with >= 10 good units in BUDGET-META.json (unit counts only) and (b) pass the
runner's own trial gate: the same load_trials_and_mask call as run_session, kept trials >= 250 and run_ibl.check_trials
(trials tables only; no spike file, no label used beyond that gate). Writes PILOT-ORDER.json in the ORDER.json format
plus, per session examined, its position in ORDER.json and the reason it was passed over. The pilot's p values are
discarded by the runner; these sessions run again normally in the main run.

  python pilot_order.py --order ../runs/ORDER.json --meta ../runs/BUDGET-META.json --out ../runs/PILOT-ORDER.json
"""
import argparse
import json
import time
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--order", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=2)
    args = ap.parse_args()
    from one.api import ONE
    from brainwidemap.bwm_loading import load_trials_and_mask
    from run_ibl import check_trials, is_network_error
    one = ONE(base_url="https://openalyx.internationalbrainlab.org", password="international", silent=True)
    order = json.loads(Path(args.order).read_text())
    rs = {s["eid"]: s["region_sessions"] for s in json.loads(Path(args.meta).read_text())["sessions"]}
    keep, seen = [], []
    for pos, s in enumerate(order["sessions"]):
        if len(keep) == args.n:
            break
        if s["eid"] not in rs:
            seen.append({"position": pos, "eid": s["eid"], "passed_over": "beyond the 60 sessions of BUDGET-META"})
            break
        if rs[s["eid"]] == 0:
            seen.append({"position": pos, "eid": s["eid"], "passed_over": "no region-session with >= 10 good units"})
            continue
        for attempt in range(4):                          # network errors: retry with backoff (as the runner)
            try:
                trials, mask = load_trials_and_mask(one, s["eid"], min_rt=0.08, max_rt=2.0, exclude_nochoice=True,
                                                    exclude_unbiased=True, truncate_to_pass=True)
                break
            except Exception as ex:
                if attempt < 3 and is_network_error(ex):
                    time.sleep(60 * 2 ** attempt)
                    continue
                raise
        trials = trials.reset_index(drop=True)
        mask = mask.to_numpy()
        if mask.sum() < 250:
            seen.append({"position": pos, "eid": s["eid"], "passed_over": "fewer than 250 kept trials"})
            continue
        why = check_trials(trials, mask)
        if why:
            seen.append({"position": pos, "eid": s["eid"], "passed_over": why})
            continue
        seen.append({"position": pos, "eid": s["eid"], "passed_over": None})
        keep.append(s)
    out = {**{k: v for k, v in order.items() if k != "sessions"}, "pilot_note": "attempt 2: first sessions of ORDER.json "
           "passing the runner's trial gate with >= 1 region-session", "examined": seen, "sessions": keep}
    Path(args.out).write_text(json.dumps(out, indent=1))
    print(len(keep), "pilot sessions at positions", [x["position"] for x in seen if x["passed_over"] is None])
    if len(keep) < args.n:
        raise SystemExit(f"only {len(keep)} pilot sessions found")


if __name__ == "__main__":
    main()
