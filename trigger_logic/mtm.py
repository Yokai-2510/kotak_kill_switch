# mtm.py
def calculate_mtm(universal_data):
    """
    Calculates Mark-to-Market (MTM) PnL based on synced positions and quotes.
    Formula: (SellAmt - BuyAmt) + (NetQty * LTP * PriceFactor * Multiplier)
    Updates: universal_data['state']['mtm']
    """
    log = universal_data['logger']
    positions = universal_data['state'].get('positions', [])
    quotes = universal_data['state'].get('quotes', {})
    
    total_pnl = 0.0
    
    try:
        for pos in positions:
            token = pos['token']
            
            # If we don't have an LTP, we cannot calculate accurate MTM for this leg.
            # We log a warning and skip (or assume 0 impact if closed).
            if token not in quotes:
                # If net qty is 0, LTP doesn't matter for Realized PnL part
                if pos['net_qty'] != 0:
                    # log.warning(f"Missing LTP for {pos['symbol']} (Tok: {token}). MTM may be inaccurate.", tags=["MTM"])
                    pass
                ltp = 0.0
            else:
                ltp = quotes[token]
            
            # Extract pre-calculated fields from positions.py
            net_qty = pos['net_qty']
            total_buy_amt = pos['total_buy_amt']
            total_sell_amt = pos['total_sell_amt']
            multiplier = pos['multiplier']
            price_factor = pos['price_factor'] # (genNum/genDen * prcNum/prcDen)
            
            # Kotak Formula:
            # PnL = (Total Sell Amt - Total Buy Amt) + (Net Qty * LTP * multiplier * price_factor)
            
            realized_part = total_sell_amt - total_buy_amt
            unrealized_part = net_qty * ltp * multiplier * price_factor
            
            leg_pnl = realized_part + unrealized_part
            total_pnl += leg_pnl
            
        # Update State
        universal_data['state']['mtm'] = round(total_pnl, 2)
        # log.info(f"MTM Calculated: {total_pnl}", tags=["MTM"])

    except Exception as e:
        log.error(f"Error calculating MTM: {e}", tags=["MTM"], exc_info=True)