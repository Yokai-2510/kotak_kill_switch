def check_sl_status(universal_data):
    """
    Iterates through orders to detect if a Stop-Loss order was executed.
    
    LOGIC BRANCHES:
    1. STANDARD (Short Options): Checks for 'BUY' orders only.
    2. TEST MODE (Long Equity): Checks for 'SELL' orders (if config enabled).
    """
    
    log = universal_data['sys']['log']
    config = universal_data['sys']['config']['kill_switch']
    
    # Check if we are in Equity Test Mode (Long positions)
    is_test_mode = config.get('test_mode_equity', False)
    
    with universal_data['sys']['lock']:
        orders = universal_data['market']['orders']
    
    sl_hit_detected = False
    
    try:
        for order in orders:
            # 1. Common Checks (Must be SL order and Must be Complete)
            o_type = order.get('type', '').upper()
            if o_type not in ['SL', 'SL-M']:
                continue
            
            status = order.get('status', '').upper()
            if status not in ['COMPLETE', 'TRADED', 'FILLED']:
                continue
            
            txn_type = order.get('transaction_type', '').upper()
            
            # --- BRANCH 1: PRODUCTION LOGIC (Short Options) ---
            # We only care if a BUY order triggered (Covering a Short)
            if txn_type in ['B', 'BUY']:
                sl_hit_detected = True
                log.warning(f"Short Leg SL Hit! (BUY Order {order.get('order_id')})", tags=["RISK", "SL_HIT"])
                break

            # --- BRANCH 2: TESTING LOGIC (Long Stocks) ---
            # Only runs if 'test_mode_equity' is TRUE in config
            # We check if a SELL order triggered (Exiting a Long)
            elif is_test_mode and txn_type in ['S', 'SELL']:
                sl_hit_detected = True
                log.warning(f"TEST MODE: Long Leg SL Hit! (SELL Order {order.get('order_id')})", tags=["RISK", "TEST_HIT"])
                break
            
        with universal_data['sys']['lock']:
            universal_data['risk']['sl_hit_status'] = sl_hit_detected

    except Exception as e:
        log.error(f"Error checking SL status: {e}", tags=["RISK"])