# H1-WR: registered negative controls

**Source of the registry:** `statistical_model_specification.md` §4 lists the negative controls:
1. permuted context labels within player;
2. OL contrast;
3. WR short-route β_P.

`preregistration.md` §13 repeats them. **No new negative control was added after the primary result.**

**Status:**
- **N1 was run.**
- **N2 and N3 were not run.** They are part of the H5 and H2 analyses, which you have not yet approved. They are described below so that their purpose is on record.

**Provenance:** run `experiments/h1_wr_robustness/20261121T233918Z/robustness.json` (key `N1_permutation`), commit `a18a1d8`, seeds 6001–6500.

## N1: context labels permuted within player (run)

**Design.** For each of 500 permutations:
1. Within every WR, the deep/short labels are shuffled across that player's own plays. Each player's number of deep and short plays is kept.
2. The registered context-specific design is rebuilt.
3. The registered REML model is refitted, and Δ̂ is recorded (point estimate).

**What it is designed to detect: mechanical artefacts**, where the pipeline produces a non-zero Δ even though play context carries no information. Possible sources:
- unequal numbers of plays per context;
- the context-specific covariate design (route_ran nested in depth);
- context-specific residual variances;
- REML behaviour near boundaries;
- any coding asymmetry between context 0 and context 1.

After permutation, every player's two "contexts" are random halves of the same plays, so the true Δ is exactly 0 by construction.

**What would indicate a problem:**
- The permutation distribution is centred away from 0. The tolerance is the MC SE: with 500 permutations, a mean shift beyond about ±0.01 would be a warning.
- Or it is systematically skewed toward the observed sign.
- Or fits fail or hit boundaries.

**Result:**

| | value |
|---|---|
| permutations / converged | 500 / 500 |
| mean Δ̂_perm (MC SE) | **0.003 (0.002)** |
| SD of Δ̂_perm | 0.053 |
| 2.5 % / 50 % / 97.5 % | −0.101 / 0.004 / 0.111 |

**Interpretation:**
- **No mechanical artefact.** The pipeline returns Δ ≈ 0 when context is uninformative, with a symmetric distribution.
- The contrast's machinery (context-specific design, separate residual variances, unequal plays per context) does not by itself manufacture a deep–short difference.

**What N1 is not:**
- The observed Δ̂ = 0.090 lies at about the 94th percentile of the permutation distribution: 5.8 % of permutations give Δ̂ ≥ 0.090.
- **This is not a test of H1, and not a p-value.** The permutation null holds the 57 players fixed, so its spread (SD 0.053) reflects only label noise within players. It omits player-sampling variability, which dominates the registered SE (0.12; Wald 0.10).
- The registered decision rests only on the player-cluster bootstrap, which is inconclusive.

## N2: OL pass-block vs run contrast, H5(a) (registered; not run, because H5 is deferred)

**Designed to detect** whether "context differences in translation" appear where the demand model predicts none. Both OL contexts have near-zero near-top-speed demand (D ≈ 0.008–0.009; `demand_measure_validation.md`). A large OL contrast would suggest the H1 machinery picks up context differences unrelated to speed demand: for example, play-type differences in outcome variance or in team scheme.

**What would indicate a problem:**
- A clearly non-zero Δ_OL. Registered reading (§12): "consistent" if the 90 % CI lies within ±0.15. At n = 53, the CI half-width is about 0.24, so this is expected to be reported as estimation.

**Result:** not run. It will be run with the H5 analyses under the registered hierarchy, once approved.

## N3: WR short-route β_P, separation (registered, descriptive; not run, because H2 is deferred)

**Designed to detect**, for H2, whether peak speed "predicts" separation even on short routes, where speed demand is low. If so, an H2 association would more likely reflect general player quality or measurement artefacts than deep-route speed.

**What would indicate a problem:**
- A short-route β_P as large as the deep-route β_P. The registered contrast is β_P^deep − β_P^short (spec §2.4, descriptive).

**Result:** not run. It belongs to the H2 estimation analysis, which awaits approval.
