import tkinter as tk
from tkinter import ttk, messagebox

class OrderBook(tk.Frame):
  def __init__(self, parent, stock_symbol):
    tk.Frame.__init__(self, parent)
    
    self.stock_symbol = stock_symbol

    # Set window title
    self.winfo_toplevel().title("Order Book")
    
    # # Create the table headers and lines
    tk.Label(self, text=self.stock_symbol).grid(row=0, columnspan=5)
    ttk.Separator(self, orient="horizontal").grid(row=1, column=0, columnspan=5, sticky="ew")
    tk.Label(self, text="BUY").grid(row=2, column=0, columnspan=2)
    tk.Label(self, text="SELL").grid(row=2, column=3, columnspan=2)
    ttk.Separator(self, orient="vertical").grid(row=2, column=2, rowspan=1, sticky="ns")
    ttk.Separator(self, orient="horizontal").grid(row=3, column=0, columnspan=5, sticky="ew")
    
    tk.Label(self, text="Price").grid(row=4, column=0)
    ttk.Separator(self, orient="vertical").grid(row=4, column=1, rowspan=1, sticky="ns")
    tk.Label(self, text="Quantity").grid(row=4, column=1)
    ttk.Separator(self, orient="vertical").grid(row=4, column=2, rowspan=1, sticky="ns")
    tk.Label(self, text="Price").grid(row=4, column=3)
    ttk.Separator(self, orient="vertical").grid(row=4, column=4, rowspan=1, sticky="ns")
    tk.Label(self, text="Quantity").grid(row=4, column=4)
    ttk.Separator(self, orient="horizontal").grid(row=5, column=0, columnspan=5, sticky="ew")

    # HARDCODE TEST: Create the rows for the BUY and SELL data
    tk.Label(self, text="$40.2").grid(row=6, column=0)
    tk.Label(self, text="50").grid(row=6, column=1)
    tk.Label(self, text="$43.8").grid(row=6, column=3)
    tk.Label(self, text="20").grid(row=6, column=4)
    ttk.Separator(self, orient="vertical").grid(row=6, column=2, rowspan=1, sticky="ns")
    ttk.Separator(self, orient="horizontal").grid(row=7, column=0, columnspan=5, sticky="ew")
    
    # Add padding to the frame
    self.grid(padx=10, pady=10)


# For temporary testing
root = tk.Tk()
order_book = OrderBook(root, "AAPL")
order_book.pack()
root.mainloop()