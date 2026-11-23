"""Build notebooks/11_final_submission.ipynb, the public Kaggle notebook for the Big Data Bowl 2027 entry.

The notebook:
  * reads the official competition files (Kaggle: /kaggle/input/nfl-big-data-bowl-2027);
  * re-runs data validation, the frozen Combine feature definitions and the registered eligibility / sample-size
    construction (counts only; combine values are never attached to game outcomes in the notebook);
  * embeds the registered results (paper/registered_results.json) with run ids, commits and seeds, and draws
    every writeup figure from them;
  * never re-runs a confirmatory model (the registered runners are one-shot) and never reads credentials.

Usage: python scripts/build_notebook_11.py
"""
from __future__ import annotations

import json
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
REG = json.loads((ROOT / "paper" / "registered_results.json").read_text())
nb = nbf.v4.new_notebook(); C = []
md = lambda s: C.append(nbf.v4.new_markdown_cell(s.strip()))  # noqa: E731
code = lambda s: C.append(nbf.v4.new_code_cell(s.strip()))  # noqa: E731

md("""
# From Combine Speed to NFL Movement: What Tracking Reveals About Receiver Separation
### NFL Big Data Bowl 2027: public reproducibility notebook

This notebook accompanies the writeup. It does four things:

1. **Validates the competition data** (files, keys, season types, registered exclusions).
2. **Re-runs the frozen feature definitions:**
   - Combine tracked 40 peak speed;
   - game play-maximum speed;
   - task contexts;
   - the registered eligibility rules.
   It checks that it reproduces the registered sample sizes exactly.
3. **Explains the registered models** and **shows the registered results** with their run IDs, code commits and seeds.
4. **Draws every figure in the writeup** from those registered results.

**What this notebook deliberately does *not* do:**
- It does not re-fit any confirmatory model. The registered analysis runners (H1-WR, H2, secondary family) are one-shot by design: each refuses a second run, so that results cannot be re-drawn until they look better. Their outputs are embedded below, read-only.
- Combine values are never joined to game outcomes in this notebook. The sample-size reconstruction uses only *whether* a player has a valid tracked 40.
- No new association, subgroup or model is computed.
- No credentials are read, and no competition data is written anywhere except the notebook's temporary work directory.

| layer | variable used |
|---|---|
| **Capacity** (Combine) | tracked 40 peak speed, yd/s |
| **Game movement** | max speed on each REG play (WR/TE: before the throw), yd/s |
| **Football performance** | separation at the throw (yd), WR deep routes |
| **Deployment** | route, coverage, alignment, body weight |
""")

