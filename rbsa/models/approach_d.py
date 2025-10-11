from __future__ import annotations
import pandas as pd
from typing import Dict, Any, List
from ..prelim import correlation_clustering, pick_medoids
from .approach_a import approach_A_pipeline

def approach_D_pipeline(X: pd.DataFrame, y: pd.Series, cfg: Dict[str, Any]) -> Dict[str, Any]:
    best = None
    for k in range(cfg["approach_D"]["cluster_k_min"], cfg["approach_D"]["cluster_k_max"]+1):
        clusters = correlation_clustering(X, k=k, method=cfg["approach_D"]["linkage"])
        medoids = pick_medoids(X, clusters)
        res = approach_A_pipeline(X[medoids], y, cfg)
        res["medoids_k"] = k
        if best is None or res["diagnostics"]["rmse"] < best["diagnostics"]["rmse"]:
            best = res
    return best
