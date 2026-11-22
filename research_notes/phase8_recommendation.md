# Phase 8 recommendation (revised in Phase 8B; final decision in Phase 8C)

## Phase 8C final decision: **B. An empirical contribution is defensible, but no new algorithm is justified.**

**Basis:** `phase8c_novelty_audit.md`.

**Read for the audit:**
- Spearing et al. 2021 (F, arXiv version);
- the step-and-turn implementation (F-code);
- RACE, Lee 2026 (P);
- Postma et al. 2022 (A);
- MLB Statcast Sprint Speed (S).

**Inaccessible:** Greene 2005 and Koop et al. 1997 (closed access, K only), and Hall & Simar 2002 (repository copy restricted; A).

**Answers in brief:**
1. **Player-specific capacity conditional on opportunity already exists in pieces**, not as one validated estimator:
   - TTA gives population attainability conditional on distance, bearing and speed (F);
   - mono-exponential models give player attainable speed as a function of distance (A/K);
   - Statcast filters for full-effort "competitive runs" (S);
   - RACE combines an envelope with athlete hierarchy (P);
   - step-and-turn has player random effects given context (F).
2. **Representation of opportunity:**
   - Only TTA and the sprint-kinematic models represent distance and time explicitly.
   - Step-and-turn uses only the lagged 0.3-s step, the lagged turn, and the defender and teammate configuration. Its code subsamples to 0.3-s steps and bounds predictions by the sample's largest step.
   - The poster and Spearing have none at the play level.
3. **Direct application to our data:**
   - Possible: order statistics, per-player QR, mono-exponential fits, Statcast-style filters, RE-SFA, RACE-style models, TTA retrained on own kinematics.
   - **Not** step-and-turn as published: it needs all 22 players, and we have only the cohort player.
4. **Combine as independent validation:** absent from all the closest works. But in-situ profiling studies already validate against sprint tests, so this is a **data advantage**, not a methodological novelty.
5. **No technically defensible algorithmic contribution.**
   - The opportunity-conditioned frontier is a specification inside existing classes.
   - Its central separation of opportunity from effort is not identifiable here. Own-trajectory distance is endogenous to effort, exogenous proxies are coarse, opponents are absent, and the noisy boundary needs a known error law.
6. **Held-out evaluation:** feasible (player-grouped and season-forward, with strong baselines), but **power-limited**. Within position n ≈ 60–77, and the minimum detectable Δρ is about 0.30.

**Consequences:**
- The algorithmic research track should be **closed** under CLAUDE.md standard 3. On that standard alone, the answer is C.
- The only defensible continuation is the **G1′ empirical benchmark**:
  - exposure and opportunity drift of game speed estimators;
  - their agreement with combine peak speed on held-out players;
  - interval calibration.
  - It would be presented without a novelty claim, and only after a separate pre-registration.

**Options for the project lead:**
1. **Approve G1′** as an empirical contribution (a new pre-registration first).
2. **Close the algorithmic track** and submit the completed confirmatory study as is.

No further literature step is recommended. The remaining inaccessible works are classical, and the decision does not depend on their unread details.

---

**Status:** recommendation only.
- **No implementation, training or modelling has been started.**
- The completed empirical study, its preregistration and the frozen analysis code are unchanged.

## 1. Evidence base

**Phase 8B read the three closest works in full** (`related_work_full_text_review.md` §2.1, §2.2, §3.5):

| work | type | what was read | inaccessible |
|---|---|---|---|
| Gutiérrez-Pérez & Agudo 2026, TTA quantile regression | arXiv preprint (claimed ACCV 2026 acceptance, unverified) | full main text; code repository (config, loss, model, training, dataset building) | supplement §A.1–A.4 |
| Shteynberg, Snavely & Solorzano 2025, effort in NFL RBs | undergraduate summer research poster (CMU SURE); not peer-reviewed | the complete poster | written report (host unreachable) |
| Nguyen & Yurko 2026, NFL step-and-turn | arXiv preprint | complete paper, Appendices A–F | code repository (not inspected) |

Phase 8B also checked DOIs and abstracts of frontier and extreme-value prior art: Hall & Simar 2002 and Einmahl & Magnus 2008 (A); Spearing et al. 2021 (A); Greene 2005, Koop et al. 1997, Battese & Coelli 1995 and Kneip et al. 2015 (S/K).

## 2. Findings against G1

**Does existing work already solve G1? Not as a problem; yes as a method.**

