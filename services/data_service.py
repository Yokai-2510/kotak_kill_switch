import time
import datetime
from kotak_api.positions import sync_positions
from kotak_api.orders import sync_orders
from kotak_api.client_login import authenticate_client

def run_data_service(universal_data):
    """
    Hybrid Data Service (Consistency Mode).
    Responsibility: 
    1. Periodic 'Source of Truth' sync for Positions and Order Book.
    2. Session health monitoring and Auto-Re-login.
    NOTE: High-speed LTP and SL updates are now handled by the WebSocket Service.
    """
    log = universal_data['sys']['log']
    
    # 1. Load Configuration (We now use longer intervals)
    mon_conf = universal_data['sys']['config'].get('monitoring', {})
    retry_conf = mon_conf.get('retry_strategy', {})
    
    # Defaults: Slow down polling to reduce server load/disconnections
    # We sync positions every 30s to find new tokens for the WebSocket to subscribe to.
    poll_consistency = 30 
    poll_idle = 60
    
    max_retries = retry_conf.get('max_retries', 5)
    base_delay = retry_conf.get('base_delay', 2)
    max_delay = retry_conf.get('max_delay', 10)
    
    consecutive_errors = 0
    log.info("Data Service started in Consistency Mode (30s Sync).", tags=["SVC", "DATA"])
    
    while universal_data['signals']['system_active']:
        try:
            # --- 1. SYNC POSITIONS (Source of Truth) ---
            # This identifies the tokens we need to stream via WebSocket
            sync_positions(universal_data)
            
            # --- 2. SYNC ORDER BOOK ---
            # Full sync to ensure the GUI order list is complete
            sync_orders(universal_data)

            # --- SUCCESS PATH ---
            if consecutive_errors > 0:
                log.info("REST Connection re-established.", tags=["DATA", "HEAL"])
                consecutive_errors = 0
            
            with universal_data['sys']['lock']:
                universal_data['status']['data_stale'] = False

            # --- DYNAMIC SLEEP ---
            now = datetime.datetime.now().time()
            is_market_open = datetime.time(9, 0) <= now <= datetime.time(15, 30)
            
            # We don't need 1s polling anymore. 
            # WebSocket handles the 'Live' part; this service handles 'Consistency'.
            time.sleep(poll_consistency if is_market_open else poll_idle)

        except Exception as e:
            # --- FAILURE PATH & AUTO-RELOGIN ---
            consecutive_errors += 1
            
            with universal_data['sys']['lock']:
                universal_data['status']['data_stale'] = True
                
            sleep_time = min(base_delay * (2 ** (consecutive_errors - 1)), max_delay)
            
            err_msg = str(e)
            if consecutive_errors == 1:
                log.warning(f"REST Sync Failed: {err_msg}. Retrying...", tags=["DATA", "WARN"])
            
            # If REST fails too many times, the session is likely dead.
            # Re-authenticating here fixes both REST and WebSocket (as WS relies on valid tokens).
            if consecutive_errors > max_retries:
                log.error("Session potentially expired. Attempting Full Refresh...", tags=["DATA", "FIX"])
                try:
                    authenticate_client(universal_data)
                    log.info("Session refreshed. WebSocket will re-connect via watchdog.", tags=["DATA", "FIX"])
                    consecutive_errors = 0
                    time.sleep(2)
                    continue 
                except:
                    pass 

            time.sleep(sleep_time)

    log.info("Data Service Stopped", tags=["SVC", "DATA"])