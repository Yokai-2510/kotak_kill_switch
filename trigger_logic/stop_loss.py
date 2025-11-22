# stop_loss.py
def check_sl_status(universal_data):
    """
    Iterates through orders to detect if a Stop-Loss order for a Sold position was executed.
    Updates: universal_data['state']['sl_hit'] = True/False
    """
    log = universal_data['logger']
    orders = universal_data['state'].get('orders', [])
    
    sl_hit_detected = False
    
    try:
        for order in orders:
            # Check 1: Is it a Stop Loss Order?
            # API 'prcTp' (Price Type) usually returns 'SL', 'SL-M'
            # Some APIs use 'trig_sl' etc. based on your order book dump.
            # We stick to standard Neo API values: "SL", "SL-M"
            o_type = order.get('type', '').upper()
            if o_type not in ['SL', 'SL-M']:
                continue
            
            # Check 2: Is it 'COMPLETE' or 'TRADED'?
            status = order.get('status', '').upper()
            if status not in ['COMPLETE', 'TRADED', 'FILLED']:
                continue
                
            # Check 3: Is it a BUY order?
            # Context: We want to kill switch if our Short Leg SL is hit.
            # Short Leg SL is a BUY order.
            txn_type = order.get('transaction_type', '').upper()
            if txn_type != 'B':
                continue
            
            # If we get here, a BUY SL order was executed.
            sl_hit_detected = True
            log.warning(f"SL Hit Detected on Order {order.get('order_id')}", tags=["RISK", "SL_HIT"])
            break
            
        universal_data['state']['sl_hit'] = sl_hit_detected

    except Exception as e:
        log.error(f"Error checking SL status: {e}", tags=["RISK"], exc_info=True)