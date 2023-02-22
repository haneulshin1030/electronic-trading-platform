# Engineering Notebook

## Part 1: Original Wire Protocol

The wire protocol allows clients to interact with the chat application by using keywords in their messages to specify their desired behavior. Specifically, the protocol consists of five keywords for actions and their corresonding behavior, the subsequent list of strings that specifies the corresponding parameters, including action, sender username, recipient username, message content, and regex expression, and the maximum possible size of the message (in our case, 280).

### The Server

#### The Connection Scheme

To communicate between the server and the clients, we create a central server socket such that for each client, it opens and listens to the client's socket and creates a new thread corresponding to it. 

The server then processes user requests by continuously listening for requests, so that when they are received, the server parses them and executes the appropriate output, and then sends a response to the client that sent the request. Specifically, the server relies on the first word of the request (the opcode) to identify the type of command, and executes separate logic for each command.

#### The Data

Some of the aforementioned commands rely on data from previous interactions between the clients and the server. We store the data corresponding to users on the server side of our chat application. Specifically, we use global records that map each username to a boolean value that kept track of whether they are logged in, a (nested) record that stores any queued messages that need to be delivered to the user, and the client socket and thread corresponding to the user in the present moment. This way, the data persists as long as the server is still running, even when a user logs out or a client shuts down.

Thus, for the commands that rely this data, we access it directly through the global variables and also modify them as needed.

We played around with what we needed to store. Originally, we created unique integer IDs for each account. However, handling both a unique username and a unique integer ID seemed repetitive in nature and made tasks unnecessarily complex, so we stuck to only using usernames as what essentially served as the primary key.

### The Client

#### The Connection Scheme

The client connects to the central server socket. To send requests to the server while also continuously listening to it, we send requests from the main thread while leaving running a second thread for receiving messages from the server. The main thread sends requests to the server whenever the user inputs one into the terminal using our wire protocol. The listening thread waits until it receives a message from the server, and each time it does, it prints the output to the client. 

#### Race Conditions

To account for race conditions, we used the `Event` class from `threading` to artificially lock and unlock in the client. For instance, we prevent the collision in which the client begins to type a new request at the same time that the server is still in the process of sending its response to the previous request. To do so, we set our `thread_running_event` variable so that we wait to begin a new request until the previous one is finished printing.

## Part 2: gRPC Implementation

We then implemented a similar chat application using gRPC. 

### Protocol Buffer
We went through many iterations of how we designed our protocol buffer and the `ChatApp` interface itself in `grpc/chatapp.proto`. Originally, we had created a separate rpc for each step of the wire protocol (e.g. send message, delete account). However, we found that unnecessarily complex and simplified our interface to only require two rpcs: sending a request to server and listening for responses. 

### The Server

The server for the gRPC implementation closely resembles our logic for that of the original. The data storage and interactions between the server and the client are nearly the same as well.

### The Client

One notable difference in the gRPC version is that all interactions between clients are processed by first queuing any messages in the global records. A separate gRPC then manages the delivery of these messages. Specifically, the client  listens for queued messages every 0.05 seconds. This simple design allows us to experience listening virtually continuously. For our purposes, every 0.05 seconds was certainly often enough, and we did not observe any differences in complexity or performance.

### Comparison

As mentioned, there were no noticeable differences in complexity or performance between the two versions. We also maintained the same limit on the buffer size between versions. However, it is worth noting that for the gRPC version, since we are not preserving the user's connection across distinct calls, we are then forced to include the sender's username in each request, which adds a restriction on the buffer size. However, this difference seems negligible for our purposes.

## Other Design Choices

### Killing the Client Cleanly

Since it is possible for the client to enter an incorrect command, a KeyError, or otherwise somehow cause unexpected behavior on their end, we implemented a `kill_client()` function to identify when this behavior occurs, close their socket, and indicate that they are now logged out. We implemented similar logic for the server.

### User Friendliness

We also designed the chat application to be user friendly in its usage: the user can interact with it in a similar way that they would with a standard terminal. For instance, they can repeatedly press Enter to create new prompts, and if they enter an invalid prompt, they are told so.

We also flush the standard output before outputting server responses so that the command prompt remains clean.

## Edge Cases and Testing

Since our method logic for the regular chat app and gRPC chat app are identical, the unit tests are primarily tested on the original chat app in `regular/unit_test.py`. We address the following cases to test the logic of our methods, which cover individual stages of our wire protocol:

- Listing accounts with an empty parameter returns a list of all users.
- Listing accounts with a regex parameter returns a matching subset of the user list.
- Logging in a user returns a successful login statement.
- Sending a message adds and stores the right formatted message in the global `messages` dictionary.
- Throw an error if a client tries to create a username that already exists.
- Throw an error if a client tries to log in to an account that doesn't exist.
- Throw an error if a client tries to send a message to a username that doesn't exist.

Below we've listed some edge case tests we have tested manually but hope to add as unit tests in the future:

- If a different user logs in, log out the previous one.
- Throw an error if the client attempts to delete a user who is logged in (who is not themself).
- If a user deletes themself, log them out (in the regular/original version).
- If a client is not logged in, throw an error if they attempt to send a message.
