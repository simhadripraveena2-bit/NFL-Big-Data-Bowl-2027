# Experiment 4 (Phase 2): Candidate C Execution Cost on Real Combine Drills

*Notebook: `notebooks/05_real_data_movement_validation.ipynb` Part C · pipeline `scripts/run_real_combine_execution.py`
(run `experiments/real_execution/20261120T231805Z`) · module `src/nfl_bdb/features/change_direction_cost.py`
(`real_drill_segment`) · figures `real_mov_execution_vs_forty.png`, `real_mov_execution_sensitivity.png`.
No performance outcomes used. **Execution cost is not combined with capacity or performance in any score.***

## 1. Bottom line
- **The method runs on real data, and its *rankings* are robust to processing choices.**
  - Smoothing window: ρ ≥ 0.97.
  - Assumed braking/lateral limits within a 5–9 yd/s² grid: ρ 0.92–0.99.
  - Onset rule and stop modelling: ρ 0.85–0.89.
- **It is not yet a validated measure.** Three problems are each disqualifying for now:
  1. **Timing validity.** Tracking gate times correlate only moderately with official times: 3-cone r = 0.65 [0.36, 0.89], shuttle r = 0.40 [0.27, 0.69]. Shuttle drill time has **negative** test–retest r in 28 players with two valid attempts.
  2. **The limits are not identifiable.** Braking/lateral capacity cannot be estimated from the drills without circularity. Game-derived envelopes (Experiments 2–3) are far below drill demands, so they produce physically impossible (negative) execution costs for 44–79% of attempts and re-rank athletes (ρ 0.49–0.61 vs reference).
  3. **Reliability is weak.** 3-cone E r = 0.58 [0.39, 0.78] (n = 32); shuttle E r = 0.20 [0.04, 0.52] (n = 28).
- **Relative to straight-line speed, E behaves as Phase 1.6 hoped, but only with assumed limits.** With the reference limits, E is nearly uncorrelated with official 40 time (3-cone ρ −0.18, shuttle 0.12). With game-derived limits it becomes strongly speed-confounded (ρ −0.77 / −0.62).

## 2. Coverage and sample sizes
| Drill | Attempts | Valid | Failed: no 40 tracking | Failed: no finish crossing | Failed: no movement | Players (valid) | Players with 2 valid attempts |
|---|---|---|---|---|---|---|---|
| 3-cone | 203 | 172 | 22 | 8 | 1 | 137 | 32 |
| Short shuttle | 225 | 158 | 24 | 40 | 3 | 125 | 28 |

- Capacities A0 and S0 come from each athlete's own best combine-40 attempt.
- Body-sensor paths are shorter than the nominal drills (3-cone median 22.1 yd; shuttle 14.8 yd vs 20 yd nominal), because athletes reach with the hand to touch the lines.
- 3-cone stop detection averages 2.62 stops per attempt against 2 expected, so some stops are spurious.

## 3. Timing validity
Best valid attempt per player vs the official time.

| Drill | n | r [95% CI] | Median tracking − official |
|---|---|---|---|
| 3-cone | 128 | 0.649 [0.36, 0.89] | +0.24 s |
| Shuttle | 117 | 0.403 [0.27, 0.69] | +0.43 s |

- Recordings usually start after movement has begun (speed at the first frame about 0.6 yd/s), and the official timing protocol differs.
- Back-extrapolating the start barely helps (r 0.65 / 0.36).
- **The tracking-based drill times carry ±0.1 s-level error, which is comparable to the between-player spread.**

## 4. Plausibility: share of negative execution costs (athlete faster than the model allows)
| Limit set (D, C in yd/s²) | 3-cone | Shuttle |
|---|---|---|
| D 5.0, C 5.0 | 31% | 78% |
| **D 6.5, C 7.0 (reference)** | **0%** | **28%** |
| D 8.0, C 9.0 | 0% | 8% |
| game envelope, position median | 44% | 79% |
| game envelope, the player's own | 46% | 77% |
| no lateral limit, D 6.5 | 0% | 18% |

- **Game-demonstrated braking and lateral envelopes (D99 ≈ 3–6, C99 ≈ 4–7 yd/s²) are lower than what the shuttle demands.** Using them as "capacity" makes the model call real performances impossible.
- **Lateral and braking capacity in combine drills exceed game envelopes:** an envelope is a lower bound, not a capacity.

## 5. Relationship with 40 time, COD deficit and drill time
Spearman ρ for the best valid attempt per player.

