import customtkinter as ctk
import random
from datetime import datetime
from gui_components import Colors, NavButton, StatusBadge
from gui_views import DashboardView, SettingsView, AccountsView

# --- MOCK DATABASE ---
DB = {
    "Account 1 (Main)": {
        "limit": "-10000", "poll": "1", "sl_req": True, "mobile": "9998887776",
        "steps": [
            {"step": "login", "type": "input", "cred_key": "mobile", "keys": ["Enter"]},
            {"step": "otp", "type": "otp", "wait": 2.0}
        ]
    },
    "Account 2 (Hedge)": {
        "limit": "-5000", "poll": "3", "sl_req": False, "mobile": "8881112223",
        "steps": []
    }
}

class KillSwitchApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Kill Switch Commander")
        self.geometry("1280x800")
        ctk.set_appearance_mode("Dark")
        self.configure(fg_color=Colors.BG_BODY)

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- SIDEBAR ---
        self.sidebar = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=Colors.BG_SIDEBAR)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)

        # Brand
        ctk.CTkLabel(self.sidebar, text="🛡️", font=("Arial", 32)).pack(pady=(40, 10))
        ctk.CTkLabel(self.sidebar, text="KILL SWITCH", font=("Roboto", 16, "bold"), text_color=Colors.TEXT_MAIN).pack()
        ctk.CTkLabel(self.sidebar, text="PRO v2.1", font=("Roboto", 10), text_color=Colors.TEXT_SUB).pack(pady=(0, 40))

        # Navigation
        self.nav_btns = {}
        self.views = {}
        
        # View Container
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

        # Initialize Views
        self.views["dashboard"] = DashboardView(self.main_area)
        self.views["accounts"] = AccountsView(self.main_area)
        self.views["settings"] = SettingsView(self.main_area, DB)

        # Create Buttons
        self.add_nav("dashboard", "Monitor", "📊")
        self.add_nav("accounts", "Accounts", "👥")
        self.add_nav("settings", "Config", "⚙️")

        # Footer
        self.footer = ctk.CTkFrame(self.sidebar, fg_color=Colors.BG_CARD, corner_radius=10, border_width=1, border_color=Colors.BORDER)
        self.footer.pack(side="bottom", fill="x", padx=15, pady=20)
        
        self.status = StatusBadge(self.footer, "ACTIVE", Colors.SUCCESS)
        self.status.pack(pady=10)
        self.clock = ctk.CTkLabel(self.footer, text="00:00:00", font=("Consolas", 12), text_color=Colors.TEXT_SUB)
        self.clock.pack(pady=(0, 10))

        # Start
        self.show("dashboard")
        self.update_loop()

    def add_nav(self, key, text, icon):
        btn = NavButton(self.sidebar, text, icon, lambda: self.show(key))
        btn.pack(fill="x", padx=15, pady=5)
        self.nav_btns[key] = btn

    def show(self, key):
        for k, btn in self.nav_btns.items(): btn.set_active(k == key)
        for k, view in self.views.items():
            if k == key: view.pack(fill="both", expand=True)
            else: view.pack_forget()

    def update_loop(self):
        # Mock Clock
        self.clock.configure(text=datetime.now().strftime("%H:%M:%S"))
        
        # Mock Dashboard Data
        dash = self.views["dashboard"]
        mtm = -random.randint(0, 12000)
        dash.card_mtm.set_value(mtm, Colors.DANGER if mtm < 0 else Colors.SUCCESS)
        dash.risk_bar.set_risk(min(abs(mtm)/10000, 1.0))
        
        # Random Log
        if random.random() > 0.98:
            dash.log(f"Heartbeat check... OK [{datetime.now().strftime('%H:%M:%S')}]")

        self.after(1000, self.update_loop)

if __name__ == "__main__":
    KillSwitchApp().mainloop()