# Feasibility Experiments B and C — Comparison, Limitations and Recommendation

*Synthesis of `candidate_b_feasibility.md` (Experiment 1) and `candidate_c_feasibility.md` (Experiment 2).
Simulation only; no NFL outcome data used; nothing here establishes real-world validity. The research
hypothesis is **not** finalised.*

## 1. Side-by-side
| | **B — capacity estimation** | **C — COD execution cost (CCMT)** |
|---|---|---|
| Question | Can S0 and A0 be estimated from game tracking when athletes rarely reach their limits? | Can time lost in direction changes, relative to the athlete's own limits, be defined and measured? |
| Formulation | linear A–S frontier; noise-corrected binning (SIMEX) + jackknife; optional pooling | fixed-path minimum-time optimal control; forward–backward solution; capacity/execution decomposition |
| Mathematical soundness | standard; SIMEX assumptions explicit | exact solver for independent limits (verified against NLP); coupled limits need NLP |
| Best simulated result | S0 bias +5.4% → +2.6–2.8% vs Morin binning; better in 21–23/23 cells | r with true execution cost 0.69 (vs 0.64 COD deficit); r with 40 time 0.10–0.16 (vs 0.32–0.47) |
| Where it fails | A0 (binning is better); calibration with pooling; frontier curvature (±12% A0); vs naive peak speed the S0 gain is a split decision (10–11 better / 9–10 worse of 23) | limit errors ≥ 10%/20% (r drops to 0.46 < COD deficit 0.52); circular limits (r 0.34); absolute bias +0.2 to +0.65 s on curved drills from 10 Hz path smoothing |
| Novelty after review | low–moderate: in-situ A–S exists; SIMEX is classical; our designs that were new (frontier likelihoods) **failed** | moderate: optimal control of running exists (Keller; Maroński), but the athlete-specific counterfactual decomposition on measured paths was not found in the literature |
| Data feasibility (real) | high for S0; A0 needs ≥ about 100 plays | combine agility drills: about 1/3 of players; braking/lateral limits not yet shown to be estimable |
| Discovery potential | low on its own ("fast in the combine → fast in games" is expected) | higher: whether *execution*, not capacity, transfers or matters is a genuinely open question |

## 2. Shared limitations
1. **No ground truth in real data.** Both experiments validate *methods* against a generator we wrote. Generator assumptions (effort distribution, linear frontier, white noise, technique independent of speed) are unverifiable and favour models that share them.
2. **Measurement pipeline sensitivity.** Smoothing window, sampling rate and noise model change results more than estimator choice (B), and path curvature at 10 Hz is biased (C).
3. **Single combine occasion; few repeated attempts.** Real reliability can only be estimated on small subsets.
4. **Combine vs game context.** Pre-planned vs reactive movement, and protocol differences.

## 3. Should B and C be combined? — **Yes, but as measurement layer + metric, conditionally.**
- **C requires B.** The execution cost is defined relative to the athlete's limits. Experiment 2 shows its advantage over the COD deficit exists only when A0/S0 are known to about ≤ 5% and braking/lateral limits to about ≤ 10%. Experiment 1 shows S0 at about 3.6–4.1% and A0 at about 3.6% (binning, ≥ 100 plays) are achievable *in simulation*; A0 is not achievable for low-snap players.
- **B alone does not meet the CLAUDE.md standards.** Its algorithmic claim is weak (no gain for A0; split decision against peak speed for S0) and its discovery potential is low. It is valuable as **infrastructure**: calibrated capacity estimates with honest uncertainty.
- **The combined programme's best claim:**
  - *Algorithm:* the CCMT decomposition, with capacity inputs from B and error propagation.
  - *Possible discovery:* whether COD execution, separately from athletic capacity, is (i) a stable trait and (ii) transfers from combine to game.
  - Both remain hypotheses.

**Recommended estimator choices if combined** (from simulation evidence, not yet real data):
- **S0:** SIMEX-corrected binning *without* pooling, cross-checked against robust peak game speed (they should agree within about 3–4%).
- **A0:** Morin binning (window 7), reported only for athletes with ≥ 100 plays.
- **Uncertainty:** play-level jackknife (unpooled; conservative).
- **Discard:** empirical-Bayes pooling, as implemented, until it is re-calibrated.

## 4. Gating checks before any outcome modelling (proposed; awaiting approval)
All use **no performance outcomes**:
1. **Real-data capacity plausibility:** agreement of game-derived S0/A0 with combine-40 S0/A0 for the same players, with uncertainty; stability across seasons.
2. **Braking and lateral limit estimability:** frontier envelopes of braking and centripetal acceleration vs speed in game data. Do they exist, and with what precision?
3. **CCMT on real combine drills:**
   - discriminant check: execution cost vs 40 time, |r| small;
   - reliability: the 2-attempt subset;
   - cross-drill consistency: shuttle vs 3-cone vs position drills.
4. **Fault handling and preprocessing lock-in:** freeze window, noise SD and exclusions *before* looking at any outcome.

If check 2 fails, C reduces to a speed-normalised deficit, and the **% COD deficit** is the simpler, nearly equivalent choice.

## 5. Unvalidatable assumptions, consolidated
- **Frontier shape:** linear A–S over game speeds.
- **Noise:** NGS noise structure and the vendor's smoothing.
- **Effort statistics:** the frequency and length of maximal efforts in games.
- **Lateral limit:** the lateral-capacity model, including any speed dependence or coupling.
- **Braking limit:** estimability of braking capacity.
- **Capacity definitions:** demonstrated vs true capacity (the identifiability limit); combine capacity = game capacity.
- **Drill layout:** combine drill geometry and gate positions.
- **Technique vs speed:** the relationship between technique and speed in real players.
