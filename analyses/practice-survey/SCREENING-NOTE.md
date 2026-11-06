# Screening note: practice survey (search + screening stage)

Written 2026-10-20 (KST). Protocol: `PROTOCOL.md` (not edited). Coding of C1–C5 was not done here.

## Search
- Database: Europe PMC REST API, `https://www.ebi.ac.uk/europepmc/webservices/rest/search`, `resultType=lite`, `pageSize=1000`, cursorMark paging, `format=json`.
- Query (exact, as in §1):
  `(decoding OR decoder OR classifier) AND (permutation OR shuffled OR shuffle) AND (block OR blocks OR context) AND (neurons OR "single units" OR "calcium imaging" OR Neuropixels OR electrophysiology) AND OPEN_ACCESS:y AND PUB_YEAR:[2024 TO 2026]`
- Retrieved: 2026-10-20T06:00:06+09:00 (one run).
- Hits: 2,370 (hitCount 2,370; all retrieved). Source: MED 2,182, PPR 154, PMC 34. Latest firstPublicationDate 2026-10-16, so nothing falls after the protocol's 2026-10-19 cut-off.
- Saved: `search.json` (query, retrieval time, hitCount, and id/source/pmcid/doi/title/journal/pubYear for every hit, plus pubType and firstPublicationDate).

## Ordering
Hits were sorted by the string value of the Europe PMC `id` field, then shuffled with `numpy.random.default_rng(20261020).permutation(2370)`. `screening.csv` `order` is the position in this shuffled list.

## Results
| | n |
|---|---|
| Hits | 2,370 |
| Screened | 2,370 (whole list; the 40-include stop was never reached) |
| Included | **14** |
| Excluded | 2,356 |

Exclusions by first failing criterion:
| Reason | n |
|---|---|
| 1 (not primary animal spike/calcium research) | 1,708 |
| 2 (no held-out population decoder of a task variable) | 171 |
| 3 (decoded variable not constant within blocks, as stated in Methods) | 304 |
| 4 | 0 |
| unclear-criterion-1 (no full text from Europe PMC) | 159 |
| unclear-criterion-2 | 1 |
| unclear-criterion-3 | 4 |
| unclear-criterion-4 | 9 |

Included (order / pmcid): 47 / PMC12660755; 61 / PMC10783789; 228 / PMC13418543; 284 / PMC7618349; 577 / PMC11574977; 626 / PMC13633270; 769 / PMC12443960; 803 / PMC12873149; 1309 / PMC11156468; 1429 / PMC11666460; 1471 / PMC13065759; 1605 / PMC13526029; 1916 / PMC12872450; 2078 / PMC13433320. Their full-text XML files are in `fulltext/`, named by PMCID (14 files). The `evidence` column gives verbatim Methods quotes (block structure | held-out evaluation | significance test). Where a Methods sentence alone did not show that a test was actually reported, a Results or figure-legend quote is added in parentheses and labelled as such.

## Deviations and interpretations (in order of impact)

1. **Fewer than 40 includes.** The whole list gave 14. The 40-paper target in §1 could not be met. The order of screening therefore has no effect on the included set.

2. **Two-stage screening (automated keyword screen, then manual reading).** Every record's full-text XML was downloaded and parsed. For 1,698 records the decision came from an automated full-text keyword screen without manual reading:
   - the article type was not a research article (review, abstract collection, editorial and so on): reason 1, 156 records;
   - the body text had fewer than 5 recording terms (spike/single unit/calcium imaging/two-photon/Neuropixels/tetrode/electrophysiology/GCaMP/firing rate …) or fewer than 3 animal-species terms: reason 1, 1,316 records;
   - recording terms were present but there were fewer than 3 decoder/classifier terms: reason 2, 67 records;
   - no full text: unclear-criterion-1, 159 records.

   The other 672 records (≥5 recording terms and ≥3 decoder terms) were judged one by one by the screening agent from their Methods text (decoder sentences, block-design sentences and significance sentences), in order through criteria 1→4. For about 200 of these, criterion 1 was decided from the title plus the keyword profile: clearly human, non-neural or modelling papers.

   Sensitivity check: re-running the automated exclusions with a broader recording regex (adding Ca2+, miniscope, ΔF/F, deconvolved, units and so on) flagged 179 records. Of these, 11 animal or neuroscience papers were read in full by the screening agent and 7 had their reason corrected (orders 100, 690, 2012, 2161, 2221, 2231, 2254). None of the 7 met all criteria. Independent coders may want to spot-check the automated exclusions.

