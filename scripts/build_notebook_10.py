"""Build notebooks/10_secondary_analysis.ipynb from the single secondary run (no model refitted)."""
import nbformat as nbf
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
nb = nbf.v4.new_notebook(); C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s))  # noqa: E731
code = lambda s: C.append(nbf.v4.new_code_cell(s))  # noqa: E731

md("""# 10 · Registered secondary analyses: DB, DL, OL (H5), Holm family, demand meta-regression

**Hierarchy (D4):**
- **Primary:** H1-WR, frozen and inconclusive.
- **Secondary, estimation:** H2, done.
- **This notebook:**
  - the **secondary Holm family** {H1-DB, H1-DL(a), H1-DL(b), H5(b)};
  - **estimation-only** H5(a), which is also the registered OL negative control N2;
  - H5(c) and H1-global;
  - **descriptive** H1-TE, used as a meta-regression input;
  - **exploratory** DL role subgroups.

It displays `scripts/run_secondary.py` (one run). No TE analysis beyond the registered descriptive estimates.""")
code("""import json, sys
from pathlib import Path
import numpy as np, polars as pl, matplotlib.pyplot as plt
ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT / 'src'))
from nfl_bdb.visualization import style
style.apply(); pl.Config.set_tbl_rows(40); pl.Config.set_tbl_cols(20); pl.Config.set_fmt_str_lengths(60); pl.Config.set_tbl_width_chars(200)
RUN = (ROOT / 'experiments/secondary/LATEST').read_text().strip(); OUT = ROOT / 'experiments/secondary' / RUN
R = json.load(open(OUT / 'secondary_result.json')); BS = np.load(OUT / 'bootstraps.npz')
print('run', RUN, '| code commit', R['code_commit'], '| join', R['join_run'], '| frozen primary', R['primary_run'], '| B', R['B'], '| seeds', R['seeds'])""")
md("## 1. Secondary Holm family (α = 0.05, m = 4; full REML player-cluster bootstrap, B = 2,000)")
code("""fam = R['family']
F = pl.DataFrame([dict(hypothesis=k, estimate=v['estimate'], ci95_lo=v['ci95'][0], ci95_hi=v['ci95'][1], ci90_hi=v['ci90'][1],
                       holm_step=v['holm_step'], holm_alpha=v['holm_alpha'], ci_holm_lo=v['ci_holm_level'][0], ci_holm_hi=v['ci_holm_level'][1],
                       p_unadjusted=v['p_unadjusted'], p_holm=v['p_holm'], decision=v['decision']) for k, v in fam.items()])
F""")
code("""fig, ax = plt.subplots(figsize=(8, 3.4))
for k, row in enumerate(F.iter_rows(named=True)):
    ax.plot([row['ci_holm_lo'], row['ci_holm_hi']], [k, k], color=style.SERIES[0], lw=2, alpha=0.4)
    ax.plot([row['ci95_lo'], row['ci95_hi']], [k, k], color=style.SERIES[0], lw=5)
    ax.plot(row['estimate'], k, 'o', color='k')
ax.axvline(0, color=style.MUTED); ax.set_yticks(range(F.height), F['hypothesis'])
ax.set_xlabel('estimate (95% CI thick; Holm-level CI thin)'); ax.set_title('Secondary Holm family')
fig.tight_layout(); fig.savefig(ROOT / 'reports/figures/secondary_family.png', dpi=150); plt.show()
print('§9 sensitivity Holm over {H1-WR, H1-DB, H2}:', R['holm_sensitivity_primary_family'])""")
md("## 2. Per-position fits (registered bivariate model; bootstrap test and delta-method Wald check)")
code("""rows = []
for p, t in R['tests'].items():
    w = R['wald'][f'{p}_full']; cov = np.array(w['cov']); se_d = float(np.sqrt(cov[0, 0] + cov[1, 1] - 2 * cov[0, 1]))
    rows.append(dict(position=p, contexts=' vs '.join(t['plays_by_ctx']), players=t['players'], plays=t['plays'], team_seasons=t['team_seasons'],
                     rho_h=t['rho'][0], rho_l=t['rho'][1], delta=t['delta'], boot_ci95=str([round(v, 3) for v in t['ci95']]), boot_se=t['se_boot'],
                     wald_se=se_d, p=t['p'], raw_slope_h=t['beta'][0] * 0.25 / t['x_sd'], raw_slope_l=t['beta'][1] * 0.25 / t['x_sd'], converged=t['converged']))
display(pl.DataFrame(rows))
pl.DataFrame([dict(fit=k, contexts=str(v.get('contexts')), rho=str(np.round(v['rho'], 3).tolist()) if 'rho' in v else v.get('error'),
                   se=str(np.round(v['se'], 3).tolist()) if 'se' in v else '', players=v['players'], plays=v['plays']) for k, v in R['wald'].items()])""")
