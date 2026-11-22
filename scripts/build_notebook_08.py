"""Build notebooks/08_h1_wr_confirmatory_analysis.ipynb from the single confirmatory run (no model is refitted here)."""
import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
nb = nbf.v4.new_notebook(); C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s))  # noqa: E731
code = lambda s: C.append(nbf.v4.new_code_cell(s))  # noqa: E731

md("""# 08 · H1-WR confirmatory analysis (sole primary hypothesis)

This notebook **only displays** the result of the single registered run produced by `scripts/run_h1_wr_confirmatory.py`. No model is refitted here.

**Registered specification** (preregistration §2, §6, §8–§12; deviations D1–D4):
- **Model:** REML bivariate-context linear mixed model.
- **Inference:** full REML player-cluster percentile bootstrap, B = 2,000.
- **Decision:** supported iff Δ̂ > 0, the 95 % CI excludes 0, and the 2025 season-forward estimate has the same sign.
- **Falsified** iff the 90 % CI upper bound is < 0.15, or the 95 % CI lies entirely below 0.
- **Otherwise:** inconclusive.

H2, DB, DL, OL and TE have **not** been analysed.

**Structure:**
- **Part A:** the confirmatory result (unchanged).
- **Part B:** registered sensitivity analyses and negative controls.
- **Part C:** exploratory interval diagnostics.""")
code("""import json, sys
from pathlib import Path
import numpy as np, polars as pl, matplotlib.pyplot as plt
ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT / 'src'))
from nfl_bdb.visualization import style
style.apply(); pl.Config.set_tbl_rows(40); pl.Config.set_fmt_str_lengths(60)
import os
OUT = Path(os.environ['H1_OUT']) if os.environ.get('H1_OUT') else ROOT / 'experiments/h1_wr_confirmatory' / (ROOT / 'experiments/h1_wr_confirmatory/LATEST').read_text().strip()
RUN = OUT.name
R = json.load(open(OUT / 'h1_wr_result.json'))
boot = np.load(OUT / 'bootstrap_delta.npy'); jack = np.load(OUT / 'jackknife_delta.npy')
print('run', RUN, '| code commit', R['code_commit'], '| join', R['join_run'], '| seed', R['seed'], '| B', R['B'])
print('DECISION:', R['decision'])""")
md("## 1. Primary result")
code("""P = R['primary']
pl.DataFrame([dict(quantity=k, value=str(v)) for k, v in [
    ('Δ̂ = ρ_deep − ρ_short (REML)', round(P['delta'], 4)), ('ρ_deep', round(P['rho_deep'], 4)), ('ρ_short', round(P['rho_short'], 4)),
    ('95% percentile CI', [round(v, 4) for v in P['ci95_percentile']]), ('90% percentile CI', [round(v, 4) for v in P['ci90_percentile']]),
    ('bootstrap SE', round(P['se_boot'], 4)), ('two-sided bootstrap p', round(P['p_two_sided'], 4)),
    ('Δ̂ > 0', P['delta_positive']), ('95% CI excludes 0 (positive)', P['ci_excludes_0_positive']),
    ('2025 season-forward Δ̂', round(P['season_forward']['delta_2025'], 4)), ('season-forward same sign', P['season_forward_same_sign']),
    ('falsified: 90% upper < 0.15', P['falsification']['ci90_upper_below_sesoi']), ('falsified: 95% CI < 0', P['falsification']['ci95_entirely_below_0']),
    ('DECISION', R['decision'])]])""")
