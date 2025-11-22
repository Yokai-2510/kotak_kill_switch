# main.py

"""
KILL SWITCH SYSTEM - CENTRAL ORCHESTRATOR
Flow: Phase 1 (Init) -> Phase 2 (Auth) -> Phase 3 (Monitor Loop)
"""

import sys
import os
import time
import argparse

# --- PHASE 1: INIT ---
from utils.initialize import initialize

# --- PHASE 2: AUTH ---
from kotak_api.client_login import authenticate

# --- PHASE 3: DATA FETCH ---
from kotak_api.positions import fetch_positions
from kotak_api.orders import fetch_orders, check_sl_hit
from kotak_api.quotes import fetch_ltp

# --- PHASE 4: TRIGGER LOGIC ---
from trigger_logic.mtm import calculate_mtm
from trigger_logic.kill_switch import check_trigger, execute_kill_switch


def run_monitor_cycle(data):
    """Single monitoring cycle - fetch data, check trigger"""
    data = fetch_positions(data)
    data = fetch_orders(data)
    data = check_sl_hit(data)
    data = fetch_ltp(data)
    data = calculate_mtm(data)
    data = check_trigger(data)
    return data


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', type=str, default='daemon', choices=['single_run', 'daemon'])
    args = parser.parse_args()
    
    project_root = os.path.dirname(os.path.abspath(__file__))

    # =========================================================
    # PHASE 1: INITIALIZE
    # =========================================================
    data = initialize(project_root)
    log = data['logger']
    cfg = data['config']
    
    log.info("=" * 50)
    log.info(f"KILL SWITCH SYSTEM ({args.mode.upper()})")
    log.info(f"MTM Limit: {cfg['kill_switch']['mtm_limit']}")
    log.info(f"Dry Run: {cfg['kill_switch']['dry_run']}")
    log.info("=" * 50)

    # =========================================================
    # PHASE 2: AUTHENTICATE
    # =========================================================
    data = authenticate(data)

    # =========================================================
    # PHASE 3: SINGLE RUN OR DAEMON LOOP
    # =========================================================
    if args.mode == 'single_run':
        data = run_monitor_cycle(data)
        data = execute_kill_switch(data)
        log.info("Single run complete")
        return

    # DAEMON MODE
    log.info("Entering monitoring loop...")
    poll_interval = cfg['monitoring']['poll_interval_seconds']
    
    while not data['state']['kill_switch_triggered']:
        try:
            data = run_monitor_cycle(data)
            
            if data['state']['kill_switch_triggered']:
                data = execute_kill_switch(data)
                break
            
            time.sleep(poll_interval)
            
        except KeyboardInterrupt:
            log.info("Stopped by user")
            break
        except Exception as e:
            log.error(f"Cycle error: {e}")
            time.sleep(poll_interval)
    
    log.info("Kill Switch System Stopped")


if __name__ == "__main__":
    main()