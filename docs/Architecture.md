
## **Project Architecture: Automated Trading Kill Switch System**

### **1. Objective**

To create a robust, automated risk management system that protects trading capital by enforcing a strict daily loss protocol. The system will **automatically disable trading** for one or more accounts when **two specific conditions are met simultaneously**:

1.  The user's **daily Mark-to-Market (MTM) loss** exceeds a pre-defined limit.
2.  A **stop-loss (SL) order on a primary sold option position** has been executed.

This dual-condition logic ensures the system only activates after a significant, confirmed loss event, preventing premature shutdowns during normal market volatility.

---

### **2. Core Logic & System Flow**

The system operates in a continuous monitoring loop for each active user engine.

#### **High-Level Flow:**

1.  **Fetch Account Data:** Continuously pull open positions and the day's order history from the Kotak Neo API.
2.  **Calculate Real-Time MTM:** Compute the total daily MTM by combining realized PnL from closed positions and unrealized PnL from open positions (using live LTPs).
3.  **Monitor SL Status:** Analyze the order history to detect if a stop-loss order for a primary sold position has been `EXECUTED` or `COMPLETE`.
4.  **Evaluate Trigger Conditions:** On every cycle, check if `(Daily MTM <= MTM_Loss_Limit)` **AND** `(Sold_Position_SL_Hit == True)`.
5.  **Execute Kill Switch:** If both conditions are true, trigger the automated kill switch sequence.
6.  **Post-Kill Actions:** Automatically square off any remaining hedge positions (optional), perform a definitive API logout, and send a notification.
7.  **Synchronization:** Replicate the kill switch command across all linked user accounts if configured.

---

### **3. Technical Architecture**

The system is built on a modular, multi-threaded Python backend with a desktop GUI for control and monitoring.

| Layer | Technology / Module | Purpose & Key Responsibilities |
| :--- | :--- | :--- |
| **Orchestration** | `services/engine.py` | The central `TradeEngine` class for each user. Manages the lifecycle of all services. |
| **API Interface** | `kotak_api/client_login.py` | A self-healing `AuthenticatedApiClient` class. Handles all API communication, including login, retries, and automatic re-authentication on session expiry. **This is the single point of contact with the broker.** |
| **Automation Layer** | `web_automation/` (Playwright) | Handles browser automation tasks that are not available via API, specifically logging into the Kotak Neo web terminal to physically activate the "Kill Switch" feature. |
| **Core Services** | `services/` | A collection of background threads, each with a single responsibility: |
| | `risk_service.py` | Fetches positions/orders via the API client, calculates MTM, and monitors for SL hits. Updates the shared state. |
| | `kill_switch_service.py`| Monitors the shared state for the trigger signal from the Risk Service. When triggered, it invokes the Automation Layer to execute the kill switch. |
| | `config_watcher.py` | Monitors the user's config file for real-time changes (e.g., updating the MTM limit) and reloads them without a restart. |
| **User Interface** | `gui/` (Tkinter / PyQt) | Provides the main dashboard for configuration, live monitoring, and manual overrides. Interacts with the backend `TradeEngine` instances. |
| **Configuration** | `source/USER_ID_config.json` | JSON files for storing user credentials, risk limits, API retry settings, and GUI preferences. |
| **Utilities** | `utils/` | Helper modules for tasks like logging (`log_manager.py`) and notifications (`notifications.py`). |

---

### **4. Detailed Service Logic**

#### **Risk Service (`risk_service.py`)**
-   **Loop Interval:** Configurable (e.g., every 2-5 seconds).
-   **Action:**
    1.  Calls `api_client.make_api_call(client.get_positions)` to get open positions.
    2.  Calls `api_client.make_api_call(client.get_order_report)` to get the day's orders.
    3.  **Computes MTM:** Iterates through positions, calculates PnL using the official formula, and sums them up.
    4.  **Checks SL Status:** Scans the order report to see if any `SL-M` or `SL` order on a sold option has a status of `COMPLETE`. Sets a flag `sl_hit_today = True` if found.
    5.  **Updates Shared State:** Safely writes the calculated MTM, open positions, and the `sl_hit_today` flag to the main `TradeEngine` state dictionary using a thread lock.