3. **No full text (159).** These are 154 Europe PMC preprints (PPR, no fullTextXML available) and 5 PMC articles whose fullTextXML endpoint returned HTTP 500 on repeated attempts: orders 669, 893, 1123, 1177, 1820. They are excluded as unclear-criterion-1. Two of them (893 BLA, 1820 gustatory cortex) look potentially relevant from their titles.

4. **The protocol's search restrictions (research articles, English, date ≤ 2026-10-19) are not in the query string.** The query was run exactly as written. Article type was handled under criterion 1. Dates were checked (all ≤ 2026-10-16). Language was not filtered separately; all included full texts are in English.

5. **How the criteria were read (strict and literal):**
   - Criterion 1: "animals" excludes human patient single-neuron studies. Recordings that are LFP, ECoG, EEG, hemodynamic or optical-imaging only fail criterion 1. Studies where the decoder input is only fiber photometry or identified single cells fail criterion 2 (not population activity).
   - Criterion 2: "held-out trials" was taken to include held-out time bins, frames or pseudo-trials, because epoch- or session-level designs have no trials. Included papers where the held-out unit is frames or time bins are 61, 626 and 803 (stated in the reason or evidence).
   - Criterion 3: the decoded variable itself must be block-, context-, rule-, session- or epoch-constant (for example drug session, hunger/satiety phase, task rule block, goal block, old/new context block). Papers that only decode per-trial variables (stimulus, choice, outcome, position) inside block tasks fail criterion 3. The block structure had to be stated in the Methods. Order 2254 (air-puff sessions described only in Results) was therefore excluded on this literal basis.
   - Criterion 4: a significance test of decoding performance against chance or a null distribution (shuffled labels, permutation, confidence interval vs shuffle) must be reported in the full text. A paper with only a qualitative "above chance", a test only in the supplement (not in the XML), or only between-condition comparisons was marked unclear-criterion-4: orders 57, 100, 507, 557, 1002, 1437, 1715, 1868, 2132.

6. **Borderline cases (for coder attention).**
   - Included: 577 (the main decoded variable is the model-estimated template; the true template is block-constant), 803 (held-out procedure stated only as "cross-validated 50 times"), 1471 (dPCA pseudo-population; significance from a shuffled 95% CI), 1605 (chance from within-block pseudo-segmentation as well as label shuffle).
   - unclear-criterion-3: 133, 616, 1243, 1333.

7. **One screener.** The protocol does not specify a second screener at the screening stage. All screening judgements were made by a single agent and need independent spot-checking.

## Files
- `search.json`: raw hits with retrieval time and query.
- `screening.csv`: 2,370 rows (order, id, pmcid, doi, title, journal, year, decision, reason, evidence).
- `fulltext/`: full-text XML of the 14 included papers (by PMCID).

**Correction (2026-11-03):** the full-text XML files of the 14 included studies are kept in the working repository and are not redistributed; `fetch_fulltext.py` downloads them from Europe PMC and checks them against `fulltext-MANIFEST.sha256`.

Correction (2026-11-06): "judged manually" and "read manually" above meant judged or read one record at a time rather than by the automatic screen; the screener was the single language-model agent named in point 7 and in MODEL-RECORD.md. Worded so on 2026-11-06.
