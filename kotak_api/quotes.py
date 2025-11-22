# kotak_api/quotes.py

def sync_ltp(universal_data):
    """
    Fetches live LTP for all tokens found in 'state']['positions'].
    Updates universal_data['state']['quotes'] = {token_str: ltp_float}
    """
    log = universal_data['logger']
    client = universal_data['client']
    positions = universal_data['state'].get('positions', [])

    if not positions:
        return

    try:
        # 1. Prepare Token List
        # API requires format: [{'instrument_token': '...', 'exchange_segment': '...'}]
        quote_tokens = []
        token_map = {} # To map result back easily

        for p in positions:
            t = p['token']
            s = p['segment']
            if t and s:
                # Build payload object
                quote_tokens.append({
                    "instrument_token": str(t),
                    "exchange_segment": str(s)
                })
                token_map[t] = 0.0 # Init

        if not quote_tokens:
            return

        # 2. API Call
        # The 'quotes' method typically accepts a list of dicts in Neo API
        response = client.quotes(instrument_tokens=quote_tokens, quote_type='LTP')

        # 3. Parse Response
        # Neo API Quote Response Structure usually:
        # {'message': [ {'instrument_token': '...', 'ltp': '...'}, ... ]}
        # OR sometimes flattened. Handling standard Neo structure:
        
        if response and 'message' in response:
            data_list = response['message']
            
            updated_quotes = {}
            
            for item in data_list:
                tk = item.get('instrument_token', '')
                ltp = float(item.get('last_traded_price', 0.0))
                if tk:
                    updated_quotes[tk] = ltp
            
            # 4. Update State
            # We overwrite or update the quotes dictionary
            universal_data['state']['quotes'].update(updated_quotes)

        elif response and 'data' in response: 
             # Fallback if response structure is different (some versions)
             # Handling 'data' key if 'message' key isn't present
             for item in response['data']:
                tk = item.get('instrument_token', '')
                ltp = float(item.get('last_traded_price', 0.0))
                if tk:
                    universal_data['state']['quotes'][tk] = ltp

    except Exception as e:
        # Don't crash on quote failure, just log (MTM will use 0 or old price)
        log.error(f"Error syncing quotes: {e}", tags=["API", "QT"], exc_info=True)