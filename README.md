# Distributed Electronic Stock Exchange

More details in our final paper: TO BE UPLOADED AS PDF

## Deployment Instructions

Install all necessary packages using this command:
```pip3 install -r requirements.txt```

To compile the .proto file and generate the stubs, execute this command:
```python3 -m grpc_tools.protoc --proto_path=. ./chatapp.proto --python_out=. --grpc_python_out=. ```

To run each server, execute `python3 server.py --server i` for `i` in `[0, 1, 2]`.

To run the manual client UI, execute `python3 client.py`.

To run the automated bot market maker client, execute `python3 market-maker.py`.

## Testing

To run the unit tests, execute `python3 testing.py`.
