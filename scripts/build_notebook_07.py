"""Build notebooks/07_synthetic_pipeline_validation.ipynb (then execute with nbconvert).
All numbers come from experiments/synthetic_validation/<LATEST>/ produced by run_synthetic_validation.py."""
import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
nb = nbf.v4.new_notebook(); C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s))  # noqa: E731
code = lambda s: C.append(nbf.v4.new_code_cell(s))  # noqa: E731

md("""# 07 · Phase 4: synthetic validation of the registered confirmatory pipeline

**No combine measurement is joined to any NFL game outcome here.** Every synthetic dataset uses a *real design*: actual eligible players, plays per context, team-seasons, routes, coverages, downs, seasons and experience. Its outcome and combine predictors are synthetic.

Nuisance parameters come from outcome-only REML fits.

How to reproduce:
1. Run `python scripts/run_synthetic_validation.py skeleton`.
2. Run each stage, `h1 h1_db h2 selection family selection_real demand_real demand_reliability demand_sim h1_s8fix h1_warp`, with a common run id.
3. Run `python scripts/build_notebook_07.py`, then execute this notebook.

Seeds come from `SeedSequence([4004, scenario, replicate])`.""")
code("""import json, sys
from pathlib import Path
import numpy as np, polars as pl, matplotlib.pyplot as plt
ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path[:0] = [str(ROOT / 'src'), str(ROOT / 'scripts')]
from nfl_bdb.visualization import style
from nfl_bdb.models.validation_summary import summarise_h1, summarise_h2
import phase4_stages as ps
style.apply()
pl.Config.set_tbl_rows(60); pl.Config.set_tbl_cols(30); pl.Config.set_tbl_width_chars(220); pl.Config.set_float_precision(3)
RUN = (ROOT / 'experiments/synthetic_validation/LATEST').read_text().strip()
OUT = ROOT / 'experiments/synthetic_validation' / RUN
FIG = ROOT / 'reports/figures'
cal = json.load(open(ROOT / 'data/interim/phase4/calibration.json'))
print('run', RUN); print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk in ('n_eligible','n_players','n_team','s2_team','sigma_b','s2b','corr_b','team_share_of_between','reliability_mean')} for k, v in cal.items()}, indent=1))""")
md("## 1. H1: registered procedure across the six required scenario families")
code("""h1 = pl.read_parquet(OUT / 'h1_WR.parquet')
fix = OUT / 'h1_WR_s8fix.parquet'
if fix.exists():
    h1 = pl.concat([h1.filter(pl.col('scenario') != 8), pl.read_parquet(fix)], how='diagonal_relaxed')
S1 = summarise_h1(h1)
S1.select('scenario','label','reps','true_delta_obs','reject','reject_mcse','reject_holm','reject_raw_contrast',
          'mean_delta_reml','bias_reml','bias_reml_mcse','bias_moment','coverage95','coverage_mcse','sd_delta_reml','mean_se_boot','disagree_rate')""")
code("""warp_path = OUT / 'h1_warp.parquet'
if warp_path.exists():
    W = pl.read_parquet(warp_path)
    WR = pl.concat([ps.warp_decisions(W, 'delta_reml', 'reml_boot'), ps.warp_decisions(W, 'delta_moment', 'moment_boot')])
    exact = W.group_by('scenario').agg(pl.col('supported_full_moment').mean().alias('exact_full_B_moment_reject')).sort('scenario')
    display(WR.sort('scenario','estimator').join(exact, on='scenario'))""")
