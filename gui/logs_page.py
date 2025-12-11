import customtkinter as ctk
import os
from gui.theme import Theme

class LogsPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        self.engines = engines
        self.current_engine = engines[0] if engines else None
        
        # --- HEADER ROW ---
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header, text="System Logs", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE).pack(side="left")

        # --- FILTERS ROW ---
        filters = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, border_width=1, border_color=Theme.BORDER)
        filters.pack(fill="x", padx=20, pady=(0, 10))
        
        # Account Selector
        ctk.CTkLabel(filters, text="Account:", font=("Arial", 11), text_color=Theme.TEXT_GRAY).pack(side="left", padx=(10, 5), pady=10)
        self.combo_acc = ctk.CTkOptionMenu(
            filters, values=[e.user_id for e in engines], 
            width=120, height=28, command=self.change_account
        )
        self.combo_acc.pack(side="left", padx=5)

        # Category Selector
        ctk.CTkLabel(filters, text="Category:", font=("Arial", 11), text_color=Theme.TEXT_GRAY).pack(side="left", padx=(15, 5))
        self.combo_cat = ctk.CTkOptionMenu(
            filters, values=["ALL", "SYS", "AUTH", "RISK", "DATA", "AUTO", "SVC"],
            width=100, height=28, command=self.refresh_logs
        )
        self.combo_cat.set("ALL")
        self.combo_cat.pack(side="left", padx=5)
        
        # Auto Scroll Switch
        self.sw_scroll = ctk.CTkSwitch(filters, text="Auto-Scroll", onvalue=True, offvalue=False)
        self.sw_scroll.select()
        self.sw_scroll.pack(side="right", padx=15)

        # --- LOG DISPLAY AREA ---
        self.text_area = ctk.CTkTextbox(
            self, 
            fg_color="#000000", 
            text_color="#00ff00", 
            font=("Consolas", 12),
            activate_scrollbars=True
        )
        self.text_area.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.text_area.configure(state="disabled")

        self.last_pos = 0
        self.update_loop()

    def change_account(self, value):
        for e in self.engines:
            if e.user_id == value:
                self.current_engine = e
                self.text_area.configure(state="normal")
                self.text_area.delete("1.0", "end")
                self.text_area.configure(state="disabled")
                self.last_pos = 0
                self.refresh_logs()
                break

    def refresh_logs(self, _=None):
        # Trigger immediate refresh
        self.update_log_display()

    def update_loop(self):
        self.update_log_display()
        self.after(2000, self.update_loop)

    def update_log_display(self):
        if not self.current_engine: return
        
        log_path = f"logs/{self.current_engine.user_id}.log"
        if not os.path.exists(log_path): return

        cat_filter = self.combo_cat.get()
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                # Simple optimization: If file got smaller (rotated), reset
                f.seek(0, 2)
                size = f.tell()
                if size < self.last_pos: self.last_pos = 0
                
                # If we are filtering, we must read whole file (expensive but necessary)
                # If "ALL", we can just read tail
                if cat_filter != "ALL":
                    f.seek(0)
                    lines = f.readlines()
                    filtered = [l for l in lines if f"[{cat_filter}" in l or "[SYS,INIT]" in l]
                    # Logic to only append new filtered lines is complex, 
                    # so for filtered view we just rewrite the buffer (okay for <1MB)
                    content = "".join(filtered[-500:]) # Show last 500 matches
                    
                    self.text_area.configure(state="normal")
                    self.text_area.delete("1.0", "end")
                    self.text_area.insert("end", content)
                    self.text_area.configure(state="disabled")
                
                else:
                    # Efficient Tail Read
                    f.seek(self.last_pos)
                    new_data = f.read()
                    if new_data:
                        self.last_pos = f.tell()
                        self.text_area.configure(state="normal")
                        self.text_area.insert("end", new_data)
                        self.text_area.configure(state="disabled")
                        
                        if self.sw_scroll.get():
                            self.text_area.see("end")

        except Exception:
            pass