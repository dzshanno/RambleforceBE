# app/utils/logging_config.py
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logging(
    log_level=logging.DEBUG,
    log_format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    log_file=None,
):
    """
    Configure logging for the application with both console and file handlers.

    Args:
        log_level: The logging level to use (default: DEBUG)
        log_format: The format string for log messages
        log_file: Optional path to a log file. If None, only console logging is used.
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Remove any existing handlers and properly close them
    for handler in logger.handlers[:]:
        handler.close()  # Properly close the handler
        logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if log_file is specified)
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file).parent
        log_path.mkdir(parents=True, exist_ok=True)

        # Create rotating file handler
        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Optional: Add a cleanup function that can be called explicitly if needed
def cleanup_logging():
    """Cleanup logging handlers"""
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        handler.close()
        root_logger.removeHandler(handler)
