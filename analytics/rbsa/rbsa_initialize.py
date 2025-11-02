"""
RBSA initialization module for notebooks.

Import this module to get pre-configured global instances of summarizer and checkpoint_runner.
These are initialized based on config.yaml in the project root.

Usage:
    from rbsa.rbsa_initialize import summarizer, checkpoint_runner

    # Use directly in notebook cells
    results = run_all_methods(cfg, data)
    for k, v in results.items():
        v["summary"] = summarizer.summarize(f"Selected: {', '.join(v['selected'])}")
"""
from __future__ import annotations
import os
from typing import Optional
from .rbsa_pipeline import load_config
from .rbsa_utils import Summarizer
from .checkpoints import CheckpointRunner

# Find project root and load config
_project_root = os.path.dirname(os.path.dirname(__file__))
cfg = load_config(os.path.join(_project_root, "config.yaml"))

# Initialize summarizer
summarizer = Summarizer(
    backend=cfg["summarization"]["backend"],
    model=cfg["summarization"]["model"],
    temperature=cfg["summarization"]["temperature"],
    system_prompt=cfg["summarization"]["system_prompt"],
)

# Initialize checkpoint runner if interactive mode enabled
checkpoint_runner: Optional[CheckpointRunner] = None
if cfg.get('interactive', {}).get('enabled', False):
    checkpoint_runner = CheckpointRunner(cfg, summarizer)
    print('✓ Interactive mode enabled')
else:
    print('✓ Batch mode')
