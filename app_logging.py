"""Centralized logging configuration."""
import logging


def get_logger(name: str) -> logging.Logger:
    """Return an INFO-level logger that writes timestamped lines to stderr.

    Handlers are added once per logger name, so repeated calls never duplicate output.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)

    return logger
