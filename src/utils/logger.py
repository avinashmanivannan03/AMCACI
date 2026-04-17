import logging
import sys
from pathlib import Path


LOG_DIR = Path("data/logs")
LOG_DIR.mkdir(parents=True, exist_ok=True)

_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(_formatter)

    # File handler - rotates daily
    file_handler = logging.FileHandler(LOG_DIR / "amcaci.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.propagate = False

    return logger

