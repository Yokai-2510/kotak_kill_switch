import customtkinter as ctk
from tkinter import font

class DashboardModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#1a1a1a")
        self.setup_ui()
    
    def setup_ui(self):
        # Top section with Global MTM and Kill Switch
        top_frame = ctk.CTkFrame(self, fg_color="#0f0f0f", corner_radius=10, 
                                border_width=1, border_color="#1f1f1f")
        top_frame.pack(fill="x", padx=20, pady=20)
        
        # Left side - Global MTM
        left_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True, padx=30, pady=25)
        
        mtm_label = ctk.CTkLabel(left_frame, text="GLOBAL MTM", 
                                 font=("SF Pro Display", 13, "bold"), 
                                 text_color="#3b82f6")
        mtm_label.pack(anchor="w")
        
        mtm_value = ctk.CTkLabel(left_frame, text="$ 4,41.00", 
                                font=("SF Pro Display", 52, "bold"), 
                                text_color="#3b82f6")
        mtm_value.pack(anchor="w", pady=(8, 25))
        
        # MTM Details
        details_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        details_frame.pack(fill="x")
        
        # MTM Limit
        limit_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        limit_frame.pack(side="left", expand=True, fill="x")
        
        ctk.CTkLabel(limit_frame, text="MTM Limit", 
                    font=("SF Pro Display", 12), 
                    text_color="#6b7280").pack(anchor="w")
        ctk.CTkLabel(limit_frame, text="$ 10:500", 
                    font=("SF Pro Display", 22, "bold"), 
                    text_color="#3b82f6").pack(anchor="w", pady=(4, 0))
        
        # Remaining Buffer
        buffer_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        buffer_frame.pack(side="left", expand=True, fill="x", padx=(40, 0))
        
        ctk.CTkLabel(buffer_frame, text="Remaining Buffer", 
                    font=("SF Pro Display", 12), 
                    text_color="#6b7280").pack(anchor="w")
        
        buffer_value_frame = ctk.CTkFrame(buffer_frame, fg_color="transparent")
        buffer_value_frame.pack(anchor="w", fill="x", pady=(4, 8))
        
        ctk.CTkLabel(buffer_value_frame, text="$ 10:500", 
                    font=("SF Pro Display", 22, "bold"), 
                    text_color="#3b82f6").pack(side="left")
        
        # Progress bar
        progress_frame = ctk.CTkFrame(buffer_frame, fg_color="transparent")
        progress_frame.pack(fill="x")
        
        progress = ctk.CTkProgressBar(progress_frame, width=280, height=7,
                                     progress_color="#3b82f6",
                                     fg_color="#252525")
        progress.set(0.45)
        progress.pack(side="left")
        
        ctk.CTkLabel(progress_frame, text="45%", 
                    font=("SF Pro Display", 14, "bold"),
                    text_color="#ffffff").pack(side="left", padx=(15, 0))
        
        # Right side - Global Kill Button
        kill_button = ctk.CTkButton(top_frame, text="GLOBAL KILL",
                                    font=("SF Pro Display", 15, "bold"),
                                    fg_color="#dc2626",
                                    hover_color="#991b1b",
                                    corner_radius=8,
                                    width=190,
                                    height=60)
        kill_button.pack(side="right", padx=30, pady=25)
        
        # Accounts Grid
        accounts_frame = ctk.CTkFrame(self, fg_color="transparent")
        accounts_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Configure grid
        accounts_frame.grid_columnconfigure(0, weight=1)
        accounts_frame.grid_columnconfigure(1, weight=1)
        accounts_frame.grid_columnconfigure(2, weight=1)
        accounts_frame.grid_rowconfigure(0, weight=1)
        
        # Account A
        self.create_account_card(accounts_frame, "Account A", "Online", 
                                "₹3 000", "₹7 000", "₹7 000", 
                                "SAFE", 30, "#3b82f6", 0, 0)
        
        # Account B
        self.create_account_card(accounts_frame, "Account B", "Online", 
                                "-₹9 100", "-₹10 000", "₹900", 
                                "HIT", 91, "#dc2626", 0, 1)
        
        # Account C
        self.create_account_card(accounts_frame, "Account C", "Disabled", 
                                "N/A", "₹0 000", "N/A", 
                                None, 0, "#4b5563", 0, 2, disabled=True)
    
    def create_account_card(self, parent, name, status, current_mtm, 
                           mtm_limit, remaining, sl_status, sl_percent, 
                           color, row, col, disabled=False):
        card = ctk.CTkFrame(parent, fg_color="#0f0f0f", corner_radius=10,
                          border_width=1, border_color="#1f1f1f")
        card.grid(row=row, column=col, padx=10, pady=0, sticky="nsew")
        
        # Header
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=22, pady=(22, 15))
        
        ctk.CTkLabel(header, text=name, 
                    font=("SF Pro Display", 22, "bold"),
                    text_color="#ffffff").pack(side="left")
        
        status_color = "#dc2626" if status == "Online" and current_mtm.startswith("-") else "#3b82f6"
        if disabled:
            status_color = "#4b5563"
            
        status_label = ctk.CTkLabel(header, text=status,
                                   font=("SF Pro Display", 13, "bold"),
                                   text_color=status_color)
        status_label.pack(side="right")
        
        # Status indicator line
        indicator = ctk.CTkFrame(card, height=2, fg_color=status_color)
        indicator.pack(fill="x", padx=22)
        
        # Metrics
        metrics_frame = ctk.CTkFrame(card, fg_color="transparent")
        metrics_frame.pack(fill="x", padx=22, pady=18)
        
        # Current MTM
        self.create_metric(metrics_frame, "Current MTM", current_mtm, 
                          "#dc2626" if current_mtm.startswith("-") else "#3b82f6")
        
        # MTM Limit
        self.create_metric(metrics_frame, "MTM Limit", mtm_limit, "#6b7280")
        
        # Remaining
        self.create_metric(metrics_frame, "Remaining", remaining, "#6b7280")
        
        # Progress bar section
        progress_section = ctk.CTkFrame(card, fg_color="transparent")
        progress_section.pack(fill="x", padx=22, pady=(8, 18))
        
        if not disabled and sl_status:
            # Progress bar
            progress = ctk.CTkProgressBar(progress_section, height=7,
                                         progress_color=color,
                                         fg_color="#252525")
            progress.set(sl_percent / 100)
            progress.pack(fill="x", pady=(0, 12))
            
            # SL Status
            sl_frame = ctk.CTkFrame(progress_section, fg_color="transparent")
            sl_frame.pack(fill="x")
            
            ctk.CTkLabel(sl_frame, text=f"SL: {sl_status}",
                        font=("SF Pro Display", 13, "bold"),
                        text_color=color).pack(side="left")
            
            ctk.CTkLabel(sl_frame, text=f"{sl_percent}%",
                        font=("SF Pro Display", 13, "bold"),
                        text_color="#ffffff").pack(side="right")
        else:
            # Empty progress bar for disabled
            empty_progress = ctk.CTkProgressBar(progress_section, height=7,
                                               progress_color="#4b5563",
                                               fg_color="#252525")
            empty_progress.set(0)
            empty_progress.pack(fill="x", pady=(0, 12))
            
            sl_frame = ctk.CTkFrame(progress_section, fg_color="transparent")
            sl_frame.pack(fill="x")
            
            ctk.CTkLabel(sl_frame, text="SL",
                        font=("SF Pro Display", 13, "bold"),
                        text_color="#4b5563").pack(side="left")
            
            ctk.CTkLabel(sl_frame, text="0%",
                        font=("SF Pro Display", 13, "bold"),
                        text_color="#4b5563").pack(side="right")
        
        # Buttons
        buttons_frame = ctk.CTkFrame(card, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=22, pady=(0, 22))
        
        if disabled:
            enable_btn = ctk.CTkButton(buttons_frame, text="ENABLE",
                                      font=("SF Pro Display", 13, "bold"),
                                      fg_color="#3b82f6",
                                      hover_color="#2563eb",
                                      corner_radius=7,
                                      height=42)
            enable_btn.pack(fill="x")
        else:
            kill_btn = ctk.CTkButton(buttons_frame, text="KILL",
                                    font=("SF Pro Display", 13, "bold"),
                                    fg_color="#252525",
                                    hover_color="#333333",
                                    text_color="#ffffff",
                                    corner_radius=7,
                                    height=42,
                                    border_width=1,
                                    border_color="#2f2f2f")
            kill_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))
            
            pause_btn = ctk.CTkButton(buttons_frame, text="PAUSE",
                                     font=("SF Pro Display", 13, "bold"),
                                     fg_color="#252525",
                                     hover_color="#333333",
                                     text_color="#ffffff",
                                     corner_radius=7,
                                     height=42,
                                     border_width=1,
                                     border_color="#2f2f2f")
            pause_btn.pack(side="right", fill="x", expand=True, padx=(6, 0))
    
    def create_metric(self, parent, label, value, value_color):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=7)
        
        ctk.CTkLabel(frame, text=label,
                    font=("SF Pro Display", 13),
                    text_color="#6b7280").pack(side="left")
        
        ctk.CTkLabel(frame, text=value,
                    font=("SF Pro Display", 17, "bold"),
                    text_color=value_color).pack(side="right")


class RiskControlsModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#1a1a1a")
        label = ctk.CTkLabel(self, text="Risk Controls Module - Coming Soon",
                           font=("SF Pro Display", 24, "bold"))
        label.pack(expand=True)


class AccountsModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#1a1a1a")
        label = ctk.CTkLabel(self, text="Accounts Module - Coming Soon",
                           font=("SF Pro Display", 24, "bold"))
        label.pack(expand=True)


class ConfigurationModule(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="#1a1a1a")
        label = ctk.CTkLabel(self, text="Configuration Module - Coming Soon",
                           font=("SF Pro Display", 24, "bold"))
        label.pack(expand=True)


class KillSwitchApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Kotak Kill Switch Commander")
        self.geometry("1440x920")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Configure grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.create_sidebar()
        
        # Main content
        self.content_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # Show dashboard by default
        self.current_module = None
        self.show_module("Dashboard")
    
    def create_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=280, fg_color="#0f0f0f", corner_radius=0,
                             border_width=0)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        
        # Add subtle right border
        border = ctk.CTkFrame(sidebar, width=1, fg_color="#1f1f1f")
        border.place(relx=1, rely=0, relheight=1, anchor="ne")
        
        # Title card
        title_card = ctk.CTkFrame(sidebar, fg_color="#141414", corner_radius=10,
                                border_width=1, border_color="#1f1f1f")
        title_card.pack(pady=(25, 20), padx=18, fill="x")
        
        title_inner = ctk.CTkFrame(title_card, fg_color="transparent")
        title_inner.pack(padx=18, pady=18)
        
        title = ctk.CTkLabel(title_inner, text="Kotak Kill Switch\nCommander",
                           font=("SF Pro Display", 19, "bold"),
                           justify="left",
                           text_color="#ffffff")
        title.pack(anchor="w")
        
        # Menu items container
        menu_container = ctk.CTkFrame(sidebar, fg_color="transparent")
        menu_container.pack(fill="x", padx=18)
        
        # Menu items
        self.menu_buttons = {}
        menu_items = ["Dashboard", "Risk Controls", "Accounts", "Configuration"]
        
        for item in menu_items:
            btn = ctk.CTkButton(menu_container, text=item,
                               font=("SF Pro Display", 14, "normal"),
                               fg_color="transparent",
                               hover_color="#1a1a1a",
                               anchor="w",
                               height=46,
                               border_width=0,
                               corner_radius=8,
                               command=lambda x=item: self.show_module(x))
            btn.pack(fill="x", pady=2)
            self.menu_buttons[item] = btn
        
        # Status card at bottom
        status_card = ctk.CTkFrame(sidebar, fg_color="#141414", corner_radius=10,
                                 border_width=1, border_color="#1f1f1f")
        status_card.pack(side="bottom", pady=25, padx=18, fill="x")
        
        status_inner = ctk.CTkFrame(status_card, fg_color="transparent")
        status_inner.pack(padx=18, pady=15)
        
        # Version
        ctk.CTkLabel(status_inner, text="Version 1.0",
                    font=("SF Pro Display", 12),
                    text_color="#6b7280").pack(anchor="w")
        
        # Status with dot
        status_container = ctk.CTkFrame(status_inner, fg_color="transparent")
        status_container.pack(anchor="w", pady=(6, 0))
        
        status_dot = ctk.CTkLabel(status_container, text="●",
                                 font=("SF Pro Display", 14),
                                 text_color="#10b981")
        status_dot.pack(side="left")
        
        ctk.CTkLabel(status_container, text=" ACTIVE",
                    font=("SF Pro Display", 12, "bold"),
                    text_color="#10b981").pack(side="left")
    
    def show_module(self, module_name):
        # Update button colors
        for name, btn in self.menu_buttons.items():
            if name == module_name:
                btn.configure(fg_color="#3b82f6", 
                            hover_color="#2563eb",
                            text_color="#ffffff",
                            font=("SF Pro Display", 14, "bold"))
            else:
                btn.configure(fg_color="transparent",
                            hover_color="#1a1a1a",
                            text_color="#9ca3af",
                            font=("SF Pro Display", 14, "normal"))
        
        # Clear current content
        if self.current_module:
            self.current_module.destroy()
        
        # Show selected module
        if module_name == "Dashboard":
            self.current_module = DashboardModule(self.content_frame)
        elif module_name == "Risk Controls":
            self.current_module = RiskControlsModule(self.content_frame)
        elif module_name == "Accounts":
            self.current_module = AccountsModule(self.content_frame)
        elif module_name == "Configuration":
            self.current_module = ConfigurationModule(self.content_frame)
        
        self.current_module.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = KillSwitchApp()
    app.mainloop()