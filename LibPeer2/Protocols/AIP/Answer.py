from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from typing import List

import struct

class Answer:

    def __init__(self, data, path: List[InstanceReference], in_reply_to):
        self.in_reply_to = in_reply_to
        self.data = data
        self.path = path


    def serialise(self, stream):
        # Write the in_reply_to field
        stream.write(self.in_reply_to)

        # Create the header
        header = struct.pack("!LB", len(self.data), len(self.path))
        stream.write(header)

        # Serialise the return path
        for reference in self.path:
            stream.write(reference.serialise().read())

        # Write the answer data
        stream.write(self.data)

    
    @staticmethod
    def deserialise(stream):
        # What is this in reply to?
        in_reply_to = stream.read(16)

        # Get the header
        header = stream.read(5)

        # Unpack
        data_len, path_size = struct.unpack("!LB", header)

        # Initialise the path array
        path = []

        # Deserialise the return path
        for i in range(path_size):
            path.append(InstanceReference.deserialise(stream))

        # Read the query data
        data = stream.read(data_len)

        # Return the object
        return Answer(data, path, in_reply_to)
