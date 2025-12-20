import sys
import time
import pyotp
from neo_api_client import NeoAPI

def authenticate_client(universal_data):    
    """
    Performs 2FA Login.
    Includes strict validation of credential structure.
    """
    log = universal_data['sys']['log']
    user_id = universal_data.get('user_id', 'UNKNOWN')
    
    log.info(f"--- Starting Auth Sequence for {user_id} ---", tags=["AUTH"])
    
    # 1. READ CREDENTIALS SAFELY
    root_creds = universal_data['sys']['creds']
    
    # Check if 'kotak' key exists
    if 'kotak' in root_creds:
        kotak_creds = root_creds['kotak']
    else:
        # Fallback: Check if credentials are flat (user pasted them directly without "kotak" wrapper)
        if 'consumer_key' in root_creds:
            log.warning("Credentials structure is flattened (missing 'kotak' wrapper). Attempting to use directly.", tags=["AUTH", "WARN"])
            kotak_creds = root_creds
        else:
            raise KeyError("Credentials missing 'kotak' block and valid keys.")

    # 2. VALIDATE REQUIRED KEYS
    required_keys = ['consumer_key', 'totp_secret', 'mobile_number', 'mpin']
    missing = [k for k in required_keys if not kotak_creds.get(k)]
    
    if missing:
        msg = f"Missing credential fields: {', '.join(missing)}"
        log.error(msg, tags=["AUTH", "FAIL"])
        raise ValueError(msg)

    # 3. AUTH LOOP
    max_retries = 3
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            log.info(f"(1/4) Initializing NeoAPI Client (Attempt {attempt})...", tags=["AUTH"])
            
            # Initialize
            client = NeoAPI(
                consumer_key=kotak_creds['consumer_key'],
                environment=kotak_creds.get('environment', 'prod')
            )
            
            log.info("(2/4) Generating TOTP...", tags=["AUTH"])
            clean_secret = kotak_creds['totp_secret'].replace(" ", "").strip()
            totp = pyotp.TOTP(clean_secret).now()
            
            log.info("(3/4) Sending Login Request...", tags=["AUTH"])
            client.totp_login(
                mobile_number=kotak_creds['mobile_number'],
                ucc=kotak_creds.get('ucc', ''),
                totp=totp
            )
            
            log.info("(4/4) Validating MPIN...", tags=["AUTH"])
            msg = client.totp_validate(mpin=kotak_creds['mpin'])
            
            # Basic check on response
            if msg and isinstance(msg, dict) and 'error' in str(msg).lower():
                 raise Exception(f"Validation Error: {msg}")

            # SUCCESS
            universal_data['sys']['api'] = client
            log.info(">>> Authentication SUCCESS <<<", tags=["AUTH"])
            return 
            
        except Exception as e:
            if attempt == max_retries:
                log.critical(f"Auth Sequence Aborted: {e}", tags=["AUTH", "CRITICAL"])
                raise e
            else:
                log.warning(f"Auth Attempt {attempt} Failed: {e}. Retrying...", tags=["AUTH", "RETRY"])
                time.sleep(retry_delay)