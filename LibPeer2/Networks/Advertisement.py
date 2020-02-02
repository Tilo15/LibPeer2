from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
from LibPeer2.Networks.PeerInfo import PeerInfo


class Advertisement:

    def __init__(self, instance_reference: InstanceReference, peer_info: PeerInfo):
        self.instance_reference = instance_reference
        self.peer_info = peer_info