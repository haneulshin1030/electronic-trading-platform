import os
import sys
import threading


class LogManager:
  def __init__(self, ip, port):
    self.ip = ip
    self.port = port
    self.log = []

    self.current_term = 0

    # The data we are managing
    self.logged_in = {}
    self.messages = {}
    self.client_sockets = {}
    self.client_threads = {}
  
  def write_to_logs(self):

  def restore_from_logs(self, log_filepath):