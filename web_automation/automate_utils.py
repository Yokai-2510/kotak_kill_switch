import imaplib
import email
import re
import time
from threading import Thread
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime

# =========================================================
#  DEBUG-ENABLED OTP LOGIC
# =========================================================

def _imap_worker(creds, gmail_conf, result_bucket):
    try:
        email_user = creds.get('email')
        email_pass = creds.get('google_app_password')
        
        # We make the filter more generic to handle domain changes
        sender_filter = "kotak" 
        timeout = gmail_conf.get('timeout_seconds', 120)

        if not email_user or not email_pass:
            result_bucket['error'] = "Missing Gmail Credentials"
            return

        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # Get baseline (UID of the last email currently in inbox)
        typ, data = mail.search(None, 'ALL')
        existing = data[0].split()
        last_uid = existing[-1] if existing else b"0"
        
        print(f">>> OTP Listener Started. Waiting for email containing '{sender_filter}'...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            mail.select("inbox")
            # Search for ANY email from the sender
            typ, data = mail.search(None, 'UNSEEN') # Or 'ALL' to be safe
            uids = data[0].split()
            
            if uids:
                for uid in reversed(uids):
                    if int(uid) <= int(last_uid): continue # Only check NEW emails
                    
                    typ, msg_data = mail.fetch(uid, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])
                    
                    sender = str(msg.get("From")).lower()
                    subject = str(msg.get("Subject"))
                    
                    print(f"DEBUG: Scanned Email -> From: {sender} | Sub: {subject}")

                    # Check if 'kotak' is in the sender address
                    if "kotak" in sender:
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    payload = part.get_payload(decode=True)
                                    if payload: body = payload.decode(errors="ignore")
                                    break
                        else:
                            payload = msg.get_payload(decode=True)
                            if payload: body = payload.decode(errors="ignore")

                        if body:
                            # Look for 4 to 6 digit OTP
                            match = re.search(r"\b(\d{4,6})\b", body)
                            if match:
                                otp = match.group(1)
                                print(f">>> SUCCESS: Found OTP {otp} in email from {sender}")
                                result_bucket['otp'] = otp
                                try: mail.logout()
                                except: pass
                                return
                            else:
                                print(f"DEBUG: Found Kotak email but no OTP digits found in body: {body[:50]}...")
            
            time.sleep(2)
            
        result_bucket['error'] = "Timeout: Kotak OTP email not detected."
        print(">>> ERROR: OTP detection timed out.")
        try: mail.logout()
        except: pass

    except Exception as e:
        print(f">>> IMAP CRITICAL ERROR: {e}")
        result_bucket['error'] = str(e)

def start_otp_listener(universal_data):
    creds = universal_data['sys']['creds'].get('gmail', {})
    config = universal_data['sys']['config'].get('gmail', {})
    result_bucket = {'otp': None, 'error': None}
    t = Thread(target=_imap_worker, args=(creds, config, result_bucket), daemon=True)
    t.start()
    return result_bucket


# =========================================================
#  KILL VERIFICATION
# =========================================================

def check_kill_email(universal_data, lookback_seconds=300):
    creds = universal_data['sys']['creds'].get('gmail', {})
    conf = universal_data['sys']['config'].get('gmail', {})
    
    email_user = creds.get('email')
    email_pass = creds.get('google_app_password')
    # Using flexible sender check here too
    kill_subj = conf.get('kill_subject', 'Kill Switch Activated')

    if not email_user or not email_pass: return False

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", timeout=15)
        mail.login(email_user, email_pass)
        mail.select("inbox")

        # Search by Subject only for broader match
        search_crit = f'(SUBJECT "{kill_subj}")'
        typ, data = mail.search(None, search_crit)
        
        uids = data[0].split()
        if not uids:
            mail.logout(); return False
            
        recent_uids = uids[-3:] 
        threshold = datetime.now().astimezone() - timedelta(seconds=lookback_seconds)
        found = False
        
        for uid in reversed(recent_uids):
            typ, msg_data = mail.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (DATE FROM)])")
            msg = email.message_from_bytes(msg_data[0][1])
            sender = str(msg.get("From")).lower()
            
            if "kotak" in sender:
                email_date = parsedate_to_datetime(msg.get("Date"))
                if email_date >= threshold:
                    found = True; break
        
        mail.logout(); return found
    except: return False