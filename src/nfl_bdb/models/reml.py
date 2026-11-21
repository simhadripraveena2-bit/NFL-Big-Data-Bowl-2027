"""REML for the pre-registered linear mixed models (Phase 4).

Model (statistical_model_specification.md §1.1 / §2.1):

    y = X beta + Z_p b + Z_t tau + eps
    b_i ~ N_d(0, Sigma_b)  per player (d = number of task contexts; unstructured covariance)
    tau_t ~ N(0, s_tau^2)   per team-season
    eps ~ N(0, s_g^2)       residual variance specific to residual group g (= task context)

The player random-effect column for (player i, context c) loads on plays of player i in context c.
Estimation profiles beta out by GLS and maximises the REML log-likelihood over the variance
parameters (Cholesky of Sigma_b, log s_tau, log s_g). All likelihood terms are evaluated through
the Woodbury identity on q x q matrices (q = n_players * d + n_team), using cross-products that are
pre-computed once per residual group, so one evaluation is O(q^3 + p q^2) and independent of the
number of plays.

    -2 l_R = sum_g n_g log s_g^2 + log|G| + log|C| + log|X' V^-1 X| + r' V^-1 r,
    C = G^-1 + Z' R^-1 Z.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import linalg, optimize, sparse


@dataclass
class RemlFit:
    beta: np.ndarray
    cov_beta: np.ndarray
    sigma_b: np.ndarray       # d x d player covariance
    s2_team: float
    s2_resid: np.ndarray      # per residual group
    neg2ll: float
    converged: bool
    n_iter: int


def _cross(X, Z, y):
    Zt = Z.T.tocsr()
    return dict(XX=X.T @ X, XZ=np.asarray((Zt @ X).T), ZZ=(Zt @ Z).toarray(), Xy=X.T @ y,
                Zy=np.asarray(Zt @ y).ravel(), yy=float(y @ y), n=len(y))


def fit_reml(y: np.ndarray, X: np.ndarray, player: np.ndarray, ctx: np.ndarray, team: np.ndarray | None,
             d: int, start: dict | None = None, maxiter: int = 300) -> RemlFit:
    """player: 0..P-1, ctx: 0..d-1 (also the residual group), team: 0..T-1 or None."""
    y = np.asarray(y, float); X = np.asarray(X, float)
    P = int(player.max()) + 1
    T = int(team.max()) + 1 if team is not None else 0
    q = P * d + T
    n = len(y)
    col_p = player * d + ctx
    rows = np.arange(n)
    Zp = sparse.csr_matrix((np.ones(n), (rows, col_p)), shape=(n, q))
    if T:
        Zp = Zp + sparse.csr_matrix((np.ones(n), (rows, P * d + team)), shape=(n, q))
    groups = [np.where(ctx == g)[0] for g in range(d)]
    cr = [_cross(X[ix], Zp[ix], y[ix]) for ix in groups]
    p = X.shape[1]
    tril = np.tril_indices(d)

    def unpack(th):
        L = np.zeros((d, d)); L[tril] = th[: len(tril[0])]
        L[np.diag_indices(d)] = np.exp(L[np.diag_indices(d)])
        k = len(tril[0])
        s2t = np.exp(2 * th[k]) if T else 0.0
        off = k + (1 if T else 0)
        s2g = np.exp(2 * th[off: off + d])
        return L, s2t, s2g

    def pieces(th):
        L, s2t, s2g = unpack(th)
        Sb = L @ L.T + 1e-10 * np.eye(d)
        w = 1 / s2g
        A = sum(w[g] * cr[g]["ZZ"] for g in range(d))
        B = sum(w[g] * cr[g]["XZ"] for g in range(d))
        Pm = sum(w[g] * cr[g]["XX"] for g in range(d))
        u = sum(w[g] * cr[g]["Zy"] for g in range(d))
        v = sum(w[g] * cr[g]["Xy"] for g in range(d))
        s = sum(w[g] * cr[g]["yy"] for g in range(d))
        Sbi = np.linalg.inv(Sb)
        Gi = np.zeros(q)
        C = A.copy()
        for i in range(P):
            sl = slice(i * d, (i + 1) * d)
            C[sl, sl] += Sbi
        if T:
            C[P * d:, P * d:] += np.eye(T) / max(s2t, 1e-12)
        cf = linalg.cho_factor(C, lower=True, check_finite=False)
        CiBt = linalg.cho_solve(cf, B.T, check_finite=False)
        Ciu = linalg.cho_solve(cf, u, check_finite=False)
        XVX = Pm - B @ CiBt
        XVy = v - B @ Ciu
        yVy = s - u @ Ciu
        logdetC = 2 * np.sum(np.log(np.diag(cf[0])))
        logdetG = P * np.linalg.slogdet(Sb)[1] + (T * np.log(max(s2t, 1e-12)) if T else 0.0)
        logdetR = sum(cr[g]["n"] * np.log(s2g[g]) for g in range(d))
        del Gi
        return Sb, s2t, s2g, XVX, XVy, yVy, logdetC, logdetG, logdetR

    def obj(th):
        try:
            Sb, s2t, s2g, XVX, XVy, yVy, ldC, ldG, ldR = pieces(th)
            cx = linalg.cho_factor(XVX, lower=True, check_finite=False)
            beta = linalg.cho_solve(cx, XVy, check_finite=False)
            quad = yVy - beta @ XVy
            ldX = 2 * np.sum(np.log(np.diag(cx[0])))
            val = ldR + ldG + ldC + ldX + quad
            return val if np.isfinite(val) else 1e30
        except (np.linalg.LinAlgError, ValueError):
            return 1e30

    # starting values: OLS residual variance split
    beta0, *_ = np.linalg.lstsq(X, y, rcond=None)
    r0 = y - X @ beta0
    v0 = np.var(r0)
    th0 = np.zeros(len(tril[0]) + (1 if T else 0) + d)
    if start is not None:
        th0 = start["theta"].copy()
    else:
        L0 = np.eye(d) * np.log(np.sqrt(0.1 * v0))
        th0[: len(tril[0])] = L0[tril]
        if T:
            th0[len(tril[0])] = np.log(np.sqrt(0.02 * v0))
        th0[len(tril[0]) + (1 if T else 0):] = [np.log(np.sqrt(np.var(r0[ctx == g]) * 0.9)) for g in range(d)]
    res = optimize.minimize(obj, th0, method="L-BFGS-B", options=dict(maxiter=maxiter))
    th = res.x
    Sb, s2t, s2g, XVX, XVy, yVy, *_ = pieces(th)
    covb = np.linalg.inv(XVX)
    beta = covb @ XVy
    fit = RemlFit(beta=beta, cov_beta=covb, sigma_b=Sb, s2_team=float(s2t), s2_resid=s2g, neg2ll=float(res.fun),
                  converged=bool(res.success), n_iter=int(res.nit))
    fit.theta = th  # type: ignore[attr-defined]
    return fit
