import sys
import re
import socket
from _thread import *
import threading

# Maximum message size
MAX_MESSAGE_SIZE = 280

# Event to indicate that threads are running
thread_running_event = threading.Event()

# Record mapping username -> boolLoggedIn, where boolLoggedIn is True if and only if username is logged in
logged_in = {}

# Record mapping receive_username -> {sender_username_1: [message_1, ...], sender_username_n: [message_1, ...]} }
messages = {}

# Record mapping username -> client socket
client_sockets = {}

# Record mapping username -> thread
client_threads = {}

def send_message(username, receive_user, message, logged_in=logged_in, messages=messages):
  """
  Send message from user to recipient.
  """
  message_to_recipient = "\nFrom " + username + ": " + message
  message_to_sender = "Message sent to " + receive_user
  message_sent = False

  # If receive_user is logged in, attempt to send the message.
  if receive_user in logged_in and logged_in[receive_user]:
    print(receive_user, logged_in[receive_user])
    receive_user_client = client_sockets[receive_user]
    message_sent = receive_user_client.send(message_to_recipient.encode('ascii'))
    print("Message sent")
  
  # If message was not sent, queue it.
  if not message_sent: 
    message_to_sender = "Message delivering"
    if username in messages[receive_user]:
      messages[receive_user][username].append(message_to_recipient)
    else:
      messages[receive_user][username] = [message_to_recipient]
  
  return message_to_sender

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


def send_undelivered_messages(client, username):
  """
  Send undelivered messages to user.
  """
  messages_to_recipient = ""
  for send_user in messages[username]:
    messages_list = messages[username][send_user]
    length = len(messages_list)
    for i in range(length):
      messages_to_recipient += messages_list[i]
    
    messages_to_recipient += "\n"

    # Remove delivered messages
    messages[username][send_user] = messages[username][send_user][length:]

  if messages_to_recipient != "":
    client.send(messages_to_recipient.encode('ascii'))
    print("Messages sent")
  return

def login(client, username, current_thread, logged_in=logged_in):
  """
  Log the user in.
  """
  logged_in[username] = True
  client_sockets[username] = client
  client_threads[username] = current_thread
  return "Account " + username + " logged in."


def create_account(client, username, current_thread):
  """
  Create new account.
  """
  messages[username] = {}
  return login(client, username, current_thread)
  

def kill_server(server_socket):
    """
    Close thread and socket for the server.
    """
    thread_running_event.clear()
    try:
      for username in logged_in:
        client_sockets[username].shutdown(socket.SHUT_RDWR)
        client_threads[username].join()
    # If socket is already closed.
    except OSError:
      pass
    server_socket.close()
    print("Closed threads.")
    sys.exit(0)

def kill_client(username):
  """
  Close thread and socket for the client (if an error such as a keyboard interrupt occurs).
  """
  if not username:
      return
  # Close client and thread for username.
  client_socket = client_sockets[username]
  try:
      if client_socket:
          client_socket.shutdown(socket.SHUT_RDWR)
  # If client socket is already closed.
  except OSError:
      pass
  logged_in[username] = False
  client_socket.close()
  print("Closed thread and socket for " + username)
  sys.exit(0)

def parse_client_request(client, username):
  """
  Parse client request and return it as a string.
  """
  # Parse from client
  request = client.recv(1024) 
    
  # If an error such as a keyboard interrupt occurs, kill the client.
  if not request:
    kill_client(username)
    return

  request_str = request.decode('UTF-8') 
  return request_str

def send_error(client, error):
  """
  Send error message to client.
  """
  error_message = "Error: " + error
  client.send(error_message.encode('ascii'))
  return

def process_user_request(client):
  """
  Process user request.
  """
  username = None
  response = None

  while thread_running_event.is_set():
    # Parse client request
    request_str = parse_client_request(client, username)
    print("Received request: " + request_str + "\n")
    
    # Split data from client into components
    request_list = request_str.split(" ") 

    opcode = request_list[0]
    print("Opcode: " + str(opcode))
    
    # Create account.
    if opcode == "create": 
      username = request_list[1]

      # Check whether username is unique.
      if username in logged_in:
        response = "Username already exists."
        send_error(client, response)
        print(response)
        continue
      
      # Create new user.
      response = create_account(client, username, threading.current_thread())
      print(response)

    # Log in.
    elif opcode == "login": 
      new_username = request_list[1]

      # Log out previous user.
      if username and new_username != username:
        logged_in[username] = False
      
      username = new_username
      # Check whether user exists.
      if username not in logged_in:
        response = "Username does not exist."
        send_error(client, response)
        print(response)
        continue
      response = login(client, username, threading.current_thread())

      # Send any queued messages.
      send_undelivered_messages(client, username)

    # List accounts.
    elif opcode == "list": 
      if len(request_list) == 1:
          criteria = ""
      else:
        criteria = request_list[1]
      match_accounts = list_accounts(criteria)
      response = "Accounts: " + str(match_accounts)
    
    # Send message to a user.
    elif opcode == "send":
      receive_user = request_list[1]

      # Check whether the client is logged in.
      if username is None:
        response = "You must be logged in to send a message."
        send_error(client, response)
        continue

      # Check whether recipient exists.
      if receive_user not in logged_in:
        response = "Username " + receive_user + " does not exist."
        send_error(client, response)
        print(response)
        continue
      
      # Prompt message.
      message_prompt = "\nEnter message below:"
      client.send(message_prompt.encode('ascii'))
      message_str = parse_client_request(client, username)

      # Send message.
      response = send_message(username, receive_user, message_str)

    # Delete account
    elif opcode == "delete":
      user_to_delete = request_list[1]
      if user_to_delete != username and logged_in[user_to_delete]:
          response = "Cannot delete a logged in user."
          send_error(client, response)
          print(response)
          continue
      if user_to_delete == username:
        username = None
      try:
        response = "Account " + user_to_delete + " deleted."
        del messages[user_to_delete]
        del logged_in[user_to_delete]
        del client_sockets[user_to_delete]
        del client_threads[user_to_delete]
      except KeyError:
        response = "Account " + user_to_delete + " doesn't exist."
        send_error(client, response)
        print(response)
        continue
    # Error checking for invalid opcode
    else:
      if opcode != "":
        print("Invalid command.")
      continue

    # Send data back to client.
    if response:
      client.send(response.encode('ascii'))
      response = None

  if username:
    logged_in[username] = False

  # Close connection
  client.close()


def main():
  HOST = '127.0.0.1'
  PORT = 6065

  server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
  server_socket.bind((HOST, PORT))

  server_socket.listen(1)
  thread_running_event.set()
  print(f"Socket is listening on {HOST}:{PORT}")

  try:
    while True:
      # Connect to client
      client_socket, client_address = server_socket.accept()
      print("Connected to " + str(client_address[0]) + ":" + str(client_address[1]))
          # Start new thread
      start_new_thread(process_user_request, (client_socket,))
  
  # If an error such as a keyboard interrupt occurs.
  except:
    kill_server(server_socket)


if __name__ == "__main__":
  main()
  
