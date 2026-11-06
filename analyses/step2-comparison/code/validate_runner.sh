#!/bin/sh
# Grid-runner validation before stamping (DESIGN.md §14 must 8; written 2026-10-21 11:31 KST).
# A: interleaved labels, drift 0 (sanity cell by construction): every rule should give about 5%.
# B: random block design, Allen drift (= the primary cell layout): ONLY P5 is computed (exact by randomisation,
#    about 5%); P1-P4 of this cell are not computed here so that no study value is opened before stamping.
# 200 replicates each, 3 workers; seed 9 (study cells use other seeds).
cd "$(dirname "$0")"
PY=<home>/Downloads/trackA-school/venv-step2/bin/python
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
mkdir -p ../validate
for w in 0 1 2; do $PY run_grid.py --design interleaved --B 12 --drift 0 --split main --reps 200 --seed 9 --worker $w --of 3 --out ../validate/A_interleaved_drift0.jsonl & done; wait
for w in 0 1 2; do $PY run_grid.py --design random --B 12 --drift 1 --split main --reps 200 --seed 9 --rules P5 --worker $w --of 3 --out ../validate/B_random_P5only.jsonl & done; wait
echo DONE
