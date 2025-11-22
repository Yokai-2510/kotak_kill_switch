# kotak_api/positions.py

def sync_positions(universal_data):
    """
    Fetches positions, parses specific fields for MTM calculation, 
    and updates universal_data['state']['positions'].
    """
    log = universal_data['logger']
    client = universal_data['client']
    
    try:
        # 1. API Call
        response = client.positions()
        
        # 2. Validation
        if not response or 'data' not in response:
            log.warning("Positions API returned no data structure.", tags=["API", "POS"])
            universal_data['state']['positions'] = []
            return

        raw_positions = response['data']
        if not raw_positions:
            # No open positions is a valid state
            universal_data['state']['positions'] = []
            return

        parsed_positions = []

        # 3. Extraction & Calculation Logic
        for p in raw_positions:
            # Safe integer extraction helper
            def get_val(key, default=0):
                try:
                    return float(p.get(key, default) or 0)
                except (ValueError, TypeError):
                    return 0.0

            # Basic Instrument Details
            token = p.get('tok', '')
            segment = p.get('exSeg', 'nse_fo') # Default to FO if missing
            symbol = p.get('trdSym', 'Unknown')
            lot_size = get_val('lotSz', 1)
            multiplier = get_val('multiplier', 1)
            
            # Price Multipliers (genNum/genDen * prcNum/prcDen)
            gen_num = get_val('genNum', 1)
            gen_den = get_val('genDen', 1)
            prc_num = get_val('prcNum', 1)
            prc_den = get_val('prcDen', 1)
            
            price_factor = (gen_num / gen_den) * (prc_num / prc_den)

            # Raw Quantities
            fl_buy_qty = get_val('flBuyQty')
            fl_sell_qty = get_val('flSellQty')
            cf_buy_qty = get_val('cfBuyQty')
            cf_sell_qty = get_val('cfSellQty')

            # --- LOGIC: FnO Adjustment ---
            # Docs: "For FnO Scrips, divide all parameters by lotSz"
            # We assume non-Equity segments are FnO. 
            # (Adjust this check if 'nse_cm' needs different handling)
            if 'cm' not in segment.lower() and lot_size > 0:
                fl_buy_qty /= lot_size
                fl_sell_qty /= lot_size
                cf_buy_qty /= lot_size
                cf_sell_qty /= lot_size

            # 1. Total Quantities
            total_buy_qty = cf_buy_qty + fl_buy_qty
            total_sell_qty = cf_sell_qty + fl_sell_qty
            net_qty = total_buy_qty - total_sell_qty

            # 2. Amount Fields (Cost Basis)
            # Note: Amounts usually don't need lot_size division in standard APIs, 
            # but relying on 'buyAmt'/'sellAmt' direct from API is safer for MTM.
            total_buy_amt = get_val('cfBuyAmt') + get_val('buyAmt')
            total_sell_amt = get_val('cfSellAmt') + get_val('sellAmt')

            # Only add if there is activity or an open position
            if total_buy_qty != 0 or total_sell_qty != 0 or net_qty != 0:
                parsed_positions.append({
                    'token': token,
                    'segment': segment,
                    'symbol': symbol,
                    'net_qty': int(net_qty),
                    'total_buy_amt': total_buy_amt,
                    'total_sell_amt': total_sell_amt,
                    'multiplier': multiplier,
                    'price_factor': price_factor,
                    'lot_size': lot_size # Kept for reference
                })

        # 4. Update State
        universal_data['state']['positions'] = parsed_positions
        # log.info(f"Synced {len(parsed_positions)} positions.", tags=["API", "POS"])

    except Exception as e:
        log.error(f"Error syncing positions: {e}", tags=["API", "POS"], exc_info=True)