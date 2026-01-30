import time
import pyotp
from neo_api_client import NeoAPI

def authenticate_client(universal_data):    
    """
    Performs 2FA Login using Kotak Neo standard sequence.
    """
    log = universal_data['sys']['log']
    user_id = universal_data.get('user_id', 'UNKNOWN')
    
    log.info(f"--- Authenticating Session: {user_id} ---", tags=["AUTH"])
    
    creds = universal_data['sys']['creds'].get('kotak', {})
    
    try:
        # FIXED: Removed 'use_default_logger' which caused the crash
        client = NeoAPI(
            consumer_key=creds['consumer_key'],
            environment=creds.get('environment', 'prod')
        )
        
        # STEP 2: Generate TOTP
        clean_secret = creds['totp_secret'].replace(" ", "").strip()
        totp_val = pyotp.TOTP(clean_secret).now()
        
        # STEP 3: TOTP Login
        log.info("Step 1: Sending Mobile/UCC/TOTP...", tags=["AUTH"])
        client.totp_login(
            mobile_number=creds['mobile_number'],
            ucc=creds['ucc'],
            totp=totp_val
        )
        
        # STEP 4: MPIN Validation
        log.info("Step 2: Validating MPIN...", tags=["AUTH"])
        response = client.totp_validate(mpin=creds['mpin'])
        
        if response and isinstance(response, dict) and response.get('stat') == 'NotOk':
            raise Exception(f"Broker Error: {response.get('message')}")

        with universal_data['sys']['lock']:
            universal_data['sys']['api'] = client
            universal_data['status']['auth_success'] = True
            
        log.info(">>> Login Successful. Session Active. <<<", tags=["AUTH", "OK"])
        return True
            
    except Exception as e:
        log.critical(f"Auth Sequence Failed: {e}", tags=["AUTH", "FAIL"])
        with universal_data['sys']['lock']:
            universal_data['status']['auth_success'] = False
            universal_data['status']['error_message'] = str(e)
        raise e