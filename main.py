"""
KOTAK KILL SWITCH - ORCHESTRATOR
Linear Init -> Auth -> Initial Check -> (Pending: Threaded Services)
"""

import sys
import threading
import time
from pathlib import Path

# --- PHASE 1: INIT ---
from utils.initialize import initialize_system

# --- PHASE 2: AUTHENTICATION ---
from kotak_api.client_login import authenticate_client

# --- PHASE 3: PRE-FLIGHT CHECK (Data Sync) ---
from services.initial_check import run_initial_system_check

# --- PHASE 4: SERVICES (Thread Targets) - PENDING ---
# from services.data_service import run_data_service
# from services.risk_service import run_risk_service
# from services.kill_switch_service import run_kill_switch_service


# ====================  1. INITIALIZATION & AUTH ====================

# Initialize Universal Dict (Config, State, Logger)
universal_data = initialize_system()
log = universal_data['logger'].info

log("=== SYSTEM STARTUP ===")

# Authenticate (Modifies universal_data['client'])
authenticate_client(universal_data)


# ====================  2. INITIAL SYSTEM CHECK ====================
log(">>> Running Pre-flight Checks...")

# Single linear pass: Syncs Positions, Orders, and Quotes to 'state'
run_initial_system_check(universal_data)

# --- DEBUG: Print State to verify Phase 2 ---
import json
print("\n[DEBUG] Current State Data:")
# Helper to serialize set/objects if needed, though basic types used here
print(json.dumps(universal_data['state']['positions'], indent=2, default=str))
print(f"Total Orders: {len(universal_data['state']['orders'])}")
print(f"LTPs: {universal_data['state']['quotes']}")


# ====================  3. START SERVICE THREADS (PENDING) ====================
# log(">>> Starting Services...")

# Thread 1: Data Service (Polls API: Positions, Orders, Quotes)
# data_thread = threading.Thread(
#     target=run_data_service, 
#     args=(universal_data,), 
#     name="DataThread", 
#     daemon=True
# )
# data_thread.start()

# Thread 2: Risk Service (Calcs MTM, Checks SL -> Sets 'trigger_signal')
# risk_thread = threading.Thread(
#     target=run_risk_service, 
#     args=(universal_data,), 
#     name="RiskThread", 
#     daemon=True
# )
# risk_thread.start()

# Thread 3: Kill Switch Service (Browser Automation -> Waits for 'trigger_signal')
# kill_thread = threading.Thread(
#     target=run_kill_switch_service, 
#     args=(universal_data,), 
#     name="KillSwitchThread", 
#     daemon=True
# )
# kill_thread.start()


# ====================  4. MAIN LOOP (PENDING) ====================
# Keep alive until system_active is set to False (by Kill Switch after execution)

# while universal_data['system_active']:
#     time.sleep(1)

log("=== SYSTEM SHUTDOWN (TEST COMPLETE) ===")