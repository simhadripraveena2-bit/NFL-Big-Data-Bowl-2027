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

H2, DB, DL and OL have **not** been analysed.""")
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
md("""## 5. Interpretation

See `research_notes/h1_wr_confirmatory_results.md`.""")
nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, ROOT / "notebooks/08_h1_wr_confirmatory_analysis.ipynb")
print("written")
