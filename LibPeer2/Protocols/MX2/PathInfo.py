from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from io import BytesIO
from typing import List

import struct

class PathInfo:

    def __init__(self, repeaters: List[InstanceReference]):
        self.repeaters = repeaters

    def return_path(self):
        path = list(self.repeaters)
        path.reverse()
        return PathInfo(path)

    def serialise(self):
        # Create buffer
        buffer = BytesIO()

        # Write number of repeaters
        buffer.write(struct.pack("!B", len(self.repeaters)))

        # Write the repeaters
        for repeater in self.repeaters:
            buffer.write(repeater.serialise().read())

        # Seek and return
        buffer.seek(0, 0)
        return buffer

    @staticmethod
    def deserialise(stream):
        count = struct.unpack("!B", stream.read(1))[0]
        repeaters = [InstanceReference.deserialise(stream) for i in range(count)]
        return PathInfo(repeaters)


    @staticmethod
    def empty():
        return PathInfo([])

