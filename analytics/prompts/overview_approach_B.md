
# Elastic Net

## Overview

Elastic Net is a regularized regression method that combines the penalties of ridge regression (L2) and lasso regression (L1). It’s controlled by a mixing parameter α (alpha) ranging from 0 to 1:
- When α = 0, Elastic Net becomes ridge regression, which shrinks coefficients toward zero but never makes them exactly zero.
- When α = 1, it becomes lasso regression, which can set some coefficients exactly to zero, performing variable selection.

## Advantages
- Balances bias and sparsity: Combines ridge’s stability with lasso’s feature selection, useful when predictors are highly correlated.
- Handles multicollinearity well: Ridge component stabilizes solutions when predictors are correlated.
- Selects groups of correlated variables: Lasso tends to pick one variable per group, but Elastic Net can retain related predictors together.

## Disadvantages
- Extra tuning complexity: Requires optimizing both α and the regularization strength λ.
- Less interpretability than lasso: Coefficients are not as sparse when α < 1.
- Performance sensitivity: Can underperform if α and λ are not well tuned for the dataset.