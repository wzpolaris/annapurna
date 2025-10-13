import logging
from pathlib import Path

log_path = Path(__file__).resolve().parent.parent / 'logs' / 'rbsa.log'
log_path.parent.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger('analytics.rbsa')
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.FileHandler(log_path, encoding='utf-8')
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)