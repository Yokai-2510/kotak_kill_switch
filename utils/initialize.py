import json
import sys
from pathlib import Path
from utils.logger import setup_logger

def load_json_file(filepath):
    """Helper to load JSON with basic error checking."""
    path = Path(filepath)
    if not path.exists():
        print(f"CRITICAL: Configuration file missing at {path}")
        sys.exit(1)
    
    with open(path, 'r') as f:
        return json.load(f)

def initialize_system():
    """
    Bootstraps the application state.
    1. Setup Logger
    2. Load Config & Credentials
    3. Initialize Empty State
    """
    logger = setup_logger()
    
    # Resolve paths relative to project root
    # Assumes utils/initialize.py -> parent = utils -> parent = Project_Root
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "source" / "config.json"
    creds_path = root_dir / "source" / "credentials.json"
    
    logger.info("Initializing system...", tags=["INIT"])
    
    config = load_json_file(config_path)
    creds = load_json_file(creds_path)
    
    # Universal Data Structure
    universal_data = {
        'config': config,
        'creds': creds,
        'logger': logger,
        'client': None,          # Populated by authentication
        'system_active': True,   # Controls the main loop
        
        # Dynamic State
        'state': {
            'mtm': 0.0,
            'sl_hit': False,
            'positions': [],
            'orders': [],
            'quotes': {},
            'kill_switch_triggered': False
        },
        
        # Threading signals
        'trigger_signal': False
    }
    
    logger.info(f"Configuration loaded. Mode: {config['kill_switch']['execution_mode']}", tags=["INIT"])
    return universal_data