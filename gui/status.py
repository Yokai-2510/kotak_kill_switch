import customtkinter as ctk
import time
import threading
import datetime
from gui.theme import Theme

# =========================================================
#  HELPER: MINI STAT WIDGET (Label + Value)
# =========================================================
class StatBox(ctk.CTkFrame):
    def __init__(self, parent, label, value, color=Theme.TEXT_WHITE):
        # Removed internal packing to let parent control layout via Grid
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
        
        # Layout: Header + 2 Rows of Metrics
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_columnconfigure(4, weight=1)

        # --- HEADER ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=5, sticky="ew", padx=15, pady=(15, 10))
        
        # Name
        cfg_name = self.engine.state['sys']['config'].get('account_name', self.user_id)
        name = cfg_name if cfg_name else self.user_id
        ctk.CTkLabel(header, text=name, font=("Arial", 14, "bold"), text_color=Theme.TEXT_WHITE).pack(side="left")
        
        # Status Badge (Top Right)
        self.lbl_badge = ctk.CTkLabel(header, text="● CHECKING", font=("Arial", 11, "bold"), text_color=Theme.TEXT_GRAY)
        self.lbl_badge.pack(side="right")

        # Divider
        ctk.CTkFrame(self, height=2, fg_color="#2a2a2a").grid(row=1, column=0, columnspan=5, sticky="ew", padx=15, pady=(0, 15))

        # --- ROW 1: CONNECTION & HEALTH ---
        self._add_label(2, 0, "API STATUS")
        self.val_api = self._add_val(3, 0, "--")

        self._add_label(2, 1, "DATA HEARTBEAT")
        self.val_beat = self._add_val(3, 1, "--")

        self._add_label(2, 2, "ACTIVE THREADS")
        self.val_threads = self._add_val(3, 2, "0")

        self._add_label(2, 3, "POLL RATE")
        self.val_poll = self._add_val(3, 3, "--")

        self._add_label(2, 4, "SYSTEM LOCK")
        self.val_lock = self._add_val(3, 4, "--")

        # --- ROW 2: CONFIG & LOGIC ---
        self._add_label(4, 0, "KILL MODE")
        self.val_mode = self._add_val(5, 0, "--")

        self._add_label(4, 1, "AUTO SQ OFF")
        self.val_sq = self._add_val(5, 1, "--")

        self._add_label(4, 2, "TRIGGER LOGIC")
        self.val_logic = self._add_val(5, 2, "--")

        self._add_label(4, 3, "CURRENT STAGE")
        self.val_stage = self._add_val(5, 3, "--")

        self._add_label(4, 4, "LAST ERROR")
        self.val_error = self._add_val(5, 4, "None", Theme.ACCENT_GREEN)

        # Add padding at bottom
        ctk.CTkLabel(self, text="", height=10).grid(row=6, column=0)

    def _add_label(self, row, col, text):
        ctk.CTkLabel(self, text=text, font=("Arial", 10, "bold"), text_color=Theme.TEXT_GRAY).grid(row=row, column=col, sticky="w", padx=15, pady=(5, 0))

    def _add_val(self, row, col, text, color=Theme.TEXT_WHITE):
        lbl = ctk.CTkLabel(self, text=text, font=("Arial", 12), text_color=color)
        lbl.grid(row=row, column=col, sticky="w", padx=15, pady=(0, 10))
        return lbl

    def update_data(self):
        # 1. READ DATA
        with self.engine.state['sys']['lock']:
            config = self.engine.state['sys']['config']
            api = self.engine.state['sys']['api']
            active = self.engine.state['signals']['system_active']
            stage = self.engine.state['status'].get('stage', 'UNKNOWN')
            err = self.engine.state['status'].get('error_message')
            
            # Derived
            ks = config.get('kill_switch', {})
            mon = config.get('monitoring', {})
            
        # 2. STATUS BADGE
        if active and api:
            self.lbl_badge.configure(text="● ONLINE", text_color=Theme.ACCENT_GREEN)
        elif not active:
            self.lbl_badge.configure(text="● INACTIVE", text_color=Theme.TEXT_GRAY)
        else:
            self.lbl_badge.configure(text="● ERROR", text_color=Theme.ACCENT_RED)

        # 3. METRICS UPDATE
        
        # API Status
        if api: self.val_api.configure(text="CONNECTED", text_color=Theme.ACCENT_GREEN)
        else: self.val_api.configure(text="DISCONNECTED", text_color=Theme.ACCENT_RED)

        # Heartbeat (Last updated time from status)
        if active and api:
            self.val_beat.configure(text="LIVE (<1s)", text_color=Theme.ACCENT_GREEN)
        else:
            self.val_beat.configure(text="STALE", text_color=Theme.TEXT_GRAY)

        # Threads
        t_count = sum(1 for t in threading.enumerate() if t.name.startswith(self.engine.user_id))
        self.val_threads.configure(text=f"{t_count} Active", text_color=Theme.TEXT_WHITE if t_count > 0 else Theme.TEXT_GRAY)

        # Poll Rate
        poll = mon.get('poll_interval_seconds', 2)
        self.val_poll.configure(text=f"{poll} sec")

        # System Lock
        self.val_lock.configure(text="ENGAGED" if active else "RELEASED", text_color=Theme.ACCENT_BLUE if active else Theme.TEXT_GRAY)

        # Row 2
        # Kill Mode
        mode = ks.get('execution_mode', 'kill_only')
        dry = ks.get('dry_run', False) # Fallback check
        # Override visual if config says dry_run directly or via execution_mode
        is_dry = dry or mode == "dry_run"
        
        mode_text = "DRY RUN" if is_dry else "LIVE KILL"
        self.val_mode.configure(text=mode_text, text_color=Theme.ACCENT_ORANGE if is_dry else Theme.ACCENT_RED)

        # Auto SQ
        sq = ks.get('auto_square_off', False)
        self.val_sq.configure(text="ENABLED" if sq else "DISABLED", text_color=Theme.ACCENT_GREEN if sq else Theme.TEXT_GRAY)

        # Logic
        sl_req = ks.get('trigger_on_sl_hit', False)
        self.val_logic.configure(text="MTM + SL EXIT" if sl_req else "MTM ONLY (PANIC)", text_color=Theme.ACCENT_BLUE)

        # Stage
        self.val_stage.configure(text=stage)

        # Error
        if err:
            short_err = (err[:20] + '..') if len(err) > 20 else err
            self.val_error.configure(text=short_err, text_color=Theme.ACCENT_RED)
        else:
            self.val_error.configure(text="None", text_color=Theme.ACCENT_GREEN)


