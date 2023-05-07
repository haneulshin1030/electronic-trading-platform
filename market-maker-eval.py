import grpc
import threading
import sys
import numpy as np
import time
import random
import os
from _thread import *

import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc


HOST = "127.0.0.1"
PORT = 8000

# Record mapping index -> replica.
server_list = [f"{HOST}:{PORT}", f"{HOST}:{PORT + 1}", f"{HOST}:{PORT+ 2}"]


def listen(stub, username):
    """
    Listen for messages from other clients.
    """
    messages = stub.SendClientMessages(pb2.Username(username=username))

    try:
        while True:
            # When a new message is found, iterate to it and print it.
            response = next(messages)
            # print(response.response)
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
                response = stub.FindLeader(pb2.LeaderRequest())
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
        opcode = "create"
        username = "user" + str(random.randint(1, 5000))
        password = "p@ssw0rD"

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

    # to ensure all users are logged in during experiment
    # before trades happen
    time.sleep(5) 

    listen_thread = threading.Thread(target=(listen), args=(stub, username))
    listen_thread.start()

    # MM params
    fades = {}
    sizes = {}
    fades['buy'] = [i + random.uniform(0, 0.02)
                    for i in np.arange(0.05, 0.51, 0.05)]
    fades['sell'] = [i + random.uniform(0, 0.02)
                     for i in np.arange(0.05, 0.51, 0.05)]
    sizes['buy'] = random.sample(range(50, 150), 10)
    sizes['sell'] = random.sample(range(50, 150), 10)

    symbol = "AAPL"

    # make this more nuanced
    if symbol == "AAPL":
        fair = 169
    elif symbol == "TSLA":
        fair = 160

    num_trades = 2 * len(fades)

    # while True:
    try:
        # while True:
        num_trade = 0
        start_time = time.time()
        for dir in ['buy', 'sell']:
            for fade, size in zip(fades[dir], sizes[dir]):
                num_trade += 1
                price = round(fair + fade, 2)
                response = stub.RequestClientOrder(
                    pb2.ClientOrder(
                        opcode="mm_update" if num_trade == num_trades else "mm",
                        username=username,
                        password=password,
                        symbol=symbol,
                        dir=dir,
                        price=price,
                        size=size,
                    )
                )
                # print_response(response.response)
        # sys.exit(0)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time: {elapsed_time} seconds")
        os._exit(0)
        

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

        # sleep(0.5)

    # Exception for if the previous leader server went down and a new leader was determined.
    except (grpc._channel._InactiveRpcError, LeaderDisconnected):
        # Terminate the current listening thread and find a new leader.
        listen_thread.join()
        leader = find_leader()
        channel = grpc.insecure_channel(server_list[leader])
        stub = pb2_grpc.ChatStub(channel)

        # Start the listening thread.
        listen_thread = threading.Thread(
            target=(listen), args=(stub, username))
        listen_thread.start()

        print("Redirected to a new server; please repeat your request.")
        pass
    # Exception for if the user does a keyboard interrupt.
    except KeyboardInterrupt:
        try:
            response = stub.RequestClientOrder(
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
        listen_thread.join()
        # break


if __name__ == "__main__":
    main()