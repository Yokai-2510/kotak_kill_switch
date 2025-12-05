import customtkinter as ctk

class Theme:
    # Colors
    BG_MAIN = "#111111"       # Deep Black background
    BG_CARD = "#1e1e1e"       # Card Surface
    BG_SIDEBAR = "#0f0f0f"    # Sidebar Surface
    
    # Button States
    BTN_ACTIVE = "#3b82f6"    # Blue (Selected)
    BTN_UNSELECTED = "#252525" # Dark Grey (Unselected) - NEW
    BTN_HOVER = "#333333"     # Hover state
    
    TEXT_WHITE = "#ffffff"
    TEXT_GRAY = "#9ca3af"     # Muted text
    
    ACCENT_BLUE = "#3b82f6"   
    ACCENT_RED = "#dc2626"    
    ACCENT_GREEN = "#10b981"  
    ACCENT_ORANGE = "#f59e0b" 
    
    BORDER = "#2f2f2f"        

    # Fonts
    FONT_HEADER = ("Arial", 20, "bold")
    FONT_TITLE = ("Arial", 16, "bold")
    FONT_BODY = ("Arial", 13)
    FONT_SMALL = ("Arial", 11)
    FONT_NUM = ("Arial", 18, "bold")