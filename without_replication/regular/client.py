import socket
import sys

from _thread import *
import threading
from threading import Thread
import time

# Event to indicate that threads are running
thread_running_event = threading.Event()

def kill_client(client_socket):
  """
  Close thread and socket for the client (if an error such as a keyboard interrupt occurs).
  """
  # Close client and thread.
  try:
      client_socket.shutdown(socket.SHUT_RDWR)
  # If client socket is already closed.
  except OSError:
      pass
  print("Closed thread and socket.")
  client_socket.close()
  sys.exit(0)

def receive_server_messages(client_socket):
  """
  Receive server messages
  """
  while thread_running_event.is_set():
    try:
      response = client_socket.recv(1024)
      sys.stdout.flush()
      print(str(response.decode('ascii')))
      thread_running_event.wait()
    except ConnectionResetError:
      kill_client()
    if not response:
      thread_running_event.clear()
  return

def main():
  HOST = '127.0.0.1' 
  PORT = 6065

  client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
  client_socket.connect((HOST, PORT))

  thread_running_event.set()
  start_new_thread(receive_server_messages, (client_socket,))

  # Send requests to the server.
  while thread_running_event.is_set():
    time.sleep(0.001)
    sys.stdout.flush()
    request = input("\n>>> ")

    # If we receive a blank space, send a new command prompt. Else, send the request to the server.
    if request != "":
      client_socket.send(request.encode('ascii'))
  
  try:
    while True and thread_running_event.is_set():
      pass
  except KeyboardInterrupt:
    kill_client()
  kill_client()


if __name__ == "__main__":
  main()
