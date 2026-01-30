import time
from playwright.sync_api import sync_playwright
from web_automation.automate_utils import start_otp_listener

def execute_kill_switch(universal_data):
    log = universal_data['sys']['log']
    config = universal_data['sys']['config']
    creds = universal_data['sys']['creds']['kotak']
    web_conf = config.get('web_automation', {})
    browser_conf = web_conf.get('browser', {})
    
    login_url = web_conf.get('login_url', "https://neo.kotaksecurities.com/Login")
    search_timeout = web_conf.get('search_timeout', 20000)
    is_headless = browser_conf.get('headless', False)
    viewport = browser_conf.get('viewport', {'width': 1280, 'height': 720})
    args = browser_conf.get('args', ["--disable-blink-features=AutomationControlled"])
    steps = web_conf.get('flow_steps', [])

    log.info(f"Starting Browser Automation (Headless: {is_headless})", tags=["AUTO", "START"])
    otp_bucket = None 

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=is_headless, args=args)
        context = browser.new_context(viewport=viewport)
        page = context.new_page()
        page.set_default_timeout(search_timeout)

        try:
            log.info(f"Navigating to {login_url}...", tags=["AUTO", "NAV"])
            page.goto(login_url)
            page.wait_for_load_state("networkidle")
            time.sleep(1)

            for step in steps:
                if not step.get('enabled', True): continue
                log.info(f"Step {step.get('id')}: {step.get('description')}", tags=["AUTO", "STEP"])

                try:
                    if step.get('action') == 'input':
                        key = step.get('cred_key')
                        val = creds.get(key, "")
                        
                        if "mobile" in key.lower():
                            if val.startswith("+91"): val = val.replace("+91", "", 1)
                            try: page.get_by_role("textbox", name="Mobile number").click()
                            except: page.locator("input[type='number']").click()
                        
                        elif "password" in key.lower():
                            page.get_by_role("textbox", name="Enter password").click()
                            otp_bucket = start_otp_listener(universal_data)

                        page.keyboard.type(val, delay=50)
                        if step.get('keys'):
                            for k in step['keys']: 
                                page.keyboard.press(k); time.sleep(0.2)

                    elif step.get('action') == 'otp':
                        if not otp_bucket: raise RuntimeError("OTP Listener missing")
                        log.info("Waiting for OTP email...", tags=["AUTO", "WAIT"])
                        start_wait, found = time.time(), False
                        while time.time() - start_wait < 120:
                            if otp_bucket['otp']:
                                found = True; break
                            if otp_bucket['error']:
                                raise RuntimeError(f"OTP Error: {otp_bucket['error']}")
                            time.sleep(1)
                        
                        if found:
                            page.keyboard.type(otp_bucket['otp'], delay=100)
                            page.wait_for_load_state("networkidle")
                        else:
                            raise RuntimeError("OTP Timeout")

                    elif step.get('action') == 'click':
                        coords = step.get('coords')
                        if coords: page.mouse.click(coords['x'], coords['y'])

                    elif step.get('action') == 'scroll':
                        for _ in range(step.get('repeats') or 1):
                            page.mouse.wheel(0, 300); time.sleep(0.2)

                    elif step.get('action') == 'keys':
                        for k in step.get('keys') or []:
                            page.keyboard.press(k); time.sleep(0.3)

                    if step.get('wait'): time.sleep(step['wait'])

                except Exception as step_e:
                    if step.get('optional'): log.warning(f"Step Failed: {step_e}", tags=["AUTO", "SKIP"])
                    else: raise step_e

            log.info("Automation Sequence Completed.", tags=["AUTO", "DONE"])
            time.sleep(2)

        except Exception as e:
            log.critical(f"Automation Critical Failure: {e}", tags=["AUTO", "FAIL"])
            try: page.screenshot(path=f"logs/error_{universal_data['user_id']}.png")
            except: pass
            raise e
        finally:
            browser.close()