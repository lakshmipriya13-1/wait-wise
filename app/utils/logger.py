import logging
import sys
from logging.handlers import RotatingFileHandler
import os

# Create logs directory inside workspace if it doesn't exist
LOGS_DIR = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

# Configure logger
logger = logging.getLogger('waitwise')
logger.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s in %(module)s (Line %(lineno)d): %(message)s'
)

# Console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# File handler with rotating backup (10MB max per file, 5 backup files)
log_file = os.path.join(LOGS_DIR, 'waitwise.log')
file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
