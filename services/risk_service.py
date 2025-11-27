import time
from trigger_logic.mtm import calculate_mtm
from trigger_logic.stop_loss import check_sl_status

def run_risk_service(universal_data):
    """
    Thread: Calculates Logic. Sets 'trigger_kill' signal if limits breached.
    """
    log = universal_data['sys']['log']
    ks_config = universal_data['sys']['config']['kill_switch']
    
    req_sl_hit = ks_config['trigger_on_sl_hit']
    poll_interval = universal_data['sys']['config']['monitoring']['poll_interval_seconds']
    
    log.info("Risk Service Started.", tags=["SVC", "RISK"])
    
    while True:
        if not universal_data['signals']['system_active']:
            break
            
        try:
            # 1. Update Metrics
            calculate_mtm(universal_data)
            check_sl_status(universal_data)
            
            # 2. Read Metrics Safely
            with universal_data['sys']['lock']:
                mtm_current = universal_data['risk']['mtm_current']
                mtm_limit = universal_data['risk']['mtm_limit']
                sl_hit_status = universal_data['risk']['sl_hit_status']
                already_triggered = universal_data['signals']['trigger_kill']

            # 3. Evaluate Trigger
            if not already_triggered:
                # Limit Logic: Since limits are negative (e.g., -10000), 
                # Breach happens if current (-12000) <= limit (-10000)
                mtm_breach = mtm_current <= mtm_limit
                
                # Composite Condition
                should_trigger = mtm_breach and (not req_sl_hit or sl_hit_status)
                
                if should_trigger:
                    log.warning(
                        f"!!! RISK TRIGGER !!! MTM: {mtm_current}, SL: {sl_hit_status}", 
                        tags=["RISK", "ALERT"]
                    )
                    # Set Signal
                    with universal_data['sys']['lock']:
                        universal_data['signals']['trigger_kill'] = True
                        
        except Exception as e:
            log.error(f"Risk Loop Error: {e}", tags=["SVC", "RISK"])
            
        time.sleep(poll_interval)

    log.info("Risk Service Stopped.", tags=["SVC", "RISK"])