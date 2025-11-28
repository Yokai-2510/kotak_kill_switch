"""
KOTAK KILL SWITCH - ORCHESTRATOR
Linear Init -> Auth -> Initial Check -> Threaded Services
"""

import sys
import threading
import time

# --- PHASE 1: INIT ---
from utils.initialize import initialize_system

# --- PHASE 2: AUTHENTICATION ---
from kotak_api.client_login import authenticate_client

# --- PHASE 3: PRE-FLIGHT CHECK ---
from services.initial_check import run_initial_system_check

# --- PHASE 4: SERVICES ---
from services.data_service import run_data_service
from services.risk_service import run_risk_service
from services.kill_switch_service import run_kill_switch_service
from services.config_watcher import run_config_watcher 

# --- PHASE 5: TESTING ---
from tests.injector import run_debug_service as run_state_injector 


def main():

    # ====================  1. INITIALIZATION & AUTH ====================
    
    # Initialize Universal Dict
    universal_data = initialize_system()
    log = universal_data['sys']['log'].info

    log("=== SYSTEM STARTUP ===", tags=["MAIN"])
    
    # Authenticate
    authenticate_client(universal_data)


    # ====================  2. INITIAL SYSTEM CHECK ====================
    
    log(">>> Running Pre-flight Checks...", tags=["MAIN"])
    run_initial_system_check(universal_data)
    
    # Debug Log for Initial State
    with universal_data['sys']['lock']:
        current_mtm = universal_data['risk']['mtm_current']
        sl_status = universal_data['risk']['sl_hit_status']
        
    log(f"Pre-flight State -> MTM: {current_mtm} | SL Hit: {sl_status}", tags=["DEBUG"])


    # ====================  3. START SERVICE THREADS ====================
    
    log(">>> Starting Services...", tags=["MAIN"])

    # Thread 1: Data Service
    data_thread = threading.Thread(target=run_data_service, args=(universal_data,), name="DataThread", daemon=True)
    data_thread.start()

    # Thread 2: Risk Service
    risk_thread = threading.Thread(target=run_risk_service, args=(universal_data,), name="RiskThread", daemon=True)
    risk_thread.start()

    # Thread 3: Kill Switch Service
    kill_thread = threading.Thread(target=run_kill_switch_service, args=(universal_data,), name="KillSwitchThread", daemon=True)
    kill_thread.start()

    # Thread 4: Config Watcher (Hot Reload)
    config_thread = threading.Thread(target=run_config_watcher, args=(universal_data,), name="ConfigThread", daemon=True)
    config_thread.start()

    # Thread 5: Injector Service (Debug)
    injector_thread = threading.Thread(target=run_state_injector, args=(universal_data,), name="InjectorThread", daemon=True)
    injector_thread.start()


    # ====================  4. MAIN LOOP ====================
    
    log("System Active. Monitoring...", tags=["MAIN"])
    
    try:
        while universal_data['signals']['system_active']:
            time.sleep(1)
            
    except KeyboardInterrupt:
        log("User Interrupted. Stopping...", tags=["MAIN"])
        with universal_data['sys']['lock']:
            universal_data['signals']['system_active'] = False

    log("=== SYSTEM SHUTDOWN ===", tags=["MAIN"])


if __name__ == "__main__":
    main()