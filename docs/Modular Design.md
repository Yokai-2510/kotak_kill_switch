	## Project Structure

```
kotak_kill_switch/
├── main.py                    # Entry point - orchestrates everything
├── requirements.txt
├── README.md
│
├── source/
│   ├── config.json            # MTM limit, settings, flags
│   └── credentials.json       # API & login credentials
│
├── kotak_api/
│   ├── client_login.py        # API authentication (TOTP + MPIN)
│   ├── positions.py           # Fetch positions data
│   ├── orders.py              # Fetch orders, check SL status
│   └── quotes.py              # Get LTP for MTM calculation
│
├── trigger_logic/
│   ├── mtm.py                 # Calculate daily MTM from positions
│   ├── stop_loss.py           # Detect if SL on sold position hit
│   ├── kill_switch_logic.py   # Core logic: MTM + SL → trigger decision
│   └── utils.py               # Helpers (logging, formatting)
│
├── web_automation/
│   ├── login.py               # Playwright: login to Kotak Neo web
│   ├── gmail_otp.py           # Gmail API: fetch OTP from email
│   └── kill_switch.py         # Playwright: click kill switch button
│
├── gui/                       # (Phase 4 - optional)
│   └── dashboard.py           # Tkinter/PyQt monitoring UI
│
└── tests/
    └── test_mtm.py            # Unit tests
```

---

## Phase 1: Core API Layer ✅ → 🔄

**Goal:** Fetch all data needed for kill switch decision

|Module|File|Function|Status|
|---|---|---|---|
|Auth|`kotak_api/client_login.py`|`fetch_client(creds)` → returns authenticated client|✅ Done|
|Positions|`kotak_api/positions.py`|`get_positions(client)` → returns positions list|🔄 Build|
|Orders|`kotak_api/orders.py`|`get_orders(client)` → returns order book|🔄 Build|
|Quotes|`kotak_api/quotes.py`|`get_ltp(client, tokens)` → returns LTP dict|🔄 Build|

**Phase 1 Success Criteria:**

- [ ] Can fetch positions with all fields needed for MTM
- [ ] Can fetch orders and identify SL orders
- [ ] Can get LTP for any instrument token

---

## Phase 2: Trigger Logic Layer

**Goal:** Compute MTM, detect SL hit, make kill switch decision

|Module|File|Function|
|---|---|---|
|MTM|`trigger_logic/mtm.py`|`calculate_mtm(positions, quotes)` → returns total PnL|
|SL Check|`trigger_logic/stop_loss.py`|`is_sl_hit(orders)` → returns True/False|
|Decision|`trigger_logic/kill_switch_logic.py`|`should_trigger(mtm, sl_hit, config)` → returns True/False|

**MTM Formula:**

```
For each position:
  PnL = (SellAmt - BuyAmt) + (NetQty × LTP × multiplier)

Total MTM = sum of all PnL
```

**Trigger Condition:**

```python
if mtm_loss >= config['mtm_limit'] and is_sl_hit:
    return True  # Trigger kill switch
```

**Phase 2 Success Criteria:**

- [ ] MTM calculation matches broker's P&L display
- [ ] SL hit detection works correctly
- [ ] Decision logic returns correct True/False

---

## Phase 3: Web Automation Layer

**Goal:** Automate browser to activate kill switch

### 3A: Gmail OTP Fetcher

|File|Function|
|---|---|
|`web_automation/gmail_otp.py`|`fetch_otp(email)` → returns latest OTP from inbox|

**Approach:**

- Use Gmail API with OAuth
- Search for recent emails from Kotak
- Extract OTP using regex

### 3B: Kotak Web Login

|File|Function|
|---|---|
|`web_automation/login.py`|`login_to_neo(creds)` → returns logged-in browser page|

**Flow:**

1. Open https://neo.kotaksecurities.com
2. Enter mobile/UCC
3. Wait for OTP email → call `fetch_otp()`
4. Enter OTP
5. Enter MPIN
6. Return authenticated page

### 3C: Kill Switch Executor

|File|Function|
|---|---|
|`web_automation/kill_switch.py`|`execute_kill_switch(page)` → clicks kill switch, returns success|

**Flow:**

1. Navigate to positions/settings
2. Find kill switch button (use Playwright codegen to get selectors)
3. Click and confirm
4. Verify success

**Phase 3 Success Criteria:**

- [ ] Can fetch OTP from Gmail automatically
- [ ] Can login to Kotak Neo web without manual input
- [ ] Can trigger kill switch via browser automation

---

## Phase 4: Main Orchestrator + GUI (Optional)

### main.py - Core Loop

```python
def main():
    # Load config
    config = load_config()
    creds = load_credentials()
    
    # Authenticate API
    client = fetch_client(creds)
    
    # Main monitoring loop
    while True:
        positions = get_positions(client)
        orders = get_orders(client)
        quotes = get_ltp(client, extract_tokens(positions))
        
        mtm = calculate_mtm(positions, quotes)
        sl_hit = is_sl_hit(orders)
        
        if should_trigger(mtm, sl_hit, config):
            # Execute kill switch
            page = login_to_neo(creds)
            execute_kill_switch(page)
            log("KILL SWITCH ACTIVATED")
            break
        
        sleep(2)  # Poll every 2 seconds
```

### GUI (Optional)

- Display live MTM
- Show positions summary
- Manual trigger button
- Status indicator (Active/Triggered)

**Phase 4 Success Criteria:**

- [ ] Full loop runs without errors
- [ ] Kill switch triggers correctly on test conditions
- [ ] System handles API errors gracefully

---

## Config Files

### source/config.json

```json
{
  "mtm_limit": 10000,
  "poll_interval_seconds": 2,
  "auto_square_off_hedges": false,
  "kill_switch_enabled": true,
  "log_level": "INFO"
}
```

### source/credentials.json

```json
{
  "consumer_key": "ec739c67-b186-42c1-b254-9456edf9f264",
  "ucc": "XARGA",
  "mobile_number": "+919310926729",
  "mpin": "251802",
  "totp_secret": "TRC5ARJYNMHYD7WNCJIR4RMOXE",
  "gmail_email": "your@gmail.com"
}
```

---

## Development Order

|Phase|Modules|Estimated Time|
|---|---|---|
|1|positions.py, orders.py, quotes.py|1 day|
|2|mtm.py, stop_loss.py, kill_switch_logic.py|1 day|
|3|gmail_otp.py, login.py, kill_switch.py|2 days|
|4|main.py integration, testing|1 day|

---

## Testing Strategy

1. **Phase 1:** Print raw API responses, verify data structure
2. **Phase 2:** Test with mock data, compare MTM with broker
3. **Phase 3:** Run Playwright in headed mode, watch automation
4. **Phase 4:** Dry-run (log instead of executing kill switch)

---

## Notes

- No `__init__.py` files needed - use direct imports
- Keep each module under 100 lines
- Log everything to file for audit trail
- Add `dry_run` flag in config for testing without executing