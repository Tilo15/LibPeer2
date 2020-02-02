from LibPeer2.Networks.PeerInfo import PeerInfo
from LibPeer2.Networks import Network

class Receiption:

    def __init__(self, stream, peer_info: PeerInfo, network: Network):
        self.stream = stream
        self.peer_info = peer_info
        self.network = network