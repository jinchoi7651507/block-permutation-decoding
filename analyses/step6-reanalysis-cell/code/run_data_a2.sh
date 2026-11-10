set -u
cd ~/reanalysis-cell
P=../venv/bin/python
O=out-a2
rm -f DONE-a2
st(){ echo "$1 exit $2 $(date -u +%H:%M:%S)"; }
echo "start $(date -u)"
$P -I code/run_cell_a2.py fetch-gate --extract-root data > a2-fetch.log 2>&1; r=$?; st fetch-gate $r
if [ $r -eq 0 ]; then
  $P -I code/run_cell_a2.py inspect --extract-root data --out $O --cache > a2-inspect.log 2>&1; r=$?; st inspect $r
fi
if [ $r -eq 0 ]; then
  $P -I code/run_cell_a2.py gate --extract-root data --out $O --cache --workers 56 > a2-gate.log 2>&1; st gate $?
  $P -I code/run_cell_a2.py compare-names --extract-root data --out $O > a2-compare.log 2>&1; st compare-names $?
  $P -I code/run_cell_a2.py select --out $O > a2-select.log 2>&1; st select $?
  for t in primary trial win600 adjacent estimated; do
    $P -I code/run_cell_a2.py test --name $t --extract-root data --out $O --cache --workers 56 > a2-test-$t.log 2>&1; st test-$t $?
  done
fi
echo "end $(date -u)"
touch DONE-a2
