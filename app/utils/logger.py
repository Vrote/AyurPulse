import logging
import os
from logging.handlers import RotatingFileHandler

# Define log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logger():
    """Configures production-grade logging to both console and file."""
    
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    log_file = os.path.join(log_dir, "ayurpulse.log")

    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        handlers=[
            # Console Handler
            logging.StreamHandler(),
            # File Handler (Rotates at 5MB, keeps 5 old logs)
            RotatingFileHandler(log_file, maxBytes=5000000, backupCount=5)
        ]
    )

    logger = logging.getLogger("AyurPulse")
    logger.info("Logging system initialized. Output: Console + 'logs/ayurpulse.log'")
    return logger

# Initialize the global logger instance
logger = setup_logger()
