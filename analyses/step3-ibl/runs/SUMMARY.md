# Step 3 summary

B = 20000, seed 20261023. Completed prefix: 459 of 459 sessions in the order.
Sessions in the prefix: finished 335, skipped 106, errored 18.
- session fewer than 250 kept trials: 106
- session session error: 18
- region-sessions excluded (fewer than 10 units): 1140
- region-sessions excluded (void/root): 324

## Q1 fake labels (118 mice, 1359 region-sessions)

| row | rate (mouse-weighted) | mice | region-sessions | usable p | NaN/None p | region-sessions < 20 usable | rs-weighted | p in 0.03-0.07 |
|---|---|---|---|---|---|---|---|---|
| P1 | 77.3% (95% 74.5 to 79.5) **inflated** | 118 | 1359 | 27180 | 0 | 0 | 78.5% | 6.3% |
| P2 | 70.4% (95% 67.5 to 72.9) **inflated** | 118 | 1359 | 27180 | 0 | 0 | 71.7% | 8.7% |
| P4 | 75.8% (95% 72.9 to 78.0) **inflated** | 118 | 1359 | 27180 | 0 | 0 | 76.8% | 7.4% |
| PS-refit (sanity: exact by construction) | 4.9% (95% 4.6 to 5.3) | 118 | 1359 | 27180 | 0 | 0 | 4.8% | 4.0% |
| PS-fixed | 57.7% (95% 55.0 to 60.0) **inflated** | 118 | 1359 | 27180 | 0 | 0 | 58.6% | 15.9% |
| P2-block | 1.0% (95% 0.8 to 1.3) | 118 | 1359 | 27180 | 0 | 0 | 0.8% | 0.3% |
| PS-refit-block | 5.0% (95% 4.6 to 5.4) | 118 | 1359 | 27180 | 0 | 0 | 4.9% | 3.8% |
| SEL-repeat | 4.9% (95% 4.6 to 5.3) | 118 | 1359 | 27180 | 0 | 0 | 4.8% | 4.0% |
| SEL-fixed | 6.1% (95% 5.6 to 6.6) | 118 | 1359 | 27180 | 0 | 0 | 6.0% | 4.8% |
| IID-SEL-repeat | 5.2% (95% 4.9 to 5.5) | 118 | 1359 | 27180 | 0 | 0 | 5.2% | 3.9% |
| IID-SEL-fixed | 5.2% (95% 4.8 to 5.5) | 118 | 1359 | 27180 | 0 | 0 | 5.2% | 4.2% |
| IID-P1 | 9.0% (95% 8.5 to 9.5) | 118 | 1359 | 27180 | 0 | 0 | 9.0% | 5.4% |
| IID-P2 | 4.8% (95% 4.5 to 5.2) | 118 | 1359 | 27180 | 0 | 0 | 5.0% | 4.2% |
| IID-P4 | 9.2% (95% 8.7 to 9.7) | 118 | 1359 | 27180 | 0 | 0 | 9.2% | 5.6% |

## Primary contrasts on fake labels (paired at region-session and draw)

- F = P2 - PS-refit (S-main): 65.6% (95% 62.6 to 68.0; Bonferroni 98.3% 61.9 to 68.5); **positive**; mice 118, region-sessions 1359, pairs 27180
- S = SEL-fixed - SEL-repeat: 1.2% (95% 0.8 to 1.5; Bonferroni 98.3% 0.8 to 1.6); **positive**; mice 118, region-sessions 1359, pairs 27180
- beside S, the same contrast in the i.i.d. control: -0.0% (95% -0.3 to 0.2); mice 118, pairs 27180

## Secondary contrasts (§7; no decision)

- P1 - PS-refit: 72.4% (95% 69.7 to 74.6); mice 118, pairs 27180
- P4 - PS-refit: 70.9% (95% 68.0 to 73.1); mice 118, pairs 27180
- PS-fixed - PS-refit: 52.8% (95% 50.2 to 55.1); mice 118, pairs 27180
- S-block: P2-block - P2: -69.4% (95% -72.0 to -66.4); mice 118, pairs 27180
- P1 - IID-P1 (Extended Data): 68.4% (95% 65.6 to 70.5); mice 118, pairs 27180

## Q2 real labels (118 mice, 1359 region-sessions)

V = share P2 - share PS-refit: 64.8% (95% 60.3 to 68.9; Bonferroni 98.3% 59.3 to 69.8); **positive**; mice 118, region-sessions with both verdicts 1359

| | PS-refit sig | PS-refit not |
|---|---|---|
| P2 sig | 146 | 884 |
| P2 not | 0 | 329 |

Discordant: P2 only 884, PS-refit only 0; exact McNemar-type p 0.0000 (descriptive: region-sessions are not independent).

| real-label verdict | own fake-label P2 rate > 10% | <= 10% | no fake value |
|---|---|---|---|
| P2 only | 883 | 1 | 0 |
| other verdicts | 466 | 9 | 0 |

