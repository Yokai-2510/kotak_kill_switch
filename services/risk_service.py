import time
from trigger_logic.mtm import calculate_mtm
from trigger_logic.stop_loss import check_sl_status
from web_automation.automate_utils import check_kill_email
from utils.file_ops import update_kill_history_disk

def run_risk_service(universal_data):
    log = universal_data['sys']['log']
    user_id = universal_data['user_id']
    
    poll_interval = universal_data['sys']['config']['monitoring']['poll_interval_seconds']
    
    log.info(f"Risk Service Started.", tags=["SVC", "RISK"])
    
    last_log_time = 0
    last_email_check = time.time()

    while universal_data['signals']['system_active']:
        try:
            # 1. Standard Risk Logic
            ks_config = universal_data['sys']['config']['kill_switch']
            req_sl_conf = ks_config.get('sell_order_exit_confirmation', True)
            
            calculate_mtm(universal_data)
            check_sl_status(universal_data)
            
            with universal_data['sys']['lock']:
                mtm_current = universal_data['risk']['mtm_current']
                mtm_limit = universal_data['risk']['mtm_limit']
                sl_hit = universal_data['risk']['sl_hit_status']
                triggered = universal_data['signals']['trigger_kill']

            # Heartbeat
            if time.time() - last_log_time > 60:
                log.info(f"Status: MTM={mtm_current} / Limit={mtm_limit} | SL_Hit={sl_hit}", tags=["RISK", "HB"])
                last_log_time = time.time()

            if not triggered:
                mtm_breach = mtm_current <= mtm_limit
                should_trigger = mtm_breach and (not req_sl_conf or sl_hit)
                
                if should_trigger:
                    log.warning(f"!!! TRIGGER !!! MTM: {mtm_current}", tags=["RISK", "ALERT"])
                    with universal_data['sys']['lock']:
                        universal_data['signals']['trigger_kill'] = True

            # 2. External Kill Detection (Every 2 Minutes)
            if time.time() - last_email_check > 120:
                # Look back 5 minutes for safety
                if check_kill_email(universal_data, lookback_seconds=300):
                    log.warning("External Kill Detected via Email!", tags=["RISK", "EXTERNAL"])
                    
                    # Lockout Sequence
                    update_kill_history_disk(user_id, True)
                    
                    with universal_data['sys']['lock']:
                        universal_data['signals']['is_locked_today'] = True
                        universal_data['signals']['system_active'] = False
                        universal_data['status']['stage'] = "KILLED (EXTERNAL)"
                    break
                
                last_email_check = time.time()
            
            time.sleep(poll_interval)

        except Exception as e:
            log.error(f"Loop Error: {e}", tags=["RISK"])
            time.sleep(5)

    log.info("Service Stopped", tags=["SVC", "RISK"])