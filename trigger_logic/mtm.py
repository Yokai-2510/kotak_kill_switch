def calculate_mtm(universal_data):
    """
    Calculates MTM PnL using the live WebSocket quote cache.
    Updates: ['risk']['mtm_current'] and ['risk']['mtm_distance']
    """
    log = universal_data['sys']['log']
    
    # 1. READ DATA (Thread-Safe)
    with universal_data['sys']['lock']:
        positions = universal_data['market']['positions']
        quotes = universal_data['market']['quotes']
        mtm_limit = universal_data['risk']['mtm_limit']
    
    total_pnl = 0.0
    stale_prices = []

    try:
        for pos in positions:
            token = str(pos['token'])
            
            # Fetch LTP from WebSocket-updated dictionary
            ltp = quotes.get(token, 0.0)
            
            # --- STALE PRICE PROTECTION ---
            # If LTP is 0.0, the WebSocket hasn't received a tick for this token yet.
            # We skip the unrealized P&L calculation for this position to avoid 
            # massive fake MTM drops (e.g. calculating -1 * 50,000 as loss).
            if ltp <= 0:
                stale_prices.append(pos.get('symbol', token))
                # Only add the realized portion (Sell - Buy)
                total_pnl += (pos['total_sell_amt'] - pos['total_buy_amt'])
                continue
            
            # Calculation Params (from REST positions sync)
            net_qty = pos['net_qty']
            total_buy_amt = pos['total_buy_amt']
            total_sell_amt = pos['total_sell_amt']
            multiplier = pos['multiplier']
            price_factor = pos['price_factor']
            
            # Formula: (Realized) + (Unrealized)
            realized_part = total_sell_amt - total_buy_amt
            unrealized_part = net_qty * ltp * multiplier * price_factor
            
            total_pnl += (realized_part + unrealized_part)
            
        # 2. WRITE RESULTS (Thread-Safe)
        with universal_data['sys']['lock']:
            universal_data['risk']['mtm_current'] = round(total_pnl, 2)
            universal_data['risk']['mtm_distance'] = round(total_pnl - mtm_limit, 2)
            
            # Log warning if some prices are missing
            if stale_prices:
                universal_data['status']['error_message'] = f"Waiting for ticks: {', '.join(stale_prices)}"
            else:
                if universal_data['status']['error_message'] and "Waiting for ticks" in universal_data['status']['error_message']:
                    universal_data['status']['error_message'] = None

    except Exception as e:
        log.error(f"Critical Error in MTM Logic: {e}", tags=["MTM", "FAIL"])