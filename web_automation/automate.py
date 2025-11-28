import time
from playwright.sync_api import sync_playwright
from web_automation.automate_utils import start_otp_listener

def execute_kill_switch(universal_data):
    """
    Main Driver: Login -> Navigate -> Kill Switch.
    """
    log = universal_data['sys']['log'].info
    config = universal_data['sys']['config']
    creds = universal_data['sys']['creds']['kotak']
    
    web_conf = config['web_automation']
    steps = web_conf['flow_steps']

    log(">>> STARTING BROWSER AUTOMATION", tags=["AUTO"])

    otp_bucket = None 

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=web_conf['browser']['headless'],
            args=web_conf['browser']['args']
        )
        context = browser.new_context(viewport=web_conf['browser']['viewport'])
        page = context.new_page()

        try:
            # 1. Navigation
            log(f"Navigating to {web_conf['login_url']}...", tags=["AUTO"])
            page.goto(web_conf['login_url'], timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            # 2. Step Execution
            for step in steps:
                s_name = step['step']
                s_type = step['type']
                log(f"Executing: {s_name}", tags=["AUTO"])

                # --- INPUT ---
                if s_type == 'input':
                    val = creds[step['cred_key']]
                    
                    # LOGIC: Handle Mobile Number (+91 strip) & Selectors
                    if "mobile" in step['cred_key'].lower():
                        if val.startswith("+91"):
                            val = val.replace("+91", "", 1)
                        
                        # Robust Mobile Selector
                        try:
                            page.get_by_role("textbox", name="Mobile number").wait_for(timeout=30000)
                        except:
                            page.get_by_placeholder("+91").wait_for(timeout=30000)
                    
                    # LOGIC: Handle Password & OTP Listener Start
                    elif "password" in step['cred_key'].lower():
                        page.get_by_role("textbox", name="Enter password").wait_for(timeout=30000)
                        
                        # Start OTP Listener *Before* Password Enter triggers OTP
                        log("Initializing OTP Listener...", tags=["AUTO"])
                        otp_bucket = start_otp_listener(universal_data)

                    # Type the cleaned value
                    page.keyboard.type(val, delay=100)
                    
                    # Press Keys defined in config (e.g. Enter)
                    if step.get('keys'):
                        for k in step['keys']: 
                            page.keyboard.press(k)
                            time.sleep(0.5)

                # --- OTP ---
                elif s_type == 'otp':
                    if not otp_bucket:
                        raise RuntimeError("OTP Listener not active! Check password step.")
                    
                    log("Waiting for OTP...", tags=["AUTO"])
                    start_wait = time.time()
                    
                    # Wait loop
                    while not otp_bucket['otp'] and not otp_bucket['error']:
                        if time.time() - start_wait > 130: break
                        time.sleep(1)
                    
                    if otp_bucket['otp']:
                        log(f"Typing OTP: {otp_bucket['otp']}", tags=["AUTO"])
                        page.keyboard.type(otp_bucket['otp'], delay=120)
                        page.wait_for_load_state("networkidle")
                    else:
                        raise RuntimeError(f"OTP Failed: {otp_bucket.get('error', 'Timeout')}")

                # --- CLICK (COORDINATES) ---
                elif s_type == 'click':
                    if step.get('coords'):
                        # Flutter-specific click
                        page.locator("flutter-view").click(position=step['coords'])
                    else:
                        log(f"Warning: Step {s_name} has no coords", tags=["AUTO"])

                # --- SCROLL ---
                elif s_type == 'scroll':
                    for _ in range(step.get('repeats', 1)):
                        page.mouse.wheel(0, 200)
                        time.sleep(step.get('step_wait', 0.15))

                # --- KEYS ---
                elif s_type == 'keys':
                    keys = step.get('keys', [])
                    
                    # LOGIC: Kill vs Dry Run Decision
                    # We check for step names like "N_popup_decision" or "popup_cancel"
                    if "popup_decision" in s_name or "popup_cancel" in s_name:
                        mode = config['kill_switch']['execution_mode']
                        is_dry = config['kill_switch']['dry_run']
                        
                        if mode == 'kill_only' and not is_dry:
                            log("!!! EXECUTION MODE: CONFIRMING KILL !!!", tags=["AUTO", "KILL"])
                            # Confirm Sequence (Tab -> Enter)
                            keys = ["Tab", "Enter"]
                        else:
                            log("DRY RUN: Cancelling Popup", tags=["AUTO", "DRY"])
                            # Cancel Sequence (Tab -> Tab -> Enter) - matches JSON default
                            keys = ["Tab", "Tab", "Enter"]

                    for k in keys:
                        page.keyboard.press(k)
                        time.sleep(0.3)

                time.sleep(step.get('wait', 1.0))

            log("Automation Sequence Successful.", tags=["AUTO", "SUCCESS"])
            time.sleep(2) # Final buffer before close

        except Exception as e:
            log(f"Automation Critical Fail: {e}", tags=["AUTO", "CRITICAL"])
            try: page.screenshot(path="logs/crash.png")
            except: pass
            raise e
        finally:
            browser.close()