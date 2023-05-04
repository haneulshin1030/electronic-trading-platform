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
import re
from sortedcontainers import SortedDict


import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc
from concurrent import futures

HOST = "127.0.0.1"
PORT = 8000

########## SERVER INFORMATION ##########

# Current threads that are running.
threads = []

# Event for when threads are running, i.e. not stopped.
event = threading.Event()

# Current server.
server = None

# Dictionary mapping index -> replica.
address_list = [f"{HOST}:{PORT}", f"{HOST}:{PORT + 1}", f"{HOST}:{PORT+ 2}"]

# Server id of leader.
leader = None

# Current live servers.
active_servers = [None, None, None]

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


def save_data(
    open_orders, order_book, user_status, passwords, positions, messages, file_name
):
    """
    Store the current dictionary of the order book, user online status, user passwords, user positions, and user messages.
    """

    # Store open orders
    with open(f"open_orders_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for symbol in symbol_list:
            for dir in dir_list:
                for price in open_orders[symbol][dir]:
                    for username, size in open_orders[symbol][dir][price]:
                        csv_writer.writerow(
                            [symbol] + [dir] + [price] + [username] + [size]
                        )

    # Store order book
    with open(f"order_book_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for symbol in symbol_list:
            for dir in dir_list:
                for price, size in list(order_book[symbol][dir].items()):
                    csv_writer.writerow([symbol] + [dir] + [price] + [size])

    # Store user status
    with open(f"user_status_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for username, online in list(user_status.items()):
            csv_writer.writerow([username] + [online])

    # Store user status
    with open(f"passwords_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for username, password in list(passwords.items()):
            csv_writer.writerow([username] + [password])

    # Store positions
    with open(f"positions_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for user in positions.keys():
            for symbol, position in list(positions[username].items()):
                csv_writer.writerow([username] + [symbol] + [position])

    # Store message queue
    with open(f"messages_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for username, message_list in list(messages.items()):
            for message in message_list:
                csv_writer.writerow([username] + [message])


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

    update_data()
    return


def match_trade(
    username, dir, symbol, sgn, opp_sgn, price, size, order_was_taken=False
):
    global positions, messages, open_orders, order_book

    if order_was_taken:
        print(f"Order book before match: \n {order_book[symbol]}\n")

    # Update user information
    positions[username][symbol] += sgn * size
    positions[username]["USD"] += opp_sgn * size * price
    print("POSITIONS:", positions)
    update_data()

    # If the user is the counterparty who posted the trade (maker)
    if order_was_taken:
        messages[username].append(trade_message(username, dir, symbol, price, size))
        print("Messages[username]:", messages)
        # Update open orders

        # If total quantity at the price with the counterparty was taken
        if size < open_orders[symbol][dir][price][0][1]:
            open_orders[symbol][dir][price][0][1] -= size
        else:
            open_orders[symbol][dir][price].pop(0)
            if len(open_orders[symbol][dir][price]) == 0:
#                 open_orders[symbol][dir].pop(price)
                del open_orders[symbol][dir][price]

        # Update order book

        # If total quantity at the price was taken
        if size < order_book[symbol][dir][price]:
            order_book[symbol][dir][price] -= size
        else:
#             order_book[symbol][dir].pop(price)
            del order_book[symbol][dir][price]

        update_data()

    if order_was_taken:
        print(f"Order book after match: \n {order_book[symbol]}\n")
    return trade_message(username, dir, symbol, price, size)


def update_data():
    """
    Sends the current dictionary of the order book, user online status, user passwords, user positions, and user messages to each of the servers.
    """
    global open_orders, order_book, user_status, passwords, positions, messages, server_id
    if leader != server_id:
        return
    for id, alive in enumerate(active_servers):
        if alive and id != leader and id != server_id:
            channel = grpc.insecure_channel(address_list[id])
            stub = pb2_grpc.ChatStub(channel)
            try:
                save_data(
                    open_orders,
                    order_book,
                    user_status,
                    passwords,
                    positions,
                    messages,
                    file_name,
                )
                stub.Send(
                    pb2.ServerData(
                        open_orders=json.dumps(open_orders),
                        order_book=json.dumps(order_book),
                        user_status=json.dumps(user_status),
                        passwords=json.dumps(passwords),
                        positions=json.dumps(positions),
                        messages=json.dumps(messages),
                    )
                )
            except:
                print(f"Server failure: {id}")
                active_servers[id] = False


class ChatServicer(pb2_grpc.ChatServicer):
    def Heartbeat(self, request, context):
        return pb2.HeartbeatResponse(leader=leader)

    def Send(self, order, context):
        """
        Send updated data to the databases.
        """
        global open_orders, order_book, user_status, passwords, positions, messages
        open_orders = json.loads(order.open_orders)
        order_book = json.loads(order.order_book)
        user_status = json.loads(order.user_status)
        passwords = json.loads(order.passwords)
        positions = json.loads(order.positions)
        messages = json.loads(order.messages)

        save_data(
            open_orders,
            order_book,
            user_status,
            passwords,
            positions,
            messages,
            file_name,
        )
        return pb2.UserResponse()

    def ServerResponse(self, order, context):
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

    def ClientMessages(self, username, context):
        """
        Return the client's pending messages, and update the data accordingly.
        """
        username = username.username

        # Shouldn't need this
        # if user not in user_status:
        #     user_status.append(username)
        #     update_data()

        while username in messages.keys():
            for message in messages[username]:
                yield pb2.Response(response=message)
            messages[username] = []
        update_data()

    def Leader(self, request, context):
        return pb2.LeaderResponse(leader=leader)


def login(username, password):
    """
    Log the user in.
    """
    global user_status
    user_status[username] = True
    update_data()
    return "Success: Account " + username + " logged in."


def create_account(username, password):
    """
    Create new account and initialize user information.
    """

    global user_status, passwords, positions, messages

    user_status[username] = True
    passwords[username] = password
    positions[username] = zero_positions
    messages[username] = []
    update_data()
    return "Success: Account " + username + " created and logged in."


def valid_password(password):
    return True


def trade_message(username, dir, symbol, price, size):
    global messages
    action_past = "Bought" if dir == "buy" else "Sold"
    preposition = "for" if dir == "buy" else "at"
    return f"{action_past} {size} shares of {symbol} {preposition} ${price:.2f}/share."


def post_message(username, dir, symbol, price, size):
    # Save dictionary data
    with open('order_book.pickle', 'wb') as file:
        pickle.dump(order_book[symbol], file)
    with open('positions.pickle', 'wb') as file:
        pickle.dump(positions[username], file)

    print("Order book:", order_book)
    
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
    global leader, server_id
    global user_status, passwords, positions, messages
    if server_id != leader:
        return pb2.Response(response=ERROR_NOT_LEADER)

    current_user = None
    response = None

    # Create account.
    if opcode == "create":

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
        new_username = username

        # Check whether user exists.
        if username not in user_status or passwords[username] != password:
            response = "Failure: Username and/or password is not valid."
        else:
            response = login(username, password)

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

        # TODO: Lock?

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
            print(order_book)
            print(open_orders)
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
            match_trade(username, dir, symbol, sgn, opp_sgn, average_price, trade_size)
            response = trade_message(username, dir, symbol, average_price, trade_size)
        else:
            response = ""

        if trade_size < size:
            print(f"Posting order for the remaining {size - trade_size} shares...")

            # Update open orders and order book
            post_order(username, dir, symbol, sgn, price, size - trade_size)
            post_message_success = post_message(
                username, dir, symbol, price, size - trade_size
            )
            print(f"{post_message_success}\n")
            print(f"Open orders: \n {open_orders[symbol]}\n")
            response += ("\n" if trade_size > 0 else "") + post_message_success
        # Unlock?

    # Exception
    elif opcode == "except":
        del messages[username]
        del logged_in[username]
        del user_list[username]
        return pb2.Response(response="")

    # Error checking for invalid opcode
    else:
        if opcode != "":
            response = "Invalid command."
        else:
            response = ""

    if response:
        # Save dictionary data
        with open('order_book.pickle', 'wb') as file:
            pickle.dump(order_book[symbol], file)
        with open('positions.pickle', 'wb') as file:
            pickle.dump(positions[username], file)

        print(f'Sending response to server: "{response}" \n')
        return pb2.Response(response=response)


def send_heartbeat(stub, id):
    """
    Send heartbeat to the server.
    """
    try:
        response = stub.Heartbeat(pb2.HeartbeatRequest())
        active_servers[id] = True
        global leader
        leader = response.leader
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


def check_leader():
    """
    Check if leader is currently active. If not, set a new leader.
    """
    global leader, messages
    if leader is None or not active_servers[leader]:
        for id, alive in enumerate(active_servers):
            if alive:
                leader = id
                print(f"The new leader is {leader}")
                return
        # No leaders found
        print("Error: No active servers.")
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
    sleep_time = random.randint(1, 5)
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
            heartbeat_thread = threading.Thread(target=start_heartbeat, args=(i,))
            heartbeat_thread.start()
            threads.append(heartbeat_thread)

    global server
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=12))
    pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server)

    global open_orders, order_book, user_status, passwords, positions, messages

    # ^ make sure these are initialized?

    # Read csv files into the server data

    # open(f"open_orders_{server_id}.csv", "a+")
    # with open(f"open_orders_{server_id}.csv", "r+") as csv_file:
    #   csv_reader = csv.reader(csv_file, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
    #   for row in csv_reader:
    #     dir, symbol, price, username, size = row
    #     if price in open_orders[symbol][dir]:
    #       open_orders[symbol][dir][price].append([username, size])
    #     else:
    #       open_orders[symbol][dir][price] = ([username, size])

    # # Store open orders
    # with open(f"open_orders_{server_id}.csv", "w+") as f:
    #     csv_writer = csv.writer(f)

    #     for symbol in symbol_list:
    #       for dir in dir_list:
    #         for price in open_orders[symbol][dir]:
    #           for username, size in open_orders[symbol][dir][price]:
    #             csv_writer.writerow([symbol] + [dir] + [price] + [username] + [size])

    # file_name = server_id
    # # Store order book
    # with open(f"order_book_{file_name}.csv", "w+") as f:
    #     csv_writer = csv.writer(f)

    #     for symbol in symbol_list:
    #       for dir in dir_list:
    #         for price, size in list(order_book[symbol][dir].items()):
    #           csv_writer.writerow([symbol] + [dir] + [price] + [size])

    # # Store user status
    # with open(f"user_status_{file_name}.csv", "w+") as f:
    #     csv_writer = csv.writer(f)

    #     for username, online in list(user_status.items()):
    #       csv_writer.writerow([username] + [online])

    # # Store user status
    # with open(f"passwords_{file_name}.csv", "w+") as f:
    #     csv_writer = csv.writer(f)

    #     for username, password in list(passwords.items()):
    #       csv_writer.writerow([username] + [password])

    # # Store positions
    # with open(f"positions_{file_name}.csv", "w+") as f:
    #     csv_writer = csv.writer(f)

    #     for user in positions.keys():
    #       for symbol, position in list(positions[username].items()):
    #         csv_writer.writerow([username] + [symbol] + [position])

    # # Store message queue
    # with open(f"messages_{file_name}.csv", "w+") as f:
    #     csv_writer = csv.writer(f)

    #     for username, message_list in list(messages.items()):
    #       for message in message_list:
    #         csv_writer.writerow([username] + [message])

    #     for row in csv_reader:
    #         if row[0] == "users_list":
    #            user_list += row
    #            continue
    #         print(row[0], row[1])
    #         if row[0] in messages.keys():
    #           messages[row[0]].append(row[1])
    #         else:
    #            user_list.append(row[0])
    #            messages[row[0]] = [row[1]]
    #     update_data()
    # open(f"{server_id}.csv", "w+")

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
