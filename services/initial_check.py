# services/initial_check.py

from kotak_api.positions import sync_positions
from kotak_api.orders import sync_orders
from kotak_api.quotes import sync_ltp

# NEW IMPORTS
from trigger_logic.mtm import calculate_mtm
from trigger_logic.stop_loss import check_sl_status

def run_initial_system_check(universal_data):
    """
    Linearly syncs data AND runs logic verification.
    """
    log = universal_data['logger']
    
    log.info(">>> Executing Initial System Check...", tags=["CHECK"])

    # --- 1. DATA SYNC ---
    sync_positions(universal_data)
    pos_count = len(universal_data['state']['positions'])
    log.info(f"Positions Synced: {pos_count}", tags=["CHECK", "POS"])

    sync_orders(universal_data)
    ord_count = len(universal_data['state']['orders'])
    log.info(f"Orders Synced: {ord_count}", tags=["CHECK", "ORD"])

    if pos_count > 0:
        sync_ltp(universal_data)
        quote_count = len(universal_data['state']['quotes'])
        log.info(f"Quotes Synced: {quote_count}", tags=["CHECK", "QT"])
    else:
        log.info("No positions, skipping Quotes.", tags=["CHECK", "QT"])

    # --- 2. LOGIC CHECK ---
    log.info(">>> Verifying Risk Logic...", tags=["CHECK"])
    
    calculate_mtm(universal_data)
    mtm = universal_data['state']['mtm']
    log.info(f"Calculated MTM: {mtm}", tags=["CHECK", "MTM"])
    
    check_sl_status(universal_data)
    sl_status = universal_data['state']['sl_hit']
    log.info(f"SL Hit Status: {sl_status}", tags=["CHECK", "SL"])

    log.info(">>> Initial Check Complete.", tags=["CHECK"])