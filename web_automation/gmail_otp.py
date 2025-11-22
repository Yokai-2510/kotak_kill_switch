import os
import time
import re
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

def get_gmail_service(universal_data):
    """
    Authenticates with Gmail API. 
    Triggers a local browser flow for OAuth on the first run.
    """
    log = universal_data['logger']
    gmail_conf = universal_data['config']['gmail']
    
    # Resolve paths relative to project root (assuming CWD is project root)
    creds_file = gmail_conf['credentials_file']
    token_file = gmail_conf['token_file']
    scopes = gmail_conf['scopes']

    creds = None
    
    # 1. Load existing token
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, scopes)
        
    # 2. Refresh or Create new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            log.info("Refreshing Gmail Access Token...", tags=["GMAIL"])
            creds.refresh(Request())
        else:
            log.info(">>> PLEASE AUTHORIZE GMAIL ACCESS IN THE BROWSER <<<", tags=["GMAIL", "AUTH"])
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, scopes)
            creds = flow.run_local_server(port=0)
            
        # Save the new token for future headless runs
        with open(token_file, 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

def fetch_latest_otp(universal_data):
    """
    Polls Gmail for the latest email from Kotak and extracts the OTP.
    Timeout: 60 seconds.
    """
    log = universal_data['logger']
    conf = universal_data['config']['gmail']
    service = get_gmail_service(universal_data)
    
    log.info("Polling Gmail for OTP...", tags=["GMAIL"])
    
    start_time = time.time()
    
    # Polling Loop
    while (time.time() - start_time) < 60:
        try:
            # Query: From specific sender, Subject contains "OTP", received in last 1 day
            # Adjust 'newer_than' if needed, but '1d' is safe.
            query = f"from:{conf['otp_sender']} {conf['otp_subject_contains']} newer_than:1d"
            
            # Get list of messages
            results = service.users().messages().list(userId='me', q=query, maxResults=1).execute()
            messages = results.get('messages', [])
            
            if not messages:
                time.sleep(3)
                continue
                
            # Get the email content
            msg_id = messages[0]['id']
            msg = service.users().messages().get(userId='me', id=msg_id).execute()
            snippet = msg.get('snippet', '')
            
            # Regex Logic:
            # Kotak OTPs are usually 4 or 6 digits. 
            # Snippet usually looks like: "Your OTP is 1234. Do not share..."
            match = re.search(r'\b(\d{4,6})\b', snippet)
            
            if match:
                otp_code = match.group(1)
                
                # Optional: Ensure this email isn't too old (check internalDate)
                msg_time = int(msg['internalDate']) / 1000
                if (time.time() - msg_time) > 120: # Ignore if older than 2 mins
                    log.warning("Found email but it looks old. Waiting for new one...", tags=["GMAIL"])
                    time.sleep(2)
                    continue
                    
                log.info(f"OTP Found: {otp_code}", tags=["GMAIL", "SUCCESS"])
                return otp_code
            
        except Exception as e:
            log.warning(f"Gmail Fetch Error: {e}. Retrying...", tags=["GMAIL"])
            
        time.sleep(3)
        
    raise Exception("Gmail Timeout: OTP email not received within 60 seconds.")