#!/usr/bin/env python3
"""Completion rule of RUN-PLATFORM.md, from run.log and replicate counts only (no p value is read or printed).

For every cell of CELLS.json (177), POWER_PILOT_CELLS.json (5) and POWER_CELLS.json (2): the number of distinct
replicate indices over the cell's worker files equals the planned number, and the last `done` line of the cell in
run.log has every return code 0 (earlier runs of a resumed cell are listed). Also lists files older than MACHINE.txt
(written by the set-up step) and lines that are not valid JSON.

  python code/check_completion.py runs_cloud
"""
import json
import re
import sys
from pathlib import Path

d = Path(sys.argv[1])
cells = json.loads((d / "CELLS.json").read_text())
cells += json.loads((d / "POWER_PILOT_CELLS.json").read_text())
cells += json.loads((d / "POWER_CELLS.json").read_text())
log = (d / "run.log").read_text().splitlines()
done = {}
for line in log:
    m = re.match(r"\S+ \S+ done\s+(\S+) rc \[([^\]]*)\]", line)
    if m:
        done.setdefault(m.group(1), []).append([int(x) for x in m.group(2).split(",") if x.strip()])
bad_cells, bad_json, resumed = [], 0, []
for c in cells:
    reps = set()
    for f in d.glob(f"{c['name']}.w*.jsonl"):
        for line in f.read_text().splitlines():
            try:
                reps.add(json.loads(line)["rep"])
            except (ValueError, KeyError):
                bad_json += 1
    runs = done.get(c["name"], [])
    ok_rc = bool(runs) and all(x == 0 for x in runs[-1])
    if len(runs) > 1:
        earlier = any(x != 0 for r in runs[:-1] for x in r)
        resumed.append(f"{c['name']} ({len(runs)} done lines; an earlier run had a nonzero rc: {earlier})")
    if len(reps) != c["reps"] or not ok_rc or reps != set(range(c["reps"])):
        bad_cells.append(f"{c['name']}: {len(reps)} of {c['reps']} replicates, last rc all 0: {ok_rc}")
t0 = (d / "MACHINE.txt").stat().st_mtime
older = sorted(f.name for f in d.iterdir() if f.stat().st_mtime < t0)
print(f"cells checked: {len(cells)} (simulation {len(cells) - 7}, power pilot 5, power 2)")
print(f"incomplete or nonzero rc: {len(bad_cells)}")
for b in bad_cells:
    print("  ", b)
print(f"unreadable lines: {bad_json}")
print(f"cells with more than one done line (resumed): {len(resumed)}")
for r in resumed:
    print("  ", r)
print(f"files older than MACHINE.txt: {len(older)} {older[:10]}")
print("COMPLETE" if not bad_cells and not bad_json else "NOT COMPLETE")
