import customtkinter as ctk
from gui.theme import Theme

# =========================================================
#  COMPONENT: GLOBAL STATISTICS HEADER
# =========================================================
class GlobalStatCard(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color=Theme.BG_CARD, corner_radius=15, border_width=1, border_color=Theme.BORDER)
        self.engines = engines
        
        self.grid_columnconfigure(0, weight=1)
        
        # --- ROW 0: TOP BAR ---
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.grid(row=0, column=0, sticky="ew", padx=25, pady=(20, 5))
        
        # Left: Net P&L
        pnl_frame = ctk.CTkFrame(top_bar, fg_color="transparent")
        pnl_frame.pack(side="left")
        ctk.CTkLabel(pnl_frame, text="NET SYSTEM P&L", font=("Arial", 11, "bold"), text_color=Theme.ACCENT_BLUE).pack(anchor="w")
        self.lbl_mtm_val = ctk.CTkLabel(pnl_frame, text="₹ 0.00", font=("Arial", 48, "bold"), text_color=Theme.TEXT_WHITE)
        self.lbl_mtm_val.pack(anchor="w")

        # Right: Controls (Grouped)
        btn_group = ctk.CTkFrame(top_bar, fg_color="transparent")
        btn_group.pack(side="right", anchor="center")

        # 1. Stop All Button
        self.btn_stop_all = ctk.CTkButton(
            btn_group,
            text="STOP ALL ENGINES",
            font=("Arial", 12, "bold"),
            fg_color="#4b5563",
            hover_color="#374151",
            height=50,
            width=160,
            corner_radius=8,
            command=self.stop_all_engines
        )
        self.btn_stop_all.pack(side="left", padx=(0, 10))

        # 2. Global Kill Button
        self.btn_kill_all = ctk.CTkButton(
            btn_group, 
            text="GLOBAL KILL SWITCH", 
            font=("Arial", 14, "bold"),
            fg_color=Theme.ACCENT_RED, 
            hover_color="#991b1b",
            height=50, 
            width=220,
            corner_radius=8,
            command=self.trigger_global_kill
        )
        self.btn_kill_all.pack(side="left")

        # --- ROW 1: METRICS GRID ---
        self.metrics_container = ctk.CTkFrame(self, fg_color="#141414", corner_radius=10, border_width=1, border_color="#2a2a2a")
        self.metrics_container.grid(row=1, column=0, sticky="ew", padx=25, pady=(15, 25))
        
        for i in range(3): self.metrics_container.grid_columnconfigure(i, weight=1)

        # Essential Metrics
        self.lbl_cap = self._create_metric(0, 0, "TOTAL RISK CAP")
        self.lbl_util = self._create_metric(0, 1, "RISK UTILIZATION", Theme.ACCENT_ORANGE)
        self.lbl_active = self._create_metric(0, 2, "ACTIVE ACCOUNTS") # Renamed
        
        self.lbl_pos = self._create_metric(1, 0, "TOTAL POSITIONS", Theme.ACCENT_BLUE)
        self.lbl_ord = self._create_metric(1, 1, "PENDING ORDERS", Theme.TEXT_WHITE)
        self.lbl_sl = self._create_metric(1, 2, "SL PROTECTION", Theme.ACCENT_GREEN)

    def _create_metric(self, row, col, label, val_color=Theme.TEXT_WHITE):
        frame = ctk.CTkFrame(self.metrics_container, fg_color="transparent")
        frame.grid(row=row, column=col, sticky="nsew", padx=20, pady=12)
        ctk.CTkLabel(frame, text=label, font=("Arial", 10, "bold"), text_color=Theme.TEXT_GRAY).pack(anchor="w")
        val = ctk.CTkLabel(frame, text="-", font=("Arial", 15, "bold"), text_color=val_color)
        val.pack(anchor="w", pady=(2, 0))
        return val

    def stop_all_engines(self):
        """Disconnects all active engines."""
        for eng in self.engines:
            if eng.state['signals']['system_active']:
                eng.stop_session()

    def trigger_global_kill(self):
        """Intelligent Global Kill."""
        kill_count = 0
        for eng in self.engines:
            with eng.state['sys']['lock']:
                sys_active = eng.state['signals']['system_active']
                killed = eng.state['signals']['kill_executed']
                locked = eng.state['signals'].get('is_locked_today', False)
                
                if sys_active and not killed and not locked:
                    eng.state['signals']['trigger_kill'] = True
                    kill_count += 1
        
        if kill_count > 0:
            self.btn_kill_all.configure(text=f"ENGAGING ({kill_count})...", fg_color=Theme.ACCENT_ORANGE)

    def update(self):
        total_mtm = 0.0
        total_limit = 0.0
        active_count = 0
        sl_hit_count = 0
        total_positions = 0
        total_pending = 0
        killable_targets = 0
        
        for eng in self.engines:
            with eng.state['sys']['lock']:
                mtm = eng.state['risk']['mtm_current']
                limit = eng.state['risk']['mtm_limit']
                sl_hit = eng.state['risk']['sl_hit_status']
                positions = eng.state['market']['positions']
                orders = eng.state['market']['orders']
                sys_active = eng.state['signals']['system_active']
                killed = eng.state['signals']['kill_executed']
                locked = eng.state['signals'].get('is_locked_today', False)
                
                total_mtm += mtm
                total_limit += limit
                total_positions += len(positions)
                
                pending = sum(1 for o in orders if o.get('status') in ['OPEN', 'TRIGGER PENDING'])
                total_pending += pending
                
                if sl_hit: sl_hit_count += 1
                if sys_active: 
                    active_count += 1
                    if not killed and not locked: killable_targets += 1
        
        # UI Updates
        color = Theme.ACCENT_GREEN if total_mtm >= 0 else Theme.ACCENT_RED
        self.lbl_mtm_val.configure(text=f"₹ {total_mtm:,.2f}", text_color=color)
        
        self.lbl_cap.configure(text=f"₹ {total_limit:,.0f}")
        self.lbl_pos.configure(text=str(total_positions))
        self.lbl_ord.configure(text=str(total_pending))
        self.lbl_active.configure(text=f"{active_count}/{len(self.engines)} Online")
        
        if total_limit != 0:
            util_pct = (abs(min(total_mtm, 0)) / abs(total_limit)) * 100
            self.lbl_util.configure(text=f"{util_pct:.1f}%")
            self.lbl_util.configure(text_color=Theme.ACCENT_RED if util_pct > 80 else Theme.ACCENT_ORANGE if util_pct > 50 else Theme.ACCENT_BLUE)
        else:
            self.lbl_util.configure(text="0%", text_color=Theme.TEXT_GRAY)

        if sl_hit_count > 0:
            self.lbl_sl.configure(text=f"{sl_hit_count} HITS", text_color=Theme.ACCENT_RED)
        else:
            self.lbl_sl.configure(text="ALL SAFE", text_color=Theme.ACCENT_GREEN)

        # Global Kill Button State
        current_text = self.btn_kill_all.cget("text")
        if "ENGAGING" in current_text and killable_targets > 0: pass
        elif killable_targets > 0:
            self.btn_kill_all.configure(text="GLOBAL KILL SWITCH", state="normal", fg_color=Theme.ACCENT_RED)
        else:
            self.btn_kill_all.configure(text="NO ACTIVE TARGETS", state="disabled", fg_color="#2a2a2a")

        # Stop All Button State
        if active_count > 0:
            self.btn_stop_all.configure(state="normal", fg_color="#4b5563")
        else:
            self.btn_stop_all.configure(state="disabled", fg_color="#2a2a2a")


