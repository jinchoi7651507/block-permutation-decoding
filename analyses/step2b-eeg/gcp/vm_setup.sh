#!/bin/bash
# On the VM: Python env with the laptop's package versions.
set -e
sudo apt-get update -qq && sudo apt-get install -y -qq python3.12-venv > /dev/null
python3.12 -m venv ~/venv-2b
~/venv-2b/bin/pip install -q --upgrade pip
~/venv-2b/bin/pip install -q -r ~/requirements-2b.txt
~/venv-2b/bin/python -c "import mne, sklearn, numpy, scipy; print(mne.__version__, sklearn.__version__, numpy.__version__, scipy.__version__)"
