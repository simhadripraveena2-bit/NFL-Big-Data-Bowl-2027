# Phase 11.0: NeurIPS/KDD research-gap reconnaissance

**Date:** 2026-11-23  
**Status:** preliminary literature reconnaissance; **no genuine gap or novelty claim is established yet**. No code, model, experiment, or new preregistration is authorized by this note.

## 1. Research objective

Target a general Computer Science / ML contribution suitable for consideration at NeurIPS or KDD. The NFL tracking project is a motivating application and possible validation environment, not the definition of the research contribution.

The target standard is:
- a precisely stated problem that matters beyond one sport;
- a demonstrable limitation of the closest existing methods;
- a new algorithm or theory (not a combination of known modules);
- strong synthetic evaluation with known counterfactual truth;
- external, temporal, and cross-domain validation where data permit.

## 2. Findings that rule out broad claims

### 2.1 Counterfactual player evaluation under a common task distribution is not new

**Susmann & D'Alessandro (2026), “The Counterfactual Combine: A Causal Framework for Player Evaluation,” arXiv:2602.23233.**  
https://arxiv.org/abs/2602.23233

The paper defines stochastic interventions that reassign repeated attempts to players, including direct and indirect standardization and “performance above random replacement.” It derives efficient influence functions and develops doubly robust/TMLE estimators. It studies NFL place kickers and MLB batters.

The paper assumes no unmeasured confounding and positivity for the chosen intervention. Its analysis treats attempts as i.i.d. observations with attempt covariates, player identity, and outcome. It does not model within-attempt multi-agent trajectory interference in the stated framework.

**Consequence:** Do not claim novelty for opportunity-standardized player evaluation, task reassignment, random replacement, or applying TMLE to player ratings.

### 2.2 Opportunity-conditioned latent speed estimation is already a crowded construction

The Phase 8C literature audit already found precedents for the main components: Statcast's opportunity filtering, RACE-style performance envelopes with hierarchical athlete effects, mono-exponential sprint models, quantile/frontier estimation, and exposure-aware extreme-value methods. The Phase 8C conclusion remains in force: merely assembling these pieces does not establish a new algorithm.

A further close paper is:

**Zhang (2026), “Counterfactual Evaluation of Temporal Observation Protocols,” arXiv:2608.22221.**  
https://arxiv.org/abs/2608.22221

It studies whether a realized observation protocol identifies the predictive value of alternative, undeployed protocols. It gives value-specific identification results and calibration / observation-design guarantees.

**Consequence:** Do not claim a new gap merely because player metrics depend on exposure, or because an alternative observation/opportunity protocol is unobserved.

### 2.3 Sequential interference and latent confounding already has a NeurIPS 2026 treatment

**Paschalidis, Daskalakis & Shah (2026), “Causal Inference for Sequential Settings under Interference and Latent Confounding,” NeurIPS 2026, arXiv:2607.14940 v2.**  
https://arxiv.org/abs/2607.14940

The paper models binary outcomes for multiple units over time using an Ising-type spatial interaction model, temporal dependence, and low-rank latent confounding. It gives non-asymptotic estimation guarantees from a single joint observation.

Important scope restrictions visible in the paper:
- binary outcomes and binary interventions;
- a known interaction matrix/network;
- homogeneous direct treatment and temporal-dependence parameters;
- the intervention is not assigned in response to the realized outcomes (the paper explicitly states this in its setup);
- a Dobrushin-type weak-interference condition is used for guarantees.

**Consequence:** Do not claim a new method for sequential network interference with latent confounding in general. A possible distinction would need to be about adaptive, state-dependent joint assignment and continuous multivariate trajectories, with its own identifiability result.

### 2.4 Active learning of network-interference response functions is now directly covered

**Liu et al. (2026), “Fill-Distance-Guided Active Learning for Causal Function Recovery under Network Interference,” arXiv:2611.24143, submitted 2026-11-18.**  
https://arxiv.org/abs/2611.24143

FANCI combines treatment-specific Gaussian processes with fill-distance-guided sequential experimental design to recover population response functions over network exposure. It includes network feasibility constraints, uniform error bounds, simulations, and an online-game experiment.

