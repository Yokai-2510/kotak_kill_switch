Here is a professional, client-ready **README.md**. It covers installation, configuration, usage, and safety protocols.

I have also included the content for `requirements.txt` at the bottom, as you will need that file for the installation step.

***

# 🛡️ Kotak Kill Switch Portal (v2.0)

**Automated Risk Management & Emergency Exit System**

The **Kotak Kill Switch Portal** is a desktop application designed for options traders. It acts as a final line of defense, monitoring your P&L in real-time and automatically disabling trading (via the Broker's Kill Switch) when specific risk criteria are met.

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
2.  **Python:** Version 3.10 or higher. [Download Here](https://www.python.org/downloads/).
3.  **Google Chrome:** Installed on your system (required for browser automation).
4.  **Kotak Neo Credentials:**
    *   User ID / Password / MPIN.
    *   **Consumer Key & Secret** (From Kotak API Dashboard).
    *   **TOTP Secret** (From an authenticator app setup).

---

## 🛠️ Installation Guide

Follow these steps to set up the application on your machine.

### 1. Extract the Application
Download and extract the provided `.zip` folder to your desired location (e.g., Desktop).

### 2. Open Terminal
*   **Windows:** Open the folder, type `cmd` in the address bar, and hit Enter.
*   **Mac/Linux:** Open Terminal and `cd` into the folder directory.

### 3. Create a Virtual Environment (Recommended)
This keeps the application dependencies isolated.
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Mac/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies
Run the following command to install required libraries:
```bash
pip install -r requirements.txt
```

### 5. Install Browser Drivers
This downloads the necessary browser binaries for the automation bot.
```bash
playwright install chromium
```

---

## 🖥️ Usage Guide

### 1. Launch the Application
Run the main script:
```bash
python main.py
```
*The application window will open after a brief initialization.*

### 2. Configure Accounts (First Time Setup)
1.  Navigate to the **Accounts** tab in the sidebar.
2.  Select the user tab (e.g., `USER_01`) at the top.
3.  **Enter Credentials:**
    *   **Alias:** Give the account a friendly name (e.g., "Main Portfolio").
    *   **Kotak Neo Credentials:** Fill in Mobile, UCC, Consumer Key, Password, MPIN, and TOTP Secret.
    *   **Gmail Configuration:** Enter your email and App Password (required for fetching OTPs during the Kill Switch process).
4.  Click **SAVE CREDENTIALS**.

### 3. Connect the System
1.  In the **Accounts** tab, toggle the **"System Active"** switch to **ON**.
2.  The system will attempt to log in.
    *   **Green (System Running):** Login successful. Monitoring started.
    *   **Red (Auth Failed):** Check your credentials and try again.

### 4. Set Risk Parameters
Navigate to the **Risk Config** tab:
1.  **Daily MTM Loss Limit:** Enter the maximum loss amount (e.g., `5000`). *Note: Enter as a positive number. The system treats it as a loss limit.*
2.  **Kill Switch Enabled:** Master toggle to arm the system.
3.  **Sell Order Exit Confirmed:**
    *   **ON:** Kill Switch triggers ONLY if MTM limit is breached **AND** a Stop-Loss order on a sold position has been executed.
    *   **OFF:** Kill Switch triggers immediately upon MTM breach (Panic Mode).
4.  **Auto Square Off:** If ON, the system attempts to close open positions via API before killing the account.
5.  Click **SAVE CHANGES**.

### 5. Monitoring
*   **Dashboard:** View global P&L and risk utilization across all accounts.
*   **Live Monitor:** View detailed open positions and order book status.
*   **Status:** View heartbeat health, API connection status, and service threads.
*   **System Logs:** View real-time logs for debugging.

---

## ⚠️ Understanding the Kill Logic

The system runs a background loop every few seconds. Here is the exact logic it follows:

1.  **Check MTM:** Is `Current MTM <= -1 * Limit`? (e.g., Loss is 6000, Limit is 5000).
2.  **Check SL Status:** Has any `BUY` order with type `SL` or `SL-M` been `COMPLETE` or `PARTIALLY_FILLED`?
3.  **Trigger Decision:**
    *   If **Sell Order Exit Confirmed** is ON: Both #1 AND #2 must be true.
    *   If **Sell Order Exit Confirmed** is OFF: Only #1 needs to be true.

**When Triggered:**
1.  **API Action:** Sends Market Exit orders for all open positions.
2.  **Browser Action:** Opens a hidden Chrome window -> Logs into Kotak Neo -> Navigates to Settings -> Clicks "Kill Switch" -> Confirms.
3.  **Shutdown:** The application stops monitoring for that account to prevent interference.

---

## ❓ Troubleshooting

**Q: The application crashes immediately on open.**
A: Ensure `config.json` and `credentials.json` exist in the `source` folder and contain valid JSON structure.

**Q: "System Active" turns on, then immediately off.**
A: Check the **System Logs** tab. It usually means Authentication failed. Verify your Password, MPIN, or Consumer Key.

**Q: Browser automation fails/times out.**
A: Ensure you have run `playwright install chromium`. Also, check if your internet connection is stable.

**Q: I don't see my logs.**
A: Logs are stored in the `logs/` folder. In the GUI, ensure you have selected the correct category/account filter.

---
