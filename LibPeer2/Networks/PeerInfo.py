import struct



class PeerInfo:

    NETWORK_TYPE = b""

    def _serialise(self):
        raise NotImplementedError()

    @staticmethod
    def _build(stream, length):
        raise NotImplementedError()


    def serialise(self):
        # Get the subclass specific data
        data = self._serialise()

        # Get type length and the data length
        type_length = struct.pack("!BB", len(self.NETWORK_TYPE), len(data))

        # Return serialised bytes
        return type_length + self.NETWORK_TYPE + data


    @staticmethod
    def deserialise(stream):
        # Get the length of the network type string and the data segment
        type_length, data_length = struct.unpack("!BB", stream.read(2))

        # Get network type
        ntype = stream.read(type_length)

        # Find the correct PeerInfo class to use
        peer_info = next((x for x in PeerInfo.__subclasses__() if x.NETWORK_TYPE == ntype), PeerInfo.__unknown_peer_info(ntype))

        # Return the object
        info = peer_info._build(stream, data_length)
        print(info)
        return info

    
    def __eq__(self, other):
        raise NotImplementedError()


    def __hash__(self):
        raise NotImplementedError()


    @staticmethod
    def __unknown_peer_info(net_type):
        # Spin up a new class for this network type
        class UnknownPeerInfo(PeerInfo):

            NETWORK_TYPE = net_type

            def __init__(self, blob: bytes):
                self.blob = blob

            def _serialise(self):
                return self.blob
                
            @staticmethod
            def _build(stream, length):
                return UnknownPeerInfo(stream.read(length))

            def __eq__(self, other):
                return other.blob == self.blob

            def __hash__(self):
                return hash((self.NETWORK_TYPE, self.blob))

        # Return the dynamic class
        return UnknownPeerInfo

    def __repr__(self):
        return "<{} NETWORK_TYPE={}>".format(self.__class__.__name__, self.NETWORK_TYPE)

