#!/bin/bash
# x86 part of REPLICATE-CHECK.md: a small c2d VM (1 h cap, DELETE) reruns replicates 0-19 of the eight B 24 S-block
# cells with the step 2 code as is, copies the rows back, and is deleted. Simulated data only.
set -u
G=${GCLOUD:-gcloud}   # set CLOUDSDK_PYTHON in the environment if gcloud needs it
Z=us-east4-a; VM=repcheckx86
D="$(cd "$(dirname "$0")" && pwd)"
S2="$D/../../results/step2-comparison"
OUT="$D/replicate_x86_rows"
T=$(mktemp -d); mkdir -p "$T/s2/runs_cloud" "$T/fm"
rsync -a --exclude __pycache__ "$S2/code" "$S2/calib_v2" "$T/s2/"
cp "$S2/runs_cloud/CELLS.json" "$T/s2/runs_cloud/"
cp "$D/replicate_check.py" "$D/foldmap_x86_c2d.json" "$T/fm/"
( cd "$T" && COPYFILE_DISABLE=1 tar --no-xattrs -czf up.tgz s2 fm )
$G compute instances create $VM --zone $Z --machine-type c2d-standard-8 --provisioning-model STANDARD \
  --image-family ubuntu-2404-lts-amd64 --image-project ubuntu-os-cloud --boot-disk-size 20GB \
  --max-run-duration 1h --instance-termination-action DELETE || exit 1
sleep 45
$G compute scp "$T/up.tgz" $VM:~/ --zone $Z --quiet || { $G compute instances delete $VM --zone $Z --quiet; exit 1; }
$G compute ssh $VM --zone $Z --quiet --command "tar xzf up.tgz && sudo apt-get -qq update >/dev/null && sudo apt-get -qq install -y python3-venv >/dev/null && python3 -m venv v && v/bin/pip -q install numpy==2.5.4 scipy==1.18.1 scikit-learn==1.7.2 && v/bin/python -c 'import numpy,scipy,sklearn,platform;print(platform.python_version(),numpy.__version__,scipy.__version__,sklearn.__version__)' > versions.txt && lscpu | grep 'Model name' >> versions.txt && cd ~/s2/code && sha256sum run_grid.py sim.py >> ~/versions.txt && cd ~ && STEP2_DIR=~/s2 v/bin/python fm/replicate_check.py run --mode asis --reps 20 --workers 1 --jobs 8 --out ~/rows > run.log 2>&1; tail -2 run.log; tar czf rows.tgz rows versions.txt run.log"
mkdir -p "$OUT"
$G compute scp $VM:~/rows.tgz "$OUT/" --zone $Z --quiet
$G compute instances delete $VM --zone $Z --quiet
( cd "$OUT" && tar xzf rows.tgz )
echo "instances left: $($G compute instances list --format='value(name)' | wc -l), disks left: $($G compute disks list --format='value(name)' | wc -l)"
