import grpc
import threading
import sys
import time
import os
import pickle
from _thread import *

import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc

# from frontend.customer_client import CustomerClient
import tkinter as tk
from tkinter import ttk


HOST = "127.0.0.1"
PORT = 8000

# Record mapping index -> replica.
server_list = [f"{HOST}:{PORT}", f"{HOST}:{PORT + 1}", f"{HOST}:{PORT+ 2}"]

# # Global variable to store CustomerClient object
# customer_client = None


# GUI for customer client
class CustomerClient(tk.Frame):
    def __init__(self, username, password, stub):
        self.username = username
        self.password = password
        self.stub = stub

        self.last_modified_order_book = -1
        self.orderbook_window = -1
        self.stock_symbol = ""

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
        
        self.positions_button = tk.Button(self.root, text="Post Order ->", command=self.post_order)
        self.positions_button.grid(row=4, column=1, padx=5, pady=5, sticky="SE")


        # Create second window: Message Log
        self.window2 = tk.Toplevel(self.root)
        self.window2.title('Notification Log')
        self.window2.geometry('400x200+0+350')
        
        # Add scrollbar for Message Log
        scrollbar = tk.Scrollbar(self.window2)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget = tk.Text(self.window2, yscrollcommand=scrollbar.set)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_widget.yview)
        # text_widget.insert(tk.END, "TEST MESSAGE\n" * 20)

        # Create third window: Open Orders Table
        # self.window3 = tk.Toplevel(self.root)
        # self.window3.title('Open Orders')
        # self.window3.geometry('400x200+0+650')
        # self.window3_rows = 3

        # tk.Label(self.window3, text="").grid(row=0, columnspan=7)
        # ttk.Separator(self.window3, orient="horizontal").grid(row=1, column=0, columnspan=7, sticky="ew")
        # ttk.Separator(self.window3, orient="vertical").grid(row=2, column=0, rowspan=1, sticky="ns")
        # tk.Label(self.window3, text="Stock").grid(row=2, column=1, sticky="W")
        # ttk.Separator(self.window3, orient="vertical").grid(row=2, column=2, rowspan=1, sticky="ns")
        # tk.Label(self.window3, text="Price").grid(row=2, column=3, sticky="W")
        # ttk.Separator(self.window3, orient="vertical").grid(row=2, column=4, rowspan=1, sticky="ns")
        # tk.Label(self.window3, text="Quantity").grid(row=2, column=5, sticky="W")
        # ttk.Separator(self.window3, orient="vertical").grid(row=2, column=6, rowspan=1, sticky="ns")
        # ttk.Separator(self.window3, orient="horizontal").grid(row=3, column=0, columnspan=7, sticky="ew")

        # HARDCODE TEST
        # ttk.Separator(self.window3, orient="vertical").grid(row=4, column=0, rowspan=1, sticky="ns")
        # tk.Label(self.window3, text="AAPL").grid(row=4, column=1, sticky="W")
        # ttk.Separator(self.window3, orient="vertical").grid(row=4, column=2, rowspan=1, sticky="ns")
        # tk.Label(self.window3, text="$40.62").grid(row=4, column=3, sticky="W")
        # ttk.Separator(self.window3, orient="vertical").grid(row=4, column=4, rowspan=1, sticky="ns")
        # tk.Label(self.window3, text="50").grid(row=4, column=5, sticky="W")
        # ttk.Separator(self.window3, orient="vertical").grid(row=4, column=6, rowspan=1, sticky="ns")
        # ttk.Separator(self.window3, orient="horizontal").grid(row=5, column=0, columnspan=7, sticky="ew")


        # Create fourth window: Positions Table
        # self.window4 = tk.Toplevel(self.root)
        # self.window4.title('Positions Table')
        # self.window4.geometry('400x200+500+0')

        # tk.Label(self.window4, text="").grid(row=0, columnspan=5)
        # ttk.Separator(self.window4, orient="horizontal").grid(row=1, column=0, columnspan=5, sticky="ew")
        # ttk.Separator(self.window4, orient="vertical").grid(row=2, column=0, rowspan=1, sticky="ns")
        # tk.Label(self.window4, text="Stock").grid(row=2, column=1, sticky="W")
        # ttk.Separator(self.window4, orient="vertical").grid(row=2, column=2, rowspan=1, sticky="ns")
        # tk.Label(self.window4, text="Shares").grid(row=2, column=3, sticky="W")
        # ttk.Separator(self.window4, orient="vertical").grid(row=2, column=4, rowspan=1, sticky="ns")
        # ttk.Separator(self.window4, orient="horizontal").grid(row=3, column=0, columnspan=5, sticky="ew")

        # Create fifth window: Stock Symbol Lookup to open its corresponding orderbook
        self.window5 = tk.Toplevel(self.root)
        self.window5.title('Stock Lookup')
        # self.window5.geometry('350x100+500+300')
        self.window5.geometry('350x100+500+0')

        tk.Label(self.window5, text="Stock Symbol:").grid(row=0, column=0, padx=5, pady=5, sticky="W")
        self.lookup_symbol_input = tk.Entry(self.window5)
        self.lookup_symbol_input.grid(row=0, column=1, padx=5, pady=5, sticky="W")

        self.show_orderbook_button = tk.Button(self.window5, text="Open Orderbook ->", command=self.open_orderbook)
        self.show_orderbook_button.grid(row=2, column=1, padx=5, pady=5, sticky="SE")

        # Start the mainloop
        self.root.after(5000, self.update_everything)
        self.root.mainloop()

    def init_orderbook(self):
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

    def open_orderbook(self):
        self.stock_symbol = self.lookup_symbol_input.get()
        # print(stock_symbol)
        self.orderbook_window = tk.Toplevel(self.root)
        title = 'Order Book: ' + self.stock_symbol
        self.orderbook_window.title(title)
        # self.orderbook_window.geometry('350x500+500+500')
        self.orderbook_window.geometry('350x500+500+200')

        self.init_orderbook()
        self.orderbook_buy_rows = 6
        self.orderbook_sell_rows = 6

        # Show initial order_book
        with open("order_book.pickle", "rb") as f:
            order_book = pickle.load(f)
        # print(order_book)
        buy_orders = order_book[self.stock_symbol]['buy']
        sell_orders = order_book[self.stock_symbol]['sell']
        buy_count = 0
        sell_count = 0
        for price in sorted(buy_orders.keys(), reverse=True):
            if buy_count < 10:
                size = buy_orders[price]
                tk.Label(self.orderbook_window, text=str(round(price, 2))).grid(row=self.orderbook_buy_rows, column=0)
                tk.Label(self.orderbook_window, text=str(size)).grid(row=self.orderbook_buy_rows, column=1)
                ttk.Separator(self.orderbook_window, orient="vertical").grid(row=self.orderbook_buy_rows, column=2, rowspan=1, sticky="ns")
                ttk.Separator(self.orderbook_window, orient="horizontal").grid(row=self.orderbook_buy_rows+1, column=0, columnspan=5, sticky="ew")
                self.orderbook_buy_rows += 2
                buy_count += 1
        for price in sorted(sell_orders.keys()):
            if sell_count < 10:
                size = sell_orders[price]
                tk.Label(self.orderbook_window, text=str(round(price, 2))).grid(row=self.orderbook_sell_rows, column=3)
                tk.Label(self.orderbook_window, text=str(size)).grid(row=self.orderbook_sell_rows, column=4)
                ttk.Separator(self.orderbook_window, orient="vertical").grid(row=self.orderbook_sell_rows, column=2, rowspan=1, sticky="ns")
                ttk.Separator(self.orderbook_window, orient="horizontal").grid(row=self.orderbook_sell_rows+1, column=0, columnspan=5, sticky="ew")
                self.orderbook_sell_rows += 2
                sell_count += 1

        # initialize the last modification time
        self.last_modified_order_book = os.path.getmtime("order_book.pickle")

    def update_everything(self):
        self.current_modified_order_book = os.path.getmtime("order_book.pickle")

        if self.current_modified_order_book != self.last_modified_order_book:
            with open("order_book.pickle", "rb") as f:
                order_book = pickle.load(f)
            # print(order_book)

            # Clear window
            if self.orderbook_window != -1:
                for widget in self.orderbook_window.winfo_children():
                    widget.destroy()

            # Create the table headers and lines
            self.init_orderbook()
            self.orderbook_buy_rows = 6
            self.orderbook_sell_rows = 6

            # Sort order_book, show 10 rows max
            buy_orders = order_book[self.stock_symbol]['buy']
            sell_orders = order_book[self.stock_symbol]['sell']
            buy_count = 0
            sell_count = 0
            for price in sorted(buy_orders.keys(), reverse=True):
                if buy_count < 10:
                    size = buy_orders[price]
                    tk.Label(self.orderbook_window, text=str(round(price, 2))).grid(row=self.orderbook_buy_rows, column=0)
                    tk.Label(self.orderbook_window, text=str(size)).grid(row=self.orderbook_buy_rows, column=1)
                    ttk.Separator(self.orderbook_window, orient="vertical").grid(row=self.orderbook_buy_rows, column=2, rowspan=1, sticky="ns")
                    ttk.Separator(self.orderbook_window, orient="horizontal").grid(row=self.orderbook_buy_rows+1, column=0, columnspan=5, sticky="ew")
                    self.orderbook_buy_rows += 2
                    buy_count += 1
            for price in sorted(sell_orders.keys()):
                if sell_count < 10:
                    size = sell_orders[price]
                    tk.Label(self.orderbook_window, text=str(round(price, 2))).grid(row=self.orderbook_sell_rows, column=3)
                    tk.Label(self.orderbook_window, text=str(size)).grid(row=self.orderbook_sell_rows, column=4)
                    ttk.Separator(self.orderbook_window, orient="vertical").grid(row=self.orderbook_sell_rows, column=2, rowspan=1, sticky="ns")
                    ttk.Separator(self.orderbook_window, orient="horizontal").grid(row=self.orderbook_sell_rows+1, column=0, columnspan=5, sticky="ew")
                    self.orderbook_sell_rows += 2
                    sell_count += 1

            self.last_modified_order_book = self.current_modified_order_book

        self.root.after(2000, self.update_everything)


    def post_order(self):
        """
        1. Frontend: client hits "Post Order->" button
        2. Backend: order is added to 3 dictionaries: order_book, messages, positions
        3. Frontend: render updated order book, message log, and positions table
        """
        # Send params to backend
        opcode = self.transaction_type.get().lower()
        username = self.username
        password = self.password
        dir = opcode
        symbol = self.symbol_input.get()
        price = float(self.price_input.get())
        size = int(self.quantity_input.get())

        response = self.stub.ServerResponse(
            pb2.Order(
                opcode=opcode,
                username=username,
                password=password,
                symbol=symbol,
                dir=dir,
                price=price,
                size=size,
            )
        )
       

        # Real-time update message log
        order_message = "Posted an order to " + opcode + " " + str(size) + " shares of " + symbol + " for $" + str(price) +"/share.\n"
        self.add_message(order_message)

        if response.response[0] != 'P': # ensure no duplicate Posted messages in non-matched case
            print_response(response.response)
            self.add_message(response.response + "\n")

    def add_message(self,message):
        self.text_widget.insert(tk.END, message)


