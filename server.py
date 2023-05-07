import grpc
import sys
import threading
import time
import csv
import optparse
import concurrent.futures
import random
import json
import pickle
import os
import glob
from pathlib import Path
from _thread import *

from sortedcontainers import SortedDict

import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc
from concurrent import futures

# lock = Lock()

HOST = "127.0.0.1"
PORT = 8000

########## SERVER INFORMATION ##########

# Current threads that are running.
threads = []

# Event for when threads are running, i.e. not stopped.
event = threading.Event()

# Current server.
server_id = None

# Dictionary mapping index -> replica.
address_list = [f"{HOST}:{PORT}", f"{HOST}:{PORT + 1}", f"{HOST}:{PORT+ 2}"]

# Server id of leader.
leader_id = None

# Current live servers.
active_servers = [None, None, None]

# Order book status ID, indicating the ID of the order book status. Incremented for each update to the order book.
order_book_status_id = 0

########## MARKET INFORMATION ##########

# List of universe of symbols
symbol_list = ["AAPL", "TSLA", "USD"]

# Default dictionary of positions in symbols

zero_positions = dict.fromkeys(symbol_list, 0)

dir_list = ["buy", "sell"]

# Dictionary mapping symbol -> {buy -> bid dictionary, sell -> offer dictionary}
# Where the bid and offer dictionaries map price -> [[user_1, quantity_1], ..., [user_n, quantity_n]]
# sorted by time priority, such that if i < j, user i has time priority over user j
open_orders = {symbol: {"buy": SortedDict(), "sell": SortedDict()}
               for symbol in symbol_list}

# Dictionary mapping symbol -> {buy -> bid dictionary, sell -> offer dictionary}
# Where the bid and offer dictionaries map price -> total quantity
order_book = {symbol: {"buy": SortedDict(), "sell": SortedDict()}
              for symbol in symbol_list}

# Dictionary mapping symbol -> {buy -> bid list, sell -> offer list}
# Where the bid and offer lists are of the form [[price_1, quantity_1], ..., [price_n, quantity_n]]
# sorted in decreasing order of competitive pricing
user_order_book = {symbol: {"buy": [], "sell": []}
                   for symbol in symbol_list}

########## USER INFORMATION ##########

# Dictionary mapping user -> online status (bool)
user_status = {}

# Dictionary mapping user -> password
passwords = {}

# Dictionary mapping username, symbol -> user's position in that symbol in shares
positions = {}

# Dictionary mapping user -> [message_1, ..., message_n], where message_i is a response message from the server
messages = {}

# Error string for if the server is not the leader.
ERROR_NOT_LEADER = "Error: server is not the leader."

# The time each server waits before checking if the leader is active
default_sleep_time = 1

lock = threading.Lock()



def save_data_locally(user_data_updated=False):
    global open_orders, order_book, user_order_book, positions, messages, server_id
    with open(f'open_orders_{server_id}.pickle', 'wb') as file:
        pickle.dump(open_orders, file)
    with open(f'order_book_{server_id}.pickle', 'wb') as file:
        pickle.dump(order_book, file)
    with open(f'user_order_book_{server_id}.pickle', 'wb') as file:
        pickle.dump(user_order_book, file)

    with open(f'positions_{server_id}.pickle', 'wb') as file:
        pickle.dump(positions, file)
    with open(f'messages_{server_id}.pickle', 'wb') as file:
        pickle.dump(messages, file)

    if user_data_updated:
        global user_status, passwords
        with open(f'user_status_{server_id}.pickle', 'wb') as file:
            pickle.dump(user_status, file)
        with open(f'passwords_{server_id}.pickle', 'wb') as file:
            pickle.dump(passwords, file)

    return


def post_order(username, dir, symbol, sgn, price, size):
    global open_orders, order_book, messages
    if size == 0:
        return

    price = round(price, 2)
    if price in open_orders[symbol][dir]:
        open_orders[symbol][dir][price].append([username, size])
        order_book[symbol][dir][price] += size
    else:
        open_orders[symbol][dir][price] = [[username, size]]
        order_book[symbol][dir][price] = size
    return


def update_positions(username, symbol, sgn, opp_sgn, price, size):
    global positions

    print(f"Updating {username}'s position in {symbol} by {sgn} * {size}...")
    positions[username][symbol] += sgn * size
    positions[username]["USD"] += opp_sgn * size * price
    print("Positions updated.")
    return


