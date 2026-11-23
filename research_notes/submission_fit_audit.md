# Phase 9A: Big Data Bowl 2027 submission-fit audit

**Scope:** documentation only.
- No model, result, preregistration or analysis code was changed.
- No statistical test was run, and no combine × outcome association was computed or inspected.
- Every number below comes from existing notes:
  - `research_findings_summary.md` (RFS);
  - `game_outcome_inventory.md` (GOI);
  - `position_specific_metrics.md` (PSM);
  - `power_analysis.md` (PA);
  - `phase8c_novelty_audit.md` (8C).

**Official requirements:** read from the competition pages with the Kaggle CLI on 2026-11-23 (pages: Description, Abstract, Evaluation, Submission Requirements, Timeline, rules).

## 1. What the competition asks for (official pages)

- **Theme:** "Combine to NFL Performance". Understand "how player movement during Combine drills translates to performance on the field during the NFL regular season".
- Analysis should be "actionable and accessible to coaches, scouts, and front offices".
- Entrants are encouraged to focus on "one small aspect of movement, a specific position group, or an individual drill".
- **Abstract:** "non-obvious, actionable linkages between 10 Hz Combine sensor tracking data and future regular-season NFL game performance … identify hidden talent, avoid costly draft busts, and design position-specific player development protocols".
- **Pass/fail gates:**
  1. The writeup explicitly links combine sensor tracking to **regular-season game performance**.
  2. Readable markdown, embedded visuals, and an attached **public Kaggle notebook**.
- **Scored components (0–10 each):**

  | component | weight | evaluation questions |
  |---|---|---|
  | Football | 30 % | week-to-week usability; accounts for football complexity; unique ideas |
  | Data science | 30 % | correct; claims backed by data; appropriate models; innovative applications |
  | Writeup | 20 % | well written; easy to follow; clearly defined motivation |
  | Visualization | 20 % | accessible, accurate, innovative charts and tables |

- **Limits:**
  - ≤ 2,000 words and fewer than 10 tables or figures (penalty otherwise);
  - code mostly in an appendix or a linked notebook;
  - a writeup that does not use player tracking data is not scored.
- **Judges:** analytics staff from the 32 NFL teams or tracking vendors.
- **Dates:**
  - deadline 2027-01-06 23:59 UTC;
  - results 2027-01-26;
  - finalists are invited to present at the 2027 Combine.

## 2. Our evidence, by layer

The four layers (from GOI §6) must not be blurred in the writeup.

| layer | what we measured | key numbers | status |
|---|---|---|---|
| **Combine athletic capacity** | tracked 40 peak speed (best of valid attempts); official 40; weight | within-position reliability, best of 2: WR 0.94, TE 0.96, DB 0.96, DL 0.99, OL 0.97. Peak speed has **34 % / 36 % of its variance outside the official 40** for WR / DB, 5 % for DL (PSM §5) | measured, reliable; **predictor side only** |
| **Regular-season game movement** (speed expression) | play-maximum speed by task context | player-level reliability WR 0.85 / 0.82, DL 0.94 / 0.86, OL 0.94 / 0.90, DB 0.65 / 0.68. Near-top-speed demand: WR deep 17 % of plays vs short 1 %; DL and OL ≤ 3 % (PSM §4) | **H1 family:** WR ρ_deep 0.58 / ρ_short 0.49, Δ 0.09 [−0.09, 0.40], inconclusive; DB, OL, TE inconclusive or uninformative; DL(a) SESOI-sized pass-rush advantage not supported |
| **Actual football performance** | WR separation at pass forward (deep routes) | player-level reliability 0.44 (between-player SD 0.13 yd); **H2:** β_P −0.020 yd/SD [−0.101, 0.063]; no combine model beats the position mean on held-out players (RFS §5) | the **only** performance outcome analysed; no incremental value of tracked peak speed detected |
| **Player deployment and role** | route mix, coverage, DL alignment (EDGE / interior), body weight | context adjustment cuts WR short-route separation reliability from 0.75 to 0.22 (PSM §3). **H1-DL(b): Holm-supported.** Pooled DL speed ↔ game-speed ρ falls from 0.55 to −0.27 with role + weight; role alone or weight alone removes most of it (RFS §6–7) | deployment explains much of what looks like player signal |

**Reading the table:**
- Most of the confirmatory work links **capacity → movement**.
- Only H2 links **capacity → performance**, and it is null-leaning and imprecise.
- Deployment is the strongest *finding*, but it is a confound story, not a performance link.

## 3. Rubric mapping (our judgement, not a prediction of scores)

| component | strengths we have | weaknesses | judgement |
|---|---|---|---|
| **Football (30 %)** | positions treated separately; task context (route depth, coverage, alignment) modelled; REG only; deployment and role confounding shown explicitly (DL) | mostly a *movement* story; little **week-to-week** use (draft and evaluation oriented); the one performance result is null; uniqueness limited (no novelty claim is possible: 8C) | **weakest component**: moderate at best |
| **Data science (30 %)** | pre-registration; frozen code; synthetic validation of the pipeline (Phase 4); player-level inference; held-out-player and season-forward checks; reliability and EIV analysis; Holm control; negative controls | inconclusive primary; no new metric or algorithm (8C); the conservative bootstrap needs careful explanation | **strongest component**: rigour and correctness are a clear differentiator |
| **Writeup (20 %)** | a clear, honest story is available (§5) | the current notes are far beyond 2,000 words, technical, and organised around hypotheses rather than decisions; a rewrite is needed | not yet written; achievable |
| **Visualization (20 %)** | Phase 2–10 figures exist (power, synthetic validation, forest plots) | built for analysts; none yet designed for coaches and scouts; must fit within the 9-item budget | not yet designed; achievable |

