"""Shared ML general/higher-order factor models; independent of report inputs."""

from dataclasses import dataclass
import math
import numpy as np
from scipy import optimize, stats


def standardize(X):
    X = np.asarray(X, dtype=float)
    if X.ndim != 2 or len(X) < 2 or not np.isfinite(X).all():
        raise ValueError("scores must be a finite model-by-task matrix")
    mu = X.mean(axis=0)
    sd = X.std(axis=0, ddof=1)
    if np.any(sd < 1e-12):
        raise ValueError("constant task scores cannot be factor analyzed")
    return (X - mu) / sd


def corr(Z):
    return np.corrcoef(Z, rowvar=False)


# ---------------------------------------------------------------- factor machinery


def paf(R, k, iterations=500, tol=1e-7):
    """Principal-axis factoring; returns loadings (p x k) and communalities."""
    p = R.shape[0]
    h2 = np.full(p, 0.7)
    L = np.zeros((p, k))
    for _ in range(iterations):
        reduced = R.copy()
        np.fill_diagonal(reduced, h2)
        values, vectors = np.linalg.eigh(reduced)
        order = np.argsort(values)[::-1]
        values = values[order][:k]
        vectors = vectors[:, order][:, :k]
        L = vectors * np.sqrt(np.maximum(values, 0.0))
        updated = np.clip((L * L).sum(axis=1), 1e-4, 0.999)
        if np.max(np.abs(updated - h2)) < tol:
            h2 = updated
            break
        h2 = updated
    return L, h2


def varimax(L, iterations=200, tol=1e-8):
    p, k = L.shape
    if k == 1:
        return L
    R = np.eye(k)
    rotation = np.eye(k)
    previous = 0.0
    for _ in range(iterations):
        transformed = L @ rotation
        u, s, vh = np.linalg.svd(
            L.T @ (transformed ** 3 - transformed @ np.diag((transformed ** 2).sum(0)) / p)
        )
        rotation = u @ vh
        objective = s.sum()
        if previous and objective / previous < 1 + tol:
            break
        previous = objective
    return L @ rotation


@dataclass
class Fit:
    N: int
    groups: list[list[int]]
    loadings: np.ndarray          # p x N first-order loadings
    gamma: np.ndarray             # N second-order loadings
    theta: np.ndarray             # p uniquenesses
    Fmin: float
    chi2: float
    df: int
    pvalue: float
    cfi: float
    tli: float
    rmsea: float
    aic: float
    bic: float
    n_params: int
    omega_total: float
    omega_h: float
    lam_g: np.ndarray             # p g loadings
    group_loadings: np.ndarray    # p x N orthogonalized group loadings
    sigma: np.ndarray
    standardized_g: np.ndarray
    standardized_group: np.ndarray
    g_variance_share: float
    ecv: float
    residual_rms: float
    boundary: bool
    iterations: int
    gradient_norm: float


