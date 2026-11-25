"""Phase 16 B: synthetic straight starts from a stationary stance with known ground truth. Simulation only.

1 ms grid. Before t0 the athlete stands (tiny stance sway). From t0 the forward acceleration builds up over
``ramp`` s (force development) and then follows an effort-scaled force-velocity law:
    a(t) = kappa * A0 * (1 - v/V) * min(1, (t - t0)/ramp)
Optional along-axis step oscillation (step_amp, 3.5-4.5 Hz) fades in above 1 yd/s. Lateral sway is small.
The recording starts ``rec_offset`` s before t0 (negative = recording starts after movement began) and lasts
``rec_len`` s; sampling at fs with a phase in [0, 1/fs). Noise: Gaussian or 1/30-yd quantisation.

Truth: t_onset = first time true speed > 1 yd/s; launch_p95_trend (PRIMARY) = 95th percentile of the propulsive
trend acceleration (no step oscillation) on the 11 instants t_onset + 0, 0.1, ..., 1.0 s; launch_p95_inst
(secondary) = the same for the instantaneous a_t including step oscillation, which 10 Hz smoothing cannot resolve;
launch_mean; trial effective acceleration A_eff = kappa * A0; athlete A0.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

DT = 0.001


@dataclass(frozen=True)
class StartTrial:
    A0: float = 7.0
    V: float = 9.0
    kappa: float = 0.85
    ramp: float = 0.2
    t0: float = 0.5           # movement start in simulation time
    step_amp: float = 0.2
    step_f: float = 4.0
    step_phase: float = 0.0
    sway: float = 0.03
    rot_deg: float = 0.0
    rec_offset: float = 0.3   # recording starts this long before t0
    rec_len: float = 4.0


def draw_start_trial(rng, A0: float, V: float, step_max: float = 0.4, offset_range=(-0.1, 0.5)) -> StartTrial:
    return StartTrial(A0=A0, V=V, kappa=rng.uniform(0.75, 0.95), ramp=rng.uniform(0.1, 0.35), t0=1.0,
                      step_amp=rng.uniform(0, step_max), step_f=rng.uniform(3.5, 4.5), step_phase=rng.uniform(0, 2 * np.pi),
                      sway=rng.uniform(0.0, 0.05), rot_deg=rng.uniform(0, 360), rec_offset=rng.uniform(*offset_range))


def simulate_start(tr: StartTrial) -> dict:
    T = tr.t0 + tr.rec_len + 0.5
    t = np.arange(0, T, DT); n = len(t)
    u = np.zeros(n); a_trend = np.zeros(n); v = 0.0
    for i in range(n):
        if t[i] >= tr.t0:
            r = min(1.0, (t[i] - tr.t0) / tr.ramp)
            a_trend[i] = tr.kappa * tr.A0 * (1 - v / tr.V) * r
            v += a_trend[i] * DT
        u[i] = v
    leg = np.clip((u - 1.0) / 1.0, 0.0, 1.0)
    u_obs = u + leg * tr.step_amp * np.sin(2 * np.pi * tr.step_f * t + tr.step_phase)
    w = tr.sway * np.sin(2 * np.pi * 1.5 * t)                    # stance / running sway (lateral velocity)
    rot = np.radians(tr.rot_deg); e = np.array([np.cos(rot), np.sin(rot)]); nr = np.array([-e[1], e[0]])
    vx = u_obs * e[0] + w * nr[0]; vy = u_obs * e[1] + w * nr[1]
    x = 50 + np.cumsum(vx) * DT; y = 25 + np.cumsum(vy) * DT
    speed = np.hypot(vx, vy); a_t = np.gradient(speed, DT)
    i_on = int(np.flatnonzero(speed > 1.0)[0]); t_on = t[i_on]
    grid = t_on + np.arange(11) * 0.1
    at_grid = np.interp(grid, t, a_t); tr_grid = np.interp(grid, t, a_trend)
    return dict(t=t, x=x, y=y, speed=speed, a_t=a_t, a_trend=a_trend,
                truth=dict(t_onset=float(t_on), t0=tr.t0, A0=tr.A0, kappa=tr.kappa, A_eff=tr.kappa * tr.A0,
                           launch_p95_trend=float(np.percentile(tr_grid, 95)), launch_p95_inst=float(np.percentile(at_grid, 95)),
                           launch_mean=float(np.mean(np.interp(np.linspace(t_on, t_on + 1, 1001), t, a_t)))), trial=tr)


def sample_start(sim: dict, phase: float, noise: str, sigma: float, rng, fs: float = 10.0) -> dict:
    tr = sim["trial"]; t = sim["t"]
    t_start = tr.t0 - tr.rec_offset + phase
    ts = np.arange(t_start, min(t_start + tr.rec_len, t[-1]), 1.0 / fs)
    x = np.interp(ts, t, sim["x"]); y = np.interp(ts, t, sim["y"])
    if sigma > 0:
        x = x + rng.normal(0, sigma, len(x)); y = y + rng.normal(0, sigma, len(y))
    if noise == "quant30":
        x = np.round(x * 30) / 30; y = np.round(y * 30) / 30
    elif noise != "gauss":
        raise ValueError(noise)
    return dict(ts=ts, x=x, y=y)
