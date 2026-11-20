# Experiment 3 (Phase 2): Can Turning / Lateral Constraints Be Estimated from Game Trajectories?

*Notebook: `notebooks/05_real_data_movement_validation.ipynb` Part B · pipeline `scripts/run_real_movement.py`
(run `experiments/real_movement/20261120T231614Z`) · figures `reports/figures/real_mov_speed_curvature.png`,
`real_mov_exposure_envelopes.png`. A theoretical friction limit is **not** assumed measurable: every quantity below
is a *demonstrated envelope*. No performance outcomes used; `player_play` supplies context only.*

## 1. Bottom line
- **A population-level lateral envelope exists and behaves like a constant lateral-acceleration limit.**
  - The 99th-percentile curvature falls as v^−2 in every position: log–log slopes −1.95 to −2.10 (99th pct), −2.07 to −2.15 (99.9th pct).
  - The level is position-specific: 99th-percentile a_n about 3.8–4.1 yd/s² (OL) to 6.2–7.0 yd/s² (WR).
- **Individual lateral envelopes (C99) are measurable but context-dependent, so they are not a fixed capacity.**
  - **Consistent across estimators:** positions vs provided heading, player-level ρ 0.997.
  - **Stable over seasons:** ρ 0.95–0.96, pooled.
  - **Within-position reliability varies:** WR 0.84, TE 0.86, DL 0.88, but DB 0.60 and OL 0.47.
  - **Context dependence:** a WR's C99 is +0.97 yd/s² [0.82, 1.07] higher on breaking than vertical routes, with only ρ = 0.47 agreement in rank. DB pass vs run: +0.65 [0.54, 0.79], ρ = 0.19.
- **A lateral limit for Candidate C cannot be taken from game data as a capacity.** Game envelopes are below drill demands (Experiment 4).

## 2. Estimators
- **a_n from positions** (SG window 5/7/9): |v × a|/|v|.
- **a_n from the provided heading:** s · |d dir/dt|, an independent source.
- Plus noise injection and 5 Hz.
- Curvature κ = a_n / v² (speed floored at 0.5 yd/s).

| Variant | Frame r with pos7 | % frames a_n > 15 yd/s² | Player C99 ρ with pos7 | Median ratio |
|---|---|---|---|---|
| heading-based | 0.957 | 0.0001 | 0.997 | 1.03 |
| pos5 / pos9 | 0.977 / 0.994 | 0.0055 / 0.0001 | 0.998 / 0.999 | 1.03 / 0.98 |
| noise 0.02 | 0.945 | 0.0013 | 0.998 | 1.02 |
| 5 Hz | 0.991 | 0.0001 | 0.999 | 0.97 |

## 3. Speed–curvature relationship
Pooled per position, 0.5 yd/s bins over 2–8 yd/s. Slope of log κ(percentile) on log v, with 95% bootstrap CI over bins.

| Position | 99th pct | 99.9th pct |
|---|---|---|
| WR | −1.95 [−2.00, −1.89] | −2.07 [−2.10, −2.04] |
| TE | −2.02 [−2.10, −1.96] | −2.10 [−2.15, −2.06] |
| OL | −2.05 [−2.24, −1.94] | −2.11 [−2.23, −2.01] |
| DL | −2.04 [−2.21, −1.92] | −2.07 [−2.17, −1.99] |
| DB | −2.10 [−2.14, −2.06] | −2.15 [−2.17, −2.11] |

- A slope of −2 is what a speed-independent lateral limit implies.
- **The a_n envelope is not perfectly flat:**
  - WR rises from about 6.2 to 7.0 yd/s² between 2 and 6.5 yd/s, then falls.
  - DL/OL fall at the highest speeds.
- Constant C is therefore a reasonable first approximation for *population* envelopes. A mild speed dependence, or simply fewer high-speed turning opportunities, cannot be excluded.

## 4. Context dependence
Same players; ≥ 30 plays in each context; median within-player difference with 95% CI.

| Position | Measure | Contrast | n | Median difference | Cross-context ρ |
|---|---|---|---|---|---|
| WR | C99 | breaking − vertical routes | 61 | **+0.97** [0.82, 1.07] | 0.47 |
| TE | C99 | breaking − vertical | 11 | +0.68 [0.43, 0.92] | 0.63 |
| DB | C99 | pass − run plays | 74 | +0.65 [0.54, 0.79] | 0.19 |
| DL | C99 | pass − run | 84 | +0.54 [0.38, 0.63] | 0.74 |
| OL | C99 | pass − run | 71 | +0.13 [0.03, 0.27] | 0.13 |

**The demonstrated lateral envelope depends on what the play asks for.** It is a *task* property as much as a *player* property.

## 5. Stability and uncertainty
- **Split-half (Spearman–Brown, pooled):** C99 0.97; κ99 at 2–4 / 4–6 / 6–8 yd/s: 0.94 / 0.90 / 0.92; Cmax 0.88–0.89.
- **Within position (C99):** WR 0.84 [split-half ρ 0.55–0.85], TE 0.86, OL 0.47, DL 0.88, DB 0.60.
- **Season to season:** C99 ρ 0.96 (2023→24, n = 65), 0.95 (2024→25, n = 139).
- **Exposure:** C99 reaches 92% of its full-data value with 10 plays, 97% with 25 and 99% with 50 plays. The maximum keeps growing.
- **Combine vs game lateral** (same players): pooled ρ 0.30 (agility) / 0.75 (skill drills), within position only 0.08 / 0.14.

## 6. Answers to the experiment's questions
| Question | Answer |
|---|---|
| Different movement contexts? | Yes — the envelope shifts by 0.1–1.0 yd/s² between contexts, and ranks are only partly preserved |
| Speed–curvature relation? | Envelope ≈ C/v² (slope ≈ −2) in all positions |
| Are estimated constraints stable? | Population envelopes: yes. Individual C99: stable over time and estimators, but context-dependent and only moderately reliable within OL/DB |
| Uncertainty quantified? | Bootstrap CIs for slopes, reliabilities and contrasts (above) |
| Friction limit measurable? | **No.** Envelopes are lower bounds shaped by tasks; maximum values are extreme-value artefacts |

## 7. Limitations
- **Curvature at 10 Hz is biased low in tight turns.** Phase 1.6 showed smoothing rounds corners; this applies equally here.
- Pooled-bin slopes are population summaries, not individual laws.
- Contexts come from `player_play` labels (route_ran, pass/run), and routes exist only for WR/TE.
- Lateral capacity cannot be validated against ground truth.
