import time
import json
import threading
from trigger_logic.stop_loss import check_sl_status

# Constants
INDEX_TOKEN_BANKNIFTY = "26009"
INDEX_SEGMENT = "nse_cm"

def run_websocket_service(universal_data):
    log = universal_data['sys']['log']
    client = universal_data['sys']['api']
    
    if not client: return

    log.info("Initializing WebSocket Service (with Live Debugging)...", tags=["SVC", "WS"])

    # =========================================================
    #  DEBUG: PERSISTENT FEED WRITER
    # =========================================================
    def dump_cache_to_file():
        """Writes the current known state of the market to a file."""
        try:
            with universal_data['sys']['lock']:
                debug_info = {
                    "last_update": time.strftime("%H:%M:%S"),
                    "bank_nifty_spot": universal_data['market'].get('index_spot', 0.0),
                    "live_quotes": universal_data['market']['quotes'],
                    "subscribed_tokens": universal_data['market'].get('subscribed_tokens', []),
                    "active_positions_count": len(universal_data['market']['positions'])
                }
            
            with open("ws_live_feed_debug.txt", "w") as f:
                f.write(json.dumps(debug_info, indent=2))
        except: pass

    # =========================================================
    #  CALLBACK: ON MESSAGE
    # =========================================================
    def on_message(message):
        try:
            payload = message
            if isinstance(message, dict) and "data" in message:
                raw_inner = message["data"]
                if isinstance(raw_inner, str):
                    try: payload = json.loads(raw_inner)
                    except: payload = raw_inner
                else: payload = raw_inner

            # --- 1. HANDLE MARKET DATA ---
            ticks = []
            if isinstance(payload, list): ticks = payload
            elif isinstance(payload, dict) and ('tk' in payload or 'ltp' in payload): ticks = [payload]
            
            if ticks:
                with universal_data['sys']['lock']:
                    for tick in ticks:
                        token = str(tick.get('tk') or tick.get('instrument_token', ''))
                        price = tick.get('ltp') or tick.get('lp') or tick.get('last_traded_price')
                        
                        if token and price is not None:
                            universal_data['market']['quotes'][token] = float(price)
                            if token == INDEX_TOKEN_BANKNIFTY:
                                universal_data['market']['index_spot'] = float(price)
                
                dump_cache_to_file() # Update debug file
                return

            # --- 2. HANDLE ORDER UPDATES ---
            if isinstance(payload, dict):
                if 'nOrdNo' in payload:
                    log.info(f"Push: Order {payload.get('nOrdNo')} update.", tags=["WS", "ORDER"])
                    # Instant reaction to SL hit via the separate thread
                    check_sl_status(universal_data, order_update=payload)
                    dump_cache_to_file()

                elif payload.get('ak') == 'ok':
                    log.info(f"WS Server Confirmed: {payload.get('msg')}", tags=["WS", "OK"])

        except Exception as e:
            log.error(f"WS Parsing Error: {e}", tags=["WS", "ERR"])

    # =========================================================
    #  LIFECYCLE MANAGEMENT
    # =========================================================
    client.on_message = on_message
    client.on_error = lambda e: log.error(f"WS Error: {e}", tags=["WS"])
    client.on_close = lambda m: log.warning("WS Closed.", tags=["WS"])

    # 1. Start Order Feed
    try:
        client.subscribe_to_orderfeed()
        time.sleep(2) 
    except: pass

    # 2. Start Ticks
    _subscribe_to_active_tokens(universal_data)

    # 3. Dynamic Resubscription Watchdog
    while universal_data['signals']['system_active']:
        try:
            time.sleep(15)
            if _needs_resubscription(universal_data):
                _subscribe_to_active_tokens(universal_data)
        except: pass

def _subscribe_to_active_tokens(universal_data):
    client = universal_data['sys']['api']
    if not client or not universal_data['signals']['system_active']: return

    with universal_data['sys']['lock']:
        positions = universal_data['market']['positions']
    
    tokens = [{"instrument_token": INDEX_TOKEN_BANKNIFTY, "exchange_segment": INDEX_SEGMENT}]
    for p in positions:
        if str(p['token']) != INDEX_TOKEN_BANKNIFTY:
            tokens.append({"instrument_token": str(p['token']), "exchange_segment": str(p['segment'])})
    
    try:
        client.subscribe(instrument_tokens=tokens)
        with universal_data['sys']['lock']:
            universal_data['market']['subscribed_tokens'] = [t['instrument_token'] for t in tokens]
    except: pass

def _needs_resubscription(universal_data):
    with universal_data['sys']['lock']:
        current_req = set([str(p['token']) for p in universal_data['market']['positions']])
        current_req.add(INDEX_TOKEN_BANKNIFTY)
        already_subbed = set(universal_data['market'].get('subscribed_tokens', []))
    return not current_req.issubset(already_subbed)