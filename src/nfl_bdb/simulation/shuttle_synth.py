"""Phase 13: continuous-time synthetic short-shuttle first reversal (R1) with known ground truth.

Simulation only. Synthetic performance is never evidence of real-world validity.

Motion is built on a 1 ms grid in a drill frame (u = along the outgoing drill axis, w = lateral):

  approach   u from -u0 to -v_entry with a half-sine acceleration pulse over T_app
  brake      constant deceleration D_in until |u| = u_c
  turn       u from -u_c to +u_c2 along a smoothstep over T_turn (zero along-axis acceleration at both
             ends: the plant), lateral reach w_turn(t) = W sin(pi tau), incoming-direction deviation
             delta blended to 0 across the turn (reversal geometry / straight-exit direction)
  outgoing   du/dt = A0 (1 - u / V)  (athlete force-velocity profile) until t_brake,
             then the acceleration is blended linearly over 0.25 s to -D_out (braking for the next line)
  sway       lateral stride sway S sin(2 pi f t + phi) throughout (small deviations from straight running)
  steps      along-axis step-frequency speed oscillation (3.5-4.5 Hz), faded in above |u| = 1 yd/s

Velocity in the world frame = R(rot) R(delta(t)) [u, w]; positions are its cumulative (trapezoid) integral,
acceleration its numerical derivative, so position, velocity and acceleration are physically consistent.
Sampling at fs with a phase uniform in [0, 1/fs); positions linearly interpolated from the 1 ms grid
(interpolation error < 1e-5 yd). Noise: iid Gaussian (sigma) or quantisation to a 1/30-yd grid (the
2023-24 Combine position grid) after a small Gaussian jitter.

Ground truth (true drill axis = outgoing direction):
  t_rev     time u crosses 0;   t_min  time of minimum true speed
  t_exit    first t > t_min with true speed >= 1 yd/s and velocity within 15 deg of the outgoing axis
  theta_05  mean true tangential acceleration on [t_exit, t_exit + 0.5]  = (|v|(t+0.5) - |v|(t)) / 0.5
  theta_27  mean true tangential acceleration on [t_exit + 0.2, t_exit + 0.7]
  A0, V     the athlete's force-velocity parameters
"""
from __future__ import annotations

from dataclasses import asdict, dataclass

import numpy as np

DT = 0.001


@dataclass(frozen=True)
class Athlete:
    A0: float
    V: float


@dataclass(frozen=True)
class TrialParams:
    u0: float = 0.6
    v_entry: float = 3.1
    T_app: float = 0.9
    D_in: float = 8.0
    u_c: float = 0.6
    u_c2: float = 0.5
    T_turn: float = 0.3
    W: float = 0.3
    delta_deg: float = 0.0
    t_brake_after_turn: float = 0.8
    D_out: float = 6.0
    sway_amp: float = 0.08
    sway_f: float = 2.0
    sway_phase: float = 0.0
    step_amp: float = 0.0      # along-axis step-frequency speed oscillation amplitude (yd/s), legs only
    step_f: float = 4.0
    step_phase: float = 0.0
    rot_deg: float = 0.0
    tail: float = 1.8          # recording continues this long after the reversal


def draw_trial(rng: np.random.Generator, sway_max: float = 0.15, step_max: float = 0.0) -> TrialParams:
    """Trial-level (within-athlete) variation. Ranges from the real-shuttle geometry audit (Phase 12)."""
    return TrialParams(
        u0=rng.uniform(0.3, 0.9), v_entry=rng.uniform(2.7, 3.6), T_app=rng.uniform(0.7, 1.0),
        D_in=rng.uniform(6.0, 10.0), u_c=rng.uniform(0.4, 0.9), u_c2=rng.uniform(0.3, 0.8),
        T_turn=rng.uniform(0.15, 0.45), W=rng.uniform(0.05, 0.5), delta_deg=rng.uniform(-10, 10),
        t_brake_after_turn=rng.uniform(0.65, 0.95), D_out=rng.uniform(5.0, 8.0),
        sway_amp=rng.uniform(0.0, sway_max), sway_f=rng.uniform(1.5, 2.5), sway_phase=rng.uniform(0, 2 * np.pi),
        step_amp=rng.uniform(0.0, step_max), step_f=rng.uniform(3.5, 4.5), step_phase=rng.uniform(0, 2 * np.pi),
        rot_deg=rng.uniform(0, 360))


def draw_athletes(rng: np.random.Generator, n: int, A0_mean=9.0, A0_cv=0.08, V_mean=9.0, V_cv=0.03) -> list[Athlete]:
    A0 = rng.normal(A0_mean, A0_mean * A0_cv, n); V = rng.normal(V_mean, V_mean * V_cv, n)
    return [Athlete(float(a), float(v)) for a, v in zip(A0, V)]


def _smoothstep(tau):
    tau = np.clip(tau, 0.0, 1.0)
    return tau * tau * (3 - 2 * tau)


