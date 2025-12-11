def check_sl_status(universal_data):
    """
    Checks if a Stop-Loss order for a Short Position has been EXECUTED.
    
    Logic based on API Docs:
    1. Order Type must be 'SL' or 'SL-M'.
    2. Transaction Type must be 'B' (Buy covering Short).
    3. Execution Check: 'filled_qty' must equal 'qty' (Strict Complete).
    """
    log = universal_data['sys']['log']
    
    with universal_data['sys']['lock']:
        orders = universal_data['market']['orders']
    
    sl_hit_detected = False
    
    try:
        for order in orders:
            # 1. Filter for SL Orders (Kotak uses 'SL', 'SL-M')
            o_type = order.get('type', '')
            if o_type not in ['SL', 'SL-M']:
                continue
            
            # 2. Filter for Buy Orders (Exiting a Sell)
            # Kotak API returns "B" for Buy
            txn = order.get('transaction_type', '')
            if txn not in ['B', 'BUY']:
                continue

            # 3. Check Execution Status (Math based)
            qty = order.get('qty', 0)
            filled = order.get('filled_qty', 0)
            status = order.get('status', '')

            # STRICT RULE: Client requires "Completely Filled" only.
            # We check if Filled Qty equals Total Qty.
            # We also check if status is explicitly 'COMPLETE' or 'FILLED' as a backup.
            is_complete = (qty > 0 and filled == qty) or status in ['COMPLETE', 'FILLED']
            
            if is_complete:
                sl_hit_detected = True
                oid = order.get('order_id')
                log.warning(f"Short Leg SL Hit! (Order {oid}: {int(filled)}/{int(qty)} filled)", tags=["RISK", "SL_HIT"])
                break
            
        with universal_data['sys']['lock']:
            universal_data['risk']['sl_hit_status'] = sl_hit_detected

    except Exception as e:
        log.error(f"Error checking SL status: {e}", tags=["RISK"])