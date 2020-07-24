from LibPeer2.Protocols.RPP.PathNode import PathNode

from typing import List
from io import BytesIO

import struct

class PathResponse:

    def __init__(self, nodes: List[PathNode]):
        self.nodes = nodes

    def serialise(self):
        # Create buffer
        buffer = BytesIO()

        # Write number of nodes
        buffer.write(struct.pack("!B", len(self.nodes)))

        # Write nodes
        for node in self.nodes:
            buffer.write(node.serialise().read())

        # Return
        buffer.seek(0, 0)
        return buffer

    @staticmethod
    def deserialise(stream):
        # Read number of nodes
        count = struct.unpack("!B", stream.read(1))[0]

        # Return path response
        return PathResponse([PathNode.deserialise(stream) for x in range(count)])