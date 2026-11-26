*A reliability-first study of athletic capacity, game-speed translation and receiver separation · NFL Big Data Bowl 2027*

## 1. The question

When a receiver runs a 4.38, scouts ask two things: *will they play fast?* and *will they get open?* The 2027 data links Combine sensor tracking to the same players' regular-season (REG) tracking for 2023–25.

We keep four things separate throughout (Figure 1):

- **Capacity**: what an athlete can do on demand; here **tracked 40 peak speed** (yd/s).
- **Game movement**: what the player does on a snap; here the **maximum speed on each REG play** (before the throw for receivers).
- **Performance**: a result an evaluator cares about, here **receiver separation at the throw**.
- **Deployment**: how a team uses the player: route mix, coverage faced, EDGE or interior alignment, and body weight.

![Figure 1: four boxes — Combine capacity, game movement, football performance, and deployment feeding movement and performance.](figures/fig1_framework.png)

We ask which tracking measurements are reliable, how top speed translates to games, whether tracking adds anything about separation, how deployment shapes the numbers, and what evaluators can trust.

## 2. Data and design

- **Cohort.** 510 prospects (2023–25 classes). 418 have at least one valid tracked 40: a clean acceleration curve (R² > 0.95) and a peak ≤ 12.5 yd/s. 332 of them also have REG game rows.
- **Eligibility.** A player is analysed only with **at least 100 qualifying regular-season opportunities** (routes, coverage snaps, pass rushes or pass blocks).
  - This leaves out rarely used players. Playing time follows draft position, so the sample is selected: among receivers, strongly on draft capital and only weakly on speed (about 0.02 s on the 40).
  - Nothing here predicts draft busts or career success.
- **Unit of analysis: the player, not the play.** Final samples:

| position | players | plays |
|---|---|---|
| WR | 57 | 19,960 |
| DL | 53 | 34,154 |
| OL | 53 | 64,285 |
| DB | 52 | 16,643 |
| TE (descriptive only) | 17 | 4,170 |

- **Safeguards.** The plan was pre-registered and the code frozen before the single Combine-to-game join. The pipeline was first tested on simulated data with known answers. A faulty game and speed spikes are removed by rule.
- **Model.** A mixed model estimates each player's *noise-free* game-speed level in each context, after adjusting for route, coverage, down, distance, formation, time to throw, season, NFL year and team-season.
  - Its correlation with Combine peak speed (ρ) measures how far Combine speed "shows up" on the field; intervals come from resampling players 2,000 times.
- **Separation source.** Separation is the competition-supplied Next Gen Stats field `separation_at_pass_forward`. We did **not** rebuild nearest-defender distance; the game files track only cohort players. The field exists for every route on a thrown pass, targeted or not, and is missing on sacks and scrambles. Where a tracked cohort defender happened to be nearest, its tracked distance matched the supplied value. That is a consistency check on a subset, not proof of every defender assignment.

## 3. Which Combine tracking measurements are reliable?

![Figure 2: tracked peak speed reliability 0.94–0.99; share of variance not explained by the official 40: WR 34%, DB 36%, OL 19%, TE 17%, DL 5%.](figures/fig2_tracking_vs_forty.png)

- **Tracked top speed is highly repeatable.** Best-of-two reliability within position is 0.94 (WR) to 0.99 (DL).
- **The official 40 explains most, not all, of it.** About a third of its variance is not explained by the official 40 (WR 34%, DB 36%).
  - That remainder mixes real differences with measurement error in both numbers, and the 40's own repeatability cannot be measured here, so we do **not** claim tracked peak speed is a separate athletic capacity.
