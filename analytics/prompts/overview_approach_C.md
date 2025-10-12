# Bayesian RBSA with Dirichlet-Spike Prior

## Overview

Approach C implements a Bayesian variant of Returns-Based Style Analysis that simultaneously performs variable selection and weight estimation using Markov Chain Monte Carlo (MCMC) sampling. This approach provides uncertainty quantification through posterior distributions and automatically identifies which assets are relevant for explaining fund returns.

## Motivation

Traditional RBSA methods (like stepwise selection or ElasticNet) provide point estimates of weights but don't naturally quantify uncertainty. The Bayesian approach offers:

1. **Probabilistic variable selection**: Each asset gets a posterior inclusion probability (PIP) indicating how confident we are it should be included
2. **Uncertainty quantification**: Full posterior distributions for weights with credible intervals
3. **Principled regularization**: Priors encode domain knowledge (e.g., weights sum to 1, sparsity is preferred)
4. **Model averaging**: Marginalizes over uncertainty about which assets to include

## Model Specification

### Likelihood

The standard RBSA linear model:

```
y_t = Σ w_j * X_j,t + ε_t
```

where:
- `y_t` = fund excess return at time t
- `X_j,t` = excess return for asset j at time t
- `w_j` = portfolio weight on asset j
- `ε_t ~ N(0, σ²)` = tracking error

### Prior Structure

**1. Dirichlet Prior on Weights**

```
w | γ ~ Dirichlet(α)
```

Where:
- `α = [1, 1, ..., 1]` (uniform Dirichlet)
- Enforces `Σ w_j = 1` and `w_j ≥ 0` (simplex constraint)
- Corresponds to long-only portfolio constraints

**2. Spike-and-Slab for Variable Selection**

```
γ_j ~ Bernoulli(π)
```

Where:
- `γ_j ∈ {0, 1}` is an inclusion indicator for asset j
- `γ_j = 1`: asset j is "active" (in the model)
- `γ_j = 0`: asset j has weight forced to zero
- `π = 0.3`: prior probability each asset is included (encodes sparsity preference)

If `γ_j = 0`, then `w_j = 0` and the weight is redistributed among active assets.

**3. Error Variance Prior**

```
σ² ~ Inverse-Gamma(α=2, β=0.01)
```

Weakly informative prior on tracking error variance.

### Posterior Distribution

The target posterior is:

```
P(w, γ, σ² | y, X) ∝ P(y | X, w, σ²) × P(w | γ) × P(γ) × P(σ²)
```

This posterior cannot be computed analytically due to the discrete γ variables and simplex constraint on w, so we use MCMC sampling.

## MCMC Sampling Algorithm

### Three-Step Gibbs/Metropolis-Hastings Sampler

**Step 1: Update Inclusion Indicators γ (Gibbs Sampling)**

For each asset j:
1. Compute likelihood ratio for including vs excluding asset j:
   ```
   log_odds = log(P(y | γ_j=1)) - log(P(y | γ_j=0)) + log(π/(1-π))
   ```
2. Convert to posterior probability:
   ```
   P(γ_j=1 | rest) = 1 / (1 + exp(-log_odds))
   ```
3. Sample `γ_j ~ Bernoulli(P(γ_j=1 | rest))`

**Step 2: Update Weights w | γ (Metropolis-Hastings on Simplex)**

Only update weights for active assets (where γ_j = 1):
1. Propose new weights via Dirichlet perturbation:
   ```
   w_prop ~ Dirichlet(w_current × 100 + 0.1)
   ```
   This concentrates proposals near current values for efficient exploration.

2. Compute acceptance ratio:
   ```
   α = min(1, P(y | w_prop) / P(y | w_current))
   ```

3. Accept proposal with probability α, otherwise keep current weights

**Step 3: Update Error Variance σ² (Gibbs Sampling)**

Conjugate Inverse-Gamma update:
```
σ² | y, w ~ Inverse-Gamma(α_post, β_post)

where:
  α_post = α_prior + n/2
  β_post = β_prior + SSE/2
  SSE = Σ(y_t - X_t · w)²
```

### Burn-in and Convergence

- **Total samples**: 5000 (default)
- **Burn-in**: 1000 samples discarded (chain convergence period)
- **Retained samples**: 4000 used for posterior inference

## Output and Interpretation

### Posterior Inclusion Probability (PIP)

```
PIP_j = P(γ_j = 1 | y, X) = (# samples with γ_j=1) / (total samples)
```

