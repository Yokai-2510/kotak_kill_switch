import time
import json
import os
import copy

# Config
INJECT_FILE = "tests/inject.json"
SNAPSHOT_FILE = "state_snapshot.json"

def run_debug_service(universal_data):
    """
    SINGLE DEBUG THREAD:
    1. Checks 'tests/inject.json' -> Updates Memory (Input)
    2. Reads Memory -> Writes FULL UNIVERSE DATA to 'state_snapshot.json' (Output)
    """
    log = universal_data['sys']['log']
    last_mtime = 0

    log.info("Debug Service Started (Full Data Dumper).", tags=["TEST"])

    # Ensure dummy inject file exists
    if not os.path.exists(INJECT_FILE):
        with open(INJECT_FILE, 'w') as f:
            json.dump({"risk": {"mtm_current": 0, "sl_hit_status": False}}, f, indent=2)

    while True:
        if not universal_data['signals']['system_active']:
            break

        try:
            # --- TASK A: INJECTOR (File -> Memory) ---
            curr_mtime = os.path.getmtime(INJECT_FILE)
            if curr_mtime != last_mtime:
                last_mtime = curr_mtime
                time.sleep(0.1) 
                
                with open(INJECT_FILE, 'r') as f:
                    data = json.load(f)

                with universal_data['sys']['lock']:
                    if "risk" in data:
                        if "mtm_current" in data['risk']:
                            val = float(data['risk']['mtm_current'])
                            universal_data['risk']['mtm_current'] = val
                            log.warning(f"💉 INJECTED MTM: {val}", tags=["TEST"])
                        
                        if "sl_hit_status" in data['risk']:
                            val = bool(data['risk']['sl_hit_status'])
                            universal_data['risk']['sl_hit_status'] = val
                            log.warning(f"💉 INJECTED SL: {val}", tags=["TEST"])


            # --- TASK B: FULL DUMPER (Memory -> File) ---
            with universal_data['sys']['lock']:
                # Construct the full dump manually to exclude Lock/API/Logger objects
                snapshot = {
                    "timestamp": time.strftime("%H:%M:%S"),
                    
                    # 1. FULL RISK DATA
                    "risk": copy.deepcopy(universal_data['risk']),
                    
                    # 2. FULL SIGNALS
                    "signals": copy.deepcopy(universal_data['signals']),
                    
                    # 3. FULL MARKET DATA (Positions, Orders, Quotes)
                    "market": copy.deepcopy(universal_data['market']),
                    
                    # 4. CONFIG (From Sys)
                    "config": copy.deepcopy(universal_data['sys']['config'])
                }

            # Atomic Write
            temp_file = SNAPSHOT_FILE + ".tmp"
            with open(temp_file, 'w') as f:
                json.dump(snapshot, f, indent=2)
            os.replace(temp_file, SNAPSHOT_FILE)

        except Exception as e:
            # Ignore IO errors during file access
            pass
        
        time.sleep(1)