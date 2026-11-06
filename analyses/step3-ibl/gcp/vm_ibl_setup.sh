#!/bin/bash
# Step 3 IBL machine set-up (code addendum 1 §1, §3): Python 3.12 env with ONE-api 3.6.1, ibllib 4.1.0, brainwidemap
# (paper repository) commit 118fc36; the paper repository checked out at the same commit for region_info.csv.
set -e
exec > ~/setup.log 2>&1
sudo apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q git curl python3.12-venv
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv venv -p 3.12 ~/ve312
uv pip install --python ~/ve312/bin/python "ONE-api==3.6.1" "ibllib==4.1.0" "git+https://github.com/int-brain-lab/paper-brain-wide-map.git@118fc36cb3602934466ad2c6087c2b3b441f9f1f"
git clone -q https://github.com/int-brain-lab/paper-brain-wide-map.git ~/pbwm && git -C ~/pbwm checkout -q 118fc36cb3602934466ad2c6087c2b3b441f9f1f
~/ve312/bin/python -c "import one, ibllib, brainwidemap, brainbox.task.closed_loop as c, hashlib; print('one', one.__version__, 'ibllib', ibllib.__version__); print('closed_loop', hashlib.sha256(open(c.__file__,'rb').read()).hexdigest())"
echo SETUP DONE
