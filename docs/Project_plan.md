
### 📋 Project Plan: Kotak Kill Switch System

#### **Phase 1: Infrastructure & Authentication**
*   [ ] **Project Setup**: Create folders (`utils`, `kotak_api`, `services`, `trigger_logic`, `web_automation`).
*   [ ] **Configuration**: Create `source/config.json` (with new kill options) and `source/credentials.json`.
*   [ ] **Logger**: Implement `utils/logger.py` (using your exact `TaggedLogger` code).
*   [ ] **Initialization**: Create `utils/initialize.py` to load config, creds, and logger into `universal_data`.
*   [ ] **Authentication**: Create `kotak_api/client_login.py` for TOTP/MPIN login.
*   [ ] **Test**: Run `main.py` up to `authenticate_client(universal_data)` successfully.

#### **Phase 2: Data Connectors (API)**
*   [ ] **Positions**: Create `kotak_api/positions.py` (Fetch & Parse).
*   [ ] **Orders**: Create `kotak_api/orders.py` (Fetch & Filter for SL).
*   [ ] **Quotes**: Create `kotak_api/quotes.py` (LTP Fetcher).
*   [ ] **Test**: Run `main.py` up to `run_initial_system_check` to print raw data snapshots.

#### **Phase 3: Risk Logic**
*   [ ] **MTM Engine**: Create `trigger_logic/mtm.py` (Calculate PnL from positions + quotes).
*   [ ] **SL Detector**: Create `trigger_logic/stop_loss.py` (Check if sold leg SL is hit).
*   [ ] **Pre-Flight**: Create `services/initial_check.py` (The linear sanity check).
*   [ ] **Test**: Verify MTM calculation matches Broker UI (roughly).

#### **Phase 4: Browser Automation (Kill Switch)**
*   [ ] **Browser Auth**: Create `web_automation/login.py` (Playwright login flow).
*   [ ] **Kill Trigger**: Create `web_automation/kill_trigger.py` (Selector logic to click "Kill Switch").
*   [ ] **Service**: Create `services/kill_switch_service.py` (Thread wrapper waiting for signal).
*   [ ] **Test**: Run a "Dry Run" where browser opens, logs in, finds button, but *does not* click.

#### **Phase 5: Live Monitoring (Daemon)**
*   [ ] **Data Service**: Create `services/data_service.py` (Threaded polling).
*   [ ] **Risk Service**: Create `services/risk_service.py` (Threaded logic & signaling).
*   [ ] **Integration**: Connect all threads in `main.py`.
*   [ ] **Final Test**: Live run with small MTM limit to verify trigger flow.

---

**Ready to start Phase 1?**
I will generate the file structure, JSON configs, and the Init/Auth modules.
(I will assume standard API fields for now and we can patch `kotak_api` in Phase 2 if names differ).