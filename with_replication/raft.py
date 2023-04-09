import os
import random
import socket
import sys
import time

from log_manager import LogManager

# Implementation of the Raft replication protocol
class RaftProtocol:
  def __init__(self, ip, port, server_name, voting=True):
    self.ip = ip
    self.port = port
    self.server_name = server_name

    # Initialize Raft-specific state variables
    self.current_term = 0 # TODO: or set to 1? need to define
    self.voted_for = -1
    self.leader_id = -1
    self.voting = voting
    self.votes = set()

    # Everything to do with the commit log file
    self.log_manager = LogManager(ip, port, server_name) # TODO: write a log manager class that writes to logs and persists
    self.commit_index = 0

    # Election timeout
    # self.election_timeout_duration = random.randint(1000, 5000)
    self.election_timeout = -1

  # Reset when previous timeout expires, start new election
  def election_timeout(self, timeout=-1):
    if timeout > 0:
      self.election_timeout = timeout
    else:
      self.election_timeout = time.time() + random.randint(1000, 6000)/1000

  # Conduct election
  def start_election(self):

  # Request votes
  def request_vote(self):

  # AND MANY MORE ELECTION PROCESSES