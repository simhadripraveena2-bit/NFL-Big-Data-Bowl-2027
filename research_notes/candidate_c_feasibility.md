# Candidate C — Feasibility of a Capacity-Constrained Change-of-Direction Cost (Experiment 2)

*Simulation study only. No NFL outcome data were used. Code: `src/nfl_bdb/features/change_direction_cost.py`,
`scripts/run_cod_simulation.py`; analysis: `notebooks/03_change_direction_simulation.ipynb`
(run `experiments/cod_sim/20261120T192154Z`; figures `reports/figures/sim_c_*.png`). Every number below is
produced by that notebook.*

## 1. Bottom line
- **The formulation works.**
  - The fixed-path minimum-time problem has an exact, fast solution for independent speed, propulsion, braking and lateral limits.
  - It matches a direct-transcription NLP to numerical precision (§3).
  - It turns any measured trajectory into **capacity cost** + **execution cost**.
- **In simulation, the execution cost recovers "time lost relative to own limits" better than the COD deficit, and is far less contaminated by straight-line speed — but only if the athlete's limits are estimated precisely.**
  - Mean Spearman r with the true execution cost is 0.69 (CCMT) vs 0.64 (COD deficit). The clearest gain is on the 3-cone drill (0.75 vs 0.58); on the shuttle and the cuts they are about equal.
  - Correlation with 40-yd time is 0.10–0.16 vs 0.32–0.47 for the COD deficit.
  - **The ranking flips once limit errors reach 10% (speed, acceleration) / 20% (braking, lateral):** r = 0.46 for CCMT vs 0.52 for the COD deficit.
- **The percentage COD deficit also removes most of the speed contamination** (r with 40 time −0.10 to −0.15). It tracks the true execution cost less well (mean r 0.61). Decoupling from speed is therefore **not unique** to CCMT.
- **Absolute "seconds lost" are biased when the path is estimated from 10 Hz positions:** +0.17 to +0.20 s on cuts, +0.65 s on the 3-cone, because smoothing rounds tight turns. The bias is roughly constant within a drill and nearly independent of speed, so within-drill **rankings** survive. Using the nominal drill path removes the bias (≤ 0.007 s).
- **Recommendation:** feasible *conditional on* (a) precise athlete limits from Candidate B and (b) a defensible lateral-limit model. Neither is established yet (§7).

## 2. Methods reviewed before claiming anything
| Prior work (access) | What it does | Relation to ours |
|---|---|---|
| COD deficit — Nimphius et al. 2016 (abstract) | 505 time − 10-m sprint time; isolates COD from linear speed (r ≈ 0 with sprint time in 17 cricketers) | primary conventional baseline (our operationalisation: drill time − own linear-sprint time over the same distance) |
| % COD deficit — Freitas et al. 2022 (abstract) | standardises time- and velocity-based deficits | baseline (our operationalisation: 100 × deficit / linear time) |
| Deceleration deficit — Bishop et al. 2021 (abstract) | deficit for deceleration tasks | not implemented (needs a dedicated deceleration test) |
| Biomechanical COD determinants — Singh et al. 2025 (abstract) | approach/exit speed, braking force, contact time (lab, pre-planned) | motivates the braking and propulsion constraints |
| Minimum-time running — Keller 1973; Maroński 1996 (metadata) | optimal control of minimum-time running (races) | **the optimal-control idea is not new** |
| Running on turns — Greene 1985 (abstract); Chang & Kram 2007 (abstract); Churchill 2015/2018 (abstract); Ohnuma 2018 (abstract) | speed–radius relations; curve speed limited (not by max leg force); individual differences in curve running | motivates the lateral constraint; **Greene's model not yet implemented** (full text not read) |
| Minimum-time on a fixed path — Velenis & Tsiotras 2008; Lipp & Boyd 2014 (metadata) | forward–backward / convex speed profiles under acceleration limits (vehicles, robots) | our solver |

