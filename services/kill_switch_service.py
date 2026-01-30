import time
import threading
from datetime import datetime
from web_automation.automate import execute_kill_switch
from web_automation.automate_utils import check_kill_email
from kotak_api.exit_trade import square_off_all_positions
from utils.file_ops import update_kill_history_disk
from utils.telegram_notifier import send_alert 
from utils.os_ops import kill_desktop_browser # Import for Hard Kill

def _async_verification_worker(universal_data):
    log = universal_data['sys']['log']
    start_time = time.time()
    found = False
    while time.time() - start_time < 300:
        if check_kill_email(universal_data, lookback_seconds=600):
            found = True; break
        time.sleep(20)
    
    status_msg = "VERIFIED" if found else "UNVERIFIED"
    log.info(f"Verification Result: {status_msg}", tags=["KILL", "RESULT"])
    send_alert(universal_data, f"{'✅' if found else '⚠️'} **Kill Status: {status_msg}**")
    update_kill_history_disk(universal_data['user_id'], found)
    with universal_data['sys']['lock']:
        if found:
            universal_data['signals']['is_locked_today'] = True
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
            web_config = universal_data['sys']['config'].get('web_automation', {})

        if triggered and not executed:
            if not ks_config.get('enabled', False):
                log.warning("Kill Switch disabled in config.", tags=["RISK"])
                time.sleep(5); continue

            with universal_data['sys']['lock']:
                universal_data['status']['stage'] = "KILLING"
            
            log.info(">>> INITIATING KILL SEQUENCE <<<", tags=["KILL", "EXEC"])
            
            try:
                # 1. API Square Off
                if ks_config.get('auto_square_off'):
                    square_off_all_positions(universal_data)
                
                # 2. Original Playwright Automation
                execute_kill_switch(universal_data)
                
                # 3. NEW: Hard OS Browser Termination (NEW logic)
                if web_config.get('hard_close_browser', False):
                    time.sleep(1) # Cleanup delay
                    kill_desktop_browser(log=log)

                # 4. Mark as Done to stop infinite retries
                with universal_data['sys']['lock']:
                    universal_data['signals']['kill_executed'] = True
                
                # 5. Background Verification
                if universal_data['sys']['config'].get('gmail', {}).get('enable_verification', True):
                    threading.Thread(target=_async_verification_worker, args=(universal_data,), daemon=True).start()
                break 

            except Exception as e:
                log.error(f"Kill Sequence Failure: {e}", tags=["KILL", "FAIL"])
                # We stop the loop here too to prevent continuous browser opening
                with universal_data['sys']['lock']:
                    universal_data['signals']['kill_executed'] = True
                    universal_data['status']['stage'] = "ERROR"

        time.sleep(0.5)