import sys
import time
import pyotp
import binascii
from neo_api_client import NeoAPI

def authenticate_client(universal_data):    
    """
    Performs 2FA Login.
    Includes Retry Logic for network stability.
    Attaches authenticated client to ['sys']['api'].
    """
    log = universal_data['sys']['log']
    creds = universal_data['sys']['creds']['kotak']
    user_id = universal_data.get('user_id', 'UNKNOWN')
    
    log.info(f"--- Starting Auth Sequence for {user_id} ---", tags=["AUTH"])
    
    required_keys = ['consumer_key', 'totp_secret', 'mobile_number', 'mpin']
    if any(not creds.get(k) for k in required_keys):
        log.error("Missing credentials.", tags=["AUTH", "FAIL"])
        raise ValueError("Missing Credentials")

    # Retry Configuration
    max_retries = 3
    retry_delay = 2

    for attempt in range(1, max_retries + 1):
        try:
            # --- STEP 1: INITIALIZE CLIENT ---
            log.info(f"(1/4) Initializing NeoAPI Client (Attempt {attempt})...", tags=["AUTH"])
            
            client = NeoAPI(
                consumer_key=creds['consumer_key'],
                environment=creds.get('environment', 'prod')
            )
            
            # --- STEP 2: GENERATE TOTP ---
            # We generate fresh TOTP every attempt to avoid expiry
            log.info("(2/4) Generating TOTP...", tags=["AUTH"])
            try:
                clean_secret = creds['totp_secret'].replace(" ", "").strip()
                totp = pyotp.TOTP(clean_secret).now()
            except Exception as e:
                # Fatal error, do not retry
                log.critical(f"TOTP Gen Failed: {repr(e)}", tags=["AUTH", "CRITICAL"])
                raise e
            
            # --- STEP 3: LOGIN REQUEST ---
            log.info(f"(3/4) Sending Login Request...", tags=["AUTH"])
            login_resp = client.totp_login(
                mobile_number=creds['mobile_number'],
                ucc=creds['ucc'],
                totp=totp
            )
            
            if not login_resp or (isinstance(login_resp, dict) and 'error' in str(login_resp).lower()):
                 raise Exception(f"Login Rejected: {login_resp}")

            # --- STEP 4: MPIN VALIDATION ---
            log.info("(4/4) Validating MPIN...", tags=["AUTH"])
            validate_resp = client.totp_validate(mpin=creds['mpin'])
            
            if not validate_resp or (isinstance(validate_resp, dict) and 'error' in str(validate_resp).lower()):
                raise Exception(f"MPIN Rejected: {validate_resp}")
                
            # --- SUCCESS ---
            universal_data['sys']['api'] = client
            log.info(">>> Authentication SUCCESS <<<", tags=["AUTH"])
            return # Exit function on success
            
        except Exception as e:
            # Check if this is the last attempt
            if attempt == max_retries:
                # Use repr() to avoid the "NoneType" string crash
                log.critical(f"Auth Sequence Aborted after {max_retries} attempts: {repr(e)}", tags=["AUTH", "CRITICAL"])
                raise e
            else:
                log.warning(f"Auth Attempt {attempt} Failed: {repr(e)}. Retrying in {retry_delay}s...", tags=["AUTH", "RETRY"])
                time.sleep(retry_delay)