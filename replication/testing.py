import unittest
from unittest.mock import MagicMock, Mock, patch
import time

import server
from server import list_accounts, create_account, update_data


# Overwrite mock methods from unittest.mock
# class MockThread:
#   def __init__(self, socket):
#     self.socket = socket
#     # self.host = host
#     # self.port = port
  
#   def send(self, message):
#     self.socket = message
#     print("Sending message:", message)

#   def receive(self, message):
#     self.socket = None

#   def start():
#     pass

#   def join():
#     pass


class UnitTests(unittest.TestCase):

  # Tests: create_account, login, and update_data
  def test_create_account(self):
    server.server_id = 0
    create_account("user1")
    self.assertEqual(server.messages["user1"], [])
    create_account("user2")
    self.assertEqual(server.messages["user2"], [])
    create_account("user3")
    self.assertEqual(server.messages["user3"], [])

  # Tests list_accounts logic
  def test_list_accounts(self):
    self.assertEqual(set(list_accounts("")), set(["user1", "user2", "user3"]))
    self.assertEqual(set(list_accounts("^use")), set(["user1", "user2", "user3"]))
    self.assertEqual(set(list_accounts("^user[13]$")), set(["user1", "user3"]))
    self.assertEqual(list_accounts(".*1.*"), ["user1"])
    self.assertEqual(list_accounts(".*[4567890].*"), [])
    
  # Tests start_heartbeat and send_heartbeat processes
  @patch('server.start_heartbeat')
  def test_start_heartbeat(self, mock_start_heartbeat):
    server.start_heartbeat(0)
    mock_start_heartbeat.assert_called()

if __name__ == '__main__':
  print("Unit tests running!")
  unittest.main()