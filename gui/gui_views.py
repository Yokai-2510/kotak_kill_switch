import customtkinter as ctk
from gui_components import MetricCard, RiskBar, Colors, StatusBadge, FormField, AutomationStepRow

# ==================== DASHBOARD VIEW ====================
class DashboardView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.grid_columnconfigure((0,1,2), weight=1)
        self.grid_rowconfigure(3, weight=1) # Log expands

        # 1. Metrics
        self.card_mtm = MetricCard(self, "Total MTM", "₹ ")
        self.card_mtm.grid(row=0, column=0, sticky="ew", padx=(0,10), pady=10)
        
        self.card_sl = MetricCard(self, "SL Breaches")
        self.card_sl.grid(row=0, column=1, sticky="ew", padx=10, pady=10)
        
        self.card_pos = MetricCard(self, "Positions")
        self.card_pos.grid(row=0, column=2, sticky="ew", padx=(10,0), pady=10)

        # 2. Risk & Kill
        self.risk_bar = RiskBar(self)
        self.risk_bar.grid(row=1, column=0, columnspan=3, sticky="ew", pady=10)

        self.btn_kill = ctk.CTkButton(self, text="⚠️ FORCE KILL SWITCH", height=50, 
                                      fg_color=Colors.DANGER, hover_color="#b91c1c",
                                      font=("Roboto", 16, "bold"), command=self.kill)
        self.btn_kill.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 20))

        # 3. Live Logs (Restored)
        log_frame = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=10, border_width=1, border_color=Colors.BORDER)
        log_frame.grid(row=3, column=0, columnspan=3, sticky="nsew")
        
        ctk.CTkLabel(log_frame, text="SYSTEM EVENTS", font=("Roboto", 11, "bold"), text_color=Colors.TEXT_SUB).pack(anchor="w", padx=15, pady=10)
        
        self.log_box = ctk.CTkTextbox(log_frame, fg_color="transparent", text_color=Colors.TEXT_SUB, font=("Consolas", 11))
        self.log_box.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.log_box.configure(state="disabled")

    def kill(self):
        self.log("MANUAL KILL INITIATED BY USER")
        self.btn_kill.configure(text="KILLING...", state="disabled")

    def log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("0.0", f"> {msg}\n")
        self.log_box.configure(state="disabled")


