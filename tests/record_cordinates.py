import time
from playwright.sync_api import sync_playwright

LOGIN_URL = "https://neo.kotaksecurities.com/Login"

def record_coords():
    print("\n============================================")
    print("      LIVE COORDINATE RECORDER (Flutter)     ")
    print("============================================")
    print("Viewport = 1366 x 768 (forced)")
    print("YOU will log in manually.")
    print("Once on dashboard, click elements to capture coordinates.")
    print("Press CTRL + C to exit.\n")

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)

        # force consistent pixel layout
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            device_scale_factor=1
        )

        page = context.new_page()
        page.goto(LOGIN_URL)
        print("[*] Login page loaded. Complete login manually...")

        # Inject click listener
        page.evaluate("""
            if (!window.__clickRecorderAdded) {
                document.addEventListener("click", (e) => {
                    console.log(`CLICK:${e.clientX},${e.clientY}`);
                });
                window.__clickRecorderAdded = true;
            }
        """)

        try:
            while True:
                msg = page.wait_for_event("console")
                text = msg.text

                if text.startswith("CLICK:"):
                    coords = text.split(":")[1]
                    x, y = coords.split(",")

                    print(f'page.locator("flutter-view").click(position={{"x": {x}, "y": {y}}})')

        except KeyboardInterrupt:
            print("\nExiting recorder...")
            browser.close()


if __name__ == "__main__":
    record_coords()
