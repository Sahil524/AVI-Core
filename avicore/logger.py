from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any


class JSONFormatter(logging.Formatter):
    """Formats log records into machine-readable JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_production_logging(log_file: Path, verbose: bool = False) -> logging.Logger:
    """Configure rotating log file handler with 5MB file cap and JSON formatting."""
    log_file = Path(log_file).resolve()
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("avicore")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Avoid duplicate handlers
    if not logger.handlers:
        handler = RotatingFileHandler(
            str(log_file),
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)

    return logger
