def sync_positions(universal_data):
    log = universal_data['sys']['log']
    client = universal_data['sys']['api']
    
    try:
        response = client.positions()
        
        # --- STRICT VALIDATION START ---
        if response is None:
            raise Exception("API returned None")
        
        stat = response.get('stat', '').lower()
        st_code = str(response.get('stCode', ''))
        
        raw_positions = []

        if stat != 'ok':
            # SPECIAL CASE: 5203 means "No Data Found" (User has no open/closed positions today)
            # This is a VALID state, not an error.
            if st_code == '5203':
                raw_positions = [] # Valid empty list
            else:
                # Actual API Error (e.g. Session Expired, Backend Error)
                raise Exception(f"API Status not OK: {response}")
        else:
            raw_positions = response.get('data', [])
            if raw_positions is None: raw_positions = []
        # --- STRICT VALIDATION END ---

        parsed_positions = []

        for p in raw_positions:
            try:
                def get_val(k, d=0): return float(p.get(k, d) or 0)
                
                token = p.get('tok', '')
                segment = p.get('exSeg', 'nse_fo')
                lot_size = get_val('lotSz', 1)
                
                multiplier = get_val('multiplier', 1)
                gen_num = get_val('genNum', 1)
                gen_den = get_val('genDen', 1)
                prc_num = get_val('prcNum', 1)
                prc_den = get_val('prcDen', 1)
                price_factor = (gen_num / gen_den) * (prc_num / prc_den)

                fl_buy = get_val('flBuyQty')
                fl_sell = get_val('flSellQty')
                cf_buy = get_val('cfBuyQty')
                cf_sell = get_val('cfSellQty')

                if 'cm' not in segment.lower() and lot_size > 0:
                    fl_buy /= lot_size; fl_sell /= lot_size
                    cf_buy /= lot_size; cf_sell /= lot_size

                net_qty = (cf_buy + fl_buy) - (cf_sell + fl_sell)
                buy_amt = get_val('cfBuyAmt') + get_val('buyAmt')
                sell_amt = get_val('cfSellAmt') + get_val('sellAmt')

                if net_qty != 0 or buy_amt != 0 or sell_amt != 0:
                    parsed_positions.append({
                        'token': token,
                        'segment': segment,
                        'symbol': p.get('trdSym', 'Unknown'),
                        'net_qty': int(net_qty),
                        'total_buy_amt': buy_amt,
                        'total_sell_amt': sell_amt,
                        'multiplier': multiplier,
                        'price_factor': price_factor
                    })
            except Exception:
                continue

        with universal_data['sys']['lock']:
            universal_data['market']['positions'] = parsed_positions
            universal_data['market']['raw']['positions'] = response

    except Exception as e:
        # If it's a real error (Network, Auth), re-raise to trigger Backoff
        raise e