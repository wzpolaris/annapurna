from __future__ import annotations

import pandas as pd

SPACE_DATA = {
    'ai-fundmodeler': [
        {"Metric": "Sharpe", "Value": 1.42, "Change": "+0.08"},
        {"Metric": "Tracking Error", "Value": 3.1, "Change": "-0.2"},
        {"Metric": "IR", "Value": 0.68, "Change": "+0.05"},
    ],
    'sherlock-holmes': [
        {"Metric": "Alerts", "Value": 9, "Change": "+2"},
        {"Metric": "Investigations", "Value": 4, "Change": "0"},
        {"Metric": "Resolution Time (hrs)", "Value": 6.4, "Change": "-1.1"},
    ],
    'risk-chat': [
        {"Metric": "VaR 95%", "Value": 2.7, "Change": "+0.4"},
        {"Metric": "Drawdown", "Value": -5.2, "Change": "-0.3"},
        {"Metric": "Beta", "Value": 0.92, "Change": "-0.01"},
    ],
    'private-illiquids': [
        {"Metric": "NAV", "Value": 213.4, "Change": "+1.7"},
        {"Metric": "Commitment Used", "Value": "78%", "Change": "+4%"},
        {"Metric": "Cash Calls", "Value": 4, "Change": "-1"},
    ],
    'optimize': [
        {"Metric": "Turnover", "Value": "12%", "Change": "+1%"},
        {"Metric": "Sector Drift", "Value": "1.8%", "Change": "-0.2%"},
        {"Metric": "Constraint Hits", "Value": 3, "Change": "0"},
    ],
    'scenarios': [
        {"Metric": "Fed Cut", "Value": "+2.1%", "Change": "+0.3%"},
        {"Metric": "Oil Shock", "Value": "-1.4%", "Change": "-0.6%"},
        {"Metric": "EUR Rally", "Value": "+0.7%", "Change": "+0.2%"},
    ],
}


def build_space_table(space_key: str) -> str:
    data = SPACE_DATA.get(space_key, SPACE_DATA['ai-fundmodeler'])
    df = pd.DataFrame(data)
    return df.to_markdown(index=False)
