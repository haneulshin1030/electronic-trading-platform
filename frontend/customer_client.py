import tkinter as tk
from tkinter import ttk

from orderbook import OrderBook

class CustomerClient(tk.Frame):
  def __init__(self, customer_id):
    self.customer_id = customer_id

    # Create root window: Customer Client inputs
    self.root = tk.Tk()
    self.root.title('Customer Client')
    self.root.geometry('400x250')

    tk.Label(self.root, text="Stock Symbol:").grid(row=0, column=0, padx=5, pady=5, sticky="W")
    self.symbol_input = tk.Entry(self.root)
    self.symbol_input.grid(row=0, column=1, padx=5, pady=5, sticky="W")
    
    tk.Label(self.root, text="Transaction Type:").grid(row=1, column=0, padx=5, pady=5, sticky="W")
    self.transaction_type = tk.StringVar(value="BUY")
    self.transaction_type_select = tk.OptionMenu(self.root, self.transaction_type, "BUY", "SELL")
    self.transaction_type_select.grid(row=1, column=1, padx=5, pady=5, sticky="W")
    
    tk.Label(self.root, text="Price:").grid(row=2, column=0, padx=5, pady=5, sticky="W")
    self.price_input = tk.Entry(self.root)
    self.price_input.grid(row=2, column=1, padx=5, pady=5, sticky="W")
    
    tk.Label(self.root, text="Quantity:").grid(row=3, column=0, padx=5, pady=5, sticky="W")
    self.quantity_input = tk.Entry(self.root)
    self.quantity_input.grid(row=3, column=1, padx=5, pady=5, sticky="W")
    
    self.positions_button = tk.Button(self.root, text="Post Order ->") #, command=self.show_positions_table)
    self.positions_button.grid(row=4, column=1, padx=5, pady=5, sticky="SE")


    # Create second window: Message Log
    self.window2 = tk.Toplevel(self.root)
    self.window2.title('Notification Log')
    self.window2.geometry('400x200+0+350')

    # HARDCODE TEST
    tk.Label(self.window2, text="").grid(row=0)
    tk.Label(self.window2, text="Posted an order to buy 100 shares of AAPL for $170.01/share.").grid(row=1)


    # Create third window: Open Orders Table
    self.window3 = tk.Toplevel(self.root)
    self.window3.title('Open Orders')
    self.window3.geometry('400x200+0+650')

    tk.Label(self.window3, text="").grid(row=0, columnspan=7)
    ttk.Separator(self.window3, orient="horizontal").grid(row=1, column=0, columnspan=7, sticky="ew")
    ttk.Separator(self.window3, orient="vertical").grid(row=2, column=0, rowspan=1, sticky="ns")
    tk.Label(self.window3, text="Stock").grid(row=2, column=1, sticky="W")
    ttk.Separator(self.window3, orient="vertical").grid(row=2, column=2, rowspan=1, sticky="ns")
    tk.Label(self.window3, text="Price").grid(row=2, column=3, sticky="W")
    ttk.Separator(self.window3, orient="vertical").grid(row=2, column=4, rowspan=1, sticky="ns")
    tk.Label(self.window3, text="Quantity").grid(row=2, column=5, sticky="W")
    ttk.Separator(self.window3, orient="vertical").grid(row=2, column=6, rowspan=1, sticky="ns")
    ttk.Separator(self.window3, orient="horizontal").grid(row=3, column=0, columnspan=7, sticky="ew")

    # HARDCODE TEST
    ttk.Separator(self.window3, orient="vertical").grid(row=4, column=0, rowspan=1, sticky="ns")
    tk.Label(self.window3, text="AAPL").grid(row=4, column=1, sticky="W")
    ttk.Separator(self.window3, orient="vertical").grid(row=4, column=2, rowspan=1, sticky="ns")
    tk.Label(self.window3, text="$40.62").grid(row=4, column=3, sticky="W")
    ttk.Separator(self.window3, orient="vertical").grid(row=4, column=4, rowspan=1, sticky="ns")
    tk.Label(self.window3, text="50").grid(row=4, column=5, sticky="W")
    ttk.Separator(self.window3, orient="vertical").grid(row=4, column=6, rowspan=1, sticky="ns")
    ttk.Separator(self.window3, orient="horizontal").grid(row=5, column=0, columnspan=7, sticky="ew")


    # Create fourth window: Positions Table
    self.window4 = tk.Toplevel(self.root)
    self.window4.title('Positions Table')
    self.window4.geometry('400x200+500+0')

    tk.Label(self.window4, text="").grid(row=0, columnspan=5)
    ttk.Separator(self.window4, orient="horizontal").grid(row=1, column=0, columnspan=5, sticky="ew")
    ttk.Separator(self.window4, orient="vertical").grid(row=2, column=0, rowspan=1, sticky="ns")
    tk.Label(self.window4, text="Stock").grid(row=2, column=1, sticky="W")
    ttk.Separator(self.window4, orient="vertical").grid(row=2, column=2, rowspan=1, sticky="ns")
    tk.Label(self.window4, text="Shares").grid(row=2, column=3, sticky="W")
    ttk.Separator(self.window4, orient="vertical").grid(row=2, column=4, rowspan=1, sticky="ns")
    ttk.Separator(self.window4, orient="horizontal").grid(row=3, column=0, columnspan=5, sticky="ew")

    # HARDCODE TEST
    ttk.Separator(self.window4, orient="vertical").grid(row=4, column=0, rowspan=1, sticky="ns")
    tk.Label(self.window4, text="AAPL").grid(row=4, column=1, sticky="W")
    ttk.Separator(self.window4, orient="vertical").grid(row=4, column=2, rowspan=1, sticky="ns")
    tk.Label(self.window4, text="50").grid(row=4, column=3, sticky="W")
    ttk.Separator(self.window4, orient="vertical").grid(row=4, column=4, rowspan=1, sticky="ns")
    ttk.Separator(self.window4, orient="horizontal").grid(row=5, column=0, columnspan=5, sticky="ew")


    # Create fifth window: Stock Symbol Lookup to open its corresponding orderbook
    self.window5 = tk.Toplevel(self.root)
    self.window5.title('Stock Lookup')
    self.window5.geometry('350x100+500+300')

    tk.Label(self.window5, text="Stock Symbol:").grid(row=0, column=0, padx=5, pady=5, sticky="W")
    self.symbol_input = tk.Entry(self.window5)
    self.symbol_input.grid(row=0, column=1, padx=5, pady=5, sticky="W")

    self.show_orderbook_button = tk.Button(self.window5, text="Open Orderbook ->", command=self.open_orderbook)
    self.show_orderbook_button.grid(row=2, column=1, padx=5, pady=5, sticky="SE")

    # Start the mainloop
    self.root.mainloop()

  def open_orderbook(self):
    self.stock_symbol = self.symbol_input.get()
    print(self.stock_symbol)
    self.orderbook_window = tk.Toplevel(self.root)
    title = 'Order Book: ' + self.stock_symbol
    self.orderbook_window.title(title)
    self.orderbook_window.geometry('350x200+500+500')

    # Create the table headers and lines
    tk.Label(self.orderbook_window, text=self.stock_symbol).grid(row=0, columnspan=5)
    ttk.Separator(self.orderbook_window, orient="horizontal").grid(row=1, column=0, columnspan=5, sticky="ew")
    tk.Label(self.orderbook_window, text="BUY").grid(row=2, column=0, columnspan=2)
    tk.Label(self.orderbook_window, text="SELL").grid(row=2, column=3, columnspan=2)
    ttk.Separator(self.orderbook_window, orient="vertical").grid(row=2, column=2, rowspan=1, sticky="ns")
    ttk.Separator(self.orderbook_window, orient="horizontal").grid(row=3, column=0, columnspan=5, sticky="ew")
    
    tk.Label(self.orderbook_window, text="Price").grid(row=4, column=0)
    ttk.Separator(self.orderbook_window, orient="vertical").grid(row=4, column=1, rowspan=1, sticky="ns")
    tk.Label(self.orderbook_window, text="Quantity").grid(row=4, column=1)
    ttk.Separator(self.orderbook_window, orient="vertical").grid(row=4, column=2, rowspan=1, sticky="ns")
    tk.Label(self.orderbook_window, text="Price").grid(row=4, column=3)
    ttk.Separator(self.orderbook_window, orient="vertical").grid(row=4, column=4, rowspan=1, sticky="ns")
    tk.Label(self.orderbook_window, text="Quantity").grid(row=4, column=4)
    ttk.Separator(self.orderbook_window, orient="horizontal").grid(row=5, column=0, columnspan=5, sticky="ew")

    # TODO: Load in real-time data

# EXAMPLE ON HOW TO RUN
CustomerClient("user1")
