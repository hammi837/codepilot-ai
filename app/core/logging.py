"""
Structured logging configuration for CodePilot AI.

Sets up JSON-friendly log formatting with log levels per environment.
"""
import logging
import sys
from app.core.config import settings


LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """Configure root logger with appropriate level and handlers."""
    level = logging.DEBUG if settings.DEBUG else logging.INFO

    logging.basicConfig(
        level=level,
        format=LOG_FORMAT,
        datefmt=DATE_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Quiet noisy third-party loggers in production
    if not settings.DEBUG:
        logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("chromadb").setLevel(logging.WARNING)

    logging.getLogger("codepilot").setLevel(level)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger under the codepilot namespace."""
    return logging.getLogger(f"codepilot.{name}")
