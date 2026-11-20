# Literature Review — Phase 1.5

*NFL Big Data Bowl 2027 · Candidates A (movement consistency), B (combine→game acceleration/speed transfer),
C (braking and change-of-direction mechanics). Compiled 2026-11-20.*

## 0. How this review was done (and what it cannot claim)

### Sources actually queried

| Source | How | Status |
|---|---|---|
| **PubMed** (NCBI E-utilities) | `esearch` + `efetch`; abstracts parsed from XML | ✅ primary source of abstracts |
| **Crossref** | bibliographic search + DOI lookup; abstracts when deposited | ✅ used to verify every DOI, title, venue and year |
| **Semantic Scholar** | Graph API | ⚠️ heavily rate-limited (HTTP 429) on this shared IP; used only for single-DOI lookups of 4 missing abstracts |
| **Google Scholar** | — | ❌ no API; not queried directly. A general web search (Phase 1) supplied leads only |
| OpenAlex | — | ❌ requires an API key tied to the user's email; not used without permission |
| Publisher pages | web fetch | ❌ publisher hosts are not on this environment's network allowlist |

### Search effort
- **62 queries in total** across 8 themes:
  - 38 structured queries (`queries.tsv`);
  - 20 gap-verification queries;
  - 4 American-football-specific checks;
  - plus about 90 targeted Crossref verifications of named landmark papers.
- 1,874 records were retrieved (1,618 unique by DOI or title) and screened by title, plus abstract where relevant.
- **123 papers were selected and verified** (DOI resolved via Crossref or PubMed): **106 with abstract read** (93 PubMed, 11 Crossref, 2 Semantic Scholar), **2 with only an automatic summary**, and **15 metadata-only** (method references).

### Access level of each paper (column "Acc." in the tables)
- **A** — I read the abstract (source given: PubMed, Crossref or Semantic Scholar).
- **T** — only an automatically generated Semantic Scholar summary was available.
- **M** — metadata only (title, authors, venue, year, DOI verified). The abstract was *not* accessed. These papers are cited only for the method they are named for, and no finding is attributed to them.

> **Honesty statement.** I read **no full texts**. Every "method" and "finding" below is taken from the paper's
> abstract as retrieved. Numbers in the tables appear in the abstracts. Where an abstract was truncated in the
> source, I report only what was visible. Before any claim is used in a submission, the full text must be read.
> The search is structured but **not** a PRISMA systematic review: there was one screener, no grey literature,
> no citation chasing beyond named landmarks, and Google Scholar was not directly queried.

---

## 1. Combine testing and NFL career or game-performance prediction

