import threading
import time
import json
from pathlib import Path
from utils.initialize import create_bot_state
from kotak_api.client_login import authenticate_client
from utils.file_ops import update_kill_history_disk

# Service Imports
from services.data_service import run_data_service
from services.risk_service import run_risk_service
from services.kill_switch_service import run_kill_switch_service
from services.config_watcher import run_config_watcher
from services.snapshot_service import run_snapshot_service

class TradeEngine:
    def __init__(self, user_id):
        self.user_id = user_id
        # Load initial state
        self.state = create_bot_state(user_id) 
        self.log = self.state['sys']['log']
        
        # Define Service Groups
        self.core_services = {
            "Data": run_data_service,
            "Config": run_config_watcher,
            "Snap": run_snapshot_service
        }
        self.active_services = {
            "Risk": run_risk_service,
            "Kill": run_kill_switch_service
        }

        # Auto-start logic (Legacy config check)
        if self.state['sys']['config'].get('account_active', False):
             self.start_session()

    def start_session(self):
        """
        Starts the engine. If locked, starts in 'Observer Mode' (No Risk/Kill).
        """
        if self.state['signals']['system_active']:
            self.log.warning("Session already active.", tags=["SYS"])
            return

        is_locked = self.state['signals'].get('is_locked_today', False)
        mode_str = "OBSERVER MODE" if is_locked else "ACTIVE TRADING MODE"
        
        self.log.info(f">>> STARTING SESSION ({mode_str}) <<<", tags=["SYS", "START"])
        self._reload_credentials() 
        
        # Reset Flags
        with self.state['sys']['lock']:
            self.state['signals']['system_active'] = True
            # Only reset kill flags if NOT locked
            if not is_locked:
                self.state['signals']['trigger_kill'] = False
                self.state['signals']['kill_executed'] = False
            
            self.state['status']['error_message'] = None
            self.state['status']['stage'] = "BOOTING"
            self.state['status']['session_start_time'] = time.time()

        # 1. Authenticate
        try:
            authenticate_client(self.state)
            self.state['status']['stage'] = "LOCKED (VIEW ONLY)" if is_locked else "RUNNING"
        except Exception as e:
            self.log.error(f"Boot Failed: {e}", tags=["SYS", "FAIL"])
            self.state['signals']['system_active'] = False
            self.state['status']['stage'] = "AUTH_ERR"
            return

        # 2. Spawn Core Services (Always Run)
        for name, func in self.core_services.items():
            self._spawn_thread(func, name)

        # 3. Spawn Active Services (Only if NOT locked)
        if not is_locked:
            for name, func in self.active_services.items():
                self._spawn_thread(func, name)
        else:
            self.log.warning("Risk & Kill services disabled due to Daily Lock.", tags=["SYS", "LOCK"])

        # 4. Start Watchdog
        self._spawn_thread(self._watchdog_loop, "Watchdog")

        self.log.info(f"Session Started in {mode_str}.", tags=["SYS", "OK"])

    def stop_session(self):
        """Signals all threads to stop."""
        if not self.state['signals']['system_active']: return

        self.log.info(">>> STOPPING SESSION <<<", tags=["SYS", "STOP"])
        
        with self.state['sys']['lock']:
            self.state['signals']['system_active'] = False
            self.state['status']['stage'] = "STOPPING"

        threads = self.state['sys']['threads']
        for name, t in list(threads.items()):
            if t.is_alive() and t is not threading.current_thread():
                t.join(timeout=1.0) 
            if name in threads: del threads[name]

        with self.state['sys']['lock']:
            self.state['sys']['api'] = None
            self.state['status']['stage'] = "IDLE"
            self.state['status']['session_start_time'] = None

    def refresh_session(self):
        """Re-authenticates the API client without stopping services."""
        if not self.state['signals']['system_active']:
            self.log.warning("Cannot refresh inactive session.", tags=["SYS"])
            return

        self.log.info("Refreshing API Session...", tags=["SYS", "REFRESH"])
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        try:
            self._reload_credentials()
            authenticate_client(self.state) # This updates state['sys']['api'] in place
            self.log.info("API Session Refreshed Successfully.", tags=["SYS", "REFRESH"])
        except Exception as e:
            self.log.error(f"Session Refresh Failed: {e}", tags=["SYS", "ERR"])

    def unlock_account(self):
        """Manually clears lock."""
        self.log.info("Manual Lock Override.", tags=["SYS", "RESET"])
        with self.state['sys']['lock']:
            self.state['signals']['is_locked_today'] = False
            self.state['sys']['config']['kill_history'] = {"locked_date": None, "timestamp": None, "verified": False}
        update_kill_history_disk(self.user_id, verified=False)

    def _spawn_thread(self, target_func, name):
        t_name = f"{self.user_id}_{name}"
        t = threading.Thread(target=target_func, args=(self.state,), name=t_name, daemon=True)
        t.start()
        self.state['sys']['threads'][name] = t

    def _watchdog_loop(self, state):
        log = state['sys']['log']
        while state['signals']['system_active']:
            time.sleep(5) 
            
            is_locked = state['signals'].get('is_locked_today', False)
            
            with state['sys']['lock']:
                threads = state['sys']['threads']
            
            # Check Core Services
            for name, func in self.core_services.items():
                if name not in threads or not threads[name].is_alive():
                    if state['signals']['system_active']:
                        log.warning(f"Core Service '{name}' died! Restarting...", tags=["SYS", "FIX"])
                        self._spawn_thread(func, name)

            # Check Active Services (Only if NOT locked)
            if not is_locked:
                for name, func in self.active_services.items():
                    if name not in threads or not threads[name].is_alive():
                        # Don't restart Kill service if it already finished successfully
                        if name == "Kill" and state['signals']['kill_executed']:
                            continue
                        
                        if state['signals']['system_active']:
                            log.warning(f"Active Service '{name}' died! Restarting...", tags=["SYS", "FIX"])
                            self._spawn_thread(func, name)
    
    def _reload_credentials(self):
        try:
            path = Path(__file__).parent.parent / "source" / "credentials.json"
            with open(path, 'r') as f:
                data = json.load(f)
                if self.user_id in data:
                    self.state['sys']['creds'] = data[self.user_id]
        except Exception as e:
            self.log.error(f"Cred Reload Failed: {e}", tags=["SYS", "WARN"])

    # Legacy wrappers
    def authenticate(self): pass 
    def run_preflight_check(self): pass
    def start_services(self): pass
    def stop(self): self.stop_session()