"""Structured logging configuration."""

import logging


def configure_logging() -> None:
    """Configure a compact default logger for local development."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
