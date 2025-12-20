import customtkinter as ctk
import threading
from gui.theme import Theme
from kotak_api.exit_trade import exit_one_position

# =========================================================
#  HELPER: DATA GRID ROW (Updated for Widgets)
# =========================================================
class GridRow(ctk.CTkFrame):
    def __init__(self, parent, values, weights, colors=None, is_header=False):
        bg_color = "#2b2b2b" if is_header else "transparent"
        super().__init__(parent, fg_color=bg_color, corner_radius=0, height=35)
        self.pack(fill="x", pady=1)
        
        for i, (val, weight) in enumerate(zip(values, weights)):
            self.grid_columnconfigure(i, weight=weight)
            
            # Formatting
            if is_header:
                text_color = Theme.ACCENT_BLUE
                font = ("Arial", 11, "bold")
                anchor = "center" # Headers centered
            else:
                text_color = Theme.TEXT_WHITE
                if colors and i < len(colors) and colors[i]: text_color = colors[i]
                font = Theme.FONT_BODY
                anchor = "center"

            # Check if value is a Widget (Button) or Text
            if isinstance(val, ctk.CTkBaseClass):
                val.grid(row=0, column=i, sticky="ns", padx=2, pady=2)
            else:
                ctk.CTkLabel(self, text=str(val), font=font, text_color=text_color, anchor=anchor).grid(row=0, column=i, sticky="nsew", padx=5, pady=5)

# =========================================================
#  COMPONENT: TABLE WIDGET
# =========================================================
class TableWidget(ctk.CTkFrame):
    def __init__(self, parent, columns, weights, title=None):
        super().__init__(parent, fg_color=Theme.BG_CARD, corner_radius=8, border_width=1, border_color=Theme.BORDER)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) 

        if title:
            ctk.CTkLabel(self, text=title, font=("Arial", 12, "bold"), text_color=Theme.TEXT_WHITE).grid(row=0, column=0, sticky="w", padx=15, pady=(10, 5))

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent", height=35)
        self.header_frame.grid(row=1, column=0, sticky="ew", padx=2)
        GridRow(self.header_frame, columns, weights, is_header=True)

        self.scroll_area = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_area.grid(row=2, column=0, sticky="nsew", padx=2, pady=(0, 5))
        self.weights = weights 

    def clear(self):
        for widget in self.scroll_area.winfo_children(): widget.destroy()

    def add_row(self, values, colors=None):
        GridRow(self.scroll_area, values, self.weights, colors)

    def show_message(self, text):
        self.clear()
        ctk.CTkLabel(self.scroll_area, text=text, text_color=Theme.TEXT_GRAY).pack(pady=20)

