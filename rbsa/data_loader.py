from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import yfinance as yf

def load_fund_returns(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["date"])
    df = df.sort_values("date").reset_index(drop=True)
    return df

def load_portfolio(csv_path: str) -> pd.DataFrame:
    """Load portfolio with ticker and weight columns."""
    df = pd.read_csv(csv_path)
    # Clean up column names (remove spaces)
    df.columns = df.columns.str.strip()
    # Clean up ticker and weight values
    df['ticker'] = df['ticker'].str.strip()
    df['wt'] = pd.to_numeric(df['wt'].astype(str).str.strip())
    return df

def download_prices(tickers, start: str, end: Optional[str] = None) -> pd.DataFrame:
    df = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    data = df['Close']
    if isinstance(data, pd.Series):
        data = data.to_frame()
    data = data.sort_index()
    return data

def to_monthly_returns(price_df: pd.DataFrame, freq: str = "ME") -> pd.DataFrame:
    px = price_df.resample(freq).last()
    rets = px.pct_change().dropna(how="all")
    return rets

def align_and_merge(fund_df: pd.DataFrame, index_rets: pd.DataFrame, rf_series: pd.Series | None) -> Tuple[pd.Series, pd.DataFrame, pd.Series | None]:
    fund = fund_df.copy()
    fund = fund.set_index("date").sort_index()
    # Align monthly
    fund = fund.resample("ME").last()
    # Align indices
    common_idx = fund.index.intersection(index_rets.index)
    fund = fund.loc[common_idx]
    X = index_rets.loc[common_idx].copy()
    rf = None
    if rf_series is not None:
        rf = rf_series.reindex(common_idx)
    return fund["fund_return"], X, rf

def compute_excess(returns: pd.DataFrame, rf: pd.Series | None) -> pd.DataFrame:
    if rf is None:
        return returns
    return returns.sub(rf, axis=0)

def compute_portfolio_returns(portfolio_df: pd.DataFrame, start: str, end: Optional[str], freq: str = "ME") -> pd.Series:
    """
    Download prices for portfolio tickers and compute weighted monthly returns.

    Args:
        portfolio_df: DataFrame with 'ticker' and 'wt' columns
        start: Start date for price download
        end: End date for price download
        freq: Frequency for resampling (default 'ME' for month-end)

    Returns:
        Series of portfolio weighted returns indexed by date
    """
    tickers = portfolio_df['ticker'].tolist()
    weights = portfolio_df['wt'].values

    # Validate weights sum to 1
    weight_sum = weights.sum()
    if not np.isclose(weight_sum, 1.0, atol=1e-6):
        print(f"Warning: Portfolio weights sum to {weight_sum:.6f}, not 1.0. Normalizing...")
        weights = weights / weight_sum

    # Download prices
    prices = download_prices(tickers, start, end)

    # Compute returns
    returns = to_monthly_returns(prices, freq)

    # Compute weighted returns
    # Handle case where some tickers might be missing
    available_tickers = [t for t in tickers if t in returns.columns]
    if len(available_tickers) < len(tickers):
        missing = set(tickers) - set(available_tickers)
        print(f"Warning: Missing data for tickers: {missing}")
        # Renormalize weights for available tickers
        available_weights = weights[[i for i, t in enumerate(tickers) if t in available_tickers]]
        available_weights = available_weights / available_weights.sum()
        weighted_returns = (returns[available_tickers] * available_weights).sum(axis=1)
    else:
        weighted_returns = (returns[tickers] * weights).sum(axis=1)

    return weighted_returns
