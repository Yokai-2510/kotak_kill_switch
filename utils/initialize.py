import json
import sys
import threading
from pathlib import Path
from utils.logger import setup_logger

def load_json_file(filepath):
    path = Path(filepath)
    if not path.exists():
        print(f"CRITICAL: Configuration file missing at {path}")
        sys.exit(1)
    with open(path, 'r') as f:
        return json.load(f)

def create_bot_state(user_id):
    """
    Creates the 'universal_data' dictionary specifically for ONE user.
    """
    root_dir = Path(__file__).parent.parent
    
    # Load FULL Registry files
    full_config = load_json_file(root_dir / "source" / "config.json")
    full_creds = load_json_file(root_dir / "source" / "credentials.json")

    # Validation
    if user_id not in full_config or user_id not in full_creds:
        print(f"ERROR: User ID {user_id} not found in config/creds.")
        sys.exit(1)

    user_config = full_config[user_id]
    user_creds = full_creds[user_id]

    # Setup Logger with Wipe Logic
    log_conf = user_config.get('logging', {})
    log_file = log_conf.get('file', f'logs/{user_id}.log')
    wipe = log_conf.get('wipe_on_start', False)
    
    full_log_path = root_dir / log_file
    logger = setup_logger(user_id, str(full_log_path), wipe_on_start=wipe)
    
    # Calculate MTM Limit
    mtm_limit = -abs(float(user_config['kill_switch']['mtm_limit']))

    # === THE UNIVERSAL STATE (Per User) ===
    universal_data = {
        "user_id": user_id,
        
        # [1] RESOURCES
        "sys": {
            "config":   user_config,
            "creds":    user_creds,
            "log":      logger,
            "api":      None,
            "lock":     threading.Lock()
        },
        
        # [NEW] STATUS FLAGS
        "status": {
            "stage": "INIT",        # INIT, AUTHING, RUNNING, ERROR, STOPPED
            "auth_success": False,
            "services_running": False,
            "error_message": None,
            "last_updated": None
        },

        # [2] MARKET DATA
        "market": {
            "positions": [], "orders": [], "quotes": {},
            "raw": { "positions": None, "orders": None, "quotes": None }
        },

        # [3] RISK METRICS
        "risk": {
            "mtm_current": 0.0, "mtm_limit": mtm_limit, "mtm_distance": 0.0, "sl_hit_status": False
        },

        # [4] SIGNALS
        "signals": {
            "system_active": True,
            "trigger_kill":  False,
            "kill_executed": False
        }
    }
    
    logger.info(f"State initialized. MTM Limit: {mtm_limit}", tags=["INIT"])
    return universal_data