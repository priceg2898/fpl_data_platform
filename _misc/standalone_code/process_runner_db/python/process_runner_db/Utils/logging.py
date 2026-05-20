import logging
from logging.handlers import TimedRotatingFileHandler
import os
import json

# Load config once at startup
CONFIG_PATH = "config.json"


def load_config(path=CONFIG_PATH):
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {"DEBUG_LEVEL": "INFO"}


config = load_config()

# Map string level to logging constant
debug_level = config.get("DEBUG_LEVEL", "INFO").upper()
if debug_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
    debug_level = "INFO"

log_level = getattr(logging, debug_level)

# Set up log files and rotation
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "process_runner.log")

handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7)
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)

# Configure logger
logger = logging.getLogger()
logger.setLevel(log_level)
logger.addHandler(handler)

# Optional console output
console = logging.StreamHandler()
console.setFormatter(formatter)
logger.addHandler(console)


def update_log_level(logger, config_path="config.json"):
    try:
        with open(config_path) as f:
            cfg = json.load(f)

        debug_level = cfg.get("DEBUG_LEVEL", "INFO").upper()

        if debug_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            debug_level = "INFO"

        log_level = getattr(logging, debug_level)

        if logger.level != log_level:
            logger.setLevel(log_level)

            for h in logger.handlers:
                h.setLevel(log_level)

            logger.info(f"Log level dynamically updated to {debug_level}")

    except Exception:
        logger.exception("Failed to update log level from config")
        raise
