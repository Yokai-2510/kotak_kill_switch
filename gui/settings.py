import customtkinter as ctk
import json
from pathlib import Path
from gui.theme import Theme

# =========================================================
#  COMPONENT: GENERAL SETTINGS FORM
# =========================================================
class GeneralSettingsForm(ctk.CTkScrollableFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine
        self.user_id = engine.user_id
        self.conf_root = self.engine.state['sys']['config']
        
        self.grid_columnconfigure(0, weight=1)

        # --- SECTION 1: POLLING ---
        self._build_header("HEARTBEAT CONFIG", 0)
        self.card_poll = self._create_card(1)
        self.entry_poll = self._add_input_row(self.card_poll, 0, "Active Polling Rate", "Seconds between API calls (Market Open)", 2)
        self.entry_idle = self._add_input_row(self.card_poll, 1, "Idle Polling Rate", "Seconds between API calls (Market Closed)", 60)

        # --- SECTION 2: TIMEOUTS ---
        self._build_header("TIMEOUTS", 2)
        self.card_time = self._create_card(3)
        self.entry_gmail_to = self._add_input_row(self.card_time, 0, "OTP Timeout", "Seconds to wait for Gmail OTP", 120)
        self.entry_web_to = self._add_input_row(self.card_time, 1, "Browser Timeout", "Milliseconds to wait for elements", 5000)

        # --- SECTION 3: LOGS ---
        self._build_header("MAINTENANCE", 4)
        self.card_logs = self._create_card(5)
        self.sw_wipe = self._add_switch_row(self.card_logs, 0, "Clean Logs on Boot", "Delete old log files when starting app")

        # --- SAVE ---
        self.btn_save = ctk.CTkButton(
            self, text="APPLY SETTINGS", font=("Arial", 14, "bold"),
            height=45, fg_color=Theme.ACCENT_BLUE, hover_color="#1d4ed8",
            command=self.save_config
        )
        self.btn_save.grid(row=6, column=0, pady=30, padx=10, sticky="ew")

        self.load_values()

    def _create_card(self, row):
        card = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        card.grid(row=row, column=0, sticky="ew", padx=10, pady=(0, 20))
        card.grid_columnconfigure(0, weight=1)
        return card

    def _build_header(self, text, row):
        lbl = ctk.CTkLabel(self, text=text, font=("Arial", 12, "bold"), text_color=Theme.ACCENT_BLUE)
        lbl.grid(row=row, column=0, sticky="w", padx=15, pady=(10, 5))

    def _add_input_row(self, parent, row, label, desc, default):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=15, pady=10)
        
        # Labels
        ctk.CTkLabel(f, text=label, font=Theme.FONT_BODY, text_color=Theme.TEXT_WHITE).pack(anchor="w")
        ctk.CTkLabel(f, text=desc, font=("Arial", 10), text_color=Theme.TEXT_GRAY).pack(anchor="w")
        
        # Entry
        entry = ctk.CTkEntry(f, width=80, height=30, border_color=Theme.BORDER, fg_color="#111")
        entry.place(relx=1.0, rely=0.5, anchor="e")
        
        # Divider
        if row > 0: 
            ctk.CTkFrame(parent, height=1, fg_color="#2a2a2a").grid(row=row, column=0, sticky="n", padx=15)
            
        return entry

    def _add_switch_row(self, parent, row, label, desc):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, sticky="ew", padx=15, pady=10)
        
        ctk.CTkLabel(f, text=label, font=Theme.FONT_BODY, text_color=Theme.TEXT_WHITE).pack(anchor="w")
        ctk.CTkLabel(f, text=desc, font=("Arial", 10), text_color=Theme.TEXT_GRAY).pack(anchor="w")
        
        sw = ctk.CTkSwitch(f, text="", progress_color=Theme.ACCENT_GREEN)
        sw.place(relx=1.0, rely=0.5, anchor="e")
        return sw

    def load_values(self):
        mon = self.conf_root.get('monitoring', {})
        self.entry_poll.insert(0, str(mon.get('poll_interval_seconds', 2)))
        self.entry_idle.insert(0, str(mon.get('off_market_interval_seconds', 60)))
        
        gmail = self.conf_root.get('gmail', {})
        web = self.conf_root.get('web_automation', {})
        self.entry_gmail_to.insert(0, str(gmail.get('timeout_seconds', 120)))
        self.entry_web_to.insert(0, str(web.get('search_timeout', 5000)))
        
        log_conf = self.conf_root.get('logging', {})
        if log_conf.get('wipe_on_start', False): self.sw_wipe.select()

    def save_config(self):
        try:
            new_poll = int(self.entry_poll.get())
            new_idle = int(self.entry_idle.get())
            new_gmail_to = int(self.entry_gmail_to.get())
            new_web_to = int(self.entry_web_to.get())
            wipe_logs = bool(self.sw_wipe.get())

            with self.engine.state['sys']['lock']:
                if 'monitoring' not in self.conf_root: self.conf_root['monitoring'] = {}
                if 'gmail' not in self.conf_root: self.conf_root['gmail'] = {}
                if 'web_automation' not in self.conf_root: self.conf_root['web_automation'] = {}
                if 'logging' not in self.conf_root: self.conf_root['logging'] = {}

                self.conf_root['monitoring']['poll_interval_seconds'] = new_poll
                self.conf_root['monitoring']['off_market_interval_seconds'] = new_idle
                self.conf_root['gmail']['timeout_seconds'] = new_gmail_to
                self.conf_root['web_automation']['search_timeout'] = new_web_to
                self.conf_root['logging']['wipe_on_start'] = wipe_logs

            self._write_to_disk()
            self.btn_save.configure(text="SAVED!", fg_color=Theme.ACCENT_GREEN)
            self.after(2000, lambda: self.btn_save.configure(text="APPLY SETTINGS", fg_color=Theme.ACCENT_BLUE))

        except ValueError:
            self.btn_save.configure(text="INVALID INPUT", fg_color=Theme.ACCENT_RED)
            self.after(2000, lambda: self.btn_save.configure(text="APPLY SETTINGS", fg_color=Theme.ACCENT_BLUE))

    def _write_to_disk(self):
        path = Path("source/config.json")
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if self.user_id in data:
                u_data = data[self.user_id]
                u_data.setdefault('monitoring', {})['poll_interval_seconds'] = int(self.entry_poll.get())
                u_data['monitoring']['off_market_interval_seconds'] = int(self.entry_idle.get())
                u_data.setdefault('gmail', {})['timeout_seconds'] = int(self.entry_gmail_to.get())
                u_data.setdefault('web_automation', {})['search_timeout'] = int(self.entry_web_to.get())
                u_data.setdefault('logging', {})['wipe_on_start'] = bool(self.sw_wipe.get())
                
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")


# =========================================================
#  PAGE: SETTINGS CONTAINER
# =========================================================
class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        
        title = ctk.CTkLabel(self, text="Global Configuration", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE)
        title.pack(anchor="w", padx=20, pady=(20, 10))

        self.tab_view = ctk.CTkTabview(
            self, 
            fg_color="transparent",
            segmented_button_fg_color=Theme.BG_CARD,
            segmented_button_selected_color=Theme.ACCENT_BLUE,
            segmented_button_unselected_color=Theme.BG_CARD,
            segmented_button_selected_hover_color=Theme.ACCENT_BLUE,
            text_color=Theme.TEXT_WHITE
        )
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        for eng in engines:
            cfg_name = eng.state['sys']['config'].get('account_name', '')
            tab_name = cfg_name if cfg_name else eng.user_id
            
            self.tab_view.add(tab_name)
            form = GeneralSettingsForm(self.tab_view.tab(tab_name), eng)
            form.pack(fill="both", expand=True)