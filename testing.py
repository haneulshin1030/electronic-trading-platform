import unittest
from unittest.mock import MagicMock, Mock, patch
import pathlib

import server
from server import create_account, valid_password
import client


class UnitTests(unittest.TestCase):

  # Tests account creation
  def test_create_account(self):
    server.server_id = 0
    create_account("user1", "P@33word")
    self.assertEqual(server.messages["user1"], [])
    self.assertEqual(server.passwords["user1"], "P@33word")
    self.assertEqual(server.user_status["user1"], True)

  # Tests password validity
  def test_valid_password(self):
    self.assertEqual(valid_password("P@33word"), True)

    # Fails length
    self.assertEqual(valid_password("1234567"), False)
    # Fails uppercase
    self.assertEqual(valid_password("p@ssw0rd"), False)
    # Fails lowercase
    self.assertEqual(valid_password("P@SSW0RD"), False)
    # Fails number
    self.assertEqual(valid_password("p@ssWORD"), False)
    # Fails special character
    self.assertEqual(valid_password("passw0RD"), False)
    
  # # Tests start_heartbeat and send_heartbeat processes
  # @patch('server.start_heartbeat')
  # def test_start_heartbeat(self, mock_start_heartbeat):
  #   server.start_heartbeat(0)
  #   mock_start_heartbeat.assert_called()
  
  # # Tests start_server process, check log files are created
  # @patch('server.start_server')
  # def test_start_server(self, mock_start_server):
  #   server.start_server()
  #   mock_start_server.assert_called()

  #   path = pathlib.Path('0.csv')
  #   self.assertTrue(path.is_file())
  #   path = pathlib.Path('1.csv')
  #   self.assertTrue(path.is_file())
  #   path = pathlib.Path('2.csv')
  #   self.assertTrue(path.is_file())

  # # Tests leader election process
  # @patch('client.find_leader')
  # def test_find_leader(self, mock_find_leader):
  #   client.find_leader()
  #   mock_find_leader.assert_called()

if __name__ == '__main__':
  print("Unit tests running!")
  unittest.main()