# Experiment 1 (Phase 2): Combine-to-Game Capacity Transfer — Real Data

*Notebook: `notebooks/04_real_data_capacity_validation.ipynb` · pipeline: `scripts/run_real_capacity.py`
(run `experiments/real_capacity/20261120T230324Z`) · figures: `reports/figures/real_cap_*.png`.
No performance or career outcomes used. Capacity is treated separately from execution, measurement error and
performance. Combine and game capacity are **not** assumed to be equal.*

## 1. Bottom line
- **Top speed transfers partially; acceleration does not (as currently measured).**
  - Within position, combine-40 peak speed vs game maximum speed (≥ 100 plays): ρ = 0.73 DL, 0.68 TE, 0.58 WR, 0.38 OL, and **0.13 DB** (95% CI −0.11 to 0.36).
  - Combine A0 vs game A0: ρ −0.05 to 0.43, and every 95% CI includes 0.
- **Level does not transfer.**
  - Game maximum speed is lower than the combine peak for almost every player: 0–5% exceed it.
  - Median ratio: 0.80 (OL) to 0.92 (DB).
  - Mean difference: −0.95 (DB) to −2.05 yd/s (OL).
  - "Combine capacity = game capacity" is rejected as an identity, as instructed we would not assume.
- **Simple game peak-speed measures are more reliable and transfer better than model-based S0.**
  - The simulation's preferred S0 estimator (SIMEX-binned) has lower split-half reliability (0.79 vs 0.91–0.98) and weaker transfer (WR ρ 0.15 vs 0.58).
  - **Game A0 is not measurable** with the current binning method: 22% of high-exposure players get A0 > 15 yd/s².
- **Exposure matters.**
  - Below 50 plays, within-position transfer is invisible (ρ ≈ 0.06).
  - The game/combine speed ratio rises by 0.066 per tenfold increase in plays (95% CI 0.049–0.083).

## 2. Sample sizes and matching coverage
Identity via verified `nfl_id` (Phase 1).

| Position | Combine participants | With 40 tracking | With game tracking | Both | Both, ≥ 50 plays | Both, ≥ 100 plays | Both, ≥ 300 plays |
|---|---|---|---|---|---|---|---|
| DB | 122 | 102 | 96 | 81 | 68 | 63 | 53 |
| DL | 118 | 93 | 98 | 77 | 70 | 61 | 39 |
| OL | 121 | 95 | 91 | 73 | 63 | 57 | 50 |
| TE | 42 | 34 | 33 | 28 | 20 | 19 | 8 |
| WR | 107 | 94 | 84 | 74 | 64 | 57 | 37 |
| **All** | **510** | **418** | **402** | **333** | **285** | **257** | **187** |

- Game data: REG + POST, 2023–25.
- 10 player-play sequences were excluded: 7 from the faulty game, 3 with speed > 12.5 yd/s.
- The main analyses use players with both measurements and ≥ 100 plays (n = 257). TE (19) is underpowered.

## 3. Measurement quality (measurement uncertainty, kept separate)
### Combine 40
- 793 attempts, 792 fitted with the mono-exponential; median R² 0.996.
- Two-attempt reliability (n = 374; within-session, so optimistic):

| Measure | Test–retest r [95% CI] | Typical error |
|---|---|---|
| peak speed | 0.987 [0.984, 0.989] | 0.09 yd/s (0.9%) |
| S0 (fit) | 0.934 [0.903, 0.957] | 0.24 yd/s (2.2%) |
| A0 (fit) | **0.454** [0.328, 0.632] | 0.94 yd/s² (11.2%) |
| τ | **0.364** [0.259, 0.490] | 11.8% |

**The acceleration side of the combine profile is not reliable.**

### Game measures
Split-half reliability uses game-parity halves, Spearman–Brown corrected.

| Measure | 20–99 plays | 100–299 plays | ≥ 300 plays |
|---|---|---|---|
| max observed speed | 0.87 | 0.91 | 0.95 |
| 2nd-best play max | 0.84 | 0.95 | 0.97 |
| mean of top-5 play maxima | 0.86 | 0.97 | 0.98 |
| S0, Morin binning | 0.78 | 0.82 | 0.80 |
| S0, SIMEX-binned | 0.73 | 0.80 | 0.79 |
| A0, binning | 0.67 | 0.69 | 0.83 |
| A0, SIMEX | 0.54 | 0.62 | 0.81 |

