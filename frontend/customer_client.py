import tkinter as tk
from tkinter import ttk, messagebox

class CustomerClient(tk.Frame):
  def __init__(self, parent, stock_symbol, customer_id):
    tk.Frame.__init__(self, parent)
    
    self.customer_id = customer_id
    self.stock_symbol = stock_symbol

    # Create root window: Customer Client inputs
    self.root = tk.Tk()
    self.root.title('Customer Client')
    self.root.geometry('400x250')

    tk.Label(self.root, text="Stock Symbol:").grid(row=0, column=0, padx=5, pady=5, sticky="W")
    self.symbol_input = tk.Entry(self.root)
    self.symbol_input.grid(row=0, column=1, padx=5, pady=5, sticky="W")
    
    tk.Label(self.root, text="Transaction Type:").grid(row=1, column=0, padx=5, pady=5, sticky="W")
    self.transaction_type = tk.StringVar()
    self.transaction_type.set("BUY")
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
    self.window2.geometry('400x200+0+300')

    # HARDCODE TEST
    tk.Label(self.window2, text="Posted an order to buy 100 shares of AAPL for $170.01/share.")

    # Create third window: Positions Table
    self.window3 = tk.Toplevel(self.root)
    self.window3.title('Positions Table')
    self.window3.geometry('400x200+0+500')



# For temporary testing
root = tk.Tk()
client = CustomerClient(root, "AAPL", "Cat").pack()
root.mainloop()