# =========================================================
#  COMPONENT: MONITOR TAB
# =========================================================
class MonitorTab(ctk.CTkFrame):
    def __init__(self, parent, engine):
        super().__init__(parent, fg_color="transparent")
        self.engine = engine
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=3) # Positions
        self.grid_rowconfigure(2, weight=2) # Orders

        # 1. SUMMARY HEADER
        self.summary_frame = ctk.CTkFrame(self, fg_color=Theme.BG_CARD, corner_radius=8, border_width=1, border_color=Theme.BORDER)
        self.summary_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=(0, 15))
        
        ctk.CTkLabel(self.summary_frame, text="REALIZED P&L", font=("Arial", 11, "bold"), text_color=Theme.TEXT_GRAY).pack(side="left", padx=(20, 5), pady=10)
        self.lbl_pnl_val = ctk.CTkLabel(self.summary_frame, text="₹ 0.00", font=("Arial", 16, "bold"), text_color=Theme.TEXT_WHITE)
        self.lbl_pnl_val.pack(side="left", padx=5, pady=10)
        self.lbl_orders_count = ctk.CTkLabel(self.summary_frame, text="Orders: 0", font=Theme.FONT_SMALL, text_color=Theme.TEXT_GRAY)
        self.lbl_orders_count.pack(side="right", padx=20, pady=10)

        # 2. POSITIONS TABLE (Added ACTION Column)
        pos_cols = ["SYMBOL", "NET QTY", "LTP", "P&L", "ACTION"]
        pos_weights = [3, 1, 1, 1, 1] # Weights adjusted
        self.table_pos = TableWidget(self, pos_cols, pos_weights, title="OPEN POSITIONS")
        self.table_pos.grid(row=1, column=0, sticky="nsew", pady=(0, 15))

        # 3. ORDERS TABLE
        ord_cols = ["ORDER ID", "TYPE", "SIDE", "STATUS", "TOKEN"]
        ord_weights = [2, 1, 1, 2, 1] 
        self.table_ord = TableWidget(self, ord_cols, ord_weights, title="ORDER BOOK")
        self.table_ord.grid(row=2, column=0, sticky="nsew")

    def execute_exit(self, btn, p_data):
        """Callback for Manual Exit Button."""
        btn.configure(text="...", state="disabled", fg_color="#4b5563")
        
        # Calculate Logic
        net_qty = int(p_data['net_qty'])
        txn_type = "S" if net_qty > 0 else "B"
        
        def worker():
            success, msg = exit_one_position(
                self.engine.state, 
                p_data['token'], 
                abs(net_qty), 
                txn_type, 
                p_data['segment'],
                # Assuming Product is NRML or extracting if available, default NRML for safety
                'NRML' 
            )
            # Logs are handled in backend, UI updates on next poll
            print(f"Manual Exit: {msg}")

        threading.Thread(target=worker, daemon=True).start()

    def update_data(self):
        if not self.engine.state['signals']['system_active']:
            self.table_pos.show_message("Account Offline")
            self.table_ord.show_message("Account Offline")
            self.lbl_pnl_val.configure(text="--", text_color=Theme.TEXT_GRAY)
            return

        with self.engine.state['sys']['lock']:
            positions = self.engine.state['market']['positions']
            orders = self.engine.state['market']['orders']
            quotes = self.engine.state['market']['quotes']
            mtm = self.engine.state['risk']['mtm_current']

        # Header Update
        pnl_color = Theme.ACCENT_GREEN if mtm >= 0 else Theme.ACCENT_RED
        self.lbl_pnl_val.configure(text=f"₹ {mtm:,.2f}", text_color=pnl_color)
        self.lbl_orders_count.configure(text=f"Orders: {len(orders)}")

        # Positions Update
        self.table_pos.clear()
        if not positions:
            self.table_pos.show_message("No Open Positions")
        else:
            for p in positions:
                symbol = p.get('symbol', 'N/A')
                net_qty = p.get('net_qty', 0)
                
                # Skip closed positions (Net Qty 0)
                if net_qty == 0: continue

                buy_amt = p.get('total_buy_amt', 0)
                sell_amt = p.get('total_sell_amt', 0)
                token = p.get('token', '')
                ltp = quotes.get(token, 0.0)
                row_pnl = (sell_amt - buy_amt) + (net_qty * ltp)
                
                # Action Button
                btn_exit = ctk.CTkButton(
                    self.table_pos.scroll_area, 
                    text="CLOSE", 
                    width=60, 
                    height=24,
                    font=("Arial", 10, "bold"),
                    fg_color=Theme.ACCENT_ORANGE,
                    hover_color="#c2410c",
                    command=lambda b=None, data=p: self.execute_exit(b, data) # Trick to bind current loop var
                )
                # Fix lambda binding: The button instance isn't passed automatically in command
                # We need a wrapper. Since we create it fresh every second, 
                # we just bind the data. To change text, we need the widget reference.
                # Simplified: Passing 'btn_exit' explicitly via closure is tricky in loops.
                # We will just trigger the action and let the next polling cycle remove the row.
                btn_exit.configure(command=lambda btn=btn_exit, data=p: self.execute_exit(btn, data))

                vals = [symbol, str(net_qty), f"{ltp:.2f}", f"{row_pnl:.2f}", btn_exit]
                colors = [Theme.TEXT_WHITE, Theme.ACCENT_BLUE, None, Theme.ACCENT_GREEN if row_pnl >= 0 else Theme.ACCENT_RED, None]
                self.table_pos.add_row(vals, colors)

        # Orders Update
        self.table_ord.clear()
        if not orders:
            self.table_ord.show_message("Order Book Empty")
        else:
            # Sort by Order ID descending (newest first)
            sorted_orders = sorted(orders, key=lambda x: x.get('order_id', ''), reverse=True)
            for o in sorted_orders:
                oid = o.get('order_id', 'N/A')
                status = o.get('status', 'N/A')
                
                status_color = Theme.TEXT_GRAY
                if status == "COMPLETE": status_color = Theme.ACCENT_BLUE
                elif status == "REJECTED": status_color = Theme.ACCENT_RED
                elif status in ["OPEN", "TRIGGER PENDING"]: status_color = Theme.ACCENT_GREEN
                elif status == "PARTIALLY_FILLED": status_color = Theme.ACCENT_ORANGE
                
                vals = [oid, o.get('type'), o.get('transaction_type'), status, o.get('token')]
                colors = [None, None, Theme.ACCENT_GREEN if o.get('transaction_type') in ['B','BUY'] else Theme.ACCENT_RED, status_color, None]
                self.table_ord.add_row(vals, colors)

class MonitorPage(ctk.CTkFrame):
    def __init__(self, parent, engines):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Live Market Monitor", font=Theme.FONT_HEADER, text_color=Theme.TEXT_WHITE).pack(anchor="w", padx=20, pady=(20, 10))
        self.tab_view = ctk.CTkTabview(self, fg_color="transparent")
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.tabs = {}
        for eng in engines:
            cfg_name = eng.state['sys']['config'].get('account_name', '')
            tab_name = cfg_name if cfg_name else eng.user_id
            self.tab_view.add(tab_name)
            monitor = MonitorTab(self.tab_view.tab(tab_name), eng)
            monitor.pack(fill="both", expand=True)
            self.tabs[tab_name] = monitor
        self.update_loop()

    def update_loop(self):
        current = self.tab_view.get()
        if current in self.tabs:
            try: self.tabs[current].update_data()
            except: pass
        self.after(1000, self.update_loop)