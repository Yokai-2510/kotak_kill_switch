import sys
import pyotp
from neo_api_client import NeoAPI

def authenticate_client(universal_data):
    """
    Performs 2FA Login (TOTP + MPIN) and attaches client to universal_data.
    Handles exceptions internally and exits on failure.
    """
    log = universal_data['logger']
    creds = universal_data['creds']['kotak']
    
    log.info("Attempting API Authentication...", tags=["AUTH"])
    
    try:
        # 1. Initialize Client
        client = NeoAPI(
            consumer_key=creds['consumer_key'],
            environment=creds.get('environment', 'prod')
        )
        
        # 2. Generate TOTP
        totp_secret = creds['totp_secret']
        totp = pyotp.TOTP(totp_secret).now()
        
        # 3. Login (Mobile + TOTP)
        login_resp = client.totp_login(
            mobile_number=creds['mobile_number'],
            ucc=creds['ucc'],
            totp=totp
        )
        
        # Basic validation
        if not login_resp or (isinstance(login_resp, str) and 'error' in login_resp.lower()):
             raise Exception(f"TOTP Login Failed: {login_resp}")

        # 4. Validate MPIN (Session Token)
        validate_resp = client.totp_validate(mpin=creds['mpin'])
        
        if not validate_resp or (isinstance(validate_resp, str) and 'error' in validate_resp.lower()):
            raise Exception(f"MPIN Validation Failed: {validate_resp}")
            
        # Success
        universal_data['client'] = client
        log.info("Authentication Successful.", tags=["AUTH", "SUCCESS"])
        
    except Exception as e:
        log.critical(f"Authentication Failed: {str(e)}", tags=["AUTH", "CRITICAL"], exc_info=True)
        sys.exit(1)


# --- STANDALONE TESTING ---
if __name__ == "__main__":
    import json
    import os
    
    print("\n>>> STARTING STANDALONE AUTH & DATA TEST")
    
    # 1. Load Credentials directly
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    creds_path = os.path.join(project_root, "source", "credentials.json")
    
    if not os.path.exists(creds_path):
        print(f"❌ Error: Credentials not found at {creds_path}")
        sys.exit(1)
        
    with open(creds_path, 'r') as f:
        creds = json.load(f)

    # 2. Mock Logger
    class MockLogger:
        def info(self, msg, tags=None): 
            print(f"[INFO] {msg} {tags if tags else ''}")
        def critical(self, msg, tags=None, exc_info=False): 
            print(f"[CRITICAL] {msg} {tags if tags else ''}")

    # 3. Construct Test Data
    test_data = {
        'creds': creds,
        'logger': MockLogger(),
        'client': None
    }
    
    # 4. Run Authentication
    authenticate_client(test_data)
    
    # 5. Test Position Fetch
    if test_data.get('client'):
        client = test_data['client']
        print(f"\n✅ SUCCESS: Client Object Created.")
        
        print("\n>>> FETCHING POSITIONS...")
        try:
            positions_resp = client.positions()
            
            # Pretty print the JSON so we can inspect structure
            print(json.dumps(positions_resp, indent=2))
            
        except Exception as e:
            print(f"❌ Error fetching positions: {e}")
            
    else:
        print("\n❌ FAILURE: Client object is None.")