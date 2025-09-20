"""
Centralized logging configuration and error handling utilities for WaifuAPI.
"""
import logging
import logging.handlers
import os
from typing import Optional, Dict, Any
from flask import current_app, request


def setup_logging(app_name: str = "waifuapi") -> logging.Logger:
    """
    Set up centralized logging configuration.

    Args:
        app_name: Name of the application for logging

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)

    # Prevent adding multiple handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # File handler for errors
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    file_handler = logging.handlers.RotatingFileHandler(
        f"{log_dir}/waifuapi.log",
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.WARNING)

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "waifuapi") -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Name for the logger

    Returns:
        Logger instance
    """
    return logging.getLogger(f"waifuapi.{name}")


def log_request_info(logger: logging.Logger, request_obj=None) -> None:
    """
    Log request information for debugging.

    Args:
        logger: Logger instance
        request_obj: Flask request object
    """
    if request_obj:
        logger.debug(f"Request Method: {request_obj.method}")
        logger.debug(f"Request URL: {request_obj.url}")
        logger.debug(f"Request Headers: {dict(request_obj.headers)}")
        if request_obj.is_json:
            logger.debug(f"Request JSON: {request_obj.get_json()}")
        elif request_obj.form:
            logger.debug(f"Request Form: {request_obj.form.to_dict()}")
        if request_obj.args:
            logger.debug(f"Request Args: {request_obj.args.to_dict()}")


class WaifuAPIError(Exception):
    """Base exception class for WaifuAPI errors."""

    def __init__(self, message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR"):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        super().__init__(self.message)


def create_error_response(message: str, status_code: int = 500, error_code: str = "INTERNAL_ERROR") -> Dict[str, Any]:
    """
    Create a standardized error response.

    Args:
        message: Error message
        status_code: HTTP status code
        error_code: Internal error code

    Returns:
        Standardized error response dictionary
    """
    return {
        "error": {
            "code": error_code,
            "message": message,
            "status_code": status_code
        }
    }


def handle_exception(e: Exception, logger: logging.Logger, context: str = "") -> Dict[str, Any]:
    """
    Handle and log exceptions consistently.

    Args:
        e: The exception that occurred
        logger: Logger instance
        context: Additional context about where the error occurred

    Returns:
        Standardized error response
    """
    error_msg = f"{context}: {str(e)}" if context else str(e)
    logger.error(error_msg, exc_info=True)

    if isinstance(e, WaifuAPIError):
        return create_error_response(e.message, e.status_code, e.error_code)

    # Handle different exception types
    if isinstance(e, ValueError):
        return create_error_response("Invalid input data", 400, "VALIDATION_ERROR")
    elif isinstance(e, PermissionError):
        return create_error_response("Access denied", 403, "ACCESS_DENIED")
    elif isinstance(e, FileNotFoundError):
        return create_error_response("Resource not found", 404, "NOT_FOUND")
    elif isinstance(e, ConnectionError):
        return create_error_response("Service unavailable", 503, "SERVICE_UNAVAILABLE")
    else:
        return create_error_response("Internal server error", 500, "INTERNAL_ERROR")