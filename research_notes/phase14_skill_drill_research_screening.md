# Phase 14: position-specific Combine skill drills (data and measurement screening)

**Run:** `20261125T004703Z`, produced by `scripts/run_phase14_skill_screening.py`. Settings: seed 1414; player bootstrap B = 1000; Savitzky–Golay windows 5, 7 (reference) and 9.

**Code:**
- `src/nfl_bdb/features/skill_drills.py`: descriptors, curve metrics, ball-phase parser, alias map;
- `tests/test_skill_drills.py`: 4 tests;
- full suite 87/87 passing, including the code-freeze test.

**Outputs (git-ignored):**
- player and attempt level: `data/interim/phase14_skill/<run>/`;
- aggregates: `experiments/phase14_skill/<run>/` (`inventory.csv`, `alias_check.csv`, `ball_phase_by_drill.csv`, `repeatability_generic.csv`, `repeatability_candidates.csv`, `cross_route_consistency.csv`, `redundancy_generic.csv`, `outcome_counts_by_drill.csv`).

**Scope:**
- No predictive model was fitted, and no combine-feature × NFL-outcome association was computed.
- The game side was used only to **count** eligible regular-season plays per player; no outcome value was aggregated.
- No feature was tuned on outcomes.
- Nothing from Phases 11–13, the registered analyses or the frozen files was changed.
- No novelty is claimed.

## 1. Dataset inventory

### 1.1 Coverage

**Drill families:**
- 6 drill families (`SKILL_DRILLS_{WR,TE,OL,DL,DB,LB}`), 5,091 player attempts, 55 drill-name × family combinations.
- `SKILL_DRILLS_LB` holds 37 attempts by 4 DL-listed athletes (2023 only); it is too small to use.
- Each family is performed only by its own combine position. LB drills are the exception: those athletes are DL in `combine_results`.

**Recording quality:**
- Every frame gap is 100 ms, and no speed exceeds 12.5 yd/s.
- No attempt is too short (< 9 frames).
- **Recordings start at rest** (start speed ≥ 1 yd/s in 0–27% of attempts, depending on drill).
- **Recordings end while the athlete is still moving in 97–100%** of attempts. The ends are truncated, so whole-drill times cannot be computed from tracking.

**Athletes per family and draft year:**

| family | 2023 | 2024 | 2025 |
|---|---|---|---|
| WR | 39 | 31 | 37 |
| TE | 12 | 13 | 17 |
| OL | 37 | 46 | 38 |
| DL | 33 | 37 | 44 |
| DB | 35 | 50 | 37 |

### 1.2 Drills, attempts and repeats

Attempts per athlete are given as counts of athletes with 1/2/3/4+ attempts.

