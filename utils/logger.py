import logging
import os
import sys

class TaggedFormatter(logging.Formatter):
    """Custom formatter that adds [TAGS] to the log output."""
    def format(self, record):
        msg = super().format(record)
        if hasattr(record, 'tags') and record.tags:
            tag_str = f"[{','.join(record.tags)}]"
            # Insert tags after timestamp/level
            parts = msg.split(' - ', 1)
            if len(parts) > 1:
                return f"{parts[0]} - {tag_str} {parts[1]}"
            return f"{tag_str} {msg}"
        return msg

class TaggedLogger:
    """Wrapper for standard logger to support tags."""
    def __init__(self, logger):
        self._logger = logger

    def info(self, msg, tags=None):
        self._logger.info(msg, extra={'tags': tags or []})

    def warning(self, msg, tags=None):
        self._logger.warning(msg, extra={'tags': tags or []})

    def error(self, msg, tags=None, exc_info=False):
        self._logger.error(msg, extra={'tags': tags or []}, exc_info=exc_info)

    def critical(self, msg, tags=None, exc_info=True):
        self._logger.critical(msg, extra={'tags': tags or []}, exc_info=exc_info)

def setup_logger():
    """
    Sets up the logging directory and handlers.
    Returns a TaggedLogger instance.
    """
    # 1. Define Log Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    log_dir = os.path.join(base_dir, 'logs')
    log_file = os.path.join(log_dir, 'kill_switch.log')

    # 2. Create Directory
    os.makedirs(log_dir, exist_ok=True)

    # 3. Setup Handlers
    logger = logging.getLogger("KotakKillSwitch")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # Formatter
    fmt = TaggedFormatter("%(asctime)s [%(levelname)s] - %(message)s", datefmt="%H:%M:%S")

    # File Handler
    fh = logging.FileHandler(log_file)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return TaggedLogger(logger)