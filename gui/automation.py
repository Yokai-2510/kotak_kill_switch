import customtkinter as ctk
import json
from pathlib import Path
from gui.theme import Theme

# =========================================================
#  COMPONENT: SINGLE STEP ROW (EDITOR)
# =========================================================
class StepRow(ctk.CTkFrame):
    """
    Represents a single automation step with DYNAMIC editable controls.
    """
    def __init__(self, parent, step_data, delete_callback):
        super().__init__(parent, fg_color=Theme.BG_CARD, height=50)
        self.pack(fill="x", pady=3)
        
        self.step_data = step_data.copy()
        self.delete_callback = delete_callback
        
        # Grid Layout
        # ID | Desc | Action | [Dynamic Params] | Wait | On/Off | Del
        self.grid_columnconfigure(3, weight=1) # Dynamic area expands
        
        # 1. ID
        self.lbl_id = ctk.CTkLabel(
            self, text=str(step_data.get('id', '#')), 
            font=("Arial", 12, "bold"), text_color=Theme.ACCENT_BLUE, width=30
        )
        self.lbl_id.grid(row=0, column=0, padx=(5,0), pady=10)
        
        # 2. Description
        self.entry_desc = ctk.CTkEntry(self, placeholder_text="Description", width=140, height=28, border_width=0, fg_color="#2b2b2b")
        self.entry_desc.insert(0, step_data.get('description', 'New Step'))
        self.entry_desc.grid(row=0, column=1, padx=5)

        # 3. Action Dropdown
        self.action_var = ctk.StringVar(value=step_data.get('action', 'keys'))
        self.combo_action = ctk.CTkOptionMenu(
            self, values=["keys", "click", "input", "otp", "scroll"],
            variable=self.action_var,
            width=80, height=28,
            fg_color="#2b2b2b", button_color="#333333",
            command=self._update_dynamic_inputs
        )
        self.combo_action.grid(row=0, column=2, padx=5)

        # 4. Dynamic Input Frame (Holds X/Y, Keys, Creds etc.)
        self.dynamic_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
        self.dynamic_frame.grid(row=0, column=3, sticky="ew", padx=5)
        
        # Input references (will be populated by _update_dynamic_inputs)
        self.inputs = {} 
        self._update_dynamic_inputs(self.action_var.get())

        # 5. Wait Time
        ctk.CTkLabel(self, text="Wait:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_GRAY).grid(row=0, column=4)
        self.entry_wait = ctk.CTkEntry(self, width=40, height=28)
        self.entry_wait.insert(0, str(step_data.get('wait', 1.0)))
        self.entry_wait.grid(row=0, column=5, padx=5)

        # 6. Enabled Toggle
        self.sw_enabled = ctk.CTkSwitch(
            self, text="", width=40, height=20,
            progress_color=Theme.ACCENT_GREEN
        )
        if step_data.get('enabled', True): self.sw_enabled.select()
        self.sw_enabled.grid(row=0, column=6, padx=5)

        # 7. Delete Button
        self.btn_delete = ctk.CTkButton(
            self, text="✕", width=28, height=28,
            fg_color="#3f1313", text_color=Theme.ACCENT_RED, hover_color="#5c1b1b",
            command=lambda: self.delete_callback(self)
        )
        self.btn_delete.grid(row=0, column=7, padx=(5, 10))

    def _update_dynamic_inputs(self, action):
        """Rebuilds the middle section based on Action Type."""
        # Clear existing
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
        self.inputs = {}

        if action == "click":
            # X and Y inputs
            coords = self.step_data.get('coords') or {'x': 0, 'y': 0}
            self.inputs['x'] = self._create_input("X:", str(coords.get('x', 0)), 40)
            self.inputs['y'] = self._create_input("Y:", str(coords.get('y', 0)), 40)

        elif action == "keys" or action == "input":
            # Keys input (Common for both)
            raw_keys = self.step_data.get('keys') or []
            keys_str = ", ".join(raw_keys)
            
            if action == "input":
                # Cred Key Input + Keys
                cred_val = self.step_data.get('cred_key') or ""
                self.inputs['cred'] = self._create_input("Cred:", cred_val, 100, "e.g. mobile_number")
                self.inputs['keys'] = self._create_input("Keys:", keys_str, 80, "Enter, Tab")
            else:
                # Just Keys
                self.inputs['keys'] = self._create_input("Keys:", keys_str, 180, "Tab, Enter")

        elif action == "scroll":
            repeats = self.step_data.get('repeats') or 1
            self.inputs['repeats'] = self._create_input("Repeats:", str(repeats), 50)

        elif action == "otp":
            ctk.CTkLabel(self.dynamic_frame, text="Auto-fetches OTP from Gmail", text_color=Theme.TEXT_GRAY, font=Theme.FONT_SMALL).pack(side="left")

    def _create_input(self, label_text, value, width, placeholder=""):
        container = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        container.pack(side="left", padx=5)
        
        ctk.CTkLabel(container, text=label_text, font=Theme.FONT_SMALL, text_color=Theme.TEXT_GRAY).pack(side="left", padx=(0,2))
        entry = ctk.CTkEntry(container, width=width, height=26, placeholder_text=placeholder)
        entry.insert(0, value)
        entry.pack(side="left")
        return entry

    def get_updated_data(self):
        """Parses UI inputs back into a clean dictionary."""
        data = self.step_data.copy()
        
        # Standard Fields
        data['description'] = self.entry_desc.get()
        data['action'] = self.action_var.get()
        data['enabled'] = bool(self.sw_enabled.get())
        data['optional'] = False # Defaulting to false as requested
        
        try:
            data['wait'] = float(self.entry_wait.get())
        except ValueError:
            data['wait'] = 1.0

        # Dynamic Fields Parsing
        action = data['action']
        
        # Reset complex fields to avoid stale data
        data['coords'] = None
        data['keys'] = None
        data['cred_key'] = None
        data['repeats'] = None

        if action == "click":
            try:
                x = int(self.inputs['x'].get())
                y = int(self.inputs['y'].get())
                data['coords'] = {'x': x, 'y': y}
            except:
                data['coords'] = {'x': 0, 'y': 0} # Safety

        elif action == "keys":
            raw = self.inputs['keys'].get()
            # Convert "Tab, Enter" -> ["Tab", "Enter"]
            data['keys'] = [k.strip() for k in raw.split(',')] if raw else []

        elif action == "input":
            data['cred_key'] = self.inputs['cred'].get()
            raw = self.inputs['keys'].get()
            if raw:
                data['keys'] = [k.strip() for k in raw.split(',')]

        elif action == "scroll":
            try:
                data['repeats'] = int(self.inputs['repeats'].get())
            except:
                data['repeats'] = 1

        return data


# =========================================================
#  COMPONENT: AUTOMATION EDITOR (PER USER)
# =========================================================
class AutomationEditor(ctk.CTkFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine
        self.user_id = engine.user_id
        self.rows = [] 
        
        # Load Steps
        self.current_steps = self.engine.state['sys']['config']['web_automation']['flow_steps']

        # Actions Header
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", pady=(0, 10), padx=5)
        
        self.btn_add = ctk.CTkButton(
            action_frame, text="+ ADD STEP", 
            font=("Arial", 12, "bold"), height=32, width=100,
            fg_color=Theme.ACCENT_GREEN, hover_color="#059669",
            command=self.add_step
        )
        self.btn_add.pack(side="left")
        
        self.btn_save = ctk.CTkButton(
            action_frame, text="SAVE CONFIG", 
            font=("Arial", 12, "bold"), height=32, width=120,
            fg_color=Theme.ACCENT_BLUE, hover_color="#1d4ed8",
            command=self.save_config
        )
        self.btn_save.pack(side="right")

        # Steps List
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.pack(fill="both", expand=True)
        
        for step in self.current_steps:
            self._create_row(step)

    def _create_row(self, step_data):
        row = StepRow(self.scroll_area, step_data, self.delete_step)
        self.rows.append(row)

    def add_step(self):
        new_id = len(self.rows) + 1
        template = {
            "id": new_id,
            "description": "New Action",
            "action": "keys",
            "keys": ["Tab"],
            "wait": 1.0,
            "enabled": True
        }
        self._create_row(template)

    def delete_step(self, row_widget):
        row_widget.destroy()
        if row_widget in self.rows:
            self.rows.remove(row_widget)

    def save_config(self):
        new_steps_list = []
        try:
            for i, row in enumerate(self.rows):
                step_data = row.get_updated_data()
                step_data['id'] = i + 1 # Auto-renumber
                new_steps_list.append(step_data)
            
            # Update RAM
            with self.engine.state['sys']['lock']:
                self.engine.state['sys']['config']['web_automation']['flow_steps'] = new_steps_list
            
            # Update Disk
            self._write_to_disk(new_steps_list)
            
            # Visual Feedback
            for i, row in enumerate(self.rows):
                row.lbl_id.configure(text=str(i + 1))

            self.btn_save.configure(text="SAVED!", fg_color=Theme.ACCENT_GREEN)
            self.after(2000, lambda: self.btn_save.configure(text="SAVE CONFIG", fg_color=Theme.ACCENT_BLUE))
            print(f"[{self.user_id}] Automation Steps Updated ({len(new_steps_list)} steps).")
            
        except Exception as e:
            print(f"Save Error: {e}")
            self.btn_save.configure(text="ERROR", fg_color=Theme.ACCENT_RED)

    def _write_to_disk(self, new_steps):
        path = Path("source/config.json")
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            if self.user_id in data:
                data[self.user_id]['web_automation']['flow_steps'] = new_steps
                
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Disk Write Error: {e}")


# =========================================================
#  PAGE: AUTOMATION PAGE CONTAINER
# =========================================================
class AutomationPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        
        title = ctk.CTkLabel(self, text="Automation Editor", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE)
        title.pack(anchor="w", padx=20, pady=(20, 10))

        self.tab_view = ctk.CTkTabview(
            self, fg_color="transparent",
            segmented_button_fg_color=Theme.BG_CARD,
            segmented_button_selected_color=Theme.ACCENT_BLUE,
            segmented_button_unselected_color=Theme.BG_CARD,
            segmented_button_selected_hover_color=Theme.ACCENT_BLUE,
            text_color=Theme.TEXT_WHITE
        )
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        for eng in engines:
            # FIX: Fetch Custom Name from Config
            cfg_name = eng.state['sys']['config'].get('account_name', '')
            tab_title = cfg_name if cfg_name else eng.user_id
            
            self.tab_view.add(tab_title)
            
            editor = AutomationEditor(self.tab_view.tab(tab_title), eng)
            editor.pack(fill="both", expand=True, padx=5, pady=5)