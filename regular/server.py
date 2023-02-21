import mysql.connector
import random
import re
import socket

from _thread import *
import threading
from threading import Thread

p_lock = threading.Lock()

# accounts: {name: id}
accounts = {}

# messages = {
#   receiveuser: {senduser: [message1, ...], senduser: [message1]}
# }
messages = {}

'''
METHODS for different operations of wire protocol
'''

# account creation
def create_account(username):
  account_id = str(random.randint(1, 1000))

  if username in accounts:
    print("Username already exists.")
    return

  # generate ID
  accounts[username] = account_id
  messages[username] = {}
  
  return account_id

# login
def login(username):
  account_id = accounts[username]
  return account_id

# send message
def send_message(username, receive_user, message):
  if username in messages[receive_user]:
    messages[receive_user][username].append(message)
  else:
    messages[receive_user][username] = [message]

# list accounts (or a subset of the accounts, by text wildcard)
def list_accounts(criteria):
  if criteria == "":
    return list(accounts.keys())
  else:
    matching_names = []
    regex = re.compile(criteria)
    for key in accounts.keys():
      if regex.match(key):
        matching_names.append(key)
    return matching_names


# multithreading
def threaded(client):
  account_id = 0
  username = ""

  while True:
    # always check for any undelivered messages
    if username != "":
      print('Entering check')
      for send_user in messages[username]:
        messages_list = messages[username][send_user]
        length = len(messages_list)
        messages_output = ""
        for i in range(length):
          messages_output += "\nFrom " + send_user + ": " + messages_list[i] + "\n"
        
        print("messages_output: " + messages_output)
        client.send(messages_output.encode('ascii'))

        # remove delivered messages
        messages[username][send_user] = messages[username][send_user][length:]

    data_list = []
    # data received from client
    data = client.recv(1024)
    data_str = data.decode('UTF-8')
    if not data:
        print('Nothing received')
        break
    print(data_str + "\n")
    
    # split data into each component
    data_list = data_str.split('|')
    opcode = data_list[0]
    print("Opcode:" + str(opcode))
    
    # wire protocol by opcode
    if opcode == '1': # create account
      username = data_list[1]
      print("Param: " + username)
      account_id = create_account(username)
      data = "account_id: " + str(account_id) + "\n"
      # print("create_account account_id: ", str(account_id))
    elif opcode == '2': # login
      print("Param: " + username)
      account_id = login(username)
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
      send_message(username, receive_user, message)
      data = "message: " + str(message) + "\n"
    elif opcode == '5': # delete account
      continue
    else: # error catching
      print("Error: invalid opcode")

    # send back reversed string
    client.send(data.encode('ascii'))

  # connection closed

  client.close()


def main():
  HOST = '127.0.0.1' 
  PORT = 6000

  serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
  serversocket.bind((HOST, PORT))

  serversocket.listen(1)
  print("Socket is listening")

  # a forever loop until client wants to exit
  while True:
    # connect to client 
    clientsocket, addr = serversocket.accept()
    print('Connected to by:', addr[0], ':', addr[1])

    # new thread, return identifier
    start_new_thread(threaded, (clientsocket,))
  
  serversocket.close()


if __name__ == "__main__":
  main()
  