# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: chatapp.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\rchatapp.proto\"u\n\x05Order\x12\x0e\n\x06opcode\x18\x01 \x01(\t\x12\x10\n\x08username\x18\x02 \x01(\t\x12\x10\n\x08password\x18\x03 \x01(\t\x12\x0e\n\x06symbol\x18\x04 \x01(\t\x12\x0b\n\x03\x64ir\x18\x05 \x01(\t\x12\r\n\x05price\x18\x06 \x01(\x02\x12\x0c\n\x04size\x18\x07 \x01(\x05\"i\n\nServerData\x12\x13\n\x0bopen_orders\x18\x01 \x01(\t\x12\x12\n\norder_book\x18\x02 \x01(\t\x12\r\n\x05users\x18\x03 \x01(\t\x12\x11\n\tpositions\x18\x04 \x01(\t\x12\x10\n\x08messages\x18\x05 \x01(\t\"\x0e\n\x0cUserResponse\"\x12\n\x10HeartbeatRequest\"#\n\x11HeartbeatResponse\x12\x0e\n\x06leader\x18\x01 \x01(\x05\"\x1c\n\x08Response\x12\x10\n\x08response\x18\x01 \x01(\t\"\x1c\n\x08Username\x12\x10\n\x08username\x18\x01 \x01(\t\"\x0f\n\rLeaderRequest\" \n\x0eLeaderResponse\x12\x0e\n\x06leader\x18\x01 \x01(\x05\x32\xe2\x01\n\x04\x43hat\x12$\n\x04Send\x12\x0b.ServerData\x1a\r.UserResponse\"\x00\x12\x34\n\tHeartbeat\x12\x11.HeartbeatRequest\x1a\x12.HeartbeatResponse\"\x00\x12%\n\x0eServerResponse\x12\x06.Order\x1a\t.Response\"\x00\x12*\n\x0e\x43lientMessages\x12\t.Username\x1a\t.Response\"\x00\x30\x01\x12+\n\x06Leader\x12\x0e.LeaderRequest\x1a\x0f.LeaderResponse\"\x00\x62\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'chatapp_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _ORDER._serialized_start=17
  _ORDER._serialized_end=134
  _SERVERDATA._serialized_start=136
  _SERVERDATA._serialized_end=241
  _USERRESPONSE._serialized_start=243
  _USERRESPONSE._serialized_end=257
  _HEARTBEATREQUEST._serialized_start=259
  _HEARTBEATREQUEST._serialized_end=277
  _HEARTBEATRESPONSE._serialized_start=279
  _HEARTBEATRESPONSE._serialized_end=314
  _RESPONSE._serialized_start=316
  _RESPONSE._serialized_end=344
  _USERNAME._serialized_start=346
  _USERNAME._serialized_end=374
  _LEADERREQUEST._serialized_start=376
  _LEADERREQUEST._serialized_end=391
  _LEADERRESPONSE._serialized_start=393
  _LEADERRESPONSE._serialized_end=425
  _CHAT._serialized_start=428
  _CHAT._serialized_end=654
# @@protoc_insertion_point(module_scope)
