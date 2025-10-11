from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional, List
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.decomposition import PCA

def winsorize(df: pd.DataFrame, p: float) -> pd.DataFrame:
    if p is None or p <= 0:
        return df.copy()
    lower = df.quantile(p, axis=0)
    upper = df.quantile(1-p, axis=0)
    return df.clip(lower, upper, axis=1)

def correlation_clustering(rets: pd.DataFrame, k: int, method: str = "average") -> List[List[str]]:
    # distance = sqrt(2*(1 - corr))
    corr = rets.corr().fillna(0.0)
    dist = np.sqrt(2*(1 - corr.clip(-1,1)))
    # convert to condensed
    iu = np.triu_indices_from(dist, 1)
    dvec = dist.values[iu]
    Z = linkage(dvec, method=method)
    labels = fcluster(Z, t=k, criterion='maxclust')
    groups = {}
    cols = list(corr.columns)
    for i, lab in enumerate(labels):
        groups.setdefault(lab, []).append(cols[i])
    return list(groups.values())

def pick_medoids(rets: pd.DataFrame, clusters: List[List[str]]) -> List[str]:
    corr = rets.corr().fillna(0.0)
    medoids = []
    for cluster in clusters:
        sub = corr.loc[cluster, cluster]
        # pick the column with highest average corr to others
        avg_corr = sub.mean(axis=1)
        medoids.append(avg_corr.idxmax())
    return medoids

def pca_summary(rets: pd.DataFrame, n_components: int = 5) -> pd.DataFrame:
    X = rets.dropna().values
    pca = PCA(n_components=min(n_components, X.shape[1]))
    pca.fit(X)
    df = pd.DataFrame({
        "component": [f"PC{i+1}" for i in range(pca.n_components_)],
        "explained_variance_ratio": pca.explained_variance_ratio_
    })
    return df

def simple_regime_marks(series: pd.Series, min_len: int = 24) -> pd.Series:
    # Placeholder: rolling median change-point heuristic
    # Output: a series with regime ids
    x = series.dropna()
    if len(x) < 2*min_len:
        return pd.Series(index=series.index, data=1)
    # crude split at rolling median change
    mid = len(x)//2
    marks = pd.Series(index=series.index, data=1)
    marks.loc[x.index[mid:]] = 2
    return marks
