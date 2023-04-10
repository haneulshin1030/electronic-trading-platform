# Engineering Notebook

## Rewriting our gRPC Wire Protocol

Our original gRPC wire protocol allowed clients to interact with a chat application by using keywords in their messages to specify the command they wished to run. The protocol consisted of five keywords for actions and their corresponding behavior, the subsequent list of strings that specifies the corresponding parameters, including action, sender username, recipient username, message content, and regex expression.

To extend our existing wire protocol to account for replication, we chose to build off of a modified version of our gRPC protocol. Previously, we stored messages sent between pairs of clients in a database, and we queried this database at short time intervals (e.g. every second) to deliver the messages in a timely fashion. However, this solution is not a valid approach for replication. Indeed, in the scenario where a server crashes before the query occurs, the messages may be lost to the clients. 

Thus, we rewrote the gRPC wire protocol to instead make use of a streaming RPC, so that the messages sent from one client are directly sent to the recipient. This approach ensures that messages stored in a database are not lost. At the same time, we still store pending messages in a database corresponding to each of our servers so that even if they go down, the information on the pending messages will not be lost.

## The Server

We used three replications, which ensures 2-fault tolerance in the case that any two of them go down. To simulate a process for leader election, we had each of the servers send a hearbeat to the others, so that each server can detect whether the other two are currently active. If the leader is not heartbeating, then one the other of the two leaders with the least server id is set as the new leader. Once the new leader is chosen, if any client tries to send a new request to the server, it will be notified of the server disconnection and will be connected to the new leader. The client will also receive a prompt to repeat its most recent message that was directed to the old leader. 

To ensure message persistence, we maintain two records (`messages` and `user_list`) of the pending messages as well as the list of active users. Whenever either of these records is updated, the update is then sent by the leader to the other two servers, which again preserves 2-fault tolerance. With regard to persistence, this information is also saved on a separate CSV file for each server.

## The Client

When the client attempts to connect, they query for the leader and are directed to that server. If, at any point, the leader goes down, then the next time the client sends a request, they are informed that the server was disconnected. They are then reconnected to the new leader server and prompted to resubmit their request. 

## Testing

To test 2-fault tolerance, we ran several tests where we started all three replicas initially, created at least two clients, and sent messages between them (among the other user commands). We then shut off subsets of the replicas, chosen at random, and showed that the clients could continue interacting with a remaining server.

To test persistence, we started all three replicas, sent some messages that were not yet received by the recipient, and then shut down all the servers. We then restarted the servers and showed that the recipient still received their pending messages upon logging in.
