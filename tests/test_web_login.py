# test_login.py
from utils.initialize import initialize_system
from playwright.sync_api import sync_playwright
from web_automation.login import login_to_neo_web

app = initialize_system()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False) # Headless=False to watch
    page = browser.new_page()
    login_to_neo_web(app, page)
    print("Test Finished. check logs.")
    input("Press Enter to close...")
    browser.close()