**What may be new** (pending full-text checks): an **athlete-specific counterfactual on the measured path**, decomposing observed time into a capacity cost and an execution cost, applied identically to combine drills and, potentially, game cuts. We found no sports application of this decomposition. That is an absence in our search, not proof.

## 3. Mathematical formulation and assumptions
Choose v(s) ≥ 0 on a fixed path s ∈ [0, L] with curvature κ(s) to minimise T = ∫ ds / v(s), subject to:
1. **C1 Speed:** v ≤ S0.
2. **C2 Propulsion:** v dv/ds ≤ A0(1 − v/S0)·g — the Hill–Keller A–S line from Candidate B.
3. **C3 Braking:** v dv/ds ≥ −D·g.
4. **C4 Lateral:** v²κ ≤ C(v).
5. **C5 Stops:** v = 0 at touch points (reversals).
6. **C6 Start:** v(0) = 0.

g = 1 means independent limits; g = √(1 − (v²κ/C)²) is friction-ellipse coupling.

- **Decomposition:** T_obs = T*_ref + (T*_own − T*_ref) + (T_obs − T*_own); capacity cost K = T*_own − T*_ref; execution cost E = T_obs − T*_own.
- **Solver:** pointwise minimum of the curvature cap, a forward maximal-propulsion pass and a backward maximal-braking pass. O(N) per path, about 5 ms for a 30-yd drill at 0.02-yd resolution.
- **Verification** (notebook 03 §2):
  - A straight 40 yd matches the closed-form mono-exponential time (4.7175 vs 4.7167 s).
  - With **independent limits**, forward–backward equals the best feasible direct-transcription NLP solution (identical discrete constraints, three starts) to numerical precision on 5 paths: relative difference 0.000%, speed-profile difference 0.000.
  - With **friction-ellipse coupling** the simple forward–backward pass is *not* optimal: the NLP is 0.9–2.8% faster on curved paths. A coupled model needs direct transcription.

| Assumption | Status |
|---|---|
| Centre-of-mass point model; no foot-contact or stride dynamics | standard simplification; 10 Hz cannot see contacts |
| Linear A–S propulsion limit | supported for maximal sprints (Phase 1.5); misspecification effects shown in Experiment 1 (curved frontier gives ±12% A0 bias) |
| Constant braking limit D | **assumption**; estimability from game data **not yet tested** |
| Lateral limit form C or C(v) | **assumption; first-order effect** (§5.3). Greene (1985) offers a validated speed–radius model to test next |
| Independent (uncoupled) limits | chosen for exact solvability; coupling changes T* by up to ~3% |
| Stop points with zero speed at reversals; no plant time beyond "dwell" | simplification; makes stop-and-go artificially cheap (§4) |
| Fixed path | does not charge path choice (§4) |
| Drill geometry known (start/finish gates) | true for standard combine drills; not for game cuts |

## 4. How curvature affects minimum feasible time (notebook 03 §3)
- **Turn cost rises with angle and with tightness, and depends on the athlete.** Figure `sim_c_curvature_cost.png`: time cost vs a straight path of equal length.
- **Optimal turning radius is athlete-specific** when turning *around* a cone. Larger radius means faster cornering on a longer path. Figure `sim_c_optimal_radius.png`.

| 90° turn around a cone | Optimal radius (yd) | Penalty if radius is 1 yd | Penalty if radius is 3 yd |
|---|---|---|---|
| fast, low lateral capacity (C = 5.5) | 0.2 | 0.078 s | 0.244 s |
| fast, high lateral capacity (C = 8.5) | 1.3 | 0.003 s | 0.032 s |
| slower, high braking (S0 = 9.8, D = 7.5) | 0.5 | 0.008 s | 0.091 s |

- **For 180° turns the optimum is the smallest radius tested for every athlete.** This is an artefact of the point-mass model with no plant cost, so reversal mechanics need a better model.
- **Implication:** path choice is part of COD skill, and a fixed-path CCMT does **not** charge for it. Free-path optimisation (between known cones) is possible for combine drills, but not for game cuts.