**Implausible values:**
- 57/402 players have binned A0 > 15 yd/s², and 20 have S0 > 14 yd/s².
- 36 have SIMEX-S0 *below* their own observed maximum.
- **Contrary to the simulation's expectation, implausible A0 is concentrated at high exposure:** 22% of players with > 300 plays, vs 0–7% below that. More frames give noise more opportunity to inflate low-speed bin maxima.

## 4. Transfer (ranking): within-position Spearman ρ [95% bootstrap CI], players with ≥ 100 plays
| Pair | WR (57) | TE (19) | OL (57) | DL (61) | DB (63) |
|---|---|---|---|---|---|
| combine peak ↔ game max | **0.585** [0.37, 0.74] | **0.684** [0.30, 0.88] | 0.381 [0.11, 0.61] | **0.734** [0.61, 0.82] | 0.132 [−0.11, 0.35] |
| combine S0 ↔ game S0 (SIMEX) | 0.147 [−0.11, 0.38] | 0.364 [−0.10, 0.69] | 0.334 [0.08, 0.56] | 0.395 [0.17, 0.59] | 0.226 [−0.04, 0.47] |
| combine A0 ↔ game A0 (binned) | 0.193 [−0.09, 0.43] | 0.428 [−0.08, 0.79] | −0.051 [−0.30, 0.21] | 0.077 [−0.18, 0.31] | 0.157 [−0.08, 0.39] |

- Pooled across positions, peak ↔ max reaches ρ = 0.85. **That is position composition, not transfer.**
- Disattenuating for measurement unreliability changes little for speed (DL 0.77, WR 0.61). Unreliability is not the explanation for weak transfer.

## 5. Agreement (level): game − combine, players with ≥ 100 plays
| Position | n | Mean game max − combine peak (yd/s) | ±1.96 SD | Median ratio | Share exceeding combine peak |
|---|---|---|---|---|---|
| DB | 63 | −0.95 | 1.07 | 0.917 | 3.2% |
| DL | 61 | −1.75 | 1.14 | 0.827 | 0% |
| OL | 57 | −2.05 | 1.23 | 0.798 | 0% |
| TE | 19 | −1.32 | 1.10 | 0.865 | 5.3% |
| WR | 57 | −1.12 | 0.63 | 0.898 | 0% |

**Exposure model** (OLS with HC3 standard errors; nuisance only): ratio = 0.728 + 0.066·log10(plays) + position effects.
- log-plays effect 95% CI [0.049, 0.083].
- OL −0.139 and DL −0.078 relative to DB.

## 6. Exposure and transfer (within-position ρ, peak ↔ max)
| Plays | n | ρ [95% CI] |
|---|---|---|
| 10–49 | 38 | 0.06 [−0.27, 0.39] |
| 50–99 | 28 | 0.45 [0.10, 0.71] |
| 100–299 | 70 | 0.57 [0.39, 0.70] |
| ≥ 300 | 187 | 0.45 [0.33, 0.56] |

## 7. Individual differences
- **At the same combine peak, game top speed varies with a residual SD of 0.31 yd/s (WR) to 0.63 yd/s (OL).** That is comparable to or larger than the between-player spread of combine peaks.
- The residual mixes role and assignment, exposure, measurement error, and any genuine "expression" difference. **It is not yet interpretable as execution.**
- Examples: DB game speeds barely track combine speed (slope 0.33); TE and DL track it closely (slopes 1.10 and 0.91).

## 8. Limitations
- Game maxima are **demonstrated** speeds, constrained by role and exposure. They are not capacity.
- WR/TE game data are route-running dropbacks only.
- Combine reliability is same-day only.
- TE n = 19.
- SIMEX's noise SD (0.01 yd) comes from simulation calibration, not validation.
- A0 binning is implausible on real data, and its high-exposure failure was **not predicted** by Phase 1.6. The simulator's noise model is incomplete: real high-frequency acceleration noise is under-represented.

## 9. Implications for the programme
- Use **robust peak-speed measures** (top-5 play-maxima mean) as the game speed-capacity proxy, with exposure ≥ 50–100 plays.
- **Do not use game A0** until a better acceleration estimator is validated. The combine A0 from the 40 is itself only moderately reliable (r = 0.45).
- The idea that combine capacity "transfers" holds for speed rankings in WR, TE and DL. It is weak for OL and absent for DB.