**Consequence:** Do not propose “learn the full causal response surface under network interference using active learning” as a new problem without a sharply different setting and theory.

### 2.5 Applied NFL multi-agent causal player valuation already has a close precedent

**Jenkins (2026), “Tackling Causality: Estimating Frame-Level Defensive Impact with Multi-Agent Transformers,” MIT Sloan Sports Analytics Conference 2026 research paper.**  
https://www.sloansportsconference.com/research-papers/tackling-causality-estimating-frame-level-defensive-impact-with-multi-agent-transformers

The public abstract claims a 22-player multi-agent Transformer for counterfactual Expected Points Saved for individual defenders, with coordination/substitution, doubly robust estimation, representation balancing, Bayesian uncertainty, synthetic validation, and game examples. The full technical details have **not yet been audited** here.

**Consequence:** A generic “multi-agent Transformer for causal defender impact” or “interference-aware defensive attribution” is not an acceptable novelty claim. The full paper must be obtained and reviewed before any nearby idea is advanced.

### 2.6 Related ML / causal foundations

- **Bayati et al. (NeurIPS 2024), “Higher-Order Causal Message Passing for Experimentation with Complex Interference.”** Unknown and non-monotone interference in multiperiod randomized experiments.  
  https://proceedings.neurips.cc/paper_files/paper/2024/hash/94f008bcc2a5eb785fb8e0ad7aedd4fc-Abstract-Conference.html
- **Zhang & Wang (NeurIPS 2025), “Online Experimental Design With Estimation-Regret Trade-off Under Network Interference.”** Sequential experiment design under interference.  
  https://proceedings.neurips.cc/paper_files/paper/2025/hash/179a2b276b954a1369ec9119c4badabb-Abstract-Conference.html
- **Kuang et al. (NeurIPS 2025), “Breaking the Order Barrier: Off-Policy Evaluation for Confounded POMDPs.”** Finite-sample guarantees for off-policy evaluation with unobserved confounding in partially observed MDPs.  
  https://proceedings.neurips.cc/paper_files/paper/2025/hash/46a675d435a6c020aef3356d6c463b10-Abstract-Conference.html
- **Bacco, Wang & Blei (CLeaR 2024), “A Causality-Inspired Plus-Minus Model for Player Evaluation in Team Sports.”** Counterfactual player substitution with factor-model adjustment for indirectly measured confounding.  
  https://proceedings.mlr.press/v236/bacco24a.html
- **Zhang, Bareinboim (UAI 2025), “Causal Eligibility Traces for Confounding Robust Off-Policy Evaluation.”** Bounds and algorithms for off-policy evaluation with unobserved confounding and lack of overlap.  
  https://proceedings.mlr.press/v286/zhang25d.html
- **“Modeling Dynamic Interference for Treatment Effect Estimation from Dynamic Graphs” (ACM TKDD, 2026).** Dynamic graph interference; full paper must be read.  
  https://doi.org/10.1145/3796240
- **Bennett et al. (NeurIPS 2024), “Efficient and Sharp Off-Policy Evaluation in Robust Markov Decision Processes.”** Sensitivity-model bounds for policy value under transition shift / unmeasured confounding.  
  https://proceedings.neurips.cc/paper_files/paper/2024/file/cd1da8043ba5c1c144ab4e10a8de6e53-Paper-Conference.pdf

## 3. Provisional research direction to investigate (not a confirmed gap)

### Counterfactual evaluation of an agent under adaptive joint behavior

**Working question:** Given offline, observational, multi-agent trajectories, can we estimate the value of replacing or changing one agent when (i) team/agent assignments adapt to prior joint states and outcomes, (ii) other agents react and interfere, (iii) behavior policies have limited joint-action support, and (iv) some common causes of assignment and outcome are latent?

This differs conceptually from fixed-task reassignment: the intervention may alter the future state and therefore the future task/opportunity distribution. The target would need to specify whether other agents are held fixed, respond under their historical policies, or respond under a target joint policy. These are different estimands and must not be conflated.

