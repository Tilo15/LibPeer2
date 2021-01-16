from LibPeer2.Protocols.MX2.InstanceReference import InstanceReference

from typing import Set

import rx.subject

class InstanceManager:
    
    def __init__(self, application_namespace: str, use_repeaters = True, networks = []):
        self.namespace = application_namespace
        self.new_peer = rx.subject.Subject()
        self.new_stream = rx.subject.Subject()
        self.use_repeaters = use_repeaters

    def establish_stream(self, peer: InstanceReference, *, in_reply_to = None) -> rx.subject.Subject:
        raise NotImplementedError()

    def find_resource_peers(self, resource: bytes) -> rx.subject.Subject:
        raise NotImplementedError()

    @property
    def resources(self) -> Set[bytes]:
        raise NotImplementedError()

