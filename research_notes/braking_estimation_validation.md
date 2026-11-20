# Experiment 2 (Phase 2): Can Braking Be Estimated Reliably from 10 Hz Game Tracking?

*Notebook: `notebooks/05_real_data_movement_validation.ipynb` Part A · pipeline: `scripts/run_real_movement.py`
(run `experiments/real_movement/20261120T231614Z`) · figures `reports/figures/real_mov_*.png`. REG+POST,
post-snap frames only (15.7 M frames with valid derivatives), documented exclusions. No performance outcomes used.*

## 1. Bottom line
- **A robust braking envelope is measurable: the 99th percentile of deceleration at speed ≥ 2 yd/s (D99).**
  - Insensitive to the estimator: ρ ≥ 0.995 with the reference across smoothing windows, speed-derivative methods, 5 Hz, and injected noise.
  - Physically plausible: player range 2.9–6.5 yd/s²; none > 12.
  - Stable across seasons: ρ 0.94–0.96.
  - Converges with about 50 plays.
- **Its ability to discriminate players *within* a position is only moderate.** Within-position split-half reliability (Spearman–Brown): DL 0.93, TE 0.72, DB 0.69, OL 0.67, WR 0.64. Pooled reliability (0.97) is inflated by between-position differences.
- **Single-frame maximum braking is not measurable:** implausible (> 12 yd/s²) for 44% of players with ≥ 100 plays.
- **D99 is a *demonstrated game envelope*, not braking capacity.**
  - It is far below what the same athletes do in combine agility drills (Experiment 4).
  - It barely relates to combine braking within position (ρ 0.04–0.12).

## 2. Estimators compared
| Variant | Method |
|---|---|
| pos5 / pos7 / pos9 | tangential acceleration a_t = (v·a)/\|v\| from Savitzky–Golay derivatives of x, y (window 5/7/9 frames, quadratic) |
| speed_sg7 | SG derivative of the provided speed `s` |
| speed_diff | central difference of the provided `s` |
| noise0.01 / noise0.02 | pos7 after adding N(0, σ²) position noise |
| 5hz | every second frame, SG window 5 |
| provided `a` | **not usable for braking**: an unsigned total-acceleration magnitude (Phase 1) |

## 3. Frame level: agreement and implausibility
| Variant | Frame r with pos7 | % frames with \|a_t\| > 12 yd/s² | Mean p99 braking | Mean p99.9 braking |
|---|---|---|---|---|
| pos5 | 0.982 | 0.023 | 5.04 | 7.21 |
| pos7 | 1 | 0.0095 | 4.88 | 6.72 |
| pos9 | 0.996 | 0.002 | 4.76 | 6.43 |
| speed_sg7 | 0.976 | 0.0002 | 4.57 | 6.14 |
| speed_diff | 0.974 | 0.0011 | 4.98 | 6.87 |
| noise 0.01 / 0.02 | 0.994 / 0.977 | 0.0095 / 0.0097 | 4.91 / 4.98 | 6.75 / 6.85 |
| 5 Hz | 0.994 | 0.0021 | 4.79 | 6.43 |

- **Smoothing and differentiation shift the level by about ±3–5%**: narrower windows produce larger braking values.
- They also change the implausible-frame rate by 10×.
- The 12 yd/s² threshold (≈ 11 m/s²) is a stated assumption.

## 4. Separating braking from turning
Braking frames (a_t < −3 yd/s², speed ≥ 2) are classed by path curvature.

| Position | Class | Median braking | Median a_n | Share of \|a\|² from turning | r(provided `a`, our \|a\|) |
|---|---|---|---|---|---|
| WR | straight | 3.85 | 0.48 | 0.01 | 0.61 |
| WR | sharp | 4.14 | 3.00 | **0.32** | 0.59 |
| DB | sharp | 3.99 | 2.96 | 0.33 | 0.64 |
| OL | sharp | 3.43 | 1.88 | 0.22 | 0.36 |

