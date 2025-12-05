import customtkinter as ctk
import json
from pathlib import Path
from gui.theme import Theme

# =========================================================
#  COMPONENT: ACCOUNT SETTINGS FORM
# =========================================================
class AccountSettingsForm(ctk.CTkScrollableFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine
        self.user_id = engine.user_id
        self.sensitive_entries = [] # To track fields that need masking
        
        # Grid Layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)

        # --- SECTION 1: IDENTITY & STATUS ---
        self._build_header("IDENTITY & STATUS", 0)
        
        self.card_id = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_id.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 20))
        self.card_id.grid_columnconfigure(1, weight=1)
        
        # Account Name (Alias)
        ctk.CTkLabel(self.card_id, text="Account Alias", font=Theme.FONT_BODY, text_color=Theme.TEXT_WHITE).grid(row=0, column=0, padx=20, pady=15, sticky="w")
        self.entry_name = ctk.CTkEntry(self.card_id, placeholder_text="e.g. Main Portfolio", height=35)
        self.entry_name.grid(row=0, column=1, padx=20, pady=15, sticky="ew")

        # Active Switch
        ctk.CTkLabel(self.card_id, text="System Active", font=("Arial", 12, "bold"), text_color=Theme.TEXT_GRAY).grid(row=0, column=2, padx=(10, 5), sticky="e")
        self.sw_active = ctk.CTkSwitch(self.card_id, text="", progress_color=Theme.ACCENT_GREEN)
        self.sw_active.grid(row=0, column=3, padx=(0, 20), sticky="e")

        # --- GLOBAL VISIBILITY TOGGLE ---
        self.vis_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.vis_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=15, pady=(0, 5))
        
        self.sw_show_creds = ctk.CTkSwitch(
            self.vis_frame, 
            text="Show Secrets", 
            font=("Arial", 11, "bold"),
            progress_color=Theme.ACCENT_ORANGE,
            command=self.toggle_visibility
        )
        self.sw_show_creds.pack(side="right")

        # --- SECTION 2: BROKER CREDENTIALS ---
        self._build_header("KOTAK NEO CREDENTIALS", 3)
        
        self.card_broker = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_broker.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 20))
        self.card_broker.grid_columnconfigure(1, weight=1)

        self.entry_mobile = self._add_field(self.card_broker, 0, "Mobile Number", "e.g. +919999999999")
        self.entry_ucc = self._add_field(self.card_broker, 1, "UCC (User Code)", "e.g. XARGA")
        self.entry_key = self._add_field(self.card_broker, 2, "Consumer Key")
        
        # Sensitive Fields
        self.entry_password = self._add_field(self.card_broker, 3, "Login Password", is_password=True)
        self.entry_mpin = self._add_field(self.card_broker, 4, "MPIN", is_password=True)
        self.entry_secret = self._add_field(self.card_broker, 5, "TOTP Secret", is_password=True)

        # --- SECTION 3: GMAIL AUTOMATION ---
        self._build_header("GMAIL OTP CREDENTIALS", 5)
        
        self.card_gmail = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_gmail.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 20))
        self.card_gmail.grid_columnconfigure(1, weight=1)

        self.entry_email = self._add_field(self.card_gmail, 0, "Email Address")
        self.entry_filter = self._add_field(self.card_gmail, 1, "Sender Filter", "noreply@nmail.kotaksecurities.com")
        self.entry_app_pass = self._add_field(self.card_gmail, 2, "App Password", is_password=True)

        # --- SAVE BUTTON ---
        self.btn_save = ctk.CTkButton(
            self, 
            text="SAVE CHANGES", 
            font=("Arial", 14, "bold"),
            fg_color=Theme.ACCENT_BLUE, 
            hover_color="#1d4ed8",
            height=50,
            command=self.save_data
        )
        self.btn_save.grid(row=7, column=0, columnspan=2, sticky="ew", padx=10, pady=20)

        # Load Data
        self.load_data()

    def _build_header(self, text, row):
        lbl = ctk.CTkLabel(self, text=text, font=("Arial", 12, "bold"), text_color=Theme.ACCENT_BLUE)
        lbl.grid(row=row, column=0, sticky="w", padx=15, pady=(5, 5))

    def _add_field(self, parent, row, label, placeholder="", is_password=False):
        ctk.CTkLabel(parent, text=label, font=Theme.FONT_BODY, text_color=Theme.TEXT_GRAY).grid(row=row, column=0, padx=20, pady=10, sticky="w")
        
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=35)
        if is_password:
            entry.configure(show="•")
            self.sensitive_entries.append(entry)
        
        entry.grid(row=row, column=1, padx=20, pady=10, sticky="ew")
        return entry

    def toggle_visibility(self):
        """Toggles masking on password fields."""
        show_char = "" if self.sw_show_creds.get() else "•"
        for entry in self.sensitive_entries:
            entry.configure(show=show_char)

    def load_data(self):
        """Populate fields from RAM."""
        config = self.engine.state['sys']['config']
        creds = self.engine.state['sys']['creds']
        kotak = creds.get('kotak', {})
        gmail = creds.get('gmail', {})

        # Identity
        self.entry_name.insert(0, config.get('account_name', self.user_id))
        if config.get('account_active'): self.sw_active.select()
        else: self.sw_active.deselect()

        # Kotak
        self.entry_mobile.insert(0, kotak.get('mobile_number', ''))
        self.entry_password.insert(0, kotak.get('login_password', ''))
        self.entry_mpin.insert(0, kotak.get('mpin', ''))
        self.entry_ucc.insert(0, kotak.get('ucc', ''))
        self.entry_key.insert(0, kotak.get('consumer_key', ''))
        self.entry_secret.insert(0, kotak.get('totp_secret', ''))

        # Gmail
        self.entry_email.insert(0, gmail.get('email', ''))
        self.entry_app_pass.insert(0, gmail.get('google_app_password', ''))
        self.entry_filter.insert(0, gmail.get('sender_filter', ''))

    def save_data(self):
        try:
            # 1. Gather Data
            new_name = self.entry_name.get().strip() or self.user_id
            is_active = bool(self.sw_active.get())
            
            kotak_data = {
                "mobile_number": self.entry_mobile.get().strip(),
                "login_password": self.entry_password.get().strip(),
                "mpin": self.entry_mpin.get().strip(),
                "ucc": self.entry_ucc.get().strip(),
                "consumer_key": self.entry_key.get().strip(),
                "totp_secret": self.entry_secret.get().strip(),
                "environment": "prod"
            }
            
            gmail_data = {
                "email": self.entry_email.get().strip(),
                "google_app_password": self.entry_app_pass.get().strip(),
                "sender_filter": self.entry_filter.get().strip()
            }

            # 2. Update RAM
            with self.engine.state['sys']['lock']:
                self.engine.state['sys']['config']['account_name'] = new_name
                self.engine.state['sys']['config']['account_active'] = is_active
                self.engine.is_active = is_active 
                
                self.engine.state['sys']['creds']['kotak'].update(kotak_data)
                self.engine.state['sys']['creds']['gmail'].update(gmail_data)

            # 3. Update Disk
            self._save_to_config_file(new_name, is_active)
            self._save_to_creds_file(kotak_data, gmail_data)

            # Feedback
            self.btn_save.configure(text="SAVED!", fg_color=Theme.ACCENT_GREEN)
            self.after(2000, lambda: self.btn_save.configure(text="SAVE CHANGES", fg_color=Theme.ACCENT_BLUE))
            print(f"[{self.user_id}] Account Settings Updated.")

        except Exception as e:
            print(f"Save Error: {e}")
            self.btn_save.configure(text="ERROR", fg_color=Theme.ACCENT_RED)

    def _save_to_config_file(self, name, is_active):
        path = Path("source/config.json")
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if self.user_id in data:
                data[self.user_id]['account_name'] = name
                data[self.user_id]['account_active'] = is_active
                
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Config Save Error: {e}")

    def _save_to_creds_file(self, kotak_data, gmail_data):
        path = Path("source/credentials.json")
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if self.user_id in data:
                if 'kotak' not in data[self.user_id]: data[self.user_id]['kotak'] = {}
                if 'gmail' not in data[self.user_id]: data[self.user_id]['gmail'] = {}
                
                data[self.user_id]['kotak'].update(kotak_data)
                data[self.user_id]['gmail'].update(gmail_data)
                
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Creds Save Error: {e}")


# =========================================================
#  PAGE: ACCOUNTS CONTAINER
# =========================================================
class AccountsPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        
        title = ctk.CTkLabel(self, text="Account Manager", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE)
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
            # Tab Title: Display Custom Name + ID
            cfg_name = eng.state['sys']['config'].get('account_name', '')
            tab_title = f"{cfg_name} ({eng.user_id})" if cfg_name else eng.user_id
            
            self.tab_view.add(tab_title)
            
            form = AccountSettingsForm(self.tab_view.tab(tab_title), eng)
            form.pack(fill="both", expand=True)