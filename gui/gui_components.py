import customtkinter as ctk
from datetime import datetime

# ==================== THEME ENGINE ====================
class Colors:
    BG_BODY = "#0f111a"       # Deep Dark Background
    BG_SIDEBAR = "#181c2e"    # Sidebar
    BG_CARD = "#22283e"       # Cards/Panels
    BG_INPUT = "#151929"      # Inputs
    
    ACCENT = "#3b82f6"        # Blue
    ACCENT_HOVER = "#2563eb"
    
    SUCCESS = "#10b981"       # Green
    WARNING = "#f59e0b"       # Orange
    DANGER = "#ef4444"        # Red
    
    TEXT_MAIN = "#ffffff"
    TEXT_SUB = "#94a3b8"
    BORDER = "#2d3548"

# ==================== NAVIGATION & STATUS ====================

class NavButton(ctk.CTkButton):
    """Sidebar Navigation Button with Active Indicator"""
    def __init__(self, master, text, icon, command):
        super().__init__(
            master, text=f"  {icon}   {text}", command=command,
            fg_color="transparent", text_color=Colors.TEXT_SUB,
            hover_color=Colors.BG_CARD, anchor="w", height=45,
            font=("Roboto", 13, "bold"), corner_radius=8
        )
        self.icon = icon
        self.label = text

    def set_active(self, is_active):
        if is_active:
            self.configure(fg_color=Colors.BG_CARD, text_color=Colors.TEXT_MAIN, border_width=1, border_color=Colors.BORDER)
        else:
            self.configure(fg_color="transparent", text_color=Colors.TEXT_SUB, border_width=0)

class StatusBadge(ctk.CTkFrame):
    """Pulsing Status Indicator"""
    def __init__(self, master, status="INIT", color=Colors.TEXT_SUB):
        super().__init__(master, fg_color="transparent")
        self.dot = ctk.CTkLabel(self, text="●", font=("Arial", 18), text_color=color)
        self.dot.pack(side="left", padx=(0, 6))
        self.lbl = ctk.CTkLabel(self, text=status, font=("Roboto", 11, "bold"), text_color=color)
        self.lbl.pack(side="left")

    def update_status(self, status, color):
        self.lbl.configure(text=status, text_color=color)
        self.dot.configure(text_color=color)

# ==================== DATA DISPLAY ====================

class MetricCard(ctk.CTkFrame):
    def __init__(self, master, title, prefix="", suffix="", color=Colors.TEXT_MAIN):
        super().__init__(master, fg_color=Colors.BG_CARD, corner_radius=12, border_width=1, border_color=Colors.BORDER)
        self.prefix = prefix
        self.suffix = suffix
        
        ctk.CTkLabel(self, text=title.upper(), font=("Roboto", 10, "bold"), text_color=Colors.TEXT_SUB).pack(anchor="w", padx=15, pady=(15, 5))
        self.value_lbl = ctk.CTkLabel(self, text=f"{prefix}0{suffix}", font=("Roboto", 26, "bold"), text_color=color)
        self.value_lbl.pack(anchor="w", padx=15, pady=(0, 15))

    def set_value(self, value, color=None):
        txt = f"{self.prefix}{value:,.2f}{self.suffix}" if isinstance(value, (float, int)) else f"{value}"
        self.value_lbl.configure(text=txt)
        if color: self.value_lbl.configure(text_color=color)

class RiskBar(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color=Colors.BG_CARD, corner_radius=12, border_width=1, border_color=Colors.BORDER)
        
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(hdr, text="RISK CAPACITY", font=("Roboto", 11, "bold"), text_color=Colors.TEXT_SUB).pack(side="left")
        self.pct_lbl = ctk.CTkLabel(hdr, text="0%", font=("Roboto", 11, "bold"), text_color=Colors.SUCCESS)
        self.pct_lbl.pack(side="right")
        
        self.bar = ctk.CTkProgressBar(self, height=8, corner_radius=4)
        self.bar.set(0)
        self.bar.pack(fill="x", padx=20, pady=(5, 20))

    def set_risk(self, pct):
        self.bar.set(pct)
        self.pct_lbl.configure(text=f"{int(pct*100)}%")
        col = Colors.SUCCESS if pct < 0.5 else Colors.WARNING if pct < 0.8 else Colors.DANGER
        self.bar.configure(progress_color=col)
        self.pct_lbl.configure(text_color=col)

