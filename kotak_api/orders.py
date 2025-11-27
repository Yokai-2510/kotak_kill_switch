def sync_orders(universal_data):
    log = universal_data['sys']['log']
    client = universal_data['sys']['api']

    try:
        response = client.order_report()
        
        clean_orders = []
        if response and 'data' in response:
            for o in response['data']:
                clean_orders.append({
                    'order_id': o.get('nOrdNo', ''),
                    'status': o.get('ordSt', '').upper(),
                    'type': o.get('prcTp', ''),
                    'transaction_type': o.get('trnsTp', ''),
                    'token': o.get('tok', '')
                })

        # Update Market Data + RAW DUMP
        with universal_data['sys']['lock']:
            universal_data['market']['orders'] = clean_orders
            universal_data['market']['raw']['orders'] = response  # <--- RAW OVERWRITE

    except Exception as e:
        log.error(f"Error syncing orders: {e}", tags=["API", "ORD"])