code("""fig, ax = plt.subplots(figsize=(9, 3.6))
ax.hist(boot, bins=60, color=style.SERIES[0], alpha=0.7)
for v, ls, lab in [(P['delta'], '-', 'Δ̂'), (P['ci95_percentile'][0], '--', '95% CI'), (P['ci95_percentile'][1], '--', None),
                   (P['ci90_percentile'][1], ':', '90% upper'), (0.15, '-.', 'SESOI 0.15'), (0, '-', None)]:
    ax.axvline(v, ls=ls, color=style.MUTED if v in (0, 0.15) else style.SERIES[1], lw=1.2, label=lab)
ax.set_xlabel('bootstrap Δ* (2,000 full REML refits)'); ax.set_ylabel('count'); ax.legend(); ax.set_title('H1-WR: bootstrap distribution of Δ')
fig.tight_layout(); fig.savefig(ROOT / 'reports/figures/h1_wr_bootstrap.png', dpi=150); plt.show()""")
md("## 2. Sample and observations per context")
code("""S = R['sample']
print('players', S['players'], '| plays', S['plays'], '| team-seasons', R['diagnostics']['team_seasons'],
      '(single-player team-seasons', R['diagnostics']['team_seasons_single_player'], ')')
display(pl.DataFrame(S['by_context'])); display(pl.DataFrame(S['plays_per_player_context'])); pl.DataFrame(S['seasons'])""")
md("## 3. Convergence and diagnostics")
code("""D = R['diagnostics']; Bt = R['bootstrap']
print(json.dumps({k: D[k] for k in ('converged', 'sigma_b', 'corr_b', 's2_team', 's2_resid', 'fixed_effect_columns', 'reliability_player_context_mean')}, indent=1))
print('bootstrap refits OK:', Bt['n_ok'], 'failed:', Bt['n_failed'], '| boot mean', round(Bt['mean'], 4), 'sd', round(Bt['sd'], 4),
      '| median − Δ̂', round(Bt['median_minus_estimate'], 4))
print('season-forward fit:', P['season_forward'])
print('seconds:', R['seconds'])""")
md("## 4. Registered accompanying reports (none affects the decision)")
code("""E = R['effect_size']; M = R['cross_check_moment']; Bc = R['bca']; By = R['bayes_sensitivity']
print('BCa 95%:', [round(v, 4) for v in Bc['ci']['0.95']], '| BCa 90%:', [round(v, 4) for v in Bc['ci']['0.9']], '| z0', round(Bc['z0'], 3), 'a', round(Bc['acceleration'], 4))
print('raw slopes (yd/s of game speed per 0.25 yd/s combine peak): deep %.3f, short %.3f' % tuple(E['raw_slope_per_0_25_yds']))
display(pl.DataFrame([dict(R_x=k, **v) for k, v in E['disattenuated'].items()]))
print('moment cross-check (spec §1.2, never decisive): Δ =', round(M['delta'], 4), 'ρ =', [round(v, 4) for v in M['rho']], '| disagrees by > SE/2:', M['disagrees_by_more_than_half_se'])
print('Bayesian sensitivity (prior N(0, 0.15²)): posterior mean %.3f, sd %.3f, P(Δ>0) %.3f, P(Δ>0.15) %.3f' %
      (By['posterior_mean'], By['posterior_sd'], By['p_delta_gt_0'], By['p_delta_gt_sesoi']))""")
