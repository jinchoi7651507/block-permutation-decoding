#!/usr/bin/env python3
"""Step 5 (DESIGN.md §2): download PAMAP2 from the UCI repository (CC BY 4.0), unpack (the archive may contain a
nested zip), copy Protocol/subject101.dat ... subject109.dat into <dir>/Protocol, and write MANIFEST.sha256 with the
SHA-256 of the downloaded archive and of the nine protocol files. UCI publishes no checksum; the manifest records
what was used.

  python fetch_pamap2.py --dir <data dir>
"""
import argparse
import hashlib
import shutil
import urllib.request
import zipfile
from pathlib import Path

URL = "https://archive.ics.uci.edu/static/public/231/pamap2+physical+activity+monitoring.zip"
NAMES = [f"subject{i}.dat" for i in range(101, 110)]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def unzip_all(z, dest):
    with zipfile.ZipFile(z) as zf:
        zf.extractall(dest)
    for inner in list(Path(dest).rglob("*.zip")):
        sub = inner.with_suffix("")
        if not sub.exists():
            unzip_all(inner, sub)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    d = Path(ap.parse_args().dir)
    d.mkdir(parents=True, exist_ok=True)
    arc = d / "pamap2_uci.zip"
    if not arc.exists():
        urllib.request.urlretrieve(URL, arc)
    work = d / "unpacked"
    if not work.exists():
        unzip_all(arc, work)
    (d / "Protocol").mkdir(exist_ok=True)
    lines = [f"{sha256(arc)}  pamap2_uci.zip"]
    for n in NAMES:
        hits = [p for p in work.rglob(n) if p.parent.name == "Protocol"]
        if len(hits) != 1:
            raise SystemExit(f"{n}: found {len(hits)} copies in Protocol folders; stop")
        shutil.copy2(hits[0], d / "Protocol" / n)
        lines.append(f"{sha256(d / 'Protocol' / n)}  Protocol/{n}")
    (d / "MANIFEST.sha256").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