code("""fig, ax = plt.subplots(1, 2, figsize=(12, 3.8))
pw = S1.filter(pl.col('scenario').is_in([1, 3, 4, 5])).sort('true_delta_obs')
ax[0].errorbar(pw['true_delta_obs'], pw['reject'], yerr=1.96*pw['reject_mcse'], marker='o', color=style.SERIES[0], label='registered (REML Δ̂, moment bootstrap CI)')
ax[0].plot(pw['true_delta_obs'], pw['reject_holm'], marker='s', color=style.SERIES[1], label='Holm level α/3')
ax[0].axhline(0.8, color=style.MUTED, ls='--', lw=1); ax[0].axhline(0.025, color=style.MUTED, ls=':', lw=1)
ax[0].set_xlabel('true Δ (observed-x scale)'); ax[0].set_ylabel('P(H1-WR supported)'); ax[0].legend(); ax[0].set_title('H1-WR: power and size')
lab = {1:'S1 null', 2:'S1b null (0/0)', 6:'S5a deployment', 7:'S5b selection', 8:'S6 diff. reliability', 10:'null, empirical resid'}
nul = S1.filter(pl.col('scenario').is_in(list(lab))).sort('scenario')
ypos = np.arange(nul.height)
ax[1].errorbar(nul['reject'], ypos, xerr=1.96*nul['reject_mcse'], fmt='o', color=style.SERIES[0], label='registered')
ax[1].plot(nul['reject_raw_contrast'], ypos, 'x', color=style.SERIES[3], label='raw (attenuated) contrast')
ax[1].axvline(0.025, color=style.MUTED, ls=':', lw=1); ax[1].axvline(0.05, color=style.MUTED, ls='--', lw=1)
ax[1].set_yticks(ypos, [lab[s] for s in nul['scenario']]); ax[1].set_xlabel('false-positive rate (true Δ = 0)'); ax[1].legend(); ax[1].set_title('H1-WR: false positives')
fig.tight_layout(); fig.savefig(FIG / 'p4_h1_power_size.png', dpi=150); plt.show()""")
code("""fig, ax = plt.subplots(figsize=(11, 3.8))
order = [1, 2, 3, 4, 5, 6, 7, 8, 9]
data, labels, cols = [], [], []
for s in order:
    g = h1.filter(pl.col('scenario') == s); tr = g['true_delta_obs'][0]
    data += [g['delta_reml'].to_numpy() - tr, g['delta_moment'].to_numpy() - tr, g['delta_naive_unadj'].to_numpy() - tr]
    labels += [f'S{s}\\nREML', 'moment', 'naive']; cols += [style.SERIES[0], style.SERIES[1], style.SERIES[3]]
bp = ax.boxplot(data, widths=0.6, patch_artist=True, showfliers=False)
for p, c in zip(bp['boxes'], cols): p.set_facecolor(c); p.set_alpha(0.55)
ax.axhline(0, color=style.MUTED, lw=1); ax.set_xticks(range(1, len(labels)+1), labels, fontsize=7); ax.set_ylabel('estimate − truth')
ax.set_title('H1-WR: estimation error by scenario (REML = registered point estimate)')
fig.tight_layout(); fig.savefig(FIG / 'p4_h1_bias.png', dpi=150); plt.show()""")
code("""direct = OUT / 'h1_direct.parquet'
if direct.exists():
    D = pl.read_parquet(direct)
    W = pl.read_parquet(OUT / 'h1_warp.parquet').select('scenario','rep', pl.col('delta_reml').alias('d_warp'), 'reml_boot')
    J = D.join(W, on=['scenario','rep'])
    rows = []
    for s, g in J.group_by('scenario', maintain_order=True):
        allw = W.filter(pl.col('scenario') == s)
        cen = np.concatenate([np.asarray(b) - e for b, e in zip(allw['reml_boot'].to_list(), allw['d_warp'].to_list())])
        qlo = np.percentile(cen, 2.5)
        warp_lo = g['delta_reml'].to_numpy() + qlo
        rows.append(dict(scenario=s, reps=g.height, same_point_estimate=bool(np.allclose(g['delta_reml'], g['d_warp'])),
                         direct_reject=float(((g['ci_lo'] > 0) & (g['delta_reml'] > 0)).mean()),
                         direct_coverage=float(((g['ci_lo'] <= g['true_delta_obs']) & (g['ci_hi'] >= g['true_delta_obs'])).mean()),
                         mean_direct_se=float(g['se'].mean()), pooled_warp_sd=float(cen.std()),
                         corr_lower_bounds=float(np.corrcoef(g['ci_lo'], warp_lo)[0, 1]),
                         mean_lower_bound_diff=float((g['ci_lo'] - warp_lo).mean())))
    display(pl.DataFrame(rows))""")
