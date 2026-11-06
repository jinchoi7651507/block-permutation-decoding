# Extended Data Fig. 3: fixed vs repeated selection inside the block permutation (rat auditory cortex)

**Status: post hoc.** This comparison was first run on 2026-10-06, after the block-permutation tests of these data had been run, and was not timestamped. This folder reruns it with the same draws (2026-10-28). It is a published example of the general rule; it is not a test of the published claim.

## Data and pipeline
- Data: Yaron et al. (2025), PLoS Biol 23: e3003242; raw recordings on Zenodo (10.5281/zenodo.15531781, CC BY 4.0), 18 sessions of rat auditory cortex, eight probability conditions, each presented as one block. `data/fetch_yaron.py` downloads the 19 files used (`data/MANIFEST.sha256`).
- Pipeline: the authors' selection and held-out test, ported to Python from their MATLAB code (Zenodo 10.5281/zenodo.15531880): units selected on odd trials, scored on even trials by the Spearman correlation of their per-condition means with the condition probability (`code/yaron_pipeline.py`). Odd and even trials come from the same blocks.
- Observed: 123 units selected, held-out correlation 0.337.

## Null and the two arms
One uniform permutation of the eight condition blocks per session, the same for odd and even trials, 1,000 permutations. In every permutation the same permuted data are scored twice:
- **selection repeated:** the selection is rerun on the permuted odd trials, and the newly selected units are scored on the permuted even trials;
- **selection fixed:** the 123 units selected on the real labels are kept, with their signs, and scored on the permuted even trials.

## Result (`results/fixed_vs_repeated.txt`)
| selection | null mean | central 95% | share of observed | p |
|---|---|---|---|---|
| fixed | 0.0014 | −0.141 to 0.143 | 0.4% | 0.001 |
| repeated | 0.1149 | 0.014 to 0.244 | 34% | 0.001 |

- With the selection repeated, the null mean is 0.115, a third of the observed correlation. With the selection fixed it is 0.001. Holding the selection fixed therefore understates what the selection alone produces under the null by 0.11, while both arms give the smallest possible p value here.
- Gate: the observed score, the number of selected units and both null means equal the 2026-10-06 run (`gate_same_as_earlier_run: true`).
- Panel: `results/panel.pdf` (`code/plot_panel.py`).

## Reading and limits
- The example shows the rule of the main text on published data: a step fitted to the labels (here the unit selection) has to be repeated inside the permutation, or the null is too low.
- Both arms permute whole blocks and so assume that the blocks are exchangeable under the null. The comparison between the arms does not depend on this, because the two arms share every permutation.
- Not tested here: whether the published conclusion about these neurons holds.

## Reproduce
```sh
cd code
python fixed_vs_repeated.py --from-csv ../results/null_draws.csv --out <dir>   # summary from the shipped draws; compare with results/
python ../data/fetch_yaron.py && (cd ../data/raw && shasum -a 256 -c ../MANIFEST.sha256)   # full rerun: data (about 1.3 GB)
python fixed_vs_repeated.py --raw ../data/raw --cache <file.npz> --worker 0 --of 1 --parts <dir>   # about 5 min to load, 2 min for the draws
python fixed_vs_repeated.py --raw ../data/raw --cache <file.npz> --collect --parts <dir> --out <dir>
python plot_panel.py --summary <dir>/fixed_vs_repeated.json --out <dir>/panel.pdf
```
Run on 2026-10-28 on the laptop of `ENVIRONMENT.md` (Python 3.12.3, numpy 2.4.6, scipy 1.18.1, h5py 3.16.0, matplotlib 3.10.9), one process: loading 293 s, 1,000 permutations about 2 min.
