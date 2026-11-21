# Selection-bias analysis (Phase 4, Part 4)

**Question:** how does the registered eligibility rule (≥ 100 primary-context opportunities and ≥ 20 plays in each context) interact with selection into playing time? What population does H1-WR then describe?

**Not changed:** the registered inclusion criteria. The alternative thresholds are sensitivity analyses only. **No combine measurement was joined to any game outcome.**

**Reproduce:** stages `selection` and `selection_real`; helpers `ps.selection_reml_approx` and `ps.selection_effective_truth`; notebook 07 §4. Run id `20261121T023847Z`; seeds `SeedSequence([4004, 300 + mechanism, replicate])`; 300 replicates per cell. Common random numbers are used across rules, so rule differences within a mechanism are paired.

## 1. Who each rule keeps (real data, outcome-free)

| rule | WR players | WR plays | median plays hi / lo | 2023–25 mean year | team-seasons / player | rounds 1–2 | UDFA |
|---|---|---|---|---|---|---|---|
| **registered (≥ 100, ≥ 20/ctx)** | **57** | 19,960 | 141 / 144 | 1.54 | 2.07 | 0.26 | 0.12 |
| ≥ 50 | 61 | 20,162 | 125 / 115 | 1.50 | 2.00 | 0.25 | 0.12 |
| ≥ 200 | 45 | 18,602 | 165 / 189 | 1.56 | 2.20 | **0.33** | **0.09** |
| all pool (≥ 5/ctx) | 69 | 20,414 | 106 / 100 | 1.47 | 1.90 | 0.22 | 0.10 |

For DB, the ≥ 50 rule keeps the same 52 players as the registered rule; ≥ 200 keeps 47; the full pool is 67.

**What changes:**
- Raising the threshold removes low-snap players. Those are disproportionately late-round and UDFA, so the cohort shifts toward early-round starters.
- Lowering it adds 4–12 players but almost no plays (+1–2 %), because those players have few routes.

**Players, not plays, are the unit of information.** The ≥ 50 and all-pool rules add players whose context means are noisy, and the REML model down-weights them.

## 2. Simulated selection mechanisms

**Setup:**
- Playing time is the real log-route count lr of each WR, a fixed design attribute.
- Two selection mechanisms tie latent quantities to it:
  - **On outcome:** playing time correlates with the player's deep-route residual level u_h (sel_outcome = 1, i.e. corr ≈ 0.71 with lr). This is the "coaches play the guys who get open deep" story.
  - **On capacity:** playing time correlates with true speed capacity z (sel_capacity = 1).
- Each mechanism is run under a null (ρ 0.3 / 0.3) and a moderate effect (0.5 / 0.3).

**Separating estimand shift from estimator bias:**
- Δ_eff is the expected Δ among the players a rule retains, from the same latent generator with no outcome noise and no fitting.
- **Estimand shift** = Δ_eff − nominal Δ. This is a change of target population.
- **Estimator bias** = mean Δ̂_REML − Δ_eff. This is an error of the method.

| mechanism | rule | n | Δ_eff | estimand shift | REML bias vs target | moment (fallback) bias vs target |
|---|---|---|---|---|---|---|
| none, null | registered | 57 | 0.000 | 0.000 | −0.003 | +0.003 |
| none, null | ≥ 200 | 45 | −0.001 | −0.001 | −0.004 | +0.004 |
| outcome, null | registered | 57 | 0.013 | +0.013 | **+0.020** | +0.028 |
| outcome, null | ≥ 50 | 61 | 0.005 | +0.005 | +0.026 | +0.037 |
| outcome, null | ≥ 200 | 45 | 0.028 | +0.028 | +0.024 | +0.033 |
| outcome, null | all pool | 69 | −0.010 | −0.010 | +0.031 | +0.038 |
| capacity, null | registered | 57 | −0.001 | −0.001 | +0.007 | **−0.048** |
| none, moderate | registered | 57 | 0.197 | −0.002 | +0.004 | −0.006 |
| outcome, moderate | registered | 57 | 0.237 | **+0.039** | +0.003 | −0.001 |
| outcome, moderate | ≥ 200 | 45 | 0.251 | **+0.052** | +0.004 | +0.006 |
| capacity, moderate | registered | 57 | 0.177 | **−0.022** | −0.012 | **−0.076** |
| capacity, moderate | ≥ 200 | 45 | 0.173 | −0.026 | −0.012 | −0.084 |
| capacity, moderate | all pool | 69 | 0.197 | −0.002 | −0.013 | −0.089 |

