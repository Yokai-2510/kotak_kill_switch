## 1. **Objective**

The **Automated Trading Kill Switch System** is a Python-based risk management tool designed to **automatically stop trading activity** when the trader’s **daily Mark-to-Market (MTM)** loss exceeds a defined limit, _and_ the **stop-loss (SL)** on a sold position is hit.

This ensures trading halts **only after a risk-defined loss scenario occurs**, protecting capital and enforcing discipline.

---

## 2. **Background — Strategy Context**

The trader’s core strategy:

- **Short ATM option** (income leg)
- **Buy far OTM hedge** (risk protection)
- **Manage losses** through **stop-losses on sold positions**    
- **Control overtrading** by enforcing a daily MTM limit


Hence, the Kill Switch acts as a **final safety brake**, automatically locking the trading system when both:

1. A stop-loss on the sold position is hit
2. Daily MTM loss ≥ predefined threshold

---

## 3. **System Flow Overview**

### 🔁 High-Level Flow

1. **Fetch positions** from Kotak Neo API    
2. **Compute MTM** (mark-to-market) using current market prices
3. **Check stop-loss hit** on sold positions
4. If **MTM ≥ limit** and **sold position SL hit** → **Trigger Kill Switch**
5. **Square off hedges (optional)**
6. **Logout and disable account trading** (via browser automation)
7. **Replicate Kill Switch** for all linked accounts

---

## 4. **Kill Switch Logic**

### Step-by-Step Logic:

1. **Get All Positions**    
    - Use `client.positions()` API        
    - Retrieve both **open and closed** option positions for the current trading day

2. **Calculate Daily MTM (Mark-to-Market)**
    - For each position:
        - Compute **Total Buy Qty**, **Total Sell Qty**, **Net Qty**
        - Compute **Total Buy Amt**, **Total Sell Amt**
        - Fetch **LTP (Last Traded Price)** via the Quote API
        - Calculate **PnL** as:
            PnL = (Total Sell Amt - Total Buy Amt) 
                  + (Net Qty * LTP * multiplier * (genNum/genDen) * (prcNum/prcDen))
                  
    - Sum all individual **PnL values** to get total **Daily MTM**

3. **Monitor Stop-Loss (SL) Status**    
    - Track the **sold option’s stop-loss order** status using the Orders API
    - Identify if any **stop-loss has been executed** (i.e., exited a sold leg)

4. **Trigger Condition**    
    - Kill Switch is triggered **only when both** are true:
        - `Daily MTM Loss ≥ Threshold (set via GUI)`
        - `Stop-Loss on Sold Position = Executed`

5. **Execute Kill Switch**    
    - **Trigger via Selenium/Playwright** automation in the **Kotak Neo web terminal** (since the API doesn’t offer a kill switch endpoint).        
    - **Deactivate trading** on the account.

6. **Optional Post-Actions**
    - **Square off all hedge positions (OTM options)**.
    - **Logout via API**, ensuring that the session is terminated across web + mobile.
    - Apply the **same kill switch command to all linked trading accounts**.        

---

## 5. **Kill Switch Flow (Summary Table)**

| Step | Action                       | Source              | Trigger Condition                | Result                    |
| ---- | ---------------------------- | ------------------- | -------------------------------- | ------------------------- |
| 1    | Fetch all positions          | Kotak Neo API       | Periodic (e.g., every 2 seconds) | Latest position data      |
| 2    | Compute MTM                  | Custom logic        | After fetching positions         | Current total profit/loss |
| 3    | Check SL hit                 | Orders API          | Real-time                        | Detect SL execution       |
| 4    | Compare MTM vs threshold     | GUI input           | Continuous                       | Determine breach          |
| 5    | Activate Kill Switch         | Selenium/Playwright | MTM ≥ limit + SL hit             | Block trading             |
| 6    | Logout + Optional hedge exit | API                 | Immediately after kill           | Ensure lockout            |
| 7    | Apply to other accounts      | Internal logic      | After main account kill          | Synchronize kill          |

---

## 6. **User Interface (GUI)**

A desktop-based GUI (using **Tkinter** or **PyQt**) will allow the user to:

### 🔧 Configuration:

- Set **daily MTM loss limit**
- Add/manage **linked accounts**
- Choose **whether to auto-square-off hedges**    
- Enable/disable **Kill Switch automation**


### 📊 Live Monitoring:

- Display **current MTM** (total and per-account)
- Show **positions summary**
- Display **Kill Switch status** (Active / Triggered)
- Provide **manual override** options (force kill, reset)

### 💬 Notifications:

- Pop-up or desktop alerts when SL hits or MTM breaches limit
- Kill Switch confirmation before execution (optional toggle)    

---

## 7. **Technical Architecture**

| Layer                | Technology            | Purpose                                              |
| -------------------- | --------------------- | ---------------------------------------------------- |
| **Data Source**      | Kotak Neo API         | Fetch positions, orders, and quotes                  |
| **Automation Layer** | Selenium / Playwright | Log in to Kotak Neo terminal and trigger kill switch |
| **Backend Logic**    | Python                | MTM computation, SL monitoring, logic control        |
| **GUI**              | Tkinter / PyQt        | User configuration and monitoring dashboard          |
| **Persistence**      | JSON / SQLite         | Store thresholds, user preferences, account info     |
| **Logging**          | Python Logging module | Track all actions, events, errors                    |

---

## 8. **Safety Features**

- ✅ Kill Switch triggers **only once** per day
- ✅ Repeated triggers are ignored until manually reset
- ✅ All actions are **timestamped and logged**
- ✅ Failsafe logout ensures no further trades
- ✅ Graceful handling of API downtime or network issues

---

## 9. **Logging and Audit**

All key events are logged, including:

- Position fetch times
- MTM calculations
- SL hits
- Kill switch triggers
- Hedge square-offs
- Logouts
- Errors or retries    

Logs are stored with timestamps for audit and debugging.

---

## 10. **Deployment & Usage**

### **Setup**

- Install Python dependencies (`neo_api_client`, `selenium` or `playwright`, `tkinter` / `pyqt5`)
- Configure Kotak Neo API credentials
- Run the GUI app and set your **MTM limit**

### **During Trading**

- Keep the app running
- App will continuously monitor MTM and SL status
- If both trigger conditions are met → **Kill Switch is executed automatically**    

---

## 11. **Key Design Principles**

- **Accuracy:** MTM calculated from all positions, updated frequently
- **Safety:** Triggers only when both SL hit and MTM breach occur
- **Automation:** Fully handles web terminal actions (no manual input)
- **Scalability:** Can manage multiple accounts from one interface
- **Transparency:** All actions visible via GUI and logged for review

---

## 12. **Example Scenario**

| Event                       | Status         | Result                 |
| --------------------------- | -------------- | ---------------------- |
| Daily MTM = ₹9,500          | SL not hit     | Continue trading       |
| SL on sold leg triggers     | MTM = ₹10,200  | Kill Switch activates  |
| Kill Switch executed        | Account logout | Trading locked for day |
| Hedge positions squared off | Optional       | Positions flattened    |

---

## 13. **Future Enhancements**

- Support for additional accounts    
- Telegram bot integration for alerts

---

