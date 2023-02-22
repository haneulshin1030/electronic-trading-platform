import grpc
from _thread import *
import threading
from threading import Thread

import chatapp_pb2 as chat
import chatapp_pb2_grpc as rpc


def main():
  HOST = '127.0.0.1' 
  PORT = 6060

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
      Client(ans)


if __name__ == "__main__":
  main()
