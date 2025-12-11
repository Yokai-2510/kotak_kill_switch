import customtkinter as ctk
import time
import threading
import datetime
from gui.theme import Theme

# =========================================================
#  HELPER: MINI STAT WIDGET
# =========================================================
class StatBox(ctk.CTkFrame):
    def __init__(self, parent, label, value, color=Theme.TEXT_WHITE):
        super().__init__(parent, fg_color="transparent")
        
        self.lbl_title = ctk.CTkLabel(self, text=label, font=("Arial", 10, "bold"), text_color=Theme.TEXT_GRAY)
        self.lbl_title.pack(anchor="w", padx=10)
        
        self.lbl_val = ctk.CTkLabel(self, text=value, font=("Arial", 13, "bold"), text_color=color)
        self.lbl_val.pack(anchor="w", padx=10)

    def update(self, value, color=Theme.TEXT_WHITE):
        self.lbl_val.configure(text=value, text_color=color)


# =========================================================
#  COMPONENT: DETAILED ENGINE CARD
# =========================================================
class EngineDetailCard(ctk.CTkFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color=Theme.BG_CARD, corner_radius=8, border_width=1, border_color=Theme.BORDER)
        self.engine = engine
        self.user_id = engine.user_id
        
        # Grid Layout: 5 Columns
        for i in range(5): self.grid_columnconfigure(i, weight=1)

        # --- HEADER ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=5, sticky="ew", padx=15, pady=(15, 10))
        
        # Account Name
        cfg_name = self.engine.state['sys']['config'].get('account_name', self.user_id)
        name = cfg_name if cfg_name else self.user_id
        ctk.CTkLabel(header, text=name, font=("Arial", 14, "bold"), text_color=Theme.TEXT_WHITE).pack(side="left")
        
        # Status Badge (Top Right)
        self.lbl_badge = ctk.CTkLabel(header, text="● CHECKING", font=("Arial", 11, "bold"), text_color=Theme.TEXT_GRAY)
        self.lbl_badge.pack(side="right")

        # Divider
        ctk.CTkFrame(self, height=2, fg_color="#2a2a2a").grid(row=1, column=0, columnspan=5, sticky="ew", padx=15, pady=(0, 15))

        # --- ROW 1: HEALTH & INFRASTRUCTURE ---
        self._add_label(2, 0, "API CONNECTION")
        self.val_api = self._add_val(3, 0, "--")

        self._add_label(2, 1, "SESSION TIME")
        self.val_time = self._add_val(3, 1, "--")

        self._add_label(2, 2, "ACTIVE THREADS")
        self.val_threads = self._add_val(3, 2, "0")

        self._add_label(2, 3, "WATCHDOG STATUS")
        self.val_watch = self._add_val(3, 3, "--")

        self._add_label(2, 4, "LOCK STATUS")
        self.val_lock = self._add_val(3, 4, "--")

        # --- ROW 2: CONFIG & LOGIC STATE ---
        self._add_label(4, 0, "LAST TRIGGER") 
        self.val_hist = self._add_val(5, 0, "--")

        self._add_label(4, 1, "AUTO SQUARE OFF")
        self.val_sq = self._add_val(5, 1, "--")

        self._add_label(4, 2, "TRIGGER LOGIC")
        self.val_logic = self._add_val(5, 2, "--")

        self._add_label(4, 3, "CURRENT STAGE")
        self.val_stage = self._add_val(5, 3, "--")

        self._add_label(4, 4, "LAST ERROR")
        self.val_error = self._add_val(5, 4, "None", Theme.ACCENT_GREEN)

        # Padding
        ctk.CTkLabel(self, text="", height=10).grid(row=6, column=0)

    def _add_label(self, row, col, text):
        ctk.CTkLabel(self, text=text, font=("Arial", 10, "bold"), text_color=Theme.TEXT_GRAY).grid(row=row, column=col, sticky="w", padx=15, pady=(5, 0))

    def _add_val(self, row, col, text, color=Theme.TEXT_WHITE):
        lbl = ctk.CTkLabel(self, text=text, font=("Arial", 12), text_color=color)
        lbl.grid(row=row, column=col, sticky="w", padx=15, pady=(0, 10))
        return lbl

    def update_data(self):
        # 1. Thread-Safe Read
        with self.engine.state['sys']['lock']:
            config = self.engine.state['sys']['config']
            api = self.engine.state['sys']['api']
            active = self.engine.state['signals']['system_active']
            stage = self.engine.state['status'].get('stage', 'UNKNOWN')
            err = self.engine.state['status'].get('error_message')
            start_time = self.engine.state['status'].get('session_start_time')
            
            # Thread Tracking
            threads = self.engine.state['sys']['threads']
            
            # Lockout
            locked = self.engine.state['signals'].get('is_locked_today', False)
            
            # Sub-configs
            ks = config.get('kill_switch', {})
            hist = config.get('kill_history', {})

        # 2. Update Badge
        if locked:
            self.lbl_badge.configure(text="● LOCKED", text_color=Theme.ACCENT_RED)
        elif active and api:
            self.lbl_badge.configure(text="● ONLINE", text_color=Theme.ACCENT_GREEN)
        elif not active:
            self.lbl_badge.configure(text="● INACTIVE", text_color=Theme.TEXT_GRAY)
        else:
            self.lbl_badge.configure(text="● ERROR", text_color=Theme.ACCENT_RED)

        # 3. Update Row 1 (Health)
        
        # API
        if api: self.val_api.configure(text="CONNECTED", text_color=Theme.ACCENT_GREEN)
        else: self.val_api.configure(text="DISCONNECTED", text_color=Theme.TEXT_GRAY)

        # Time
        if start_time and active:
            elapsed = int(time.time() - start_time)
            self.val_time.configure(text=time.strftime('%H:%M:%S', time.gmtime(elapsed)))
        else:
            self.val_time.configure(text="--:--:--")

        # Threads
        t_count = len(threads)
        self.val_threads.configure(text=f"{t_count} Running", text_color=Theme.TEXT_WHITE if t_count > 0 else Theme.TEXT_GRAY)

        # Watchdog
        wd_alive = "Watchdog" in threads and threads["Watchdog"].is_alive()
        if active:
            self.val_watch.configure(text="HEALTHY" if wd_alive else "CRASHED", text_color=Theme.ACCENT_GREEN if wd_alive else Theme.ACCENT_RED)
        else:
            self.val_watch.configure(text="OFF", text_color=Theme.TEXT_GRAY)

        # Lock Status
        self.val_lock.configure(text="YES" if locked else "NO", text_color=Theme.ACCENT_RED if locked else Theme.ACCENT_GREEN)

        # 4. Update Row 2 (Logic)
        
        # History (UPDATED LOGIC)
        ts = hist.get('timestamp')
        verified = hist.get('verified')
        
        if ts:
            # Format: "2023-10-25 14:30:00" -> "14:30:00 (V)"
            try:
                time_only = ts.split(' ')[1]
            except:
                time_only = ts
                
            status_char = " (V)" if verified else " (?)"
            color = Theme.ACCENT_RED if verified else Theme.ACCENT_ORANGE
            self.val_hist.configure(text=f"{time_only}{status_char}", text_color=color)
        else:
            self.val_hist.configure(text="None", text_color=Theme.TEXT_GRAY)

        # Auto SQ
        sq_enabled = ks.get('auto_square_off', False)
        self.val_sq.configure(text="ON" if sq_enabled else "OFF", text_color=Theme.ACCENT_GREEN if sq_enabled else Theme.TEXT_GRAY)

        # Trigger Logic
        sl_conf = ks.get('sell_order_exit_confirmation', True)
        self.val_logic.configure(text="MTM + SL" if sl_conf else "MTM ONLY", text_color=Theme.ACCENT_BLUE)

        # Stage
        self.val_stage.configure(text=stage)

        # Error
        if err:
            short_err = (str(err)[:18] + '..') if len(str(err)) > 18 else str(err)
            self.val_error.configure(text=short_err, text_color=Theme.ACCENT_RED)
        else:
            self.val_error.configure(text="None", text_color=Theme.ACCENT_GREEN)