- **For defensive linemen, tracking adds almost nothing.** Peak speed, the 40, the 10-yard split and weight are nearly one dimension: speed–weight r = −0.80, and only 5% of peak-speed variance is not explained by the 40.
- **Early acceleration is not trustworthy.** The tracked 0–10 yd time barely repeats within WRs (reliability 0.20), and peak speed relates only weakly to the 10-yard split (ρ = −0.33).
- **Candidate drill measures were screened for reliability only**, never linked to game outcomes. Shuttle (0.21 within position) and three-cone (0.34) acceleration repeat poorly; DL "bend" barely agrees between left and right sides (0.14–0.31); WR route-start acceleration is consistent across routes (0.69) but only as a relative ranking. None is a validated performance measure.

## 4. Players reach near-top game speed more often on deep routes than on short routes

![Figure 3: plays reaching 90% of own top speed: WR deep 16.9%, WR short 0.8%, DL and OL 3% or less.](figures/fig3_speed_demand.png)

Using game data only, we counted how often a snap brings a player within 10% of their own top game speed.

- **WR deep routes do so on 17% of snaps, short routes on 1%.**
- DL and OL reach it on 3% of snaps or fewer.

This is descriptive. It is not a direct measurement of opportunity, and it is not evidence that Combine speed has a stronger effect on deep routes. It is why the pre-registered test compared deep with short routes.

## 5. Does Combine top speed show up in game speed?

![Figure 4: correlation of Combine and game speed by position and context, with 95% intervals; WR about 0.5–0.6, DB and OL weak.](figures/fig4_translation.png)

- **Receivers: yes, on both route types.** A WR's Combine top speed is associated with game speed: ρ = 0.58 on deep routes and 0.49 on short routes.
  - The raw slopes are equal: about 0.11 yd/s of game speed per 0.25 yd/s of Combine speed.
- **Primary question: is the link stronger on deep routes?**
  - **H1-WR: INCONCLUSIVE. Δ = ρ_deep − ρ_short = 0.090, 95% CI [−0.089, 0.400]** (p = 0.21).
  - Every registered robustness variant gave Δ between 0.07 and 0.12, and a shuffled-label control was centred at zero.
- **Why inconclusive, and what that does not mean.** Before seeing any data, our power analysis showed that 57 receivers give 80% power only for a difference of **0.27–0.33** (central scenario about 0.30). Power at a true difference of 0.20 was only about 0.44.
  - The interval includes zero, so a deep-route advantage is not supported; it also includes our smallest effect of interest (0.15), so it is not ruled out. This is **not** evidence that the two contexts are equivalent.
- **Other positions:** DL shows a strong pooled association (ρ ≈ 0.55) that Section 7 explains; DB (ρ 0.09–0.29) and OL (0.03–0.11) are weak and imprecise; TE (n = 17) is descriptive only.

## 6. Does tracked top speed make receivers more open?

![Figure 5: deep-route separation per SD of tracked speed, −0.7 inches (95% CI −3.6 to +2.3); held-out R² below the position average.](figures/fig5_h2_separation.png)

This is the Combine-to-performance link. Planned as primary, it was demoted to a secondary, estimation-focused analysis before any Combine-to-game association was examined, because simulations showed about 60 receivers could not power it.

**H2: INCONCLUSIVE. With the official 40 held fixed, β_P = −0.020 yd per SD of tracked peak speed, 95% CI [−0.101, 0.063]** (57 WRs, 9,935 deep routes on thrown passes).

- **No incremental predictive value was detected for tracked peak speed beyond the official 40 for deep-route separation.** The interval rules out a gain larger than about 2 inches per SD.
- On receivers left out of fitting, adding tracked speed to the 40 lowered out-of-sample R² by 0.024 (90% lower bound −0.036); neither model beat the position average. A 2025 season-forward check agreed (RMSE change −0.0003 yd), and correcting for error in the 40 kept the estimate at or below zero.

**This does not show that speed has no effect on separation.** Deep separation is a weak player trait:
- player-level reliability is **0.44**;
- the between-player SD is 0.13 yd, against 1.73 yd of play-to-play variation.

The data rule out a large added separation signal from tracked top speed. They cannot rule out a small one.

