"""Build notebooks/12_turn_recovery_feasibility.ipynb (Phase 11, measurement feasibility only).

The committed notebook has its outputs stripped: trajectory panels and player-level scatter plots show
individual athletes' combine data. Execute a copy into the git-ignored build/ directory:

    python scripts/run_turn_recovery_feasibility.py           # once; writes experiments/phase11_turn_recovery/LATEST
    python scripts/build_notebook_12.py --execute             # writes build/notebooks/12_...executed.ipynb

Only the two aggregate figures (reliability forest plot and sensitivity panel; no athlete-level points)
are written to reports/figures/phase11_*.png.
"""
import subprocess
import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
nb = nbf.v4.new_notebook(); C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s))  # noqa: E731
code = lambda s: C.append(nbf.v4.new_code_cell(s))  # noqa: E731

md("""# 12 · Phase 11, Stage 1: three-cone turn retention and recovery: measurement feasibility

**Scope.** This notebook uses only NFL Combine data. No NFL game outcome is read, joined or modelled, and no registered analysis is touched.

**Question.** Can speed retention during a change of direction, and speed recovery after it, be measured *reliably* from 10 Hz Combine three-cone tracking?

**How to reproduce:**
1. Run `python scripts/run_turn_recovery_feasibility.py`.
2. Run `python scripts/build_notebook_12.py --execute`.

**Why the committed copy has no outputs:** its plots show individual athletes' trajectories. The executed copy lives in the git-ignored `build/`.

Report: `research_notes/phase11_turn_recovery_feasibility.md`.""")
code("""import json, sys
from pathlib import Path
import numpy as np, polars as pl, matplotlib.pyplot as plt
ROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()
sys.path.insert(0, str(ROOT / 'src'))
from nfl_bdb.features.turn_recovery import TurnParams, detect_turns, with_
pl.Config.set_tbl_rows(60); pl.Config.set_tbl_cols(30); pl.Config.set_tbl_width_chars(220); pl.Config.set_float_precision(3)
RUN = (ROOT / 'experiments/phase11_turn_recovery/LATEST').read_text().strip()
EXP = ROOT / 'experiments/phase11_turn_recovery' / RUN
DAT = ROOT / 'data/interim/phase11_turn_recovery' / RUN
FIG = ROOT / 'reports/figures'
S = json.load(open(EXP / 'summary.json')); CFG = json.load(open(EXP / 'config.json'))
print('run', RUN); print(json.dumps(CFG['reference'], indent=1))""")

md("## A. Data audit (recomputed from the raw three-cone tracking)")
code("print(json.dumps(S['audit'], indent=1))")

