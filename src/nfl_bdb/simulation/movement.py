"""Synthetic football-like movement with known acceleration–speed capacity, plus the
measurement pipeline (sampling, position noise, smoothing, differentiation).

Units: yards, seconds (yd/s, yd/s^2) throughout.

Ground-truth capacity model (Hill–Keller / linear acceleration–speed line, generalised):
    a_max(v) = A0 * (1 - (v / S0) ** k)        (k = 1 is the linear A–S model)
An effort of intensity e in (0, 1] accelerates at e * a_max(v). Only maximal efforts (e ≈ 1)
touch the frontier — most in-game movement is sub-maximal, and opportunities for maximal
efforts depend on role (the censoring problem Candidate B addresses).
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import savgol_filter

M_PER_YD = 0.9144


@dataclass
class GameSimConfig:
    fs: float = 10.0               # tracking sampling rate (Hz)
    dt: float = 0.01               # integration step (s)
    play_median_s: float = 7.0     # median play duration incl. 1 s pre-snap (Phase 1: median 70 frames)
    play_log_sd: float = 0.20
    presnap_s: float = 1.0
    noise_sd: float = 0.01         # white position noise per axis (yd); 0.01 matches real game d2x/d2s statistics
    noise_ar_sd: float = 0.0       # slowly varying (AR1) position error per axis (yd)
    noise_ar_rho: float = 0.95
    round_to: float = 0.01         # data are reported to 0.01 yd
    spike_play_rate: float = 0.0   # fraction of plays containing a tracking fault burst
    k_shape: float = 1.0           # frontier shape exponent (1 = linear A–S)
    acc_lag_s: float = 0.10        # first-order lag on acceleration commands (humans cannot change acceleration instantly)
    lat_acc_max: float = 6.0       # bound on centripetal accel used to limit heading changes
    sg_window: int = 5             # Savitzky–Golay window (frames) for derivatives
    sg_poly: int = 2


def _segment_draw(rng, n, v, S0, D, p_max):
    """Draw new movement segments for n plays. Returns arrays (type, dur, e, vt, b, omega)."""
    u = rng.random(n)
    p_eff = np.where(v < 2.0, 0.8, 0.45)
    p_cru = np.where(v < 2.0, 0.1, 0.25)
    typ = np.where(u < p_eff, 1, np.where(u < p_eff + p_cru, 2, 3))
    is_max = rng.random(n) < p_max
    e = np.where(is_max, rng.uniform(0.97, 1.0, n), 0.05 + 0.85 * rng.beta(2.0, 2.0, n))
    vt_sub = v + rng.uniform(1.0, 1.0, n) + rng.random(n) * np.maximum(0.5, 0.9 * S0 - v - 1.0)
    vt = np.where(is_max, S0 * rng.uniform(0.985, 1.0, n), np.minimum(vt_sub, 0.95 * S0))
    dur = np.where(typ == 1, np.where(is_max, rng.uniform(2.0, 5.0, n), rng.uniform(0.5, 3.0, n)),
                   np.where(typ == 2, rng.uniform(0.3, 1.5, n), rng.uniform(0.4, 2.0, n)))
    b = rng.uniform(1.0, 1.0, n) * rng.uniform(1.0, np.maximum(1.01, D), n)
    omega = rng.normal(0.0, 0.6, n)
    return typ, dur, e, vt, b, omega, is_max


def simulate_game_tracks(A0, S0, D, p_max, n_plays, cfg: GameSimConfig, rng: np.random.Generator):
    """Simulate plays for athletes (arrays A0, S0, D, p_max, n_plays of equal length).

    Returns dict of frame-level arrays at cfg.fs: athlete, play, t, x, y (measured, noisy),
    v_true, a_true (tangential), maxeff (frame belongs to a maximal effort).
    """
    A0, S0, D, p_max = map(np.asarray, (A0, S0, D, p_max))
    n_plays = np.asarray(n_plays, dtype=int)
    ath = np.repeat(np.arange(len(A0)), n_plays)
    P = len(ath)
    a0, s0, dd, pm = A0[ath], S0[ath], D[ath], p_max[ath]
    T = np.exp(np.log(cfg.play_median_s) + cfg.play_log_sd * rng.standard_normal(P))
    n_steps = int(np.ceil(T.max() / cfg.dt))
    rec_every = int(round(1.0 / (cfg.fs * cfg.dt)))
    n_rec = n_steps // rec_every + 1

    v = rng.uniform(0.0, 0.4, P)
    h = rng.uniform(0, 2 * np.pi, P)
    x = np.zeros(P); y = np.zeros(P)
    typ = np.zeros(P, int); left = np.full(P, cfg.presnap_s); e = np.zeros(P); vt = np.zeros(P)
    b = np.zeros(P); om = np.zeros(P); ismax = np.zeros(P, bool)
    X = np.full((P, n_rec), np.nan); Y = X.copy(); V = X.copy(); A = X.copy(); MX = np.zeros((P, n_rec), bool)
    a_state = np.zeros(P)
    r = 0
    for step in range(n_steps + 1):
        t = step * cfg.dt
        alive = t <= T
        need = alive & (left <= 0)
        if need.any():
            idx = np.where(need)[0]
            ty, du, ee, vv, bb, oo, mm = _segment_draw(rng, len(idx), v[idx], s0[idx], dd[idx], pm[idx])
            typ[idx], left[idx], e[idx], vt[idx], b[idx], om[idx], ismax[idx] = ty, du, ee, vv, bb, oo, mm
        frac = np.clip(v / s0, 0, 1)
        front = a0 * (1 - frac ** cfg.k_shape)
        cmd = np.where(typ == 1, e * front, np.where(typ == 3, -b, 0.0))
        cmd = np.where((typ == 0) | ~alive, 0.0, cmd)
        if cfg.acc_lag_s > 0:
            a_state = a_state + (cmd - a_state) * min(1.0, cfg.dt / cfg.acc_lag_s)
        else:
            a_state = cmd
        acc = np.minimum(a_state, front)          # never exceed the capacity frontier
        v_new = np.maximum(v + acc * cfg.dt, 0.0)
        reach_up = (typ == 1) & (v_new >= vt)
        v_new = np.where(reach_up, np.maximum(vt, v), v_new)
        stop_br = (typ == 3) & (v_new <= 0.0)
        acc = (v_new - v) / cfg.dt          # realised tangential acceleration at the current state
        a_state = np.where(reach_up | (v_new <= 0), acc, a_state)
        if step % rec_every == 0:
            X[alive, r], Y[alive, r], V[alive, r], A[alive, r] = x[alive], y[alive], v[alive], acc[alive]
            MX[alive, r] = ismax[alive] & (typ[alive] == 1)
            r += 1
        left = np.where(reach_up | stop_br, 0.0, left - cfg.dt)
        # heading: limit centripetal acceleration v*|omega| <= lat_acc_max
        om_eff = np.clip(om, -cfg.lat_acc_max / np.maximum(v, 0.5), cfg.lat_acc_max / np.maximum(v, 0.5))
        h = h + np.where(typ == 0, 0.0, om_eff) * cfg.dt
        vm = 0.5 * (v + v_new)
        x = x + vm * np.cos(h) * cfg.dt; y = y + vm * np.sin(h) * cfg.dt
        v = v_new

    # measurement: noise, faults, rounding
    Xm, Ym = X.copy(), Y.copy()
    if cfg.noise_sd > 0:
        Xm += rng.normal(0, cfg.noise_sd, Xm.shape); Ym += rng.normal(0, cfg.noise_sd, Ym.shape)
    if cfg.noise_ar_sd > 0:
        for M in (Xm, Ym):
            z = np.zeros(P)
            sd_inn = cfg.noise_ar_sd * np.sqrt(1 - cfg.noise_ar_rho ** 2)
            for j in range(n_rec):
                z = cfg.noise_ar_rho * z + rng.normal(0, sd_inn, P)
                M[:, j] += z
    if cfg.spike_play_rate > 0:
        bad = np.where(rng.random(P) < cfg.spike_play_rate)[0]
        for p in bad:
            nvalid = int(np.sum(~np.isnan(Xm[p])))
            if nvalid < 20: continue
            j0 = rng.integers(5, nvalid - 10); L = rng.integers(2, 6)
            ang = rng.uniform(0, 2 * np.pi); mag = rng.uniform(0.5, 2.0)
            Xm[p, j0:j0 + L] += mag * np.cos(ang); Ym[p, j0:j0 + L] += mag * np.sin(ang)
    if cfg.round_to:
        Xm = np.round(Xm / cfg.round_to) * cfg.round_to; Ym = np.round(Ym / cfg.round_to) * cfg.round_to

    valid = ~np.isnan(X)
    pid = np.repeat(np.arange(P)[:, None], n_rec, axis=1)
    tt = np.repeat((np.arange(n_rec) / cfg.fs)[None, :], P, axis=0)
    return dict(athlete=ath[pid[valid]], play=pid[valid], t=tt[valid], x=Xm[valid], y=Ym[valid],
                v_true=V[valid], a_true=A[valid], maxeff=MX[valid])


def kinematics_from_positions(x, y, play, fs: float, window: int = 5, poly: int = 2):
    """Speed, tangential and normal acceleration and curvature from positions, per play,
    via Savitzky–Golay derivatives. Arrays must be ordered by (play, time)."""
    n = len(x)
    s = np.full(n, np.nan); at = np.full(n, np.nan); an = np.full(n, np.nan)
    bounds = np.flatnonzero(np.diff(play)) + 1
    starts = np.r_[0, bounds]; ends = np.r_[bounds, n]
    dt = 1.0 / fs
    for a, b in zip(starts, ends):
        L = b - a
        if L < window:
            continue
        xs, ys = x[a:b], y[a:b]
        vx = savgol_filter(xs, window, poly, deriv=1, delta=dt); vy = savgol_filter(ys, window, poly, deriv=1, delta=dt)
        ax = savgol_filter(xs, window, poly, deriv=2, delta=dt); ay = savgol_filter(ys, window, poly, deriv=2, delta=dt)
        sp = np.hypot(vx, vy)
        safe = np.maximum(sp, 1e-6)
        s[a:b] = sp
        at[a:b] = (vx * ax + vy * ay) / safe
        an[a:b] = np.abs(vx * ay - vy * ax) / safe
    curv = an / np.maximum(s, 1e-6) ** 2
    return s, at, an, curv


def sample_athletes(rng, n_per_pos: int, calib: dict, rho_SA: float = -0.3):
    """Draw ground-truth athletes per position from calibration means/SDs (combine-40 fits).

    calib: {pos: dict(S0_mean, S0_sd, A0_mean, A0_sd, p_max, D_mean)}.
    """
    out = {k: [] for k in ("pos", "A0", "S0", "D", "p_max")}
    for pos, c in calib.items():
        z = rng.multivariate_normal([0, 0], [[1, rho_SA], [rho_SA, 1]], n_per_pos)
        S0 = c["S0_mean"] + c["S0_sd"] * z[:, 0]
        A0 = c["A0_mean"] + c["A0_sd"] * z[:, 1]
        D = c["D_mean"] * np.exp(0.15 * rng.standard_normal(n_per_pos))
        pm = c["p_max"] * np.exp(0.5 * rng.standard_normal(n_per_pos))
        out["pos"] += [pos] * n_per_pos; out["A0"].append(A0); out["S0"].append(S0)
        out["D"].append(D); out["p_max"].append(np.clip(pm, 0, 0.9))
    return dict(pos=np.array(out["pos"]), A0=np.concatenate(out["A0"]), S0=np.concatenate(out["S0"]),
                D=np.concatenate(out["D"]), p_max=np.concatenate(out["p_max"]))


def kinematics_fast(x, y, play, fs: float, window: int = 5, poly: int = 2):
    """Vectorised Savitzky–Golay kinematics on concatenated plays (ordered by play, time).

    Frames within window//2 of a play boundary are returned as NaN (edges are not used), which
    keeps the computation a single convolution. Returns speed, tangential accel, normal accel."""
    from scipy.ndimage import convolve1d
    from scipy.signal import savgol_coeffs
    dt = 1.0 / fs
    c1 = savgol_coeffs(window, poly, deriv=1, delta=dt, use="conv")
    c2 = savgol_coeffs(window, poly, deriv=2, delta=dt, use="conv")
    vx = convolve1d(x, c1, mode="nearest"); vy = convolve1d(y, c1, mode="nearest")
    ax = convolve1d(x, c2, mode="nearest"); ay = convolve1d(y, c2, mode="nearest")
    sp = np.hypot(vx, vy); safe = np.maximum(sp, 1e-6)
    at = (vx * ax + vy * ay) / safe
    an = np.abs(vx * ay - vy * ax) / safe
    h = window // 2
    n = len(x)
    bad = np.zeros(n, bool)
    idx = np.arange(n)
    for k in range(-h, h + 1):
        j = np.clip(idx + k, 0, n - 1)
        bad |= play[j] != play
    bad[:h] = True; bad[n - h:] = True
    for arr in (sp, at, an):
        arr[bad] = np.nan
    return sp, at, an
