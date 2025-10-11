from __future__ import annotations
import numpy as np
import pandas as pd
from typing import Tuple, Dict, Any, List
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.stats.stattools import durbin_watson
from statsmodels.regression.linear_model import yule_walker

def rolling_origin_splits(dates: pd.DatetimeIndex, window: int, horizon: int):
    # yields (train_idx, test_idx)
    for start in range(0, len(dates) - (window + horizon) + 1):
        train = dates[start:start+window]
        test = dates[start+window:start+window+horizon]
        yield train, test

def hac_se(X: np.ndarray, resid: np.ndarray, lag: int = 6):
    # Placeholder: return simple homoskedastic SE vector of zeros (to avoid heavy deps).
    # In the notebook we can compute robust errors if desired.
    return np.zeros(X.shape[1])

def model_diagnostics(y: pd.Series, yhat: pd.Series, resid: pd.Series, k: int = None) -> Dict[str, Any]:
    """
    Calculate comprehensive model diagnostics including information criteria.

    Args:
        y: Actual values
        yhat: Predicted values
        resid: Residuals
        k: Number of parameters (assets). If None, inferred from context.

    Returns:
        Dict with RMSE, MAE, R², Adjusted R², AIC, AICc, BIC, and diagnostic tests
    """
    n = len(y)
    rmse = float(np.sqrt(np.mean((y - yhat)**2)))
    mae  = float(np.mean(np.abs(y - yhat)))

    # Calculate R²
    ss_res = np.sum(resid**2)
    ss_tot = np.sum((y - y.mean())**2)
    r2 = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0

    # Calculate Adjusted R² if k is provided
    adj_r2 = r2
    if k is not None and n > k + 1:
        adj_r2 = float(1 - (1 - r2) * (n - 1) / (n - k - 1))

    # Calculate information criteria
    # Note: These are computed for constrained regression (non-negative, sum-to-one)
    # Relative comparisons are valid, but absolute values should be interpreted cautiously
    aic = np.nan
    aicc = np.nan
    bic = np.nan

    if k is not None and k > 0 and ss_res > 0:
        # Log-likelihood for normal errors (up to constant)
        log_likelihood = -0.5 * n * (np.log(2 * np.pi) + np.log(ss_res / n) + 1)

        # AIC = 2k - 2ln(L)
        aic = float(2 * k - 2 * log_likelihood)

        # AICc (corrected AIC for small samples)
        # AICc = AIC + 2k(k+1)/(n-k-1)
        if n > k + 1:
            aicc = float(aic + (2 * k * (k + 1)) / (n - k - 1))
        else:
            aicc = np.inf  # Undefined when n <= k+1

        # BIC = k*ln(n) - 2ln(L)
        bic = float(k * np.log(n) - 2 * log_likelihood)

    # Diagnostic tests
    dw = float(durbin_watson(resid))
    lb = acorr_ljungbox(resid, lags=[6], return_df=True).iloc[0,0]

    return {
        "rmse": rmse,
        "mae": mae,
        "r2": r2,
        "adj_r2": adj_r2,
        "aic": aic,
        "aicc": aicc,
        "bic": bic,
        "dw": dw,
        "ljungbox_stat_lag6": float(lb),
        "n_obs": n,
        "n_params": k if k is not None else np.nan
    }

def composite_score(metrics: Dict[str, float], weights: Dict[str, int]) -> float:
    # Lower-is-better for rmse/mae; assume inputs already normalized if needed
    score = 0.0
    for k, w in weights.items():
        v = metrics.get(k, 0.0)
        score += w * v
    return score


