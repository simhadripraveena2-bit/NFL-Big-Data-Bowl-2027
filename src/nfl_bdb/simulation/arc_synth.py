"""Phase 15 B4: synthetic curved running (pass-rush-like arc) with known ground truth. Simulation only.

Path on a 1 ms grid: straight lead-in, curvature ramped linearly from 0 to 1/R over ``ramp`` s, constant
curvature until the total heading change reaches ``dtheta``, ramped back to 0, straight lead-out. Speed
v(t) = v0 + a_t t (tangential acceleration). Heading rate omega = v kappa; positions integrate the velocity.
Truth per instant: speed, heading rate, curvature, centripetal acceleration v^2 kappa.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

DT = 0.001


@dataclass(frozen=True)
class ArcTrial:
    v0: float = 4.0
    a_t: float = 1.0
    R: float = 3.5
    dtheta_deg: float = 100.0
    ramp: float = 0.2
    direction: int = 1          # +1 left (counter-clockwise), -1 right
    lead_in: float = 1.0
    lead_out: float = 1.2
    rot_deg: float = 0.0


def draw_arc_trial(rng: np.random.Generator) -> ArcTrial:
    """Ranges bracket the real pass-rush arcs (radius ~2.9-4.1 yd, speed ~3.7-4.8 yd/s; Phase 14)."""
    return ArcTrial(v0=rng.uniform(3.0, 5.0), a_t=rng.uniform(0.0, 2.0), R=rng.uniform(2.0, 5.0),
                    dtheta_deg=rng.uniform(60, 150), ramp=rng.uniform(0.1, 0.4), direction=int(rng.choice([-1, 1])),
                    rot_deg=rng.uniform(0, 360))


def simulate_arc(tr: ArcTrial) -> dict:
    k_max = 1.0 / tr.R
    # build curvature as a function of time, given v(t); constant part length found by integrating heading
    T_max = tr.lead_in + 2 * tr.ramp + 6.0 + tr.lead_out
    t = np.arange(0, T_max, DT); v = tr.v0 + tr.a_t * t
    target = np.radians(tr.dtheta_deg)
    kap = np.zeros_like(t)
    i0 = int(tr.lead_in / DT); nr = max(int(tr.ramp / DT), 1)
    ramp_up = np.linspace(0, k_max, nr, endpoint=False)
    kap[i0:i0 + nr] = ramp_up
    head = np.cumsum(v * kap) * DT
    # heading still needed after ramp-up, reserving the ramp-down contribution (approx. same as ramp-up)
    h_ramp = head[i0 + nr - 1]
    i = i0 + nr; acc = h_ramp
    while acc < target - h_ramp and i < len(t) - nr - 1:
        kap[i] = k_max; acc += v[i] * k_max * DT; i += 1
    kap[i:i + nr] = np.linspace(k_max, 0, nr, endpoint=False)
    i_end = i + nr
    n_total = i_end + int(tr.lead_out / DT)
    t, v, kap = t[:n_total], v[:n_total], kap[:n_total]
    omega = tr.direction * v * kap
    theta = np.radians(tr.rot_deg) + np.cumsum(omega) * DT
    vx, vy = v * np.cos(theta), v * np.sin(theta)
    x = 40 + np.cumsum(vx) * DT; y = 20 + np.cumsum(vy) * DT
    const = (kap >= k_max * (1 - 1e-9))
    return dict(t=t, x=x, y=y, speed=v, omega=omega, kappa=kap, a_n=v * v * kap, const=const, trial=tr)


def sample_arc(sim: dict, phase: float, noise: str, sigma: float, rng: np.random.Generator, fs: float = 10.0) -> dict:
    t = sim["t"]; ts = np.arange(phase, t[-1], 1.0 / fs)
    x = np.interp(ts, t, sim["x"]); y = np.interp(ts, t, sim["y"])
    if sigma > 0:
        x = x + rng.normal(0, sigma, len(x)); y = y + rng.normal(0, sigma, len(y))
    if noise == "quant30":
        x = np.round(x * 30) / 30; y = np.round(y * 30) / 30
    elif noise != "gauss":
        raise ValueError(noise)
    idx = np.clip(np.round(ts / 0.001).astype(int), 0, len(t) - 1)
    return dict(ts=ts, x=x, y=y, speed=sim["speed"][idx], omega=np.abs(sim["omega"][idx]), kappa=sim["kappa"][idx],
                a_n=sim["a_n"][idx], const=sim["const"][idx])
