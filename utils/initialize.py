import json
import sys
import threading
from datetime import datetime
from pathlib import Path
from utils.logger import setup_logger

# =========================================================
#  DEFAULT TEMPLATES (Used if files are missing)
# =========================================================

DEFAULT_CREDS = {
  "USER_01": {
    "kotak": {
      "consumer_key": "ENTER_CONSUMER_KEY",
      "ucc": "ENTER_UCC",
      "mobile_number": "ENTER_MOBILE",
      "mpin": "ENTER_MPIN",
      "totp_secret": "ENTER_TOTP_SECRET",
      "login_password": "ENTER_PASSWORD",
      "environment": "prod"
    },
    "gmail": {
      "email": "ENTER_GMAIL@gmail.com",
      "google_app_password": "ENTER_APP_PASSWORD",
      "sender_filter": "noreply@nmail.kotaksecurities.com"
    }
  }
}

DEFAULT_CONFIG = {
  "USER_01": {
    "account_active": False,
    "account_name": "Main Account",
    "kill_switch": {
      "enabled": True,
      "mtm_limit": 5000.0,
      "sell_order_exit_confirmation": True,
      "auto_square_off": True
    },
    "kill_history": {
      "locked_date": None,
      "timestamp": None,
      "verified": False
    },
    "monitoring": {
      "poll_interval_seconds": 2,
      "off_market_interval_seconds": 60
    },
    "logging": {
      "level": "INFO",
      "file": "logs/USER_01_kill_switch.log",
      "wipe_on_start": True,
      "snapshot_interval": 30
    },
    "gmail": {
      "timeout_seconds": 120,
      "otp_subject": "OTP",
      "kill_subject": "Kill Switch Activated"
    },
    "web_automation": {
      "login_url": "https://neo.kotaksecurities.com/Login",
      "search_timeout": 20000,
      "browser": {
        "headless": False,
        "viewport": { "width": 1366, "height": 768 },
        "args": ["--disable-blink-features=AutomationControlled"]
      },
      "flow_steps": [
        { "id": 1, "description": "Enter Mobile", "action": "input", "enabled": True, "cred_key": "mobile_number", "keys": ["Enter"], "wait": 1.2 },
        { "id": 2, "description": "Enter Password", "action": "input", "enabled": True, "cred_key": "login_password", "keys": ["Enter"], "wait": 0.3 },
        { "id": 3, "description": "Trigger OTP", "action": "keys", "enabled": True, "keys": [], "wait": 1.5 },
        { "id": 4, "description": "Process OTP", "action": "otp", "enabled": True, "wait": 2.0 },
        { "id": 5, "description": "Dismiss Risk Popup", "action": "keys", "enabled": True, "keys": ["Tab", "Tab", "Enter"], "wait": 1.5, "optional": True },
        { "id": 6, "description": "Dismiss Gen Popup", "action": "keys", "enabled": True, "keys": ["Tab", "Tab", "Enter"], "wait": 1.0, "optional": True },
        { "id": 7, "description": "Open Menu", "action": "click", "enabled": True, "coords": { "x": 1285, "y": 27 }, "wait": 1.2 },
        { "id": 8, "description": "Open Acct Details", "action": "keys", "enabled": True, "keys": ["Tab", "Tab", "Tab", "Enter"], "wait": 1.2 },
        { "id": 9, "description": "Focus Canvas", "action": "click", "enabled": True, "coords": { "x": 499, "y": 224 }, "wait": 0.5 },
        { "id": 10, "description": "Scroll Down", "action": "scroll", "enabled": True, "repeats": 10, "wait": 0.5 },
        { "id": 11, "description": "Click Kill Switch", "action": "click", "enabled": True, "coords": { "x": 480, "y": 225 }, "wait": 1.0 },
        { "id": 12, "description": "Uncheck All", "action": "keys", "enabled": True, "keys": ["Tab", "Tab", "Enter"], "wait": 1.0 },
        { "id": 13, "description": "Click Disable Btn", "action": "keys", "enabled": True, "keys": ["Tab", "Tab", "Tab", "Tab", "Tab", "Tab", "Tab", "Enter"], "wait": 1.0 },
        { "id": 14, "description": "Click CONFIRM (Kill)", "action": "click", "enabled": True, "coords": { "x": 587, "y": 615 }, "wait": 1.0 },
        { "id": 15, "description": "Click CANCEL (Test)", "action": "click", "enabled": False, "coords": { "x": 667, "y": 617 }, "wait": 1.0 }
      ]
    }
  }
}