| row | rate (mouse-weighted) | mice | usable | NaN/None | rs-weighted | p in 0.03-0.07 |
|---|---|---|---|---|---|---|
| P1 | 80.3% (95% 76.5 to 83.4) | 118 | 1359 | 0 | 82.0% | 5.2% |
| P2 | 74.6% (95% 70.2 to 78.5) | 118 | 1359 | 0 | 75.8% | 8.1% |
| P4 | 79.5% (95% 75.7 to 82.7) | 118 | 1359 | 0 | 80.9% | 7.0% |
| PS-refit | 9.8% (95% 7.7 to 12.9) | 118 | 1359 | 0 | 10.7% | 6.9% |
| PS-fixed | 63.8% (95% 58.9 to 68.3) | 118 | 1359 | 0 | 66.4% | 11.8% |
| P1-block | 1.9% (95% 1.1 to 3.6) | 118 | 1359 | 0 | 2.2% | 0.6% |
| P2-block | 1.6% (95% 0.9 to 3.3) | 118 | 1359 | 0 | 1.8% | 0.7% |
| P4-block | 1.3% (95% 0.6 to 3.0) | 118 | 1359 | 0 | 1.3% | 0.4% |
| PS-refit-block | 6.8% (95% 5.0 to 9.3) | 118 | 1359 | 0 | 6.6% | 5.9% |
| PS-fixed-block | 1.1% (95% 0.5 to 2.8) | 118 | 1359 | 0 | 1.1% | 0.3% |
| SEL-repeat | 8.0% (95% 6.2 to 11.1) | 118 | 1359 | 0 | 8.5% | 5.5% |
| SEL-fixed | 10.6% (95% 8.3 to 13.9) | 118 | 1359 | 0 | 11.0% | 7.2% |

## Positive control (stimulus side, PS-refit p < 0.05)

| region group | significant | not | mice |
|---|---|---|---|
| stimulus-significant | 221 | 323 | 108 |
| other | 96 | 707 | 112 |
| no value | 1 | 11 | 9 |

Region-sessions with no usable PS-refit p (excluded): 0

## Extended Data: regions with >= 3 sessions (real labels; significant / usable; descriptive)

