#!/usr/bin/env python3
"""Checks of steps 4 and 5 on synthetic data only (no study data). Run: python test_synthetic.py
1. Haxby-shaped labels and volumes: blocks (8 per run, one per category), first-m equalization, the subj5 run drop
   (88 blocks), exclusion with a reason when a run is incomplete.
2. Assignments: half of each run's blocks in class 1, no repeats or swaps; the P5 draw keeps every run balanced
   (8-block runs of step 4 and 6-block runs of step 5); whole-block folds = block mod k.
3. Rules on independent noise (labels by block, no drift): rates near nominal.
4. Rules with voxel-specific slow drift: trial-level rules above nominal, P5 not.
5. PAMAP2-shaped array: window features, NaN handling, timestamp gaps, 24 blocks, runs of 6, exclusion.
6. End to end: run_haxby.py and run_pamap2.py in --test mode on synthetic feature files (all splits, the
   positive controls), then a resume after a truncated last line (no duplicate, stored rows checked).
7. summarize.py on complete synthetic rows (counts, primary contrast, sign count) and its refusal of test rows.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
S5 = HERE.parents[1] / "step5-pamap2" / "code"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(S5))
import engine  # noqa: E402
import prepare_haxby as ph  # noqa: E402
import prepare_pamap2 as pp  # noqa: E402

engine.N_PERM = 40


def haxby_like(rng, n_runs=12, vol_per_block=9, rest=6, nvox=40, drift=0.0):
    cats = list(ph.CATS)
    lab, run = [], []
    for r in range(n_runs):
        lab += ["rest"] * rest
        run += [r] * rest
        for c in rng.permutation(cats):
            lab += [c] * vol_per_block + ["rest"] * rest
            run += [r] * (vol_per_block + rest)
    lab, run = np.array(lab), np.array(run)
    T = len(lab)
    slow = np.cumsum(rng.standard_normal((T, nvox)), axis=0) * drift / np.sqrt(T)     # voxel-specific slow drift
    return rng.standard_normal((T, nvox)) + slow, lab, run


def check_haxby_build():
    rng = np.random.default_rng(1)
    vox, lab, run = haxby_like(rng)
    feat, info = ph.build(vox, lab, run, "subj1")
    assert info["included"] and info["n_blocks"] == 96 and info["m"] == 9, info
    assert np.bincount(feat["block"]).tolist() == [9] * 96
    for r in range(12):
        assert sorted(feat["block_category"][feat["block_run"] == r]) == sorted(ph.CATS)
    assert np.isfinite(feat["X_detrended"]).all()
    lab2 = lab.copy()
    lab2[np.where(lab2 != "rest")[0][0]] = "rest"                          # one block shorter: m = 8
    assert ph.build(vox, lab2, run, "subj1")[1]["m"] == 8
    f5, i5 = ph.build(vox, lab, run, "subj5")                              # run 8 dropped: 88 blocks, 11 runs
    assert i5["included"] and i5["n_blocks"] == 88 and 8 not in i5["runs"], i5
    lab3 = lab.copy()
    lab3[(run == 3) & (lab == "cat")] = "rest"                             # a run without one category: excluded
    f3, i3 = ph.build(vox, lab3, run, "subj2")
    assert f3 is None and not i3["included"] and "run 3" in i3["reason"], i3
    print("1 Haxby build, subj5 drop, exclusion: OK")
    return feat


def check_assignments(feat):
    for b_run, half in ((feat["block_run"], 4), (np.arange(24) // 6, 3)):
        vs = engine.within_run_assignments(b_run, 30, 41, 0)
        keys = {tuple(v) for v in vs}
        assert len(keys) == 30 and not any(tuple(1 - v) in keys for v in vs)
        draw = engine.within_run_draw(vs[0], b_run)
        rng = np.random.default_rng(0)
        for v in vs + [draw(rng) for _ in range(50)]:
            assert all(v[b_run == r].sum() == half for r in np.unique(b_run))
    blk = np.repeat(np.arange(24), 3)
    fl = engine.folds_for("block", np.zeros((72, 1)), np.zeros(72), blk, blk // 6, 0, 4)
    assert len(fl) == 4 and all(set(blk[te] % 4) == {k} for k, (_, te) in enumerate(fl))
    print("2 assignments, P5 draw, block folds: OK")


def rates(drift, n_data, rng):
    hits = {k: 0 for k in ("P1", "P2", "P3", "P4", "P5")}
    for i in range(n_data):
        vox, lab, run = haxby_like(rng, n_runs=6, nvox=24, drift=drift)
        feat, _ = ph.build(vox, lab, run, "subjX")
        v = engine.within_run_assignments(feat["block_run"], 1, 41, 100 + i)[0]
        X, blk, rr = feat["X_raw"], feat["block"], feat["run"]
        y = v[blk]
        fl = engine.folds_for("main", X, y, blk, rr, 7 + i, 5)
        out = engine.run_rules(engine.sim.pipeline(k=10), X, y, blk, rr, fl, feat["block_run"], np.random.default_rng(i), 7 + i)
        for k in hits:
            hits[k] += int(out[k] is not None and out[k] < 0.05)
    return hits


def check_rules():
    ph.EXPECTED_BLOCKS["subjX"] = 48
    rng = np.random.default_rng(3)
    h0 = rates(0.0, 12, rng)
    print("3 no drift, 12 datasets, hits per rule:", h0)
    assert h0["P5"] <= 3
    h1 = rates(10.0, 8, rng)
    print("4 slow drift, 8 datasets, hits per rule:", h1)
    assert h1["P2"] >= 4 and h1["P5"] <= 2                  # nominal would give about 0.4 of 8


def pamap_like(rng, n_win=600, gap_at=None):
    n = 200 * n_win
    data = rng.standard_normal((n, 54))
    data[:, 0] = np.arange(n) * 0.01
    if gap_at is not None:
        data[gap_at:, 0] += 5.0
    data[rng.random(n) < 0.9, 2] = np.nan                  # heart rate at about 9 Hz
    data[1000:1300, 5] = np.nan                            # a gap in one IMU channel (window 5 loses 200 rows)
    return data


def check_pamap2():
    rng = np.random.default_rng(5)
    feat, info = pp.build(pamap_like(rng))
    assert info["included"] and info["n_features"] == 55, info
    assert info["windows_dropped"]["imu"] == 1 and info["windows_kept"] == 599, info
    assert feat["block_run"].tolist() == [i // 6 for i in range(24)]
    assert np.all(feat["block_t0"][1:] > feat["block_t1"][:-1])
    _, ig = pp.build(pamap_like(rng, gap_at=200 * 300 + 50))
    assert ig["windows_dropped"]["gap"] == 1, ig
    _, i2 = pp.build(pamap_like(rng, n_win=400))
    assert not i2["included"] and "fewer than 480" in i2["reason"], i2
    print("5 PAMAP2 build, gaps, exclusion: OK")


def end_to_end():
    py = sys.executable
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        rng = np.random.default_rng(9)
        vox, lab, run = haxby_like(rng, nvox=30, drift=10.0)
        f4, i4 = ph.build(vox, lab, run, "subj1")
        (d / "f4").mkdir()
        np.savez_compressed(d / "f4" / "subj1.npz", **f4)
        (d / "f4" / "subj1.json").write_text(json.dumps(i4))
        f5, i5 = pp.build(pamap_like(rng))
        i5["subject"] = "subject101"
        (d / "f5").mkdir()
        np.savez_compressed(d / "f5" / "subject101.npz", **f5)
        (d / "f5" / "subject101.json").write_text(json.dumps(i5))
        env = {"OMP_NUM_THREADS": "1", "PATH": "/usr/bin:/bin"}
        r4 = [py, str(HERE / "run_haxby.py"), "--features", str(d / "f4"), "--subject", "subj1", "--out-dir", str(d / "runs"), "--test"]
        r5 = [py, str(S5 / "run_pamap2.py"), "--features", str(d / "f5"), "--subject", "subject101", "--out-dir", str(d / "runs"), "--test"]
        for cmd in (r4, r5):
            subprocess.run(cmd, check=True, env=env, capture_output=True)
        p4, p5 = d / "runs" / "rows.step4.subj1.test.jsonl", d / "runs" / "rows.step5.subject101.test.jsonl"
        rows4 = [json.loads(l) for l in p4.read_text().splitlines()]
        rows5 = [json.loads(l) for l in p5.read_text().splitlines()]
        assert len(rows4) == 2 * 2 * 4 + 2 and len(rows5) == 2 * 3 + 2 * 2, (len(rows4), len(rows5))
        assert {r["split"] for r in rows4} == {"main", "tool", "run", "block"} and {r["split"] for r in rows5} == {"main", "tool", "block"}
        pos = [r for r in rows4 if r["arm"] == "pos_face_house"]
        assert all(len(r["labels"]) == 24 and sum(r["labels"]) == 12 for r in pos)
        lines = p4.read_text().splitlines()
        p4.write_text("\n".join(lines[:-1]) + "\n" + lines[-1][:20])       # truncated last line
        subprocess.run(r4, check=True, env=env, capture_output=True)
        again = [json.loads(l) for l in p4.read_text().splitlines()]
        keys = [(r["arm"], r["prep"], r["assignment"], r["split"]) for r in again]
        assert len(again) == len(rows4) and len(set(keys)) == len(keys)
        subprocess.run(r5, check=True, env=env, capture_output=True)         # nothing left to do
        assert len(p5.read_text().splitlines()) == len(rows5)
    print("6 end to end (both runners, controls, resume): OK")


def summary_case(st, d, rng):
    subs = [f"subj{i}" for i in range(1, 7)] if st == 4 else [f"subject{i}" for i in range(101, 110)]
    (d / "runs").mkdir()
    (d / "f").mkdir()
    base = {"step": st, "n_perm": 200, "versions": {"numpy": "2.5.4", "scikit-learn": "1.7.2"}}
    for s in subs:
        inc = not (st == 5 and s == "subject109")
        (d / "f" / f"{s}.json").write_text(json.dumps({"subject": s, "included": inc, "reason": None if inc else "short"}))
        if not inc:
            continue
        rows = []
        fake = lambda **k: dict(base, subject=s, arm="fake", P1=0.01, P2=0.01, P3=float(rng.random()), P4=0.01, P5=float(rng.random()), **k)
        if st == 4:
            rows += [fake(prep=p, assignment=v, split=sp) for p in ("detrended", "raw") for v in range(30) for sp in ("main", "tool", "run", "block")]
            rows += [dict(base, subject=s, arm="pos_face_house", prep="detrended", assignment=0, split=sp, P1=0.001, P2=0.001,
                          P3=0.001, P4=0.001, P5=0.005) for sp in ("main", "run")]
        else:
            rows += [fake(prep="windows2s", assignment=v, split=sp) for v in range(30) for sp in ("main", "tool", "block")]
            rows += [dict(base, subject=s, arm=f"pos_delta{x}", prep="windows2s", assignment=v, split="main", P1=0.001, P2=0.001,
                          P3=0.001, P4=0.001, P5=0.01) for x in (0.5, 1.0) for v in range(30)]
        (d / "runs" / f"rows.step{st}.{s}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    return [sys.executable, str(HERE / "summarize.py"), "--step", str(st), "--rows", str(d / "runs"), "--features", str(d / "f"),
            "--out", str(d / "out")], subs


def check_summary():
    rng = np.random.default_rng(11)
    for st in (4, 5):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            cmd, subs = summary_case(st, d, rng)
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            sj = json.loads((d / "out" / "summary.json").read_text())
            n = 6 if st == 4 else 8
            assert sj["primary"]["subjects_with_E_above_0"] == n and sj["primary"]["positive"] is True, sj["primary"]
            prep = "detrended" if st == 4 else "windows2s"
            assert sj["cells"][f"fake/{prep}/main/P2"]["mean"] == 1.0 and sj["cells"][f"fake/{prep}/main/P2"]["subjects_ge5"] == n
            f = d / "runs" / f"rows.step{st}.{subs[0]}.jsonl"
            lines = f.read_text().splitlines()
            r0 = json.loads(lines[0])
            f.write_text("\n".join([json.dumps(dict(r0, test=True))] + lines[1:]) + "\n")       # the test flag alone
            res = subprocess.run(cmd, capture_output=True, text=True)
            assert res.returncode != 0 and "test rows" in res.stderr, res.stderr[-300:]
            f.write_text("\n".join(lines[1:]) + "\n")                                         # one row missing
            res = subprocess.run(cmd, capture_output=True, text=True)
            assert res.returncode != 0 and "control rows" in res.stderr, res.stderr[-300:]
            f.write_text("\n".join(lines) + "\n")
            (d / "f" / f"{subs[-1]}.json").unlink()                                             # a subject without its JSON
            res = subprocess.run(cmd, capture_output=True, text=True)
            assert res.returncode != 0 and "feature JSONs" in res.stderr, res.stderr[-300:]
    print("7 summary checks (steps 4 and 5): counts, key sets, refusals: OK")


if __name__ == "__main__":
    feat = check_haxby_build()
    check_assignments(feat)
    check_rules()
    check_pamap2()
    end_to_end()
    check_summary()
    print("ALL OK")
