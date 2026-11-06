# Audit of the automatic exclusions (practice survey)

Written 2026-10-20 23:06 KST. Auditor: one agent, independent of the screener. `screening.csv` was not changed. Protocol: `PROTOCOL.md` §2 (four inclusion criteria). Screening: `SCREENING-NOTE.md` deviation 2.

## Sampling frame and draw
- Frame: the 1,698 rows of `screening.csv` whose `reason` contains `keyword screen`, `article type` or `no full text`. This gives exactly 1,698 (1,316 keyword reason 1; 156 article type reason 1; 67 keyword reason 2; 159 unclear-criterion-1). It matches the count in SCREENING-NOTE. The 7 records corrected in the sensitivity check (orders 100, 690, 2012, 2161, 2221, 2231, 2254) now have manual reasons, so they are not in the frame.
- Frame sorted by `order`, then `idx = numpy.random.default_rng(20261021).choice(1698, 40, replace=False)` (positions in the sorted frame), sorted.
- Drawn orders (40): 63, 79, 98, 127, 137, 304, 305, 368, 375, 476, 508, 517, 518, 521, 663, 669, 901, 902, 1020, 1127, 1209, 1288, 1358, 1359, 1461, 1522, 1559, 1624, 1638, 1691, 1758, 1763, 1795, 1798, 1894, 1898, 2021, 2054, 2116, 2139.
- How the sample breaks down by automatic reason: 35 keyword reason 1; 2 article type (98 abstract collection, 1638 review); 1 keyword reason 2 (368); 2 no full text (669, 1020). (Expected from the frame shares: 31.0 / 3.7 / 1.6 / 3.7.)
- Full text: `https://www.ebi.ac.uk/europepmc/webservices/rest/{PMCID}/fullTextXML`, fetched 2026-10-20 around 23:02 KST. 38 of 40 returned XML. 669 returned HTTP 500 three times (it is one of the 5 PMC 500-errors in SCREENING-NOTE). 1020 is a preprint (PPR992842) with no PMCID. For both, the Europe PMC core record (abstract, publication type) was used. 517 returned XML with no `<body>` (a `restricted-by` record); it was judged from the abstract.
- Judging: Methods (or the closest section when there is none) read against criteria 1→4. The first failing criterion is recorded. Quotes are verbatim from the XML or abstract.

## Per-record results
Judgement codes: **CE** = correctly excluded; **WI** = would be included; **U** = unclear.

