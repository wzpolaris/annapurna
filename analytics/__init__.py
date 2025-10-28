# import logging
# from pathlib import Path

# # Try to use ConcurrentLogHandler for multi-worker safety
# try:
#     from concurrent_log_handler import ConcurrentRotatingFileHandler
#     CONCURRENT_LOGGING = True
# except ImportError:
#     CONCURRENT_LOGGING = False
#     print("Warning: concurrent-log-handler not installed. Using standard FileHandler.")
#     print("Install with: pip install concurrent-log-handler")

# log_path = Path(__file__).resolve().parent.parent / 'logs' / 'rbsa.log'
# log_path.parent.mkdir(parents=True, exist_ok=True)

# logger = logging.getLogger('analytics.rbsa')
# logger.setLevel(logging.INFO)
# if not logger.handlers:
#     if CONCURRENT_LOGGING:
#         # Thread and process-safe handler with rotation
#         handler = ConcurrentRotatingFileHandler(
#             log_path, 
#             maxBytes=10*1024*1024,  # 10MB per file
#             backupCount=5,          # Keep 5 backup files
#             encoding='utf-8'
#         )
#     else:
#         # Fallback to standard handler
#         handler = logging.FileHandler(log_path, encoding='utf-8')
    
#     formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
#     handler.setFormatter(formatter)
#     logger.addHandler(handler)