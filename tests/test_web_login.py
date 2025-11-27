# tests/auto_kill_switch_flow.py
# Single-file, linear automation (Playwright sync + IMAP OTP)
# Edit creds below if needed.

import time
import imaplib
import email
import re
from threading import Thread
from playwright.sync_api import sync_playwright

# -------------------------
# Credentials (as requested)
# -------------------------
MOBILE = "9310926729"
PASSWORD = "Fumaken@2510"

GMAIL_USER = "ethanarkham@gmail.com"
GMAIL_APP_PASS = "ncyvowmeeagsdkwe"   # app password (IMAP)

# -------------------------
# Hard-coded coords (confirmed)
# -------------------------
COORD_ES_AVATAR = {"x": 1285, "y": 27}    # click ES avatar
COORD_ACCOUNT_CANVAS = {"x": 499, "y": 224}  # click blank canvas to focus content
COORD_MANAGE_KILLSWITCH = {"x": 480, "y": 225}  # Manage -> Kill Switch

# -------------------------
# OTP fetcher (threaded)
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
            # baseline last UID
            typ, data = mail.search(None, f'(FROM "{self.sender_filter}")')
            existing = data[0].split()
            last_uid_before = existing[-1] if existing else b'0'
            print(f"[*] OTP baseline UID: {last_uid_before.decode() if last_uid_before!=b'0' else '0'}")

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
                        # pick first part that's text
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
                    else:
                        print("[!] New email but no OTP found; waiting...")
                time.sleep(2)

            self.error = "Timeout waiting for OTP"
            print("[!] OTP timeout")
            mail.logout()

        except Exception as e:
            self.error = str(e)
            print(f"[!] OTP fetch error: {e}")

# -------------------------
# Helpers: safe wait
# -------------------------
def safe_wait(seconds=1):
    time.sleep(seconds)

