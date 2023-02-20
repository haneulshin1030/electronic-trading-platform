import socket
import mysql.connector
import random
from _thread import *
import threading

p_lock = threading.Lock()

# accounts: {name: id}
accounts = {}

# key: ID, value: dictionary of {recipientID: messages}
# messages = {
#   sendUserID: {receiveUserID1: [message1], receiveUserID2: [message1, message2]}
# }
messages = {}

# methods for different operations of wire protocol
def create_account(username):
  account_id = str(random.randint(0, 1000))

  if username in accounts:
    print("Username already exists.")
    return

  # generate ID
  accounts[username] = account_id
  messages[account_id] = {}
  
  data = "account_id: " + str(account_id) + "\n"
  print(data)

# multithreading
def threaded(client):
  while True:
    data_list = []
    # data received from client
    data = client.recv(1024)
    data_str = data.decode('UTF-8')
    if not data:
        print('Error: nothing received')
        break
    print(data_str + "\n")
    
    # Split data into each component
    data_list = data_str.split('|')
    opcode = data_list[0]
    print("Opcode:" + str(opcode))
    
    # Wire protocol by opcode
    if opcode == '1':
      print("Param:" + data_list[1])
      create_account(data_list[1])

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
  