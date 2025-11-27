import sys
import pyotp
from neo_api_client import NeoAPI

def authenticate_client(universal_data):    
    #   Performs 2FA Login and attaches client to ['sys']['api']

    log = universal_data['sys']['log']
    creds = universal_data['sys']['creds']['kotak']
    
    log.info("Attempting API Authentication...", tags=["AUTH"])
    
    try:
        # 1. Initialize Client
        client = NeoAPI(consumer_key=creds['consumer_key'],environment=creds.get('environment', 'prod'))
        
        # 2. Generate TOTP
        totp_secret = creds['totp_secret']
        totp = pyotp.TOTP(totp_secret).now()
        
        # 3. Login (Mobile + TOTP)
        login_resp = client.totp_login(mobile_number=creds['mobile_number'],ucc=creds['ucc'],totp=totp)
        
        if not login_resp or (isinstance(login_resp, str) and 'error' in login_resp.lower()):
             raise Exception(f"TOTP Login Failed: {login_resp}")

        # 4. Validate MPIN
        validate_resp = client.totp_validate(mpin=creds['mpin'])
        
        if not validate_resp or (isinstance(validate_resp, str) and 'error' in validate_resp.lower()):
            raise Exception(f"MPIN Validation Failed: {validate_resp}")
            
        # Success -> Store in SYS category
        universal_data['sys']['api'] = client
        log.info("Authentication Successful.", tags=["AUTH", "SUCCESS"])
        
    except Exception as e:
        log.critical(f"Authentication Failed: {str(e)}", tags=["AUTH", "CRITICAL"], exc_info=True)
        sys.exit(1)