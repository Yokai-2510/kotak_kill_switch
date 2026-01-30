import customtkinter as ctk
import time
import threading
import datetime
from gui.theme import Theme

# =========================================================
#  COMPONENT: MINI STAT WIDGET (HUD)
# =========================================================

class StatBox(ctk.CTkFrame):
    def __init__(self, parent, label, value, color=Theme.TEXT_WHITE):
        super().__init__(parent, fg_color="transparent")
        self.lbl_title = ctk.CTkLabel(self, text=label, font=("Arial", 10, "bold"), text_color=Theme.TEXT_GRAY)
        self.lbl_title.pack(anchor="w", padx=10)
        self.lbl_val = ctk.CTkLabel(self, text=value, font=("Arial", 14, "bold"), text_color=color)
        self.lbl_val.pack(anchor="w", padx=10)

    def update(self, value, color=Theme.TEXT_WHITE):
        self.lbl_val.configure(text=value, text_color=color)

# =========================================================
#  COMPONENT: STATUS DETAIL ROW (Table Style)
# =========================================================
class StatusRow(ctk.CTkFrame):
    def __init__(self, parent, label, value="--", color=Theme.TEXT_WHITE):
        super().__init__(parent, fg_color="transparent")
        self.pack(fill="x", pady=2, padx=10)
        self.lbl_title = ctk.CTkLabel(self, text=label, font=("Arial", 12), text_color=Theme.TEXT_GRAY)
        self.lbl_title.pack(side="left")
        self.lbl_val = ctk.CTkLabel(self, text=value, font=("Arial", 12, "bold"), text_color=color)
        self.lbl_val.pack(side="right")

    def update(self, text, color=Theme.TEXT_WHITE):
        self.lbl_val.configure(text=text, text_color=color)