# =========================================================
#  PAGE: SYSTEM STATUS CONTAINER
# =========================================================
class StatusPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        self.engines = engines
        self._is_visible = False
        self._update_job = None
        self.start_time = time.time()

        # --- HEADER ---
        title = ctk.CTkLabel(self, text="System Health Telemetry", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE)
        title.pack(anchor="w", padx=20, pady=(20, 10))

        # --- TOP HUD (GLOBAL METRICS) ---
        hud_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, height=80, border_width=1, border_color=Theme.BORDER)
        hud_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Grid Layout for Perfect Alignment (4 Columns)
        hud_frame.grid_columnconfigure(0, weight=1)
        hud_frame.grid_columnconfigure(1, weight=1)
        hud_frame.grid_columnconfigure(2, weight=1)
        hud_frame.grid_columnconfigure(3, weight=1)
        
        # Stat Boxes positioned via Grid
        self.stat_market = StatBox(hud_frame, "MARKET HOURS", "CLOSED", Theme.ACCENT_ORANGE)
        self.stat_market.grid(row=0, column=0, sticky="ew", padx=10, pady=15)
        
        self.stat_uptime = StatBox(hud_frame, "SESSION UPTIME", "00:00:00")
        self.stat_uptime.grid(row=0, column=1, sticky="ew", padx=10, pady=15)
        
        self.stat_threads = StatBox(hud_frame, "GLOBAL THREADS", "0")
        self.stat_threads.grid(row=0, column=2, sticky="ew", padx=10, pady=15)
        
        self.stat_gui = StatBox(hud_frame, "GUI REFRESH", "1000ms")
        self.stat_gui.grid(row=0, column=3, sticky="ew", padx=10, pady=15)

        # --- SCROLLABLE AREA FOR ENGINES ---
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
        # Market Status
        now = datetime.datetime.now().time()
        m_start = datetime.time(9, 15)
        m_end = datetime.time(15, 30)
        is_open = m_start <= now <= m_end
        self.stat_market.update("OPEN" if is_open else "CLOSED", Theme.ACCENT_GREEN if is_open else Theme.ACCENT_ORANGE)

        # Uptime
        elapsed = int(time.time() - self.start_time)
        self.stat_uptime.update(time.strftime('%H:%M:%S', time.gmtime(elapsed)))

        # Global Threads
        self.stat_threads.update(str(threading.active_count()))

        # 2. Update Engine Cards
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