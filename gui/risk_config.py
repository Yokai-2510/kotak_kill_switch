import customtkinter as ctk
import json
from pathlib import Path
from gui.theme import Theme

# =========================================================
#  COMPONENT: RISK SETTINGS FORM (PER USER)
# =========================================================
class RiskConfigTab(ctk.CTkScrollableFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine
        self.user_id = engine.user_id
        
        # Load current config snapshot
        self.current_config = self.engine.state['sys']['config']['kill_switch']

        # --- LAYOUT ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # 1. MTM LIMIT SECTION
        self._build_section_header("CAPITAL PROTECTION", 0)
        
        self.card_mtm = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_mtm.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 20))
        
        ctk.CTkLabel(self.card_mtm, text="Daily MTM Loss Limit (₹)", font=Theme.FONT_BODY, text_color=Theme.TEXT_GRAY).pack(anchor="w", padx=20, pady=(15, 5))
        
        self.entry_mtm = ctk.CTkEntry(self.card_mtm, height=40, font=("Arial", 16), placeholder_text="e.g. 5000")
        self.entry_mtm.pack(fill="x", padx=20, pady=(0, 20))
        
        # Pre-fill (Absolute value)
        self.entry_mtm.insert(0, str(abs(self.current_config.get('mtm_limit', 0))))

        # 2. TRIGGER LOGIC SECTION
        self._build_section_header("KILL LOGIC", 2)
        
        self.card_logic = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        self.card_logic.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 20))
        
        # Master Switch
        self.sw_enabled = self._add_switch(
            self.card_logic, 
            "Kill Switch Enabled", 
            "Master toggle. If OFF, the system will never kill trades automatically."
        )
        
        # The Critical "AND" Condition
        self.sw_sl_trigger = self._add_switch(
            self.card_logic, 
            "Require SL Exit to Kill", 
            "If ON, system waits for SL Order to COMPLETE before killing. If OFF, kills immediately on MTM breach."
        )
        
        # Auto Square Off
        self.sw_auto_sq = self._add_switch(
            self.card_logic, 
            "Auto Square Off (API)", 
            "Attempt to close all open positions via API before browser automation starts."
        )

        # 3. SAVE BUTTON
        self.btn_save = ctk.CTkButton(
            self, 
            text="SAVE CHANGES", 
            font=("Arial", 14, "bold"),
            fg_color=Theme.ACCENT_BLUE, 
            hover_color="#1d4ed8",
            height=50,
            command=self.save_config
        )
        self.btn_save.grid(row=4, column=0, columnspan=2, sticky="ew", padx=10, pady=20)

        # Initialize Switch Values
        self._load_values()

    def _build_section_header(self, text, row):
        lbl = ctk.CTkLabel(self, text=text, font=("Arial", 12, "bold"), text_color=Theme.ACCENT_BLUE)
        lbl.grid(row=row, column=0, sticky="w", padx=15, pady=(5, 5))

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
        """Set switches based on current config."""
        cfg = self.current_config
        
        if cfg.get('enabled'): self.sw_enabled.select()
        if cfg.get('trigger_on_sl_hit'): self.sw_sl_trigger.select() # Mapped to "Require SL Exit"
        if cfg.get('auto_square_off'): self.sw_auto_sq.select()

    def save_config(self):
        """Writes to RAM and Disk."""
        try:
            # 1. Parse Input
            mtm_val = float(self.entry_mtm.get()) 
            abs_mtm = abs(mtm_val)
            
            # 2. Construct New Config Dict
            # Cleaned up: Removed dry_run, test_mode, execution_mode
            new_ks_config = {
                "enabled": bool(self.sw_enabled.get()),
                "mtm_limit": abs_mtm,
                "trigger_on_sl_hit": bool(self.sw_sl_trigger.get()), # This is the critical logic flag
                "auto_square_off": bool(self.sw_auto_sq.get()),
                
                # Hardcoded defaults for safety/simplicity
                "execution_mode": "kill_only", 
                "test_mode_equity": False,
                "dry_run": False
            }

            # 3. Update RAM (Thread Safe)
            with self.engine.state['sys']['lock']:
                # Update the sub-dictionary
                self.engine.state['sys']['config']['kill_switch'].update(new_ks_config)
                # Update derived risk limit (Negative value)
                self.engine.state['risk']['mtm_limit'] = -abs_mtm

            # 4. Update Disk (JSON)
            self._write_to_disk(new_ks_config)
            
            # Feedback
            self.btn_save.configure(text="SAVED!", fg_color=Theme.ACCENT_GREEN)
            self.after(2000, lambda: self.btn_save.configure(text="SAVE CHANGES", fg_color=Theme.ACCENT_BLUE))
            print(f"[{self.user_id}] Risk Config Updated.")

        except ValueError:
            self.btn_save.configure(text="INVALID NUMBER", fg_color=Theme.ACCENT_RED)
            self.after(2000, lambda: self.btn_save.configure(text="SAVE CHANGES", fg_color=Theme.ACCENT_BLUE))

    def _write_to_disk(self, new_ks_config):
        path = Path("source/config.json")
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if self.user_id in data:
                # Merge updates to preserve other keys if any exist
                data[self.user_id]['kill_switch'].update(new_ks_config)
                
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving config to disk: {e}")


# =========================================================
#  PAGE: RISK CONFIG CONTAINER
# =========================================================
class RiskConfigPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        
        # Header
        title = ctk.CTkLabel(self, text="Risk Configuration", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE)
        title.pack(anchor="w", padx=20, pady=(20, 10))

        # Tab View
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
        
        # Create a Tab for each User
        for eng in engines:
            # Custom Name
            cfg_name = eng.state['sys']['config'].get('account_name', '')
            tab_title = cfg_name if cfg_name else eng.user_id
            
            self.tab_view.add(tab_title)
            
            # Add the Form to the tab
            form = RiskConfigTab(self.tab_view.tab(tab_title), eng)
            form.pack(fill="both", expand=True)