- **Problem not solved (F level).**
  - None of the three works estimates a per-athlete latent speed capacity that accounts for exposure, with pooling, per-athlete uncertainty and external validation.
  - TTA uses a 99th-percentile per-player v_max as a known input. Its canonical code computes it within the test match, which the config calls "look-ahead leakage".
  - The poster fits independent per-player 0.95 quantile curves, to measure effort.
  - Step-and-turn pools players for *mean* step length.
- **Method largely exists:**

  | G1 ingredient | existing work | evidence |
  |---|---|---|
  | conditional quantile regression | TTA; poster QR / QGAM | F |
  | player random effects and hierarchical shrinkage with posterior uncertainty | step-and-turn; Bayesian / true-RE SFA | F; S/K |
  | context-dependent one-sided deficits | Battese–Coelli | S/K |
  | exposure-aware extreme-value estimation (occurrence rate, covariates, endpoints) | Spearing et al. 2021; Einmahl & Magnus 2008 | A |
  | boundary under observation noise | Hall & Simar 2002 | A |

**Decision:**
- **G1 as an algorithmic contribution is rejected.** Assembling these components is not an original algorithm.
- **G1 is reformulated as G1′**, an empirical identification and validation study:
  - does game-derived top speed drift with exposure?
  - which existing estimator best recovers an independently measured capacity (combine tracked peak speed), with calibrated intervals, for held-out players?

## 3. Re-scoring (1 = weak, 5 = strong)

| criterion | G1 (algorithm) | **G1′ (empirical)** | G2 | G3 | G4 |
|---|---|---|---|---|---|
| technical novelty | 1 (components exist) | 2 (no new method; an untested question) | 2 (was 3) | 3 | 2 |
| scientific significance | 4 | 4 | 4 | 4 | 3 |
| feasibility | 4 | 4 | 2 | 2 | 5 |
| data availability (ability to validate) | 5 | 5 | 2 | 1 | 4 |
| strength of baselines (higher = clearer benchmark) | 4 | 5 (concrete: M1, TTA-style v_max, M3b, M7, M4b, M10) | 3 | 2 | 4 |
| potential for measurable improvement | 4 → n/a | 3 (a negative result is possible) | 3 | 2 | 3 |
| **total (/30)** | rejected | **23** | 16 | 14 | 21 |

**Changes since Phase 8:**
- G1 (24) is split into G1 (rejected) and G1′ (23).
- G2 drops from 17 to 16: per-player A–D quantile curves exist (F), and so does noise-aware boundary estimation (A).
- G3 and G4 are unchanged: no new evidence bears on them.

## 4. Recommendation

**No defensible algorithmic gap is established by the available evidence.** That holds for G1, G2 and G4. G3 might yield a selection-model method, but it is weakly identifiable in these data and its literature has not been reviewed. A G1-type algorithm would be a combination of existing methods, which the project lead's rules exclude.

**The most defensible remaining direction is G1′.** It is empirical and does not satisfy CLAUDE.md standard 3 (a new algorithm) on its own.
- **Why G1′:** the reviewed works use game-derived player speed traits (TTA's v_max) or player effects (step-and-turn) without testing them against an independent measurement. The competition data uniquely has one for the same athletes.
- **What it would deliver:** a pre-registered benchmark of existing estimators (Q1 exposure drift, Q2 within-position agreement with combine peak speed on held-out and season-forward players, Q3 interval calibration), with identical splits and paired tests.
- **Known risks:**
  - construct gap: combine ≠ game capacity, so the comparison is on ranks and calibration, not levels;
  - selection into exposure (G3);
  - a negative result is likely and acceptable.

**Options for the project lead (no default is assumed):**
1. Approve G1′ as an empirical contribution and accept that the algorithmic standard is not met by this direction.
2. Require one more literature step first. Read in full Spearing et al. 2021, Greene 2005 / Koop et al. 1997, Hall & Simar 2002 and the step-and-turn code. Only then decide whether the "attainable-speed bound per play" element (`algorithmic_research_gaps.md`, G1′) could be a genuine method contribution.
3. Close the algorithmic track: report that no defensible algorithmic gap was found, and submit the completed empirical study as is.

## 5. Explicitly not claimed

- That G1, G1′ or any candidate is novel.
- That combining existing methods is an original contribution.
- That combine peak speed *is* game capacity.
- That the backup-RB pattern in the poster is an exposure artefact (it is consistent with one; untested).
- That TTA's published numbers used the leaking v_max scope (not determined).
- Anything about the inaccessible TTA supplement, the Shteynberg report, or the priority-2 full texts.
