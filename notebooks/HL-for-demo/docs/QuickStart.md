# Quick Start (Extended)

Key pieces:

- `src/` – factor construction, unified model, Monte Carlo, and fund overlays.
- `whitepaper/` – multi-file markdown whitepaper describing the theory and design.
- `notebooks/` – worked examples.

Recommended workflow:

1. **Build real factors**:  
   Open `notebooks/03_real_data_factors.ipynb` and run it with internet access enabled
   to download IWM, HYG, IEF, QQQ, and VIX via yfinance and construct SC, CS, INNOV, and TAIL.

2. **Inspect structural betas and factor-implied returns**:  
   Use `notebooks/01_build_factors_and_structural_betas.ipynb` but swap synthetic factors
   for the real ones you built in step 1.

3. **Apply fund-specific overlays** (strategy mix, sector, geography, investment type):  
   See `notebooks/05_fund_overlays.ipynb` and map your fund's characteristics to overlay parameters.

4. **Run Monte Carlo and compute VaR/CVaR**:  
   Use `notebooks/02_monte_carlo_risk.ipynb` and `notebooks/04_var_cvar_plots.ipynb` to simulate paths
   and visualise risk distributions for Buyout and VC (or any custom overlay betas).

5. **Integrate into your asset-allocation stack**:  
   Use the factor covariance, structural or blended betas, and simulated return distributions
   to compare Buyout and VC risk vs public equity and to feed a Black–Litterman engine.
