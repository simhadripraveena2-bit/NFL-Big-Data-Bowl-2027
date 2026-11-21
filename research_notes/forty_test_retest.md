# 40-yard dash test–retest reliability (approved deviation D3)

**Scope:** combine data only.
- Inputs: `combine_tracking` (FORTY_YARD_DASH, PLAYER rows) and `combine_results`.
- **No NFL game table was opened.** This analysis has no access to any game outcome.

**Reproduce:**
- `python scripts/run_forty_reliability.py`
- Code: `src/nfl_bdb/features/forty_reliability.py`.
- Run `experiments/forty_reliability/20261121T134306Z`, code at commit `a690b9a` plus the D3 files; bootstrap seed 4040.

## 1. Data

- 793 tracked 40 attempts from 418 players: 375 with two attempts, 43 with one.
- 789 attempts are valid under the registered rule (mono-exponential R² > 0.95 and peak ≤ 12.5 yd/s). No valid attempt exceeds the spike threshold.
- The provider's track starts at movement onset (first-frame speed ≈ 0.6 yd/s) and ends at about 40 yd. The median along-axis length is 40.4 yd; 160 tracks end 0–1.5 yd short of 40 and are extrapolated at their final speed.
- **Official times exist only as one value per player** (the best attempt). Per-attempt official times are not in the data.

## 2. Test–retest of single attempts

First two usable attempts per player; ICC(3,1), with player-bootstrap 95 % CI.

| measure | ALL | WR | TE | DB | DL | OL |
|---|---|---|---|---|---|---|
| **tracked peak speed** (registered x, valid attempts) | 0.987 (0.984–0.989) | **0.889 (0.82–0.94)** | 0.928 | 0.926 | 0.976 | 0.933 |
| tracked 0–40 time | 0.671 | 0.223 | 0.238 | 0.110 | 0.908 | 0.773 |
| tracked 0–10 time | 0.213 | 0.199 | −0.035 | 0.066 | 0.629 | 0.581 |
| flying 10–35 yd split | 0.991 | **0.887 (0.83–0.93)** | 0.942 | 0.943 | 0.987 | 0.943 |

The ICC(2,1), absolute-agreement version, is within 0.01 of these values. The mean attempt-2 − attempt-1 difference is ≤ 0.04 yd/s or s, so there is no practice or fatigue effect.

**Single-attempt SEM:**
- peak speed: 0.08–0.10 yd/s;
- 0–40 time: 0.08–0.35 s;
- flying split: 0.013–0.021 s.

## 3. Findings

**1. Within-position R_x is lower than the registered value.**
- The registered value R_x = 0.987 (protocol §7, used in the Phase 4 simulations and in the H2 EIV refit) is the **pooled** test–retest correlation, and it is reproduced exactly here (0.987).
- Pooled reliability is inflated by between-position differences in speed, as CLAUDE.md already warns.
- Within position, single-attempt reliability is 0.89 (WR) to 0.98 (DL).
- The registered predictor is the **maximum over valid attempts**. Its reliability is approximated by Spearman–Brown for two attempts:

| | WR | TE | DB | DL | OL |
|---|---|---|---|---|---|
| **R_x (best of 2), within position** | **0.94** | 0.96 | 0.96 | 0.99 | 0.97 |

**2. The 0–40 time from tracking is not a usable stand-in for the electronic 40.**
- Its start is the provider's track onset, not the electronic start, and the 0–10 yd segment carries almost all the noise (WR ICC 0.20).
- Within WR, the best tracked 0–40 time correlates only 0.41 with the official 40.
- **Therefore the official 40's own test–retest reliability R_F cannot be estimated directly from these data.**

**3. Bounds on R_F (within position, classical independent errors).**
- The latent correlation between true 40 speed and true peak speed must be ≤ 1. With r = corr(x, official 40) and R_x as above, this gives R_F ≥ r² / R_x.

| | WR | TE | DB | DL | OL |
|---|---|---|---|---|---|
| corr(peak x, official 40) | 0.814 | 0.911 | 0.797 | 0.975 | 0.899 |
| **lower bound on R_F** | **0.70** | 0.86 | 0.66 | 0.96 | 0.84 |
| corr(flying 10–35 split, official 40) | 0.897 | 0.917 | 0.915 | 0.987 | 0.953 |

- The flying split is not an independent measurement: it shares 25 yd of the same runs as the official time. A bound built on it, 0.897² / 0.94 ≈ 0.86 for WR, therefore holds only under a stronger assumption, and is reported for context only.
- The test–retest here is **within one combine session**. Day-to-day variation is not captured, so every reliability above is an upper bound for "capacity on another day".

## 4. Consequences (no decision rule changes)

**H1 decisions are unaffected.** Δ is defined and tested on the observed-x scale (Phase 4 S9 shows measurement error only attenuates Δ). The disattenuated ρ that the protocol reports alongside will use the **within-position** R_x (WR 0.94) as well as the registered 0.987. This is a reporting addition, logged in §15.

**For H2, the registered EIV refit at R_F = 0.95 (with R_x = 0.987) stays the decision criterion.** The data say:
- WR R_F is only bounded below by 0.70 (about 0.86 under the stronger assumption). So R_F = 0.95 is not demonstrated.
- WR R_x is about 0.94, so peak speed is not much more reliable than the 40 may be.

By the Phase 4 population calculation, the precision artefact is between 0.02 (R_F 0.95) and about 0.10 (R_F 0.80) for a 40 validity of 0.3. The EIV sensitivity grid R_F ∈ {0.85, 0.90, 0.95, 0.99} and the tipping-point R_F will be reported, using both R_x values. **H2 stays estimation-focused** (see the D4 question in the deviations log).

**There is no evidence of a practice or order effect between attempts**, so "max over attempts" is not systematically favouring the second attempt.