code("""db = summarise_h1(pl.read_parquet(OUT / 'h1_DB.parquet'))
db.select('scenario','label','reps','reject','reject_mcse','bias_reml','coverage95','sd_delta_reml','mean_se_boot')""")
md("### DB: why the man / underneath-zone player correlation changed sign (outcome-only, real data)")
code("""pl.Config.set_fmt_str_lengths(70)
pl.read_parquet(OUT / 'db_corr_decomposition.parquet').filter(pl.col('data').str.starts_with('registered'))""")
md("## 2. H2: incremental value of tracked peak speed beyond the official 40")
code("""h2 = pl.read_parquet(OUT / 'h2.parquet'); S2 = summarise_h2(h2)
S2.select('scenario','label','reps','true_partial','reject','reject_mcse','reject_holm','reject_wald_reml','full_support','mean_partial_hat','bias_partial','sd_partial_hat',
          'agree_sign_reml_2s','mean_dr2_cv','p_dr2_ge_002','p_lb90_pos','p_eiv_pos','mean_dRMSE_sf')""")
code("""fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
m = S2.filter(pl.col('scenario') <= 5).sort('true_partial')
ax[0].errorbar(m['true_partial'], m['reject'], yerr=1.96*m['reject_mcse'], marker='o', color=style.SERIES[0], label='β_P test (fixed-sequence level)')
ax[0].plot(m['true_partial'], m['full_support'], marker='s', color=style.SERIES[2], label='all registered H2 criteria')
ax[0].plot(m['true_partial'], m['p_predictive_ok'], marker='^', color=style.SERIES[1], label='predictive criterion only')
ax[0].axhline(0.025, color=style.MUTED, ls=':', lw=1); ax[0].set_xlabel('true partial correlation (peak | 40)'); ax[0].set_ylabel('probability'); ax[0].legend(); ax[0].set_title('H2 at n = 57 WRs')
for k, s in enumerate([1, 4, 5]):
    g = h2.filter(pl.col('scenario') == s)
    ax[1].hist(g['dr2_cv'], bins=40, alpha=0.5, color=style.SERIES[k], label=f'partial {g["true_partial"][0]}')
ax[1].axvline(0.02, color=style.MUTED, ls='--'); ax[1].set_xlabel('ΔR²_CV (held-out players)'); ax[1].legend(); ax[1].set_title('Incremental predictive value')
fig.tight_layout(); fig.savefig(FIG / 'p4_h2.png', dpi=150); plt.show()""")
code("""S2.select('scenario','label','mean_dr2_player_cv_same_reps','mean_dr2_playsplit')""")
md("## 3. Sequential testing exactly as registered, and Holm separately")
code("""fam = pl.read_parquet(OUT / 'family.parquet')
fam.group_by('combo', maintain_order=True).agg(pl.len().alias('reps'), pl.col('fs_h1').mean(), pl.col('fs_h2').mean(), pl.col('fs_h2_supported').mean(),
    pl.col('any_fs').mean().alias('P(any fixed-seq rejection)'), pl.col('holm_h1').mean(), pl.col('holm_db').mean(), pl.col('holm_h2').mean(), pl.col('any_holm').mean().alias('P(any Holm rejection)'))""")
