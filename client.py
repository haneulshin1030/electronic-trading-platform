import socket 
HOST = '127.0.0.1' 
PORT = 6000

def client_soc():
	clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
	clientsocket.connect((HOST, PORT))

	# Get username
	username = input("Your username: ");
	sent = clientsocket.send(username.encode('ascii'));
	print('Message sent, %d/%d bytes transmitted' % (sent, len(username))) 

	# Get recipient name
	recipient = input("Recipient username: ");
	sent = clientsocket.send(recipient.encode('ascii'));
	print('Message sent, %d/%d bytes transmitted' % (sent, len(recipient)))

	

	clientsocket.close()

client_soc()