md("## 0. Setup: locate the competition data, the pipeline code and a scratch work directory")
code(r"""
import json, os, sys, time, tempfile, platform
from pathlib import Path
import numpy as np, polars as pl
import matplotlib, matplotlib.pyplot as plt
pl.Config.set_tbl_rows(30); pl.Config.set_tbl_cols(20); pl.Config.set_tbl_width_chars(180)

# Kaggle mounts attached datasets under /kaggle/input/<slug>/ and writes to /kaggle/working.
# The two roots can be overridden only to simulate that layout locally.
KAGGLE_INPUT = Path(os.environ.get('KAGGLE_INPUT_ROOT', '/kaggle/input'))
KAGGLE_WORKING = Path(os.environ.get('KAGGLE_WORKING_ROOT', '/kaggle/working'))
IS_KAGGLE = KAGGLE_INPUT.exists()

def find_data_dir():
    cands = [os.environ.get('NFL_BDB_DATA'), str(KAGGLE_INPUT / 'nfl-big-data-bowl-2027'),
             str(KAGGLE_INPUT / 'competitions/nfl-big-data-bowl-2027')]
    if IS_KAGGLE:   # mounts may be /kaggle/input/<slug>/, .../competitions/<slug>/ or deeper: search up to 4 levels
        cands += [str(p.parent) for d in range(1, 5) for p in sorted(KAGGLE_INPUT.glob('*/' * d + 'combine_results.csv'))]
    here = Path.cwd()
    cands += [str(p / 'data/raw/nfl-big-data-bowl-2027') for p in (here, here.parent)]
    for c in cands:
        if c and (Path(c) / 'combine_results.csv').exists():
            return Path(c)
    raise FileNotFoundError('competition CSVs not found: attach the nfl-big-data-bowl-2027 competition data')

def find_code_dir():
    cands = [os.environ.get('NFL_BDB_CODE')]
    if IS_KAGGLE:   # the pipeline code is attached as a small Kaggle dataset (src/ + scripts/; no data)
        # <root>/src/nfl_bdb/__init__.py -> parents[0]=nfl_bdb, [1]=src, [2]=<root> (the dataset root we need)
        # searched up to 4 levels deep (e.g. /kaggle/input/datasets/<owner>/<slug>/src/...); the root must also hold the manifest
        hits = [p.parents[2] for d in range(1, 5) for p in sorted(KAGGLE_INPUT.glob('*/' * d + 'src/nfl_bdb/__init__.py'))]
        cands += [str(h) for h in hits if (h / 'research_notes/code_freeze.json').exists()] + [str(h) for h in hits]
    here = Path.cwd()
    cands += [str(here), str(here.parent)]
    for c in cands:
        if c and (Path(c) / 'src/nfl_bdb/__init__.py').exists():
            root = Path(c)
            assert (root / 'src/nfl_bdb/__init__.py').exists() and root.name != 'src', f'bad code root {root}'
            return root
    raise FileNotFoundError('pipeline code not found: attach the nfl-bdb-2027 pipeline-code dataset')

DATA = find_data_dir(); CODE = find_code_dir()
# Scratch files (Parquet copies of the competition CSVs, play features) go to a temporary directory under /tmp.
# Never /kaggle/working: Kaggle saves that folder as notebook output, which would expose competition data copies.
WORK = Path(os.environ.get('NFL_BDB_WORK') or tempfile.mkdtemp(prefix='nfl_bdb_work_'))
WORK.mkdir(parents=True, exist_ok=True)
# safety: never write into the repository's registered data directory
assert 'data/interim' not in str(WORK.resolve()), 'work directory must not be the registered data/interim'
assert not str(WORK.resolve()).startswith(str(KAGGLE_WORKING.resolve())), 'work directory must not be inside /kaggle/working (saved as output)'
sys.path[:0] = [str(CODE / 'src'), str(CODE / 'scripts')]
_v = tuple(int(x) for x in pl.__version__.split('.')[:2])
assert _v >= (1, 0), f'polars >= 1.0 required (found {pl.__version__}); run: pip install -U polars'
print('Kaggle:', IS_KAGGLE, '| python', platform.python_version(), '| polars', pl.__version__, '| matplotlib', matplotlib.__version__)
print('data :', DATA); print('code :', CODE); print('work :', WORK)

# Run switches. Combine features take a few minutes; the game pipeline reads ~2 GB of tracking (~10-20 min).
RUN_COMBINE_FEATURES = True
RUN_GAME_PIPELINE = os.environ.get('NFL_BDB_SKIP_GAME', '0') != '1'
""")

code(r"""
# Point the frozen I/O module at the competition files and the scratch work directory BEFORE importing anything
# that caches paths. The frozen code itself is not modified (its hashes are checked in section 2).
from nfl_bdb.data import io as nio
nio.RAW, nio.INTERIM = DATA, WORK
from nfl_bdb.data import play_table as pt
pt.FEATURES = WORK / 'phase3_play_features.parquet'
from nfl_bdb.data import confirmatory_data as cd
import run_phase3_screening as p3
p3.INTERIM, p3.FEAT, p3.MATCH = WORK, WORK / 'phase3_play_features.parquet', WORK / 'phase3_matchups.parquet'
from run_real_capacity import forty_fits
from nfl_bdb.visualization import submission_figures as sf
assert nio.raw_path('players') == DATA / 'players.csv' and pt.FEATURES.parent == WORK
print('frozen pipeline imported; reading from', nio.RAW, 'writing to', nio.INTERIM)
""")

md("""
## 1. Registered results (read-only, embedded)

These numbers were produced once by the registered runners. They are embedded verbatim from `paper/registered_results.json`, which was built from the run outputs by `scripts/build_registered_results.py`. Each block names its source run file.
""")
code("REGISTERED = json.loads(r'''" + json.dumps(REG, indent=1) + "''')\n"
     "print('blocks:', [k for k in REGISTERED if not k.startswith('_')])\n"
     "print(json.dumps(REGISTERED['_sources'], indent=1))")

