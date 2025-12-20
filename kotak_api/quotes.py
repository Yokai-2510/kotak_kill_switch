def sync_ltp(universal_data):
    log = universal_data['sys']['log']
    client = universal_data['sys']['api']

    with universal_data['sys']['lock']:
        positions = universal_data['market']['positions']

    if not positions:
        return

    try:
        quote_tokens = []
        for p in positions:
            if p['token'] and p['segment']:
                quote_tokens.append({
                    "instrument_token": str(p['token']),
                    "exchange_segment": str(p['segment'])
                })

        if not quote_tokens: return

        response = client.quotes(instrument_tokens=quote_tokens, quote_type='ltp')

        # --- STRICT VALIDATION ---
        if response is None:
            raise Exception("Quote API returned None")
        # Note: Quotes API might not strictly have 'stat' field in all versions, 
        # but usually does. We check for list presence.
        data_list = []
        if 'message' in response: data_list = response['message']
        elif 'data' in response: data_list = response['data']
        
        if not data_list and response.get('stat') != 'Ok':
             raise Exception(f"Quote API Error: {response}")
        # -------------------------

        updated_quotes = {}
        for item in data_list:
            tk = item.get('instrument_token', '')
            ltp = float(item.get('last_traded_price', 0.0) or 0.0)
            if tk and ltp > 0: # Only update if we have a valid price
                updated_quotes[tk] = ltp

        with universal_data['sys']['lock']:
            universal_data['market']['quotes'].update(updated_quotes)
            universal_data['market']['raw']['quotes'] = response

    except Exception as e:
        # Re-raise to preserve old prices
        raise e