import grpc
import threading
from concurrent import futures
import random

import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc

class Server(pb2_grpc.ChatAppServicer):
  def __init__(self):
    # accounts: {name: id}
    self.accounts = {}

    # messages = {
    #   receiveuser: {senduser: [message1, ...], senduser: [message1]}
    # }
    self.messages = {}

    # logged_in: {username: boolLoggedIn}
    self.logged_in = {}

    # clients: {username: client}
    self.clients = {}


  # when client inputs something into server
  def SendData(self, request: pb2.Data, context):
    data_str = str(request.data)

    if not data_str:
      print('Nothing received')
    print(data_str + "\n")
    
    # split data into each component
    data_list = data_str.split('|')

    opcode = data_list[0]
    print("Opcode:" + str(opcode))
    
    # wire protocol by opcode
    if opcode == '1': # create account
      username = data_list[1]
      print("Param: " + username)
      if username in self.accounts:
        print("Username already exists.")
        return pb2.Empty()

      # generate ID
      self.accounts[username] = str(random.randint(1, 1000))
      self.messages[username] = {}
      account_id = login(client, username)
      data = "account_id: " + str(account_id) + "\n"
      # print("create_account account_id: ", str(account_id))
    elif opcode == '2': # login
      username = data_list[1]
      print("Param: " + username)
      account_id = login(client, username)
      send_undelivered_messages(client, username)
      data = "account_id: " + str(account_id) + "\n"
      # print("login account_id: ", str(account_id))
    elif opcode == '3': # list accounts
      criteria = data_list[1]
      print("Param: " + criteria)
      match_accounts = list_accounts(criteria)
      data = "accounts: " + str(match_accounts) + "\n"
    elif opcode == '4': # send message
      receive_user = data_list[1]
      message = data_list[2]
      data = send_message(username, receive_user, message)
    elif opcode == '5': # delete account
      return # TODO
    elif opcode == '6': # print client
      username = data_list[1]
      print(clients[username])
    else: # error catching
      print("Error: invalid opcode")

    return pb2.Empty()


def main():
  HOST = '127.0.0.1'
  PORT = 6060

  # create gRPC server with max 4 threads at a time
  server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))

  # add server to gRPC
  pb2_grpc.add_ChatAppServicer_to_server(Server(), server)
  print("Socket is listening")

  server.add_insecure_port('[::]:' + str(PORT))
  server.start()
  server.wait_for_termination()

if __name__ == "__main__":
  main()