MC SE of each bias is about 0.007. Full table: notebook 07.

## 3. Decisions (FPR and power) under selection

**Rejection rates** (MC SE ≈ 0.008 at the null and 0.028 at moderate):
- *Fallback*: REML Δ̂ with the moment-bootstrap CI, B = 2,000 per replicate.
- *REML approx.*: the full REML bootstrap. Its shape comes from the matching warp-speed scenario, so this is an approximation.

| mechanism | rule | fallback reject | REML approx. reject |
|---|---|---|---|
| none, null | registered | 0.020 | 0.003 |
| none, null | ≥ 200 | 0.040 | 0.003 |
| outcome, null | registered | **0.073** | 0.037 |
| outcome, null | ≥ 50 | 0.073 | 0.023 |
| outcome, null | ≥ 200 | 0.077 | 0.040 |
| outcome, null | all pool | 0.057 | 0.017 |
| capacity, null | registered | 0.007 | 0.017 |
| none, moderate | registered | 0.410 | 0.473 |
| none, moderate | all pool | 0.377 | 0.503 |
| outcome, moderate | registered | 0.527 | 0.593 |
| capacity, moderate | registered | **0.187** | 0.363 |
| capacity, moderate | all pool | 0.147 | 0.440 |

Nominal directional size is 0.025.

## 4. Interpretation: what selection does to H1

**1. Selection on capacity is range restriction.**
- Retained starters are faster, so the capacity spread shrinks. The deep-context correlation, which is the larger one, shrinks more.
- The selected population's Δ is about 0.02 smaller (−11 % of a moderate effect).
- REML tracks that target, with bias −0.012.
- **The fallback moment estimator does not** (−0.08). Its power halves (0.19 vs 0.36 under REML).

**2. Selection on the outcome mainly changes who is in the population.**
- If coaches play WRs who reach high deep-route speeds, the retained WRs' deep-route level is partly selected.
- Under a true effect, the eligible population's Δ is inflated by +0.04 (registered rule) to +0.05 (≥ 200).
- REML estimates that inflated target without additional bias.
- Under the null there is also a small genuine estimator bias (+0.02–0.03). Players with more plays carry more weight, and their deep levels are selected upward.
- **This is the one mechanism that inflates false positives:**
  - fallback: 0.073 ± 0.015;
  - full REML bootstrap (approx.): 0.037 ± 0.011, within 1.1 MC SE of nominal.

**3. Threshold choice matters less than the mechanism.** Under every mechanism:
- the ≥ 50 rule and the registered rule agree within MC error;
- the ≥ 200 rule amplifies both estimand shifts (stronger selection) and costs 12 players;
- the all-pool rule (≥ 5/ctx) has the smallest estimand shift, but slightly larger REML bias under outcome selection, from noisier low-play players.

**The registered threshold sits at a sensible compromise.**

**4. What the result means.** H1-WR describes **WRs with a regular route-running role in 2023–2025 (≥ 100 routes)**. It does not describe drafted WRs in general.
- If the protocol's answer is "deep-route speed translates better", it is conditional on a coach having already given the player routes.
- That conditioning is the natural population for a scouting question ("among receivers who will play, which combine speed matters deep?"). It is not the population for a draft-bust question.
- This interpretation must accompany any result.

## 5. Recommended reporting (no change to the registered rule)

- Report the ≥ 50, ≥ 200 and all-pool estimates as registered sensitivity analyses, with the cohort composition table (§1).
- Interpret a drift of Δ̂ that rises with the threshold as consistent with selection on deep-route level (§4, point 2). Do not treat it as evidence for H1.
- **Proposed deviation (not implemented).** Use the full REML bootstrap for all selection sensitivity analyses. The fallback moment estimator is biased under capacity selection and has a false-positive rate of 0.073 under outcome selection. See `synthetic_validation.md` §3.
