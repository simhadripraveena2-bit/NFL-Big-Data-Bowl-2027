# Phase 18: research-branch closure and evidence audit (Phases 11–17)

**Status:** documentation and research-integrity phase only.
- No analysis was rerun or changed.
- No NFL outcome value was read and no outcome model was fitted.
- No frozen file, registered hypothesis or earlier report was edited.

**Branch closed:** the Combine **measurement-development branch** (Phases 11 Stage 1 – 17). Every result below is quoted from the original phase reports, which remain the source of record. Where this note and a phase report differ, the phase report governs.

---

## 1. Executive summary

- **What the branch asked.** After the registered confirmatory study finished, the branch looked for a new, reliable Combine movement measurement that could later be linked to NFL performance under a new pre-registration. It looked at:
  - change of direction (three-cone, short shuttle);
  - a continuous-time acceleration estimator;
  - position-specific skill drills (WR routes, DL pass rush, others).
- **What survived.** Only **WR route-launch acceleration** (Phases 15–16) is *conditionally measurable*:
  - cross-route generalizability G(10) 0.69 (cell-z);
  - largely unexplained by the official 10-yd split, 40 or tracked peak speed (≈ 11% of athlete variance);
  - only a **relative** score (−12% synthetic magnitude bias);
  - redundancy with true early-sprint acceleration is **unresolved**, because the tracked-40 reference is not test-retest reliable.
- **Why it stops there.** Phase 17 showed that a launch × separation study on the available cohort is underpowered:
  - 54 WR;
  - MDE true partial r 0.66–0.70, not reached at the H2 reliability of 0.44; power 0.14–0.29 at ρ = 0.3;
  - 53 of the 54 players were already used by H1/H2.
- **Everything else was rejected** (§7), as a construct, on reliability, or on pre-specified synthetic criteria.
- **No new combine × NFL-outcome association was computed** at any point in Phases 11–17 (§2.3 audit). The registered H1/H2 and secondary results are byte-for-byte unchanged (§2.2).
- **Decision.** The measurement branch is **closed**. No measurement is approved for outcome validation on this dataset. Any future outcome test of route launch needs independent data (§8) and a new, separately approved pre-registration.

## 2. Complete phase history

### 2.1 Phase table

Earlier phases (0–10.3) are summarised in `research_findings_summary.md` and CLAUDE.md. This table covers the closed branch and the parallel Phase 11.0/11.2 reconnaissance.

| phase | report | commit(s) | data used | decision |
|---|---|---|---|---|
| 11.0 | `phase11_research_gap_scouting.md` | 7b8ebde | literature only | no gap or novelty established; one causal-identifiability candidate kept for a formal check |
| "11.1" (causal) | same note, §§ 8–12 | 1f53c2a | literature only | candidate narrowed to shared-confounder causal-equilibrium identifiability; no implementation |
| 11.2 | `phase11_identifiability_counterexample.md` | a83736c | none (formal SCM) | baseline non-identifiability counterexample; "not a publishable contribution"; proceed only with a non-trivial positive result (none produced) |
| 11 Stage 1 | `phase11_turn_recovery_feasibility.md` | 7a474c4 | Combine three-cone; REG row **counts** only | C re-acceleration CONDITIONAL GO; C retention NO-GO; recovery times NO-GO |
| 11.1 (construct) | `phase11_1_c_reacceleration_construct_audit.md` | 7fbf4a2 | Combine only | Stage 1 window never after the turn; candidate A (late-loop speed gain) CONDITIONAL GO as measurement only, NO-GO as post-turn acceleration; candidate B NO-GO |
| 12 | `phase12_short_shuttle_acceleration_feasibility.md` | fc7fcf1 | Combine only | feature NO-GO; shuttle setting CONDITIONAL GO for method work only |
| 13 | `phase13_continuous_time_acceleration.md` | 91c923d (protocol before holdout), 15ccce8, 31d6c83 | synthetic only | Stage E FAILED; nothing frozen; no real-data stage |
| 14 | `phase14_skill_drill_research_screening.md` | 657b7ee | Combine; outcome-population **counts** only | CONDITIONAL GO (measurement only): WR route composite, DL arc bend |
| 15 | `phase15_wr_dl_measurement_validation.md` | d0a4665 (decision before holdout), 4e1afbf, 22bbc58 | Combine only | WR route launch CONDITIONAL GO; WR peak/mean speed, a_n, braking, speed ratio NO-GO; DL bend NO-GO; DL arc speed CONDITIONAL GO |
| 16 | `phase16_wr_launch_redundancy_audit.md` | 2a3fc47 (protocol before real data/holdout), 1ad525a | synthetic + Combine only | launch frozen; relative scores only; CONDITIONAL GO for one new WR pre-registration (not drafted) |
| 17 | `phase17_wr_outcome_feasibility.md` | 4700fd9 | eligibility flags, route **counts**, null flags, published aggregates | NO-GO confirmatory; CONDITIONAL GO only for an estimation-only exploratory analysis |
| 18 | this note | (this commit) | reports and git history only | branch closed |

