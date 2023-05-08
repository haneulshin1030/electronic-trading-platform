import unittest
from unittest.mock import MagicMock, Mock, patch
import pathlib
from sortedcontainers import SortedDict

import server
from server import create_account, valid_password, login, post_order, handle_server_response
import client


user1_pw = "P@33word"
user2_pw = "pa$$w0rD"
user3_pw = "p_SSw2rd"

class UnitTests(unittest.TestCase):
  
  # Tests account creation
  def test_create_account(self):
    server.server_id = 0

    create_account("user1", user1_pw)
    self.assertEqual(server.messages["user1"], [])
    self.assertEqual(server.passwords["user1"], user1_pw)
    self.assertEqual(server.user_status["user1"], True)
    create_account("user2", user2_pw)
    self.assertEqual(server.messages["user2"], [])
    self.assertEqual(server.passwords["user2"], user2_pw)
    self.assertEqual(server.user_status["user2"], True)

  # Tests login
  def test_login(self):
    self.assertEqual(login("user1", user1_pw), "Success: Account user1 logged in.")
    self.assertEqual(login("user1", "password"), "Failure: Username and/or password is not valid.")
    self.assertEqual(login("user2", user1_pw), "Failure: Username and/or password is not valid.")

  # Tests password validity
  def test_valid_password(self):
    self.assertEqual(valid_password(user1_pw), True)

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

  def test_post_order(self):
    # Reset
    server.order_book = {symbol: {"buy": SortedDict(), "sell": SortedDict()} for symbol in server.symbol_list}
    server.open_orders = {symbol: {"buy": SortedDict(), "sell": SortedDict()} for symbol in server.symbol_list}

    init_positions = server.positions
    post_order("user1", "buy", "AAPL", -1, 170, 100)
    post_order("user1", "buy", "AAPL", -1, 171, 150)

    # Check that open_orders and order_book are updated correctly
    self.assertEqual(server.order_book['AAPL']['buy'], SortedDict({170: 100, 171: 150}))
    self.assertEqual(server.order_book['AAPL']['sell'], SortedDict())

    post_order("user1", "sell", "AAPL", -1, 171, 300)
    post_order("user2", "sell", "TSLA", -1, 160, 200)
    post_order("user2", "sell", "AAPL", -1, 161, 130)

    # Check that open_orders and order_book are updated correctly
    self.assertEqual(server.order_book['AAPL']['buy'], SortedDict({170: 100, 171: 150}))
    self.assertEqual(server.order_book['AAPL']['sell'], SortedDict({161: 130, 171: 300}))
    self.assertEqual(server.open_orders['AAPL']['buy'], SortedDict({170: [['user1', 100]], 171: [['user1', 150]]}))
    self.assertEqual(server.open_orders['TSLA']['sell'], SortedDict({160: [['user2', 200]]}))

    # Check that positions are NOT updated
    self.assertEqual(init_positions, server.positions)

  def test_match_trade(self):
    """
    These unit tests will test for a number of different trades scenarios and edge cases including price-time priority, regNMS order protection, and other financial metrics.
    """
    # Reset params
    server.leader_id = 0
    server.order_book = {symbol: {"buy": SortedDict(), "sell": SortedDict()} for symbol in server.symbol_list}
    server.open_orders = {symbol: {"buy": SortedDict(), "sell": SortedDict()} for symbol in server.symbol_list}
    
    # User A: BUY, AAPL, $170, 100 shares -> no trade
    handle_server_response('buy', 'user1', user1_pw, 'buy', 'AAPL', 170, 100)
    self.assertEqual(server.order_book['AAPL']['buy'], SortedDict({170: 100}))

    # User B: SELL, AAPL, $175, 50 shares -> no trade
    handle_server_response('sell', 'user2', user2_pw, 'sell', 'AAPL', 175, 50)
    self.assertEqual(server.order_book['AAPL']['sell'], SortedDict({175: 50}))

    # User A: BUY, AAPL, $176, 120 -> TRADE happens
    handle_server_response('buy', 'user1', user1_pw, 'buy', 'AAPL', 176, 120)
    self.assertEqual(server.order_book['AAPL']['buy'], SortedDict({170: 100, 176: 70}))

    # User B: BUY, TSLA, $160, 100 -> no trade
    handle_server_response('buy', 'user1', user1_pw, 'buy', 'TSLA', 160, 100)
    self.assertEqual(server.order_book['TSLA']['buy'], SortedDict({160: 100}))

    # User B: SELL, AAPL, $168, 200 -> TRADE happens
    # tests PRICE-time priority
    handle_server_response('sell', 'user2', user2_pw, 'sell', 'AAPL', 168, 200)
    self.assertEqual(server.order_book['AAPL']['sell'], SortedDict({168: 30}))
    
    # User C: SELL, AAPL, $168, 142 -> no trade
    create_account("user3", user3_pw)
    handle_server_response('sell', 'user3', user3_pw, 'sell', 'AAPL', 168, 142)
    self.assertEqual(server.order_book['AAPL']['sell'], SortedDict({168: 172}))

    # User A: BUY, AAPL, $170, 200 -> TRADE happens
    # tests price-TIME priority
    handle_server_response('buy', 'user1', user1_pw, 'buy', 'AAPL', 170, 200)
    self.assertEqual(server.order_book['AAPL']['buy'], SortedDict({170: 28}))

    # User B: BUY, AAPL, $171, 84 -> no trade
    handle_server_response('buy', 'user2', user2_pw, 'buy', 'AAPL', 171, 84)
    self.assertEqual(server.order_book['AAPL']['buy'], SortedDict({170: 28, 171: 84}))

    # User C: SELL, AAPL, $169, 300 -> TRADE happens
    # tests RegNMS and average pricing
    handle_server_response('sell', 'user3', user3_pw, 'sell', 'AAPL', 169, 300)
    self.assertEqual(server.order_book['AAPL']['sell'], SortedDict({169: 188}))

  # Tests start_heartbeat and send_heartbeat processes
  @patch('server.start_heartbeat')
  def test_start_heartbeat(self, mock_start_heartbeat):
    server.start_heartbeat(0)
    mock_start_heartbeat.assert_called()
  
  # Tests start_server process, check pickle file logic
  @patch('server.start_server')
  def test_start_server(self, mock_start_server):
    server.start_server()
    mock_start_server.assert_called()

  # Tests leader election process
  @patch('client.find_leader')
  def test_find_leader(self, mock_find_leader):
    client.find_leader()
    mock_find_leader.assert_called()

if __name__ == '__main__':
  print("Unit tests running!")
  unittest.main()