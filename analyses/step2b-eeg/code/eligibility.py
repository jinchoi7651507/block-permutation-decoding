#!/usr/bin/env python3
"""Step 2b eligibility and subject draw (DESIGN.md v1 §2), written before running (2026-10-21 12:17 KST; design v2).

Downloads only the small BrainVision header/marker files (.vhdr, .vmrk) of every raw subject and the public META
table; no EEG signal. Markers (EEG_Info on the server): S200 = eyes open, S210 = eyes closed.
Eligible = (i) .vhdr, .vmrk and .eeg listed; (ii) the condition markers form 16 segments that alternate EC/EO,
each 50-80 s long (segment = from one condition marker to the next; the last segment to the last marker of the
recording or, if none, 60 s assumed and flagged); (iii) sampling interval read from .vhdr.
Draw: 40 subjects from the eligible IDs with numpy default_rng(20261021), stratified by the META age bin into
young (age bin starting at 20-35) and old (55+) in proportion to the eligible counts (rounded, remainder to young);
the full seeded order of each stratum is saved so that replacements follow it. Output: lemon_eligibility.json,
SUBJECTS.txt (to be OTS-stamped before any .eeg download).
"""
import json
import re
import urllib.request
from pathlib import Path

import numpy as np

BASE = "https://ftp.gwdg.de/pub/misc/MPI-Leipzig_Mind-Brain-Body-LEMON"
RAW = BASE + "/EEG_MPILMBB_LEMON/EEG_Raw_BIDS_ID/"
META = BASE + "/Behavioural_Data_MPILMBB_LEMON/META_File_IDs_Age_Gender_Education_Drug_Smoke_SKID_LEMON.csv"
OUT = Path(__file__).resolve().parent.parent / "eligibility"
CACHE = OUT / "markers"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read().decode("latin-1")


def links(url):
    return re.findall(r'href="([^"?]+)"', get(url))


def parse(sub, vhdr, vmrk):
    si = re.search(r"SamplingInterval=(\d+(?:\.\d+)?)", vhdr)
    fs = 1e6 / float(si.group(1)) if si else None
    mk = []
    for line in vmrk.splitlines():
        m = re.match(r"Mk\d+=([^,]*),([^,]*),(\d+),", line)
        if m:
            mk.append((m.group(1).strip(), m.group(2).strip().replace(" ", ""), int(m.group(3))))
    cond = [(d, p) for t, d, p in mk if d in ("S200", "S210")]
    out = {"sub": sub, "fs": fs, "n_markers": len(mk), "n_condition_markers": len(cond),
           "other_markers": sorted({d for t, d, p in mk if d not in ("S200", "S210")})}
    # collapse repeated identical consecutive markers into segment starts
    seg = []
    for d, p in cond:
        if not seg or seg[-1][0] != d:
            seg.append((d, p))
    out["n_segments"] = len(seg)
    out["first"] = "EO" if seg and seg[0][0] == "S200" else ("EC" if seg else None)
    if fs and len(seg) >= 2:
        durs = [(seg[i + 1][1] - seg[i][1]) / fs for i in range(len(seg) - 1)]
        out["durations_s"] = [round(x, 2) for x in durs]
    else:
        out["durations_s"] = []
    alt = all(seg[i][0] != seg[i + 1][0] for i in range(len(seg) - 1))
    ok_d = len(out["durations_s"]) == 15 and all(50 <= x <= 80 for x in out["durations_s"])
    out["eligible_markers"] = bool(len(seg) == 16 and alt and ok_d)
    out["last_segment_assumed_60s"] = True
    return out


def main():
    OUT.mkdir(exist_ok=True); CACHE.mkdir(exist_ok=True)
    subs = sorted(l.strip("/") for l in links(RAW) if l.startswith("sub-"))
    rows = []
    for s in subs:
        files = links(RAW + s + "/RSEEG/")
        have = {ext: any(f.endswith(ext) for f in files) for ext in (".vhdr", ".vmrk", ".eeg")}
        r = {"sub": s, **{"has" + k: v for k, v in have.items()}}
        if have[".vhdr"] and have[".vmrk"]:
            vh, vm = CACHE / f"{s}.vhdr", CACHE / f"{s}.vmrk"
            if not vh.exists():
                vh.write_text(get(f"{RAW}{s}/RSEEG/{s}.vhdr"), encoding="latin-1")
            if not vm.exists():
                vm.write_text(get(f"{RAW}{s}/RSEEG/{s}.vmrk"), encoding="latin-1")
            r.update(parse(s, vh.read_text(encoding="latin-1"), vm.read_text(encoding="latin-1")))
        r["eligible"] = bool(all(have.values()) and r.get("eligible_markers"))
        rows.append(r)
        print(s, r["eligible"], r.get("n_segments"), flush=True)
    meta_txt = get(META)
    (OUT / "META.csv").write_text(meta_txt)
    lines = [l.split(",") for l in meta_txt.splitlines() if l.strip()]
    head = [h.strip().strip('"') for h in lines[0]]
    ai = next(i for i, h in enumerate(head) if "Age" in h)
    age = {l[0].strip().strip('"'): l[ai].strip().strip('"') for l in lines[1:]}
    for r in rows:
        a = age.get(r["sub"])
        r["age_bin"] = a
        r["stratum"] = None if a is None else ("old" if a[:2].isdigit() and int(a[:2]) >= 55 else "young")
    elig = [r for r in rows if r["eligible"] and r["stratum"]]
    rng = np.random.default_rng(20261021)
    order = {}
    for st in ("young", "old"):
        ids = sorted(r["sub"] for r in elig if r["stratum"] == st)
        order[st] = [ids[i] for i in rng.permutation(len(ids))]
    n_old = int(round(40 * len(order["old"]) / max(1, len(elig))))
    if len(order["old"]) < n_old or len(order["young"]) < 40 - n_old:
        raise SystemExit(f"too few eligible subjects: young {len(order['young'])}, old {len(order['old'])}; need {40 - n_old}, {n_old}")
    chosen = order["young"][:40 - n_old] + order["old"][:n_old]
    res = {"n_subjects": len(rows), "n_eligible": len(elig), "n_young": len(order["young"]), "n_old": len(order["old"]),
           "draw": {"seed": 20261021, "n_young": 40 - n_old, "n_old": n_old, "chosen": chosen, "seeded_order": order},
           "first_condition_counts": {k: sum(1 for r in rows if r["sub"] in chosen and r.get("first") == k) for k in ("EC", "EO")},
           "rows": rows}
    (OUT / "lemon_eligibility.json").write_text(json.dumps(res, indent=1))
    (OUT / "SUBJECTS.txt").write_text("\n".join(chosen) + "\n")
    print(json.dumps({k: v for k, v in res.items() if k not in ("rows", "draw")}, indent=1), res["draw"]["n_young"], res["draw"]["n_old"])


if __name__ == "__main__":
    main()
