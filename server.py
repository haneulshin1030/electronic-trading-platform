import socket 
HOST = '127.0.0.1' 
PORT = 6000

# key: username, value: messages
accounts = {}

def create_user(username):
	if username in accounts:
		print("Username already exists.")
		return

	accounts[username] = []

def server():
	serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
	serversocket.bind((HOST, PORT))

	serversocket.listen()
	clientsocket, addr = serversocket.accept()
	print('Connected to by:', addr)
	data = clientsocket.recv(128)
	data = data.decode('ascii')

server()