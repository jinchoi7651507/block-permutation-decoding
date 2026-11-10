# Figures

`make_bc_figures.py` draws Figs 1, 2a and 2b; `make_ed_figures.py` draws Extended Data Figs 1–10 (panel a of Extended Data Fig. 3 also has its own figure in `analyses/yaron-panel/results/panel.pdf`; panels b and c read `step6-reanalysis-cell/vm-out-a2/a2-out.tgz` and `step6b-reanalysis-sciadv/out/tests.json`). Both read only the shipped outputs in `analyses/`. Fig. 1 also reads the step 4 and step 5 summaries (open markers). Both print every plotted value with its source file and key; those printouts are `figures_values.txt` (rows of Fig. 1 are numbered from 0 there, 1–4 in the paper).

```sh
cd figures && python make_bc_figures.py && python make_ed_figures.py
```

Needs numpy and matplotlib (3.10.9 used). On 2026-11-02, and again on 2026-11-03 after Fig. 1 gained the post hoc datasets, the 13 PDFs rebuilt this way were byte-identical to the figure files of the manuscript (PDF metadata fields left empty); checked again on 2026-11-09 after Extended Data Figs 2 and 3 changed.