def trade_message(username, dir, symbol, price, size):
    action_past = "Bought" if dir == "buy" else "Sold"
    preposition = "for" if dir == "buy" else "at"
    return f"{action_past} {size} shares of {symbol} {preposition} ${price:.2f}/share."


def match_trade(
    username, dir, symbol, sgn, opp_sgn, price, size, order_was_taken=False
):
    global positions, messages, open_orders, order_book

    if order_was_taken:
        print(f"Order book before match: \n {order_book[symbol]}\n")
        print(f"User positions before match: \n {positions[username]}")

    # Update user information
    update_positions(username, symbol, sgn, opp_sgn, price, size)

    # If the user is the counterparty who posted the trade (maker)
    if order_was_taken:
        messages[username].append(trade_message(
            username, dir, symbol, price, size))
        # Update open orders

        # If total quantity at the price with the counterparty was taken
        if size < open_orders[symbol][dir][price][0][1]:
            open_orders[symbol][dir][price][0][1] -= size
        else:
            open_orders[symbol][dir][price].pop(0)
            if len(open_orders[symbol][dir][price]) == 0:
                del open_orders[symbol][dir][price]

        # Update order book

        # If total quantity at the price was taken
        if size < order_book[symbol][dir][price]:
            order_book[symbol][dir][price] -= size
        else:
            del order_book[symbol][dir][price]

    if order_was_taken:
        print(f"Order book after match: \n {order_book[symbol]}\n")
        print(f"User positions after match: \n {positions[username]}")

    return trade_message(username, dir, symbol, price, size)


def send_server_data_to_servers(user_data_updated=False):
    """
    If current server is the leader, each time an update to the data occurs, 
    saves the data locally and
    sends the open orders, order book, user online status, user passwords, 
    user positions, and user messages to each of the servers.
    """
    global open_orders, order_book, user_status, passwords, positions, messages, server_id

    if leader_id != server_id:
        return

    for id, alive in enumerate(active_servers):
        # If the other server is alive and not the leader
        if alive and id != leader_id and id != server_id:
            channel = grpc.insecure_channel(address_list[id])
            stub_for_other_server = pb2_grpc.ChatStub(channel)
            try:
                print(f"Sending data to server {id}...")
                stub_for_other_server.ReceiveServerMarketData(
                    pb2.ServerMarketData(
                        open_orders=json.dumps(open_orders),
                        order_book=json.dumps(order_book),
                        positions=json.dumps(positions),
                        messages=json.dumps(messages)
                    )
                )
                if user_data_updated:
                    stub_for_other_server.ReceiveServerClientData(
                        pb2.ServerClientData(
                            user_status=json.dumps(user_status),
                            passwords=json.dumps(passwords)
                        )
                    )

            except:
                print(f"Server failure: {id}")
                active_servers[id] = False


class ChatServicer(pb2_grpc.ChatServicer):
    def Heartbeat(self, request, context):
        return pb2.HeartbeatResponse(leader=leader_id)

    def ReceiveServerMarketData(self, server_market_data, context):
        """
        Send updated server market data to the other servers.
        """
        global open_orders, order_book, positions, messages
        open_orders = json.loads(server_market_data.open_orders)
        order_book = json.loads(server_market_data.order_book)
        positions = json.loads(server_market_data.positions)
        messages = json.loads(server_market_data.messages)

        save_data_locally()

        return pb2.ServerResponse()

    def ReceiveServerClientData(self, server_client_data, context):
        """
        Send updated server client data to the other servers.
        """
        global user_status, passwords
        user_status = json.loads(server_client_data.user_status)
        passwords = json.loads(server_client_data.passwords)

        save_data_locally(user_data_updated=True)

        return pb2.ServerResponse()

    def ReceiveClientMarketData(self, client_market_data, context):
        """
        Send updated server client data to the other servers.
        """
        global user_order_book
        return pb2.ClientMarketData(user_order_book=json.dumps(user_order_book))

    def RequestClientOrder(self, order, context):
        """
        Manage the server's response to user input.
        """
        return handle_server_response(
            order.opcode,
            order.username,
            order.password,
            order.dir,
            order.symbol,
            order.price,
            order.size,
        )

    def SendClientMessages(self, username, context):
        """
        Return the client's pending messages, and update the data accordingly.
        """

        username = username.username

        while username in messages.keys():
            for message in messages[username]:
                yield pb2.Response(response=message)
            messages[username] = []

    def FindLeader(self, request, context):
        return pb2.LeaderResponse(leader=leader_id)


