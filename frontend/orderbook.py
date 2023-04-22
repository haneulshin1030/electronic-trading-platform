import tkinter as tk
from tkinter import messagebox

class OrderBook(tk.Frame):
  def __init__(self, parent, stock_symbol):
    tk.Frame.__init__(self, parent)
    
    self.stock_symbol = stock_symbol
    
    # Create the table headers
    tk.Label(self, text=self.stock_symbol).grid(row=0, columnspan=4)
    tk.Label(self, text="BUY").grid(row=1, column=0, columnspan=2)
    tk.Label(self, text="SELL").grid(row=1, column=2, columnspan=2)
    tk.Label(self, text="Price").grid(row=2, column=0)
    tk.Label(self, text="Quantity").grid(row=2, column=1)
    tk.Label(self, text="Price").grid(row=2, column=2)
    tk.Label(self, text="Quantity").grid(row=2, column=3)

    # Draw lines between rows and columns for headers
    # self.canvas = tk.Canvas(self)
    # self.canvas.create_line(0, 0, 100, 0, fill="#000000")

    # HARDCODE TEST: Create the rows for the BUY and SELL data
    tk.Label(self, text="$40.2").grid(row=3, column=0)
    tk.Label(self, text="50").grid(row=3, column=1)
    tk.Label(self, text="$43.8").grid(row=3, column=2)
    tk.Label(self, text="20").grid(row=3, column=3)
    
    # Add padding to the frame
    self.grid(padx=10, pady=10)


# For temporary testing
root = tk.Tk()
order_book = OrderBook(root, "AAPL")
order_book.pack()
root.mainloop()