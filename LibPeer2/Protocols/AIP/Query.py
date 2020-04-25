from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from typing import List

import struct
import uuid
import rx

class Query:

    def __init__(self, data, max_replies = 10, hops = 0, return_path: List[InstanceReference] = [], identifier = None):
        self.identifier = identifier or uuid.uuid4().bytes
        self.data = data
        self.max_replies = max_replies
        self.hops = hops
        self.return_path = return_path
        self.answer = rx.subject.Subject()


    def serialise(self, stream):
        # Write query identifier
        stream.write(self.identifier)

        # Create the header
        header = struct.pack("!BBHB", self.hops, self.max_replies, len(self.data), len(self.return_path))
        stream.write(header)

        # Serialise the return path
        for reference in self.return_path:
            stream.write(reference.serialise())

        # Write the query data
        stream.write(self.data)

    
    @staticmethod
    def deserialise(stream):
        # Read the identifier
        identifier = stream.read(16)

        # Get the header
        header = stream.read(5)

        # Unpack
        hops, max_replies, data_len, return_path_size = struct.unpack("!BBHB", header)

        # Initialise the return path array
        return_path = []

        # Deserialise the return path
        for i in range(return_path_size):
            return_path.append(InstanceReference.deserialise(stream))

        # Read the query data
        data = stream.read(data_len)

        # Return the object
        return Query(data, max_replies, hops, return_path, identifier)
