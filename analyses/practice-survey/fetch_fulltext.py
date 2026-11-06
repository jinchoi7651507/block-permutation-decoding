#!/usr/bin/env python3
"""Download the full-text XML of the 14 included studies from Europe PMC into fulltext/ (not redistributed) and
compare them with fulltext-MANIFEST.sha256, the hashes of the copies used for the quote check (2026-11-02/03).
Europe PMC can update a record, so a mismatch is reported, not fatal.

  python fetch_fulltext.py
"""
import csv
import hashlib
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/{}/fullTextXML"


def main():
    ids = sorted({r["pmcid"] for r in csv.DictReader(open(HERE / "coding_final.csv", encoding="utf-8"))})
    ref = dict(l.split()[::-1] for l in (HERE / "fulltext-MANIFEST.sha256").read_text().splitlines() if l.strip())
    (HERE / "fulltext").mkdir(exist_ok=True)
    for pm in ids:
        p = HERE / "fulltext" / f"{pm}.xml"
        if not p.exists():
            urllib.request.urlretrieve(URL.format(pm), p)
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        print(f"{pm}: {'same as the copy used' if ref.get(f'fulltext/{pm}.xml') == h else 'differs from the copy used (record updated?)'}")


if __name__ == "__main__":
    main()