**Pass/fail gates:**
1. **Linkage:** passes *only* if H2 (separation = performance) is presented explicitly as the performance link. H1 alone (game speed) could be read as movement, not performance, so this is a real risk.
2. **Completeness:** requires porting a reproducible public Kaggle notebook. The current pipeline is local scripts. This is a work item, not a scientific issue.

## 4. Actionable findings (already established; no new tests)

Each finding is listed with the layer it belongs to and its evidence status.

| # | message for evaluators | layer | status |
|---|---|---|---|
| F1 | **Tracked combine top speed is a reliable athlete measurement, and for WRs and DBs about a third of it is not captured by the 40 time.** The 40 mixes early acceleration and top speed (WR ρ peak vs 10-yd split −0.33). | capacity | descriptive measurement (PSM §5; D3); no outcome claim |
| F2 | **A receiver's combine top speed tracks how fast he runs in games, about equally on short and deep routes** (ρ ≈ 0.5–0.6). Combine speed does not "switch on" only on deep routes. | capacity → movement | registered estimate; Δ inconclusive (not "no difference") |
| F3 | **Top speed is rarely the binding constraint on an NFL play.** WRs reach ≥ 90 % of their own top speed on 17 % of deep routes and 1 % of short routes; DL and OL on ≤ 3 % of snaps. | movement (no combine data) | outcome-blind descriptive (PSM §4) |
| F4 | **Tracked top speed did not add information about deep-route separation beyond the 40.** The CI rules out more than about 2 inches per SD. No combine speed model beat the position average for held-out receivers. | capacity → performance | registered estimation (H2); "not detected", not "proven zero" |
| F5 | **Raw separation is mostly deployment.** After route and coverage adjustment, short-route separation is barely a player trait (reliability 0.22); deep separation is a weak trait (0.44). | performance vs deployment | outcome-blind measurement (PSM §3; H2) |
| F6 | **For defensive linemen, "combine speed" is largely body type and role.** The DL speed ↔ game-speed link is substantially sensitive to role and weight adjustment, and within EDGE or interior it is near zero. | capacity ↔ deployment | Holm-supported H1-DL(b) + descriptive audit; no causal reading |

**Who can use which finding:**
- **Scouts and personnel:** F1, F2, F4, F6. Evaluate DL speed relative to body type and role, and do not price tracked top speed as a separation signal.
- **Coaches:** F3 and F5. Speed is a deep-route resource. Judge separation against route and coverage context, not raw.
- **Analysts:** F5 and the method itself: player-level reliability, context adjustment, held-out players.
- **Week-to-week use:** limited to F3 and F5 (context-adjusted separation and speed-demand profiles). These are descriptive tools, not new models.

## 5. Biggest submission weakness

**The story is about game movement more than football performance.**
- The primary test (H1-WR) and four of the five Holm-family tests use **play-maximum speed**, which is speed *expression*, not performance (GOI §6).
- Our only performance outcome (H2, WR deep separation) is null-leaning and has low player-level reliability (0.44).
- Judges explicitly look for links to **performance**, **week-to-week usability** and **actionable** insight. Both primary results being inconclusive compounds this.

**Available performance outcomes** (existing reliability and sample-size reports; no new association computed):

| outcome | position | context-adjusted split-half reliability [95 % CI] | season → season | eligible players (≥ 100 opps) | players with a valid tracked 40 (registered samples) | used so far? |
|---|---|---|---|---|---|---|
| separation at pass forward, deep | WR | 0.61 [0.17, 0.83] (PSM); 0.44 in the H2 model | 0.28 | 41 (PSM) | 57 (H2 sample) | **yes (H2), null-leaning** |
| targets per route | WR | **0.78** [0.60, 0.88] | 0.41 | 63 | ≈ 57 | no |
| pressure per rush | DL | 0.50 [0.18, 0.72] | 0.30 | 69 | 53 (25 EDGE / 28 interior) | no |
| pressure allowed per pass block | OL | 0.47 [0.17, 0.70] | 0.40 | 66 | 53 | no |
| peak pressure probability allowed | OL | 0.69 [0.44, 0.84] | 0.32 | 66 | 53 | no; listed as **exploratory** in preregistration v1.0 §2 |

**Structural limits that apply to any new performance test:**
- **Power is set by players.** n ≈ 53–57. For a single correlation at n = 53, the 80 %-power minimum detectable *observed* r is about 0.38 (Fisher z, two-sided α 0.05). Divided by the attenuation factor √(R_x · R_y), the *true-score* r needed is about 0.54 for DL pressure (R_y 0.50) and about 0.46 for OL peak pressure probability (0.69).
- **Predictor collinearity.** In DL, peak speed has only 5 % variance outside the 40, and |ρ| with weight is 0.80. A DL performance link cannot be attributed to combine *tracking* or to speed rather than body type (RFS §7).
- **Deployment.** Targets per route is reliable (0.78), but it is a usage rate driven by role, QB and scheme. Draft capital drives both role and athletic profile, which is a selection confound (RFS §9.3).
- **Forking paths.** Every remaining outcome would be chosen *after* the H1 and H2 results were seen. For WR (H2 already null) and DL (role and weight already shown to absorb the movement link), a new test risks looking like outcome shopping, however carefully it is pre-registered.

## 6. Bottom line of the audit

- **Data-science quality is the entry's strongest asset.** Football relevance is its weakest.
- The performance gap cannot be closed convincingly with the available outcomes: power, reliability, predictor collinearity and deployment confounding all bind.
- The entry can still pass both gates and be useful, if the writeup:
  1. leads with the **performance** question and H2;
  2. presents the movement results as the mechanism ("does combine speed even show up on the field, and where?");
  3. turns F1–F6 into clear evaluator guidance.

The path is decided in `submission_story_recommendation.md`.