md("""## B. Turn detection on representative attempts

**Detection steps:**
- Smooth positions with Savitzky–Golay (window 7, order 2).
- A frame is *turning* if |heading rate| ≥ 60°/s, or if speed < 1 yd/s (heading is undefined near a stop).
- Merge runs separated by ≤ 2 frames.
- Keep a run as a turn only if the entry→exit chord heading change is ≥ 45°.
- Label turns against the template R1, R2 (touch reversals), [B1], C (loop around the far cone), [B2].

The panels below show the path coloured by speed and the speed trace with detected turns shaded. The attempts are chosen by rule, not by hand: the attempts closest to the median C retention and at its 10th and 90th percentiles, plus one non-template attempt.""")
code("""ct = (pl.read_parquet(ROOT / 'data/interim/combine_tracking.parquet')
      .filter((pl.col('drill_type') == 'THREE_CONE_DRILL') & (pl.col('entity_type') == 'PLAYER')).sort('event_id', 'time'))
T = pl.read_parquet(DAT / 'turns.parquet'); A = pl.read_parquet(DAT / 'attempts.parquet')
Tref = T.filter((pl.col('config') == 'reference') & pl.col('template_ok'))
Cr = Tref.filter(pl.col('label') == 'C').sort('retention')
picks = [Cr.row(int(q * (Cr.height - 1)), named=True)['event_id'] for q in (0.1, 0.5, 0.9)]
nt = A.filter((pl.col('config') == 'reference') & pl.col('ok') & ~pl.col('template_ok'))['event_id'].to_list()
picks += nt[:1]
COL = dict(R1='tab:red', R2='tab:orange', B1='tab:olive', C='tab:blue', B2='tab:purple')

def show(eid, ax_xy, ax_v, p=TurnParams()):
    g = ct.filter(pl.col('event_id') == eid)
    r = detect_turns(g['x'].to_numpy(), g['y'].to_numpy(), g['s'].to_numpy(), p)
    k = r['kin']; t = np.arange(len(g)) / p.fs
    sc = ax_xy.scatter(g['x'], g['y'], c=k['speed'], s=8, cmap='viridis', vmin=0, vmax=7)
    ax_xy.set_aspect('equal'); ax_xy.set_title(f"template={r['template_ok']}", fontsize=9)
    ax_v.plot(t, k['speed'], 'k-', lw=1, label='speed (SG of x,y)'); ax_v.plot(t, g['s'], ':', c='gray', lw=1, label='provided s')
    for tr in r['turns']:
        c = COL.get(tr['label'], 'gray')
        ax_v.axvspan(tr['start'] / p.fs, tr['end'] / p.fs, color=c, alpha=0.2)
        ax_v.plot(tr['i_min'] / p.fs, tr['v_min'], 'v', c=c); ax_v.plot(tr['i_entry'] / p.fs, tr['v_entry'], '^', c=c)
        ax_v.text(tr['i_min'] / p.fs, tr['v_min'] - 0.5, f"{tr['label'] or '?'} {tr['chord_deg']:.0f}°", fontsize=7, ha='center', color=c)
        if not tr['recovery_censored'] and tr['recovery_time'] > 0:
            ax_v.plot([tr['i_min'] / p.fs, tr['i_min'] / p.fs + tr['recovery_time']], [p.recovery_frac * tr['v_entry']] * 2, c=c, lw=2)
    ax_v.set_xlabel('s'); ax_v.set_ylabel('yd/s'); ax_v.set_ylim(-1, 8)
    return sc

fig, ax = plt.subplots(len(picks), 2, figsize=(12, 3.2 * len(picks)), gridspec_kw=dict(width_ratios=[1, 2.2]))
for i, e in enumerate(picks):
    show(e, ax[i, 0], ax[i, 1])
ax[0, 1].legend(fontsize=8, loc='upper right'); fig.tight_layout(); plt.show()""")
md("""**How to read the speed panels:**
- **▲** marks entry speed; **▼** marks minimum speed.
- The horizontal bar runs from the minimum to the first crossing of 90% of entry speed (the recovery time).
- Shading shows the turning segment.

**What the panels show:**
- R1 and R2 are touch-and-return reversals: speed falls to about 0.3 yd/s.
- C is a loop, and the only turn that retains a non-trivial fraction of speed.
- B1 and B2 are gentle curves with no speed loss.

## Turn-level descriptives (reference configuration, template attempts)""")
code("pl.read_parquet(EXP / 'turn_descriptives.parquet')")

md("""## D. Test–retest reliability

**Method:**
- Pairs are each athlete's first two template-valid attempts, in chronological order.
- ICC(3,1) is consistency; ICC(2,1) is absolute agreement.
- TE is the typical error, SD(diff)/√2.
- Within-position values use attempts centred on the position mean.
- CIs come from a player bootstrap (B = 2000, seed 1111).

**Censoring:** censored recoveries are treated as missing. R1 recovery is censored in 90% of attempts.""")
code("""R = pl.read_parquet(EXP / 'reliability.parquet')
Rr = R.filter(pl.col('config') == 'reference')
Rr.select('feature', 'n_pairs', 'icc31', 'icc31_lo', 'icc31_hi', 'icc21', 'spearman', 'spearman_lo', 'spearman_hi', 'te', 'te_pct',
          'mean_diff', 'icc31_within_pos', 'icc31_within_pos_lo', 'icc31_within_pos_hi', 'icc1_all')""")
code("""d = Rr.filter(pl.col('n_pairs') >= 8).sort('icc31')
fig, ax = plt.subplots(figsize=(7, 4.5)); yy = np.arange(d.height)
ax.errorbar(d['icc31'], yy + 0.12, xerr=[d['icc31'] - d['icc31_lo'], d['icc31_hi'] - d['icc31']], fmt='o', c='k', label='ICC(3,1) pooled')
ax.errorbar(d['icc31_within_pos'], yy - 0.12, xerr=[d['icc31_within_pos'] - d['icc31_within_pos_lo'], d['icc31_within_pos_hi'] - d['icc31_within_pos']],
            fmt='s', c='tab:blue', mfc='white', label='within position')
ax.set_yticks(yy); ax.set_yticklabels(d['feature']); ax.axvline(0.75, ls='--', c='gray', lw=0.8); ax.axvline(0, c='gray', lw=0.5)
ax.set_xlabel(f"single-attempt test-retest ICC(3,1), 95% player bootstrap\\n(n = {int(d['n_pairs'].max())} athletes with 2 valid attempts; dashed line = 0.75)")
ax.legend(fontsize=8, loc='lower right'); ax.set_xlim(-0.3, 1); fig.tight_layout()
fig.savefig(FIG / 'phase11_turn_reliability.png', dpi=150); plt.show()""")

