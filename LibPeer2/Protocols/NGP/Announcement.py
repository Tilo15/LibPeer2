from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from typing import List
from io import BytesIO

import struct

class Announcement:

    def __init__(self, instances: List[InstanceReference]):
        self.instances = instances

    def serialise(self):
        # Create buffer
        buffer = BytesIO()

        # Write number of instances
        buffer.write(struct.pack("!B", len(self.instances)))

        # Write instances
        for instance in self.instances:
            buffer.write(instance.serialise().read())

        # Return
        buffer.seek(0, 0)
        return buffer

    @staticmethod
    def deserialise(stream):
        # Read number of instances
        count = struct.unpack("!B", stream.read(1))[0]

        # Return announcement
        return Announcement([InstanceReference.deserialise(stream) for x in range(count)])