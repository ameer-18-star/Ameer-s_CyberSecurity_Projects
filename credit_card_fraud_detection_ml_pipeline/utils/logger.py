"""
utils/logger.py
---------------
Centralised logging setup for the fraud detection pipeline.
Logs to both console (stdout) and a timestamped file in outputs/.
"""

import logging
import os
from datetime import datetime


def setup_logger(name: str = "FraudDetector") -> logging.Logger:
    """
    Create and return a logger that writes to console + file.

    Returns
    -------
    logging.Logger
    """
    os.makedirs("outputs", exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join("outputs", f"run_{timestamp}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Clear any existing handlers (prevents duplicate output on re-import)
    if logger.handlers:
        logger.handlers.clear()

    fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S"
    )

    # ── Console handler ────────────────────────────────────────────────────
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # ── File handler ───────────────────────────────────────────────────────
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.info(f"Logger initialised — log file: {log_file}")
    return logger
