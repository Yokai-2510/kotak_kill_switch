You are correct. The README should explicitly show the JSON structure for `credentials.json` so the user (or client) knows exactly how to format the file if they are setting it up manually before launching the GUI.

Here is the **corrected and updated `README.md`**.

I have added a specific section for **"Configuration Files"** that includes the exact JSON structure for `credentials.json` matching your code.

***

# 🛡️ Kotak Kill Switch Portal (v2.0)

**Automated Risk Management & Emergency Exit System**

The **Kill Switch Portal** is a desktop application designed for options traders. It acts as a final line of defense, monitoring your P&L in real-time and automatically disabling trading (via the Broker's Kill Switch) when specific risk criteria are met.

---

## 🚀 Key Features

*   **Real-Time Monitoring:** Tracks MTM (Mark-to-Market) and Stop-Loss orders continuously.
*   **Dual-Trigger Logic:** Activates only when **Daily MTM Limit is breached** AND **Stop-Loss is hit** (configurable).
*   **Hybrid Execution:**
    1.  **Soft Kill:** Attempts to auto-square off all open positions via API.
    2.  **Hard Kill:** Simultaneously launches a browser automation bot to physically click the "Kill Switch" button in the Kotak Neo Web Portal.
*   **Multi-Account Support:** Manage multiple user IDs from a single dashboard.
*   **Dynamic Control:** Connect/Disconnect accounts without restarting the application.
*   **Secure:** Credentials are masked in the GUI and sanitized in logs.

---

## 📋 Prerequisites

Before installing, ensure you have the following:

1.  **Operating System:** Windows 10/11, macOS, or Linux.
2.  **Python:** Version 3.10 or higher.
3.  **Google Chrome:** Installed on your system (required for browser automation).
4.  **Kotak Neo Credentials:** Consumer Key, Secret, Mobile, Password, MPIN.
5.  **Gmail App Password:** Required for reading OTPs and Kill Confirmations.

---

## 🛠️ Installation Guide

### Step 1: Setup Folder
Download and extract the software. Open a terminal inside the folder.

### Step 2: Install Dependencies
```bash
# 1. Create Virtual Environment
python -m venv .venv

# 2. Activate
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 3. Install Libraries
pip install -r requirements.txt

# 4. Install Browser Engine
playwright install chromium
```

---

## ⚙️ Configuration Files (First Run)

The application uses two JSON files in the `source/` folder. You can edit these manually or use the GUI.

### 1. `source/credentials.json`
Create this file if it doesn't exist. It **must** follow this structure:

```json
{
  "USER_01": {
    "kotak": {
      "consumer_key": "YOUR_CONSUMER_KEY",
      "ucc": "YOUR_UCC",
      "mobile_number": "+919999999999",
      "mpin": "123456",
      "totp_secret": "YOUR_TOTP_SECRET",
      "login_password": "YOUR_PASSWORD",
      "environment": "prod"
    },
    "gmail": {
      "email": "your_email@gmail.com",
      "google_app_password": "abcd efgh ijkl mnop",
      "sender_filter": "noreply@nmail.kotaksecurities.com"
    }
  }
}
```

### 2. `source/config.json`
This file stores your risk limits and automation settings. The app will generate defaults, but ensure your **MTM Limit** is set correctly.

---

## 🖥️ Usage Guide

### 1. Launch the Application
```bash
python main.py
```

### 2. Connect Account
1.  Go to the **Accounts** tab.
2.  Verify your credentials are loaded.
3.  Toggle **"System Active"** to **ON**.
    *   **Green:** Connected successfully.
    *   **Red:** Authentication failed (Check credentials).

### 3. Set Risk Rules
Go to **Risk Config**:
*   **MTM Limit:** Enter your max loss (e.g., `5000`).
*   **Sell Order Exit Confirmed:**
    *   **ON:** Waits for a Stop-Loss order to fill before killing (Safe Mode).
    *   **OFF:** Kills immediately on MTM breach (Panic Mode).
*   **Auto Square Off:** Tries to close positions via API before the hard kill.

### 4. Monitoring Status
*   **Dashboard:** Shows P&L and Risk Utilization.
*   **Status Tab:**
    *   **WATCHDOG:** Should be "HEALTHY".
    *   **LAST TRIGGER:** Shows the timestamp of the last Kill event.
    *   **LOCK STATUS:** If "YES", the account is locked for the day.

---

## ⚠️ Kill Switch Logic & Safety

1.  **Verification:**
    After the browser automation runs, the system scans your Gmail for a confirmation email from Kotak.
    *   **Email Found:** Status becomes **KILLED (VERIFIED)**. Account is locked until tomorrow.
    *   **No Email:** Status becomes **KILLED (UNCONFIRMED)**. Likely a test run or network issue.

2.  **Emergency Reset:**
    If you triggered a test or need to unlock the account manually:
    *   Go to **Settings**.
    *   Click **RESET KILL STATUS**.
    *   This re-enables the "System Active" toggle.

3.  **Browser Mode:**
    *   By default, the browser runs in **Headless Mode** (invisible).
    *   To see the browser open and click buttons, go to **Settings** and turn **Headless Mode OFF**.

---

## 📄 requirements.txt

```text
customtkinter
neo_api_client
playwright
pyotp
packaging
requests
urllib3
```
