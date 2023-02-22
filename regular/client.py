import socket
import sys

from _thread import *
import threading
from threading import Thread
import time


# lock = threading.Lock()
# sending_message = False

event = threading.Event()
event.set()

def receive_server_messages(clientsocket):
  # global sending_message
  while True:
    event.wait(timeout=0.1)
    data = clientsocket.recv(1024)
    event.clear()
    sys.stdout.flush()
    print(str(data.decode('ascii')))
    event.set()
  return

def main():
  HOST = '127.0.0.1' 
  PORT = 6043

  clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
  clientsocket.connect((HOST, PORT))

  # global sending_message

  start_new_thread(receive_server_messages, (clientsocket,))

  # message to send to server
  while True:
    event.wait()
    time.sleep(0.001)
    sys.stdout.flush()
    event.clear()
    ans = input("\n>>> ")

    if ans != "":
      clientsocket.send(ans.encode('ascii'))
    event.set()

  # close the connection
  clientsocket.close()


if __name__ == "__main__":
  main()
