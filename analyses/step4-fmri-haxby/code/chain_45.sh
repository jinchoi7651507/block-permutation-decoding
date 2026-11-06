#!/bin/bash
# Steps 4 and 5 chain (DESIGN §11 / §10 order): wait for both Bitcoin attestations, check the hash lists, then
# step 4 (fetch, prepare, run six subjects in parallel) and afterwards step 5 (fetch, prepare, run in parallel).
# Data folders are outside the repository. Log: ../runs/chain.log. Re-running is safe (fetch skips present files,
# runners resume).
set -u
PE="$(cd "$(dirname "$0")/../../.." && pwd)"
PY="${PY:?set PY to the analysis python}"
D4="${DATA4:?set DATA4}"; D5="${DATA5:?set DATA5}"; F4="$D4/features"; F5="$D5/features"
S4="$PE/results/step4-fmri-haxby"; S5="$PE/results/step5-pamap2"
L="$S4/runs/chain.log"
log() { echo "$(date '+%F %T %Z') $*" >> "$L"; }
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
log "chain start"
for S in "$S4" "$S5"; do
  until (cd "$S" && ots upgrade DESIGN-v2.sha256.ots 2>&1 | grep -q "Success! Timestamp complete"); do sleep 300; done
  log "attested: $S"; (cd "$S" && ots info DESIGN-v2.sha256.ots | grep -i "BitcoinBlockHeaderAttestation" >> "$L")
  (cd "$S" && shasum -a 256 -c DESIGN-v2.sha256 >> "$L" 2>&1) || { log "HASH MISMATCH in $S, stop"; exit 1; }
done
log "step 4 fetch"; "$PY" "$S4/code/fetch_haxby.py" --dir "$D4" >> "$S4/runs/fetch.log" 2>&1 || { log "fetch failed"; exit 1; }
for i in 1 2 3 4 5 6; do "$PY" "$S4/code/prepare_haxby.py" --subject-dir "$D4/subj$i" --subject "subj$i" --out "$F4" >> "$S4/runs/prepare.log" 2>&1; done
log "step 4 prepared"
for i in 1 2 3 4 5 6; do
  "$PY" "$S4/code/run_haxby.py" --features "$F4" --subject "subj$i" --out-dir "$S4/runs" > "$S4/runs/run.subj$i.out" 2> "$S4/runs/run.subj$i.err" &
done
wait; log "step 4 runs finished"
log "step 5 fetch"; "$PY" "$S5/code/fetch_pamap2.py" --dir "$D5" >> "$S5/runs/fetch.log" 2>&1 || { log "fetch 5 failed"; exit 1; }
for i in $(seq 101 109); do "$PY" "$S5/code/prepare_pamap2.py" --file "$D5/Protocol/subject$i.dat" --subject "subject$i" --out "$F5" >> "$S5/runs/prepare.log" 2>&1; done
log "step 5 prepared"
for batch in "101 102 103 104 105 106" "107 108 109"; do              # at most six processes (macOS bash 3.2: no wait -n)
  for i in $batch; do
    "$PY" "$S5/code/run_pamap2.py" --features "$F5" --subject "subject$i" --out-dir "$S5/runs" > "$S5/runs/run.subject$i.out" 2> "$S5/runs/run.subject$i.err" &
  done
  wait
done
log "step 5 runs finished"; log "chain done"
