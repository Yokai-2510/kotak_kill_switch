import customtkinter as ctk
import threading
import json
from pathlib import Path
from gui.theme import Theme

class AccountSettingsForm(ctk.CTkScrollableFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine
        self.user_id = engine.user_id
        self.sensitive_entries = []
        
        self.grid_columnconfigure(0, weight=1)
        
        # --- HEADER ---
        self._build_header("IDENTITY & CONTROL", 0)
        self.card_id = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_id.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 20))
        
        self.card_id.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(self.card_id, text="Alias:", font=Theme.FONT_BODY, text_color=Theme.TEXT_WHITE).grid(row=0, column=0, padx=(20, 10), pady=15, sticky="w")
        self.entry_name = ctk.CTkEntry(self.card_id, placeholder_text="Name", height=30)
        self.entry_name.grid(row=0, column=1, padx=(0, 20), pady=15, sticky="ew")

        # Refresh Button
        self.btn_refresh = ctk.CTkButton(self.card_id, text="⟳", width=40, fg_color="#4b5563", command=self.refresh_session)
        self.btn_refresh.grid(row=0, column=2, padx=(0, 5), pady=15, sticky="e")

        self.sw_show_creds = ctk.CTkSwitch(self.card_id, text="Show Secrets", font=("Arial", 11, "bold"), progress_color=Theme.ACCENT_ORANGE, command=self.toggle_visibility)
        self.sw_show_creds.grid(row=0, column=3, padx=(0, 15), pady=15, sticky="e")

        self.sw_active = ctk.CTkSwitch(self.card_id, text="System Active", font=("Arial", 12, "bold"), progress_color=Theme.ACCENT_GREEN, command=self.on_active_toggle)
        self.sw_active.grid(row=0, column=4, padx=(0, 20), pady=15, sticky="e")

        # --- CREDENTIALS ---
        self._build_header("KOTAK NEO CREDENTIALS", 3)
        self.card_broker = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_broker.grid(row=4, column=0, sticky="ew", padx=10, pady=(0, 20))
        self.card_broker.grid_columnconfigure(1, weight=1)

        self.entry_mobile = self._add_field(self.card_broker, 0, "Mobile Number", mask=True)
        self.entry_ucc = self._add_field(self.card_broker, 1, "UCC (User Code)", mask=True)
        self.entry_key = self._add_field(self.card_broker, 2, "Consumer Key", mask=True)
        self.entry_password = self._add_field(self.card_broker, 3, "Login Password", mask=True)
        self.entry_mpin = self._add_field(self.card_broker, 4, "MPIN", mask=True)
        self.entry_secret = self._add_field(self.card_broker, 5, "TOTP Secret", mask=True)

        self._build_header("GMAIL CONFIGURATION", 5)
        self.card_gmail = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_gmail.grid(row=6, column=0, sticky="ew", padx=10, pady=(0, 20))
        self.card_gmail.grid_columnconfigure(1, weight=1)

        self.entry_email = self._add_field(self.card_gmail, 0, "Email Address", mask=True)
        self.entry_app_pass = self._add_field(self.card_gmail, 1, "App Password", mask=True)
        self.entry_filter = self._add_field(self.card_gmail, 2, "Sender Filter")

        self.btn_save = ctk.CTkButton(self, text="SAVE CREDENTIALS", font=("Arial", 14, "bold"), fg_color=Theme.ACCENT_BLUE, hover_color="#1d4ed8", height=45, command=self.save_data)
        self.btn_save.grid(row=7, column=0, sticky="ew", padx=10, pady=20)

        self.load_data()
        self.update_toggle_state()

    # ... (Helpers: _build_header, _add_field, toggle_visibility, load_data - Same as before) ...
    def _build_header(self, text, row):
        ctk.CTkLabel(self, text=text, font=("Arial", 12, "bold"), text_color=Theme.ACCENT_BLUE).grid(row=row, column=0, sticky="w", padx=15, pady=(5, 5))

    def _add_field(self, parent, row, label, placeholder="", mask=False):
        ctk.CTkLabel(parent, text=label, font=Theme.FONT_BODY, text_color=Theme.TEXT_GRAY).grid(row=row, column=0, padx=20, pady=10, sticky="w")
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=35)
        if mask:
            entry.configure(show="•")
            self.sensitive_entries.append(entry)
        entry.grid(row=row, column=1, padx=20, pady=10, sticky="ew")
        return entry

    def toggle_visibility(self):
        show_char = "" if self.sw_show_creds.get() else "•"
        for entry in self.sensitive_entries: entry.configure(show=show_char)

    def load_data(self):
        config = self.engine.state['sys']['config']
        creds = self.engine.state['sys']['creds']
        kotak = creds.get('kotak', {})
        gmail = creds.get('gmail', {})
        self.entry_name.insert(0, config.get('account_name', self.user_id))
        self.entry_mobile.insert(0, kotak.get('mobile_number', ''))
        self.entry_ucc.insert(0, kotak.get('ucc', ''))
        self.entry_key.insert(0, kotak.get('consumer_key', ''))
        self.entry_password.insert(0, kotak.get('login_password', ''))
        self.entry_mpin.insert(0, kotak.get('mpin', ''))
        self.entry_secret.insert(0, kotak.get('totp_secret', ''))
        self.entry_email.insert(0, gmail.get('email', ''))
        self.entry_app_pass.insert(0, gmail.get('google_app_password', ''))
        self.entry_filter.insert(0, gmail.get('sender_filter', ''))

    def update_toggle_state(self):
        is_locked = self.engine.state['signals'].get('is_locked_today', False)
        is_active = self.engine.state['signals']['system_active']

        if is_active:
            self.sw_active.select()
            if is_locked:
                self.sw_active.configure(state="normal", text="LOCKED (VIEW ONLY)", progress_color=Theme.ACCENT_ORANGE)
            else:
                self.sw_active.configure(state="normal", text="SYSTEM RUNNING", progress_color=Theme.ACCENT_GREEN)
        else:
            self.sw_active.deselect()
            # If locked but stopped, allow starting (into Observer Mode)
            if is_locked:
                self.sw_active.configure(state="normal", text="LOCKED (START VIEWER)", progress_color=Theme.ACCENT_RED)
            else:
                self.sw_active.configure(state="normal", text="SYSTEM STOPPED", progress_color=Theme.ACCENT_RED)

    def on_active_toggle(self):
        is_turning_on = bool(self.sw_active.get())
        self.sw_active.configure(state="disabled", text="PROCESSING...")
        def worker():
            if is_turning_on:
                self.save_data_logic() 
                self.engine.start_session()
            else:
                self.engine.stop_session()
            self.after(0, self._post_toggle_ui)
        threading.Thread(target=worker, daemon=True).start()

    def _post_toggle_ui(self):
        self.sw_active.configure(state="normal")
        self.update_toggle_state()
        stage = self.engine.state['status'].get('stage')
        if stage == "AUTH_ERR":
            self.sw_active.deselect()
            self.sw_active.configure(text="AUTH FAILED", progress_color=Theme.ACCENT_RED)

    def refresh_session(self):
        self.engine.refresh_session()

    # ... (Save logic unchanged) ...
    def save_data(self):
        self.btn_save.configure(text="SAVING...", state="disabled")
        threading.Thread(target=self._save_worker, daemon=True).start()

    def _save_worker(self):
        self.save_data_logic()
        self.after(0, lambda: self.btn_save.configure(text="SAVED!", state="normal", fg_color=Theme.ACCENT_GREEN))
        self.after(2000, lambda: self.btn_save.configure(text="SAVE CREDENTIALS", fg_color=Theme.ACCENT_BLUE))

    def save_data_logic(self):
        new_name = self.entry_name.get().strip() or self.user_id
        kotak_data = {
            "mobile_number": self.entry_mobile.get().strip(),
            "ucc": self.entry_ucc.get().strip(),
            "consumer_key": self.entry_key.get().strip(),
            "login_password": self.entry_password.get().strip(),
            "mpin": self.entry_mpin.get().strip(),
            "totp_secret": self.entry_secret.get().strip(),
            "environment": "prod"
        }
        gmail_data = {
            "email": self.entry_email.get().strip(),
            "google_app_password": self.entry_app_pass.get().strip(),
            "sender_filter": self.entry_filter.get().strip()
        }
        with self.engine.state['sys']['lock']:
            self.engine.state['sys']['config']['account_name'] = new_name
            self.engine.state['sys']['creds']['kotak'].update(kotak_data)
            self.engine.state['sys']['creds']['gmail'].update(gmail_data)
        self._write_to_disk(new_name, kotak_data, gmail_data)

    def _write_to_disk(self, name, k_data, g_data):
        c_path = Path("source/config.json")
        try:
            with open(c_path, 'r') as f: c_data = json.load(f)
            if self.user_id in c_data:
                c_data[self.user_id]['account_name'] = name
                c_data[self.user_id]['account_active'] = self.engine.state['signals']['system_active']
                with open(c_path, 'w') as f: json.dump(c_data, f, indent=2)
        except: pass
        cr_path = Path("source/credentials.json")
        try:
            with open(cr_path, 'r') as f: cr_data = json.load(f)
            if self.user_id in cr_data:
                cr_data[self.user_id]['kotak'].update(k_data)
                cr_data[self.user_id]['gmail'].update(g_data)
                with open(cr_path, 'w') as f: json.dump(cr_data, f, indent=2)
        except: pass

class AccountsPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Account Manager", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE).pack(anchor="w", padx=20, pady=(20, 10))
        self.tab_view = ctk.CTkTabview(self, fg_color="transparent")
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        for eng in engines:
            cfg_name = eng.state['sys']['config'].get('account_name', '')
            tab_title = cfg_name if cfg_name else eng.user_id
            self.tab_view.add(tab_title)
            AccountSettingsForm(self.tab_view.tab(tab_title), eng).pack(fill="both", expand=True)