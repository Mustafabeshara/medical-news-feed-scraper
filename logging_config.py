"""Logging configuration for the application."""

import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging(
    log_level: str = "INFO",
    log_file: str = None,
    log_format: str = None
) -> None:
    """
    Configure logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        log_format: Optional custom log format
    """
    if log_format is None:
        log_format = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(filename)s:%(lineno)d] - %(message)s"
        )
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # Suppress noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("feedparser").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class StructuredLogger:
    """Wrapper for structured logging."""
    
    def __init__(self, logger: logging.Logger):
        """Initialize structured logger."""
        self.logger = logger
    
    def log_event(self, event: str, **kwargs) -> None:
        """Log a structured event."""
        context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        self.logger.info(f"{event} | {context}" if context else event)
    
    def log_error(self, error: str, exception: Exception = None, **kwargs) -> None:
        """Log an error with context."""
        context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        message = f"{error} | {context}" if context else error
        self.logger.error(message, exc_info=exception)
    
    def log_performance(self, operation: str, duration: float, **kwargs) -> None:
        """Log performance metrics."""
        context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        message = f"Performance: {operation} took {duration:.2f}s | {context}" if context else f"Performance: {operation} took {duration:.2f}s"
        self.logger.info(message)
