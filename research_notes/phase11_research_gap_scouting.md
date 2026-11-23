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


---

# Phase 11.1: Narrowing the candidate after full-paper checks

**Date:** 2026-11-23  
**Status:** one sharper candidate retained for a formal identifiability test; **still no novelty claim and no implementation authorized**.

## 8. What the closest new papers actually cover

### 8.1 Learning in Causal Markov Games (NeurIPS 2026)

**Maiti & Bareinboim, “Learning in Causal Markov Games,” Columbia CausalAI technical report R-152 / NeurIPS 2026.**  
https://causalai.net/r152.pdf

The formal definition is a structural causal model over state, joint actions and per-agent rewards. Each stage has:
- per-agent latent action drivers Ui,t;
- a shared state-noise component Us,t;
- per-agent reward noises Uy_i,t;
- Xi,t = f_Xi(St, Ui,t);
- rewards that may depend on the vector of per-agent Ui,t;
- next state that depends on the previous stage's per-agent action latents.

Crucially, the exogenous distribution factorizes across the Ui,t, state noise and reward noises, and stages are i.i.d. The independence of the per-agent Ui,t gives conditional independence of natural intuitions Xi,t given the observed state, which is what makes counterfactual policies decentralized and product-form.

The no-post-hoc-intuition algorithm is limited to **two players** and uses active uniform exploration plus linear-independence conditions on reward and transition signatures to identify an opponent's unobserved natural intuition. The post-hoc-observation algorithm has a finite-sample result but requires observing every player's natural intuition after the fact. The tabular sample complexity contains a cubic dependence on the product of action-set sizes.

**What this makes precise:** shared, correlated per-agent latent drivers and persistent latent common causes are not represented in this model class. This is a formal scope restriction, not merely an empirical weakness. A reviewer also explicitly questioned the independence assumption, but reviewer criticism alone is not evidence of novelty.

### 8.2 Sequential Causal Games (2026)

**Maiti & Bareinboim, “Sequential Causal Games,” technical report R-145.**  
https://causalai.net/r145.pdf

This framework introduces natural, interventional and counterfactual actions and Causal Nash Equilibrium. Its introduction explicitly notes that the Markov-game abstraction rules out explicit latent variables / hidden common causes influencing both agent actions and state transitions across time. It therefore does not close the shared-persistent-confounder gap.

### 8.3 Proximal credit assignment in cooperative MARL (NeurIPS 2026)

**Joo, Ha & Lee, “Rethinking Credit Assignment in Cooperative MARL via Interventional Reward Response,” NeurIPS 2026.**  
https://mhha.netlify.app/publication/neurips26/

The public abstract states that the paper defines agent-level credit as an interventional reward response, uses proximal causal inference with observable proxies and an outcome bridge, and integrates the resulting signal into cooperative policy gradients under partial observability.

**Audit status:** the full technical PDF / supplement has not yet been obtained; only the public abstract and publication record are available. This is a mandatory close-paper read before any related method is advanced. Do not claim a gap in proximal multi-agent credit until this paper is reviewed in full.

### 8.4 “Value Identifiable, Credit Not” (2026 preprint / workshop manuscript)

**Anonymous, “Value Identifiable, Credit Not: A Credit-First Identifiability Frontier for Confounded Sequential Decision-Making.”**  
https://openreview.net/attachment?id=1LbCpjOpAv&name=pdf

The paper formulates sequential proximal moment restrictions M theta = y, proves a linear functional is identifiable iff its coefficient is in the row space of M, and computes partial-identification intervals by linear programming when it is not. It defines temporal interventional credit under a fixed continuation policy. Its experiments include 2- and 3-agent cooperative Dec-POMDPs with a latent environmental factor affecting local action tendencies and global rewards.

Its formal estimand is principally **one action at a time over a sequential horizon**, not the general-sum causal Nash equilibrium of a multi-agent Markov game. Still, proximal credit and partial-identification intervals are already present; these ingredients alone cannot be claimed as new.