# ==================== CONFIGURATION WIDGETS ====================

class FormField(ctk.CTkFrame):
    """Label + Input Field"""
    def __init__(self, master, label, placeholder="", show=None):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="x", pady=5)
        
        ctk.CTkLabel(self, text=label, font=("Roboto", 12), text_color=Colors.TEXT_MAIN).pack(anchor="w", pady=(0, 2))
        self.entry = ctk.CTkEntry(self, placeholder_text=placeholder, show=show, 
                                  fg_color=Colors.BG_INPUT, border_color=Colors.BORDER, height=35)
        self.entry.pack(fill="x")

    def get(self): return self.entry.get()
    def set(self, val): 
        self.entry.delete(0, "end")
        self.entry.insert(0, str(val))

class AutomationStepRow(ctk.CTkFrame):
    """Visual Editor for a single Automation Step"""
    def __init__(self, master, step_data, delete_cb):
        super().__init__(master, fg_color=Colors.BG_INPUT, corner_radius=6, border_width=1, border_color=Colors.BORDER)
        self.pack(fill="x", pady=3)
        
        # Name
        self.ent_name = ctk.CTkEntry(self, width=120, height=28, font=("Consolas", 11), fg_color=Colors.BG_BODY, border_width=0)
        self.ent_name.insert(0, step_data.get("step", ""))
        self.ent_name.pack(side="left", padx=5, pady=5)

        # Type
        self.opt_type = ctk.CTkOptionMenu(self, width=80, height=28, values=["click", "input", "keys", "otp", "scroll"], 
                                          fg_color=Colors.BG_CARD, button_color=Colors.BORDER, font=("Consolas", 11))
        self.opt_type.set(step_data.get("type", "click"))
        self.opt_type.pack(side="left", padx=2)

        # Coords
        coords = step_data.get("coords") or {}
        self.ent_x = ctk.CTkEntry(self, width=40, height=28, placeholder_text="X", fg_color=Colors.BG_BODY, border_width=0)
        self.ent_x.insert(0, coords.get("x", ""))
        self.ent_x.pack(side="left", padx=2)
        
        self.ent_y = ctk.CTkEntry(self, width=40, height=28, placeholder_text="Y", fg_color=Colors.BG_BODY, border_width=0)
        self.ent_y.insert(0, coords.get("y", ""))
        self.ent_y.pack(side="left", padx=2)

        # Details
        self.ent_keys = ctk.CTkEntry(self, width=80, height=28, placeholder_text="Keys/Key", fg_color=Colors.BG_BODY, border_width=0)
        k_val = step_data.get("cred_key") or ",".join(step_data.get("keys", []))
        if k_val: self.ent_keys.insert(0, k_val)
        self.ent_keys.pack(side="left", padx=2, expand=True, fill="x")

        # Wait
        self.ent_wait = ctk.CTkEntry(self, width=35, height=28, placeholder_text="S", fg_color=Colors.BG_BODY, border_width=0)
        self.ent_wait.insert(0, str(step_data.get("wait", 1.0)))
        self.ent_wait.pack(side="left", padx=2)

        # Delete
        ctk.CTkButton(self, text="×", width=28, height=28, fg_color="transparent", hover_color=Colors.DANGER, 
                      text_color=Colors.DANGER, command=lambda: delete_cb(self)).pack(side="right", padx=2)

    def get_data(self):
        x, y = self.ent_x.get(), self.ent_y.get()
        coords = {"x": int(x), "y": int(y)} if x and y else None
        
        # Basic heuristic for keys vs cred_key based on type
        typ = self.opt_type.get()
        keys_val = self.ent_keys.get()
        keys = keys_val.split(",") if typ == "keys" and keys_val else None
        cred_key = keys_val if typ == "input" else None

        return {
            "step": self.ent_name.get(),
            "type": typ,
            "coords": coords,
            "keys": keys,
            "cred_key": cred_key,
            "wait": float(self.ent_wait.get() or 0)
        }