# Distributed Electronic Stock Exchange

Developed by [@haneulshin1030](https://github.com/haneulshin1030) and [@catyeo18](https://github.com/catyeo18).

We present an implementation of a distributed electronic stock exchange. The exchange allows both human traders and automated market makers to create accounts and make trades with each other on the exchange server. The proposed and constructed distributed system leverages a streaming RPC and heartbeat mechanism to provide scalability, reliability, persistence, and fault tolerance. The system design takes into consideration several key functionalities, including real-time access to market and user data, fair trade matching algorithms (quantified by price-time priority and the RegNMS Order Protection Rule), and remote server-server and server-client communication to ensure an efficient and easy-to-use electronic stock exchange that can handle large-scale trading volumes. We also evaluate our system on the basis of unit tests for accuracy and market metrics, as well as general testing for speed and latency. 

More details can be found in our final paper [here](CS262_Final_Paper.pdf).

## Deployment Instructions

Install all necessary packages using this command:
```pip3 install -r requirements.txt```

Compile the .proto file and generate the stubs:
```python3 -m grpc_tools.protoc --proto_path=. ./chatapp.proto --python_out=. --grpc_python_out=. ```

To run the exchange server, execute `python3 server.py`.

<!-- To run each server, execute `python3 server.py --server i` for `i` in `[0, 1, 2]`. -->

To run the manual client, execute `python3 client.py`.

To run the automated bot market maker client, execute `python3 market-maker.py`.

## Testing

To run the unit tests, execute `python3 testing.py`.

## Project Organization
- `chatapp.proto`: objects defined by the gRPC protocol
- `server.py`: exchange server
- `client.py`: human trader client
- `market-maker.py`: market maker client that generates automated trades
- `testing.py`: unit tests
- `evaluation.py`: script for evaluation experiments (discussed more in section 4.1.2 of our paper)
