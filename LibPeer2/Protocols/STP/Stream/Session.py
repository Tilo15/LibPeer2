from LibPeer2.Protocols.STP.Stream.Features import Feature
from LibPeer2.Protocols.STP.Stream.EgressStream import EgressStream
from LibPeer2.Protocols.STP.Stream.IngressStream import IngressStream

from typing import List

class Session:

    def __init__(self, features, identifier: bytes, ping: float, reference: bytes = b"\x00"*16, ingress = False):
        # Instansiate class members
        self.ingress = ingress
        self.features: List[Feature] = [x() for x in features]
        self.identifier = identifier
        self.reference = reference
        self.open = True
        self.ping = ping

        if(ingress):
            self.stream = IngressStream
        else:
            self.stream = EgressStream


    def send_segment(self, )