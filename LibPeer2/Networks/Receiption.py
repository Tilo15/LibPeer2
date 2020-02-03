from LibPeer2.Networks.PeerInfo import PeerInfo

class Receiption:

    def __init__(self, stream, peer_info: PeerInfo, network):
        self.stream = stream
        self.peer_info = peer_info
        self.network = network