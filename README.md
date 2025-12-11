Here is a comprehensive, user-centric **README.md**. It is written specifically for the **End User (Trader)**, focusing on safety, logic flow, and ease of use.

I have also included the `requirements.txt` content at the bottom, as it is necessary for the installation step.

***

# 🛡️ Kotak Neo Kill Switch Portal (v2.0)

**Automated Risk Management & Emergency Exit System**

The **Kill Switch Portal** is a desktop application designed for serious options traders using Kotak Neo. It acts as an automated "Risk Manager" that sits silently in the background, monitoring your P&L. If your losses exceed your predefined limit, it automatically intervenes to **Square Off positions** and **Disable Trading** on your account to prevent further damage.

---

## 🧠 How It Works (The Logic)

The system operates on a **"Dual-Trigger & Hybrid Execution"** model to ensure safety without accidental firings.

### 1. The Trigger Logic
The Kill Switch activates **ONLY** when specific conditions are met simultaneously:
1.  **MTM Breach:** Your Realized + Unrealized Loss exceeds your limit (e.g., Loss > ₹10,000).
2.  **Stop-Loss Confirmation (Optional):** You can configure it to trigger *only* if a Stop-Loss order on a specific Sold position has actually been executed. This prevents panic exits during temporary MTM spikes.

### 2. The Execution Sequence (When Triggered)
Once triggered, the system performs a parallel "Hard" and "Soft" kill:
*   **Step A (API Square Off):** Immediately sends Market Exit orders for all open positions via the API.
*   **Step B (Browser Automation):** Simultaneously opens a hidden Chrome window, logs into the Kotak Neo website, navigates to settings, and physically clicks the **"Kill Switch"** button.
*   **Step C (Verification):** It scans your Gmail for the official "Kill Switch Activated" email from Kotak to confirm the action was successful.
*   **Step D (Daily Lockout):** Once verified, the application **LOCKS** your profile for the rest of the day. You cannot restart the session or place new trades through the app, preventing "Revenge Trading."

---

## 📦 Installation Guide

### Prerequisites
*   **Windows 10/11** (Preferred) or macOS/Linux.
*   **Google Chrome** installed.
*   **Python 3.10+** installed.

### Step 1: Setup
1.  Download and unzip the software folder.
2.  Open the folder.
3.  Right-click inside the folder and select **"Open Terminal"** (or CMD).

### Step 2: Install Dependencies
Run the following commands one by one in the terminal:

```bash
# 1. Create a virtual environment (Recommended)
python -m venv .venv

# 2. Activate the environment
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate

# 3. Install required libraries
pip install -r requirements.txt

# 4. Install browser drivers for automation
playwright install chromium
```

### Step 3: Launch
To start the application:
```bash
python main.py
```

---

## 🖥️ Interface Walkthrough

### 1. Accounts (The Control Center)
This is where you manage connections.
*   **Input Credentials:** Enter your Mobile, Password, MPIN, and API Keys.
*   **Gmail Config:** Enter your email and App Password (needed to read OTPs and Kill Confirmations).
*   **System Active Switch:**
    *   **Toggle ON:** Connects to Kotak, starts monitoring P&L, and arms the Kill Switch.
    *   **Toggle OFF:** Disconnects and stops monitoring.
    *   **Status:** Displays "RUNNING", "STOPPED", or "LOCKED" (if you hit your loss limit today).

### 2. Risk Config (The Rules)
Define when the system should pull the plug.
*   **MTM Limit:** The maximum loss you are willing to take (e.g., `5000`). Enter as a positive number.
*   **Kill Switch Enabled:** Master toggle. If OFF, the system monitors but will **NOT** take action.
*   **Sell Order Exit Confirmed:**
    *   **ON:** Safe Mode. Waits for a Stop-Loss order to be filled before killing.
    *   **OFF:** Panic Mode. Kills immediately when MTM limit is touched, regardless of open orders.
*   **Auto Square Off:** If ON, tries to close positions via API before blocking the account.

### 3. Dashboard (The Overview)
A high-level view of your trading health.
*   **Net System P&L:** Total P&L across all active accounts.
*   **Global Kill Switch:** A big red button to manually trigger the Kill sequence on ALL active accounts immediately.
*   **Account Cards:** Shows individual status, MTM, and whether an account is "Safe", "Killing", or "Locked".

### 4. Live Monitor
Shows raw data directly from the broker.
*   **Open Positions:** Real-time P&L per position.
*   **Order Book:** Status of your pending and executed orders.

### 5. Status & Logs
*   **Status:** Technical telemetry. Check here to see if the "Watchdog" is running or if the system detected a kill.
*   **System Logs:** A detailed text log of everything the bot is doing (e.g., "Scanning for Price", "Heartbeat OK", "Error Logging In").

---

## ⚠️ Important Safety Notes

1.  **Daily Lockout:**
    If the Kill Switch triggers and is verified via email, the app will enter **"LOCKED (VIEW ONLY)"** mode. You cannot use the app to trade again until the next day.
    *   *Emergency:* If this was a mistake, go to **Settings > Emergency Reset** to unlock manually.

2.  **Gmail Integration:**
    For the verification to work, you must use an **App Password** for Gmail (not your normal login password). This ensures the bot can check for the "Kill Switch Activated" email.

3.  **Headless Mode:**
    In **Settings**, you can enable "Headless Mode".
    *   **ON:** The browser automation runs invisibly in the background.
    *   **OFF:** You will see the Chrome window open and click the buttons automatically (Recommended for first-time testing).

---

## 📄 requirements.txt

Save the following text into a file named `requirements.txt` in the main folder:

```text
customtkinter
neo_api_client
playwright
pyotp
packaging
requests
urllib3
```