def calculate_composite_score(diagnostics: Dict[str, Any], n_obs: int) -> Dict[str, float]:
    """
    Calculate composite model selection score.

    Combines multiple criteria with automatic weighting based on sample size.
    For small samples (n < 60), emphasizes AICc. For large samples, emphasizes BIC.

    Args:
        diagnostics: Model diagnostics dict
        n_obs: Number of observations

    Returns:
        Dict with individual normalized scores and composite score
    """
    # Extract metrics
    r2 = diagnostics.get("r2", 0)
    adj_r2 = diagnostics.get("adj_r2", 0)
    aicc = diagnostics.get("aicc", np.inf)
    bic = diagnostics.get("bic", np.inf)

    # Normalize to [0, 1] scale where 1 is best
    # R² and Adj-R² are already in [0, 1] with higher = better
    r2_score = r2
    adj_r2_score = adj_r2

    # For AICc and BIC, we'll normalize relative to a baseline
    # (This requires comparing across candidates, so we'll do percentage contribution)
    # For now, use direct values (will be normalized in ranking function)
    aicc_score = -aicc if not np.isnan(aicc) and not np.isinf(aicc) else -np.inf
    bic_score = -bic if not np.isnan(bic) and not np.isinf(bic) else -np.inf

    # Sample-size dependent weighting
    if n_obs < 60:
        # Small sample: prioritize AICc and Adj-R²
        weights = {
            "r2": 0.15,
            "adj_r2": 0.35,
            "aicc": 0.40,
            "bic": 0.10
        }
    else:
        # Large sample: prioritize BIC and Adj-R²
        weights = {
            "r2": 0.10,
            "adj_r2": 0.30,
            "aicc": 0.20,
            "bic": 0.40
        }

    # Calculate weighted composite (before normalization, higher is better)
    composite = (
        weights["r2"] * r2_score +
        weights["adj_r2"] * adj_r2_score +
        weights["aicc"] * aicc_score +
        weights["bic"] * bic_score
    )

    return {
        "r2_score": r2_score,
        "adj_r2_score": adj_r2_score,
        "aicc_score": aicc_score,
        "bic_score": bic_score,
        "composite_raw": composite,
        "weights_used": weights
    }

# Summarization wrapper (OpenAI-or-offline)
class Summarizer:
    def __init__(self, backend: str, model: str, temperature: float, system_prompt: str):
        self.backend = backend
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt

        # Load environment variables if using OpenAI
        if self.backend.lower() == "openai":
            self._load_env()

    def _load_env(self):
        """Load environment variables from .env file."""
        try:
            from dotenv import load_dotenv
            import os

            # Load .env from project root
            load_dotenv()

            # Verify API key is loaded
            if not os.getenv("OPENAI_API_KEY"):
                print("Warning: OPENAI_API_KEY not found in environment")
        except ImportError:
            print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")
        except Exception as e:
            print(f"Warning: Could not load .env file: {e}")

    def summarize(self, text: str) -> str:
        if self.backend.lower() != "openai":
            # offline fallback: simple heuristic
            lines = text.strip().splitlines()
            head = lines[:5]
            return "Offline summary: " + " ".join([l.strip() for l in head])[:500]
        # If 'openai', attempt to call; user must configure OPENAI_API_KEY and install openai
        try:
            from openai import OpenAI
            client = OpenAI()  # Automatically reads OPENAI_API_KEY from environment

            # Check if using GPT-5 (new Responses API) or GPT-4 (Chat Completions API)
            if self.model.startswith("gpt-5"):
                # GPT-5 uses the new Responses API
                prompt = f"{self.system_prompt}\n\n{text[:8000]}"
                resp = client.responses.create(
                    model=self.model,
                    input=prompt,
                    reasoning={"effort": "medium"},
                    text={"verbosity": "medium"}
                )
                return resp.output_text.strip()
            else:
                # GPT-4 and earlier use Chat Completions API
                resp = client.chat.completions.create(
                    model=self.model,
                    temperature=self.temperature,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": text[:8000]},
                    ],
                )
                return resp.choices[0].message.content.strip()
        except Exception as e:
            return f"OpenAI call failed: {str(e)}\n\nFalling back to offline mode."
