import socket 
import protocol
HOST = '127.0.0.1' 
PORT = 6000

def client_soc():
	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
	clientsocket.connect((HOST, PORT))

	client_protocol = Protocol(280, "", "", "")
	client_protocol.login_user()

	# TODO: send unsent messages to current user?

	client_protocol.send_message()

	clientsocket.close()

client_soc()