def simulate(ath: Athlete, tp: TrialParams) -> dict:
    """Continuous-time (1 ms) trajectory and ground truth."""
    # --- along-axis velocity u (outgoing positive) ---
    seg_u, seg_w, seg_delta = [], [], []
    # approach: half-sine acceleration pulse from -u0 to -v_entry
    n1 = int(round(tp.T_app / DT)); t1 = np.arange(n1) * DT
    u1 = -(tp.u0 + (tp.v_entry - tp.u0) * (1 - np.cos(np.pi * t1 / tp.T_app)) / 2)
    seg_u.append(u1); seg_w.append(np.zeros(n1)); seg_delta.append(np.full(n1, tp.delta_deg))
    # brake to -u_c
    n2 = int(round((tp.v_entry - tp.u_c) / tp.D_in / DT)); u2 = -tp.v_entry + tp.D_in * np.arange(1, n2 + 1) * DT
    seg_u.append(u2); seg_w.append(np.zeros(n2)); seg_delta.append(np.full(n2, tp.delta_deg))
    # turn
    n3 = int(round(tp.T_turn / DT)); tau = np.arange(1, n3 + 1) / n3
    u3 = -tp.u_c + (tp.u_c + tp.u_c2) * _smoothstep(tau)
    seg_u.append(u3); seg_w.append(tp.W * np.sin(np.pi * tau)); seg_delta.append(tp.delta_deg * (1 - _smoothstep(tau)))
    i_turn_end = n1 + n2 + n3
    # outgoing: FV acceleration then blend to braking
    n4 = int(round(tp.tail / DT)); u4 = np.empty(n4); u = tp.u_c2
    nb = int(round(tp.t_brake_after_turn / DT)); nbl = int(round(0.25 / DT))
    for i in range(n4):
        a_fv = ath.A0 * (1 - u / ath.V)
        if i < nb:
            a = a_fv
        else:
            f = min((i - nb) / nbl, 1.0); a = (1 - f) * a_fv + f * (-tp.D_out)
        u = u + a * DT; u4[i] = u
    seg_u.append(u4); seg_w.append(np.zeros(n4)); seg_delta.append(np.zeros(n4))
    u = np.concatenate(seg_u); w = np.concatenate(seg_w); dl = np.radians(np.concatenate(seg_delta))
    t = np.arange(len(u)) * DT
    w = w + tp.sway_amp * np.sin(2 * np.pi * tp.sway_f * t + tp.sway_phase)
    # step-frequency along-axis oscillation, faded in/out with |u| so the turn itself is not perturbed
    leg = np.clip((np.abs(u) - 1.0) / 1.0, 0.0, 1.0)
    u = u + np.sign(u) * leg * tp.step_amp * np.sin(2 * np.pi * tp.step_f * t + tp.step_phase)
    # rotate by the incoming deviation, then globally
    cu, su = np.cos(dl), np.sin(dl)
    ua, wa = cu * u - su * w, su * u + cu * w
    rot = np.radians(tp.rot_deg); e = np.array([np.cos(rot), np.sin(rot)]); nrm = np.array([-e[1], e[0]])
    vx = ua * e[0] + wa * nrm[0]; vy = ua * e[1] + wa * nrm[1]
    x = 50 + np.r_[0, np.cumsum((vx[1:] + vx[:-1]) / 2) * DT]; y = 25 + np.r_[0, np.cumsum((vy[1:] + vy[:-1]) / 2) * DT]
    speed = np.hypot(vx, vy)
    ax = np.gradient(vx, DT); ay = np.gradient(vy, DT)
    a_t = np.where(speed > 1e-9, (vx * ax + vy * ay) / np.maximum(speed, 1e-9), 0.0)
    # ground truth
    i_rev = int(np.flatnonzero((u[:-1] < 0) & (u[1:] >= 0))[0])
    i_min = int(np.argmin(speed[: i_turn_end + 200]))
    cosd = (vx * e[0] + vy * e[1]) / np.maximum(speed, 1e-12)
    ok = (speed >= 1.0) & (cosd >= np.cos(np.radians(15.0)))
    ok[: i_min + 1] = False
    i_exit = int(np.flatnonzero(ok)[0])
    t_exit = t[i_exit]

    def sp_at(tt):
        return float(np.interp(tt, t, speed))
    truth = dict(t_rev=float(t[i_rev]), t_min=float(t[i_min]), v_min=float(speed[i_min]), t_exit=float(t_exit),
                 v_exit=float(speed[i_exit]), theta_05=(sp_at(t_exit + 0.5) - sp_at(t_exit)) / 0.5,
                 theta_27=(sp_at(t_exit + 0.7) - sp_at(t_exit + 0.2)) / 0.5, A0=ath.A0, V=ath.V,
                 t_turn_end=float(t[i_turn_end]), T_total=float(t[-1]), axis=e)
    return dict(t=t, x=x, y=y, vx=vx, vy=vy, speed=speed, a_t=a_t, truth=truth)


def sample(sim: dict, fs: float, phase: float, noise: str, sigma: float, rng: np.random.Generator) -> dict:
    """Sample the continuous trajectory at fs with sampling phase in [0, 1/fs); add measurement noise.
    noise: 'gauss' (iid N(0, sigma^2) per coordinate) or 'quant30' (jitter sigma, then round to 1/30 yd)."""
    t = sim["t"]; ts = np.arange(phase, t[-1], 1.0 / fs)
    x = np.interp(ts, t, sim["x"]); y = np.interp(ts, t, sim["y"]); s = np.interp(ts, t, sim["speed"])
    if sigma > 0:
        x = x + rng.normal(0, sigma, len(x)); y = y + rng.normal(0, sigma, len(y))
    if noise == "quant30":
        x = np.round(x * 30) / 30; y = np.round(y * 30) / 30
    elif noise != "gauss":
        raise ValueError(noise)
    return dict(ts=ts, x=x, y=y, s=s, t0=float(ts[0]))


def trial_dict(tp: TrialParams) -> dict:
    return asdict(tp)
