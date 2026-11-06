# Step 3 budget outcome — DRAFT (not stamped; for review and the author's decision)

Written 2026-10-26 21:55 KST from the timing pilot (attempt 2) and the label-free preparation outputs. No p value exists in the pilot rows (all None by the runner) and none was read. Governs: `DESIGN-v1-CODE-ADDENDUM.md` §3 (machine and budget), RUNNOTE (ONE username; pilot attempts 1 and 2).

## Inputs
- **Price** (`PRICE-2026-10-26.json`): c2d-highcpu-56, us-east4, on-demand, listed in the Cloud Billing Catalog API on 2026-10-26 11:48 UTC: 3,211.9 KRW per hour (2.364 USD per hour; implied 1,358.75 KRW per USD). Deviation from the addendum's wording: it says "read from the Google Cloud pricing page ... converted at that day's KRW rate"; the catalog API is Google's own price list and gives the KRW price directly (the web pricing page could not be read by the tools available).
- **Cap:** X = 40,000 KRW → 12.45 machine-hours → C = 697.4 vCPU-hours (56 vCPUs).
- **r** (BUDGET-META.json, first 60 sessions of the order, unit counts only): 4.217 region-sessions per session (includes sessions the runner will skip in about 9 s each, so r × t_rs overstates the cost per session: conservative).
- **t_rs** (pilot attempt 2, W = 56: 2 pilot processes + 54 dummy loads; PILOT-ORDER = ORDER positions 2 and 4): session 2: 1,333 s for 2 region-sessions (667 s each); session 4: 5,366 s for 6 region-sessions (894 s each); pooled 6,699 s / 8 = **837 s = 0.2326 vCPU-hours per region-session**, download included (session_seconds; ONE cache-table download before it is excluded). /usr/bin/time elapsed 22:18 and 1:29:30.
- **Memory:** peak RSS per pilot process 3.47 GB and **5.56 GB** (session 4, 1,333 kept trials); machine memory used at most 12.8 GB with the tiny dummies. **Disk:** 4.5 GB used, at most 0.67 GB freed per session.
- Caveats (review of the pilot script): t_rs and peak memory come from 2 gate-passing sessions, not a random sample; the dummies (400 × 30 synthetic) understate memory and bandwidth contention; after process 0 ended (22 min), process 1 ran with W − 1 processes; the disk limit rests on two freed_gb values.

## Workers and the formula
- Addendum §3: workers = min(vCPUs, disk limit, RAM limit from the pilot's peak memory). With 5.56 GB per process and 112 GB on c2d-highcpu-56 (90% usable), **W = 18** (RAM-bound); disk: 18 × ~0.7 GB ≪ 60 GB.
- The formula "sessions = floor(C / (t_rs × r))" with C in vCPU-hours assumes all 56 vCPUs run workers. Applied literally it gives 711 (more than the 459 sessions of the order). With W = 18 only 18 vCPUs work, so the vCPU-hours the cap buys **for workers** are 12.45 h × 18 = 224.2, giving **floor(224.2 / (0.2326 × 4.217)) = 228 sessions = 120 mice** (ORDER prefix). This reading (workers' vCPU-hours, not machine vCPU-hours) is proposed here and needs review.
- Minimum target 30 mice: met under every option below.

## Options for the author (only the first keeps the machine type named as the example in §3)
| machine | KRW/h | RAM | W (RAM) | sessions under the cap | mice | whole order (459) would need |
|---|---|---|---|---|---|---|
| **c2d-highcpu-56** (as §3) | 3,212 | 112 GB | 18 | 228 | 120 | 25.0 h, about 80,000 KRW |
| c2d-standard-56 | 3,890 | 224 GB | 36 | 377 | 129 | 12.5 h, about 48,700 KRW |
| c2d-highmem-56 | 5,247 | 448 GB | 56 | 435 | 135 | 8.0 h, about 42,200 KRW |
§3 names "one compute-optimised x86 machine (e.g. c2d-highcpu-56)": all three are compute-optimised C2D machines, so the second and third are within its wording but change the RAM limit; the choice is the author's, made before the order is stamped. Prices use the same catalog SKUs (C2D core and RAM, us-east4).

## Time cap and stop rule
- Machine time cap (§3): C / vCPUs plus 10% = 12.45 h × 1.1 = **13.7 h** (worst-case spend about 44,000 KRW, 10% over X by the stamped rule); reaching it is handled by the prefix rule (`summarize_ibl.py` ii).
- In-order dispatch through claims; sessions beyond the planned count are not dispatched.

## To do before the stamp
Review (statistician + IBL user) of this draft, especially the workers' vCPU-hours reading and the RAM limit; the author's machine choice; then the outcome is finalised and hashed with ORDER.json, STIM-REGIONS.json, BUDGET-META.json, REALISM.json and PILOT-ORDER.json → OpenTimestamps → attestation → run.

## Review (2026-10-26 22:0x, `../review-budget-outcome.txt`): ready after MUST fixes; open before the stamp
- Corrections accepted: RAM peak 5.31 GiB (not 5.56 GB), machine 110 GiB, the 30-s sampler missed the peak (log max 3.68 GB), sessions in the first 60 reach 524 good units against 306 in the pilot session (peak about 7 GB plausible); the "workers' vCPU-hours" reading is a stated deviation (C_workers = (X/price) × W; time cap = (X/price) × 1.1 = 13.70 h); t_rs at W 56 is conservative for a smaller W; "mice" are mice in the planned ORDER prefix before skips.
- Still to do: disk limit from the ONE datasets table (label-free file sizes over the planned prefix); out-of-memory procedure (detection of dead workers, stop, --requeue, restart; truncated-line check); full hash list (PILOT-ORDER in pilot-attempt-2/runs/, PRICE, pilot rows and logs, MACHINE.txt, runs_pilot.sha); market KRW/USD rate of the day beside the catalog price; whether boot disk, IP, set-up and copy-back count inside X.
- Reviewer's recommendation: c2d-highmem-56 (W = 56 = vCPUs, formula literal, 435 sessions / 135 mice in the prefix, RAM margin 1.3×; one deviation: same CPU and core price, more RAM than the pilot machine). Author decides.

**[Superseded 2026-10-27 by `BUDGET-OUTCOME.md` / `.json`: machine c2d-highmem-56, X 60,000 KRW, W 47 from the disk limit v2, all 459 sessions, cap 754 min.]**
