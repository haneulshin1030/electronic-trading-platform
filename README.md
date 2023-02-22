# Chat App
CS 262: Distributed Computing
Single-server, multi-client chat app in the shell.

## Wire Protocol
1. **Account creation.** `1|username` → returns accountID
2. **Login**. `2|username`
3. **List accounts** (or a subset of the accounts, by text wildcard):
  - `3|^.[a]` (regex handling) → returns all usernames that have the letter a at the 2nd digit
  - `3|`  (blank case) → returns all accounts
4. **Send message**. `4|username of receiver|message` → return Delivered/Queued status
5. **Account deletion**. `5|username` → deletes account.


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