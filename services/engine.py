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
from services.websocket_service import run_websocket_service # <--- NEW MODULE

class TradeEngine:
    def __init__(self, user_id):
        self.user_id = user_id
        self.state = create_bot_state(user_id) 
        self.log = self.state['sys']['log']
        
        # 1. Core Services (Required for basic monitoring)
        self.core_services = {
            "Data": run_data_service,      # Slow REST Sync
            "Config": run_config_watcher,  # Limit Monitor
            "Websocket": run_websocket_service # <--- LIVE STREAM (LTP/Orders)
        }
        
        # 2. Active Services (Operational Risk Management)
        self.active_services = {
            "Risk": run_risk_service,
            "Kill": run_kill_switch_service
        }

        if self.state['sys']['config'].get('account_active', False):
             self.start_session()

    def start_session(self):
        """Starts the engine session and spawns all background threads."""
        if self.state['signals']['system_active']:
            self.log.warning("Session already active.", tags=["SYS"])
            return

        is_locked = self.state['signals'].get('is_locked_today', False)
        mode_str = "OBSERVER MODE" if is_locked else "ACTIVE TRADING MODE"
        
        self.log.info(f">>> STARTING SESSION ({mode_str}) <<<", tags=["SYS", "START"])
        self._reload_credentials() 
        
        with self.state['sys']['lock']:
            self.state['signals']['system_active'] = True
            if not is_locked:
                self.state['signals']['trigger_kill'] = False
                self.state['signals']['kill_executed'] = False
            
            self.state['status']['error_message'] = None
            self.state['status']['data_stale'] = False
            self.state['status']['stage'] = "BOOTING"
            self.state['status']['session_start_time'] = time.time()

        try:
            # 1. Authenticate with Kotak (Initial Handshake)
            authenticate_client(self.state)
            self.state['status']['stage'] = "LOCKED (VIEW ONLY)" if is_locked else "RUNNING"
        except Exception as e:
            self.log.error(f"Boot Failed: {e}", tags=["SYS", "FAIL"])
            self.state['signals']['system_active'] = False
            self.state['status']['stage'] = "AUTH_ERR"
            return

        # 2. Spawn Core Services (Includes WebSocket)
        for name, func in self.core_services.items():
            self._spawn_thread(func, name)

        # 3. Spawn Risk & Kill Services (Only if not locked for the day)
        if not is_locked:
            for name, func in self.active_services.items():
                self._spawn_thread(func, name)
        else:
            self.log.warning("Risk & Kill services disabled (Daily Lock).", tags=["SYS", "LOCK"])

        # 4. Start Watchdog (Self-Healing)
        self._spawn_thread(self._watchdog_loop, "Watchdog")
        self.log.info(f"Session Started. Monitoring via WebSocket.", tags=["SYS", "OK"])

    def stop_session(self):
        """Cleanly stops all threads and closes connections."""
        if not self.state['signals']['system_active']: return
        self.log.info(">>> STOPPING SESSION <<<", tags=["SYS", "STOP"])
        
        with self.state['sys']['lock']:
            self.state['signals']['system_active'] = False
            self.state['status']['stage'] = "STOPPING"

        # Signal threads to stop and join
        threads = self.state['sys']['threads']
        for name, t in list(threads.items()):
            if t.is_alive() and t is not threading.current_thread():
                t.join(timeout=1.0) 
            if name in threads: del threads[name]

        with self.state['sys']['lock']:
            # Invalidate the API client to force WebSocket closure
            self.state['sys']['api'] = None
            self.state['status']['stage'] = "IDLE"
            self.state['status']['session_start_time'] = None

    def refresh_session(self):
        """Manually force re-authentication and re-stream."""
        if not self.state['signals']['system_active']:
            return
        self.log.info("Refreshing API & Stream Session...", tags=["SYS", "REFRESH"])
        threading.Thread(target=self._refresh_worker, daemon=True).start()

    def _refresh_worker(self):
        try:
            self._reload_credentials()
            authenticate_client(self.state) 
            self.log.info("API Session Refreshed. WebSocket will auto-reconnect.", tags=["SYS", "REFRESH"])
        except Exception as e:
            self.log.error(f"Session Refresh Failed: {e}", tags=["SYS", "ERR"])

    def unlock_account(self):
        """Clears daily kill lockout."""
        self.log.info("Manual Lock Override.", tags=["SYS", "RESET"])
        with self.state['sys']['lock']:
            self.state['signals']['is_locked_today'] = False
            self.state['signals']['trigger_kill'] = False
            self.state['signals']['kill_executed'] = False
            
            curr_stage = str(self.state['status'].get('stage', ''))
            if self.state['signals']['system_active'] and ("LOCKED" in curr_stage or "KILLED" in curr_stage):
                 self.state['status']['stage'] = "RUNNING"
            
            self.state['sys']['config']['kill_history'] = {"locked_date": None, "timestamp": None, "verified": False}
            
        update_kill_history_disk(self.user_id, verified=False)

    def _spawn_thread(self, target_func, name):
        """Standardized thread spawner."""
        t_name = f"{self.user_id}_{name}"
        t = threading.Thread(target=target_func, args=(self.state,), name=t_name, daemon=True)
        t.start()
        self.state['sys']['threads'][name] = t

    def _watchdog_loop(self, state):
        """Ensures all services (especially WebSocket) remain running."""
        log = state['sys']['log']
        while state['signals']['system_active']:
            time.sleep(5) 
            is_locked = state['signals'].get('is_locked_today', False)
            with state['sys']['lock']:
                threads = state['sys']['threads']
            
            # Monitor Core Services (Config, Data, Websocket)
            for name, func in self.core_services.items():
                if name not in threads or not threads[name].is_alive():
                    if state['signals']['system_active']:
                        log.warning(f"Thread '{name}' crashed! Restarting...", tags=["SYS", "FIX"])
                        self._spawn_thread(func, name)

            # Monitor Action Services (Risk, Kill)
            if not is_locked:
                for name, func in self.active_services.items():
                    if name not in threads or not threads[name].is_alive():
                        # If Kill already executed, we don't need to restart it
                        if name == "Kill" and state['signals']['kill_executed']: continue
                        if state['signals']['system_active']:
                            log.warning(f"Thread '{name}' crashed! Restarting...", tags=["SYS", "FIX"])
                            self._spawn_thread(func, name)
    
    def _reload_credentials(self):
        """Reloads credentials.json from disk."""
        try:
            path = Path(__file__).parent.parent / "source" / "credentials.json"
            if not path.exists(): return
            with open(path, 'r') as f:
                data = json.load(f)
                if self.user_id in data:
                    self.state['sys']['creds'] = data[self.user_id]
        except Exception as e:
            self.log.error(f"Cred Reload Failed: {e}", tags=["SYS", "WARN"])