from __future__ import annotations
import numpy as np
from typing import Tuple, Optional, Callable
from scipy.optimize import minimize

def nnls_simplex(X: np.ndarray, y: np.ndarray, sum_to_one: bool = True, tol: float = 1e-9) -> np.ndarray:
    n = X.shape[1]
    w0 = np.ones(n)/n
    bounds = [(0.0, None) for _ in range(n)]
    constraints = []
    if sum_to_one:
        constraints.append({'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0})
    # objective
    def obj(w):
        r = y - X.dot(w)
        return 0.5*np.dot(r, r)
    res = minimize(obj, w0, method='SLSQP', bounds=bounds, constraints=constraints, options={'ftol': tol, 'maxiter': 1000})
    if not res.success:
        # fallback: project nonneg and renormalize
        w = np.clip(w0, 0, None)
        s = w.sum()
        return w/s if sum_to_one and s>0 else w
    w = np.clip(res.x, 0, None)
    if sum_to_one and w.sum() > 0:
        w = w / w.sum()
    return w
