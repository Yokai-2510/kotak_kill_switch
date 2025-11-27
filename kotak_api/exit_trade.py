import time

def square_off_all_positions(universal_data):
    """
    Fetches all positions and places MARKET exit orders for any open position.
    Used during the Kill Switch sequence.
    """
    log = universal_data['sys']['log']
    client = universal_data['sys']['api']
    
    log.warning(">>> INITIATING AUTO-SQUARE OFF SEQUENCE <<<", tags=["RISK", "SQ_OFF"])

    try:
        # 1. Fetch Fresh Positions
        response = client.positions()
        
        if not response or 'data' not in response:
            log.info("No positions data found to square off.", tags=["SQ_OFF"])
            return

        raw_positions = response['data']
        orders_placed = 0

        for p in raw_positions:
            try:
                # --- A. Calculate Net Qty ---
                # Using safe float conversion helper
                def get_val(key): 
                    return float(p.get(key, 0) or 0)

                fl_buy = get_val('flBuyQty')
                fl_sell = get_val('flSellQty')
                cf_buy = get_val('cfBuyQty')
                cf_sell = get_val('cfSellQty')

                # Net Qty = Total Buy - Total Sell
                total_buy = fl_buy + cf_buy
                total_sell = fl_sell + cf_sell
                net_qty = int(total_buy - total_sell)

                # If Net Qty is 0, position is already closed
                if net_qty == 0:
                    continue

                # --- B. Prepare Exit Order ---
                # If Net Qty is Positive (Long) -> We need to SELL
                # If Net Qty is Negative (Short) -> We need to BUY
                transaction_type = "S" if net_qty > 0 else "B"
                abs_qty = abs(net_qty)

                # Essential fields from position data
                symbol = p.get('trdSym', '')
                segment = p.get('exSeg', '')
                product = p.get('prod', 'NRML') # Default to Normal if missing
                token = p.get('tok', '')

                log.info(f"Squaring off {symbol}: {transaction_type} {abs_qty} Qty ({product})", tags=["SQ_OFF"])

                # --- C. Place Market Order ---
                # Referencing Place_Order.md
                order_resp = client.place_order(
                    exchange_segment=segment,
                    product=product,
                    price="0",              # Market Order
                    order_type="MKT",
                    quantity=str(abs_qty),
                    validity="DAY",
                    trading_symbol=symbol,
                    transaction_type=transaction_type,
                    amo="NO"
                )

                if order_resp and order_resp.get('stat') == "Ok":
                    log.info(f"Order Placed. ID: {order_resp.get('nOrdNo')}", tags=["SQ_OFF", "SUCCESS"])
                    orders_placed += 1
                else:
                    log.error(f"Failed to place exit order for {symbol}: {order_resp}", tags=["SQ_OFF", "FAIL"])
                
                # Small delay to prevent rate limit spamming if many positions
                time.sleep(0.2)

            except Exception as inner_e:
                log.error(f"Error processing position {p.get('trdSym')}: {inner_e}", tags=["SQ_OFF", "ERR"])
                continue

        log.info(f"Square Off Complete. Total Orders Placed: {orders_placed}", tags=["SQ_OFF"])

    except Exception as e:
        log.critical(f"Critical Failure in Square Off Module: {e}", tags=["SQ_OFF", "CRITICAL"], exc_info=True)