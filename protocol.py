class Protocol:
  def __init__(self, length, username, recipient, data):
    self.length = 280
    self.username = ""
    self.recipient = ""
    self.data = "" # message data?

  def login_user():
    # Get username
    self.username = input("Your username: ");
    sent = clientsocket.send(self.username.encode('ascii'));
    print('Message sent, %d/%d bytes transmitted' % (sent, len(self.username))) 

  def send_message():
    # Get recipient name
    self.recipient = input("Recipient username: ");
    sent = clientsocket.send(self.recipient.encode('ascii'));
    print('Message sent, %d/%d bytes transmitted' % (sent, len(self.recipient)))

    # Prompt message
    self.data = input("Enter your message here: ");
    sent = clientsocket.send(self.data.encode('ascii'));
    print('Message sent, %d/%d bytes transmitted' % (sent, len(self.data)))