| order | PMCID | Title (shortened) | Automatic reason | Judgement (first failing criterion) | Quote |
|---|---|---|---|---|---|
| 63 | PMC12875639 | GPT-4 Omni vs specialised neural networks (skin lesions) | 1 keyword | CE (1: no neural recording) | "We evaluated GPT-4o using 1,000 random cases from the PAD-UFES-20 dataset with 50 repeated trials." |
| 79 | PMC13278741 | Atrial flutter circuits from ECG | 1 keyword | CE (1: human cardiac) | "we enrolled 97 consecutive patients with AFL who underwent catheter-based EP intervention." |
| 98 | PMC12282809 | 2nd Int. Conf. on Public Health and Health Sciences | 1 article type: abstract | CE (1: abstract collection; the only neuron item is a patch-clamp DRG/HEK study with no decoder) | "we recorded the action potential of DRG neurons by current clamp method, and observe the effects of C15 and XE991 on neurons excitability." |
| 127 | PMC12578254 | Conditional VAE for neurofeedback | 1 keyword | CE (1: human EEG) | "This study leverages two public EEG-MI datasets with distinct cohorts and acquisition setups." |
| 137 | PMC12919843 | Scenario-based portfolio optimization | 1 keyword | CE (1: finance) | "This section introduces the key methods and concepts used in our study." (scenario optimisation of asset returns) |
| 304 | PMC12768531 | Metacognitive representations of agency | 1 keyword | CE (1: human EEG) | "We assessed whether violations of visual representations ... affect participants' sense of agency using behavioral and electroencephalography data (EEG)." |
| 305 | PMC11950404 | Triclabendazole resistance in Fasciola hepatica | 1 keyword | CE (1: genomics) | "Adult F. hepatica parasites were collected from naturally infected cattle at slaughterhouses" |
| 368 | PMC11126972 | TIDA neurons' network efficiency in vivo | 2 keyword (<3 decoder terms) | CE (2: animal calcium imaging, but no held-out decoder; cells and recordings are sorted by rule-based thresholds) | "All recorded calcium waves were classified in 3 categories according to the duration of ON and frequency" |
| 375 | PMC12063830 | Landslide susceptibility mapping | 1 keyword | CE (1: geoscience) | "Luolong County is situated in the northeastern part of the Tibet Autonomous Region" |
| 476 | PMC12003885 | Federated learning for breast cancer | 1 keyword | CE (1: no neural recording) | "The successful integration of privacy protection measures in any healthcare area necessitates the implementation of federated learning." |
| 508 | PMC13263383 | Epilepsy diagnosis from EEG entropy | 1 keyword | CE (1: human EEG) | "This analytical study used EEG data from the University of Bonn, including healthy controls (HCs) ... and epileptic seizure patients" |
| 517 | PMC13648456 | ProxiNet (spatial transcriptomics) | 1 keyword | CE (1: transcriptomics; judged from abstract, XML has no body) | "Here, we developed ProxiNet, a spatially supervised framework that learns transcriptomic signatures of pairwise cellular proximity" |
| 518 | PMC11184972 | Decoding EEG responses to visual stimuli | 1 keyword | CE (1: human EEG) | "We acquired data from ten healthy subjects (3 females), 23 ± 2 years old" |
| 521 | PMC12834399 | sEH inhibition in Alzheimer's mice | 1 keyword | CE (1: mice, but no spike/calcium recordings; histology and microbiota) | "5-month-old male and female Wild-Type (WT Control, n=12) and 5xFAD mice (n=25) were used." |
| 663 | PMC11189588 | Neuronal avalanches in temporal lobe epilepsy | 1 keyword | CE (1: human hdEEG) | "We retrospectively enrolled 70 patients with temporal lobe epilepsy, who underwent high-density electroencephalography (hdEEG)" |
| 669 | PMC13223030 | AI classification of Alzheimer's from neuroimaging: a review | unclear-1 (no full text, HTTP 500) | CE in substance (1: review), judged from the Europe PMC record; Methods not readable | pubType: "review-article"; abstract: "Features are extracted from medical images and trained using AI learning models" |
| 901 | PMC13503106 | Dopamine signals: sensory intensity and RPE | 1 keyword | CE (1: fibre photometry of a dopamine sensor, not spikes or calcium imaging of neurons; the decoding is a single-signal auROC with no held-out evaluation, so it would also fail 2) | "we used multi-site fiber photometry recordings of the fluorescent dopamine sensor GRAB-DA" |
| 902 | PMC13168177 | Autoantibody screening in PANDAS | 1 keyword | CE (1: immunology) | "We employed this system for unbiased screening of potential autoimmune targets in PANDAS." |
| 1020 | (PPR992842) | State-dependent DBS in Parkinson's disease | unclear-1 (no full text, preprint) | CE in substance (1: human patients, ECoG), judged from the abstract; Methods not readable | "adapting DBS burst delivery to ongoing movement speed in 24 PD patients ... motor cortex electrocorticography" |
| 1127 | PMC12028213 | Parotid tumours from DCE/DW-MRI | 1 keyword | CE (1: human MRI) | "This was a retrospective study involving 41 patients ... who underwent neck MRI" |
| 1209 | PMC13578614 | MARBLE MRI marker of LATE-NC | 1 keyword | CE (1: human MRI) | "applying machine learning methods on brain magnetic resonance imaging (MRI) and neuropathology data from 918 community-based older adults." |
| 1288 | PMC11368949 | Natural gas load forecasting | 1 keyword | CE (1: energy forecasting) | "The core idea of ensemble learning is to combine multiple relatively simple and moderately accurate models" |
| 1358 | PMC13269409 | Ferroptotic vulnerability after isoflurane | 1 keyword | CE (1: transcriptomics and histology) | "By integrating single-cell and bulk transcriptomic profiling with in vivo behavioral, histological, and biochemical phenotyping" |
| 1359 | PMC12650059 | ML risk stratification of hippocampal atrophy | 1 keyword | CE (1: human clinical/CSF) | "to stratify Alzheimer's disease (AD) patients by risk of hippocampal volume decline using routine clinical and cerebrospinal fluid (CSF) variables." |
| 1461 | PMC13319115 | Rainfall prediction in Pakistan | 1 keyword | CE (1: meteorology) | "for predicting rainfall occurrence in ten climatically diverse cities in Pakistan." |
| 1522 | PMC10871532 | Encoding of melody in human auditory cortex | 1 keyword | CE (1: human intracranial) | "Eight patients undergoing treatment for intractable epilepsy participated in the study" |
| 1559 | PMC11420495 | Remote sensing scene classification | 1 keyword | CE (1: satellite imagery) | "Data sharing is not applicable to this article as no datasets were generated during the current study." (Abstract: "Scene classification in satellite images") |
| 1624 | PMC11659776 | Prosodic hierarchy and cortical entrainment | 1 keyword | CE (1: human EEG) | "We recruited 33 native speakers of German (5 males)." |
| 1638 | PMC13144522 | Progress in image-based profiling | 1 article type: review | CE (1: review, cell microscopy) | article-type "review-article"; "Here, we review the evolving computational landscape of image-based profiling" |
| 1691 | PMC12218136 | Pain classification in hip-fracture patients | 1 keyword | CE (1: human face/audio) | "an automatic multimodal pain recognition system that integrates facial expression and audio data." |
| 1758 | PMC11709427 | High-throughput tracking of C. elegans disease models | 1 keyword | CE (1: behaviour only, no neural recording) | "CRISPR guide RNAs were designed to target large deletions" (phenotyping by video tracking) |
| 1763 | PMC13388300 | Multi-omics of Tianwang Buxin Dan | 1 keyword | CE (1: rat omics, no neural recording) | "Data were collected from a para-chlorophenylalanine (PCPA)- induced insomnia rat model" with "transcriptomic and metabolomic profiling" |
| 1795 | PMC12402162 | Connectome-constrained ligand-receptor analysis | 1 keyword | CE (1: human MRI) | "We used the publicly available data that participated in the Human Connectome Project (HCP; S1200)" |
| 1798 | PMC11228270 | Multistage CNN for Alzheimer's from MRI | 1 keyword | CE (1: human MRI) | "the brain MRI scans were classified into two classes (healthy and dementia)" |
| 1894 | PMC12248717 | White-light endoscopy to hyperspectral images | 1 keyword | CE (1: endoscopy) | "a retrospective, observational study utilising publicly available datasets ... for gastrointestinal disease classification." |
| 1898 | PMC13461148 | Spine nanostructure of cultured neurons | 1 keyword | CE (1: mouse neurons, but fixed-cell morphology, no activity recording) | "Neuronal culture and genotyping of tissue samples from genetically modified mice" (decoding is of spine morphology, abstract) |
| 2021 | PMC12947046 | Pairwise neural networks for ranking molecules | 1 keyword | CE (1: chemistry) | "how it was adapted to learn rankings, and the data used for the evaluation." (graph neural networks on molecules) |
| 2054 | PMC12053643 | Cognitive fatigue detection from biosignals | 1 keyword | CE (1: human biosignals) | "an extensive range of simulations is accomplished on the MEFAR dataset." |
| 2116 | PMC12202505 | Cellular hierarchies of ETMR tumours | 1 keyword | CE (1: human tumour transcriptomics) | "ETMR samples were collected from patients treated at the Boston Children's Hospital" |
| 2139 | PMC11379379 | EMS mutagenesis probability map in C. elegans | 1 keyword | CE (1: genomics) | "we utilized mutation data from a total of 737 strains isolated after EMS mutagenesis" |

