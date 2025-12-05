import customtkinter as ctk
from gui.theme import Theme

# =========================================================
#  COMPONENT: GLOBAL STATISTICS HEADER (COMPACT LAYOUT)
# =========================================================
class GlobalStatCard(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color=Theme.BG_CARD, corner_radius=15, border_width=1, border_color=Theme.BORDER)
        self.engines = engines
        
        # MAIN LAYOUT: Single Column, 2 Rows
        # Row 0: Top Bar (P&L + Button)
        # Row 1: Metrics Grid
        self.grid_columnconfigure(0, weight=1)
        
        # --- ROW 0: TOP BAR (P&L Left, Kill Button Right) ---
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 5))
        
        # Left Side: P&L
        pnl_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        pnl_frame.pack(side="left")
        
        ctk.CTkLabel(pnl_frame, text="NET SYSTEM P&L", font=("Arial", 11, "bold"), text_color=Theme.ACCENT_BLUE).pack(anchor="w")
        self.lbl_mtm_val = ctk.CTkLabel(pnl_frame, text="₹ 0.00", font=("Arial", 48, "bold"), text_color=Theme.TEXT_WHITE)
        self.lbl_mtm_val.pack(anchor="w")

        # Right Side: Global Kill Button (Moved Up)
        self.btn_kill_all = ctk.CTkButton(
            top_bar, 
            text="GLOBAL KILL SWITCH", 
            font=("Arial", 14, "bold"),
            fg_color=Theme.ACCENT_RED, 
            hover_color="#991b1b",
            height=50, 
            width=200,
            corner_radius=8,
            command=self.trigger_global_kill
        )
        self.btn_kill_all.pack(side="right", anchor="center")

        # --- ROW 1: EXTENDED METRICS GRID (3x2) ---
        self.metrics_container = ctk.CTkFrame(self, fg_color="#141414", corner_radius=10, border_width=1, border_color="#2a2a2a")
        self.metrics_container.grid(row=1, column=0, sticky="ew", padx=25, pady=(15, 25))
        
        # Configure internal grid (3 Columns)
        self.metrics_container.grid_columnconfigure(0, weight=1)
        self.metrics_container.grid_columnconfigure(1, weight=1)
        self.metrics_container.grid_columnconfigure(2, weight=1)

        # Helper to create metric cells
        def create_metric(row, col, label, val_color=Theme.TEXT_WHITE):
            frame = ctk.CTkFrame(self.metrics_container, fg_color="transparent")
            frame.grid(row=row, column=col, sticky="nsew", padx=20, pady=12)
            
            lbl = ctk.CTkLabel(frame, text=label, font=("Arial", 10, "bold"), text_color=Theme.TEXT_GRAY)
            lbl.pack(anchor="w")
            
            val = ctk.CTkLabel(frame, text="-", font=("Arial", 15, "bold"), text_color=val_color)
            val.pack(anchor="w", pady=(2, 0))
            return val

        # -- Grid Content --
        # Row A
        self.lbl_cap = create_metric(0, 0, "TOTAL RISK CAP")
        self.lbl_util = create_metric(0, 1, "RISK UTILIZATION", Theme.ACCENT_ORANGE) # New Metric
        self.lbl_active = create_metric(0, 2, "ACTIVE ENGINES")
        
        # Row B
        self.lbl_worst = create_metric(1, 0, "WORST HIT", Theme.ACCENT_RED) # New Metric
        self.lbl_pos = create_metric(1, 1, "OPEN POSITIONS", Theme.ACCENT_BLUE)
        self.lbl_sl = create_metric(1, 2, "SL STATUS", Theme.ACCENT_GREEN)

    def trigger_global_kill(self):
        """Intelligent Kill Logic"""
        kill_count = 0
        for eng in self.engines:
            # Check Config Enabled
            is_active = eng.state['sys']['config'].get('account_active', False)
            if not is_active: continue
            
            # Check Runtime State (Only kill if currently RUNNING or KILLING)
            with eng.state['sys']['lock']:
                stage = eng.state['status'].get('stage')
                if stage in ["RUNNING", "KILLING"]:
                    eng.state['signals']['trigger_kill'] = True
                    kill_count += 1

        if kill_count > 0:
            self.btn_kill_all.configure(text=f"ENGAGING ({kill_count})...", fg_color=Theme.ACCENT_ORANGE)
        else:
            # Visual feedback for useless click
            self.btn_kill_all.configure(text="NO ACTIVE TARGETS", fg_color="#4b5563")
            # The update loop will reset this text shortly

    def update(self):
        total_mtm = 0.0
        total_limit = 0.0
        active_count = 0
        sl_hit_count = 0
        total_positions = 0
        total_engines = len(self.engines)
        
        worst_mtm = 999999999
        worst_user = "None"
        
        # Track if we have ANY running engines (for button state)
        any_running = False
        
        for eng in self.engines:
            is_active = eng.state['sys']['config'].get('account_active', False)
            if not is_active: continue
            
            with eng.state['sys']['lock']:
                mtm = eng.state['risk']['mtm_current']
                limit = eng.state['risk']['mtm_limit']
                sl_hit = eng.state['risk']['sl_hit_status']
                pos_count = len(eng.state['market']['positions'])
                stage = eng.state['status'].get('stage')
                
                total_mtm += mtm
                total_limit += limit
                total_positions += pos_count
                
                if sl_hit: sl_hit_count += 1
                if stage == "RUNNING": 
                    active_count += 1
                    any_running = True
                
                # Logic: Find worst performer
                if mtm < worst_mtm:
                    worst_mtm = mtm
                    cfg_name = eng.state['sys']['config'].get('account_name', '')
                    worst_user = cfg_name if cfg_name else eng.user_id
        
        # 1. P&L Display
        color = Theme.ACCENT_GREEN if total_mtm >= 0 else Theme.ACCENT_RED
        self.lbl_mtm_val.configure(text=f"₹ {total_mtm:,.2f}", text_color=color)
        
        # 2. Metrics Updates
        self.lbl_cap.configure(text=f"₹ {total_limit:,.0f}")
        self.lbl_pos.configure(text=str(total_positions))
        self.lbl_active.configure(text=f"{active_count}/{total_engines} Online")
        
        # 3. New: Risk Utilization %
        if total_limit != 0:
            util_pct = (abs(min(total_mtm, 0)) / abs(total_limit)) * 100
            self.lbl_util.configure(text=f"{util_pct:.1f}% Used")
            self.lbl_util.configure(text_color=Theme.ACCENT_RED if util_pct > 80 else Theme.ACCENT_ORANGE if util_pct > 50 else Theme.ACCENT_BLUE)
        else:
            self.lbl_util.configure(text="0%", text_color=Theme.TEXT_GRAY)

        # 4. New: Worst Hit
        if worst_mtm < 0:
            short_name = (worst_user[:12] + '..') if len(worst_user) > 12 else worst_user
            self.lbl_worst.configure(text=f"{short_name} (₹{worst_mtm:.0f})", text_color=Theme.ACCENT_RED)
        else:
            self.lbl_worst.configure(text="None", text_color=Theme.ACCENT_GREEN)

        # 5. SL Status
        if sl_hit_count > 0:
            self.lbl_sl.configure(text=f"{sl_hit_count} HITS DETECTED", text_color=Theme.ACCENT_RED)
        else:
            self.lbl_sl.configure(text="ALL SAFE", text_color=Theme.ACCENT_GREEN)

        # 6. Button State (Auto-Manage)
        # Check current text to allow "ENGAGING" to persist for a split second
        current_text = self.btn_kill_all.cget("text")
        if "ENGAGING" in current_text and any_running: return

        if any_running:
            self.btn_kill_all.configure(text="GLOBAL KILL SWITCH", state="normal", fg_color=Theme.ACCENT_RED, text_color=Theme.TEXT_WHITE)
        else:
            self.btn_kill_all.configure(text="ALL SYSTEMS STOPPED", state="disabled", fg_color="#2a2a2a", text_color=Theme.TEXT_GRAY)


