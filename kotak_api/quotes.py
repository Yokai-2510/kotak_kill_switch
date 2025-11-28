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

        updated_quotes = {}
        data_list = []
        
        if response and 'message' in response:
            data_list = response['message']
        elif response and 'data' in response:
            data_list = response['data']
            
        for item in data_list:
            tk = item.get('instrument_token', '')
            ltp = float(item.get('last_traded_price', 0.0))
            if tk: updated_quotes[tk] = ltp

        # Update Market Data + RAW DUMP
        with universal_data['sys']['lock']:
            universal_data['market']['quotes'].update(updated_quotes)
            universal_data['market']['raw']['quotes'] = response  # <--- RAW OVERWRITE

    except Exception as e:
        log.error(f"Error syncing quotes: {e}", tags=["API", "QT"])