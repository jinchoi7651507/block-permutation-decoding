"""Download the Yaron et al. 2025 files this panel reads and check them against MANIFEST.sha256.

Source: Zenodo 10.5281/zenodo.15531781 (CC-BY 4.0): the 18 session files res*.mat and tables.mat.
Each file is checked against the Zenodo md5, then its SHA-256 is written to MANIFEST.local.sha256;
compare it with the shipped MANIFEST.sha256. Files whose md5 already matches are not fetched again.

    python fetch_yaron.py            ->  raw/, MANIFEST.local.sha256
"""
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

RECORD = "15531781"
HERE = Path(__file__).resolve().parent
RAW = HERE / "raw"
WANT = re.compile(r"^(res\d+|tables)\.mat$")


def digest(path: Path, algo: str) -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    RAW.mkdir(exist_ok=True)
    with urllib.request.urlopen(f"https://zenodo.org/api/records/{RECORD}") as r:
        rec = json.load(r)
    files = sorted((f for f in rec["files"] if WANT.match(f["key"])), key=lambda f: f["key"])
    rows = []
    for f in files:
        dest = RAW / f["key"]
        md5 = f["checksum"].split(":", 1)[1]
        if not (dest.exists() and dest.stat().st_size == f["size"] and digest(dest, "md5") == md5):
            tmp = dest.with_suffix(dest.suffix + ".part")
            print(f"fetch {f['key']} ({f['size'] / 1e6:.1f} MB)", flush=True)
            urllib.request.urlretrieve(f["links"]["self"], tmp)
            if digest(tmp, "md5") != md5:
                sys.exit(f"md5 mismatch: {f['key']}")
            tmp.rename(dest)
        rows.append(f"{digest(dest, 'sha256')}  {f['key']}")
    out = HERE / "MANIFEST.local.sha256"
    out.write_text("\n".join(rows) + "\n")
    print(f"{len(rows)} files, {out.name} written; check: diff MANIFEST.sha256 {out.name}")


if __name__ == "__main__":
    main()