def listen(stub, username):
    """
    Listen for messages from other clients.
    """
    messages = stub.ClientMessages(pb2.Username(username=username))

    try:
        while True:
            # When a new message is found, iterate to it and print it.
            output = next(messages)
            print("RESPONSE:", output[0].response)
            print("ORDER BOOK:", output[1].order_book)
            print("POSITIONS:", output[1].positions)
    except:
        return


def leader_server():
    """
    Determines the leader server.
    """
    channel = None
    stub = None
    found = False
    while not found:
        for i, server_address in enumerate(server_list):
            try:
                # Create insecure channel to current server.
                channel = grpc.insecure_channel(server_address)
                stub = pb2_grpc.ChatStub(channel)

                # Send request to server to ask who the leader is.
                resp = stub.Leader(pb2.LeaderRequest())
                return resp.leader

            # If the server is not live, continue.
            except grpc._channel._InactiveRpcError:
                continue
        time.sleep(1)


def find_leader():
    """
    Determines which server is the leader.
    """
    channel = None
    stub = None
    connected_to_leader = False
    while not connected_to_leader:
        for i, addr in enumerate(server_list):
            try:
                channel = grpc.insecure_channel(addr)
                stub = pb2_grpc.ChatStub(channel)

                # Query for the leader server. If found, return.
                response = stub.Leader(pb2.LeaderRequest())
                print("Leader:", response.leader)
                return response.leader

            # server was not live, try next server
            except grpc._channel._InactiveRpcError:
                continue
        time.sleep(3)


