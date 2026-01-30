import json
import sys
import threading
from datetime import datetime
from pathlib import Path
from utils.logger import setup_logger
from web_automation.automate_utils import check_kill_email

# =========================================================
#  DEFAULT CONFIG TEMPLATE
# =========================================================
# This ensures new users or repaired configs have the right keys.
DEFAULT_CONFIG_UNIT = {
    "account_active": False,
    "account_name": "New Account",
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
        "poll_interval_seconds": 30,
        "off_market_interval_seconds": 60
    },
    "logging": {
        "level": "INFO",
        "wipe_on_start": True,
        "snapshot_interval": 30
    },
    "gmail": {
        "timeout_seconds": 120,
        "otp_subject": "OTP",
        "kill_subject": "Kill Switch Activated",
        "enable_verification": True
    },
    "web_automation": {
        "login_url": "https://neo.kotaksecurities.com/Login",
        "search_timeout": 20000,
        "hard_close_browser": True, # For OS Browser Termination
        "browser": {
            "headless": False,
            "viewport": { "width": 1366, "height": 768 },
            "args": ["--disable-blink-features=AutomationControlled"]
        },
        "flow_steps": [] 
    }
}

# =========================================================
#  FILE OPERATIONS
# =========================================================

def load_json_file(filepath):
    path = Path(filepath)
    if not path.exists(): return {}
    with open(path, 'r') as f:
        try: return json.load(f)
        except: return {}

def save_json_file(filepath, data):
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

# =========================================================
#  STATE INITIALIZATION
# =========================================================

def create_bot_state(user_id):
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "source" / "config.json"
    creds_path = root_dir / "source" / "credentials.json"
    
    full_config = load_json_file(config_path)
    full_creds = load_json_file(creds_path)

    if user_id not in full_config or user_id not in full_creds:
        print(f"CRITICAL: User ID {user_id} missing in local files.")
        sys.exit(1)

    user_config = full_config[user_id]
    user_creds = full_creds[user_id]
    logger = setup_logger(user_id, user_creds)
    
    today_str = datetime.now().strftime("%Y-%m-%d")
    is_locked_today = False
    
    # --- 1. CHECK DISK HISTORY ---
    kill_hist = user_config.get('kill_history', {})
    if kill_hist.get('locked_date') == today_str:
        is_locked_today = True
        logger.warning(f"Engine locked via local history (Killed Today).", tags=["INIT", "LOCK"])

    # --- 2. AUTOMATIC GMAIL DETECTION ---
    # Scans Gmail for a "Kill Switch" email from today to force a lock
    if not is_locked_today:
        logger.info("Startup Scan: Searching Gmail for Kill confirmation...", tags=["INIT", "GMAIL"])
        
        # Build temp state for the email check utility
        temp_state = {"sys": {"creds": user_creds, "config": user_config}}
        
        # Search lookback of 12 hours (43200 seconds)
        if check_kill_email(temp_state, lookback_seconds=43200):
            is_locked_today = True
            logger.warning("GMAIL DETECTION: External Kill Email found. Locking account.", tags=["INIT", "GMAIL"])
            
            # Sync to local config
            user_config['kill_history'] = {
                "locked_date": today_str,
                "timestamp": f"Detected via Gmail @ {datetime.now().strftime('%H:%M:%S')}",
                "verified": True
            }
            save_json_file(config_path, full_config)

    # Risk Metrics setup
    mtm_limit = -abs(float(user_config.get('kill_switch', {}).get('mtm_limit', 5000)))

    # =========================================================
    #  CONSTRUCT UNIVERSAL STATE
    # =========================================================
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
            "error_message": "Account Killed / Locked Today" if is_locked_today else None,
            "session_start_time": None
        },
        "market": {
            "positions": [], 
            "orders": [], 
            "quotes": {}, 
            "index_spot": 0.0, # Bank Nifty Spot Heartbeat
            "subscribed_tokens": [], # For WebSocket tracking
            # --- CRITICAL FIX: Initialize raw storage to prevent REST sync crashes ---
            "raw": {
                "positions": None,
                "orders": None,
                "quotes": None
            }
        },
        "risk": {
            "mtm_current": 0.0, 
            "mtm_limit": mtm_limit, 
            "sl_hit_status": False
        },
        "signals": {
            "system_active": False,
            "trigger_kill":  False,
            "kill_executed": False,
            "is_locked_today": is_locked_today 
        }
    }
    
    logger.info(f"State Initialized Successfully.", tags=["SYS", "INIT"])
    return universal_data