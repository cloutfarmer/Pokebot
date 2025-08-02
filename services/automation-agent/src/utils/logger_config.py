"""
Logging configuration for the automation agent
"""

import os
import sys
from pathlib import Path

from loguru import logger


def setup_logging() -> None:
    """Configure loguru logging with console and file outputs."""
    
    # Remove default logger
    logger.remove()
    
    # Get log level from environment
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    
    # Console logging with colors
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True,
    )
    
    # File logging
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    
    log_file = logs_dir / os.getenv("LOG_FILE", "automation.log")
    
    logger.add(
        log_file,
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="50 MB",
        retention="7 days",
        compression="gz",
    )
    
    # Error file logging
    error_log_file = logs_dir / "errors.log"
    logger.add(
        error_log_file,
        level="ERROR",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}\n{exception}",
        rotation="10 MB",
        retention="30 days",
        backtrace=True,
        diagnose=True,
    )
    
    logger.info(f"📊 Logging configured - Level: {log_level}, File: {log_file}")