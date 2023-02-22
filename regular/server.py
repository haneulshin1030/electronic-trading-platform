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
  message_to_recipient = "\nFrom " + username + ": " + message
  message_to_sender = "Message sent"
  message_sent = False

  # if receive_user is logged in, attempt to send the message
  print(receive_user, logged_in[receive_user])
  if logged_in[receive_user]:
    receive_user_client = clients[receive_user]
    message_sent = receive_user_client.send(message_to_recipient.encode('ascii'))
    print("Message sent")
  
  if not message_sent:
    message_to_sender = "Message delivering"
    if username in messages[receive_user]:
      messages[receive_user][username].append(message_to_recipient)
    else:
      messages[receive_user][username] = [message_to_recipient]
  
  return message_to_sender

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

# send undelivered messages
def send_undelivered_messages(client, username):
  messages_to_recipient = ""
  for send_user in messages[username]:
    messages_list = messages[username][send_user]
    length = len(messages_list)
    for i in range(length):
      messages_to_recipient += messages_list[i]
    
    messages_to_recipient += "\n"

    # remove delivered messages
    # TODO: can probably replace with deletion?
    messages[username][send_user] = messages[username][send_user][length:]

  if messages_to_recipient != "":
    client.send(messages_to_recipient.encode('ascii'))
    print("Messages sent")
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
        continue
      # generate ID
      accounts[username] = str(random.randint(1, 1000))
      messages[username] = {}
      account_id = login(client, username)
      data = "Account " + username + " logged in."
    elif opcode == '2': # login
      username = data_list[1]
      if username not in accounts:
        data = "Username does not exist."
        continue
      print("Param: " + username)
      account_id = login(client, username)
      send_undelivered_messages(client, username)
      data = username + " logged in." 
    elif opcode == '3': # list accounts
      criteria = data_list[1]
      print("Param: " + criteria)
      match_accounts = list_accounts(criteria)
      data = "Accounts: " + str(match_accounts)
    elif opcode == '4': # send message
      receive_user = data_list[1]
      if receive_user not in accounts:
        data = "Username " + receive_user + " does not exist."
        continue
      message = data_list[2]
      data = send_message(username, receive_user, message)
    elif opcode == '5': # delete account
      username = data_list[1]
      try:
        data = "Account " + username + " deleted."
        del accounts[username]
        del messages[username]
        del logged_in[username]
        del clients[username]
      except KeyError:
        data = "Account " + username + " doesn't exist."
    else: # error catching
      print("Error: invalid opcode")

    # send back reversed string
    if data:
      client.send(data.encode('ascii'))

  if username:
    logged_in[username] = False
  # connection closed

  client.close()


def main():
  HOST = '127.0.0.1'
  PORT = 6043

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
  
