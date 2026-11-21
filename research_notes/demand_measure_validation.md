# Demand-measure validation (Phase 4, Part 3)

**Scope:** the near-top-speed task-demand measure D(p, c) registered in `preregistration.md` §3.3. It is validated here using real game speeds only. **No combine measurement was joined to any game outcome.** All demand quantities use only each player's own game `vmax_play` values.

**The registered definition is unchanged:**
- **T_i** = mean of the player's five largest REG play maxima.
- **share_ic** = fraction of the player's plays in context c with vmax_play ≥ 0.90 T_i.
- **D(p, c)** = median share over eligible players.
- **Cross-fitting:** random player halves, seed 3503.

**Reproduce:**
- Stages: `python scripts/run_synthetic_validation.py demand_real|demand_reliability|demand_sim <run>`. The code is `src/nfl_bdb/features/demand.py` and `scripts/phase4_stages.py`.
- Tables: notebook 07 §5. Run id `20261121T023847Z`.

## 1. Cell demand at 85 / 90 / 95 % and the absolute 7.5 yd/s threshold

D is the median share of a player's plays that reach the threshold.

| pos | context | 85 % | **90 % (registered)** | 95 % | ≥ 7.5 yd/s |
|---|---|---|---|---|---|
| WR | deep | 0.339 | **0.183** | 0.054 | 0.656 |
| WR | short | 0.027 | **0.004** | 0.000 | 0.138 |
| TE | deep | 0.440 | **0.184** | 0.071 | 0.354 |
| TE | short | 0.058 | **0.023** | 0.009 | 0.040 |
| DB | man | 0.125 | **0.058** | 0.023 | 0.280 |
| DB | deep zone | 0.057 | **0.028** | 0.013 | 0.151 |
| DB | under zone | 0.033 | **0.014** | 0.006 | 0.089 |
| DL | pass rush | 0.051 | **0.026** | 0.016 | 0.013 |
| DL | run | 0.027 | **0.013** | 0.006 | 0.003 |
| OL | pass block | 0.013 | **0.008** | 0.004 | 0.000 |
| OL | run | 0.017 | **0.009** | 0.004 | 0.000 |

**Agreement across thresholds (cell level, 11 cells, Spearman):**
- 85 vs 90: 0.945
- 90 vs 95: 0.982
- 85 vs 95: 0.927
- 90 vs absolute: 0.761

**Within each position, the registered high-demand context has the larger D at every relative threshold:**
- WR deep > short;
- TE deep > short;
- DB man > deep zone > under zone;
- DL pass rush > run.

**OL is the exception.** Run ≥ pass block at 85 % and 90 %, and the two tie at 95 %. The OL difference, 0.0088 vs 0.0077, is about one cross-fit SD (§3). OL demand is therefore near zero and **indistinguishable between its two contexts**. This is consistent with H5's role as a low-demand comparison. It also means an OL Δ cannot be interpreted as a demand contrast.

The absolute threshold re-orders positions, because big players never reach 7.5 yd/s. That is the reason the registered measure is player-relative. The absolute variant stays a sensitivity analysis only.

**Verdict:** the registered 90 % threshold is not knife-edge. The ordering of contexts (and of cells for the meta-regression) is essentially the same at 85 % and 95 %.

## 2. Player-level stability (split-half by game parity, Spearman–Brown)

| pos | context | 85 % | 90 % | 95 % |
|---|---|---|---|---|
| WR | deep | 0.79 | 0.71 | 0.65 |
| WR | short | 0.08 | −0.13 | 0.07 |
| DB | man | 0.71 | 0.71 | 0.23 |
| DB | under zone | 0.55 | 0.46 | 0.09 |
| DB | deep zone | 0.48 | 0.18 | 0.08 |
| DL | pass rush | 0.75 | 0.66 | 0.57 |
| DL | run | 0.56 | −0.01 | −0.01 |
| OL | pass block | 0.68 | 0.60 | 0.27 |
| OL | run | 0.69 | 0.69 | 0.46 |

TE values (n = 15–18) are unstable and are listed in the notebook only.

**Interpretation:**
- Player-level shares are reliable only where demand is non-trivial: WR deep, DB man and DL pass rush.
- Where D ≈ 0 (WR short, DL run), the share is a floor-bound count, and player-level reliability is ≈ 0.
- **This does not threaten the registered analysis.** D enters only as a cell-level median, a property of the task, not of the player. The cell median is stable (§3).
- It does rule out using a player's own share as a player covariate. That use was never registered.

## 3. Cross-fitting: registered split and 500 random splits

**Registered split (seed 3503):** halves of 28 / 29 WRs. D_half(deep) is 0.179 and 0.191; D_full is 0.183.

**Across 500 random player-half splits** (D_half; SD and quantiles across splits):

