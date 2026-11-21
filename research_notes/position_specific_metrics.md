# Phase 3, Task 3: Position-Specific, Opportunity-Adjusted Metrics and Their Measurement Quality

*Run `experiments/phase3_screening/20261121T010253Z` (`opportunities_*.parquet`, `context_*.parquet`,
`outcome_reliability.parquet`, `speed_demand.parquet`, `predictor_structure.parquet`). REG only.
**Outcome-blind:** reliabilities and opportunity structure only. No outcome was correlated with any combine measure.*

## 1. Opportunity definitions (the denominators)
| Position | Opportunity | Definition | Median per player (all seasons) |
|---|---|---|---|
| WR / TE | route | pass play with `route_ran` | WR 277, TE 183 |
| DL | pass rush | `player_get_off` non-null | 201 |
| OL | pass block | `pass_rushers_encountered` non-null | 424 |
| DB | coverage snap | pass play, `coverage_assignment` not null and ≠ `NO_ASSIGNMENT` | 253 |
| DL / DB | run snap | `pass_result == ""` | DL 153, DB 170 |

**Every outcome is a per-opportunity rate or mean, never a raw total.** Examples: targets per route, pressures per rush, pressures allowed per pass block.

## 2. Context mix within opportunities (why context adjustment is required)
- **WR routes:**
  - Route depth: 13.5k deep (GO / POST / CORNER / WHEEL), 17.5k short (SLANT / HITCH / OUT / IN / FLAT / ANGLE / SCREEN), 4.5k other.
  - Coverage: 9.7k vs man, 25.7k vs zone.
- **TE routes:** 1.9k deep, 4.8k short.
- **DL rushes:** EDGE 20.2k, interior 13.1k.
- **OL blocks:** T 20.1k, G 21.9k, C 6.4k.
- **DB coverage:** deep zone 18.1k, man 10.0k, underneath zone 10.5k.
- **Time to throw** (pass plays with a throw): < 2.5 s ≈ 40%, 2.5–3.5 s ≈ 40%, ≥ 3.5 s ≈ 20%, at every position.
- **Context explains a large share of play-level variance:**
  - separation: R² 0.24 (man vs zone medians alone differ by 1.6 yd);
  - WR route max speed: R² 0.50;
  - get-off: R² 0.23;
  - pressure: R² 0.11.

**Context adjustment.** Play-level OLS residuals on one-hot context, fitted pooled within position, then averaged per player ("adj").
- Covariates are pre-snap or exogenous: route, coverage shell, down, distance bin, formation, motion, alignment, season, and time-to-throw bin where relevant.
- Post-snap outcome-like variables are never covariates. Examples: `pass_length`, and `dropback_duration` for OL, which is truncated by pressure.
- **Time to throw is a borderline covariate.** It is partly caused by coverage and pressure, so it is included only as a sensitivity term in the later models.

## 3. Reliability of candidate player-level metrics
Players with ≥ 100 opportunities; game-parity split halves with ≥ 50 each, Spearman–Brown corrected; 95% bootstrap CI over players.

| Position | Metric | Layer | Eligible n | Split-half: raw | Split-half: context-adjusted [95% CI] | Season → season ρ (adj) |
|---|---|---|---|---|---|---|
| WR | separation at pass forward | performance | 63 | 0.81 | **0.61** [0.28, 0.78] | 0.47 |
| WR | separation, deep routes | performance | 41 | 0.71 | 0.61 [0.17, 0.83] | 0.28 |
| WR | separation, short routes | performance | 44 | 0.75 | **0.22** [−0.66, 0.60] | 0.31 |
| WR | targets per route | performance | 63 | 0.83 | **0.78** [0.60, 0.88] | 0.41 |
| WR | route max speed before throw | expression | 63 | 0.93 | **0.91** [0.83, 0.95] | 0.79 |
| TE | separation | performance | 21 | 0.74 | 0.45 [−0.63, 0.83] | −0.08 |
| TE | targets per route | performance | 21 | 0.71 | 0.64 [0.00, 0.90] | 0.27 |
| TE | route max speed | expression | 21 | 0.94 | 0.95 [0.85, 0.99] | 0.75 |
| DL | get-off (NGS) | expression | 69 | 0.96 | **0.90** [0.82, 0.94] | 0.67 |
| DL | tracked 1-s forward displacement | expression | 69 | 0.96 | 0.91 [0.85, 0.95] | 0.75 |
| DL | pressure per rush | performance | 69 | 0.62 | **0.50** [0.18, 0.72] | 0.30 |
| DL | tackles per run snap | performance | 58 | 0.53 | 0.47 [0.13, 0.69] | 0.39 |
| OL | pressure allowed per block | performance | 66 | 0.62 | 0.47 [0.17, 0.70] | 0.40 |
| OL | peak pressure probability allowed | performance | 66 | 0.84 | **0.69** [0.44, 0.84] | 0.32 |
| OL | lateral displacement at 1.5 s | expression | 66 | 0.89 | 0.89 [0.80, 0.94] | 0.28 |
| DB | play max speed (coverage) | expression | 67 | 0.71 | 0.68 [0.44, 0.82] | 0.62 |
| DB | … in man coverage | expression | 35 | 0.77 | 0.76 [0.50, 0.89] | 0.59 |
| DB | … in deep zone | expression | 53 | 0.66 | 0.75 [0.54, 0.89] | 0.57 |
| DB | cushion | deployment | 52 | 0.95 | 0.97 [0.93, 0.99] | 0.67 |
| DB | tackles per run snap | performance | 63 | 0.62 | 0.39 [−0.06, 0.66] | 0.49 |

