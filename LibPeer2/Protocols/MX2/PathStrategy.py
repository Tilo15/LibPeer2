from LibPeer2.Networks.PeerInfo import PeerInfo
from LibPeer2.Protocols.MX2.PathInfo import PathInfo

class PathStrategy:

    def __init__(self, path: PathInfo, first_hop: PeerInfo):
        self.path = path
        self.first_hop = first_hop