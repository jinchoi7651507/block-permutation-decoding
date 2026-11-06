# Step 3 budget outcome (code addendum 1 §3, §4): machine, workers, sessions, time cap

Written 2026-10-27 before the run, from label-free preparation outputs and the timing pilot (no p value exists in the pilot rows; none was read). Values in `BUDGET-OUTCOME.json` (read by the run script). Hashed with every input listed in `../BUDGET-OUTCOME.sha256` and timestamped before the run. Run notes: `../RUNNOTE.md`; reviews: `../review-budget-outcome.txt`, `../review-pilot-script-ibl.txt`, `../review-run-script-ibl.txt`.

## Decisions made before this record (author, 2026-10-26, after the timing pilot, before the order is stamped; no result seen)
- Machine: **c2d-highmem-56** (56 vCPU, 448 GiB; compute-optimised x86 as §3 requires). §3 names c2d-highcpu-56 as an example; with the pilot's peak memory per process (5.31 GiB) the 112 GiB of c2d-highcpu-56 would allow only 18 workers. Same CPU (AMD EPYC 7B13) and core price as the pilot machine; more RAM (deviation from "t_rs measured on the same machine": stated).
- Cost cap: **X = 60,000 KRW**. **Deviation from the stamped value of §3 (X = 40,000 KRW, approved before any IBL data):** raised by the author after the timing pilot, on cost information only (price, t_rs, memory, disk), with no result seen, so that the whole order can complete. At 40,000 KRW the same computation gives 365 sessions.

## Inputs
- Price: 5,247.17 KRW per hour (Cloud Billing Catalog API, 2026-10-26 11:48 UTC, C2D core and RAM SKUs, us-east4; `PRICE-2026-10-26.json`). Deviation: §3 says "pricing page, converted at that day's KRW rate"; the catalog is Google's price list and gives the billed KRW price directly; the day's market rate (1,323.9 KRW per USD, `FX-2026-10-26.txt`) is recorded beside it. Boot disk, IP, set-up, copy-back and the time between the worker cap and the last-resort shutdown (cap + 45 min) are billed separately and are not inside X (small; stated).
- X / price = 11.435 machine-hours.
- t_rs = 837 vCPU-seconds per region-session (timing pilot attempt 2: 6,699 s over 8 region-sessions in 2 sessions, W = 56 at once incl. 54 dummy loads; RUNNOTE).
- r = 4.217 region-sessions per session (BUDGET-META.json, first 60 sessions; includes sessions the runner skips in seconds, so the cost per session is overstated: conservative).
- Disk: largest session 1.216 GB (`../runs/DISK-SIZES.json`, version 2: the datasets the runner downloads, largest over revisions; checked against the pilot: 0.012 vs 0.01 GB and 0.667 vs 0.67 GB measured). With 0.05 GB per worker for trials and probe-level files: 60 GB / 1.266 GB = **47 workers** (the pure stamped rule, 60 / 1.216, gives 49; the allowance is conservative). The worker's ONE cache tables add nothing measurable (cache_tables_gb 0.0; in the pilot, disk use returned to the same level while both pilot caches still existed). Version 1 of the size count (every spike-sorting dataset over every revision, about 11 times the measured use, `DISK-SIZES-v1.json`) is kept and not used (stated deviation in the method of the count, not in the 60 GB rule).
- RAM: peak 5.31 GiB per process in the pilot (sessions with more units may need about 7 GiB); 47 × 7 = 329 of 440 GiB.

## Outcome
- **Workers W = 47** = min(56 vCPUs, disk 47, RAM 56+).
- Because W < vCPUs, the cap buys W × X/price = 537.4 vCPU-hours for the workers (the machine's vCPU-hours would be 640.4; using the workers' share is a stated reading of §3 so that the count is what X actually pays for). Sessions = floor(537.4 / (t_rs × r)) = 547 > 459, so **all 459 sessions of ORDER.json are planned (139 mice in the prefix before skips)**.
- **Time cap: X/price × 1.1 = 754 minutes**; every worker is stopped there and the prefix rule of `summarize_ibl.py` (ii) applies. Expected run time for the whole order about 9.6 h (about 50,000 KRW), conservative; t_rs measured at W = 56 overstates the per-region-session time at W = 47.
- Stop rule, cut order and "no result opened during the run" unchanged (DESIGN §9). Dead-worker procedure: `vm_ibl_run.sh` header (written before this record).

## Caveats (reviews)
t_rs and peak memory come from 2 gate-passing sessions, not a random sample; the dummy loads understate contention; the 10% slack is shorter than the longest sessions, so the realised prefix can fall short of 459 (both reported); the pilot's input order (PILOT-ORDER.json, RUNNOTE) is a stated deviation; the ONE username set-up is an environment fix (RUNNOTE).
