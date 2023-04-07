import grpc
import time
from _thread import *

import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc


def main():
  """
  Connect to the server.
  """

  HOST = '127.0.0.1' 
  PORT = 6061

  with grpc.insecure_channel(HOST + ":" + str(PORT)) as channel:
      stub = pb2_grpc.ChatAppStub(channel)
      
      # Ask for initial username so that the client can listen for messages.
      username = input("Enter a username or create a new one: ")
      if not username:
        return
      
      response = stub.Send(
        pb2.Request(opcode="start", username=username, recipient="", message="", regex="")
      )

      def listen():
        """
        Continuously listen for messages.
        """
        try:
          while True:
            time.sleep(0.05)
            responses = stub.Listen(pb2.Request(opcode='', username=username, recipient='', message="", regex=""))
            if(not responses.empty):
              print(responses.message)
        except ValueError:
            print("Shutting down.")
        except KeyboardInterrupt:
            print("Shutting down.")
        return

      start_new_thread(listen, ())

      # Parse client requests.
      
      try:
        while True:
          request = input("\n>>> ")
          request_list = request.split(" ") 
          if len(request_list) == 0:
            continue

          # Initialize parameters of Request
          opcode = request_list[0]
          recipient = ""
          message = ""
          regex = ""

          # Create account.
          if opcode == "create": 
            username = request_list[1]

          # Log in.
          elif opcode == "login": 
            username = request_list[1]

          # List accounts.
          elif opcode == "list": 
            if len(request_list) > 1:
              regex = request_list[1]
          
          # Send message to a user.
          elif opcode == "send":
            recipient = request_list[1]
            message = request_list[2]
   
          # Delete account
          elif opcode == "delete":
            recipient = request_list[1]

          else:
            if opcode != "":
              print("Error: Invalid command.", flush = True)
            continue
          
          response = stub.Send(pb2.Request(opcode=opcode, username=username, recipient=recipient, message=message, regex=regex))
          print(response.response, flush = True)

      except KeyboardInterrupt:
          response = stub.Send(pb2.Request(opcode="except", username=username, recipient='', message="", regex=""))
          return



if __name__ == "__main__":
  main()