# =========================================================
#  PAGE: STATUS PAGE CONTAINER
# =========================================================
class StatusPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        self.engines = engines
        self._is_visible = False
        self._update_job = None
        self.app_start_time = time.time()

        # --- HEADER ---
        title = ctk.CTkLabel(self, text="System Health Telemetry", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE)
        title.pack(anchor="w", padx=20, pady=(20, 10))

        # --- HUD ---
        hud_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, height=80, border_width=1, border_color=Theme.BORDER)
        hud_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        for i in range(4): hud_frame.grid_columnconfigure(i, weight=1)
        
        self.stat_market = StatBox(hud_frame, "MARKET", "CLOSED", Theme.ACCENT_ORANGE)
        self.stat_market.grid(row=0, column=0, sticky="ew", padx=10, pady=15)
        
        self.stat_uptime = StatBox(hud_frame, "APP UPTIME", "00:00:00")
        self.stat_uptime.grid(row=0, column=1, sticky="ew", padx=10, pady=15)
        
        self.stat_threads = StatBox(hud_frame, "GLOBAL THREADS", "0")
        self.stat_threads.grid(row=0, column=2, sticky="ew", padx=10, pady=15)
        
        self.stat_gui = StatBox(hud_frame, "REFRESH", "1000ms")
        self.stat_gui.grid(row=0, column=3, sticky="ew", padx=10, pady=15)

        # --- CARDS SCROLL ---
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True)

        self.cards = []
        for eng in engines:
            card = EngineDetailCard(self.scroll_area, eng)
            card.pack(fill="x", padx=10, pady=5)
            self.cards.append(card)

        self.update_loop()

    def update_loop(self):
        if not self._is_visible: return

        # 1. Update HUD
        now = datetime.datetime.now().time()
        m_start = datetime.time(9, 15)
        m_end = datetime.time(15, 30)
        is_open = m_start <= now <= m_end
        self.stat_market.update("OPEN" if is_open else "CLOSED", Theme.ACCENT_GREEN if is_open else Theme.ACCENT_ORANGE)

        elapsed = int(time.time() - self.app_start_time)
        self.stat_uptime.update(time.strftime('%H:%M:%S', time.gmtime(elapsed)))

        self.stat_threads.update(str(threading.active_count()))

        # 2. Update Cards
        for card in self.cards:
            card.update_data()

        self._update_job = self.after(1000, self.update_loop)

    def pack(self, **kwargs):
        self._is_visible = True
        if self._update_job is None: self.update_loop()
        super().pack(**kwargs)

    def pack_forget(self):
        self._is_visible = False
        if self._update_job:
            self.after_cancel(self._update_job)
            self._update_job = None
        super().pack_forget()