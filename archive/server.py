import socket 
HOST = '127.0.0.1' 
PORT = 6000

# key: username, value: dictionary of {recipient: messages}
# accounts = {
# 	"cat": {"haneul": [message1], "mohib": [message1, message2]}
# }
accounts = {}



def create_user(username):
	if username in accounts:
		print("Username already exists.")
		return

	accounts[username] = {}

def server():
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
	serversocket.bind((HOST, PORT))

	serversocket.listen()
	clientsocket, addr = serversocket.accept()
	print('Connected to by:', addr)

	# Receive username
	username = clientsocket.recv(128)
	username = username.decode('ascii')
	print("Received username is", username)
	create_user(username)

	# Receive recipient name
	recipient = clientsocket.recv(128)
	recipient = recipient.decode('ascii')
	print("Received recipient is", recipient)
	# TODO: check recipient name is valid, error otherwise
	
	# TODO: check if recipient is active and set up queue properly

	# Receive message
	msg = clientsocket.recv(128)
	msg = msg.decode('ascii')
	print("Received msg is", msg)
	if recipient in accounts[username]:
		accounts[username][recipient].append(msg)
	else:
		accounts[username][recipient] = [msg]


server()