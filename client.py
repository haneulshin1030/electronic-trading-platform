import socket


def main():
  HOST = '127.0.0.1' 
  PORT = 6000

  clientsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
  clientsocket.connect((HOST, PORT))

  # message to send to server
  while True:
    ans = input("\nEnter your request: ")

    if ans == "":
      ans2 = input("\nDo you want to continue (y/n):")
      if ans2 == 'y':
        continue
      else:
        break
    else:
      clientsocket.send(ans.encode('ascii'))
      data = clientsocket.recv(1024)

      # print the received message
      # here it would be a reverse of sent message
      print('Received from the server: ', str(data.decode('ascii')))
      continue

  # close the connection
  clientsocket.close()


if __name__ == "__main__":
  main()