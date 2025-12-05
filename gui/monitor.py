import customtkinter as ctk
from gui.theme import Theme

# =========================================================
#  HELPER: DATA GRID ROW
# =========================================================
class GridRow(ctk.CTkFrame):
    """
    A single row that guarantees column alignment using Grid weights.
    """
    def __init__(self, parent, values, weights, colors=None, is_header=False):
        # Header gets a distinct background
        bg_color = "#2b2b2b" if is_header else "transparent"
        super().__init__(parent, fg_color=bg_color, corner_radius=0, height=35 if is_header else 30)
        self.pack(fill="x", pady=1)
        
        # Create columns based on weights
        for i, (val, weight) in enumerate(zip(values, weights)):
            self.grid_columnconfigure(i, weight=weight)
            
            # Styling
            if is_header:
                text_color = Theme.ACCENT_BLUE
                font = ("Arial", 11, "bold")
                anchor = "w" if i == 0 else "e" 
            else:
                text_color = Theme.TEXT_WHITE
                if colors and i < len(colors) and colors[i]:
                    text_color = colors[i]
                font = Theme.FONT_BODY
                anchor = "w" if i == 0 else "e" 

            # Padding
            pad_x = (10, 5) if anchor == "w" else (5, 10)

            lbl = ctk.CTkLabel(
                self, 
                text=str(val), 
                font=font,
                text_color=text_color,
                anchor=anchor
            )
            lbl.grid(row=0, column=i, sticky="nsew", padx=pad_x, pady=5)


# =========================================================
#  COMPONENT: REUSABLE TABLE WIDGET
# =========================================================
class TableWidget(ctk.CTkFrame):
    def __init__(self, parent, columns, weights, title=None):
        super().__init__(parent, fg_color=Theme.BG_CARD, corner_radius=8, border_width=1, border_color=Theme.BORDER)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) 

        # 1. Title
        if title:
            lbl = ctk.CTkLabel(self, text=title, font=("Arial", 12, "bold"), text_color=Theme.TEXT_WHITE)
            lbl.grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        # 2. Header Row
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=35)
        self.header_frame.grid(row=1, column=0, sticky="ew", padx=2)
        GridRow(self.header_frame, columns, weights, is_header=True)

        # 3. Scrollable Data Area
        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.grid(row=2, column=0, sticky="nsew", padx=2, pady=(0, 5))
        
        self.weights = weights 

    def clear(self):
        for widget in self.scroll_area.winfo_children():
            widget.destroy()

    def add_row(self, values, colors=None):
        GridRow(self.scroll_area, values, self.weights, colors)

    def show_message(self, text):
        self.clear()
        ctk.CTkLabel(self.scroll_area, text=text, text_color=Theme.TEXT_GRAY).pack(pady=20)


