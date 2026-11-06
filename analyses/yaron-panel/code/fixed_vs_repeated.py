"""Fixed vs repeated unit selection inside the block permutation, rat auditory cortex (Extended Data Fig. 3 of the paper).

Data: Yaron et al. 2025 (PLoS Biol 23: e3003242), Zenodo 10.5281/zenodo.15531781 (../data/fetch_yaron.py).
Pipeline: the authors' selection on odd trials and held-out scoring on even trials (yaron_pipeline.py).

Null: one uniform permutation of the eight condition blocks per session, the same for odd and even trials
(seeds default_rng([11, 1, session, draw]), draws 0..999). For every draw the same permuted data are scored two ways:
  repeated  selection rerun on the permuted odd trials, then scored on the permuted even trials;
  fixed     the units selected on the real data kept, with their signs, and scored on the permuted even trials.
p = (1 + #{null >= observed}) / (R + 1). Gate: the observed score, the number of selected units and both null
means must equal the earlier run of this analysis with the same draws (2026-10-06, four decimals).

POST HOC: this comparison was first run on 2026-10-06, after the block-permutation tests of these data had been
run; this script reruns it with the same draws.

    python fixed_vs_repeated.py --raw <raw folder> --cache <file.npz> --worker k --of n --parts <dir>   (one process each)
    python fixed_vs_repeated.py --raw <raw folder> --cache <file.npz> --collect --parts <dir> --out ../results
    python fixed_vs_repeated.py --from-csv ../results/null_draws.csv --out <dir>    (summary from the shipped draws)
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

import yaron_pipeline as yp

R = 1000
GATE = {"observed": 0.3368, "selected": 123, "repeated_mean": 0.1149, "fixed_mean": 0.0014}   # 2026-10-06 run


def load(raw: Path, cache: Path | None):
    if cache is not None and cache.exists():
        z = np.load(cache)
        data, sess = z["data"], z["sess"]
    else:
        sessions = yp.load_all(raw)
        allom, depth, srow = yp.pooled_rows(sessions)
        data, omind = yp.build_data(allom, depth)
        sess = yp.session_of_data_rows(srow, omind)
        if cache is not None:
            np.savez(cache, data=data, sess=sess)
    rho, cnt, peon, sign, _ = yp.score(data, yp.ODD, yp.EVEN)
    return data, sess, rho, cnt, peon, sign


def one_draw(data, sess, peon, sign, d):
    pd = yp.permute_blocks(data, sess, yp.draw_perms_full(d, int(sess.max()) + 1))
    repeated = yp.score(pd, yp.ODD, yp.EVEN)[0]
    fixed = yp.heldout_rho(pd, yp.EVEN, peon, sign)[0]
    return {"draw": d, "repeated": float(repeated), "fixed": float(fixed) if np.isfinite(fixed) else 0.0}


def summarize(rows, obs, cnt, out_dir: Path):
    out = {"observed": float(obs), "selected": int(cnt), "R": R, "arms": {}}
    lines = ["Fixed vs repeated selection inside the block permutation (Yaron et al. 2025 data)",
             f"observed held-out rho {obs:.4f}, {cnt} units selected; R = {R}", "",
             f"{'selection':<10}{'null mean':>10}{'2.5%':>8}{'97.5%':>8}{'share':>8}{'p':>8}"]
    for arm in ("fixed", "repeated"):
        v = np.array([rows[d][arm] for d in range(R)])
        lo, hi = np.percentile(v, [2.5, 97.5])
        p = float((1 + np.sum(v >= obs - 1e-12)) / (R + 1))
        out["arms"][arm] = {"null_mean": float(v.mean()), "q025": float(lo), "q975": float(hi),
                            "share": float(v.mean() / obs), "p": p}
        lines.append(f"{arm:<10}{v.mean():>10.4f}{lo:>8.3f}{hi:>8.3f}{v.mean() / obs:>8.3f}{p:>8.4f}")
    a = out["arms"]
    gate = (round(obs, 4) == GATE["observed"] and cnt == GATE["selected"]
            and round(a["repeated"]["null_mean"], 4) == GATE["repeated_mean"]
            and round(a["fixed"]["null_mean"], 4) == GATE["fixed_mean"])
    out["gate_same_as_earlier_run"] = bool(gate)
    out["selection_effect"] = a["repeated"]["null_mean"] - a["fixed"]["null_mean"]
    lines += ["", f"repeated minus fixed null mean: {out['selection_effect']:+.4f}",
              f"gate (observed score, units selected and both null means equal the 2026-10-06 run): {gate}"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "fixed_vs_repeated.json").write_text(json.dumps(out, indent=1) + "\n")
    (out_dir / "fixed_vs_repeated.txt").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path)
    ap.add_argument("--cache", type=Path)
    ap.add_argument("--parts", type=Path)
    ap.add_argument("--worker", type=int)
    ap.add_argument("--of", type=int)
    ap.add_argument("--collect", action="store_true")
    ap.add_argument("--from-csv", type=Path)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()

    if a.from_csv:                                   # summary from the shipped draws (no raw data needed)
        meta = json.loads((a.from_csv.parent / "fixed_vs_repeated.json").read_text())
        rows = {}
        for ln in a.from_csv.read_text().splitlines()[1:]:
            d, f, r = ln.split(",")
            rows[int(d)] = {"fixed": float(f), "repeated": float(r)}
        summarize(rows, meta["observed"], meta["selected"], a.out)
        return

    data, sess, obs, cnt, peon, sign = load(a.raw, a.cache)
    a.parts.mkdir(parents=True, exist_ok=True)
    if not a.collect:
        part = a.parts / f"part{a.worker}.jsonl"
        have = {json.loads(x)["draw"] for x in part.read_text().splitlines()} if part.exists() else set()
        for d in range(a.worker, R, a.of):
            if d in have:
                continue
            t0 = time.time()
            with part.open("a") as fh:
                fh.write(json.dumps(one_draw(data, sess, peon, sign, d)) + "\n")
            if d % 50 == a.worker:
                print(f"worker {a.worker}: draw {d} ({time.time() - t0:.1f} s)", flush=True)
        return

    rows = {}
    for part in sorted(a.parts.glob("part*.jsonl")):
        for ln in part.read_text().splitlines():
            x = json.loads(ln)
            rows[x["draw"]] = x
    missing = sorted(set(range(R)) - set(rows))
    if missing:
        raise SystemExit(f"{len(missing)} draws missing")
    summarize(rows, obs, cnt, a.out)
    with (a.out / "null_draws.csv").open("w") as fh:
        fh.write("draw,fixed,repeated\n")
        for d in range(R):
            fh.write(f"{d},{rows[d]['fixed']!r},{rows[d]['repeated']!r}\n")


if __name__ == "__main__":
    main()
