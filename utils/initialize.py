import json
import sys
import threading
from datetime import datetime
from pathlib import Path
from utils.logger import setup_logger

def load_json_file(filepath):
    path = Path(filepath)
    if not path.exists():
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def save_json_file(filepath, data):
    """Helper to write back config updates safely."""
    path = Path(filepath)
    try:
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving JSON: {e}")

def create_bot_state(user_id):
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "source" / "config.json"
    
    full_config = load_json_file(config_path)
    full_creds = load_json_file(root_dir / "source" / "credentials.json")

    # Basic Validation
    if user_id not in full_config or user_id not in full_creds:
        print(f"CRITICAL: User ID {user_id} missing in Config or Creds.")
        sys.exit(1)

    user_config = full_config[user_id]
    user_creds = full_creds[user_id]

    # Initialize Logger
    logger = setup_logger(user_id, user_creds)
    
    # ---------------------------------------------------------
    # PART A LOGIC: MIDNIGHT RESET & LOCKOUT CHECK
    # ---------------------------------------------------------
    kill_hist = user_config.get('kill_history', {})
    locked_date_str = kill_hist.get('locked_date')
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    is_locked_today = False
    
    # Check Logic
    if locked_date_str:
        if locked_date_str == today_str:
            # Date matches today. Enforce Lock.
            is_locked_today = True
            logger.warning(f"Account is LOCKED for the day (Killed on {locked_date_str}).", tags=["INIT", "LOCK"])
        else:
            # It is an old date. Log it, but DO NOT LOCK and DO NOT WIPE.
            # This preserves the date for the "Status" tab history.
            is_locked_today = False
            logger.info(f"Previous Kill detected on {locked_date_str}. Resetting lock for New Day ({today_str}).", tags=["INIT", "RESET"])
    
    # ---------------------------------------------------------
    
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