**Naming collision:** two different notes carry the label "Phase 11.1": the causal-identifiability narrowing (commit 1f53c2a) and the three-cone construct audit (7fbf4a2). They are unrelated. In this note, "Phase 11.1" without qualification means the construct audit, as in CLAUDE.md.

### 2.2 Protection of registered findings (Task D)

Every check below was run on 2026-11-25 for this note.

| check | result |
|---|---|
| `git diff --stat b306164..HEAD` (Phase 10.3 → now) on the registered reports, `paper/`, `src/nfl_bdb/models/`, `code_freeze.json` and `research_findings_summary.md` | **no changes**. Pre-existing files changed in the branch: CLAUDE.md (status lines) and `.gitignore` (two Phase 11 Combine-only reliability figures allowed); everything else is new files |
| registered run outputs (`experiments/h1_wr_confirmatory/20261121T223645Z`, `h1_wr_robustness`, `h2_estimation/20261122T012339Z`, `secondary/20261122T015315Z`, `data/interim/confirmatory_join/20261121T135032Z`) | still present; newest file times 2026-11-21 13:51 to 2026-11-22 02:04, all before Phase 11 began (2026-11-23) |
| H1-WR primary in `h1_wr_result.json` | Δ = 0.0900 (registered 0.090); 2025 season-forward 0.219 — **unchanged** |
| H2 in `h2_result.json` | β_P = −0.0200 yd/SD (registered −0.020) — **unchanged** |
| `scripts/check_writeup_numbers.py` | 43/43 OK |
| `tests/test_code_freeze.py` (12 frozen files, SHA-256) | pass (§9) |
| pre-registration §15 deviations log | still D1–D4. Phases 11–17 are **not** protocol deviations: they test no registered hypothesis. Each report is labelled in its header as measurement-only, synthetic, or feasibility-only |

### 2.3 Outcome-firewall audit

All code added since Phase 10.3 was searched for NFL outcome columns (`separation_at_pass_forward`, `target`, `time_to_pressure`, pressure, yards, `player_play`).

| script | what it reads from `player_play` | outcome values used? |
|---|---|---|
| `run_turn_recovery_feasibility.py` (11) | `game_id`, `nfl_id` → REG row count per player | no |
| `run_c_reacc_construct_audit.py` (11.1) | nothing (docstring: no game table opened) | no |
| Phases 12, 13, 15, 16 runners | no game tables | no |
| `run_phase14_skill_screening.py` (14) | counts of rows meeting `is_not_null()` filters on `separation_at_pass_forward`, `player_get_off`, `pass_rushers_encountered`, and the categorical `coverage_assignment` (deployment); **`target` is loaded in the column list but never referenced** | no: counts only |
| `run_phase17_power.py` (17) | `is_not_null()` flag on separation; team-season counts | no: counts only |
| Phase 17 overlap check | `nfl_id` and `elig_h1` / `elig_h2` flags from the registered eligibility files | no |

**No route-launch, three-cone, shuttle, arc or other Phase 11–17 feature was ever joined to an NFL outcome value.**

