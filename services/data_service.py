import time
import datetime
from kotak_api.positions import sync_positions
from kotak_api.orders import sync_orders
from kotak_api.quotes import sync_ltp
from kotak_api.client_login import authenticate_client

def run_data_service(universal_data):
    """
    Thread: Polls API.
    Features: Auto-Heal (Re-Auth), Adaptive Polling, and Error Backoff.
    """
    log = universal_data['sys']['log']
    config = universal_data['sys']['config']['monitoring']
    
    # Config Durations
    poll_active = config.get('poll_interval_seconds', 2)
    poll_idle = config.get('off_market_interval_seconds', 60)
    
    error_count = 0
    
    log.info("Data Service Started.", tags=["SVC", "DATA"])
    
    while True:
        if not universal_data['signals']['system_active']:
            break

        # --- 1. SYNC DATA ---
        try:
            sync_positions(universal_data)
            sync_orders(universal_data)
            
            with universal_data['sys']['lock']:
                has_positions = bool(universal_data['market']['positions'])
            
            if has_positions:
                sync_ltp(universal_data)
            
            # Reset error count on success
            if error_count > 0:
                error_count = 0
                log.info("Connection Stable.", tags=["DATA"])
                
        except Exception as e:
            error_count += 1
            # Use repr(e) to avoid "__str__ returned non-string" crashes
            log.warning(f"Connection Lost (Attempt {error_count}): {repr(e)}", tags=["DATA", "WARN"])
            
            # --- AUTO HEAL LOGIC ---
            try:
                # Wait a bit before hammering the server again
                time.sleep(2)
                
                log.info("Attempting Re-Authentication...", tags=["DATA", "HEAL"])
                authenticate_client(universal_data)
                log.info("Re-Authentication Successful.", tags=["DATA", "HEAL"])
                
            except Exception as auth_e:
                log.error(f"Auto-Heal Failed: {repr(auth_e)}", tags=["DATA", "FAIL"])

        # --- 2. ADAPTIVE SLEEP ---
        now = datetime.datetime.now().time()
        market_start = datetime.time(9, 0)
        market_end = datetime.time(23, 55)
        
        base_sleep = poll_active if (market_start <= now <= market_end) else poll_idle
        
        # Exponential Backoff: If we have errors, sleep longer (2s -> 4s -> 6s...)
        # Cap at 10 seconds to avoid being offline too long
        actual_sleep = min(base_sleep + (error_count * 2), 10)
        
        time.sleep(actual_sleep)
    
    log.info("Data Service Stopped.", tags=["SVC", "DATA"])