# ==================== SETTINGS VIEW (The Config Engine) ====================
class SettingsView(ctk.CTkFrame):
    def __init__(self, master, mock_data):
        super().__init__(master, fg_color="transparent")
        self.data = mock_data
        self.current_acc = list(mock_data.keys())[0]

        # 1. Account Header
        header = ctk.CTkFrame(self, fg_color=Colors.BG_CARD, corner_radius=10, border_width=1, border_color=Colors.BORDER)
        header.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(header, text="ACTIVE ACCOUNT PROFILE", font=("Roboto", 10, "bold"), text_color=Colors.TEXT_SUB).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.acc_menu = ctk.CTkOptionMenu(header, values=list(mock_data.keys()), command=self.load_account,
                                          fg_color=Colors.BG_INPUT, button_color=Colors.BORDER,
                                          text_color=Colors.TEXT_MAIN, width=300)
        self.acc_menu.pack(anchor="w", padx=20, pady=(0, 15))

        # 2. Tabs
        self.tabs = ctk.CTkTabview(self, fg_color=Colors.BG_CARD, segmented_button_fg_color=Colors.BG_INPUT, 
                                   segmented_button_selected_color=Colors.ACCENT, text_color=Colors.TEXT_MAIN)
        self.tabs.pack(fill="both", expand=True)
        
        self.tab_gen = self.tabs.add("System & Risk")
        self.tab_cred = self.tabs.add("Credentials")
        self.tab_auto = self.tabs.add("Automation Flow")

        self._build_general_tab()
        self._build_creds_tab()
        self._build_auto_tab()
        
        self.load_account(self.current_acc)

    def _build_general_tab(self):
        f = ctk.CTkScrollableFrame(self.tab_gen, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.inp_limit = FormField(f, "Max MTM Loss Limit (₹)", "-10000")
        self.inp_poll = FormField(f, "API Poll Interval (sec)", "2")
        
        # Toggle
        self.sw_sl = ctk.CTkSwitch(f, text="Trigger only if Stop-Loss Hit?")
        self.sw_sl.pack(anchor="w", pady=15)
        
        # Save
        ctk.CTkButton(f, text="Save Changes", fg_color=Colors.SUCCESS, hover_color="#059669", 
                      command=self.save).pack(anchor="w", pady=20)

    def _build_creds_tab(self):
        f = ctk.CTkScrollableFrame(self.tab_cred, fg_color="transparent")
        f.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.inp_ck = FormField(f, "Consumer Key")
        self.inp_cs = FormField(f, "Consumer Secret", show="*")
        self.inp_mob = FormField(f, "Mobile Number")
        self.inp_mpin = FormField(f, "MPIN")
        self.inp_pass = FormField(f, "Login Password", show="*")

    def _build_auto_tab(self):
        # Header actions
        h = ctk.CTkFrame(self.tab_auto, fg_color="transparent")
        h.pack(fill="x", padx=10, pady=10)
        ctk.CTkButton(h, text="+ Add Step", width=80, height=28, fg_color=Colors.ACCENT, 
                      command=self.add_step).pack(side="right")
        ctk.CTkLabel(h, text="WEB AUTOMATION SEQUENCE", font=("Roboto", 12, "bold")).pack(side="left")

        # Steps List
        self.step_list = ctk.CTkScrollableFrame(self.tab_auto, fg_color="transparent")
        self.step_list.pack(fill="both", expand=True, padx=5)
        self.step_rows = []

    def load_account(self, acc_id):
        self.current_acc = acc_id
        d = self.data[acc_id]
        
        # Load General
        self.inp_limit.set(d.get("limit", ""))
        self.inp_poll.set(d.get("poll", ""))
        if d.get("sl_req"): self.sw_sl.select() 
        else: self.sw_sl.deselect()
        
        # Load Creds
        self.inp_mob.set(d.get("mobile", ""))
        self.inp_mpin.set(d.get("mpin", ""))
        
        # Load Automation
        for r in self.step_rows: r.destroy()
        self.step_rows.clear()
        for s in d.get("steps", []):
            self.add_step(s)

    def add_step(self, data=None):
        if not data: data = {"step": "new", "type": "click"}
        row = AutomationStepRow(self.step_list, data, self.del_step)
        self.step_rows.append(row)

    def del_step(self, row):
        row.destroy()
        self.step_rows.remove(row)

    def save(self):
        print(f"Saving config for {self.current_acc}...")
        # Extract steps
        steps = [r.get_data() for r in self.step_rows]
        print(f"Steps: {len(steps)}")


# ==================== ACCOUNTS VIEW ====================
class AccountsView(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        # Simple placeholder - usually a list of cards
        ctk.CTkLabel(self, text="CONNECTED ACCOUNTS", font=("Roboto", 12, "bold"), text_color=Colors.TEXT_SUB).pack(anchor="w", padx=10, pady=10)
        
        self.c = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.c.pack(fill="both", expand=True)
        
        self.add_card("Main Account (XARGA)", "Connected", Colors.SUCCESS)
        self.add_card("Hedge Account (YBR01)", "Auth Error", Colors.DANGER)

    def add_card(self, name, status, color):
        f = ctk.CTkFrame(self.c, fg_color=Colors.BG_CARD, border_width=1, border_color=Colors.BORDER)
        f.pack(fill="x", pady=5, padx=5)
        ctk.CTkLabel(f, text="👤  "+name, font=("Roboto", 14)).pack(side="left", padx=20, pady=20)
        ctk.CTkLabel(f, text=status, text_color=color, font=("Roboto", 12, "bold")).pack(side="right", padx=20)