#### **Kill Switch Service (`kill_switch_service.py`)**
-   **Loop Interval:** Fast (e.g., every 1 second).
-   **State:** Holds an internal flag, `kill_switch_triggered_today = False`.
-   **Action:**
    1.  Reads MTM, SL status, and the user's MTM limit from the shared state.
    2.  Checks the trigger condition: `if MTM <= mtm_limit and sl_hit_today and not kill_switch_triggered_today:`.
    3.  If true:
        *   Sets its internal flag `kill_switch_triggered_today = True` to prevent re-triggers.
        *   Logs the critical event.
        *   Calls the browser automation module to perform the web-based kill switch action.
        *   If configured, iterates through remaining hedge positions and calls `api_client.make_api_call(client.place_order)` to square them off.
        *   Calls `api_client.make_api_call(client.logout)`.
        *   Calls the notification utility to send a Telegram alert.
    4.  The service continues to run but will not trigger again for the rest of the day.

---

### **5. Safety & Reliability Features**

-   ✅ **Self-Healing API:** The `AuthenticatedApiClient` automatically handles session disconnects, ensuring the monitoring services remain active throughout market hours.
-   ✅ **Atomic Trigger:** The kill switch logic is contained within a single service that uses a "trigger-once" flag (`kill_switch_triggered_today`) to guarantee it only fires once per day.
-   ✅ **Daily Reset:** The `TradeEngine` resets all states (including `sl_hit_today` and `kill_switch_triggered_today`) at the start of each new trading day.
-   ✅ **Configurable Retries:** All API calls are protected by a configurable retry mechanism, adding resilience against temporary network or broker API issues.
-   ✅ **Comprehensive Logging:** All actions, state changes, API calls, and errors are timestamped and logged, creating a full audit trail.
-   ✅ **Graceful Shutdown:** The `TradeEngine` properly manages the lifecycle of all service threads, ensuring a clean exit when the application is closed.

---

### **6. User Interface (GUI) - Functional Specification**

#### **Configuration Screen:**
-   **MTM Loss Limit:** Numeric input (e.g., -10000).
-   **Auto-Square-Off Hedges:** Checkbox (On/Off).
-   **Delete Logs on Boot:** Checkbox (On/Off).
-   **API Retry Settings:** Inputs for "Max Retries" and "Retry Delay".
-   **Telegram Settings:** Inputs for "Bot Token" and "Chat ID".
-   **Save Button:** Persists all settings to the user's JSON config file.

#### **Dashboard / Live Monitor:**
-   **Global Status Card:** Displays aggregated Net System P&L, Total Open Positions, and overall system status.
-   **Per-Engine Cards:** One card for each configured user (`Eshaan Test`, `Inactive Test`, etc.). Each card displays:
    -   User ID and Monitoring Status (`ACTIVE` / `STOPPED`).
    -   **Current MTM:** Live updated value.
    -   **MTM Limit:** The configured limit.
    -   **Risk Utilization:** A progress bar showing `(Current MTM / MTM Limit) * 100`.
    -   **SL Status:** A label showing `SAFE` or `HIT TODAY`.
    -   **Open Positions:** A count of open positions.
-   **Action Buttons:**
    -   **Start/Stop Switch:** A visually distinct switch to activate or deactivate monitoring for that engine.
    -   **Manual Kill:** A button to immediately trigger the kill switch sequence, bypassing the logic.
    -   **Manual Exit:** A button next to each listed position (in a detailed view) to exit that specific position.

This architecture is modular, robust, and directly implements the dual-condition logic you require, while incorporating the critical fixes and enhancements we've discussed.