def fit_higher_order(R, n, groups):
    """ML higher-order model g -> N group factors -> subtests (simple structure).

    Each subtest loads on exactly one first-order group factor; group factors are
    correlated only through g. Factor variances are fixed to 1; signs are aligned
    so each group's loadings sum positive.
    """
    R = np.asarray(R, dtype=float)
    if R.ndim != 2:
        raise ValueError("R must be a correlation matrix")
    p = R.shape[0]
    N = len(groups)
    if N == 2:
        raise ValueError("two-group hierarchical g is not identified; use N=1 or N>=3")
    if N < 1 or (N > 1 and any(len(group) < 3 for group in groups)):
        raise ValueError("hierarchy requires at least three indicators per group")
    if R.shape != (p, p) or not np.isfinite(R).all() or not np.allclose(R, R.T):
        raise ValueError("R must be a finite symmetric correlation matrix")
    if n < 3 or not np.allclose(np.diag(R), 1) or np.linalg.eigvalsh(R).min() <= 1e-9:
        raise ValueError("R must be positive definite with unit diagonal; no automatic regularization")
    if sorted(i for group in groups for i in group) != list(range(p)):
        raise ValueError("groups must partition variables")
    group_of = np.empty(p, dtype=int)
    for j, group in enumerate(groups):
        group_of[group] = j
    free, n_gamma, n_theta = p, (0 if N == 1 else N), p

    L0, _ = paf(R, N)
    L0 = varimax(L0)
    for j in range(N):
        if L0[:, j].sum() < 0:
            L0[:, j] *= -1

    def unpack(x):
        loadings = np.zeros((p, N))
        for i in range(p):
            loadings[i, group_of[i]] = x[i]
        if N == 1:
            gamma = np.array([1.0])
        else:
            gamma = x[free:free + n_gamma]
        log_theta = x[free + n_gamma:]
        theta = np.exp(log_theta)
        return loadings, gamma, theta

    def implied(loadings, gamma, theta):
        phi = np.outer(gamma, gamma)
        if N > 1:
            phi[np.diag_indices(N)] = 1.0
        return loadings @ phi @ loadings.T + np.diag(theta)

    def objective(x):
        loadings, gamma, theta = unpack(x)
        sigma = implied(loadings, gamma, theta)
        sign, logdet = np.linalg.slogdet(sigma)
        if sign <= 0 or not np.isfinite(logdet):
            return 1e12, np.zeros_like(x)
        try:
            inv = np.linalg.inv(sigma)
        except np.linalg.LinAlgError:
            return 1e12, np.zeros_like(x)
        value = logdet + float(np.trace(R @ inv))
        if not np.isfinite(value):
            return 1e12, np.zeros_like(x)
        phi = np.outer(gamma, gamma)
        np.fill_diagonal(phi, 1.0)
        derivative = inv - inv @ R @ inv
        loading_gradient = 2 * derivative @ loadings @ phi
        gradient = [loading_gradient[np.arange(p), group_of]]
        if N > 1:
            block = loadings.T @ derivative @ loadings
            np.fill_diagonal(block, 0)
            gradient.append(2 * block @ gamma)
        gradient.append(np.diag(derivative) * theta)
        return value, np.concatenate(gradient)

    bounds = [(-3.0, 3.0)] * free
    if N > 1:
        bounds += [(-0.995, 0.995)] * n_gamma
    bounds += [(-9.0, 2.0)] * n_theta

    starts = []
    for gamma_start in ([1.0] if N == 1 else (0.5, 0.8)):
        vals = np.array([L0[i, group_of[i]] for i in range(p)])
        # scale each group so its largest loading is about 0.8
        for j in range(N):
            members = np.array(groups[j])
            top = np.max(np.abs(vals[members])) if len(members) else 0.0
            if top > 1e-9:
                vals[members] *= 0.8 / top
        theta = np.clip(1.0 - vals ** 2, 0.05, 0.95)
        x = [vals]
        if N > 1:
            x.append(np.full(N, gamma_start))
        x.append(np.log(theta))
        starts.append(np.concatenate(x))
    # one neutral start
    vals = np.array([L0[i, group_of[i]] for i in range(p)])
    vals = vals / (np.abs(vals).max() + 1e-9) * 0.7
    x0 = [vals]
    if N > 1:
        x0.append(np.full(N, 0.7))
    x0.append(np.log(np.full(p, 0.3)))
    starts.append(np.concatenate(x0))

    best = None
    for start in starts:
        result = optimize.minimize(
            objective, start, jac=True, method="L-BFGS-B", bounds=bounds,
            options={"maxiter": 4000, "ftol": 1e-10, "gtol": 1e-6},
        )
        if result.success and np.isfinite(result.fun) and (best is None or result.fun < best.fun):
            best = result
    if best is None:
        raise RuntimeError("no ML optimization start converged")
    loadings, gamma, theta = unpack(best.x)
    for j in range(N):
        if loadings[:, j].sum() < 0:
            loadings[:, j] *= -1
            if N > 1:
                gamma[j] *= -1
    if (loadings @ gamma).sum() < 0:
        gamma *= -1
    sigma = implied(loadings, gamma, theta)
    sign, logdet = np.linalg.slogdet(sigma)
    if sign <= 0:
        raise RuntimeError("fitted covariance matrix is not positive definite")
    Fmin = logdet + float(np.trace(R @ np.linalg.inv(sigma))) - \
        np.linalg.slogdet(R)[1] - p
    Fmin = max(Fmin, 0.0)
    n_params = free + n_gamma + n_theta
    df = p * (p + 1) // 2 - n_params
    chi2 = (n - 1) * Fmin
    chi2_null = -(n - 1) * np.linalg.slogdet(R)[1]
    df_null = p * (p - 1) // 2
    cfi = 1 - max(chi2 - df, 0.0) / max(chi2_null - df_null, 1e-12)
    tli = ((chi2_null / df_null) - (chi2 / df)) / ((chi2_null / df_null) - 1.0) \
        if df > 0 and df_null > 0 and math.isfinite(chi2) else np.nan
    rmsea = math.sqrt(max((chi2 - df) / (df * (n - 1)), 0.0)) if df > 0 else np.nan
    pvalue = float(stats.chi2.sf(chi2, df)) if df > 0 else np.nan
    aic = chi2 + 2 * n_params
    bic = chi2 + math.log(n) * n_params

    phi = np.outer(gamma, gamma)
    if N > 1:
        phi[np.diag_indices(N)] = 1.0
    common = loadings @ phi @ loadings.T
    lam_g = loadings @ gamma
    group_loadings = loadings * np.sqrt(np.maximum(1.0 - gamma ** 2, 0.0))
    scale = np.sqrt(np.diag(sigma))
    standardized_g = lam_g / scale
    standardized_group = group_loadings / scale[:, None]
    # Omega is reliability of a unit-weight composite, not a trace variance share.
    composite_variance = float(sigma.sum())
    omega_total = float(common.sum() / composite_variance)
    omega_h = float(lam_g.sum() ** 2 / composite_variance)
    g_variance_share = float(np.mean(standardized_g ** 2))
    ecv = float(np.sum(standardized_g ** 2) / np.sum(np.diag(common) / np.diag(sigma)))
    implied_correlation = sigma / np.outer(scale, scale)
    residual = (R - implied_correlation)[np.triu_indices(p, 1)]
    boundary = any(min(abs(value - lower), abs(value - upper)) < 1e-4
                   for value, (lower, upper) in zip(best.x, bounds))
    return Fit(
        N=N, groups=groups, loadings=loadings, gamma=gamma, theta=theta,
        Fmin=Fmin, chi2=chi2, df=df, pvalue=pvalue, cfi=cfi, tli=tli,
        rmsea=rmsea, aic=aic, bic=bic, n_params=n_params,
        omega_total=omega_total, omega_h=omega_h,
        lam_g=lam_g, group_loadings=group_loadings,
        sigma=sigma, standardized_g=standardized_g, standardized_group=standardized_group,
        g_variance_share=g_variance_share, ecv=ecv, residual_rms=float(np.sqrt(np.mean(residual ** 2))),
        boundary=boundary, iterations=int(best.nit), gradient_norm=float(np.max(np.abs(best.jac))),
    )

def discover_groups(R, N):
    if N == 1:
        return [list(range(R.shape[0]))]
    L, _ = paf(R, N)
    L = varimax(L)
    for j in range(N):
        if L[:, j].sum() < 0:
            L[:, j] *= -1
    assignment = np.argmax(np.abs(L), axis=1)
    groups = [[] for _ in range(N)]
    for i, group in enumerate(assignment):
        groups[group].append(i)
    if any(len(group) < (3 if N >= 3 else 2) for group in groups):
        return None
    return groups


def point_g_scores(Z, R, fit):
    lam = fit.lam_g
    score = Z @ np.linalg.pinv(R) @ lam
    score = (score - score.mean()) / score.std(ddof=1)
    return score


