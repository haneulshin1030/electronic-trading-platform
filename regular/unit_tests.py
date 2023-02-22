import unittest

from server import list_accounts, login, send_message, send_undelivered_messages


test_accounts = {
  "user1": 594,
  "user2": 109,
  "user3": 837
}

test_messages = {
  "user1": {
    "user2": ["message2to1a", "message2to1b", "message2to1c"],
    "user3": ["message3to1a", "message3to1b"]
  },
  "user2": {
    "user1": [],
    "user3": []
  },
  "user3": {
    "user1": ["message1to3a"],
    "user2": []
  }
}

"""Unit tests cover each method on our server side"""
class UnitTests(unittest.TestCase):
  
  # def test_create_accounts():
    # did we not used to have a method for account creation?
    # would be good to test to make sure duplicate usernames aren't allowed
  
  def test_list_accounts(self):
    # Empty case = list all accounts
    self.assertEqual(list_accounts("", test_accounts), ["user1", "user2", "user3"])
    
    # Regex cases
    self.assertEqual(list_accounts("^use", test_accounts), ["user1", "user2", "user3"])
    self.assertEqual(list_accounts("^user[13]$", test_accounts), ["user1", "user3"])
    self.assertEqual(list_accounts(".*1.*", test_accounts), ["user1"])
    self.assertEqual(list_accounts(".*[4567890].*", test_accounts), [])


if __name__ == '__main__':
  print("Unit tests running...")
  unittest.main()
  print("Unit tests completed!")