# -------------------------
# Main linear procedure
# -------------------------
def main():
    print("\n=== KOTAK NEO - AUTO KILL-SWITCH FLOW (TEST) ===\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False, args=[
            "--disable-blink-features=AutomationControlled",
            "--disable-web-security",
            "--disable-features=IsolateOrigins,site-per-process",
        ])
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36")
        )
        page = context.new_page()

        try:
            # -------- Step A: Open login page --------
            print("[A] Opening login page...")
            page.goto("https://neo.kotaksecurities.com/Login", timeout=90000)
            page.wait_for_load_state("networkidle")
            safe_wait(2)

            # -------- Step B: Fill mobile and continue --------
            print("[B] Typing mobile number...")
            # fallback locators: sometimes exact role label differs; try multiple
            try:
                page.get_by_role("textbox", name="Mobile number").wait_for(timeout=20000)
            except Exception:
                try:
                    page.get_by_placeholder("+91").wait_for(timeout=20000)
                except Exception:
                    pass
            page.keyboard.type(MOBILE, delay=100)
            safe_wait(0.5)
            page.keyboard.press("Enter")
            safe_wait(2)

            # -------- Step C: Password and trigger OTP --------
            print("[C] Typing password...")
            page.get_by_role("textbox", name="Enter password").wait_for(timeout=30000)
            page.keyboard.type(PASSWORD, delay=100)

            print("[C] Starting OTP listener...")
            otp_fetcher = OTPFetcher(GMAIL_USER, GMAIL_APP_PASS, timeout=120)
            otp_fetcher.start()
            safe_wait(2)

            print("[C] Submitting password to request OTP...")
            page.keyboard.press("Enter")  # triggers OTP
            # Wait a short moment for OTP email to be generated
            safe_wait(2)

            # Wait for OTP
            print("[C] Waiting for OTP (up to 120s)...")
            start = time.time()
            while not otp_fetcher.otp and not otp_fetcher.error and time.time() - start < 130:
                safe_wait(1)
            if otp_fetcher.error:
                raise RuntimeError(f"OTP fetcher error: {otp_fetcher.error}")
            if not otp_fetcher.otp:
                raise RuntimeError("OTP not received in time.")

            # Enter OTP (the site advances as digits are typed)
            print(f"[C] Entering OTP: {otp_fetcher.otp}")
            safe_wait(1)
            page.keyboard.type(otp_fetcher.otp, delay=120)

            # Wait for landing/dashboard
            print("[C] Waiting for dashboard to load...")
            page.wait_for_load_state("networkidle", timeout=45000)
            safe_wait(3)

            # -------- Step D: Dismiss notification popup (if present) --------
            print("[D] Trying to dismiss notification popup (Tab, Tab, Enter)...")
            # do a couple of safe tab/enter attempts to close the popup if present
            for _ in range(2):
                page.keyboard.press("Tab")
                safe_wait(0.6)
            page.keyboard.press("Enter")
            safe_wait(2)

            # -------- Step E: Open ES profile (by coordinate) --------
            print("[E] Clicking ES avatar (coordinate)...")
            page.locator("flutter-view").click(position=COORD_ES_AVATAR)
            safe_wait(1.2)

            # Now 3 tabs + Enter selects "Account details" (you observed this)
            print("[E] Pressing Tab x3 + Enter to open Account details (defensive)...")
            page.keyboard.press("Tab"); safe_wait(0.4)
            page.keyboard.press("Tab"); safe_wait(0.4)
            page.keyboard.press("Tab"); safe_wait(0.4)
            page.keyboard.press("Enter"); safe_wait(1.2)

            # -------- Step F: Focus content pane and scroll down (mouse wheel) --------
            print("[F] Clicking account canvas to focus, then scrolling (mouse wheel)...")
            page.locator("flutter-view").click(position=COORD_ACCOUNT_CANVAS)
            safe_wait(0.6)

            # Mouse-wheel scrolling (small steps). Adjust iterations if needed.
            # This uses mouse wheel because keyboard PageDown did not always focus the inner pane.
            for i in range(10):   # 10 steps; tweak count if you need more/less
                page.mouse.wheel(0, 200)   # scroll down
                safe_wait(0.15)

            safe_wait(0.6)

            # -------- Step G: Click Manage (Kill Switch) via coordinate --------
            print(f"[G] Clicking Manage (Kill Switch) at {COORD_MANAGE_KILLSWITCH} ...")
            page.locator("flutter-view").click(position=COORD_MANAGE_KILLSWITCH)
            safe_wait(1.2)

            # Now the Kill Switch widget is visible.
            # According to your mapping:
            # - pressing Tab twice then Enter highlights "Disable segments"
            # - that shows confirmation dialog: tabs in dialog -> first = cross, second = Confirm, third = Cancel
            # We'll use that flow and ultimately choose CANCEL (to avoid any destructive action).
            print("[G] Navigating kill-switch widget using TABs and choosing CANCEL on popup...")

            # Two tabs to highlight "Disable segments" (defensive: press 2-3 tabs)
            page.keyboard.press("Tab"); safe_wait(0.5)
            page.keyboard.press("Tab"); safe_wait(0.6)
            # Enter to open the confirmation
            page.keyboard.press("Enter")
            safe_wait(2.0)

            # Popup appeared; per your notes: Tab x3 then Enter = Cancel
            page.keyboard.press("Tab"); safe_wait(0.45)
            page.keyboard.press("Tab"); safe_wait(0.45)
            page.keyboard.press("Tab"); safe_wait(0.45)
            page.keyboard.press("Enter")
            safe_wait(1.0)

            print("[✓] Kill-switch dialog cancelled (no changes made).")

            # Final: keep the browser open for observation
            print("\nScript finished. Browser remains open for your inspection.")
            input("Press ENTER in terminal to close browser and exit...")

        except Exception as e:
            print(f"[ERROR] {e}")
            print("Screenshot will be captured to ./logs for debugging if possible.")
            try:
                page.screenshot(path="logs/failure_screenshot.png", full_page=True)
                print("Saved logs/failure_screenshot.png")
            except Exception:
                pass
            input("Press ENTER to close browser and exit...")
        finally:
            try:
                browser.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
