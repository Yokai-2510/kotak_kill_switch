from kotak_api.positions import sync_positions
from kotak_api.orders import sync_orders
from kotak_api.quotes import sync_ltp
from trigger_logic.mtm import calculate_mtm
from trigger_logic.stop_loss import check_sl_status

def run_initial_system_check(universal_data):
    """
    Linearly syncs data AND runs logic verification before threads start.
    """
    log = universal_data['sys']['log']
    
    log.info(">>> Executing Initial System Check...", tags=["CHECK"])

    # --- 1. DATA SYNC ---
    sync_positions(universal_data)
    sync_orders(universal_data)
    
    # Only fetch quotes if positions exist
    if universal_data['market']['positions']:
        sync_ltp(universal_data)

    # --- 2. LOGIC CHECK ---
    calculate_mtm(universal_data)
    check_sl_status(universal_data)

    # Log Snapshot
    with universal_data['sys']['lock']:
        mtm = universal_data['risk']['mtm_current']
        sl = universal_data['risk']['sl_hit_status']
        
    log.info(f"Check Complete. MTM: {mtm} | SL Hit: {sl}", tags=["CHECK"])