md("## 3. H1-DL(b): role sorting (registered) and exploratory role subgroups")
code("""b = R['dl_b']
print('pooled rho (mean of contexts): registered model %.3f -> + alignment x context + combine weight x context %.3f' % (b['base_pooled'], b['adjusted_pooled']))
print('per context: base', np.round(b['base_rho'], 3), '| adjusted', np.round(b['adjusted_rho'], 3), '| roles', b['roles'], '| bootstrap draws', b['boot_ok'])
dlb = BS['DLb']
fig, ax = plt.subplots(figsize=(7, 3.2))
ax.hist(dlb[:, 4], bins=50, alpha=0.6, color=style.SERIES[0], label='pooled ρ, registered model'); ax.hist(dlb[:, 5], bins=50, alpha=0.6, color=style.SERIES[1], label='pooled ρ, + role & weight')
ax.legend(); ax.set_xlabel('bootstrap pooled ρ (DL)'); ax.set_title('H1-DL(b): role/body-type sorting'); fig.tight_layout(); plt.show()
for k in ('DL_EDGE_only', 'DL_INTERIOR_LINE_only'):
    v = R['wald'][k]; print('EXPLORATORY', k, 'rho', np.round(v['rho'], 3), 'Wald SE', np.round(v['se'], 3), 'players', v['players'])""")
md("## 4. Offensive linemen: H5(a) = negative control N2, H5(b), H5(c)")
code("""print('H5(a) Δ_OL:', {k: (np.round(v, 3).tolist() if isinstance(v, list) else v) for k, v in R['h5a'].items()})
print('H5(b) Δ_WR − Δ_OL:', {k: fam['H5(b)'][k] for k in ('estimate', 'ci95', 'ci90', 'p_unadjusted', 'p_holm', 'decision')})
H = R['h5c']
display(pl.DataFrame([dict(swap=k, predicted=v['pred'], pi90_lo=v['pi90'][0], pi90_hi=v['pi90'][1], observed_pooled_OL=v['observed'], departure=v['departure'],
                           se_obs=v['se_obs'], se_fit=v['se_fit'], omega2=v['omega2'], lambda_noOL=v['lam_noOL'], D_OL=v['D_OL']) for k, v in H.items()]))
print('H5(c) reading:', H['averaged']['reading'], '| PI width', round(H['averaged']['pi_width'], 3))""")
md("## 5. H1-global: cross-fitted demand meta-regression (estimation only) and TE (descriptive)")
code("""G = R['h1_global']
for s in ('D_A_rho_B', 'D_B_rho_A'):
    print(s, 'λ = %.3f (SE %.3f), ω² = %.4f, cell-bootstrap 95%% CI %s' % (G[s]['lam'], G[s]['lam_se'], G[s]['omega2'], np.round(G[s]['lam_boot_ci95'], 2).tolist()))
print('averaged λ:', G['averaged'])
cells = pl.DataFrame(G['D_A_rho_B']['cells']).with_columns(pl.lit('D:A / ρ:B').alias('swap'))
cells = pl.concat([cells, pl.DataFrame(G['D_B_rho_A']['cells']).with_columns(pl.lit('D:B / ρ:A').alias('swap'))])
display(cells)
fig, ax = plt.subplots(figsize=(7, 3.8))
for k, (s, g) in enumerate(cells.group_by('swap', maintain_order=True)):
    ax.errorbar(g['D'], g['rho'], yerr=1.96 * g['se'], fmt='o', color=style.SERIES[k], alpha=0.7, label=s[0])
ax.set_xlabel('cross-fitted near-top-speed demand D'); ax.set_ylabel('ρ (half-sample, ±1.96 SE)'); ax.legend(); ax.set_title('H1-global (descriptive): 11 cells')
fig.tight_layout(); fig.savefig(ROOT / 'reports/figures/h1_global.png', dpi=150); plt.show()
w = R['wald']['TE_full']; cov = np.array(w['cov'])
print('H1-TE (DESCRIPTIVE ONLY, n = %d): ρ_deep %.3f (SE %.3f), ρ_short %.3f (SE %.3f), Δ %.3f (Wald SE %.3f)' %
      (w['players'], w['rho'][0], w['se'][0], w['rho'][1], w['se'][1], w['rho'][0] - w['rho'][1], np.sqrt(cov[0, 0] + cov[1, 1] - 2 * cov[0, 1])))""")
md("See `research_notes/secondary_family_results.md`, `db_secondary_results.md`, `dl_secondary_results.md` and `ol_secondary_results.md`.")
nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
nbf.write(nb, ROOT / "notebooks/10_secondary_analysis.ipynb")
print("written")
