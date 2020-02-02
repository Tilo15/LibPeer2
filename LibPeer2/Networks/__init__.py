from LibPeer2.Networks.PeerInfo import PeerInfo
from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference
import rx

class Network:

    NETWORK_IDENTIFIER = b""

    def __init__(self):
        self.incoming_advertisment = rx.subjects.Subject()
        self.incoming_receiption = rx.subjects.Subject()

    def bring_up(self):
        raise NotImplementedError

    def bring_down(self):
        raise NotImplementedError

    def advertise(self, InstanceReference: InstanceReference):
        raise NotImplementedError

    def send(self, buffer, peer_info: PeerInfo):
        raise NotImplementedError
