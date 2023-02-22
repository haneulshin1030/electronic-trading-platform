# Chat App
CS 262: Distributed Computing
Single-server, multi-client chat app in the shell.

## Wire Protocol
1. **Account creation.** `create <username>` creates a new account under `<username>` if it is unused and returns a success statement.
2. **Login.** `login <username>` logs into `<username>` if the account exists and returns a success statement.
3. **List Accounts.** (or a subset of the accounts, by text wildcard): returns all accounts that match a regex expression, e.g.
    - `list ^.[a]`  (regex handling) returns all usernames that have the letter a at the 2nd digit
    - `list`  (blank case) → returns all accounts
4. **Send message.** `send <recipient>` initiates a prompt for a message to send to `<recipient>`, and then sends the message and returns a status that indicates whether the message was sent or queued. 
    - For the gRPC veresion, the syntax is `send <recipient> <message>`
5. **Account deletion.** `delete <username>` deletes `<username>`, and if (in the original version) `<username>` is not logged in, or if it is the current user, and a status statement is returned. Any queued messages to be delivered to `<username>` are deleted.


## Regular Chat App

Tutorials/Resources referenced: 
- [Varun's wire protocol demo](https://github.com/vargandhi/cs262-WP)
- [GeeksForGeeks multithreading](https://www.geeksforgeeks.org/socket-programming-multi-threading-python/)

### Deployment Instructions

Install all necessary packages with
`pip3 install -r requirements.txt`.

In your terminal, enter `/regular`.

To run the server, execute `python3 server.py`.

To run the client, execute `python3 client.py`.

To run the unit tests, execute `python3 unit_tests.py`.

## gRPC Chat App

Tutorials/Resources referenced:
- [gRPC Python documentation](https://grpc.io/docs/languages/python/basics)
- [gRPC Python tutorial](https://www.velotio.com/engineering-blog/grpc-implementation-using-python)

### Deployment Instructions

Install all necessary libraries using this command:
```pip3 install -r requirements.txt```

In your terminal, enter `/grpc`.

To compile the .proto file and generate the stubs, execute this command:
```python3 -m grpc_tools.protoc --proto_path=. ./chatapp.proto --python_out=. --grpc_python_out=. ```

To run the server, execute `python3 server.py`.

To run the client, execute `python3 client.py`.