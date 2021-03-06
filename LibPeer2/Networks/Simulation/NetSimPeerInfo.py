from LibPeer2.Networks.PeerInfo import PeerInfo

class NetSimPeerInfo(PeerInfo):

    NETWORK_TYPE = b"NetSim"

    def __init__(self, identifier: bytes):
        self.identifier = identifier

    def _serialise(self):
        return self.identifier
        

    @staticmethod
    def _build(stream, length):
        return NetSimPeerInfo(stream.read(16))


    def __eq__(self, other):
        return other.identifier == self.identifier

    def __hash__(self):
        return hash(self.identifier)