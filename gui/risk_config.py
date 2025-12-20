import customtkinter as ctk
import json
from pathlib import Path
from gui.theme import Theme

class RiskConfigTab(ctk.CTkScrollableFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine
        self.user_id = engine.user_id
        
        self.current_config = self.engine.state['sys']['config']['kill_switch']

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. MTM LIMIT
        self._build_section_header("CAPITAL PROTECTION", 0)
        self.card_mtm = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_mtm.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 20))
        
        ctk.CTkLabel(self.card_mtm, text="Daily MTM Loss Limit (₹)", font=Theme.FONT_BODY, text_color=Theme.TEXT_GRAY).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.entry_mtm = ctk.CTkEntry(self.card_mtm, height=40, font=("Arial", 16), placeholder_text="e.g. 5000")
        self.entry_mtm.pack(fill="x", padx=20, pady=(0, 20))
        self.entry_mtm.insert(0, str(abs(self.current_config.get('mtm_limit', 0))))

        # 2. LOGIC
        self._build_section_header("KILL LOGIC", 2)
        self.card_logic = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_logic.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 20))
        
        self.sw_enabled = self._add_switch(self.card_logic, "Kill Switch Enabled", "Master toggle.")
        
        # Renamed Switch
        self.sw_sl_conf = self._add_switch(self.card_logic, "Sell Order Exit Confirmation", "Kill ONLY if SL order is filled.")
        
        self.sw_auto_sq = self._add_switch(self.card_logic, "Auto Square Off (API)", "Close open positions before Kill.")

        # 3. SAVE
        self.btn_save = ctk.CTkButton(
            self, text="SAVE CHANGES", font=("Arial", 14, "bold"),
            fg_color=Theme.ACCENT_BLUE, hover_color="#1d4ed8", height=50,
            command=self.save_config
        )
        self.btn_save.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=20)
        self._load_values()

    def _build_section_header(self, text, row):
        ctk.CTkLabel(self, text=text, font=("Arial", 12, "bold"), text_color=Theme.ACCENT_BLUE).grid(row=row, column=0, sticky="w", padx=15, pady=(5, 5))

    def _add_switch(self, parent, text, tooltip):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=20, pady=10)
        lbl_frame = ctk.CTkFrame(frame, fg_color="transparent")
        lbl_frame.pack(side="left")
        ctk.CTkLabel(lbl_frame, text=text, font=("Arial", 13, "bold"), text_color=Theme.TEXT_WHITE).pack(anchor="w")
        ctk.CTkLabel(lbl_frame, text=tooltip, font=("Arial", 11), text_color=Theme.TEXT_GRAY).pack(anchor="w")
        switch = ctk.CTkSwitch(frame, text="", progress_color=Theme.ACCENT_GREEN)
        switch.pack(side="right")
        return switch

    def _load_values(self):
        cfg = self.current_config
        if cfg.get('enabled'): self.sw_enabled.select()
        # Map JSON key 'sell_order_exit_confirmation' to switch
        if cfg.get('sell_order_exit_confirmation'): self.sw_sl_conf.select()
        if cfg.get('auto_square_off'): self.sw_auto_sq.select()

    def save_config(self):
        try:
            raw_mtm = self.entry_mtm.get().strip()
            if not raw_mtm: raise ValueError("Empty")
            mtm_val = float(raw_mtm)
            abs_mtm = abs(mtm_val)
            
            # Clean Config Structure based on your request
            new_ks_config = {
                "enabled": bool(self.sw_enabled.get()),
                "mtm_limit": abs_mtm,
                "sell_order_exit_confirmation": bool(self.sw_sl_conf.get()),
                "auto_square_off": bool(self.sw_auto_sq.get())
            }

            with self.engine.state['sys']['lock']:
                self.engine.state['sys']['config']['kill_switch'].update(new_ks_config)
                self.engine.state['risk']['mtm_limit'] = -abs_mtm

            self._write_to_disk(new_ks_config)
            
            self.btn_save.configure(text="SAVED!", fg_color=Theme.ACCENT_GREEN)
            self.after(2000, lambda: self.btn_save.configure(text="SAVE CHANGES", fg_color=Theme.ACCENT_BLUE))
            print(f"[{self.user_id}] Risk Config Updated.")

        except ValueError:
            self.btn_save.configure(text="INVALID NUMBER!", fg_color=Theme.ACCENT_RED)
            self.entry_mtm.configure(border_color=Theme.ACCENT_RED)
            self.after(2000, lambda: self._reset_btn())

    def _reset_btn(self):
        self.btn_save.configure(text="SAVE CHANGES", fg_color=Theme.ACCENT_BLUE)
        self.entry_mtm.configure(border_color=Theme.BORDER)

    def _write_to_disk(self, new_ks_config):
        path = Path("source/config.json")
        try:
            with open(path, 'r') as f: data = json.load(f)
            if self.user_id in data:
                data[self.user_id]['kill_switch'].update(new_ks_config)
                with open(path, 'w') as f: json.dump(data, f, indent=2)
        except Exception: pass

class RiskConfigPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Risk Configuration", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE).pack(anchor="w", padx=20, pady=(20, 10))
        self.tab_view = ctk.CTkTabview(self, fg_color="transparent")
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        for eng in engines:
            cfg_name = eng.state['sys']['config'].get('account_name', '')
            tab_title = cfg_name if cfg_name else eng.user_id
            self.tab_view.add(tab_title)
            RiskConfigTab(self.tab_view.tab(tab_title), eng).pack(fill="both", expand=True)