### 8.5 Counterfactual effect propagation (ICML 2024/2025)

**Triantafyllou et al., “Agent-Specific Effects” (ICML 2024)** and **“Counterfactual Effect Decomposition in Multi-Agent Sequential Decision Making” (ICML 2025).**  
https://proceedings.mlr.press/v235/triantafyllou24a.html  
https://proceedings.mlr.press/v267/triantafyllou25a.html

These papers define and estimate counterfactual agent-specific effects, including propagation through selected downstream agents and Shapley-style decompositions. Their structural causal model assumes mutually independent exogenous noises and uses noise monotonicity to identify cross-world counterfactuals.

**Consequence:** neither counterfactual effect propagation nor Shapley attribution is a new idea. A new target cannot simply rename ASE or replace independent noise with a correlated latent variable.

### 8.6 Other direct overlaps

- **Overman, Shirani & Bayati (NeurIPS 2026), “Causal Effects with Unobserved Unit Types in Interacting Human-AI Systems,” arXiv:2603.01339.** Handles causal effects by unobserved unit type under unknown interaction networks via causal message passing and composition-diverse subpopulations. It is based on experimental treatment variation, not strategic policy learning or causal equilibrium computation. https://arxiv.org/abs/2603.01339
- **Wang et al. (TMLR 2025), “MACCA: Offline Multi-agent Reinforcement Learning with Causal Credit Assignment.”** Learns a DBN and decomposed per-agent reward from offline cooperative data. https://arxiv.org/abs/2312.03644
- **Deshmukh et al. (NeurIPS 2026), “COSAC: Counterfactual Credit Assignment in Sequential Cooperative Teams.”** Establishes a sequential team-credit estimator and bias/variance analysis, but studies fixed-order contextual-bandit teams with a shared reward and sequential policy updates; it does not define an offline hidden-confounder causal equilibrium. https://arxiv.org/abs/2604.17693
- **Jenkins (SSAC 2026), “Tackling Causality.”** Applied NFL 22-player counterfactual defender valuation; do not claim generic multi-agent causal player attribution.

## 9. Revised candidate: proxy-assisted causal equilibrium learning with shared persistent confounding

The previous broad candidate “counterfactual evaluation under adaptive joint behavior” is too broad and overlaps substantially with offline OPE, interference and causal credit work.

The only candidate retained for a **formal gap test** is:

> **Can we identify or sharply partially identify causal best-response values and a causal equilibrium in a partially observed, general-sum Markov game when a persistent shared latent state jointly influences multiple agents' natural actions, the state transition and rewards, using only passive trajectories and observable proxies—without post-hoc access to natural actions or active uniform exploration?**

This is intentionally narrower than “causal MARL with confounding.” It targets the intersection of:
- general-sum strategic equilibrium (not only cooperative team credit);
- shared / correlated latent causes across agents (not conditionally independent per-agent intuition noise);
- persistence of the common cause across time;
- passive / offline trajectories (not active uniform exploration);
- proxy-assisted point or partial identification (not assuming latent actions observed);
- decentralized policy execution despite correlated private information.

### Candidate estimand

For a general-sum game, agent i's causal best-response value under a candidate policy profile pi would be defined under a precise structural intervention on its decision rule, while other agents continue under their specified policies and react to the resulting public state/history. A causal equilibrium is a profile in which no agent can improve this interventional value by changing its admissible policy.

This is **not yet mathematically defined**. In particular, we must decide whether a player can condition on its private proxy / natural signal, whether common latent information can be shared, and whether the equilibrium is ex ante or type-contingent. These choices change the equilibrium concept and cannot be hidden in notation.

### What could constitute a real contribution

