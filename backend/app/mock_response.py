from __future__ import annotations

import base64
from io import BytesIO
import random
from typing import List

import matplotlib.pyplot as plt
import pandas as pd

from .schemas import ResponseBlock

LATEX_SNIPPETS = [
    r"The Sharpe ratio is given by $S = \frac{\mu - r_f}{\sigma}$.",
    r"Variance decomposition: $\sigma^2 = w^T \Sigma w$.",
    r"Posterior mean $\mu_{t+1} = \mu_t + K (y_t - H \mu_t)$."
]


def _markdown_block(space_key: str) -> ResponseBlock:
    note = random.choice(LATEX_SNIPPETS)
    content = (
        f"#### Mock analysis for `{space_key}`\n"
        "This is a placeholder response generated locally for rapid prototyping.\n\n"
        f"{note}\n"
        "- Data refreshed just now\n\n"
        "- No backend call was made"
    )
    return ResponseBlock(type='markdown', content=content)


def _plot_block() -> ResponseBlock:
    x = list(range(5))
    y = [random.uniform(-2, 2) for _ in x]
    plt.style.use('seaborn-v0_8')
    fig, ax = plt.subplots(figsize=(4, 2.5))
    ax.plot(x, y, marker='o', color='#02BD9D')
    ax.set_title('Mock signal trajectory')
    ax.set_xlabel('Step')
    ax.set_ylabel('Value')
    ax.grid(True, alpha=0.3)

    buffer = BytesIO()
    fig.tight_layout()
    fig.savefig(buffer, format='png')
    plt.close(fig)
    buffer.seek(0)
    encoded = base64.b64encode(buffer.read()).decode('ascii')
    uri = f'data:image/png;base64,{encoded}'
    return ResponseBlock(type='image', content=uri, altText='Mock trajectory plot')


def _html_table_block() -> ResponseBlock:
    df = pd.DataFrame(
        {
            'Scenario': ['Baseline', 'Stress', 'Opportunity'],
            'Return (%)': [round(random.uniform(-4, 6), 2) for _ in range(3)],
            'Probability': [0.6, 0.25, 0.15]
        }
    )
    html = df.to_html(index=False, classes='mock-table', border=0)
    return ResponseBlock(type='html', content=html)


_GENERATORS = [_markdown_block, _plot_block, _html_table_block]


def generate_mock_blocks(space_key: str) -> List[ResponseBlock]:
    count = random.randint(1, len(_GENERATORS))
    selected = random.sample(_GENERATORS, count)
    blocks: List[ResponseBlock] = []
    for generator in selected:
        if generator is _markdown_block:
            blocks.append(generator(space_key))
        else:
            blocks.append(generator())  # type: ignore[arg-type]
    return blocks
