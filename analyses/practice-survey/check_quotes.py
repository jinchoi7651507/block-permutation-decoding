#!/usr/bin/env python3
"""Check that every coder quote in coding_final.csv occurs in the full text of its study (fulltext/<pmcid>.xml).
Written 2026-11-02 (after an outside critique of the survey; descriptive check, fixed before it was run).

Text normalization, applied to both the XML text (tags removed, entities unescaped) and the quote: Unicode NFKC,
curly quotes and dashes to ASCII, whitespace collapsed, lower case. A quote with an ellipsis ("..." or "…") or a
" | " separator is split into parts, and each part of at least 20 characters must occur. A quote passes when all
its parts occur. Empty quotes are counted separately. Output: quote_check.csv (one line per quote) and a summary
printed and written to quote_check.md.

  python check_quotes.py
"""
import csv
import html
import re
import unicodedata
from pathlib import Path

HERE = Path(__file__).resolve().parent
MAP = {"‘": "'", "’": "'", "“": '"', "”": '"', "–": "-", "—": "-", "−": "-",
       " ": " ", " ": " ", " ": " "}


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    for k, v in MAP.items():
        s = s.replace(k, v)
    return re.sub(r"\s+", " ", s).strip().lower()


def xml_text(p):
    t = p.read_text(encoding="utf-8", errors="replace")
    t = re.sub(r"<[^>]+>", " ", t)
    return norm(html.unescape(t))


def parts(q):
    return [x.strip(" .;,\"'") for x in re.split(r"\.\.\.|…| \| ", q) if len(x.strip(" .;,\"'")) >= 20]


def main():
    rows = list(csv.DictReader(open(HERE / "coding_final.csv", encoding="utf-8")))
    cache, out = {}, []
    for r in rows:
        pm = r["pmcid"]
        if pm not in cache:
            cache[pm] = xml_text(HERE / "fulltext" / f"{pm}.xml")
        for coder in ("A", "B"):
            q = r[f"quote_{coder}"]
            if not q.strip():
                out.append((pm, r["item"], coder, "empty", ""))
                continue
            ps = [norm(x) for x in parts(q)]
            missing = [x for x in ps if x not in cache[pm]]
            status = "no part of 20+ characters" if not ps else ("found" if not missing else "not found")
            out.append((pm, r["item"], coder, status, " || ".join(missing)[:300]))
    with open(HERE / "quote_check.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pmcid", "item", "coder", "status", "missing_parts"])
        w.writerows(out)
    n = {s: sum(o[3] == s for o in out) for s in ("found", "not found", "empty", "no part of 20+ characters")}
    final_rows = [o for o in out if o[3] == "not found"]
    lines = ["# Quote check of coding_final.csv against the full texts", "",
             f"Quotes: {len(out)} (70 coded items x 2 coders). Found: {n['found']}. Not found: {n['not found']}. "
             f"Empty: {n['empty']}. No part of 20+ characters: {n['no part of 20+ characters']}.", ""]
    if final_rows:
        lines += ["| pmcid | item | coder | missing part |", "|---|---|---|---|"]
        lines += [f"| {o[0]} | {o[1]} | {o[2]} | {o[4][:150]} |" for o in final_rows]
    (HERE / "quote_check.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
