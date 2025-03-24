import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from src.config import get_settings

settings = get_settings()

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

REPOSITORY_LOG_FILE = LOG_DIR / "repository.log"
SERVICE_LOG_FILE = LOG_DIR / "service.log"
API_LOG_FILE = LOG_DIR / "api.log"

LOG_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"  # noqa: Typo


def setup_logger(name: str, log_file: Path, level: int = logging.INFO) -> logging.Logger:
    """
    Configure a logger with daily file rotation and optional console logging.
    
    This function creates or retrieves a logger by name, sets its logging level, and attaches a
    TimedRotatingFileHandler that rotates the log file at midnight with up to 7 backups. Log message
    propagation is disabled, and if debug mode is enabled in the settings, a console handler is also
    attached.
    
    Args:
        name (str): The identifier for the logger.
        log_file (Path): The file path to store log output.
        level (int): The logging level threshold.
    
    Returns:
        logging.Logger: The configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent logging from propagating to the root logger
    logger.propagate = False

    formatter = logging.Formatter(LOG_FORMAT)

    file_handler = TimedRotatingFileHandler(
        log_file, when="midnight", interval=1, backupCount=7, encoding="utf-8"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    if settings.DEBUG:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger


repository_logger = setup_logger("repository", REPOSITORY_LOG_FILE)
service_logger = setup_logger("service", SERVICE_LOG_FILE)
api_logger = setup_logger("api", API_LOG_FILE)
