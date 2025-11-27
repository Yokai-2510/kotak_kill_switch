import time
from kotak_api.positions import sync_positions
from kotak_api.orders import sync_orders
from kotak_api.quotes import sync_ltp

def run_data_service(universal_data):
    """
    Thread: Polls API for Positions, Orders, and Quotes.
    """
    log = universal_data['sys']['log']
    poll_interval = universal_data['sys']['config']['monitoring']['poll_interval_seconds']
    
    log.info("Data Service Started.", tags=["SVC", "DATA"])
    
    while True:
        # Check active status safely
        if not universal_data['signals']['system_active']:
            break

        try:
            sync_positions(universal_data)
            sync_orders(universal_data)
            
            # Check if we need quotes
            with universal_data['sys']['lock']:
                has_positions = bool(universal_data['market']['positions'])
            
            if has_positions:
                sync_ltp(universal_data)
                
        except Exception as e:
            log.error(f"Data Loop Error: {e}", tags=["SVC", "DATA"])
            
        time.sleep(poll_interval)
    
    log.info("Data Service Stopped.", tags=["SVC", "DATA"])