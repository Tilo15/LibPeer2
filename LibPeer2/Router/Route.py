from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Networks import Network
from LibPeer2.Networks.PeerInfo import PeerInfo

class Route:

    def __init__(self, instance: InstanceReference, peer: PeerInfo, network: Network):
        self.instance = instance
        self.network = network
        self.peer = peer