def login(username, password):
    """
    Log the user in.
    """
    global user_status

    # Check whether user exists.
    if username not in user_status or passwords[username] != password:
        response = "Failure: Username and/or password is not valid."
    else:
        response = "Success: Account " + username + " logged in."
        user_status[username] = True
    return response


def create_account(username, password):
    """
    Create new account and initialize user information.
    """

    global user_status, passwords, positions, messages

    user_status[username] = True
    passwords[username] = password
    positions[username] = zero_positions.copy()
    messages[username] = []
    return "Success: Account " + username + " created and logged in."


def valid_password(password):
    """
    Checks whether the password satisfies the following criteria:
    - Minumum of 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 numerical digit
    - At least and 1 character from ., !, _, @, or $
    """
    l, u, p, d = False, False, False, False

    if len(password) < 8:
        return False

    for c in password:
        if c.islower():
            l = True
        if c.isupper():
            u = True
        if c.isdigit():
            d = True
        if c == '@' or c == '$' or c == '_' or c == '.' or c == '!':
            p = True

    return l and u and p and d


def post_message(username, dir, symbol, price, size):
    # Save dictionary data
    # with open('order_book_dump.pickle', 'wb') as file:
    #     pickle.dump(order_book, file)
    # with open('positions.pickle', 'wb') as file:
    #     pickle.dump(positions, file)

    preposition = "for" if dir == "buy" else "at"
    return f"Posted an order to {dir} {size} shares of {symbol} {preposition} ${price:.2f}/share."


def find_best_price(opp, symbol, price):
    global open_orders
    # Find best existing bid or offer price
    best_price = None
    if opp == "sell":
        best_price = min(open_orders[symbol][opp].keys())
        if price < best_price:
            return None
    else:
        best_price = max(open_orders[symbol][opp].keys())
        if price > best_price:
            return None
    return best_price