md("""
## 2. Code integrity: the frozen pipeline files are unchanged

The confirmatory code was frozen (sha256 manifest `research_notes/code_freeze.json`, 12 files) before the single Combine-to-game join. The code bundle ships the manifest and all 12 files. Every file must be present and match its registered SHA-256; anything missing or changed stops the notebook.
""")
code(r"""
import hashlib
man = CODE / 'research_notes/code_freeze.json'
assert man.exists(), f'freeze manifest missing: {man}'
m = json.loads(man.read_text())['files']
assert len(m) == 12, f'expected 12 frozen files in the manifest, found {len(m)}'
missing = [f for f in m if not (CODE / f).is_file()]
assert not missing, f'frozen files missing from the code bundle: {missing}'
status = {f: hashlib.sha256((CODE / f).read_bytes()).hexdigest() == h for f, h in m.items()}
print(pl.DataFrame({'file': list(status), 'sha256_matches_freeze': list(status.values())}))
assert all(status.values()), f'frozen files differ from the registered freeze: {[f for f, ok in status.items() if not ok]}'
print('all 12 frozen files present; all SHA-256 digests verified')
""")

md("""
## 3. Data validation

These checks need no modelling: file presence, row counts, key uniqueness, season types and the registered exclusions.

**Registered exclusions:**
- faulty game 2025101205, plays 1289 and 1314;
- speed spikes with s > 12.5 yd/s;
- plays nullified by penalty;
- PRE season dropped; POST used only as robustness;
- outcomes from **REG only**.
""")
code(r"""
t0 = time.time()
files = ['players', 'combine_results', 'combine_tracking', 'player_play', 'games', 'player_career_successes',
         'game_tracking_2023', 'game_tracking_2024', 'game_tracking_2025']
rows = {f: nio.scan_raw(f).select(pl.len()).collect().item() for f in files}
print(pl.DataFrame({'file': list(rows), 'rows': list(rows.values())}))
players = nio.scan_raw('players').collect(); cr = nio.scan_raw('combine_results').collect()
games = nio.scan_raw('games').collect(); pp = nio.scan_raw('player_play').collect()
assert players['nfl_id'].n_unique() == players.height == 510, 'players: 510 unique prospects'
assert cr['nfl_id'].n_unique() == cr.height == 510, 'combine_results: one row per prospect'
pp_st = pp.join(games.select('game_id', 'season_type'), on='game_id', how='left')
print(pp_st.group_by('season_type').len().sort('season_type'))
dup = pp.group_by('game_id', 'play_id', 'nfl_id').len().filter(pl.col('len') > 1).height
print('duplicate (game, play, player) keys in player_play:', dup); assert dup == 0
faulty = pp.filter((pl.col('game_id') == 2025101205) & pl.col('play_id').is_in([1289, 1314])).height
spikes = {y: nio.scan_raw(f'game_tracking_{y}').filter(pl.col('s') > 12.5).select(pl.len()).collect().item() for y in (2023, 2024, 2025)}
print('faulty-game player rows:', faulty, '| tracking frames with s > 12.5 yd/s:', spikes)
print(f'validation {time.time() - t0:.0f}s')
""")

md("""
## 4. Feature definitions: Combine capacity (combine data only)

**Tracked 40 peak speed, x_peak (yd/s).** For every Combine 40-yard-dash attempt, the sensor speed trace s(t) is fitted with a mono-exponential sprint curve, `s(t) = S0 (1 − exp(−(t − t0)/τ))`, up to the peak.

- **Valid attempt:** the fit has R² > 0.95 and the attempt's maximum speed is ≤ 12.5 yd/s.
- **x_peak** is the maximum over a player's valid attempts.
- It is standardised within position, using all Combine participants of that position.

The frozen functions `run_real_capacity.forty_fits` and `confirmatory_data.predictor_table` are used unchanged. The checks compare against the registered predictor table: the number of valid players per position and the x_peak sums.
""")
code(r"""
if RUN_COMBINE_FEATURES:
    t0 = time.time()
    nio.build_parquet_cache()            # typed Parquet copies of the CSVs, in the work directory only
    attempts = forty_fits()
    pred = cd.predictor_table(attempts, nio.load('combine_results', lazy=False))
    got = (pred.filter(pl.col('valid_tracked_40')).group_by('pos')
           .agg(pl.len().alias('n_valid'), pl.col('x_peak').sum().alias('x_peak_sum')).sort('pos'))
    tgt = pl.DataFrame(REGISTERED['repro_targets']['predictor_summary']).select('pos', 'n_valid', 'x_peak_sum')
    cmp = got.join(tgt, on='pos', suffix='_registered')
    print(cmp)
    assert pred.height == REGISTERED['repro_targets']['predictor_rows'] == 510
    assert (cmp['n_valid'] == cmp['n_valid_registered']).all(), 'valid tracked-40 counts differ from registration'
    assert np.allclose(cmp['x_peak_sum'], cmp['x_peak_sum_registered'], atol=1e-6), 'x_peak values differ'
    print('valid tracked 40, all positions:', int(pred['valid_tracked_40'].sum()), f'| {time.time() - t0:.0f}s')
""")

