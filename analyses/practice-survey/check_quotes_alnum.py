#!/usr/bin/env python3
"""Second pass of check_quotes.py (written 2026-11-02 after the first pass had been seen; post hoc). The first pass
flagged 33 of 140 quotes; the cases inspected were formatting differences (XML tags such as <xref> and <ext-link>
replaced by spaces, '[...]' separators, dashes). This pass compares letters and digits only (everything else
removed, lower case) and splits quotes at '...', the ellipsis character, ' | ' and '[...]'; every part of at least
15 characters must occur in the full text.

  python check_quotes_alnum.py
"""
import csv
import re
from pathlib import Path

import check_quotes as cq

HERE = Path(__file__).resolve().parent


def al(s):
    return re.sub(r"[^0-9a-z]", "", s)


def main():
    rows = list(csv.DictReader(open(HERE / "coding_final.csv", encoding="utf-8")))
    cache, bad = {}, []
    for r in rows:
        pm = r["pmcid"]
        if pm not in cache:
            cache[pm] = al(cq.xml_text(HERE / "fulltext" / f"{pm}.xml"))
        for c in "AB":
            ps = [al(cq.norm(x)) for x in re.split(r"\.\.\.|…| \| |\[\s*\.\.\.\s*\]|\[\s*…\s*\]", r["quote_" + c])]
            ps = [x for x in ps if len(x) >= 15]
            if not ps or any(x not in cache[pm] for x in ps):
                bad.append((pm, r["item"], c))
    msg = f"Second pass (letters and digits only, post hoc): {2 * len(rows) - len(bad)} of {2 * len(rows)} quotes found; not found: {bad or 'none'}."
    md = HERE / "quote_check.md"                         # replace an earlier second-pass line instead of appending again
    lines = [l for l in md.read_text(encoding="utf-8").splitlines() if not l.startswith("Second pass (letters and digits only")]
    md.write_text("\n".join(lines).rstrip("\n") + "\n\n" + msg + "\n", encoding="utf-8")
    print(msg)


if __name__ == "__main__":
    main()
