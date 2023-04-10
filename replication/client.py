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

def main():
    listen_thread = None

    leader = find_leader()
    print(server_list[leader])
    channel = grpc.insecure_channel(server_list[leader])
    stub = pb2_grpc.ChatStub(channel)
      
    # Ask for initial username so that the client can listen for messages.
    username = input("Enter a username or create a new one: ")

    if not username:
      return 
    response = stub.ServerResponse(
      pb2.Request(opcode="start", username=username, recipient="", message="", regex="")
    )

    print_response(response.response)

    listen_thread = threading.Thread(target=(listen), args=(stub, username))
    listen_thread.start()


    while True:
      try:
        while True:
          request = input("\n>>> ")
          request_list = request.split(" ") 
          if len(request_list) == 0:
            continue

          # Initialize parameters of Request
          opcode = request_list[0]
          recipient = ""
          message = ""
          regex = ""

          # Parse client requests.

          # Create account.
          if opcode == "create": 
            username = request_list[1]

          # Log in.
          elif opcode == "login": 
            username = request_list[1]

          # List accounts.
          elif opcode == "list": 
            if len(request_list) > 1:
              regex = request_list[1]
          
          # Send message to a user.
          elif opcode == "send":
            recipient = request_list[1]
            message = request_list[2]
    
          # Delete account
          elif opcode == "delete":
            recipient = request_list[1]

          else:
            if opcode != "":
              print("Error: Invalid command.", flush = True)
            continue
          response = stub.ServerResponse(pb2.Request(opcode=opcode, username=username, recipient=recipient, message=message, regex=regex))
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
            response = stub.ServerResponse(pb2.Request(opcode="except", username=username, recipient='', message="", regex=""))
            print_response(response.response)
          except grpc._channel._InactiveRpcError:
              pass
          listen_thread.join()
          break

if __name__ == "__main__":
  main()
