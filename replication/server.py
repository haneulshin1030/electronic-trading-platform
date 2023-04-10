import grpc
import sys
import threading
import time
import csv
import optparse
import concurrent.futures
import random
import json
import re

import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc
from concurrent import futures

HOST = '127.0.0.1'
PORT = 8000

# Current threads that are running.
threads = []

# Event for when threads are running, i.e. not stopped.
event = threading.Event()

# Current server.
server = None

# Record mapping index -> replica.
address_list = [f"{HOST}:{PORT}", f"{HOST}:{PORT + 1}", f"{HOST}:{PORT+ 2}"]

# Server id of leader.
leader = None

# Current live servers.
active_servers = [None, None, None]

# List of currently active users
user_list = []

# Maximum message size
MAX_MESSAGE_SIZE = 280

# Record mapping username -> boolLoggedIn, where boolLoggedIn is True if and only if username is logged in
logged_in = {}

# Record mapping receive_username -> [message_1, ..., message_n], where message_i is a string of the form "From {user}: {message}"
messages = {}

# Error string for if the server is not the leader.
ERROR_NOT_LEADER = "Error: server is not the leader."

def store_messages(messages, file_name):
    """
    Store the current dictionary of pending messages in a CSV file.
    """
    with open(f"{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)
        for username, message_list in list(messages.items()):
          for message in message_list:
            csv_writer.writerow([username] + [message])

def update_data():
    """
    Sends the updated data, including the list of pending messages and the active users, to each of the servers.
    """
    global server_id
    if leader != server_id:
        return
    for id, alive in enumerate(active_servers):
        if alive and id != leader and id != server_id:
            channel = grpc.insecure_channel(address_list[id])
            stub = pb2_grpc.ChatStub(channel)
            try:
                store_messages(messages, server_id)
                stub.Send(pb2.Data(csv=json.dumps(messages), user_list=json.dumps(user_list)))
            except:
                print(f"Server failure: {id}")
                active_servers[id] = False


class ChatServicer(pb2_grpc.ChatServicer):
    def Heartbeat(self, request, context):
        return pb2.HeartbeatResponse(leader=leader)
    
    def Send(self, request, context):
        """
        Send updated data to the databases.
        """
        global messages, user_list, server_id
        messages = json.loads(request.csv)
        user_list = json.loads(request.user_list)
        
        store_messages(messages, server_id)
        return pb2.UserResponse()
    
    def ServerResponse(self, request, context): 
        '''
        Manage the server's response to user input.
        '''
        return handle_server_response(request.opcode, request.username, request.recipient, request.message, request.regex)
    
    def ClientMessages(self, username, context):
        '''
        Return the client's pending messages, and update the data accordingly.
        '''
        username = username.username
        
        if username not in user_list:
            user_list.append(username)
            update_data()

        print(user_list)
        while username in user_list:
            if username in messages and len(messages[username]) != 0:
                for message in messages[username]:
                  yield pb2.Response(response = message)
                messages[username] = []
        update_data()

    def Leader(self, request, context):
        return pb2.LeaderResponse(leader = leader)


def list_accounts(criteria):
  """
  List accounts (or a subset of the accounts, by text wildcard).
  """
  global user_list
  unique_elements = list(set(user_list))
  if criteria == "":
    return unique_elements
  else:
    matching_names = []
    regex = re.compile(criteria)
    for key in unique_elements:
      if regex.match(key):
        matching_names.append(key)
    return matching_names


def login(username):
  """
  Log the user in.
  """
  global user_list
  user_list.append(username)
  update_data()
  return "Account " + username + " logged in."

def create_account(username):
  """
  Create new account.
  """
  messages[username] = []
  return login(username)

def handle_server_response(opcode, request_username, recipient, message, regex):
    '''
    Handle the server's response to the input.
    '''
    # If this server is not the leader, error.
    global leader
    global server_id
    global user_list
    if(server_id != leader):
        return pb2.Response(response = ERROR_NOT_LEADER)

    username = None
    response = None

    # Create account.
    if opcode == "create": 
      username = request_username

      # Log out previous user.
      if username and request_username != username:
        logged_in[username] = False

      # Check whether username is unique.
      if username in user_list:
        response = "Username already exists."
      else:    
        # Create new user.
        response = create_account(username)
        update_data()

    # Log in.
    elif opcode == "login": 
      new_username = request_username

      # Log out previous user.
      if username and new_username != username:
        logged_in[username] = False
      username = new_username   
      
      # Check whether user exists.
      if username not in user_list:
        response = "Username does not exist."
      else:
        response = login(username)

    # Response to starting prompt.
    elif opcode == "start": 
      username = request_username
      print(username)

      # Check whether user exists.
      if username not in user_list:
        response = create_account(username)
      else:
        response = login(username)

    # List accounts.
    elif opcode == "list": 
      criteria = regex
      match_accounts = list_accounts(criteria)
      response = "Accounts: " + str(match_accounts)
    
    # Send message to a user.
    elif opcode == "send":
      username = request_username
      receive_user = recipient
      # Check whether recipient exists.
      if receive_user not in user_list:
        response = "Username " + receive_user + " does not exist."
      # Send message.
      else:
        msg = "From " + username + ": " + message
        messages[receive_user].append(msg)
        response = "Message sent to " + receive_user
        update_data()
        # send_database_and_users()

    # Delete account
    elif opcode == "delete":
      user_to_delete = recipient
      # Unlike in the original version, we do not allow active clients to be logged out.
      if user_to_delete in user_list:
         response = "Cannot delete a user who is currently active."
         return pb2.Response(response = response) 
      
      if user_to_delete in   update_data():
        del messages[user_to_delete]
        del user_list[user_to_delete]
        response = "Account " + user_to_delete + " deleted."
        update_data()
      else:
        response = "Account " + user_to_delete + " doesn't exist."
   
    # Exception
    elif opcode == "except":
      del messages[request_username]
      del logged_in[request_username]
      del user_list[request_username]
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

def send_heartbeat(stub, id):
    """
    Send heartbeat to the server.
    """
    try: 
        response = stub.Heartbeat(pb2.HeartbeatRequest())
        active_servers[id] = True
        global leader
        leader = response.leader
    except:
        print(f"Server currently down: {id}.")
        active_servers[id] = False
  
def kill_server():
    """
    Kill the server.
    """
    event.clear()
    server.stop(0)
    try:
        for thread in threads:
            thread.join()
    except (OSError):
        pass
    print("Killed thread.")
    sys.exit(0)

def check_leader():
  '''
  Check if leader is currently active. If not, set a new leader.
  '''
  global leader, messages
  if leader is None or not active_servers[leader]:
      for id, alive in enumerate(active_servers):
          if alive:
              leader = id
              print(f"The new leader is {leader}")
              return
      # No leaders found
      print("Error: No active servers.")
      kill_server()

def start_heartbeat(id):
    """
    Start heartbeat of server.
    """
    channel = grpc.insecure_channel(address_list[id])
    stub = pb2_grpc.ChatStub(channel)
    send_heartbeat(stub, id)
    while None in active_servers:
        continue
    sleep_time = random.randint(1, 5)
    while event.is_set():
        time.sleep(sleep_time)
        send_heartbeat(stub, id)
        check_leader()

def start_server():
    """
    Start the server.
    """
    # Start heartbeat of other servers.
    for i in range(3):
        if i != server_id:
            heartbeat_thread = threading.Thread(
                target=start_heartbeat, args=(i,)
            )
            heartbeat_thread.start()
            threads.append(heartbeat_thread)

    global server
    server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers=12))
    pb2_grpc.add_ChatServicer_to_server(ChatServicer(), server)

    global messages
    # messages = {}

    # Create csv file and append data.
    open(f"{server_id}.csv", "a+")
    with open(f"{server_id}.csv", "r+") as csv_file:
        csv_reader = csv.reader(csv_file, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
        for row in csv_reader:
            # print(row[0], row[1])
            if row[0] in user_list:
              messages[row[0]].append(row[1])
            else:
               user_list.append(row[0])
               messages[row[0]] = [row[1]]
        update_data()

    # Start server.
    server_address = f"{HOST}:{PORT + server_id}"
    server.add_insecure_port(server_address)
    print(f"Starting server {server_id} at address {server_address}")
    server.start()
    server.wait_for_termination()

def main():
  """
  Create three servers.
  """
  global server_id
  # Get flag for system id
  p = optparse.OptionParser()
  p.add_option('--server_id', '-s', default="0")
  options, _ = p.parse_args()
  server_id = int(options.server_id)
  
  if server_id not in [0, 1, 2]:
      assert "Error: Must input a valid server id in [0, 1, 2]."
      return
  
  active_servers[server_id] = True
  event.set()
  try:
      start_server()
  except KeyboardInterrupt:
      kill_server()

if __name__ == "__main__":
  main()