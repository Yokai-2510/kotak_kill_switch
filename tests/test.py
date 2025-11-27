# auto_kill_switch_final.py
# Clean, corrected, fully working version


import time
import imaplib
import email
import re
from threading import Thread
from playwright.sync_api import sync_playwright


# -------------------------
# Credentials
# -------------------------
MOBILE = "9310926729"
PASSWORD = "Fumaken@2510"

GMAIL_USER = "ethanarkham@gmail.com"
GMAIL_APP_PASS = "ncyvowmeeagsdkwe"


# -------------------------
# Hard-coded coords (confirmed)
# -------------------------
COORD_ES_AVATAR = {"x": 1285, "y": 27}
COORD_ACCOUNT_CANVAS = {"x": 499, "y": 224}
COORD_MANAGE_KILLSWITCH = {"x": 480, "y": 225}

# Popup safe center click
COORD_POPUP_CENTER = {"x": 680, "y": 450}

# -------------------------
# Mode: Activate or only Test?
# -------------------------
ACTUALLY_ACTIVATE_KILL_SWITCH = False   # ← set to True only when you want to FIRE


# -------------------------
# OTP Fetcher
# -------------------------
class OTPFetcher:
    def __init__(self, email_user, email_pass, sender_filter="noreply@nmail.kotaksecurities.com", timeout=120):
        self.email_user = email_user
        self.email_pass = email_pass
        self.sender_filter = sender_filter
        self.timeout = timeout
        self.otp = None
        self.error = None

    def start(self):
        t = Thread(target=self._run, daemon=True)
        t.start()
        return t

    def _run(self):
        try:
            mail = imaplib.IMAP4_SSL("imap.gmail.com")
            mail.login(self.email_user, self.email_pass)
            mail.select("inbox")

            typ, data = mail.search(None, f'(FROM "{self.sender_filter}")')
            existing = data[0].split()
            last_uid_before = existing[-1] if existing else b"0"

            print(f"[*] OTP baseline UID: {last_uid_before.decode()}")

            start = time.time()
            while time.time() - start < self.timeout:
                mail.select("inbox")
                typ, data = mail.search(None, f'(FROM "{self.sender_filter}")')
                uids = data[0].split()
                if not uids:
                    time.sleep(2)
                    continue

                latest = uids[-1]
                if latest > last_uid_before:
                    typ, msg_data = mail.fetch(latest, "(RFC822)")
                    msg = email.message_from_bytes(msg_data[0][1])

                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                        else:
                            body = msg.get_payload(0).get_payload(decode=True).decode(errors="ignore")
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    m = re.search(r"\b(\d{4,6})\b", body)
                    if m:
                        self.otp = m.group(1)
                        print(f"[*] OTP found: {self.otp}")
                        mail.logout()
                        return

                time.sleep(2)

            self.error = "Timeout waiting for OTP"
            mail.logout()

        except Exception as e:
            self.error = str(e)


# -------------------------
# Helper
# -------------------------
def safe_wait(t=1):
    time.sleep(t)


