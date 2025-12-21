# **Kotak Kill Switch - User Guide**

## **1. Overview**

The Kotak Kill Switch is an automated risk management application for traders using the Kotak Neo platform. Its sole purpose is to act as a final safety brake to prevent overtrading and catastrophic losses.

It operates on a strict **dual-condition trigger**:
1.  A **stop-loss order** on a primary sold option position is executed.
2.  Your **total daily Mark-to-Market (MTM)** loss exceeds your configured limit.

When both conditions are met, the system automatically activates the kill switch in the Kotak Neo web terminal, squares off optional hedge positions, and logs you out, effectively ending your trading day.

---

## **2. Initial Setup**

Follow these steps to get the application running for the first time.

#### **Step 1: Prerequisites**
Ensure you have Python (version 3.10+) and Git installed on your system.

#### **Step 2: Get the Code**
Open a terminal or command prompt and clone the project repository:
```bash
git clone <repository_url>
cd kotak_kill_switch
```

#### **Step 3: Set Up a Virtual Environment**
This isolates the project's dependencies.
```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```

#### **Step 4: Install Dependencies**
Install all required Python packages.
```bash
pip install -r requirements.txt
```

#### **Step 5: Install Browser for Automation**
The application uses Playwright for browser automation. Install its necessary components:
```bash
playwright install
```

---

## **3. Configuration**

Configuration is managed in the `source/` directory. You must create two files for each user account you want to manage.

#### **A. Credentials File (`source/USER_01_credentials.json`)**
This file stores your secret API credentials. **Never share this file.**
```json
{
  "consumer_key": "YOUR_API_KEY_FROM_KOTAK",
  "consumer_secret": "YOUR_API_SECRET_FROM_KOTAK",
  "mobile_number": "YOUR_REGISTERED_MOBILE_NUMBER",
  "password": "YOUR_KOTAK_TRADING_PASSWORD",
  "otp": "YOUR_MPIN_OR_STATIC_OTP"
}
```

#### **B. Configuration File (`source/USER_01_config.json`)**
This file controls the behavior of the application for that user.

```json
{
  "runtime_settings": {
    "delete_logs_on_boot": true,
    "log_directory": "logs"
  },
  "api_retry_settings": {
    "max_retries": 3,
    "delay_seconds": 5
  },
  "risk_params": {
    "mtm_limit": -10000.0,
    "check_interval_seconds": 5,
    "auto_square_off_hedges": false
  },
  "automation_steps": [
    { "action": "input", "target": "#mobile_number", "value": "credentials" },
    { "action": "click", "target": "text=Enter" },
    { "action": "input", "target": "#login_password", "value": "credentials" },
    { "action": "keys", "target": "Tab,Tab,Enter" },
    { "action": "click", "target": "text=Kill Switch" }
  ],
  "telegram_settings": {
    "bot_token": "YOUR_TELEGRAM_BOT_TOKEN",
    "chat_id": "YOUR_TELEGRAM_CHAT_ID"
  }
}
```
- **`mtm_limit`**: The core setting. Enter your max daily loss as a negative number (e.g., `-10000`).
- **`check_interval_seconds`**: How often the system checks your MTM and orders.
- **`automation_steps`**: The sequence of browser actions to execute the kill switch. **You can edit this if the Kotak website changes.**

---

## **4. Running the Application**

From the project's root directory (`kotak_kill_switch/`), with your virtual environment activated, run:
```bash
python main.py
```
The GUI application will launch.

---

## **5. GUI Guide**

The application is controlled through a simple, multi-tab interface.

#### **A. Dashboard**
This is your main overview.
- **Global Kill Switch:** A large button to manually trigger the kill switch for ALL active engines simultaneously.
- **Engine Cards:** One card is displayed for each user you have configured.
    - **Status:** Shows if the engine is `IDLE`, `RUNNING`, `LOCKED`, or has `FAILED`.
    - **MTM / Limit:** Shows your current Mark-to-Market PnL versus your configured limit.
    - **Risk Utilization:** A progress bar that fills up as you approach your MTM limit.
    - **SL Status:** `SAFE` or `HIT TODAY`. Changes to `HIT TODAY` as soon as the system detects a stop-loss on a sold leg has been executed.
    - **Start/Stop Switch:** The main control to activate or deactivate monitoring for that specific engine.

#### **B. Risk Config**
- Select a user from the dropdown.
- Set the **Daily MTM Limit** and other risk parameters.
- Click **"Save Config"** to apply changes instantly, without a restart.

#### **C. Automation**
- View and edit the sequence of browser automation steps. This allows you to adapt to changes in the Kotak Neo website layout without needing to modify the code.

#### **D. Live Monitor**
- Displays a real-time grid of your open positions and working orders fetched from the broker.
- **Exit Position Button:** A button next to each open position allows you to send an immediate market order to square it off.

#### **E. System Logs**
- A live, scrolling view of the application's log file. You can see authentications, MTM calculations, and any errors in real-time.

---

## **6. Key Workflows**

#### **Normal Daily Operation**
1.  Run `python main.py`.
2.  Navigate to the **Dashboard**.
3.  For the account(s) you wish to monitor, toggle the switch from **"Inactive"** to **"Active"**.
4.  The engine for that user will authenticate and begin monitoring in the background. You can now minimize the application.

#### **Automatic Kill Sequence**
1.  You are trading, and a stop-loss on one of your sold options is hit. The **SL Status** on the dashboard will change to **`HIT TODAY`**. The system is now armed.
2.  Later, your daily MTM drops and becomes less than or equal to your MTM limit (e.g., ≤ -10,000).
3.  The **Risk Service** detects that both conditions are now true.
4.  The **Kill Switch Service** takes over. The engine status changes to **`KILLED (EXECUTING)`**.
5.  A browser window (or a background process if in headless mode) will open, log in, navigate, and click the kill switch button.
6.  A Telegram alert is sent confirming the action.
7.  The engine status changes to **`LOCKED`**. It cannot be restarted for the rest of the day.

#### **Manual Reset**
If a kill switch was triggered (or you want to reset the state for the next day), you can perform a manual reset.
1.  Go to the **Settings** tab.
2.  Click the **"Reset Kill Status"** button for the desired user.
3.  This clears the lock, and the engine status will return to `STOPPED`. You can now restart it from the dashboard if needed.