md("""
## 5. Feature definitions: game movement, contexts and the registered samples

**Feature definitions:**
- **Play-maximum speed (yd/s):** the maximum tracked speed from the `ball_snap` frame onward. For WR/TE it stops at the `pass_forward` / `pass_shovel` frame (`vmax_prepass`); for DB/DL/OL it runs to the end of the tracked play (`vmax_play`).
- **Task contexts (frozen):**
  - WR/TE: route depth. Deep = GO / POST / CORNER / WHEEL; short = HITCH / SLANT / OUT / FLAT / SCREEN / ANGLE; IN / CROSS excluded as ambiguous.
  - DB: coverage assignment (man / deep zone / underneath zone).
  - DL: pass rush vs run.
  - OL: pass block vs run.
- **Separation (H2 performance outcome):** `separation_at_pass_forward`, the distance to the nearest defender at the throw. It is defined on every route of a thrown pass, and the inventory showed it equals the tracked nearest-defender distance.
- **Eligibility:** a valid tracked 40; ≥ 100 primary REG opportunities; ≥ 20 plays in each contrast context (H2: ≥ 30 deep and ≥ 20 short routes, plus an official 40).

**What this section does:** the frozen Phase 3 feature stage and `confirmatory_data` eligibility functions rebuild the play table and the analysis frames, then compare **counts** with the registered join. Combine values are not attached to any play here.
""")
code(r"""
if RUN_GAME_PIPELINE:
    t0 = time.time()
    p3.features()                                   # per player-play speed features, one season at a time
    d, log = cd.outcome_table()                     # REG only + registered exclusions
    reg_log = REGISTERED['repro_targets']['play_exclusions']
    print(pl.DataFrame({'step': list(log), 'rebuilt': list(log.values()), 'registered': [reg_log[k] for k in log]}))
    assert all(log[k] == reg_log[k] for k in log), 'play exclusions differ from registration'
    out = []
    for pos in cd.CONTRASTS:
        fr, el = cd.h1_eligible(d, pred, pos)
        tg = REGISTERED['repro_targets']['frames'][f'h1_{pos}']
        byctx = dict(fr.group_by('ctx').len().iter_rows())
        out.append(dict(frame=f'H1-{pos}', players=int(el['elig_h1'].sum()), players_registered=tg['eligible_h1'],
                        plays=fr.height, plays_registered=tg['rows_after_join'],
                        by_context=str(byctx), by_context_registered=str({r['ctx']: r['len'] for r in tg['plays_by_context']})))
    f2, e2 = cd.h2_eligible(d, pred); tg = REGISTERED['repro_targets']['frames']['h2_WR']
    out.append(dict(frame='H2-WR', players=int(e2['elig_h2'].sum()), players_registered=tg['players'], plays=f2.height,
                    plays_registered=tg['rows_after_join'], by_context=str(dict(f2.group_by('route_depth').len().iter_rows())),
                    by_context_registered=str({r['route_depth']: r['len'] for r in tg['plays_by_depth']})))
    samples = pl.DataFrame(out); print(samples)
    assert (samples['players'] == samples['players_registered']).all() and (samples['plays'] == samples['plays_registered']).all(), \
        'registered sample sizes not reproduced'
    print(f'game pipeline {time.time() - t0:.0f}s: all registered sample sizes reproduced')
""")

