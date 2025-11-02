# Cluster-then-Span (Approach D)

## Overview

Cluster-then-Span is a factor selection methodology that groups similar assets into clusters first, then selects representative assets to "span" the investment universe. This approach reduces redundancy and multicollinearity while maintaining explanatory power.

---

## The Procedure

### Step 1: Cluster Assets by Correlation

Group factor assets based on their return correlations using **hierarchical agglomerative clustering**.

**Distance Metric:**
```python
corr = returns.corr()
distance = sqrt(2 * (1 - correlation))
```

- High correlation → small distance (assets grouped together)
- Low/negative correlation → large distance (assets in separate clusters)

**Clustering Algorithm:**
- **Method**: Hierarchical agglomerative clustering (scipy `linkage`)
- **Linkage**: Average linkage (configurable via `approach_D.linkage` in config)
- **Number of clusters**: Tests k from `cluster_k_min` to `cluster_k_max`

**Example Clusters:**
- **US Large Cap Equity**: IWF, IWD, SPY, IWB
- **US Small Cap**: IWM, IWO, IWN
- **International Equity**: EFA, EEM
- **Fixed Income**: AGG, IEF, LQD, TIP
- **Alternatives**: DBC, VNQI

---

### Step 2: Select Representative Assets (Medoids)

From each cluster, select the single asset that best represents that cluster.

**Selection Method: Medoid Selection**
- For each cluster, compute the average correlation of each asset to all others in the cluster
- Select the asset with the **highest average correlation** (most "central" asset)
- This is the **medoid** - the actual data point closest to the cluster center

**Why Medoids?**
- Always selects a real asset (not a synthetic combination)
- Most representative of the cluster's behavior
- Reduces within-cluster redundancy

---

### Step 3: Span with Selected Representatives

Run constrained RBSA (Approach A) using only the selected representative assets.

**Process:**
1. Iterate through different values of k (number of clusters)
2. For each k:
   - Cluster assets into k groups
   - Pick k medoids (one per cluster)
   - Run Approach A (constrained optimization) with these k assets
   - Record RMSE
3. Select the k that produces the **lowest RMSE**

**Result:**
- Parsimonious asset selection (one per cluster)
- Reduced multicollinearity
- Interpretable factor exposures

---

## Implementation Details

### Configuration Parameters

From `config.yaml`:
```yaml
approach_D:
  linkage: "average"        # Linkage method: average, ward, single, complete
  cluster_k_min: 3          # Minimum number of clusters to test
  cluster_k_max: 8          # Maximum number of clusters to test
```

### Code Flow

```python
def approach_D_pipeline(X, y, cfg):
    best = None
    for k in range(cfg["approach_D"]["cluster_k_min"],
                   cfg["approach_D"]["cluster_k_max"]+1):
        # Step 1: Cluster assets
        clusters = correlation_clustering(X, k=k, method=cfg["approach_D"]["linkage"])

        # Step 2: Pick medoids
        medoids = pick_medoids(X, clusters)

        # Step 3: Span with selected assets
        res = approach_A_pipeline(X[medoids], y, cfg)

        # Track best k
        if best is None or res["diagnostics"]["rmse"] < best["diagnostics"]["rmse"]:
            best = res

    return best
```

### Distance Formula Derivation

The correlation-to-distance conversion uses:
```
distance = sqrt(2 * (1 - correlation))
```

**Properties:**
- `corr = 1.0` → `dist = 0.0` (perfectly correlated, no distance)
- `corr = 0.0` → `dist = sqrt(2) ≈ 1.41` (uncorrelated)
- `corr = -1.0` → `dist = 2.0` (perfectly negatively correlated, max distance)

This is a standard metric for converting correlation matrices to distance matrices for clustering.

---

## Advantages

1. **Reduces Multicollinearity**
   - Similar assets don't compete in the same model
   - Only one representative per correlation cluster

2. **Parsimony**
   - Fewer assets needed to explain returns
   - Simpler, more interpretable models

3. **Factor Coverage**
   - Representatives "span" the full factor space
   - No major factor groups omitted

4. **Robustness**
   - Less prone to overfitting than unconstrained selection
   - Correlation structure guides selection before optimization

5. **Interpretability**
   - Clear factor exposures (one representative per group)
   - Easy to explain: "US equity via IWB, credit via LQD, etc."

---

## Disadvantages

1. **Pre-commits to Clustering**
   - Asset groupings determined before optimization
   - May miss optimal combinations that cross clusters

2. **K Selection**
   - Requires testing multiple k values
   - Optimal k may vary over time (regime-dependent)

3. **Correlation-Based Only**
   - Clusters based on correlation, not economic interpretation
   - May group assets for statistical rather than fundamental reasons

4. **Medoid Sensitivity**
   - Representative selection sensitive to correlation estimation
   - Short sample periods may produce unstable medoids

---

## Comparison to Other Approaches

| Approach | Method | Asset Selection | Multicollinearity Handling |
|----------|--------|-----------------|----------------------------|
| **A (Constrained)** | Optimization with parsimony penalty | Simultaneously | Penalty for extra assets |
| **B (Elastic Net)** | Regularized regression | Automatically via L1/L2 | Elastic Net shrinkage |
| **C (Bayesian)** | Probabilistic (Dirichlet-spike prior) | Posterior inclusion prob | Spike prior for sparsity |
| **D (Cluster-Span)** | Hierarchical clustering + optimization | Two-stage: cluster, then optimize | **Pre-groups similar assets** |

**Key Distinction:** Approach D is the only method that uses asset correlation structure to **pre-filter** candidates before optimization.

---

## When to Use Approach D

**Best suited for:**
- Large factor universes with known redundancy (e.g., multiple overlapping ETFs)
- Investors who want explicit factor diversification
- Situations where interpretability matters (one representative per factor group)
- When multicollinearity is a known problem in other approaches

**Less suitable for:**
- Small universes where clustering provides little benefit
- When optimal combination requires multiple assets from same cluster
- High-frequency or regime-shifting data (clusters may be unstable)

---

## References

- **Hierarchical Clustering**: scipy.cluster.hierarchy.linkage
- **Distance Metric**: Standard correlation-to-distance conversion
- **Medoid Selection**: Maximizes average within-cluster correlation

---

## Example Output

For a 14-asset universe, Approach D might:
1. Test k = 3, 4, 5, 6, 7, 8 clusters
2. Find k = 5 produces lowest RMSE
3. Select 5 medoids representing:
   - US Equity (IWB)
   - International (EFA)
   - Fixed Income (AGG)
   - Credit (HYG)
   - Alternatives (DBC)
4. Run constrained optimization with these 5 assets

**Result**: Simple, interpretable model with one representative per major factor group.
