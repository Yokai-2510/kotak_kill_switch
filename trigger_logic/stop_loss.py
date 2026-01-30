def check_sl_status(universal_data, order_update=None):
    """
    Evaluates Order execution to detect hit Stop-Losses.
    Directly triggered by WebSocket updates for zero-latency reaction.
    """
    log = universal_data['sys']['log']
    sl_hit_detected = False

    # 1. READ DATA (Thread-Safe)
    with universal_data['sys']['lock']:
        # If we have a single incremental update from WebSocket, use it.
        # Otherwise, scan the full order book (Consistency Sync fallback).
        orders_to_check = [order_update] if order_update else universal_data['market']['orders']

    try:
        for order in orders_to_check:
            # --- Field Normalization (Handles REST vs WebSocket differences) ---
            # Kotak REST uses 'prcTp', WS uses 'type' or 'prcTp'
            o_type = order.get('prcTp') or order.get('type') or ''
            # Kotak REST uses 'trnsTp', WS uses 'transaction_type' or 'trnsTp'
            txn = order.get('trnsTp') or order.get('transaction_type') or ''
            # Kotak REST uses 'status', WS uses 'ordSt'
            status = str(order.get('ordSt') or order.get('status') or '').upper()
            
            # --- 1. FILTER FOR SL ORDERS ---
            if o_type not in ['SL', 'SL-M']:
                continue
            
            # --- 2. FILTER FOR EXIT ORDERS (Buy covering Short) ---
            if txn not in ['B', 'BUY']:
                continue

            # --- 3. CHECK EXECUTION STATUS ---
            qty = float(order.get('qty') or 0)
            filled = float(order.get('fldQty') or order.get('filled_qty') or 0)

            # Rule: Success if status is Traded/Complete OR if Qty perfectly matches Filled Qty
            is_complete = (status in ['TRADED', 'COMPLETE', 'FILLED']) or (qty > 0 and filled == qty)
            
            if is_complete:
                oid = order.get('nOrdNo') or order.get('order_id')
                log.warning(f"STOP-LOSS HIT: Order {oid} is {status}", tags=["RISK", "SL_HIT"])
                sl_hit_detected = True
                break
            
        # 2. UPDATE RISK STATE
        if sl_hit_detected:
            with universal_data['sys']['lock']:
                universal_data['risk']['sl_hit_status'] = True
                
                # --- DUAL TRIGGER EVALUATION ---
                # If SL is hit, we immediately check if MTM is already below limit.
                # If yes, we set the trigger signal for the Kill Switch Service.
                mtm_now = universal_data['risk']['mtm_current']
                mtm_limit = universal_data['risk']['mtm_limit']
                
                if mtm_now <= mtm_limit:
                    log.critical(f"DUAL TRIGGER MET: MTM ({mtm_now}) <= Limit ({mtm_limit}) + SL Hit!", tags=["RISK", "KILL"])
                    universal_data['signals']['trigger_kill'] = True

    except Exception as e:
        log.error(f"Error in Stop-Loss monitoring: {e}", tags=["RISK", "ERR"])