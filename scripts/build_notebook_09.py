"""Build notebooks/09_h2_estimation_analysis.ipynb from the single H2 estimation run (models are not refitted;
only deterministic, labelled post-run diagnostics are recomputed)."""
import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
nb = nbf.v4.new_notebook(); C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s))  # noqa: E731
code = lambda s: C.append(nbf.v4.new_code_cell(s))  # noqa: E731

md("""# 09 · H2: incremental value of tracked peak speed beyond the official 40 (secondary, estimation-focused)

**Status (D4):** H2 was registered as the second primary test. Before any association was inspected it was demoted to a **secondary, estimation-focused** analysis.
- Its registered variables, 57-WR sample, model, measurement-error grid, player-grouped CV and decision criteria are preserved.
- The criteria are evaluated **descriptively**. Nothing here is confirmatory evidence.

This notebook displays the single run `scripts/run_h2_estimation.py`. DB, DL, OL and TE have not been analysed.""")
code("""import json, sys
from pathlib import Path
import numpy as np, polars as pl, matplotlib.pyplot as plt
ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from nfl_bdb.visualization import style
style.apply(); pl.Config.set_tbl_rows(40); pl.Config.set_fmt_str_lengths(60)
RUN = (ROOT / 'experiments/h2_estimation/LATEST').read_text().strip(); OUT = ROOT / 'experiments/h2_estimation' / RUN
R = json.load(open(OUT / 'h2_result.json')); BS = np.load(OUT / 'bootstraps.npz')
print('run', RUN, '| code commit', R['code_commit'], '| join', R['join_run'], '| seeds', R['seeds'], '| B', R['B'], '| B_cv', R['B_cv'])
print(json.dumps(R['sample'], indent=1))""")
md("## 1. Incremental effect estimate (REML, deep routes)")
code("""d, rb = R['deep'], R['reml_bootstrap']
pl.DataFrame([dict(quantity=k, estimate=str(v)) for k, v in [
    ('β_P (yd of deep separation per within-sample SD of peak speed, 40 held fixed)', round(d['beta_P'], 4)),
    ('  95% CI, REML player-cluster bootstrap (registered)', [round(v, 4) for v in rb['deep_beta_P']['ci95']]),
    ('  90% CI', [round(v, 4) for v in rb['deep_beta_P']['ci90']]),
    ('  bootstrap SE / two-sided p', (round(rb['deep_beta_P']['se'], 4), round(R['p_boot_reml'], 3))),
    ('  Wald SE / z / p (t, df 54)', (round(d['se_wald'], 4), round(R['wald']['z'], 3), round(R['wald']['p_t_df'], 3))),
    ('  two-stage WLS (HC3) β_P / 95% bootstrap CI (Phase-4-validated check)', (round(R['two_stage']['beta_P'], 4), [round(v, 4) for v in R['two_stage']['ci95_boot']])),
    ('β_F (official 40, sign-reversed, per SD)', round(d['beta_F'], 4)), ('  95% CI', [round(v, 4) for v in rb['deep_beta_F']['ci95']]),
    ('β_P* (true-level SD units)', round(d['beta_P_std'], 3)), ('true-scale partial correlation r_P·F', round(d['partial'], 3)),
    ('  95% bootstrap interval (degenerate, see §1b)', [round(v, 3) for v in rb['deep_partial']['ci95']]),
    ('ΔR² of the true between-player level', round(d['dR2_true'], 4)), ('R² true level: F alone / F + x', (round(d['R2_true_F'], 4), round(d['R2_true_full'], 4))),
    ('between-player SD of deep separation (yd) / residual SD', (round(d['s2b'] ** 0.5, 3), round(d['s2'] ** 0.5, 3))),
    ('mean reliability of player deep-separation levels', round(R['reliability_deep_level'], 3)), ('corr(F, x) in the 57', round(R['sample']['r_F_x'], 3))]])""")
