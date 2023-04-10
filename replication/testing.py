import unittest
from unittest.mock import MagicMock, Mock, patch
import time
import socket
import threading
from _thread import *

from server import list_accounts, login
import server, client


# Overwrite mock methods from unittest.mock
class MockSocket:

class MockThread:
  def __init__(self, socket):
    self.socket = socket
    # self.host = host
    # self.port = port
  
  def send(self, message):
    self.socket = message
    print("Sending message:", message)

  def receive(self, message):
    self.socket = None

  def start():
    pass

  def join():
    pass

class UnitTests(unittest.TestCase):

  def test_leader_server(self):
    