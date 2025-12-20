import threading
import time
import requests

# Track last sent messages to prevent spamming
_last_sent_cache = {} # { "user_id": { "msg_hash": timestamp } }

def _send_worker(bot_token, chat_id, message, log):
    """
    Background worker that actually hits the Telegram API.
    """
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=5)
        if response.status_code != 200:
            log.warning(f"Telegram Send Failed: {response.text}", tags=["TELEGRAM"])
    except Exception as e:
        log.warning(f"Telegram Connection Error: {e}", tags=["TELEGRAM"])

def send_alert(universal_data, message):
    """
    Public function to trigger an alert.
    Checks config -> Checks Rate Limit -> Spawns Thread.
    """
    user_id = universal_data['user_id']
    log = universal_data['sys']['log']
    
    # 1. Check Configuration
    conf = universal_data['sys']['config'].get('notifications', {})
    if not conf.get('enable_telegram', False):
        return

    # 2. Get Credentials
    creds = universal_data['sys']['creds'].get('telegram', {})
    token = creds.get('bot_token')
    chat_id = creds.get('chat_id')
    
    if not token or not chat_id:
        return

    # 3. Anti-Spam (Rate Limiting)
    # Don't send the exact same message more than once per minute
    now = time.time()
    if user_id not in _last_sent_cache:
        _last_sent_cache[user_id] = {}
        
    # Clean old cache
    user_cache = _last_sent_cache[user_id]
    keys_to_del = [k for k, t in user_cache.items() if now - t > 60]
    for k in keys_to_del: del user_cache[k]
    
    msg_hash = hash(message)
    if msg_hash in user_cache:
        return # Skip (Duplicate)
    
    user_cache[msg_hash] = now

    # 4. Spawn Thread (Non-blocking)
    # We create a formatted message with the User Alias
    alias = universal_data['sys']['config'].get('account_name', user_id)
    formatted_msg = f"🚨 *{alias} Alert*\n\n{message}"
    
    t = threading.Thread(target=_send_worker, args=(token, chat_id, formatted_msg, log), daemon=True)
    t.start()