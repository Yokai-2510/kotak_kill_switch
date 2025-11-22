import time

# Placeholder for Phase 4 Imports
# from web_automation.kill_trigger import execute_browser_kill

def run_kill_switch_service(universal_data):
    """
    Background thread that waits for 'trigger_signal'.
    When triggered:
      1. (Future) Executes Browser Automation to lock account.
      2. Sets universal_data['system_active'] = False to shut down all threads.
    """
    log = universal_data['logger']
    config = universal_data['config']['kill_switch']
    
    log.info("Kill Switch Service Armed & Waiting...", tags=["SVC", "KILL"])
    
    while universal_data['system_active']:
        
        if universal_data['trigger_signal']:
            log.info(">>> INITIATING KILL SWITCH SEQUENCE <<<", tags=["KILL", "EXEC"])
            
            if config['dry_run']:
                log.info("[DRY RUN] Kill Switch would execute here.", tags=["KILL", "DRY"])
            else:
                log.info("Executing Live Kill Switch...", tags=["KILL", "LIVE"])
                # TODO: Phase 4 - Call Browser Automation Here
                # execute_browser_kill(universal_data)
                pass
            
            # SHUTDOWN SEQUENCE
            log.info("Stopping System...", tags=["KILL", "SHUTDOWN"])
            universal_data['system_active'] = False
            break
            
        time.sleep(0.5) # Fast poll for high responsiveness

    log.info("Kill Switch Service Disarmed.", tags=["SVC", "KILL"])