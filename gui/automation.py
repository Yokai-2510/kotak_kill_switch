import customtkinter as ctk
import json
import threading
from pathlib import Path
from gui.theme import Theme

class StepRow(ctk.CTkFrame):
    def __init__(self, parent, step_data, delete_callback):
        super().__init__(parent, fg_color=Theme.BG_CARD, height=50)
        self.pack(fill="x", pady=3)
        self.step_data = step_data.copy()
        
        # Layout: ID | Desc | Action | Dynamic (Expands) | Wait | On/Off | Del
        self.grid_columnconfigure(3, weight=1) 
        
        # 1. ID
        ctk.CTkLabel(self, text=str(step_data.get('id', '#')), font=("Arial", 12, "bold"), text_color=Theme.ACCENT_BLUE, width=30).grid(row=0, column=0, padx=5, pady=10)
        
        # 2. Description
        self.entry_desc = ctk.CTkEntry(self, placeholder_text="Description", width=140, fg_color="#2b2b2b")
        self.entry_desc.insert(0, step_data.get('description', 'Action'))
        self.entry_desc.grid(row=0, column=1, padx=5)

        # 3. Action Dropdown
        self.action_var = ctk.StringVar(value=step_data.get('action', 'keys'))
        self.combo_action = ctk.CTkOptionMenu(
            self, 
            values=["keys", "click", "input", "otp", "scroll"], 
            variable=self.action_var, 
            width=90, 
            fg_color="#333333",
            button_color="#444444",
            command=self._update_dynamic
        )
        self.combo_action.grid(row=0, column=2, padx=5)

        # 4. Dynamic Inputs (The expandable area)
        self.dynamic_frame = ctk.CTkFrame(self, fg_color="transparent", height=30)
        self.dynamic_frame.grid(row=0, column=3, sticky="ew", padx=5)
        self.inputs = {}
        self._update_dynamic(self.action_var.get())

        # 5. Wait
        ctk.CTkLabel(self, text="Wait:", font=Theme.FONT_SMALL, text_color=Theme.TEXT_GRAY).grid(row=0, column=4)
        self.entry_wait = ctk.CTkEntry(self, width=40)
        self.entry_wait.insert(0, str(step_data.get('wait', 1.0)))
        self.entry_wait.grid(row=0, column=5, padx=5)

        # 6. Toggle
        self.sw_enabled = ctk.CTkSwitch(self, text="", width=40, progress_color=Theme.ACCENT_GREEN)
        if step_data.get('enabled', True): self.sw_enabled.select()
        self.sw_enabled.grid(row=0, column=6, padx=5)

        # 7. Delete
        ctk.CTkButton(
            self, text="✕", width=30, 
            fg_color="#3f1313", text_color=Theme.ACCENT_RED, hover_color="#5c1b1b", 
            command=lambda: delete_callback(self)
        ).grid(row=0, column=7, padx=5)

    def _update_dynamic(self, action):
        for w in self.dynamic_frame.winfo_children(): w.destroy()
        self.inputs = {}
        
        # EXPANDED WIDTHS HERE
        if action == "click":
            c = self.step_data.get('coords') or {'x':0, 'y':0}
            self.inputs['x'] = self._mk_inp("X:", c.get('x'), 50)
            self.inputs['y'] = self._mk_inp("Y:", c.get('y'), 50)
            
        elif action == "keys":
            keys = ", ".join(self.step_data.get('keys') or [])
            # Broad input for keys
            self.inputs['keys'] = self._mk_inp("Keys:", keys, 300) 
            
        elif action == "input":
            # Credential key
            self.inputs['cred'] = self._mk_inp("Cred:", self.step_data.get('cred_key', ''), 120)
            # Keys after input
            keys = ", ".join(self.step_data.get('keys') or [])
            self.inputs['keys'] = self._mk_inp("Keys:", keys, 150)
            
        elif action == "scroll":
            self.inputs['rep'] = self._mk_inp("Repeats:", self.step_data.get('repeats', 1), 60)
            
        elif action == "otp":
            ctk.CTkLabel(self.dynamic_frame, text="Auto-fetches OTP from Gmail", text_color="gray", font=("Arial", 11)).pack(side="left", padx=5)

    def _mk_inp(self, lbl, val, w):
        f = ctk.CTkFrame(self.dynamic_frame, fg_color="transparent")
        f.pack(side="left", padx=5)
        ctk.CTkLabel(f, text=lbl, font=("Arial",10), text_color="gray").pack(side="left")
        e = ctk.CTkEntry(f, width=w, height=26)
        e.insert(0, str(val))
        e.pack(side="left", padx=(5,0))
        return e

    def get_data(self):
        d = self.step_data.copy()
        d.update({
            'description': self.entry_desc.get(),
            'action': self.action_var.get(),
            'enabled': bool(self.sw_enabled.get()),
            'wait': float(self.entry_wait.get() or 0)
        })
        act = d['action']
        if act == 'click':
            d['coords'] = {'x': int(self.inputs['x'].get()), 'y': int(self.inputs['y'].get())}
        elif act == 'keys':
            k = self.inputs['keys'].get()
            d['keys'] = [x.strip() for x in k.split(',')] if k else []
        elif act == 'input':
            d['cred_key'] = self.inputs['cred'].get()
            k = self.inputs['keys'].get()
            d['keys'] = [x.strip() for x in k.split(',')] if k else []
        elif act == 'scroll':
            d['repeats'] = int(self.inputs['rep'].get())
        return d

