import time
import threading
from datetime import datetime
from web_automation.automate import execute_kill_switch
from web_automation.automate_utils import check_kill_email
from kotak_api.exit_trade import square_off_all_positions
from utils.file_ops import update_kill_history_disk

def _async_verification_worker(universal_data):
    """
    Background thread that polls for email confirmation.
    Runs for 5 minutes then gives up.
    """
    log = universal_data['sys']['log']
    user_id = universal_data['user_id']
    
    log.info("Starting Async Kill Verification (5min timeout)...", tags=["KILL", "ASYNC"])
    
    start_time = time.time()
    found = False
    
    # Poll every 20 seconds for 5 minutes
    while time.time() - start_time < 300:
        if check_kill_email(universal_data, lookback_seconds=600):
            found = True
            break
        time.sleep(20)
        
    # Update Final Status
    status_msg = "VERIFIED" if found else "UNVERIFIED"
    log.info(f"Async Verification Result: {status_msg}", tags=["KILL", "RESULT"])
    
    # 1. Disk Update
    update_kill_history_disk(user_id, found)
    
    # 2. RAM Update
    with universal_data['sys']['lock']:
        universal_data['sys']['config']['kill_history']['verified'] = found
        if found:
            universal_data['sys']['config']['kill_history']['locked_date'] = datetime.now().strftime("%Y-%m-%d")
            universal_data['status']['stage'] = "KILLED (VERIFIED)"
        else:
            universal_data['status']['stage'] = "KILLED (UNVERIFIED)"

def run_kill_switch_service(universal_data):
    log = universal_data['sys']['log']
    
    log.info("Kill Switch Service Armed.", tags=["SVC", "KILL"])
    
    while universal_data['signals']['system_active']:
        with universal_data['sys']['lock']:
            triggered = universal_data['signals']['trigger_kill']
            executed = universal_data['signals']['kill_executed']
            ks_config = universal_data['sys']['config']['kill_switch']
            kill_enabled = ks_config.get('enabled', False)
            auto_sq = ks_config.get('auto_square_off', False)

        if triggered and not executed:
            if not kill_enabled:
                log.warning("RISK TRIGGERED but Kill Switch DISABLED.", tags=["RISK"])
                time.sleep(5)
                continue

            with universal_data['sys']['lock']:
                universal_data['status']['stage'] = "KILLING"
            
            log.info(">>> INITIATING KILL SEQUENCE <<<", tags=["KILL", "EXEC"])
            
            # Parallel Execution
            threads = []
            
            # 1. API Soft Kill
            if auto_sq:
                t1 = threading.Thread(target=square_off_all_positions, args=(universal_data,))
                t1.start()
                threads.append(t1)
                
            # 2. Browser Hard Kill
            browser_success = False
            try:
                execute_kill_switch(universal_data)
                browser_success = True
                with universal_data['sys']['lock']:
                    universal_data['signals']['kill_executed'] = True
            except Exception as e:
                log.critical(f"Browser Kill Failed: {e}", tags=["KILL", "FAIL"])
                with universal_data['sys']['lock']:
                    universal_data['status']['stage'] = "ERROR"
                    universal_data['status']['error_message'] = "Browser Kill Failed"

            # Cleanup API thread
            for t in threads:
                t.join(timeout=5.0)

            if browser_success:
                # 3. Transition to Locked State
                with universal_data['sys']['lock']:
                    universal_data['signals']['is_locked_today'] = True
                    universal_data['status']['stage'] = "KILLED (WAITING)"
                
                # 4. Spawn Detached Verification Worker
                t_verify = threading.Thread(target=_async_verification_worker, args=(universal_data,), daemon=True)
                t_verify.start()
                
                log.info("Browser Action Complete. Verification running in background.", tags=["KILL"])
                
                # 5. Exit this service loop (Job Done), but keep Engine running for Data
                break

        time.sleep(0.5)