## 3. Candidate decision matrix (Task B)

### 3.1 Evidence types

These are **not interchangeable** and are never pooled.

| code | evidence type | what it supports | what it does not support |
|---|---|---|---|
| **TR** | test-retest: two repeats of the *same* task by the same athlete | stability of a single measurement occasion | — |
| **LR** | left/right agreement: mirrored sides of a drill (side confounded with order) | that the athlete trait is shared across sides | test-retest reliability; side and order effects are confounded |
| **XR** | cross-route generalizability: G coefficient over *different* routes (G-study) or split-half over route sets | that a trait generalizes over a task universe | repeatability of any one route |
| **SA** | synthetic measurement accuracy: recovery of a known truth in simulation | estimator validity under the simulated mechanism | real-athlete reliability |

**Retrospective relabelling.** Phase 14 called the DL pass-rush and gauntlet agreement values "ICC". Phase 15 then showed the two attempts are left and right sides (DL: 101 of 102 pairs; gauntlet: 97–99%). Those values are **LR**, not TR. The numbers are unchanged; only the label is corrected here.

### 3.2 Matrix

| # | measurement | physical construct | operational definition | sample | evidence (type: value) | main limitation | outcome availability | final decision |
|---|---|---|---|---|---|---|---|---|
| 1 | three-cone C retention | speed kept through the C loop | speed-retention ratio through the detected C segment (Phase 11 template; ≈ minimum speed, ρ 0.97) | 193 valid attempts / 155 athletes; 34 with 2 valid | TR: 0.49 [0.13, 0.72] | trades off with re-acceleration within athlete (ρ −0.72); pairs are a selected subgroup | none joined | **NO-GO** |
| 2 | three-cone R1/R2 recovery times | time to regain speed after touch reversals | time to recovery_frac × entry speed | as #1 | TR: 0.28–0.64, processing-sensitive (v_stop, speed source) | R1 90% censored | none joined | **NO-GO** |
| 3 | three-cone "C re-acceleration" = **late-loop speed gain** (11.1 candidate A) | speed gained in the 2nd half of the C loop | Stage 1 0.5-s window after the C apex (inside the turn: 61% wholly, rest partly) | 34 TR pairs | TR: 0.64 [0.42, 0.81]; within-position 0.60 | **not post-turn acceleration**: 56% of squared acceleration is centripetal; within-athlete ρ with centripetal share −0.94 | none joined | measurement-only CONDITIONAL GO; **closed** with the branch |
| 4 | three-cone post-exit slope (candidate B) | acceleration after leaving the turn | a_t slope after detected exit | 26 TR pairs | TR: 0.34 [−0.02, 0.64] | still curving ~48 deg/s after exit; no straight phase exists | none | **NO-GO** |
| 5 | short-shuttle straight-exit acceleration | linear re-acceleration after a 180° reversal | mean a_t in a straight post-R1 window (≤ 15° heading change) | 211 valid R1 / 163 athletes; 37 TR pairs | TR: R1 0.46 pooled, **0.21 within position**; R2 −0.24 | value driven by 10-Hz window-start timing (~0.8 yd/s² per frame ≈ between-athlete SD) | none | **NO-GO** (feature) |
| 6 | continuous-time acceleration (E1–E3) | sampling-robust post-turn a_t | E1 Phase 12; E2 sub-frame exit; E3 cubic smoothing spline, λ = 1e-4, a_t over [exit+0.2, exit+0.7] | synthetic, held-out seeds 2001–2003 | SA: R_meas 0.68 / 0.69 / 0.63–0.73 vs required ≥ 0.80; coverage 0.46–0.62 | step-frequency oscillation and position noise, not sampling phase, limit accuracy | none (never run on real data) | **FAILED** pre-specified criteria |
| 7 | WR route peak / mean speed | top speed expressed in routes | per-route peak / mean of SG speed; G-study | 107 WR, 1,286 attempts | XR: peak G10 0.40 (leave-one-route-out 0.07–0.52) | route-dependent; not a stable athlete trait | separation (not joined) | **NO-GO** |
| 8 | WR route a_n, braking | turning / deceleration in routes | per-route centripetal and braking a_t percentiles | as #7 | XR: a_n p95 G10 0.34 raw / 0.47 cell-z; braking p05 G10 0.04 | route geometry dominates | not joined | **NO-GO** |
| 9 | WR speed-expression ratio | route speed relative to sprint speed | route peak / tracked-40 peak | as #7 | XR: G10 0.71, **but 59% from the tracked-40 denominator** | ratio inherits a reliable constant | not joined | **NO-GO** |
| 10 | WR route composite (Phase 14) | general route-movement quality | z-composite over routes | ~107 WR | XR (split-half over route sets): 0.55–0.66 | superseded by the Phase 15 G-study, which separates the components | not joined | superseded by #11 |
| 11 | **WR route launch** (frozen, Phase 16) | early acceleration out of the route start | p95 of a_t over 1.0 s from the first frame > 1 yd/s (SG7); route × year cell-z; athlete mean (≥ 8 routes) | 107 WR, 1,252 valid attempts; 54 outcome-eligible | XR: G10 0.65 raw / **0.69 cell-z** (LORO 0.62–0.73), G(8) 0.64; SA: onset +0.04 s, rank 0.95, **magnitude −12%** | relative score only; redundancy with true early-sprint acceleration unresolved (tracked-40 launch TR 0.02–0.18) | separation: 54 WR, 53 reused from H1/H2; Phase 17 MDE 0.66–0.70 | CONDITIONAL GO as a **measurement only**; outcome study **NO-GO** on this data |
| 12 | WR gauntlet steady speed | speed kept while catching | median speed within ≥ 80% of attempt peak | 107 WR, 93 pairs | **LR** (mirror directions, 97–99%): 0.70 (year-centred 0.64) | balls untracked; pacing set by throwers; construct unclear | not joined | not pursued (Phase 14 rank 3); **closed** |
| 13 | DL pass-rush arc bend | ability to turn tightly at speed | arc curvature / radius / median a_n | 114 athletes; 101 L/R pairs | **LR**: 0.14–0.31 (Phase 14 "ICC 0.49" relabelled LR); SA: smoothing error 7–10%, geometry-dependent | sides confounded with order (right first 109/114); speed–curvature coupling | pressure / get-off counts only | **NO-GO** |
| 14 | DL arc speed (SG-corrected) | speed carried through the arc | analytic SG-corrected speed on the arc | as #13 | SA: error ≈ 0.4%; **LR**: 0.41 [0.28, 0.54] (year-centred 0.36) | side/order confound; overlaps sprint speed (ρ −0.70 with the forty for peak speed) | not joined | measurement-only CONDITIONAL GO; **closed**, not "bend" |
| 15 | DL run-the-hoop loop a_n | bend in a circular loop | left vs right loop a_n within one attempt | 109 | **LR / within-attempt split**: 0.41 [0.26, 0.55] | loops not equivalent (speed differs by 0.98 yd/s) | not joined | not pursued; **closed** |
| 16 | other Phase 14 drills (OL drop/mirror/wave, DB 45°, DB line, TE) | various | Phase 14 definitions | 93–125 per drill | DB 45° pooled 0.90 → **year-centred 0.09**; DB line attempts are different variants; OL reactive partner untracked | layout/year artefacts; untracked stimuli | not joined | **NO-GO** / not pursued |

