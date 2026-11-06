# LEMON eligibility run: two problems found (analysis note, 2026-10-21 12:08 KST; nothing stamped, no EEG downloaded)

Run of `code/eligibility.py` (committed before running, 05a81e7): 220 raw subject folders; markers and META only.
1. **Criterion too strict (design v1 §2):** 181 subjects have 16 alternating condition segments, but "every segment 55–65 s" removes all subjects with one longer segment (e.g. sub-010004: one segment 74.7 s). Eligible: 31 (25 young, 6 old). Proposed deviation: 16 alternating segments, each 50–80 s; recorded as a deviation before rerunning.
2. **Draw bug:** the script asked for 40 subjects (32 young, 8 old) from strata with 25 and 6 eligible and silently returned 31. Fix: assert enough eligible subjects per stratum.
3. **All 212 subjects with condition markers start with S210 (eyes closed per the server's EEG_Info),** although EEG_Info says half of the participants started with EC. Either the marker coding or the info text is wrong for part of the sample; the design's data check (posterior alpha EC > EO per subject, v1 §2) decides it after download. Until then the EC/EO labels are treated as unverified.
Awaiting the author's go for the deviation in item 1.
