import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime

# --- CREDENTIALS (USER_01) ---
EMAIL_USER = "ethanarkham@gmail.com"
EMAIL_PASS = "ncyv owme eags dkwe"
SENDER_FILTER = "noreply@nmail.kotaksecurities.com"
SUBJECT_FILTER = "Kill Switch Activated"

def decode_mime_header(header_value):
    """
    Decodes headers like =?UTF-8?B?S2lsbCBTd2l0Y2ggQWN0aXZhdGVk...?=
    into readable strings.
    """
    if not header_value:
        return ""
        
    decoded_fragments = decode_header(header_value)
    result_str = ""
    
    for content, encoding in decoded_fragments:
        if isinstance(content, bytes):
            if encoding:
                try:
                    result_str += content.decode(encoding)
                except LookupError:
                    # Fallback for unknown encodings
                    result_str += content.decode('utf-8', errors='ignore')
                except UnicodeDecodeError:
                    result_str += content.decode('utf-8', errors='ignore')
            else:
                # No encoding specified, usually ascii or utf-8
                result_str += content.decode('utf-8', errors='ignore')
        else:
            result_str += str(content)
            
    return result_str

def run_debug():
    print(f"--- GMAIL DECODER TEST ---")
    print(f"Target: '{SUBJECT_FILTER}' inside emails from '{SENDER_FILTER}'")
    
    try:
        # 1. CONNECT
        print("\n1. Connecting to Gmail IMAP...")
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(EMAIL_USER, EMAIL_PASS)
        print("   [SUCCESS] Logged in.")
        
        mail.select("inbox")

        # 2. SEARCH BY SENDER
        print(f"\n2. Searching emails from sender...")
        typ, data = mail.search(None, f'(FROM "{SENDER_FILTER}")')
        uids = data[0].split()
        
        if len(uids) == 0:
            print("   [ERROR] No emails found from Kotak.")
            return

        print(f"   -> Found {len(uids)} emails. Checking last 5...")

        # 3. INSPECT & DECODE
        recent_uids = uids[-5:]
        
        for uid in reversed(recent_uids):
            # Fetch Header
            typ, msg_data = mail.fetch(uid, "(RFC822.HEADER)")
            msg = email.message_from_bytes(msg_data[0][1])
            
            # --- THE FIX IS HERE ---
            raw_subject = msg.get("Subject", "")
            clean_subject = decode_mime_header(raw_subject)
            date_str = msg.get("Date", "")
            
            print("-" * 60)
            print(f"ID: {uid.decode()}")
            print(f"Raw Subject:   {raw_subject}")
            print(f"Clean Subject: {clean_subject}")
            print(f"Date:          {date_str}")
            
            # MATCH CHECK
            if SUBJECT_FILTER.lower() in clean_subject.lower():
                print(f"\n>>> ✅ MATCH CONFIRMED! <<<")
                print(f">>> The system CAN read this email now.")
            else:
                print(f"\n(No match)")

        mail.logout()

    except Exception as e:
        print(f"\n[CRITICAL ERROR]: {e}")

if __name__ == "__main__":
    run_debug()