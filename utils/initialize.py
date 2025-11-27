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

def initialize_system():
    logger = setup_logger()
    root_dir = Path(__file__).parent.parent
    config = load_json_file(root_dir / "source" / "config.json")
    creds = load_json_file(root_dir / "source" / "credentials.json")
    
    mtm_limit = -abs(float(config['kill_switch']['mtm_limit']))

    universal_data = {
        # [1] RESOURCES
        "sys": {
            "config":   config,
            "creds":    creds,
            "log":      logger,
            "api":      None,
            "lock":     threading.Lock()
        },

        # [2] MARKET DATA (Updated Structure)
        "market": {
            "positions": [],
            "orders":    [],
            "quotes":    {},
            
            # NEW: Raw API Response Storage
            "raw": {
                "positions": None,
                "orders":    None,
                "quotes":    None
            }
        },

        # [3] RISK METRICS
        "risk": {
            "mtm_current":   0.0,
            "mtm_limit":     mtm_limit,
            "mtm_distance":  0.0,
            "sl_hit_status": False
        },

        # [4] SIGNALS
        "signals": {
            "system_active": True,
            "trigger_kill":  False,
            "kill_executed": False
        }
    }
    
    logger.info(f"System Initialized. MTM Limit: {mtm_limit}", tags=["INIT"])
    return universal_data