## 4. Measurement lessons

1. **Name the evidence type.** TR, LR, XR and SA answer different questions (§3.1). A mirrored-side agreement is not a test-retest reliability, and a synthetic accuracy is not a real-athlete reliability.
2. **Check what a window actually covers.** The three-cone "re-acceleration" window was never after the turn (11.1). Verify a window's geometry (heading change, centripetal share) before naming its construct.
3. **10-Hz timing can dominate acceleration features.** A one-frame shift of a short window moves shuttle acceleration by about one between-athlete SD (12). Synthetic sampling phase was not the main error source, but step oscillation and noise were (13).
4. **Standardise by year (and route).** Drill layouts change across Combine years. Pooled ICCs can be pure layout artefacts (DB 45°: 0.90 → 0.09), so always report year-centred values (14).
5. **Within-position reliability is the relevant one.** Pooled values are inflated by position differences (shuttle 0.46 → 0.21).
6. **Ratios to reliable constants inflate generalizability.** The WR speed-expression ratio's G10 0.71 is mostly its tracked-40 denominator (15).
7. **Smoothing biases curve measures.** SG(2) attenuates speed and a_n on tight curves; the analytic SG speed correction is valid for speed on uniform circles but not for curvature or a_n on real arcs (15).
8. **Freeze before holdout.** Phases 13, 15 and 16 committed their protocols or decisions before the held-out or real-data stage, and Phase 13 accepted its failure. Keep doing this.
9. **A reference must itself be reliable.** Redundancy of route launch with early-sprint acceleration could not be settled, because the tracked-40 first-second acceleration has TR 0.02–0.18 (16).
10. **Repeaters are selected.** Athletes with two valid attempts differ from the rest (~0.3 SD faster in the three-cone): TR estimates describe a subgroup (11.1).

