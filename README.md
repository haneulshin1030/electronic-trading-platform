# Distributed Electronic Stock Exchange

Developed by [@haneulshin1030](https://github.com/haneulshin1030) and [@catyeo18](https://github.com/catyeo18).

More details in our final paper: TO BE UPLOADED AS PDF

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
- `evaluation.py` and `market-maker-eval.py`: scripts for evaluation experiments we ran (discussed more in section 4.1.2 of our paper)
