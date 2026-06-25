import logging
import os
from datetime import datetime
from src.utils.paths import get_base_path

# Build paths relative to the application root
BASE_DIR = get_base_path()
LOG_DIR = os.path.join(BASE_DIR, "logs")

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

LOG_FILE = os.path.join(LOG_DIR, f"punpro_{datetime.now().strftime('%Y%m%d')}.log")

def setup_logger(name: str = "PunPro") -> logging.Logger:
    """Sets up a professional logger with file and console handlers."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers if called multiple times
    if not logger.handlers:
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # File Handler
        fh = logging.FileHandler(LOG_FILE, encoding='utf-8')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)

        # Console Handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)

        logger.addHandler(fh)
        logger.addHandler(ch)

    return logger

def setup_github_reporting():
    """Activa envío automático de errores a GitHub Issues."""
    try:
        from src.services.github_error_reporter import install_github_error_handler, flush_pending_reports
        import threading

        install_github_error_handler(logger)
        threading.Thread(
            target=flush_pending_reports,
            name="GitHubErrorStartupFlush",
            daemon=True,
        ).start()
    except Exception:
        pass

# Global logger instance
logger = setup_logger()
setup_github_reporting()