md("""
**Descriptive context (game tracking only, no combine data): players reach near-top game speed more often on deep routes than on short routes.** The measure is the share of plays on which a player reaches ≥ 90 % of his own top game speed, where own top speed is the mean of his 5 fastest REG plays. It describes what was observed. It is not a direct measurement of opportunity, and it does not show that Combine speed has a stronger effect on deep routes (that was H1-WR, which is inconclusive). The registered values are shown; see writeup Figure 3.
""")
code(r"""
print(pl.DataFrame(REGISTERED['speed_demand']['rows']).sort('pos', 'context'))
""")

md(r"""
## 6. The registered models (explained, not re-fitted)

### H1: does Combine top speed show up in game speed, and more so where the task demands it?

For position $p$ with two task contexts $c \in \{h, l\}$ (e.g. deep vs short routes), each play's maximum speed is modelled as

$$y_{ijc} = \mathbf{w}_{ij}^\top\boldsymbol\gamma_c + \beta_c\,x_i + b_{ic} + u_{t(ij)} + \varepsilon_{ijc}, \qquad (b_{ih}, b_{il}) \sim N(0, \Sigma_b),$$

where:
- $\mathbf{w}$ holds pre-snap covariates (route, coverage shell, down, distance bin, formation, time-to-throw bin, season, NFL year);
- $x_i$ is standardised Combine peak speed;
- $b_{ic}$ is a correlated player effect;
- $u$ is a team-season effect.

The estimand is the correlation between Combine speed and the player's **noise-free** game-speed level,

$$\rho_c = \frac{\beta_c}{\sqrt{\beta_c^2 + \Sigma_{b,cc}}}, \qquad \Delta = \rho_h - \rho_l .$$

- **Fit:** REML.
- **Inference:** player-cluster percentile bootstrap, B = 2,000.
- **Decision rule:**
  - *supported* if the 95 % CI excludes 0 (Δ > 0);
  - *falsified* if the 90 % upper bound is < 0.15 (the smallest effect of interest);
  - otherwise *inconclusive*.
- Phase 4 simulations on the real design showed the bootstrap is valid but conservative (null size ≤ 0.0125 vs 0.025).

### H2: does tracked top speed add information about deep-route separation beyond the official 40?

$$s_{ij} = \mathbf{w}_{ij}^\top\boldsymbol\gamma + \beta_F F_i + \beta_P x_i + b_i + u_{t(ij)} + \varepsilon_{ij},$$

where $F_i$ is the sign-reversed official 40 time, on WR deep routes of thrown passes.

- **Reported:** $\beta_P$ (yards per SD of tracked peak speed), with a player-cluster bootstrap CI.
- **Prediction for held-out players:** player-grouped 10-fold CV × 20, plus a 2025 season-forward check.
- **Errors-in-variables sensitivity:** across plausible reliabilities of the official 40.
- **Status:** H2 was demoted to a **secondary, estimation-focused** analysis *before any association was examined* (deviation D4), because it could not be powered.

### DL role and weight (H1-DL(b), Holm family)

The pooled DL correlation (mean of pass-rush and run) is re-estimated with EDGE/interior role × context and Combine weight × context added. The registered test is the difference, pooled − adjusted.

**Holm correction** is applied over {H1-DB, H1-DL(a), H1-DL(b), H5(b)}.
""")

md("## 7. Registered results and decisions")
code(r"""
R = REGISTERED
h1, h2, con = R['h1_wr'], R['h2'], R['contrasts']
rows = [
  ('H1-WR (primary)', f"Δ = {h1['delta']:.3f}", f"[{h1['ci95'][0]:.3f}, {h1['ci95'][1]:.3f}]", h1['decision'], f"run {h1['run']}, commit {h1['code_commit'][:7]}, seed {h1['seed']}, B {h1['B']}"),
  ('H2 (secondary, estimation)', f"β_P = {h2['beta_P_yd_per_sd']:.3f} yd/SD", f"[{h2['beta_P_ci95_yd'][0]:.3f}, {h2['beta_P_ci95_yd'][1]:.3f}]", h2['label'], f"commit {h2['code_commit'][:7]}, B {h2['B']}"),
]
for k in ['H1-DB', 'H1-DL(a)', 'H1-DL(b)', 'H5(b)']:
    c = con[k]; rows.append((f'{k} (Holm)', f"{c['estimate']:.3f}", f"[{c['ci95'][0]:.3f}, {c['ci95'][1]:.3f}]",
                             f"{c['decision']} (Holm p = {c['p_holm']:.3f})", R['contrasts']['source']))
print(pl.DataFrame(rows, schema=['analysis', 'estimate', '95% CI', 'registered decision', 'provenance'], orient='row'))
print(f"\nH2 detail: held-out-player ΔR²_CV = {h2['cv_frozen']['dr2']:.3f} (90% LB {h2['cv_frozen']['lb90']:.3f}); "
      f"season-forward ΔRMSE = {h2['season_forward']['dRMSE']:.4f} yd; deep-separation reliability = {h2['reliability_deep_level']:.2f}; "
      f"between-player SD = {h2['between_player_sd_yd']:.2f} yd")
print(f"H1-DL(b) detail: pooled ρ {R['dl_b']['base_pooled']:.3f} → adjusted {R['dl_b']['adjusted_pooled']:.3f} (role + weight)")
""")

