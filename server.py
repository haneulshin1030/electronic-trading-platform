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

########## SERVER INFORMATION ##########

# Current threads that are running.
threads = []

# Event for when threads are running, i.e. not stopped.
event = threading.Event()

# Current server.
server = None

# Dictionary mapping index -> replica.
address_list = [f"{HOST}:{PORT}", f"{HOST}:{PORT + 1}", f"{HOST}:{PORT+ 2}"]

# Server id of leader.
leader = None

# Current live servers.
active_servers = [None, None, None]

########## MARKET INFORMATION ##########

# List of universe of symbols
symbol_list = ['AAPL', 'TSLA', 'USD']

# Default dictionary of positions in symbols

zero_positions = dict.fromkeys(symbol_list, 0)

dir_list = ['buy', 'sell']

# Dictionary mapping symbol -> {buy -> bid dictionary, sell -> offer dictionary}
# Where the bid and offer dictionaries map price -> [{user_1, quantity_1}, ..., {user_n, quantity_n}]
# sorted by time priority, such that if i < j, user i has time priority over user j
open_orders = dict.fromkeys(symbol_list, {'buy': {}, 'sell': {}})

# Dictionary mapping symbol -> {buy -> bid dictionary, sell -> offer dictionary}
# Where the bid and offer dictionaries map price -> total quantity
order_book = dict.fromkeys(symbol_list, {'buy': {}, 'sell': {}})

########## USER INFORMATION ##########

# Dictionary mapping user -> online status (bool)
user_status = {}

# Dictionary mapping user -> password
passwords = {}

# Dictionary mapping user, symbol -> user's position in that symbol in shares
positions = {}

# Dictionary mapping user -> [message_1, ..., message_n], where message_i is a response message from the server
messages = {}

# Error string for if the server is not the leader.
ERROR_NOT_LEADER = "Error: server is not the leader."

