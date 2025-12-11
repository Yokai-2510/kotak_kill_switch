def sync_orders(universal_data):
    """
    Fetches Order Book and parses strictly based on Kotak Neo API docs.
    Extracts numerical quantities for precise status checks.
    """
    log = universal_data['sys']['log']
    client = universal_data['sys']['api']

    try:
        response = client.order_report()
        
        clean_orders = []
        # API Doc says: response['data'] is a list of objects
        if response and 'data' in response and isinstance(response['data'], list):
            for o in response['data']:
                try:
                    # Helper to safely get numbers
                    qty = float(o.get('qty', 0))
                    fld_qty = float(o.get('fldQty', 0))
                    
                    clean_orders.append({
                        'order_id': o.get('nOrdNo', ''),
                        'status': o.get('ordSt', '').upper(),  # e.g., "open", "complete"
                        'type': o.get('prcTp', '').upper(),    # e.g., "L", "MKT", "SL", "SL-M"
                        'transaction_type': o.get('trnsTp', '').upper(), # "B" or "S"
                        'token': o.get('tok', ''),
                        'qty': qty,
                        'filled_qty': fld_qty,
                        'pending_qty': qty - fld_qty
                    })
                except Exception:
                    continue

        # Update Market Data
        with universal_data['sys']['lock']:
            universal_data['market']['orders'] = clean_orders
            universal_data['market']['raw']['orders'] = response

    except Exception as e:
        log.error(f"Error syncing orders: {e}", tags=["API", "ORD"])