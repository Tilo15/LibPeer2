

class PeerInfo:

    NETWORK_TYPE = b""

    def serialise(self):
        raise NotImplementedError()

    @staticmethod
    def _build(stream):
        raise NotImplementedError()

    @staticmethod
    def deserialise(ntype, stream):
        # Find the correct PeerInfo class to use
        peer_info = next(x for x in PeerInfo.__subclasses__() if x.NETWORK_TYPE == ntype)

        # Return the object
        return peer_info._build(stream)

    
    def __eq__(self, other):
        raise NotImplementedError()


    def __hash__(self):
        raise NotImplementedError()