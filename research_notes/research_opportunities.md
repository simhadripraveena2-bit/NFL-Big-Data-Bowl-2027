# Research Opportunity Assessment (Phase 1)

*Status: exploratory. No hypothesis has been selected and no model has been trained. Every empirical statement
cites a computation in `notebooks/01_dataset_exploration.ipynb`. The literature notes come from a **preliminary
web scan, not a systematic review**. Nothing here is a novelty claim; each direction lists the prior work that
must be checked before one could be made.*

## 1. What the data uniquely enables

The competition's distinctive asset is the **same 510 athletes measured twice by the same kind of sensor**: once in
standardised, repeated combine drills (10 Hz, 6,310 attempts, zero dropped frames) and again in 314,944 tracked NFL
player-plays (10 Hz, ≈1 s pre-snap to play end). The official site describes 2027 as the first Big Data Bowl to pair
combine tracking with in-game data ([NFL Operations](https://operations.nfl.com/gameday/analytics/big-data-bowl),
[Sports Video Group](https://www.sportsvideo.org/2026/10/08/nfl-announces-ninth-annual-big-data-bowl-powered-by-aws/)).
Prior work on combine predictive validity therefore relied almost entirely on stopwatch and tape-measure results
rather than tracking.

Facts from Phase 1 that shape every direction:

| Fact | Implication |
|---|---|
| `a` is an unsigned acceleration magnitude in both sources | braking, turning and propulsion must be separated by derivation |
| Combine `dis` ≠ frame displacement (≈0.46×) | derive distance from `x, y` |
| `dir` uses the NGS convention in both sources; `o` exists only in games | body-vs-travel direction (e.g. backpedal) is game-only |
| Game tracking holds only cohort players and no ball | no opponent-relative geometry from tracking; `player_play` supplies separation, cushion, pressure and get-off |
| 40-yard recordings end ≈0.5 s after peak speed | sprint braking is not observable in the 40; braking lives in the agility and skill drills |
| Skill drills are standardised paths repeated 6–18 times per player | within-player reliability and movement consistency are measurable |
| Game sequences include ≈1 s before the snap | stance and get-off are observable in games |
| WR/TE game data covers only route-running dropbacks (no run or blocking snaps); OL/DL/DB include run plays | WR/TE in-game envelopes describe route running only; cross-position comparisons are not like-for-like |

## 2. Candidate directions

Each direction is listed with its data support, a feasibility probe where one was run, prior work to check, and
risks. They are ordered by how strongly the current data supports them.

### D1. Combine → game kinematic translation (speed and acceleration capacity)
- **Question:** do individual acceleration–speed capacities measured in combine drills reappear in game movement, and does the gap between them carry information?
- **Data support:** the combine 40 gives clean maximal-effort speed curves (fig05). Game data gives each player's in-situ speed and acceleration envelope across thousands of frames.
- **Probe (descriptive):** combine 40 peak speed vs in-game 99th-percentile speed. Spearman ρ by position: WR 0.59 (n = 68), DL 0.67 (75), TE 0.49 (24), DB 0.21 (75), OL 0.14 (67) (fig12).
  - **Caveat:** the DL and DB groups mix sub-positions (DT/DE/OLB; CB/S) whose game roles differ. Their ρ may mostly reflect sub-position composition, so these are *not* translation estimates.
- **Prior work to check:** the *in-situ acceleration–speed profile* (Morin et al., 2021, *J. Biomech.*, [record](https://opact.sdu.edu.tr/vufind/SummonRecord/FETCH-LOGICAL-c497t-ed5c4f0473a2f08a22e955da72b7bea7f6c46cbbe41fe26951ee4670b444cf7c3/Details)) and its rugby extension ([Miguens et al., PMC10784250](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10784250/)), which derive A–S profiles from game GPS in other sports. NGS "Combine IQ" already ranks top speed, 10-yd speed and acceleration from combine chips ([AP via NBC](https://www.nbclosangeles.com/news/sports/nfl/nfl-nextgen-stats-team-new-tool-combine-results/3642262/)). A search for studies linking combine sprint tests to NFL *in-game tracking* speed found none, but absence from one search is not evidence of absence.
- **Risks:**
  - Game speed is role-limited (OL rarely sprint), so envelope estimation must condition on play type and assignment.
  - Upper-envelope estimators are sensitive to outliers; there is a known 2025 fault (see inventory §5).

### D2. Braking and change-of-direction mechanics
- **Question:** is the ability to *decelerate and re-orient*, rather than to accelerate, the combine trait that transfers to games?
- **Data support:**
  - Agility and skill drills contain strong derived braking. Median strongest ds/dt per attempt: shuttle −7.9, three-cone −5.9, DL drills −3.6 yd/s² (fig13).
  - Game player-plays almost always contain a braking episode (mode around −2 to −4 yd/s²).
  - The three-cone shows the expected speed-minimum and heading-spike structure at the cones (fig07).
- **Prior work to check:** horizontal deceleration as a foundation of change of direction ([Harper et al., 2022, *Sports Med.*](https://link.springer.com/article/10.1007/s40279-022-01693-0); [PMC9474351](https://pmc.ncbi.nlm.nih.gov/articles/PMC9474351)). Soccer "significant turn" definitions, e.g. ≤ −2 m/s², ≥ 20° heading change, re-acceleration within 1 s ([Griffiths, Lancaster MRes](https://eprints.lancs.ac.uk/211641/6/2023GriffithsMRes.pdf.docx)).
- **Risks:**
  - Finite-difference acceleration amplifies positional noise, so smoothing is a substantive method choice.
  - Heading is undefined near zero speed (fig07).
  - `a` cannot be used directly.

### D3. Movement signatures from standardised drill trajectories
- **Question:** beyond scalar times, does the *shape* of a player's path and speed profile in a fixed drill encode transferable skill (e.g. route-break sharpness, pass-pro mirroring, DB transition)? Does the *consistency* across repeated attempts matter?
- **Data support:**
  - 56 drill names with fixed choreography (fig04).
  - Median attempts per player: WR 14, TE 11, DB 10, DL 8, OL 8. This enables within-player reliability (ICC) and variability estimates, which a single stopwatch time cannot give.
  - Ball tracks for 551 WR/TE catching attempts allow player–ball timing.
- **Prior work to check:** functional data analysis and trajectory-embedding work in sports. Recent tracking-transformer work in prior Big Data Bowls ([SumerSports BDB 2026](https://sumersports.com/the-zone/sumersports-big-data-bowl-2026); "step-and-turn" generative movement model, [arXiv 2603.17866](https://arxiv.org/pdf/2603.17866)). Applying any of this to combine drills needs a dedicated literature search.
- **Risks:**
  - Drill names drift by year and need harmonising.
  - Alignment (rotation, start point, time warping) differs by drill.
  - Many drills × many shape descriptors creates a large multiple-comparisons burden.

### D4. Position-specific mechanism pairs (combine drill → matched in-game metric)
The dataset supports *mechanistically matched* pairs, which are more defensible than "combine → career":

| Group | Combine source | In-game target (`player_play` or derived from tracking) |
|---|---|---|
| WR / TE | route drills (curl, comeback, slant, dagger): break deceleration and re-acceleration | `separation_at_pass_forward` (87.7% non-null on WR/TE rows) |
| DL | 40 start phase, pass-rush and get-off drills | `player_get_off`, `time_to_pressure`, `pressure` |
| OL | wave / slide-and-shuffle, mirror, pull drills | `pressure_allowed`, `time_to_pressure_allowed`, `peak_pressure_probability_allowed` |
| DB | backpedal-and-transition, W drill, box drill | `cushion`, coverage outcomes; game `o` vs `dir` exposes backpedals (≈11% of frames at s > 3 have \|o − dir\| > 90°) |

- **Risk:** in-game targets depend on teammates, opponents and scheme. They need adjustment, such as play context from `player_play`.

### D5. Incremental value over existing measures
- **Question:** does tracking add information beyond the official `forty`, `three_cone`, `short_shuttle`, the NGS athleticism score and draft position?
- **Why it matters:** the literature broadly finds stopwatch drills weak predictors of NFL success, with position-specific exceptions. See [arXiv 2303.05774](https://arxiv.org/pdf/2303.05774), [Inside Science](https://www.aip.org/inside-science/how-much-does-the-combine-reveal-about-future-nfl-players), [SumerSports](https://sumersports.com/the-zone/nfl-combine-by-position-how-do-the-40-yard-dash-and-other-drills-predict-nfl-success); the cited studies are heterogeneous and several are not peer-reviewed. Any tracking result must therefore beat these baselines, not a null model.
- **Note:** the competition's own coverage flags null results as a real possibility ([Lets Data Science](https://letsdatascience.com/news/nfl-opens-big-data-bowl-2027-competition-36beec5a)).

### D6. Career success outcomes (lowest support, for now)
- `player_career_successes` gives snaps, games and starts plus rare honours: 11 players with any Pro Bowl and 7 with any All-Pro.
- Outcomes are heavily right-censored by draft class (median starts: 5 / 2 / 0 for 2023 / 24 / 25; fig11).
- Career totals are better treated as exposure or opportunity variables than as primary targets. Play-level performance metrics have far more data.

## 3. Statistical challenges

1. **Small n per position.** With ≥ 100 REG plays there are 63–77 players per group (TE 21). The approximate minimum detectable correlation (α = 0.05, power 0.8) is r ≈ 0.31–0.35, or 0.58 for TE. Small effects are undetectable per position, so pooling with hierarchical partial pooling is likely necessary.
2. **Heterogeneous position groups.** DL contains DT/DE/OLB and DB contains CB/S. Analyses within combine positions can be dominated by composition (Simpson's paradox risk; see the D1 caveat).
3. **Selection and endogeneity.** Combine → draft capital → playing time → measured outcomes. Exposure is not random; draft pick is a confounder or mediator that must be modelled explicitly.
4. **Right-censoring and unequal exposure** across classes (1–3 seasons) argue for rate outcomes or survival / exposure-adjusted designs.
5. **Repeated measures and leakage.** Thousands of frames and plays per player, but the unit of inference is the *player* (n ≈ 500). Any validation must split by player (and ideally by draft class), never by frame or play.
6. **Measurement error.** Derived acceleration and heading are noise-amplified. Combine and game `a` differ in smoothing (r = 0.99 vs 0.88 with ‖dv/dt‖).
7. **Multiple comparisons.** 56 drills × many descriptors × 5 positions. This needs pre-registration of a small hypothesis set or FDR control, plus held-out confirmation.
8. **Role confounding in games.** Movement envelopes reflect assignments as much as capacity (fig08). Condition on play type, alignment and assignment.
9. **Missing-not-at-random drills.** About 60% skip the official agility drills, and tracking exists only for those who ran them.
10. **Coordinate normalisation.** Game `x, y` are raw field coordinates; `play_direction` (from `player_play`, 50 nulls) is needed to normalise.
11. **Unresolved data issues.** About 1% tracking ↔ `player_play` mismatch, one faulty 2025 game, drill-name synonyms, and undocumented combine `dis`.

## 4. Recommended next steps (for approval, not yet started)
1. Confirm column definitions on the Kaggle data page: combine `dis`, the career-field windows (postseason?), and the `a` smoothing.
2. Run a **systematic literature review** for D1–D3. This is required before any novelty claim under the CLAUDE.md standards.
3. Phase 2 groundwork, if approved:
   - a cleaning layer: fault exclusion, drill-name harmonisation, coordinate normalisation, a principled smoothing filter;
   - a test-retest reliability study of drill-derived quantities across repeated attempts. Only reliable quantities are worth relating to game outcomes.

## Sources consulted (preliminary scan)
- [NFL Operations: Big Data Bowl](https://operations.nfl.com/gameday/analytics/big-data-bowl)
- [Sports Video Group: ninth annual Big Data Bowl announcement](https://www.sportsvideo.org/2026/10/08/nfl-announces-ninth-annual-big-data-bowl-powered-by-aws/)
- [Lets Data Science: NFL opens BDB 2027](https://letsdatascience.com/news/nfl-opens-big-data-bowl-2027-competition-36beec5a)
- [Front Office Sports: BDB 2027 focus on the combine](https://frontofficesports.com/article/nfl-data-competition-will-focus-on-what-matters-at-scouting-combine/)
- [arXiv 2303.05774: NFL Career Success as Predicted by NFL Scouting Combine](https://arxiv.org/pdf/2303.05774)
- [Inside Science: How much does the combine reveal?](https://www.aip.org/inside-science/how-much-does-the-combine-reveal-about-future-nfl-players)
- [SumerSports: combine by position](https://sumersports.com/the-zone/nfl-combine-by-position-how-do-the-40-yard-dash-and-other-drills-predict-nfl-success)
- [AP / NBC: NGS Combine IQ](https://www.nbclosangeles.com/news/sports/nfl/nfl-nextgen-stats-team-new-tool-combine-results/3642262/)
- [Yahoo Sports: tracking data at the combine](https://sports.yahoo.com/player-tracking-data-gains-value-092439389.html)
- [Morin et al. 2021, in-situ A–S profile (record)](https://opact.sdu.edu.tr/vufind/SummonRecord/FETCH-LOGICAL-c497t-ed5c4f0473a2f08a22e955da72b7bea7f6c46cbbe41fe26951ee4670b444cf7c3/Details)
- [Miguens et al., in-situ A–S profiling in rugby](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10784250/)
- [Harper et al. 2022, deceleration review](https://link.springer.com/article/10.1007/s40279-022-01693-0)
- [PMC9474351](https://pmc.ncbi.nlm.nih.gov/articles/PMC9474351)
- [Griffiths, Lancaster MRes: turn definitions](https://eprints.lancs.ac.uk/211641/6/2023GriffithsMRes.pdf.docx)
- [SumerSports BDB 2026](https://sumersports.com/the-zone/sumersports-big-data-bowl-2026)
- [arXiv 2603.17866: NFL step-and-turn](https://arxiv.org/pdf/2603.17866)
