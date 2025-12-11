import imaplib
import email
import re
import time
from threading import Thread
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

# =========================================================
#  ORIGINAL OTP LOGIC (Restored)
# =========================================================

def _imap_worker(creds, gmail_conf, result_bucket):
    """
    Internal worker: Connects to Gmail IMAP and listens for Kotak OTP.
    """
    try:
        # 1. Extract Credentials
        email_user = creds.get('email')
        email_pass = creds.get('google_app_password')
        
        # 2. Extract Config with Fallbacks
        sender_filter = gmail_conf.get('sender_filter') or creds.get('sender_filter') or "noreply@nmail.kotaksecurities.com"
        timeout = gmail_conf.get('timeout_seconds', 120)

        if not email_user or not email_pass:
            result_bucket['error'] = "Missing Gmail Credentials"
            return

        # 3. Connect IMAP
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # Get baseline UID (Ignore old emails)
        typ, data = mail.search(None, f'(FROM "{sender_filter}")')
        existing = data[0].split()
        last_uid = existing[-1] if existing else b"0"

        start = time.time()
        
        # Poll loop
        while time.time() - start < timeout:
            mail.select("inbox")
            typ, data = mail.search(None, f'(FROM "{sender_filter}")')
            uids = data[0].split()
            
            if not uids: 
                time.sleep(1)
                continue

            latest = uids[-1]
            if latest > last_uid:
                # Fetch body
                typ, msg_data = mail.fetch(latest, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            payload = part.get_payload(decode=True)
                            if payload:
                                body = payload.decode(errors="ignore")
                                break
                else:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        body = payload.decode(errors="ignore")

                # Extract 4-6 digit OTP
                if body:
                    # Look for 4-6 digits (Kotak standard)
                    match = re.search(r"\b(\d{4,6})\b", body)
                    if match:
                        result_bucket['otp'] = match.group(1)
                        try: mail.logout()
                        except: pass
                        return

            time.sleep(1.5)
            
        result_bucket['error'] = "Timeout waiting for OTP email"
        try: mail.logout()
        except: pass

    except Exception as e:
        result_bucket['error'] = str(e)

def start_otp_listener(universal_data):
    """
    Starts the background thread and returns a result bucket dict.
    """
    # Accessing Single-Account Structure
    creds = universal_data['sys']['creds'].get('gmail', {})
    config = universal_data['sys']['config'].get('gmail', {})
    
    result_bucket = {'otp': None, 'error': None}
    
    t = Thread(target=_imap_worker, args=(creds, config, result_bucket), daemon=True)
    t.start()
    
    return result_bucket

# =========================================================
#  NEW FUNCTIONALITY (For Kill Verification Only)
# =========================================================

def check_kill_email(universal_data, lookback_seconds=300):
    """
    Blocking Check: Scans for 'Kill Switch Activated' email.
    Used ONLY during the Kill Verification phase.
    """
    creds = universal_data['sys']['creds'].get('gmail', {})
    conf = universal_data['sys']['config'].get('gmail', {})
    
    email_user = creds.get('email')
    email_pass = creds.get('google_app_password')
    sender = conf.get('sender_filter', 'noreply@nmail.kotaksecurities.com')
    kill_subj = conf.get('kill_subject', 'Kill Switch Activated')

    if not email_user or not email_pass:
        return False

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=15)
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # Search for specific Sender AND Subject
        search_crit = f'(FROM "{sender}" SUBJECT "{kill_subj}")'
        typ, data = mail.search(None, search_crit)
        
        uids = data[0].split()
        if not uids:
            mail.logout()
            return False
            
        # Check recent matches
        recent_uids = uids[-3:] 
        now_utc = datetime.now().astimezone() 
        threshold = now_utc - timedelta(seconds=lookback_seconds)
        found = False
        
        for uid in reversed(recent_uids):
            try:
                typ, msg_data = mail.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (DATE)])")
                raw_header = msg_data[0][1]
                msg = email.message_from_bytes(raw_header)
                date_str = msg.get("Date")
                
                if date_str:
                    email_date = parsedate_to_datetime(date_str)
                    if email_date >= threshold:
                        found = True
                        break
            except: continue
        
        try: mail.logout()
        except: pass
        
        return found

    except Exception:
        return False