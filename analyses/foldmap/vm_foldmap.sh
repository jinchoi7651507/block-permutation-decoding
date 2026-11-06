#!/bin/bash
# Small x86 check of the GroupKFold fold map (c2d-standard-2, same CPU family as the step 2 cloud run).
# Creates the VM with a 1 h cap (DELETE), installs the pinned versions, runs foldmap_check.py, copies the JSON back,
# deletes the VM and lists the remaining instances. No study data involved.
set -u
G=${GCLOUD:-gcloud};   # set CLOUDSDK_PYTHON in the environment if gcloud needs it
Z=us-east4-a; VM=foldmapx86
D="$(cd "$(dirname "$0")" && pwd)"
$G compute instances create $VM --zone $Z --machine-type c2d-standard-2 --provisioning-model STANDARD \
  --image-family ubuntu-2404-lts-amd64 --image-project ubuntu-os-cloud --boot-disk-size 20GB \
  --max-run-duration 1h --instance-termination-action DELETE || exit 1
sleep 45
$G compute scp "$D/foldmap_check.py" $VM:~/ --zone $Z --quiet
$G compute ssh $VM --zone $Z --quiet --command "sudo apt-get -qq update >/dev/null && sudo apt-get -qq install -y python3-venv >/dev/null && python3 -m venv v && v/bin/pip -q install numpy==2.5.4 scipy==1.18.1 scikit-learn==1.7.2 && v/bin/python foldmap_check.py > foldmap.json && grep -o -w -E 'avx512f|avx2' /proc/cpuinfo | sort -u | tr '\n' ' ' > cpuflags.txt; lscpu | grep 'Model name' >> cpuflags.txt"
$G compute scp $VM:~/foldmap.json "$D/foldmap_x86_c2d.json" --zone $Z --quiet
$G compute scp $VM:~/cpuflags.txt "$D/foldmap_x86_c2d_cpu.txt" --zone $Z --quiet
$G compute instances delete $VM --zone $Z --quiet
echo "instances left: $($G compute instances list --format='value(name)' | tr '\n' ' ')"
