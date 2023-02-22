import unittest

from server import list_accounts, login, send_message


test_accounts = {
  "user1": 594,
  "user2": 109,
  "user3": 837
}

test_messages = {
  "user1": {
    "user2": ["\nFrom user2: message2to1a", "\nFrom user2: message2to1b", "\nFrom user2: message2to1c"],
    "user3": ["\nFrom user3: message3to1a", "\nFrom user3: message3to1b"]
  },
  "user2": {
    "user1": [],
    "user3": []
  },
  "user3": {
    "user1": ["\nFrom user1: message1to3a"],
    "user2": []
  }
}

"""Unit tests cover each method on our server side"""
class UnitTests(unittest.TestCase):
  
  def test_list_accounts_empty(self):
    # Empty case = list all accounts
    self.assertEqual(list_accounts("", test_accounts), ["user1", "user2", "user3"])
    
  def test_list_accounts_regex(self):
    # Regex cases to get subset of accounts
    self.assertEqual(list_accounts("^use", test_accounts), ["user1", "user2", "user3"])
    self.assertEqual(list_accounts("^user[13]$", test_accounts), ["user1", "user3"])
    self.assertEqual(list_accounts(".*1.*", test_accounts), ["user1"])
    self.assertEqual(list_accounts(".*[4567890].*", test_accounts), [])

  def test_login(self):
    self.assertEqual(login("", "user1", test_accounts), "Account user1 logged in.")
    self.assertEqual(login("", "user2", test_accounts), "Account user2 logged in.")
    self.assertEqual(login("", "user3", test_accounts), "Account user3 logged in.")
  
  def test_send_message1(self):
    send_message("user1", "user2", "message1to2a", {}, test_messages)
    self.assertEqual(test_messages["user2"]["user1"], ["\nFrom user1: message1to2a"])
    
  def test_send_message2(self):
    send_message("user1", "user3", "message1to3b", {}, test_messages)
    self.assertEqual(test_messages["user3"]["user1"], ["\nFrom user1: message1to3a", "\nFrom user1: message1to3b"])

if __name__ == '__main__':
  print("Unit tests running!")
  unittest.main()
