# kotak_api/orders.py

def sync_orders(universal_data):
    """
    Fetches order report and updates universal_data['state']['orders'].
    Used by Risk Service to check for SL-M triggers.
    """
    log = universal_data['logger']
    client = universal_data['client']

    try:
        # 1. API Call
        response = client.order_report()

        # 2. Validation
        if not response or 'data' not in response:
            # It is possible to have no orders
            universal_data['state']['orders'] = []
            return

        raw_orders = response['data']
        
        # 3. Extraction (Keeping raw fields relevant to SL check)
        # We don't need to parse everything, just what 'trigger_logic' needs.
        clean_orders = []
        for o in raw_orders:
            clean_orders.append({
                'order_id': o.get('nOrdNo', ''),
                'status': o.get('ordSt', '').upper(),  # e.g., 'COMPLETE', 'TRADED', 'REJECTED'
                'type': o.get('prcTp', ''),            # e.g., 'MKT', 'L', 'SL', 'SL-M'
                'transaction_type': o.get('trnsTp', ''), # 'B' or 'S'
                'symbol': o.get('trdSym', ''),
                'token': o.get('tok', ''),
                'price': o.get('prc', 0),
                'trigger_price': o.get('trgPrc', 0)
            })

        # 4. Update State
        universal_data['state']['orders'] = clean_orders
        # log.info(f"Synced {len(clean_orders)} orders.", tags=["API", "ORD"])

    except Exception as e:
        log.error(f"Error syncing orders: {e}", tags=["API", "ORD"], exc_info=True)