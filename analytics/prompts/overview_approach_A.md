# NNLS

## Overview

Approach A implements NNLS

The procedure uses stepwise_nnls which adds variables until benefit is below threshold.

Pseudo-code
```python
    cols = stepwise_nnls(X, y, max_k=max_k, sum_to_one=sum_to_one, eps_rmse=eps, mode=mode)
    result = fit_one(X, y, cols, sum_to_one=sum_to_one)
```

## Motivation

In returns-based style analysis (RBSA), using iterative NNLS helps estimate the combination of style or factor indexes (e.g., equity, bond, or sector indexes) that best replicate a fund’s return pattern under non-negative and sum-to-one constraints.

When adding new spanning indexes, iterative NNLS offers practical advantages:

## Role in RBSA

Iterative NNLS recalculates weights by repeatedly solving the constrained regression as new indexes are added, ensuring that all weights remain non-negative and that only the most explanatory indexes receive positive allocations. This mimics portfolio-style composition while maintaining interpretability.

## Advantages

-	Adaptive inclusion: Iteratively adjusts weights to reflect newly added indexes without restarting from scratch.
-	Economic interpretability: Keeps weights non-negative, so new indexes represent additive exposures rather than offsets.
-	Stability: Avoids abrupt jumps in weights that can occur with unconstrained or fully re-estimated models.
-	Scalable updating: Suitable for expanding index sets over time as market benchmarks evolve.

## Disadvantages

-	Path dependence: The order or timing of index additions can affect the final solution slightly.
-	No shrinkage control: Does not penalize overfitting; adding too many indexes can dilute explanatory power.