class LeaderDisconnected(Exception):
    "The leader was disconnected."
    pass


# Error string for if the server is not the leader.
ERROR_NOT_LEADER = "Error: server is not the leader."


def print_response(response):
    """
    Check whether the response indicates that the server is not the leader, and raise an exception if so.
    Otherwise, print the response to the user.
    """
    if response == ERROR_NOT_LEADER:
        raise LeaderDisconnected
    else:
        print(response, flush=True)


def query():
    response = input().lower()
    return response in ["", "y", "ye", "yes"]


def main():
    listen_thread = None

    leader = find_leader()
    print(server_list[leader])
    channel = grpc.insecure_channel(server_list[leader])
    stub = pb2_grpc.ChatStub(channel)

    opcode = None
    username = None
    password = None

    # Prompt the client to either sign in or create a new account until success.
    while not username:
        print("Would you like to log in to an existing account? (Y/n)")

        if query():
            opcode = "login"
            username = input("Username: ")
            password = input("Password: ")
        else:
            opcode = "create"
            print("Please select a username.")
            username = input("Username: ")
            print("Please select a password satisfying the criterion.")
            password = input("Password: ")

        response = stub.ServerResponse(
            pb2.Order(
                opcode=opcode,
                username=username,
                password=password,
                symbol="",
                dir="",
                price=-1,
                size=-1,
            )
        )

        if not response.response.startswith("Success"):
            print_response(response.response)
            username = None

    print_response(response.response)

    listen_thread = threading.Thread(target=(listen), args=(stub, username))
    listen_thread.start()

    customer_client = CustomerClient(username, password, stub)
    
    # This code is not used anymore now that UI has been added
    while True:
        try:
            while True:
                request = input("\n>>> ")
                order_params = request.split(" ")
                if len(order_params) == 0:
                    continue

                # Initialize parameters of Order
                opcode = order_params[0]
                dir = ""
                symbol = ""
                price = -1
                size = -1

                # Parse client requests.

                # Create account.
                if opcode == "create":
                    username = order_params[1]
                    password = order_params[2]

                # Log in.
                elif opcode == "login":
                    username = order_params[1]
                    password = order_params[2]

                # Send message to a user.
                elif opcode == "buy" or opcode == "sell":
                    opcode, symbol, price, size = order_params
                    price = float(price)
                    size = int(size)
                    dir = opcode
            

                # Delete account
                # elif opcode == "delete":
                #   recipient = order_params[1]

                else:
                    if opcode != "":
                        print("Error: Invalid command.", flush=True)
                    continue

                response = stub.ServerResponse(
                    pb2.Order(
                        opcode=opcode,
                        username=username,
                        password=password,
                        symbol=symbol,
                        dir=dir,
                        price=price,
                        size=size,
                    )
                )
                print_response(response.response)

        # Exception for if the previous leader server went down and a new leader was determined.
        except (grpc._channel._InactiveRpcError, LeaderDisconnected):
            # Terminate the current listening thread and find a new leader.
            listen_thread.join()
            leader = find_leader()
            channel = grpc.insecure_channel(server_list[leader])
            stub = pb2_grpc.ChatStub(channel)

            # Start the listening thread.
            listen_thread = threading.Thread(target=(listen), args=(stub, username))
            listen_thread.start()

            print("Redirected to a new server; please repeat your request.")
            pass
        # Exception for if the user does a keyboard interrupt.
        except KeyboardInterrupt:
            try:
                response = stub.ServerResponse(
                    pb2.Order(
                        opcode="except",
                        username=username,
                        password="",
                        symbol="",
                        dir="",
                        price=-1,
                        size=-1,
                    )
                )
                print_response(response.response)
            except grpc._channel._InactiveRpcError:
                pass
            listen_thread.join()
            break


if __name__ == "__main__":
    main()