![Figure 6: receiver metric reliability before and after context adjustment; short-route separation falls from 0.75 to 0.22.](figures/fig6_reliability.png)

**Separation is shaped by context.** Raw separation looks like a stable receiver trait (reliability 0.81). After adjusting for route, coverage, down and formation, it falls to 0.61, and **short-route separation falls from 0.75 to 0.22.** Median separation differs by 1.6 yd between man and zone alone, so ranking receivers on raw separation largely ranks how they were used.

## 7. The pooled defensive-line speed association is substantially sensitive to role and body-weight adjustment

![Figure 7: EDGE lighter and faster than interior; pooled DL correlation 0.55 falls to about zero with role or weight, −0.27 with both.](figures/fig7_dl_role_weight.png)

EDGE rushers are lighter and faster than interior linemen: speed, weight and role travel together.

- **H1-DL(b) was supported after Holm adjustment (p = 0.032).** What was supported is the *change* between the pooled and adjusted estimates. The pooled association is **substantially sensitive to role and weight adjustment**: it falls from 0.55 to −0.27 when role and Combine weight are both adjusted for (registered difference 0.82, 95% CI [0.16, 1.54]).
- **Descriptively,** role alone (−0.05) or weight alone (−0.08) removes nearly all of it, and within EDGE (0.05) and within interior linemen (0.01) it is about zero.
- **This is not a causal statement.** The jointly adjusted −0.27 is imprecise (its interval spans zero). It is not evidence that speed hurts linemen: role is partly *chosen because of* athleticism, and these data cannot separate the three.

## 8. What evaluators can and cannot trust

| Measurement or claim | What the evidence shows | Use it? |
|---|---|---|
| Tracked 40 peak speed | repeatable (0.94–0.99); the 40 explains ~two-thirds for WR/DB, nearly all for DL | Yes, alongside the 40; not as a separate capacity |
| 0–10 yd time, drill acceleration, DL "bend" | low repeatability | No |
| WR Combine speed → game speed | ρ 0.49–0.58 on both route types; deep advantage inconclusive | Yes, as a guide to how fast a receiver plays |
| Tracked speed → deep separation, beyond the 40 | nothing detected; small effects not excluded | No separation premium |
| Raw separation | largely route and coverage context | Compare within similar usage |
| Pooled DL speed association | sensitive to role and body weight | Judge within body type and alignment |

**Limitations:**
- **Players, not plays, limit learning:** 52–57 per position, so only large differences were detectable.
- **Observational and selected:** usage partly results from athleticism; eligibility required 100 opportunities.
- **Movement is not performance:** separation is the only (noisy) performance outcome; DB coverage outcomes cannot be built.
- **A follow-up we chose not to run:** whether tracked peak speed adds to the 40 for *game speed*. A simulation judged against criteria fixed in advance showed 57 receivers were too few, so that model was never fitted to real data. It supports no conclusion either way.

We make no novelty claim: these are pre-registered estimates with honest uncertainty.

## Appendix: reproducibility and references

- **Notebook.** The public Kaggle notebook re-runs data validation, Combine feature definitions and the registered sample sizes from the competition files, and draws every figure from the stored registered results. Confirmatory models are one-shot and not re-fitted.
- **Registered analyses:** H1-WR (primary); H2 (secondary, estimation); Holm family H1-DB, H1-DL(a), H1-DL(b), H5(b). On simulated data the pipeline kept false positives at or below 0.0125 against a nominal 0.025.
- **Literature** (DOIs verified; abstracts read; full texts not read):
  - Clark K.P. et al. (2019). *The NFL combine 40-yard dash: how important is maximum velocity?* J Strength Cond Res 33(6):1542–1550. doi:10.1519/JSC.0000000000002081.
  - Morin J-B. et al. (2021). *Individual acceleration-speed profile in-situ: a proof of concept in professional football players.* J Biomech 123:110524. doi:10.1016/j.jbiomech.2021.110524.
