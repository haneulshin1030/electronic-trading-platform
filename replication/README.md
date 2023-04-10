# Chat App
CS 262: Distributed Computing

Single-server, multi-client chat app in the shell, built with replication and 2-fault tolerance.

## Wire Protocol
1. **Account creation.** `create <username>` creates a new account under `<username>` if it is unused and returns a success statement.
2. **Login.** `login <username>` logs into `<username>` if the account exists and returns a success statement.
3. **List Accounts.** (or a subset of the accounts, by text wildcard): returns all accounts that match a regex expression, e.g.
    - `list ^.[a]`  (regex handling) returns all usernames that have the letter a at the 2nd digit
    - `list`  (blank case) → returns all accounts
4. **Send message.** `send <recipient> <message>` sends the message and returns a status that indicates whether the message was sent or queued. 
5. **Account deletion.** `delete <username>` deletes `<username>`, and if (in the original version) `<username>` is not logged in, or if it is the current user, and a status statement is returned. Any queued messages to be delivered to `<username>` are deleted.

## Engineering Notebook
More details about the design decisions we made can be found in [notebook.md](notebook.md).

## gRPC Chat App

### Deployment Instructions

Install all necessary libraries using this command:
```pip3 install -r requirements.txt```

To compile the .proto file and generate the stubs, execute this command:
```python3 -m grpc_tools.protoc --proto_path=. ./chatapp.proto --python_out=. --grpc_python_out=. ```

To run each server, execute `python3 server.py --server i` for `i` in `[0, 1, 2]`.

To run the client, execute `python3 client.py`.
