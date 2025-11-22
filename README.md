Here is a complete, professional **README.md** formatted for GitHub. It covers installation, configuration, architecture, and safety disclaimers.

You can save this directly as `README.md` in your project root.

***

# 🛡️ Kotak Neo Automated Kill Switch

A robust, Python-based risk management system for **Kotak Securities (Neo)**. This tool monitors your trading portfolio in real-time and automatically **disables trading** (Kill Switch) when specific risk criteria are met.

Unlike standard API wrappers, this system uses a **Hybrid Architecture**:
1.  **API Layer:** Fetches real-time Positions, Orders, and Quotes (LTP) for microsecond-latency monitoring.
2.  **Web Automation Layer (Playwright):** Logs into the Kotak Neo Web Portal to execute the "Kill Switch" (which is not available via the public API).

---

## 🚀 Key Features

*   **Double-Trigger Logic:** Activates Kill Switch only when:
    *   Daily MTM Loss exceeds your defined limit (e.g., ₹10,000).
    *   **AND** A Stop-Loss (SL) order on a Sold Position has been hit (configurable).
*   **Automated Login System:**
    *   Handles Kotak Neo 2FA (Mobile + Password).
    *   **Auto-fetches OTP** from your Gmail using Google API.
    *   Bypasses Flutter Web limitations using keyboard emulation.
*   **Daemon Mode:** Runs continuously during market hours.
*   **Detailed Logging:** Tagged logging system (console + file) for audit trails.
*   **Dry Run Support:** Test the logic without actually locking your account.

---

## 📂 Project Structure

```text
kotak_kill_switch/
├── main.py                    # Entry point (Orchestrator)
├── requirements.txt           # Python dependencies
├── logs/                      # Application logs
├── source/
│   ├── config.json            # Risk limits & System settings
│   ├── credentials.json       # API Keys & Login Secrets
│   ├── gmail_credentials.json # Google OAuth Client Secret
│   └── gmail_token.json       # Auto-generated Gmail Token
├── kotak_api/                 # Phase 1 & 2: Data Fetching (NeoAPI)
├── trigger_logic/             # Phase 3: MTM & SL Calculations
├── services/                  # Threaded Services (Data, Risk, Kill)
├── web_automation/            # Phase 4: Playwright & Gmail Logic
└── utils/                     # Logger & Initialization
```

---

## 🛠️ Installation & Setup

### 1. Prerequisites
*   Python 3.10+
*   Google Cloud Project (for Gmail API)
*   Kotak Neo Account (API Credentials)

### 2. Install Dependencies
```bash
git clone https://github.com/yourusername/kotak-kill-switch.git
cd kotak-kill-switch

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install libraries
pip install -r requirements.txt

# Install Playwright Browsers
playwright install chromium
```

### 3. Google Gmail API Setup
1.  Go to [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a project -> Enable **Gmail API**.
3.  Go to **Credentials** -> Create **OAuth 2.0 Client ID** (Desktop App).
4.  Download the JSON file, rename it to `gmail_credentials.json`, and place it in the `source/` folder.

---

## ⚙️ Configuration

### 1. Credentials (`source/credentials.json`)
Create this file to store sensitive data.

```json
{
  "kotak": {
    "consumer_key": "YOUR_NEO_CONSUMER_KEY",
    "mobile_number": "9999999999",
    "mpin": "123456",
    "totp_secret": "YOUR_TOTP_SECRET_BASE32",
    "environment": "prod",
    "ucc": "YOUR_CLIENT_CODE",
    "kotak_neo_login_password": "YourWebPassword"
  },
  "gmail": {
    "email": "your_email@gmail.com",
    "credentials_file": "source/gmail_credentials.json",
    "token_file": "source/gmail_token.json",
    "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
    "otp_sender": "noreply@kotaksecurities.com",
    "otp_subject_contains": "OTP"
  }
}
```

### 2. Settings (`source/config.json`)
Configure your risk limits.

```json
{
  "kill_switch": {
    "enabled": true,
    "dry_run": false,               
    "mtm_limit": 10000,             
    "trigger_on_sl_hit": true,      
    "execution_mode": "kill_only"   
  },
  "monitoring": {
    "poll_interval_seconds": 2
  },
  "web_automation": {
    "headless": false,
    "login_url": "https://neo.kotaksecurities.com/Login"
  }
}
```
*   `dry_run`: If `true`, logic triggers but browser won't click the final button.
*   `execution_mode`: currently supports `kill_only` (locks account).
*   `mtm_limit`: The loss amount (absolute value) that triggers the system.

---

## ▶️ Usage

### First Run (Authorization)
On the very first run, a browser window will open asking you to authorize the Gmail API access. This generates the `gmail_token.json`.

```bash
python main.py
```

### Modes
**1. Daemon Mode (Default):**
Runs continuously, polling data and monitoring risk.
```bash
python main.py
```

**2. Single Run Mode:**
Runs one check cycle and exits (useful for debugging logic).
```bash
python main.py --mode single_run
```

---

## 🧠 Architecture Flow

1.  **Init:** Loads config, sets up logger, authenticates API.
2.  **Threads Start:**
    *   `DataThread`: Polls Positions, Orders, and Quotes every 2 seconds.
    *   `RiskThread`: Calculates Realized + Unrealized PnL. Checks if SL orders on sold legs are `COMPLETE`.
    *   `KillSwitchThread`: Waits for the `trigger_signal`.
3.  **Trigger Event:**
    *   If `MTM <= -10000` **AND** `SL_Hit == True`:
    *   `RiskThread` sets `trigger_signal = True`.
4.  **Execution:**
    *   `KillSwitchThread` wakes up.
    *   Launches Chromium via Playwright.
    *   Logs in -> Reads OTP from Gmail -> Enters OTP.
    *   Navigates to Settings -> Clicks "Kill Switch".
    *   Shuts down the system.

---

## ⚠️ Disclaimer

**USE AT YOUR OWN RISK.**

This software is for educational purposes only. Automated trading systems can fail due to internet issues, API downtime, or software bugs.
*   Always monitor the system while it is running.
*   The authors are **not responsible** for any financial losses incurred while using this software.
*   Test thoroughly in `dry_run` mode before using real capital.

---

## 📜 License

MIT License. See `LICENSE` file for details.
