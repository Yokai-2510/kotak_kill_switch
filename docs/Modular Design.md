	Here is the updated **Modular Design Document (v2.0)**.

This document reflects the transition from a linear script to an **Event-Driven, Multi-Threaded Desktop Application**. It details the architecture of the current codebase.

---

# 🏗️ Modular Design Document (v2.0)

## 1. Project Structure

```text
kotak_kill_switch/
├── main.py                      # Application Entry Point (Launcher)
├── requirements.txt             # Dependency List
├── README.md                    # User Guide
│
├── source/                      # Data Persistence Layer
│   ├── config.json              # Risk limits, Automation steps, Kill History
│   └── credentials.json         # User secrets (Masked in Logs/GUI)
│
├── services/                    # Background Worker Threads
│   ├── engine.py                # THE CONTROLLER: Manages Session, Auth, & Threads
│   ├── data_service.py          # API Polling (Positions/Orders) with Auto-Heal
│   ├── risk_service.py          # Logic Calculation + External Kill Detection
│   ├── kill_switch_service.py   # Execution Coordinator (Parallel API + Browser)
│   ├── snapshot_service.py      # State persistence to disk (Low freq)
│   └── config_watcher.py        # Hot-swap Risk Limits at runtime
│
├── gui/                         # Presentation Layer (CustomTkinter)
│   ├── gui_app.py               # Main Window & Page Loader
│   ├── dashboard.py             # Global Stats & "Global Kill" Button
│   ├── accounts.py              # Login Management & Dynamic Start/Stop
│   ├── monitor.py               # Live Data Grid (Positions/OrderBook)
│   ├── risk_config.py           # MTM Limit & Logic Switches
│   ├── automation.py            # Drag-and-Drop Step Editor
│   ├── status.py                # Telemetry (Watchdog, Threads, Lock Status)
│   ├── settings.py              # App Config (Timeouts, Headless, Reset)
│   ├── logs_page.py             # Live Log Viewer with Filters
│   └── theme.py                 # Color Palette & Fonts
│
├── web_automation/              # The "Hands" (Playwright + IMAP)
│   ├── automate.py              # Main Browser Driver (Login -> Nav -> Click)
│   └── automate_utils.py        # Gmail Scanner (OTP + Kill Confirmation)
│
├── kotak_api/                   # The "Eyes" (NeoAPI Wrapper)
│   ├── client_login.py          # 2FA Authentication Logic
│   ├── positions.py             # Position Data Normalization
│   ├── orders.py                # Order Book Parsing
│   ├── quotes.py                # Real-time LTP Fetcher
│   └── exit_trade.py            # API-based Square Off Logic
│
└── utils/                       # Shared Utilities
    ├── initialize.py            # State Factory, Midnight Reset, Default Gen
    ├── logger.py                # Structured Logging with Credential Masking
    └── file_ops.py              # Safe JSON Writing (Kill History)
```

---

## 2. Core Architecture: The "Engine" Model

The system is built around the **`TradeEngine`** class (`services/engine.py`). Unlike v1.0, this is not a linear script. It is a **State Controller**.

*   **Role:** Each User ID gets one Engine instance.
*   **State:** The Engine holds the `universal_data` dictionary (RAM) protected by a `threading.Lock`.
*   **Lifecycle:**
    1.  **Idle:** Engine initialized, Config loaded. No API connection.
    2.  **Locked:** If `kill_history` shows a verified kill today, Engine refuses to start (Observer Mode).
    3.  **Running:** User clicks "Active". Engine authenticates and spawns worker threads.
    4.  **Stopped:** User clicks "Inactive". Engine signals threads to exit and cleans up API objects.

---

## 3. Service Layer (The Workers)

These run as Daemon Threads inside the Engine.

| Service | Responsibility | Logic Flow |
| :--- | :--- | :--- |
| **Data Service** | Fetch Market Data | `Positions` -> `Orders` -> `Quotes` -> `Sleep(Adaptive)` |
| **Risk Service** | Decision Making | 1. Calculate MTM<br>2. Check SL Status (`qty == fldQty`)<br>3. Check Logic (`MTM < Limit` AND `SL Hit`)<br>4. Check External Kill (Gmail Scan) |
| **Kill Service** | Execution | **Parallel:** Launch Browser Automation AND API Square Off.<br>**Post-Action:** Spawn Async Verification Worker (Non-blocking). |
| **Watchdog** | Self-Healing | Runs inside `engine.py`. Checks `is_alive()` on all threads every 5s. Restarts them if they crash. |

---

## 4. Automation Layer (Verification Logic)

The system now implements a **"Trust but Verify"** model.

*   **Browser:** Playwright script reads dynamic steps from `config.json`. Supports Headless/Headed modes.
*   **Verification:**
    *   **Pre-Kill:** Gmail OTP Listener (for Login).
    *   **Post-Kill:** Gmail Header Scanner (`automate_utils.py`). Looks for email from Kotak with subject "Kill Switch Activated".
*   **Result:**
    *   **Verified:** Lock Account for Day.
    *   **Unverified:** Warning status, allows Reset.

---

## 5. GUI Architecture (Event-Driven)

The GUI does not run logic; it reflects the state of the Engine.

*   **Data Binding:** The GUI pulls data from `engine.state` (RAM) using the thread lock.
*   **Actions:** Buttons (Start/Stop, Save) trigger methods in `engine.py`.
*   **Safety:**
    *   **Input Validation:** `risk_config.py` prevents saving invalid numbers.
    *   **Credential Masking:** `accounts.py` hides passwords by default.
    *   **Threaded Saving:** "Save" buttons run in background threads to prevent UI freezing.

---

## 6. Key Workflows

### A. The Startup Sequence
1.  `main.py` calls `load_registry`.
2.  `TradeEngine` initialized.
3.  `utils/initialize.py` checks `config.json` for `kill_history`.
    *   If Date != Today: **Reset Lock**.
    *   If Date == Today: **Set Lock Flag**.
4.  GUI Launches.

### B. The Kill Sequence
1.  **Risk Service** detects MTM Breach + SL Hit.
2.  Sets `signals['trigger_kill'] = True`.
3.  **Kill Service** wakes up:
    *   **Thread A:** Calls `kotak_api.exit_trade`.
    *   **Thread B:** Calls `web_automation.automate`.
4.  Browser closes. Status updates to `KILLED (VERIFYING)`.
5.  **Async Worker** polls Gmail for 5 minutes.
6.  If Email found -> Write to Disk -> Status `KILLED (VERIFIED)`.

### C. The Reset Sequence
1.  User clicks **"Reset Kill Status"** in Settings.
2.  Calls `engine.unlock_account()`.
3.  Clears `kill_history` in RAM and Disk.
4.  Updates Status to `IDLE`.
5.  User can now toggle "System Active".