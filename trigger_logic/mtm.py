def calculate_mtm(universal_data):
    """
    Calculates MTM PnL based on synced positions and quotes.
    Updates: ['risk']['mtm_current'] and ['risk']['mtm_distance']
    """
    log = universal_data['sys']['log']
    
    # 1. READ DATA (Thread-Safe)
    with universal_data['sys']['lock']:
        positions = universal_data['market']['positions']
        quotes = universal_data['market']['quotes']
        mtm_limit = universal_data['risk']['mtm_limit']
    
    total_pnl = 0.0
    
    try:
        for pos in positions:
            token = pos['token']
            
            # Fetch LTP or default to 0.0
            ltp = quotes.get(token, 0.0)
            
            # Calculation Params
            net_qty = pos['net_qty']
            total_buy_amt = pos['total_buy_amt']
            total_sell_amt = pos['total_sell_amt']
            multiplier = pos['multiplier']
            price_factor = pos['price_factor']
            
            # PnL Formula
            realized_part = total_sell_amt - total_buy_amt
            unrealized_part = net_qty * ltp * multiplier * price_factor
            
            total_pnl += (realized_part + unrealized_part)
            
        # 2. WRITE RISK METRICS (Thread-Safe)
        with universal_data['sys']['lock']:
            universal_data['risk']['mtm_current'] = round(total_pnl, 2)
            universal_data['risk']['mtm_distance'] = round(total_pnl - mtm_limit, 2)

    except Exception as e:
        log.error(f"Error calculating MTM: {e}", tags=["MTM"])