# =========================================================
#  FILE OPERATIONS
# =========================================================

def _ensure_defaults_exist(root_dir):
    """
    Checks if config/creds exist. If not, creates them.
    Useful for first-time installation or compiled builds.
    """
    source_dir = root_dir / "source"
    
    # 1. Create source folder if missing
    if not source_dir.exists():
        try:
            source_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"CRITICAL: Could not create source directory: {e}")
            return

    creds_path = source_dir / "credentials.json"
    config_path = source_dir / "config.json"

    # 2. Create Credentials if missing
    if not creds_path.exists():
        print(">>> First Run Detected: Generating default credentials.json...")
        with open(creds_path, 'w') as f:
            json.dump(DEFAULT_CREDS, f, indent=2)

    # 3. Create Config if missing
    if not config_path.exists():
        print(">>> First Run Detected: Generating default config.json...")
        with open(config_path, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)

def load_json_file(filepath):
    path = Path(filepath)
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(filepath, data):
    path = Path(filepath)
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving JSON: {e}")

# =========================================================
#  STATE INITIALIZATION
# =========================================================

def create_bot_state(user_id):
    root_dir = Path(__file__).parent.parent
    
    # --- CHECK FILES BEFORE LOADING ---
    _ensure_defaults_exist(root_dir)
    # ----------------------------------

    config_path = root_dir / "source" / "config.json"
    full_config = load_json_file(config_path)
    full_creds = load_json_file(root_dir / "source" / "credentials.json")

    # Basic Validation
    if user_id not in full_config or user_id not in full_creds:
        # Fallback: If user not found, try to auto-add them from default template if needed
        # For now, just exit to prevent undefined behavior
        print(f"CRITICAL: User ID {user_id} missing in Config or Creds.")
        sys.exit(1)

    user_config = full_config[user_id]
    user_creds = full_creds[user_id]

    logger = setup_logger(user_id, user_creds)
    
    # --- MIDNIGHT RESET LOGIC ---
    kill_hist = user_config.get('kill_history', {})
    locked_date_str = kill_hist.get('locked_date')
    today_str = datetime.now().strftime("%Y-%m-%d")
    is_locked_today = False
    
    if locked_date_str:
        if locked_date_str == today_str:
            is_locked_today = True
            logger.warning(f"Account is LOCKED for the day (Killed on {locked_date_str}).", tags=["INIT", "LOCK"])
        else:
            is_locked_today = False
            logger.info(f"Previous Kill detected on {locked_date_str}. Resetting lock for New Day ({today_str}).", tags=["INIT", "RESET"])
    
    # Defaults
    mtm_limit = -abs(float(user_config.get('kill_switch', {}).get('mtm_limit', 5000)))

    universal_data = {
        "user_id": user_id,
        "sys": {
            "config":   user_config,
            "creds":    user_creds,
            "log":      logger,
            "api":      None,
            "lock":     threading.Lock(),
            "threads":  {} 
        },
        "status": {
            "stage": "LOCKED" if is_locked_today else "IDLE", 
            "auth_success": False,
            "error_message": "Account Killed Today" if is_locked_today else None,
            "session_start_time": None
        },
        "market": {
            "positions": [], "orders": [], "quotes": {},
            "raw": { "positions": None, "orders": None, "quotes": None }
        },
        "risk": {
            "mtm_current": 0.0, "mtm_limit": mtm_limit, "mtm_distance": 0.0, "sl_hit_status": False
        },
        "signals": {
            "system_active": False,
            "trigger_kill":  False,
            "kill_executed": False,
            "is_locked_today": is_locked_today 
        }
    }
    
    logger.info(f"State Initialized.", tags=["SYS", "INIT"])
    return universal_data