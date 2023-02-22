import grpc
import re

import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc
from concurrent import futures

# Maximum message size
MAX_MESSAGE_SIZE = 280

# Record mapping username -> boolLoggedIn, where boolLoggedIn is True if and only if username is logged in
logged_in = {}

# Record mapping receive_username -> [message_1, ..., message_n], where message_i is a string of the form "From {user}: {message}"
messages = {}


def list_accounts(criteria, logged_in=logged_in):
  """
  List accounts (or a subset of the accounts, by text wildcard).
  """
  if criteria == "":
    return list(logged_in.keys())
  else:
    matching_names = []
    regex = re.compile(criteria)
    for key in logged_in.keys():
      if regex.match(key):
        matching_names.append(key)
    return matching_names


def login(username, logged_in=logged_in):
  """
  Log the user in.
  """
  logged_in[username] = True
  return "Account " + username + " logged in."


def create_account(username):
  """
  Create new account.
  """
  messages[username] = {}
  return login(username)


class ChatApp(pb2_grpc.ChatAppServicer):
  def __init__(self):
    pass

  def Listen(self, request, context):
    """
    Listen for pending messages.
    """
    message_list = []
    if request.username in messages:
      message_list = messages[request.username]
      messages[request.username] = []
    return pb2.Responses(message = "\n".join(message_list), empty = len(message_list) == 0)

  def Send(self, request, context):
    """
    Send request to server.
    """
    opcode = request.opcode
    response = None

    # Create account.
    if opcode == "create": 
      username = request.username

      # Check whether username is unique.
      if username in logged_in:
        response = "Username already exists."
      else:    
        # Create new user.
        response = create_account(username)

    # Log in.
    elif opcode == "login": 
      username = request.username

      # Check whether user exists.
      if username not in logged_in:
        response = "Username does not exist."
      else:
        response = login(username)

    # Response to starting prompt.
    elif opcode == "start": 
      username = request.username

      # Check whether user exists.
      if username not in logged_in:
        response = create_account(username)
      else:
        response = login(username)

    # List accounts.
    elif opcode == "list": 
      criteria = request.regex
      match_accounts = list_accounts(criteria)
      response = "Accounts: " + str(match_accounts)
    
    # Send message to a user.
    elif opcode == "send":
      username = request.username
      receive_user = request.recipient

      # Check whether recipient exists.
      if receive_user not in logged_in:
        response = "Username " + receive_user + " does not exist."
      # Send message.
      else:
        messages[receive_user].append(("From " + username + ": " + request.message)[0:MAX_MESSAGE_SIZE])
        response = "Message sent to " + receive_user

    # Delete account
    elif opcode == "delete":
      user_to_delete = request.recipient
      if logged_in[user_to_delete]:
          response = "Cannot delete a logged in user."
      else:
        if user_to_delete in logged_in:
          del messages[user_to_delete]
          del logged_in[user_to_delete]
          response = "Account " + user_to_delete + " deleted."
        else:
          response = "Account " + user_to_delete + " doesn't exist."
   
    # Exception
    elif opcode == "except":
      del messages[request.username]
      del logged_in[request.username]
      return pb2.Response(response = "")

    # Error checking for invalid opcode
    else:
      if opcode != "":
        response = "Invalid command."
      else:
        response = ""

    if response:
      print(response)
      return pb2.Response(response = response) 


def main():
  HOST = '127.0.0.1'
  PORT = 6061
  """
  Create the server.
  """

  try:
      server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
      pb2_grpc.add_ChatAppServicer_to_server(ChatApp(), server)
      server.add_insecure_port(HOST + ":" + str(PORT))
      server.start()
      print(f"Socket is listening on {HOST}:{PORT}")
      server.wait_for_termination()
  except KeyboardInterrupt:
      server.stop(0)
  return

if __name__ == "__main__":
  main()
  
