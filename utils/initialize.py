# utils/initialize.py
import json
import logging
from pathlib import Path

def load_json(path):
    with open(path, 'r') as f:
        return json.load(f)

def setup_logging(log_cfg):
    Path(log_cfg['file']).parent.mkdir(exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_cfg['level']),
        format='%(asctime)s | %(levelname)s | %(message)s',
        handlers=[
            logging.FileHandler(log_cfg['file']),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('kill_switch')

def initialize(config_path="source/config.json", creds_path="source/credentials.json"):
    """Initialize and return universal app state"""
    config = load_json(config_path)
    creds = load_json(creds_path)
    logger = setup_logging(config['logging'])
    
    app = {
        'config': config,
        'creds': creds,
        'logger': logger,
        'client': None,
        'state': {
            'kill_switch_triggered': False,
            'current_mtm': 0.0,
            'sl_hit': False,
            'positions': [],
            'orders': []
        }
    }
    
    logger.info("Initialized app state")
    return app


if __name__ == "__main__":
    app = initialize()
    print(f"Config loaded: {list(app['config'].keys())}")
    print(f"Creds loaded: {list(app['creds'].keys())}")