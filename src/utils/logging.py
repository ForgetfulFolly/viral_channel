import logging
import os
import json
from logging.handlers import RotatingFileHandler
from typing import Any


class ConsoleFormatter(logging.Formatter):
    """
    Human-readable log formatter for console output.
    Formats logs as: "{timestamp} [{level}] {module}: {message}".
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%SZ")
        level = record.levelname
        module = record.name
        message = record.getMessage()
        return f"{timestamp} [{level}] {module}: {message}"


class JsonFormatter(logging.Formatter):
    """
    JSON-lines formatter for file output.
    Formats logs as JSON objects with fields:
    - timestamp (ISO 8601 UTC format)
    - level
    - module
    - message
    - extra
    """

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%SZ"),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
            "extra": record.__dict__.get("extra", {}),
        }
        return json.dumps(log_record)


def setup_logging(
    log_dir: str,
    log_level: str = "INFO",
    module_name: str = "viral_channel"
) -> logging.Logger:
    """
    Configure and return a Logger instance.

    Args:
        log_dir (str): Directory where log files will be stored.
        log_level (str): Logging level for the console handler (default: "INFO").
        module_name (str): Name of the module for the log file (default: "viral_channel").

    Returns:
        logging.Logger: Configured root logger.
    """
    try:
        os.makedirs(log_dir, exist_ok=True)
    except OSError as e:
        raise RuntimeError(f"Failed to create log directory {log_dir}: {e}")

    logger = logging.getLogger(module_name)
    if logger.hasHandlers():
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    console_formatter = ConsoleFormatter()
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file = os.path.join(log_dir, f"{module_name}.log")
    file_handler = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = JsonFormatter()
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


def get_logger(module_name: str) -> logging.Logger:
    """
    Get a child logger for a specific module.

    Args:
        module_name (str): Name of the module (e.g., "discovery.youtube").

    Returns:
        logging.Logger: Child logger under the "viral_channel" namespace.
    """
    if not module_name:
        raise ValueError("module_name must be a non-empty string")

    return logging.getLogger(f"viral_channel.{module_name}")