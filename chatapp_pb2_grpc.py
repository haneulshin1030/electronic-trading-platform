# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import chatapp_pb2 as chatapp__pb2


class ChatStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.ReceiveServerMarketData = channel.unary_unary(
                '/Chat/ReceiveServerMarketData',
                request_serializer=chatapp__pb2.ServerMarketData.SerializeToString,
                response_deserializer=chatapp__pb2.ServerResponse.FromString,
                )
        self.ReceiveServerClientData = channel.unary_unary(
                '/Chat/ReceiveServerClientData',
                request_serializer=chatapp__pb2.ServerClientData.SerializeToString,
                response_deserializer=chatapp__pb2.ServerResponse.FromString,
                )
        self.ReceiveClientMarketData = channel.unary_unary(
                '/Chat/ReceiveClientMarketData',
                request_serializer=chatapp__pb2.ClientMarketData.SerializeToString,
                response_deserializer=chatapp__pb2.ServerResponse.FromString,
                )
        self.Heartbeat = channel.unary_unary(
                '/Chat/Heartbeat',
                request_serializer=chatapp__pb2.HeartbeatRequest.SerializeToString,
                response_deserializer=chatapp__pb2.HeartbeatResponse.FromString,
                )
        self.RequestClientOrder = channel.unary_unary(
                '/Chat/RequestClientOrder',
                request_serializer=chatapp__pb2.ClientOrder.SerializeToString,
                response_deserializer=chatapp__pb2.Response.FromString,
                )
        self.SendClientMessages = channel.unary_stream(
                '/Chat/SendClientMessages',
                request_serializer=chatapp__pb2.Username.SerializeToString,
                response_deserializer=chatapp__pb2.Response.FromString,
                )
        self.FindLeader = channel.unary_unary(
                '/Chat/FindLeader',
                request_serializer=chatapp__pb2.LeaderRequest.SerializeToString,
                response_deserializer=chatapp__pb2.LeaderResponse.FromString,
                )


class ChatServicer(object):
    """Missing associated documentation comment in .proto file."""

    def ReceiveServerMarketData(self, request, context):
        """Send updated versions of the message queue and user list to the other servers
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ReceiveServerClientData(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ReceiveClientMarketData(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def Heartbeat(self, request, context):
        """Send heartbeat to other servers to indicate activity
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def RequestClientOrder(self, request, context):
        """Generate server response to user order
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def SendClientMessages(self, request, context):
        """Send messages between clients
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def FindLeader(self, request, context):
        """Query for the current leader server
        """
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_ChatServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'ReceiveServerMarketData': grpc.unary_unary_rpc_method_handler(
                    servicer.ReceiveServerMarketData,
                    request_deserializer=chatapp__pb2.ServerMarketData.FromString,
                    response_serializer=chatapp__pb2.ServerResponse.SerializeToString,
            ),
            'ReceiveServerClientData': grpc.unary_unary_rpc_method_handler(
                    servicer.ReceiveServerClientData,
                    request_deserializer=chatapp__pb2.ServerClientData.FromString,
                    response_serializer=chatapp__pb2.ServerResponse.SerializeToString,
            ),
            'ReceiveClientMarketData': grpc.unary_unary_rpc_method_handler(
                    servicer.ReceiveClientMarketData,
                    request_deserializer=chatapp__pb2.ClientMarketData.FromString,
                    response_serializer=chatapp__pb2.ServerResponse.SerializeToString,
            ),
            'Heartbeat': grpc.unary_unary_rpc_method_handler(
                    servicer.Heartbeat,
                    request_deserializer=chatapp__pb2.HeartbeatRequest.FromString,
                    response_serializer=chatapp__pb2.HeartbeatResponse.SerializeToString,
            ),
            'RequestClientOrder': grpc.unary_unary_rpc_method_handler(
                    servicer.RequestClientOrder,
                    request_deserializer=chatapp__pb2.ClientOrder.FromString,
                    response_serializer=chatapp__pb2.Response.SerializeToString,
            ),
            'SendClientMessages': grpc.unary_stream_rpc_method_handler(
                    servicer.SendClientMessages,
                    request_deserializer=chatapp__pb2.Username.FromString,
                    response_serializer=chatapp__pb2.Response.SerializeToString,
            ),
            'FindLeader': grpc.unary_unary_rpc_method_handler(
                    servicer.FindLeader,
                    request_deserializer=chatapp__pb2.LeaderRequest.FromString,
                    response_serializer=chatapp__pb2.LeaderResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'Chat', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class Chat(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def ReceiveServerMarketData(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Chat/ReceiveServerMarketData',
            chatapp__pb2.ServerMarketData.SerializeToString,
            chatapp__pb2.ServerResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ReceiveServerClientData(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Chat/ReceiveServerClientData',
            chatapp__pb2.ServerClientData.SerializeToString,
            chatapp__pb2.ServerResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def ReceiveClientMarketData(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Chat/ReceiveClientMarketData',
            chatapp__pb2.ClientMarketData.SerializeToString,
            chatapp__pb2.ServerResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def Heartbeat(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Chat/Heartbeat',
            chatapp__pb2.HeartbeatRequest.SerializeToString,
            chatapp__pb2.HeartbeatResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def RequestClientOrder(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Chat/RequestClientOrder',
            chatapp__pb2.ClientOrder.SerializeToString,
            chatapp__pb2.Response.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def SendClientMessages(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/Chat/SendClientMessages',
            chatapp__pb2.Username.SerializeToString,
            chatapp__pb2.Response.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def FindLeader(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/Chat/FindLeader',
            chatapp__pb2.LeaderRequest.SerializeToString,
            chatapp__pb2.LeaderResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
