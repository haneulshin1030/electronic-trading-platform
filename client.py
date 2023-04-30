import grpc
import threading
import sys
import time
from _thread import *

import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc


HOST = '127.0.0.1'
PORT = 8000

# Record mapping index -> replica.
server_list = [f"{HOST}:{PORT}", f"{HOST}:{PORT + 1}", f"{HOST}:{PORT+ 2}"]

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
      print(response, flush = True)

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
    while(not username):
      print("Would you like to log in into an existing account? (Y/n)")

      if query():
        opcode = "login"
        username = input("Username:")
        password = input("Password:")
      else:
        opcode = "create"
        print("Please select a username.")
        username = input("Username:")
        print("Please select a password satisfying the criterion.")
        password = input("Password:")

      response = stub.ServerResponse(
        response = stub.ServerResponse(pb2.Order(opcode=opcode, username=username, password=password, dir="", symbol="", price=-1, size=-1))
      )
      if not response.startswith("Success"):
        username = None

    print_response(response.response)

    listen_thread = threading.Thread(target=(listen), args=(stub, username))
    listen_thread.start()

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
          elif opcode == "send":
            opcode, dir, symbol, price, size = order_params
    
          # Delete account
          # elif opcode == "delete":
          #   recipient = order_params[1]

          else:
            if opcode != "":
              print("Error: Invalid command.", flush = True)
            continue
          
          response = stub.ServerResponse(pb2.Order(opcode=opcode, username=username, password=password, dir=dir, symbol=symbol, price=price, size=size))
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
            response = stub.ServerResponse(pb2.Order(opcode="except", username=username, password="", dir="", symbol="", price=-1, size=-1))
            print_response(response.response)
          except grpc._channel._InactiveRpcError:
              pass
          listen_thread.join()
          break

if __name__ == "__main__":
  main()
