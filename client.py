import socket 
HOST = '127.0.0.1' 
PORT = 6000

def client_soc():
	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
	clientsocket.connect((HOST, PORT))

	username = input("Your username: ");
	sent = clientsocket.send(username.encode('ascii'));
	print('Message sent, %d/%d bytes transmitted' % (sent, len(username))) 

	# msg = 'Hello, World!'
	# bmsg = msg.encode('ascii')
	# sent = clientsocket.send(bmsg)
	# print('Message sent, %d/%d bytes transmitted' % (sent, len(msg))) 

	clientsocket.close()

client_soc()