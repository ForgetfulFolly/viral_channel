import os
import json
import logging
import pytest
from unittest.mock import patch, MagicMock
from logging.handlers import RotatingFileHandler
from src.utils.logging import setup_logging, get_logger, ConsoleFormatter, JsonFormatter


@pytest.fixture
def log_dir(tmp_path):
    """Fixture to provide a temporary directory for logs."""
    return tmp_path / "logs"


@pytest.fixture
def logger_name():
    """Fixture to provide a default logger name."""
    return "test_logger"


@pytest.fixture
def setup_logger(log_dir, logger_name):
    """Fixture to set up a logger for testing."""
    return setup_logging(log_dir=str(log_dir), log_level="DEBUG", module_name=logger_name)


def test_setup_logging_creates_log_directory(log_dir, logger_name):
    """Test that setup_logging creates the log directory if it does not exist."""
    assert not log_dir.exists()
    setup_logging(log_dir=str(log_dir), log_level="INFO", module_name=logger_name)
    assert log_dir.exists()
    assert log_dir.is_dir()


def test_console_formatter_output(setup_logger, capsys):
    """Test that the ConsoleFormatter produces the correct human-readable format."""
    logger = setup_logger
    logger.info("Test console log")
    captured = capsys.readouterr()
    assert "INFO" in captured.err
    assert "Test console log" in captured.err
    assert "test_logger" in captured.err


def test_json_formatter_output(log_dir, setup_logger):
    """Test that the JsonFormatter produces valid JSON lines with required fields."""
    logger = setup_logger
    log_file = log_dir / "test_logger.log"
    logger.info("Test JSON log", extra={"key": "value"})

    with open(log_file, "r") as f:
        log_line = f.readline()
        log_data = json.loads(log_line)

    assert "timestamp" in log_data
    assert "level" in log_data
    assert "module" in log_data
    assert "message" in log_data
    assert "extra" in log_data
    assert log_data["message"] == "Test JSON log"
    assert log_data["extra"] == {"key": "value"}


def test_rotating_file_handler_configuration(log_dir, logger_name):
    """Test that the RotatingFileHandler is configured with the correct max_bytes and backup_count."""
    logger = setup_logging(log_dir=str(log_dir), log_level="DEBUG", module_name=logger_name)
    file_handler = next(
        handler for handler in logger.handlers if isinstance(handler, RotatingFileHandler)
    )
    assert file_handler.maxBytes == 10 * 1024 * 1024  # 10 MB
    assert file_handler.backupCount == 5


def test_get_logger_returns_child_logger(logger_name):
    """Test that get_logger returns a child logger under the 'viral_channel' namespace."""
    logger = get_logger(logger_name)
    assert logger.name == f"viral_channel.{logger_name}"


def test_get_logger_returns_same_instance(logger_name):
    """Test that multiple calls to get_logger with the same name return the same logger instance."""
    logger1 = get_logger(logger_name)
    logger2 = get_logger(logger_name)
    assert logger1 is logger2


def test_setup_logging_idempotency(log_dir, logger_name):
    """Test that setup_logging is idempotent and does not duplicate handlers."""
    logger = setup_logging(log_dir=str(log_dir), log_level="DEBUG", module_name=logger_name)
    initial_handler_count = len(logger.handlers)
    setup_logging(log_dir=str(log_dir), log_level="DEBUG", module_name=logger_name)
    assert len(logger.handlers) == initial_handler_count


def test_console_and_file_handler_log_levels(log_dir, logger_name):
    """Test that console and file handlers can have different log levels."""
    logger = setup_logging(log_dir=str(log_dir), log_level="WARNING", module_name=logger_name)
    console_handler = next(
        handler for handler in logger.handlers if isinstance(handler, logging.StreamHandler)
    )
    file_handler = next(
        handler for handler in logger.handlers if isinstance(handler, RotatingFileHandler)
    )
    assert console_handler.level == logging.WARNING
    assert file_handler.level == logging.DEBUG