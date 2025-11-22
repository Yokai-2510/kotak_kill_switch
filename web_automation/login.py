import time
from playwright.sync_api import Page, expect
from web_automation.gmail_otp import fetch_latest_otp

def login_to_neo_web(universal_data, page: Page):
    """
    Automates login for Kotak Neo (Flutter Web).
    Flow: Mobile -> Password -> OTP -> Popup handling.
    """
    log = universal_data['logger']
    creds = universal_data['creds']['kotak']
    web_conf = universal_data['config']['web_automation']
    
    log.info("Launching Kotak Neo Web...", tags=["WEB", "LOGIN"])
    page.goto(web_conf['login_url'])
    page.wait_for_load_state('networkidle') # Wait for initial load

    # --- STEP 1: MOBILE NUMBER ---
    try:
        log.info("Entering Mobile Number...", tags=["WEB"])
        # Flutter accessible role
        mobile_box = page.get_by_role("textbox", name="Enter mobile number")
        mobile_box.wait_for(timeout=10000)
        mobile_box.click()
        mobile_box.fill(creds['mobile_number'])
        time.sleep(0.5)
        
        # Submit via Keyboard (Bypasses Flutter button click issues)
        page.keyboard.press("Enter")
    except Exception as e:
        log.error(f"Failed at Mobile Number step: {e}", tags=["WEB", "ERROR"])
        raise

    # --- STEP 2: PASSWORD ---
    try:
        log.info("Entering Password...", tags=["WEB"])
        pass_box = page.get_by_role("textbox", name="Enter password")
        pass_box.wait_for(timeout=10000)
        pass_box.click()
        pass_box.fill(creds['kotak_neo_login_password'])
        time.sleep(0.5)
        
        page.keyboard.press("Enter")
    except Exception as e:
        log.error(f"Failed at Password step: {e}", tags=["WEB", "ERROR"])
        raise

    # --- STEP 3: OTP ---
    try:
        log.info("Waiting for OTP Input...", tags=["WEB"])
        # Wait for the transition to the OTP screen
        # We target the 3rd textbox (index 2) as per your codegen recording
        # Or we wait for a textbox to appear that is empty
        page.wait_for_selector("input[type='text']", timeout=10000)
        
        # Fetch OTP from Gmail (Blocking call)
        otp_code = fetch_latest_otp(universal_data)
        
        log.info(f"Entering OTP: {otp_code}", tags=["WEB"])
        
        # Strategy: Find the OTP box. 
        # Since "textbox" name might change, we try the strategy that worked in your recording:
        # page.get_by_role("textbox").nth(2)
        otp_box = page.get_by_role("textbox").nth(2)
        
        # Fallback: If nth(2) fails, try last available textbox
        if not otp_box.is_visible():
            otp_box = page.get_by_role("textbox").last
            
        otp_box.click()
        otp_box.fill(otp_code)
        time.sleep(0.5)
        
        page.keyboard.press("Enter")
        
    except Exception as e:
        log.error(f"Failed at OTP step: {e}", tags=["WEB", "ERROR"])
        raise

    # --- STEP 4: POPUP HANDLING ---
    # Wait for login to complete or popup to appear
    log.info("Checking for Post-Login Popups...", tags=["WEB"])
    time.sleep(3) # Grace period for page load
    
    try:
        # Common popups: "Skip for now", "Enable notifications", "No thanks"
        # We look for a button with 'Skip' text
        skip_btn = page.get_by_role("button", name="Skip for now")
        if skip_btn.is_visible():
            log.info("Popup detected: Clicking 'Skip for now'", tags=["WEB"])
            skip_btn.click()
            
        # Also check for 'Later' or generic close 'X' if needed
        # (Add more logic here if other popups appear)
        
    except Exception:
        # Non-critical
        pass

    # --- VERIFICATION ---
    try:
        # Wait for URL to change to /Home or /dashboard
        page.wait_for_url("**/Home", timeout=15000)
        log.info("✅ Web Login Successful.", tags=["WEB", "SUCCESS"])
    except Exception:
        log.warning("URL did not change to Home, but proceeding (might be already logged in).", tags=["WEB"])