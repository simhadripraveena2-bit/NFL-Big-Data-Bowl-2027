# Phase 11.2: Minimal non-identifiability counterexample

**Status:** formal sandbox, not a novelty result. This is the first negative-control problem the proposed method must solve.

## 1. Question

Can a unilateral causal policy value be recovered from passive multi-agent trajectories when both agents' natural actions are driven by a hidden common cause and the intervention has no support in part of the latent population?

We construct two structural causal models (SCMs) that produce exactly the same observational distribution but disagree on the counterfactual value of changing one agent's action.

## 2. Two-agent, two-stage setup

Let the persistent hidden context be

\[
C\sim \operatorname{Bernoulli}(1/2).
\]

A recorded proxy is

\[
W=C\oplus E,\qquad E\sim \operatorname{Bernoulli}(q),\quad 0<q<1/2,
\]

with E independent of C. The proxy is noisy; the argument below also holds if W reveals C perfectly.

At stage 1, under the observed behaviour policy, both agents' natural actions are

\[
A_{1,1}=C,\qquad A_{2,1}=C.
\]

At stage 2, agent 2 responds to the public first-stage action profile:

\[
A_{2,2}=C\oplus A_{1,1}.
\]

Thus agent 2 has a state-dependent response to agent 1's first-stage action, and C persists across the two stages.

We consider two candidate reward mechanisms for agent 1:

**SCM M0 (reward driven by the persistent context):**

\[
R_1=C.
\]

**SCM M1 (reward driven by the focal action):**

\[
R_1=A_{1,1}.
\]

All other structural equations and exogenous distributions are identical.

## 3. Observational equivalence

Under the natural behaviour policy, \(A_{1,1}=A_{2,1}=C\). Therefore in both models,

\[
R_1=C=A_{1,1},
\qquad
A_{2,2}=C\oplus C=0.
\]

The full recorded vector

\[
O=(W,A_{1,1},A_{2,1},A_{2,2},R_1)
\]

has exactly the same distribution under M0 and M1, for every \(q\in[0,1/2)\). No sample size can distinguish these two SCMs from passive observations of O.

## 4. Different causal values

Now intervene on the focal agent's first-stage action while leaving agent 2's structural response mechanism unchanged.

Under \(do(A_{1,1}=1)\):

- M0: \(R_1=C\), so \(\mathbb E[R_1\mid do(A_{1,1}=1)]=1/2\).
- M1: \(R_1=1\), so \(\mathbb E[R_1\mid do(A_{1,1}=1)]=1\).

Under \(do(A_{1,1}=0)\):

- M0: \(\mathbb E[R_1\mid do(A_{1,1}=0)]=1/2\).
- M1: \(\mathbb E[R_1\mid do(A_{1,1}=0)]=0\).

Consequently the average causal effect of setting the focal action to 1 rather than 0 is

\[
\tau_{M0}=0,\qquad \tau_{M1}=1.
\]

The two SCMs agree on every passive observation but disagree maximally on the intervention value.

## 5. Interpretation and limits

This is a valid **non-identifiability witness** for the unrestricted model class. It establishes that passive observational data alone cannot identify the focal causal action value when:
- a persistent hidden common cause drives both agents' natural actions;
- no within-context action variation is observed (positivity fails);
- the recorded proxy does not add independent intervention variation.

The example includes a responsive second agent, but the reward mechanism here does not depend on agent 2's second-stage response. It therefore does **not** establish a novel result about strategic spillovers or general-sum equilibrium learning.

It also does not show that proximal identification is impossible under sufficiently strong proxy-completeness / bridge assumptions. It only proves that such assumptions, or an alternative source of variation, are necessary for a point-identification claim in this model class.

A perfect proxy for C alone does not repair the lack of action support: even conditioning on C, the natural data never show the counterfactual focal action in that context.

## 6. What must be solved next

The important question is whether a useful positive result exists once assumptions are added.

1. **Support:** characterize the precise joint-action support condition needed for unilateral deviations and the opponents' response policies.
2. **Proxy validity:** define treatment-inducing and outcome-inducing proxies with conditional independence restrictions that remain meaningful when agents share C.
3. **Bridge:** derive the *joint* proximal moment equations for two agents; do not assume a single-agent bridge applies componentwise.
4. **Identification:** determine whether a best-response payoff is identified even when the full latent distribution and all cross-world counterfactuals are not.
5. **Equilibrium:** establish whether point identification of each unilateral deviation value is sufficient for identifying an equilibrium set. If not, characterize the identified equilibrium correspondence or payoff bounds.
6. **Minimality:** compare the resulting conditions directly with Causal Markov Games, Sequential Causal Games, interventional reward response, “Value Identifiable, Credit Not,” and sequential proximal OPE.

## 7. Decision

This counterexample is a baseline impossibility check, not a publishable contribution. Proceed only if the next stage yields a nontrivial positive identification theorem, a sharp decision-relevant partial-identification result, or a computationally useful equilibrium algorithm that is not already implied by the closest work.
