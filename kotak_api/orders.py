def sync_orders(universal_data):
    log = universal_data['sys']['log']
    client = universal_data['sys']['api']

    try:
        response = client.order_report()
        
        # --- STRICT VALIDATION ---
        if response is None:
            raise Exception("API returned None")
            
        stat = response.get('stat', '').lower()
        st_code = str(response.get('stCode', ''))
        
        raw_data = []

        if stat != 'ok':
            # Whitelist "No Data" error
            if st_code == '5203':
                raw_data = []
            else:
                raise Exception(f"API Status not OK: {response}")
        else:
            raw_data = response.get('data', [])
            if raw_data is None: raw_data = []
        # -------------------------
        
        clean_orders = []
        for o in raw_data:
            try:
                qty = float(o.get('qty', 0) or 0)
                fld_qty = float(o.get('fldQty', 0) or 0)
                
                clean_orders.append({
                    'order_id': o.get('nOrdNo', ''),
                    'status': o.get('ordSt', '').upper(),
                    'type': o.get('prcTp', '').upper(),
                    'transaction_type': o.get('trnsTp', '').upper(),
                    'token': o.get('tok', ''),
                    'qty': qty,
                    'filled_qty': fld_qty,
                    'pending_qty': qty - fld_qty
                })
            except Exception:
                continue

        with universal_data['sys']['lock']:
            universal_data['market']['orders'] = clean_orders
            universal_data['market']['raw']['orders'] = response

    except Exception as e:
        raise e