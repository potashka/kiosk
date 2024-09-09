# app/logging_config.py
import logging
from logging.handlers import RotatingFileHandler

# Настройка логгера
log_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Настройка файла логов
LOG_FILE = "app.log"
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5*1024*1024, backupCount=5)
file_handler.setFormatter(log_formatter)

# Настройка консольного вывода логов
console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Общий логгер
logger = logging.getLogger("app_logger")
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console_handler)
