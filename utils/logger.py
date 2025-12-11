import logging
import sys
import os
import re
from logging.handlers import RotatingFileHandler

# --- CONFIGURATION ---
LOG_DIR = "logs"
MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3                # Keep 3 old files

class CredentialFilter(logging.Filter):
    """
    Scans log messages for sensitive patterns and masks them.
    """
    def __init__(self, sensitive_strings=None):
        super().__init__()
        self.sensitive_strings = sensitive_strings or []
        # Regex to catch key-value pairs like 'login_password': '123'
        self.regex_assign = re.compile(r"('login_password'|'mpin'|'totp_secret'|'google_app_password')\s*[:=]\s*['\"](.*?)['\"]")

    def filter(self, record):
        msg = record.getMessage()
        
        # 1. Mask specific known secrets (from memory)
        for secret in self.sensitive_strings:
            if secret and len(secret) > 4: # Don't mask short common words
                if secret in msg:
                    msg = msg.replace(secret, "********")

        # 2. Mask regex patterns (JSON dumps)
        msg = self.regex_assign.sub(r"\1: '********'", msg)
        
        record.msg = msg
        return True

class StructuredLogger:
    def __init__(self, user_id, sensitive_data=None):
        self.user_id = user_id
        self.logger = logging.getLogger(f"Engine_{user_id}")
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False # Prevent double logging in root
        
        # Prevent adding duplicate handlers if re-initialized
        if self.logger.hasHandlers():
            self.logger.handlers.clear()

        # Format: [TIME] [USER] [LEVEL] [TAGS] - Message
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(user_id)s] [%(levelname)s] %(tags)s - %(message)s",
            datefmt="%H:%M:%S"
        )

        # 1. File Handler (Rotates at 5MB)
        os.makedirs(LOG_DIR, exist_ok=True)
        file_path = os.path.join(LOG_DIR, f"{user_id}.log")
        fh = RotatingFileHandler(file_path, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT)
        fh.setFormatter(formatter)
        fh.addFilter(CredentialFilter(sensitive_data))
        self.logger.addHandler(fh)

        # 2. Console Handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(formatter)
        ch.addFilter(CredentialFilter(sensitive_data))
        self.logger.addHandler(ch)

        # Context for Formatter
        self.extra = {'user_id': user_id, 'tags': '[SYS]'}

    def _log(self, level, msg, tags):
        # Format tags list to string: ["RISK", "API"] -> "[RISK,API]"
        if isinstance(tags, list):
            tag_str = f"[{','.join(tags)}]"
        elif isinstance(tags, str):
            tag_str = f"[{tags}]"
        else:
            tag_str = "[GEN]"
            
        self.extra['tags'] = tag_str
        self.logger.log(level, msg, extra=self.extra)

    def info(self, msg, tags=None):
        self._log(logging.INFO, msg, tags)

    def warning(self, msg, tags=None):
        self._log(logging.WARNING, msg, tags)

    def error(self, msg, tags=None, exc_info=False):
        self.extra['tags'] = tags or "[ERR]"
        self.logger.error(msg, extra=self.extra, exc_info=exc_info)

    def critical(self, msg, tags=None, exc_info=True):
        self.extra['tags'] = tags or "[CRIT]"
        self.logger.critical(msg, extra=self.extra, exc_info=exc_info)

# Helper to build logger safely
def setup_logger(user_id, creds_dict=None):
    # Extract secrets for masking
    secrets = []
    if creds_dict:
        k = creds_dict.get('kotak', {})
        g = creds_dict.get('gmail', {})
        secrets = [
            k.get('login_password'), 
            k.get('mpin'), 
            k.get('totp_secret'), 
            g.get('google_app_password')
        ]
    return StructuredLogger(user_id, sensitive_data=secrets)