import time
import datetime
from kotak_api.positions import sync_positions
from kotak_api.orders import sync_orders
from kotak_api.quotes import sync_ltp
from kotak_api.client_login import authenticate_client

def run_data_service(universal_data):
    log = universal_data['sys']['log']
    config = universal_data['sys']['config']['monitoring']
    
    poll_active = config.get('poll_interval_seconds', 2)
    poll_idle = config.get('off_market_interval_seconds', 60)
    
    consecutive_errors = 0
    
    log.info("Service Started", tags=["SVC", "DATA"])
    
    while universal_data['signals']['system_active']:
        try:
            # --- 1. SYNC ---
            sync_positions(universal_data)
            sync_orders(universal_data)
            
            with universal_data['sys']['lock']:
                has_pos = bool(universal_data['market']['positions'])
            
            if has_pos:
                sync_ltp(universal_data)

            # Reset error counter on success
            if consecutive_errors > 0:
                log.info("Connection re-established.", tags=["DATA", "HEAL"])
                consecutive_errors = 0

            # --- 2. SLEEP ---
            now = datetime.datetime.now().time()
            is_market_open = datetime.time(9, 0) <= now <= datetime.time(23, 55)
            time.sleep(poll_active if is_market_open else poll_idle)

        except Exception as e:
            consecutive_errors += 1
            err_msg = str(e)
            
            # SPAM PREVENTION: Only log unique/critical errors or periodic summaries
            if consecutive_errors == 1:
                log.warning(f"Connection Lost: {err_msg}", tags=["DATA", "WARN"])
            elif consecutive_errors % 10 == 0:
                log.warning(f"Connection still down (x{consecutive_errors})...", tags=["DATA", "WAIT"])

            # BACKOFF STRATEGY: Sleep longer if errors persist (max 10s)
            backoff_time = min(2 + consecutive_errors, 10)
            time.sleep(backoff_time)
            
            # Auto-Heal Trigger
            if consecutive_errors > 5:
                try:
                    log.info("Attempting Re-Auth...", tags=["DATA", "FIX"])
                    authenticate_client(universal_data)
                except:
                    pass # Quiet fail, retry next loop

    log.info("Service Stopped", tags=["SVC", "DATA"])