# Gate fix candidates for the Figure 2 clustering item (run 1: sizes 206/429/626, agreement 0.553)

Written 2026-11-08 (KST; `date` at 11:3x). Comparison with the authors' MATLAB code only. The `tests` stage was not run and no decoding accuracy or p value was computed. Data were read as the gate reads them (cell traces, events, saved `clusterIDs`). The saved `clusters_fig2.mat` also holds `clusterMeta.distMatrix`, `Z`, `cellOrder`, `AnimalCellID`; the distance matrix was used only to compare the clustering input. Nothing in `code/` was edited; the patches are untested copies applied in a scratch mirror.

## What matches
- `Figure2.m` lines 280-287: `pdist(data,'euclidean')`, `linkage(...,'ward')`, `cluster(Z,'maxclust',3)`, data = `self_lever_matrix'` (cells x 120). The port's `fig2_clusters` does the same. Ward on the authors' saved `distMatrix` with scipy gives the saved `clusterIDs` with agreement 1.0 (118/868/275). The algorithm, k, distance and linkage are right. No randomness is involved (no kmeans, no seed): the clustering is deterministic, so a correct port can reach agreement 1.0.
- Per-mouse cell counts match the saved `AnimalCellID` (199/123/294/331/236/78).
- Distances between cells of mice 4-6 equal the saved distances exactly (mice with no skipped trials). All cells of mice 1-3 differ. The saved matrix was traced back to the cause below by recovering the authors' 120-point rows from the saved distances (trilateration against mice 4-6) and regressing them on single trials.

## Cause 1 (main): trial label lag, `Figure2.m` line 197
`TrialType1(CGlobal)=TStype(Clocal);` with `Clocal` incremented only for kept trials (line 202), while `TStype` is indexed in the full event list (line 182: cued Hit, self Hit, Go). When a trial is skipped by the window test (line 192), every later trial takes the label of an earlier event. Mouse 1 skips 2 self-paced Hits (event frames 41997, 42112 > nf - 150), mouse 2 skips 1, mouse 3 skips 1. Both skipped events are the last self-paced Hits, so the first 2 (1, 1) Go trials get label 1 (self-paced) and enter `Trial1MatrixAll` (line 215, `TrialType1==1`). The recovered authors' rows are the mean over the 87 (75, 88) self-paced Hits plus those 2 (1, 1) Go trials with equal weight 1/89 (1/76, 1/89). The port's `build_trials` labels by event type, so it averages 87 trials without the Go trials.
Patch: `fix1-trial-label-lag.patch` (new argument `matlab_label_lag`, default False; `mouse_trials` passes True only for mode "fig2").

## Cause 2 (two cells): constant raw trace, `Figure2.m` lines 152-153 and 169
Mouse 3 has two cells with a constant raw trace (value 1.0; raw indices 94 and 180, identical rows). In MATLAB `dF_Anya_test.m` the interpolated baseline is exactly 1, dF is exactly 0, and `zscore` (line 169) returns zeros for a zero standard deviation. In the port scipy's extrapolating `interp1d` returns 1 +/- 1e-16, dF is about 1e-14 noise, and the z-score scales it to unit variance. The two cells then sit far from the origin (distance to the nearest other cell 1.64 instead of 0.67). Alone, fix 1 gives agreement 0.787 (130/137/994) and fix 2 alone 0.799; both are needed.
Patch: `fix2-constant-cells.patch` (`df_anya`: exact baseline when all window percentiles are equal; `matlab_zscore`: standard deviation 0 replaced by 1, as MATLAB zscore does).

## Result of the candidate patches (scratch mirror, gate's own Figure 2 code path)
- original port: sizes 206/429/626, agreement 0.5527 (reproduces gate run 1)
- fix 1 only: 130/137/994, 0.787; fix 2 only: 70/136/1055, 0.799
- fix 1 + fix 2: 118/275/868, agreement 1.0000, n = 1261. The gate item can be met.
Both patches apply to `code/` with `git apply -p1` from the folder `reanalysis-sciadv/`.

## Do the fixes touch what the tests (section 4) use?
- Fix 1: no, as written. The flag is False by default and only Figure 2 mode (`include_go=True`, unbinned, gate only) sets it.
  CAUTION, separate decision for the author: `Figure4.m` line 92 has the same `TStype(Clocal)` pattern (list line 77, `Clocal` line 99). In the deposited Figure 4 code the Go trials (list order after the self-paced Hits) are always in the list, and the same skipped late self-paced Hits (mice 1-3) shift the labels, so the first Go trials are labelled self-paced in the authors' decoding (Idx1 = `TrialType1==1`, line 113). The port omits Go trials for the Figure 4 pipeline (DESIGN 3.3). Whether to mirror this in the PERI/decoding is a design question: it would change the trial sets used by the tests, so it is NOT included in these patches and needs the author's decision (DESIGN 3.5 lets port fixes follow the authors' code, but it changes the decoded trial set).
- Fix 2: no effect on the Figure 4 pipeline. All 9 cells of mouse 3 whose window percentiles are all equal (including the two constant cells) fail the Figure 4 filter (`fig4_keep_cell` False), so they are dropped before z-scoring, with and without the patch. For the other mice no cell has equal percentiles. Figure 2 mode keeps all cells, so only the gate's Figure 2 clustering changes.
