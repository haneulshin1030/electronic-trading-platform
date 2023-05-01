import tkinter as tk
from tkinter import ttk, messagebox

class CustomerClient(tk.Frame):
  def __init__(self, parent, stock_symbol, customer_id):
    tk.Frame.__init__(self, parent)
    
    self.customer_id = customer_id
    self.stock_symbol = stock_symbol

    # Set window title
    self.winfo_toplevel().title("Customer Client")

    tk.Label(self, text="Stock Symbol:").grid(row=0, column=0, padx=5, pady=5, sticky="W")
    self.symbol_input = tk.Entry(self)
    self.symbol_input.grid(row=0, column=1, padx=5, pady=5, sticky="W")
    
    tk.Label(self, text="Transaction Type:").grid(row=1, column=0, padx=5, pady=5, sticky="W")
    self.transaction_type = tk.StringVar()
    self.transaction_type.set("BUY")
    self.transaction_type_select = tk.OptionMenu(self, self.transaction_type, "BUY", "SELL")
    self.transaction_type_select.grid(row=1, column=1, padx=5, pady=5, sticky="W")
    
    tk.Label(self, text="Price:").grid(row=2, column=0, padx=5, pady=5, sticky="W")
    self.price_input = tk.Entry(self)
    self.price_input.grid(row=2, column=1, padx=5, pady=5, sticky="W")
    
    tk.Label(self, text="Quantity:").grid(row=3, column=0, padx=5, pady=5, sticky="W")
    self.quantity_input = tk.Entry(self)
    self.quantity_input.grid(row=3, column=1, padx=5, pady=5, sticky="W")
    
    self.positions_button = tk.Button(self, text="Post Order ->", command=self.show_positions_table)
    self.positions_button.grid(row=4, column=1, padx=5, pady=5, sticky="SE")


# For temporary testing
root1 = tk.Tk()
client = CustomerClient(root, "AAPL", "Cat").pack()
root1.mainloop()