**Potential contribution shape, only if the literature audit supports it:**
1. define a trajectory-level, focal-agent intervention with an explicit response model for the other agents;
2. characterize identifiability and non-identifiability under adaptive assignment, interference, latent confounding, and partial joint-action support;
3. derive an estimator or sharp sensitivity bounds that exploit structured/local interaction and do not require full joint-policy overlap;
4. provide finite-sample / asymptotic guarantees under explicit assumptions;
5. validate on synthetic multi-agent environments with known counterfactual truth, then on NFL tracking and at least one non-sports domain.

This is a **candidate problem statement**, not an assertion that no prior work solves it. Offline MARL, multi-agent OPE, robust POMDP OPE, sequential causal inference, and dynamic graph interference remain important neighboring literatures to audit.

## 4. Initial candidate ranking

| Candidate | NeurIPS/KDD potential | Main risk | Current status |
|---|---|---|---|
| Adaptive joint-behavior counterfactual evaluation under interference | High if new identification/estimation theory is possible | Very crowded; direct SSAC26 application; robust OPE and sequential network causal work | **Investigate first; not validated** |
| Opportunity/exposure-aware latent athlete capacity | Moderate empirical value | RACE, Statcast, EVT/frontier and observation-protocol papers overlap; Phase 8C rejected a novelty claim | Deprioritize as primary algorithm |
| Reliability-aware separation / performance estimation | Moderate | Reliability and measurement-error methods are mature; current player-level separation reliability is 0.44 | Retain as application / diagnostic |
| Sports counterfactual benchmark with simulator-ground-truth | Potential KDD or NeurIPS Datasets & Benchmarks | Benchmark alone may not meet main-track algorithmic bar; data rights and simulator fidelity | Backup path |

## 5. Data constraints inherited from the current project

The NFL Big Data Bowl 2027 data used in the completed project tracks only the eligible Combine cohort players in game data; it does not include all opponents and all other players for each play. The current data therefore cannot, by itself, support a full 22-player interaction model.

The Phase 8C audit notes that the 2022 NFL tracking data used in earlier Big Data Bowl work contains full-player tracking, but linking the right seasons, player IDs, play context and outcomes still needs a separate data audit. Any publication using competition data must respect Kaggle's access and redistribution terms; raw competition data must not be placed in a public repository or benchmark.

## 6. Immediate next phase: literature and identifiability audit

Do not implement a neural architecture yet. The next research tasks are:

1. Obtain and read the complete SSAC26 “Tackling Causality” paper; document its estimand, SCM/DAG, assignment mechanism, treatment/outcome feedback, interference model, assumptions, estimator, and validation.
2. Read the complete FANCI paper (arXiv:2611.24143), including proofs and the online-game experiment; identify whether any setting overlaps the proposed observational/adaptive target.
3. Read the complete NeurIPS 2026 sequential-interference paper, including proofs and assumptions; map its limitations precisely.
4. Audit multi-agent offline OPE / Markov games, robust POMDP OPE, dynamic graph interference, and adaptive treatment regimes for methods that already handle adaptive joint policies and continuous trajectories.
5. Formalize a minimal two-agent / two-step counterexample showing why existing single-agent or fixed-assignment player metrics fail under adaptive feedback and interaction. If no non-identifiability or estimation problem can be demonstrated, reject this direction.
6. Inventory accessible datasets with full multi-agent trajectories, observed actions/roles, temporal outcomes, and repeated entities. Establish which variables are pre-treatment, post-treatment, or jointly determined.

**Gate before coding:** produce a related-work matrix, a structural causal model, a precise estimand, sufficient/necessary identification conditions (or impossibility result), a baseline list, and a data-feasibility report. Only then decide whether a new algorithm can be justified.

## 7. Current decision

**No research gap is yet declared genuine.** The broad opportunity-adjusted player-evaluation idea is already covered. The only direction retained for deeper investigation is adaptive, joint-behavior counterfactual evaluation under sequential interference and latent confounding. If the full-paper audit shows this is already solved, we will pivot rather than rebrand existing methods.