- ACAd: P2 9/12, PS-refit 2/12
- ACAv: P2 5/8, PS-refit 0/8
- ACB: P2 6/9, PS-refit 0/9
- AId: P2 5/6, PS-refit 1/6
- AIp: P2 3/4, PS-refit 1/4
- AIv: P2 3/4, PS-refit 2/4
- AM: P2 0/4, PS-refit 0/4
- ANcr1: P2 3/3, PS-refit 1/3
- ANcr2: P2 2/3, PS-refit 0/3
- AON: P2 7/9, PS-refit 0/9
- APN: P2 28/30, PS-refit 5/30
- AUDp: P2 4/5, PS-refit 0/5
- AUDv: P2 4/5, PS-refit 0/5
- AV: P2 3/5, PS-refit 0/5
- BLA: P2 4/6, PS-refit 0/6
- BMA: P2 5/7, PS-refit 0/7
- BST: P2 3/6, PS-refit 1/6
- CA1: P2 27/47, PS-refit 1/47
- CA3: P2 19/25, PS-refit 0/25
- CEA: P2 2/3, PS-refit 0/3
- CENT2: P2 8/8, PS-refit 0/8
- CENT3: P2 7/8, PS-refit 1/8
- CLI: P2 2/3, PS-refit 0/3
- COAp: P2 3/4, PS-refit 0/4
- COPY: P2 5/5, PS-refit 0/5
- CP: P2 36/43, PS-refit 7/43
- CS: P2 4/5, PS-refit 0/5
- CUL4 5: P2 15/15, PS-refit 2/15
- CUN: P2 2/4, PS-refit 0/4
- DCO: P2 5/6, PS-refit 0/6
- DEC: P2 4/5, PS-refit 0/5
- DG: P2 21/29, PS-refit 1/29
- DN: P2 3/3, PS-refit 0/3
- DP: P2 6/7, PS-refit 0/7
- ECT: P2 2/5, PS-refit 0/5
- ENTl: P2 12/13, PS-refit 3/13
- ENTm: P2 7/11, PS-refit 0/11
- EPd: P2 5/7, PS-refit 1/7
- EPv: P2 2/3, PS-refit 1/3
- Eth: P2 3/11, PS-refit 1/11
- FOTU: P2 4/4, PS-refit 1/4
- FRP: P2 2/3, PS-refit 0/3
- GPe: P2 6/6, PS-refit 1/6
- GRN: P2 11/11, PS-refit 2/11
- IC: P2 6/11, PS-refit 1/11
- ILA: P2 5/7, PS-refit 0/7
- IP: P2 13/13, PS-refit 1/13
- IRN: P2 17/19, PS-refit 4/19
- LAV: P2 2/3, PS-refit 1/3
- LD: P2 5/10, PS-refit 0/10
- LGd: P2 11/15, PS-refit 0/15
- LGv: P2 3/4, PS-refit 0/4
- LH: P2 3/3, PS-refit 2/3
- LHA: P2 2/5, PS-refit 0/5
- LP: P2 23/38, PS-refit 1/38
- LSr: P2 8/21, PS-refit 2/21
- LSv: P2 2/4, PS-refit 0/4
- MD: P2 9/11, PS-refit 1/11
- MDRN: P2 2/3, PS-refit 0/3
- MEA: P2 1/6, PS-refit 0/6
- MG: P2 5/9, PS-refit 2/9
- MOp: P2 20/22, PS-refit 6/22
- MOs: P2 22/26, PS-refit 4/26
- MRN: P2 48/57, PS-refit 10/57
- MS: P2 1/3, PS-refit 0/3
- MV: P2 11/13, PS-refit 1/13
- NLL: P2 2/3, PS-refit 0/3
- NOD: P2 4/5, PS-refit 0/5
- NTS: P2 3/3, PS-refit 0/3
- ORBl: P2 4/5, PS-refit 0/5
- ORBm: P2 4/4, PS-refit 1/4
- ORBvl: P2 5/5, PS-refit 2/5
- PA: P2 3/4, PS-refit 0/4
- PAA: P2 2/3, PS-refit 0/3
- PAG: P2 19/21, PS-refit 0/21
- PAR: P2 1/5, PS-refit 0/5
- PARN: P2 5/8, PS-refit 0/8
- PB: P2 5/7, PS-refit 1/7
- PCG: P2 3/5, PS-refit 0/5
- PCN: P2 1/3, PS-refit 1/3
- PF: P2 3/3, PS-refit 1/3
- PGRN: P2 3/3, PS-refit 1/3
- PIR: P2 4/16, PS-refit 0/16
- PL: P2 8/10, PS-refit 1/10
- PO: P2 20/29, PS-refit 4/29
- POL: P2 1/4, PS-refit 0/4
- POST: P2 4/8, PS-refit 0/8
- PPN: P2 10/10, PS-refit 2/10
- PRM: P2 3/5, PS-refit 0/5
- PRNc: P2 6/6, PS-refit 2/6
- PRNr: P2 13/15, PS-refit 4/15
- PSV: P2 3/4, PS-refit 1/4
- PYR: P2 3/3, PS-refit 0/3
- PoT: P2 2/3, PS-refit 0/3
- ProS: P2 4/7, PS-refit 0/7
- RN: P2 7/8, PS-refit 3/8
- RSPagl: P2 6/8, PS-refit 2/8
- RSPd: P2 8/10, PS-refit 0/10
- RSPv: P2 7/12, PS-refit 0/12
- RT: P2 11/14, PS-refit 3/14
- SCm: P2 33/35, PS-refit 7/35
- SCs: P2 5/7, PS-refit 0/7
- SF: P2 4/4, PS-refit 0/4
- SGN: P2 3/5, PS-refit 1/5
- SI: P2 5/6, PS-refit 0/6
- SIM: P2 8/8, PS-refit 0/8
- SMT: P2 3/4, PS-refit 1/4
- SPIV: P2 7/7, PS-refit 2/7
- SPVI: P2 2/4, PS-refit 0/4
- SPVO: P2 3/3, PS-refit 0/3
- SSp-bfd: P2 13/13, PS-refit 0/13
- SSp-ll: P2 3/3, PS-refit 0/3
- SSp-m: P2 5/6, PS-refit 0/6
- SSp-tr: P2 4/6, PS-refit 1/6
- SSp-ul: P2 3/4, PS-refit 2/4
- SSs: P2 6/8, PS-refit 2/8
- SUB: P2 8/12, PS-refit 0/12
- SUT: P2 3/5, PS-refit 2/5
- SUV: P2 6/6, PS-refit 0/6
- TEa: P2 4/5, PS-refit 1/5
- TRN: P2 6/6, PS-refit 0/6
- TTd: P2 4/6, PS-refit 0/6
- V: P2 5/5, PS-refit 0/5
- VAL: P2 4/5, PS-refit 1/5
- VISa: P2 19/20, PS-refit 0/20
- VISam: P2 6/7, PS-refit 0/7
- VISl: P2 3/5, PS-refit 0/5
- VISli: P2 2/4, PS-refit 0/4
- VISp: P2 13/17, PS-refit 0/17
- VISpm: P2 4/6, PS-refit 1/6
- VPL: P2 10/10, PS-refit 3/10
- VPM: P2 16/18, PS-refit 1/18
- VeCB: P2 2/3, PS-refit 1/3
- ZI: P2 13/14, PS-refit 3/14
