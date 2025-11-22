# client_login.py - For Kotak Neo API v2.0.0+
from neo_api_client import NeoAPI
import pyotp

def fetch_client(credentials, debug=False):
    try:
        # v2.0.0: Only need consumer_key (the token from NEO app/website)
        client = NeoAPI(
            consumer_key=credentials['consumer_key'],
            environment=credentials.get('environment', 'prod'),
            access_token=None,
            neo_fin_key=None
        )
        
        # Generate TOTP
        totp = pyotp.TOTP(credentials['totp_secret'])
        current_totp = totp.now()
        
        if debug:
            print(f"[DEBUG] Generated TOTP: {current_totp}")
        
        # TOTP login (generates view token and session id)
        login_response = client.totp_login(
            mobile_number=credentials['mobile_number'],
            ucc=credentials['ucc'],
            totp=current_totp
        )
        
        if debug:
            print(f"[DEBUG] totp_login response: {login_response}")
        
        if login_response and 'error' in str(login_response).lower():
            raise Exception(f"TOTP login failed: {login_response}")
        
        # Validate with MPIN (generates trade token)
        validate_response = client.totp_validate(mpin=credentials['mpin'])
        
        if debug:
            print(f"[DEBUG] totp_validate response: {validate_response}")
        
        if validate_response and 'error' in str(validate_response).lower():
            raise Exception(f"TOTP validate failed: {validate_response}")
        
        return client
    except Exception as e:
        raise Exception(f"Authentication failed: {str(e)}")


if __name__ == "__main__":
    credentials = {
        "consumer_key": "ec739c67-b186-42c1-b254-9456edf9f264",  # Token from NEO website
        "ucc": "XARGA",  # Your Unique Client Code
        "mobile_number": "+919310926729",  # With country code
        "mpin": "251802",  # Your 6-digit MPIN
        "totp_secret": "TRC5ARJYNMHYD7WNCJIR4RMOXE",  # For TOTP generation
        "environment": "prod"
    }
    
    try:
        client = fetch_client(credentials, debug=True)
        print("✓ Successfully authenticated!")
        
        # Test positions API
        positions = client.positions()
        print(f"Positions: {positions}")
    except Exception as e:
        print(f"✗ Error: {str(e)}")