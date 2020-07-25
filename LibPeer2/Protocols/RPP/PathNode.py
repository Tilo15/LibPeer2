from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Networks.PeerInfo import PeerInfo

from typing import List
from io import BytesIO

import struct

FLAGS_NONE = 0
FLAGS_BRIDGE = 1

class PathNode:

    def __init__(self, instance: InstanceReference, flags: int, info: PeerInfo):
        self.instance = instance
        self.flags = flags
        self.peer_info = info


    def has_flag(self, flag: int):
        return (self.flags & flag) == flag


    def serialise(self):
        # Create buffer
        buffer = BytesIO()

        # Write the instance
        buffer.write(self.instance.serialise().read())

        # Write flags
        buffer.write(struct.pack("!B", self.flags))

        # Write peer info
        buffer.write(self.peer_info.serialise())

        # Return
        buffer.seek(0, 0)
        return buffer

    @staticmethod
    def deserialise(stream):
        # Read instance
        instance = InstanceReference.deserialise(stream)

        # Read flags
        flags = struct.unpack("!B", stream.read(1))[0]

        # Read peer info
        info = PeerInfo.deserialise(stream)

        # Return query
        return PathNode(instance, flags, info)