## 5. Population experiment (300 synthetic athletes per cell; 4 drills; 2 attempts)
**Generator.**
- Capacities (A0, S0) come from the combine-40 calibration (same as Experiment 1). D and C are assumptions.
- A latent **technique trait z**, independent of speed in the base case, sets:
  - the fractions of capacity used: η_A, η_D, η_C;
  - the dwell time at touch points.

**Measurement.**
- Positions at 10 Hz with 0.01 yd noise (as Experiment 1), rounded to 0.01 yd.
- Savitzky–Golay window 7.
- Gate-to-gate timing (start gate 0.5 yd, finish-line crossing).
- The athlete's "estimated" own limits are the true values × lognormal error: 5% for A0/S0, 10% for D/C in base.
- The reference is the position-mean limits.

### 5.1 Base cell: what each measure tracks (Spearman r; larger = worse orientation)
| Drill | Measure | r with true execution cost | r with 40-yd time | partial r with poor technique, given 40 time |
|---|---|---|---|---|
| 3-cone | **CCMT execution cost** | **0.754** | 0.163 | **0.687** |
| 3-cone | COD deficit | 0.580 | 0.473 | 0.467 |
| 3-cone | % COD deficit | 0.578 | −0.154 | 0.492 |
| 3-cone | total time | 0.507 | 0.689 | 0.456 |
| shuttle | **CCMT execution cost** | 0.727 | 0.098 | 0.684 |
| shuttle | COD deficit | 0.725 | 0.407 | 0.658 |
| shuttle | % COD deficit | **0.747** | −0.137 | 0.686 |
| cut 90° | **CCMT execution cost** | **0.628** | 0.134 | **0.556** |
| cut 90° | COD deficit | 0.619 | 0.321 | 0.465 |
| cut 90° | % COD deficit | 0.560 | −0.103 | 0.457 |
| cut 135° | **CCMT execution cost** | **0.637** | 0.152 | **0.571** |
| cut 135° | COD deficit | 0.626 | 0.395 | 0.485 |

Full table (incl. peak braking, COD speed, execution ratio, capacity cost, ablations) in notebook 03 §5.

**Ablations (base).**
- *Reference limits only* (no athlete-specific limits): r with true E 0.45–0.59, r with 40 time 0.25–0.32. **The athlete-specific counterfactual is what does the work.**
- *No lateral limit:* worse on curved drills (0.53–0.54 vs 0.63–0.64 on cuts); identical on the straight-line shuttle.
- *Capacity cost K:* nearly unrelated to technique (r 0.03–0.11), as intended.

### 5.2 Sensitivity (mean over 4 drills; r with true execution cost)
| Cell | CCMT exec. cost | CCMT nominal path | COD deficit | % COD deficit |
|---|---|---|---|---|
| base | 0.686 | 0.674 | 0.638 | 0.610 |
| noise 0 / 0.02 / 0.05 yd | 0.700 / 0.671 / 0.688 | 0.685 / 0.660 / 0.699 | 0.621 / 0.588 / 0.616 | 0.589 / 0.594 / 0.630 |
| 5 Hz / 25 Hz | 0.661 / 0.736 | 0.701 / 0.723 | 0.597 / 0.645 | 0.555 / 0.596 |
| window 5 / 9 | 0.730 / 0.672 | 0.721 / 0.661 | 0.592 / 0.601 | 0.586 / 0.585 |
| **limit error 0%** | **0.987** | **0.997** | 0.653 | 0.583 |
| **limit error 10% / 20%** | **0.457** | 0.448 | **0.519** | 0.483 |
| **limit error 20% / 30%** | **0.348** | 0.337 | **0.550** | 0.443 |
| limits biased +10% | 0.713 | 0.699 | 0.612 | 0.565 |
| lateral limit unknown (position mean) | 0.642 | 0.637 | 0.642 | 0.596 |
| technique correlated with speed (ρ = 0.3) | 0.739 | 0.726 | 0.587 | 0.552 |
| **circular limits** (D, C estimated from own drill behaviour) | **0.344** | 0.296 | 0.617 | 0.595 |