### What the table says
1. **Speed-expression metrics are highly reliable (0.88–0.95). Performance metrics are not (0.47–0.78).**
   - Any combine → performance correlation will be attenuated by √(rel_x · rel_y).
   - With rel_x ≈ 0.99 (tracked peak speed) and rel_y = 0.5, the ceiling multiplier is ≈ 0.70.
2. **Context adjustment removes much of what looked like a player trait.**
   - WR separation reliability falls from 0.81 to 0.61, and **short-route separation from 0.75 to 0.22**.
   - Raw separation differences between WRs are largely *deployment*: route mix and man/zone exposure.
   - This matters for the scientific question. A combine–raw-separation correlation could simply reflect how fast players are used, not what speed produces.
3. **TE player-level metrics are not estimable with useful precision** (n = 21; adjusted CIs include 0). TE stays descriptive.
4. **Year-to-year stability of performance rates is modest** (adj 0.28–0.49). Pooling seasons per player is necessary.

## 4. Speed demand: how often game tasks reach a player's own top speed
- Share of plays whose max speed is ≥ 90% of the player's own top-5 mean.
- Uses no combine data.

| Position | Context | Plays | Median play max speed (yd/s) | Share ≥ 90% of own top |
|---|---|---|---|---|
| WR | deep routes | 13,484 | 7.92 | **0.17** |
| WR | short routes | 17,375 | 6.49 | 0.01 |
| TE | deep routes | 1,875 | 7.19 | **0.19** |
| TE | short routes | 4,649 | 5.91 | 0.03 |
| DB | man | 10,025 | 6.63 | 0.07 |
| DB | deep zone | 18,121 | 5.95 | 0.03 |
| DB | underneath zone | 10,499 | 5.56 | 0.02 |
| DL | pass / run | 30,793 / 21,634 | 4.61 / 3.50 | 0.03 / 0.01 |
| OL | pass / run | 51,921 / 34,316 | 3.23 / 3.01 | 0.01 / 0.01 |

**Speed demand differs by more than an order of magnitude between contexts *within* a position** (WR deep vs short: 17% vs 1%). It is a natural, measurable moderator for "where should combine speed matter?".

## 5. Predictor side: what combine tracking adds beyond the official 40 (within position)
| Position | ρ(tracked peak speed, official 40) | Unique variance of peak speed | ρ(peak speed, 10-yd split) | ρ(peak speed, weight) |
|---|---|---|---|---|
| WR (94) | −0.83 | **34%** | −0.33 | −0.26 |
| TE (34) | −0.91 | 17% | −0.56 | −0.06 |
| OL (95) | −0.89 | 19% | −0.57 | −0.06 |
| DL (93) | **−0.97** | **5%** | −0.87 | **−0.80** |
| DB (102) | −0.80 | **36%** | −0.47 | −0.22 |

- **"Incremental value beyond the 40" is testable only for WR and DB**, where about a third of peak-speed variance is not in the 40 time.
- **In DL, the forty, the 10-yd split, peak speed and body weight are essentially one dimension (|ρ| 0.80–0.97).**
  - DL combine speed is largely a proxy for body type, which matches edge vs interior role.
  - So the Phase 2 DL speed transfer (ρ 0.73) may partly reflect *role sorting*, not speed translation.
- **In WR, top speed and early acceleration (10-yd split) are nearly separate traits** (ρ −0.33). The 40 time mixes them.

## 6. Recommended position-specific metric set for modelling
| Position | Primary performance outcome | Secondary | Speed-expression (mechanism) | Status |
|---|---|---|---|---|
| WR | separation at pass forward, **deep routes** (context-adjusted) | targets per route | route max speed before throw | adequate (n 41–63) |
| TE | — | — | route max speed | descriptive only (n ≈ 20) |
| DL | pressure per rush | — | get-off / 1-s forward displacement | adequate (n 53–69); predictors collinear with weight |
| OL | peak pressure probability allowed | pressure allowed per block | lateral displacement at 1.5 s | adequate n, weak theory for speed |
| DB | — (no coverage outcome) | tackles per run snap (weak) | play max speed by coverage role | expression only |