## Summary
- **Wrongly excluded: 0 of 40** (0 WI, 0 U). 40 CE. For 38 of them the Methods were read; 2 (669, 1020) had no full text and were judged from the abstract and publication type.
- Wilson 95% interval for the miss rate: **0 to 8.8%** (0/40). With only the 38 full-text records: 0 to 9.2%.
- The automatic reason matched the first failing criterion in every full-text record (37 × reason 1, 1 × reason 2 for 368). For 669 and 1020 the recorded reason (unclear-criterion-1) is right as a process label, but both would fail criterion 1 on content.

## What this means for the 14 included papers
- Point estimate of includable papers missed among the 1,698: **0**. The Wilson upper bound, applied to all 1,698 records, gives up to **about 149** (0.0876 × 1,698). Put another way, the audit alone cannot rule out a true count well above 14. The bound is this loose because 40 is a small sample. It does not mean misses are likely.
- Base rates suggest the real number is far lower. Among the 672 records that passed the keyword screen and were read by hand, only 14 were included (2.1%). In this sample, 36 of 40 automatic exclusions had no animal neural recording at all, and their topics were finance, geoscience, human MRI/EEG, genomics and so on. Only 4 (368, 521, 901, 1898) involved animal neural tissue, and none of these had a held-out population decoder of neural activity. If automatic exclusions were includable at even the 2.1% rate of the hand-read stratum, that would be about 36 papers. The evidence (0/40 here, 0/11 in the screener's broader-regex sensitivity check) points to a rate well below that.
- In short: the audit found no sign that the keyword screen dropped includable papers. A random sample of 40, though, cannot bound the miss count tightly enough to make "14 is the complete set" a confident statement. The risk is concentrated in a small subset that random sampling rarely hits.

## Issues found and suggested next steps
1. **Low power where misses could occur.** Misses are only plausible among automatic exclusions that do mention animals and recordings. A targeted check would be more informative per record read: for example, read every automatic exclusion with ≥1 recording term and ≥3 animal terms, or every reason-2 keyword exclusion (67 records; 368 was the only one sampled).
2. **Restricted XML scored as "no recordings".** 517's fullTextXML has front matter but no `<body>`. The keyword screen saw zero terms and coded it as reason 1 rather than unclear-criterion-1. It was harmless here (transcriptomics), but the same thing would silently exclude a relevant paper with restricted text. A check for body-less XML across the 1,316 keyword reason-1 records is advisable.
3. **No-full-text group (159).** Both sampled records would fail criterion 1 on their abstracts. The two titles SCREENING-NOTE flags as potentially relevant (893, 1820) remain the main open risk in this group and were not in the sample.

## Reproduction
Scratch scripts (not part of the survey files): `draw.py` (frame and draw), `fetch.py` (Europe PMC XML), `prof.py` / `meth.py` / `sn.py` (keyword profile, Methods openings, snippet search), in the session scratchpad `.../scratchpad/audit/`.
