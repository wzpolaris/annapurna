"""Factor construction utilities for the unified privates model.

This module provides helpers to build the four core factors:

- SC     : small-cap equity return series
- CS     : credit spread factor (HY vs Treasuries)
- INNOV  : innovation / tech cycle factor
- TAIL   : tail-risk factor based on positive ΔVIX

The functions are written to be usable with either real market data
or synthetic / test data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

try:
    import yfinance as yf  # Optional; can be disabled in offline environments
except Exception:  # pragma: no cover
    yf = None


def download_prices(tickers, start="2000-01-01", end=None) -> pd.DataFrame:
    """Download adjusted close prices via yfinance.

    Parameters
    ----------
    tickers : list[str]
        Tickers to download (e.g. ["IWM", "HYG", "IEF", "QQQ", "^VIX"]).
    start : str
        Start date (YYYY-MM-DD).
    end : str or None
        End date (YYYY-MM-DD). If None, uses latest.

    Returns
    -------
    pd.DataFrame
        Adjusted close prices with datetime index and tickers as columns.
    """
    if yf is None:
        raise RuntimeError("yfinance is not available; install yfinance or provide your own price data.")
    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    # yfinance returns multiindex; we keep 'Adj Close' level
    if isinstance(data.columns, pd.MultiIndex):
        #data = data['Adj Close']
        data = data['Close']
    return data


def to_returns(prices: pd.DataFrame, freq: str = "M") -> pd.DataFrame:
    """Convert price series to log-returns aggregated at the given frequency."""
    logp = np.log(prices).dropna()
    logp = logp.resample(freq).last()
    rets = logp.diff().dropna()
    return rets


def build_sc_factor(returns: pd.DataFrame, sc_ticker: str = "IWM") -> pd.Series:
    """Extract SC factor from returns.

    Parameters
    ----------
    returns : DataFrame
        DataFrame of log-returns.
    sc_ticker : str
        Column name to use as SC.

    Returns
    -------
    Series
        Small-cap factor series.
    """
    sc = returns[sc_ticker].copy()
    sc.name = "SC"
    return sc


def build_spread_factor(hy_ret: pd.Series, gov_ret: pd.Series) -> pd.Series:
    """Construct credit spread factor as HY residual vs Treasuries.

    CS_t is the residual from regressing HY on Gov:

        HY_t = a + phi * Gov_t + e_t
        CS_t = e_t

    Parameters
    ----------
    hy_ret : Series
        HY ETF returns (e.g. HYG).
    gov_ret : Series
        Treasury ETF returns (e.g. IEF).

    Returns
    -------
    Series
        Credit spread factor CS_t.
    """
    df = pd.concat([hy_ret, gov_ret], axis=1).dropna()
    df.columns = ["HY", "GOV"]
    y = df["HY"].values
    x = df["GOV"].values
    X = np.vstack([np.ones_like(x), x]).T
    a, phi = np.linalg.lstsq(X, y, rcond=None)[0]
    cs = df["HY"] - (a + phi * df["GOV"])
    cs.name = "CS"
    return cs.reindex(hy_ret.index)


def build_innovation_factor(ndq_ret: pd.Series, sc_ret: pd.Series, ma_window: int = 6) -> pd.Series:
    """Build innovation factor as a moving average of NDQ minus small-cap.

    INNOV_t = MA_{ma_window}( r_NDQ_t - r_SC_t )

    Parameters
    ----------
    ndq_ret : Series
        Nasdaq (or Nasdaq 100) return series (e.g. QQQ).
    sc_ret : Series
        Small-cap return series (SC).
    ma_window : int
        Moving average window (in periods).

    Returns
    -------
    Series
        Innovation factor series.
    """
    aligned = pd.concat([ndq_ret, sc_ret], axis=1).dropna()
    aligned.columns = ["NDQ", "SC"]
    diff = aligned["NDQ"] - aligned["SC"]
    innov = diff.rolling(ma_window).mean()
    innov.name = "INNOV"
    return innov.reindex(sc_ret.index)


def build_tail_factor(delta_vix: pd.Series, window: int = 60) -> pd.Series:
    """Build tail factor from changes in VIX.

    Steps:
    1. Compute rolling mean and std of ΔVIX.
    2. Form z-score: z_t = (ΔVIX_t - mu_t) / sigma_t.
    3. Take positive part: z_t^+ = max(z_t, 0).
    4. Tail factor: TAIL_t = log(1 + z_t^+).

    Parameters
    ----------
    delta_vix : Series
        Changes in VIX (e.g. daily or monthly).
    window : int
        Rolling window length for mean/std.

    Returns
    -------
    Series
        Tail factor TAIL_t.
    """
    dv = delta_vix.dropna()
    mu = dv.rolling(window).mean()
    sigma = dv.rolling(window).std()
    z = (dv - mu) / sigma
    z_pos = z.clip(lower=0.0)
    tail = np.log1p(z_pos)
    tail.name = "TAIL"
    return tail.reindex(delta_vix.index)
