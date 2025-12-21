
# **System Architecture Document (v2.1)**

## **1. Core Architecture: The Multi-Engine, Event-Driven Model**

The application is a multi-threaded, event-driven desktop system built around a central **Controller** pattern. Each configured user account is managed by an independent, isolated **`TradeEngine`** instance (`services/engine.py`), which acts as a state controller.

*   **Engine Instance:** One `TradeEngine` is instantiated per user ID at startup.
*   **State Management:** Each engine maintains a dedicated, in-memory `state` dictionary, protected by a `threading.Lock`. This dictionary is the single source of truth for all real-time data for that user (MTM, positions, status, etc.).
*   **Lifecycle Control:** The `TradeEngine` manages the complete lifecycle of its associated services.
    1.  **IDLE:** Initial state. Configuration is loaded, but no API connections or background threads are active.
    2.  **LOCKED:** On initialization, the engine checks a persistent `kill_history.json`. If a verified kill switch event occurred on the current trading day, the engine enters a `LOCKED` state and refuses to start, operating only in a read-only "Observer Mode."
    3.  **RUNNING:** When activated by the user via the GUI, the engine authenticates with the broker and spawns its suite of worker threads (services).
    4.  **STOPPED:** When deactivated, the engine signals all its threads to terminate gracefully, joins them, and cleans up API connections.

## **2. Project Structure**

```text
kotak_kill_switch/
├── main.py                      # Application Entry Point (Launcher)
│
├── source/                      # Configuration & Persistence
│   ├── USER_ID_config.json      # User-specific risk limits, automation steps, etc.
│   ├── USER_ID_credentials.json # User-specific API secrets
│   └── kill_history.json        # Persistent record of verified kill switch events
│
├── services/                    # Background Worker Threads (The "Brain")
│   ├── engine.py                # The Controller: Manages state, auth, and service threads.
│   ├── data_service.py          # API Polling: Fetches positions, orders, and quotes.
│   ├── risk_service.py          # Core Logic: Calculates MTM, detects SL hits & external triggers.
│   └── kill_switch_service.py   # Execution: Coordinates parallel API & browser automation.
│
├── gui/                         # Presentation Layer (CustomTkinter)
│   ├── gui_app.py               # Main Application Window and Frame Manager
│   ├── dashboard.py             # Global summary and control panel.
│   ├── risk_config.py           # GUI for editing user-specific risk parameters.
│   └── ... (other UI component files)
│
├── web_automation/              # Browser Automation (The "Hands")
│   ├── automate.py              # Main Playwright driver for browser interaction.
│   └── email_verifier.py        # IMAP/Gmail utility for OTP and kill switch confirmation.
│
├── kotak_api/                   # Broker Interface Layer (The "Senses")
│   ├── client_login.py          # Self-healing AuthenticatedApiClient class.
│   ├── positions.py             # Position data fetching and normalization.
│   ├── orders.py                # Order history fetching and parsing.
│   └── ... (other API wrapper files)
│
└── utils/                       # Shared Helper Modules
    ├── initialize.py            # State initialization and daily reset logic.
    ├── logger.py                # Structured logging with credential masking.
    └── file_ops.py              # Atomic JSON read/write operations.
```

## **3. Service Layer: The Engine's Worker Threads**

All services are managed by the `TradeEngine` and operate as independent, daemonized background threads. They communicate and share data exclusively through the engine's thread-safe `state` dictionary.

