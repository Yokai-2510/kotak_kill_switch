import time
from trigger_logic.mtm import calculate_mtm
from trigger_logic.stop_loss import check_sl_status

def run_risk_service(universal_data):
    """
    Background thread that calculates MTM/SL status and checks against limits.
    If Limit breached + SL Hit -> Sets universal_data['trigger_signal'] = True.
    """
    log = universal_data['logger']
    ks_config = universal_data['config']['kill_switch']
    monitor_config = universal_data['config']['monitoring']
    
    mtm_limit = -abs(ks_config['mtm_limit'])  # Ensure limit is negative (e.g., -10000)
    req_sl_hit = ks_config['trigger_on_sl_hit']
    
    log.info(f"Risk Service Started. Limit: {mtm_limit}, Req SL: {req_sl_hit}", tags=["SVC", "RISK"])
    
    while universal_data['system_active']:
        try:
            # 1. Update Calculations based on latest Data
            calculate_mtm(universal_data)
            check_sl_status(universal_data)
            
            # 2. Check Triggers
            current_mtm = universal_data['state']['mtm']
            sl_hit_status = universal_data['state']['sl_hit']
            
            # Logic: Trigger if MTM is WORSE than limit (e.g. -12000 < -10000)
            mtm_breached = current_mtm <= mtm_limit
            
            # Combined Condition
            # If 'trigger_on_sl_hit' is True, we NEED sl_hit_status to be True
            # If 'trigger_on_sl_hit' is False, we ignore SL status
            condition_met = mtm_breached and (not req_sl_hit or sl_hit_status)
            
            if condition_met:
                log.warning(
                    f"!!! TRIGGER DETECTED !!! MTM: {current_mtm}, SL Hit: {sl_hit_status}", 
                    tags=["RISK", "TRIGGER"]
                )
                universal_data['trigger_signal'] = True
                
                # We do NOT stop the system here. 
                # We let the KillSwitchService handle the execution and shutdown.
                time.sleep(1) 
                
        except Exception as e:
            log.error(f"Risk Loop Error: {e}", tags=["SVC", "RISK"])
            
        time.sleep(monitor_config['poll_interval_seconds'])

    log.info("Risk Service Stopped.", tags=["SVC", "RISK"])