# =========================================================
#  COMPONENT: MONITOR TAB (PER USER)
# =========================================================
class MonitorTab(ctk.CTkFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine
        
        # --- MAIN LAYOUT (GRID) ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3) # Positions
        self.grid_rowconfigure(2, weight=2) # Orders

        # --- 1. USER SUMMARY HEADER ---
        self.summary_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=8, border_width=1, border_color=Theme.BORDER)
        self.summary_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 15))
        
        self.lbl_pnl_title = ctk.CTkLabel(self.summary_frame, text="REALIZED P&L", font=("Arial", 11, "bold"), text_color=Theme.TEXT_GRAY)
        self.lbl_pnl_title.pack(side="left", padx=(20, 5), pady=10)
        
        self.lbl_pnl_val = ctk.CTkLabel(self.summary_frame, text="₹ 0.00", font=("Arial", 16, "bold"), text_color=Theme.TEXT_WHITE)
        self.lbl_pnl_val.pack(side="left", padx=5, pady=10)

        self.lbl_orders_count = ctk.CTkLabel(self.summary_frame, text="Orders: 0", font=Theme.FONT_SMALL, text_color=Theme.TEXT_GRAY)
        self.lbl_orders_count.pack(side="right", padx=20, pady=10)

        # --- 2. POSITIONS TABLE ---
        pos_cols = ["SYMBOL", "NET QTY", "BUY AMT", "SELL AMT", "LTP", "P&L"]
        pos_weights = [3, 1, 1, 1, 1, 1]
        
        self.table_pos = TableWidget(self, pos_cols, pos_weights, title="OPEN POSITIONS")
        self.table_pos.grid(row=1, column=0, sticky="nsew", pady=(0, 15))

        # --- 3. ORDERS TABLE (FULL ORDER BOOK) ---
        # Changed "Active Stop-Loss Orders" to "Order Book"
        # Weights: Order ID needs more space
        ord_cols = ["ORDER ID", "TYPE", "SIDE", "STATUS", "TOKEN"]
        ord_weights = [3, 1, 1, 1, 1] 
        
        self.table_ord = TableWidget(self, ord_cols, ord_weights, title="ORDER BOOK")
        self.table_ord.grid(row=2, column=0, sticky="nsew")

    def update_data(self):
        """Refreshes the tables."""
        
        if not self.engine.is_active:
            self.table_pos.show_message("Account Disabled")
            self.table_ord.show_message("Account Disabled")
            return

        with self.engine.state['sys']['lock']:
            positions = self.engine.state['market']['positions']
            orders = self.engine.state['market']['orders']
            quotes = self.engine.state['market']['quotes']
            mtm = self.engine.state['risk']['mtm_current']

        # C. Update Header
        pnl_color = Theme.ACCENT_GREEN if mtm >= 0 else Theme.ACCENT_RED
        self.lbl_pnl_val.configure(text=f"₹ {mtm:,.2f}", text_color=pnl_color)
        self.lbl_orders_count.configure(text=f"Total Orders: {len(orders)}")

        # D. Update Positions Table
        self.table_pos.clear()
        if not positions:
            self.table_pos.show_message("No Open Positions")
        else:
            for p in positions:
                symbol = p.get('symbol', 'N/A')
                net_qty = p.get('net_qty', 0)
                buy_amt = p.get('total_buy_amt', 0)
                sell_amt = p.get('total_sell_amt', 0)
                token = p.get('token', '')
                ltp = quotes.get(token, 0.0)
                
                row_pnl = (sell_amt - buy_amt) + (net_qty * ltp)
                row_color = Theme.ACCENT_GREEN if row_pnl >= 0 else Theme.ACCENT_RED
                
                vals = [
                    symbol, 
                    str(net_qty), 
                    f"{buy_amt:.0f}", 
                    f"{sell_amt:.0f}", 
                    f"{ltp:.2f}", 
                    f"{row_pnl:.2f}"
                ]
                colors = [Theme.TEXT_WHITE, Theme.ACCENT_BLUE, None, None, None, row_color]
                self.table_pos.add_row(vals, colors)

        # E. Update Orders Table (SHOW ALL)
        self.table_ord.clear()
        
        if not orders:
            self.table_ord.show_message("Order Book Empty")
        else:
            # Show active orders first (optional logic, currently showing sequential)
            for o in orders:
                oid = o.get('order_id', 'N/A')
                otype = o.get('type', 'N/A')
                side = o.get('transaction_type', 'N/A')
                status = o.get('status', 'N/A')
                token = o.get('token', '')

                # Visuals
                side_color = Theme.ACCENT_GREEN if side in ['B', 'BUY'] else Theme.ACCENT_RED
                status_color = Theme.TEXT_GRAY
                
                if status == "COMPLETE": status_color = Theme.ACCENT_BLUE
                elif status == "REJECTED": status_color = Theme.ACCENT_RED
                elif status == "OPEN": status_color = Theme.ACCENT_GREEN
                elif status == "TRIGGER PENDING": status_color = Theme.ACCENT_ORANGE
                
                vals = [oid, otype, side, status, token]
                colors = [None, None, side_color, status_color, None]
                self.table_ord.add_row(vals, colors)


# =========================================================
#  PAGE: MAIN MONITOR CONTAINER
# =========================================================
class MonitorPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        self.engines = engines
        
        # Title
        title = ctk.CTkLabel(self, text="Live Market Monitor", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE)
        title.pack(anchor="w", padx=20, pady=(20, 10))

        # Styled Tab View
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
        
        self.tabs = {}
        
        for eng in engines:
            # Use Custom Name for Tab Title if available
            cfg_name = eng.state['sys']['config'].get('account_name', '')
            tab_name = cfg_name if cfg_name else eng.user_id
            
            self.tab_view.add(tab_name)
            
            monitor = MonitorTab(self.tab_view.tab(tab_name), eng)
            monitor.pack(fill="both", expand=True)
            self.tabs[tab_name] = monitor

        self.update_loop()

    def update_loop(self):
        current = self.tab_view.get()
        # Find the engine corresponding to the current tab name
        # (Since we might have renamed the tab from user_id to account_name)
        active_monitor = self.tabs.get(current)
        
        if active_monitor:
            try:
                active_monitor.update_data()
            except Exception: pass
        
        self.after(1000, self.update_loop)