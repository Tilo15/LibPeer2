import struct



class PeerInfo:

    NETWORK_TYPE = b""

    def _serialise(self):
        raise NotImplementedError()

    @staticmethod
    def _build(stream):
        raise NotImplementedError()


    def serialise(self):
        # Get type length
        type_length = struct.pack("!B", len(self.NETWORK_TYPE))

        # Return serialised bytes
        return type_length + self.NETWORK_TYPE + self._serialise()


    @staticmethod
    def deserialise(stream):
        # Get the length of the network type string
        type_length = struct.unpack("!B", stream.read(1))[0]

        # Get network type
        ntype = stream.read(type_length)

        # Find the correct PeerInfo class to use
        peer_info = next(x for x in PeerInfo.__subclasses__() if x.NETWORK_TYPE == ntype)

        # Return the object
        return peer_info._build(stream)

    
    def __eq__(self, other):
        raise NotImplementedError()


    def __hash__(self):
        raise NotImplementedError()