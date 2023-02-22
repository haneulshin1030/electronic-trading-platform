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

testing = False
def print_test(text):
  if testing:
    print(text)

def receive_server_messages(clientsocket):
  # global sending_message
  while True:
    print_test("waiting 1a")
    event.wait(timeout=0.1)
    print_test("1b")
    data = clientsocket.recv(1024)
    print_test("1c")
    event.clear()
    print_test("1d")
    # print_test('\nReceived from the server: ', str(data.decode('ascii')))
    sys.stdout.flush()
    print(str(data.decode('ascii')))
    print_test("1e")
    event.set()
    print_test("1f")
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
    print_test("waiting 2a")
    event.wait()
    print_test("2b")
    time.sleep(0.001)
    sys.stdout.flush()
    print_test("2c")
    event.clear()
    print_test("2d")
    ans = input("\n>>> ")
    print_test("2e")

    if ans != "":
      # print(2)
      clientsocket.send(ans.encode('ascii'))
    print_test("2f")
    event.set()
    print_test("2g")

      # print the received message
      # here it would be a reverse of sent message
  
  # close the connection
  clientsocket.close()


if __name__ == "__main__":
  main()