# -------------------------
# MAIN SCRIPT
# -------------------------
def main():

    print("\n=== KOTAK NEO AUTO KILL SWITCH (FINAL VERSION) ===\n")

    if ACTUALLY_ACTIVATE_KILL_SWITCH:
        print("⚠️  REAL MODE — KILL SWITCH WILL ACTIVATE")
        input("Press ENTER to continue or Ctrl+C to exit...")
    else:
        print("🟦 TEST MODE — You are SAFE (Cancel will be pressed)\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36")
        )
        page = context.new_page()

        try:
            # ---------------------------------------------------------
            # LOGIN PAGE
            # ---------------------------------------------------------
            print("[A] Opening login page...")
            page.goto("https://neo.kotaksecurities.com/Login", timeout=90000)
            page.wait_for_load_state("networkidle")
            safe_wait(2)

            # Mobile number
            print("[B] Entering mobile...")
            page.get_by_role("textbox", name="Mobile number").wait_for()
            page.keyboard.type(MOBILE, delay=100)
            page.keyboard.press("Enter")
            safe_wait(2)

            # Password
            print("[C] Entering password...")
            page.get_by_role("textbox", name="Enter password").wait_for()
            page.keyboard.type(PASSWORD, delay=100)

            print("[C] Starting OTP listener...")
            otp_fetcher = OTPFetcher(GMAIL_USER, GMAIL_APP_PASS)
            otp_fetcher.start()
            safe_wait(2)

            print("[C] Submitting login (OTP request)...")
            page.keyboard.press("Enter")
            safe_wait(2)

            # Wait for OTP
            print("[C] Waiting for OTP...")
            start = time.time()
            while not otp_fetcher.otp and not otp_fetcher.error and time.time() - start < 130:
                safe_wait(1)

            if otp_fetcher.error:
                raise RuntimeError(otp_fetcher.error)
            if not otp_fetcher.otp:
                raise RuntimeError("OTP not received.")

            print(f"[C] Entering OTP: {otp_fetcher.otp}")
            page.keyboard.type(otp_fetcher.otp, delay=120)
            page.wait_for_load_state("networkidle")
            safe_wait(3)

            # ---------------------------------------------------------
            # CLOSE POPUP
            # ---------------------------------------------------------
            print("[D] Closing possible popup...")
            page.keyboard.press("Tab")
            safe_wait(0.4)
            page.keyboard.press("Tab")
            safe_wait(0.4)
            page.keyboard.press("Enter")
            safe_wait(2)

            # ---------------------------------------------------------
            # OPEN ACCOUNT DETAILS
            # ---------------------------------------------------------
            print("[E] Clicking ES avatar...")
            page.locator("flutter-view").click(position=COORD_ES_AVATAR)
            safe_wait(1)

            print("[E] Selecting Account Details (Tab x3 + Enter)...")
            page.keyboard.press("Tab"); safe_wait(0.4)
            page.keyboard.press("Tab"); safe_wait(0.4)
            page.keyboard.press("Tab"); safe_wait(0.4)
            page.keyboard.press("Enter")
            safe_wait(1.5)

            # ---------------------------------------------------------
            # SCROLL DOWN TO KILL SWITCH
            # ---------------------------------------------------------
            print("[F] Scrolling down to Kill Switch section...")
            page.locator("flutter-view").click(position=COORD_ACCOUNT_CANVAS)
            safe_wait(0.6)

            for _ in range(10):
                page.mouse.wheel(0, 200)
                safe_wait(0.15)

            safe_wait(1)

            # ---------------------------------------------------------
            # CLICK MANAGE (Kill Switch)
            # ---------------------------------------------------------
            print("[G] Clicking Manage (Kill Switch)...")
            page.locator("flutter-view").click(position=COORD_MANAGE_KILLSWITCH)
            safe_wait(1.5)

            # ---------------------------------------------------------
            # CORRECT TAB SEQUENCE (your confirmed mapping)
            # ---------------------------------------------------------
            print("[H] Anchoring Kill-Switch widget focus...")
            page.locator("flutter-view").click(position={"x": 600, "y": 300})
            safe_wait(0.5)

            print("[H] Tab → Back")
            page.keyboard.press("Tab"); safe_wait(0.5)

            print("[H] Tab → Disable all segments")
            page.keyboard.press("Tab"); safe_wait(0.5)

            print("[H] Enter → CHECK 'Disable all segments'")
            page.keyboard.press("Enter")
            safe_wait(0.8)

            print("[H] Tab → NSE Equity")
            page.keyboard.press("Tab"); safe_wait(0.5)

            print("[H] Tab → BSE Equity")
            page.keyboard.press("Tab"); safe_wait(0.5)

            print("[H] Tab → Disable segments button")
            page.keyboard.press("Tab"); safe_wait(0.5)

            print("[H] Enter → Open confirmation popup")
            page.keyboard.press("Enter")
            safe_wait(1.8)
            # -------- Step I: Confirmation Popup --------
            print("[I] Forcing popup focus (flutter)…")

            # 1) Move mouse slightly (forces flutter to detect input device)
            page.mouse.move(680, 440)
            safe_wait(0.05)

            # 2) Click twice to force the popup to receive focus
            page.locator("flutter-view").click(position={"x": 680, "y": 440})
            safe_wait(0.10)
            page.locator("flutter-view").click(position={"x": 680, "y": 440})
            safe_wait(0.25)

            # NOW TAB WILL WORK 100% (inside popup)
            if ACTUALLY_ACTIVATE_KILL_SWITCH:
                print("[I] Activating KILL SWITCH (confirm)…")
                page.keyboard.press("Tab")    # → focus CONFIRM
                safe_wait(0.3)
                page.keyboard.press("Enter")  # → CONFIRM
                safe_wait(1.0)
            else:
                print("[I] TEST MODE — Selecting CANCEL…")
                page.keyboard.press("Tab")    # → Confirm
                safe_wait(0.3)
                page.keyboard.press("Tab")    # → Cancel
                safe_wait(0.3)
                page.keyboard.press("Enter")  # → CANCEL
                safe_wait(1.0)


            safe_wait(1)

            print("\nDone. Browser open for inspection.")
            input("Press ENTER to close...")

        except Exception as e:
            print("\n[ERROR]", e)
            try:
                page.screenshot(path="error.png")
                print("Screenshot saved: error.png")
            except:
                pass
            input("Press ENTER to close browser...")

        finally:
            browser.close()


if __name__ == "__main__":
    main()