All positions are in notebook 05 §A3.
- **In sharp turns, a fifth to a third of the total acceleration is turning, not braking.** Any braking measure built on the provided `a` would be contaminated.
- The provided `a` agrees only moderately with our acceleration-vector magnitude (r 0.24–0.67 during braking). The vendor's smoothing differs from ours, which is **another reason not to use `a`**.
- Speed lost while turning is still longitudinal (a_t). Reported separately: D99_straight (κ < 0.05 yd⁻¹) and D99_turn (κ ≥ 0.2 yd⁻¹). Median D99_turn ≥ D99_straight in every position.

## 5. Player level (≥ 100 plays, n = 307)
| Position | n | D99 | D99_straight | D99_turn | Dmax (single frame) |
|---|---|---|---|---|---|
| DB | 74 | 5.47 | 5.33 | 5.81 | 15.3 |
| DL | 78 | 4.26 | 4.14 | 4.35 | 7.89 |
| OL | 70 | 3.32 | 3.24 | 3.37 | 6.40 |
| TE | 22 | 5.24 | 5.00 | 5.67 | 14.8 |
| WR | 63 | 5.94 | 5.47 | 6.79 | 18.7 |

Values are medians, in yd/s².

**Estimator sensitivity (player D99 vs pos7):**
- Rank ρ 0.995–0.999 for every variant.
- Level ratios: 0.96 (speed_sg7) to 1.03 (pos5).
- **Rankings are robust; absolute level depends on the processing (±4%).**

**Reliability (Spearman–Brown, game-parity halves, pooled):**
- D99 0.97, D99_straight 0.94–0.95, D99_turn 0.96–0.97 (all variants); Dmax 0.77–0.92.
- **Within position (D99, pos7):** WR 0.64, TE 0.72, OL 0.67, DL 0.93, DB 0.69.

**Season to season:** D99 ρ 0.96 (2023→24, n = 65) and 0.94 (2024→25, n = 139); D99_straight 0.89–0.90. These are pooled across positions.

**Exposure / censoring** (231 players with ≥ 300 plays, random play subsets):
- The D99 ratio to its full-data value is 0.95 at 10 plays, 0.98 at 25, 0.99 at 50, and 1.00 at 200.
- Dmax keeps rising with more plays (median 5.4 → 8.3 yd/s²). The maximum is an extreme-value statistic, not a capacity.

**Combine vs game braking** (same players):
- Agility drills: pooled ρ 0.41, **within position 0.04** [−0.15, 0.23].
- Skill drills: pooled 0.55, within position 0.12 [0.01, 0.23].

## 6. Can the data support reliable braking estimates?
| Criterion | Result |
|---|---|
| Robust to smoothing / differentiation / 5 Hz / noise (ranking) | ✅ ρ ≥ 0.995 |
| Level stable to processing | ⚠️ ±3–5% |
| Physically plausible | ✅ for D99; ❌ for single-frame max |
| Separable from turning | ✅ via a_t / a_n decomposition and curvature classes |
| Reliable within position | ⚠️ 0.64–0.93 |
| Stable across seasons | ✅ (pooled) |
| Equals braking *capacity* | ❌ not demonstrable: the game envelope is far below drill demands and does not track combine braking |

**Conclusion:** use D99, from a_t not the provided `a`, as a *game braking-demand / demonstrated-braking* descriptor. **Do not use it as the athlete's braking capacity D** in Candidate C; Experiment 4 shows why.

## 7. Limitations
- **True deceleration is unknowable here:** no validation study of NGS deceleration accuracy was found (Phase 1.5).
- The noise injection tests robustness to *additional* noise only, not to the vendor's unknown filter.
- The 5 Hz test is a subsample of the already-smoothed 10 Hz signal.
- Role confounding: what a player is asked to do sets the braking they demonstrate.
