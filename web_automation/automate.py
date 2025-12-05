import time
from playwright.sync_api import sync_playwright
from web_automation.automate_utils import start_otp_listener


def execute_kill_switch(universal_data):
    
    """ Main Driver: Login -> Navigate -> Kill Switch. """
    
    log_func = universal_data['sys']['log'].info
    warn_func = universal_data['sys']['log'].warning
    
    config = universal_data['sys']['config']
    creds = universal_data['sys']['creds']['kotak']
    
    web_conf = config['web_automation']
    steps = web_conf['flow_steps']    
    search_timeout = web_conf.get('search_timeout', 5000)

    log_func(">>> STARTING BROWSER AUTOMATION", tags=["AUTO"])

    otp_bucket = None 

    with sync_playwright() as p:
        browser_args = web_conf['browser'].get('args', [])
        is_headless = web_conf['browser'].get('headless', False)
        
        browser = p.chromium.launch(headless=is_headless, args=browser_args)
        context = browser.new_context(viewport=web_conf['browser']['viewport'])
        page = context.new_page()

        try:
            log_func(f"Navigating to Login URL...", tags=["AUTO"])
            page.goto(web_conf['login_url'], timeout=60000)
            page.wait_for_load_state("networkidle")
            time.sleep(2)

            for step in steps:
                s_id = step.get('id')
                s_desc = step.get('description', 'Unknown')
                s_action = step.get('action')
                is_enabled = step.get('enabled', True)
                is_optional = step.get('optional', False)
                
                # Pure Config Logic .
                if not is_enabled:
                    log_func(f"Step {s_id}: {s_desc} (SKIPPED by config)", tags=["AUTO", "SKIP"])
                    continue

                log_func(f"Step {s_id}: {s_desc} ({s_action})", tags=["AUTO"])

                try:
                    # --- INPUT ---
                    if s_action == 'input':
                        val = creds[step['cred_key']]
                        
                        if "mobile" in step['cred_key'].lower():
                            if val.startswith("+91"): val = val.replace("+91", "", 1)
                            try: 
                                page.get_by_role("textbox", name="Mobile number").wait_for(timeout=search_timeout)
                            except: 
                                page.get_by_placeholder("+91").wait_for(timeout=search_timeout)
                        
                        elif "password" in step['cred_key'].lower():
                            page.get_by_role("textbox", name="Enter password").wait_for(timeout=search_timeout)
                            log_func("Start OTP Listener...", tags=["AUTO"])
                            otp_bucket = start_otp_listener(universal_data)

                        page.keyboard.type(val, delay=100)
                        
                        if step.get('keys'):
                            for k in step['keys']: 
                                page.keyboard.press(k)
                                time.sleep(0.5)

                    # --- OTP ---
                    elif s_action == 'otp':
                        if not otp_bucket: raise RuntimeError("OTP Listener not active!")
                        log_func("Waiting for OTP...", tags=["AUTO"])
                        
                        start_wait = time.time()
                        while not otp_bucket['otp'] and not otp_bucket['error']:
                            if time.time() - start_wait > 130: break
                            time.sleep(1)
                        
                        if otp_bucket['otp']:
                            log_func(f"OTP: {otp_bucket['otp']}", tags=["AUTO"])
                            page.keyboard.type(otp_bucket['otp'], delay=120)
                            page.wait_for_load_state("networkidle")
                        else:
                            raise RuntimeError(f"OTP Error: {otp_bucket.get('error')}")

                    # --- CLICK ---
                    elif s_action == 'click':
                        coords = step.get('coords')
                        if coords:
                            # Using mouse click at exact coordinates
                            page.mouse.click(coords['x'], coords['y'])
                        else:
                            warn_func(f"Step {s_id}: Missing coordinates for click", tags=["AUTO"])

                    # --- SCROLL ---
                    elif s_action == 'scroll':
                        repeats = step.get('repeats') or 1
                        for _ in range(repeats):
                            page.mouse.wheel(0, 200)
                            time.sleep(0.15)

                    # --- KEYS ---
                    elif s_action == 'keys':
                        keys = step.get('keys') or []
                        for k in keys:
                            page.keyboard.press(k)
                            time.sleep(0.3)

                    # Post-Step Wait
                    wait_time = step.get('wait')
                    if wait_time: time.sleep(wait_time)

                except Exception as step_e:
                    if is_optional:
                        warn_func(f"Step {s_id} skipped (Optional/Failed).", tags=["AUTO"])
                    else:
                        raise step_e

            log_func("Automation Sequence Successful.", tags=["AUTO", "SUCCESS"])
            time.sleep(2)


        except Exception as e:
            log_func(f"Automation Critical Fail: {e}", tags=["AUTO", "CRITICAL"])
            try: 
                user_prefix = universal_data.get('user_id', 'unknown')
                page.screenshot(path=f"logs/crash_{user_prefix}.png")
            except: 
                pass
            raise e
        finally:
            browser.close()