import customtkinter as ctk
import time
from gui.theme import Theme
from gui.dashboard import DashboardPage
from gui.monitor import MonitorPage
from gui.risk_config import RiskConfigPage
from gui.automation import AutomationPage
from gui.accounts import AccountsPage
from gui.status import StatusPage
from gui.settings import SettingsPage
from gui.logs_page import LogsPage  # <--- IMPORT NEW PAGE

class KillSwitchApp(ctk.CTk):
    def __init__(self, engines):
        super().__init__()
        self.engines = engines
        
        self.title("Kotak Kill Switch Portal")
        self.geometry("1440x900")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color=Theme.BG_MAIN)
        
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=260, fg_color=Theme.BG_SIDEBAR, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        ctk.CTkFrame(self.sidebar, width=1, fg_color=Theme.BORDER).place(relx=1, rely=0, relheight=1, anchor="ne")

        self.content_area = ctk.CTkFrame(self, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)

        self._build_sidebar_menu()

        # Loading Overlay
        self.loading_overlay = ctk.CTkFrame(self, fg_color=Theme.BG_MAIN, corner_radius=0)
        self.loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        self.loading_label = ctk.CTkLabel(self.loading_overlay, text="INITIALIZING SYSTEM...", font=("Arial", 24, "bold"), text_color=Theme.ACCENT_BLUE)
        self.loading_label.place(relx=0.5, rely=0.45, anchor="center")
        
        self.loading_sub = ctk.CTkLabel(self.loading_overlay, text="Preparing environment...", font=("Arial", 14), text_color=Theme.TEXT_GRAY)
        self.loading_sub.place(relx=0.5, rely=0.5, anchor="center")
        
        self.loading_bar = ctk.CTkProgressBar(self.loading_overlay, width=400, height=6, progress_color=Theme.ACCENT_BLUE, fg_color="#222222")
        self.loading_bar.place(relx=0.5, rely=0.55, anchor="center")
        self.loading_bar.set(0)

        self.pages = {}
        self.current_page_name = None
        self.after(200, self._deferred_loading)

    def _deferred_loading(self):
        page_list = [
            ("Dashboard", DashboardPage),
            ("Live Monitor", MonitorPage),
            ("Risk Config", RiskConfigPage),
            ("Automation", AutomationPage),
            ("Accounts", AccountsPage),
            ("System Logs", LogsPage),  # <--- REGISTER PAGE
            ("Settings", SettingsPage),
            ("Status", StatusPage)
        ]
        
        total_pages = len(page_list)
        for i, (name, ClassRef) in enumerate(page_list):
            progress = (i + 1) / total_pages
            self.loading_sub.configure(text=f"Loading module: {name}...")
            self.loading_bar.set(progress)
            self.update() 
            try:
                self.pages[name] = ClassRef(self.content_area, self.engines)
                self.pages[name].pack_forget()
            except Exception as e:
                print(f"Error loading {name}: {e}")
            time.sleep(0.05) 

        self.loading_sub.configure(text="Ready!")
        self.loading_bar.set(1.0)
        self.update()
        time.sleep(0.2)
        self.loading_overlay.destroy()
        self.show_page("Dashboard")

    def _build_sidebar_menu(self):
        title_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        title_frame.pack(pady=(40, 40), padx=25, fill="x")
        ctk.CTkLabel(title_frame, text="Kill Switch\nPortal", font=("Arial", 22, "bold"), justify="left", text_color=Theme.TEXT_WHITE).pack(anchor="w")

        self.nav_buttons = {}
        # ADD "System Logs" to menu items
        menu_items = [
            "Dashboard", "Live Monitor", "Risk Config", 
            "Automation", "Accounts", "System Logs", "Settings", "Status"
        ]
        
        for item in menu_items:
            btn = ctk.CTkButton(
                self.sidebar, 
                text=item,
                font=Theme.FONT_BODY,
                fg_color=Theme.BTN_UNSELECTED,
                text_color=Theme.TEXT_GRAY,
                hover_color=Theme.BTN_HOVER,
                anchor="w",
                height=45,
                corner_radius=8,
                command=lambda x=item: self.show_page(x)
            )
            btn.pack(pady=4, padx=15, fill="x")
            self.nav_buttons[item] = btn

        footer = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        footer.pack(side="bottom", pady=30, padx=30, fill="x")
        ctk.CTkLabel(footer, text="● System Active", font=("Arial", 12, "bold"), text_color=Theme.ACCENT_GREEN).pack(anchor="w")
        ctk.CTkLabel(footer, text="v2.0 Optimized", font=("Arial", 11), text_color=Theme.TEXT_GRAY).pack(anchor="w")

    def show_page(self, page_name):
        if self.current_page_name == page_name: return
        for name, btn in self.nav_buttons.items():
            if name == page_name:
                btn.configure(fg_color=Theme.BTN_ACTIVE, text_color=Theme.TEXT_WHITE, font=("Arial", 13, "bold"))
            else:
                btn.configure(fg_color=Theme.BTN_UNSELECTED, text_color=Theme.TEXT_GRAY, font=Theme.FONT_BODY)

        if self.current_page_name and self.current_page_name in self.pages:
            self.pages[self.current_page_name].pack_forget()

        if page_name in self.pages:
            self.pages[page_name].pack(fill="both", expand=True)
            self.current_page_name = page_name