- **Measurement noise, sampling rate and smoothing** matter far less than **limit precision**.
- **Circular estimation destroys the metric.** An athlete who never brakes hard cannot be distinguished from one who cannot, which is a fundamental identifiability limit.
- A common bias in the limits (+10%) barely matters for *ranking*.

### 5.3 Absolute bias (base)
| Drill | Mean true E (s) | Bias, estimated path | Bias, nominal path |
|---|---|---|---|
| cut 90° | 0.147 | +0.199 | +0.007 |
| cut 135° | 0.157 | +0.170 | +0.007 |
| shuttle | 0.361 | −0.002 | +0.002 |
| 3-cone | 0.689 | +0.646 | −0.001 |

The correlation of this bias with S0 is between −0.08 and −0.01.

### 5.4 Reliability
Simulated attempt-to-attempt reliability is r ≥ 0.96 for every metric. This is **uninformative**: it reflects the simulation's small attempt-level variation. Real reliability can only be measured on the 2-attempt combine subset (about 25% of agility-drill participants).

## 6. Optimal control vs vehicle dynamics vs trajectory optimisation: which is appropriate?
| Formulation | Appropriate? | Why |
|---|---|---|
| Fixed-path, independent limits (vehicle-dynamics forward–backward) | **Yes (base)** | exact (verified), O(N), interpretable, robust |
| Fixed-path with friction-ellipse coupling | Possible, via direct transcription (NLP) | forward–backward is not optimal here; coupling is not identifiable from our data without a lateral-capacity model |
| Free-path trajectory optimisation through cones | Combine drills only, later | non-convex; needs cone positions (not in the data, but standard geometry); would charge path choice |
| Full musculoskeletal optimal control | **No** | 10 Hz centre-of-mass tracking cannot constrain it |
| Learned (RL / deep) movement models | **No** as primary | not interpretable; no ground truth; n ≈ 500 athletes |

## 7. Assumptions that cannot be validated with the available dataset
1. **Lateral (centripetal) capacity and its speed dependence.** No ground truth; it changes T* by tenths of a second (notebook 03 §3.3).
2. **Braking capacity estimable as a frontier from game data.** Untested. Combine 40 recordings stop about 0.5 s after peak speed (Phase 1), so the cleanest maximal-braking efforts are missing.
3. **"Demonstrated capacity" equals true capacity.** Execution cost is only defined relative to *demonstrated* limits (the circular-limits result).
4. **Combine drill geometry and gate positions.** Approximated; cone positions are not in the data.
5. **Pre-planned combine COD vs reactive game COD** (Singh et al. 2025): transfer cannot be validated by simulation.
6. **Independence of technique and speed** in the base simulation is a design choice. The ρ = 0.3 cell shows the metric still tracks execution, but the real relationship is unknown.
7. **Tracking accuracy for deceleration and curvature** in NGS data: no validation study was found (Phase 1.5).

## 8. Go / no-go
**Conditional go** for a *real-data feasibility* step, with no outcome modelling, gated on these checks:
- **(a)** Candidate B delivers A0 and S0 with ≤ 5% error on real data (which can only be checked indirectly, e.g. combine-40 vs in-game agreement).
- **(b)** Braking and lateral frontiers are estimable from game data with a stated precision.
- **(c)** On real combine data, the execution cost is **not** strongly correlated with 40 time (the discriminant check H-C2).
- **(d)** Reliability holds on the 2-attempt subset.

If (a) or (b) fails, the **% COD deficit** is a simpler, nearly speed-independent alternative, and CCMT's advantage disappears.