md("""## 5. Interpretation of the confirmatory result

See `research_notes/h1_wr_confirmatory_results.md`.

---
# Part B: registered sensitivity analyses (they do not re-decide H1)

From `scripts/run_h1_wr_robustness.py`. Notes: `h1_wr_robustness_results.md` and `h1_wr_negative_controls.md`.""")
code("""ROB = ROOT / 'experiments/h1_wr_robustness' / (ROOT / 'experiments/h1_wr_robustness/LATEST').read_text().strip()
RB = json.load(open(ROB / 'robustness.json')); DG = json.load(open(ROB / 'bootstrap_diagnostics.json'))
print('robustness run', ROB.name, '| code commit', RB['code_commit'], '| seeds', RB['seeds'])
lab = {'R1': 'R1 eligibility >= 50', 'R2': 'R2 eligibility >= 200', 'R3': 'R3 without time-to-throw', 'R4': 'R4 REG + POST',
       'R8': 'R8 mean-of-attempts peak', 'R9': 'R9 IN/CROSS as short', 'R11': 'R11 + playing time',
       'R12_class_2023': 'R12 class 2023', 'R12_class_2024': 'R12 class 2024', 'R12_class_2025': 'R12 class 2025 (new players)',
       'R13_2023_2024': 'R13 2023+2024 fit', 'R13_2025': 'R13 2025 fit'}
rows = [dict(check='PRIMARY (confirmatory)', delta=P['delta'], ci_lo=P['ci95_percentile'][0], ci_hi=P['ci95_percentile'][1], se=P['se_boot'], players=S['players'], plays=S['plays'])]
rows += [dict(check=lab[k], delta=v['delta'], ci_lo=v['ci_lo'], ci_hi=v['ci_hi'], se=v['se_boot'], players=v['players'], plays=v['plays']) for k, v in RB['registered'].items()]
C6 = RB['R6_ceiling']; rows.append(dict(check='R6 ceiling-robust outcome', delta=C6['delta'], ci_lo=C6['ci'][0], ci_hi=C6['ci'][1], se=C6['se_boot'], players=C6['players'], plays=None))
SEN = pl.DataFrame(rows, infer_schema_length=None); SEN""")
code("""fig, ax = plt.subplots(figsize=(8, 6))
yy = np.arange(SEN.height)[::-1]
ax.errorbar(SEN['delta'], yy, xerr=[SEN['delta'] - SEN['ci_lo'], SEN['ci_hi'] - SEN['delta']], fmt='o', color=style.SERIES[0], capsize=2)
ax.plot(SEN['delta'][0], yy[0], 'o', color=style.SERIES[1], ms=9)
ax.axvline(0, color=style.MUTED, lw=1); ax.axvline(0.15, color=style.MUTED, lw=1, ls='-.', label='SESOI 0.15')
ax.set_yticks(yy, SEN['check']); ax.set_xlabel('Δ = ρ_deep − ρ_short (95% CI, full REML bootstrap)'); ax.legend(loc='lower right')
ax.set_title('H1-WR: registered sensitivity analyses')
fig.tight_layout(); fig.savefig(ROOT / 'reports/figures/h1_wr_sensitivity_forest.png', dpi=150); plt.show()""")
code("""lo = np.array([x['delta'] for x in RB['R5_leave_one_team_out']])
print('R5 leave-one-team-out: %d teams, delta range %.3f to %.3f' % (len(lo), lo.min(), lo.max()))
SP = RB['R7_spline']; cvd = pl.DataFrame(SP['cv'])
sb = np.load(ROB / 'bootstraps.npz')['spline']
print('R7 spline: avg derivative deep %.3f short %.3f, diff %.3f, 95%% CI [%.3f, %.3f] | linear slope diff %.3f' %
      (SP['avg_deriv'][0], SP['avg_deriv'][1], SP['diff'], *np.nanpercentile(sb[:, 2], [2.5, 97.5]), SP['linear_slope_diff']))
print('R7 player-grouped CV (10x20): RMSE linear %.4f, spline %.4f, spline better in %d/20 repeats' %
      (cvd['rmse_linear'].mean(), cvd['rmse_spline'].mean(), int((cvd['rmse_spline'] < cvd['rmse_linear']).sum())))
fig, ax = plt.subplots(figsize=(6, 3.6))
g = np.array(SP['grid']); cu = np.array(SP['curves'])
for c, name in enumerate(['deep', 'short']):
    ax.plot(g, cu[c] - cu[c].mean(), color=style.SERIES[c], label=name)
ax.set_xlabel('combine peak speed (within-sample SD units)'); ax.set_ylabel('f_c(x), centred (yd/s)'); ax.legend(); ax.set_title('R7 spline fits')
fig.tight_layout(); plt.show()
display(pl.DataFrame(RB['R14_selection']))""")
md("""## Negative control N1: context labels permuted within player (registered)
N2 (OL contrast) and N3 (WR short-route β_P) belong to H5 and H2, which are deferred.""")
code("""pv = np.array([x['delta'] for x in RB['N1_permutation']])
print('N1: %d permutations, mean %.4f (MC SE %.4f), SD %.3f, 2.5/97.5%% [%.3f, %.3f]' % (len(pv), pv.mean(), pv.std() / np.sqrt(len(pv)), pv.std(), *np.percentile(pv, [2.5, 97.5])))
fig, ax = plt.subplots(figsize=(7, 3.2))
ax.hist(pv, bins=40, color=style.SERIES[2], alpha=0.75); ax.axvline(0, color=style.MUTED); ax.axvline(P['delta'], color=style.SERIES[1], ls='--', label='observed Δ̂ (not a test)')
ax.set_xlabel('Δ̂ with permuted context labels'); ax.legend(); ax.set_title('N1: no mechanical artefact if centred at 0')
fig.tight_layout(); plt.show()""")
md("""---
# Part C: exploratory diagnostics (bootstrap intervals and the Wald check)
These diagnostics explain the intervals. **The registered percentile interval remains primary.** See `h1_wr_bootstrap_diagnostics.md`.""")
code("""print(json.dumps({k: DG[k] for k in ('distribution', 'bca')}, indent=1)[:2500])
display(pl.DataFrame([dict(variant=k, level_lo=v['levels'][0], level_hi=v['levels'][1], lo=v['interval'][0], hi=v['interval'][1]) for k, v in DG['bca']['decomposition'].items()]))
display(pl.DataFrame(DG['phase4_bootstrap_world']))""")
code("""J = DG['jackknife']; print('player jackknife: range', [round(v, 3) for v in J['range']], '| max change', round(J['max_abs_change'], 3), '| sign changes', J['sign_changes'], '| jackknife SE', round(J['sd_jackknife_se'], 3))
display(pl.DataFrame(J['top5_influence']))
for k in ('leave_one_team_out', 'leave_one_team_season_out'):
    print(k, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in DG[k].items()})
W = DG['wald']; print('Wald: delta %.4f, SE %.4f, 95%% CI [%.3f, %.3f], 90%% CI [%.3f, %.3f]; criterion reproduced to %.1e; Hessian eigen [%.1f, %.1f]' %
      (W['delta'], W['se'], *W['ci95'], *W['ci90'], W['criterion_reproduced_abs_diff'], W['hessian_min_eig'], W['hessian_max_eig']))
cal = ROOT / 'experiments/h1_wr_robustness_dev/wald_calibration.parquet'
if cal.exists():
    wc = pl.read_parquet(cal)
    display(wc.group_by('scenario').agg(pl.len().alias('reps'), pl.col('delta').std().alias('sd_delta'), pl.col('se').mean().alias('mean_wald_se'),
        ((pl.col('delta') - pl.col('truth')).abs() <= 1.96 * pl.col('se')).mean().alias('coverage'), ((pl.col('delta') - 1.96 * pl.col('se')) > 0).mean().alias('reject')).sort('scenario'))""")
code("""fig, ax = plt.subplots(figsize=(8, 2.8))
iv = [('percentile (primary)', P['ci95_percentile']), ('BCa', DG['bca']['decomposition']['full_bca']['interval']), ('Wald (check)', W['ci95'])]
for k, (name, (lo_, hi_)) in enumerate(iv):
    ax.plot([lo_, hi_], [k, k], lw=5, color=style.SERIES[k], solid_capstyle='butt'); ax.plot(P['delta'], k, 'k|', ms=14)
ax.axvline(0, color=style.MUTED); ax.axvline(0.15, color=style.MUTED, ls='-.')
ax.set_yticks(range(3), [n for n, _ in iv]); ax.set_xlabel('Δ (95% intervals)'); ax.set_title('H1-WR: the three registered intervals')
fig.tight_layout(); fig.savefig(ROOT / 'reports/figures/h1_wr_intervals.png', dpi=150); plt.show()""")
nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, ROOT / "notebooks/08_h1_wr_confirmatory_analysis.ipynb")
print("written")