# =========================================================
#  COMPONENT: ACCOUNT CARD
# =========================================================
class AccountCard(ctk.CTkFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color=Theme.BG_CARD, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        self.engine = engine
        self.user_id = engine.user_id
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)

        # 1. Header Row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=3, sticky="ew", padx=15, pady=(15, 10))
        
        cfg_name = self.engine.state['sys']['config'].get('account_name', '')
        display_name = cfg_name if cfg_name else self.user_id
        
        self.lbl_name = ctk.CTkLabel(header, text=display_name, font=("Arial", 13, "bold"), text_color=Theme.TEXT_WHITE)
        self.lbl_name.pack(side="left")
        
        self.lbl_status = ctk.CTkLabel(header, text="OFFLINE", font=("Arial", 10, "bold"), text_color=Theme.TEXT_GRAY)
        self.lbl_status.pack(side="right")

        # Divider
        ctk.CTkFrame(self, height=2, fg_color="#2a2a2a").grid(row=1, column=0, columnspan=3, sticky="ew", padx=15, pady=(0, 15))

        # 2. Main MTM
        self.lbl_mtm = ctk.CTkLabel(self, text="₹ 0.00", font=("Arial", 28, "bold"), text_color=Theme.TEXT_WHITE)
        self.lbl_mtm.grid(row=2, column=0, columnspan=3, pady=(0, 5))
        
        self.progress = ctk.CTkProgressBar(self, height=4, corner_radius=2, progress_color=Theme.ACCENT_BLUE, fg_color="#2a2a2a")
        self.progress.grid(row=3, column=0, columnspan=3, sticky="ew", padx=30, pady=(0, 20))
        self.progress.set(0.0)

        # 3. Stats Grid
        self._add_stat(4, 0, "RISK LIMIT", "₹ 0")
        self.lbl_limit = self.last_val_label
        
        self._add_stat(4, 1, "POSITIONS", "0")
        self.lbl_pos_count = self.last_val_label
        
        self._add_stat(4, 2, "SL STATUS", "SAFE")
        self.lbl_sl_status = self.last_val_label

        # 4. Control Row
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=15, pady=(20, 20))
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)

        # Pause Logic
        self.btn_pause = ctk.CTkButton(
            btn_frame, text="PAUSE", height=35,
            fg_color="#252525", border_width=1, border_color="#4b5563", text_color="#d1d5db", 
            hover_color="#374151", font=("Arial", 11, "bold"),
            command=self.toggle_pause
        )
        self.btn_pause.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Kill Switch (Updated Styling)
        self.btn_kill = ctk.CTkButton(
            btn_frame, text="KILL", height=35,
            fg_color="#252525", 
            border_width=1, 
            border_color=Theme.ACCENT_RED, 
            text_color=Theme.ACCENT_RED, 
            hover_color="#3f1313", 
            font=("Arial", 11, "bold"),
            command=self.trigger_kill
        )
        self.btn_kill.grid(row=0, column=1, sticky="ew", padx=(5, 0))

    def _add_stat(self, r, c, title, val):
        f = ctk.CTkFrame(self, fg_color="transparent")
        f.grid(row=r, column=c)
        ctk.CTkLabel(f, text=title, font=("Arial", 9, "bold"), text_color=Theme.TEXT_GRAY).pack()
        l = ctk.CTkLabel(f, text=val, font=("Arial", 12, "bold"), text_color=Theme.TEXT_WHITE)
        l.pack()
        self.last_val_label = l

    def toggle_pause(self):
        with self.engine.state['sys']['lock']:
            curr = self.engine.state['sys']['config']['kill_switch'].get('enabled', False)
            self.engine.state['sys']['config']['kill_switch']['enabled'] = not curr

    def trigger_kill(self):
        self.btn_kill.configure(text="...", state="disabled")
        with self.engine.state['sys']['lock']:
            self.engine.state['signals']['trigger_kill'] = True

    def update_data(self):
        with self.engine.state['sys']['lock']:
            mtm = self.engine.state['risk']['mtm_current']
            limit = self.engine.state['risk']['mtm_limit']
            sl_hit = self.engine.state['risk']['sl_hit_status']
            stage = self.engine.state['status'].get('stage', 'INIT')
            sys_active = self.engine.state['signals']['system_active']
            locked = self.engine.state['signals'].get('is_locked_today', False)
            positions = len(self.engine.state['market']['positions'])
            ks_enabled = self.engine.state['sys']['config']['kill_switch'].get('enabled', False)
            
            raw_name = self.engine.state['sys']['config'].get('account_name', '')
            if raw_name: self.lbl_name.configure(text=raw_name)

        # 1. Update Metrics
        self.lbl_mtm.configure(text=f"₹ {mtm:,.2f}", text_color=Theme.ACCENT_GREEN if mtm >= 0 else Theme.ACCENT_RED)
        self.lbl_limit.configure(text=f"₹ {limit:,.0f}")
        self.lbl_pos_count.configure(text=str(positions))
        
        if sl_hit:
            self.lbl_sl_status.configure(text="HIT!", text_color=Theme.ACCENT_ORANGE)
        else:
            self.lbl_sl_status.configure(text="SAFE", text_color=Theme.ACCENT_GREEN)

        ratio = 0.0
        if limit < 0 and mtm < 0: ratio = min(abs(mtm) / abs(limit), 1.0)
        self.progress.set(ratio)
        self.progress.configure(progress_color=Theme.ACCENT_RED if ratio > 0.8 else Theme.ACCENT_BLUE)

        # 2. Update Controls & Status Text
        if locked:
            status_text = "LOCKED"
            status_col = Theme.ACCENT_RED
            if "VERIFIED" in stage: status_text = "KILLED (VERIFIED)"
            elif "UNVERIFIED" in stage: status_text = "KILLED (UNCONFIRMED)"
            elif "EXTERNAL" in stage: status_text = "KILLED (EXTERNAL)"
            else: status_text = "LOCKED (VIEW ONLY)"
            
            self.btn_kill.configure(state="disabled", text="KILLED", fg_color="#252525", border_color=Theme.BORDER, text_color=Theme.TEXT_GRAY)
            self.btn_pause.configure(state="disabled")

        elif sys_active:
            status_text = "RUNNING"
            status_col = Theme.ACCENT_GREEN
            
            if "KILLING" in stage:
                status_text = "KILLING..."
                status_col = Theme.ACCENT_ORANGE
                self.btn_kill.configure(text="...", state="disabled", fg_color="#252525")
            elif "WAITING" in stage:
                status_text = "VERIFYING..."
                status_col = Theme.ACCENT_ORANGE
            else:
                # ACTIVE KILL BUTTON STYLE (Bright Red)
                self.btn_kill.configure(
                    text="KILL", 
                    state="normal", 
                    fg_color=Theme.ACCENT_RED, 
                    border_color=Theme.ACCENT_RED, 
                    text_color=Theme.TEXT_WHITE,
                    hover_color="#991b1b"
                )

            # Pause Button Logic
            if ks_enabled:
                self.btn_pause.configure(text="PAUSE", fg_color="#252525", state="normal")
            else:
                self.btn_pause.configure(text="RESUME", fg_color=Theme.ACCENT_BLUE, state="normal")
                status_text = "PAUSED"
                status_col = Theme.ACCENT_BLUE

        else:
            # Stopped
            status_text = "OFFLINE"
            status_col = Theme.TEXT_GRAY
            self.btn_kill.configure(state="disabled", fg_color="#252525", border_color=Theme.BORDER, text_color=Theme.TEXT_GRAY)
            self.btn_pause.configure(state="disabled")

        self.lbl_status.configure(text=status_text, text_color=status_col)


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