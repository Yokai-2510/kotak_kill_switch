import time
from kotak_api.positions import sync_positions
from kotak_api.orders import sync_orders
from kotak_api.quotes import sync_ltp

def run_data_service(universal_data):
    """
    Background thread that continuously fetches Positions, Orders, and Quotes.
    Stops when universal_data['system_active'] becomes False.
    """
    log = universal_data['logger']
    config = universal_data['config']['monitoring']
    poll_interval = config['poll_interval_seconds']
    
    log.info("Data Service Started.", tags=["SVC", "DATA"])
    
    while universal_data['system_active']:
        try:
            # 1. Fetch Positions & Orders (Base Data)
            sync_positions(universal_data)
            sync_orders(universal_data)
            
            # 2. Fetch Quotes (Dependent on Positions)
            # Only fetch if we have positions to quote
            if universal_data['state']['positions']:
                sync_ltp(universal_data)
                
        except Exception as e:
            log.error(f"Data Loop Error: {e}", tags=["SVC", "DATA"])
            
        # Wait for next tick
        time.sleep(poll_interval)
    
    log.info("Data Service Stopped.", tags=["SVC", "DATA"])