def handle_server_response(opcode, username, password, dir, symbol, price, size):
    """
    Handle the server's response to the input.
    """
    # If this server is not the leader, error.
    global leader_id, server_id
    global user_status, passwords, positions, messages
    if server_id != leader_id:
        return pb2.Response(response=ERROR_NOT_LEADER)

    response = None
    user_data_updated = False

    # Create account.
    if opcode == "create":
        user_data_updated = True
        # Check whether username is unique.
        if username in user_status:
            response = "Failure: Username already exists."
        elif not valid_password(password):
            response = "Failure: Invalid password."
        else:
            # Create new user.
            response = create_account(username, password)

    # Log in.
    elif opcode == "login":
        user_data_updated = True
        response = login(username, password)

    # Send order book to client
    elif opcode == "init_orderbook":
        send_order_book_to_clients(symbol)
        response = "Order book initialized."
    # Post a user's order in the market and execute any matched trades
    # Think about race conditions? Lock and unlock?
    elif opcode == "buy" or opcode == "sell":

        preposition = None

        # Opposite direction
        if dir == "buy":
            opp = "sell"
            sgn = 1
            opp_sgn = -1
            preposition = "for"
        else:
            opp = "buy"
            sgn = -1
            opp_sgn = 1
            preposition = "at"

        print(
            f"\nORDER RECEIVED: Received order to {dir} {size} shares of {symbol} {preposition} ${price:.2f}/share."
        )

        # Check if there are matching trades, and excute them if so

        trade_size = 0
        cumulative_price = 0

        lock.acquire()

        while size - trade_size > 0:
            print("Matching trades...")
            # print(f"Order book: \n {order_book[symbol]}")

            # Check if there are no orders in the opposite direction
            if len(order_book[symbol][opp]) == 0:
                print("No orders in the opposite direction.")
                break

            best_price = find_best_price(opp, symbol, price)
            if best_price is None:
                break
            # print(order_book)
            # print(open_orders)
            print(f"Current best price: {best_price}")

            while size - trade_size > 0 and best_price in open_orders[symbol][opp]:
                cur_size = min(
                    open_orders[symbol][opp][best_price][0][1], size - trade_size
                )

                # Trade occurred
                if cur_size > 0:
                    trade_size += cur_size
                    cumulative_price += cur_size * best_price
                    counterparty = open_orders[symbol][opp][best_price][0][0]
                    print(
                        f"Matching {cur_size} shares at price {best_price} with {counterparty}..."
                    )

                    # Update counterparty information
                    match_trade(
                        counterparty,
                        opp,
                        symbol,
                        opp_sgn,
                        sgn,
                        best_price,
                        cur_size,
                        order_was_taken=True,
                    )
                    print("Trades matched")

        print(f"Matched a total of {trade_size} shares.\n")

        # Update user information
        if trade_size > 0:
            average_price = round(cumulative_price / trade_size, 2)
            print(
                f"Matching {trade_size} shares at average price {average_price} with all counterparties..."
            )
            match_trade(username, dir, symbol, sgn,
                        opp_sgn, average_price, trade_size)
            response = trade_message(
                username, dir, symbol, average_price, trade_size)

            print(f"User positions after match: \n {positions[username]}")
        else:
            response = ""

        if trade_size < size:
            print(
                f"Posting order for the remaining {size - trade_size} shares...")

            # Update open orders and order book
            post_order(username, dir, symbol, sgn, price, size - trade_size)
            post_message_success = post_message(
                username, dir, symbol, price, size - trade_size
            )
            print(f"{post_message_success}\n")
            print(f"Open orders: \n {open_orders[symbol]}\n")
            response += ("\n" if trade_size > 0 else "") + post_message_success

        lock.release()

    # Exception
    elif opcode == "except":
        del messages[username]
        return pb2.Response(response="")

    # Error checking for invalid opcode
    else:
        if opcode != "":
            response = "Invalid command."
        else:
            response = ""

    print("Saving data locally...")
    save_data_locally(user_data_updated)
    print("Sending server data to other servers...")
    send_server_data_to_servers(user_data_updated)
    if symbol:
        send_order_book_to_clients(symbol)

    if response:
        # Save dictionary data
        print("ORDER BOOK")
        print(order_book)
        # with open('order_book_dump.pickle', 'wb') as file:
        #     pickle.dump(order_book, file)
        # with open('positions.pickle', 'wb') as file:
        #     pickle.dump(positions, file)

        print(f'Sending response to server: "{response}" \n')
        return pb2.Response(response=response)


def send_heartbeat(stub, id):
    """
    Send heartbeat to the server.
    """
    # Check if server is online
    try:
        response = stub.Heartbeat(pb2.HeartbeatRequest())
        active_servers[id] = True
        global leader_id
        leader_id = response.leader
    except:
        # print(f"Server currently down: {id}.") UNCOMMENT THIS?
        active_servers[id] = False


def kill_server():
    """
    Kill the server.
    """
    event.clear()
    server.stop(0)
    try:
        for thread in threads:
            thread.join()
    except (OSError):
        pass
    print("Killed thread.")
    sys.exit(0)


def reformat_data():
    global open_orders, order_book, positions

    for symbol in symbol_list:
        for dir in dir_list:
            open_orders[symbol][dir] = SortedDict({float(price): [[user, int(float(
                size))] for user, size in order_list] for price, order_list in open_orders[symbol][dir].items()})

    for symbol in symbol_list:
        for dir in dir_list:
            order_book[symbol][dir] = SortedDict({float(price): int(float(
                size)) for price, size in order_book[symbol][dir].items()})

    # for symbol in symbol_list:
    #     for dir in dir_list:
    #         user_order_book[symbol][dir] = [(float(price), int(
    #             float(size))) for price, size in user_order_book[symbol][dir]]

    for username in user_status.keys():
        positions[username] = {symbol: int(float(position))
                               for symbol, position in positions[username].items()}

    return


def send_new_leader_to_clients():
    global leader_id, messages
    for username in user_status.keys():
        messages[username].append(f"Connecting to server {leader_id}...")
    return