md("""### 1b. Why the true-scale partial correlation has no usable interval
The between-player variance of deep separation is small (σ_b ≈ 0.13 yd; the play-level SD is ≈ 1.7 yd). In many resamples REML puts it at the boundary (≈ 0). The partial correlation, β_P / √(β_P²(1 − r²) + σ_b²), then becomes ±1. The raw-scale β_P stays well behaved.""")
code("""fig, ax = plt.subplots(1, 2, figsize=(11, 3.4))
ax[0].hist(BS['deep_beta_P'], bins=60, color=style.SERIES[0], alpha=0.7, label='deep (H2)')
ax[0].hist(BS['short_beta_P'], bins=60, color=style.SERIES[1], alpha=0.5, label='short (N3)')
ax[0].axvline(0, color=style.MUTED); ax[0].set_xlabel('β_P* bootstrap (yd per SD of peak, 40 fixed)'); ax[0].legend(); ax[0].set_title('β_P: REML player bootstrap')
ax[1].hist(BS['deep_partial'], bins=60, color=style.SERIES[2], alpha=0.75)
ax[1].set_xlabel('true-scale partial correlation (bootstrap)'); ax[1].set_title('share at ±1: %.2f' % np.mean(np.abs(BS['deep_partial']) > 0.99))
fig.tight_layout(); fig.savefig(ROOT / 'reports/figures/h2_bootstrap.png', dpi=150); plt.show()""")
md("## 2. Prediction on held-out players (never held-out plays)")
code("""cvf, cve, loo = R['cv_frozen'], R['cv_extended'], R['cv_lopo']
print('Registered criterion engine (frozen h2_cv, 10-fold x 20): R2_CV M1 %.4f, M2 %.4f, ΔR²_CV %.4f; 90%% bootstrap lower bound (B=%d) %.4f' %
      (cvf['r2_m1'], cvf['r2_m2'], cvf['dr2'], R['B_cv'], cvf['lb90']))
rows = []
for m_ in ['M0', 'M1', 'M2', 'M2s', 'M3']:
    rows.append(dict(model=m_, R2_cv=cve[f'R2_{m_}'], RMSE_cv=cve[f'RMSE_{m_}'], spearman_cv=cve[f'spearman_{m_}'], lpd_cv=cve[f'lpd_{m_}'],
                     R2_lopo=loo[f'R2_{m_}'], RMSE_lopo=loo[f'RMSE_{m_}']))
display(pl.DataFrame(rows))
print('extended (stratified by draft class): ΔR² %.4f (SD over repeats %.4f), ΔRMSE %.4f, ΔSpearman %.3f, ΔLPD %.4f' %
      (cve['dR2_CV'], cve['repeat_dR2_sd'], cve['dRMSE_CV'], cve['dSpearman_CV'], cve['dLPD_CV']))
print('season-forward (fit 2023-24, predict 2025 levels):', {k: (round(v, 4) if isinstance(v, float) else v) for k, v in R['season_forward'].items()})""")
code("""fig, ax = plt.subplots(figsize=(7, 3.2))
ax.bar(range(5), [cve[f'R2_{m_}'] for m_ in ['M0', 'M1', 'M2', 'M2s', 'M3']], color=[style.MUTED, style.SERIES[0], style.SERIES[1], style.SERIES[2], style.SERIES[3]])
ax.axhline(0, color='k', lw=0.8); ax.set_xticks(range(5), ['M0 mean', 'M1 40', 'M2 40+peak', 'M2s 40+spline', 'M3 40+10yd'])
ax.set_ylabel('R² on held-out players'); ax.set_title('Held-out-player prediction of deep separation level')
fig.tight_layout(); fig.savefig(ROOT / 'reports/figures/h2_cv.png', dpi=150); plt.show()""")
md("## 3. Measurement error in the official 40: increment vs precision")
code("""display(pl.DataFrame(R['eiv_grid']))
print('registered EIV refit (R_F 0.95, R_x 0.987): β_P %.4f, 95%% bootstrap CI [%.4f, %.4f]' % (R['eiv_registered']['beta_P'], *R['eiv_registered']['ci95']))
print('tipping point as stored by the run (DEFECTIVE helper, = EIV singularity):', R['eiv_tipping_RF'])""")
md("""**Post-run correction (deterministic; no estimate changes).** The stored "tipping points" equal r(F, x)²/R_x. That is the admissibility bound below which the EIV correction is undefined, and where β_P flips sign through infinity. The corrected helper searches only the admissible range.""")
code("""import run_h2_estimation as H
from nfl_bdb.models import confirmatory as cf, h2_extensions as h2
ids, F, x, ten, dc, A = H.load(); D = A['deep']
res = cf.residualise_np(D['W'], D['y']); m, n, sw2 = cf.player_stats(D['pid'], res, len(ids))
fig, ax = plt.subplots(figsize=(7, 3.2))
for k, rx in enumerate((0.94, 0.987)):
    lo = h2.admissible_rel_F(F, x, rx); g = np.linspace(lo + 0.01, 1.0, 60)
    ax.plot(g, [cf.eiv_two_stage(m, n, sw2, F, x, rel_F=f, rel_x=rx)[1] for f in g], color=style.SERIES[k], label=f'R_x = {rx} (admissible R_F > {lo:.3f})')
    print(f'R_x {rx}: admissible R_F > {lo:.4f}; corrected tipping point: {h2.tipping_point(m, n, sw2, F, x, rx)}')
ax.axhline(0, color=style.MUTED); ax.set_xlabel('assumed reliability of the official 40 (R_F)'); ax.set_ylabel('EIV β_P'); ax.legend(fontsize=8)
ax.set_title('EIV β_P is ≤ 0 for every admissible R_F'); fig.tight_layout(); plt.show()""")
code("""art = pl.DataFrame(R['precision_artefact']).with_columns(pl.col('a').round(3), pl.col('spurious_partial').round(3))
print('validity of the observed 40 for the true deep-separation level (sqrt R² true, F):', round(R['validity_obs'], 3))
art = art.filter(pl.col('rel_x') == 0.987).with_columns(pl.when(pl.col('a') == 0.3).then(pl.lit('a = 0.3')).when(pl.col('a') == 0.6).then(pl.lit('a = 0.6'))
                                                     .otherwise(pl.lit('a = estimated')).alias('validity'))
print('Expected spurious partial (peak | observed 40) if separation depended ONLY on true 40 speed; R_x cancels algebraically.')
print('Observed REML partial for comparison: %.3f (raw β_P %.4f)' % (R['deep']['partial'], R['deep']['beta_P']))
art.pivot(index='rel_F', on='validity', values='spurious_partial').sort('rel_F')""")
md("## 4. Registered H2 negative control N3: WR short-route separation")
code("""s, c = R['short'], R['contrast_N3']
print('short routes: β_P %.4f (Wald SE %.4f), 95%% bootstrap CI [%.4f, %.4f]; β_F %.4f' % (s['beta_P'], s['se_wald'], *rb['short_beta_P']['ci95'], s['beta_F']))
print('contrast β_P(deep) − β_P(short): %.4f, 95%% CI [%.4f, %.4f], 90%% CI [%.4f, %.4f]' % (c['estimate'], *c['ci95'], *c['ci90']))""")
md("## 5. Registered H2 decision criteria (evaluated descriptively, D4)")
code("""pl.DataFrame([dict(criterion=k, value=str(v)) for k, v in R['criteria'].items()])""")
md("See `research_notes/h2_estimation_results.md` for the interpretation.")
nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, ROOT / "notebooks/09_h2_estimation_analysis.ipynb")
print("written")