class AutomationEditor(ctk.CTkFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine
        self.user_id = engine.user_id
        self.rows = []
        
        # Header Controls
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.pack(fill="x", pady=10)
        
        ctk.CTkButton(
            head, text="+ ADD STEP", width=100, height=30,
            fg_color=Theme.ACCENT_GREEN, hover_color="#059669",
            font=("Arial", 12, "bold"),
            command=self.add_step
        ).pack(side="left")
        
        self.btn_save = ctk.CTkButton(
            head, text="SAVE CONFIG", width=120, height=30,
            fg_color=Theme.ACCENT_BLUE, hover_color="#1d4ed8",
            font=("Arial", 12, "bold"),
            command=self.save
        )
        self.btn_save.pack(side="right")

        # Steps List
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        
        # Load existing
        conf = self.engine.state['sys']['config']
        steps = conf.get('web_automation', {}).get('flow_steps', [])
        for s in steps: self._add_row_ui(s)

    def _add_row_ui(self, data):
        r = StepRow(self.scroll, data, self.delete_step)
        self.rows.append(r)

    def add_step(self):
        self._add_row_ui({'id': len(self.rows)+1, 'action':'keys', 'wait':1.0, 'enabled':True})

    def delete_step(self, widget):
        widget.destroy()
        if widget in self.rows: self.rows.remove(widget)

    def save(self):
        self.btn_save.configure(text="SAVING...", state="disabled")
        threading.Thread(target=self._save_worker, daemon=True).start()

    def _save_worker(self):
        try:
            new_steps = []
            for i, r in enumerate(self.rows):
                d = r.get_data()
                d['id'] = i + 1
                new_steps.append(d)
            
            # RAM Update
            with self.engine.state['sys']['lock']:
                self.engine.state['sys']['config'].setdefault('web_automation', {})['flow_steps'] = new_steps
            
            # Disk Update
            path = Path("source/config.json")
            with open(path, 'r') as f: data = json.load(f)
            if self.user_id in data:
                data[self.user_id].setdefault('web_automation', {})['flow_steps'] = new_steps
                with open(path, 'w') as f: json.dump(data, f, indent=2)

            self.after(0, lambda: self.btn_save.configure(text="SAVED!", fg_color=Theme.ACCENT_GREEN, state="normal"))
        except Exception as e:
            print(e)
            self.after(0, lambda: self.btn_save.configure(text="ERROR", fg_color=Theme.ACCENT_RED, state="normal"))
        
        self.after(2000, lambda: self.btn_save.configure(text="SAVE CONFIG", fg_color=Theme.ACCENT_BLUE))

class AutomationPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Automation Editor", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE).pack(anchor="w", padx=20, pady=(20, 10))
        
        self.tab = ctk.CTkTabview(
            self, 
            fg_color="transparent",
            segmented_button_fg_color=Theme.BG_CARD,
            segmented_button_selected_color=Theme.ACCENT_BLUE,
            segmented_button_unselected_color=Theme.BG_CARD,
            segmented_button_selected_hover_color=Theme.ACCENT_BLUE,
            text_color=Theme.TEXT_WHITE
        )
        self.tab.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        for eng in engines:
            name = eng.state['sys']['config'].get('account_name', eng.user_id)
            self.tab.add(name)
            AutomationEditor(self.tab.tab(name), eng).pack(fill="both", expand=True)