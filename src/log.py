# src/log.py
"""
Logging configuration for G7Static.
Sets up a logger with both console and file handlers, configurable log level, and professional formatting.
"""
import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "g7static.log")

logger = logging.getLogger("G7StaticLogs")
logger.setLevel(LOG_LEVEL)

# Formatter
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Console Handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(LOG_LEVEL)

# File Handler
file_handler = logging.FileHandler(LOG_FILE)
file_handler.setFormatter(formatter)
file_handler.setLevel(LOG_LEVEL)

# Avoid duplicate handlers if re-imported
if not logger.hasHandlers():
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

logger.propagate = False