| Service | Responsibility | Logic Flow & Key Features |
| :--- | :--- | :--- |
| **Data Service** | **Data Acquisition** | **`Positions` -> `Orders` -> `Quotes` -> `Sleep(configurable)`.** Uses the self-healing `AuthenticatedApiClient` for all calls, making it resilient to session disconnects. Populates the `state` with fresh market data. |
| **Risk Service** | **Decision Making** | **`Read State` -> `Calculate` -> `Update Signals`.** <br>1. Calculates MTM from data provided by the Data Service.<br>2. Analyzes order history to confirm if a sold-leg SL order is `COMPLETE`.<br>3. Checks for external kill triggers (e.g., via email scan).<br>4. If `(MTM <= Limit AND SL_Hit)` OR `External_Kill`, it sets a `trigger_kill` flag in the `state`. |
| **Kill Switch Service** | **Execution & Verification** | **`Detect Signal` -> `Execute Actions` -> `Verify`.** <br>1. Monitors the `trigger_kill` flag.<br>2. On trigger, it spawns two parallel threads: one for **API-based square-off** of hedges and another for **browser automation** to activate the terminal's kill switch.<br>3. After execution, it spawns a non-blocking **async verification worker** to check for the confirmation email. |
| **Engine Watchdog** | **Self-Healing** | A high-level loop within the `TradeEngine` itself. Periodically checks `thread.is_alive()` for all its service threads. If a thread has crashed, it logs a critical error and attempts to restart it. |

## **4. Automation & Verification: "Trust, but Verify" Protocol**

The system employs a closed-loop verification model to ensure the kill switch action was successful.

*   **Browser Automation:** The Playwright script (`automate.py`) is designed to be dynamic, reading its sequence of steps (clicks, key presses, etc.) directly from the user's `config.json`. This allows for easy updates without changing code. It supports both headless and headed execution modes.
*   **Verification Worker:**
    *   **Pre-Action (Login):** An IMAP/Gmail utility (`email_verifier.py`) is used to fetch the 2FA OTP for the browser login sequence.
    *   **Post-Action (Confirmation):** After the `KillSwitchService` triggers, an async worker repeatedly scans the user's inbox for a confirmation email from Kotak (e.g., subject: "Kill Switch Activated"). This verification step is crucial.
*   **Outcome & State Change:**
    *   **Verified:** If the email is found, the worker updates the persistent `kill_history.json` and sets the engine's status to `LOCKED`.
    *   **Unverified:** If the email is not found after a timeout (e.g., 5 minutes), the engine's status changes to `KILL_UNVERIFIED`, alerting the user to a potential failure in the automation.

## **5. Key System Workflows**

#### **A. Application Startup Sequence**
1.  `main.py` launches, identifies all configured user IDs from the file system.
2.  A `TradeEngine` instance is created for each user.
3.  During initialization, each `TradeEngine` calls `utils/initialize.py`.
4.  The initializer reads `kill_history.json`. If a verified kill for that user occurred on the current date, the engine's internal `is_locked` flag is set to `True`.
5.  The `gui_app.py` is launched, receiving the list of initialized (but idle) engines.

#### **B. Kill Switch Execution Sequence**
1.  The **Risk Service** detects the dual trigger condition (`MTM <= Limit` AND `SL_Hit`).
2.  It updates the shared state: `state['signals']['trigger_kill'] = True`.
3.  The **Kill Switch Service** detects this flag change.
4.  It immediately sets its internal "triggered_today" flag to `True` to prevent re-firing.
5.  It launches two parallel threads:
    *   **Thread A:** Calls `kotak_api` functions to square off any remaining hedge positions.
    *   **Thread B:** Calls `web_automation/automate.py` to perform the browser-based kill switch action.
6.  Once the threads complete, the engine's status is updated to `KILLED_PENDING_VERIFICATION`.
7.  The non-blocking **Verification Worker** begins polling the user's email.
8.  Upon finding the confirmation email, it writes to `kill_history.json`, and the engine's final status becomes `LOCKED`.

#### **C. Manual Reset Sequence**
1.  The user clicks the "Reset Kill Status" button in the GUI settings page.
2.  This action calls the `engine.unlock_account()` method for the selected user.
3.  This method clears the `kill_history` entry for the current day, both in memory and on disk (`kill_history.json`).
4.  The engine's status is reset to `STOPPED`. The user can now manually restart the session.