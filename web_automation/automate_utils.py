import imaplib
import email
import re
import time
from threading import Thread

def _imap_worker(creds, config, result_bucket):
    """
    Internal worker: Connects to Gmail IMAP and listens for Kotak OTP.
    """
    try:
        email_user = creds['email']
        email_pass = creds['google_app_password']
        sender_filter = config['sender_filter']
        timeout = config['timeout_seconds']

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
                
                body = msg.get_payload(decode=True).decode(errors="ignore")
                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() == "text/plain":
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break

                # Extract 4-6 digit OTP
                match = re.search(r"\b(\d{4,6})\b", body)
                if match:
                    result_bucket['otp'] = match.group(1)
                    mail.logout()
                    return

            time.sleep(1.5)
            
        result_bucket['error'] = "Timeout waiting for OTP"
        mail.logout()

    except Exception as e:
        result_bucket['error'] = str(e)

def start_otp_listener(universal_data):
    """
    Starts the background thread and returns a result bucket dict.
    Access result_bucket['otp'] to see if value arrived.
    """
    # ACCESSING NEW STRUCTURE
    creds = universal_data['sys']['creds']['gmail']
    config = universal_data['sys']['config']['gmail']
    
    result_bucket = {'otp': None, 'error': None}
    
    t = Thread(target=_imap_worker, args=(creds, config, result_bucket), daemon=True)
    t.start()
    
    return result_bucket