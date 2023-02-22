import socket

from _thread import *
import threading
from threading import Thread

# lock = threading.Lock()

sending_message = False

def receive_messages(clientsocket):
  global sending_message
  while True:
    if not sending_message:
      data = clientsocket.recv(1024)
      print('\nReceived from the server: ', str(data.decode('ascii')))
  return

def main():
  HOST = '127.0.0.1' 
  PORT = 6025

  clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
  clientsocket.connect((HOST, PORT))

  global sending_message

  # start_new_thread(receive_messages, (clientsocket,))

  # message to send to server
  while True:
    ans = input("\nEnter your request: ")

    if ans == "":
      ans2 = input("\nDo you want to continue (y/n):")
      if ans2 == 'y':
        continue
      else:
        return
    else:
      sending_message = True #lock..?
      clientsocket.send(ans.encode('ascii'))
      data = clientsocket.recv(1024)
      print('Received from the server1: ', str(data.decode('ascii')))
      sending_message = False

      # print the received message
      # here it would be a reverse of sent message
  
  print("Blah")
  # close the connection
  clientsocket.close()


if __name__ == "__main__":
  main()