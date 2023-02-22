import mysql.connector
import random
import re
import socket
import time

from _thread import *
import threading
from threading import Thread


# TODO: limit messages to 280 characters

p_lock = threading.Lock()

# accounts: {name: id}
accounts = {}

# messages = {
#   receiveuser: {senduser: [message1, ...], senduser: [message1]}
# }
messages = {}

# logged_in: {username: boolLoggedIn}
logged_in = {}

# clients: {username: client}
clients = {}

'''
METHODS for different operations of wire protocol
'''

# send message
def send_message(username, receive_user, message):
  # if receive_user is logged in, attempt to send the message
  if logged_in[receive_user]:
    receive_user_client = clients[receive_user]
    message_sent = receive_user_client.send(message.encode('ascii'))
  
  success_statement = None

  if message_sent:
    success_statement = "Message sent from " + username + " to " + receive_user + ": " + message
  else:
    if username in messages[receive_user]:
      messages[receive_user][username].append(message)
    else:
      messages[receive_user][username] = [message]
  
  return success_statement

# list accounts (or a subset of the accounts, by text wildcard)
def list_accounts(criteria, accounts=accounts):
  if criteria == "":
    return list(accounts.keys())
  else:
    matching_names = []
    regex = re.compile(criteria)
    for key in accounts.keys():
      if regex.match(key):
        matching_names.append(key)
    return matching_names

# send undelivered messages
def send_undelivered_messages(client, username):
  messages_output = ""
  for send_user in messages[username]:
    messages_list = messages[username][send_user]
    length = len(messages_list)
    for i in range(length):
      messages_output += "\nFrom " + send_user + ": " + messages_list[i] + "\n"
    
    messages_output += "\n"

    # remove delivered messages
    # TODO: can probably replace with deletion?
    messages[username][send_user] = messages[username][send_user][length:]

  print("messages_output: " + messages_output)
  client.send(messages_output.encode('ascii'))
  return

# login
def login(client, username):
  logged_in[username] = True # TODO: lock something?
  account_id = accounts[username]
  clients[username] = client
  return account_id
  
# multithreading: get data and process request
def threaded(client):
  account_id = 0
  username = None

  while True:
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
      if username in accounts:
        print("Username already exists.")
        return

      # generate ID
      accounts[username] = str(random.randint(1, 1000))
      messages[username] = {}
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

    # send back reversed string
    if data:
      client.send(data.encode('ascii'))

  # connection closed

  client.close()


def main():
  HOST = '127.0.0.1'
  PORT = 6025

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
  