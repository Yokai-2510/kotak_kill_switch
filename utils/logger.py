"""
Tagged logging system with console and file handlers.
Supports INFO, WARNING, ERROR, CRITICAL levels with optional exception tracebacks.
"""

import logging
import os
from typing import List, Optional


class TaggedFormatter(logging.Formatter):
    """Custom formatter that prepends tags to log messages."""
    
    def format(self, record: logging.LogRecord) -> str:
        log_message = super().format(record)
        
        # Add tags if present in record
        if hasattr(record, 'tags') and record.tags:
            tags_str = f"[{','.join(record.tags)}] "
            parts = log_message.split(" - ", 1)
            if len(parts) > 1:
                log_message = f"{parts[0]} - {tags_str}{parts[1]}"
        
        return log_message


class TaggedLogger:
    """Logger wrapper that supports tags and proper exception handling."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def _log(self, level: int, msg: str, tags: Optional[List[str]] = None, **kwargs):
        """Internal helper that passes kwargs including exc_info to logger."""
        extra_data = {'tags': tags if tags else []}
        self.logger.log(level, msg, extra=extra_data, **kwargs)
    
    def info(self, msg: str, tags: Optional[List[str]] = None):
        """Log INFO level message."""
        self._log(logging.INFO, msg, tags)
    
    def warning(self, msg: str, tags: Optional[List[str]] = None):
        """Log WARNING level message."""
        self._log(logging.WARNING, msg, tags)
    
    def error(self, msg: str, tags: Optional[List[str]] = None, exc_info: bool = False):
        """Log ERROR level message with optional exception traceback."""
        self._log(logging.ERROR, msg, tags, exc_info=exc_info)
    
    def critical(self, msg: str, tags: Optional[List[str]] = None, exc_info: bool = False):
        """Log CRITICAL level message with optional exception traceback."""
        self._log(logging.CRITICAL, msg, tags, exc_info=exc_info)


_logger_instance = None  # Singleton instance


def setup_logger() -> TaggedLogger:
    """Get or create singleton logger instance with console and file handlers."""
    
    global _logger_instance
    
    if _logger_instance:
        return _logger_instance
    
    # Create base logger
    logger = logging.getLogger("KillSwitch_System")
    logger.setLevel(logging.INFO)
    
    # Clear existing handlers
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # Create formatter
    formatter = TaggedFormatter(
        "%(asctime)s [%(levelname)-8s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler
    # Resolves to Project_Root/logs/kill_switch.log
    try:
        log_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'logs'
        )
        os.makedirs(log_dir, exist_ok=True)
        
        file_handler = logging.FileHandler(
            os.path.join(log_dir, "kill_switch.log"),
            mode='a'
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"WARNING: Could not set up file logging: {e}")
    
    # Create and cache singleton
    _logger_instance = TaggedLogger(logger)
    
    return _logger_instance