| pos | context | D_full | mean D_half | SD | 5–95 % |
|---|---|---|---|---|---|
| WR | deep | 0.183 | 0.183 | 0.010 | 0.165–0.196 |
| WR | short | 0.004 | 0.003 | 0.002 | 0.000–0.006 |
| TE | deep | 0.184 | 0.179 | 0.048 | 0.098–0.244 |
| DB | man | 0.058 | 0.060 | 0.009 | 0.049–0.074 |
| DB | deep zone | 0.028 | 0.029 | 0.002 | 0.026–0.032 |
| DB | under zone | 0.014 | 0.014 | 0.003 | 0.010–0.018 |
| DL | pass rush | 0.026 | 0.028 | 0.004 | 0.024–0.037 |
| DL | run | 0.013 | 0.013 | 0.001 | 0.011–0.014 |
| OL | pass block | 0.008 | 0.008 | 0.001 | 0.006–0.009 |
| OL | run | 0.009 | 0.009 | 0.001 | 0.008–0.011 |

**Findings:**
- Half-sample D is unbiased (mean D_half − D_full ≤ 0.002 everywhere).
- Half-sample D is stable relative to the gaps between cells, except TE deep (n = 18, SD 0.048).
- **The cell ordering used by the meta-regression does not depend on the seed.** The WR, DB and DL high-vs-low gaps exceed 4 split-SDs.
- The OL gap does not exceed its split-SD (see §1).

## 4. Out-of-sample T_i (leakage check on the normaliser)

T_i is estimated on one game-parity half, and shares are computed on the other. This removes the mechanical link where a player's own top-5 plays sit in the numerator.

| pos | context | in-sample T (half 0 / 1) | out-of-sample T (half 0 / 1) |
|---|---|---|---|
| WR | deep | 0.234 / 0.222 | 0.230 / 0.211 |
| WR | short | 0.000 / 0.005 | 0.000 / 0.005 |
| DB | man | 0.092 / 0.092 | 0.072 / 0.094 |
| DL | pass rush | 0.048 / 0.039 | 0.041 / 0.040 |
| OL | pass block / run | 0.014 / 0.012, 0.014 / 0.017 | 0.011 / 0.012, 0.015 / 0.014 |

The values are on half the games, so they are not equal to the full-sample D. Using an out-of-sample T moves D by ≤ 0.02, and context orderings are unchanged. TE deep moves more, 0.343 → 0.234 in one half, which reflects n = 18. **The self-normalisation leak is negligible.**

## 5. Split-sample leakage simulation (the meta-regression slope λ)

**World:** a synthetic 11-cell world with real-like demand spread. Each position has 55 players and 40–300 plays per cell. The capacity–level correlation is ρ_k = 0.3 + λ (D_k − mean D).

**Comparison:** λ̂ from the REML random-effects meta-regression, using
- same-sample D (D and ρ from the same players), versus
- registered cross-fitting (D from one half, ρ from the other).

400 replicates per cell; MC SE of a rate ≤ 0.025.

| λ | D from | mean λ̂ | SD(λ̂) | mean SE | P(λ̂/SE > 1.96) |
|---|---|---|---|---|---|
| 0 | same sample | 0.00 | 1.11 | 1.18 | 0.025 |
| 0 | **cross-fit** | −0.06 | 0.98 | 1.51 | **0.000** |
| 1.5 | same sample | 1.84 | 1.02 | 1.16 | 0.395 |
| 1.5 | **cross-fit** | 1.94 | 1.04 | 1.44 | 0.208 |
| 3.0 | same sample | 3.87 | 0.96 | 1.12 | 0.928 |
| 3.0 | **cross-fit** | 3.99 | 0.99 | 1.38 | 0.902 |

**Findings:**
- **There is no detectable same-sample leakage bias in this world.** λ̂ under the null is centred at 0, and same-sample size is nominal.
- Both versions over-estimate λ by about 0.3–1.0 at λ > 0, by a similar amount. This is shared bias from noisy D.
- **Cross-fitting is conservative.** Its model SE overstates the empirical SD (1.51 vs 0.98 under the null), and power at λ = 1.5 halves (0.21 vs 0.40).
- The registered cross-fit is therefore valid but costly. This is a power cost, not a validity failure, so no deviation is required.
- If the slope test is ever used confirmatorily, a proposed deviation would be to report the same-sample λ̂ alongside. **The meta-regression is already secondary in the protocol, so nothing is proposed.**

**Limitation:** the simulated world has demand driven by cell means. It does not contain a mechanism where a player's own speed both defines D and enters ρ beyond what §4 measures. The real-data out-of-sample-T check (§4) is the direct guard for that.

## 6. Verdict

The demand measure is validated for its registered use: a **cell-level** contrast of near-top-speed exposure.
- It is insensitive to the 85/90/95 % choice.
- It is stable across player halves.
- It is not driven by self-normalisation leakage.
- Its cross-fitting is valid, but conservative.

**Two limits must be stated with the results:**
1. OL contexts do not differ in demand.
2. Player-level shares are unreliable in low-demand contexts, so they must not be used as player covariates.
