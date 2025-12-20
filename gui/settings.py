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

        # --- 1. CONNECTIVITY & RETRIES ---
        self._build_header("API & CONNECTIVITY", 0)
        self.card_conn = self._create_card(1)
        
        # Polling (Grouped tightly with Retries now)
        self.entry_poll = self._add_input_row(self.card_conn, 0, "Active Polling Rate", "Seconds (Market Open)", 2)
        self.entry_idle = self._add_input_row(self.card_conn, 1, "Idle Polling Rate", "Seconds (Market Closed)", 60)
        
        # Retry Logic (Removed Divider to fix gap)
        self.entry_retries = self._add_input_row(self.card_conn, 2, "Max Retries", "Attempts before re-login", 5)
        self.entry_delay = self._add_input_row(self.card_conn, 3, "Retry Delay", "Base seconds between retries", 2)

        # --- 2. NOTIFICATIONS ---
        self._build_header("NOTIFICATIONS", 4)
        self.card_notify = self._create_card(5)
        self.sw_telegram = self._add_switch_row(self.card_notify, 0, "Enable Telegram Alerts", "Send Risk & Kill alerts to bot")

        # --- 3. BROWSER AUTOMATION ---
        self._build_header("BROWSER AUTOMATION", 6)
        self.card_browser = self._create_card(7)
        self.sw_headless = self._add_switch_row(self.card_browser, 0, "Headless Mode", "Hide browser window")
        self.sw_verify = self._add_switch_row(self.card_browser, 1, "Require Email Verify", "Wait for 'Kill Activated' email")
        self.entry_gmail_to = self._add_input_row(self.card_browser, 2, "Gmail OTP Timeout", "Seconds to wait for emails", 120)
        self.entry_web_to = self._add_input_row(self.card_browser, 3, "Browser Timeout", "Ms to wait for elements", 20000)

        # --- 4. MAINTENANCE ---
        self._build_header("MAINTENANCE", 8)
        self.card_logs = self._create_card(9)
        self.sw_wipe = self._add_switch_row(self.card_logs, 0, "Clean Logs on Boot", "Delete old log files on start")

        # --- 5. EMERGENCY RESET ---
        self._build_header("EMERGENCY RESET", 10)
        self.card_reset = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.ACCENT_RED)
        self.card_reset.grid(row=11, column=0, sticky="ew", padx=10, pady=(0, 20))
        self.card_reset.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(self.card_reset, text="Daily Kill Lockout", font=("Arial", 12, "bold"), text_color=Theme.TEXT_WHITE).pack(anchor="w", padx=15, pady=(15, 0))
        ctk.CTkLabel(self.card_reset, text="Manually clear the 'Killed Today' status if it was a test.", font=("Arial", 11), text_color=Theme.TEXT_GRAY).pack(anchor="w", padx=15, pady=0)
        self.btn_reset = ctk.CTkButton(self.card_reset, text="RESET KILL STATUS", fg_color="#3f1313", hover_color="#5c1b1b", text_color=Theme.ACCENT_RED, border_width=1, border_color=Theme.ACCENT_RED, command=self.reset_kill_status)
        self.btn_reset.pack(fill="x", padx=15, pady=15)

        self.btn_save = ctk.CTkButton(self, text="APPLY SETTINGS", font=("Arial", 14, "bold"), height=45, fg_color=Theme.ACCENT_BLUE, hover_color="#1d4ed8", command=self.save_config)
        self.btn_save.grid(row=12, column=0, pady=30, padx=10, sticky="ew")
        self.load_values()

    def reset_kill_status(self):
        self.engine.unlock_account()
        self.btn_reset.configure(text="UNLOCKED!", fg_color=Theme.ACCENT_GREEN, text_color=Theme.TEXT_WHITE)
        self.after(2000, lambda: self.btn_reset.configure(text="RESET KILL STATUS", fg_color="#3f1313", text_color=Theme.ACCENT_RED))

    # Helpers
    def _create_card(self, row):
        card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        card.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 20))
        card.grid_columnconfigure(0, weight=1)
        return card
    def _build_header(self, text, row):
        ctk.CTkLabel(self, text=text, font=("Arial", 12, "bold"), text_color=Theme.ACCENT_BLUE).grid(row=row, column=0, sticky="w", padx=15, pady=(10, 5))
    
    def _add_input_row(self, parent, row, label, desc, default):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=15, pady=10)
        ctk.CTkLabel(f, text=label, font=Theme.FONT_BODY, text_color=Theme.TEXT_WHITE).pack(anchor="w")
        ctk.CTkLabel(f, text=desc, font=("Arial", 10), text_color=Theme.TEXT_GRAY).pack(anchor="w")
        
        entry = ctk.CTkEntry(f, width=80, height=30, border_color=Theme.BORDER, fg_color="#111")
        # Added x=-10 to shift input slightly left for alignment
        entry.place(relx=1.0, x=-10, rely=0.5, anchor="e")
        
        if row > 0: ctk.CTkFrame(parent, height=1, fg_color="#2a2a2a").grid(row=row, column=0, sticky="n", padx=15)
        return entry

    def _add_switch_row(self, parent, row, label, desc):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=15, pady=10)
        ctk.CTkLabel(f, text=label, font=Theme.FONT_BODY, text_color=Theme.TEXT_WHITE).pack(anchor="w")
        ctk.CTkLabel(f, text=desc, font=("Arial", 10), text_color=Theme.TEXT_GRAY).pack(anchor="w")
        
        sw = ctk.CTkSwitch(f, text="", progress_color=Theme.ACCENT_GREEN)
        # Added x=-10 to align switch margin with inputs
        sw.place(relx=1.0, x=-10, rely=0.5, anchor="e")
        return sw

    def load_values(self):
        mon = self.conf_root.get('monitoring', {})
        retry = mon.get('retry_strategy', {})
        self.entry_poll.insert(0, str(mon.get('poll_interval_seconds', 2)))
        self.entry_idle.insert(0, str(mon.get('off_market_interval_seconds', 60)))
        self.entry_retries.insert(0, str(retry.get('max_retries', 5)))
        self.entry_delay.insert(0, str(retry.get('base_delay', 2)))

        notif = self.conf_root.get('notifications', {})
        if notif.get('enable_telegram', False): self.sw_telegram.select()

        gmail = self.conf_root.get('gmail', {})
        web = self.conf_root.get('web_automation', {})
        browser = web.get('browser', {})
        
        self.entry_gmail_to.insert(0, str(gmail.get('timeout_seconds', 120)))
        self.entry_web_to.insert(0, str(web.get('search_timeout', 20000)))
        
        if browser.get('headless', False): self.sw_headless.select()
        else: self.sw_headless.deselect()
        
        if gmail.get('enable_verification', True): self.sw_verify.select()
        else: self.sw_verify.deselect()

        if self.conf_root.get('logging', {}).get('wipe_on_start', False): self.sw_wipe.select()

    def save_config(self):
        try:
            new_poll = int(self.entry_poll.get())
            new_idle = int(self.entry_idle.get())
            max_retries = int(self.entry_retries.get())
            base_delay = int(self.entry_delay.get())
            gmail_to = int(self.entry_gmail_to.get())
            web_to = int(self.entry_web_to.get())
            
            enable_tg = bool(self.sw_telegram.get())
            is_headless = bool(self.sw_headless.get())
            enable_verify = bool(self.sw_verify.get())
            wipe_logs = bool(self.sw_wipe.get())

            with self.engine.state['sys']['lock']:
                u_data = self.conf_root
                if 'monitoring' not in u_data: u_data['monitoring'] = {}
                if 'notifications' not in u_data: u_data['notifications'] = {}
                if 'gmail' not in u_data: u_data['gmail'] = {}
                if 'web_automation' not in u_data: u_data['web_automation'] = {}
                if 'browser' not in u_data['web_automation']: u_data['web_automation']['browser'] = {}
                if 'logging' not in u_data: u_data['logging'] = {}

                u_data['monitoring']['poll_interval_seconds'] = new_poll
                u_data['monitoring']['off_market_interval_seconds'] = new_idle
                u_data['monitoring']['retry_strategy'] = {
                    "max_retries": max_retries,
                    "base_delay": base_delay,
                    "max_delay": 10
                }
                u_data['notifications']['enable_telegram'] = enable_tg
                u_data['notifications']['notify_on_kill'] = True
                u_data['notifications']['notify_on_mtm_breach'] = True
                u_data['gmail']['timeout_seconds'] = gmail_to
                u_data['gmail']['enable_verification'] = enable_verify
                u_data['web_automation']['search_timeout'] = web_to
                u_data['web_automation']['browser']['headless'] = is_headless
                u_data['logging']['wipe_on_start'] = wipe_logs

            self._write_to_disk()
            self.btn_save.configure(text="SAVED!", fg_color=Theme.ACCENT_GREEN)
            self.after(2000, lambda: self.btn_save.configure(text="APPLY SETTINGS", fg_color=Theme.ACCENT_BLUE))
        except ValueError:
            self.btn_save.configure(text="INVALID INPUT", fg_color=Theme.ACCENT_RED)
            self.after(2000, lambda: self.btn_save.configure(text="APPLY SETTINGS", fg_color=Theme.ACCENT_BLUE))

    def _write_to_disk(self):
        path = Path("source/config.json")
        try:
            with open(path, 'r') as f: data = json.load(f)
            if self.user_id in data:
                u_mem = self.conf_root
                u_disk = data[self.user_id]
                u_disk['monitoring'] = u_mem['monitoring']
                u_disk['notifications'] = u_mem['notifications']
                u_disk['gmail'] = u_mem['gmail']
                u_disk['web_automation'] = u_mem['web_automation']
                u_disk['logging']['wipe_on_start'] = u_mem['logging']['wipe_on_start']
                with open(path, 'w') as f: json.dump(data, f, indent=2)
        except: pass

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Global Configuration", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE).pack(anchor="w", padx=20, pady=(20, 10))
        self.tab_view = ctk.CTkTabview(self, fg_color="transparent")
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        for eng in engines:
            cfg_name = eng.state['sys']['config'].get('account_name', '')
            tab_name = cfg_name if cfg_name else eng.user_id
            self.tab_view.add(tab_name)
            GeneralSettingsForm(self.tab_view.tab(tab_name), eng).pack(fill="both", expand=True)