md("""
**How to read these (registered wording):**
- **H1-WR is INCONCLUSIVE.** The deep-vs-short difference is neither supported nor ruled out.
- **H2 is INCONCLUSIVE.** No incremental predictive value of tracked peak speed beyond the official 40 was detected for deep-route separation. This is **not** evidence that speed has no effect on separation: the true-scale partial correlation could not be estimated, because deep separation has low player-level reliability (0.44).
- **H1-DL(b) is supported after Holm adjustment (p = 0.032).** The pooled DL association is substantially sensitive to role and weight adjustment. The adjusted value must not be read causally.
""")

md("## 8. Figures (as in the writeup), drawn from the registered results")
code(r"""
sf.apply_style()
rendered = []
for name, fn in sf.FIGURES.items():
    fig = fn(REGISTERED)
    w, h = (fig.get_size_inches() * fig.dpi).round().astype(int)
    rendered.append((name, int(w), int(h), len(fig.axes)))
    plt.show(); plt.close(fig)
print(pl.DataFrame(rendered, schema=['figure', 'width_px', 'height_px', 'axes'], orient='row'))
assert len(rendered) == 7 and all(r[3] >= 1 for r in rendered), 'expected 7 rendered figures'
print('figures rendered:', len(rendered))
""")

md("""
## 9. Reproducibility statement

| step | re-executed here? | how verified |
|---|---|---|
| data validation | yes | assertions in §3 |
| Combine feature definitions (tracked 40 peak speed) | yes, frozen functions | valid-player counts and x_peak sums equal the registered predictor table (§4) |
| game features, exclusions, eligibility, sample sizes | yes, frozen functions (counts only) | equal the registered join validation (§5) |
| H1-WR, H2, secondary-family model fits and bootstraps | **no** (one-shot registered runners) | embedded outputs with run ID, commit and seed (§1, §7) |
| figures | yes, from the embedded registered results | identical to the writeup |

**Why the confirmatory fits are not re-run.** Each runner (`scripts/run_h1_wr_confirmatory.py`, `run_h2_estimation.py`, `run_secondary.py`) refuses to run a second time. Silently re-running them would turn a single pre-registered test into a repeatable one.

An auditor can repeat a fit in the project repository on a fresh copy, under a new run ID labelled as a *reproduction*, with approval. That reproduction would be compared with, but never replace, the registered result. The full REML bootstraps (B = 2,000) take roughly 20–60 minutes per family on 4 CPUs.
""")

md("""
## 10. Clean-up: no competition data left in the notebook outputs

The scratch directory with Parquet copies of the competition files is deleted. The check then confirms that nothing data-like (CSV, Parquet, NumPy) was written to `/kaggle/working`, the folder Kaggle publishes as notebook output.
""")
code(r"""
import shutil
shutil.rmtree(WORK, ignore_errors=True)
print('scratch directory removed:', not WORK.exists())
if KAGGLE_WORKING.exists():
    leaked = [str(p) for p in KAGGLE_WORKING.rglob('*') if p.is_file() and p.suffix.lower() in ('.csv', '.parquet', '.npy', '.npz', '.feather', '.zip')]
    print('data-like files in', KAGGLE_WORKING, ':', leaked or 'none')
    assert not leaked, 'competition-derived data files found in /kaggle/working'
import resource
print(f'peak memory (max RSS) of this kernel: {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**2:.2f} GB')
""")

nb["cells"] = C
nb["metadata"] = {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                  "language_info": {"name": "python"}}
out = ROOT / "notebooks" / "11_final_submission.ipynb"
nbf.write(nb, out)
print("wrote", out)