| family | drill (harmonised) | years | attempts | athletes | attempts per athlete 1/2/3/4+ | median frames (5th–95th percentile) | ball rows |
|---|---|---|---|---|---|---|---|
| WR | GAUNTLET_DRILL | 23–25 | 200 | 107 | 14/**93**/0/0 | 91 (85–98) | 0 |
| WR | 12 route drills (COMEBACK, CURL, DAGGER, GO, OVER_SHOULDER_ADJUST, POST_CORNER_R, RED_ZONE_FADE, SLANT, SLOT_SAIL, SLOT_STRIKE, SPEED_OUT, POST_CORNER_L 23–24) | 23–25 | 80–124 each | 70–107 each | mostly 1; 2 attempts for 1–17 athletes | 43–72 | 2025 only |
| WR | CIRCUS_ROUTE_LEFT | 25 | 43 | 37 | 31/6 | 56 | 2025 |
| TE | GAUNTLET_DRILL | 23–25 | 81 | 41 | 1/**40** | 90 | 0 |
| TE | CORNER_ROUTE | 23–25 | 61 | 30 | 1/28/0/1 | 69 | 2025 |
| TE | 6 other route/catch drills, BLOCK_EXPLOSION | 23–25 | 35–46 each | 28–42 | mostly 1 | 42–64 | 2025 |
| OL | PASS_RUSH_DROP | 23–25 | 239 | 120 | 2/**117**/1 | 44 | 0 |
| OL | PASS_PRO-MIRROR, FIVE_YARD_WAVE, SCREEN, 3 PULL drills | 23–25 | 93–121 each | 93–121 | 1 | 38–154 | 0 |
| DL | PASS_RUSH_DRILL | 23–25 | 217 | 114 | 12/**101**/1 | 45 | 0 |
| DL | RUN_THE_HOOP_DRILL | 23–25 | 119 | 109 | 99/10 | 76 | 0 |
| DL | BODY_CONTROL, FOUR_BAG, FRONT_START_WAVE, RUN_AND_CLUB | 23–25 | 112–113 | 111–112 | 1 | 57–116 | 0 |
| DL | BACK_PEDAL_AND_REACT | 23–25 | 58 | 55 | 52/3 | 106 | 0 |
| DL | SHORT_ZONE_BREAKS (23–24) vs SHORT_ZONE_BREAK_{FLAT_WHEEL, FORWARD, INSIDE} (25) | — | 105 vs 18–20 each | 36 vs 18–20 | 2023–24: 3 attempts = 3 variants | 53–137 | 0 |
| DB | BACK_PEDAL_AND_TRANSITION_45 | 23–25 | 241 | 122 | 3/**119** | 98 | 0 |
| DB | LINE_DRILL | 23–25 | 217 | 118 | 19/**99** | 70 | 0 |
| DB | BOX, W, GAUNTLET, 90° BREAK, TERYL_AUSTIN_1/2 | 23–25 | 103–125 | 101–122 | 1 | 67–102 | 0 |

### 1.3 Aliases

**Merging rule (fixed before looking at the results):** two names are merged only if the median duration, path length and both extents agree within 15%.

| alias → canonical | duration | path | major extent | minor extent | decision |
|---|---|---|---|---|---|
| LINE (2023) → LINE_DRILL (DB) | 1.04 | 1.15 | 1.14 | 1.05 | merged (verified) |
| PASS_PRO_MIRROR_DRILL (2023) → PASS_PRO-MIRROR_DRILL (OL) | 1.07 | 1.08 | 1.00 | 0.98 | merged (verified) |
| OVER_THE_SHOULDER_ADJUST (2023) → OVER_SHOULDER_ADJUST (TE) | 0.99 | 1.12 | 1.12 | **1.18** | merged in the code, but fails the rule; TE drill not used further |
| SPEED_OUT_LEFT (2024) → SPEED_OUT_ROUTE_LEFT (WR) | 1.07 | 1.04 | 1.01 | 1.15 | merged in the code, but borderline (minor-extent ratio 1.15); in the route composite it is standardised within route × year |

**Not merged** (different tasks):
- **DL SHORT_ZONE_BREAKS (2023–24) vs the three 2025 SHORT_ZONE_BREAK variants.** Medians differ (duration 7.3 vs 5.8–11.4 s; path length 39 vs 30–65 yd), and the 2023–24 attempts are the three variants under one name.
- **WR POST_CORNER_ROUTE_LEFT (23–24) vs _RIGHT.** These are mirror routes of different depth (path 32 vs 53 yd).

### 1.4 Ball tracking

**Availability:**
- BALL rows exist **only in 2025**, only for WR and TE catching drills: 551 of the 712 2025 WR/TE attempts. There are none for the gauntlets, and none in 2023–24.

**Linkage is clean at record level:**
- Every BALL row shares its attempt's `event_id`, its `nfl_id` (the receiver) and an exact player timestamp.
- No ball event lacks a player event.

## 2. Representative trajectory findings

Trajectories were inspected per drill in plots kept in a private scratchpad, never committed.

| family | what the coordinates show |
|---|---|
| WR routes | Release, stem and break geometry are clear and consistent within a route (e.g. slot strike: a sharp ~160° stop-and-return; comeback: deep stem then a 140° break back). Routes are run at 6–10 yd/s peak. Facing direction is not recorded (no `o`) |
| WR/TE gauntlet | A ~50 yd straight lateral run across the field at near-constant 8–9 yd/s while catching successive balls (balls not tracked) |
| WR/TE ball (2025) | The ball sits at the passer, flies at about 14–22 yd/s (median 18.6) for 1–3 s on deep throws, then joins the receiver. **But:** contact is ambiguous; the ball position often "teleports" 2–5 yd at or just after contact; some balls never reach the receiver |
| DL pass rush | A short curved start (~2–3 yd radius arc around a bag) then a ~15 yd straight sprint |
| DL run-the-hoop | A figure-8 around two hoops (radius about 1.8 yd) at about 3.2 yd/s. Clear left and right loops |
| DL other | Wave/lateral-reaction, four-bag and body-control drills: short shuffles and redirections led by a coach; the coach is not tracked |
| OL mirror / wave | Lateral shuffles of about 3 yd reacting to a partner or coach (not tracked), then a sprint out |
| OL pass-rush drop | A short drop or turn, then a ~10 yd run; two attempts = two sides |
| DB 45° transition, 90° break, W, box, Teryl Austin | Backward-then-forward runs with breaks. **Backpedal cannot be distinguished from forward running** (no orientation); only path direction is observed. Layouts differ between years (Section 5) |
| DB line | A long straight run with small weaves; the two attempts are not the same variant (Section 5) |

## 3. Candidate movement measurements

All quantities come from Savitzky–Golay-smoothed positions. The vendor `a` and `dis` channels are not used.

| quantity | definition | drill relevance | measurable? |
|---|---|---|---|
| peak and mean moving speed | max / mean of \|v\| (frames ≥ 1 yd/s) | speed expressed in the task | yes; truncated ends can cut the run |
| tangential acceleration bursts | 95th / 5th percentile of d\|v\|/dt | acceleration and braking in breaks | yes, but noisy (Phases 11–13) |
| **centripetal acceleration in curves ("bend")** | a_n = \|v\|·\|ω\| on frames with \|v\| ≥ 2 yd/s and \|ω\| ≥ 60°/s; median a_n, median speed, radius \|v\|/\|ω\|, and left vs right turning | edge "bend" (DL pass-rush arc, hoop); route breaks | yes. SG smoothing **attenuates speed on tight curves**: about −5% at R = 2 yd, v = 4 yd/s, window 7; larger windows attenuate more (unit test). Hoop median a_n is 5.44 / 5.31 / 5.14 yd/s² at windows 5 / 7 / 9 |
| heading change, axis reversals, lateral extent | integrated \|ω\|; sign changes of the along-axis velocity; minor-axis range | path geometry, shuffles | yes, but dominated by drill layout |
| gauntlet steady speed and speed CV | median speed (and CV, minimum/peak) between the first and last frame ≥ 80% of the attempt's peak | keeping speed while catching | yes (no ball data) |
| **WR route composite** | each route measure z-scored within route × draft year, averaged over an athlete's routes | route-running speed and bend across many routes | yes; a generalisability measure, **not test-retest** |
| catch-phase measures (approach, adjustment, catch) | throw = start of ball flight; contact = first ball–receiver distance ≤ 1 yd; held ≥ 5 frames; flagged if the ball jumps > 25 yd/s near contact | body adjustment to the ball | **not reliably.** Only 9.8% of 551 ball attempts give an unambiguous catch phase: contact found 89%, flight ≥ 3 frames 41%, held 43%, ball jump near contact 22%, any ball jump in the attempt 56%. 2025 only |
| pass-protection mirror / reaction | lateral shuffle speed and reversals | pass sets | the partner/coach is not tracked, so reaction cannot be separated from the stimulus; one attempt each |

## 4. Measurement limitations

1. **Sampling rate (10 Hz).**
   - Acceleration-type quantities are fragile (Phases 11–13).
   - Curve quantities need ≥ 5 qualifying frames.
   - Tight curves are attenuated by smoothing (Section 3).
2. **No orientation.** Backpedal, facing and hip turns are not observable, so DB "transition" measures are path-based only.
3. **No event markers.** Catch, contact and start cues are inferred. The ball position is discontinuous near contact.
4. **Untracked stimuli.** Coaches, partners, bags and hoops are not tracked. Their positions vary between years (Section 5).
5. **Truncated ends.** 97–100% of recordings end mid-run, so total drill times cannot be computed.
6. **Repeats are often not equivalent.**
   - In two-attempt drills the attempts are usually mirror sides (pass-rush drill 92%, DB 45° 100%, gauntlet 97–99%).
   - DB line-drill attempts are different variants: duration and path ICC are negative.
   - DL short-zone breaks are three different variants.
7. **Ball data:** 2025 only, about 30–38 WR per route. 2025 draftees also have only one NFL season.

## 5. Repeatability (first two attempts in chronological order; player bootstrap 95% CI)

**Layout check:** drill layouts change between years, so **every ICC is also reported year-centred** (both attempts centred on the draft-year mean). This guards against the inflation that position differences caused in earlier phases.

### 5.1 Generic descriptors in designed-repeat drills (window 7)

| drill (pairs) | peak speed | mean moving speed | bend a_n p95 | duration | note |
|---|---|---|---|---|---|
| WR gauntlet (93) | 0.57 → **0.53** | 0.65 → **0.56** | 0.16 → 0.09 | 0.39 → 0.36 | sides mirrored 99% |
| TE gauntlet (40) | 0.62 → 0.62 | 0.78 → **0.77** | 0.58 → 0.54 | 0.89 → 0.30 | |
| DL pass-rush drill (102) | 0.62 → **0.60** | 0.39 → 0.31 | 0.45 → **0.42** | 0.22 → 0.13 | sides mirrored 92% |
| OL pass-rush drop (118) | 0.56 → 0.51 | 0.16 → 0.15 | 0.13 → 0.06 | 0.04 → 0.02 | |
| DB 45° transition (119) | 0.57 → 0.51 | 0.38 → **0.00** | 0.66 → **0.02** | **0.90 → 0.09** | pooled ICC is a year/layout artefact |
| DB line drill (99) | 0.49 → 0.40 | 0.51 → 0.37 | 0.12 → 0.03 | −0.27 → −0.27 | attempts are different variants |
| DL short-zone breaks (35) | 0.29 → 0.23 | 0.24 → 0.07 | 0.24 → 0.18 | 0.21 → −0.11 | 3 variants, not repeats |
| TE corner route (29) | 0.63 → 0.54 | 0.36 → 0.11 | 0.42 → 0.25 | 0.30 → −0.14 | |
| WR speed-out (17) / post-corner R (15) | 0.44 / 0.57 | 0.61 / 0.54 | ≈ 0 / 0.48 | — | too few pairs |

**Reading:**
- **Smoothing:** the window (5 vs 7 vs 9) changes these ICCs by ≤ 0.07 and rank agreement is ≥ 0.92 everywhere.
- **Year-centring:** removes most of the DB 45° and TE-gauntlet-duration "reliability".

### 5.2 Candidate-specific measures

| candidate | measure | athletes (pairs) | ICC(3,1) [95% CI] | year-centred | windows 5 / 9 | TE % | note |
|---|---|---|---|---|---|---|---|
| **WR gauntlet** | steady speed | 107 (93) | **0.70 [0.56, 0.80]** | 0.64 | 0.69 / 0.70 | 2.3 | |
| WR gauntlet | speed CV | 107 (93) | 0.54 [0.29, 0.71] | 0.45 | 0.54 / 0.56 | 29 | |
| TE gauntlet | steady speed | 41 (40) | 0.77 [0.59, 0.87] | 0.76 | 0.77 / 0.77 | 1.7 | small n |
| DB gauntlet | steady speed | 119 (4) | — | — | — | — | single attempts |
| **DL pass-rush arc** | median bend a_n (yd/s²) | 107 (75) | **0.49 [0.34, 0.63]** | 0.44 | 0.43 / 0.51 | 5.2 | ≥ 5 curve frames needed; 183/217 attempts qualify |
| DL pass-rush arc | median curve speed | 107 (75) | 0.49 [0.31, 0.65] | 0.43 | 0.49 / 0.50 | 6.0 | |
| DL pass-rush arc | curve radius | 107 (75) | 0.39 [0.21, 0.57] | 0.34 | 0.42 / 0.37 | 9.2 | |
| DL run-the-hoop | bend a_n | 109 (10) | 0.46 [−0.19, 0.66] | 0.34 | 0.37 / 0.54 | 3.9 | only 10 repeats |
| DL run-the-hoop | left vs right loop a_n, within one attempt | 109 | 0.41 [0.26, 0.55] | — | — | 5.7 | split-half, not test-retest; left − right speed differs by 0.98 yd/s, so the loops are not equivalent halves |

### 5.3 Cross-route consistency (WR; generalisability across different route drills, NOT test-retest)

**Method:** route values are z-scored within route × year. Athletes need ≥ 6 routes (median 12). Each athlete's routes are randomly split in half 500 times, and the half correlation is Spearman–Brown corrected.

| WR route composite | athletes | split-half reliability, median [2.5–97.5% of splits] | ρ with forty | ρ with 10-yd | ρ with 3-cone | ρ with shuttle |
|---|---|---|---|---|---|---|
| peak speed | 106 | **0.55** [0.41, 0.65] | −0.20 | −0.04 | −0.41 | −0.12 |
| tangential acceleration p95 | 106 | **0.66** [0.57, 0.75] | −0.14 | −0.16 | −0.30 | −0.28 |
| bend a_n p95 | 106 | 0.47 [0.31, 0.59] | 0.02 | −0.02 | −0.15 | −0.13 |
| mean moving speed | 106 | 0.35 [0.16, 0.50] | −0.21 | 0.02 | −0.39 | −0.14 |
| braking p05 | 106 | 0.13 [−0.13, 0.35] | 0.05 | 0.19 | 0.06 | 0.18 |

TE route composites (29 athletes, median 7 routes): reliability −0.02 to 0.54, too few athletes.

### 5.4 Overlap with generic combine speed (player means, Spearman; descriptive only)

| candidate | ρ with forty / 10-yd / 3-cone / shuttle |
|---|---|
| WR gauntlet steady speed | −0.07 / −0.10 / −0.09 / −0.14 |
| DL pass-rush arc bend a_n | −0.50 / −0.39 / −0.57 / −0.49 |
| DL pass-rush peak speed | −0.70 / −0.57 / −0.67 / −0.53 |
| DL hoop bend a_n | −0.45 / −0.37 / −0.39 / −0.33 |

**Interpretation:**
- **Low overlap is not proof of new information.** The WR gauntlet and route composites barely overlap with the forty, but that may mean they reflect effort, pacing or drill execution rather than athletic capacity.
- **DL bend partly overlaps with speed and agility.** About a quarter to a third of its rank variance is shared with the forty and three-cone.

## 6. Outcome availability and matching counts (counts only)

**Eligible-play definitions** (REG season only; combine position):

| position | eligible plays | outcome-defined plays |
|---|---|---|
| WR/TE | routes on pass plays | routes with separation at pass forward (all thrown routes, targeted or not). Targets per route uses all routes |
| DL | pass-rush snaps with a get-off value | the same snaps; pressure = `time_to_pressure` non-null |
| OL | pass-block snaps (`pass_rushers_encountered` non-null) | the same snaps; pressure allowed |
| DB | coverage snaps (MAN or zone; rushers and prevent excluded) | **none attributable** to the DB, so these snaps are deployment only. The only attributable DB performance is run-play tackling. Coverage outcomes would need the nearest-defender reconstruction (≈ 4.8k plays, exploratory) |

**Drill participants with ≥ 100 outcome-defined REG plays** (≥ 50 in brackets):

| drill | participants | any REG plays | ≥ 100 (≥ 50) | ≥ 100 by draft year 2023 / 2024 / 2025 |
|---|---|---|---|---|
| WR gauntlet | 107 | 83 | **63** (69) | 29 / 19 / 15 |
| WR route drills (each) | 70–107 | 60–83 | 48–63 | e.g. slant 29 / 19 / 15 |
| WR circus (2025 only) / WR with 2025 ball data | 37 | 23 | 15 (17) | 0 / 0 / 15 |
| TE drills | 28–42 | 21–33 | 11–21 | ≤ 8 per year |
| DL pass-rush drill | 114 | 95 | **60** (73) | 20 / 23 / 17 |
| DL run-the-hoop | 109 | 90 | 57 (69) | 19 / 22 / 16 |
| OL drills | 93–121 | 71–89 | 53–66 | ≈ 20–23 per year |
| DB drills | 101–122 | 75–91 | 55–67 coverage snaps (no attributable outcome) | — |

**Whole position populations with ≥ 100 outcome-defined plays:** WR 63, TE 21, DL 63, OL 66, DB 67 (deployment only).

**Statistical implication:** with about 60 matched athletes per position, any later outcome study could detect only correlations of about |r| ≥ 0.36 (80% power, two-sided α = 0.05) before measurement attenuation. Nothing was computed here.

## 7. Candidate ranking

Each row is scored on measurement quality, number of athletes, number of repeats, football relevance, outcome compatibility, and potential beyond generic speed.

| rank | candidate | measurement | athletes | repeats | relevance | outcome link | beyond sprint? |
|---|---|---|---|---|---|---|---|
| **1** | **WR route-drill composite** (peak speed, acceleration bursts and bend across ~12 routes) | robust; standardised per route × year; no event markers needed | 106 | none (generalisability 0.47–0.66 instead) | high (route running) | separation and targets per route: 63 with ≥ 100 routes | ρ with forty −0.14 to −0.20; may be effort or pacing |
| **2** | **DL pass-rush drill arc bend** (median a_n, curve speed) | ICC 0.49 (year-centred 0.44), window-robust; smoothing attenuates tight curves | 107 | 75 pairs | high (edge bend) | pressure and get-off: 60 with ≥ 100 rush snaps | partial (ρ −0.39 to −0.57 with sprint and agility) |
| 3 | WR gauntlet steady speed | ICC 0.70 (year-centred 0.64), robust | 107 | 93 pairs | moderate (speed while catching; no ball data) | weak conceptual link to separation | ρ with forty −0.07, but construct unclear (pacing set by throwers?) |
| 4 | DL run-the-hoop bend | only 10 repeats; left/right split 0.41 | 109 | 10 | high | 57 | partial |
| 5 | OL pass-rush drop / mirror / wave | low ICC except peak speed; reactive partner untracked | 120 | 117 pairs (drop) | moderate | pressure allowed: 66 | — |
| 6 | WR/TE catch-phase (ball) | catch phase identifiable in 9.8% of attempts; 2025 only | ≈ 30–38 per route | ≈ 0 | high | 15 with ≥ 100 routes | — |
| 7 | DB drills | year/layout artefacts (45°: 0.90 → 0.09 year-centred); line-drill attempts are different variants; no orientation | 122 | 99–119 pairs | moderate | none attributable | — |
| 8 | TE drills | small n (≤ 42) | ≤ 42 | 28–40 pairs | moderate | 21 | — |
| 9 | DL short-zone breaks | 3 variants; name changed in 2025 | 36 + 20 | not repeats | low | 25 + 7 | — |

## 8. GO / CONDITIONAL GO / NO-GO

| candidate | decision | reason |
|---|---|---|
| **WR route-drill composite** | **CONDITIONAL GO for deeper measurement work** | Large sample, many routes per athlete, cross-route consistency 0.55–0.66 for peak speed and acceleration bursts, little overlap with the forty, and direct relevance to route running. Conditions: (i) it is generalisability, not test-retest; (ii) effort and pacing must be separated from capacity before interpretation; (iii) standardise within route × year; (iv) bend and braking components are weaker (0.47; 0.13) |
| **DL pass-rush arc bend** | **CONDITIONAL GO for deeper measurement work** | True repeats (75 pairs), moderate repeatability (0.49, year-centred 0.44), window-robust, football-relevant. Conditions: model the arc geometry explicitly (bag position unknown); report the smoothing attenuation of a_n; handle left/right sides; overlaps partly with speed and agility |
| WR/TE gauntlet steady speed | **NO-GO as a candidate now (exploratory only)** | Repeatable, but the construct (athlete pace vs passer timing) cannot be established without ball data, and the link to an outcome is weak |
| DL run-the-hoop bend | NO-GO for now | Only 10 test-retest pairs; loops not equivalent |
| WR/TE catch-phase / body adjustment | **NO-GO** | Catch phase identifiable in 9.8% of attempts; ball discontinuities; 2025 only (about 15 athletes with outcomes) |
| OL drills | NO-GO | Reactive stimulus untracked; low repeatability of everything except peak speed |
| DB drills | NO-GO | Pooled repeatability is a year/layout artefact; no orientation; no attributable coverage outcome |
| TE drills, DL short-zone breaks, LB drills | NO-GO | Too few athletes, or non-equivalent variants |
| Outcome validation of any skill-drill feature | **NO-GO now** | Not attempted. About 60 athletes per position limits detection to \|r\| ≳ 0.36 |

## 9. Recommended next experiment

**A measurement study of the two conditional candidates, still without outcomes.** Everything below should be pre-specified before any statistic is computed.

1. **WR route composite.**
   - Run a G-study (variance components athlete × route × year) to estimate how many routes are needed for a given generalisability.
   - Test invariance across years and layouts (2023/2024/2025 separately).
   - Separate *capacity* from *execution* by expressing route peak speed and acceleration bursts relative to the athlete's own tracked 40-yd peak speed. This must be a fixed definition stated in advance, not selected by its relationship with anything.
   - Check whether the composite is stable when single routes are left out.
2. **DL pass-rush arc.**
   - Define the arc segment geometrically (curvature-based start and end).
   - Estimate bend as a_n at matched speed or radius (a speed–radius envelope).
   - Quantify the SG attenuation of a_n with synthetic arcs and correct it or bound it.
   - Report left vs right separately and as a side-averaged score.
   - Year-centre all reliabilities.
3. **Only then**, and only with the lead's approval, write a pre-registration that names one outcome per candidate (WR: separation, opportunity-adjusted; DL: pressure per rush). It must state the ≈ 60-athlete power limit up front.
