import grpc
import threading
import sys
import time
import os
import pickle
import shutil
import random
import json
import ast
import numpy as np

from _thread import *

import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc

import tkinter as tk
from tkinter import ttk

leader_id = None

HOST = "127.0.0.1"
PORT = 8000

lock = threading.Lock()

# Record mapping index -> replica.
server_list = [f"{HOST}:{PORT}", f"{HOST}:{PORT + 1}", f"{HOST}:{PORT+ 2}"]

# List of universe of symbols
symbol_list = ["AAPL", "TSLA", "USD"]

# # Global variable to store CustomerClient object
# customer_client = None


# GUI for customer client
class CustomerClient(tk.Frame):
    def __init__(self, username, password, stub):
        self.username = username
        self.password = password
        self.stub = stub

        # self.last_modified_order_book = -1
        self.orderbook_window = -1
        self.stock_symbol = ""

        # self.user_order_book = {symbol: {"buy": [], "sell": []}
        # for symbol in symbol_list}
        self.buy_orders = []
        self.sell_orders = []

        # Listen for messages
        self.listen_thread = threading.Thread(
            target=(self.listen_for_messages), args=(username,))
        self.listen_thread.start()

        # Create root window: Customer Client inputs
        self.root = tk.Tk()
        self.root.title('Market Maker Client')
        self.root.geometry('400x250')

        tk.Label(self.root, text="Stock Symbol:").grid(
            row=0, column=0, padx=5, pady=5, sticky="W")
        self.symbol_input = tk.Entry(self.root)
        self.symbol_input.grid(row=0, column=1, padx=5, pady=5, sticky="W")

        tk.Label(self.root, text="Transaction Type:").grid(
            row=1, column=0, padx=5, pady=5, sticky="W")
        self.transaction_type = tk.StringVar(value="BUY")
        self.transaction_type_select = tk.OptionMenu(
            self.root, self.transaction_type, "BUY", "SELL", "BOTH")
        self.transaction_type_select.grid(
            row=1, column=1, padx=5, pady=5, sticky="W")

        tk.Label(self.root, text="Fair Value:").grid(
            row=2, column=0, padx=5, pady=5, sticky="W")
        self.price_input = tk.Entry(self.root)
        self.price_input.grid(row=2, column=1, padx=5, pady=5, sticky="W")

        tk.Label(self.root, text="Quantity:").grid(
            row=3, column=0, padx=5, pady=5, sticky="W")
        self.quantity_input = tk.Entry(self.root)
        self.quantity_input.grid(row=3, column=1, padx=5, pady=5, sticky="W")

        self.positions_button = tk.Button(
            self.root, text="Generate Bot", command=self.init_orders)
        self.positions_button.grid(
            row=4, column=1, padx=5, pady=5, sticky="SE")

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

        # Create fifth window: Stock Symbol Lookup to open its corresponding orderbook
        self.window5 = tk.Toplevel(self.root)
        self.window5.title('Stock Lookup')
        # self.window5.geometry('350x100+500+300')
        self.window5.geometry('350x100+500+0')

        tk.Label(self.window5, text="Stock Symbol:").grid(
            row=0, column=0, padx=5, pady=5, sticky="W")
        self.lookup_symbol_input = tk.Entry(self.window5)
        self.lookup_symbol_input.grid(
            row=0, column=1, padx=5, pady=5, sticky="W")

        self.show_orderbook_button = tk.Button(
            self.window5, text="Open Orderbook", command=self.open_orderbook)
        self.show_orderbook_button.grid(
            row=2, column=1, padx=5, pady=5, sticky="SE")

        # Start the mainloop
        # self.root.after(10000, self.update_everything)
        self.root.mainloop()

    def init_positions(self):
        # Create table headers and lines
        tk.Label(self.window4, text="").grid(row=0, columnspan=5)
        ttk.Separator(self.window4, orient="horizontal").grid(
            row=1, column=0, columnspan=5, sticky="ew")
        ttk.Separator(self.window4, orient="vertical").grid(
            row=2, column=0, rowspan=1, sticky="ns")
        tk.Label(self.window4, text="Stock").grid(row=2, column=1, sticky="W")
        ttk.Separator(self.window4, orient="vertical").grid(
            row=2, column=2, rowspan=1, sticky="ns")
        tk.Label(self.window4, text="Shares").grid(row=2, column=3, sticky="W")
        ttk.Separator(self.window4, orient="vertical").grid(
            row=2, column=4, rowspan=1, sticky="ns")
        ttk.Separator(self.window4, orient="horizontal").grid(
            row=3, column=0, columnspan=5, sticky="ew")

    def init_orderbook(self):
        # Create the table headers and lines
        tk.Label(self.orderbook_window, text=self.stock_symbol).grid(
            row=0, columnspan=5)
        ttk.Separator(self.orderbook_window, orient="horizontal").grid(
            row=1, column=0, columnspan=5, sticky="ew")
        tk.Label(self.orderbook_window, text="BUY").grid(
            row=2, column=0, columnspan=2)
        tk.Label(self.orderbook_window, text="SELL").grid(
            row=2, column=3, columnspan=2)
        ttk.Separator(self.orderbook_window, orient="vertical").grid(
            row=2, column=2, rowspan=1, sticky="ns")
        ttk.Separator(self.orderbook_window, orient="horizontal").grid(
            row=3, column=0, columnspan=5, sticky="ew")

        tk.Label(self.orderbook_window, text="Price").grid(row=4, column=0)
        ttk.Separator(self.orderbook_window, orient="vertical").grid(
            row=4, column=1, rowspan=1, sticky="ns")
        tk.Label(self.orderbook_window, text="Quantity").grid(row=4, column=1)
        ttk.Separator(self.orderbook_window, orient="vertical").grid(
            row=4, column=2, rowspan=1, sticky="ns")
        tk.Label(self.orderbook_window, text="Price").grid(row=4, column=3)
        ttk.Separator(self.orderbook_window, orient="vertical").grid(
            row=4, column=4, rowspan=1, sticky="ns")
        tk.Label(self.orderbook_window, text="Quantity").grid(row=4, column=4)
        ttk.Separator(self.orderbook_window, orient="horizontal").grid(
            row=5, column=0, columnspan=5, sticky="ew")

    def open_orderbook(self):
        self.stock_symbol = self.lookup_symbol_input.get()
        self.orderbook_window = tk.Toplevel(self.root)
        title = 'Order Book: ' + self.stock_symbol
        self.orderbook_window.title(title)
        self.orderbook_window.geometry('350x500+500+200')

        self.init_orderbook()
        self.orderbook_buy_rows = 6
        self.orderbook_sell_rows = 6

        for size, price in self.buy_orders:
            tk.Label(self.orderbook_window, text=price).grid(
                # tk.Label(self.orderbook_window, text=str(round(price, 2))).grid(
                row=self.orderbook_buy_rows, column=0)
            tk.Label(self.orderbook_window, text=size).grid(
                # tk.Label(self.orderbook_window, text=str(size)).grid(
                row=self.orderbook_buy_rows, column=1)
            ttk.Separator(self.orderbook_window, orient="vertical").grid(
                row=self.orderbook_buy_rows, column=2, rowspan=1, sticky="ns")
            ttk.Separator(self.orderbook_window, orient="horizontal").grid(
                row=self.orderbook_buy_rows+1, column=0, columnspan=5, sticky="ew")
            self.orderbook_buy_rows += 2

        # add most expensive 10 sell orders
        # for price in list(sell_orders.keys())[:10]:
        for size, price in self.sell_orders:
            # size = sell_orders[price]
            # tk.Label(self.orderbook_window, text=str(round(price, 2))).grid(
            tk.Label(self.orderbook_window, text=price).grid(
                row=self.orderbook_sell_rows, column=3)
            # tk.Label(self.orderbook_window, text=str(size)).grid(
            tk.Label(self.orderbook_window, text=size).grid(
                row=self.orderbook_sell_rows, column=4)
            ttk.Separator(self.orderbook_window, orient="vertical").grid(
                row=self.orderbook_sell_rows, column=2, rowspan=1, sticky="ns")
            ttk.Separator(self.orderbook_window, orient="horizontal").grid(
                row=self.orderbook_sell_rows+1, column=0, columnspan=5, sticky="ew")
            self.orderbook_sell_rows += 2

        # initialize the last modification time
        # self.last_modified_order_book = os.path.getmtime(
        #     f"order_book_{leader_id}.pickle")

        self.root.after(10, self.update_everything)

    def update_everything(self):
        try:

            # Clear window
            if self.orderbook_window != -1:
                for widget in self.orderbook_window.winfo_children():
                    widget.destroy()

            # Create the table headers and lines
            self.init_orderbook()
            self.orderbook_buy_rows = 6
            self.orderbook_sell_rows = 6

            print(self.buy_orders)
            print(self.sell_orders)
            for size, price in self.buy_orders:
                # size = buy_orders[price]
                tk.Label(self.orderbook_window, text=price).grid(
                    # tk.Label(self.orderbook_window, text=str(round(price, 2))).grid(
                    row=self.orderbook_buy_rows, column=0)
                tk.Label(self.orderbook_window, text=size).grid(
                    # tk.Label(self.orderbook_window, text=str(size)).grid(
                    row=self.orderbook_buy_rows, column=1)
                ttk.Separator(self.orderbook_window, orient="vertical").grid(
                    row=self.orderbook_buy_rows, column=2, rowspan=1, sticky="ns")
                ttk.Separator(self.orderbook_window, orient="horizontal").grid(
                    row=self.orderbook_buy_rows+1, column=0, columnspan=5, sticky="ew")
                self.orderbook_buy_rows += 2

            for size, price in self.sell_orders:
                # size = sell_orders[price]
                # tk.Label(self.orderbook_window, text=str(round(price, 2))).grid(
                tk.Label(self.orderbook_window, text=price).grid(
                    row=self.orderbook_sell_rows, column=3)
                # tk.Label(self.orderbook_window, text=str(size)).grid(
                tk.Label(self.orderbook_window, text=size).grid(
                    row=self.orderbook_sell_rows, column=4)
                ttk.Separator(self.orderbook_window, orient="vertical").grid(
                    row=self.orderbook_sell_rows, column=2, rowspan=1, sticky="ns")
                ttk.Separator(self.orderbook_window, orient="horizontal").grid(
                    row=self.orderbook_sell_rows+1, column=0, columnspan=5, sticky="ew")
                self.orderbook_sell_rows += 2

                # self.last_modified_order_book = self.current_modified_order_book
        except EOFError:
            self.root.after(100, self.update_everything)

    def attempt_to_post_order(self, opcode, username, password, dir, symbol, price, size):
        global leader_id

        """
        Continue attempting to post the order until the leader is found.
        """
        response = None

        try:
            response = self.stub.RequestClientOrder(
                pb2.ClientOrder(
                    opcode=opcode,
                    username=username,
                    password=password,
                    symbol=symbol,
                    dir=dir,
                    price=price,
                    size=size,
                )
            )
        # Exception for if the previous leader server went down and a new leader was determined.
        except (grpc._channel._InactiveRpcError, LeaderDisconnected):
            # Terminate the current listening thread and find a new leader.
            self.listen_thread.join()
            leader_id, self.stub = find_leader()
            channel = grpc.insecure_channel(server_list[leader_id])
            self.stub = pb2_grpc.ChatStub(channel)

            # Start the listening thread.
            self.listen_thread = threading.Thread(
                target=(self.listen_for_messages), args=(username,))
            self.listen_thread.start()

            response = self.attempt_to_post_order(opcode, username,
                                                  password, dir, symbol, price, size)
        except KeyboardInterrupt:
            try:
                response = self.stub.RequestClientOrder(
                    pb2.ClientOrder(
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
            self.listen_thread.join()

        return response

    def post_orders(self):
        # Send params to backend
        opcode = self.transaction_type.get().lower()
        username = self.username
        password = self.password
        dir = opcode
        symbol = self.symbol_input.get()
        fair_value = float(self.price_input.get())

        dir_list = []
        if opcode == 'buy':
            dir_list = ['buy']
        elif opcode == 'sell':
            dir_list = ['sell']
        else:
            dir_list = ['buy', 'sell']

        # Market Maker Parameters
        # TODO: move constants to top of file
        fades = {}
        sizes = {}

        fades['buy'] = [i + random.uniform(0, 0.02)
                        for i in np.arange(0.05, 0.51, 0.05)]
        fades['sell'] = [i + random.uniform(0, 0.02)
                         for i in np.arange(0.05, 0.51, 0.05)]
        size = int(self.quantity_input.get())
        sizes['buy'] = random.sample(
            range(max(0, size - 30), size + 30), 10)
        sizes['sell'] = random.sample(
            range(max(0, size - 30), size + 30), 10)

        while True:
            for dir in dir_list:
                for fade, size in zip(fades[dir], sizes[dir]):
                    price = round(fair_value + fade, 2)

                    response = self.attempt_to_post_order(dir, username, password,
                                                          dir, symbol, price, size)
                    print_response(response.response)
                    self.add_message(response.response + "\n")
                    time.sleep(0.5)
            time.sleep(5)

    def init_orders(self):
        """
        1. Frontend: client hits "Post Order->" button
        2. Backend: order is added to 3 dictionaries: order_book, messages, positions
        3. Frontend: render updated order book, message log, and positions table
        """

        self.post_thread = threading.Thread(
            target=(self.post_orders), args=())
        self.post_thread.start()

    def add_message(self, message):
        self.text_widget.insert(tk.END, message)

    def listen_for_messages(self, username):
        """
        Listen for messages from other clients.
        """

        messages = self.stub.SendClientMessages(
            pb2.Username(username=username))

        try:
            while True:
                # lock.acquire()
                # When a new message is found, iterate to it and print it.
                response = next(messages)
                print_response(response.response)
                # If new leader message

                response_text = response.response
                if response_text[:10] == "Connecting":
                    global leader_id
                    leader_id, self.stub = find_leader()
                elif response_text[:6] == "Update":
                    # print(response_text)
                    order_lists = response_text[8:].split(';')
                    buy_orders = order_lists[0]
                    sell_orders = order_lists[1]

                    self.buy_orders = ast.literal_eval(
                        buy_orders) if buy_orders != '[]' else []
                    self.sell_orders = ast.literal_eval(
                        sell_orders) if sell_orders != '[]' else []
                    self.root.after(100, self.update_everything)
                    # self.update_everything()
                else:
                    self.add_message(response.response + "\n")
        except:
            return


def find_leader():
    """
    Determines which server is the leader.
    """
    stub = None
    channel = None
    connected_to_leader = False
    while not connected_to_leader:
        for i, addr in enumerate(server_list):
            try:
                channel = grpc.insecure_channel(addr)
                stub = pb2_grpc.ChatStub(channel)

                # Query for the leader server. If found, return.
                response = stub.FindLeader(pb2.LeaderRequest())
                print("Leader:", response.leader)
                return response.leader, stub

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
    global leader_id

    listen_thread = None
    leader_id, stub = find_leader()
    print(server_list[leader_id])
    channel = grpc.insecure_channel(server_list[leader_id])
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
            print("Please select a password with a minumum of 8 characters and at least one uppercase letter, one lowercase letter, one numerical digit, and one character from ., !, _, @, or $.")
            password = input("Password: ")

        response = stub.RequestClientOrder(
            pb2.ClientOrder(
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

    # Create customer client
    customer_client = CustomerClient(username, password, stub)

    # This code is not used anymore now that UI has been added
    # while True:
    #     try:
    #         while True:
    #             request = input("\n>>> ")
    #             order_params = request.split(" ")
    #             if len(order_params) == 0:
    #                 continue

    #             # Initialize parameters of ClientOrder
    #             opcode = order_params[0]
    #             dir = ""
    #             symbol = ""
    #             price = -1
    #             size = -1

    #             # Parse client requests.

    #             # Create account.
    #             if opcode == "create":
    #                 username = order_params[1]
    #                 password = order_params[2]

    #             # Log in.
    #             elif opcode == "login":
    #                 username = order_params[1]
    #                 password = order_params[2]

    #             # Send message to a user.
    #             elif opcode == "buy" or opcode == "sell":
    #                 opcode, symbol, price, size = order_params
    #                 price = float(price)
    #                 size = int(size)
    #                 dir = opcode

    #             # Delete account
    #             # elif opcode == "delete":
    #             #   recipient = order_params[1]

    #             else:
    #                 if opcode != "":
    #                     print("Error: Invalid command.", flush=True)
    #                 continue

    #             response = stub.RequestClientOrder(
    #                 pb2.ClientOrder(
    #                     opcode=opcode,
    #                     username=username,
    #                     password=password,
    #                     symbol=symbol,
    #                     dir=dir,
    #                     price=price,
    #                     size=size,
    #                 )
    #             )
    #             print_response(response.response)

    #     # Exception for if the previous leader server went down and a new leader was determined.
    #     except (grpc._channel._InactiveRpcError, LeaderDisconnected):
    #         # Terminate the current listening thread and find a new leader.
    #         listen_thread.join()
    #         leader_id = find_leader()
    #         channel = grpc.insecure_channel(server_list[leader_id])
    #         stub = pb2_grpc.ChatStub(channel)

    #         # Start the listening thread.
    #         listen_thread = threading.Thread(
    #             target=(customer_client.listen_for_messages), args=(customer_client, stub, username))
    #         listen_thread.start()

    #         print("Redirected to a new server; please repeat your request.")
    #         pass
    # Exception for if the user does a keyboard interrupt.


if __name__ == "__main__":
    main()
