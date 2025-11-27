import time
from web_automation.automate import execute_kill_switch
from kotak_api.exit_trade import square_off_all_positions

def run_kill_switch_service(universal_data):
    """
    Thread: Watches for 'trigger_kill' signal.
    Sequence:
      1. Square Off Open Positions (API)
      2. Execute Browser Kill Switch (Web Automation)
      3. Shutdown System
    """
    log = universal_data['sys']['log']
    
    log.info("Kill Switch Service Armed.", tags=["SVC", "KILL"])
    
    while True:
        # Check active status
        if not universal_data['signals']['system_active']:
            break
            
        # Check Trigger Signal
        with universal_data['sys']['lock']:
            triggered = universal_data['signals']['trigger_kill']
            executed = universal_data['signals']['kill_executed']
            
        if triggered and not executed:
            log.info(">>> TRIGGER RECEIVED. INITIATING SEQUENCE <<<", tags=["KILL", "EXEC"])
            
            # --- STEP 1: AUTO SQUARE OFF (API) ---
            # We do this FIRST because if we disable segments first, the API exit orders might be rejected.
            ks_config = universal_data['sys']['config']['kill_switch']
            
            if ks_config.get('auto_square_off', False):
                try:
                    square_off_all_positions(universal_data)
                except Exception as e:
                    # We log error but continue to Kill Switch (Safety First)
                    log.error(f"Square Off Step Failed: {e}", tags=["KILL", "ERR"])

            # --- STEP 2: BROWSER KILL SWITCH ---
            try:
                execute_kill_switch(universal_data)
                
                with universal_data['sys']['lock']:
                    universal_data['signals']['kill_executed'] = True
                
                log.info("Kill Switch Executed Successfully.", tags=["KILL", "SUCCESS"])
                
            except Exception as e:
                log.critical(f"Kill Switch Execution FAILED: {e}", tags=["KILL", "FAIL"])
            
            # --- STEP 3: SHUTDOWN ---
            log.info("Initiating System Shutdown...", tags=["KILL"])
            with universal_data['sys']['lock']:
                universal_data['signals']['system_active'] = False
            break
            
        time.sleep(0.5) # Fast poll

    log.info("Kill Switch Service Disarmed.", tags=["SVC", "KILL"])