## 5. Statistical power limitations

- **Players, not plays, limit power.** This held throughout:
  - H1-WR MDE Δρ ≈ 0.30;
  - H2 MDE partial r ≈ 0.6;
  - Phase 17 launch × separation MDE 0.66–0.70 at n = 54;
  - about 250 WR needed for 80% power at true partial 0.3.
- **Outcome reliability has a ceiling.** The separation reliabilities are reconciled in Phase 17 §3:
  - Phase 3's 0.61 = player + team-season;
  - 0.44–0.45 = player-only;
  - team-season variance ≈ 1.1 × player variance caps the player-only reliability at about 0.63 for this cohort, whatever the exposure.
- **Predictor reliability.** Combine drills offer 1–2 attempts. Only cross-route designs (WR, G(8) 0.64) reach moderate generalizability. Attenuation √(R_x R_y) ≈ 0.5–0.6 halves observable effects.
- **Selection.** Only about 59% of measurable WR reach 100 thrown routes. Exposure is earned, so the eligible cohort is range-restricted (Phase 17: about 15% downward bias of the corrected estimate under λ = 0.3).
- **Cohort reuse.** The 2023–2025 Combine classes with NFL tracking are one cohort. They have been used by H1/H2 and cannot provide an independent confirmation.

## 6. Current approved research questions

No new research question was approved in Phases 11–18. The approved and completed questions are the registered ones (pre-registration v1.0 with D1–D4):

| question | role | registered result |
|---|---|---|
| H1-WR: combine speed translates more on deep than short routes | sole primary | **inconclusive** (Δ 0.090, 95% CI [−0.089, 0.400], p 0.211) |
| H2: combine peak speed adds to the 40 for WR deep separation | secondary, estimation | **inconclusive**; β_P −0.020 yd/SD [−0.101, 0.063] |
| Holm family {H1-DB, H1-DL(a), H1-DL(b), H5(b)} | secondary | H1-DL(b) supported (Holm p 0.032, adjustment-sensitive, no causal reading); H1-DL(a) falsified; H1-DB, H5(b) inconclusive |
| H5(a)/(c), H1-global; TE | estimation; descriptive | as reported in `secondary_family_results.md` |

The submission package (Phase 9B–10.3) is still awaiting the lead's final review. It is **not submitted**, and Phases 11–18 do not change it.

## 7. Rejected research directions (Task C)

Each direction below is closed. Reopening one needs a new, separately approved protocol.

