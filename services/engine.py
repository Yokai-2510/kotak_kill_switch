import threading
import json
from pathlib import Path
from utils.initialize import create_bot_state
from kotak_api.client_login import authenticate_client
from services.initial_check import run_initial_system_check
from services.data_service import run_data_service
from services.risk_service import run_risk_service
from services.kill_switch_service import run_kill_switch_service
from services.config_watcher import run_config_watcher
from services.snapshot_service import run_snapshot_service, safe_serialize

class TradeEngine:
    def __init__(self, user_id):
        self.user_id = user_id
        self.state = create_bot_state(user_id) 
        self.log = self.state['sys']['log']
        self.threads = []
        
        # Helper to check if enabled
        self.is_active = self.state['sys']['config'].get('account_active', False)
        
        # Update Status
        self._update_status("STOPPED" if not self.is_active else "INIT")
        
        # Create initial snapshot immediately (so GUI doesn't crash on disabled users)
        self._init_snapshot()

    def _update_status(self, stage, error=None):
        """Helper to safely update status dict"""
        with self.state['sys']['lock']:
            self.state['status']['stage'] = stage
            if error:
                self.state['status']['error_message'] = str(error)

    def _init_snapshot(self):
        """Creates a default snapshot file at startup"""
        file_path = Path(__file__).parent.parent / "logs" / f"{self.user_id}_snapshot.json"
        
        # Clean safe copy
        data = {
            "timestamp": "INIT",
            "user_id": self.user_id,
            "status": self.state['status'],
            "risk": self.state['risk'],
            "market": self.state['market'],
            "signals": self.state['signals'],
            "sys": {
                "config": self.state['sys']['config'],
                "creds": self.state['sys']['creds'],
                "api_status": "Disconnected"
            }
        }
        
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2, default=safe_serialize)
        except Exception:
            pass

    def authenticate(self):
        """Phase 2: Auth"""
        if not self.is_active:
            self.log.warning("Account Inactive. Skipping Auth.", tags=["AUTH"])
            return

        self._update_status("AUTHING")
        self.state['status']['error_message'] = None

        try:
            authenticate_client(self.state)
            
            with self.state['sys']['lock']:
                self.state['status']['auth_success'] = True
                self.state['status']['stage'] = "AUTH_OK"
            
        except Exception as e:
            self.log.critical(f"Auth Failed: {e}", tags=["AUTH"])
            
            with self.state['sys']['lock']:
                self.state['status']['auth_success'] = False
                self.state['status']['stage'] = "ERROR"
                self.state['status']['error_message'] = str(e)

    def run_preflight_check(self):
        """Phase 3: Checks"""
        if not self.is_active: return
        
        if not self.state['status']['auth_success']:
            self.log.error("Skipping checks: Authentication failed previously.", tags=["CHECK"])
            return

        try:
            run_initial_system_check(self.state)
            with self.state['sys']['lock']:
                mtm = self.state['risk']['mtm_current']
                sl = self.state['risk']['sl_hit_status']
            self.log.info(f"Check Complete. MTM: {mtm} | SL: {sl}", tags=["CHECK"])
        except Exception as e:
            self.log.error(f"Pre-flight Check Failed: {e}", tags=["CHECK"])
            self._update_status("ERROR", error=str(e))

    def start_services(self):
        """Phase 4: Threads"""
        if not self.is_active:
            self.log.warning("Account Inactive. No services started.", tags=["ENGINE"])
            return
            
        if not self.state['status']['auth_success']:
             self.log.error("CRITICAL: Cannot start services because Authentication Failed.", tags=["ENGINE"])
             return

        services = [
            (run_data_service, "Data"),
            (run_risk_service, "Risk"),
            (run_kill_switch_service, "Kill"),
            (run_config_watcher, "Config"),
            (run_snapshot_service, "Snapshot")
        ]
        
        for func, name in services:
            t_name = f"{self.user_id}_{name}"
            t = threading.Thread(target=func, args=(self.state,), name=t_name, daemon=True)
            t.start()
            self.threads.append(t)
            
        self.log.info("All Services Started.", tags=["ENGINE"])
        
        with self.state['sys']['lock']:
            self.state['status']['services_running'] = True
            self.state['status']['stage'] = "RUNNING"

    def stop(self):
        """Graceful Stop"""
        self.log.info("Stopping Engine...", tags=["ENGINE"])
        with self.state['sys']['lock']:
            self.state['signals']['system_active'] = False
            self.state['status']['services_running'] = False
            self.state['status']['stage'] = "STOPPED"