import grpc
from _thread import *
import threading
from threading import Thread

import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc


HOST = '127.0.0.1' 
PORT = 6060

class Client:
  def __init__(self, input):
    self.input = input

    # create gRPC channel & stub (bind client & server)
    self.channel = grpc.insecure_channel(HOST + ':' + str(PORT))
    self.stub = rpc.ChatServerStub(self.channel)

  # sends data to server
  def send_data(self, event):
    data_object = pb2.Data()
    data_object.data = self.input
    self.stub.SendData(data_object)


def main():
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
      # start client
      Client(ans)


if __name__ == "__main__":
  main()
