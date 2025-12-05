import logging
import os
import sys

class TaggedFormatter(logging.Formatter):
    """Custom formatter that adds [TAGS] to the log output."""
    def format(self, record):
        msg = super().format(record)
        if hasattr(record, 'tags') and record.tags:
            tag_str = f"[{','.join(record.tags)}]"
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

def setup_logger(user_id, log_file_path, wipe_on_start=False):
    """
    Sets up a specific logger for a specific user.
    """
    # 1. Ensure Directory Exists
    log_dir = os.path.dirname(log_file_path)
    os.makedirs(log_dir, exist_ok=True)

    # 2. Create Unique Logger Name (Critical for Thread Safety)
    logger_name = f"KillSwitch_{user_id}"
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear() # Prevent duplicate logs

    # Formatter
    fmt = TaggedFormatter(f"%(asctime)s [{user_id}] [%(levelname)s] - %(message)s", datefmt="%H:%M:%S")

    # File Handler
    # 'w' mode overwrites file (wipes it), 'a' mode appends
    file_mode = 'w' if wipe_on_start else 'a'
    fh = logging.FileHandler(log_file_path, mode=file_mode)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return TaggedLogger(logger)