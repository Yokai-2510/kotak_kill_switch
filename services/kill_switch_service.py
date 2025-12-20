import time
import threading
from datetime import datetime
from web_automation.automate import execute_kill_switch
from web_automation.automate_utils import check_kill_email
from kotak_api.exit_trade import square_off_all_positions
from utils.file_ops import update_kill_history_disk
from utils.telegram_notifier import send_alert 

def _async_verification_worker(universal_data):
    """Background worker for email verification."""
    log = universal_data['sys']['log']
    user_id = universal_data['user_id']
    
    start_time = time.time()
    found = False
    
    # Poll for 5 minutes
    while time.time() - start_time < 300:
        if check_kill_email(universal_data, lookback_seconds=600):
            found = True
            break
        time.sleep(20)
    
    # Final Result
    status_msg = "VERIFIED" if found else "UNVERIFIED"
    log.info(f"Verification Result: {status_msg}", tags=["KILL", "RESULT"])
    
    # Notify
    alert_icon = "✅" if found else "⚠️"
    send_alert(universal_data, f"{alert_icon} **Kill Status: {status_msg}**\nAccount Locked: {found}")

    update_kill_history_disk(user_id, found)
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
            gmail_conf = universal_data['sys']['config'].get('gmail', {})
            verify_enabled = gmail_conf.get('enable_verification', True)

        if triggered and not executed:
            if not kill_enabled:
                log.warning("RISK TRIGGERED but Kill Switch DISABLED.", tags=["RISK"])
                time.sleep(5)
                continue

            with universal_data['sys']['lock']:
                universal_data['status']['stage'] = "KILLING"
            
            # Notify Start
            send_alert(universal_data, "⚔️ **KILL SWITCH ACTIVATED**\nExecuting Auto-Square Off & Browser Kill.")
            log.info(">>> INITIATING KILL SEQUENCE <<<", tags=["KILL", "EXEC"])
            
            threads = []
            if auto_sq:
                t1 = threading.Thread(target=square_off_all_positions, args=(universal_data,))
                t1.start()
                threads.append(t1)
                
            browser_success = False
            try:
                execute_kill_switch(universal_data)
                browser_success = True
                with universal_data['sys']['lock']:
                    universal_data['signals']['kill_executed'] = True
            except Exception as e:
                log.critical(f"Browser Kill Failed: {e}", tags=["KILL", "FAIL"])
                send_alert(universal_data, f"❌ **BROWSER KILL FAILED**\nError: {e}")
                with universal_data['sys']['lock']:
                    universal_data['status']['stage'] = "ERROR"
                    universal_data['status']['error_message'] = "Browser Kill Failed"

            for t in threads: t.join(timeout=5.0)

            if browser_success:
                if verify_enabled:
                    with universal_data['sys']['lock']:
                        universal_data['signals']['is_locked_today'] = True
                        universal_data['status']['stage'] = "KILLED (WAITING)"
                    
                    t_verify = threading.Thread(target=_async_verification_worker, args=(universal_data,), daemon=True)
                    t_verify.start()
                else:
                    # Verification Disabled
                    send_alert(universal_data, "✅ **Kill Complete** (Verification Disabled). Account Locked.")
                    update_kill_history_disk(universal_data['user_id'], True)
                    with universal_data['sys']['lock']:
                        universal_data['signals']['is_locked_today'] = True
                        universal_data['sys']['config']['kill_history']['verified'] = True
                        universal_data['sys']['config']['kill_history']['locked_date'] = datetime.now().strftime("%Y-%m-%d")
                        universal_data['status']['stage'] = "KILLED (NO VERIFY)"
                
                break

        time.sleep(0.5)