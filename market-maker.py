import grpc
import threading
import sys
import os
import numpy as np
import pickle
import time
import random
from _thread import *
import tkinter as tk
from tkinter import ttk

import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc


HOST = "127.0.0.1"
PORT = 8000

# Record mapping index -> replica.
server_list = [f"{HOST}:{PORT}", f"{HOST}:{PORT + 1}", f"{HOST}:{PORT+ 2}"]


# GUI for market maker client
class MarketClient(tk.Frame):
    def __init__(self, username, password, stub):
        self.username = username
        self.password = password
        self.stub = stub

        self.last_modified_order_book = -1
        self.orderbook_window = -1
        self.stock_symbol = ""

        # Create root window: input
        self.root = tk.Tk()
        self.root.title('Market Client')
        self.root.geometry('500x100+1000+0')

        tk.Label(self.root, text="Stock Symbol:").grid(row=0, column=0, padx=5, pady=5, sticky="W")
        self.symbol_input = tk.Entry(self.root)
        self.symbol_input.grid(row=0, column=1, padx=5, pady=5, sticky="W")
        
        self.positions_button = tk.Button(self.root, text="Generate Automated Orders ->", command=self.post_order)
        self.positions_button.grid(row=2, column=1, padx=5, pady=5, sticky="SE")

        # Create second window: Message Log
        self.window2 = tk.Toplevel(self.root)
        self.window2.title('Notification Log')
        self.window2.geometry('500x500+1000+200')
        
        # Add scrollbar for Message Log
        scrollbar = tk.Scrollbar(self.window2)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.text_widget = tk.Text(self.window2, yscrollcommand=scrollbar.set)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.text_widget.yview)
        # text_widget.insert(tk.END, "TEST MESSAGE\n" * 20)

        # Create window: Stock Symbol Lookup to open its corresponding orderbook
        self.window5 = tk.Toplevel(self.root)
        self.window5.title('Stock Lookup')
        # self.window5.geometry('350x100+500+300')
        self.window5.geometry('350x100+1500+0')

        tk.Label(self.window5, text="Stock Symbol:").grid(row=0, column=0, padx=5, pady=5, sticky="W")
        self.lookup_symbol_input = tk.Entry(self.window5)
        self.lookup_symbol_input.grid(row=0, column=1, padx=5, pady=5, sticky="W")

        self.show_orderbook_button = tk.Button(self.window5, text="Open Orderbook ->", command=self.open_orderbook)
        self.show_orderbook_button.grid(row=2, column=1, padx=5, pady=5, sticky="SE")

        # Start the mainloop
        self.root.after(2000, self.update_everything)
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
        self.orderbook_window.geometry('350x500+1500+200')

        self.init_orderbook()
        self.orderbook_buy_rows = 6
        self.orderbook_sell_rows = 6

        # Show initial order_book
        with open("order_book.pickle", "rb") as f:
            order_book = pickle.load(f)
        print(order_book)
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
            print(order_book)

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
        symbol = self.symbol_input.get()

        # MM params
        fades = {}
        sizes = {}
        fades['buy'] = [i + random.uniform(0, 0.02) for i in np.arange(0.05, 0.51, 0.05) ]
        fades['sell'] = [i + random.uniform(0, 0.02) for i in np.arange(0.05, 0.51, 0.05) ]
        sizes['buy'] = random.sample(range(50, 150), 10)
        sizes['sell'] = random.sample(range(50, 150), 10)
       
        # Generate automated trades
        if symbol == "AAPL":
            fair = 169
        elif symbol == "TSLA":
            fair = 160
  
        num_trades = 2 * len(fades)

        while True:
            for dir in ['buy', 'sell']:
                for fade, size in zip(fades[dir], sizes[dir]): 
                    num_trade += 1
                    price = round(fair + fade, 2)
                    response = self.stub.ServerResponse(
                        pb2.Order(
                            opcode="mm_update" if num_trade == num_trades else "mm",
                            username=self.username,
                            password=self.password,
                            symbol=symbol,
                            dir=dir,
                            price=price,
                            size=size,
                        )
                    )
                    # Real-time update message log
                    print_response(response.response)
                    self.add_message(response.response + "\n")
                    time.sleep(1)

        # Real-time update message log
        # order_message = "Posted an order to " + opcode + " " + str(size) + " shares of " + symbol + " for $" + str(price) +"/share.\n"
        # self.add_message(order_message)

        # if response.response[0] != 'P': # ensure no duplicate Posted messages in non-matched case
        #     print_response(response.response)
        #     self.add_message(response.response + "\n")

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
            response = next(messages)
            print(response.response)
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

    # market_client = MarketClient(username, password, stub)

    # MM params
    fades = {}
    sizes = {}
    fades['buy'] = [i + random.uniform(0, 0.02) for i in np.arange(0.05, 0.51, 0.05) ]
    fades['sell'] = [i + random.uniform(0, 0.02) for i in np.arange(0.05, 0.51, 0.05) ]
    sizes['buy'] = random.sample(range(50, 150), 10)
    sizes['sell'] = random.sample(range(50, 150), 10)
    
    # simple example (use to explain price time priority?)
    # fades['buy'] = [round(i, 2) for i in np.arange(0.1, 1, 0.1)] 
    # fades['sell'] = [round(i, 2) for i in np.arange(0.1, 1, 0.1)] 
    # fades['sell'].reverse()
    # sizes['buy'] = [100] * 10 
    # sizes['sell'] = [100] * 10 
    
    request = input("\n>>> ")
    order_params = request.split(" ")
    # if len(order_params) == 0:
        # break
    
    symbol = order_params[0] 
    
    # make this more nuanced
    if symbol == "AAPL":
        fair = 169
    elif symbol == "TSLA":
        fair = 160
        
    while True:
        try:
            while True:
            
                for dir in ['buy', 'sell']:
                    for fade, size in zip(fades[dir], sizes[dir]):    
                        price = round(fair + fade, 2)
                        response = stub.ServerResponse(
                            pb2.Order(
                                opcode=dir,
                                username=username,
                                password=password,
                                symbol=symbol,
                                dir=dir,
                                price=price,
                                size=size,
                            )
                        )
                        print_response(response.response)
                        time.sleep(1)
                
                
                # width = 0.50
                # opcode, symbol, fair, width, size = order_params
                # # fair = float(fair)
                # # width = float(width)
                # # size = int(size)

                # Send message to a user.
                # opcode, symbol, price, size = order_params
                # price = float(price)
                # size = int(size)
                # dir = opcode
                    

                # Delete account
                # elif opcode == "delete":
                #   recipient = order_params[1]

                # else:
                #     if opcode != "":
                #         print("Error: Invalid command.", flush=True)
                #     continue
                



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