md("## 4. Selection: the eligibility threshold")
code("""sel = pl.read_parquet(OUT / 'selection.parquet')
SS = summarise_h1(sel)
SS.select('mech','mechanism','rule','reps','n_players','true_delta_obs','reject','reject_mcse','mean_delta_reml','bias_reml','bias_reml_mcse','coverage95').sort('mech','rule')""")
code("""fig, ax = plt.subplots(figsize=(10, 3.6))
rules = list(ps.SEL_RULES)
for k, mid in enumerate([1, 2, 3, 4, 5, 6]):
    g = SS.filter(pl.col('mech') == mid)
    vals = [g.filter(pl.col('rule') == r)['bias_reml'][0] for r in rules]
    errs = [1.96 * g.filter(pl.col('rule') == r)['bias_reml_mcse'][0] for r in rules]
    ax.errorbar(np.arange(4) + (k - 2.5) * 0.1, vals, yerr=errs, fmt='o', color=style.SERIES[k], label=g['mechanism'][0])
ax.axhline(0, color=style.MUTED, lw=1); ax.set_xticks(range(4), [r.split(':')[0] for r in rules], fontsize=8); ax.set_ylabel('bias of REML Δ̂')
ax.legend(fontsize=7, ncol=2); ax.set_title('Selection: bias of H1-WR under eligibility rules')
fig.tight_layout(); fig.savefig(FIG / 'p4_selection.png', dpi=150); plt.show()""")
code("""pl.read_parquet(OUT / 'selection_real.parquet')""")
md("## 5. Demand definition (real game speeds only; no combine data)")
code("""cells = pl.read_parquet(OUT / 'demand_cells.parquet')
cells.filter(pl.col('min_plays') == 1).pivot(index=['pos','ctx'], on='def', values='D').sort('pos','ctx')""")
code("""pl.read_parquet(OUT / 'demand_threshold_agreement.parquet').sort('pos','ctx')""")
code("""rel = pl.read_parquet(OUT / 'demand_reliability.parquet')
rel.pivot(index=['pos','ctx','n'], on='threshold', values='spearman_brown').sort('pos','ctx')""")
code("""xf = pl.read_parquet(OUT / 'demand_crossfit.parquet')
reg = xf.filter(pl.col('split') == -1)
inst = xf.filter(pl.col('split') >= 0).group_by('pos','ctx').agg(pl.col('D_full').first(), pl.col('D_half').mean().alias('mean_half'),
        pl.col('D_half').std().alias('sd_half'), (pl.col('D_half') - pl.col('D_full')).mean().alias('bias_half'),
        pl.col('D_half').quantile(0.05).alias('q05'), pl.col('D_half').quantile(0.95).alias('q95')).sort('pos','ctx')
display(reg.sort('pos','ctx','half')); inst""")
code("""oos = pl.read_parquet(OUT / 'demand_oos_T.parquet')
oos.group_by('pos','ctx','T_source').agg(pl.col('D').mean()).pivot(index=['pos','ctx'], on='T_source', values='D').sort('pos','ctx')""")
code("""fig, ax = plt.subplots(figsize=(10, 3.6))
cc = cells.filter(pl.col('min_plays') == 1).sort('pos','ctx')
keys = cc.select('pos','ctx').unique(maintain_order=True)
for k, d in enumerate(['share_85','share_90','share_95']):
    v = [cc.filter((pl.col('pos')==p)&(pl.col('ctx')==c)&(pl.col('def')==d))['D'][0] for p, c in keys.iter_rows()]
    ax.bar(np.arange(keys.height) + (k-1)*0.27, v, width=0.27, color=style.SEQ_BLUE[2+2*k], label=d.replace('share_','≥ ')+'% of own top-5')
ax.set_xticks(range(keys.height), [f'{p}\\n{c}' for p, c in keys.iter_rows()], fontsize=7); ax.set_ylabel('D (median share of plays)'); ax.legend()
ax.set_title('Near-top-speed demand by position-context and threshold (registered: 90%)')
fig.tight_layout(); fig.savefig(FIG / 'p4_demand_thresholds.png', dpi=150); plt.show()""")
code("""ds = pl.read_parquet(OUT / 'demand_sim.parquet')
ds.group_by('lam','crossfit').agg(pl.len().alias('reps'), pl.col('lam_hat').mean(), pl.col('lam_hat').std().alias('sd'), pl.col('reject').mean()).sort('lam','crossfit')""")
md("""## 6. Conclusions

See `research_notes/synthetic_validation.md`, `demand_measure_validation.md` and `selection_bias_analysis.md`. Those notes take their numbers from the tables above.""")
nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, ROOT / "notebooks/07_synthetic_pipeline_validation.ipynb")
print("written")
