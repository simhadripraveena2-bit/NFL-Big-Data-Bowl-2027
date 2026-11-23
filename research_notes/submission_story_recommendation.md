# Phase 9A: submission story recommendation

**Basis:** `submission_fit_audit.md`.

**Scope:** documentation only. No new analysis, test or association. Nothing below changes a model, result, the preregistration, or analysis code.

## 1. Decision: **A. Submit the completed empirical study, with an honest and actionable interpretation.**

### Why not B (one more performance analysis)

The single best candidate was identified and assessed. It is **not** recommended.

| item | DL pressure per rush (best candidate) |
|---|---|
| why it was the best candidate | the strongest football theory (the competition's own example: "first-step quickness … compared to pass-rush"); a true performance outcome; the largest eligible n among performance outcomes with a speed rationale |
| reliability | context-adjusted split-half 0.50 [0.18, 0.72]; season → season 0.30 (PSM §3) |
| sample size | 53 DL with a valid tracked 40 (25 EDGE, 28 interior); about 34k rush snaps |
| minimum detectable effect | observed r ≈ 0.38 (n = 53, 80 % power, two-sided α 0.05), i.e. **true-score r ≈ 0.54** after attenuation (√(0.99 × 0.50) ≈ 0.70). Within role (n 25 / 28) it is far larger |
| identification | DL tracked peak speed has 5 % variance outside the 40 and ρ −0.80 with weight. H1-DL(b) already showed that role and weight absorb most of the DL speed signal. A pressure association could not be attributed to combine *tracking* or to speed rather than body type, and role is a mediator (adjusting for it risks collider bias) |
| forking paths | chosen after the DL movement result was known, so it would read as outcome shopping |
| expected information | likely inconclusive; any non-null would be uninterpretable as a tracking signal |

**A draft preregistration outline is recorded only so the lead can overrule this decision** (§6). It is not proposed for execution.

The other outcomes are weaker:
- **WR targets per route:** reliable (0.78), but a usage and deployment rate. WR is already covered by H2.
- **OL pressure allowed** (0.47) and **OL peak pressure probability** (0.69): there is weak theory for combine top speed in pass protection, and OL speed barely shows in game movement (ρ 0.03–0.11).

### Why not C

- The entry passes both gates if H2 is framed as the performance link and a public notebook is attached.
- Its rigour is unusual for the competition.
- It gives evaluators six concrete, defensible messages (audit §4).
- It is not likely to win on football novelty. But a careful, decision-oriented null and confound study is a legitimate and useful entry, and it is better than an under-powered additional test.

## 2. Proposed title

**"Fast on Sundays, Not More Open: What Combine Tracking Speed Does and Doesn't Tell NFL Evaluators"**

Alternative: "Where Combine Speed Shows Up: Speed Expression, Separation and Body Type in the 2023–25 Rookie Class".

## 3. Central message for NFL decision-makers (about 80 words)

> Combine sensor tracking measures top speed reliably. For receivers and defensive backs, about a third of it is not in the 40 time. A receiver's combine top speed carries into how fast he runs in games, on short and deep routes alike. But it did not tell us how open he gets: tracked top speed added nothing measurable to deep-route separation beyond the 40. For defensive linemen, "combine speed" is mostly body type and role. Use tracked speed to forecast speed, not separation, and judge linemen's speed within their body type.

## 4. Story structure (≤ 2,000 words, ≤ 9 figures or tables)

| section | content | about | visual |
|---|---|---|---|
| 1. The question | "Does combine speed translate to the field, and does it make players better?" Define the four layers: capacity → movement → performance, with deployment in between | 200 | **V1:** four-layer schematic, with the cohort and sample sizes |
| 2. Measuring combine speed with tracking | tracked peak speed vs the official 40; reliability; unique variance by position (F1) | 200 | **V2:** WR/DB vs DL "what tracking adds beyond the 40" bars (34 / 36 / 5 %) |
| 3. When does an NFL play ask for top speed? | speed demand by position and context (F3) | 200 | **V3:** demand heat-strip (WR deep 17 % … OL 1 %) |
| 4. Does combine speed show up in game speed? | H1-WR with ρ deep and short and Δ; other positions (F2) | 300 | **V4:** forest plot of ρ_c by position and context, with intervals |
| 5. Does it make receivers more open? (performance) | H2 β_P, held-out-player prediction, EIV; separation is mostly deployment (F4, F5) | 400 | **V5:** "2-inch ceiling" interval plot; **V6:** separation reliability, raw vs context-adjusted |
| 6. Defensive linemen: speed or body type? | H1-DL(b) and the role / weight audit (F6) | 300 | **V7:** DL speed–weight–role scatter with the pooled vs within-role ρ |
| 7. What evaluators should do | the six findings as guidance; limits (n ≈ 53–57 per position, associational, REG 2023–25 only) | 250 | **T1:** guidance table |
| Appendix | pre-registration, synthetic validation, bootstrap, code (linked notebook) | outside the word count where allowed | — |

**Total:** about 1,850 words; 8 visuals.

**Writing rules carried over from the frozen study:**
- "inconclusive" and "not detected", never "no effect";
- no causal reading of the DL adjusted value;
- no novelty claim (CLAUDE.md literature rule; 8C);
- within-position reliabilities only;
- REG only.

## 5. Work needed for Phase 9B (only after approval)

1. **Writeup:** draft to the structure above and keep the word count. Present numbers exactly as in `research_findings_summary.md`.
2. **Visuals:** design V1–V7 and T1 for accessibility (colour-blind-safe, direct labels). Build them from **already-computed** outputs only: no new estimates.
3. **Public Kaggle notebook:** a reproducible path from competition data to the figures, using the frozen code and registered outputs. Competition data stays on Kaggle, and nothing is redistributed (rules §Data).
4. **Final consistency check:** every number in the writeup traced to a results note and a run id.

## 6. Record only: draft preregistration outline for the rejected option B

**Not proposed for execution.** Recorded only so the lead can overrule this decision with full information.

| element | outline |
|---|---|
| hypothesis | among DL, tracked combine peak speed is positively associated with context-adjusted pressure per rush (REG 2023–25) |
| outcome | `time_to_pressure` non-null per pass rush (`player_get_off` non-null), as a player-level random-effect logit with pre-snap covariates (alignment, down, distance bin, formation, season) and a team-season effect |
| predictor | registered tracked 40 peak speed (standardised within position across all combine DL) |
| sample | the registered DL sample (53 players, ≥ 100 rushes, valid tracked 40) |
| primary estimand | the true-score correlation between peak speed and the player's pressure propensity; a secondary model adds weight and role, interpreted descriptively (mediator) |
| inference | player-cluster bootstrap B = 2,000; single test α 0.05; equivalence-type statement with SESOI 0.15 |
| validation before the join | synthetic planted-effect run on the real design, then a power check (expected about 0.3 at true r 0.3) |
| stated limitations | n = 53; R_y 0.50; speed ≡ weight ≡ role in DL; role is a mediator; draft-capital selection; associational only |

## 7. Decision requested

Approve **A**, and with it Phase 9B (writeup, visuals and the public notebook from existing results only). Or overrule with B (§6).
