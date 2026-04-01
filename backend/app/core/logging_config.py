import os
import sys

from loguru import logger


def setup_logging():
    # Remove default handler
    logger.remove()

    # Create logs directory if it doesn't exist
    log_base_dir = "logs"

    # Configure log format and path
    # Path format: logs/YYYY/MM/app_year_month.log
    log_path = os.path.join(log_base_dir, "{time:YYYY}", "{time:MM}", "app.log")

    # Add stdout handler
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # Add file handler with rotation and year/month structure
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="10 MB",
        retention="1 year",
        compression="zip",
        enqueue=True,  # Asynchronous logging
    )

    return logger
