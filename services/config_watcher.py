import time
import json
import os
from pathlib import Path

def run_config_watcher(universal_data):
    """
    Monitors 'config.json'. Reloads ONLY the specific User's section.
    """
    log = universal_data['sys']['log']
    user_id = universal_data['user_id'] 
    
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "source" / "config.json"
    
    last_mtime = 0
    if config_path.exists():
        last_mtime = os.path.getmtime(config_path)

    log.info(f"Config Watcher Active", tags=["SVC", "CONFIG"])

    while True:
        if not universal_data['signals']['system_active']:
            break

        try:
            current_mtime = os.path.getmtime(config_path)
            
            if current_mtime != last_mtime:
                time.sleep(0.1) # Wait for write to finish
                last_mtime = current_mtime
                
                try:
                    with open(config_path, 'r') as f:
                        full_config = json.load(f)
                    
                    if user_id in full_config:
                        new_user_config = full_config[user_id]
                        
                        with universal_data['sys']['lock']:
                            # Update Raw Config
                            universal_data['sys']['config'] = new_user_config
                            
                            # Update Logic Limits
                            raw_limit = new_user_config['kill_switch']['mtm_limit']
                            new_mtm_limit = -abs(float(raw_limit))
                            universal_data['risk']['mtm_limit'] = new_mtm_limit
                        
                        log.info(f"HOT RELOAD: Limits updated to {new_mtm_limit}", tags=["CONFIG"])
                    
                except Exception as e:
                    log.error(f"Config Reload Error: {e}", tags=["CONFIG"])

        except Exception:
            pass
            
        time.sleep(1)