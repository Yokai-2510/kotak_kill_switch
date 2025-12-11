import time
from playwright.sync_api import sync_playwright
from web_automation.automate_utils import start_otp_listener

def execute_kill_switch(universal_data):
    """ 
    Main Driver: Login -> Navigate -> Kill Switch. 
    Reads browser settings dynamically from config.json.
    """
    log = universal_data['sys']['log']
    
    # 1. Load Config
    config = universal_data['sys']['config']
    creds = universal_data['sys']['creds']['kotak']
    
    web_conf = config.get('web_automation', {})
    browser_conf = web_conf.get('browser', {})
    
    # 2. Parse Browser Settings
    login_url = web_conf.get('login_url', "https://neo.kotaksecurities.com/Login")
    search_timeout = web_conf.get('search_timeout', 20000) # Default 20s
    
    is_headless = browser_conf.get('headless', False)
    viewport = browser_conf.get('viewport', {'width': 1280, 'height': 720})
    args = browser_conf.get('args', ["--disable-blink-features=AutomationControlled"])

    steps = web_conf.get('flow_steps', [])

    log.info(f"Starting Browser Automation (Headless: {is_headless})", tags=["AUTO", "START"])

    otp_bucket = None 

    with sync_playwright() as p:
        # Launch Browser
        browser = p.chromium.launch(headless=is_headless, args=args)
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        
        # Set default timeout for all actions
        page.set_default_timeout(search_timeout)

        try:
            log.info(f"Navigating to {login_url}...", tags=["AUTO", "NAV"])
            page.goto(login_url)
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            for step in steps:
                s_id = step.get('id')
                s_desc = step.get('description', 'Action')
                s_action = step.get('action')
                is_enabled = step.get('enabled', True)
                is_optional = step.get('optional', False)
                wait_time = step.get('wait', 0.5)

                if not is_enabled:
                    continue

                log.info(f"Step {s_id}: {s_desc}", tags=["AUTO", "STEP"])

                try:
                    # --- INPUT ---
                    if s_action == 'input':
                        key = step.get('cred_key')
                        val = creds.get(key, "")
                        
                        # Mobile Number Formatting
                        if "mobile" in key.lower():
                            if val.startswith("+91"): val = val.replace("+91", "", 1)
                            # FIX: Use search_timeout instead of hardcoded 2000ms
                            try: 
                                page.get_by_role("textbox", name="Mobile number").click(timeout=search_timeout)
                            except: 
                                # Try alternative selectors if role fails
                                try: page.get_by_placeholder("Enter mobile number").click(timeout=search_timeout)
                                except: page.locator("input[type='number']").click(timeout=search_timeout)
                        
                        # Password Logic
                        elif "password" in key.lower():
                            page.get_by_role("textbox", name="Enter password").click()
                            # Start OTP listener early if next step needs it
                            log.info("Starting OTP Listener in background...", tags=["AUTO"])
                            otp_bucket = start_otp_listener(universal_data)

                        page.keyboard.type(val, delay=50)
                        
                        # Press Enter keys if defined
                        if step.get('keys'):
                            for k in step['keys']: 
                                page.keyboard.press(k)
                                time.sleep(0.2)

                    # --- OTP ---
                    elif s_action == 'otp':
                        if not otp_bucket: 
                            raise RuntimeError("OTP Listener was not started in previous steps!")
                        
                        log.info("Waiting for OTP from Email...", tags=["AUTO", "WAIT"])
                        
                        # Poll for OTP
                        start_wait = time.time()
                        found = False
                        while time.time() - start_wait < 120: # 2 min max
                            if otp_bucket['otp']:
                                found = True
                                break
                            if otp_bucket['error']:
                                raise RuntimeError(f"OTP Listener Error: {otp_bucket['error']}")
                            time.sleep(1)
                        
                        if found:
                            log.info(f"Applying OTP: {otp_bucket['otp']}", tags=["AUTO"])
                            page.keyboard.type(otp_bucket['otp'], delay=100)
                            page.wait_for_load_state("networkidle")
                        else:
                            raise RuntimeError("OTP Timeout - Email not received")

                    # --- CLICK (COORDINATES) ---
                    elif s_action == 'click':
                        coords = step.get('coords')
                        if coords:
                            page.mouse.click(coords['x'], coords['y'])
                        else:
                            log.warning(f"Step {s_id}: Missing coordinates", tags=["AUTO"])

                    # --- SCROLL ---
                    elif s_action == 'scroll':
                        repeats = step.get('repeats') or 1
                        for _ in range(repeats):
                            page.mouse.wheel(0, 300)
                            time.sleep(0.2)

                    # --- KEYS ---
                    elif s_action == 'keys':
                        keys = step.get('keys') or []
                        for k in keys:
                            page.keyboard.press(k)
                            time.sleep(0.3)

                    # Post-Step Wait
                    if wait_time: time.sleep(wait_time)

                except Exception as step_e:
                    if is_optional:
                        log.warning(f"Optional Step {s_id} Failed: {step_e}", tags=["AUTO", "SKIP"])
                    else:
                        raise step_e

            log.info("Automation Sequence Completed.", tags=["AUTO", "DONE"])
            time.sleep(2)

        except Exception as e:
            log.critical(f"Automation Critical Failure: {e}", tags=["AUTO", "FAIL"])
            # Save screenshot for debugging
            try: 
                user = universal_data.get('user_id', 'unknown')
                page.screenshot(path=f"logs/error_{user}.png")
            except: pass
            raise e
        finally:
            browser.close()