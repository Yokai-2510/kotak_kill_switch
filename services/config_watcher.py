import time
import json
import os
from pathlib import Path

def run_config_watcher(universal_data):
    """
    Thread: Monitors 'source/config.json' for changes.
    If changed:
      1. Reloads JSON from disk.
      2. Updates universal_data['sys']['config'] (RAM).
      3. Recalculates Derived Risk Limits (RAM).
    """
    log = universal_data['sys']['log']
    
    # Locate Config File
    root_dir = Path(__file__).parent.parent
    config_path = root_dir / "source" / "config.json"
    
    last_mtime = 0
    
    # Initialize timestamp
    if config_path.exists():
        last_mtime = os.path.getmtime(config_path)

    log.info("Config Watcher Started. Hot-Reload Active.", tags=["SVC", "CONFIG"])

    while True:
        # Check active status
        if not universal_data['signals']['system_active']:
            break

        try:
            # Check for modification
            current_mtime = os.path.getmtime(config_path)
            
            if current_mtime != last_mtime:
                # File Changed!
                time.sleep(0.1) # Tiny wait to ensure write is complete
                last_mtime = current_mtime
                
                # Attempt Load
                try:
                    with open(config_path, 'r') as f:
                        new_config = json.load(f)
                    
                    # --- CRITICAL UPDATE SECTION ---
                    with universal_data['sys']['lock']:
                        
                        # 1. Update Raw Config
                        universal_data['sys']['config'] = new_config
                        
                        # 2. Update Derived Risk Values
                        # (Convert positive limit to negative float for logic comparison)
                        raw_limit = new_config['kill_switch']['mtm_limit']
                        new_mtm_limit = -abs(float(raw_limit))
                        
                        universal_data['risk']['mtm_limit'] = new_mtm_limit
                        
                        # 3. Update Test Flags
                        # (Any other derived flags can be updated here)
                    
                    log.info(f"HOT RELOAD: MTM Limit updated to {new_mtm_limit}", tags=["CONFIG", "UPDATE"])
                    
                except json.JSONDecodeError:
                    log.error("Config File is invalid JSON. Ignoring update.", tags=["CONFIG", "ERROR"])
                except Exception as e:
                    log.error(f"Config Update Failed: {e}", tags=["CONFIG", "ERROR"])

        except FileNotFoundError:
            log.error("Config file not found!", tags=["CONFIG", "ERROR"])
        except Exception as e:
            # Keep thread alive even if OS errors occur
            pass
            
        time.sleep(1) # Poll frequency