# =========================================================
#  COMPONENT: ACCOUNT CARD
# =========================================================
class AccountCard(ctk.CTkFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        self.engine = engine
        self.user_id = engine.user_id
        self.current_stage = None 
        
        self.grid_columnconfigure(1, weight=1)

        # 1. Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(20, 10))
        
        # Name
        cfg_name = self.engine.state['sys']['config'].get('account_name', '')
        display_name = cfg_name if cfg_name else self.user_id
        self.lbl_name = ctk.CTkLabel(header_frame, text=display_name, font=Theme.FONT_TITLE, text_color=Theme.TEXT_WHITE)
        self.lbl_name.pack(side="left")
        
        # Status
        self.lbl_status = ctk.CTkLabel(header_frame, text="OFFLINE", font=("Arial", 10, "bold"), text_color=Theme.TEXT_GRAY)
        self.lbl_status.pack(side="right")

        ctk.CTkFrame(self, height=2, fg_color="#2a2a2a").grid(row=1, column=0, columnspan=2, sticky="ew", padx=20)

        # 2. Metrics
        metrics_frame = ctk.CTkFrame(self, fg_color="transparent")
        metrics_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=20, pady=15)
        metrics_frame.grid_columnconfigure(1, weight=1)

        # MTM
        ctk.CTkLabel(metrics_frame, text="Current MTM", font=Theme.FONT_SMALL, text_color=Theme.TEXT_GRAY).grid(row=0, column=0, sticky="w", pady=2)
        self.lbl_mtm = ctk.CTkLabel(metrics_frame, text="₹ 0.00", font=Theme.FONT_NUM, text_color=Theme.TEXT_WHITE)
        self.lbl_mtm.grid(row=0, column=1, sticky="e", pady=2)

        # Limit
        ctk.CTkLabel(metrics_frame, text="MTM Limit", font=Theme.FONT_SMALL, text_color=Theme.TEXT_GRAY).grid(row=1, column=0, sticky="w", pady=2)
        self.lbl_limit = ctk.CTkLabel(metrics_frame, text="₹ 0.00", font=("Arial", 14), text_color=Theme.TEXT_GRAY)
        self.lbl_limit.grid(row=1, column=1, sticky="e", pady=2)

        # Sell Leg
        ctk.CTkLabel(metrics_frame, text="Sell Leg", font=Theme.FONT_SMALL, text_color=Theme.TEXT_GRAY).grid(row=2, column=0, sticky="w", pady=2)
        self.lbl_leg_status = ctk.CTkLabel(metrics_frame, text="OPEN", font=("Arial", 12, "bold"), text_color=Theme.ACCENT_GREEN)
        self.lbl_leg_status.grid(row=2, column=1, sticky="e", pady=2)

        # 3. Risk Meter
        self.progress = ctk.CTkProgressBar(self, height=6, corner_radius=3, progress_color=Theme.ACCENT_BLUE, fg_color="#2a2a2a")
        self.progress.grid(row=3, column=0, columnspan=2, sticky="ew", padx=20, pady=(5, 15))
        self.progress.set(0.0)

        # 4. Controls
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=4, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        self.btn_kill = ctk.CTkButton(
            btn_frame, text="KILL", 
            fg_color="#252525", border_width=1, border_color=Theme.ACCENT_RED, text_color=Theme.ACCENT_RED, 
            hover_color="#3f1313", height=40,
            command=self.trigger_kill
        )
        self.btn_kill.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        self.btn_pause = ctk.CTkButton(
            btn_frame, text="PAUSE", 
            fg_color="#252525", border_width=1, border_color="#4b5563", text_color="#d1d5db", 
            hover_color="#374151", height=40,
            command=self.toggle_pause
        )
        self.btn_pause.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def trigger_kill(self):
        self.btn_kill.configure(text="PROCESSING...", state="disabled", border_color=Theme.ACCENT_ORANGE, text_color=Theme.ACCENT_ORANGE)
        with self.engine.state['sys']['lock']:
            self.engine.state['signals']['trigger_kill'] = True

    def toggle_pause(self):
        with self.engine.state['sys']['lock']:
            curr = self.engine.state['sys']['config']['kill_switch'].get('enabled', False)
            self.engine.state['sys']['config']['kill_switch']['enabled'] = not curr

    def update_data(self):
        with self.engine.state['sys']['lock']:
            is_active = self.engine.state['sys']['config'].get('account_active', False)
            kill_enabled = self.engine.state['sys']['config']['kill_switch'].get('enabled', False)
            mtm = self.engine.state['risk']['mtm_current']
            limit = self.engine.state['risk']['mtm_limit']
            sl_hit = self.engine.state['risk']['sl_hit_status']
            stage = self.engine.state['status'].get('stage', 'INIT')
            sys_active = self.engine.state['signals']['system_active']
            raw_name = self.engine.state['sys']['config'].get('account_name', '')
            
        if raw_name: self.lbl_name.configure(text=raw_name)

        if not is_active:
            status = "ACCOUNT DISABLED"
            col = Theme.TEXT_GRAY
            border_col = Theme.BORDER
            self.btn_pause.configure(text="PAUSE", state="disabled", border_color=Theme.BORDER, text_color=Theme.TEXT_GRAY)
            self.btn_kill.configure(state="disabled", border_color=Theme.BORDER, text_color=Theme.TEXT_GRAY)
            
        elif stage == "KILLED":
            status = "TRADING TERMINATED"
            col = Theme.ACCENT_RED
            border_col = Theme.ACCENT_RED
            self.btn_kill.configure(text="TERMINATED", state="disabled", border_color="#3f1313", text_color="#3f1313")
            self.btn_pause.configure(state="disabled")
            
        elif stage == "KILLING":
            status = "KILL SWITCH ENGAGED"
            col = Theme.ACCENT_ORANGE
            border_col = Theme.ACCENT_ORANGE
            self.btn_kill.configure(text="PROCESSING...", state="disabled", border_color=Theme.ACCENT_ORANGE, text_color=Theme.ACCENT_ORANGE)
            
        elif not kill_enabled:
            status = "KILL SWITCH PAUSED"
            col = Theme.ACCENT_BLUE
            border_col = Theme.ACCENT_BLUE
            self.btn_pause.configure(text="RESUME", state="normal", border_color=Theme.ACCENT_BLUE, text_color=Theme.ACCENT_BLUE)
            self.btn_kill.configure(state="disabled")
            
        elif stage == "RUNNING":
            status = "MONITORING ACTIVE"
            col = Theme.ACCENT_GREEN
            border_col = Theme.ACCENT_GREEN
            self.btn_pause.configure(text="PAUSE", state="normal", border_color="#4b5563", text_color="#d1d5db")
            self.btn_kill.configure(text="KILL", state="normal", border_color=Theme.ACCENT_RED, text_color=Theme.ACCENT_RED)
            
        elif stage == "ERROR":
            status = "SYSTEM ERROR"
            col = Theme.ACCENT_RED
            border_col = Theme.ACCENT_RED
            
        elif not sys_active:
            status = "MONITORING STOPPED"
            col = Theme.TEXT_GRAY
            border_col = Theme.BORDER
            
        else:
            status = f"● {stage}"
            col = Theme.TEXT_GRAY
            border_col = Theme.BORDER

        self.lbl_status.configure(text=f"● {status}", text_color=col)
        self.configure(border_color=border_col)

        self.lbl_mtm.configure(text=f"₹ {mtm:,.2f}", text_color=Theme.ACCENT_GREEN if mtm >= 0 else Theme.ACCENT_RED)
        self.lbl_limit.configure(text=f"Max: ₹ {limit:,.0f}")

        if sl_hit: self.lbl_leg_status.configure(text="CLOSED (SL HIT)", text_color=Theme.ACCENT_ORANGE)
        else: self.lbl_leg_status.configure(text="OPEN", text_color=Theme.ACCENT_GREEN)

        ratio = 0.0
        if limit < 0 and mtm < 0:
            ratio = min(abs(mtm) / abs(limit), 1.0)
        self.progress.set(ratio)
        if ratio > 0.8: self.progress.configure(progress_color=Theme.ACCENT_RED)
        else: self.progress.configure(progress_color=Theme.ACCENT_BLUE)


# =========================================================
#  PAGE: DASHBOARD CONTAINER
# =========================================================
class DashboardPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        self.engines = engines
        
        self.header = GlobalStatCard(self, engines)
        self.header.pack(fill="x", padx=0, pady=(0, 10))

        self.grid_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.grid_area.pack(fill="both", expand=True)
        
        self.grid_area.grid_columnconfigure(0, weight=1)
        self.grid_area.grid_columnconfigure(1, weight=1)
        self.grid_area.grid_columnconfigure(2, weight=1)

        self.cards = []
        for i, eng in enumerate(engines):
            card = AccountCard(self.grid_area, eng)
            row, col = divmod(i, 3)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            self.cards.append(card)

        self.update_loop()

    def update_loop(self):
        try:
            self.header.update()
            for card in self.cards:
                card.update_data()
        except Exception: pass
        self.after(500, self.update_loop)