**Interpretation:**
- PIP ≈ 1.0: Strong evidence asset is relevant
- PIP ≈ 0.5: Uncertain (model can't decide)
- PIP ≈ 0.0: Strong evidence asset is irrelevant

**Selection threshold**: Assets with PIP ≥ 0.5 are included in final model (configurable)

### Posterior Weight Distributions

For each asset j, we have 4000 posterior samples of its weight. This provides:

- **Posterior mean**: `E[w_j | y, X]` (point estimate)
- **Posterior standard deviation**: `SD[w_j | y, X]` (uncertainty measure)
- **95% credible interval**: `[Q_0.025, Q_0.975]` (likely range of true weight)

**Note**: These are marginal distributions averaging over all possible models (values of γ).

### Final Model

After MCMC:
1. Select assets with PIP ≥ threshold
2. Refit using constrained NNLS (non-negative least squares with sum-to-one constraint)
3. This gives point estimates comparable to other approaches while leveraging Bayesian variable selection

## Implementation Details

### Configuration Parameters

From `config.yaml`:
```yaml
approach_C:
  mcmc_samples: 5000        # Total MCMC iterations
  mcmc_burnin: 1000         # Burn-in samples to discard
  pip_threshold: 0.5        # Threshold for including assets
```

### Code Location

- **Implementation**: `rbsa/models/approach_c.py`
- **Function**: `dirichlet_spike_slab_mcmc()`
- **Pipeline**: `approach_C_pipeline()`

### Key Hyperparameters

| Parameter | Value | Interpretation |
|-----------|-------|----------------|
| `alpha_dir` | `[1, 1, ..., 1]` | Uniform Dirichlet (no weight bias) |
| `prior_inclusion` | 0.3 | Expect ~30% of assets to be relevant |
| `sigma2_prior_shape` | 2.0 | Weak prior on error variance |
| `sigma2_prior_scale` | 0.01 | Small baseline tracking error |

### Numerical Stability

The code includes several numerical safeguards:

1. **Log-sum-exp trick** for computing posterior odds (lines 81-91)
2. **Probability clipping** to [0, 1] range (line 94)
3. **Renormalization** when excluding assets (lines 72-73)
4. **Fallback sampling** if no assets selected (lines 121-123)

## Advantages

1. **Automatic variable selection**: No need for separate selection + estimation steps
2. **Uncertainty quantification**: Get credible intervals on weights, not just point estimates
3. **Model averaging**: PIP marginalizes over model uncertainty
4. **Theoretically principled**: Based on probability theory, not heuristics
5. **Flexible priors**: Can encode domain knowledge (e.g., sparsity, weight bounds)

## Disadvantages

1. **Computational cost**: MCMC requires thousands of iterations (~10-30 seconds)
2. **Tuning required**: Burn-in length, proposal distributions need calibration
3. **Convergence diagnostics**: Should check trace plots, effective sample size (not currently implemented)
4. **Point estimates**: Final model still uses NNLS refit, not full Bayesian weights
5. **Simplex sampling**: Metropolis-Hastings on constrained space can be slow to mix

## Comparison with Other Approaches

| Feature | Approach A (Stepwise) | Approach B (ElasticNet) | Approach C (Bayesian) |
|---------|----------------------|------------------------|----------------------|
| Variable selection | Greedy forward | L1 regularization | Probabilistic (PIP) |
| Uncertainty | None | None (bootstrap possible) | Full posterior |
| Sparsity control | max_k parameter | α parameter | Prior inclusion prob |
| Computation | Fast (seconds) | Fast (seconds) | Slow (10-30 sec) |
| Interpretability | Simple | Moderate | Complex |
| Constraint handling | Native | Refit after selection | Native (Dirichlet) |

## When to Use Approach C

**Use Bayesian RBSA when:**
- Uncertainty quantification is important (e.g., risk reporting, audits)
- Dataset is noisy or small (posterior averaging helps)
- You want probabilistic statements ("80% confident weight > 0.2")
- Variable selection is uncertain (multiple models fit similarly)

**Use other approaches when:**
- Speed is critical (production systems)
- Point estimates are sufficient
- Simpler explanations are needed for stakeholders

## Example Output

From a typical run:

```
Posterior Inclusion Probabilities (PIP):
asset     PIP  mean_weight  std_weight
  AGG 1.00000     0.171665    0.030327
  HYG 1.00000     0.302969    0.042649
  IWD 1.00000     0.237538    0.033373
  IWF 1.00000     0.284245    0.030295
  BIL 0.32400     0.001224    0.006323
  ...

Selected assets (PIP >= 0.5): AGG, HYG, IWD, IWF

Final NNLS weights (PIP >= 0.5):
  HYG: 0.3033 (PIP=1.000)
  IWF: 0.2817 (PIP=1.000)
  IWD: 0.2413 (PIP=1.000)
  AGG: 0.1737 (PIP=1.000)
```

**Interpretation**: Four assets have PIP = 1.0 (selected in 100% of MCMC samples), indicating strong evidence they explain the fund. BIL has PIP = 0.32, indicating marginal relevance (included in only 32% of models).

## References

- George, E. I., & McCulloch, R. E. (1993). "Variable selection via Gibbs sampling." *Journal of the American Statistical Association*.
- Polson, N. G., & Scott, J. G. (2011). "Shrink globally, act locally: Sparse Bayesian regularization and prediction." *Bayesian Statistics*.
- Aitchison, J. (1986). *The Statistical Analysis of Compositional Data*. Chapman & Hall. (Dirichlet distributions)

## Future Enhancements

Potential improvements not yet implemented:

1. **Convergence diagnostics**: Gelman-Rubin R̂, effective sample size
2. **Multiple chains**: Run parallel chains to assess convergence
3. **Adaptive proposals**: Tune Metropolis-Hastings acceptance rate during burn-in
4. **Hierarchical priors**: Learn optimal prior_inclusion from data
5. **Time-varying weights**: Extend to dynamic Bayesian RBSA
