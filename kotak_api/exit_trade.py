import time

def square_off_all_positions(universal_data):
    """
    Auto-Kill Logic: Iterates ALL open positions and closes them.
    """
    log = universal_data['sys']['log']
    client = universal_data['sys']['api']
    
    log.warning(">>> INITIATING AUTO-SQUARE OFF SEQUENCE <<<", tags=["RISK", "SQ_OFF"])

    try:
        response = client.positions()
        if not response or 'data' not in response:
            log.info("No positions data found.", tags=["SQ_OFF"])
            return

        orders_placed = 0
        for p in response['data']:
            try:
                # Calculate Net Qty
                fl_buy = float(p.get('flBuyQty', 0) or 0)
                fl_sell = float(p.get('flSellQty', 0) or 0)
                cf_buy = float(p.get('cfBuyQty', 0) or 0)
                cf_sell = float(p.get('cfSellQty', 0) or 0)
                
                net_qty = int((fl_buy + cf_buy) - (fl_sell + cf_sell))

                if net_qty == 0: continue

                # Determine Action (Close Long -> Sell, Close Short -> Buy)
                transaction_type = "S" if net_qty > 0 else "B"
                abs_qty = abs(net_qty)
                
                _place_market_exit(client, p, transaction_type, str(abs_qty), log)
                orders_placed += 1
                time.sleep(0.1) # Throttle slightly

            except Exception as inner_e:
                log.error(f"Error processing position {p.get('trdSym')}: {inner_e}", tags=["SQ_OFF"])
                continue

        log.info(f"Square Off Complete. Exit Orders: {orders_placed}", tags=["SQ_OFF"])

    except Exception as e:
        log.critical(f"Square Off Critical Fail: {e}", tags=["SQ_OFF", "FAIL"])


def exit_one_position(universal_data, token, qty, txn_type, segment, product):
    """
    Manual Exit Logic: Closes a SPECIFIC position from the GUI.
    """
    log = universal_data['sys']['log']
    client = universal_data['sys']['api']
    
    # 1. Safety Check: Don't allow manual exit if Kill Switch is firing
    if universal_data['signals']['trigger_kill']:
        log.warning("Manual Exit BLOCKED: Kill Switch is Active!", tags=["MANUAL", "BLOCK"])
        return

    log.info(f"Manual Exit Requested: {txn_type} {qty} (Token: {token})", tags=["MANUAL"])

    try:
        # Construct a partial position object for the helper
        # We only need specific fields for the order placement
        p_data = {
            'tok': token,
            'exSeg': segment,
            'prod': product,
            'trdSym': f"Token_{token}" # Fallback symbol name
        }
        
        # 2. Place Order
        resp = _place_market_exit(client, p_data, txn_type, str(qty), log)
        
        if resp and resp.get('stat') == "Ok":
            return True, f"Order {resp.get('nOrdNo')}"
        else:
            return False, f"API Error: {resp}"

    except Exception as e:
        log.error(f"Manual Exit Failed: {e}", tags=["MANUAL"])
        return False, str(e)


def _place_market_exit(client, p_data, txn_type, qty_str, log):
    """Internal Helper to send the API request."""
    symbol = p_data.get('trdSym', '')
    segment = p_data.get('exSeg', 'nse_fo')
    product = p_data.get('prod', 'NRML')
    
    log.info(f"Exiting {symbol}: {txn_type} {qty_str} ({product})", tags=["TRADE"])
    
    return client.place_order(
        exchange_segment=segment,
        product=product,
        price="0",
        order_type="MKT",
        quantity=qty_str,
        validity="DAY",
        trading_symbol=symbol,
        transaction_type=txn_type,
        amo="NO"
    )