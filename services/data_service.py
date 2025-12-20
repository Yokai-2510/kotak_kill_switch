import time
import datetime
from kotak_api.positions import sync_positions
from kotak_api.orders import sync_orders
from kotak_api.quotes import sync_ltp
from kotak_api.client_login import authenticate_client

def run_data_service(universal_data):
    log = universal_data['sys']['log']
    
    # 1. Load Configuration
    mon_conf = universal_data['sys']['config'].get('monitoring', {})
    retry_conf = mon_conf.get('retry_strategy', {})
    
    poll_active = mon_conf.get('poll_interval_seconds', 2)
    poll_idle = mon_conf.get('off_market_interval_seconds', 60)
    
    # Retry Parameters
    max_retries = retry_conf.get('max_retries', 5)
    base_delay = retry_conf.get('base_delay', 2)
    max_delay = retry_conf.get('max_delay', 10)
    
    consecutive_errors = 0
    
    log.info("Data Service Started (Resilient Mode).", tags=["SVC", "DATA"])
    
    while universal_data['signals']['system_active']:
        try:
            # --- SYNC DATA ---
            # If these fail, they raise Exception -> We jump to 'except' -> Old data is preserved.
            sync_positions(universal_data)
            sync_orders(universal_data)
            
            with universal_data['sys']['lock']:
                has_pos = bool(universal_data['market']['positions'])
            
            if has_pos:
                sync_ltp(universal_data)

            # --- SUCCESS PATH ---
            if consecutive_errors > 0:
                log.info("Connection re-established.", tags=["DATA", "HEAL"])
                consecutive_errors = 0
            
            # Mark data as Fresh
            with universal_data['sys']['lock']:
                universal_data['status']['data_stale'] = False

            # Sleep
            now = datetime.datetime.now().time()
            is_market_open = datetime.time(9, 0) <= now <= datetime.time(23, 55)
            time.sleep(poll_active if is_market_open else poll_idle)

        except Exception as e:
            # --- FAILURE PATH ---
            consecutive_errors += 1
            
            # Mark data as Stale (UI can show warning, but MTM retains value)
            with universal_data['sys']['lock']:
                universal_data['status']['data_stale'] = True
                
            # Calculate Backoff (2s, 4s, 8s...)
            sleep_time = min(base_delay * (2 ** (consecutive_errors - 1)), max_delay)
            
            err_msg = str(e)
            if consecutive_errors == 1:
                log.warning(f"Connection Lost: {err_msg}. Retrying in {sleep_time}s...", tags=["DATA", "WARN"])
            elif consecutive_errors % 5 == 0:
                log.warning(f"Still disconnected (Attempt {consecutive_errors})...", tags=["DATA", "WAIT"])

            # Auto-Heal (Re-Login) if stuck too long
            if consecutive_errors > max_retries:
                log.error("Max Retries Hit. Attempting Session Refresh...", tags=["DATA", "FIX"])
                try:
                    authenticate_client(universal_data)
                    consecutive_errors = 0 # Reset if auth works
                    log.info("Session Refreshed.", tags=["DATA", "FIX"])
                    time.sleep(1)
                    continue 
                except:
                    pass # Auth failed, wait loop continues

            time.sleep(sleep_time)

    log.info("Data Service Stopped", tags=["SVC", "DATA"])