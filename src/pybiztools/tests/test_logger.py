import logging
import os
import tempfile
from unittest.mock import patch

from pybiztools.logger import get_log_level_from_env, setup_logger


class TestLogger:
    """Test cases for logger utility functions."""

    def test_get_log_level_from_env(self):
        """Test get_log_level_from_env maps environment variables to correct log levels."""
        log_level_mappings = {
            "DEBUG": logging.DEBUG,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
            "debug": logging.DEBUG,  # case insensitive
            "INVALID": logging.INFO,  # invalid defaults to INFO
        }

        # Test default case (no LOG_LEVEL set)
        with patch.dict(os.environ, {}, clear=True):
            level = get_log_level_from_env()
            assert level == logging.INFO

        # Test each mapping
        for env_value, expected_level in log_level_mappings.items():
            with patch.dict(os.environ, {"LOG_LEVEL": env_value}):
                level = get_log_level_from_env()
                assert level == expected_level

    def test_setup_logger_creates_logger(self):
        """Test setup_logger creates a logger with correct name and level."""
        logger_name = "test_logger"
        log_level = logging.DEBUG

        # Clear any existing handlers to ensure clean test
        test_logger = logging.getLogger(logger_name)
        test_logger.handlers.clear()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOG_DIR": temp_dir}):
                logger = setup_logger(logger_name, log_level)

                assert logger.name == logger_name
                assert logger.level == log_level
                assert len(logger.handlers) == 2  # Console and file handlers

    def test_setup_logger_default_parameters(self):
        """Test setup_logger with default parameters."""
        # Use unique logger name to avoid conflicts
        logger_name = "test_default_logger"
        test_logger = logging.getLogger(logger_name)
        test_logger.handlers.clear()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOG_DIR": temp_dir}):
                logger = setup_logger(logger_name)

                assert logger.name == logger_name
                assert logger.level == logging.INFO
                assert len(logger.handlers) == 2

    def test_setup_logger_console_handler(self):
        """Test setup_logger creates console handler correctly."""
        logger_name = "test_console_logger"
        test_logger = logging.getLogger(logger_name)
        test_logger.handlers.clear()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOG_DIR": temp_dir}):
                logger = setup_logger(logger_name)

                # Find console handler
                console_handlers = [
                    h
                    for h in logger.handlers
                    if isinstance(h, logging.StreamHandler)
                    and not hasattr(h, "baseFilename")
                ]
                assert len(console_handlers) == 1

                console_handler = console_handlers[0]
                # Check that the console handler is using stdout (can be represented differently)
                import sys

                assert console_handler.stream == sys.stdout

    def test_setup_logger_file_handler(self):
        """Test setup_logger creates file handler correctly."""
        logger_name = "test_file_logger"
        test_logger = logging.getLogger(logger_name)
        test_logger.handlers.clear()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOG_DIR": temp_dir}):
                logger = setup_logger(logger_name)

                # Find file handler
                file_handlers = [
                    h for h in logger.handlers if hasattr(h, "baseFilename")
                ]
                assert len(file_handlers) == 1

                file_handler = file_handlers[0]
                expected_path = os.path.join(temp_dir, f"{logger_name}.log")
                assert file_handler.baseFilename == expected_path

    def test_setup_logger_creates_log_directory(self):
        """Test setup_logger creates log directory if it doesn't exist."""
        logger_name = "test_dir_logger"
        test_logger = logging.getLogger(logger_name)
        test_logger.handlers.clear()

        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = os.path.join(temp_dir, "custom_logs")

            with patch.dict(os.environ, {"LOG_DIR": log_dir}):
                # Verify directory doesn't exist initially
                assert not os.path.exists(log_dir)

                logger = setup_logger(logger_name)

                # Verify directory was created
                assert os.path.exists(log_dir)
                assert os.path.isdir(log_dir)

    def test_setup_logger_idempotent(self):
        """Test setup_logger doesn't add duplicate handlers when called multiple times."""
        logger_name = "test_idempotent_logger"
        test_logger = logging.getLogger(logger_name)
        test_logger.handlers.clear()

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {"LOG_DIR": temp_dir}):
                logger1 = setup_logger(logger_name)
                initial_handler_count = len(logger1.handlers)

                logger2 = setup_logger(logger_name)
                final_handler_count = len(logger2.handlers)

                assert initial_handler_count == final_handler_count
                assert logger1 is logger2  # Should return same logger instance
