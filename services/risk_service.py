import time
from trigger_logic.mtm import calculate_mtm
from trigger_logic.stop_loss import check_sl_status
from web_automation.automate_utils import check_kill_email
from utils.file_ops import update_kill_history_disk
from utils.telegram_notifier import send_alert 

def run_risk_service(universal_data):
    """
    Risk Service: The central evaluator.
    - Continuously calculates MTM using WebSocket ticks.
    - Evaluates dual-trigger logic (MTM + SL).
    - Periodically scans Gmail for external kill triggers.
    """
    log = universal_data['sys']['log']
    user_id = universal_data['user_id']
    
    # Poll rate for logic evaluation (1s is sufficient as WebSocket updates the data)
    poll_interval = 1.0
    
    # Gmail Scan Interval (Slow poll every 2 minutes to avoid IMAP throttling)
    GMAIL_SCAN_INTERVAL = 120 
    last_gmail_check = time.time()
    
    log.info(f"Risk Service Active. Monitoring Limits & SL Status.", tags=["SVC", "RISK"])
    
    while universal_data['signals']['system_active']:
        try:
            # 1. Update Metrics
            # These functions now use the real-time WebSocket cache
            calculate_mtm(universal_data)
            
            # 2. Evaluate Dual-Trigger Logic
            with universal_data['sys']['lock']:
                mtm_current = universal_data['risk']['mtm_current']
                mtm_limit = universal_data['risk']['mtm_limit']
                sl_hit = universal_data['risk']['sl_hit_status']
                triggered = universal_data['signals']['trigger_kill']
                
                ks_enabled = universal_data['sys']['config']['kill_switch'].get('enabled', False)
                sl_required = universal_data['sys']['config']['kill_switch'].get('sell_order_exit_confirmation', True)

            # Check for MTM Breach
            mtm_breach = mtm_current <= mtm_limit

            # Logic: MTM Breach AND (SL Hit OR SL not required)
            if ks_enabled and not triggered:
                should_trigger = mtm_breach and (not sl_required or sl_hit)
                
                if should_trigger:
                    msg = (f"🚨 **RISK TRIGGERED**\n"
                           f"User: {user_id}\n"
                           f"MTM: ₹{mtm_current}\n"
                           f"SL Hit: {'YES' if sl_hit else 'NO (BYPASSED)'}\n"
                           f"Action: Initiating Kill Switch Sequence.")
                    
                    log.warning("MTM/SL Logic Met. Setting Trigger Signal.", tags=["RISK", "ALERT"])
                    send_alert(universal_data, msg)
                    
                    with universal_data['sys']['lock']:
                        universal_data['signals']['trigger_kill'] = True

            # 3. EXTERNAL GMAIL MONITORING (Push Detection)
            # Detects if a kill switch was activated via another machine or mobile
            if time.time() - last_gmail_check > GMAIL_SCAN_INTERVAL:
                # Check for "Kill Switch Activated" email in last 10 minutes
                if check_kill_email(universal_data, lookback_seconds=600):
                    log.warning("EXTERNAL KILL DETECTED! Gmail confirmation found.", tags=["RISK", "EXTERNAL"])
                    send_alert(universal_data, "🛑 **EXTERNAL KILL DETECTED**\nAccount locked via Gmail confirmation.")
                    
                    # Update local disk history
                    update_kill_history_disk(user_id, verified=True)
                    
                    with universal_data['sys']['lock']:
                        universal_data['signals']['is_locked_today'] = True
                        universal_data['signals']['system_active'] = False
                        universal_data['status']['stage'] = "LOCKED (EXTERNAL)"
                    
                    # Exit loop as account is now locked
                    break
                    
                last_gmail_check = time.time()

            time.sleep(poll_interval)

        except Exception as e:
            log.error(f"Risk Loop Error: {e}", tags=["RISK", "ERR"])
            time.sleep(5)

    log.info("Risk Service Stopped", tags=["SVC", "RISK"])