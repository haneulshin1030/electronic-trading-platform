import grpc
import threading
import sys
import time
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


# GUI for customer client
class CustomerClient(tk.Frame):
  def __init__(self, username, password, stub):
    self.username = username
    self.password = password
    self.stub = stub

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
    self.window2_rows = 0
    
    # Add scrollbar for Message Log
    scrollbar = tk.Scrollbar(self.window2)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    self.text_widget = tk.Text(self.window2, yscrollcommand=scrollbar.set)
    self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.config(command=self.text_widget.yview)
    # text_widget.insert(tk.END, "TEST MESSAGE\n" * 20)

    # Create third window: Open Orders Table
    self.window3 = tk.Toplevel(self.root)
    self.window3.title('Open Orders')
    self.window3.geometry('400x200+0+650')
    self.window3_rows = 3

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
    # ttk.Separator(self.window3, orient="vertical").grid(row=4, column=0, rowspan=1, sticky="ns")
    # tk.Label(self.window3, text="AAPL").grid(row=4, column=1, sticky="W")
    # ttk.Separator(self.window3, orient="vertical").grid(row=4, column=2, rowspan=1, sticky="ns")
    # tk.Label(self.window3, text="$40.62").grid(row=4, column=3, sticky="W")
    # ttk.Separator(self.window3, orient="vertical").grid(row=4, column=4, rowspan=1, sticky="ns")
    # tk.Label(self.window3, text="50").grid(row=4, column=5, sticky="W")
    # ttk.Separator(self.window3, orient="vertical").grid(row=4, column=6, rowspan=1, sticky="ns")
    # ttk.Separator(self.window3, orient="horizontal").grid(row=5, column=0, columnspan=7, sticky="ew")


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
    self.lookup_symbol_input = tk.Entry(self.window5)
    self.lookup_symbol_input.grid(row=0, column=1, padx=5, pady=5, sticky="W")

    self.show_orderbook_button = tk.Button(self.window5, text="Open Orderbook ->", command=self.open_orderbook)
    self.show_orderbook_button.grid(row=2, column=1, padx=5, pady=5, sticky="SE")

    # Start the mainloop
    self.root.mainloop()


  def open_orderbook(self):
    stock_symbol = self.lookup_symbol_input.get()
    print(stock_symbol)
    self.orderbook_window = tk.Toplevel(self.root)
    title = 'Order Book: ' + stock_symbol
    self.orderbook_window.title(title)
    self.orderbook_window.geometry('350x200+500+500')

    # Create the table headers and lines
    tk.Label(self.orderbook_window, text=stock_symbol).grid(row=0, columnspan=5)
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

  def post_order(self):
    """
    1. Frontend: client hits "Post Order->" button
    2. Backend: order is added to 3 dictionaries: order_book, messages, positions
    3. Frontend: render updated order book, message log, and positions table
    """
    # Grab values
    # stock_symbol = self.symbol_input.get()
    # transaction_type = self.transaction_type.get()
    # price = self.price_input.get()
    # quantity = self.quantity_input.get()

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
    print_response(response.response)

    # Real-time update message log
    order_message = "Posted an order to " + opcode + " " + str(size) + " shares of " + symbol + " for $" + str(price) +"/share.\n"
    # tk.Label(self.window2, text=order_message).grid(row=self.window2_rows+1)
    self.text_widget.insert(tk.END, order_message)
    self.window2_rows += 1


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

    customer_client = CustomerClient(username, password, stub)
    
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
