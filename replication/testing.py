import unittest
from unittest.mock import MagicMock, Mock, patch
import pathlib

import server
from server import list_accounts, create_account
import client


class UnitTests(unittest.TestCase):

  # Tests create_account, login, and update_data
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
  
  # Tests start_server process, check log files are created
  @patch('server.start_server')
  def test_start_server(self, mock_start_server):
    server.start_server()
    mock_start_server.assert_called()

    path = pathlib.Path('0.csv')
    self.assertTrue(path.is_file())
    path = pathlib.Path('1.csv')
    self.assertTrue(path.is_file())
    path = pathlib.Path('2.csv')
    self.assertTrue(path.is_file())

  # Tests leader election process
  @patch('client.find_leader')
  def test_find_leader(self, mock_find_leader):
    client.find_leader()
    mock_find_leader.assert_called()

if __name__ == '__main__':
  print("Unit tests running!")
  unittest.main()