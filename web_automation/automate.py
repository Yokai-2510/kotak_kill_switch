import time
from playwright.sync_api import sync_playwright
from web_automation.automate_utils import start_otp_listener

def execute_kill_switch(universal_data):
    """
    Main Driver: Login -> Navigate -> Kill Switch.
    Reads 'flow_steps' from config and executes linearly.
    """
    log = universal_data['sys']['log'].info
    
    # ACCESSING NEW STRUCTURE
    config = universal_data['sys']['config']
    creds = universal_data['sys']['creds']['kotak']
    
    web_conf = config['web_automation']
    steps = web_conf['flow_steps']

    log(">>> STARTING BROWSER AUTOMATION", tags=["AUTO"])

    otp_bucket = None 

    with sync_playwright() as p:
        # 1. Setup Browser
        browser = p.chromium.launch(
            headless=web_conf['browser']['headless'],
            args=web_conf['browser']['args']
        )
        context = browser.new_context(
            viewport=web_conf['browser']['viewport']
        )
        page = context.new_page()

        try:
            # 2. Open Login Page
            page.goto(web_conf['login_url'], timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            # 3. Iterate Config Steps
            for step in steps:
                s_name = step['step']
                s_type = step['type']
                
                log(f"Step: {s_name}", tags=["AUTO"])

                # --- A. INPUT FIELDS ---
                if s_type == 'input':
                    # Fallback Selector Logic
                    try:
                        target = "Mobile number" if "mobile" in s_name else "Enter password"
                        page.get_by_role("textbox", name=target).wait_for(timeout=5000)
                    except:
                        if "mobile" in s_name: 
                            page.get_by_placeholder("+91").wait_for(timeout=5000)

                    # Type Credential
                    val = creds[step['cred_key']]
                    page.keyboard.type(val, delay=100)

                    # Auto-Start OTP Listener on Password Step
                    if "password" in step['cred_key']:
                        log("Starting OTP Listener...", tags=["AUTO"])
                        otp_bucket = start_otp_listener(universal_data)

                    # Press Keys (e.g. Enter)
                    if step['keys']:
                        for k in step['keys']: page.keyboard.press(k)

                # --- B. OTP HANDLING ---
                elif s_type == 'otp':
                    if not otp_bucket: 
                        raise RuntimeError("OTP listener was not started in previous step!")
                    
                    log("Waiting for OTP...", tags=["AUTO"])
                    
                    # Blocking Wait
                    start_wait = time.time()
                    while not otp_bucket['otp'] and not otp_bucket['error']:
                        if time.time() - start_wait > 130: break
                        time.sleep(1)
                    
                    if otp_bucket['otp']:
                        log(f"Entering OTP: {otp_bucket['otp']}", tags=["AUTO"])
                        page.keyboard.type(otp_bucket['otp'], delay=120)
                        page.wait_for_load_state("networkidle")
                    else:
                        raise RuntimeError(f"OTP Failure: {otp_bucket['error']}")

                # --- C. CLICKS (Coordinate Based) ---
                elif s_type == 'click':
                    # Flutter-specific coordinate click
                    page.locator("flutter-view").click(position=step['coords'])

                # --- D. SCROLL ---
                elif s_type == 'scroll':
                    for _ in range(step['repeats']):
                        page.mouse.wheel(0, 200)
                        time.sleep(step.get('step_wait', 0.15))

                # --- E. KEYS & DECISIONS ---
                elif s_type == 'keys':
                    keys = step['keys']
                    
                    # LOGIC: Kill vs Dry Run
                    if "popup_cancel" in s_name:
                        mode = config['kill_switch']['execution_mode']
                        is_dry_run = config['kill_switch']['dry_run']
                        
                        if mode == 'kill_only' and not is_dry_run:
                            log("!!! EXECUTING KILL CONFIRM !!!", tags=["AUTO", "KILL"])
                            # Confirm Sequence: Tab -> Enter
                            keys = ["Tab", "Enter"] 
                        else:
                            log("Executing CANCEL (Dry Run)", tags=["AUTO", "DRY"])
                            # Cancel Sequence: Tab -> Tab -> Enter
                            keys = ["Tab", "Tab", "Enter"] 

                    for k in keys:
                        page.keyboard.press(k)
                        time.sleep(0.3)

                # Post-step wait
                time.sleep(step['wait'])

            log("Automation Sequence Complete.", tags=["AUTO"])

        except Exception as e:
            log(f"Automation Error: {e}", tags=["AUTO", "ERR"])
            try: page.screenshot(path="logs/error.png")
            except: pass
            raise e # Propagate to kill thread
        finally:
            browser.close()