Only if the full related-work audit permits it:
1. an SCM for persistent shared confounding in general-sum Markov games with decentralized observations;
2. a theorem characterizing which best-response / equilibrium-payoff functionals are identifiable from passive joint trajectories and cross-agent proxies;
3. a matching non-identifiability counterexample when joint-proxy completeness or support fails;
4. a scalable estimator or sharp partial-identification procedure with finite-sample error bounds;
5. an equilibrium-learning procedure whose guarantees do not require online uniform exploration or post-hoc observation of every natural action;
6. synthetic tests with exact equilibrium ground truth, followed by multi-agent benchmarks and a non-sports application.

**Not sufficient:** adding a shared latent variable to the CMG definition, adding a proximal bridge to an existing algorithm, using a Transformer, or improving an NFL predictive metric without a new theorem / algorithm and strong baselines.

## 10. Formal gate before implementation

The next deliverable is a **two-player, two-stage structural identifiability study**, not a neural model.

### Experiment A: model and observational equivalence

Construct a binary two-agent, two-stage game with:
- one persistent shared latent cause C;
- optional private latent variables U1, U2;
- natural action mechanisms for each agent;
- a public state transition;
- general-sum per-agent rewards;
- observable treatment-inducing and outcome-inducing proxy candidates.

Build two SCMs with the same observational distribution over all recorded variables but different causal best-response values / equilibria, if possible. This supplies an impossibility result in the absence of sufficient proxies.

### Experiment B: positive identification

Add explicit proxy assumptions and derive the joint bridge equations. Determine whether:
- the relevant best-response payoff is a linear functional of bridge parameters;
- its identifiability condition is a row-space / completeness condition;
- correlated proxy measurements across agents are enough to identify the joint latent type distribution;
- policy-support and equilibrium computation introduce additional non-identifiability.

Do not assume that a single-agent proximal-RL theorem transfers automatically to a game.

### Experiment C: baseline comparison and complexity

Compare the theoretical target against:
- Causal Markov Games (Maiti & Bareinboim, 2026);
- sequential causal games (Maiti & Bareinboim, 2026);
- proximal RL / confounded POMDP OPE (Bennett & Kallus);
- proximal interventional reward response (Joo et al., NeurIPS 2026; full paper read required);
- MACCA;
- ICML 2024/2025 agent-specific effect / counterfactual decomposition;
- “Value Identifiable, Credit Not”;
- standard POSG / Bayesian Markov game solutions.

Quantify the additional assumptions, identifiability gap, and computational complexity. A table showing a missing intersection is not proof of novelty.

### Decision rule

- **Proceed** only if we prove a nontrivial positive identification theorem or a sharp impossibility / partial-identification theorem that is not a direct corollary of the closest papers, then derive an estimator with a meaningful computational/statistical advantage.
- **Pivot** if the target reduces to a routine combination of correlated-type Bayesian games and proximal RL.
- **Reject** if passive proxies cannot identify a useful equilibrium quantity and no useful, decision-relevant partial bounds are possible.

## 11. Practical application and data

The current 2027 NFL competition dataset is not suitable as the primary testbed for this problem: it tracks only the Combine cohort players, not all 22 players and the ball. The earlier full-player 2022 tracking data may be a secondary application after a data-rights, entity-linkage and variable-timing audit.

For the main synthetic evaluation, use small general-sum games with known latent common causes first. Then test on at least one established MARL benchmark where a shared persistent context can be injected in a controlled, reproducible way. NFL / sports tracking can remain an application, not the proof of generality.

## 12. Updated status

- Broad common-opportunity athlete evaluation: **rejected as a novelty claim**.
- Generic sequential multi-agent credit assignment: **too crowded** (ICML 2024/2025, MACCA, IRR, COSAC, and a 2026 partial-identification manuscript).
- Generic offline policy evaluation under network interference: **too crowded**.
- Shared-confounder causal Markov games with passive proxy observation and general-sum equilibrium learning: **retained only as a formal gap-test candidate**.
- **No genuine gap declared. No code or model has been started.** The immediate work is mathematical counterexample / identification, then close-paper audit of IRR and the full SSAC26 paper.
