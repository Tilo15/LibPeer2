from LibPeer2.Networks.PeerInfo import PeerInfo

class NetSimPeerInfo(PeerInfo):

    NETWORK_TYPE = b"NetSim"

    def __init__(self, identifier: bytes):
        self.identifier = identifier

    def _serialise(self):
        return self.identifier
        

    @staticmethod
    def _build(stream):
        return NetSimPeerInfo(stream.read(16))