set -u
cd ~/reanalysis-cell
P=../venv/bin/python
rm -f DONE-a3 PACKED-a3 a3-out.tgz
echo "start $(date -u)"
$P -I code/fetch_data_retry.py data > a3-fetch-retry.log 2>&1; r=$?; echo "fetch-retry exit $r $(date -u +%H:%M:%S)"
if [ $r -eq 0 ]; then
  $P -I -c "import sys; sys.path.insert(0, 'code'); import run_cell_a2, threadpoolctl; from concurrent.futures import ProcessPoolExecutor as P; print(threadpoolctl.threadpool_info()); print(P(1).submit(threadpoolctl.threadpool_info).result())" > blas-a2-order.out 2>&1; echo "blas exit $? $(date -u +%H:%M:%S)"
  $P -I code/run_cell_a3.py fill --extract-root data --prior out-a2 --out out-a3 --workers 56 > a3-fill.log 2>&1; echo "fill exit $? $(date -u +%H:%M:%S)"
fi
echo "end $(date -u)"
touch DONE-a3
