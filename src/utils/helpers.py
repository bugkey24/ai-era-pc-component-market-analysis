"""Utility helpers for the AI-Era PC Market Analysis project."""

import logging
from pathlib import Path
from typing import Optional

import yaml


def load_config(path: str = "config.yaml") -> dict:
    """Load and return the project configuration from a YAML file."""
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(config_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def setup_logger(
    name: str = "pipeline",
    level: str = "INFO",
    fmt: Optional[str] = None,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """Create and return a configured :class:`logging.Logger`.

    A named logger avoids polluting the root logger.  Handlers are only
    attached once so repeated calls are safe.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = fmt or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    formatter = logging.Formatter(fmt)

    # Always attach a stream handler
    stream = logging.StreamHandler()
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    # Optionally attach a file handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
