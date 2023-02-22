# Chat App
Single-server, multi-client chat app.

## Regular Chat App

Tutorials/Resources referenced: TF's wire protocol demo (ADD LINK)

### Deployment Instructions

Install all necessary libraries using this command:
```pip3 install requirements.txt```

## gRPC Chat App

Tutorials/Resources referenced:
- [gRPC Python documentation](https://grpc.io/docs/languages/python/basics)
- [gRPC Python tutorial](https://www.velotio.com/engineering-blog/grpc-implementation-using-python)

### Deployment Instructions

Enter `/grpc`.

To compile the .proto file and generate the stubs, execute this command:
```python3 -m grpc_tools.protoc --proto_path=. ./chatapp.proto --python_out=. --grpc_python_out=. ```