import os
import sys
import logging

from logging.handlers import RotatingFileHandler


def get_log_level_from_env() -> int:
    """Get log level from environment variable or use default"""
    log_level_str: str = os.getenv("LOG_LEVEL", "INFO").upper()

    # Map string log levels to logging module constants
    level_map: dict[str, int] = {
        "DEBUG": logging.DEBUG,  # 10
        "INFO": logging.INFO,  # 20
        "WARNING": logging.WARNING,  # 30
        "ERROR": logging.ERROR,  # 40
        "CRITICAL": logging.CRITICAL,  # 50
    }

    # Return the mapped level or default to INFO if invalid
    return level_map.get(log_level_str, logging.INFO)


def setup_logger(
    name: str = "pybiztools", log_level: int = logging.INFO
) -> logging.Logger:
    """Setup app wide logging utiltity"""
    logger: logging.Logger = logging.getLogger(name)

    # If the logger has not been setup yet...
    if not logger.handlers:
        logger.setLevel(log_level)

        formatter: logging.Formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # For logging to stdout
        console_handler: logging.StreamHandler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # For logging to a file
        log_dir = os.getenv("LOG_DIR", "logs")
        log_file_path = os.path.join(log_dir, f"{name}.log")

        # Create the log directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler: logging.RotatingFileHandler = RotatingFileHandler(
            filename=log_file_path, maxBytes=1024, backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


logger: logging.Logger = setup_logger(
    "pybiztools", log_level=get_log_level_from_env()
)
