import grpc
import chatapp_pb2 as pb2
import chatapp_pb2_grpc as pb2_grpc

class Server(pb2_grpc.ChatAppServicer):
  def __init__(self):
    # accounts: {name: id}
    self.accounts = {}

    # messages = {
    #   receiveuser: {senduser: [message1, ...], senduser: [message1]}
    # }
    self.messages = {}

    # logged_in: {username: boolLoggedIn}
    self.logged_in = {}

    # clients: {username: client}
    self.clients = {}

  def receive_message(self, request, context):
    # receive data from incoming request
    sender_name = request.sender_name
    receiver_name = request.receiver_name
    message = request.message

    received = {
      'message': message,
      'sender_name': sender_name,
      'receiver_name': receiver_name
    }
    return pb2.Message(**received)

  def send_message(self, request: pb2.Message, context):
    sender_name = request.sender_name
    receiver_name = request.receiver_name
    message = request.message

    if sender_name in self.messages[receiver_name]:
      self.messages[receiver_name][sender_name].append(message)
    else:
      self.messages[receiver_name][sender_name] = [message]

    return pb2.Empty()