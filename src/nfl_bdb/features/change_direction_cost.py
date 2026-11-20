"""Capacity-constrained minimum-time (CCMT) change-of-direction cost.

Problem (fixed path, centre-of-mass point model). Given a path parameterised by arc length
s in [0, L] with signed curvature kappa(s), choose a speed profile v(s) >= 0 that minimises

    T = integral_0^L ds / v(s)

subject to, for every s,
    (C1) v(s) <= S0                                  maximal speed
    (C2) a_t = v dv/ds <= A0 (1 - v/S0) * g(v, s)    propulsion: athlete's A–S line (Hill–Keller form)
    (C3) a_t >= -D * g(v, s)                         braking capacity
    (C4) a_n = v^2 |kappa| <= C(v)                   lateral (centripetal) capacity
    (C5) v = 0 at stop points (180° reversals: line touches in shuttle / 3-cone drills)
    (C6) v(0) = v_start; v(L) free (or fixed)
with g = 1 (independent limits) or g = sqrt(1 - (a_n / C(v))^2) ("friction ellipse" coupling: lateral
use of capacity reduces tangential capacity — the g–g diagram idea from vehicle dynamics).

Solution. With constraints of this form the minimum-time profile is the pointwise minimum of
(i) the curvature/speed cap, (ii) a forward pass integrating the maximal propulsion from the start
and every stop point, and (iii) a backward pass integrating maximal braking from the end and every
stop point. This forward–backward construction is the standard solution of minimum-time travel on
a fixed path with acceleration limits (Velenis & Tsiotras 2008, DOI 10.1007/s10957-008-9381-7;
Lipp & Boyd 2014, DOI 10.1080/00207179.2013.875224 — cited for the method; abstracts not read).
We verify it numerically against a direct-transcription NLP (``min_time_nlp``).

Prior human-running work (for scoping novelty): optimal control of minimum-time running exists
(Keller 1973; Maroński 1996) and speed–radius relations for running on turns exist (Greene 1985;
Chang & Kram 2007). What we add is the athlete-specific *counterfactual on a measured path* and the
decomposition  T_obs = T*_ref + (T*_own - T*_ref) + (T_obs - T*_own):
    capacity cost  K = T*_own - T*_ref     (own limits vs a reference athlete, same path)
    execution cost E = T_obs - T*_own      (time lost relative to own demonstrated limits)
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.signal import savgol_filter


# ----------------------------------------------------------------------------- paths
@dataclass
class Path:
    s: np.ndarray        # arc length grid (yd)
    x: np.ndarray
    y: np.ndarray
    kappa: np.ndarray    # unsigned curvature (1/yd)
    stop: np.ndarray     # bool, v must be 0 here

    @property
    def length(self):
        return float(self.s[-1])


def path_from_waypoints(wp, radii, ds=0.02, reversal_deg=170.0):
    """Polyline through waypoints with interior corners rounded by circular arcs.

    radii[i] is the fillet radius at interior waypoint i+1. Corners turning more than
    ``reversal_deg`` are treated as stop points (touch-and-return), not fillets.
    """
    wp = np.asarray(wp, float)
    radii = list(radii)
    pts, kap, stops = [], [], []

    def add_line(p0, p1):
        L = np.linalg.norm(p1 - p0)
        n = max(int(np.ceil(L / ds)), 1)
        t = np.linspace(0, 1, n + 1)[1:]
        for tt in t:
            pts.append(p0 + tt * (p1 - p0)); kap.append(0.0); stops.append(False)

    cur = wp[0].copy()
    pts.append(cur.copy()); kap.append(0.0); stops.append(False)
    for i in range(1, len(wp) - 1):
        a, b, c = wp[i - 1], wp[i], wp[i + 1]
        d1 = (b - a) / np.linalg.norm(b - a); d2 = (c - b) / np.linalg.norm(c - b)
        turn = np.degrees(np.arccos(np.clip(d1 @ d2, -1, 1)))
        r = radii[i - 1]
        if turn >= reversal_deg or r <= 0:
            add_line(cur, b); stops[-1] = turn >= reversal_deg; cur = b.copy(); continue
        if turn < 1e-6:
            continue
        phi = np.radians(turn)
        tlen = r * np.tan(phi / 2)
        lim = 0.49 * min(np.linalg.norm(b - a), np.linalg.norm(c - b))
        if tlen > lim:
            tlen = lim; r = tlen / np.tan(phi / 2)
        p_in, p_out = b - d1 * tlen, b + d2 * tlen
        add_line(cur, p_in)
        sgn = np.sign(d1[0] * d2[1] - d1[1] * d2[0])
        nrm = np.array([-d1[1], d1[0]]) * sgn
        ctr = p_in + nrm * r
        ang0 = np.arctan2(p_in[1] - ctr[1], p_in[0] - ctr[0])
        n = max(int(np.ceil(r * phi / ds)), 2)
        for tt in np.linspace(0, 1, n + 1)[1:]:
            ang = ang0 + sgn * phi * tt
            pts.append(ctr + r * np.array([np.cos(ang), np.sin(ang)])); kap.append(1.0 / r); stops.append(False)
        cur = p_out
    add_line(cur, wp[-1])
    P = np.array(pts)
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    return Path(s=seg, x=P[:, 0], y=P[:, 1], kappa=np.array(kap), stop=np.array(stops))


def resample_path(path: Path, ds=0.02) -> Path:
    s_new = np.arange(0, path.length + 1e-9, ds)
    k = np.interp(s_new, path.s, path.kappa)
    stop = np.zeros(len(s_new), bool)
    for s_stop in path.s[path.stop]:
        stop[np.argmin(np.abs(s_new - s_stop))] = True
    return Path(s=s_new, x=np.interp(s_new, path.s, path.x), y=np.interp(s_new, path.s, path.y), kappa=k, stop=stop)


# ----------------------------------------------------------------------------- athlete limits
@dataclass
class AthleteLimits:
    A0: float            # theoretical max acceleration (yd/s^2), A–S intercept
    S0: float            # theoretical max speed (yd/s)
    D: float             # max braking deceleration (yd/s^2)
    C: float             # lateral capacity (yd/s^2): constant, or value at v = 0 for the speed model
    lat_slope: float = 0.0   # C(v) = C * (1 - lat_slope * v / S0); 0 => constant lateral limit
    ellipse: bool = False    # couple tangential and lateral capacity
    lateral: bool = True     # ablation switch: ignore lateral limit entirely

    def C_of(self, v):
        return np.maximum(self.C * (1 - self.lat_slope * np.asarray(v) / self.S0), 1e-3)

    def scaled(self, eta_A=1.0, eta_D=1.0, eta_C=1.0, eta_S=1.0):
        return replace(self, A0=self.A0 * eta_A, D=self.D * eta_D, C=self.C * eta_C, S0=self.S0 * eta_S)


def _cap(path: Path, lim: AthleteLimits):
    """Speed cap from (C1) and (C4). For the speed-dependent lateral model solve v^2 k = C(v)."""
    cap = np.full(len(path.s), lim.S0 * 0.9999)
    if lim.lateral:
        k = np.maximum(path.kappa, 1e-9)
        if lim.lat_slope == 0:
            cap = np.minimum(cap, np.sqrt(lim.C / k))
        else:  # k v^2 + C*slope/S0 v - C = 0
            a, b, c = k, lim.C * lim.lat_slope / lim.S0, -lim.C
            cap = np.minimum(cap, (-b + np.sqrt(b * b - 4 * a * c)) / (2 * a))
    cap[path.stop] = 0.0
    return cap


def _g(v, kappa, lim):
    if not (lim.ellipse and lim.lateral):
        return np.ones_like(np.asarray(v, float))
    r = v * v * kappa / lim.C_of(v)
    return np.sqrt(np.clip(1 - r * r, 0.0, 1.0))


def min_time_profile(path: Path, lim: AthleteLimits, v_start=0.0, v_end=None, scheme="rk2"):
    """Forward–backward minimum-time speed profile. Returns (v_star, T_star, t_of_s).

    scheme="rk2": midpoint integration of v^2 (default, accurate on fine grids);
    scheme="euler": explicit node-wise constraints identical to ``min_time_nlp`` (for verification)."""
    s, k = path.s, path.kappa
    n = len(s); ds = np.diff(s)
    cap = _cap(path, lim)
    if scheme == "euler":
        vf = np.empty(n); vf[0] = min(v_start, cap[0])
        for i in range(n - 1):
            v = vf[i]
            a = max(lim.A0 * (1 - v / lim.S0) * _g(v, k[i], lim), 0.0)
            vf[i + 1] = min(np.sqrt(v * v + 2 * a * ds[i]), cap[i + 1])
        vb = np.empty(n); vb[-1] = cap[-1] if v_end is None else min(v_end, cap[-1])
        for i in range(n - 1, 0, -1):
            # largest v_{i-1} with (v_i^2 - v_{i-1}^2)/(2 ds) >= -D g(v_i)
            vb[i - 1] = min(np.sqrt(vb[i] ** 2 + 2 * lim.D * _g(vb[i], k[i], lim) * ds[i - 1]), cap[i - 1])
        v = np.minimum(np.minimum(vf, vb), cap)
        vv = v[:-1] + v[1:]
        dt = np.where(vv > 1e-9, 2 * ds / np.maximum(vv, 1e-9), np.inf)
        t = np.r_[0, np.cumsum(dt)]
        return v, float(t[-1]), t
    vf = np.empty(n); vf[0] = min(v_start, cap[0])
    for i in range(n - 1):            # forward: maximal propulsion (RK2 in v^2)
        v = vf[i]
        a1 = lim.A0 * (1 - v / lim.S0) * _g(v, k[i], lim)
        vm = np.sqrt(max(v * v + a1 * ds[i], 0.0))
        a2 = lim.A0 * (1 - vm / lim.S0) * _g(vm, 0.5 * (k[i] + k[i + 1]), lim)
        vf[i + 1] = min(np.sqrt(max(v * v + 2 * max(a2, 0.0) * ds[i], 0.0)), cap[i + 1])
    vb = np.empty(n); vb[-1] = cap[-1] if v_end is None else min(v_end, cap[-1])
    for i in range(n - 1, 0, -1):     # backward: maximal braking
        v = vb[i]
        d1 = lim.D * _g(v, k[i], lim)
        vm = np.sqrt(v * v + d1 * ds[i - 1])
        d2 = lim.D * _g(vm, 0.5 * (k[i] + k[i - 1]), lim)
        vb[i - 1] = min(np.sqrt(v * v + 2 * d2 * ds[i - 1]), cap[i - 1])
    v = np.minimum(np.minimum(vf, vb), cap)
    vv = v[:-1] + v[1:]
    dt = np.where(vv > 1e-9, 2 * ds / np.maximum(vv, 1e-9), np.inf)
    t = np.r_[0, np.cumsum(dt)]
    return v, float(t[-1]), t


def min_time_nlp(path: Path, lim: AthleteLimits, n_nodes=80, v_start=0.0):
    """Direct-transcription check: variables b_i = v_i^2 on a coarse grid; SLSQP.

    Constraints use the same explicit (node-i) acceleration evaluation as a first-order scheme, so
    agreement with ``min_time_profile`` (on the same grid) validates the forward–backward solution."""
    from scipy.optimize import minimize
    P = resample_path(path, path.length / (n_nodes - 1))
    s, k = P.s, P.kappa; ds = np.diff(s)
    cap = _cap(P, lim)
    nn = len(s)

    def obj(b):
        v = np.sqrt(np.maximum(b, 1e-10))
        return np.sum(2 * ds / (v[:-1] + v[1:] + 1e-6))

    def cons(b):
        v = np.sqrt(np.maximum(b, 0)); acc = np.diff(b) / (2 * ds)
        prop = lim.A0 * (1 - v[:-1] / lim.S0) * _g(v[:-1], k[:-1], lim) - acc
        brake = acc + lim.D * _g(v[1:], k[1:], lim)
        return np.r_[prop, brake]
    v_fb, T_fb, _ = min_time_profile(P, lim, v_start=v_start, scheme="euler")
    bnds = [(0, c ** 2) for c in cap]
    bnds[0] = (v_start ** 2, v_start ** 2)
    best = None
    rng = np.random.default_rng(0)
    starts = [np.minimum(v_fb ** 2 * 0.5, cap ** 2), np.minimum(v_fb ** 2 * 0.95, cap ** 2),
              np.minimum((v_fb * rng.uniform(0.3, 1.0, nn)) ** 2, cap ** 2)]
    for b0 in starts:
        b0[0] = v_start ** 2
        r = minimize(obj, b0, method="SLSQP", bounds=bnds, constraints=[dict(type="ineq", fun=cons)],
                     options=dict(maxiter=1000, ftol=1e-12))
        viol = max(0.0, -np.min(cons(r.x)))
        if viol < 1e-6 and (best is None or obj(r.x) < best[0]):
            best = (obj(r.x), r)
    if best is None:
        return dict(T_nlp=np.nan, T_fb_same_grid=T_fb, success=False, v_nlp=None, v_fb=v_fb, s=s)
    return dict(T_nlp=float(best[0]), T_fb_same_grid=T_fb, success=bool(best[1].success),
                v_nlp=np.sqrt(np.maximum(best[1].x, 0)), v_fb=v_fb, s=s)


# ----------------------------------------------------------------------------- execution & measurement
def simulate_execution(path: Path, lim: AthleteLimits, eta=(1.0, 1.0, 1.0), dwell=0.0, fs=10.0,
                       noise_sd=0.01, rng=None, pre_s=0.5, post_s=0.8):
    """Athlete runs the path using fractions eta = (eta_A, eta_D, eta_C) of their capacities, plus
    ``dwell`` seconds standing at each stop point, starting from rest and *running through* the
    finish (continuing straight at the finishing speed). Returns the true time from start to
    finish and noisy positions sampled at ``fs`` with sampling phase randomised."""
    rng = rng or np.random.default_rng(0)
    run_lim = lim.scaled(*eta)
    v, _, t = min_time_profile(path, run_lim)
    t = t.copy()
    for i in np.flatnonzero(path.stop):
        t[i:] += dwell
    T_true = float(t[-1])
    phase = rng.uniform(0, 1.0 / fs)
    tt = np.arange(-pre_s + phase, T_true + post_s, 1.0 / fs)
    s_of_t = np.interp(tt, t, path.s, left=0.0, right=path.length)
    x = np.interp(s_of_t, path.s, path.x); y = np.interp(s_of_t, path.s, path.y)
    after = tt > T_true
    if after.any():   # run through the finish along the final heading at the final speed
        d = np.array([path.x[-1] - path.x[-2], path.y[-1] - path.y[-2]]); d /= np.linalg.norm(d)
        extra = v[-1] * (tt[after] - T_true)
        x[after] = path.x[-1] + d[0] * extra; y[after] = path.y[-1] + d[1] * extra
    x = x + rng.normal(0, noise_sd, len(x)); y = y + rng.normal(0, noise_sd, len(y))
    if noise_sd > 0:
        x = np.round(x, 2); y = np.round(y, 2)
    finish_dir = np.array([path.x[-1] - path.x[-2], path.y[-1] - path.y[-2]]); finish_dir /= np.linalg.norm(finish_dir)
    return dict(T_true=T_true, t=tt, x=x, y=y, v_profile=v, t_profile=t,
                finish_point=np.array([path.x[-1], path.y[-1]]), finish_dir=finish_dir)


def estimate_path(x, y, fs=10.0, window=7, poly=2, ds=0.02, finish_point=None, finish_dir=None,
                  start_dist=0.5, stop_speed=0.6, onset_speed=0.3, edge_yd=1.0):
    """Recover path geometry, curvature, stop points and gate-to-gate time from noisy positions.

    * smoothing: Savitzky–Golay on positions (time domain); curvature from smoothed derivatives;
    * start gate: the time the athlete's cumulative distance (from movement onset) reaches
      ``start_dist`` yd — avoids the bias of detecting onset from a smoothed speed trace;
    * finish gate: the crossing of the finish line (point + direction, assumed known from the
      drill layout), linearly interpolated between frames;
    * stop points: interior local speed minima below ``stop_speed`` farther than ``edge_yd`` from
      either end of the path.
    Returns (Path from onset to finish, T_obs between gates, s_start_on_path, speed trace)."""
    dt = 1.0 / fs
    xs = savgol_filter(x, window, poly); ys = savgol_filter(y, window, poly)
    vx = savgol_filter(x, window, poly, deriv=1, delta=dt); vy = savgol_filter(y, window, poly, deriv=1, delta=dt)
    ax = savgol_filter(x, window, poly, deriv=2, delta=dt); ay = savgol_filter(y, window, poly, deriv=2, delta=dt)
    sp = np.hypot(vx, vy)
    i0 = int(np.flatnonzero(sp > onset_speed)[0])
    i0 = max(i0 - 1, 0)
    # finish crossing
    proj = (xs - finish_point[0]) * finish_dir[0] + (ys - finish_point[1]) * finish_dir[1]
    cand = np.flatnonzero((proj[:-1] < 0) & (proj[1:] >= 0) & (np.arange(len(proj) - 1) > i0))
    j = int(cand[-1]) if len(cand) else len(proj) - 2
    t_fin = (j + (-proj[j]) / (proj[j + 1] - proj[j])) * dt
    seg = slice(i0, j + 2)
    X, Y = xs[seg], ys[seg]
    s = np.r_[0, np.cumsum(np.hypot(np.diff(X), np.diff(Y)))]
    tt = np.arange(i0, j + 2) * dt
    t_start = float(np.interp(start_dist, s, tt))
    # truncate the path at the finish crossing
    s_fin = float(np.interp(t_fin, tt, s))
    kap = np.abs(vx * ay - vy * ax)[seg] / np.maximum(sp[seg], 0.3) ** 3
    sps = sp[seg]
    stop_idx = [i for i in range(1, len(sps) - 1) if sps[i] < stop_speed and sps[i] <= sps[i - 1]
                and sps[i] <= sps[i + 1] and edge_yd < s[i] < s_fin - edge_yd]
    keep = np.r_[True, np.diff(s) > 1e-6]
    idx = np.flatnonzero(keep)
    P = Path(s=s[keep], x=X[keep], y=Y[keep], kappa=kap[keep], stop=np.isin(idx, stop_idx))
    P = resample_path(P, ds)
    m = P.s <= s_fin + 1e-9
    P = Path(s=P.s[m], x=P.x[m], y=P.y[m], kappa=np.where(P.stop[m], 0.0, P.kappa[m]), stop=P.stop[m])
    return P, float(t_fin - t_start), start_dist, sp


def linear_sprint_time(dist, lim: AthleteLimits):
    """Time to cover ``dist`` from rest under the A–S line (closed-form mono-exponential)."""
    from scipy.optimize import brentq
    tau = lim.S0 / lim.A0
    d = lambda t: lim.S0 * (t - tau * (1 - np.exp(-t / tau))) - dist
    return brentq(d, 1e-6, 60)


def conventional_measures(T_obs, dist, lim_sprint: AthleteLimits, speed_trace=None, fs=10.0, s_from=0.0):
    """Total time, COD deficit (Nimphius et al. 2016 logic: COD time minus linear sprint time over the
    same distance), percentage COD deficit (our operationalisation of the Freitas et al. 2022 idea),
    mean COD speed and peak braking from the measured speed trace."""
    T_lin = linear_sprint_time(dist, lim_sprint) - (linear_sprint_time(s_from, lim_sprint) if s_from > 0 else 0.0)
    out = dict(total_time=T_obs, codd=T_obs - T_lin, codd_pct=100 * (T_obs - T_lin) / T_lin, cod_speed=dist / T_obs)
    if speed_trace is not None:
        a = np.gradient(savgol_filter(speed_trace, 7, 2), 1 / fs)
        out["peak_braking"] = float(-np.min(a))
    return out


def segment_time(path: Path, lim: AthleteLimits, s_from=0.0):
    """Minimum time from rest at s = 0, counted from arc length ``s_from`` to the end."""
    _, _, t = min_time_profile(path, lim)
    return float(t[-1] - np.interp(s_from, path.s, t))


def ccmt_cost(path: Path, T_obs: float, lim_own: AthleteLimits, lim_ref: AthleteLimits, s_from=0.0):
    """CCMT decomposition over the gate segment [s_from, end]:
    execution cost E = T_obs - T*(own), capacity cost K = T*(own) - T*(ref)."""
    T_own = segment_time(path, lim_own, s_from)
    T_ref = segment_time(path, lim_ref, s_from)
    return dict(T_star_own=T_own, T_star_ref=T_ref, execution_cost=T_obs - T_own, capacity_cost=T_own - T_ref,
                execution_ratio=T_obs / T_own)


# ----------------------------------------------------------------------------- drills
def drill_paths(radius=0.75):
    """Synthetic drill geometries (yd). Shapes approximate the combine drills; they are not the
    official specifications."""
    r = radius
    d = {}
    d["shuttle_5_10_5"] = path_from_waypoints([[0, 0], [5, 0], [-5, 0], [0, 0]], [0, 0])
    # 3-cone (L): A(0,0) B(0,5) C(5,5). A->B touch, B->A touch, A->B, around C (clockwise), back around B, to A
    d["three_cone"] = path_from_waypoints(
        [[0, 0], [0, 5], [0, 0], [0, 5.0 + r], [5 + r, 5 + r], [5 + r, 5 - r], [4.0, 5 - r], [-r, 5.0 + r * 0.2], [-r * 0.2, -0.0]],
        [0, 0, r, r, r, r, 2 * r])
    for ang in (45, 90, 135):
        th = np.radians(ang)
        d[f"cut_{ang}"] = path_from_waypoints([[0, 0], [10, 0], [10 + 6 * np.cos(th), 6 * np.sin(th)]], [r if ang < 120 else 0.5 * r])
    d["straight_20"] = path_from_waypoints([[0, 0], [20, 0]], [])
    return d


def cone_turn_path(radius, turn_deg=90.0, approach=10.0, exit_len=10.0, ds=0.02):
    """Path that goes *around* a cone at the origin: straight approach tangent to a circle of
    ``radius`` centred on the cone, an arc turning ``turn_deg`` degrees, then a straight exit.
    Larger radius = faster cornering but a longer path — the trade-off behind path choice."""
    r = float(radius); th = np.radians(turn_deg)
    pts, kap = [], []
    for xx in np.arange(-approach, 0.0, ds):          # approach along y = r, moving +x
        pts.append((xx, r)); kap.append(0.0)
    n = max(int(np.ceil(r * th / ds)), 2)
    for a in np.linspace(np.pi / 2, np.pi / 2 - th, n):   # clockwise arc around the cone
        pts.append((r * np.cos(a), r * np.sin(a))); kap.append(1.0 / r)
    a_end = np.pi / 2 - th
    d = np.array([np.sin(a_end), -np.cos(a_end)])          # tangent direction (clockwise)
    p_end = np.array([r * np.cos(a_end), r * np.sin(a_end)])
    for t in np.arange(ds, exit_len + ds, ds):
        pts.append(tuple(p_end + d * t)); kap.append(0.0)
    P = np.array(pts)
    s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    return Path(s=s, x=P[:, 0], y=P[:, 1], kappa=np.array(kap), stop=np.zeros(len(s), bool))


# ----------------------------------------------------------------------------- real combine drills (Phase 2)
def real_drill_segment(x, y, s, fs=10.0, window=7, poly=2, onset="raw", stop_speed=1.0, edge_yd=1.0, ds=0.02,
                       stops=True):
    """Gate and path for a real combine agility attempt (3-cone or short shuttle), both of which
    finish by crossing back over the start line.

    onset: "raw"  = last frame with provided speed <= 0.3 yd/s before speed first exceeds 1.0 yd/s
                     (frame 0 if the recording already starts in motion);
           "extrapolated" = linear back-extrapolation of the first 5 frames of the speed rise to s = 0.
    finish: last crossing of the line through the start point perpendicular to the final heading.
    Returns dict(path, T_obs, L, n_stops, ok, reason)."""
    s = np.asarray(s, float); x = np.asarray(x, float); y = np.asarray(y, float)
    k = np.flatnonzero(s > 1.0)
    if len(k) == 0 or len(s) < window + 5:
        return dict(ok=False, reason="no movement")
    i0 = int(k[0])
    while i0 > 0 and s[i0] > 0.3:
        i0 -= 1
    t0 = float(i0)
    if onset == "extrapolated":
        tt = np.arange(i0, min(i0 + 5, len(s))); sl, ic = np.polyfit(tt, s[tt], 1)
        if sl > 0:
            t0 = min(-ic / sl, float(i0))
    p0 = np.array([x[i0], y[i0]])
    d = np.array([x[-1] - x[-4], y[-1] - y[-4]]); nd = np.linalg.norm(d)
    if nd < 1e-6:
        return dict(ok=False, reason="no final heading")
    d /= nd
    proj = (x - p0[0]) * d[0] + (y - p0[1]) * d[1]
    c = np.flatnonzero((proj[:-1] < 0) & (proj[1:] >= 0)); c = c[c > i0 + 10]
    if len(c) == 0:
        return dict(ok=False, reason="no finish crossing")
    j = int(c[-1]); tf = j + (-proj[j]) / (proj[j + 1] - proj[j])
    dt = 1.0 / fs
    xs = savgol_filter(x, window, poly); ys = savgol_filter(y, window, poly)
    vx = savgol_filter(x, window, poly, deriv=1, delta=dt); vy = savgol_filter(y, window, poly, deriv=1, delta=dt)
    ax = savgol_filter(x, window, poly, deriv=2, delta=dt); ay = savgol_filter(y, window, poly, deriv=2, delta=dt)
    sp = np.hypot(vx, vy)
    seg = slice(i0, j + 2)
    X, Y = xs[seg], ys[seg]
    sarc = np.r_[0, np.cumsum(np.hypot(np.diff(X), np.diff(Y)))]
    s_fin = float(np.interp(tf, np.arange(i0, j + 2), sarc))
    kap = np.abs(vx * ay - vy * ax)[seg] / np.maximum(sp[seg], 0.3) ** 3
    sps = sp[seg]
    stop_idx = [i for i in range(1, len(sps) - 1) if stops and sps[i] < stop_speed and sps[i] <= sps[i - 1]
                and sps[i] <= sps[i + 1] and edge_yd < sarc[i] < s_fin - edge_yd]
    keep = np.r_[True, np.diff(sarc) > 1e-6]
    idx = np.flatnonzero(keep)
    P = Path(s=sarc[keep], x=X[keep], y=Y[keep], kappa=kap[keep], stop=np.isin(idx, stop_idx))
    P = resample_path(P, ds)
    m = P.s <= s_fin + 1e-9
    P = Path(s=P.s[m], x=P.x[m], y=P.y[m], kappa=np.where(P.stop[m], 0.0, P.kappa[m]), stop=P.stop[m])
    return dict(ok=True, reason="", path=P, T_obs=float((tf - t0) * dt), L=float(P.length), n_stops=int(P.stop.sum()))