1. **Three-cone late-loop speed gain is not post-turn acceleration.** The Stage 1 window lies inside the C turn in every attempt (61% wholly). About 56% of squared acceleration is centripetal. The athlete's value mirrors the centripetal share (within-athlete ρ −0.94). The three-cone has no straight post-turn phase. Post-exit slope is unreliable (TR 0.34).
2. **Short-shuttle acceleration is not sufficiently repeatable.** R1 TR 0.46 pooled, 0.21 within position; R2 −0.24. The value is driven by 10-Hz window-start timing.
3. **Continuous-time acceleration estimation did not pass its synthetic validation criteria.** Held-out R_meas 0.63–0.73 against a required ≥ 0.80; coverage 0.46–0.62. Nothing was frozen and no real-data stage was run.
4. **DL pass-rush bend is not sufficiently reliable.** Curvature, radius and a_n reach LR agreement of only 0.14–0.31, with 7–10% geometry-dependent smoothing error. The two attempts are mirrored sides confounded with order, so no TR exists. Arc speed (LR 0.41) is a speed measure, not bend.
5. **WR route-launch acceleration is conditionally measurable but not sufficiently validated as an independent athletic capacity.**
   - XR G10 0.69 and SA rank recovery 0.95 support a *relative drill score*.
   - The −12% magnitude bias rules out absolute values.
   - Without a reliable early-sprint reference it cannot be shown to be distinct from linear acceleration capacity.
   - It is **not** a new capacity.
6. **The proposed WR route-launch × separation study is underpowered and reuses the existing H1/H2 cohort.** 54 eligible WR (53 in H1/H2); MDE true partial r 0.66–0.70; power 0.14–0.29 at ρ = 0.3. Phase 17's optional estimation-only CONDITIONAL GO is **not taken up**: this closeout recommends against running it on the current data.
7. **Also closed:**
   - WR route peak/mean speed, a_n and braking, and the speed-expression ratio (NO-GO, Phase 15);
   - WR gauntlet and DL run-the-hoop (not pursued);
   - OL and DB skill drills (layout artefacts, untracked stimuli, variant mismatch).
   - The Phase 11.0/11.2 causal-identifiability track produced no positive result. It stays closed together with the algorithmic track (Phase 8C).

## 8. Requirements for independent future validation

Each future outcome validation of route launch, or any surviving Combine drill measure, would need all of the following:

1. **Independent athletes.** Combine classes not used by H1/H2: 2026 onward, with Combine route-drill tracking, followed by NFL thrown-route tracking. About 18 eligible WR per class. **About 250 WR (about 11–14 classes)** are needed for 80% power at true partial 0.3. A first replication sample (about 50–60 WR from 3 new classes) is useful for estimation only.
2. **League-wide tracking** (all 22 players and the ball) to adjust separation for defender assignment, coverage and quarterback / team-season effects. This would lower the team-season share and raise the player-only reliability above the ~0.63 ceiling.
3. **A reliable early-sprint reference.** Either multiple tracked 10-yd starts per athlete or a timing-gate 0–5 yd split, to settle whether launch is redundant with linear acceleration.
4. **More repeats.** Repeated same-side drill attempts for test-retest (not mirror sides), in a fixed and documented layout per year.
5. **A new pre-registration**, written and approved before any join:
   - estimand as in Phase 17 §5;
   - R_x and R_y declared in advance;
   - player-level inference, team-season sensitivity and selection modelling.
   - The frozen Phase 16 launch definition (`configs/phase16_protocol.json`, `src/nfl_bdb/features/launch.py`) is reused unchanged.

## 9. Final research status

- **Measurement-development branch (Phases 11–17): CLOSED.** No measurement is approved for outcome validation on this dataset. Route launch is recorded as a conditionally measurable, relative WR drill score. Every report, result and run directory is preserved unchanged.
- **Registered confirmatory study: complete and unchanged.**
  - H1-WR inconclusive;
  - H2 inconclusive (estimation);
  - H1-DL(b) supported with adjustment-sensitivity caveats;
  - code freeze intact (12/12);
  - deviations log D1–D4 only.
- **Algorithmic track:** closed (Phase 8C). **Causal-identifiability scouting:** closed with no positive result (11.0/11.2).
- **Submission:** package built and public code/notebook released (10.3). The Writeup has not been created on Kaggle, and the entry is not submitted, pending the lead's final review.
- **Verification for this phase:**
  - full test suite: 106 passed, including `tests/test_code_freeze.py`;
  - writeup number checker: 43/43.
- **Next step:** the lead's decision on the final submission. No new analysis is authorized.
