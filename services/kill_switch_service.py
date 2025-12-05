import time
from web_automation.automate import execute_kill_switch
from kotak_api.exit_trade import square_off_all_positions

def run_kill_switch_service(universal_data):
    """
    Watches for 'trigger_kill'.
    Checks if Kill Switch is ENABLED in config before executing.
    """
    log = universal_data['sys']['log']
    
    log.info("Kill Switch Service Armed.", tags=["SVC", "KILL"])
    
    while True:
        if not universal_data['signals']['system_active']:
            break
            
        # Get Signals & Config
        with universal_data['sys']['lock']:
            triggered = universal_data['signals']['trigger_kill']
            executed = universal_data['signals']['kill_executed']
            
            # Dynamic check of the enabled flag
            ks_config = universal_data['sys']['config']['kill_switch']
            kill_enabled = ks_config.get('enabled', False)
            auto_sq_off = ks_config.get('auto_square_off', False)
            
        if triggered and not executed:
            
            # --- GUARD CLAUSE ---
            if not kill_enabled:
                log.warning(">>> RISK LIMIT HIT! Kill Switch is DISABLED. Taking NO Action. <<<", tags=["RISK", "MONITOR"])
                time.sleep(5) # Prevent log spam
                continue
            
            # --- 1. SET STATUS TO PROCESSING ---
            with universal_data['sys']['lock']:
                universal_data['status']['stage'] = "KILLING"

            # --- EXECUTION SEQUENCE ---
            log.info(">>> TRIGGER RECEIVED. INITIATING KILL SEQUENCE <<<", tags=["KILL", "EXEC"])
            
            # 1. Auto Square Off (API)
            if auto_sq_off:
                try:
                    square_off_all_positions(universal_data)
                except Exception as e:
                    log.error(f"Square Off Step Failed: {e}", tags=["KILL", "ERR"])

            # 2. Browser Kill Switch
            try:
                execute_kill_switch(universal_data)
                
                with universal_data['sys']['lock']:
                    universal_data['signals']['kill_executed'] = True
                    universal_data['status']['stage'] = "KILLED" # <--- Critical: Set final state
                
                log.info("Kill Switch Executed Successfully.", tags=["KILL", "SUCCESS"])
                
            except Exception as e:
                log.critical(f"Kill Switch Execution FAILED: {e}", tags=["KILL", "FAIL"])
                with universal_data['sys']['lock']:
                    universal_data['status']['stage'] = "ERROR"
                    universal_data['status']['error_message'] = "Kill Execution Failed"
            
            # 3. System Shutdown
            log.info("Initiating System Shutdown in 3 seconds...", tags=["KILL"])
            
            # --- THE FIX: WAIT FOR GUI TO UPDATE ---
            time.sleep(3.0) 
            
            with universal_data['sys']['lock']:
                universal_data['signals']['system_active'] = False
            break
            
        time.sleep(0.5)

    log.info("Kill Switch Service Disarmed.", tags=["SVC", "KILL"])