| Limits | Drill | E vs official 40 | E vs combine S0 | E vs COD deficit | E vs % COD deficit | E vs official drill time |
|---|---|---|---|---|---|---|
| D 6.5, C 7.0 | 3-cone | −0.18 | 0.13 | 0.57 | 0.65 | −0.14 |
| D 6.5, C 7.0 | shuttle | 0.12 | −0.19 | 0.79 | 0.74 | 0.14 |
| D 8.0, C 9.0 | 3-cone | −0.23 | 0.17 | 0.61 | 0.68 | −0.15 |
| position game envelope | 3-cone | **−0.77** | 0.73 | 0.16 | 0.82 | −0.74 |
| position game envelope | shuttle | −0.62 | 0.55 | 0.40 | 0.79 | −0.52 |

- Conventional measures vs official 40 time:
  - COD deficit: ρ 0.04 (3-cone), 0.11 (shuttle).
  - **% COD deficit: −0.76 / −0.42.** In real data the percentage deficit is speed-confounded, the opposite of what the simulation suggested.
  - Tracking drill time: 0.62 / 0.53.
- **E is mostly a re-expression of the COD deficit** (ρ 0.57–0.79 with the reference limits). Its claimed advantage — a path- and athlete-specific counterfactual — could only show if the limits were credible, and they are not yet.

## 6. Drill differences
Players with both drills, n = 86.
- E, 3-cone vs shuttle: ρ = 0.39 [0.17, 0.57].
- COD deficit: ρ = 0.29 [0.08, 0.51].
- Official drill times: 0.90 (n = 80), which is inflated by position composition.

Execution cost is drill-specific to a large degree; it is not a single general trait.

## 7. Sensitivity of rankings (Spearman ρ vs the reference)
| Change | 3-cone | Shuttle | Median shift in E (s) |
|---|---|---|---|
| SG window 5 / 9 | 0.97 / 0.98 | 0.98 / 0.99 | ≤ 0.03 |
| extrapolated onset | 0.90 | 0.89 | +0.17 to +0.19 |
| no stop constraints | 0.85 | 0.89 | +0.22 to +0.33 |
| limit grid (D 5–8, C 5–9) | 0.92–0.98 | 0.97–0.99 | −0.70 to +0.40 |
| game envelope (position) | **0.61** | **0.56** | −0.82 / −0.37 |
| game envelope (player) | 0.56 | 0.49 | −0.66 / −0.30 |
| no lateral limit | 0.76 | 0.94 | +0.38 / +0.06 |

**Rankings are robust to smoothing and to uniform changes of the assumed limits. They are not robust to athlete-specific limits or to dropping the lateral constraint (3-cone).** Absolute values of E are not interpretable: they shift by up to 0.8 s.

## 8. Within-player reliability (players with 2 valid attempts only)
| Drill | Measure | n | Test–retest r [95% CI] | Typical error |
|---|---|---|---|---|
| 3-cone | E | 32 | 0.58 [0.39, 0.78] | 0.31 s |
| 3-cone | COD deficit | 32 | 0.39 [0.12, 0.68] | 0.49 s |
| 3-cone | tracking time | 32 | 0.40 [0.16, 0.72] | 0.58 s |
| shuttle | E | 28 | 0.20 [0.04, 0.52] | 0.39 s |
| shuttle | COD deficit | 28 | −0.42 [−0.68, 0.31] | 0.68 s |
| shuttle | tracking time | 28 | −0.61 [−0.88, 0.25] | 0.95 s |

- The 3-cone E is more repeatable than the COD deficit in this small sample, but the CIs overlap.
- **Shuttle tracking times are not repeatable**, which points to gating failures. The shuttle results should not be used.
- No individual repeatability is claimed for the 70–80% of players with a single valid attempt.

## 9. Assessment against the Phase 2 questions
| Question | Answer |
|---|---|
| Execution cost vs 40 time | ≈ 0 with assumed limits; strongly speed-confounded with game-derived limits |
| vs conventional COD deficit | strongly related (ρ 0.57–0.79): largely the same information so far |
| Drill differences | weak cross-drill consistency (ρ 0.39) |
| Sensitivity to path smoothing | small (ρ ≥ 0.97) |
| Robust rankings? | to smoothing and uniform limits, yes; to athlete-specific limits, onset and stops, partially |
| Two attempts for reliability? | only 32 (3-cone) and 28 (shuttle) players; 3-cone r = 0.58, shuttle not reliable |

## 10. Recommendation
Candidate C's *execution* component is **not yet measurable with acceptable validity** on real combine data. Before any link to performance, it needs:
- **(a)** a validated gating/timing method, for example registration to the drill template, or use of official times with a template path;
- **(b)** an external, non-circular source of braking and lateral capacity. Game envelopes are not capacities. Possibly maximal skill-drill envelopes, which are higher, but with the circularity caveat;
- **(c)** better stop and touch modelling. The body sensor never reaches the line.

The 3-cone is the more promising drill; the shuttle is currently unusable.
