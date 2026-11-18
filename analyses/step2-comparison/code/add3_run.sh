#!/bin/bash
# Driver of the toolbox runs and fixed-order cells on the cloud machine. Run from ~/pe/results/step2-comparison/code.
# Env: PY312 (step 2 environment), PY39 (PyMVPA environment), COSMO (CoSMoMVPA checkout at fe5acaf), W (workers).
# Every step is resumable; a step starts only after the previous one finished on all workers.
set -u
R=..; T=$R/runs_add3/tools; D=$T/data; G=$T/gate
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONWARNINGS=ignore
log() { echo "$(date -u '+%F %T') UTC $*" >> $R/runs_add3/run_tools.log; }
mkdir -p $D $G
# 1. simulation cells (run_add3_cells.py)
$PY312 run_add3_cells.py --workers $W > $R/runs_add3/cells.out 2>&1; log "cells rc $?"
# 2. data: all files before any tool starts (worker indices depend on the sorted file list), then manifest
for k in $(seq 0 $((W-1))); do $PY312 add3_tools_data.py --out $D --worker $k --of $W & done; wait
n=$(ls $D/L*_r*.mat | wc -l); [ "$n" = "2000" ] || { log "DATA INCOMPLETE ($n files), stop"; exit 2; }
$PY312 add3_tools_data.py --out $D --manifest > /dev/null; log "data 2000 files, manifest $(sha256sum $D/MANIFEST.sha256 | cut -c1-16)"
# 3. gate inputs that are not study rows: PyMVPA regenerated draws + G3 + exact G4; CoSMoMVPA single-class check
$PY39 add3_pymvpa.py --data $D --gate $G > $G/pymvpa_gate.out 2>&1; log "pymvpa gate rc $?"
octave --no-gui -q add3_cosmo_errcheck.m $COSMO $G/cosmo_errcheck.txt > /dev/null 2>&1; log "cosmo errcheck rc $?"
# 4. tool rows (CoSMoMVPA main writes the G1 permutation files for L2 replicates 0-49), reference rows
for v in main zscore; do
  for k in $(seq 0 $((W-1))); do octave --no-gui -q add3_cosmo.m $COSMO $D $T/cosmo_$v.w$k.csv $k $W 200 $G $v > /dev/null 2>$T/cosmo_$v.w$k.err & done; wait
  log "cosmo $v done"
done
for v in main zscore chunks; do
  for k in $(seq 0 $((W-1))); do $PY39 add3_pymvpa.py --data $D --out $T/pymvpa_$v.w$k.csv --variant $v --worker $k --of $W > $T/pymvpa_$v.w$k.err 2>&1 & done; wait
  log "pymvpa $v done"
done
for k in $(seq 0 $((W-1))); do $PY312 add3_reference.py --data $D --out $T/ref.w$k.jsonl --worker $k --of $W > $T/ref.w$k.err 2>&1 & done; wait
log "reference done"
# 5. gate (Python part) and completion counts (no rate printed)
$PY312 add3_gate.py --data $D --gate $G --cosmo-error-check $G/cosmo_errcheck.txt > $G/gate.out 2>&1; log "gate rc $?"
$PY312 add3_completion.py --tools $T > $T/COMPLETION-TOOLS.txt 2>&1; log "completion rc $?"
log "end"