def save_data(open_orders, order_book, user_status, passwords, positions, messages, file_name):
    """
    Store the current dictionary of the order book, user online status, user passwords, user positions, and user messages.
    """

    # Store open orders
    with open(f"open_orders_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for symbol in symbol_list:
          for dir in dir_list:
            for price in open_orders[symbol][dir]:
              for user, size in open_orders[symbol][dir][price]:
                csv_writer.writerow([symbol] + [dir] + [price] + [user] + [size])
              
    # Store order book
    with open(f"order_book_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for symbol in symbol_list:
          for dir in dir_list:
            for price, size in list(order_book[symbol][dir].items()):
              csv_writer.writerow([symbol] + [dir] + [price] + [size])
                
    # Store user status
    with open(f"user_status_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for user, online in list(user_status.items()):
          csv_writer.writerow([user] + [online])

    # Store user status
    with open(f"passwords_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for user, password in list(passwords.items()):
          csv_writer.writerow([user] + [password])

    # Store positions
    with open(f"positions_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for user in positions.keys():
          for symbol, position in list(positions[user].items()):
            csv_writer.writerow([user] + [symbol] + [position])

    # Store message queue
    with open(f"messages_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for user, message_list in list(messages.items()):
          for message in message_list:
            csv_writer.writerow([user] + [message])

def update_order_book(symbol, dir, price, user, size):
  global order_book
  
  symbol, dir, price, user, size = row
  if price in open_orders[symbol][dir]:
    open_orders[symbol][dir][price].append({user, size})
  else:
    open_orders[symbol][dir][price] = ({user, size})
  

def update_data():
    """
    Sends the current dictionary of the order book, user online status, user passwords, user positions, and user messages to each of the servers.
    """
    global open_orders, order_book, user_status, passwords, positions, messages, server_id
    if leader != server_id:
        return
    for id, alive in enumerate(active_servers):
        if alive and id != leader and id != server_id:
            channel = grpc.insecure_channel(address_list[id])
            stub = pb2_grpc.ChatStub(channel)
            try:
                save_data(open_orders, order_book, user_status, passwords, positions, messages, file_name):
                stub.Send(pb2.ServerData(open_orders=json.dumps(open_orders), order_book=json.dumps(order_book), user_status=json.dumps(user_status), passwords=json.dumps(passwords), positions=json.dumps(positions), messages=json.dumps(messages)))
            except:
                print(f"Server failure: {id}")
                active_servers[id] = False

class ChatServicer(pb2_grpc.ChatServicer):
    def Heartbeat(self, request, context):
        return pb2.HeartbeatResponse(leader=leader)
    
    def Send(self, order, context):
        """
        Send updated data to the databases.
        """
        global open_orders, order_book, user_status, passwords, positions, messages
        open_orders = json.loads(order.open_orders)
        order_book = json.loads(order.order_book)
        user_status = json.loads(order.user_status)
        passwords = json.loads(order.passwords)
        positions = json.loads(order.positions)
        messages = json.loads(order.messages)
        
        save_data(open_orders, order_book, user_status, passwords, positions, messages, file_name):
        return pb2.UserResponse()
    
    def ServerResponse(self, order, context): 
        '''
        Manage the server's response to user input.
        '''
        return handle_server_response(order.opcode, order.user, order.password, order.dir, order.symbol, order.price, order.size)
    
    def ClientMessages(self, user, context):
        '''
        Return the client's pending messages, and update the data accordingly.
        '''
        user = user.username
        
        # Shouldn't need this
        # if user not in user_status:
        #     user_status.append(username)
        #     update_data()

        while user in messages.keys():
              for message in messages[user]:
                yield pb2.Response(response = message)
              messages[user] = []
        update_data()

    def Leader(self, request, context):
        return pb2.LeaderResponse(leader = leader)


def login(username):
  """
  Log the user in.
  """
  global user_status
  user_status[username] = True
  return "Success: Account " + username + " logged in."

def create_account(username, password):
  """
  Create new account and initialize user information.
  """

  global user_status, passwords, positions, messages

  user_status[username] = True
  passwords[username] = password
  positions[username] = zero_positions
  messages[username] = []
  return "Success: Account " + username + " created and logged in."

def valid_password(password):
  return True

def trade_message(dir, symbol, price, size):
  action = "Bought" if dir == "buy" else "Sold"
  preposition = "for" if dir == "buy" else "at"
  return f"{action} {size} shares of {symbol} {preposition} ${price}/share."

def handle_server_response(opcode, username, password, dir, symbol, price, size):
    '''
    Handle the server's response to the input.
    '''
    # If this server is not the leader, error.
    global leader, server_id
    global user_status, passwords, positions, messages
    if server_id != leader:
      return pb2.Response(response = ERROR_NOT_LEADER)

    current_user = None
    response = None

    # Create account.
    if opcode == "create": 

      # Check whether username is unique.
      if username in user_status:
        response = "Username already exists."
      elif not valid_password(password):
        response = "Invalid password."
      else:    
        # Create new user.
        response = create_account(username)
        update_data()

    # Log in.
    elif opcode == "login": 
      new_username = request_username
      
      # Check whether user exists.
      if username not in user_status or passwords[username] != password:
        response = "Username and/or password is not valid."
      else:
        response = login(username)
        update_data()

    # Post a user's order in the market and execute any matched trades
    # Think about race conditions? Lock and unlock?
    elif opcode == "order":
      
      # Opposite direction
      if dir == "buy":
        opp = "sell"
        sgn = 1
        opp_sgn = -1
      else:
        opp = "buy"
        sgn = -1
        opp_sgn = 1
      
      # Check if there are matching trades, and excute them if so
      
      trade_size = 0
      cumulative_price = 0
      
      # Lock?
      
      while True:
        # Find best existing bid or offer price
        if opp == "sell":
          best_price = min(open_orders[symbol][opp], key=open_orders[symbol][opp].get)
          if price < best_price:
            break
        else:
          best_price = min(open_orders[symbol][opp], key=open_orders[symbol][opp].get)
          if price > best_price:
            break
        
        while size - trade_size > 0 and len(open_orders[symbol][opp][best_price]) > 0:
          cur_size = min(open_orders[symbol][opp][best_price][0][1], size - trade_size)
          
          # Trade occurred
          if cur_size > 0:
            trade_size += cur_size
            cumulative_price += cur_size * best_price
            counterparty = open_orders[symbol][opp][best_price][0][0]
            
            # Update counterparty information
            positions[counterparty][symbol] += opp_sgn * cur_size
            positions[counterparty]['USD'] += sgn * cur_size * best_price
            messages[counterparty].append(trade_message(opp, symbol, best_price, cur_size))
            
            # Update open orders
            if cur_size < open_orders[symbol][opp][best_price][0][1]:
              open_orders[symbol][opp][best_price][0][1] -= cur_size
            else:
              open_orders[symbol][opp][best_price][0].pop(0)
            
            # Update order book
            if cur_size == order_book[symbol][opp][best_price]:
              order_book[symbol][opp].pop(best_price)
            else:
              order_book[symbol][opp][best_price] -= cur_size
      
      # Update user information
      average_price = cumulative_price / trade_size
      positions[counterparty][symbol] += sgn * trade_size
      positions[counterparty]['USD'] += opp_sgn * trade_size * average_price
      messages[counterparty].append(trade_message(dir, symbol, average_price, trade_size))       
      
      # Update open orders and order book
      if trade_size < size:
        if price in order_book[symbol][dir]:
          open_orders[symbol][dir][price].append({username, size - trade_size})
          order_book[symbol][dir][price] += size - trade_size
        else:
          open_orders[symbol][dir][price] = [{username, price}]
          order_book[symbol][dir][price] = size - trade_size

      update_data()
      
      # Unlock?
      
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

    global open_orders, order_book, user_status, passwords, positions, messages

    # ^ make sure these are initialized?

    # Read csv files into the server data
    
    open(f"open_orders_{server_id}.csv", "a+")
    with open(f"open_orders_{server_id}.csv", "r+") as csv_file:
      csv_reader = csv.reader(csv_file, quotechar='"', delimiter=',', quoting=csv.QUOTE_ALL, skipinitialspace=True)
      for row in csv_reader:
        symbol, dir, price, user, size = row
        if price in open_orders[symbol][dir]:
          open_orders[symbol][dir][price].append({user, size})
        else:
          open_orders[symbol][dir][price] = ({user, size})
        


    # Store open orders
    with open(f"open_orders_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for symbol in symbol_list:
          for dir in dir_list:
            for price in open_orders[symbol][dir]:
              for user, size in open_orders[symbol][dir][price]:
                csv_writer.writerow([symbol] + [dir] + [price] + [user] + [size])
              
    # Store order book
    with open(f"order_book_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for symbol in symbol_list:
          for dir in dir_list:
            for price, size in list(order_book[symbol][dir].items()):
              csv_writer.writerow([symbol] + [dir] + [price] + [size])
                
    # Store user status
    with open(f"user_status_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for user, online in list(user_status.items()):
          csv_writer.writerow([user] + [online])

    # Store user status
    with open(f"passwords_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for user, password in list(passwords.items()):
          csv_writer.writerow([user] + [password])

    # Store positions
    with open(f"positions_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for user in positions.keys():
          for symbol, position in list(positions[user].items()):
            csv_writer.writerow([user] + [symbol] + [position])

    # Store message queue
    with open(f"messages_{file_name}.csv", "w+") as f:
        csv_writer = csv.writer(f)

        for user, message_list in list(messages.items()):
          for message in message_list:
            csv_writer.writerow([user] + [message])
            
            
        for row in csv_reader:
            if row[0] == "users_list":
               user_list += row
               continue
            print(row[0], row[1])
            if row[0] in messages.keys():
              messages[row[0]].append(row[1])
            else:
               user_list.append(row[0])
               messages[row[0]] = [row[1]]
        update_data()
    open(f"{server_id}.csv", "w+")

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
