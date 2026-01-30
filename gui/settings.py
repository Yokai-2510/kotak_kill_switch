import customtkinter as ctk
import json
from pathlib import Path
from gui.theme import Theme

class GeneralSettingsForm(ctk.CTkScrollableFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine
        self.user_id = engine.user_id
        self.conf_root = self.engine.state['sys']['config']
        self.grid_columnconfigure(0, weight=1)

        # --- 1. API & CONNECTIVITY ---
        self._build_header("API & CONNECTIVITY", 0)
        self.card_conn = self._create_card(1)
        self.entry_poll = self._add_input_row(self.card_conn, 0, "Active Polling Rate", "Seconds (Consistency Sync)", 30)
        self.entry_idle = self._add_input_row(self.card_conn, 1, "Idle Polling Rate", "Seconds (Off-market)", 60)
        self.entry_retries = self._add_input_row(self.card_conn, 2, "Max Retries", "Attempts before re-login", 5)

        # --- 2. NOTIFICATIONS ---
        self._build_header("NOTIFICATIONS", 4)
        self.card_notify = self._create_card(5)
        self.sw_telegram = self._add_switch_row(self.card_notify, 0, "Enable Telegram Alerts", "Send Risk & Kill alerts to bot")

        # --- 3. BROWSER AUTOMATION (REDO) ---
        self._build_header("BROWSER AUTOMATION & HARD KILL", 6)
        self.card_browser = self._create_card(7)
        
        self.sw_headless = self._add_switch_row(self.card_browser, 0, "Headless Mode", "Hide the automation browser window")
        
        # --- NEW HARD KILL TOGGLE ---
        self.sw_hard_kill = self._add_switch_row(
            self.card_browser, 1, 
            "Hard Close OS Browser", 
            "Force-kill ALL Chrome processes on the OS after Kill Switch fires"
        )
        
        self.sw_verify = self._add_switch_row(self.card_browser, 2, "Require Email Verification", "Wait for 'Kill Activated' email to lock account")
        self.entry_web_to = self._add_input_row(self.card_browser, 3, "Browser Search Timeout", "Ms to wait for web elements (e.g. 20000)", 20000)

        # --- 4. MAINTENANCE & RESET ---
        self._build_header("MAINTENANCE", 8)
        self.card_reset = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.ACCENT_RED)
        self.card_reset.grid(row=9, column=0, sticky="ew", padx=10, pady=(0, 20))
        
        btn_reset_frame = ctk.CTkFrame(self.card_reset, fg_color="transparent")
        btn_reset_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(btn_reset_frame, text="Emergency Reset", font=("Arial", 12, "bold"), text_color=Theme.TEXT_WHITE).pack(side="left")
        self.btn_reset = ctk.CTkButton(
            btn_reset_frame, text="RESET KILL LOCK", width=120, height=28,
            fg_color="#3f1313", hover_color="#5c1b1b", text_color=Theme.ACCENT_RED, 
            border_width=1, border_color=Theme.ACCENT_RED, command=self.reset_kill_status
        )
        self.btn_reset.pack(side="right")

        # --- SAVE BUTTON ---
        self.btn_save = ctk.CTkButton(self, text="APPLY ALL SETTINGS", font=("Arial", 14, "bold"), height=45, fg_color=Theme.ACCENT_BLUE, hover_color="#1d4ed8", command=self.save_config)
        self.btn_save.grid(row=10, column=0, pady=30, padx=10, sticky="ew")
        
        self.load_values()

    # --- UI HELPERS ---
    def _create_card(self, row):
        card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        card.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 20))
        card.grid_columnconfigure(0, weight=1)
        return card

    def _build_header(self, text, row):
        ctk.CTkLabel(self, text=text, font=("Arial", 11, "bold"), text_color=Theme.ACCENT_BLUE).grid(row=row, column=0, sticky="w", padx=15, pady=(10, 5))
    
    def _add_input_row(self, parent, row, label, desc, default):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=15, pady=10)
        ctk.CTkLabel(f, text=label, font=Theme.FONT_BODY, text_color=Theme.TEXT_WHITE).pack(anchor="w")
        ctk.CTkLabel(f, text=desc, font=("Arial", 10), text_color=Theme.TEXT_GRAY).pack(anchor="w")
        entry = ctk.CTkEntry(f, width=100, height=28, fg_color="#111")
        entry.place(relx=1.0, x=-10, rely=0.5, anchor="e")
        return entry

    def _add_switch_row(self, parent, row, label, desc):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=15, pady=10)
        ctk.CTkLabel(f, text=label, font=Theme.FONT_BODY, text_color=Theme.TEXT_WHITE).pack(anchor="w")
        ctk.CTkLabel(f, text=desc, font=("Arial", 10), text_color=Theme.TEXT_GRAY).pack(anchor="w")
        sw = ctk.CTkSwitch(f, text="", progress_color=Theme.ACCENT_GREEN)
        sw.place(relx=1.0, x=-10, rely=0.5, anchor="e")
        return sw

    # --- LOGIC ---
    def reset_kill_status(self):
        self.engine.unlock_account()
        self.btn_reset.configure(text="LOCK CLEARED!", fg_color=Theme.ACCENT_GREEN, text_color=Theme.TEXT_WHITE)
        self.after(2000, lambda: self.btn_reset.configure(text="RESET KILL LOCK", fg_color="#3f1313", text_color=Theme.ACCENT_RED))

    def load_values(self):
        mon = self.conf_root.get('monitoring', {})
        retry = mon.get('retry_strategy', {})
        self.entry_poll.insert(0, str(mon.get('poll_interval_seconds', 30)))
        self.entry_idle.insert(0, str(mon.get('off_market_interval_seconds', 60)))
        self.entry_retries.insert(0, str(retry.get('max_retries', 5)))

        notif = self.conf_root.get('notifications', {})
        if notif.get('enable_telegram'): self.sw_telegram.select()

        gmail = self.conf_root.get('gmail', {})
        web = self.conf_root.get('web_automation', {})
        browser = web.get('browser', {})
        
        self.entry_web_to.insert(0, str(web.get('search_timeout', 20000)))
        
        if browser.get('headless'): self.sw_headless.select()
        if web.get('hard_close_browser'): self.sw_hard_kill.select() # <--- LOAD NEW KEY
        if gmail.get('enable_verification', True): self.sw_verify.select()

    def save_config(self):
        try:
            with self.engine.state['sys']['lock']:
                # Update Monitoring
                self.conf_root['monitoring']['poll_interval_seconds'] = int(self.entry_poll.get())
                self.conf_root['monitoring']['off_market_interval_seconds'] = int(self.entry_idle.get())
                self.conf_root['monitoring']['retry_strategy']['max_retries'] = int(self.entry_retries.get())
                
                # Update Automation Toggles
                self.conf_root['notifications']['enable_telegram'] = bool(self.sw_telegram.get())
                self.conf_root['web_automation']['browser']['headless'] = bool(self.sw_headless.get())
                self.conf_root['web_automation']['hard_close_browser'] = bool(self.sw_hard_kill.get()) # <--- SAVE NEW KEY
                self.conf_root['web_automation']['search_timeout'] = int(self.entry_web_to.get())
                self.conf_root['gmail']['enable_verification'] = bool(self.sw_verify.get())

            self._write_to_disk()
            self.btn_save.configure(text="SETTINGS APPLIED!", fg_color=Theme.ACCENT_GREEN)
            self.after(2000, lambda: self.btn_save.configure(text="APPLY ALL SETTINGS", fg_color=Theme.ACCENT_BLUE))
        except Exception as e:
            self.btn_save.configure(text="ERROR SAVING", fg_color=Theme.ACCENT_RED)
            self.after(2000, lambda: self.btn_save.configure(text="APPLY ALL SETTINGS", fg_color=Theme.ACCENT_BLUE))

    def _write_to_disk(self):
        path = Path("source/config.json")
        try:
            with open(path, 'r') as f: data = json.load(f)
            if self.user_id in data:
                data[self.user_id].update(self.conf_root)
                with open(path, 'w') as f: json.dump(data, f, indent=2)
        except: pass

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Global System Configuration", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE).pack(anchor="w", padx=20, pady=(20, 10))
        self.tab_view = ctk.CTkTabview(self, fg_color="transparent", segmented_button_selected_color=Theme.ACCENT_BLUE)
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        for eng in engines:
            name = eng.state['sys']['config'].get('account_name', eng.user_id)
            self.tab_view.add(name)
            GeneralSettingsForm(self.tab_view.tab(name), eng).pack(fill="both", expand=True)