from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from typing import List
from io import BytesIO

import struct

class PathQuery:

    def __init__(self, target: InstanceReference, ttl: int, blacklist: List[InstanceReference]):
        self.target = target
        self.ttl = ttl
        self.blacklist = blacklist


    def serialise(self):
        # Create buffer
        buffer = BytesIO()

        # Write the target instance
        buffer.write(self.target.serialise().read())

        # Write the TTL and number of blacklist instances
        buffer.write(struct.pack("!BB", self.ttl, len(self.blacklist)))

        # Write instances
        for instance in self.instances:
            buffer.write(instance.serialise().read())

        # Return
        buffer.seek(0, 0)
        return buffer

    @staticmethod
    def deserialise(stream):
        # Read target instance
        instance = InstanceReference.deserialise(stream)

        # Read TTL and number of instances
        ttl, blacklist_count = struct.unpack("!BB", stream.read(1))

        # Return query
        return PathQuery(target, ttl - 1, [InstanceReference.deserialise(stream) for x in range(count)])