def send_order_book_to_clients(symbol):
    global user_order_book, order_book, messages, order_book_status_id

    print("Sending order book to clients...")
    n = len(order_book[symbol]['buy'])

    user_order_book[symbol]['buy'] = [order_book[symbol]
                                      ['buy'].peekitem(i) for i in range(n - 1, -1, -1)[-10:]]

    m = len(order_book[symbol]['sell'])

    user_order_book[symbol]['sell'] = [order_book[symbol]
                                       ['sell'].peekitem(i) for i in range(m)[:10]]

    for username in user_status.keys():
        messages[username].append(
            f"Update: {user_order_book[symbol]['buy']};{user_order_book[symbol]['sell']}")

    print(f"User Order Book:\n {user_order_book}")
    order_book_status_id += 1
    return


def check_leader():
    """
    Check if leader is currently active. If not, set a new leader.
    """
    global leader_id, messages
    if leader_id is None or not active_servers[leader_id]:
        for id, alive in enumerate(active_servers):
            if alive:
                leader_id = id
                print(f"The new leader is {leader_id}")
                if server_id == leader_id:
                    reformat_data()
                    send_new_leader_to_clients()
                return
        # No leaders found
        print("Error: No active servers.")

        # TODO: remove this eventually
        for file in glob.glob("*.pickle"):
            os.remove(file)

        kill_server()


def start_heartbeat(id):
    """
    Start heartbeat of server.
    """
    channel = grpc.insecure_channel(address_list[id])
    stub = pb2_grpc.ChatStub(channel)
    send_heartbeat(stub, id)
    while None in active_servers:
        continue
    sleep_time = default_sleep_time
    while event.is_set():
        time.sleep(sleep_time)
        send_heartbeat(stub, id)
        check_leader()


def start_server():
    """
    Start the server.
    """
    # Start heartbeat of other servers.
    for i in range(3):
        if i != server_id:
            heartbeat_thread = threading.Thread(
                target=start_heartbeat, args=(i,))
            heartbeat_thread.start()
            threads.append(heartbeat_thread)

    # Persistence: load all data previously saved locally to server
    # If this is the only remaining server, then it will have all the updates
    # Otherwise, if another server was already alive and sending updates, then it will
    # send this server the updated data now that it is online.
    if Path(f'user_status_{server_id}.pickle').is_file():
        global open_orders, order_book, user_order_book, user_status, passwords, positions, messages
        with open(f'user_status_{server_id}.pickle', 'rb') as file:
            user_status = pickle.load(file)
        with open(f'passwords_{server_id}.pickle', 'rb') as file:
            passwords = pickle.load(file)
        with open(f'open_orders_{server_id}.pickle', 'rb') as file:
            open_orders = pickle.load(file)
            open_orders = {symbol: {"buy": SortedDict(open_orders[symbol]['buy']), "sell": SortedDict(open_orders[symbol]['sell'])}
                           for symbol in symbol_list}
        with open(f'order_book_{server_id}.pickle', 'rb') as file:
            order_book = pickle.load(file)
            order_book = {symbol: {"buy": SortedDict(order_book[symbol]['buy']), "sell": SortedDict(order_book[symbol]['sell'])}
                          for symbol in symbol_list}
        # with open(f'user_order_book_{server_id}.pickle', 'rb') as file:
        #     user_order_book = pickle.load(file)

        with open(f'positions_{server_id}.pickle', 'rb') as file:
            positions = pickle.load(file)
        with open(f'messages_{server_id}.pickle', 'rb') as file:
            messages = pickle.load(file)
        for symbol in symbol_list:
            send_order_book_to_clients(symbol)

    global server
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=12))
    pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server)

    # Start server.
    server_address = f"{HOST}:{PORT + server_id}"
    server.add_insecure_port(server_address)
    print(f"Starting server {server_id} at address {server_address}")
    server.start()
    server.wait_for_termination()


def main():
    """
    Create three servers.
    """
    global server_id
    # Get flag for system id
    p = optparse.OptionParser()
    p.add_option("--server_id", "-s", default="0")
    options, _ = p.parse_args()
    server_id = int(options.server_id)

    if server_id not in [0, 1, 2]:
        assert "Error: Must input a valid server id in [0, 1, 2]."
        return

    active_servers[server_id] = True
    event.set()
    try:
        start_server()
    except KeyboardInterrupt:
        kill_server()


if __name__ == "__main__":
    main()
