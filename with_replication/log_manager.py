import os
import sys
import threading


class LogManager:
  def __init__(self, ip, port, server_name):
    self.ip = ip
    self.port = port
    self.server_name = server_name
    self.log = []

    self.current_term = 0

    # The data we are managing
    self.logged_in = {}
    self.messages = {}
    self.client_sockets = {}
    self.client_threads = {}
  
  def write_to_logs(self):
    # TODO: ADD LOGIC OF WHAT DATA TO WRITE
    data = ""
    
    log_filepath = "logs/" + self.server_name + ".txt"
    file = open(log_filepath, "a+")
    file.write(data + "\n")
    file.close()

    return data

  def restore_from_logs(self):
    log_filepath = "logs/" + self.server_name + ".txt"

    if not os.path.exists(log_filepath):
      print("Error: log filepath does not exist")
    
    file = open(log_filepath, "r+")
    all_lines = file.read().splitlines()
    non_empty_lines = list(filter(lambda x: x != '', all_lines))
    file.close()

    # TODO: RESTORE LOGIC
      
