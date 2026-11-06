#!/usr/bin/env python3
"""Download the 32 Allen Visual Coding Neuropixels brain_observatory_1.1 session NWB files
(about 80 GB: 74.5 GB for the 30 new sessions plus about 6 GB for the 2 original ones).
Run with --only original first (gate 0 in README), then without --only.

DO NOT RUN before PREREG-trackA.md is final, committed and OpenTimestamps-attested (README step 1).

  python3 download_sessions.py --dir <target folder> [--only new|original|all]

Resumes partial files (HTTP Range), checks each file's size against the server, and writes
MANIFEST.sha256 in the target folder when every file is complete. Single process.
"""
import argparse
import csv
import hashlib
import sys
import urllib.request
from pathlib import Path

BASE = "https://allen-brain-observatory.s3.us-west-2.amazonaws.com/visual-coding-neuropixels/ecephys-cache"
PKG = Path(__file__).resolve().parent.parent


def remote_size(url):
    req = urllib.request.Request(url, method="HEAD")
    with urllib.request.urlopen(req, timeout=60) as r:
        return int(r.headers["Content-Length"])


def fetch(url, dest, size):
    have = dest.stat().st_size if dest.exists() else 0
    if have == size:
        return "complete"
    if have > size:
        dest.unlink()
        have = 0
    req = urllib.request.Request(url, headers={"Range": f"bytes={have}-"} if have else {})
    with urllib.request.urlopen(req, timeout=120) as r:
        if have and r.status != 206:                 # server ignored the Range request: start over
            dest.unlink()
            return fetch(url, dest, size)
        fh = dest.open("ab")
        done = have
        while True:
            chunk = r.read(8 << 20)
            if not chunk:
                break
            fh.write(chunk)
            done += len(chunk)
            print(f"\r  {dest.name}: {done / 1e9:6.2f} / {size / 1e9:.2f} GB", end="", flush=True)
        fh.close()
    print()
    return "complete" if dest.stat().st_size == size else "INCOMPLETE"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--only", choices=("all", "new", "original"), default="all")
    args = ap.parse_args()
    target = Path(args.dir)
    target.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((PKG / "sessions_trackA.csv").open()))
    rows = [r for r in rows if args.only == "all" or r["set"] == args.only]
    status = {}
    for r in rows:
        sid = r["session_id"]
        url = f"{BASE}/session_{sid}/session_{sid}.nwb"
        dest = target / f"session_{sid}.nwb"
        for attempt in range(5):
            try:
                status[sid] = fetch(url, dest, remote_size(url))
                break
            except Exception as e:  # network errors: retry with resume
                print(f"\n  {sid}: attempt {attempt + 1} failed: {e}", file=sys.stderr)
                status[sid] = f"FAILED: {e}"
        print(f"{sid}: {status[sid]}", flush=True)
    bad = {k: v for k, v in status.items() if v != "complete"}
    if bad:
        print("NOT complete; rerun the same command to resume:", bad)
        sys.exit(1)
    with (target / "MANIFEST.sha256").open("w") as fh:
        for r in rows:
            p = target / f"session_{r['session_id']}.nwb"
            h = hashlib.sha256()
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(16 << 20), b""):
                    h.update(chunk)
            fh.write(f"{h.hexdigest()}  {p.name}\n")
    print("all complete; MANIFEST.sha256 written")


if __name__ == "__main__":
    main()