| # | Citation | DOI | Design / method (from abstract) | Key findings (from abstract) | Acc. |
|---|---|---|---|---|---|
| 1 | McGee & Burkett (2003) *JSCR* 17:6 | [10.1519/1533-4287(2003)017<0006:TNFLCA>2.0.CO;2](https://doi.org/10.1519/1533-4287(2003)017<0006:tnflca>2.0.co;2) | 326 players, 2000 combine; position-specific prediction equations for draft status | Reported r² = 1.00 for RB, WR and DB; 0.70 OL; 0.59 DL; 0.22 LB; 0.84 QB. *(r² = 1.00 with these n strongly suggests overfitting.)* | A-PM |
| 2 | Sierer et al. (2008) *JSCR* | [10.1519/JSC.0b013e31815ef90c](https://doi.org/10.1519/jsc.0b013e31815ef90c) | Drafted vs non-drafted, 2004–05 (n = 321); t-tests in 3 size groups | 40-yd and 3-cone differ in all groups; vertical and pro-agility for skill players; bench for linemen | A-PM |
| 3 | Kuzmits & Adams (2008) *JSCR* | [10.1519/JSC.0b013e318185f09d](https://doi.org/10.1519/jsc.0b013e318185f09d) | QB/RB/WR 1999–2004; correlations with draft order, salary, games and position stats | "No consistent statistical relationship" except sprint tests for RBs | A-PM |
| 4 | Robbins (2010) *JSCR* | [10.1519/JSC.0b013e3181f927cc](https://doi.org/10.1519/jsc.0b013e3181f927cc) | n = 1,155 drafted players, 2005–09; raw, ratio- and allometric-scaled tests vs draft order | Little association with draft order; normalisation gave no advantage; sprint and jumps weigh most | A-PM |
| 5 | Robbins (2012) *JSCR* | [10.1519/JSC.0b013e318225b5fa](https://doi.org/10.1519/jsc.0b013e318225b5fa) | n = 1,136; correlations among 9.1-, 18.3-, 36.6- and flying 18.3-m sprints and jumps | 9.1-m and flying 18.3-m sprints measure partly independent qualities (acceleration vs max speed); recommends the flying 18.3 m for max speed | A-PM |
| 6 | Teramoto et al. (2016) *JSCR* | [10.1519/JSC.0000000000001202](https://doi.org/10.1519/jsc.0000000000001202) | RB n = 276, WR n = 447 (2000–09); regression + PCA adjusted for games, draft position, height, weight | 10-yd split was the strongest predictor of RB yards/attempt; vertical jump predicted WR yards/reception | A-PM |
| 7 | Hedlund (2018) *JSCR* | [10.1519/JSC.0000000000002252](https://doi.org/10.1519/jsc.0000000000002252) | N = 5,506 (2002–16); Pro Bowl / All-Pro vs combine results by position | Position-specific descriptive differences between future elite and other players | A-PM |
| 8 | Vincent, Blissmer & Hatfield (2019) *JSCR* | [10.1519/JSC.0000000000002937](https://doi.org/10.1519/JSC.0000000000002937) | 2005–10 combine players; hierarchical regression on first 3–4 years of position stats | Combine explained 4–62% of variance in individual stats; "modest predictors" | A-PM |
| 9 | LaPlaca & McCullick (2020) *JSCR* | [10.1519/JSC.0000000000003479](https://doi.org/10.1519/JSC.0000000000003479) | 15 positions; Spearman correlations with performance indicators | Every position had at least one test correlated with performance (many tests per position, so multiplicity is a concern) | A-PM |
| 10 | Cook et al. (2020) *JSCR* | [10.1519/JSC.0000000000003676](https://doi.org/10.1519/JSC.0000000000003676) | 2013–17 (n = 1,537); z-scored tests vs next-season performance | Combine explained ≈2.6% of next-year performance variance; most r < 0.3 | A-PM |
| 11 | Rishis, Johnston & Baker (2023) *J Sports Sci* | [10.1080/02640414.2023.2207853](https://doi.org/10.1080/02640414.2023.2207853) | PRISMA systematic review (1,954 screened, 68 included) | Mixed evidence. Only **1** included study used *playing performance* and 12 studied combine tests; calls for more long-term research | A-PM |
| 12 | Doyle et al. (2026) *JSCR* | [10.1519/JSC.0000000000005654](https://doi.org/10.1519/jsc.0000000000005654) | n = 3,681; PCA (momentum, power, COD, strength) + logistic regression with Monte-Carlo CV | Components explain within-position variance, but draft prediction is poor (AUC < 0.75); some undrafted groups scored higher | A-PM |
| 13 | Zhao et al. (2025) *Sci Rep* | [10.1038/s41598-025-07383-x](https://doi.org/10.1038/s41598-025-07383-x) | 2000–24 (n = 3,446); z-scores and total athleticism score vs drafted status, ROC | AUCs about 0.56–0.72; the 40-yd z-score had the highest AUC | A-PM |
| 14 | LaPlaca (2025) *RQES* | [10.1080/02701367.2024.2448827](https://doi.org/10.1080/02701367.2024.2448827) | 15 positions; t-tests: ≥10 games/season vs fewer | At least one test differed for every position | A-PM |
| 15 | Clark et al. (2019) *JSCR* | [10.1519/JSC.0000000000002081](https://doi.org/10.1519/jsc.0000000000002081) | 2016 combine; **mono-exponential model fitted to the 9.1/18.3/36.6-m splits** | v_max correlated with split times (r = 0.72, 0.83, 0.94). τ (= v_max/a_max) was almost identical in fast and slow groups (0.768 vs 0.773 s) | A-PM |
| 16 | Agar-Newman et al. (2024) *JSCR* | [10.1519/JSC.0000000000004799](https://doi.org/10.1519/JSC.0000000000004799) | 1999–2020 (n = 4,149); train/test regression predicting sprint splits from jumps and anthropometrics | Adjusted R² 0.74–0.79 for split segments | A-PM |
| 17 | Gillen (2023) *JSCR* | [10.1519/JSC.0000000000004546](https://doi.org/10.1519/JSC.0000000000004546) | 2015–19 (n = 3,015); percentile norms, allometric scaling | Position-specific norms; scaling changes position differences | A-PM |
| 18 | Mann et al. (2016) *JSCR* 30:893 | [10.1519/JSC.0000000000001329](https://doi.org/10.1519/JSC.0000000000001329) | Division-I players (n = 64); duplicate trials in 2 weeks; pro-agility and 3-cone **hand-timed** | ICC: 3-cone 0.962, 10-yd 0.974, pro-agility 0.914. CV 1.2–1.9%. Smallest worthwhile difference 3.7–6.6% | A-PM |
| 19 | Gillen et al. (2018) *JSCR* | [10.1519/JSC.0000000000002498](https://doi.org/10.1519/JSC.0000000000002498) | Youth (6–15 y) combine tests, 2 attempts | Adequate reliability except the 10-yd dash | A-PM |
| 20 | Gogos et al. (2020) *PLOS ONE* (Australian football) | [10.1371/journal.pone.0234400](https://doi.org/10.1371/journal.pone.0234400) | AFL draftees 1999–2016 (n = 1,488); boosted regression trees | Tests explained 4% of matches played and 3% of in-game performance; each test < 2% | A-PM |
| 21 | Asprey et al. (2020) *Phys Ther Rehabil* | [10.7243/2055-2386-7-8](https://doi.org/10.7243/2055-2386-7-8) | Combine vs career longevity (title only) | — | M |

**Synthesis.**
- Four decades of studies use **stopwatch and tape-measure results** and mostly **draft status** as the outcome. They find weak, inconsistent, position-dependent associations. The best-designed recent work (Cook 2020; Doyle 2026) explains little variance, and the AFL analogue agrees (Gogos 2020).
- Methodological weaknesses are common: over-fitted equations (#1), many uncorrected correlations (#9), no cross-validation, draft position used as both outcome and confounder, and **no measurement-error modelling** of single-occasion tests.
- The 2023 systematic review found only one study using playing performance as the outcome.
- **No retrieved study used combine *tracking* data**. In our searches, "NFL combine" plus "tracking/RFID/Next Gen Stats" returned no peer-reviewed hits. Clark 2019 is the closest: it reconstructs velocity curves from three split times.

---

## 2. Sprint mechanics and acceleration–speed (A–S) profiling

| # | Citation | DOI | Design / method | Key findings | Acc. |
|---|---|---|---|---|---|
| 22 | Samozino et al. (2016) *Scand J Med Sci Sports* 26:648 | [10.1111/sms.12490](https://doi.org/10.1111/sms.12490) | Inverse-dynamics macroscopic model on spatiotemporal data, validated against force plates | Bias < 5% for F0, V0 and Pmax; inter-trial SEM < 5% | A-PM |
| 23 | Morin & Samozino (2016) *IJSPP* | [10.1123/ijspp.2015-0638](https://doi.org/10.1123/ijspp.2015-0638) | Practitioner guide to force–velocity profiles | Interpretation framework (optimal profile, imbalance) | A-PM |
| 24 | Ettema (2024) *IJSPP* | [10.1123/ijspp.2023-0110](https://doi.org/10.1123/ijspp.2023-0110) | Critical commentary | FV profiling adds **no information** beyond the velocity–time curve; at best identifies between-athlete differences, which performance times already give | A-PM |
| 25 | Haugen & Buchheit (2016) *Sports Med* 46:641 | [10.1007/s40279-015-0446-0](https://doi.org/10.1007/s40279-015-0446-0) | Methodological review of sprint monitoring | Starting procedures and triggering devices can cause time differences larger than years of training gains; GPS adequate only for longer distances (truncated) | A-PM |
| 26 | Fornasier-Santos et al. (2022) *Sensors* | [10.3390/s22228610](https://doi.org/10.3390/s22228610) | 5 systems recording 40-m sprints simultaneously | v_max agrees across systems; early-acceleration variables differ by 4.8–12.9%; inter-trial CV < 5.7% | A-PM |
| 27 | **Morin et al. (2021)** *J Biomech* | [10.1016/j.jbiomech.2021.110524](https://doi.org/10.1016/j.jbiomech.2021.110524) | **In-situ A–S profile:** GPS from several sessions; max acceleration per 0.2 m/s speed bin from 3 m/s; linear fit | Highly linear profiles (all R² > 0.984); good 2-week reliability (16 professionals) | A-PM |
| 28 | Clavel et al. (2023) *J Biomech* | [10.1016/j.jbiomech.2023.111602](https://doi.org/10.1016/j.jbiomech.2023.111602) | Week-to-week reliability, 18 U19 players | Reliability depends on the **spread of points**, needing efforts up to ≥ 95% of max speed, more than on session count; S0 is sensitive to session content | A-PM |
| 29 | Miguens et al. (2024) *Sports Med Open* | [10.1186/s40798-023-00672-7](https://doi.org/10.1186/s40798-023-00672-7) | 49 rugby players, 61.5 M positions; **DBSCAN outlier removal**; repeated sub-fits to estimate error | ICC 0.72–0.92 across 2-week phases; highest A0 in *games*, highest S0 in *speed sessions*; position-dependent | A-PM |
| 30 | Cormier et al. (2023) *J Biomech* | [10.1016/j.jbiomech.2023.111724](https://doi.org/10.1016/j.jbiomech.2023.111724) | 15 elite female soccer players; in-situ profiles vs isolated 40-m sprints; CI vs boxplot outlier rules | Boxplot rule gives good agreement with sprint-derived A0 and S0; CI rule shows proportional bias | A-PM |
| 31 | Jovanović et al. (2024) *Sensors* | [10.3390/s24196192](https://doi.org/10.3390/s24196192) | 31 youth basketball players; LPS (Kinexon) vs laser; time–velocity vs velocity–acceleration methods | Only **max sprint speed** has acceptable sensitivity (MDC < 5%); A0, τ and Pmax > 10%. Caution when inferring acceleration capacity in situ | A-PM |
| 32 | Alonso-Callejo et al. (2022) *Sci Rep* | [10.1038/s41598-022-23790-w](https://doi.org/10.1038/s41598-022-23790-w) | Professional soccer, 5 positions, 6 microcycles | Match day gives higher A0, peak acceleration and peak speed than training; position effects | A-PM |
| 33 | Alonso-Callejo et al. (2026) *IJSPP* | [10.1123/ijspp.2025-0292](https://doi.org/10.1123/ijspp.2025-0292) | 3 seasons, men and women; windows of 1–5 microcycles | Most reliable: 2 microcycles including a match day; competitive data beat non-competitive | A-PM |
| 34 | Cardoso et al. (2023) *J Sports Sci* 41:1868 | [10.1080/02640414.2024.2305005](https://doi.org/10.1080/02640414.2024.2305005) | 141 academy players, U14 to B-team | S0 lower in U14; A0 does not differ across ages | A-PM |
| 35 | Al Haddad et al. (2015) *IJSPP* | [10.1123/ijspp.2014-0539](https://doi.org/10.1123/ijspp.2014-0539) | 180 youth soccer players; maximal sprint speed (MSS, test) vs peak match speed (GPS) | Faster players reach higher absolute match peak speed; match peak = 85–94% of MSS, varying with age and position | A-PM |
| 36 | Dillon et al. (2021) *J Sports Sci* | [10.1080/02640414.2021.1876330](https://doi.org/10.1080/02640414.2021.1876330) | 29 AFL players; 10 Hz GPS sprint tests vs matches | Match peak velocity *exceeded* test peak by 0.28 m/s | A-PM |
| 37 | Massard et al. (2017) *Sci Med Football* | [10.1080/24733938.2017.1398409](https://doi.org/10.1080/24733938.2017.1398409) | "Is sprint testing necessary?" (title only) | — | M |

**Synthesis.**
- A two-parameter description, either the mono-exponential (Clark 2019) or the linear A–S line (Morin 2021), fits maximal sprints well.
- In-situ profiling recovers those parameters from routine soccer and rugby tracking. Its weak points are **outlier handling** (DBSCAN, boxplot or CI rules give different answers), **coverage of near-maximal efforts** (Clavel 2023), and the **poor sensitivity of acceleration-side parameters** (Jovanović 2024).
- Test–match relations exist but are modest and context-dependent: match peaks can fall below *or* above test values (Al Haddad 2015; Dillon 2021).
- Ettema (2024) warns that re-parameterised profiles may contain no information beyond the raw curve. **Any "new metric" must show added information, not re-description.**
- **In our searches, no study applied in-situ A–S profiling to American football or linked an athlete's combine-day sprint profile to the same athlete's in-game profile.**

---

## 3. Deceleration and change-of-direction (COD) biomechanics

| # | Citation | DOI | Design / method | Key findings | Acc. |
|---|---|---|---|---|---|
| 38 | **Harper et al. (2022)** *Sports Med* | [10.1007/s40279-022-01693-0](https://doi.org/10.1007/s40279-022-01693-0) | Narrative / evidence review of horizontal deceleration | Early-stance (< 50 ms) braking forces up to **2.7×** those of first acceleration steps. Key qualities: braking force *control* and *attenuation* (eccentric, isometric and reactive strength; technique) | A-PM |
| 39 | Harper, Carling & Kiely (2019) *Sports Med* | [10.1007/s40279-019-01170-1](https://doi.org/10.1007/s40279-019-01170-1) | Systematic review + meta-analysis of high (> 2.5 m/s²) and very high (> 3.5 m/s²) accelerations vs decelerations in match play; 19 studies including American football | Quantified accel vs decel frequencies; risk-of-bias checklist for GPS processing | A-PM |
| 40 | McBurnie et al. (2021) *Sports Med* | [10.1007/s40279-021-01583-x](https://doi.org/10.1007/s40279-021-01583-x) | Narrative review | High braking loads link to tissue damage and fatigue; argues for deceleration training | A-PM |
| 41 | Harper et al. (2020) *Sports Biomech* | [10.1080/14763141.2020.1792968](https://doi.org/10.1080/14763141.2020.1792968) | Radar maximal deceleration test after a 20-m sprint; intra-day n = 38, inter-day n = 12 | Many variables reliable intra-day (ICC > 0.75, CV < 10%); **only kinetic variables reliable inter-day** | A-PM |
| 42 | **Ellens et al. (2022)** *J Sports Sci* | [10.1080/02640414.2022.2054535](https://doi.org/10.1080/02640414.2022.2054535) | Scoping review of 276 studies on deriving and cleaning acceleration data | **60% of studies did not report how acceleration was derived or cleaned** | A-PM |
| 43 | Delves et al. (2021) *Sports Med Open* | [10.1186/s40798-021-00332-8](https://doi.org/10.1186/s40798-021-00332-8) | Systematic review of acceleration metrics | Heterogeneous metrics; proposes a reporting framework | A-PM |
| 44 | **Nimphius et al. (2016)** *JSCR* | [10.1519/JSC.0000000000001421](https://doi.org/10.1519/jsc.0000000000001421) | 17 cricketers; COD deficit = 505 time − 10-m time | COD deficit unrelated to sprint time (r ≈ −0.11 to 0.10), while 505 time was related (r = 0.52–0.70); 5 of 17 classified differently | A-PM |
| 45 | Bishop et al. (2021) *J Sports Sci* 39:1088 | [10.1080/02640414.2020.1857578](https://doi.org/10.1080/02640414.2020.1857578) | 25 rugby players; COD deficit vs deceleration deficit | Only moderate agreement on limb dominance (κ 0.41–0.48); jumps relate to speed but not to the deficits | A-PM |
| 46 | Freitas et al. (2022) *JSCR* | [10.1519/JSC.0000000000004118](https://doi.org/10.1519/JSC.0000000000004118) | Methods paper | Percentage-based COD deficit to reconcile time- and velocity-derived versions | A-PM |
| 47 | Dos'Santos et al. (2017) *JSCR* | [10.1519/JSC.0000000000001535](https://doi.org/10.1519/JSC.0000000000001535) | 40 athletes, 180° turns with force plates on the last 2 contacts | Braking and propulsive forces, impulses and contact times on the penultimate and final contacts determine 180° COD speed | A-PM |
| 48 | Fox (2018) *Sports Med* | [10.1007/s40279-018-0931-3](https://doi.org/10.1007/s40279-018-0931-3) | Review: ACL risk vs performance in COD | Partial alignment, e.g. forefoot strike and trunk lean toward the cut | A-PM |
| 49 | **Singh et al. (2025)** *Sports Med* | [10.1007/s40279-025-02278-3](https://doi.org/10.1007/s40279-025-02278-3) | Systematic review, 13 studies (374 participants), 45–180° COD | Faster COD: shorter contact time, **higher approach and exit velocities**, larger braking and propulsive forces, trunk lean, lower centre of mass. **All tasks were pre-planned** | A-PM |
| 50 | Zhang et al. (2022) *Front Physiol* | [10.3389/fphys.2022.1027811](https://doi.org/10.3389/fphys.2022.1027811) | 103 soccer players; force–velocity profile, linear deceleration test, 505 | 10-m time strongly associated with 505; braking power moderately associated; sex differences | A-PM |
| 51 | Silva et al. (2026) *IJSPP* | [10.1123/ijspp.2026-0174](https://doi.org/10.1123/ijspp.2026-0174) | 52 professionals, 3,048 match COD events from GNSS, by angle; mixed-effects models | Entry ≈ 14.9 km/h, braking ≈ −4.2 m/s², decel-to-accel interval ≈ 0.6 s, re-acceleration ≈ 1.7 m/s²; angle associated with entry speed | A-PM |
| 52 | Churchill et al. (2015) *Sports Biomech* | [10.1080/14763141.2015.1024717](https://doi.org/10.1080/14763141.2015.1024717) | 7 sprinters, 3-D video, bend (r = 37.7 m) vs straight | Bend reduces speed by 4.7%, mainly via step frequency and length | A-PM |
| 53 | Churchill et al. (2018) *Sports Biomech* | [10.1080/14763141.2018.1427279](https://doi.org/10.1080/14763141.2018.1427279) | 9 sprinters in lanes 2/5/8 | Tighter radius gives > 2% speed loss; "some athletes are better able to accommodate tighter radii" | A-PM |
| 54 | Serpiello et al. (2018) *J Sports Sci* | [10.1080/02640414.2017.1411867](https://doi.org/10.1080/02640414.2017.1411867) | Ultra-wideband local positioning vs Vicon; linear and 45° COD drills | Speed and acceleration acceptable; **deceleration errors larger**; COD errors moderate to very large, worse at the court edge | A-PM |
| 55 | Fuchs et al. (2023) *Sports Biomech* | [10.1080/14763141.2022.2110513](https://doi.org/10.1080/14763141.2022.2110513) | Local positioning (50 Hz) vs Vicon | Peak deceleration agreement CCC 0.73, error ≈ 25%; time-series acceleration error ≈ 14% | A-PM |
| 56 | Luteberget et al. (2018) *Front Physiol* | [10.3389/fphys.2018.00115](https://doi.org/10.3389/fphys.2018.00115) | Local positioning validity indoors vs infrared cameras | Validity depends on the geometry of the setup (truncated) | A-PM |

**Synthesis.**
- Deceleration is mechanically distinct and important (Harper 2022), but **measured worst** by tracking systems (Serpiello 2018; Fuchs 2023), and its processing is under-reported (Ellens 2022).
- COD ability is conventionally *isolated* from speed with time-difference deficits (Nimphius 2016; Freitas 2022). These need only timing gates and **ignore the path and speed profile actually used**.
- Biomechanical determinants (Singh 2025) come from **force-plate lab tasks, pre-planned, small n**.
- Match COD has just begun to be characterised from tracking (Silva 2026, soccer).
- Bend sprinting shows that curvature limits speed and that individuals differ in tolerating curvature (Churchill 2018).
- **No retrieved study derived COD or braking capacity from combine trajectories, nor linked combine COD mechanics to in-game COD behaviour in American football.** We found **no validation study of NFL in-game tracking for deceleration.**

---

## 4. Movement variability and motor control

| # | Citation | DOI | Design / method | Key findings | Acc. |
|---|---|---|---|---|---|
| 57 | Davids et al. (2003) *Sports Med* | [10.2165/00007256-200333040-00001](https://doi.org/10.2165/00007256-200333040-00001) | Position paper (dynamical systems) | Variability is functional and adaptive, not just noise | A-PM |
| 58 | Bartlett, Wheat & Robins (2007) *Sports Biomech* | [10.1080/14763140701322994](https://doi.org/10.1080/14763140701322994) | Review | Elite athletes never reproduce identical patterns; questions "representative trials" | A-PM |
| 59 | Preatoni et al. (2013) *Sports Biomech* | [10.1080/14763141.2012.738700](https://doi.org/10.1080/14763141.2012.738700) | Review | How movement-variability quantification depends on task and question; open questions | A-PM |
| 60 | Riley & Turvey (2002) *J Mot Behav* | [10.1080/00222890209601934](https://doi.org/10.1080/00222890209601934) | Tutorial | "More variable ≠ more random"; variability structure reveals control | A-PM |
| 61 | **Müller & Sternad (2004)** *J Exp Psychol HPP* | [10.1037/0096-1523.30.1.212](https://doi.org/10.1037/0096-1523.30.1.212) | Tolerance–noise–covariation (TNC) decomposition relative to a solution manifold | Skill gains come from reduced noise, exploiting tolerance and, less so, covariation | A-PM |
| 62 | **Scholz & Schöner (1999)** *Exp Brain Res* | [10.1007/s002210050738](https://doi.org/10.1007/s002210050738) | Uncontrolled manifold (UCM) | Operational test of which task variables are stabilised | A-PM |
| 63 | **Todorov & Jordan (2002)** *Nat Neurosci* | [10.1038/nn963](https://doi.org/10.1038/nn963) | Stochastic optimal feedback control | Optimal control lets variability live in task-irrelevant dimensions | A-PM |
| 64 | Hiley et al. (2013) *Hum Mov Sci* | [10.1016/j.humov.2012.11.007](https://doi.org/10.1016/j.humov.2012.11.007) | 4 gymnasts × 10 repetitions | More elite gymnasts are *less* variable in mechanically important aspects and *more* variable in less important ones | A-PM |
| 65 | Cowin et al. (2022) *Sports Med Open* | [10.1186/s40798-022-00473-4](https://doi.org/10.1186/s40798-022-00473-4) | Scoping review | Framework distinguishing types of movement variability | A-PM |
| 66 | Möhler et al. (2020) *Eur J Sport Sci* | [10.1080/17461391.2019.1709561](https://doi.org/10.1080/17461391.2019.1709561) | UCM on running, 13 experts vs 12 novices, 20 cycles | No expertise difference in UCM ratio; novices showed more variance overall | A-PM |
| 67 | Mansourizadeh et al. (2020) *Gait Posture* | [10.1016/j.gaitpost.2020.01.013](https://doi.org/10.1016/j.gaitpost.2020.01.013) | COD coordination variability, groin pain vs controls | Altered coordination and higher variability with pain | A-PM |

**Synthesis.**
- Theory predicts that skilled performers show **low variability in task-relevant dimensions and tolerance elsewhere** (Todorov & Jordan 2002; Müller & Sternad 2004). Hiley 2013 supports this, but with n = 4.
- All of these analyses need **many repetitions of the same task per person** (10–20+).

## 5. Reliability, intra-individual variability (IIV) and location-scale models

| # | Citation | DOI | Design / method | Key findings | Acc. |
|---|---|---|---|---|---|
| 68 | Hopkins (2000) *Sports Med* | [10.2165/00007256-200030010-00001](https://doi.org/10.2165/00007256-200030010-00001) | Review | Typical error (within-subject SD, often as CV), systematic change and retest correlation | A-PM |
| 69 | Atkinson & Nevill (1998) *Sports Med* | [10.2165/00007256-199826040-00002](https://doi.org/10.2165/00007256-199826040-00002) | Review | Relative-reliability statistics depend on sample range; prefer absolute error tied to "analytical goals" | A-PM |
| 70 | Weir (2005) *JSCR* | [10.1519/15184.1](https://doi.org/10.1519/15184.1) | Tutorial | Choice of ICC form (whether systematic error is included); SEM | A-PM |
| 71 | Koo & Li (2016) *J Chiropr Med* | [10.1016/j.jcm.2016.02.012](https://doi.org/10.1016/j.jcm.2016.02.012) | Guideline | 10 ICC forms; report model, type and definition; interpretation bands | A-PM |
| 72 | Shrout & Fleiss (1979) *Psychol Bull* | [10.1037/0033-2909.86.2.420](https://doi.org/10.1037/0033-2909.86.2.420) | Methods | Six ICC forms with confidence intervals | A-PM |
| 73 | McGraw & Wong (1996) *Psychol Methods* | [10.1037/1082-989X.1.1.30](https://doi.org/10.1037/1082-989x.1.1.30) | ICC inference (cited for method only) | — | M |
| 74 | Currell & Jeukendrup (2008) *Sports Med* | [10.2165/00007256-200838040-00003](https://doi.org/10.2165/00007256-200838040-00003) | Review | Validity, reliability and sensitivity of performance tests | A-PM |
| 75 | Morral-Yepes et al. (2022) *JSCR* | [10.1519/JSC.0000000000003753](https://doi.org/10.1519/JSC.0000000000003753) | Systematic review, 42 studies | Agility-test ICC mostly 0.79–0.99 | A-PM |
| 76 | Altmann et al. (2019) *PLOS ONE* | [10.1371/journal.pone.0220982](https://doi.org/10.1371/journal.pone.0220982) | Systematic review, 90 studies / 167 soccer speed tests | Most tests ICC > 0.75 and CV < 3%; agility validity unstudied | A-PM |
| 77 | Warneke et al. (2025) *Eur J Appl Physiol* | [10.1007/s00421-025-05720-6](https://doi.org/10.1007/s00421-025-05720-6) | Simulation from real countermovement-jump data | ICC ≥ 0.9 can coexist with > 20% mean absolute % error; ICC ignores systematic error | A-PM |
| 78 | **Hedeker et al. (2008)** *Biometrics* | [10.1111/j.1541-0420.2007.00924.x](https://doi.org/10.1111/j.1541-0420.2007.00924.x) | **Mixed-effects location-scale model** | A subject-level random effect on the within-subject variance, correlated with the location effect | A-PM |
| 79 | Rast et al. (2012) *Multivar Behav Res* | [10.1080/00273171.2012.658328](https://doi.org/10.1080/00273171.2012.658328) | Location-scale model, N = 178 × 7 days | Individual differences in within-person variability, explained by covariates | A-PM |
| 80 | Dunton et al. (2013) *Int J Stat Med Res* | [10.6000/1929-6029.2013.02.02.05](https://doi.org/10.6000/1929-6029.2013.02.02.05) | Location-scale model, N = 14, twice-daily diaries over 6 weeks | Within-person variability in self-efficacy predicted behaviour beyond the mean | A-CR |
| 81 | Williams, Martin & Rast (2019) *PsyArXiv* | [10.31234/osf.io/hpq7w](https://doi.org/10.31234/osf.io/hpq7w) | Bayesian test of homogeneous within-person variance; individually varying ICCs | Within-person variance is heterogeneous in cognitive tasks, so a single ICC can misdescribe individuals (preprint) | A-CR |
| 82 | MacDonald, Nyberg & Bäckman (2006) *Trends Neurosci* | [10.1016/j.tins.2006.06.011](https://doi.org/10.1016/j.tins.2006.06.011) | Review | Intra-individual variability as a marker of underlying system state | A-PM |
| 83 | Brennan (2001) *Generalizability Theory* (Springer) | [10.1007/978-1-4757-3456-0](https://doi.org/10.1007/978-1-4757-3456-0) | G-theory reference (cited for method only) | — | M |

**Synthesis.**
- Reliability methodology is mature: ICC, typical error and the smallest worthwhile change. Its known pitfalls (Warneke 2025; Atkinson & Nevill 1998) argue for reporting absolute error.
- Combine-type agility tests are reliable when hand- or gate-timed (Mann 2016: ICC 0.91–0.97).
- **Location-scale models** treat each person's *within-person variance* as an individual trait, and in psychology that trait predicts behaviour beyond the mean (Dunton 2013). **We found no application to athletic movement tests.** They need many repetitions per person (7–40 in the cited studies).

## 6. Functional data analysis (FDA) of movement

| # | Citation | DOI | Design / method | Key findings | Acc. |
|---|---|---|---|---|---|
| 84 | Ramsay & Silverman (2005) *Functional Data Analysis* | [10.1007/b98888](https://doi.org/10.1007/b98888) | Textbook (method only) | — | M |
| 85 | Morris (2015) *Annu Rev Stat Appl* | [10.1146/annurev-statistics-010814-020413](https://doi.org/10.1146/annurev-statistics-010814-020413) | Review of functional regression | Basis representations; three classes of functional regression | A-CR |
| 86 | Yao, Müller & Wang (2005) *JASA* | [10.1198/016214504000001745](https://doi.org/10.1198/016214504000001745) | FPCA for sparse or irregular curves (method only) | — | M |
| 87 | Happ & Greven (2018) *JASA* | [10.1080/01621459.2016.1273115](https://doi.org/10.1080/01621459.2016.1273115) | Multivariate FPCA on different domains (method only) | — | M |
| 88 | Marron et al. (2015) *Stat Sci* | [10.1214/15-STS524](https://doi.org/10.1214/15-STS524) | Review of amplitude vs phase variation | Phase variability inflates variance and distorts principal components; L²-based alignment is unsatisfactory | A-CR |
| 89 | Warmenhoven et al. (2019) *Sports Biomech* 18:317 | [10.1080/14763141.2017.1392594](https://doi.org/10.1080/14763141.2017.1392594) | Methods with rowing data | Practical considerations: temporal normalisation, removing unwanted variation, preserving timing | A-PM |
| 90 | Warmenhoven et al. (2019) *Sports Biomech* | [10.1080/14763141.2017.1384050](https://doi.org/10.1080/14763141.2017.1384050) | Bivariate FPCA | "Movement signatures" from concurrent curves (force–angle) | A-PM |
| 91 | Donoghue et al. (2008) *MSSE* | [10.1249/MSS.0b013e31816c4807](https://doi.org/10.1249/mss.0b013e31816c4807) | FPCA on running kinematics, 12 + 12 participants | FDA retains curve information that discrete measures discard | A-PM |
| 92 | Ryan et al. (2006) *Sports Biomech* | [10.1080/14763141.2006.9628228](https://doi.org/10.1080/14763141.2006.9628228) | FDA tutorial (vertical jump) | Introduces registration and FPCA for kinematics | A-PM |
| 93 | Donà et al. (2009) *Sports Biomech* | [10.1080/14763140903414425](https://doi.org/10.1080/14763140903414425) | FPCA, 7 race walkers | Component scores reveal technique differences missed by mean ± SD curves | A-PM |
| 94 | White et al. (2022) *J Biomech* 140:111167 | [10.1016/j.jbiomech.2022.111167](https://doi.org/10.1016/j.jbiomech.2022.111167) | 512 preprocessing pipelines on 385 jumps (registration, padding, FPCA) | Registration helps *classification*; the effect on regression depends on the pipeline | A-PM |
| 95 | Kipp et al. (2020) *Sports Biomech* | [10.1080/14763141.2020.1820074](https://doi.org/10.1080/14763141.2020.1820074) | Bivariate FPCA of barbell paths, 6 lifters | Trajectory components correlate with performance | A-PM |
| 96 | Chu et al. (2020) *JQAS* | [10.1515/jqas-2019-0047](https://doi.org/10.1515/jqas-2019-0047) | **Model-based curve clustering (Bernstein basis, EM) of 33,967 NFL routes** | Recovers the route tree without labels | A-CR |

**Synthesis.**
- FDA and FPCA are established in sports biomechanics, but sample sizes are usually tiny (4–24 athletes).
- Results are **sensitive to registration and preprocessing** (Marron 2015; White 2022).
- In NFL tracking, curve clustering of routes works (Chu 2020).
- FPCA of *combine* trajectories is unexplored in what we retrieved.

## 7. Machine learning and statistics for sports tracking trajectories

| # | Citation | DOI | Design / method | Key findings | Acc. |
|---|---|---|---|---|---|
| 97 | Franks et al. (2015) *Ann Appl Stat* | [10.1214/14-AOAS799](https://doi.org/10.1214/14-aoas799) | Hierarchical spatial models of defensive skill, NBA tracking | Spatial characterisation of defensive skill | A-CR |
| 98 | Cervone et al. (2016) *JASA* 111:585 | [10.1080/01621459.2016.1141685](https://doi.org/10.1080/01621459.2016.1141685) | Multiresolution stochastic process; hierarchical spatiotemporal transition kernels | Real-time expected possession value | A-S2 |
| 99 | Yurko et al. (2020) *JQAS* 16:163 | [10.1515/jqas-2019-0056](https://doi.org/10.1515/jqas-2019-0056) | LSTM ball-carrier model in a continuous-time valuation framework (NFL) | Within-play expected-yards valuation | A-CR |
| 100 | Dutta, Yurko & Ventura (2020) *JQAS* | [10.1515/jqas-2020-0017](https://doi.org/10.1515/jqas-2020-0017) | Mixture models on tracking features | Unsupervised man/zone coverage labels | A-CR |
| 101 | Nguyen, Yurko & Matthews (2023) *Am Stat* 78:199 | [10.1080/00031305.2023.2242442](https://doi.org/10.1080/00031305.2023.2242442) | STRAIN: rate of distance closure (strain-rate analogy) + multilevel model | Interpretable pass-rush metric; predictive of pressure; stable over time | A-S2 |
| 102 | Nguyen et al. (2025) *Sci Rep* | [10.1038/s41598-025-85993-1](https://doi.org/10.1038/s41598-025-85993-1) | Contact windows to fractional tackles | Continuous tackle credit, including for defensive linemen | A-PM |
| 103 | Schmid et al. (2021) *Front Sports Act Living* | [10.3389/fspor.2021.669845](https://doi.org/10.3389/fspor.2021.669845) | Multi-agent imitation learning ("ghosting"), NFL season | League-average defensive trajectories; 81% accuracy on a pass-completion proxy | A-PM |
| 104 | Felsen, Lucey & Ganguly (2018) *ECCV* | [10.1007/978-3-030-01252-6_45](https://doi.org/10.1007/978-3-030-01252-6_45) | Conditional variational autoencoder for multi-agent motion | Personalised trajectory prediction | T |
| 105 | Wang et al. (2024) *Sports Med* 54:2663 | [10.1007/s40279-024-02030-3](https://doi.org/10.1007/s40279-024-02030-3) | Self-supervised axial-attention transformer, 90,524 NBA possessions | Masked pretraining improves play recognition | A-PM |
| 106 | Yue et al. (2022) *AAAI* | [10.1609/aaai.v36i8.20881](https://doi.org/10.1609/aaai.v36i8.20881) | TS2Vec hierarchical contrastive time-series representations | State of the art on the UCR/UEA archives | A-CR |
| 107 | Sakoe & Chiba (1978) *IEEE TASSP* 26:43 | [10.1109/TASSP.1978.1163055](https://doi.org/10.1109/TASSP.1978.1163055) | Dynamic time warping with a slope constraint | — | T |
| 108 | Gaspar et al. (2017) *J Biomech* | [10.1016/j.jbiomech.2017.02.025](https://doi.org/10.1016/j.jbiomech.2017.02.025) | DTW vs correlation, RMSE and Geers metrics | DTW captures phase *and* amplitude error | A-PM |
| 109 | Yu et al. (2022) *PLOS ONE* | [10.1371/journal.pone.0272848](https://doi.org/10.1371/journal.pone.0272848) | DTW clustering of basketball ball trajectories | Clusters align with scoring-rate context | A-PM |
| 110 | Torres-Ronda et al. (2022) *Sports Med Open* | [10.1186/s40798-022-00408-z](https://doi.org/10.1186/s40798-022-00408-z) | Narrative review of tracking systems | Metric selection and time-series segmentation need theory | A-PM |
| 111 | Ghasem et al. (2021) *Curr Sports Med Rep* | [10.1249/JSR.0000000000000873](https://doi.org/10.1249/jsr.0000000000000873) | Review of NFL tracking and biosensors | Limited evidence for injury prevention; mostly fan-facing use | A-PM |
| 112 | (HDSR, 2020) "Recreating the Game…" | [10.1162/99608f92.6e25c7ee](https://doi.org/10.1162/99608f92.6e25c7ee) | Tracking analytics, basketball and football (authors not retrieved) | — | M |

**Synthesis.**
- NFL-tracking statistics favours **interpretable, physically motivated metrics with multilevel models**, such as STRAIN (#101) and fractional tackles (#102), alongside deep sequence models (#99, #103).
- Self-supervised trajectory encoders (#105, #106) need tens of thousands of sequences. Our *athlete-level* n (~500) is the binding constraint, not the frame count.

## 8. Measurement error, mixed and hierarchical models, frontier estimation, optimal speed profiles

| # | Citation | DOI | Design / method | Key findings | Acc. |
|---|---|---|---|---|---|
| 113 | Frost & Thompson (2000) *JRSS-A* | [10.1111/1467-985X.00164](https://doi.org/10.1111/1467-985x.00164) | Compares 6 correction methods for regression dilution | Repeat measurements estimate the correction; the correlation-based estimator has lower variance | A-CR |
| 114 | Hutcheon, Chiolero & Hanley (2010) *BMJ* | [10.1136/bmj.c2289](https://doi.org/10.1136/bmj.c2289) | Regression dilution tutorial (method only) | — | M |
| 115 | Carroll, Ruppert & Stefanski (1995) *Measurement Error in Nonlinear Models* | [10.1007/978-1-4899-4477-1](https://doi.org/10.1007/978-1-4899-4477-1) | Measurement-error models (method only) | — | M |
| 116 | Newans et al. (2022) *IJSPP* | [10.1123/ijspp.2021-0496](https://doi.org/10.1123/ijspp.2021-0496) | Mixed models vs repeated-measures ANOVA, 472 rugby observations | Repeated-measures ANOVA would discard ≥ 48.7% of data | A-PM |
| 117 | Bates et al. (2015) *J Stat Softw* 67(1) | [10.18637/jss.v067.i01](https://doi.org/10.18637/jss.v067.i01) | lme4 (method only) | — | M |
| 118 | Gelman (2006) *Bayesian Anal* | [10.1214/06-BA117A](https://doi.org/10.1214/06-BA117A) | Priors for hierarchical variances | Inverse-gamma "noninformative" priors are problematic; prefer half-t or uniform on the SD | A-CR |
| 119 | de Paula Oliveira & Newell (2024) *Sci Rep* | [10.1038/s41598-024-51232-2](https://doi.org/10.1038/s41598-024-51232-2) | Mixed-effects + PCA athlete rating (NBA) | Hierarchical structure improves reliability of ratings | A-PM |
| — | Aigner, Lovell & Schmidt (1977) *J Econometrics* | [10.1016/0304-4076(77)90052-5](https://doi.org/10.1016/0304-4076(77)90052-5) | **Stochastic frontier** model (method only) | — | M |
| — | Koenker & Bassett (1978) *Econometrica* | [10.2307/1913643](https://doi.org/10.2307/1913643) | **Quantile regression** (method only) | — | M |
| — | Velenis & Tsiotras (2008) *J Optim Theory Appl* | [10.1007/s10957-008-9381-7](https://doi.org/10.1007/s10957-008-9381-7) | **Minimum-time speed profile** under acceleration limits on a path (method only) | — | M |
| — | Lipp & Boyd (2014) *Int J Control* | [10.1080/00207179.2013.875224](https://doi.org/10.1080/00207179.2013.875224) | **Minimum-time speed optimisation over a fixed path** (convex; method only) | — | M |

---

## 9. Cross-cutting conclusions

1. **The combine literature is old-data, old-method and weak-signal.**
   - It relies on stopwatch summaries, draft status as the outcome, many uncorrected tests and no measurement-error modelling.
   - Only one study in the 2023 systematic review used playing performance.
   - Tracking-based combine research is absent from the peer-reviewed literature we could retrieve.
2. **Sports science has the right measurement ideas, developed in other sports.** These are in-situ A–S profiling, deceleration and COD deficits, and reliability and typical error. None has been applied to linked combine→NFL tracking.
3. **Measurement quality is a first-order issue**, not a footnote. Deceleration and acceleration-side parameters are the least reliable (Fuchs 2023; Serpiello 2018; Jovanović 2024; Harper 2020), and acceleration processing is under-reported (Ellens 2022).
4. **Interpretability wins in NFL tracking research.** Recent accepted work (STRAIN, fractional tackles) pairs physically motivated metrics with multilevel models. This is a realistic template for our contribution.
5. **Novelty claims remain provisional** until the full texts of the closest papers have been read: Morin 2021, Miguens 2024, Clark 2019, Silva 2026, Nimphius 2016, Chu 2020, Hedeker 2008.

## Appendix — search log
Queries (verbatim) are stored with the raw search results in the session scratchpad. They are not committed, because the records contain publisher abstracts. Themes and queries:
- **T1 FDA:** "functional data analysis sprint running kinematics"; "functional principal component analysis biomechanics"; "functional data analysis sport performance curves"; "curve registration time warping functional data biomechanics".
- **T2 Variability:** "movement variability motor control sport review"; "movement variability skilled performance expertise"; "uncontrolled manifold analysis athletes"; "movement variability change of direction injury".
- **T3 Reliability:** "reliability intraclass correlation agility test"; "test-retest reliability sprint timing gates"; "generalizability theory sport performance measurement"; "measures of reliability sports medicine science"; "guideline selecting reporting intraclass correlation coefficients"; "reliability validity GPS local positioning system acceleration".
- **T4 A–S:** "in-situ acceleration-speed profile"; "force-velocity profile sprint running mechanical"; "mono-exponential sprint velocity model maximal sprint"; "40-yard dash velocity profile American football".
- **T5 Decel/COD:** "horizontal deceleration team sports review"; "change of direction deficit"; "change of direction biomechanics performance determinants"; "deceleration demands match play GPS"; "pro agility shuttle three-cone drill"; "maneuverability curvilinear sprint change of direction speed".
- **T6 Combine:** "NFL combine predict performance"; "NFL scouting combine draft"; "NFL combine career success"; "combine tests position American football players performance"; "NFL combine sprint performance return".
- **T7 ML:** "trajectory prediction team sports tracking deep learning"; "player tracking data American football"; "representation learning player trajectories sports"; "dynamic time warping sports movement"; "data-driven ghosting player tracking".
- **T8 Stats:** "measurement error regression calibration covariate error"; "linear mixed models repeated measures sports science"; "hierarchical Bayesian model athlete performance"; "draft position playing time sunk cost NFL".
- **Gap checks (G1–G14, H1–H4):** combine tracking / RFID / Next Gen Stats; intra-individual variability in athletes; test vs match peak speed; pro-agility and L-cone reliability; deceleration vs match performance; location-scale models in sport; FDA of team-sport tracking; NFL route clustering; regression dilution in athletes; elastic FDA; ultra-wideband validity; curvilinear sprint in American football; NFL tracking speed and injury; ML for the draft; DTW trial variability; A–S profile in American football; deceleration in American football; 40-yd reliability; American-football GPS match demands.
