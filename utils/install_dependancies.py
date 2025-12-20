import subprocess
import sys
import os
import json
from pathlib import Path

# --- CONFIGURATION ---
REQUIRED_PACKAGES = [
    "customtkinter",
    "neo_api_client",
    "playwright",
    "pyotp",
    "packaging",
    "requests",
    "urllib3"
]

SAMPLE_CREDS = {
  "USER_01": {
    "kotak": {
      "consumer_key": "YOUR_CONSUMER_KEY",
      "ucc": "YOUR_UCC",
      "mobile_number": "9999999999",
      "mpin": "123456",
      "totp_secret": "YOUR_TOTP_SECRET",
      "login_password": "YOUR_PASSWORD",
      "environment": "prod"
    },
    "gmail": {
      "email": "your_email@gmail.com",
      "google_app_password": "abcd efgh ijkl mnop",
      "sender_filter": "noreply@nmail.kotaksecurities.com"
    },
    "telegram": {
      "bot_token": "",
      "chat_id": ""
    }
  }
}

def install_package(package):
    """Installs a single package via pip."""
    try:
        print(f"📦 Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installed.")
    except subprocess.CalledProcessError:
        print(f"❌ Failed to install {package}. Check your internet connection.")
        sys.exit(1)

def install_playwright_browsers():
    """Runs the secondary playwright install command."""
    try:
        print("🌍 Installing Playwright Browsers (Chromium)...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Playwright browsers ready.")
    except subprocess.CalledProcessError:
        print("❌ Failed to install Playwright browsers.")

def create_sample_creds():
    """Generates source/credentials.json if missing."""
    root = Path(__file__).parent
    source_dir = root / "source"
    creds_path = source_dir / "credentials.json"

    if not source_dir.exists():
        source_dir.mkdir(parents=True, exist_ok=True)

    if not creds_path.exists():
        print("📄 Creating sample credentials.json...")
        with open(creds_path, "w") as f:
            json.dump(SAMPLE_CREDS, f, indent=2)
        print(f"✅ Created: {creds_path}")
    else:
        print("ℹ️ credentials.json already exists. Skipping generation.")

def main():
    print("=== AUTO INSTALLER STARTED ===\n")
    
    # 1. Upgrade PIP
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    except: pass

    # 2. Install Python Libraries
    for package in REQUIRED_PACKAGES:
        install_package(package)

    # 3. Install Playwright Binaries
    install_playwright_browsers()

    # 4. Generate Files
    create_sample_creds()

    print("\n=== INSTALLATION COMPLETE ===")
    print("You can now run: python main.py")

if __name__ == "__main__":
    main()