md("""## Sensitivity to processing choices

Each change is made one at a time from the reference. The tables report:
- template-match rate;
- ICC(3,1);
- Spearman rank agreement of player means with the reference configuration.

No setting was chosen by its correlation with any outcome.""")
code("""P = ['C_retention', 'C_recovery_time', 'C_reacc', 'R2_recovery_time', 'R2_reacc']
print(R.filter(pl.col('feature').is_in(P)).pivot(index='config', on='feature', values='icc31'))
SENS = pl.read_parquet(EXP / 'sensitivity.parquet'); SENS""")
code("""cfgs = SENS['config'].to_list()
fig, ax = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
icc = R.filter(pl.col('feature').is_in(P)).pivot(index='config', on='feature', values='icc31')
icc = icc.join(pl.DataFrame({'config': cfgs, '_o': range(len(cfgs))}), on='config').sort('_o')
rk = SENS.select('config', *[f'rank_vs_ref_{f}' for f in P])
for j, f in enumerate(P):
    ax[0].plot(icc[f], range(len(cfgs)), 'o-', lw=0.6, ms=4, label=f)
    ax[1].plot(rk[f'rank_vs_ref_{f}'], range(len(cfgs)), 'o-', lw=0.6, ms=4, label=f)
ax[0].set_yticks(range(len(cfgs))); ax[0].set_yticklabels(cfgs, fontsize=8); ax[0].invert_yaxis()
ax[0].set_xlabel('ICC(3,1)'); ax[1].set_xlabel('rank agreement of player means with reference (Spearman)')
ax[0].legend(fontsize=7); fig.tight_layout(); fig.savefig(FIG / 'phase11_turn_sensitivity.png', dpi=150); plt.show()""")

md("## C. Player-level aggregation: mean vs median vs first vs best attempt (athletes with ≥ 2 valid attempts)")
code("pl.read_parquet(EXP / 'aggregation_agreement.parquet')")

md("""## Retention and re-acceleration trade-off

At C, an athlete who keeps more speed through the loop (higher retention) re-accelerates less afterwards. The question is whether this is a trait or a choice of turn shape made on each attempt. The test below takes within-athlete differences between the two attempts.""")
code("""from scipy.stats import spearmanr
c = Tref.filter(pl.col('label') == 'C').sort('nfl_id', 'order')
print('attempt level   rho(retention, reacc) =', round(spearmanr(c['retention'], c['reacc']).statistic, 2), ' n =', c.height)
g = c.group_by('nfl_id', maintain_order=True).head(2).group_by('nfl_id').agg('retention', 'reacc', 'duration').filter(pl.col('retention').list.len() == 2)
dr = np.array([b - a for a, b in g['retention'].to_list()]); da = np.array([b - a for a, b in g['reacc'].to_list()])
print('within athlete  rho(d retention, d reacc) =', round(spearmanr(dr, da).statistic, 2), ' n =', len(dr))
fig, ax = plt.subplots(1, 2, figsize=(10, 4))
ax[0].scatter(c['retention'], c['reacc'], s=10, alpha=0.6); ax[0].set_xlabel('C retention'); ax[0].set_ylabel('C re-acceleration (yd/s²)')
ax[1].scatter(dr, da, s=14); ax[1].axhline(0, c='gray', lw=0.5); ax[1].axvline(0, c='gray', lw=0.5)
ax[1].set_xlabel('Δ retention (attempt 2 − 1)'); ax[1].set_ylabel('Δ re-acceleration'); fig.tight_layout(); plt.show()""")

md("""## E. Comparison with conventional combine measures (descriptive)

**Method:**
- Spearman correlations of player means, with player-bootstrap CIs.
- A within-position version: ranks centred within position.
- Adjusted R² of each feature on position plus the official forty, the official three-cone and the tracked peak speed.

**Interpretation:** these are associations between measurements, not causal statements.""")
code("""COMP = pl.read_parquet(EXP / 'conventional_comparison.parquet')
print(COMP.pivot(index='feature', on='measure', values='spearman'))
print(COMP.pivot(index='feature', on='measure', values='spearman_within_pos'))
R2 = pl.read_parquet(EXP / 'conventional_r2.parquet'); R2.pivot(index='feature', on='model', values='adj_r2')""")
code("pl.read_parquet(EXP / 'feature_intercorrelation.parquet').sort('spearman')")

nb["cells"] = C
nb["metadata"]["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
out = ROOT / "notebooks" / "12_turn_recovery_feasibility.ipynb"
nbf.write(nb, out)
print("wrote", out)
if "--execute" in sys.argv:
    dst = ROOT / "build" / "notebooks"; dst.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, "-m", "jupyter", "nbconvert", "--to", "notebook", "--execute", str(out),
                    "--output-dir", str(dst), "--output", "12_turn_recovery_feasibility.executed.ipynb",
                    "--ExecutePreprocessor.timeout=900"], check=True, cwd=ROOT / "notebooks")
    print("executed ->", dst)
