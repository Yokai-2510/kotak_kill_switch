
# 🛡️ Kotak Neo Kill Switch & Risk Manager

**Automated Capital Protection System for Options Traders**

The **Kotak Kill Switch Portal** is a high-performance desktop application designed to enforce trading discipline. It acts as an automated risk manager that monitors your P&L in real-time and executes a multi-stage emergency exit ("Kill Switch") if your predefined loss limits are breached.

---

## 🚀 Key Features

*   **Real-Time Risk Monitoring:** Continuously tracks Mark-to-Market (MTM) losses and Stop-Loss order statuses.
*   **Dual-Trigger Logic:** Configurable logic that triggers only when *Daily MTM Limit is breached* AND *Stop-Loss is hit*, preventing panic exits during temporary volatility.
*   **Hybrid Execution (Soft & Hard Kill):**
    1.  **API Square-Off:** Instantly sends market exit orders for all open positions.
    2.  **Browser Hard Kill:** Simultaneously launches an automated browser to physically click the "Kill Switch" in the Kotak Neo Web Portal.
*   **Multi-Account Support:** Manage and monitor multiple user IDs from a single dashboard.
*   **Smart Verification:** Scans Gmail for official "Kill Switch Activated" confirmation emails to ensure the account is truly disabled.
*   **Telegram Alerts:** Sends instant notifications to your phone regarding risk status, triggers, and lockouts.

---

## 🛠️ Installation & Setup

### Prerequisites
*   **OS:** Windows 10/11 (Recommended), macOS, or Linux.
*   **Python:** Version 3.10 or higher.
*   **Google Chrome:** Installed on the system.

### Method 1: The One-Click Installer (Recommended)
We have provided a script that sets up the environment, installs dependencies, and downloads browser drivers automatically.

1.  Open the project folder in your Terminal / Command Prompt.
2.  Run the installer:
    ```bash
    python install_dependencies.py
    ```
3.  Once finished, launch the app:
    ```bash
    python main.py
    ```

### Method 2: Manual Installation
If you prefer manual setup:
```bash
# 1. Create Virtual Environment
python -m venv .venv
# Windows: .venv\Scripts\activate
# Mac/Linux: source .venv/bin/activate

# 2. Install Packages
pip install customtkinter neo_api_client playwright pyotp packaging requests urllib3

# 3. Install Browser Drivers
playwright install chromium
```

### 📦 compiling to EXE (Optional)
To convert this script into a standalone `.exe` file for easy distribution:
1.  Install PyInstaller: `pip install pyinstaller`
2.  Run the build command:
    ```bash
    pyinstaller --noconsole --onefile --name="KotakKillSwitch" --icon=icon.ico main.py
    ```
*(Note: Ensure you copy the `source/` folder next to the generated `.exe` for it to work).*

---

## ⚙️ Configuration Guide (Credential Setup)

The application requires specific credentials to function. Here is how to get them:

### 1. Kotak Neo API Credentials
*   **Login:** Go to the [Kotak Neo API Dashboard](https://kotaksecurities.com/trade-api).
*   **Create App:** Create a new application (Default Environment).
*   **Copy Details:** Copy the `Consumer Key` and `Consumer Secret`.
*   **Mobile/MPIN:** Use your standard Kotak login details.

### 2. Gmail App Password (For OTP & Verification)
*   **Why?** You cannot use your normal Gmail password for automation.
*   **How:**
    1.  Go to your **Google Account Settings** > **Security**.
    2.  Enable **2-Step Verification**.
    3.  Search for **"App Passwords"**.
    4.  Create a new one named "KillSwitch" and copy the 16-character code. Use this as your `Gmail App Password`.

### 3. Telegram Alerts (Optional)
*   **Get Bot Token:** Open Telegram and search for **@BotFather**. Send `/newbot` and follow instructions to get the `HTTP API Token`.
*   **Get Chat ID:** Search for **@userinfobot** and click Start. It will give you your numeric `ID`.

---

## 🖥️ Usage & Workflow

### 1. Account Setup
*   Navigate to the **Accounts** tab.
*   Enter your Kotak, Gmail, and Telegram credentials.
*   Click **Save Credentials**.

### 2. Risk Configuration
*   Go to **Risk Config**.
*   **MTM Limit:** Set your max daily loss (e.g., `5000`).
*   **Sell Order Exit Confirmed:**
    *   **ON:** Wait for SL Order to fill before killing (Safe Mode).
    *   **OFF:** Kill immediately on MTM breach (Panic Mode).
*   **Auto Square Off:** Enable this to close positions via API before the hard kill.

### 3. Operation
*   Go to the **Dashboard**.
*   Click **START ENGINE** on your account card.
*   **Status:**
    *   🟢 **RUNNING:** Monitoring active.
    *   🟠 **VERIFYING:** Kill triggered, waiting for email confirmation.
    *   🔴 **LOCKED:** Account killed and locked for the day.

### 4. Emergency Controls
*   **Manual Exit:** In the **Live Monitor** tab, click "CLOSE" next to any open position to exit it immediately.
*   **Global Kill Switch:** In the **Dashboard**, the red "Global Kill" button stops ALL active accounts immediately.
*   **Emergency Reset:** If you need to unlock an account manually (e.g., after a test run), go to **Settings** > **Reset Kill Status**.

---

## 📝 Technical Logic Flow

1.  **Monitor:** The `Data Service` polls the API (Adaptive Poll Rate: 1s during market, 60s idle).
2.  **Evaluate:** The `Risk Service` calculates Net MTM.
    *   *Condition:* `Current MTM <= -1 * Limit`.
3.  **Trigger:** If Logic is met -> `signals['trigger_kill'] = True`.
4.  **Execute (Parallel):**
    *   **Thread A:** Calls API `place_order` to exit positions.
    *   **Thread B:** Launches Headless Chrome -> Logs in -> Clicks Kill Switch.
5.  **Verify:** Background worker polls Gmail for "Kill Switch Activated" email.
6.  **Lock:** If email is found, `config.json` is updated with today's date, preventing the engine from restarting until tomorrow.

---

### ⚠️ Disclaimer
*This software is a tool for risk management assistance. It depends on third-party APIs (Kotak, Gmail, Telegram) and internet connectivity. The developer is not responsible for trading losses incurred due to API failures, network issues, or market slippage.*