# =========================================================
#  COMPONENT: USER TELEMETRY TAB
# =========================================================
class UserStatusTab(ctk.CTkScrollableFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine

        # --- SECTION 1: INFRASTRUCTURE ---
        self._add_header("CORE INFRASTRUCTURE")
        self.card_infra = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_infra.pack(fill="x", padx=10, pady=(0, 15))
        
        self.row_api = StatusRow(self.card_infra, "REST API Connection")
        self.row_ws = StatusRow(self.card_infra, "WebSocket Stream (Ticks/Orders)")
        self.row_engine = StatusRow(self.card_infra, "Engine Master State")
        self.row_threads = StatusRow(self.card_infra, "Active Worker Threads")

        # --- SECTION 2: KILL SWITCH CONFIG & SEQUENCE ---
        self._add_header("KILL SWITCH LOGIC & SEQUENCE")
        self.card_ks = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_ks.pack(fill="x", padx=10, pady=(0, 15))
        
        self.row_mtm_logic = StatusRow(self.card_ks, "MTM Breach Logic")
        self.row_sl_conf = StatusRow(self.card_ks, "Sell Order SL Confirmation")
        self.row_sq_off = StatusRow(self.card_ks, "API Auto Square-Off")
        self.row_hard_kill = StatusRow(self.card_ks, "Hard OS Browser Termination")
        self.row_email = StatusRow(self.card_ks, "Gmail Kill Verification")
        self.row_stage = StatusRow(self.card_ks, "CURRENT SEQUENCE STAGE", color=Theme.ACCENT_BLUE)

        # --- SECTION 3: LIVE METRICS ---
        self._add_header("LIVE SESSION METRICS")
        self.card_metrics = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_metrics.pack(fill="x", padx=10, pady=(0, 15))
        
        self.row_time = StatusRow(self.card_metrics, "Session Uptime")
        self.row_pos = StatusRow(self.card_metrics, "Active Positions")
        self.row_ks_status = StatusRow(self.card_metrics, "Kill Switch Status")
        self.row_err = StatusRow(self.card_metrics, "Last System Error", color=Theme.ACCENT_GREEN)

    def _add_header(self, text):
        ctk.CTkLabel(self, text=text, font=("Arial", 10, "bold"), text_color=Theme.ACCENT_BLUE).pack(anchor="w", padx=15, pady=(10, 2))

    def update_telemetry(self):
        with self.engine.state['sys']['lock']:
            # Infra
            api_connected = bool(self.engine.state['sys']['api'])
            threads = self.engine.state['sys']['threads']
            ws_alive = "Websocket" in threads and threads["Websocket"].is_alive()
            engine_active = self.engine.state['signals']['system_active']
            
            # KS Logic Settings
            cfg = self.engine.state['sys']['config']
            ks = cfg.get('kill_switch', {})
            mtm_enabled = ks.get('enabled', False)
            sl_req = ks.get('sell_order_exit_confirmation', True)
            sq_enabled = ks.get('auto_square_off', False)
            hard_kill_enabled = cfg.get('web_automation', {}).get('hard_close_browser', False)
            email_verify = cfg.get('gmail', {}).get('enable_verification', True)
            
            # State
            stage = self.engine.state['status'].get('stage', 'IDLE')
            triggered = self.engine.state['signals']['trigger_kill']
            executed = self.engine.state['signals']['kill_executed']
            locked = self.engine.state['signals'].get('is_locked_today', False)
            
            # Metrics
            start_time = self.engine.state['status'].get('session_start_time')
            pos_count = len(self.engine.state['market']['positions'])
            last_err = self.engine.state['status'].get('error_message')

        # Update UI Rows
        self.row_api.update("CONNECTED" if api_connected else "DISCONNECTED", Theme.ACCENT_GREEN if api_connected else Theme.ACCENT_RED)
        self.row_ws.update("STREAMING" if ws_alive else "OFFLINE", Theme.ACCENT_GREEN if ws_alive else Theme.ACCENT_RED)
        self.row_engine.update("ACTIVE" if engine_active else "STOPPED", Theme.ACCENT_BLUE if engine_active else Theme.TEXT_GRAY)
        self.row_threads.update(f"{len(threads)} Running")

        self.row_mtm_logic.update("ENABLED" if mtm_enabled else "DISABLED", Theme.ACCENT_GREEN if mtm_enabled else Theme.TEXT_GRAY)
        self.row_sl_conf.update("REQUIRED" if sl_req else "DISABLED (Bypass)", Theme.ACCENT_ORANGE if sl_req else Theme.ACCENT_BLUE)
        self.row_sq_off.update("ENABLED" if sq_enabled else "DISABLED", Theme.ACCENT_BLUE if sq_enabled else Theme.TEXT_GRAY)
        self.row_hard_kill.update("ENABLED (Taskkill)" if hard_kill_enabled else "DISABLED", Theme.ACCENT_RED if hard_kill_enabled else Theme.TEXT_GRAY)
        self.row_email.update("REQUIRED" if email_verify else "DISABLED", Theme.ACCENT_GREEN if email_verify else Theme.TEXT_GRAY)
        self.row_stage.update(stage.upper())

        # Metrics
        uptime = "--:--:--"
        if engine_active and start_time:
            uptime = time.strftime('%H:%M:%S', time.gmtime(int(time.time() - start_time)))
        self.row_time.update(uptime)
        self.row_pos.update(str(pos_count))
        
        # Kill Status Logic
        ks_text, ks_col = "NOT TRIGGERED", Theme.TEXT_GRAY
        if locked: ks_text, ks_col = "LOCKED (DAILY)", Theme.ACCENT_RED
        elif executed: ks_text, ks_col = "EXECUTED", Theme.ACCENT_RED
        elif triggered: ks_text, ks_col = "TRIGGERED", Theme.ACCENT_ORANGE
        self.row_ks_status.update(ks_text, ks_col)
        
        self.row_err.update(str(last_err)[:35] if last_err else "None", Theme.ACCENT_RED if last_err else Theme.ACCENT_GREEN)

# =========================================================
#  PAGE: MAIN STATUS PAGE
# =========================================================
class StatusPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        self.engines = engines
        self._is_visible = False
        self.app_start_time = time.time()

        # --- HEADER (HUD) ---
        hud_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, height=80, border_width=1, border_color=Theme.BORDER)
        hud_frame.pack(fill="x", padx=20, pady=(20, 10))
        for i in range(4): hud_frame.grid_columnconfigure(i, weight=1)
        
        self.stat_spot = StatBox(hud_frame, "BANKNIFTY SPOT (WS)", "0.00", Theme.ACCENT_BLUE)
        self.stat_spot.grid(row=0, column=0, sticky="ew", padx=10, pady=15)
        
        self.stat_uptime = StatBox(hud_frame, "APP UPTIME", "00:00:00")
        self.stat_uptime.grid(row=0, column=1, sticky="ew", padx=10, pady=15)
        
        self.stat_threads = StatBox(hud_frame, "TOTAL THREADS", "0")
        self.stat_threads.grid(row=0, column=2, sticky="ew", padx=10, pady=15)
        
        self.stat_market = StatBox(hud_frame, "MARKET STATUS", "CHECKING...")
        self.stat_market.grid(row=0, column=3, sticky="ew", padx=10, pady=15)

        # --- USER TABS ---
        self.tab_view = ctk.CTkTabview(self, fg_color="transparent", segmented_button_selected_color=Theme.ACCENT_BLUE)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.tabs = {}
        for eng in engines:
            name = eng.state['sys']['config'].get('account_name', eng.user_id)
            self.tab_view.add(name)
            tab_content = UserStatusTab(self.tab_view.tab(name), eng)
            tab_content.pack(fill="both", expand=True)
            self.tabs[name] = tab_content

        self.update_loop()

    def update_loop(self):
        if self._is_visible:
            # 1. Update Global HUD
            # Pull Spot Price from the first engine that has it
            spot_price = 0.0
            for eng in self.engines:
                with eng.state['sys']['lock']:
                    val = eng.state['market'].get('index_spot', 0.0)
                    if val > 0:
                        spot_price = val
                        break
            self.stat_spot.update(f"{spot_price:,.2f}", Theme.ACCENT_GREEN if spot_price > 0 else Theme.ACCENT_RED)
            
            # Uptime & Threads
            elapsed = int(time.time() - self.app_start_time)
            self.stat_uptime.update(time.strftime('%H:%M:%S', time.gmtime(elapsed)))
            self.stat_threads.update(str(threading.active_count()))
            
            # Market Status
            now = datetime.datetime.now().time()
            if datetime.time(9, 15) <= now <= datetime.time(15, 30):
                self.stat_market.update("OPEN", Theme.ACCENT_GREEN)
            else:
                self.stat_market.update("CLOSED", Theme.ACCENT_ORANGE)

            # 2. Update Visible User Tab
            curr = self.tab_view.get()
            if curr in self.tabs:
                self.tabs[curr].update_telemetry()
        
        self.after(1000, self.update_loop)

    def pack(self, **kwargs):
        self._is_visible = True
        super().pack(**kwargs)

    def pack_forget(self):
        self._is_visible = False
        super().pack_forget()